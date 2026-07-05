"""Test data factories for TaxStox backend.

Creates deterministic, realistic test data for all domain models.
No real PDFs, no external dependencies, no network calls.

All monetary values use Decimal. All dates are fixed for reproducibility.
"""

from datetime import date
from decimal import Decimal

from src.models.ais import (
    AISData,
    AISEquityMFSale,
    AISOtherUnitSale,
    AISSavingsInterest,
    AISTDSEntry,
)
from src.models.form16 import (
    ChapterVIADeductions,
    Form16Annexure,
    Form16Data,
    Form16PartA,
    Form16PartB,
    QuarterlyTDS,
    Regime,
    Section10Exemptions,
    TaxComputation,
)
from src.models.tax import (
    CGSaleEntry,
    CGDateRanges,
    ClassifiedCGData,
    UserAnswers,
)


# ── Form 16 Factory ──────────────────────────────────────────────────

def make_form16_data(
    salary: Decimal = Decimal("1000000"),
    perquisites: Decimal = Decimal("0"),
    profits_in_lieu: Decimal = Decimal("0"),
    std_deduction: Decimal = Decimal("75000"),
    professional_tax: Decimal = Decimal("0"),
    hra_received: Decimal = Decimal("0"),
    lta_received: Decimal = Decimal("0"),
    basic: Decimal = Decimal("500000"),
    special_allowance: Decimal = Decimal("200000"),
    employer_nps: Decimal = Decimal("0"),
    tds_deducted: Decimal = Decimal("50000"),
    regime_new: bool = True,
    sec80c: Decimal = Decimal("0"),
    sec80d: Decimal = Decimal("0"),
    employee_pan: str = "ABCDE1234F",
    employer_name: str = "TEST EMPLOYER LTD",
    employer_tan: str = "BLRA04654G",
    assessment_year: str = "2026-27",
) -> Form16Data:
    """Create a complete Form16Data object with realistic values.

    Args:
        salary: Section 17(1) salary
        perquisites: Section 17(2) perquisites
        profits_in_lieu: Section 17(3) profits in lieu
        std_deduction: Standard deduction (₹75K New, ₹50K Old)
        professional_tax: Professional tax paid
        hra_received: HRA received (for Annexure)
        lta_received: LTA received
        basic: Basic salary component
        special_allowance: Special allowance component
        employer_nps: Employer NPS contribution (80CCD(2))
        tds_deducted: Total TDS deducted by employer
        regime_new: True for New Regime (115BAC), False for Old
        sec80c: 80C deduction from Form 16
        sec80d: 80D deduction from Form 16
    """
    total_gross = salary + perquisites + profits_in_lieu

    exemptions = Section10Exemptions(
        hra_1013A=Decimal("0"),
        travel_concession_105=Decimal("0"),
    )

    deductions_80c = sec80c
    income_head_salary = max(
        Decimal("0"),
        total_gross - exemptions.total - std_deduction - professional_tax,
    )

    chapter_vi = ChapterVIADeductions(
        sec80c=deductions_80c,
        sec80ccd2=employer_nps,
        sec80d=sec80d,
    )

    tax_comp = TaxComputation(
        taxable_income=income_head_salary - chapter_vi.total,
        tax_on_income=Decimal("0"),
        health_education_cess=Decimal("0"),
        net_tax_payable=tds_deducted,
    )

    part_a = Form16PartA(
        certificate_no="TESTCERT001",
        employer_name=employer_name,
        employer_tan=employer_tan,
        employee_name="TEST TAXPAYER",
        employee_pan=employee_pan,
        assessment_year=assessment_year,
        period_from=date(2025, 4, 1),
        period_to=date(2026, 3, 31),
        quarterly_tds=[
            QuarterlyTDS(
                quarter="Q1",
                receipt_number="RCPT001",
                amount_paid=salary / Decimal("4"),
                tds_deducted=tds_deducted / Decimal("4"),
                tds_deposited=tds_deducted / Decimal("4"),
            ),
            QuarterlyTDS(
                quarter="Q2",
                receipt_number="RCPT002",
                amount_paid=salary / Decimal("4"),
                tds_deducted=tds_deducted / Decimal("4"),
                tds_deposited=tds_deducted / Decimal("4"),
            ),
            QuarterlyTDS(
                quarter="Q3",
                receipt_number="RCPT003",
                amount_paid=salary / Decimal("4"),
                tds_deducted=tds_deducted / Decimal("4"),
                tds_deposited=tds_deducted / Decimal("4"),
            ),
            QuarterlyTDS(
                quarter="Q4",
                receipt_number="RCPT004",
                amount_paid=salary / Decimal("4"),
                tds_deducted=tds_deducted / Decimal("4"),
                tds_deposited=tds_deducted / Decimal("4"),
            ),
        ],
        total_amount_paid=salary,
        total_tds_deducted=tds_deducted,
        total_tds_deposited=tds_deducted,
    )

    part_b = Form16PartB(
        opting_out_115bac=not regime_new,
        salary_171=salary,
        perquisites_172=perquisites,
        profits_lieu_173=profits_in_lieu,
        total_gross_salary=total_gross,
        exemptions_s10=exemptions,
        std_deduction_16ia=std_deduction,
        professional_tax_16iii=professional_tax,
        income_under_head_salaries=income_head_salary,
        gross_total_income=income_head_salary,
        chapter_vi_a=chapter_vi,
        taxable_income=income_head_salary - chapter_vi.total,
        tax_computation=tax_comp,
    )

    annexure = Form16Annexure(
        basic=basic,
        hra=hra_received,
        special_allowance=special_allowance,
        lta=lta_received,
        nps_employer=employer_nps,
    )

    return Form16Data(part_a=part_a, part_b=part_b, annexure=annexure)


