"""Business & Professional Income Engine — Sections 28-44DB.

Presumptive taxation (44AD, 44ADA, 44AE) and basic P&L computation.

Traceability: C4.3 (Business Income — 0%→60%, P2)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional


class BusinessType(str, Enum):
    REGULAR = "regular"         # Full books of accounts
    PRESUMPTIVE_44AD = "44ad"   # Small business (turnover ≤ ₹2Cr, 8%/6% deemed)
    PRESUMPTIVE_44ADA = "44ada" # Professionals (gross receipts ≤ ₹50L, 50% deemed)
    PRESUMPTIVE_44AE = "44ae"   # Transporters (per-vehicle deemed income)


@dataclass(frozen=True)
class BusinessIncomeBreakdown:
    """Result of business income computation."""
    business_type: BusinessType
    gross_turnover: Decimal = Decimal("0")
    deemed_income: Decimal = Decimal("0")         # Presumptive income
    net_profit_as_per_pnl: Decimal = Decimal("0") # Regular books
    depreciation: Decimal = Decimal("0")
    other_allowances: Decimal = Decimal("0")
    other_disallowances: Decimal = Decimal("0")
    income_from_business: Decimal = Decimal("0")
    is_audit_required: bool = False

    def to_dict(self) -> dict:
        return {
            "business_type": self.business_type.value,
            "gross_turnover": str(self.gross_turnover),
            "deemed_income": str(self.deemed_income),
            "net_profit": str(self.net_profit_as_per_pnl),
            "depreciation": str(self.depreciation),
            "income_from_business": str(self.income_from_business),
            "audit_required": self.is_audit_required,
        }


class BusinessIncomeEngine:
    """Computes income under the head 'Profits & Gains of Business or Profession'.

    Supports presumptive taxation (44AD/44ADA/44AE) and basic P&L method.
    """

    # FY2025-26 limits
    LIMIT_44AD_TURNOVER = Decimal("20000000")     # ₹2Cr
    LIMIT_44AD_DIGITAL_TURNOVER = Decimal("30000000")  # ₹3Cr (95% digital)
    LIMIT_44ADA_RECEIPTS = Decimal("5000000")      # ₹50L for 44ADA
    LIMIT_44ADA_DIGITAL = Decimal("7500000")        # ₹75L (95% digital)
    AUDIT_THRESHOLD_44AB = Decimal("10000000")      # ₹1Cr (business)
    AUDIT_THRESHOLD_PROFESSION = Decimal("5000000") # ₹50L (profession)
    PRESUMPTIVE_RATE_44AD = Decimal("0.08")          # 8%
    PRESUMPTIVE_RATE_44AD_DIGITAL = Decimal("0.06")  # 6% (digital receipts)
    PRESUMPTIVE_RATE_44ADA = Decimal("0.50")          # 50%
    PRESUMPTIVE_44AE_PER_VEHICLE = Decimal("7500")    # Per ton per month (heavy goods)

    def compute_presumptive(
        self,
        business_type: BusinessType,
        gross_turnover: Decimal,
        digital_receipts_pct: Decimal = Decimal("0"),
        heavy_vehicles_count: int = 0,
        heavy_vehicles_months: int = 12,
    ) -> BusinessIncomeBreakdown:
        """Compute business income under presumptive taxation."""
        result = BusinessIncomeBreakdown(business_type=business_type)
        result = BusinessIncomeBreakdown(
            business_type=business_type,
            gross_turnover=gross_turnover,
        )

        if business_type == BusinessType.PRESUMPTIVE_44AD:
            # 8% deemed, 6% for digital receipts
            if digital_receipts_pct >= Decimal("95"):
                rate = self.PRESUMPTIVE_RATE_44AD_DIGITAL
            else:
                rate = self.PRESUMPTIVE_RATE_44AD

            deemed = gross_turnover * rate
            limit = self.LIMIT_44AD_DIGITAL_TURNOVER if digital_receipts_pct >= Decimal("95") else self.LIMIT_44AD_TURNOVER

            return BusinessIncomeBreakdown(
                business_type=business_type,
                gross_turnover=gross_turnover,
                deemed_income=deemed,
                income_from_business=deemed,
                is_audit_required=gross_turnover > self.AUDIT_THRESHOLD_44AB,
            )

        elif business_type == BusinessType.PRESUMPTIVE_44ADA:
            deemed = gross_turnover * self.PRESUMPTIVE_RATE_44ADA
            limit = self.LIMIT_44ADA_DIGITAL if digital_receipts_pct >= Decimal("95") else self.LIMIT_44ADA_RECEIPTS

            return BusinessIncomeBreakdown(
                business_type=business_type,
                gross_turnover=gross_turnover,
                deemed_income=deemed,
                income_from_business=deemed,
                is_audit_required=gross_turnover > self.AUDIT_THRESHOLD_PROFESSION,
            )

        elif business_type == BusinessType.PRESUMPTIVE_44AE:
            # Per heavy goods vehicle per month
            deemed = Decimal(str(heavy_vehicles_count * heavy_vehicles_months)) * self.PRESUMPTIVE_44AE_PER_VEHICLE
            return BusinessIncomeBreakdown(
                business_type=business_type,
                deemed_income=deemed,
                income_from_business=deemed,
            )

        return result

    def compute_regular(
        self,
        gross_turnover: Decimal,
        net_profit: Decimal,
        depreciation: Decimal = Decimal("0"),
        disallowances: Decimal = Decimal("0"),
    ) -> BusinessIncomeBreakdown:
        """Compute business income from P&L (regular books)."""
        income = net_profit + disallowances - depreciation
        return BusinessIncomeBreakdown(
            business_type=BusinessType.REGULAR,
            gross_turnover=gross_turnover,
            net_profit_as_per_pnl=net_profit,
            depreciation=depreciation,
            other_disallowances=disallowances,
            income_from_business=max(Decimal("0"), income),
            is_audit_required=gross_turnover > self.AUDIT_THRESHOLD_44AB,
        )
