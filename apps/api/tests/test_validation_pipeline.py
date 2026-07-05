"""Unit tests for Compliance Validation Pipeline."""

from src.engine.validation_pipeline import (
    ValidationPipeline,
    ValidationReport,
    ValidationResult,
    Severity,
    check_pan_format,
    check_deduction_limits,
    check_total_income_positive,
)


class TestValidationResult:
    def test_passing_result(self):
        r = ValidationResult(
            rule_id="V-TEST", rule_name="Test",
            severity=Severity.INFO, passed=True, message="OK",
        )
        assert r.is_blocking is False

    def test_blocking_error(self):
        r = ValidationResult(
            rule_id="V-TEST", rule_name="Test",
            severity=Severity.ERROR, passed=False, message="Fail",
        )
        assert r.is_blocking is True

    def test_warning_not_blocking(self):
        r = ValidationResult(
            rule_id="V-TEST", rule_name="Test",
            severity=Severity.WARNING, passed=False, message="Warn",
        )
        assert r.is_blocking is False


class TestValidationPipeline:
    def test_pipeline_runs_rules(self):
        pipeline = ValidationPipeline("test")
        pipeline.add_rule(check_pan_format)
        report = pipeline.run({"pan": "ABCDE1234F"})
        assert report.passed == 1

    def test_pipeline_catches_errors(self):
        pipeline = ValidationPipeline("test")
        pipeline.add_rule(check_pan_format)
        report = pipeline.run({"pan": "INVALID"})
        assert report.errors >= 1

    def test_can_proceed_with_no_blocking(self):
        results = (
            ValidationResult("V-1", "Test", Severity.WARNING, False, "warn"),
            ValidationResult("V-2", "Test", Severity.INFO, True, "info"),
        )
        report = ValidationReport(results=results, context="test")
        assert report.can_proceed is True

    def test_cannot_proceed_with_error(self):
        results = (
            ValidationResult("V-1", "Test", Severity.ERROR, False, "error"),
        )
        report = ValidationReport(results=results, context="test")
        assert report.can_proceed is False


class TestBuiltinRules:
    def test_pan_valid(self):
        r = check_pan_format({"pan": "ABCDE1234F"})
        assert r.passed

    def test_pan_missing(self):
        r = check_pan_format({"pan": ""})
        assert not r.passed
        assert r.severity == Severity.ERROR

    def test_deduction_within_limit(self):
        r = check_deduction_limits({"sec80c": "100000"})
        assert r.passed

    def test_deduction_exceeds_limit(self):
        r = check_deduction_limits({"sec80c": "200000"})
        assert not r.passed

    def test_negative_income(self):
        r = check_total_income_positive({"total_income": "-5000"})
        assert not r.passed
