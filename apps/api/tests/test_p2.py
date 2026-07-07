"""Unit tests for P2 — Business & Professional Taxation."""

from decimal import Decimal


class TestBusinessIncome:
    def test_presumptive_44ad_basic(self):
        from src.engine.business_income import BusinessIncomeEngine, BusinessType
        engine = BusinessIncomeEngine()
        result = engine.compute_presumptive(
            BusinessType.PRESUMPTIVE_44AD,
            gross_turnover=Decimal("5000000"),
        )
        assert result.income_from_business == Decimal("400000")  # 8%

    def test_presumptive_44ad_digital(self):
        from src.engine.business_income import BusinessIncomeEngine, BusinessType
        engine = BusinessIncomeEngine()
        result = engine.compute_presumptive(
            BusinessType.PRESUMPTIVE_44AD,
            gross_turnover=Decimal("5000000"),
            digital_receipts_pct=Decimal("95"),
        )
        assert result.income_from_business == Decimal("300000")  # 6%

    def test_presumptive_44ada(self):
        from src.engine.business_income import BusinessIncomeEngine, BusinessType
        engine = BusinessIncomeEngine()
        result = engine.compute_presumptive(
            BusinessType.PRESUMPTIVE_44ADA,
            gross_turnover=Decimal("2000000"),
        )
        assert result.income_from_business == Decimal("1000000")  # 50%

    def test_presumptive_44ae(self):
        from src.engine.business_income import BusinessIncomeEngine, BusinessType
        engine = BusinessIncomeEngine()
        result = engine.compute_presumptive(
            BusinessType.PRESUMPTIVE_44AE,
            gross_turnover=Decimal("0"),
            heavy_vehicles_count=2,
            heavy_vehicles_months=12,
        )
        assert result.income_from_business == Decimal("180000")  # 2×12×7500

    def test_regular_pnl(self):
        from src.engine.business_income import BusinessIncomeEngine, BusinessType
        engine = BusinessIncomeEngine()
        result = engine.compute_regular(
            gross_turnover=Decimal("8000000"),
            net_profit=Decimal("1200000"),
            depreciation=Decimal("200000"),
        )
        assert result.income_from_business == Decimal("1000000")

    def test_audit_required_above_threshold(self):
        from src.engine.business_income import BusinessIncomeEngine, BusinessType
        engine = BusinessIncomeEngine()
        result = engine.compute_presumptive(
            BusinessType.PRESUMPTIVE_44AD,
            gross_turnover=Decimal("15000000"),
        )
        assert result.is_audit_required


class Test80G:
    def test_100_no_limit(self):
        from src.engine.donation_80g import (
            Donation80GEngine, DonationEntry, DoneeCategory,
        )
        engine = Donation80GEngine()
        result = engine.compute(
            donations=[
                DonationEntry("PM Relief Fund", Decimal("10000"),
                             DoneeCategory.FULL_100_NO_LIMIT),
            ],
            adjusted_gti=Decimal("500000"),
        )
        assert result.deduction_80g == Decimal("10000")

    def test_50_with_limit(self):
        from src.engine.donation_80g import (
            Donation80GEngine, DonationEntry, DoneeCategory,
        )
        engine = Donation80GEngine()
        result = engine.compute(
            donations=[
                DonationEntry("Registered Trust", Decimal("50000"),
                             DoneeCategory.FULL_50_WITH_LIMIT),
            ],
            adjusted_gti=Decimal("500000"),
        )
        # 50% of 50000 = 25000. Qualifying limit = 10% of 500K = 50000.
        # min(25000, 50000) = 25000
        assert result.deduction_80g == Decimal("25000")

    def test_cash_above_2k_not_deductible(self):
        from src.engine.donation_80g import (
            Donation80GEngine, DonationEntry, DoneeCategory,
        )
        engine = Donation80GEngine()
        result = engine.compute(
            donations=[
                DonationEntry("Trust", Decimal("5000"),
                             DoneeCategory.FULL_50_WITH_LIMIT, is_cash=True),
            ],
            adjusted_gti=Decimal("500000"),
        )
        assert result.deduction_80g == Decimal("0")

    def test_multiple_categories(self):
        from src.engine.donation_80g import (
            Donation80GEngine, DonationEntry, DoneeCategory,
        )
        engine = Donation80GEngine()
        result = engine.compute(
            donations=[
                DonationEntry("PM Fund", Decimal("5000"),
                             DoneeCategory.FULL_100_NO_LIMIT),
                DonationEntry("Trust", Decimal("10000"),
                             DoneeCategory.FULL_50_WITH_LIMIT),
            ],
            adjusted_gti=Decimal("500000"),
        )
        # 100% no limit: 5000. 50% with limit: min(5000, 50000) = 5000.
        # Total: 10000
        assert result.deduction_80g == Decimal("10000")
