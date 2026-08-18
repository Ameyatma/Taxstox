"""PR3 Tests — Architecture Remediation.

Verifies findings 3.1–3.9:
  3.1  Hardcoded AY/FY removed from builders (FinancialYear flows through)
  3.2  salary_computer.py deduction/exemption constants from RuleRepository
  3.3  deductions_computer.py limits from RuleRepository
  3.4  classifier.py CG rates from RuleRepository
  3.5  ITR-2 PartB-TTI special-rate key fix
  3.6  ITR-1 PartB-TI house-property/deductions key fix
  3.7  validator.py deduction limits from RuleRepository
  3.8  TenantContextMiddleware registration
  3.9  Shared to_decimal() utility (parsers deduplicated)
"""

import os
from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest

from src.builders.itr1 import ITR1Builder
from src.builders.itr_json_builder import ITRJSONBuilder
from src.builders.validator import ITRValidator
from src.engine.classifier import ClassificationEngine
from src.engine.deductions_computer import DeductionsComputer
from src.engine.regime_optimizer_v2 import RegimeOptimizerV2
from src.engine.rules.config import FY2024_25, FY2025_26, rule_repository
from src.engine.salary_computer import SalaryComputer
from src.models.financial_year import FinancialYear
from src.models.form16 import Regime
from src.models.tax import (
    CGSaleEntry,
    ClassifiedCGData,
    RegimeResult,
    UnifiedTaxData,
)
from src.utils.decimal_utils import to_decimal
from tests.factories import make_form16_data, make_user_answers


# ── 3.1: Hardcoded AY/FY removed from builders ──────────────────────

class TestPR3AssessmentYear:
    """Builders derive AssessmentYear from FinancialYear, not a hardcoded constant."""

    def test_itr2_builder_assessment_year_from_fy(self):
        builder = ITRJSONBuilder(FinancialYear.from_string("FY2024-25"))
        out = builder.build(UnifiedTaxData())
        assert out["PartA_GeneralInfo"]["AssessmentYear"] == "2025-26"

    def test_itr1_builder_assessment_year_from_fy(self):
        builder = ITR1Builder(FinancialYear.from_string("FY2024-25"))
        out = builder.build(UnifiedTaxData())
        assert out["PartA_GeneralInfo"]["AssessmentYear"] == "2025-26"

    def test_builder_defaults_to_fy2025_26(self):
        assert ITRJSONBuilder()._ay == "2026-27"
        assert ITR1Builder()._ay == "2026-27"

    def test_builder_no_module_level_ay_constant(self):
        """3.1: No module-level AY/FY string constants remain in the builders."""
        import src.builders.itr_json_builder as itr2_mod
        import src.builders.itr1 as itr1_mod

        for mod in (itr2_mod, itr1_mod):
            for name in ("AY", "FY"):
                assert not hasattr(mod, name), f"{mod.__name__} still defines {name}"


# ── 3.2: salary_computer.py uses RuleRepository ─────────────────────

class TestPR3SalaryComputer:
    """Salary exemptions/deductions come from TaxYearConfig, not hardcoded values."""

    def test_std_deduction_new_regime_from_config(self):
        config = rule_repository.get(FY2025_26)
        form16 = make_form16_data(salary=Decimal("1000000"), regime_new=True)
        result = SalaryComputer().compute(form16=form16, is_new_regime=True)
        assert result.std_deduction == config.new_regime.std_deduction
        assert result.std_deduction == Decimal("75000")

    def test_std_deduction_old_regime_from_config(self):
        config = rule_repository.get(FY2025_26)
        form16 = make_form16_data(salary=Decimal("1000000"), regime_new=False)
        result = SalaryComputer().compute(form16=form16, is_new_regime=False)
        assert result.std_deduction == config.old_regime.std_deduction
        assert result.std_deduction == Decimal("50000")

    def test_professional_tax_capped_from_config(self):
        config = rule_repository.get(FY2025_26)
        form16 = make_form16_data(salary=Decimal("1000000"), professional_tax=Decimal("4000"))
        result = SalaryComputer().compute(form16=form16, is_new_regime=True)
        assert result.professional_tax == config.max_professional_tax
        assert result.professional_tax == Decimal("2500")

    def test_hra_metro_and_non_metro_from_config(self):
        config = rule_repository.get(FY2025_26)
        form16 = make_form16_data(
            salary=Decimal("1000000"), basic=Decimal("100000"),
            hra_received=Decimal("50000"), regime_new=False,
        )
        computer = SalaryComputer()
        metro = computer.compute(
            form16=form16, rent_paid=Decimal("20000"), metro_city=True, is_new_regime=False,
        )
        non_metro = computer.compute(
            form16=form16, rent_paid=Decimal("20000"), metro_city=False, is_new_regime=False,
        )
        # 50% of basic (metro) vs 40% of basic (non-metro)
        assert metro.hra_exemption == Decimal("100000") * config.hra_metro_pct
        assert non_metro.hra_exemption == Decimal("100000") * config.hra_non_metro_pct
        assert metro.hra_exemption == Decimal("50000")
        assert non_metro.hra_exemption == Decimal("40000")

    def test_backward_compat_without_financial_year(self):
        """compute() without financial_year still works (defaults FY2025-26)."""
        form16 = make_form16_data(salary=Decimal("1000000"), regime_new=True)
        result = SalaryComputer().compute(form16=form16, is_new_regime=True)
        assert result.std_deduction == Decimal("75000")
        assert result.income_from_salary == Decimal("925000")


