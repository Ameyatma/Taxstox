"""80G Donation Engine — Qualifying limits, donee categories.

Section 80G: Deduction for donations to charitable institutions.
Different donee types have different qualifying limits (50%, 100%).

Traceability: C5.5 (Donation 80G Engine — 0%→60%, P2)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class DoneeCategory(str, Enum):
    """80G donee categories determine the qualifying limit."""
    FULL_100_NO_LIMIT = "100_no_limit"    # PM Relief Fund, etc. — 100%, no qualifying limit
    FULL_50_NO_LIMIT = "50_no_limit"      # JN Memorial Fund — 50%, no qualifying limit
    FULL_100_WITH_LIMIT = "100_limit"     # Govt/local authority — 100%, subject to qualifying limit
    FULL_50_WITH_LIMIT = "50_limit"       # Registered trusts — 50%, subject to qualifying limit


@dataclass(frozen=True)
class DonationEntry:
    """A single donation."""
    donee_name: str
    amount: Decimal
    category: DoneeCategory
    has_receipt: bool = True
    is_cash: bool = False                  # Cash donations > ₹2,000 not deductible
    pan_of_donee: str = ""


@dataclass(frozen=True)
class DonationResult:
    """80G deduction computation result."""
    donations: tuple[DonationEntry, ...]
    total_donated: Decimal = Decimal("0")
    eligible_amount: Decimal = Decimal("0")   # After cash limit, category caps
    qualifying_limit_pct: Decimal = Decimal("0.10")  # 10% of adjusted GTI
    adjusted_gti: Decimal = Decimal("0")
    deduction_80g: Decimal = Decimal("0")
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "total_donated": str(self.total_donated),
            "eligible_amount": str(self.eligible_amount),
            "deduction_80g": str(self.deduction_80g),
            "explanation": self.explanation,
        }


class Donation80GEngine:
    """Computes 80G deduction per donee category rules.

    Rules:
    - Cash donations > ₹2,000 are NOT deductible
    - 100% no-limit: full amount deductible, no qualifying limit
    - 50% no-limit: 50% of amount deductible, no qualifying limit
    - 100% with limit: 100% deductible, subject to 10% of adjusted GTI
    - 50% with limit: 50% deductible, subject to 10% of adjusted GTI
    - Adjusted GTI = Gross Total Income - all deductions except 80G
    """

    CASH_LIMIT = Decimal("2000")
    QUALIFYING_LIMIT_PCT = Decimal("0.10")  # 10% of adjusted GTI

    def compute(
        self,
        donations: list[DonationEntry],
        adjusted_gti: Decimal,
    ) -> DonationResult:
        """Compute 80G deduction from donations list."""
        qualifying_limit = adjusted_gti * self.QUALIFYING_LIMIT_PCT
        total_donated = sum(d.amount for d in donations)
        eligible = Decimal("0")
        subject_to_limit = Decimal("0")

        for d in donations:
            # Cash limit
            amount = d.amount
            if d.is_cash and amount > self.CASH_LIMIT:
                continue  # Not deductible

            if d.category == DoneeCategory.FULL_100_NO_LIMIT:
                eligible += amount
            elif d.category == DoneeCategory.FULL_50_NO_LIMIT:
                eligible += amount * Decimal("0.50")
            elif d.category == DoneeCategory.FULL_100_WITH_LIMIT:
                subject_to_limit += amount
            elif d.category == DoneeCategory.FULL_50_WITH_LIMIT:
                subject_to_limit += amount * Decimal("0.50")

        # Apply qualifying limit to limited-category donations
        limited_deduction = min(subject_to_limit, qualifying_limit)
        deduction = eligible + limited_deduction

        return DonationResult(
            donations=tuple(donations),
            total_donated=total_donated,
            eligible_amount=eligible + subject_to_limit,
            qualifying_limit_pct=self.QUALIFYING_LIMIT_PCT,
            adjusted_gti=adjusted_gti,
            deduction_80g=deduction,
            explanation=(
                f"Total donated: ₹{total_donated:,.0f}. "
                f"Eligible: ₹{eligible + subject_to_limit:,.0f}. "
                f"Qualifying limit (10% of AGTI): ₹{qualifying_limit:,.0f}. "
                f"80G deduction: ₹{deduction:,.0f}."
            ),
        )
