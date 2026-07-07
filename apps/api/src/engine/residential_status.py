"""Residential Status Engine — Section 6 of the Income Tax Act, 1961.

Determines ROR (Resident and Ordinarily Resident), RNOR (Resident but
Not Ordinarily Resident), NR (Non-Resident), and Deemed Resident.

Traceability: C2.2 (Residential Status — 5%→80%, P1)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from decimal import Decimal

from src.models.financial_year import FinancialYear


class ResidentialStatus(str, Enum):
    ROR = "ROR"        # Resident and Ordinarily Resident
    RNOR = "RNOR"      # Resident but Not Ordinarily Resident
    NR = "NR"          # Non-Resident


@dataclass(frozen=True)
class ResidentialStatusResult:
    """Determined residential status with reasoning."""

    status: ResidentialStatus
    days_in_india_fy: int              # Days present in India during the FY
    days_in_india_preceding_4: int      # Days in preceding 4 FYs
    days_in_india_preceding_7: int      # Days in preceding 7 FYs
    is_citizen_or_pio: bool = False     # Indian citizen or Person of Indian Origin
    india_income_exceeds_15l: bool = False  # India-sourced income > ₹15L
    non_resident_in_9_of_10: bool = False  # NR in 9 of 10 preceding FYs
    explanation: str = ""


class ResidentialStatusEngine:
    """Determines residential status per Section 6.

    Pure domain logic. No external dependencies. Deterministic.
    """

    def determine(
        self,
        days_in_india_fy: int,
        days_in_india_preceding_4: int,
        days_in_india_preceding_7: int = 0,
        is_citizen_or_pio: bool = False,
        india_income: Decimal = Decimal("0"),
        non_resident_in_9_of_10: bool = False,
    ) -> ResidentialStatusResult:
        """Determine residential status from factual inputs.

        Args:
            days_in_india_fy: Days present in India during the financial year
            days_in_india_preceding_4: Days in India during the 4 preceding FYs
            days_in_india_preceding_7: Days in India during the 7 preceding FYs
            is_citizen_or_pio: Indian citizen or Person of Indian Origin
            india_income: Income from Indian sources (for deemed resident test)
            non_resident_in_9_of_10: Was NR in 9 out of 10 preceding FYs
        """

        # ── Step 1: Basic Residence Test (Section 6(1)) ──
        condition_a = days_in_india_fy >= 182
        condition_b = (
            days_in_india_fy >= 60
            and days_in_india_preceding_4 >= 365
        )

        # Exception: 60 days → 182 days for citizens/PIO with India income > ₹15L
        # who are not liable to tax in any other country
        if is_citizen_or_pio and india_income > Decimal("1500000"):
            condition_b = False  # Only 182-day test applies

        # Visiting citizen/PIO: 60→120 days if India income ≤ ₹15L
        if is_citizen_or_pio and india_income <= Decimal("1500000"):
            condition_b = days_in_india_fy >= 120 and days_in_india_preceding_4 >= 365

        is_resident = condition_a or condition_b

        # ── Step 2: Deemed Resident (Section 6(1A)) ──
        # Indian citizen/PIO with India income > ₹15L, not liable to tax elsewhere.
        # Deemed residents bypass the basic 182-day test.
        deemed_resident = (
            is_citizen_or_pio
            and india_income > Decimal("1500000")
            and days_in_india_fy >= 120
        )

        if deemed_resident:
            return ResidentialStatusResult(
                status=ResidentialStatus.RNOR,
                days_in_india_fy=days_in_india_fy,
                days_in_india_preceding_4=days_in_india_preceding_4,
                days_in_india_preceding_7=days_in_india_preceding_7,
                is_citizen_or_pio=True,
                india_income_exceeds_15l=True,
                non_resident_in_9_of_10=non_resident_in_9_of_10,
                explanation="Deemed Resident (RNOR): Indian citizen/PIO with India "
                            "income > ₹15L, not liable to tax in any other country. "
                            "Always RNOR regardless of prior residence history.",
            )

        if not is_resident:
            return ResidentialStatusResult(
                status=ResidentialStatus.NR,
                days_in_india_fy=days_in_india_fy,
                days_in_india_preceding_4=days_in_india_preceding_4,
                days_in_india_preceding_7=days_in_india_preceding_7,
                is_citizen_or_pio=is_citizen_or_pio,
                india_income_exceeds_15l=india_income > Decimal("1500000"),
                non_resident_in_9_of_10=non_resident_in_9_of_10,
                explanation=f"Non-Resident: {days_in_india_fy} days in India during FY "
                            f"(< 182 days, basic conditions not met).",
            )

        # ── Step 3: Ordinarily Resident Test (Section 6(6)) ──
        is_ror = (
            not non_resident_in_9_of_10  # Was resident in ≥2 of 10 preceding FYs
            and days_in_india_preceding_7 <= 729  # ≤ 729 days in preceding 7 FYs
        )

        if is_ror:
            explanation = (
                f"Resident and Ordinarily Resident: {days_in_india_fy} days in FY "
                f"(≥182 or basic conditions met) + ordinarily resident conditions satisfied."
            )
        else:
            explanation = (
                f"Resident but Not Ordinarily Resident: Meets residence test but "
                f"fails ordinarily resident conditions (NR in 9/10 yrs: {non_resident_in_9_of_10}, "
                f"days in 7 preceding FYs: {days_in_india_preceding_7})."
            )

        return ResidentialStatusResult(
            status=ResidentialStatus.ROR if is_ror else ResidentialStatus.RNOR,
            days_in_india_fy=days_in_india_fy,
            days_in_india_preceding_4=days_in_india_preceding_4,
            days_in_india_preceding_7=days_in_india_preceding_7,
            is_citizen_or_pio=is_citizen_or_pio,
            india_income_exceeds_15l=india_income > Decimal("1500000"),
            non_resident_in_9_of_10=non_resident_in_9_of_10,
            explanation=explanation,
        )
