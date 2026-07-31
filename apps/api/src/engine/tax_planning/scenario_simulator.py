"""Scenario Simulator — Recomputes tax with modified inputs.

Uses RuleEvaluator to deterministically recompute tax for
what-if scenarios. No duplicated tax logic.

Traceability: C19.1 (Scenario Simulator — 0%→40%, P6)
"""

from __future__ import annotations

from decimal import Decimal

from src.domain.tax_planning.scenario import (
    TaxScenario,
    ScenarioComparison,
    ScenarioVariable,
)
from src.engine.rules.evaluator import RuleEvaluator
from src.engine.rules.config import rule_repository
from src.models.financial_year import FinancialYear


class ScenarioSimulator:
    """Simulates what-if tax scenarios by re-running RuleEvaluator.

    Engine. Deterministic. Every scenario is a real tax computation
    using the same RuleEvaluator as live filing.
    """

    def __init__(self) -> None:
        self._evaluator = RuleEvaluator()

    def simulate(
        self,
        scenario: TaxScenario,
        baseline_breakdown: dict,
        financial_year_str: str = "FY2025-26",
        regime: str = "new",
    ) -> ScenarioComparison:
        """Run a scenario and produce a comparison against baseline.

        Args:
            scenario: The scenario to simulate
            baseline_breakdown: Current tax breakdown dict
            financial_year_str: FY for rule lookup
            regime: "old" or "new"

        Returns:
            ScenarioComparison with side-by-side analysis
        """
        fy = FinancialYear.from_string(financial_year_str)
        config = rule_repository.get(fy)
        regime_config = config.get_regime(regime)

        # Extract baseline values
        original_income = Decimal(str(baseline_breakdown.get("total_income", "0")))
        original_tax = Decimal(str(baseline_breakdown.get("final_tax", "0")))
        original_rate = (
            (original_tax / original_income * Decimal("100")).quantize(Decimal("0.1"))
            if original_income > 0 else Decimal("0")
        )

        # Apply scenario variables
        modified = scenario.apply_to_breakdown(baseline_breakdown)
        scenario_income = Decimal(str(modified.get("total_income", str(original_income))))

        # Recompute with modified inputs
        scenario_tax = self._evaluate_scenario_tax(scenario_income, regime_config)
        scenario_rate = (
            (scenario_tax / scenario_income * Decimal("100")).quantize(Decimal("0.1"))
            if scenario_income > 0 else Decimal("0")
        )

        return ScenarioComparison(
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            variables_changed=tuple(scenario.variables),
            original_total_income=original_income,
            original_final_tax=original_tax,
            original_effective_rate=original_rate,
            scenario_total_income=scenario_income,
            scenario_final_tax=scenario_tax,
            scenario_effective_rate=scenario_rate,
            tax_difference=original_tax - scenario_tax,
            income_difference=scenario_income - original_income,
        )

    def _evaluate_scenario_tax(self, total_income: Decimal, regime_config) -> Decimal:
        """Compute tax for a scenario income value."""
        tax = self._evaluator.compute_slab_tax(total_income, regime_config.slabs)
        rebate = self._evaluator.compute_rebate(tax, total_income, regime_config)
        tax_after_rebate = tax - rebate

        from src.engine.rules.config import rule_repository
        fy25 = FinancialYear.from_string("FY2025-26")
        config = rule_repository.get(fy25)
        surcharge = self._evaluator.compute_surcharge(total_income, tax_after_rebate, config)
        cess = self._evaluator.compute_cess(tax_after_rebate, surcharge, config.cess_rate)

        return self._evaluator.round_final_tax(tax_after_rebate + surcharge + cess)

    @staticmethod
    def quick_scenario(
        name: str, income_change: Decimal, baseline_breakdown: dict,
        financial_year: str = "FY2025-26", regime: str = "new",
    ) -> ScenarioComparison:
        """Convenience: create and run a quick income-change scenario."""
        scenario = TaxScenario.create(name, f"What if income changes by ₹{income_change:,.0f}")
        original_income = Decimal(str(baseline_breakdown.get("total_income", "0")))
        scenario.add_variable("total_income", "Total Income", original_income,
                             max(Decimal("0"), original_income + income_change))
        simulator = ScenarioSimulator()
        return simulator.simulate(scenario, baseline_breakdown, financial_year, regime)
