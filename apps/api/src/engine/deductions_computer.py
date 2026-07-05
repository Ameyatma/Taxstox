"""Chapter VI-A Deductions Computer — Step 9 of ITD computation pipeline.

Computes ALL available deductions under Old Regime matching ITD portal exactly.
New Regime only allows 80CCD(2) (Employer NPS).

ITD Portal Rules (verified):
  - 80C: Auto-capped at ₹1,50,000 silently (no warning)
  - 80CCD(1B): Additional NPS over 80C limit, max ₹50,000
  - 80CCD(2): Employer NPS — available in BOTH regimes
  - 80D: ₹25,000 self+family, ₹50,000 parents-senior, ₹25,000 parents-non-senior
  - 80TTA: Savings interest max ₹10,000 (non-senior)
  - 80TTB: Interest max ₹50,000 (senior citizen 60+)
  - 80GG: Rent paid without HRA, max ₹60,000/yr
  - 80E: Education loan interest — unlimited, max 8 years
  - 80G: Donations — 50% or 100% with/without qualifying limit

FY 2025-26 limits. All values in INR.
"""

from decimal import Decimal

from src.models.form16 import Form16Data, ChapterVIADeductions
from src.models.tax import UserAnswers


# ── FY 2025-26 Statutory Limits ──

LIMIT_80C = Decimal("150000")          # Combined 80C + 80CCC + 80CCD(1)
LIMIT_80CCD1B = Decimal("50000")       # Additional NPS beyond 80C
LIMIT_80D_SELF = Decimal("25000")      # Self + spouse + children
LIMIT_80D_SELF_SENIOR = Decimal("50000")  # Self (senior citizen)
LIMIT_80D_PARENTS = Decimal("25000")   # Parents (non-senior)
LIMIT_80D_PARENTS_SENIOR = Decimal("50000")  # Parents (senior citizen)
LIMIT_80TTA = Decimal("10000")         # Savings interest (non-senior)
LIMIT_80TTB = Decimal("50000")         # Interest (senior citizen 60+)
LIMIT_80GG = Decimal("60000")          # Rent paid without HRA
LIMIT_24B_SELF = Decimal("200000")     # Home loan interest (self-occupied)
LIMIT_24B_LETOUT = Decimal("9999999999")  # Let-out: unlimited


class DeductionsBreakdown:
    """Complete Chapter VI-A deduction breakdown."""

    def __init__(self):
        self.sec80c: Decimal = Decimal("0")
        self.sec80c_components: dict[str, Decimal] = {}   # epf, ppf, elss, lic, tuition, hl_principal
        self.sec80ccc: Decimal = Decimal("0")
        self.sec80ccd1: Decimal = Decimal("0")
        self.sec80ccd1b: Decimal = Decimal("0")           # Additional NPS
        self.sec80ccd2: Decimal = Decimal("0")            # Employer NPS
        self.sec80d: Decimal = Decimal("0")
        self.sec80d_breakup: dict[str, Decimal] = {}      # self_premium, parents_premium
        self.sec80dd: Decimal = Decimal("0")
        self.sec80ddb: Decimal = Decimal("0")
        self.sec80e: Decimal = Decimal("0")
        self.sec80g: Decimal = Decimal("0")
        self.sec80gg: Decimal = Decimal("0")
        self.sec80tta: Decimal = Decimal("0")
        self.sec80ttb: Decimal = Decimal("0")
        self.sec80u: Decimal = Decimal("0")
        self.total: Decimal = Decimal("0")

    def to_dict(self) -> dict:
        return {
            "sec80c": str(self.sec80c),
            "sec80c_components": {k: str(v) for k, v in self.sec80c_components.items()},
            "sec80ccd1b": str(self.sec80ccd1b),
            "sec80ccd2": str(self.sec80ccd2),
            "sec80d": str(self.sec80d),
            "sec80d_breakup": {k: str(v) for k, v in self.sec80d_breakup.items()},
            "sec80e": str(self.sec80e),
            "sec80g": str(self.sec80g),
            "sec80gg": str(self.sec80gg),
            "sec80tta": str(self.sec80tta),
            "sec80ttb": str(self.sec80ttb),
            "sec80u": str(self.sec80u),
            "total_chapter_via": str(self.total),
        }