# ── 3.3: deductions_computer.py uses RuleRepository ─────────────────

class TestPR3DeductionsComputer:
    """Deduction limits come from TaxYearConfig, not hardcoded constants."""

    def test_80c_capped_from_config(self):
        config = rule_repository.get(FY2025_26)
        form16 = make_form16_data(salary=Decimal("1000000"), sec80c=Decimal("200000"))
        result = DeductionsComputer().compute(form16=form16, is_new_regime=False)
        assert result.sec80c == config.get_deduction_limit("80C", "old")
        assert result.sec80c == Decimal("150000")

    def test_80ccd1b_capped_from_config(self):
        config = rule_repository.get(FY2025_26)
        form16 = make_form16_data(salary=Decimal("1000000"))
        answers = make_user_answers(
            has_additional_80c=True, additional_80c={"nps_own": Decimal("60000")},
        )
        result = DeductionsComputer().compute(form16=form16, answers=answers, is_new_regime=False)
        assert result.sec80ccd1b == config.get_deduction_limit("80CCD(1B)")
        assert result.sec80ccd1b == Decimal("50000")

    def test_80d_self_and_non_senior_parents_from_config(self):
        config = rule_repository.get(FY2025_26)
        form16 = make_form16_data(salary=Decimal("1000000"))
        answers = make_user_answers(
            has_health_insurance=True,
            health_premium_self=Decimal("30000"),
            health_premium_parents=Decimal("30000"),
            parents_senior_citizen=False,
        )
        result = DeductionsComputer().compute(form16=form16, answers=answers, is_new_regime=False)
        # 30,000 self → 25,000; 30,000 parents (non-senior) → 25,000
        assert result.sec80d == Decimal("50000")
        assert result.sec80d == config.get_deduction_limit("80D_SELF") + config.get_deduction_limit("80D_PARENTS")

    def test_80d_senior_parents_from_config(self):
        form16 = make_form16_data(salary=Decimal("1000000"))
        answers = make_user_answers(
            has_health_insurance=True,
            health_premium_self=Decimal("30000"),
            health_premium_parents=Decimal("40000"),
            parents_senior_citizen=True,
        )
        result = DeductionsComputer().compute(form16=form16, answers=answers, is_new_regime=False)
        # 30,000 self → 25,000; 40,000 senior parents → 40,000 (cap 50,000)
        assert result.sec80d == Decimal("65000")

    def test_backward_compat_without_financial_year(self):
        form16 = make_form16_data(salary=Decimal("1000000"), sec80c=Decimal("200000"))
        result = DeductionsComputer().compute(form16=form16, is_new_regime=False)
        assert result.sec80c == Decimal("150000")


# ── 3.4: classifier.py uses RuleRepository ──────────────────────────

