"""Custom Report Engine — Parameterized report generation with CSV/PDF export.

Engine layer. Renders report templates with tenant-specific data.

Traceability: C14.6 (Custom Report Builder — 0%→30%, P5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from src.domain.reporting.custom_report import (
    ReportTemplate,
    ReportSchedule,
    ReportFormat,
    ReportFrequency,
    build_standard_templates,
)
from src.domain.enterprise.tenant import Tenant


@dataclass
class ReportGenerationResult:
    """Result of generating a report."""

    template_id: UUID
    tenant_id: UUID
    format: ReportFormat = ReportFormat.CSV
    generated_at: str = ""
    content: str = ""                    # CSV string or JSON
    filename: str = ""
    row_count: int = 0
    success: bool = True
    error_message: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()


class CustomReportEngine:
    """Generates reports from templates with tenant data.

    Engine layer. Template-driven — each template defines a report
    structure. Data is pulled from tenant + portfolio.
    """

    def __init__(self) -> None:
        self._templates: dict[str, ReportTemplate] = {
            t.template_id.hex: t for t in build_standard_templates()
        }

    @property
    def available_templates(self) -> list[ReportTemplate]:
        return list(self._templates.values())

    def get_template(self, template_id: UUID) -> ReportTemplate | None:
        return self._templates.get(template_id.hex)

    def generate(
        self,
        template: ReportTemplate,
        tenant: Tenant,
        parameters: dict[str, str] | None = None,
        format: ReportFormat = ReportFormat.CSV,
    ) -> ReportGenerationResult:
        """Generate a report from a template and tenant data.

        Args:
            template: The report template to use
            tenant: Tenant aggregate with portfolio data
            parameters: Template parameter values
            format: Output format

        Returns:
            ReportGenerationResult with content
        """
        params = parameters or {}

        if format == ReportFormat.CSV:
            return self._generate_csv(template, tenant, params)
        elif format == ReportFormat.JSON:
            return self._generate_json(template, tenant, params)
        else:
            return ReportGenerationResult(
                template_id=template.template_id,
                tenant_id=tenant.tenant_id,
                format=format,
                success=False,
                error_message=f"Format {format.value} not yet implemented",
            )

    def _generate_csv(
        self, template: ReportTemplate, tenant: Tenant, params: dict[str, str],
    ) -> ReportGenerationResult:
        """Generate CSV report."""
        import csv
        import io

        financial_year = params.get("financial_year", "FY2025-26")
        output = io.StringIO()
        writer = csv.writer(output)

        portfolio = getattr(tenant, 'portfolio', None)

        # Header
        writer.writerow([
            "Client ID", "Financial Year", "ITR Type", "Status",
            "Priority", "Due Date", "Assigned To",
        ])

        # Data rows
        row_count = 0
        if portfolio:
            for fs in portfolio.filing_statuses:
                if financial_year and fs.financial_year != financial_year:
                    continue
                writer.writerow([
                    str(fs.client_user_id), fs.financial_year, fs.itr_type,
                    fs.status.value, fs.priority.value, fs.due_date,
                    str(fs.assigned_to) if fs.assigned_to else "",
                ])
                row_count += 1

        return ReportGenerationResult(
            template_id=template.template_id,
            tenant_id=tenant.tenant_id,
            format=ReportFormat.CSV,
            content=output.getvalue(),
            filename=f"{template.name.lower().replace(' ', '_')}_{financial_year}.csv",
            row_count=row_count,
        )

    def _generate_json(
        self, template: ReportTemplate, tenant: Tenant, params: dict[str, str],
    ) -> ReportGenerationResult:
        """Generate JSON report."""
        import json

        financial_year = params.get("financial_year", "FY2025-26")
        portfolio = getattr(tenant, 'portfolio', None)

        data = {
            "template": template.name,
            "tenant": tenant.name,
            "financial_year": financial_year,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "clients": [],
        }

        if portfolio:
            for fs in portfolio.filing_statuses:
                if financial_year and fs.financial_year != financial_year:
                    continue
                data["clients"].append({
                    "client_id": str(fs.client_user_id),
                    "financial_year": fs.financial_year,
                    "itr_type": fs.itr_type,
                    "status": fs.status.value,
                    "priority": fs.priority.value,
                    "due_date": fs.due_date,
                    "is_overdue": fs.is_overdue,
                })

        return ReportGenerationResult(
            template_id=template.template_id,
            tenant_id=tenant.tenant_id,
            format=ReportFormat.JSON,
            content=json.dumps(data, indent=2),
            filename=f"{template.name.lower().replace(' ', '_')}_{financial_year}.json",
            row_count=len(data["clients"]),
        )

    @staticmethod
    def schedule_report(
        template_id: UUID, tenant_id: UUID,
        frequency: ReportFrequency = ReportFrequency.MONTHLY,
        format: ReportFormat = ReportFormat.CSV,
        recipients: list[str] | None = None,
    ) -> ReportSchedule:
        """Create a scheduled report."""
        schedule = ReportSchedule.create(
            template_id=template_id, tenant_id=tenant_id,
            frequency=frequency, format=format,
        )
        if recipients:
            schedule.recipients = recipients
        return schedule
