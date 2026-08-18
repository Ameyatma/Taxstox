"""End-to-end test with real Form 16 and AIS PDFs (FY 2025-26 golden filing).

PR4: This real-data E2E test is OFF by default. It runs only when the operator
supplies the filing PDFs and identity via environment variables — no real PAN,
DOB, password, or personal filesystem paths are committed to the repository.

Required environment (all must be set and the PDFs must exist, otherwise the
entire module is skipped with an explicit reason):
  TAXSTOX_E2E_FORM16_PATH     — path to the Form 16 PDF
  TAXSTOX_E2E_AIS_PATH        — path to the AIS PDF
  TAXSTOX_E2E_PAN             — employee PAN (10 chars; also the Form 16 password)
  TAXSTOX_E2E_DOB             — employee DOB, DDMMYYYY (derives the AIS password)
  TAXSTOX_E2E_FORM16_PASSWORD — optional; defaults to PAN

EXPECTED below holds the golden reference values for a specific historical
filing (verified against the ITD ACK). Pointing the env vars at a *different*
filing means these golden values must be updated in lockstep — the assertions
fail loudly on drift rather than printing a warning and passing.
"""

import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.parsers.form16_parser import Form16Parser
from src.parsers.ais_parser import AISParser
from src.engine.classifier import ClassificationEngine
from src.engine.regime_optimizer_v2 import RegimeOptimizerV2
from src.models.tax import UnifiedTaxData, UserAnswers
from src.builders.itr_json_builder import ITRJSONBuilder
from src.builders.validator import ITRValidator

# ── Test configuration (externalized — no PII committed) ────────────────
PAN = os.environ.get("TAXSTOX_E2E_PAN", "").strip()
DOB = os.environ.get("TAXSTOX_E2E_DOB", "").strip()
FORM16_PASSWORD = os.environ.get("TAXSTOX_E2E_FORM16_PASSWORD", PAN).strip()
FORM16_PATH = Path(os.environ.get("TAXSTOX_E2E_FORM16_PATH", "")).expanduser()
AIS_PATH = Path(os.environ.get("TAXSTOX_E2E_AIS_PATH", "")).expanduser()

_MISSING = [
    name
    for name, value in {
        "TAXSTOX_E2E_FORM16_PATH": FORM16_PATH,
        "TAXSTOX_E2E_AIS_PATH": AIS_PATH,
        "TAXSTOX_E2E_PAN": PAN,
        "TAXSTOX_E2E_DOB": DOB,
    }.items()
    if not value
]

_SKIP_REASON = (
    "Real-data E2E is disabled by default. Set TAXSTOX_E2E_FORM16_PATH, "
    "TAXSTOX_E2E_AIS_PATH, TAXSTOX_E2E_PAN, and TAXSTOX_E2E_DOB (and ensure the "
    "PDFs exist) to run it. Missing: " + (", ".join(_MISSING) if _MISSING else "PDF file(s)")
)

pytestmark = pytest.mark.skipif(
    bool(_MISSING) or not (FORM16_PATH.is_file() and AIS_PATH.is_file()),
    reason=_SKIP_REASON,
)


def _dob_date(dob: str) -> date:
    """Parse a DDMMYYYY DOB string into a date (guaranteed 8 chars when present)."""
    return date(int(dob[4:8]), int(dob[2:4]), int(dob[0:2]))


# Known-correct values from the golden filing (verified against ITD portal).
EXPECTED = {
    "employer_tan": "BLRA04654G",
    "employer_name": "APPLIED MATERIALS",
    "gross_salary": Decimal("1871602"),
    "income_salaries": Decimal("1796602"),
    "employer_tds": Decimal("155738"),
    "regime": "new",
    "nps_employer": Decimal("47869"),
    "ltcg_112a": Decimal("58273"),  # 10 Quant ELSS redemptions
    "stcg_other": Decimal("5194"),  # 4 ETF sales
    "savings_interest": Decimal("757"),
    "total_income": Decimal("1754687"),
    "tax_with_cess": Decimal("156974"),
    "self_assessment_tax": Decimal("1240"),
    "balance_payable": Decimal("0"),
}


# ── Fixtures: one parse/classify/optimize/build pass, shared across tests ──
@pytest.fixture(scope="module")
def form16():
    """Parse the real Form 16 PDF (encrypted with the employee PAN)."""
    return Form16Parser().parse(FORM16_PATH, password=FORM16_PASSWORD)


@pytest.fixture(scope="module")
def ais():
    """Parse the real AIS PDF (PAN+DOB derive the decryption password)."""
    return AISParser().parse(AIS_PATH, PAN, DOB)


@pytest.fixture(scope="module")
def classified(ais):
    """Classify AIS capital-gain sales into ITR schedule buckets (raw, pre-exemption)."""
    return ClassificationEngine().classify(ais.equity_mf_sales, ais.other_unit_sales)


@pytest.fixture(scope="module")
def regime_result(form16, classified):
    """Run regime optimization (New vs Old) using the canonical v2 engine."""
    return RegimeOptimizerV2().optimize(
        form16=form16,
        classified_cg=classified,
        answers=UserAnswers(),  # default: no to every question
        savings_interest=EXPECTED["savings_interest"],
        other_interest=Decimal("0"),
    )


@pytest.fixture(scope="module")
def itr_json(form16, ais, classified, regime_result):
    """Build the full ITR JSON from the parsed + classified data."""
    unified = UnifiedTaxData(
        pan=PAN,
        dob=_dob_date(DOB),
        form16=form16,
        ais=ais,
        user_answers=UserAnswers(),
        capital_gains=classified,
        regime_result=regime_result,
        recommended_regime=regime_result.recommended,
    )
    return ITRJSONBuilder().build(unified)


