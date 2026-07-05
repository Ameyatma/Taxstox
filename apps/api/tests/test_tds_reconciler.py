"""Unit tests for TDS Reconciliation Engine."""

from decimal import Decimal

from src.engine.tds_reconciler import TDSReconciler


class TestTDSReconciler:
    def test_empty_inputs(self):
        reconciler = TDSReconciler()
        report = reconciler.reconcile()
        assert report.form16_tds == Decimal("0")
        assert len(report.findings) == 0

    def test_matching_f16_and_ais(self):
        """Form 16 and AIS salary TDS match → clean finding."""
        from tests.factories import make_form16_data, make_ais_data

        form16 = make_form16_data(
            salary=Decimal("1000000"),
            tds_deducted=Decimal("50000"),
        )
        ais = make_ais_data(
            pan="ABCDE1234F",
            savings_interest=Decimal("5000"),
        )
        from src.models.ais import AISTDSEntry
        ais.salary_tds = [
            AISTDSEntry(
                information_code="TDS-192",
                information_source="TEST EMPLOYER",
                tds_deducted=Decimal("50000"),
                tds_deposited=Decimal("50000"),
            )
        ]

        reconciler = TDSReconciler()
        report = reconciler.reconcile(form16=form16, ais=ais)

        matches = [f for f in report.findings if f.severity == "match"]
        assert len(matches) >= 1

    def test_mismatched_f16_and_ais(self):
        """Form 16 and AIS TDS mismatch → error finding."""
        from tests.factories import make_form16_data, make_ais_data

        form16 = make_form16_data(
            salary=Decimal("1000000"),
            tds_deducted=Decimal("50000"),
        )
        ais = make_ais_data(pan="ABCDE1234F")
        from src.models.ais import AISTDSEntry
        ais.salary_tds = [
            AISTDSEntry(
                information_code="TDS-192",
                tds_deducted=Decimal("30000"),  # Different!
            )
        ]

        reconciler = TDSReconciler()
        report = reconciler.reconcile(form16=form16, ais=ais)

        errors = [f for f in report.findings if f.severity == "error"]
        assert len(errors) >= 1

    def test_non_salary_tds_flag(self):
        """Non-salary TDS generates warning for missed credits."""
        from tests.factories import make_ais_data
        from src.models.ais import AISTDSEntry

        ais = make_ais_data(pan="ABCDE1234F")
        ais.other_tds = [
            AISTDSEntry(
                information_code="TDS-194A",
                information_source="TEST BANK",
                tds_deducted=Decimal("5000"),
            )
        ]

        reconciler = TDSReconciler()
        report = reconciler.reconcile(ais=ais)

        warnings = [f for f in report.findings if f.severity == "warning"]
        assert len(warnings) >= 1

    def test_reconciliation_report_properties(self):
        reconciler = TDSReconciler()
        report = reconciler.reconcile()
        assert report.is_clean is True
        assert "reconciled" in report.summary.lower()
