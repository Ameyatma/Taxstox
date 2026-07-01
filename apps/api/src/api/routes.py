"""FastAPI routes for TaxStox ITR Auto-Filing."""

import tempfile
import logging
from pathlib import Path
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.models.api import (
    UploadRequest,
    UploadResponse,
    QuestionsResponse,
    AnswersSubmitRequest,
    TaxSummaryResponse,
    ExportResponse,
)
from src.models.tax import UserAnswers
from src.parsers.form16_parser import Form16Parser
from src.parsers.ais_parser import AISParser
from src.engine.classifier import ClassificationEngine
from src.engine.regime_optimizer import RegimeOptimizer
from src.engine.questions import QuestionEngine
from src.builders.itr_json_builder import ITRJSONBuilder
from src.builders.validator import ITRValidator
from src.utils.password_resolver import PasswordResolver
from src.utils.session import session_manager, Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ITR"])


def get_session(session_id: str) -> Session:
    """Dependency: get valid session or 404."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    return session


# ── Step 1: Upload PDFs ────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_pdfs(
    pan: str = Form(...),
    dob: str = Form(...),
    form16_pdf: Optional[UploadFile] = File(None),
    ais_pdf: Optional[UploadFile] = File(None),
    form16_password: Optional[str] = Form(None),
):
    """
    Upload Form 16 and/or AIS PDFs.

    - PAN + DOB are mandatory (DOB in DDMMYYYY format for AIS password)
    - Form 16 password is optional — auto-tried if not provided
    - AIS password is auto-computed from PAN+DOB
    """
    # Create session
    session = session_manager.create(pan, dob)

    form16_parsed = False
    ais_parsed = False
    password_required = False
    password_hint = None
    data_summary = {}

    # Parse Form 16
    if form16_pdf:
        content = await form16_pdf.read()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            parser = Form16Parser()

            # Try provided password, then PAN candidates
            passwords_to_try = []
            if form16_password:
                passwords_to_try.append(form16_password.strip())
            passwords_to_try.extend(PasswordResolver.get_form16_candidates(pan))

            last_error = None
            for pwd in passwords_to_try:
                try:
                    session.form16 = parser.parse(tmp_path, password=pwd)
                    logger.info(f"PARSED with pwd={pwd}: salary={session.form16.part_b.total_gross_salary}, employer={session.form16.part_a.employer_name}, regime={session.form16.regime}")
                    form16_parsed = True
                    break
                except (ValueError, RuntimeError) as e:
                    last_error = str(e)
                    logger.warning(f"Parse failed with pwd={pwd}: {e}")
                    continue

            if not form16_parsed:
                password_required = True
                password_hint = PasswordResolver.get_password_hint("form16", pan)

        finally:
            tmp_path.unlink(missing_ok=True)

    # Parse AIS
    if ais_pdf:
        content = await ais_pdf.read()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            ais_password = PasswordResolver.get_ais_password(pan, dob)
            ais_parser = AISParser()
            session.ais = ais_parser.parse(tmp_path, pan, dob)
            ais_parsed = True
        except Exception as e:
            logger.error(f"AIS parsing failed: {e}")
            # AIS might be corrupted or password might be wrong
            # Don't block — user can still proceed with Form 16 only
        finally:
            tmp_path.unlink(missing_ok=True)

    # Build summary
    if form16_parsed and session.form16:
        data_summary["salary"] = str(session.form16.part_b.total_gross_salary)
        data_summary["employer"] = session.form16.part_a.employer_name
        data_summary["regime_from_f16"] = session.form16.regime.value

    if ais_parsed and session.ais:
        data_summary["equity_mf_sales"] = len(session.ais.equity_mf_sales)
        data_summary["other_unit_sales"] = len(session.ais.other_unit_sales)
        data_summary["savings_interest"] = str(session.ais.total_savings_interest)

    # Determine status
    if form16_parsed or ais_parsed:
        session.status = "parsed"
        status = "parsed"
    elif password_required:
        status = "password_required"
    else:
        status = "error"

    return UploadResponse(
        session_id=session.session_id,
        status=status,
        data_summary=data_summary if data_summary else None,
        password_required=password_required,
        password_hint=password_hint,
    )


# ── Step 2: Process & Get Questions ─────────────────────────────────

@router.post("/process/{session_id}", response_model=QuestionsResponse)
async def process_and_get_questions(
    session_id: str,
    session: Session = Depends(get_session),
):
    """
    Run classification + regime optimization, then return smart questions.
    This is called after successful upload. No user answers needed yet.
    """
    if not session.form16:
        raise HTTPException(status_code=400, detail="Form 16 is required for processing.")

    # Classify capital gains
    classifier = ClassificationEngine()
    equity_sales = session.ais.equity_mf_sales if session.ais else []
    other_sales = session.ais.other_unit_sales if session.ais else []
    session.classified_cg = classifier.classify(equity_sales, other_sales)

    # Optimize regime
    optimizer = RegimeOptimizer()
    savings_interest = session.ais.total_savings_interest if session.ais else Decimal("0")
    other_interest = session.ais.total_tds_interest if session.ais else Decimal("0")
    session.regime_result = optimizer.optimize(
        session.form16,
        session.classified_cg,
        session.user_answers,
        savings_interest,
        other_interest,
    )

    # Generate questions
    question_engine = QuestionEngine()
    response = question_engine.generate(
        itr_type="ITR-2",
        form16=session.form16,
        ais=session.ais,
        recommended_regime=session.regime_result.recommended,
        regime_savings=session.regime_result.savings,
    )
    session.status = "classified"
    return response


# ── Step 3: Submit Answers & Get Tax Summary ────────────────────────

@router.post("/answers/{session_id}", response_model=TaxSummaryResponse)
async def submit_answers(
    session_id: str,
    request: AnswersSubmitRequest,
    session: Session = Depends(get_session),
):
    """
    Submit user's yes/no answers, recompute tax, return the 1-page summary.
    """
    # Update user answers
    answers = request.answers
    session.user_answers = UserAnswers(
        pays_rent=answers.get("rent") == "yes",
        rent_per_month=Decimal(str(answers.get("rent_amount", "0"))),
        rent_city_metro=answers.get("rent_city") == "yes",
        landlord_pan=answers.get("rent_landlord_pan", ""),
        has_health_insurance=answers.get("health_insurance") == "yes",
        health_premium_self=Decimal(str(answers.get("health_premium_self", "0"))),
        health_premium_parents=Decimal(str(answers.get("health_premium_parents", "0"))),
        parents_senior_citizen=answers.get("parents_senior_citizen") == "yes",
        has_additional_80c=answers.get("additional_80c") == "yes",
        additional_80c_breakup=_extract_80c_breakup(answers),
        has_home_loan=answers.get("home_loan") == "yes",
        home_loan_interest=Decimal(str(answers.get("home_loan_interest", "0"))),
        home_loan_self_occupied=answers.get("home_loan_type", "self") == "self",
        has_other_income=answers.get("other_income") == "yes",
    )

    # Recompute regime with answers
    optimizer = RegimeOptimizer()
    savings_interest = session.ais.total_savings_interest if session.ais else Decimal("0")
    other_interest = session.ais.total_tds_interest if session.ais else Decimal("0")
    session.regime_result = optimizer.optimize(
        session.form16,
        session.classified_cg,
        session.user_answers,
        savings_interest,
        other_interest,
    )

    r = session.regime_result
    is_new = session.regime_result.recommended.value == "new"
    breakdown = r.new_breakdown if is_new else r.old_breakdown

    session.status = "questions_answered"

    from datetime import date
    return TaxSummaryResponse(
        income={
            "Salary": Decimal(breakdown.get("income_salary", "0")),
            "Capital Gains": Decimal(breakdown.get("income_cg", "0")),
            "Interest": Decimal(breakdown.get("income_interest", "0")),
        },
        deductions={
            "Employer NPS (80CCD(2))": session.form16.part_b.chapter_vi_a.sec80ccd2,
        },
        taxable_income=Decimal(breakdown.get("total_income", "0")),
        tax_breakdown={
            "Tax on Slab Income": Decimal(breakdown.get("tax_slab", "0")),
            "Tax on Special Rates (CG)": Decimal(breakdown.get("tax_special_rates", "0")),
            "Rebate 87A": Decimal(breakdown.get("rebate_87a", "0")),
            "Health & Education Cess": Decimal(breakdown.get("cess", "0")),
        },
        payments={
            "TDS by Employer": session.form16.part_a.total_tds_deducted,
            "Other TDS": session.ais.total_non_salary_tds if session.ais else Decimal("0"),
        },
        balance_payable=Decimal(breakdown.get("net_tax", "0"))
        - session.form16.part_a.total_tds_deducted
        - (session.ais.total_non_salary_tds if session.ais else Decimal("0")),
        regime=session.regime_result.recommended,
        regime_savings=session.regime_result.savings,
        filing_deadline=date(2026, 7, 31),
    )


# ── Step 4: Build & Export ITR JSON ─────────────────────────────────

@router.post("/export/{session_id}", response_model=ExportResponse)
async def export_itr_json(
    session_id: str,
    session: Session = Depends(get_session),
):
    """
    Build the final ITR JSON, validate it, and return it for download.
    """
    # Build JSON
    builder = ITRJSONBuilder()
    unified = session.unified_data
    unified.regime_result = session.regime_result
    unified.recommended_regime = session.regime_result.recommended

    itr_json = builder.build(unified)

    # Validate
    validator = ITRValidator()
    report = validator.validate(itr_json)

    session.itr_json = itr_json
    session.status = "built"

    if not report.can_file:
        # Return JSON anyway but flag validation issues
        return ExportResponse(
            filename=f"{session.pan}_ITR2_{session.form16.part_a.assessment_year.replace('-', '_')}.json",
            json_data=itr_json,
            validation_passed=False,
            validation_warnings=[
                r.message for r in report.results
                if not r.passed and r.severity != "info"
            ],
        )

    return ExportResponse(
        filename=f"{session.pan}_ITR2_{session.form16.part_a.assessment_year.replace('-', '_')}.json",
        json_data=itr_json,
        validation_passed=True,
    )


# ── Broker Statement Upload ──────────────────────────────────────────

@router.post("/upload/broker-statement/{session_id}")
async def upload_broker_statement(
    session_id: str,
    file: UploadFile = File(...),
    broker: str = Form("zerodha"),
    session: Session = Depends(get_session),
):
    """
    Upload a broker trade statement (Zerodha CSV, CAMS PDF, etc.)
    and auto-classify capital gains into the session.
    """
    from src.parsers.broker_statements.zerodha import parse_zerodha_tradebook, parse_zerodha_tax_pnl

    content = await file.read()

    try:
        if broker.lower() == "zerodha":
            # Try Tax P&L format first (preferred), fall back to tradebook
            try:
                entries = parse_zerodha_tax_pnl(content, file.filename or "")
            except Exception:
                entries = parse_zerodha_tradebook(content, file.filename or "")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported broker: {broker}. Currently supported: zerodha")

        if not entries:
            raise HTTPException(status_code=400, detail="No valid sell transactions found in the uploaded file.")

        # Classify the entries
        from src.engine.classifier import ClassificationEngine
        engine = ClassificationEngine()

        # Separate equity/non-equity entries and classify
        equity_sales = []
        other_sales = []

        # Convert CGSaleEntry to AIS-compatible format for classification
        from src.models.ais import AISEquityMFSale, AISOtherUnitSale

        for e in entries:
            if e.asset_class in ("equity", "equity_mf"):
                equity_sales.append(AISEquityMFSale(
                    date_of_sale=e.date,
                    isin=e.isin,
                    security_name=e.security_name,
                    quantity=e.quantity,
                    sale_price_per_unit=e.sale_price,
                    sale_consideration=e.consideration,
                    cost_of_acquisition=e.cost,
                    stt_paid=Decimal("1") if e.stt_paid else Decimal("0"),
                    term=e.term or "Short",
                ))
            else:
                other_sales.append(AISOtherUnitSale(
                    date_of_sale=e.date,
                    isin=e.isin,
                    security_name=e.security_name,
                    quantity=e.quantity,
                    sale_price=e.sale_price,
                    sale_consideration=e.consideration,
                    cost_of_acquisition=e.cost,
                    term=e.term or "Short",
                ))

        # Merge with existing AIS data if any
        if session.ais:
            equity_sales = (session.ais.equity_mf_sales or []) + equity_sales
            other_sales = (session.ais.other_unit_sales or []) + other_sales

        # Classify
        classified = engine.classify(equity_sales, other_sales)
        session.classified_cg = classified

        return {
            "status": "classified",
            "entries_found": len(entries),
            "equity_sales": len(equity_sales),
            "other_sales": len(other_sales),
            "total_cg": str(classified.total_cg),
            "total_stcg": str(classified.total_stcg),
            "total_ltcg": str(classified.total_ltcg),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Broker statement parsing failed")
        raise HTTPException(status_code=500, detail=f"Failed to parse statement: {str(e)}")


# ── Document Upload ──────────────────────────────────────────────────

@router.post("/upload/document/{session_id}")
async def upload_document(
    session_id: str,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    session: Session = Depends(get_session),
):
    """
    Upload an investment proof document for deduction tracking.

    Supported doc_types: 80c_ppf, 80c_elss, 80c_lic, 80c_tuition,
                         80d_insurance, hra_rent_receipt, home_loan_cert,
                         other
    """
    valid_types = {
        "80c_ppf", "80c_elss", "80c_lic", "80c_tuition",
        "80d_insurance", "hra_rent_receipt", "home_loan_cert", "other",
    }

    if doc_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid doc_type. Must be one of: {', '.join(sorted(valid_types))}")

    # Store document metadata in session
    if not hasattr(session, "documents"):
        session.documents = []
    session.documents.append({
        "doc_type": doc_type,
        "filename": file.filename or "unknown",
        "size": len(await file.read()),
    })

    return {
        "status": "uploaded",
        "doc_type": doc_type,
        "filename": file.filename,
        "total_documents": len(session.documents),
    }


# ── Health Check ────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "TaxStox ITR Engine", "version": "0.1.0"}


# ── Helper ──────────────────────────────────────────────────────────

def _extract_80c_breakup(answers: dict) -> dict[str, Decimal]:
    """Extract 80C breakup from answer dict."""
    mapping = {
        "80c_ppf": "ppf",
        "80c_elss": "elss",
        "80c_lic": "lic",
        "80c_tuition": "tuition",
        "80c_home_loan_principal": "home_loan_principal",
        "80ccd1b_nps": "nps_own",
    }
    breakup = {}
    for key, label in mapping.items():
        val = answers.get(key)
        if val:
            try:
                breakup[label] = Decimal(str(val))
            except Exception:
                pass
    return breakup