class TestPR3Classifier:
    """Capital-gains rates and exemption come from TaxYearConfig."""

    def test_stcg_rate_from_config(self):
        config = rule_repository.get(FY2025_26)
        engine = ClassificationEngine()
        stcg = CGSaleEntry(
            date=date(2025, 8, 15), gain=Decimal("500"),
            tax_rate="15%", itr_schedule="ScheduleCG_A2",
        )
        data = ClassifiedCGData(cg_a2_stcg_111a=[stcg])
        summary = engine.get_tax_summary(data, FY2025_26)
        assert summary["stcg_15pct_tax"] == Decimal("500") * config.equity_stcg_rate
        assert summary["stcg_15pct_tax"] == Decimal("75.00")

    def test_ltcg_112a_rate_from_config(self):
        config = rule_repository.get(FY2025_26)
        engine = ClassificationEngine()
        ltcg = CGSaleEntry(
            date=date(2025, 4, 21), gain=Decimal("200000"), term="Long",
            itr_schedule="Schedule112A", qualifies_for_125k_exemption=True,
        )
        data = ClassifiedCGData(schedule_112a=[ltcg])
        summary = engine.get_tax_summary(data, FY2025_26)
        assert summary["ltcg_112a_taxable"] == Decimal("75000")
        assert summary["ltcg_112a_tax"] == Decimal("75000") * config.equity_ltcg_rate
        assert summary["ltcg_112a_tax"] == Decimal("9375.00")

    def test_112a_exemption_from_config(self):
        config = rule_repository.get(FY2025_26)
        engine = ClassificationEngine()
        ltcg = CGSaleEntry(
            date=date(2025, 4, 21), gain=Decimal("200000"),
            itr_schedule="Schedule112A", qualifies_for_125k_exemption=True,
        )
        data = ClassifiedCGData(schedule_112a=[ltcg])
        engine.apply_112a_exemption(data, FY2025_26)
        assert data.schedule_112a[0].gain_after_exemption == (
            Decimal("200000") - config.ltcg_112a_exemption
        )
        assert data.schedule_112a[0].gain_after_exemption == Decimal("75000")


# ── 3.5 / 3.6: Builder key fixes ────────────────────────────────────

class TestPR3BuilderKeys:
    """ITR builders read the keys the optimizer actually emits."""

    def test_itr2_partb_tti_special_rates_keys(self):
        """3.5: TaxOnSpecialRates sums tax_112a + tax_stcg_15pct + tax_ltcg_other."""
        data = UnifiedTaxData(
            recommended_regime=Regime.NEW,
            regime_result=RegimeResult(new_breakdown={
                "total_income": "1500000",
                "tax_slab": "100000",
                "tax_112a": "12500",
                "tax_stcg_15pct": "7500",
                "tax_ltcg_other": "2500",
                "rebate_87a": "0",
                "cess": "4000",
                "net_tax": "126500",
            }),
        )
        tti = ITRJSONBuilder()._build_partb_tti(data)
        assert tti["TaxOnSpecialRates"] == "22500"          # 12500 + 7500 + 2500
        assert tti["TotalTaxBeforeRebate"] == "122500"      # 100000 + 22500

    def test_itr1_partb_ti_home_loan_negated(self):
        """3.6: House property loss is negated; deductions use deductions_total."""
        data = UnifiedTaxData(
            recommended_regime=Regime.NEW,
            regime_result=RegimeResult(new_breakdown={
                "income_salary": "1000000",
                "home_loan_loss": "200000",
                "income_interest": "10000",
                "deductions_total": "150000",
            }),
        )
        ti = ITR1Builder()._build_partb_ti(data)
        assert ti["HouseProperty"] == "-200000"
        assert ti["GrossTotalIncome"] == "810000"           # 1000000 - 200000 + 10000
        assert ti["TotalDeductions"] == "150000"
        assert ti["TotalIncome"] == "660000"


# ── 3.7: validator.py uses RuleRepository ───────────────────────────

class TestPR3Validator:
    """Validator deduction limits come from RuleRepository."""

    def test_80c_limit_from_config(self):
        validator = ITRValidator()
        over = validator._check_80c_limits(
            {"ScheduleVIA": {"Section80C": {"Total80C": "200000"}}}
        )
        under = validator._check_80c_limits(
            {"ScheduleVIA": {"Section80C": {"Total80C": "100000"}}}
        )
        assert over.check_name == "80c_limits"
        assert over.passed is False
        assert under.passed is True

    def test_80d_non_senior_parents_limit_from_config(self):
        """Non-senior parents premium over ₹25,000 is now flagged (correctness fix)."""
        validator = ITRValidator()
        r = validator._check_80d_limits({"ScheduleVIA": {"Section80D": {
            "HealthPremiumSelf": "20000",
            "HealthPremiumParents": "30000",
            "ParentsSeniorCitizen": "N",
        }}})
        assert r.passed is False

    def test_80d_senior_parents_limit_from_config(self):
        validator = ITRValidator()
        r = validator._check_80d_limits({"ScheduleVIA": {"Section80D": {
            "HealthPremiumSelf": "20000",
            "HealthPremiumParents": "40000",
            "ParentsSeniorCitizen": "Y",
        }}})
        assert r.passed is True

    def test_80ccd1b_limit_from_config(self):
        validator = ITRValidator()
        r = validator._check_80ccd_limits(
            {"ScheduleVIA": {"Section80CCD1B": {"Amount": "60000"}}}
        )
        assert r.check_name == "80ccd_limits"
        assert r.passed is False

    def test_112a_limit_from_config(self):
        validator = ITRValidator()
        r = validator._check_112a_exemption(
            {"Schedule112A": {"TotalDeduction": "130000"}}
        )
        assert r.passed is False

    def test_home_loan_interest_limit_from_config(self):
        validator = ITRValidator()
        r = validator._check_home_loan_interest_limit(
            {"ScheduleHP": {"TotalInterestPayable": "250000"}}
        )
        assert r.passed is False


