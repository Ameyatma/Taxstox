"""Unit tests for Interest Engine — 234A, 234B, 234C, 234F."""

from datetime import date
from decimal import Decimal

from src.engine.interest_engine import InterestEngine, InterestResult
from src.models.financial_year import FinancialYear


FY2025_26 = FinancialYear.from_string("FY2025-26")


class Test234ALateFiling:
    def test_no_interest_if_filed_on_time(self):
        engine = InterestEngine()
        result = engine.compute(
            tax_liability=Decimal("50000"),
            tds_credited=Decimal("50000"),
            advance_tax_paid=Decimal("0"),
            self_assessment_tax=Decimal("0"),
            filing_date=date(2026, 7, 31),  # On due date
            fy=FY2025_26,
        )
        assert result.interest_234a == Decimal("0")

    def test_interest_if_filed_late(self):
        engine = InterestEngine()
        result = engine.compute(
            tax_liability=Decimal("50000"),
            tds_credited=Decimal("0"),
            advance_tax_paid=Decimal("0"),
            self_assessment_tax=Decimal("0"),
            filing_date=date(2026, 9, 15),  # ~1.5 months late
            fy=FY2025_26,
        )
        assert result.interest_234a > Decimal("0")

    def test_no_interest_if_tax_fully_covered_by_tds(self):
        engine = InterestEngine()
        result = engine.compute(
            tax_liability=Decimal("50000"),
            tds_credited=Decimal("50000"),
            advance_tax_paid=Decimal("0"),
            self_assessment_tax=Decimal("0"),
            filing_date=date(2026, 9, 15),  # Late, but TDS covers tax
            fy=FY2025_26,
        )
        assert result.interest_234a == Decimal("0")


class Test234BAdvanceTax:
    def test_no_interest_if_advance_tax_paid(self):
        engine = InterestEngine()
        result = engine.compute(
            tax_liability=Decimal("100000"),
            tds_credited=Decimal("0"),
            advance_tax_paid=Decimal("90000"),  # 90%
            self_assessment_tax=Decimal("0"),
            filing_date=date(2026, 7, 31),
            fy=FY2025_26,
        )
        assert result.interest_234b == Decimal("0")

    def test_senior_citizen_exempt_no_business(self):
        engine = InterestEngine()
        result = engine.compute(
            tax_liability=Decimal("200000"),
            tds_credited=Decimal("0"),
            advance_tax_paid=Decimal("0"),
            self_assessment_tax=Decimal("0"),
            filing_date=date(2026, 7, 31),
            fy=FY2025_26,
            is_senior_citizen=True,
            has_business_income=False,
        )
        assert result.interest_234b == Decimal("0")

    def test_below_10k_threshold(self):
        """No advance tax needed if assessed tax ≤ ₹10,000."""
        engine = InterestEngine()
        result = engine.compute(
            tax_liability=Decimal("15000"),
            tds_credited=Decimal("10000"),
            advance_tax_paid=Decimal("0"),
            self_assessment_tax=Decimal("0"),
            filing_date=date(2026, 7, 31),
            fy=FY2025_26,
        )
        assert result.interest_234b == Decimal("0")


class Test234F:
    def test_no_fee_on_time(self):
        engine = InterestEngine()
        result = engine.compute(
            tax_liability=Decimal("100000"),
            tds_credited=Decimal("100000"),
            advance_tax_paid=Decimal("0"),
            self_assessment_tax=Decimal("0"),
            filing_date=date(2026, 7, 31),
            fy=FY2025_26,
        )
        assert result.late_filing_fee_234f == Decimal("0")

    def test_5000_fee_until_dec_31(self):
        engine = InterestEngine()
        result = engine.compute(
            tax_liability=Decimal("100000"),
            tds_credited=Decimal("0"),
            advance_tax_paid=Decimal("0"),
            self_assessment_tax=Decimal("0"),
            filing_date=date(2026, 10, 1),
            fy=FY2025_26,
            total_income=Decimal("600000"),  # Above ₹5L
        )
        assert result.late_filing_fee_234f == Decimal("5000")

    def test_1000_fee_low_income(self):
        engine = InterestEngine()
        result = engine.compute(
            tax_liability=Decimal("10000"),
            tds_credited=Decimal("0"),
            advance_tax_paid=Decimal("0"),
            self_assessment_tax=Decimal("0"),
            filing_date=date(2026, 10, 1),
            fy=FY2025_26,
        )
        assert result.late_filing_fee_234f == Decimal("1000")


class TestInterestResult:
    def test_result_is_immutable(self):
        result = InterestResult(interest_234a=Decimal("1000"))
        assert result.total == Decimal("1000")

    def test_clean_result_no_interest(self):
        result = InterestResult()
        assert "No interest" in result.interest_explanation
