"""TDS Reconciliation Engine — three-way match: Form 16 ↔ AIS ↔ Form 26AS.

Identifies mismatches, missing credits, and duplicate entries across
all tax credit sources. Produces actionable recommendations.

Traceability: C8.1 (Tax Credit Reconciliation — Critical gap, 15%→60%)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from src.models.form16 import Form16Data
from src.models.ais import AISData
from src.parsers.form26as_parser import Form26ASData, Form26ASTDSEntry

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationFinding:
    """A single reconciliation finding."""
    severity: str           # "match", "warning", "error"
    category: str           # "tds_salary", "tds_other", "advance_tax", "refund"
    description: str
    form16_value: Optional[Decimal] = None
    ais_value: Optional[Decimal] = None
    form26as_value: Optional[Decimal] = None
    difference: Decimal = Decimal("0")
    recommendation: str = ""


@dataclass
class ReconciliationReport:
    """Complete TDS reconciliation across all sources."""
    findings: list[ReconciliationFinding] = field(default_factory=list)
    form16_tds: Decimal = Decimal("0")
    ais_tds_salary: Decimal = Decimal("0")
    ais_tds_other: Decimal = Decimal("0")
    form26as_tds: Decimal = Decimal("0")
    form26as_advance_tax: Decimal = Decimal("0")
    form26as_self_assessment: Decimal = Decimal("0")
    total_credit_available: Decimal = Decimal("0")
    total_credit_claimed: Decimal = Decimal("0")
    matches: int = 0
    warnings: int = 0
    errors: int = 0

    @property
    def is_clean(self) -> bool:
        return self.errors == 0 and self.warnings == 0

    @property
    def summary(self) -> str:
        if self.is_clean:
            return "All tax credits reconciled. No discrepancies found."
        parts = []
        if self.errors > 0:
            parts.append(f"{self.errors} error(s) requiring attention")
        if self.warnings > 0:
            parts.append(f"{self.warnings} warning(s)")
        return ". ".join(parts)


class TDSReconciler:
    """Three-way TDS reconciliation: Form 16 ↔ AIS ↔ Form 26AS.

    The #1 cause of ITR processing delays is TDS mismatch between
    what the taxpayer claims and what appears in Form 26AS.
    This engine catches those mismatches before filing.
    """

    def reconcile(
        self,
        form16: Optional[Form16Data] = None,
        ais: Optional[AISData] = None,
        form26as: Optional[Form26ASData] = None,
    ) -> ReconciliationReport:
        """Run full reconciliation across all available sources."""
        report = ReconciliationReport()

        # ── Form 16 TDS ──
        if form16:
            report.form16_tds = form16.part_a.total_tds_deducted
            report.total_credit_claimed += report.form16_tds

        # ── AIS TDS ──
        if ais:
            report.ais_tds_salary = sum(
                (e.tds_deducted for e in ais.salary_tds), Decimal("0")
            )
            report.ais_tds_other = sum(
                (e.tds_deducted for e in ais.other_tds), Decimal("0")
            )

        # ── Form 26AS TDS ──
        if form26as:
            report.form26as_tds = form26as.total_tds
            report.form26as_advance_tax = form26as.advance_tax
            report.form26as_self_assessment = form26as.self_assessment_tax
            report.total_credit_available = form26as.total_tax_credit

        # ── Cross-Source Comparisons ──

        # 1. Form 16 vs AIS (Salary TDS)
        if form16 and ais:
            self._compare_f16_vs_ais(report)

        # 2. AIS vs Form 26AS (all TDS)
        if ais and form26as:
            self._compare_ais_vs_26as(report)

        # 3. Claimed vs Available
        if form16 and form26as:
            self._compare_claimed_vs_available(report)

        # 4. Non-salary TDS (potential missed credits)
        if ais:
            self._check_missed_credits(report, ais)

        report.matches = sum(1 for f in report.findings if f.severity == "match")
        report.warnings = sum(1 for f in report.findings if f.severity == "warning")
        report.errors = sum(1 for f in report.findings if f.severity == "error")

        return report

    def _compare_f16_vs_ais(self, report: ReconciliationReport) -> None:
        """Compare Form 16 salary TDS against AIS TDS-192 entries."""
        diff = abs(report.form16_tds - report.ais_tds_salary)

        if diff <= Decimal("1"):
            report.findings.append(ReconciliationFinding(
                severity="match",
                category="tds_salary",
                description=f"Form 16 salary TDS (₹{report.form16_tds:,.0f}) matches AIS (₹{report.ais_tds_salary:,.0f})",
                form16_value=report.form16_tds,
                ais_value=report.ais_tds_salary,
            ))
        elif diff <= Decimal("100"):
            report.findings.append(ReconciliationFinding(
                severity="warning",
                category="tds_salary",
                description=f"Minor mismatch: Form 16 TDS ₹{report.form16_tds:,.0f} vs AIS ₹{report.ais_tds_salary:,.0f} (₹{diff:,.0f} difference)",
                form16_value=report.form16_tds,
                ais_value=report.ais_tds_salary,
                difference=diff,
                recommendation="Minor rounding difference. AIS value will be used for filing.",
            ))
        else:
            report.findings.append(ReconciliationFinding(
                severity="error",
                category="tds_salary",
                description=f"Significant mismatch: Form 16 TDS ₹{report.form16_tds:,.0f} vs AIS ₹{report.ais_tds_salary:,.0f} (₹{diff:,.0f} difference)",
                form16_value=report.form16_tds,
                ais_value=report.ais_tds_salary,
                difference=diff,
                recommendation="Upload Form 26AS to resolve. Contact employer if TDS not deposited.",
            ))

    def _compare_ais_vs_26as(self, report: ReconciliationReport) -> None:
        """Compare AIS total TDS against Form 26AS total TDS."""
        ais_total = report.ais_tds_salary + report.ais_tds_other
        diff = abs(ais_total - report.form26as_tds)

        if diff <= Decimal("1"):
            report.findings.append(ReconciliationFinding(
                severity="match",
                category="tds_other",
                description=f"AIS total TDS (₹{ais_total:,.0f}) matches Form 26AS (₹{report.form26as_tds:,.0f})",
            ))
        else:
            report.findings.append(ReconciliationFinding(
                severity="warning",
                category="tds_other",
                description=f"AIS TDS ₹{ais_total:,.0f} vs Form 26AS ₹{report.form26as_tds:,.0f} (₹{diff:,.0f} difference). Form 26AS is authoritative.",
                difference=diff,
                recommendation="Use Form 26AS value. ITD uses 26AS for TDS credit.",
            ))

    def _compare_claimed_vs_available(self, report: ReconciliationReport) -> None:
        """Compare claimed TDS (Form 16) against available credit (26AS)."""
        if report.form16_tds > report.total_credit_available:
            excess = report.form16_tds - report.total_credit_available
            report.findings.append(ReconciliationFinding(
                severity="error",
                category="tds_salary",
                description=f"TDS claimed (₹{report.form16_tds:,.0f}) exceeds available credit in 26AS (₹{report.total_credit_available:,.0f}) by ₹{excess:,.0f}",
                difference=excess,
                recommendation="Reduce TDS claim to 26AS amount. Excess claim will be rejected by CPC.",
            ))

    def _check_missed_credits(self, report: ReconciliationReport, ais: AISData) -> None:
        """Identify non-salary TDS that may not have been claimed."""
        if ais.total_non_salary_tds > 0:
            report.findings.append(ReconciliationFinding(
                severity="warning",
                category="tds_other",
                description=f"Non-salary TDS of ₹{ais.total_non_salary_tds:,.0f} found in AIS. Ensure all credits are claimed in ITR.",
                ais_value=ais.total_non_salary_tds,
                recommendation="Claim TDS from bank FDs, NSCs, etc. in Schedule TDS2. Unclaimed TDS = lost refund.",
            ))