# ── AIS Factory ──────────────────────────────────────────────────────

def make_ais_data(
    pan: str = "ABCDE1234F",
    name: str = "TEST TAXPAYER",
    dob: date | None = None,
    savings_interest: Decimal = Decimal("0"),
    term_deposit_interest: Decimal = Decimal("0"),
    equity_mf_sales: list[dict] | None = None,
    other_unit_sales: list[dict] | None = None,
) -> AISData:
    """Create an AISData object with optional capital gains entries.

    Args:
        pan: Taxpayer PAN
        name: Taxpayer name
        dob: Date of birth (defaults to 1995-04-25)
        savings_interest: Total savings account interest
        term_deposit_interest: Total term deposit interest
        equity_mf_sales: List of dicts with equity MF sale fields
        other_unit_sales: List of dicts with other unit sale fields
    """
    if dob is None:
        dob = date(1995, 4, 25)

    # Build savings interest entries
    savings_list = []
    if savings_interest > 0:
        savings_list.append(
            AISSavingsInterest(
                bank_name="TEST BANK",
                account_number="1234567890",
                account_type="Saving",
                interest_amount=savings_interest,
                reported_on=date(2026, 3, 31),
            )
        )

    # Build equity MF sale entries
    equity_list = []
    if equity_mf_sales:
        for s in equity_mf_sales:
            equity_list.append(
                AISEquityMFSale(
                    amc_name="Test AMC",
                    isin=s.get("isin", ""),
                    security_name=s.get("security_name", ""),
                    date_of_sale=_parse_date(s.get("date_of_sale", "")),
                    quantity=Decimal(s.get("quantity", "0")),
                    sale_price_per_unit=Decimal(s.get("sale_price_per_unit", "0")),
                    sale_consideration=Decimal(s.get("sale_consideration", "0")),
                    stt_paid=Decimal(s.get("stt_paid", "0")),
                    cost_of_acquisition=Decimal(s.get("cost_of_acquisition", "0")),
                    term=s.get("term", "Short"),
                )
            )

    # Build other unit sale entries
    other_list = []
    if other_unit_sales:
        for s in other_unit_sales:
            other_list.append(
                AISOtherUnitSale(
                    depository="CDSL",
                    security_name=s.get("security_name", ""),
                    isin=s.get("isin", ""),
                    date_of_sale=_parse_date(s.get("date_of_sale", "")),
                    quantity=Decimal(s.get("quantity", "0")),
                    sale_price=Decimal(s.get("sale_price", "0")),
                    sale_consideration=Decimal(s.get("sale_consideration", "0")),
                    cost_of_acquisition=Decimal(s.get("cost_of_acquisition", "0")),
                    term=s.get("term", "Short"),
                )
            )

    return AISData(
        pan=pan,
        name=name,
        dob=dob,
        savings_interest=savings_list,
        term_deposit_interest=(
            [AISSavingsInterest(
                bank_name="TEST BANK FD",
                account_number="9876543210",
                account_type="Term Deposit",
                interest_amount=term_deposit_interest,
                reported_on=date(2026, 3, 31),
            )]
            if term_deposit_interest > 0
            else []
        ),
        equity_mf_sales=equity_list,
        other_unit_sales=other_list,
    )


# ── UserAnswers Factory ──────────────────────────────────────────────

