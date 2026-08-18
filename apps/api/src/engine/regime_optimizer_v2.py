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
        audit_context=None,  # PR2: Optional AuditContext for audit trail
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
            audit_context=audit_context,
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
            audit_context=audit_context,
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
        audit_context=None,  # PR2: Optional AuditContext for audit trail
    ) -> dict:
        """Compute complete tax for one regime, matching ITD portal step-by-step.

        M1: All FY-specific values come from TaxYearConfig via RuleRepository.
        PR2: Emits AuditEvent at each major computation step when audit_context provided.
        """
        ua = answers or UserAnswers()
        cg = classified_cg or ClassifiedCGData()
        regime_config = config.new_regime if is_new_regime else config.old_regime
        regime_key = "new" if is_new_regime else "old"
        fy_label = config.financial_year.label

        # PR2: Import audit types for event emission
        from src.engine.audit import AuditEventType as AET

        def _audit(event_type, desc, input_data=None, output_data=None, rule_ref=""):
            """Emit audit event if context is available. PR2."""
            if audit_context:
                return audit_context.event(
                    event_type, "tax_computation", "C6.1",
                    desc, input_data=input_data, output_data=output_data,
                    rule_reference=rule_ref,
                )

        _audit(AET.INCOME_COMPUTED, f"Computing salary income ({regime_key} regime)",
               output_data={"income_head": "salary"}, rule_ref="salary_171")

        # ── Step 1-4: Salary Income ──
        salary = self.salary_computer.compute(
            form16=form16,
            rent_paid=rent_paid_monthly,
            metro_city=metro_city,
            is_new_regime=is_new_regime,
            children_count=children_count,
            financial_year=config.financial_year,
        )
        _audit(AET.INCOME_COMPUTED, f"Salary income: ₹{salary.income_from_salary:,.0f}",
               output_data={"income": str(salary.income_from_salary), "income_head": "salary",
                           "hra_exemption": str(salary.hra_exemption)},
               rule_ref="sec_171")

        # ── Step 5: House Property Income ──
        home_loan_loss = Decimal("0")
        if ua.has_home_loan and ua.home_loan_self_occupied:
            home_loan_limit = config.get_deduction_limit("24B_SELF", regime_key)
            home_loan_loss = min(ua.home_loan_interest or Decimal("0"), home_loan_limit)
        _audit(AET.INCOME_COMPUTED, f"House property loss: ₹{home_loan_loss:,.0f}",
               output_data={"income": str(-home_loan_loss), "income_head": "house_property"},
               rule_ref="sec_24b")

        # ── Step 6: Capital Gains ──
        cg_summary = self._cg_summary(cg, financial_year=config.financial_year)
        _audit(AET.INCOME_COMPUTED, f"Capital gains: ₹{cg.total_cg:,.0f}",
               output_data={"income": str(cg.total_cg), "income_head": "capital_gains"},
               rule_ref="sec_112a")

        # ── Step 7: Other Sources ──
        total_interest = savings_interest + other_interest
        _audit(AET.INCOME_COMPUTED, f"Other sources: ₹{total_interest:,.0f}",
               output_data={"income": str(total_interest), "income_head": "other_sources"},
               rule_ref="sec_56")

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
            financial_year=config.financial_year,
        )
        _audit(AET.DEDUCTION_APPLIED, f"Deductions: ₹{deductions.total:,.0f}",
               output_data={"section": "VI-A", "amount": str(deductions.total)},
               rule_ref="chapter_vi_a")

        # ── Step 10: Total Income ──
        total_income = max(Decimal("0"), gross_total - deductions.total)

        # ── Step 11: Slab Tax ──
        slab_taxable = max(Decimal("0"), slab_income - deductions.total)
        slab_tax = self._evaluator.compute_slab_tax(slab_taxable, regime_config.slabs)
        _audit(AET.SLAB_APPLIED, f"Slab tax on ₹{slab_taxable:,.0f}: ₹{slab_tax:,.0f}",
               input_data={"taxable_income": str(slab_taxable)},
               output_data={"slab_tax": str(slab_tax)},
               rule_ref="sec_115bac" if is_new_regime else "slab_old")

        # ── Step 12: Tax on Special Rate Income ──
        tax_112a = cg_summary["ltcg_112a_tax"]
        tax_stcg_15 = cg_summary["stcg_15pct_tax"]
        tax_ltcg_other = cg_summary["ltcg_other_tax"]
        special_rate_tax = tax_112a + tax_stcg_15 + tax_ltcg_other

        # ── Step 13: Tax Before Rebate ──
        tax_before_rebate = slab_tax + special_rate_tax

        # ── Step 14: Rebate u/s 87A ──
        rebate = self._evaluator.compute_rebate(
            tax_before_rebate, total_income, regime_config,
        )
        _audit(AET.REBATE_APPLIED, f"87A rebate: ₹{rebate:,.0f}",
               input_data={"tax_before_rebate": str(tax_before_rebate), "total_income": str(total_income)},
               output_data={"rebate": str(rebate)},
               rule_ref="sec_87a")

        tax_after_rebate = max(Decimal("0"), tax_before_rebate - rebate)

        # ── Step 15: Surcharge ──
        surcharge = self._evaluator.compute_surcharge(
            total_income, tax_after_rebate, config,
        )
        _audit(AET.SURCHARGE_APPLIED, f"Surcharge: ₹{surcharge:,.0f}",
               output_data={"surcharge": str(surcharge)},
               rule_ref="surcharge")

        # ── Step 16: HEC ──
        cess = self._evaluator.compute_cess(tax_after_rebate, surcharge, config.cess_rate)
        _audit(AET.CESS_APPLIED, f"HEC: ₹{cess:,.0f}",
               output_data={"cess": str(cess)},
               rule_ref="cess")

        # ── Step 17: Final Tax ──
        net_tax = self._evaluator.round_final_tax(tax_after_rebate + surcharge + cess)
        _audit(AET.TAX_FINALIZED, f"Final tax: ₹{net_tax:,.0f}",
               output_data={"net_tax": str(net_tax)},
               rule_ref="sec_288b")

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

    def _cg_summary(
        self,
        classified_cg: ClassifiedCGData,
        financial_year: Optional[FinancialYear] = None,
    ) -> dict:
        """Compute capital gains tax summary from classified data.

        M1: Module-level import — no circular dependency exists
        (classifier does not import optimizer).
        PR3: Propagate financial_year so CG rates come from RuleRepository.
        """
        engine = ClassificationEngine()
        try:
            summary = engine.get_tax_summary(classified_cg, financial_year=financial_year)
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