# ── 3.8: TenantContextMiddleware registration ──────────────────────

def _make_request(headers):
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": headers,
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


class TestPR3TenantMiddleware:
    """TenantContextMiddleware is registered and resolves tenant context."""

    @pytest.mark.skipif(
        not os.environ.get("TAXSTOX_JWT_SECRET"),
        reason="TAXSTOX_JWT_SECRET not configured",
    )
    def test_tenant_middleware_registered(self):
        from src.main import app
        from src.middleware.tenant_context import TenantContextMiddleware

        classes = [m.cls for m in app.user_middleware]
        assert TenantContextMiddleware in classes

    def test_tenant_middleware_resolves_header(self):
        from src.middleware.tenant_context import TenantContextMiddleware

        tenant_uuid = "123e4567-e89b-12d3-a456-426614174000"
        middleware = TenantContextMiddleware(app=None)
        req = _make_request([(b"x-tenant-id", tenant_uuid.encode())])
        assert middleware._resolve_tenant(req) == UUID(tenant_uuid)

    @pytest.mark.skipif(
        not os.environ.get("TAXSTOX_JWT_SECRET"),
        reason="TAXSTOX_JWT_SECRET not configured",
    )
    def test_tenant_middleware_no_claims_returns_none(self):
        from src.auth.jwt import _current_claims
        from src.middleware.tenant_context import TenantContextMiddleware

        _current_claims.set({})
        middleware = TenantContextMiddleware(app=None)
        assert middleware._resolve_tenant(_make_request([])) is None


# ── 3.9: Shared to_decimal() utility ────────────────────────────────

class TestPR3DecimalUtility:
    """Exactly one shared to_decimal() preserves parser edge cases."""

    def test_to_decimal_edge_cases(self):
        assert to_decimal(None) == Decimal("0")
        assert to_decimal("") == Decimal("0")
        assert to_decimal("   ") == Decimal("0")
        assert to_decimal("1,23,456.78") == Decimal("123456.78")
        assert to_decimal("1 234.56") == Decimal("1234.56")
        assert to_decimal("-1,234.50") == Decimal("-1234.50")
        assert to_decimal("0") == Decimal("0")
        assert to_decimal("abc") == Decimal("0")

    def test_parsers_share_one_to_decimal(self):
        import src.parsers.ais_parser as ais
        import src.parsers.form16_parser as f16
        import src.parsers.form26as_parser as f26
        import src.utils.decimal_utils as du

        # No local duplicates remain
        assert not hasattr(ais, "_to_decimal")
        assert not hasattr(f16.Form16Parser, "_to_decimal")
        assert not hasattr(f26.Form26ASParser, "_to_decimal")

        # All three parsers point at the single shared implementation
        assert ais.to_decimal is du.to_decimal
        assert f16.to_decimal is du.to_decimal
        assert f26.to_decimal is du.to_decimal


# ── Financial-year propagation through the optimizer ────────────────

class TestPR3FinancialYearPropagation:
    """financial_year flows from optimizer into sub-computers and breakdown."""

    def test_optimizer_propagates_fy_to_breakdown(self):
        optimizer = RegimeOptimizerV2()
        form16 = make_form16_data(salary=Decimal("1500000"), regime_new=True)
        result = optimizer.optimize(
            form16=form16,
            classified_cg=ClassifiedCGData(),
            answers=make_user_answers(),
            financial_year=FY2024_25,
        )
        assert result.new_breakdown["financial_year"] == "FY2024-25"

    def test_optimizer_fy_changes_tax(self):
        """FY2024-25 new-regime slabs differ from FY2025-26 → different tax."""
        optimizer = RegimeOptimizerV2()
        form16 = make_form16_data(salary=Decimal("1500000"), regime_new=True)
        args = dict(form16=form16, classified_cg=ClassifiedCGData(), answers=make_user_answers())
        fy2425 = optimizer.optimize(**args, financial_year=FY2024_25)
        fy2526 = optimizer.optimize(**args, financial_year=FY2025_26)
        assert fy2425.new_tax != fy2526.new_tax
        # At ₹14.25L taxable, FY24-25 (20% marginal) > FY25-26 (15% marginal)
        assert fy2425.new_tax > fy2526.new_tax
