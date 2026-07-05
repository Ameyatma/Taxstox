"""Unit tests for SalaryComputer — income under head 'Salaries'.

Verifies ITD portal-matched salary computation for:
- New Regime (115BAC): standard deduction ₹75K, no S10 exemptions
- Old Regime: standard deduction ₹50K, S10 exemptions (HRA, LTA, child edu)
- Professional tax capping at ₹2,500
- Multi-component salary breakup
- Edge cases: zero salary, negative income floor
"""

from decimal import Decimal

import pytest

from src.engine.salary_computer import SalaryComputer
from tests.factories import make_form16_data


class TestSalaryComputerNewRegime:
    """Salary computation under New Regime (115BAC)."""

    def test_basic_salary_new_regime(self):
        """Simple salary with no perquisites, no exemptions."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("1000000"),
            perquisites=Decimal("0"),
            profits_in_lieu=Decimal("0"),
            std_deduction=Decimal("75000"),
            professional_tax=Decimal("0"),
            regime_new=True,
        )
        result = computer.compute(form16=form16, is_new_regime=True)

        assert result.gross_salary == Decimal("1000000")
        assert result.std_deduction == Decimal("75000")
        assert result.professional_tax == Decimal("0")
        assert result.income_from_salary == Decimal("925000")

    def test_salary_with_perquisites_new_regime(self):
        """Salary with perquisites added to gross."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("1500000"),
            perquisites=Decimal("100000"),
            profits_in_lieu=Decimal("0"),
            std_deduction=Decimal("75000"),
            regime_new=True,
        )
        result = computer.compute(form16=form16, is_new_regime=True)

        assert result.gross_salary == Decimal("1600000")
        assert result.income_from_salary == Decimal("1525000")

    def test_salary_with_professional_tax_new_regime(self):
        """Professional tax deducted but capped at ₹2,500."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("1000000"),
            std_deduction=Decimal("75000"),
            professional_tax=Decimal("3000"),
            regime_new=True,
        )
        result = computer.compute(form16=form16, is_new_regime=True)

        assert result.professional_tax == Decimal("2500")  # Capped
        assert result.income_from_salary == Decimal("922500")

    def test_negative_income_floor_at_zero(self):
        """Income from salary should never go below zero."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("50000"),
            std_deduction=Decimal("75000"),
            regime_new=True,
        )
        result = computer.compute(form16=form16, is_new_regime=True)

        assert result.income_from_salary == Decimal("0")


class TestSalaryComputerOldRegime:
    """Salary computation under Old Regime."""

    def test_basic_salary_old_regime(self):
        """Old regime has lower standard deduction (₹50K)."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("1000000"),
            std_deduction=Decimal("50000"),
            regime_new=False,
        )
        result = computer.compute(form16=form16, is_new_regime=False)

        assert result.std_deduction == Decimal("50000")
        assert result.income_from_salary == Decimal("950000")

    def test_hra_exemption_metro(self):
        """HRA exemption for metro city: min(actual HRA, rent-10% basic, 50% basic)."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("1200000"),
            basic=Decimal("600000"),
            hra_received=Decimal("300000"),
            std_deduction=Decimal("50000"),
            regime_new=False,
        )
        rent_paid = Decimal("25000")  # Monthly
        result = computer.compute(
            form16=form16,
            rent_paid=rent_paid,
            metro_city=True,
            is_new_regime=False,
        )

        # HRA = min(300000, 25000*12 - 10%*600000, 50%*600000)
        # = min(300000, 300000 - 60000, 300000)
        # = min(300000, 240000, 300000)
        # = 240000
        assert result.hra_exemption == Decimal("240000")
        assert result.income_from_salary > Decimal("0")

    def test_hra_exemption_non_metro(self):
        """HRA exemption for non-metro: 40% of basic instead of 50%."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("1200000"),
            basic=Decimal("600000"),
            hra_received=Decimal("300000"),
            std_deduction=Decimal("50000"),
            regime_new=False,
        )
        rent_paid = Decimal("25000")
        result = computer.compute(
            form16=form16,
            rent_paid=rent_paid,
            metro_city=False,
            is_new_regime=False,
        )

        # HRA = min(300000, 300000 - 60000, 40%*600000)
        # = min(300000, 240000, 240000)
        # = 240000
        assert result.hra_exemption == Decimal("240000")

    def test_no_hra_when_not_received(self):
        """HRA exemption should be zero if no HRA component in salary."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("1000000"),
            hra_received=Decimal("0"),
            std_deduction=Decimal("50000"),
            regime_new=False,
        )
        result = computer.compute(
            form16=form16,
            rent_paid=Decimal("25000"),
            metro_city=True,
            is_new_regime=False,
        )

        assert result.hra_exemption == Decimal("0")

    def test_no_hra_when_no_rent_paid(self):
        """HRA exemption should be zero if no rent paid."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("1000000"),
            basic=Decimal("500000"),
            hra_received=Decimal("200000"),
            std_deduction=Decimal("50000"),
            regime_new=False,
        )
        result = computer.compute(
            form16=form16,
            rent_paid=Decimal("0"),
            is_new_regime=False,
        )

        assert result.hra_exemption == Decimal("0")


class TestSalaryComputerEdgeCases:
    """Edge case handling."""

    def test_none_form16_returns_zero(self):
        """No Form 16 should return empty breakdown."""
        computer = SalaryComputer()
        result = computer.compute(form16=None)

        assert result.gross_salary == Decimal("0")
        assert result.income_from_salary == Decimal("0")

    def test_all_zero_inputs(self):
        """All zero inputs should produce zero income."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("0"),
            std_deduction=Decimal("0"),
            regime_new=True,
        )
        result = computer.compute(form16=form16, is_new_regime=True)

        assert result.gross_salary == Decimal("0")
        assert result.income_from_salary == Decimal("0")

    def test_professional_tax_within_limit(self):
        """Professional tax at exactly ₹2,500 should remain unchanged."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("1000000"),
            std_deduction=Decimal("75000"),
            professional_tax=Decimal("2500"),
            regime_new=True,
        )
        result = computer.compute(form16=form16, is_new_regime=True)

        assert result.professional_tax == Decimal("2500")

    def test_child_education_exemption(self):
        """Child education allowance: ₹100/month/child, max 2 children."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("1000000"),
            std_deduction=Decimal("50000"),
            regime_new=False,
        )
        result = computer.compute(
            form16=form16,
            children_count=2,
            is_new_regime=False,
        )

        # ₹100 × 2 children × 12 months = ₹2,400
        assert result.child_edu_exemption == Decimal("2400")

    def test_child_education_capped_at_two(self):
        """Child education exemption capped at 2 children."""
        computer = SalaryComputer()
        form16 = make_form16_data(
            salary=Decimal("1000000"),
            std_deduction=Decimal("50000"),
            regime_new=False,
        )
        result = computer.compute(
            form16=form16,
            children_count=4,
            is_new_regime=False,
        )

        # ₹100 × 2 (capped) × 12 = ₹2,400
        assert result.child_edu_exemption == Decimal("2400")

    def test_to_dict_output(self):
        """Breakdown to_dict produces expected keys."""
        computer = SalaryComputer()
        form16 = make_form16_data(salary=Decimal("1000000"), regime_new=True)
        result = computer.compute(form16=form16, is_new_regime=True)

        d = result.to_dict()
        assert "gross_salary" in d
        assert "std_deduction" in d
        assert "income_from_salary" in d
        assert d["income_from_salary"] == str(result.income_from_salary)
