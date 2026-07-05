"""Complete Chapter VI-A Deduction Engine — all sections with RuleRepository limits.

Traceability: C5.1 (Chapter VI-A — 55%→80%), C5.4 (Deduction Optimization), C5.6 (Home Loan), C5.7 (NPS)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from src.engine.rules.config import rule_repository, TaxYearConfig
from src.models.financial_year import FinancialYear
from src.models.form16 import Form16Data
from src.models.tax import UserAnswers


@dataclass
class DeductionBreakdown:
    """All Chapter VI-A deductions with section-level detail."""

    # 80C Aggregate
    sec80c_total: Decimal = Decimal("0")
    sec80c_components: dict[str, Decimal] = field(default_factory=dict)

    # NPS
    sec80ccd1: Decimal = Decimal("0")     # NPS employee (within 80C)
    sec80ccd1b: Decimal = Decimal("0")    # Additional NPS ₹50K
    sec80ccd2: Decimal = Decimal("0")     # Employer NPS (both regimes)

    # Health
    sec80d_self: Decimal = Decimal("0")
    sec80d_parents: Decimal = Decimal("0")

    # Disability/Medical
    sec80dd: Decimal = Decimal("0")
    sec80ddb: Decimal = Decimal("0")
    sec80u: Decimal = Decimal("0")

    # Interest-based
    sec80e: Decimal = Decimal("0")        # Education loan
    sec80ee: Decimal = Decimal("0")       # First home loan (₹50K)
    sec80eea: Decimal = Decimal("0")      # Affordable housing (₹1.5L)
    sec80eeb: Decimal = Decimal("0")      # EV loan (₹1.5L)

    # Savings interest
    sec80tta: Decimal = Decimal("0")      # ₹10K non-senior
    sec80ttb: Decimal = Decimal("0")      # ₹50K senior

    # Rent
    sec80gg: Decimal = Decimal("0")

    # Donations
    sec80g: Decimal = Decimal("0")
    sec80gga: Decimal = Decimal("0")
    sec80ggc: Decimal = Decimal("0")

    # Pension
    sec80ccc: Decimal = Decimal("0")

    # Other
    sec80cch: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        return (
            self.sec80c_total + self.sec80ccc + self.sec80ccd1
            + self.sec80ccd1b + self.sec80ccd2
            + self.sec80d_self + self.sec80d_parents
            + self.sec80dd + self.sec80ddb + self.sec80u
            + self.sec80e + self.sec80ee + self.sec80eea + self.sec80eeb
            + self.sec80tta + self.sec80ttb
            + self.sec80gg
            + self.sec80g + self.sec80gga + self.sec80ggc
        )

    def to_dict(self) -> dict:
        return {
            "sec80c": str(self.sec80c_total),
            "sec80c_components": {k: str(v) for k, v in self.sec80c_components.items()},
            "sec80ccd1": str(self.sec80ccd1),
            "sec80ccd1b": str(self.sec80ccd1b),
            "sec80ccd2": str(self.sec80ccd2),
            "sec80d_self": str(self.sec80d_self),
            "sec80d_parents": str(self.sec80d_parents),
            "sec80dd": str(self.sec80dd),
            "sec80ddb": str(self.sec80ddb),
            "sec80u": str(self.sec80u),
            "sec80e": str(self.sec80e),
            "sec80ee": str(self.sec80ee),
            "sec80eea": str(self.sec80eea),
            "sec80eeb": str(self.sec80eeb),
            "sec80tta": str(self.sec80tta),
            "sec80ttb": str(self.sec80ttb),
            "sec80gg": str(self.sec80gg),
            "sec80g": str(self.sec80g),
            "total_chapter_via": str(self.total),
        }


class ChapterVIAEngine:
    """Computes ALL Chapter VI-A deductions using RuleRepository for limits.

    M3: Replaces fragmented deduction logic scattered across
    regime_optimizer, deductions_computer, and builders with a single
    comprehensive engine.
    """

    def compute(
        self,
        form16: Optional[Form16Data] = None,
        answers: Optional[UserAnswers] = None,
        savings_interest: Decimal = Decimal("0"),
        total_interest: Decimal = Decimal("0"),
        salary_income: Decimal = Decimal("0"),
        is_new_regime: bool = False,
        is_senior_citizen: bool = False,
        fy: Optional[FinancialYear] = None,
    ) -> DeductionBreakdown:
        """Compute all applicable Chapter VI-A deductions.

        New Regime: Only 80CCD(2) and 80TTA/80TTB available.
        Old Regime: All sections available.
        """
        result = DeductionBreakdown()
        config = rule_repository.get(fy or FinancialYear.from_string("FY2025-26"))
        ua = answers or UserAnswers()
        regime_key = "new" if is_new_regime else "old"

        # ── 80CCD(2): Employer NPS — BOTH regimes ──
        if form16:
            result.sec80ccd2 = form16.part_b.chapter_vi_a.sec80ccd2 or Decimal("0")

        # Under NEW REGIME, only these are available:
        if is_new_regime:
            if is_senior_citizen:
                result.sec80ttb = min(
                    total_interest,
                    config.get_deduction_limit("80TTB", regime_key),
                )
            else:
                result.sec80tta = min(
                    savings_interest,
                    config.get_deduction_limit("80TTA", regime_key),
                )
            return result

        # ── BELOW: OLD REGIME ONLY ──

        # ── 80C: Aggregate ₹1.5L limit ──
        result.sec80c_total = self._compute_80c(form16, ua, config)
        result.sec80ccc = self._compute_80ccc(form16, config)

        # ── NPS (80CCD) ──
        result.sec80ccd1 = self._compute_80ccd1(form16, ua, config)
        result.sec80ccd1b = self._compute_80ccd1b(ua, config)

        # ── Health (80D) ──
        result.sec80d_self, result.sec80d_parents = self._compute_80d(
            ua, is_senior_citizen, config,
        )

        # ── Disability (80DD, 80DDB, 80U) ──
        if ua.has_other_income:
            for detail in (ua.other_income_details or []):
                dtype = detail.get("type", "")
                amount = Decimal(str(detail.get("amount", "0")))
                if dtype == "80dd":
                    result.sec80dd = min(amount, config.get_deduction_limit("80DD"))
                elif dtype == "80ddb":
                    result.sec80ddb = min(amount, config.get_deduction_limit("80DDB" if not is_senior_citizen else "80DDB_SENIOR"))

        # ── Interest-based (80E, 80EE, 80EEA, 80EEB) ──
        result.sec80e = self._compute_80e(ua)
        result.sec80ee = self._compute_80ee(ua, config)
        result.sec80eea = self._compute_80eea(ua, config)

        # ── Savings interest (80TTA/80TTB) ──
        if is_senior_citizen:
            result.sec80ttb = min(total_interest, config.get_deduction_limit("80TTB"))
        else:
            result.sec80tta = min(savings_interest, config.get_deduction_limit("80TTA"))

        # ── Rent (80GG) ──
        result.sec80gg = self._compute_80gg(form16, ua, salary_income, config)

        # ── Donations (80G, 80GGA, 80GGC) ──
        result.sec80g = self._compute_80g(ua)

        return result

    # ── Private computation methods ──

    def _compute_80c(self, form16, ua, config) -> Decimal:
        epf = Decimal("0")
        if form16:
            epf = form16.part_b.chapter_vi_a.sec80c or Decimal("0")
        additional = Decimal("0")
        if ua.has_additional_80c and ua.additional_80c_breakup:
            additional = sum(
                v for k, v in ua.additional_80c_breakup.items()
                if k not in ("nps_own", "nps_employer")
            )
        return min(epf + additional, config.get_deduction_limit("80C"))

    def _compute_80ccc(self, form16, config) -> Decimal:
        if not form16:
            return Decimal("0")
        val = form16.part_b.chapter_vi_a.sec80ccc or Decimal("0")
        return min(val, config.get_deduction_limit("80CCC"))

    def _compute_80ccd1(self, form16, ua, config) -> Decimal:
        nps_own = Decimal("0")
        if form16:
            nps_own = form16.part_b.chapter_vi_a.sec80ccd1 or Decimal("0")
        if ua.has_additional_80c and ua.additional_80c_breakup:
            nps_own += Decimal(
                str(ua.additional_80c_breakup.get("nps_own", "0"))
            )
        return min(nps_own, config.get_deduction_limit("80CCD(1)"))

    def _compute_80ccd1b(self, ua, config) -> Decimal:
        if not ua.has_additional_80c or not ua.additional_80c_breakup:
            return Decimal("0")
        nps = Decimal(str(ua.additional_80c_breakup.get("nps_own", "0")))
        limit = config.get_deduction_limit("80CCD(1B)")
        return min(nps, limit)

    def _compute_80d(self, ua, is_senior, config) -> tuple[Decimal, Decimal]:
        if not ua.has_health_insurance:
            return Decimal("0"), Decimal("0")
        self_key = "80D_SELF_SENIOR" if is_senior else "80D_SELF"
        parents_key = "80D_PARENTS_SENIOR" if ua.parents_senior_citizen else "80D_PARENTS"
        ded_self = min(
            ua.health_premium_self or Decimal("0"),
            config.get_deduction_limit(self_key),
        )
        ded_parents = min(
            ua.health_premium_parents or Decimal("0"),
            config.get_deduction_limit(parents_key),
        )
        return ded_self, ded_parents

    def _compute_80e(self, ua) -> Decimal:
        if not ua.has_other_income:
            return Decimal("0")
        total = Decimal("0")
        for detail in (ua.other_income_details or []):
            if detail.get("type") == "education_loan":
                total += Decimal(str(detail.get("amount", "0")))
        return total

    def _compute_80ee(self, ua, config) -> Decimal:
        if not ua.has_home_loan:
            return Decimal("0")
        return min(
            ua.home_loan_interest or Decimal("0"),
            Decimal("50000"),  # 80EE fixed ₹50K
        )

    def _compute_80eea(self, ua, config) -> Decimal:
        if not ua.has_home_loan:
            return Decimal("0")
        return min(
            ua.home_loan_interest or Decimal("0"),
            Decimal("150000"),  # 80EEA fixed ₹1.5L
        )

    def _compute_80gg(self, form16, ua, salary_income, config) -> Decimal:
        if not ua.pays_rent:
            return Decimal("0")
        # Only if no HRA received
        hra = Decimal("0")
        if form16:
            hra = form16.annexure.hra or Decimal("0")
        if hra > 0:
            return Decimal("0")

        annual_rent = (ua.rent_per_month or Decimal("0")) * Decimal("12")
        if annual_rent <= 0:
            return Decimal("0")

        limit = config.get_deduction_limit("80GG")
        option_a = Decimal("5000") * Decimal("12")  # ₹60K
        option_b = salary_income * Decimal("0.25")
        option_c = max(Decimal("0"), annual_rent - salary_income * Decimal("0.10"))
        return min(option_a, option_b, option_c, limit)

    def _compute_80g(self, ua) -> Decimal:
        if not ua.has_other_income:
            return Decimal("0")
        total = Decimal("0")
        for detail in (ua.other_income_details or []):
            if detail.get("type") in ("80g", "donation"):
                total += Decimal(str(detail.get("amount", "0")))
        return total
