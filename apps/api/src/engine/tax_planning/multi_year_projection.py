"""Multi-Year Projection Engine — Projects tax liability across future years.

Uses RuleEvaluator with assumed income growth, deduction changes,
and regime shifts.

Traceability: C19.3 (Multi-Year Projection — 0%→30%, P6)
"""

from __future__ import annotations

from decimal import Decimal

from src.domain.tax_planning.projection import (
    MultiYearProjection,
    YearProjection,
    ProjectionAssumption,
)
from src.engine.rules.evaluator import RuleEvaluator
from src.engine.rules.config import rule_repository
from src.models.financial_year import FinancialYear


class MultiYearProjectionEngine:
    """Projects tax liability across multiple financial years.

    Engine. Uses current RuleEvaluator with growth assumptions.
    Future FY rules are assumed similar to current unless overridden.
    """

    def __init__(self) -> None:
        self._evaluator = RuleEvaluator()

    def project(
        self,
        current_income: Decimal,
        current_deductions: Decimal,
        start_year: str = "FY2025-26",
        num_years: int = 5,
        income_growth_rate: Decimal = Decimal("0.10"),
        deductions_growth_rate: Decimal = Decimal("0.05"),
        regime: str = "new",
    ) -> MultiYearProjection:
        """Generate a multi-year tax projection.

        Args:
            current_income: Current total income
            current_deductions: Current total deductions
            start_year: Starting FY
            num_years: Number of years to project
            income_growth_rate: Annual income growth (0.10 = 10%)
            deductions_growth_rate: Annual deduction growth
            regime: Starting regime

        Returns:
            MultiYearProjection with year-by-year breakdown
        """
        projection = MultiYearProjection.create(start_year, num_years)
        projection.current_regime = regime
        projection.add_assumption("income_growth_rate", "Annual Income Growth",
                                  income_growth_rate * 100, "%")
        projection.add_assumption("deductions_growth_rate", "Annual Deduction Growth",
                                  deductions_growth_rate * 100, "%")

        income = current_income
        deductions = current_deductions
        current_fy = FinancialYear.from_string(start_year)

        for i in range(num_years):
            fy_label = _advance_fy(start_year, i)

            try:
                config = rule_repository.get(FinancialYear.from_string(fy_label))
            except KeyError:
                # Use current FY rules for future years
                config = rule_repository.get(current_fy)

            regime_config = config.get_regime(regime)
            taxable = max(Decimal("0"), income - deductions)

            # Compute tax
            tax = self._evaluator.compute_slab_tax(taxable, regime_config.slabs)
            rebate = self._evaluator.compute_rebate(tax, taxable, regime_config)
            tax_after_rebate = tax - rebate
            surcharge = self._evaluator.compute_surcharge(taxable, tax_after_rebate, config)
            cess = self._evaluator.compute_cess(tax_after_rebate, surcharge, config.cess_rate)
            final_tax = self._evaluator.round_final_tax(tax_after_rebate + surcharge + cess)

            effective_rate = (
                (final_tax / taxable * Decimal("100")).quantize(Decimal("0.1"))
                if taxable > 0 else Decimal("0")
            )

            projection.add_year(YearProjection(
                financial_year=fy_label,
                projected_income=income.quantize(Decimal("0.01")),
                projected_deductions=deductions.quantize(Decimal("0.01")),
                projected_tax=final_tax,
                projected_effective_rate=effective_rate,
                regime=regime,
            ))

            # Grow for next year
            income = (income * (Decimal("1") + income_growth_rate)).quantize(Decimal("0.01"))
            deductions = (deductions * (Decimal("1") + deductions_growth_rate)).quantize(Decimal("0.01"))

        return projection


def _advance_fy(fy: str, offset: int) -> str:
    """Increment a financial year string by offset years."""
    try:
        parts = fy.replace("FY", "").split("-")
        start = int(parts[0]) + offset
        end = start + 1
        return f"FY{start}-{str(end)[-2:]}"
    except (ValueError, IndexError):
        return fy
