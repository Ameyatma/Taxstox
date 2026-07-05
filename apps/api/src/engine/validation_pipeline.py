"""Composable Compliance Validation Pipeline.

Replaces monolithic validator with pluggable, explainable validation rules.
Every rule is independent, testable, and produces machine+human-readable output.

Traceability: C8.3 (ITR Schema Validation), C8.5 (Regulatory Limit Validation),
             COD-001 (God module validator — refactored)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Protocol


class Severity(str, Enum):
    ERROR = "error"       # Blocks filing
    WARNING = "warning"   # Should be reviewed; does not block
    INFO = "info"         # Informational only


@dataclass(frozen=True)
class ValidationResult:
    """Single validation check result — machine + human readable."""

    rule_id: str                          # e.g., "V-PAN-001"
    rule_name: str                        # e.g., "PAN Format Validation"
    severity: Severity
    passed: bool
    message: str                          # Human-readable
    details: dict = field(default_factory=dict)  # Machine-readable context

    @property
    def is_blocking(self) -> bool:
        return not self.passed and self.severity == Severity.ERROR


@dataclass(frozen=True)
class ValidationReport:
    """Aggregated validation report from a pipeline run."""

    results: tuple[ValidationResult, ...]
    context: str = ""  # e.g., "pre_filing", "itr_generation"

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.severity == Severity.ERROR and not r.passed)

    @property
    def warnings(self) -> int:
        return sum(1 for r in self.results if r.severity == Severity.WARNING and not r.passed)

    @property
    def can_proceed(self) -> bool:
        """Filing can proceed if no blocking errors."""
        return not any(r.is_blocking for r in self.results)

    @property
    def blocking_issues(self) -> list[ValidationResult]:
        return [r for r in self.results if r.is_blocking]

    @property
    def summary(self) -> str:
        parts = [f"{self.passed} passed"]
        if self.errors:
            parts.append(f"{self.errors} error(s)")
        if self.warnings:
            parts.append(f"{self.warnings} warning(s)")
        return ", ".join(parts)


# Validation rule: callable that takes context dict and returns ValidationResult
ValidationRule = Callable[[dict], ValidationResult]


class ValidationPipeline:
    """Composable, ordered validation pipeline.

    Usage:
        pipeline = ValidationPipeline("pre_filing")
        pipeline.add_rule(check_pan_format)
        pipeline.add_rule(check_deduction_limits)
        report = pipeline.run(context={"form16": ..., "ais": ...})
    """

    def __init__(self, context: str = "") -> None:
        self.context = context
        self._rules: list[ValidationRule] = []

    def add_rule(self, rule: ValidationRule) -> None:
        self._rules.append(rule)

    def add_rules(self, rules: list[ValidationRule]) -> None:
        self._rules.extend(rules)

    def run(self, data: dict) -> ValidationReport:
        results = tuple(rule(data) for rule in self._rules)
        return ValidationReport(results=results, context=self.context)


# ── Built-in Validation Rules ────────────────────────────────────────

def check_pan_format(data: dict) -> ValidationResult:
    """V-PAN-001: PAN must match [A-Z]{5}[0-9]{4}[A-Z]."""
    import re
    pan = data.get("pan", "")
    pattern = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
    if not pan:
        return ValidationResult(
            rule_id="V-PAN-001", rule_name="PAN Presence",
            severity=Severity.ERROR, passed=False,
            message="PAN is missing. PAN is mandatory for all ITR forms.",
            details={"pan": ""},
        )
    if not pattern.match(pan.upper()):
        return ValidationResult(
            rule_id="V-PAN-001", rule_name="PAN Format",
            severity=Severity.ERROR, passed=False,
            message=f"PAN '{pan}' does not match valid format (ABCDE1234F).",
            details={"pan": pan},
        )
    return ValidationResult(
        rule_id="V-PAN-001", rule_name="PAN Format",
        severity=Severity.INFO, passed=True,
        message="PAN format is valid.",
        details={"pan": pan[:3] + "**" + pan[-1]},
    )


def check_assessment_year(data: dict) -> ValidationResult:
    """V-AY-001: Assessment year must be valid."""
    ay = data.get("assessment_year", "")
    valid = {"2025-26", "2026-27", "2027-28"}
    if ay not in valid:
        return ValidationResult(
            rule_id="V-AY-001", rule_name="Assessment Year Validity",
            severity=Severity.WARNING, passed=False,
            message=f"Assessment year '{ay}' may be invalid.",
            details={"assessment_year": ay, "valid": list(valid)},
        )
    return ValidationResult(
        rule_id="V-AY-001", rule_name="Assessment Year Validity",
        severity=Severity.INFO, passed=True,
        message=f"Assessment year {ay} is valid.",
    )


def check_deduction_limits(data: dict) -> ValidationResult:
    """V-DED-001: 80C must not exceed ₹1,50,000."""
    from decimal import Decimal
    sec80c = Decimal(str(data.get("sec80c", "0")))
    limit = Decimal("150000")
    if sec80c > limit:
        return ValidationResult(
            rule_id="V-DED-001", rule_name="80C Limit",
            severity=Severity.ERROR, passed=False,
            message=f"80C deduction ₹{sec80c:,.0f} exceeds ₹{limit:,.0f} limit.",
            details={"claimed": str(sec80c), "limit": str(limit), "excess": str(sec80c - limit)},
        )
    return ValidationResult(
        rule_id="V-DED-001", rule_name="80C Limit",
        severity=Severity.INFO, passed=True,
        message=f"80C deduction ₹{sec80c:,.0f} within ₹{limit:,.0f} limit.",
    )


def check_total_income_positive(data: dict) -> ValidationResult:
    """V-INC-001: Total income should be non-negative."""
    from decimal import Decimal
    total = Decimal(str(data.get("total_income", "0")))
    if total < 0:
        return ValidationResult(
            rule_id="V-INC-001", rule_name="Total Income Non-Negative",
            severity=Severity.ERROR, passed=False,
            message=f"Total income is negative (₹{total:,.0f}).",
            details={"total_income": str(total)},
        )
    return ValidationResult(
        rule_id="V-INC-001", rule_name="Total Income Non-Negative",
        severity=Severity.INFO, passed=True,
        message="Total income is non-negative.",
    )
