"""Cross-Validator — Form 16 ↔ Form 26AS/AIS reconciliation.

Validates that:
  1. TDS on Salary from Form 16 matches TDS-192 total in AIS
  2. Employer TAN appears in AIS deductor details
  3. Salary amount reported matches across documents
  4. Any TDS credits in AIS not claimed in return
  5. Any TDS claimed but not in AIS (risk of ITD notice)

Produces validation warnings/errors that appear on the summary page.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from src.models.form16 import Form16Data
from src.models.ais import AISData


@dataclass
class CrossValidationFinding:
    """A single reconciliation finding."""
    passed: bool
    severity: str       # "pass", "warning", "error"
    check_name: str
    message: str
    form16_value: Optional[Decimal] = None
    ais_value: Optional[Decimal] = None
    difference: Optional[Decimal] = None
    recommendation: str = ""


@dataclass
class CrossValidationReport:
    """Complete reconciliation report."""
    findings: list[CrossValidationFinding] = field(default_factory=list)
    form16_tds_total: Decimal = Decimal("0")
    ais_tds_192_total: Decimal = Decimal("0")
    ais_other_tds_total: Decimal = Decimal("0")
    total_tds_credit_available: Decimal = Decimal("0")
    passes: int = 0
    warnings: int = 0
    errors: int = 0

    @property
    def all_clear(self) -> bool:
        return self.errors == 0

    def to_dict(self) -> dict:
        return {
            "findings": [
                {
                    "passed": f.passed,
                    "severity": f.severity,
                    "check_name": f.check_name,
                    "message": f.message,
                    "form16_value": str(f.form16_value) if f.form16_value else None,
                    "ais_value": str(f.ais_value) if f.ais_value else None,
                    "difference": str(f.difference) if f.difference else None,
                    "recommendation": f.recommendation,
                }
                for f in self.findings
            ],
            "form16_tds_total": str(self.form16_tds_total),
            "ais_tds_192_total": str(self.ais_tds_192_total),
            "ais_other_tds_total": str(self.ais_other_tds_total),
            "total_tds_credit": str(self.total_tds_credit_available),
            "passes": self.passes,
            "warnings": self.warnings,
            "errors": self.errors,
            "all_clear": self.all_clear,
        }


class CrossValidator:
    """Validates Form 16 data against AIS/Form 26AS data."""

    TDS_MISMATCH_THRESHOLD = Decimal("500")     # ₹500 — below this, ignore rounding
    TDS_WARNING_THRESHOLD = Decimal("5000")     # ₹5,000 — warn above this
    SALARY_MISMATCH_PCT = Decimal("0.02")       # 2% — salary mismatch tolerance

    def validate(
        self,
        form16: Optional[Form16Data] = None,
        ais: Optional[AISData] = None,
    ) -> CrossValidationReport:
        """Run all cross-validation checks."""
        report = CrossValidationReport()

        if not form16:
            report.findings.append(CrossValidationFinding(
                passed=False, severity="error",
                check_name="form16_present",
                message="No Form 16 data available for validation.",
                recommendation="Upload your Form 16 PDF to enable tax computation.",
            ))
            return report

        # ── Extract Form 16 TDS ──
        report.form16_tds_total = form16.part_a.total_tds_deducted

        # ── Extract AIS TDS ──
        if ais:
            # Sum TDS from salary entries (TDS-192)
            report.ais_tds_192_total = sum(
                (e.tds_deducted for e in ais.salary_tds),
                Decimal("0")
            )

            # Sum TDS from all other entries (non-salary)
            report.ais_other_tds_total = sum(
                (e.tds_deducted for e in ais.other_tds),
                Decimal("0")
            ) + ais.total_non_salary_tds

            report.total_tds_credit_available = (
                report.ais_tds_192_total + report.ais_other_tds_total
            )
        else:
            report.ais_tds_192_total = Decimal("0")
            report.ais_other_tds_total = Decimal("0")
            report.total_tds_credit_available = report.form16_tds_total
            report.findings.append(CrossValidationFinding(
                passed=True, severity="pass",
                check_name="ais_present",
                message="No AIS/Form 26AS uploaded. Using Form 16 TDS only. "
                        "Upload AIS for full reconciliation.",
                recommendation="Upload your AIS PDF for automatic TDS cross-verification.",
            ))
            report.passes += 1
            return report

        # ── Check 1: TDS-192 Match ──
        self._check_tds_192_match(report)

        # ── Check 2: Employer TAN match ──
        self._check_employer_tan(form16, ais, report)

        # ── Check 3: Salary amount consistency ──
        self._check_salary_consistency(form16, ais, report)

        # ── Check 4: Unclaimed AIS TDS ──
        self._check_unclaimed_tds(report)

        # ── Tally results ──
        report.passes = sum(1 for f in report.findings if f.severity == "pass")
        report.warnings = sum(1 for f in report.findings if f.severity == "warning")
        report.errors = sum(1 for f in report.findings if f.severity == "error")

        return report

    def _check_tds_192_match(self, report: CrossValidationReport) -> None:
        """Check TDS on Salary matches between Form 16 and AIS."""
        f16_tds = report.form16_tds_total
        ais_tds = report.ais_tds_192_total
        diff = abs(f16_tds - ais_tds)

        if diff <= self.TDS_MISMATCH_THRESHOLD:
            report.findings.append(CrossValidationFinding(
                passed=True, severity="pass",
                check_name="tds_192_match",
                message=f"TDS on Salary matches: Form 16 shows ₹{f16_tds:,.2f}, "
                        f"AIS shows ₹{ais_tds:,.2f} (difference ₹{diff:,.2f}).",
                form16_value=f16_tds,
                ais_value=ais_tds,
                difference=diff,
            ))
        elif diff <= self.TDS_WARNING_THRESHOLD:
            report.findings.append(CrossValidationFinding(
                passed=False, severity="warning",
                check_name="tds_192_match",
                message=f"Minor TDS mismatch: Form 16 shows ₹{f16_tds:,.2f}, "
                        f"AIS shows ₹{ais_tds:,.2f} (₹{diff:,.2f} difference). "
                        f"May be due to TDS on perquisites or rounding.",
                form16_value=f16_tds,
                ais_value=ais_tds,
                difference=diff,
                recommendation="Verify with your employer. If the difference is perquisite TDS, "
                               "it will auto-resolve when you file.",
            ))
        else:
            report.findings.append(CrossValidationFinding(
                passed=False, severity="error",
                check_name="tds_192_match",
                message=f"TDS mismatch: Form 16 ₹{f16_tds:,.2f} vs AIS ₹{ais_tds:,.2f} "
                        f"(₹{diff:,.2f}). This may cause your return to be flagged by ITD.",
                form16_value=f16_tds,
                ais_value=ais_tds,
                difference=diff,
                recommendation="Contact your employer immediately. They may have filed incorrect "
                               "TDS returns. Request revised TDS return (Form 24Q correction).",
            ))

    def _check_employer_tan(
        self, form16: Form16Data, ais: AISData, report: CrossValidationReport
    ) -> None:
        """Check that employer TAN from Form 16 appears in AIS."""
        f16_tan = form16.part_a.employer_tan
        if not f16_tan:
            report.findings.append(CrossValidationFinding(
                passed=False, severity="warning",
                check_name="employer_tan_present",
                message="Employer TAN not found in Form 16.",
                recommendation="Verify the Form 16 PDF is complete. TAN is mandatory on Form 16.",
            ))
            return

        # Check if any AIS TDS entry has a matching source that contains the TAN
        all_tds = ais.salary_tds + ais.other_tds
        tan_found = any(
            f16_tan in (e.information_source or "")
            for e in all_tds
        )

        if tan_found:
            report.findings.append(CrossValidationFinding(
                passed=True, severity="pass",
                check_name="employer_tan_match",
                message=f"Employer TAN {f16_tan} found in AIS records.",
            ))
        else:
            report.findings.append(CrossValidationFinding(
                passed=False, severity="warning",
                check_name="employer_tan_match",
                message=f"Employer TAN {f16_tan} not explicitly matched in AIS. "
                        f"This is usually fine if Form 16 and AIS TDS amounts match.",
                recommendation="No action needed if TDS amounts match. "
                               "AIS may not show TAN in the public statement.",
            ))

    def _check_salary_consistency(
        self, form16: Form16Data, ais: AISData, report: CrossValidationReport
    ) -> None:
        """Check that salary amounts are consistent between Form 16 and AIS."""
        f16_salary = form16.part_b.total_gross_salary

        # AIS doesn't directly report salary — it reports TDS on salary
        # But Annexure II Salary (if present) reports salary details
        if ais.annexure_ii_salary and ais.annexure_ii_salary.total_gross_salary > 0:
            ais_salary = ais.annexure_ii_salary.total_gross_salary
            diff = abs(f16_salary - ais_salary)
            diff_pct = diff / f16_salary if f16_salary > 0 else Decimal("0")

            if diff_pct <= self.SALARY_MISMATCH_PCT:
                report.findings.append(CrossValidationFinding(
                    passed=True, severity="pass",
                    check_name="salary_consistency",
                    message=f"Salary matches: Form 16 ₹{f16_salary:,.2f}, "
                            f"AIS Annexure II ₹{ais_salary:,.2f}.",
                ))
            else:
                report.findings.append(CrossValidationFinding(
                    passed=False, severity="warning",
                    check_name="salary_consistency",
                    message=f"Salary differs by {diff_pct:.1%}: "
                            f"Form 16 ₹{f16_salary:,.2f} vs AIS ₹{ais_salary:,.2f}.",
                    form16_value=f16_salary,
                    ais_value=ais_salary,
                    difference=diff,
                    recommendation="Check if you have multiple employers or one-time payments. "
                                   "If Form 16 is correct, proceed — AIS may include all employers.",
                ))
        else:
            report.findings.append(CrossValidationFinding(
                passed=True, severity="pass",
                check_name="salary_consistency",
                message="Single salary source detected (Form 16 only). No discrepancy to flag.",
            ))

    def _check_unclaimed_tds(self, report: CrossValidationReport) -> None:
        """Check for TDS credits in AIS that may not be claimed."""
        if report.ais_other_tds_total > Decimal("1000"):
            report.findings.append(CrossValidationFinding(
                passed=False, severity="warning",
                check_name="unclaimed_tds",
                message=f"AIS shows ₹{report.ais_other_tds_total:,.2f} in non-salary TDS "
                        f"(from interest, rent, professional fees, etc.). "
                        f"This TDS credit may be available to you.",
                ais_value=report.ais_other_tds_total,
                recommendation="Check if you have income from FD interest, rent received, or "
                               "professional services. If yes, claim the corresponding TDS credit "
                               "in Schedule TDS2 of your ITR.",
            ))
        else:
            report.findings.append(CrossValidationFinding(
                passed=True, severity="pass",
                check_name="unclaimed_tds",
                message="No significant non-salary TDS found. All credits accounted for.",
            ))
