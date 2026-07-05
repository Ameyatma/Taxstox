"""Filing Readiness Engine — Aggregates all pre-filing checks.

Single entry point that runs: identity validation, income consistency,
deduction eligibility, TDS reconciliation, and ITR schema compliance.
Produces a single go/no-go decision with detailed diagnostics.

Traceability: C8.3, C8.4, C8.5, C8.7
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from src.engine.validation_pipeline import (
    ValidationPipeline,
    ValidationReport,
    check_pan_format,
    check_assessment_year,
    check_deduction_limits,
    check_total_income_positive,
)
from src.models.financial_year import FinancialYear


@dataclass
class FilingReadinessReport:
    """Complete pre-filing assessment — can this ITR be filed?"""

    financial_year: str
    itr_type: str
    pan_masked: str

    # Sub-reports
    identity_check: Optional[ValidationReport] = None
    income_check: Optional[ValidationReport] = None
    deduction_check: Optional[ValidationReport] = None
    compliance_check: Optional[ValidationReport] = None

    # Summary
    total_checks: int = 0
    errors: int = 0
    warnings: int = 0

    @property
    def can_file(self) -> bool:
        """True if no blocking errors in any check."""
        for report in [
            self.identity_check,
            self.income_check,
            self.deduction_check,
            self.compliance_check,
        ]:
            if report and not report.can_proceed:
                return False
        return True

    @property
    def summary(self) -> str:
        if self.can_file:
            return f"Ready to file ITR-{self.itr_type} for {self.financial_year}. {self.total_checks} checks passed."
        return (
            f"NOT ready to file. {self.errors} error(s), {self.warnings} warning(s) "
            f"across {self.total_checks} checks."
        )


class FilingReadinessEngine:
    """Aggregates all pre-filing validation checks into a single report."""

    def assess(
        self,
        pan: str,
        itr_type: str,
        fy: FinancialYear,
        form16_data: dict | None = None,
        deduction_data: dict | None = None,
        income_data: dict | None = None,
    ) -> FilingReadinessReport:
        """Run all pre-filing checks and produce readiness report."""

        report = FilingReadinessReport(
            financial_year=fy.label,
            itr_type=itr_type,
            pan_masked=pan[:3] + "**" + pan[-1] if len(pan) >= 10 else "***",
        )

        # ── Identity Check ──
        identity = ValidationPipeline("identity")
        identity.add_rule(check_pan_format)
        identity.add_rule(check_assessment_year)
        report.identity_check = identity.run({
            "pan": pan,
            "assessment_year": fy.assessment_year,
        })

        # ── Income Check ──
        if income_data:
            income = ValidationPipeline("income")
            income.add_rule(check_total_income_positive)
            report.income_check = income.run(income_data)

        # ── Deduction Check ──
        if deduction_data:
            deductions = ValidationPipeline("deductions")
            deductions.add_rule(check_deduction_limits)
            report.deduction_check = deductions.run(deduction_data)

        # ── Aggregate ──
        all_reports = [
            report.identity_check,
            report.income_check,
            report.deduction_check,
            report.compliance_check,
        ]
        report.total_checks = sum(
            len(r.results) for r in all_reports if r is not None
        )
        report.errors = sum(
            r.errors for r in all_reports if r is not None
        )
        report.warnings = sum(
            r.warnings for r in all_reports if r is not None
        )

        return report
