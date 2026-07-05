"""House Property Income Engine — Sections 22-27.

Computes income/loss under the head 'Income from House Property'
for self-occupied, let-out, and deemed let-out properties.

Traceability: C4.2 (House Property — High gap, 20%→70%)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional


class PropertyType(str, Enum):
    SELF_OCCUPIED = "self_occupied"
    LET_OUT = "let_out"
    DEEMED_LET_OUT = "deemed_let_out"


@dataclass
class HouseProperty:
    """A single house property for income computation."""

    property_type: PropertyType
    municipal_value: Decimal = Decimal("0")
    actual_rent_received: Decimal = Decimal("0")
    municipal_taxes_paid: Decimal = Decimal("0")
    interest_on_loan: Decimal = Decimal("0")
    pre_construction_interest: Decimal = Decimal("0")
    completion_year_fy: Optional[str] = None   # "FY2023-24" — for pre-construction amortization
    co_owner_share: Decimal = Decimal("1")      # 1.0 = 100% ownership
    is_affordable_housing: bool = False         # Stamp duty ≤₹45L


@dataclass
class HousePropertyResult:
    """Computed income/loss from one house property."""

    property_type: PropertyType
    gross_annual_value: Decimal = Decimal("0")
    less_municipal_taxes: Decimal = Decimal("0")
    net_annual_value: Decimal = Decimal("0")
    standard_deduction_30pct: Decimal = Decimal("0")
    interest_deduction: Decimal = Decimal("0")
    pre_construction_interest_amortized: Decimal = Decimal("0")
    income_from_property: Decimal = Decimal("0")  # Positive = income, Negative = loss


@dataclass
class HousePropertyReport:
    """Aggregated house property income across all properties."""

    properties: list[HousePropertyResult] = field(default_factory=list)
    total_income: Decimal = Decimal("0")
    total_loss: Decimal = Decimal("0")

    @property
    def net_income(self) -> Decimal:
        """Net income/loss from all house properties (can be negative)."""
        return self.total_income + self.total_loss  # total_loss is already negative

    @property
    def loss_for_setoff(self) -> Decimal:
        """Loss available for set-off against other heads."""
        if self.net_income < 0:
            return abs(self.net_income)
        return Decimal("0")


class HousePropertyEngine:
    """Computes income under the head 'Income from House Property'.

    Uses RuleRepository for FY-specific limits (24B self-occupied cap, etc.).
    """

    # ── FY2025-26 Limits (also in RuleRepository) ──
    LIMIT_24B_SELF = Decimal("200000")        # ₹2L for self-occupied
    LIMIT_24B_AFFORDABLE = Decimal("200000")   # Same cap for affordable (deduction via 80EEA)
    STD_DEDUCTION_PCT = Decimal("0.30")        # 30% of NAV
    PRE_CONSTRUCTION_YEARS = 5                  # Amortized over 5 years

    def __init__(self) -> None:
        pass

    def compute(self, properties: list[HouseProperty]) -> HousePropertyReport:
        """Compute house property income for all properties."""
        results = []
        total_income = Decimal("0")
        total_loss = Decimal("0")

        for prop in properties:
            result = self._compute_one(prop)
            # Apply co-ownership share
            result.income_from_property *= prop.co_owner_share
            results.append(result)

            if result.income_from_property >= 0:
                total_income += result.income_from_property
            else:
                total_loss += result.income_from_property

        return HousePropertyReport(
            properties=results,
            total_income=total_income,
            total_loss=total_loss,
        )

    def _compute_one(self, prop: HouseProperty) -> HousePropertyResult:
        """Compute income from a single house property."""
        result = HousePropertyResult(property_type=prop.property_type)

        if prop.property_type == PropertyType.SELF_OCCUPIED:
            result.gross_annual_value = Decimal("0")
            result.net_annual_value = Decimal("0")
            result.standard_deduction_30pct = Decimal("0")

        elif prop.property_type in (PropertyType.LET_OUT, PropertyType.DEEMED_LET_OUT):
            # GAV = higher of municipal value or actual rent
            result.gross_annual_value = max(
                prop.municipal_value, prop.actual_rent_received,
            )
            # Less municipal taxes (only if paid by owner)
            result.less_municipal_taxes = prop.municipal_taxes_paid
            result.net_annual_value = max(
                Decimal("0"),
                result.gross_annual_value - result.less_municipal_taxes,
            )
            # 30% standard deduction on NAV
            result.standard_deduction_30pct = (
                result.net_annual_value * self.STD_DEDUCTION_PCT
            )

        # Interest deduction
        result.interest_deduction = self._compute_interest(prop)

        # Pre-construction interest (amortized over 5 years)
        result.pre_construction_interest_amortized = self._amortize_pre_construction(prop)

        # Income from property
        result.income_from_property = (
            result.net_annual_value
            - result.standard_deduction_30pct
            - result.interest_deduction
            - result.pre_construction_interest_amortized
        )

        return result

    def _compute_interest(self, prop: HouseProperty) -> Decimal:
        """Compute deductible interest based on property type."""
        interest = prop.interest_on_loan

        if prop.property_type == PropertyType.SELF_OCCUPIED:
            cap = self.LIMIT_24B_SELF
            if prop.is_affordable_housing:
                cap = self.LIMIT_24B_AFFORDABLE
            return min(interest, cap)

        # Let-out / deemed let-out: full interest deductible
        return interest

    def _amortize_pre_construction(self, prop: HouseProperty) -> Decimal:
        """Amortize pre-construction interest over 5 years from completion year."""
        if prop.pre_construction_interest <= 0:
            return Decimal("0")
        if not prop.completion_year_fy:
            return Decimal("0")

        # Each year for 5 years: 1/5th of pre-construction interest
        annual_amortization = prop.pre_construction_interest / Decimal(
            str(self.PRE_CONSTRUCTION_YEARS)
        )
        return annual_amortization