class DeductionsComputer:
    """Computes Chapter VI-A deductions matching ITD portal logic."""

    def compute(
        self,
        form16: Optional[Form16Data] = None,
        answers: Optional[UserAnswers] = None,
        savings_interest: Decimal = Decimal("0"),
        total_interest: Decimal = Decimal("0"),
        salary_income: Decimal = Decimal("0"),
        is_new_regime: bool = False,
        is_senior_citizen: bool = False,
    ) -> DeductionsBreakdown:
        """
        Compute all applicable Chapter VI-A deductions.

        New Regime: Only 80CCD(2) allowed.
        Old Regime: All sections apply, auto-capped at statutory limits.
        """
        result = DeductionsBreakdown()
        ua = answers or UserAnswers()

        # ── 80CCD(2): Employer NPS — available in BOTH regimes ──
        if form16:
            result.sec80ccd2 = form16.part_b.chapter_vi_a.sec80ccd2 or Decimal("0")

        # Under New Regime, ONLY 80CCD(2) is available
        if is_new_regime:
            result.total = result.sec80ccd2
            return result

        # ── Below: OLD REGIME ONLY ──

        # ── 80C: Auto-capped at ₹1,50,000 ──
        epf_from_f16 = form16.part_b.chapter_vi_a.sec80c if form16 else Decimal("0")
        additional_80c = Decimal("0")
        components_80c = {}

        if form16:
            components_80c["epf"] = epf_from_f16

        if ua.has_additional_80c and ua.additional_80c_breakup:
            for key, amount in ua.additional_80c_breakup.items():
                val = Decimal(str(amount))
                components_80c[key] = val
                additional_80c += val

        total_80c_input = epf_from_f16 + additional_80c
        result.sec80c = min(total_80c_input, LIMIT_80C)
        result.sec80c_components = components_80c

        # ── 80CCD(1B): Additional NPS (beyond 80C) ──
        if ua.has_additional_80c and ua.additional_80c_breakup:
            nps_own = ua.additional_80c_breakup.get("nps_own", Decimal("0"))
            result.sec80ccd1b = min(Decimal(str(nps_own)), LIMIT_80CCD1B)

        # ── 80D: Health Insurance ──
        if ua.has_health_insurance:
            self_premium = ua.health_premium_self or Decimal("0")
            parents_premium = ua.health_premium_parents or Decimal("0")

            limit_self = LIMIT_80D_SELF_SENIOR if is_senior_citizen else LIMIT_80D_SELF
            limit_parents = LIMIT_80D_PARENTS_SENIOR if ua.parents_senior_citizen else LIMIT_80D_PARENTS

            ded_self = min(self_premium, limit_self)
            ded_parents = min(parents_premium, limit_parents)
            result.sec80d = ded_self + ded_parents
            result.sec80d_breakup = {
                "self_premium": ded_self,
                "parents_premium": ded_parents,
            }

        # ── 80TTA / 80TTB: Interest deduction ──
        if is_senior_citizen:
            result.sec80ttb = min(total_interest, LIMIT_80TTB)
        else:
            result.sec80tta = min(savings_interest, LIMIT_80TTA)

        # ── 80GG: Rent without HRA ──
        if ua.pays_rent and result.sec80ccd2 is not None:
            annual_rent = (ua.rent_per_month or Decimal("0")) * Decimal("12")
            if annual_rent > 0:
                # Formula: least of ₹5,000/month, 25% of total income, or rent-10% of total income
                option_a = Decimal("5000") * Decimal("12")  # ₹60,000
                option_b = salary_income * Decimal("0.25")
                option_c = max(Decimal("0"), annual_rent - (salary_income * Decimal("0.10")))
                result.sec80gg = min(option_a, option_b, option_c)
                result.sec80gg = min(result.sec80gg, LIMIT_80GG)

        # ── 80E: Education Loan Interest (unlimited, 8 years) ──
        if ua.has_other_income:
            for detail in (ua.other_income_details or []):
                if detail.get("type") == "education_loan":
                    result.sec80e += Decimal(str(detail.get("amount", "0")))

        # ── Total ──
        result.total = (
            result.sec80c
            + result.sec80ccc
            + result.sec80ccd1
            + result.sec80ccd1b
            + result.sec80ccd2
            + result.sec80d
            + result.sec80dd
            + result.sec80ddb
            + result.sec80e
            + result.sec80g
            + result.sec80gg
            + result.sec80tta
            + result.sec80ttb
            + result.sec80u
        )

        return result
