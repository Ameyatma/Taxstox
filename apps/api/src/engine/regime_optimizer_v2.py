"""Regime Optimizer v2 — ITD Portal-Matched Tax Computation Engine.

Computes tax under Old and New regimes with EXACT portal matching logic.
M1: Refactored to use RuleRepository — no hardcoded FY constants.

Traceability:
  C12.1 (Finance Act Versioning), C12.3 (Rule Repository), C12.4 (Rule Evaluation),
  ARC-001 (Rules hardcoded → extracted), ARC-002 (Single FY → multi-FY),
  ARC-005 (Dual optimizers → v2 canonical), ARC-007 (Slab duplication → unified),
  R01 (FY2026 obsolescence → multi-year support)
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from src.engine.classifier import ClassificationEngine
from src.engine.deductions_computer import DeductionsComputer
from src.engine.rules.config import rule_repository, TaxYearConfig
from src.engine.rules.evaluator import RuleEvaluator
from src.engine.salary_computer import SalaryComputer
from src.models.financial_year import FinancialYear
from src.models.form16 import Form16Data, Regime
from src.models.tax import ClassifiedCGData, RegimeResult, UserAnswers


class RegimeOptimizerV2:
    """Computes and compares tax under Old and New regimes using ITD portal logic.

    M1: Uses RuleRepository for all FY-specific constants. No hardcoded rates.
    """

    def __init__(self) -> None:
        self.salary_computer = SalaryComputer()
        self.deductions_computer = DeductionsComputer()
        self._evaluator = RuleEvaluator()

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
        financial_year: Optional[FinancialYear] = None,
    ) -> RegimeResult:
        """Run full comparison and return the optimal regime.

        Args:
            financial_year: FY for tax computation. Defaults to FY2025-26
                           for backward compatibility with existing callers.
        """
        fy = financial_year or FinancialYear.from_string("FY2025-26")
        config = rule_repository.get(fy)

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
            config=config,
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
            config=config,
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
        config: TaxYearConfig,
    ) -> dict:
        """Compute complete tax for one regime, matching ITD portal step-by-step.

        M1: All FY-specific values come from TaxYearConfig via RuleRepository.
        No hardcoded constants.
        """
        ua = answers or UserAnswers()
        cg = classified_cg or ClassifiedCGData()
        regime_config = config.new_regime if is_new_regime else config.old_regime
        regime_key = "new" if is_new_regime else "old"

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
            home_loan_limit = config.get_deduction_limit("24B_SELF", regime_key)
            home_loan_loss = min(ua.home_loan_interest or Decimal("0"), home_loan_limit)

        # ── Step 6: Capital Gains ──
        cg_summary = self._cg_summary(cg)

        # ── Step 7: Other Sources ──
        total_interest = savings_interest + other_interest

        # ── Step 8: Gross Total Income ──
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

        # ── Step 11-14: Tax using RuleEvaluator (M1) ──
        slab_taxable = max(Decimal("0"), slab_income - deductions.total)
        slab_tax = self._evaluator.compute_slab_tax(slab_taxable, regime_config.slabs)

        # ── Step 12: Tax on Special Rate Income ──
        tax_112a = cg_summary["ltcg_112a_tax"]
        tax_stcg_15 = cg_summary["stcg_15pct_tax"]
        tax_ltcg_other = cg_summary["ltcg_other_tax"]
        special_rate_tax = tax_112a + tax_stcg_15 + tax_ltcg_other

        # ── Step 13: Tax Before Rebate ──
        tax_before_rebate = slab_tax + special_rate_tax

        # ── Step 14: Rebate u/s 87A (M1: from TaxYearConfig) ──
        rebate = self._evaluator.compute_rebate(
            tax_before_rebate, total_income, regime_config,
        )

        tax_after_rebate = max(Decimal("0"), tax_before_rebate - rebate)

        # ── Step 15: Surcharge (M1: from TaxYearConfig) ──
        surcharge = self._evaluator.compute_surcharge(
            total_income, tax_after_rebate, config,
        )

        # ── Step 16: HEC (M1: from TaxYearConfig) ──
        cess = self._evaluator.compute_cess(tax_after_rebate, surcharge, config.cess_rate)

        # ── Step 17: Final Tax (M1: RuleEvaluator rounding) ──
        net_tax = self._evaluator.round_final_tax(tax_after_rebate + surcharge + cess)

        return {
            "gross_salary": str(salary.gross_salary),
            "hra_exemption": str(salary.hra_exemption),
            "lta_exemption": str(salary.lta_exemption),
            "total_exemptions_s10": str(salary.total_exemptions),
            "std_deduction": str(salary.std_deduction),
            "professional_tax": str(salary.professional_tax),
            "income_salary": str(salary.income_from_salary),
            "home_loan_loss": str(home_loan_loss),
            "income_cg": str(cg.total_cg),
            "cg_ltcg_112a": str(cg_summary["ltcg_112a_total"]),
            "cg_stcg_15pct": str(cg_summary["stcg_15pct_total"]),
            "cg_ltcg_other": str(cg_summary["ltcg_other_total"]),
            "cg_stcg_slab": str(cg_summary["stcg_slab_total"]),
            "income_interest": str(total_interest),
            "savings_interest": str(savings_interest),
            "other_interest": str(other_interest),
            "slab_income": str(slab_income),
            "special_rate_income": str(special_rate_income),
            "gross_total": str(gross_total),
            "deductions_total": str(deductions.total),
            "deductions_detail": deductions.to_dict(),
            "total_income": str(total_income),
            "tax_slab": str(slab_tax),
            "tax_112a": str(tax_112a),
            "tax_stcg_15pct": str(tax_stcg_15),
            "tax_ltcg_other": str(tax_ltcg_other),
            "tax_before_rebate": str(tax_before_rebate),
            "rebate_87a": str(rebate),
            "surcharge": str(surcharge),
            "cess": str(cess),
            "net_tax": str(net_tax),
            "regime": regime_key,
            "financial_year": config.financial_year.label,
        }

    def _cg_summary(self, classified_cg: ClassifiedCGData) -> dict:
        """Compute capital gains tax summary from classified data.

        M1: Module-level import — no circular dependency exists
        (classifier does not import optimizer).
        """
        engine = ClassificationEngine()
        try:
            summary = engine.get_tax_summary(classified_cg)
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
