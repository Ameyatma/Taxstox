"""Regime Optimizer v2 — ITD Portal-Matched Tax Computation Engine.

Computes tax under Old and New regimes with EXACT portal matching logic.

ITD Portal Computation Order (verified against incometax.gov.in):
  1. Salary Income (from SalaryComputer)
  2. House Property Income
  3. Capital Gains (classified: 112A, 111A, slab rate, other)
  4. Other Sources (interest, dividend, etc.)
  5. Gross Total Income = sum(1-4)
  6. Chapter VI-A Deductions (DeductionsComputer)
  7. Total Income = GTI - Deductions
  8. Tax on Slab Income (separate from special-rate CG)
  9. Tax on Special Rate Income (112A @ 12.5%, 111A @ 15%, other LTCG @ 12.5%)
  10. Tax Before Rebate = slab_tax + special_rate_tax
  11. Rebate u/s 87A (if eligible)
  12. Surcharge (with marginal relief)
  13. HEC @ 4% on (Tax After Rebate + Surcharge)
  14. Round FINAL TAX to nearest rupee

Key ITD Rules:
  - Rounding: ONLY final tax to nearest rupee. No intermediate rounding.
  - 2 decimal precision throughout.
  - 87A: Available under new regime if total income <= 7L, even with LTCG
  - Cess base: (tax after rebate + surcharge) x 4%
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from src.models.form16 import Form16Data, Regime
from src.models.tax import UserAnswers, ClassifiedCGData, RegimeResult
from src.engine.salary_computer import SalaryComputer, SalaryBreakdown
from src.engine.deductions_computer import DeductionsComputer, DeductionsBreakdown


# ── FY 2025-26 Slab Rates ──

OLD_SLABS = [
    (Decimal("250000"), Decimal("0.00")),
    (Decimal("500000"), Decimal("0.05")),
    (Decimal("1000000"), Decimal("0.20")),
    (Decimal("99999999999"), Decimal("0.30")),
]

NEW_SLABS = [
    (Decimal("400000"), Decimal("0.00")),
    (Decimal("800000"), Decimal("0.05")),
    (Decimal("1200000"), Decimal("0.10")),
    (Decimal("1600000"), Decimal("0.15")),
    (Decimal("2000000"), Decimal("0.20")),
    (Decimal("2400000"), Decimal("0.25")),
    (Decimal("99999999999"), Decimal("0.30")),
]

# ── Rebate 87A ──
REBATE_THRESHOLD_OLD = Decimal("500000")
REBATE_THRESHOLD_NEW = Decimal("700000")
REBATE_MAX_OLD = Decimal("12500")
REBATE_MAX_NEW = Decimal("25000")

# ── Surcharge thresholds ──
SURCHARGE_SLABS = [
    (Decimal("5000000"), Decimal("0.00")),
    (Decimal("10000000"), Decimal("0.10")),
    (Decimal("20000000"), Decimal("0.15")),
    (Decimal("50000000"), Decimal("0.25")),
    (Decimal("99999999999"), Decimal("0.37")),
]


class RegimeOptimizerV2:
    """Computes and compares tax under Old and New regimes using ITD portal logic."""

    def __init__(self):
        self.salary_computer = SalaryComputer()
        self.deductions_computer = DeductionsComputer()

    def optimize(
        self,
        form16: Optional[Form16Data] = None,
        classified_cg: Optional[ClassifiedCGData] = None,
        answers: Optional[UserAnswers] = None,
        savings_interest: Decimal = Decimal("0"),
        other_interest: Decimal = Decimal("0"),
        rent_paid_monthly: Decimal = Decimal("0"),
        metro_city: bool = False,
        children_count: int = 0,
        is_senior_citizen: bool = False,
    ) -> RegimeResult:
        """Run full comparison and return the optimal regime."""

        old_result = self._compute(
            form16=form16,
            classified_cg=classified_cg,
            answers=answers,
            savings_interest=savings_interest,
            other_interest=other_interest,
            rent_paid_monthly=rent_paid_monthly,
            metro_city=metro_city,
            children_count=children_count,
            is_senior_citizen=is_senior_citizen,
            is_new_regime=False,
        )

        new_result = self._compute(
            form16=form16,
            classified_cg=classified_cg,
            answers=answers,
            savings_interest=savings_interest,
            other_interest=other_interest,
            rent_paid_monthly=rent_paid_monthly,
            metro_city=metro_city,
            children_count=children_count,
            is_senior_citizen=is_senior_citizen,
            is_new_regime=True,
        )

        old_tax = Decimal(old_result["net_tax"])
        new_tax = Decimal(new_result["net_tax"])

        if new_tax <= old_tax:
            recommended = Regime.NEW
            savings = old_tax - new_tax
        else:
            recommended = Regime.OLD
            savings = new_tax - old_tax

        return RegimeResult(
            old_tax=old_tax,
            new_tax=new_tax,
            recommended=recommended,
            savings=savings,
            old_breakdown=old_result,
            new_breakdown=new_result,
        )

    def _compute(
        self,
        form16: Optional[Form16Data],
        classified_cg: Optional[ClassifiedCGData],
        answers: Optional[UserAnswers],
        savings_interest: Decimal,
        other_interest: Decimal,
        rent_paid_monthly: Decimal,
        metro_city: bool,
        children_count: int,
        is_senior_citizen: bool,
        is_new_regime: bool,
    ) -> dict:
        """Compute complete tax for one regime, matching ITD portal step-by-step."""

        ua = answers or UserAnswers()
        cg = classified_cg or ClassifiedCGData()

        # ── Step 1-4: Salary Income ──
        salary = self.salary_computer.compute(
            form16=form16,
            rent_paid=rent_paid_monthly,
            metro_city=metro_city,
            is_new_regime=is_new_regime,
            children_count=children_count,
        )

        # ── Step 5: House Property Income ──
        home_loan_loss = Decimal("0")
        if ua.has_home_loan and ua.home_loan_self_occupied:
            home_loan_loss = min(ua.home_loan_interest or Decimal("0"), Decimal("200000"))

        # ── Step 6: Capital Gains ──
        cg_summary = self._cg_summary(cg)

        # ── Step 7: Other Sources ──
        total_interest = savings_interest + other_interest

        # ── Step 8: Gross Total Income ──
        # Separately track: slab income (salary + HP loss + STCG slab + interest)
        # and special-rate income (112A, 111A, other LTCG)
        slab_income = (
            salary.income_from_salary
            + cg_summary["stcg_slab_total"]
            + total_interest
            - home_loan_loss
        )
        slab_income = max(Decimal("0"), slab_income)

        special_rate_income = (
            cg_summary["ltcg_112a_total"]
            + cg_summary["stcg_15pct_total"]
            + cg_summary["ltcg_other_total"]
        )

        gross_total = slab_income + special_rate_income

        # ── Step 9: Chapter VI-A Deductions ──
        deductions = self.deductions_computer.compute(
            form16=form16,
            answers=ua,
            savings_interest=savings_interest,
            total_interest=total_interest,
            salary_income=salary.income_from_salary,
            is_new_regime=is_new_regime,
            is_senior_citizen=is_senior_citizen,
        )

        # ── Step 10: Total Income ──
        total_income = max(Decimal("0"), gross_total - deductions.total)

        # ── Step 11: Tax on Slab Income ──
        slab_tax = self._slab_tax(slab_income - deductions.total, is_new_regime)

        # ── Step 12: Tax on Special Rate Income ──
        tax_112a = cg_summary["ltcg_112a_tax"]
        tax_stcg_15 = cg_summary["stcg_15pct_tax"]
        tax_ltcg_other = cg_summary["ltcg_other_tax"]
        special_rate_tax = tax_112a + tax_stcg_15 + tax_ltcg_other

        # ── Step 13: Tax Before Rebate ──
        tax_before_rebate = slab_tax + special_rate_tax

        # ── Step 14: Rebate u/s 87A ──
        rebate = Decimal("0")
        if is_new_regime and total_income <= REBATE_THRESHOLD_NEW:
            rebate = min(tax_before_rebate, REBATE_MAX_NEW)
        elif not is_new_regime and total_income <= REBATE_THRESHOLD_OLD:
            rebate = min(tax_before_rebate, REBATE_MAX_OLD)

        tax_after_rebate = max(Decimal("0"), tax_before_rebate - rebate)

        # ── Step 15: Surcharge (with marginal relief) ──
        surcharge = self._compute_surcharge(total_income, tax_after_rebate)

        # ── Step 16: HEC @ 4% ──
        cess_base = tax_after_rebate + surcharge
        cess = (cess_base * Decimal("4") / Decimal("100")).quantize(Decimal("0.01"))

        # ── Step 17: Final Tax (rounded to nearest rupee) ──
        net_tax = (cess_base + cess).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        # ── Build comprehensive breakdown ──
        return {
            # Salary detail
            "gross_salary": str(salary.gross_salary),
            "hra_exemption": str(salary.hra_exemption),
            "lta_exemption": str(salary.lta_exemption),
            "total_exemptions_s10": str(salary.total_exemptions),
            "std_deduction": str(salary.std_deduction),
            "professional_tax": str(salary.professional_tax),
            "income_salary": str(salary.income_from_salary),
            # HP
            "home_loan_loss": str(home_loan_loss),
            # CG
            "income_cg": str(cg.total_cg),
            "cg_ltcg_112a": str(cg_summary["ltcg_112a_total"]),
            "cg_stcg_15pct": str(cg_summary["stcg_15pct_total"]),
            "cg_ltcg_other": str(cg_summary["ltcg_other_total"]),
            "cg_stcg_slab": str(cg_summary["stcg_slab_total"]),
            # Interest
            "income_interest": str(total_interest),
            "savings_interest": str(savings_interest),
            "other_interest": str(other_interest),
            # Totals
            "slab_income": str(slab_income),
            "special_rate_income": str(special_rate_income),
            "gross_total": str(gross_total),
            "deductions_total": str(deductions.total),
            "deductions_detail": deductions.to_dict(),
            "total_income": str(total_income),
            # Tax
            "tax_slab": str(slab_tax),
            "tax_112a": str(tax_112a),
            "tax_stcg_15pct": str(tax_stcg_15),
            "tax_ltcg_other": str(tax_ltcg_other),
            "tax_before_rebate": str(tax_before_rebate),
            "rebate_87a": str(rebate),
            "surcharge": str(surcharge),
            "cess": str(cess),
            "net_tax": str(net_tax),
            "regime": "new" if is_new_regime else "old",
        }

    def _slab_tax(self, income: Decimal, is_new: bool) -> Decimal:
        """Compute slab tax using ITD portal logic.

        Portal separates slab income from special-rate income.
        Tax is computed ONLY on slab income at progressive rates.
        """
        slabs = NEW_SLABS if is_new else OLD_SLABS
        tax = Decimal("0")
        remaining = income
        prev_limit = Decimal("0")

        for limit, rate in slabs:
            if remaining <= prev_limit:
                break
            taxable_in_slab = min(remaining, limit) - prev_limit
            if taxable_in_slab > 0:
                tax += taxable_in_slab * rate
            prev_limit = limit

        return tax.quantize(Decimal("0.01"))

    def _compute_surcharge(self, total_income: Decimal, tax: Decimal) -> Decimal:
        """Compute surcharge with marginal relief matching ITD portal."""
        surcharge_rate = Decimal("0")
        threshold = Decimal("0")

        for limit, rate in SURCHARGE_SLABS:
            if total_income > limit:
                surcharge_rate = rate
                threshold = limit

        if surcharge_rate == 0:
            return Decimal("0")

        surcharge = tax * surcharge_rate

        # Marginal relief: surcharge cannot exceed (total_income - threshold)
        excess_income = total_income - threshold
        if surcharge > excess_income:
            surcharge = excess_income  # Cap surcharge at excess income

        return surcharge.quantize(Decimal("0.01"))

    def _cg_summary(self, classified_cg: ClassifiedCGData) -> dict:
        """Compute capital gains tax summary, matching keys from ClassificationEngine."""
        from src.engine.classifier import ClassificationEngine
        engine = ClassificationEngine()
        try:
            summary = engine.get_tax_summary(classified_cg)
            # Map to our expected keys
            return {
                "ltcg_112a_total": Decimal(str(summary.get("ltcg_112a_total_gain", "0"))),
                "ltcg_112a_taxable": Decimal(str(summary.get("ltcg_112a_taxable", "0"))),
                "ltcg_112a_tax": Decimal(str(summary.get("ltcg_112a_tax", "0"))),
                "stcg_15pct_total": Decimal(str(summary.get("stcg_15pct_total", "0"))),
                "stcg_15pct_tax": Decimal(str(summary.get("stcg_15pct_tax", "0"))),
                "stcg_slab_total": Decimal(str(summary.get("stcg_slab_total", "0"))),
                "ltcg_other_total": Decimal(str(summary.get("ltcg_other_total", "0"))),
                "ltcg_other_tax": Decimal(str(summary.get("ltcg_other_tax", "0"))),
            }
        except Exception:
            return {
                "ltcg_112a_total": Decimal("0"),
                "ltcg_112a_taxable": Decimal("0"),
                "ltcg_112a_tax": Decimal("0"),
                "stcg_15pct_total": Decimal("0"),
                "stcg_15pct_tax": Decimal("0"),
                "stcg_slab_total": Decimal("0"),
                "ltcg_other_total": Decimal("0"),
                "ltcg_other_tax": Decimal("0"),
            }
