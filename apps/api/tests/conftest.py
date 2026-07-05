"""Shared test fixtures for TaxStox backend tests.

All fixtures use factory functions to create deterministic test data.
No real PDFs, no external dependencies, no network calls.
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest

# Ensure backend source is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.factories import (  # noqa: E402
    make_ais_data,
    make_classified_cg_data,
    make_form16_data,
    make_user_answers,
)


@pytest.fixture
def sample_form16_data():
    """Form 16 for a salaried individual, FY2025-26, New Regime, no deductions beyond employer NPS."""
    return make_form16_data(
        salary=Decimal("1871602"),
        perquisites=Decimal("0"),
        profits_in_lieu=Decimal("0"),
        std_deduction=Decimal("75000"),
        professional_tax=Decimal("0"),
        hra_received=Decimal("0"),
        lta_received=Decimal("0"),
        basic=Decimal("932472"),
        special_allowance=Decimal("240424"),
        employer_nps=Decimal("47869"),
        tds_deducted=Decimal("155738"),
        regime_new=True,
    )


@pytest.fixture
def sample_form16_data_old_regime():
    """Form 16 for a salaried individual, FY2025-26, Old Regime, with HRA and 80C."""
    return make_form16_data(
        salary=Decimal("1500000"),
        perquisites=Decimal("0"),
        profits_in_lieu=Decimal("0"),
        std_deduction=Decimal("50000"),
        professional_tax=Decimal("2500"),
        hra_received=Decimal("300000"),
        lta_received=Decimal("50000"),
        basic=Decimal("800000"),
        special_allowance=Decimal("200000"),
        employer_nps=Decimal("0"),
        tds_deducted=Decimal("120000"),
        regime_new=False,
        sec80c=Decimal("150000"),
        sec80d=Decimal("25000"),
    )


@pytest.fixture
def sample_ais_data():
    """AIS with savings interest only."""
    return make_ais_data(
        pan="ABCDE1234F",
        name="TEST TAXPAYER",
        savings_interest=Decimal("757"),
        term_deposit_interest=Decimal("0"),
    )


@pytest.fixture
def sample_ais_data_with_capital_gains():
    """AIS with equity MF sales (long term + short term) and other unit sales."""
    return make_ais_data(
        pan="ABCDE1234F",
        name="TEST TAXPAYER",
        savings_interest=Decimal("757"),
        term_deposit_interest=Decimal("0"),
        equity_mf_sales=[
            {
                "security_name": "Quant ELSS Tax Saver Fund",
                "isin": "INF966L01986",
                "date_of_sale": "2025-04-21",
                "quantity": "19.79",
                "sale_price_per_unit": "383.77",
                "sale_consideration": "7596",
                "cost_of_acquisition": "5000",
                "stt_paid": "0.20",
                "term": "Long",
            },
            {
                "security_name": "SBI Equity Fund",
                "isin": "INF200K01234",
                "date_of_sale": "2025-08-15",
                "quantity": "50",
                "sale_price_per_unit": "120.00",
                "sale_consideration": "6000",
                "cost_of_acquisition": "5500",
                "stt_paid": "0.15",
                "term": "Short",
            },
        ],
        other_unit_sales=[
            {
                "security_name": "TATA Gold ETF",
                "isin": "INF277KA1976",
                "date_of_sale": "2026-02-27",
                "quantity": "5",
                "sale_price": "15.38",
                "sale_consideration": "77",
                "cost_of_acquisition": "76",
                "term": "Short",
            },
        ],
    )


@pytest.fixture
def sample_user_answers():
    """Default user answers — no additional deductions."""
    return make_user_answers()


@pytest.fixture
def sample_user_answers_with_deductions():
    """User answers with rent, health insurance, 80C, and home loan."""
    return make_user_answers(
        pays_rent=True,
        rent_per_month=Decimal("25000"),
        rent_city_metro=True,
        has_health_insurance=True,
        health_premium_self=Decimal("15000"),
        health_premium_parents=Decimal("20000"),
        parents_senior_citizen=False,
        has_additional_80c=True,
        additional_80c={"ppf": Decimal("50000"), "elss": Decimal("30000")},
        has_home_loan=True,
        home_loan_interest=Decimal("180000"),
        home_loan_self_occupied=True,
    )


@pytest.fixture
def sample_classified_cg_data():
    """Pre-classified capital gains data from sample AIS."""
    return make_classified_cg_data()
