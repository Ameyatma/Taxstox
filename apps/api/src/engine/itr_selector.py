"""ITR Form Selector — Auto-selects the correct ITR form based on income sources.

Rules (for FY 2025-26 / AY 2026-27):
  ITR-1 (SAHAJ): Salary/pension + one house property + interest income + agricultural income ≤ ₹5,000
                 Total income ≤ ₹50L. NO capital gains, NO business income, NO foreign income.
  ITR-2: Salary + multiple house properties + capital gains + foreign income + agricultural income > ₹5,000
         NO business/profession income.
  ITR-3: Business/profession income (full P&L) + any of ITR-2 sources.
  ITR-4 (SUGAM): Presumptive income u/s 44AD, 44ADA, 44AE. Total income ≤ ₹50L.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class ITRForm(str, Enum):
    ITR1 = "ITR-1"
    ITR2 = "ITR-2"
    ITR3 = "ITR-3"
    ITR4 = "ITR-4"


@dataclass
class ITRSelectionResult:
    """The recommended ITR form with reasoning."""
    form: ITRForm
    eligibility: dict = field(default_factory=dict)
    disqualifiers: list[str] = field(default_factory=list)
    explanation: str = ""


class ITRSelector:
    """Determines the correct ITR form based on detected income sources."""

    def select(
        self,
        has_salary: bool = False,
        has_house_property: bool = False,
        house_property_count: int = 0,
        has_capital_gains: bool = False,
        has_business_income: bool = False,
        business_type: str = "",  # "full_pnl" or "presumptive"
        has_foreign_income: bool = False,
        has_agricultural_income: bool = False,
        agricultural_income_amount: Decimal = Decimal("0"),
        has_crypto_vda: bool = False,
        has_other_sources: bool = False,
        total_income: Decimal = Decimal("0"),
    ) -> ITRSelectionResult:
        """Select the appropriate ITR form."""
        disqualifiers: list[str] = []
        eligibility: dict = {"itr1": True, "itr2": True, "itr3": True, "itr4": True}

        # ── ITR-1 disqualifiers ──
        if has_capital_gains:
            disqualifiers.append("Capital gains detected — ITR-1 does not support capital gains.")
            eligibility["itr1"] = False
        if has_business_income:
            disqualifiers.append("Business/profession income detected.")
            eligibility["itr1"] = False
        if has_foreign_income:
            disqualifiers.append("Foreign income/assets detected — requires ITR-2 or ITR-3.")
            eligibility["itr1"] = False
        if house_property_count > 1:
            disqualifiers.append(f"Multiple house properties ({house_property_count}) — ITR-1 supports only one.")
            eligibility["itr1"] = False
        if has_agricultural_income and agricultural_income_amount > 5000:
            disqualifiers.append(f"Agricultural income ₹{agricultural_income_amount:,.0f} exceeds ₹5,000 limit for ITR-1.")
            eligibility["itr1"] = False
        if has_crypto_vda:
            disqualifiers.append("Crypto/VDA income — requires ITR-2 or ITR-3.")
            eligibility["itr1"] = False
        if total_income > 5_000_000:
            disqualifiers.append(f"Total income ₹{total_income:,.0f} exceeds ₹50L limit for ITR-1.")
            eligibility["itr1"] = False

        # ── ITR-2 disqualifiers ──
        if has_business_income and business_type == "full_pnl":
            disqualifiers.append("Full P&L business income — requires ITR-3.")
            eligibility["itr2"] = False

        # ── ITR-4 disqualifiers ──
        if has_capital_gains:
            eligibility["itr4"] = False
        if has_foreign_income:
            eligibility["itr4"] = False
        if house_property_count > 1:
            eligibility["itr4"] = False
        if total_income > 5_000_000:
            eligibility["itr4"] = False
        if has_business_income and business_type == "full_pnl":
            eligibility["itr4"] = False
        if not has_business_income:
            eligibility["itr4"] = False  # ITR-4 only for presumptive business

        # ── ITR-3 disqualifiers ──
        if not has_business_income:
            eligibility["itr3"] = False  # ITR-3 only for business income
        if has_business_income and business_type != "full_pnl":
            eligibility["itr3"] = False

        # ── Select the appropriate form ──
        if eligibility.get("itr1") and not any(
            not eligibility.get(f) for f in ["itr1"]
        ):
            form = ITRForm.ITR1
            explanation = "ITR-1 (SAHAJ): Suitable for salaried individuals with simple income."
        elif eligibility.get("itr2") and not has_business_income:
            form = ITRForm.ITR2
            explanation = "ITR-2: Suitable for individuals with capital gains, multiple house properties, or foreign income."
        elif eligibility.get("itr3") and has_business_income:
            form = ITRForm.ITR3
            explanation = "ITR-3: Required for individuals with business/profession income (full P&L)."
        elif eligibility.get("itr4") and business_type == "presumptive":
            form = ITRForm.ITR4
            explanation = "ITR-4 (SUGAM): For presumptive taxation under sections 44AD, 44ADA, or 44AE."
        else:
            # Default to ITR-2 (most flexible for non-business)
            form = ITRForm.ITR2
            explanation = "ITR-2: Recommended based on your income profile."

        return ITRSelectionResult(
            form=form,
            eligibility=eligibility,
            disqualifiers=disqualifiers,
            explanation=explanation,
        )


# Convenience function
def select_itr_form(**kwargs) -> ITRSelectionResult:
    return ITRSelector().select(**kwargs)
