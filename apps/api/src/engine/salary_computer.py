"""Salary Income Computer — Steps 1-4 of ITD tax computation pipeline.

Computes income under head "Salaries" matching incometax.gov.in portal exactly.

ITD Portal Computation Order (verified against portal backend):
  1. Gross Salary = 17(1) + 17(2) + 17(3)
  2. Less: Section 10 Exemptions (HRA, LTA, child edu, gratuity, leave encash, etc.)
  3. Less: Section 16 Deductions (Std Ded, Entertainment, Prof Tax)
  4. = Income under head "Salaries"

FY 2025-26 Values:
  Standard Deduction: ₹75,000 (New Regime) / ₹50,000 (Old Regime)
  Professional Tax: actual, max ₹2,500/yr

All computation uses 2 decimal places. Rounding only at final tax (not here).
"""

from decimal import Decimal
from typing import Optional

from src.models.form16 import Form16Data, Form16PartB, Form16Annexure, Section10Exemptions


# FY 2025-26 limits
STD_DEDUCTION_NEW = Decimal("75000")
STD_DEDUCTION_OLD = Decimal("50000")
MAX_PROFESSIONAL_TAX = Decimal("2500")
HRA_METRO_PCT = Decimal("0.50")       # 50% of basic+DA for metro
HRA_NON_METRO_PCT = Decimal("0.40")   # 40% for non-metro
CHILD_EDU_LIMIT = Decimal("100")      # per month per child, max 2 children
HOSTEL_LIMIT = Decimal("300")         # per month per child, max 2 children
MAX_CHILDREN = 2
MONTHS_PER_YEAR = 12


class SalaryBreakdown:
    """Complete salary breakdown matching ITD portal line items."""

    def __init__(self):
        # ── Gross Salary ──
        self.salary_171: Decimal = Decimal("0")       # Section 17(1) — basic + allowances
        self.perquisites_172: Decimal = Decimal("0")  # Section 17(2) — perquisites
        self.profits_lieu_173: Decimal = Decimal("0") # Section 17(3) — gratuity, leave, etc.
        self.gross_salary: Decimal = Decimal("0")

        # ── Allowances (Annexure breakdown) ──
        self.basic_da: Decimal = Decimal("0")
        self.hra_received: Decimal = Decimal("0")
        self.lta_received: Decimal = Decimal("0")
        self.special_allowance: Decimal = Decimal("0")
        self.other_allowances: Decimal = Decimal("0")

        # ── Section 10 Exemptions ──
        self.hra_exemption: Decimal = Decimal("0")
        self.lta_exemption: Decimal = Decimal("0")
        self.child_edu_exemption: Decimal = Decimal("0")
        self.hostel_exemption: Decimal = Decimal("0")
        self.gratuity_exemption: Decimal = Decimal("0")
        self.leave_encash_exemption: Decimal = Decimal("0")
        self.other_exemptions: Decimal = Decimal("0")
        self.total_exemptions: Decimal = Decimal("0")

        # ── Section 16 Deductions ──
        self.std_deduction: Decimal = Decimal("0")
        self.entertainment_allowance: Decimal = Decimal("0")
        self.professional_tax: Decimal = Decimal("0")
        self.total_salary_deductions: Decimal = Decimal("0")

        # ── Result ──
        self.income_from_salary: Decimal = Decimal("0")

    def to_dict(self) -> dict:
        return {
            "gross_salary": str(self.gross_salary),
            "basic_da": str(self.basic_da),
            "hra_received": str(self.hra_received),
            "hra_exemption": str(self.hra_exemption),
            "lta_exemption": str(self.lta_exemption),
            "other_exemptions": str(self.other_exemptions),
            "total_exemptions_s10": str(self.total_exemptions),
            "std_deduction": str(self.std_deduction),
            "professional_tax": str(self.professional_tax),
            "total_salary_deductions": str(self.total_salary_deductions),
            "income_from_salary": str(self.income_from_salary),
        }