# ── Tests ────────────────────────────────────────────────────────────────
def test_form16_parsing(form16):
    """Form 16 PDF parses to the golden filing's known-correct values."""
    assert form16.part_a.employee_pan == PAN, (
        f"PAN mismatch: {form16.part_a.employee_pan} != {PAN}"
    )
    assert form16.part_a.employer_tan == EXPECTED["employer_tan"], (
        f"TAN mismatch: {form16.part_a.employer_tan}"
    )
    assert EXPECTED["employer_name"] in form16.part_a.employer_name.upper(), (
        f"Employer: {form16.part_a.employer_name}"
    )
    assert form16.part_a.total_tds_deducted == EXPECTED["employer_tds"], (
        f"TDS: {form16.part_a.total_tds_deducted} != {EXPECTED['employer_tds']}"
    )
    assert form16.part_b.salary_171 == EXPECTED["gross_salary"], (
        f"Gross salary: {form16.part_b.salary_171} != {EXPECTED['gross_salary']}"
    )
    assert form16.part_b.income_under_head_salaries == EXPECTED["income_salaries"], (
        f"Income under head salaries: {form16.part_b.income_under_head_salaries}"
    )
    assert form16.regime.value == EXPECTED["regime"], (
        f"Regime: {form16.regime.value} != {EXPECTED['regime']}"
    )
    assert form16.part_b.chapter_vi_a.sec80ccd2 == EXPECTED["nps_employer"], (
        f"80CCD(2): {form16.part_b.chapter_vi_a.sec80ccd2} != {EXPECTED['nps_employer']}"
    )
    assert form16.part_b.std_deduction_16ia == Decimal("75000"), (
        f"Standard deduction: {form16.part_b.std_deduction_16ia} != 75000"
    )


def test_ais_parsing(ais):
    """AIS PDF parses to the golden filing's known-correct values."""
    assert ais.pan == PAN, f"AIS PAN: {ais.pan} != {PAN}"
    assert ais.name, "AIS name is empty"

    assert len(ais.equity_mf_sales) >= 1, "No equity MF sales found in AIS"
    total_emf_gain = sum(
        (s.sale_consideration - s.cost_of_acquisition for s in ais.equity_mf_sales),
        Decimal("0"),
    )
    assert abs(total_emf_gain - EXPECTED["ltcg_112a"]) <= 1, (
        f"Equity MF LTCG: {total_emf_gain} != {EXPECTED['ltcg_112a']}"
    )

    assert len(ais.other_unit_sales) >= 1, "No other-unit (ETF) sales found in AIS"
    total_otu_gain = sum(
        (s.sale_consideration - s.cost_of_acquisition for s in ais.other_unit_sales),
        Decimal("0"),
    )
    assert abs(total_otu_gain - EXPECTED["stcg_other"]) <= 1, (
        f"ETF STCG: {total_otu_gain} != {EXPECTED['stcg_other']}"
    )

    assert ais.total_savings_interest == EXPECTED["savings_interest"], (
        f"Savings interest: {ais.total_savings_interest} != {EXPECTED['savings_interest']}"
    )


def test_classification(classified):
    """Capital gains classify into 112A (equity LTCG) and CG buckets correctly."""
    engine = ClassificationEngine()

    assert len(classified.schedule_112a) >= 1, "No 112A (equity LTCG) entries classified"

    # Applying the 112A exemption and summarizing must be stable and non-negative.
    summary = engine.get_tax_summary(classified)
    assert Decimal(summary["ltcg_112a_taxable"]) >= 0
    assert Decimal(summary["ltcg_112a_tax"]) >= 0


def test_regime_optimizer(regime_result):
    """Regime optimizer recommends New regime and matches the golden tax figure."""
    assert regime_result.recommended.value == "new", (
        f"Expected NEW regime, got {regime_result.recommended.value}"
    )
    assert regime_result.new_tax <= regime_result.old_tax, (
        f"New regime tax {regime_result.new_tax} should not exceed old {regime_result.old_tax}"
    )
    assert abs(regime_result.new_tax - EXPECTED["tax_with_cess"]) <= 2, (
        f"New regime tax: {regime_result.new_tax} != {EXPECTED['tax_with_cess']} (±2)"
    )


def test_json_builder(itr_json):
    """ITR JSON builder produces the required top-level schedules."""
    assert "PartA_GeneralInfo" in itr_json, "Missing PartA_GeneralInfo"
    assert "ScheduleS" in itr_json, "Missing ScheduleS"
    assert itr_json["ScheduleS"].get("SalaryIncome"), "No salary income entries"

    # Tax-paid schedule must carry the employer TDS and a zero balance payable.
    tax_paid = itr_json.get("ScheduleTaxPaid", {})
    assert tax_paid, "Missing ScheduleTaxPaid"
    tds = Decimal(tax_paid.get("TDS", {}).get("SalaryTDS", "0"))
    assert tds == EXPECTED["employer_tds"], f"Salary TDS: {tds} != {EXPECTED['employer_tds']}"
    balance = Decimal(tax_paid.get("BalancePayable", "0"))
    assert balance == EXPECTED["balance_payable"], (
        f"Balance payable: {balance} != {EXPECTED['balance_payable']}"
    )


def test_validator(itr_json):
    """Built ITR JSON passes the validator with no blocking errors."""
    report = ITRValidator().validate(itr_json)
    assert report.can_file, (
        f"Validator blocking errors: "
        f"{[r.message for r in report.results if not r.passed and r.severity != 'warning']}"
    )