"""Multi-Year Tax Projection — Forward-looking tax projections across FYs.

Enables taxpayers to see projected tax liability across future years
based on assumed income growth, deduction changes, and regime shifts.

Traceability: C19.3 (Multi-Year Projection — 0%→30%, P6)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ProjectionAssumption:
    """A single assumption for multi-year projection. Value object."""

    variable: str                      # e.g., "income_growth_rate"
    label: str                         # "Annual Income Growth"
    value: Decimal                     # e.g., 0.10 for 10%
    unit: str = "%"


@dataclass(frozen=True)
class YearProjection:
    """Projected tax for a single year. Value object."""

    financial_year: str
    projected_income: Decimal
    projected_deductions: Decimal
    projected_tax: Decimal
    projected_effective_rate: Decimal
    regime: str = "new"
    notes: str = ""


@dataclass
class MultiYearProjection:
    """Multi-year tax projection spanning several financial years. Entity."""

    projection_id: UUID
    start_year: str                      # "FY2025-26"
    end_year: str                        # "FY2029-30"
    assumptions: list[ProjectionAssumption] = field(default_factory=list)
    years: list[YearProjection] = field(default_factory=list)
    current_regime: str = "new"

    @staticmethod
    def create(start_year: str, years: int = 5) -> MultiYearProjection:
        return MultiYearProjection(
            projection_id=uuid4(), start_year=start_year,
            end_year=_increment_fy(start_year, years),
        )

    def add_assumption(self, variable: str, label: str, value: Decimal, unit: str = "%") -> None:
        self.assumptions.append(ProjectionAssumption(
            variable=variable, label=label, value=value, unit=unit,
        ))

    def add_year(self, projection: YearProjection) -> None:
        self.years.append(projection)

    @property
    def total_tax_across_years(self) -> Decimal:
        return sum(y.projected_tax for y in self.years)

    @property
    def avg_effective_rate(self) -> Decimal:
        total_income = sum(y.projected_income for y in self.years)
        if total_income == 0:
            return Decimal("0")
        return (self.total_tax_across_years / total_income * Decimal("100")).quantize(Decimal("0.1"))

    @property
    def summary(self) -> str:
        return (
            f"Projection {self.start_year}–{self.end_year}: "
            f"Total tax ₹{self.total_tax_across_years:,.0f} "
            f"(avg {self.avg_effective_rate}% effective rate)"
        )


def _increment_fy(fy: str, count: int) -> str:
    """Increment a financial year string by N years."""
    try:
        parts = fy.replace("FY", "").split("-")
        start = int(parts[0])
        end = start + count
        return f"FY{end}-{str(end + 1)[-2:]}"
    except (ValueError, IndexError):
        return fy
