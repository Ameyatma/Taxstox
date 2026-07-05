"""Unit tests for domain model validation.

Verifies Pydantic v2 model validation, Decimal handling,
enum correctness, and computed properties.
"""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.models.ais import AISData
from src.models.form16 import (
    ChapterVIADeductions,
    Form16Data,
    Form16PartA,
    Form16PartB,
    Form16Annexure,
    Regime,
    Section10Exemptions,
    TaxComputation,
)
from src.models.tax import (
    CGSaleEntry,
    ClassifiedCGData,
    CGDateRanges,
    RegimeResult,
    UserAnswers,
)
from src.models.user import UserCreate


class TestForm16Models:
    """Form 16 domain model validation."""

    def test_regime_enum_new(self):
        """Regime enum resolves correctly."""
        form16 = Form16PartB(opting_out_115bac=False)
        data = Form16Data(
            part_a=Form16PartA(),
            part_b=form16,
            annexure=Form16Annexure(),
        )
        assert data.regime == Regime.NEW

    def test_regime_enum_old(self):
        """Old regime when opted OUT of 115BAC."""
        form16 = Form16PartB(opting_out_115bac=True)
        data = Form16Data(
            part_a=Form16PartA(),
            part_b=form16,
            annexure=Form16Annexure(),
        )
        assert data.regime == Regime.OLD

    def test_effective_salary(self):
        """Effective salary property."""
        form16 = Form16PartB(
            income_under_head_salaries=Decimal("1796602"),
        )
        data = Form16Data(
            part_a=Form16PartA(),
            part_b=form16,
            annexure=Form16Annexure(),
        )
        assert data.effective_salary == Decimal("1796602")

    def test_section10_total(self):
        """Section 10 exemptions total computed correctly."""
        exemptions = Section10Exemptions(
            hra_1013A=Decimal("100000"),
            travel_concession_105=Decimal("50000"),
            gratuity_1010=Decimal("200000"),
        )
        assert exemptions.total == Decimal("350000")

    def test_chapter_vi_total(self):
        """Chapter VI-A deductions total."""
        d = ChapterVIADeductions(
            sec80c=Decimal("150000"),
            sec80ccd2=Decimal("47869"),
            sec80d=Decimal("25000"),
        )
        assert d.total == Decimal("222869")


class TestAISModels:
    """AIS domain model computed properties."""

    def test_total_non_salary_tds(self):
        """Non-salary TDS total."""
        from src.models.ais import AISTDSEntry
        ais = AISData(
            other_tds=[
                AISTDSEntry(tds_deducted=Decimal("5000")),
                AISTDSEntry(tds_deducted=Decimal("3000")),
            ]
        )
        assert ais.total_non_salary_tds == Decimal("8000")

    def test_all_interest_income(self):
        """Combined savings + term deposit interest."""
        from src.models.ais import AISSavingsInterest, AISTermDepositInterest
        ais = AISData(
            savings_interest=[
                AISSavingsInterest(interest_amount=Decimal("757")),
            ],
            term_deposit_interest=[
                AISTermDepositInterest(interest_amount=Decimal("15000")),
            ],
        )
        assert ais.all_interest_income == Decimal("15757")


class TestTaxModels:
    """Unified tax model validation."""

    def test_cg_sale_entry_period_mapping(self):
        """Date period mapping for Schedule CG Section F."""
        entry = CGSaleEntry(date=date(2025, 5, 1))  # May
        assert entry.period == "Upto15Of6"

        entry2 = CGSaleEntry(date=date(2025, 7, 1))  # July
        assert entry2.period == "Upto15Of9"

        entry3 = CGSaleEntry(date=date(2025, 10, 1))  # October
        assert entry3.period == "Up16Of9To15Of12"

        entry4 = CGSaleEntry(date=date(2026, 1, 15))  # January
        assert entry4.period == "Up16Of12To15Of3"

        entry5 = CGSaleEntry(date=date(2026, 3, 20))  # Late March
        assert entry5.period == "Up16Of3To31Of3"

    def test_cg_date_ranges_initialized_empty(self):
        """Date ranges default to zero for all periods."""
        ranges = CGDateRanges()
        assert ranges.ltcg_12_5pct["Upto15Of6"] == Decimal("0")
        assert len(ranges.ltcg_12_5pct) == 5

    def test_cg_date_ranges_validate_sums(self):
        """Validate sums function checks totals."""
        ranges = CGDateRanges()
        ranges.ltcg_12_5pct["Upto15Of6"] = Decimal("1000")
        ranges.stcg_app_rate["Upto15Of9"] = Decimal("500")

        assert ranges.validate_sums(Decimal("1000"), Decimal("500")) is True
        assert ranges.validate_sums(Decimal("2000"), Decimal("500")) is False

    def test_classified_cg_totals(self):
        """Classified CG computed totals."""
        from datetime import date as dt_date
        data = ClassifiedCGData(
            cg_a2_stcg_111a=[
                CGSaleEntry(date=dt_date(2025, 6, 1), gain=Decimal("500")),
                CGSaleEntry(date=dt_date(2025, 7, 1), gain=Decimal("300")),
            ],
            cg_a5_stcg_app_rate=[
                CGSaleEntry(date=dt_date(2025, 8, 1), gain=Decimal("100")),
            ],
            schedule_112a=[
                CGSaleEntry(date=dt_date(2025, 4, 1), gain=Decimal("2596")),
            ],
        )
        # total_stcg = a2 (500+300) + a5 (100) = 900
        assert data.total_stcg == Decimal("900")
        assert data.total_ltcg == Decimal("2596")
        assert data.total_cg == Decimal("3496")

    def test_regime_result_savings(self):
        """Regime result computes savings correctly."""
        result = RegimeResult(
            old_tax=Decimal("100000"),
            new_tax=Decimal("80000"),
            recommended=Regime.NEW,
            savings=Decimal("20000"),
        )
        assert result.savings == Decimal("20000")
        assert result.recommended == Regime.NEW

    def test_user_answers_defaults(self):
        """UserAnswers defaults are sane."""
        answers = UserAnswers()
        assert answers.pays_rent is False
        assert answers.rent_per_month == Decimal("0")
        assert answers.has_health_insurance is False


class TestUserModel:
    """User registration model validation."""

    def test_valid_pan_accepted(self):
        """Valid PAN format passes validation."""
        user = UserCreate(
            email="test@example.com",
            password="securepass123",
            pan="ABCDE1234F",
            name="Test User",
        )
        assert user.pan == "ABCDE1234F"

    def test_invalid_pan_rejected(self):
        """Invalid PAN format raises validation error."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="securepass123",
                pan="INVALID",
                name="Test User",
            )

    def test_pan_lowercase_converted(self):
        """PAN is uppercase-d on validation."""
        user = UserCreate(
            email="test@example.com",
            password="securepass123",
            pan="abcde1234f",
            name="Test User",
        )
        assert user.pan == "ABCDE1234F"

    def test_invalid_email_rejected(self):
        """Invalid email raises validation error."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                password="securepass123",
                pan="ABCDE1234F",
                name="Test User",
            )

    def test_short_password_rejected(self):
        """Password < 8 chars raises validation error."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="short",
                pan="ABCDE1234F",
                name="Test User",
            )
