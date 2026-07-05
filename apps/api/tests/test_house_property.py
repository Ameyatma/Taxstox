"""Unit tests for House Property Income Engine."""

from decimal import Decimal

from src.engine.house_property import (
    HouseProperty,
    HousePropertyEngine,
    PropertyType,
)


class TestSelfOccupied:
    def test_self_occupied_basic(self):
        """Self-occupied: GAV=0, interest capped at ₹2L."""
        engine = HousePropertyEngine()
        prop = HouseProperty(
            property_type=PropertyType.SELF_OCCUPIED,
            interest_on_loan=Decimal("180000"),
        )
        report = engine.compute([prop])
        result = report.properties[0]
        assert result.gross_annual_value == Decimal("0")
        assert result.interest_deduction == Decimal("180000")
        assert result.income_from_property == Decimal("-180000")

    def test_self_occupied_interest_capped(self):
        """Interest above ₹2L capped."""
        engine = HousePropertyEngine()
        prop = HouseProperty(
            property_type=PropertyType.SELF_OCCUPIED,
            interest_on_loan=Decimal("250000"),
        )
        report = engine.compute([prop])
        assert report.properties[0].interest_deduction == Decimal("200000")

    def test_self_occupied_no_standard_deduction(self):
        """Self-occupied gets no 30% standard deduction."""
        engine = HousePropertyEngine()
        prop = HouseProperty(property_type=PropertyType.SELF_OCCUPIED)
        report = engine.compute([prop])
        assert report.properties[0].standard_deduction_30pct == Decimal("0")


class TestLetOut:
    def test_let_out_basic(self):
        """Let-out: GAV, 30% std deduction, full interest."""
        engine = HousePropertyEngine()
        prop = HouseProperty(
            property_type=PropertyType.LET_OUT,
            municipal_value=Decimal("300000"),
            actual_rent_received=Decimal("360000"),
            municipal_taxes_paid=Decimal("10000"),
            interest_on_loan=Decimal("200000"),
        )
        report = engine.compute([prop])
        result = report.properties[0]
        assert result.gross_annual_value == Decimal("360000")
        assert result.net_annual_value == Decimal("350000")
        assert result.standard_deduction_30pct == Decimal("105000")
        assert result.interest_deduction == Decimal("200000")
        assert result.income_from_property == Decimal("45000")

    def test_let_out_full_interest_no_cap(self):
        """Let-out interest is NOT capped at ₹2L."""
        engine = HousePropertyEngine()
        prop = HouseProperty(
            property_type=PropertyType.LET_OUT,
            actual_rent_received=Decimal("600000"),
            interest_on_loan=Decimal("500000"),
        )
        report = engine.compute([prop])
        assert report.properties[0].interest_deduction == Decimal("500000")


class TestMultipleProperties:
    def test_aggregation(self):
        """Multiple properties aggregate correctly."""
        engine = HousePropertyEngine()
        props = [
            HouseProperty(
                property_type=PropertyType.SELF_OCCUPIED,
                interest_on_loan=Decimal("150000"),
            ),
            HouseProperty(
                property_type=PropertyType.LET_OUT,
                actual_rent_received=Decimal("300000"),
                interest_on_loan=Decimal("100000"),
            ),
        ]
        report = engine.compute(props)
        # Self-occupied: -150K, Let-out: 300K - 90K(std) - 100K(int) = 110K
        # Total: -40K
        assert report.net_income == Decimal("-40000")
        assert report.loss_for_setoff == Decimal("40000")


class TestCoOwnership:
    def test_co_owner_share(self):
        """50% co-owner gets half the income/loss."""
        engine = HousePropertyEngine()
        prop = HouseProperty(
            property_type=PropertyType.SELF_OCCUPIED,
            interest_on_loan=Decimal("200000"),
            co_owner_share=Decimal("0.50"),
        )
        report = engine.compute([prop])
        assert report.properties[0].income_from_property == Decimal("-100000")
