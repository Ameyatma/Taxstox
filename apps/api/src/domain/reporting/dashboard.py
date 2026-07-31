"""Firm Dashboard — Metrics, deadlines, and staff activity for CA firms.

Provides the data model for firm-wide operational dashboards.

Traceability: C21.4 (Firm Dashboard — 30%→70%, P5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID


class MetricType(str, Enum):
    COUNT = "count"
    AMOUNT = "amount"
    PERCENTAGE = "percentage"
    DURATION = "duration"


@dataclass(frozen=True)
class DashboardMetric:
    """A single dashboard metric. Value object."""

    metric_id: str
    label: str                           # "Total Clients", "Filed Returns"
    value: Decimal
    metric_type: MetricType = MetricType.COUNT
    unit: str = ""                       # "clients", "₹", "%", "days"
    trend: str = "stable"                # "up", "down", "stable"
    trend_value: Decimal = Decimal("0")  # Change since last period
    comparison_label: str = ""           # "vs last month"

    @property
    def display_value(self) -> str:
        """Formatted display value."""
        if self.metric_type == MetricType.AMOUNT:
            return f"₹{self.value:,.0f}"
        elif self.metric_type == MetricType.PERCENTAGE:
            return f"{self.value:.1f}%"
        elif self.metric_type == MetricType.COUNT:
            return f"{int(self.value):,}"
        return str(self.value)


@dataclass
class FirmDashboard:
    """Complete firm dashboard for a CA firm tenant.

    Aggregates operational metrics, filing pipeline, staff activity,
    and deadline tracking.
    """

    tenant_id: UUID
    tenant_name: str = ""
    period_start: str = ""               # Dashboard period
    period_end: str = ""
    generated_at: str = ""

    # Key Metrics
    total_clients: DashboardMetric = field(default_factory=lambda: DashboardMetric(
        metric_id="total_clients", label="Total Clients", value=Decimal("0"),
        metric_type=MetricType.COUNT, unit="clients",
    ))
    active_filings: DashboardMetric = field(default_factory=lambda: DashboardMetric(
        metric_id="active_filings", label="Active Filings", value=Decimal("0"),
        metric_type=MetricType.COUNT, unit="filings",
    ))
    completed_filings: DashboardMetric = field(default_factory=lambda: DashboardMetric(
        metric_id="completed_filings", label="Completed Filings", value=Decimal("0"),
        metric_type=MetricType.COUNT, unit="filings",
    ))
    completion_rate: DashboardMetric = field(default_factory=lambda: DashboardMetric(
        metric_id="completion_rate", label="Completion Rate", value=Decimal("0"),
        metric_type=MetricType.PERCENTAGE, unit="%",
    ))
    revenue_this_month: DashboardMetric = field(default_factory=lambda: DashboardMetric(
        metric_id="revenue", label="Revenue (30 days)", value=Decimal("0"),
        metric_type=MetricType.AMOUNT, unit="₹",
    ))
    new_clients: DashboardMetric = field(default_factory=lambda: DashboardMetric(
        metric_id="new_clients", label="New Clients", value=Decimal("0"),
        metric_type=MetricType.COUNT, unit="clients",
    ))

    # Pipeline
    filings_by_status: dict[str, int] = field(default_factory=dict)
    filings_by_itr_type: dict[str, int] = field(default_factory=dict)

    # Staff
    staff_activity: list[dict] = field(default_factory=list)
    total_staff: int = 0

    # Deadlines
    upcoming_deadlines: list[dict] = field(default_factory=list)
    overdue_count: int = 0

    # Trends
    monthly_trend: list[dict] = field(default_factory=list)
    revenue_trend: list[dict] = field(default_factory=list)

    # Regime distribution
    regime_breakdown: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    @property
    def all_metrics(self) -> list[DashboardMetric]:
        return [
            self.total_clients, self.active_filings, self.completed_filings,
            self.completion_rate, self.revenue_this_month, self.new_clients,
        ]

    @property
    def summary(self) -> str:
        return (
            f"Firm: {self.tenant_name} | "
            f"Clients: {self.total_clients.display_value} | "
            f"Completion: {self.completion_rate.display_value} | "
            f"Revenue: {self.revenue_this_month.display_value}"
        )


@dataclass
class DeadlineTracker:
    """Track filing deadlines for a tenant's clients."""

    tenant_id: UUID
    deadlines: list[dict] = field(default_factory=list)

    def add_deadline(
        self, client_user_id: UUID, client_name: str,
        deadline_type: str, due_date: str, financial_year: str = "",
    ) -> None:
        self.deadlines.append({
            "client_id": str(client_user_id),
            "client_name": client_name,
            "type": deadline_type,                # "itr_filing", "audit", "tds_return"
            "due_date": due_date,
            "financial_year": financial_year,
            "days_remaining": self._days_until(due_date),
        })

    def get_upcoming(self, days: int = 30) -> list[dict]:
        """Get deadlines within the next N days."""
        upcoming = []
        for d in self.deadlines:
            remaining = self._days_until(d["due_date"])
            if 0 <= remaining <= days:
                d["days_remaining"] = remaining
                upcoming.append(d)
        return sorted(upcoming, key=lambda d: d["days_remaining"])

    @property
    def overdue(self) -> list[dict]:
        """Get overdue deadlines."""
        return [
            d for d in self.deadlines
            if self._days_until(d["due_date"]) < 0
        ]

    @property
    def overdue_count(self) -> int:
        return len(self.overdue)

    @staticmethod
    def _days_until(date_str: str) -> int:
        """Calculate days until a date. Negative = overdue."""
        from datetime import date
        try:
            target = date.fromisoformat(date_str)
            today = date.today()
            return (target - today).days
        except (ValueError, TypeError):
            return 999
