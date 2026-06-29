"""Regime Optimizer — Compares Old vs New tax regimes.

Computes tax under both regimes and recommends the winner.
Accounts for all deductions available under old regime and
the limited deductions under new regime (only 80CCD(2)).

FY 2025-26 (AY 2026-27) Slab Rates:
─────────────────────────────────────────────────────────
Old Regime (no 115BAC):
  Up to ₹2,50,000         Nil
  ₹2,50,001 - ₹5,00,000    5%
  ₹5,00,001 - ₹10,00,000  20%
  Above ₹10,00,000         30%
  + Cess @ 4%

New Regime (115BAC):
  Up to ₹4,00,000         Nil
  ₹4,00,001 - ₹8,00,000    5%
  ₹8,00,001 - ₹12,00,000  10%
  ₹12,00,001 - ₹16,00,000 15%
  ₹16,00,001 - ₹20,00,000 20%
  ₹20,00,001 - ₹24,00,000 25%
  Above ₹24,00,000         30%
  + Cess @ 4%
"""

from decimal import Decimal
from typing import Optional

from src.models.form16 import Form16Data, ChapterVIADeductions, Regime
from src.models.tax import UserAnswers, ClassifiedCGData, RegimeResult

# FY 2025-26 Standard Deduction
STD_DEDUCTION_OLD = Decimal("50000")
STD_DEDUCTION_NEW = Decimal("75000")

# Old Regime 80C limit
LIMIT_80C = Decimal("150000")
# Old Regime 80CCD(1B) additional NPS limit
LIMIT_80CCD1B = Decimal("50000")
# Old Regime 80D — Health Insurance
LIMIT_80D_SELF = Decimal("25000")
LIMIT_80D_SELF_SENIOR = Decimal("50000")
LIMIT_80D_PARENTS = Decimal("25000")
LIMIT_80D_PARENTS_SENIOR = Decimal("50000")
# Old Regime 80TTA — Savings Interest
LIMIT_80TTA = Decimal("10000")
# Old Regime 80GG — Rent (no HRA)
LIMIT_80GG = Decimal("60000")
# Old Regime 24(b) — Home Loan Interest (Self-Occupied)
LIMIT_24B_SELF = Decimal("200000")

# Rebate u/s 87A
REBATE_87A_OLD = Decimal("12500")  # Tax ≤ ₹5L
REBATE_87A_NEW_LIMIT = Decimal("25000")  # Taxable income ≤ ₹7L
REBATE_87A_NEW_MAX = Decimal("60000")  # Max rebate ₹60K under new regime
REBATE_THRESHOLD_OLD = Decimal("500000")
REBATE_THRESHOLD_NEW = Decimal("700000")


