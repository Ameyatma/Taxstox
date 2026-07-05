"""FinancialYear value object — typesafe, validated, immutable.

Replaces raw strings ("FY2025-26", "2026-27") throughout the codebase.
Enforces Financial Year = April 1 to March 31 (Indian tax year).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from functools import total_ordering

# Pattern: "FY2025-26" or "FY2024-25"
FY_PATTERN = re.compile(r"^FY(\d{4})-(\d{2})$")


@total_ordering
@dataclass(frozen=True)
class FinancialYear:
    """An Indian financial year (April 1 to March 31).

    Examples:
        FY2025-26: April 1, 2025 to March 31, 2026
        FY2024-25: April 1, 2024 to March 31, 2025

    Properties:
        start_year: The calendar year the FY starts in (e.g., 2025 for FY2025-26)
        end_year: The calendar year the FY ends in (e.g., 2026 for FY2025-26)
        assessment_year: e.g., "2026-27" for FY2025-26
        start_date: April 1 of start_year
        end_date: March 31 of end_year
    """

    start_year: int
    end_year: int

    def __post_init__(self) -> None:
        if self.end_year != self.start_year + 1:
            raise ValueError(
                f"Invalid financial year: end_year ({self.end_year}) "
                f"must be start_year + 1 ({self.start_year + 1})"
            )
        if self.start_year < 2000 or self.start_year > 2100:
            raise ValueError(
                f"Financial year out of range: {self.start_year}"
            )

    @classmethod
    def from_string(cls, fy_str: str) -> FinancialYear:
        """Parse from string formats: 'FY2025-26', '2025-26', 'FY2025'."""
        fy_str = fy_str.strip()

        # "FY2025-26"
        match = FY_PATTERN.match(fy_str)
        if match:
            start = int(match.group(1))
            end = int(f"20{match.group(2)}")
            return cls(start_year=start, end_year=end)

        # "2025-26" (no FY prefix)
        match = re.match(r"^(\d{4})-(\d{2})$", fy_str)
        if match:
            start = int(match.group(1))
            end = int(f"20{match.group(2)}")
            return cls(start_year=start, end_year=end)

        raise ValueError(f"Invalid financial year format: '{fy_str}'. Expected 'FY2025-26'.")

    @classmethod
    def from_date(cls, d: date) -> FinancialYear:
        """Determine the financial year for a given date."""
        if d.month >= 4:
            return cls(start_year=d.year, end_year=d.year + 1)
        else:
            return cls(start_year=d.year - 1, end_year=d.year)

    @classmethod
    def current(cls) -> FinancialYear:
        """Current financial year based on today's date."""
        return cls.from_date(date.today())

    @property
    def assessment_year(self) -> str:
        """Assessment year string, e.g., '2026-27' for FY2025-26."""
        start_short = str(self.end_year)[2:]
        end_short = str(self.end_year + 1)[2:]
        return f"{self.end_year}-{end_short}"

    @property
    def start_date(self) -> date:
        return date(self.start_year, 4, 1)

    @property
    def end_date(self) -> date:
        return date(self.end_year, 3, 31)

    @property
    def previous(self) -> FinancialYear:
        return FinancialYear(start_year=self.start_year - 1, end_year=self.end_year - 1)

    @property
    def next(self) -> FinancialYear:
        return FinancialYear(start_year=self.start_year + 1, end_year=self.end_year + 1)

    @property
    def label(self) -> str:
        """Standard label: 'FY2025-26'."""
        end_short = str(self.end_year)[2:]
        return f"FY{self.start_year}-{end_short}"

    def __str__(self) -> str:
        return self.label

    def __repr__(self) -> str:
        return f"FinancialYear('{self.label}')"

    def __lt__(self, other: FinancialYear) -> bool:
        return (self.start_year, self.end_year) < (other.start_year, other.end_year)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FinancialYear):
            return NotImplemented
        return self.start_year == other.start_year and self.end_year == other.end_year

    def __hash__(self) -> int:
        return hash((self.start_year, self.end_year))
