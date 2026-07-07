"""Compliance Checker — AIS completeness + anomaly detection.

Flags missing income, unusual patterns, and potential reporting errors
based on AIS data cross-referencing.

Traceability: C8.4 (AIS Completeness — 10%→60%), C8.6 (Anomaly Detection — 0%→40%, P1)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional


class FindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ComplianceFinding:
    """A single compliance finding."""
    finding_id: str
    category: str          # "ais_gap", "anomaly", "missing_income"
    severity: FindingSeverity
    description: str
    recommendation: str = ""
    estimated_impact: Decimal = Decimal("0")
    source_field: str = ""


@dataclass
class ComplianceReport:
    """Aggregated compliance findings."""
    findings: list[ComplianceFinding] = field(default_factory=list)

    @property
    def errors(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.ERROR)

    @property
    def warnings(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.WARNING)

    @property
    def is_clean(self) -> bool:
        return self.errors == 0 and self.warnings == 0


class ComplianceChecker:
    """Checks AIS completeness and detects anomalies.

    Compares AIS-reported financial data against what the user has
    provided, flagging gaps, unusual patterns, and potential errors.
    """

    # ── AIS Completeness Checks ──

    def check_ais_completeness(
        self,
        ais_has_salary_tds: bool = False,
        user_has_salary: bool = False,
        ais_has_interest: Decimal = Decimal("0"),
        user_has_interest: Decimal = Decimal("0"),
        ais_has_dividend: bool = False,
        user_has_dividend: bool = False,
        ais_cg_count: int = 0,
        user_cg_count: int = 0,
        ais_has_foreign_assets: bool = False,
        user_has_foreign_assets: bool = False,
    ) -> ComplianceReport:
        """Check if all AIS-reported income is captured in user data."""
        report = ComplianceReport()

        # Salary TDS exists in AIS but no salary reported
        if ais_has_salary_tds and not user_has_salary:
            report.findings.append(ComplianceFinding(
                finding_id="AIS-GAP-001",
                category="ais_gap",
                severity=FindingSeverity.WARNING,
                description="AIS shows salary TDS but no salary income added. "
                            "Your employer has reported TDS deductions to the IT Department.",
                recommendation="Add salary income details or upload Form 16.",
                source_field="ais.salary_tds",
            ))

        # Interest in AIS exceeds user-reported
        if ais_has_interest > user_has_interest:
            gap = ais_has_interest - user_has_interest
            report.findings.append(ComplianceFinding(
                finding_id="AIS-GAP-002",
                category="ais_gap",
                severity=FindingSeverity.WARNING,
                description=f"AIS shows interest income of ₹{ais_has_interest:,.0f} "
                            f"but only ₹{user_has_interest:,.0f} reported. "
                            f"Gap: ₹{gap:,.0f}.",
                recommendation="Add missing interest from bank FDs, savings accounts, etc.",
                estimated_impact=gap,
                source_field="ais.savings_interest",
            ))

        # Dividends in AIS not reported
        if ais_has_dividend and not user_has_dividend:
            report.findings.append(ComplianceFinding(
                finding_id="AIS-GAP-003",
                category="ais_gap",
                severity=FindingSeverity.INFO,
                description="AIS shows dividend income. Post-2020, all dividends are taxable.",
                recommendation="Report dividend income under 'Other Sources'.",
                source_field="ais.dividend",
            ))

        # Capital gains count mismatch
        if ais_cg_count > user_cg_count:
            missing = ais_cg_count - user_cg_count
            report.findings.append(ComplianceFinding(
                finding_id="AIS-GAP-004",
                category="ais_gap",
                severity=FindingSeverity.WARNING,
                description=f"AIS shows {ais_cg_count} capital gains transactions "
                            f"but only {user_cg_count} captured. Missing: {missing}.",
                recommendation="Upload broker statements or manually add missing sales.",
                source_field="ais.equity_mf_sales",
            ))

        # Foreign assets
        if ais_has_foreign_assets and not user_has_foreign_assets:
            report.findings.append(ComplianceFinding(
                finding_id="AIS-GAP-005",
                category="ais_gap",
                severity=FindingSeverity.ERROR,
                description="AIS indicates foreign assets/income. Schedule FA is mandatory.",
                recommendation="Report foreign assets under Schedule FA. Penalty applies for non-disclosure.",
                source_field="ais.foreign_assets",
            ))

        return report

    # ── Anomaly Detection ──

    def detect_anomalies(
        self,
        total_income: Decimal = Decimal("0"),
        previous_year_income: Optional[Decimal] = None,
        tds_to_tax_ratio: Optional[Decimal] = None,
        deduction_to_income_ratio: Optional[Decimal] = None,
    ) -> ComplianceReport:
        """Detect unusual patterns that may indicate errors or scrutiny risk."""
        report = ComplianceReport()

        # Large drop in income (potential missed income)
        if previous_year_income and previous_year_income > 0:
            if total_income < previous_year_income * Decimal("0.50"):
                drop_pct = ((previous_year_income - total_income) / previous_year_income) * 100
                report.findings.append(ComplianceFinding(
                    finding_id="ANM-001",
                    category="anomaly",
                    severity=FindingSeverity.WARNING,
                    description=f"Income dropped {drop_pct:.0f}% from previous year "
                                f"(₹{previous_year_income:,.0f} → ₹{total_income:,.0f}).",
                    recommendation="Verify all income sources are captured. A significant drop "
                                  "may trigger ITD scrutiny.",
                ))

        # Unusually high deductions relative to income
        if deduction_to_income_ratio and deduction_to_income_ratio > Decimal("0.50"):
            pct = deduction_to_income_ratio * 100
            report.findings.append(ComplianceFinding(
                finding_id="ANM-002",
                category="anomaly",
                severity=FindingSeverity.WARNING,
                description=f"Deductions are {pct:.0f}% of total income — unusually high.",
                recommendation="Verify all deductions are supported by documentation. "
                              "High deduction ratios may trigger ITD notice.",
            ))

        # TDS significantly exceeds tax liability (potential refund fraud flag)
        if tds_to_tax_ratio and tds_to_tax_ratio > Decimal("3.0"):
            report.findings.append(ComplianceFinding(
                finding_id="ANM-003",
                category="anomaly",
                severity=FindingSeverity.INFO,
                description=f"TDS is {tds_to_tax_ratio:.1f}x the computed tax liability. "
                            f"Large refunds may face additional scrutiny.",
                recommendation="Ensure all income is reported correctly. Refund will be processed "
                              "after ITD verification.",
            ))

        return report