class RegimeOptimizer:
    """Computes and compares tax under Old and New regimes."""

    def optimize(
        self,
        form16: Form16Data,
        classified_cg: ClassifiedCGData,
        answers: UserAnswers,
        savings_interest: Decimal = Decimal("0"),
        other_interest: Decimal = Decimal("0"),
    ) -> RegimeResult:
        """Run full comparison and return the optimal regime choice."""
        old_result = self._compute_old_regime(
            form16, classified_cg, answers, savings_interest, other_interest,
        )
        new_result = self._compute_new_regime(
            form16, classified_cg, answers, savings_interest, other_interest,
        )

        old_tax = old_result["net_tax"]
        new_tax = new_result["net_tax"]

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

    def _compute_old_regime(
        self,
        form16: Form16Data,
        classified_cg: ClassifiedCGData,
        answers: UserAnswers,
        savings_interest: Decimal,
        other_interest: Decimal,
    ) -> dict:
        """Compute tax under the Old Regime."""
        # ---- INCOME ----
        salary = form16.part_b.salary_171
        perquisites = form16.part_b.perquisites_172
        total_gross_salary = salary + perquisites

        # Allowances exempt u/s 10
        exemptions = form16.part_b.exemptions_s10.total

        # Standard Deduction
        std_ded = STD_DEDUCTION_OLD

        # Professional Tax
        prof_tax = form16.part_b.professional_tax_16iii

        income_salary = total_gross_salary - exemptions - std_ded - prof_tax
        if income_salary < 0:
            income_salary = Decimal("0")

        # House Property (if home loan)
        home_loan_loss = Decimal("0")
        if answers.has_home_loan and answers.home_loan_self_occupied:
            home_loan_loss = min(answers.home_loan_interest, LIMIT_24B_SELF)

        # Capital Gains
        cg_summary = self._cg_tax_summary(classified_cg)
        total_cg_income = classified_cg.total_cg
        stcg_slab = cg_summary["stcg_slab_total"]  # This gets added to normal income

        # Other Sources (Interest)
        total_interest = savings_interest + other_interest

        # Gross Total Income
        gross_total = (
            income_salary
            + stcg_slab  # STCG slab rate added to regular income
            + total_interest
            - home_loan_loss
        )
        if gross_total < 0:
            gross_total = Decimal("0")

        # ---- DEDUCTIONS (Chapter VI-A) ----
        deductions = self._compute_old_deductions(form16, answers, total_interest)

        # Total Income (taxable at slab rates)
        total_income_slab = max(Decimal("0"), gross_total - deductions.total)

        # ---- TAX ON SLAB INCOME ----
        tax_slab = self._slab_tax_old(total_income_slab)

        # ---- ADD SPECIAL RATE CG TAX ----
        tax_112a = cg_summary["ltcg_112a_tax"]
        tax_stcg_15 = cg_summary["stcg_15pct_tax"]
        tax_ltcg_other = cg_summary["ltcg_other_tax"]

        total_tax_before_cess = tax_slab + tax_112a + tax_stcg_15 + tax_ltcg_other

        # ---- REBATE u/s 87A ----
        rebate = Decimal("0")
        total_income_all = total_income_slab + cg_summary["ltcg_112a_taxable"] + cg_summary["stcg_15pct_total"] + cg_summary["ltcg_other_total"]
        if total_income_all <= REBATE_THRESHOLD_OLD:
            rebate = min(total_tax_before_cess, REBATE_87A_OLD)

        # ---- CESS ----
        tax_after_rebate = max(Decimal("0"), total_tax_before_cess - rebate)
        cess = (tax_after_rebate * Decimal("4") / Decimal("100")).quantize(Decimal("1"))

        net_tax = tax_after_rebate + cess

        return {
            "income_salary": income_salary,
            "income_cg": total_cg_income,
            "income_interest": total_interest,
            "home_loan_loss": home_loan_loss,
            "gross_total": gross_total,
            "deductions_total": deductions.total,
            "total_income": total_income_slab + cg_summary["ltcg_112a_taxable"] + cg_summary["stcg_15pct_total"] + cg_summary["ltcg_other_total"],
            "tax_slab": tax_slab,
            "tax_special_rates": tax_112a + tax_stcg_15 + tax_ltcg_other,
            "rebate_87a": rebate,
            "cess": cess,
            "net_tax": net_tax,
        }

    def _compute_new_regime(
        self,
        form16: Form16Data,
        classified_cg: ClassifiedCGData,
        answers: UserAnswers,
        savings_interest: Decimal,
        other_interest: Decimal,
    ) -> dict:
        """Compute tax under the New Regime (115BAC)."""
        # ---- INCOME ----
        # Under new regime: no exemptions (HRA, LTA, etc.), standard ₹75K deduction
        salary = form16.part_b.salary_171
        perquisites = form16.part_b.perquisites_172
        total_gross_salary = salary + perquisites

        # Only Standard Deduction (₹75K) and Employer NPS (80CCD(2)) available
        std_ded = STD_DEDUCTION_NEW

        income_salary = total_gross_salary - std_ded
        if income_salary < 0:
            income_salary = Decimal("0")

        # Home loan loss: NOT deductible under new regime for self-occupied property
        home_loan_loss = Decimal("0")

        # Capital Gains
        cg_summary = self._cg_tax_summary(classified_cg)
        stcg_slab = cg_summary["stcg_slab_total"]

        # Other Sources
        total_interest = savings_interest + other_interest

        # Gross Total Income
        gross_total = income_salary + stcg_slab + total_interest - home_loan_loss
        if gross_total < 0:
            gross_total = Decimal("0")

        # ---- DEDUCTIONS ----
        # New regime: ONLY 80CCD(2) (Employer NPS) is available
        deductions_total = form16.part_b.chapter_vi_a.sec80ccd2

        total_income_slab = max(Decimal("0"), gross_total - deductions_total)

        # ---- TAX ON SLAB INCOME ----
        tax_slab = self._slab_tax_new(total_income_slab)

        # ---- ADD SPECIAL RATE CG TAX (same in both regimes) ----
        tax_112a = cg_summary["ltcg_112a_tax"]
        tax_stcg_15 = cg_summary["stcg_15pct_tax"]
        tax_ltcg_other = cg_summary["ltcg_other_tax"]

        total_tax_before_cess = tax_slab + tax_112a + tax_stcg_15 + tax_ltcg_other

        # ---- REBATE u/s 87A ----
        rebate = Decimal("0")
        total_income_all = total_income_slab + cg_summary["ltcg_112a_taxable"] + cg_summary["stcg_15pct_total"] + cg_summary["ltcg_other_total"]
        if total_income_all <= REBATE_THRESHOLD_NEW:
            rebate = min(total_tax_before_cess, REBATE_87A_NEW_MAX)

        # ---- CESS ----
        tax_after_rebate = max(Decimal("0"), total_tax_before_cess - rebate)
        cess = (tax_after_rebate * Decimal("4") / Decimal("100")).quantize(Decimal("1"))

        net_tax = tax_after_rebate + cess

        return {
            "income_salary": income_salary,
            "income_cg": classified_cg.total_cg,
            "income_interest": total_interest,
            "gross_total": gross_total,
            "deductions_total": deductions_total,
            "total_income": total_income_slab + cg_summary["ltcg_112a_taxable"] + cg_summary["stcg_15pct_total"] + cg_summary["ltcg_other_total"],
            "tax_slab": tax_slab,
            "tax_special_rates": tax_112a + tax_stcg_15 + tax_ltcg_other,
            "rebate_87a": rebate,
            "cess": cess,
            "net_tax": net_tax,
        }

    def _compute_old_deductions(
        self,
        form16: Form16Data,
        answers: UserAnswers,
        total_interest: Decimal,
    ) -> ChapterVIADeductions:
        """Compute Chapter VI-A deductions under Old Regime."""
        d = ChapterVIADeductions()

        # 80C: EPF from Form 16 + user's additional 80C investments
        epf_from_form16 = form16.part_b.chapter_vi_a.sec80c
        additional_80c = Decimal("0")
        if answers.has_additional_80c and answers.additional_80c_breakup:
            additional_80c = sum(answers.additional_80c_breakup.values())
        d.sec80c = min(epf_from_form16 + additional_80c, LIMIT_80C)

        # 80CCD(1B): Additional NPS (user's own NPS beyond employer)
        if answers.has_additional_80c and "nps_own" in answers.additional_80c_breakup:
            d.sec80ccd1b = min(
                answers.additional_80c_breakup["nps_own"], LIMIT_80CCD1B
            )

        # 80CCD(2): Employer NPS (available in BOTH regimes)
        d.sec80ccd2 = form16.part_b.chapter_vi_a.sec80ccd2

        # 80D: Health Insurance
        if answers.has_health_insurance:
            d.sec80d = self._compute_80d(answers)

        # 80TTA: Savings Bank Interest
        d.sec80tta = min(total_interest, LIMIT_80TTA)

        # 80GG: Rent paid (if no HRA received)
        if answers.pays_rent and form16.annexure.hra == 0:
            d.sec80gg = self._compute_80gg(answers)

        # 80E: Education Loan Interest
        if answers.has_other_income:
            for detail in answers.other_income_details:
                if detail.get("type") == "education_loan":
                    d.sec80e += Decimal(str(detail.get("amount", "0")))

        return d

    def _compute_80d(self, answers: UserAnswers) -> Decimal:
        """Compute 80D deduction for health insurance."""
        total = Decimal("0")

        # Self + spouse + children
        limit_self = LIMIT_80D_SELF  # ₹25,000
        total += min(answers.health_premium_self, limit_self)

        # Parents
        if answers.parents_senior_citizen:
            limit_parents = LIMIT_80D_PARENTS_SENIOR  # ₹50,000
        else:
            limit_parents = LIMIT_80D_PARENTS  # ₹25,000
        total += min(answers.health_premium_parents, limit_parents)

        return total

    def _compute_80gg(self, answers: UserAnswers) -> Decimal:
        """Compute 80GG deduction for rent paid (no HRA)."""
        annual_rent = answers.rent_per_month * Decimal("12")
        # Least of: (a) ₹5,000/month, (b) 25% of total income, (c) rent - 10% of total income
        # Simplified: cap at ₹60,000
        return min(annual_rent, LIMIT_80GG)

    @staticmethod
    def _slab_tax_old(income: Decimal) -> Decimal:
        """Old regime slab tax."""
        tax = Decimal("0")
        remaining = income

        if remaining > Decimal("1000000"):
            tax += (remaining - Decimal("1000000")) * Decimal("0.30")
            remaining = Decimal("1000000")
        if remaining > Decimal("500000"):
            tax += (remaining - Decimal("500000")) * Decimal("0.20")
            remaining = Decimal("500000")
        if remaining > Decimal("250000"):
            tax += (remaining - Decimal("250000")) * Decimal("0.05")

        return tax.quantize(Decimal("1"))

    @staticmethod
    def _slab_tax_new(income: Decimal) -> Decimal:
        """New regime (115BAC) slab tax for FY 2025-26."""
        tax = Decimal("0")
        remaining = income

        if remaining > Decimal("2400000"):
            tax += (remaining - Decimal("2400000")) * Decimal("0.30")
            remaining = Decimal("2400000")
        if remaining > Decimal("2000000"):
            tax += (remaining - Decimal("2000000")) * Decimal("0.25")
            remaining = Decimal("2000000")
        if remaining > Decimal("1600000"):
            tax += (remaining - Decimal("1600000")) * Decimal("0.20")
            remaining = Decimal("1600000")
        if remaining > Decimal("1200000"):
            tax += (remaining - Decimal("1200000")) * Decimal("0.15")
            remaining = Decimal("1200000")
        if remaining > Decimal("800000"):
            tax += (remaining - Decimal("800000")) * Decimal("0.10")
            remaining = Decimal("800000")
        if remaining > Decimal("400000"):
            tax += (remaining - Decimal("400000")) * Decimal("0.05")

        return tax.quantize(Decimal("1"))

    def _cg_tax_summary(self, classified_cg: ClassifiedCGData) -> dict:
        """Get capital gains tax summary from classified data."""
        from src.engine.classifier import ClassificationEngine
        engine = ClassificationEngine()
        return engine.get_tax_summary(classified_cg)


def optimize_regime(
    form16: Form16Data,
    classified_cg: ClassifiedCGData,
    answers: UserAnswers,
    savings_interest: Decimal = Decimal("0"),
    other_interest: Decimal = Decimal("0"),
) -> RegimeResult:
    """Convenience function for regime optimization."""
    optimizer = RegimeOptimizer()
    return optimizer.optimize(
        form16, classified_cg, answers, savings_interest, other_interest,
    )
