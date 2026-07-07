"""Unit tests for P1 — Complete Individual Tax Filing."""

from decimal import Decimal


class TestResidentialStatus:
    def test_ror_basic(self):
        from src.engine.residential_status import (
            ResidentialStatusEngine, ResidentialStatus,
        )
        engine = ResidentialStatusEngine()
        result = engine.determine(
            days_in_india_fy=200,
            days_in_india_preceding_4=400,
            days_in_india_preceding_7=500,
        )
        assert result.status == ResidentialStatus.ROR

    def test_non_resident(self):
        from src.engine.residential_status import (
            ResidentialStatusEngine, ResidentialStatus,
        )
        engine = ResidentialStatusEngine()
        result = engine.determine(
            days_in_india_fy=30,
            days_in_india_preceding_4=100,
        )
        assert result.status == ResidentialStatus.NR

    def test_rnor_deemed_resident(self):
        from src.engine.residential_status import (
            ResidentialStatusEngine, ResidentialStatus,
        )
        engine = ResidentialStatusEngine()
        result = engine.determine(
            days_in_india_fy=130,
            days_in_india_preceding_4=200,
            is_citizen_or_pio=True,
            india_income=Decimal("2000000"),
        )
        assert result.status == ResidentialStatus.RNOR

    def test_rnor_not_ordinarily(self):
        from src.engine.residential_status import (
            ResidentialStatusEngine, ResidentialStatus,
        )
        engine = ResidentialStatusEngine()
        result = engine.determine(
            days_in_india_fy=200,
            days_in_india_preceding_4=400,
            days_in_india_preceding_7=800,
            non_resident_in_9_of_10=True,
        )
        assert result.status == ResidentialStatus.RNOR

    def test_182_day_rule_for_high_income_citizen(self):
        from src.engine.residential_status import (
            ResidentialStatusEngine, ResidentialStatus,
        )
        engine = ResidentialStatusEngine()
        result = engine.determine(
            days_in_india_fy=100,
            days_in_india_preceding_4=400,
            is_citizen_or_pio=True,
            india_income=Decimal("2000000"),
        )
        # 100 days < 120 → NR (neither 182-day nor 120-day met)
        assert result.status == ResidentialStatus.NR


class TestProvisionTracer:
    def test_lookup(self):
        from src.engine.provision_tracer import ProvisionTracer
        prov = ProvisionTracer.lookup("87a")
        assert prov is not None
        assert "87A" in prov.section

    def test_trace_computation(self):
        from src.engine.provision_tracer import ProvisionTracer
        tracer = ProvisionTracer()
        traces = tracer.trace({
            "gross_salary": "1000000",
            "std_deduction": "75000",
            "net_tax": "50000",
        })
        assert len(traces) >= 3

    def test_lookup_unknown(self):
        from src.engine.provision_tracer import ProvisionTracer
        assert ProvisionTracer.lookup("nonexistent") is None


class TestComplianceChecker:
    def test_ais_gap_salary(self):
        from src.engine.compliance_checker import ComplianceChecker
        checker = ComplianceChecker()
        report = checker.check_ais_completeness(
            ais_has_salary_tds=True,
            user_has_salary=False,
        )
        assert report.warnings >= 1

    def test_ais_gap_interest(self):
        from src.engine.compliance_checker import ComplianceChecker
        checker = ComplianceChecker()
        report = checker.check_ais_completeness(
            ais_has_interest=Decimal("5000"),
            user_has_interest=Decimal("1000"),
        )
        gaps = [f for f in report.findings if f.finding_id == "AIS-GAP-002"]
        assert len(gaps) == 1

    def test_clean_report(self):
        from src.engine.compliance_checker import ComplianceChecker
        checker = ComplianceChecker()
        report = checker.check_ais_completeness()
        assert report.is_clean

    def test_anomaly_income_drop(self):
        from src.engine.compliance_checker import ComplianceChecker
        checker = ComplianceChecker()
        report = checker.detect_anomalies(
            total_income=Decimal("300000"),
            previous_year_income=Decimal("1000000"),
        )
        assert report.warnings >= 1

    def test_anomaly_no_previous_year(self):
        from src.engine.compliance_checker import ComplianceChecker
        checker = ComplianceChecker()
        report = checker.detect_anomalies(
            total_income=Decimal("500000"),
        )
        assert report.is_clean
