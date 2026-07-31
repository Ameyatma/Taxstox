"""Tax Scenario Simulator — What-if analysis for income and deduction changes.

Allows taxpayers to see how changes affect their final tax liability.
Uses RuleEvaluator to recompute deterministically.

Traceability: C19.1 (Scenario Simulator — 0%→40%, P6)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ScenarioVariable:
    """A single variable to change in a what-if scenario. Value object."""

    variable: str                      # e.g., "salary", "80c", "home_loan_interest"
    label: str                         # e.g., "Salary Income"
    original_value: Decimal
    new_value: Decimal
    unit: str = "₹"                    # "₹", "%", "count"


@dataclass(frozen=True)
class ScenarioComparison:
    """Side-by-side comparison of original vs. scenario tax. Value object."""

    scenario_id: UUID
    scenario_name: str
    variables_changed: tuple[ScenarioVariable, ...]

    # Original
    original_total_income: Decimal
    original_final_tax: Decimal
    original_effective_rate: Decimal

    # Scenario
    scenario_total_income: Decimal
    scenario_final_tax: Decimal
    scenario_effective_rate: Decimal

    # Difference
    tax_difference: Decimal             # Positive = scenario saves tax
    income_difference: Decimal

    @property
    def saves_tax(self) -> bool:
        return self.tax_difference > 0

    @property
    def summary(self) -> str:
        direction = "saves" if self.saves_tax else "costs"
        return (
            f"Scenario '{self.scenario_name}': {direction} ₹{abs(self.tax_difference):,.0f} "
            f"in tax. Effective rate: {self.original_effective_rate:.1f}% → {self.scenario_effective_rate:.1f}%"
        )


@dataclass
class TaxScenario:
    """A complete what-if tax scenario. Entity."""

    scenario_id: UUID
    name: str                            # "Maxed out 80C", "Switched to New Regime"
    description: str = ""
    variables: list[ScenarioVariable] = field(default_factory=list)

    @staticmethod
    def create(name: str, description: str = "") -> TaxScenario:
        return TaxScenario(scenario_id=uuid4(), name=name, description=description)

    def add_variable(
        self, variable: str, label: str,
        original_value: Decimal, new_value: Decimal, unit: str = "₹",
    ) -> None:
        self.variables.append(ScenarioVariable(
            variable=variable, label=label,
            original_value=original_value, new_value=new_value, unit=unit,
        ))

    def apply_to_breakdown(self, breakdown: dict) -> dict:
        """Apply scenario variables to a tax breakdown dict. Returns modified copy."""
        modified = dict(breakdown)
        for var in self.variables:
            modified[var.variable] = str(var.new_value)
        return modified

    @property
    def total_change(self) -> Decimal:
        """Sum of all variable changes."""
        total = Decimal("0")
        for var in self.variables:
            total += var.new_value - var.original_value
        return total
