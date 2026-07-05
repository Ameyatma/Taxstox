"""Unit tests for FinancialYear value object."""

from datetime import date
from decimal import Decimal

import pytest

from src.models.financial_year import FinancialYear


class TestFinancialYearCreation:
    def test_from_string_fy_format(self):
        fy = FinancialYear.from_string("FY2025-26")
        assert fy.start_year == 2025
        assert fy.end_year == 2026

    def test_from_string_no_prefix(self):
        fy = FinancialYear.from_string("2024-25")
        assert fy.start_year == 2024
        assert fy.end_year == 2025

    def test_from_date_april(self):
        fy = FinancialYear.from_date(date(2025, 4, 1))
        assert fy.start_year == 2025
        assert fy.end_year == 2026

    def test_from_date_january(self):
        fy = FinancialYear.from_date(date(2026, 1, 15))
        assert fy.start_year == 2025
        assert fy.end_year == 2026

    def test_from_date_march(self):
        fy = FinancialYear.from_date(date(2026, 3, 31))
        assert fy.start_year == 2025
        assert fy.end_year == 2026

    def test_invalid_range_raises(self):
        with pytest.raises(ValueError):
            FinancialYear(start_year=2025, end_year=2025)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            FinancialYear.from_string("not-a-year")


class TestFinancialYearProperties:
    def test_assessment_year(self):
        fy = FinancialYear.from_string("FY2025-26")
        assert fy.assessment_year == "2026-27"

    def test_label(self):
        fy = FinancialYear.from_string("FY2025-26")
        assert fy.label == "FY2025-26"

    def test_start_date(self):
        fy = FinancialYear.from_string("FY2025-26")
        assert fy.start_date == date(2025, 4, 1)

    def test_end_date(self):
        fy = FinancialYear.from_string("FY2025-26")
        assert fy.end_date == date(2026, 3, 31)

    def test_previous(self):
        fy = FinancialYear.from_string("FY2025-26")
        assert fy.previous.label == "FY2024-25"

    def test_next(self):
        fy = FinancialYear.from_string("FY2025-26")
        assert fy.next.label == "FY2026-27"


class TestFinancialYearComparison:
    def test_ordering(self):
        fy1 = FinancialYear.from_string("FY2024-25")
        fy2 = FinancialYear.from_string("FY2025-26")
        assert fy1 < fy2

    def test_equality(self):
        fy1 = FinancialYear.from_string("FY2025-26")
        fy2 = FinancialYear(start_year=2025, end_year=2026)
        assert fy1 == fy2

    def test_hashable(self):
        fy1 = FinancialYear.from_string("FY2025-26")
        fy2 = FinancialYear.from_string("FY2025-26")
        d = {fy1: "test"}
        assert d[fy2] == "test"