def make_user_answers(
    pays_rent: bool = False,
    rent_per_month: Decimal = Decimal("0"),
    rent_city_metro: bool = True,
    landlord_pan: str = "",
    has_health_insurance: bool = False,
    health_premium_self: Decimal = Decimal("0"),
    health_premium_parents: Decimal = Decimal("0"),
    parents_senior_citizen: bool = False,
    has_additional_80c: bool = False,
    additional_80c: dict[str, Decimal] | None = None,
    has_home_loan: bool = False,
    home_loan_interest: Decimal = Decimal("0"),
    home_loan_self_occupied: bool = True,
    has_other_income: bool = False,
) -> UserAnswers:
    """Create a UserAnswers object."""
    return UserAnswers(
        pays_rent=pays_rent,
        rent_per_month=rent_per_month,
        rent_city_metro=rent_city_metro,
        landlord_pan=landlord_pan,
        has_health_insurance=has_health_insurance,
        health_premium_self=health_premium_self,
        health_premium_parents=health_premium_parents,
        parents_senior_citizen=parents_senior_citizen,
        has_additional_80c=has_additional_80c,
        additional_80c_breakup=additional_80c or {},
        has_home_loan=has_home_loan,
        home_loan_interest=home_loan_interest,
        home_loan_self_occupied=home_loan_self_occupied,
        has_other_income=has_other_income,
    )


# ── ClassifiedCGData Factory ─────────────────────────────────────────

def make_classified_cg_data() -> ClassifiedCGData:
    """Create a ClassifiedCGData with a few representative entries."""
    # Equity LTCG (Schedule 112A)
    ltcg_entry = CGSaleEntry(
        date=date(2025, 4, 21),
        isin="INF966L01986",
        security_name="Quant ELSS Tax Saver Fund",
        quantity=Decimal("19.79"),
        sale_price=Decimal("383.77"),
        consideration=Decimal("7596"),
        cost=Decimal("5000"),
        stt_paid=True,
        term="Long",
        asset_class="equity_mf",
        gain=Decimal("2596"),
        tax_rate="12.5%",
        itr_section="112A",
        itr_schedule="Schedule112A",
        qualifies_for_125k_exemption=True,
        gain_after_exemption=Decimal("0"),
    )

    # Equity STCG (Schedule CG A2, 111A)
    stcg_15_entry = CGSaleEntry(
        date=date(2025, 8, 15),
        isin="INF200K01234",
        security_name="SBI Equity Fund",
        quantity=Decimal("50"),
        sale_price=Decimal("120.00"),
        consideration=Decimal("6000"),
        cost=Decimal("5500"),
        stt_paid=True,
        term="Short",
        asset_class="equity_mf",
        gain=Decimal("500"),
        tax_rate="15%",
        itr_section="111A",
        itr_schedule="ScheduleCG_A2",
        qualifies_for_125k_exemption=False,
        gain_after_exemption=Decimal("500"),
    )

    # Non-equity STCG (Schedule CG A5, slab rate)
    stcg_slab_entry = CGSaleEntry(
        date=date(2026, 2, 27),
        isin="INF277KA1976",
        security_name="TATA Gold ETF",
        quantity=Decimal("5"),
        sale_price=Decimal("15.38"),
        consideration=Decimal("77"),
        cost=Decimal("76"),
        stt_paid=False,
        term="Short",
        asset_class="etf_gold",
        gain=Decimal("1"),
        tax_rate="Slab",
        itr_section="A5",
        itr_schedule="ScheduleCG_A5",
        qualifies_for_125k_exemption=False,
        gain_after_exemption=Decimal("1"),
    )

    date_ranges = CGDateRanges()
    date_ranges.ltcg_12_5pct["Upto15Of6"] = Decimal("2596")
    date_ranges.stcg_15pct["Upto15Of9"] = Decimal("500")
    date_ranges.stcg_app_rate["Up16Of3To31Of3"] = Decimal("1")

    return ClassifiedCGData(
        schedule_112a=[ltcg_entry],
        cg_a2_stcg_111a=[stcg_15_entry],
        cg_a5_stcg_app_rate=[stcg_slab_entry],
        cg_b8_ltcg_other=[],
        date_ranges=date_ranges,
    )


# ── Helpers ──────────────────────────────────────────────────────────

def _parse_date(date_str: str) -> date:
    """Parse YYYY-MM-DD string to date, with fallback."""
    if not date_str:
        return date.today()
    try:
        parts = date_str.split("-")
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return date.today()