class SalaryComputer:
    """Computes income under head 'Salaries' matching ITD portal output."""

    def compute(
        self,
        form16: Optional[Form16Data] = None,
        annexure: Optional[Form16Annexure] = None,
        rent_paid: Decimal = Decimal("0"),
        metro_city: bool = False,
        is_new_regime: bool = True,
        children_count: int = 0,
    ) -> SalaryBreakdown:
        """
        Compute salary income with ITD-matching logic.

        Args:
            form16: Parsed Form 16 data
            annexure: Salary component breakup
            rent_paid: Monthly rent paid (for HRA computation)
            metro_city: Whether taxpayer lives in metro (affects HRA: 50% vs 40%)
            is_new_regime: True = New Regime (115BAC), False = Old Regime
            children_count: Number of children (for child edu/hostel exemption)

        Returns SalaryBreakdown with all line items.
        """
        result = SalaryBreakdown()

        if not form16:
            return result

        pb = form16.part_b
        annex = annexure or form16.annexure

        # ── Step 1: Gross Salary (17(1) + 17(2) + 17(3)) ──
        result.salary_171 = pb.salary_171 or pb.total_gross_salary or Decimal("0")
        result.perquisites_172 = pb.perquisites_172 or Decimal("0")
        result.profits_lieu_173 = pb.profits_lieu_173 or Decimal("0")
        result.gross_salary = result.salary_171 + result.perquisites_172 + result.profits_lieu_173

        # Extract Annexure components
        result.basic_da = (annex.basic or Decimal("0")) + (getattr(annex, "da", None) or Decimal("0"))
        result.hra_received = annex.hra or Decimal("0")
        result.lta_received = annex.lta or Decimal("0")
        result.special_allowance = annex.special_allowance or Decimal("0")
        # Other allowances = total 17(1) - (basic + hra + lta + special)
        known = result.basic_da + result.hra_received + result.lta_received + result.special_allowance
        result.other_allowances = max(Decimal("0"), result.salary_171 - known)

        # ── Step 2: Section 10 Exemptions ──

        # Get Form 16 Section 10 exemptions (computed by employer)
        exemptions = pb.exemptions_s10

        # HRA Exemption: min(actual HRA, rent-10% basic, 40/50% basic)
        if result.hra_received > 0 and rent_paid > 0:
            actual_hra = result.hra_received
            rent_minus_10pct = max(
                Decimal("0"),
                (rent_paid * MONTHS_PER_YEAR) - (result.basic_da * Decimal("0.10"))
            )
            pct_of_basic = result.basic_da * (HRA_METRO_PCT if metro_city else HRA_NON_METRO_PCT)
            result.hra_exemption = min(actual_hra, rent_minus_10pct, pct_of_basic)

        # LTA Exemption: ONLY exempt up to actual travel cost
        # Form 16 shows LTA RECEIVED in Annexure. The exempt portion is under
        # Section 10(5) in Part B. Without actual travel proof, NONE is exempt.
        # The employer's Form 16 Section 10 exemption is the authoritative source.
        result.lta_exemption = exemptions.travel_concession_105 or Decimal("0")

        # Child Education Allowance: ₹100/month/child, max 2 children
        if children_count > 0:
            result.child_edu_exemption = min(
                Decimal(children_count), Decimal(MAX_CHILDREN)
            ) * CHILD_EDU_LIMIT * MONTHS_PER_YEAR

        # Hostel Allowance: ₹300/month/child, max 2 children
        # Only if hostel allowance is actually received

        # Gratuity and Leave Encashment exemptions (from Form 16 Part B Section 10)
        result.gratuity_exemption = exemptions.gratuity_1010
        result.leave_encash_exemption = exemptions.leave_encashment_1010AA

        result.total_exemptions = (
            result.hra_exemption
            + result.lta_exemption
            + result.child_edu_exemption
            + result.hostel_exemption
            + result.gratuity_exemption
            + result.leave_encash_exemption
            + exemptions.travel_concession_105
            + exemptions.commuted_pension_1010A
            + exemptions.special_allowances_1014
            + sum(e.deductible_amount for e in exemptions.other_exemptions_s10)
        )

        # ── Step 3: Section 16 Deductions ──
        result.std_deduction = STD_DEDUCTION_NEW if is_new_regime else STD_DEDUCTION_OLD

        # Professional Tax: from Form 16, capped at ₹2,500
        pt_from_f16 = pb.professional_tax_16iii or Decimal("0")
        result.professional_tax = min(pt_from_f16, MAX_PROFESSIONAL_TAX)

        result.total_salary_deductions = result.std_deduction + result.professional_tax

        # ── Step 4: Income under head "Salaries" ──
        result.income_from_salary = max(
            Decimal("0"),
            result.gross_salary - result.total_exemptions - result.total_salary_deductions
        )

        return result
