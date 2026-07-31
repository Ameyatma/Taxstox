"""Custom Report Builder — Parameterized report templates and scheduling.

Enables CA firms to define, parameterize, and schedule custom reports.

Traceability: C14.6 (Custom Report Builder — 0%→30%, P5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class ReportFormat(str, Enum):
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "excel"
    JSON = "json"


class ReportFrequency(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


@dataclass(frozen=True)
class ReportParameter:
    """A configurable parameter for a report template. Value object."""

    parameter_id: str
    label: str                           # "Financial Year", "ITR Type"
    param_type: str                      # "text", "select", "date_range", "number"
    default_value: str = ""
    options: tuple[str, ...] = ()        # For select type
    required: bool = True


@dataclass
class ReportTemplate:
    """A report template definition. Entity."""

    template_id: UUID
    name: str                            # "Monthly Filing Summary"
    description: str = ""
    category: str = ""                   # "filing", "revenue", "clients", "compliance"
    parameters: list[ReportParameter] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    @staticmethod
    def create(name: str, description: str = "", category: str = "") -> ReportTemplate:
        return ReportTemplate(
            template_id=uuid4(), name=name, description=description,
            category=category,
        )

    def add_parameter(self, param: ReportParameter) -> None:
        self.parameters.append(param)
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


@dataclass
class ReportSchedule:
    """A scheduled report generation. Entity."""

    schedule_id: UUID
    template_id: UUID
    tenant_id: UUID
    frequency: ReportFrequency = ReportFrequency.ONCE
    format: ReportFormat = ReportFormat.CSV
    recipients: list[str] = field(default_factory=list)  # Email addresses
    parameters: dict[str, str] = field(default_factory=dict)
    next_run_at: str = ""
    is_active: bool = True
    last_run_at: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @staticmethod
    def create(
        template_id: UUID, tenant_id: UUID,
        frequency: ReportFrequency = ReportFrequency.ONCE,
        format: ReportFormat = ReportFormat.CSV,
    ) -> ReportSchedule:
        return ReportSchedule(
            schedule_id=uuid4(), template_id=template_id,
            tenant_id=tenant_id, frequency=frequency, format=format,
        )

    def set_parameter(self, key: str, value: str) -> None:
        self.parameters[key] = value

    def disable(self) -> None:
        self.is_active = False

    def enable(self) -> None:
        self.is_active = True


# ── Pre-built Templates ───────────────────────────────────────────────

def build_standard_templates() -> list[ReportTemplate]:
    """Build the standard report template library."""

    templates: list[ReportTemplate] = []

    # Template 1: Monthly Filing Summary
    t1 = ReportTemplate.create(
        "Monthly Filing Summary",
        "Summary of all filings completed this month with tax and regime breakdown",
        "filing",
    )
    t1.add_parameter(ReportParameter("month", "Month", "select",
        default_value="current",
        options=("current", "previous", "january", "february", "march", "april", "may", "june",
                 "july", "august", "september", "october", "november", "december"),
    ))
    t1.add_parameter(ReportParameter("financial_year", "Financial Year", "select",
        default_value="FY2025-26",
        options=("FY2025-26", "FY2024-25"),
    ))
    templates.append(t1)

    # Template 2: Client Portfolio by Status
    t2 = ReportTemplate.create(
        "Client Portfolio Status",
        "All clients grouped by filing status with counts and percentages",
        "clients",
    )
    t2.add_parameter(ReportParameter("financial_year", "Financial Year", "select",
        default_value="FY2025-26",
        options=("FY2025-26", "FY2024-25"),
    ))
    templates.append(t2)

    # Template 3: Revenue Summary
    t3 = ReportTemplate.create(
        "Revenue Summary",
        "Revenue breakdown by month with per-client averages",
        "revenue",
    )
    t3.add_parameter(ReportParameter("period", "Period", "select",
        default_value="current_month",
        options=("current_month", "current_quarter", "current_year", "last_year"),
    ))
    templates.append(t3)

    # Template 4: Deadline Compliance
    t4 = ReportTemplate.create(
        "Deadline Compliance Report",
        "Clients approaching or past filing deadlines with days remaining",
        "compliance",
    )
    t4.add_parameter(ReportParameter("financial_year", "Financial Year", "select",
        default_value="FY2025-26",
        options=("FY2025-26", "FY2024-25"),
    ))
    t4.add_parameter(ReportParameter("days_threshold", "Days Before Deadline", "number",
        default_value="30",
    ))
    templates.append(t4)

    return templates
