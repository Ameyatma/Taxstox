"""Firm Dashboard Engine — Computes firm-wide metrics and deadline tracking.

Engine layer. Uses domain models, accesses tenant data via repository.
No framework imports.

Traceability: C21.4 (Firm Dashboard — 30%→70%, P5)
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from src.domain.reporting.dashboard import (
    FirmDashboard,
    DashboardMetric,
    MetricType,
    DeadlineTracker,
)
from src.domain.enterprise.tenant import Tenant, TenantRepository


class FirmDashboardEngine:
    """Computes firm dashboard metrics from tenant and filing data.

    Engine. Orchestrates data from Tenant aggregate, filing records,
    and activity logs into a coherent dashboard.
    """

    def __init__(self, repo: TenantRepository) -> None:
        self._repo = repo

    def compute(self, tenant_id: UUID) -> FirmDashboard:
        """Compute the complete firm dashboard for a tenant."""
        tenant = self._repo.get(tenant_id)
        if not tenant:
            return FirmDashboard(tenant_id=tenant_id, tenant_name="Unknown")

        dashboard = FirmDashboard(
            tenant_id=tenant_id,
            tenant_name=tenant.name,
        )

        # Basic metrics from tenant aggregate
        dashboard.total_clients = DashboardMetric(
            metric_id="total_clients", label="Total Clients",
            value=Decimal(str(tenant.active_client_count)),
            metric_type=MetricType.COUNT, unit="clients",
        )
        dashboard.total_staff = tenant.staff_count

        # Compute completion rate from portfolio if available
        portfolio = getattr(tenant, 'portfolio', None)
        if portfolio:
            completed = portfolio.clients_by_status.get("filed", 0)
            total_statuses = len(portfolio.filing_statuses)
            if total_statuses > 0:
                rate = (completed / total_statuses) * 100
            else:
                rate = 0.0
            dashboard.completion_rate = DashboardMetric(
                metric_id="completion_rate", label="Completion Rate",
                value=Decimal(str(round(rate, 1))),
                metric_type=MetricType.PERCENTAGE, unit="%",
            )
            dashboard.completed_filings = DashboardMetric(
                metric_id="completed_filings", label="Completed Filings",
                value=Decimal(str(completed)),
                metric_type=MetricType.COUNT, unit="filings",
            )
            dashboard.active_filings = DashboardMetric(
                metric_id="active_filings", label="Active Filings",
                value=Decimal(str(total_statuses - completed)),
                metric_type=MetricType.COUNT, unit="filings",
            )
            dashboard.filings_by_status = portfolio.clients_by_status

        # Revenue from subscription
        sub = getattr(tenant, 'subscription', None)
        if sub:
            price = getattr(sub, 'price_per_filing', Decimal("0"))
            filings = Decimal(str(portfolio.filing_statuses if portfolio else 0))
            rev = (filings * price).quantize(Decimal("0.01"))
            dashboard.revenue_this_month = DashboardMetric(
                metric_id="revenue", label="Revenue (30 days)",
                value=rev, metric_type=MetricType.AMOUNT, unit="₹",
            )

        # Subscription tier info
        if sub:
            tier_name = getattr(sub, 'tier', 'free')
            dashboard.regime_breakdown = {"tier": str(tier_name)}

        return dashboard


class DeadlineTrackerEngine:
    """Computes deadline tracking for a tenant's clients."""

    @staticmethod
    def from_tenant(tenant: Tenant) -> DeadlineTracker:
        """Build deadline tracker from tenant's client portfolio."""
        tracker = DeadlineTracker(tenant_id=tenant.tenant_id)

        portfolio = getattr(tenant, 'portfolio', None)
        if not portfolio:
            return tracker

        for fs in portfolio.filing_statuses:
            tracker.add_deadline(
                client_user_id=fs.client_user_id,
                client_name=str(fs.client_user_id),  # Name would come from user service
                deadline_type="itr_filing",
                due_date=fs.due_date or "2026-07-31",
                financial_year=fs.financial_year,
            )

        return tracker

    @staticmethod
    def compute_overdue_summary(tenant: Tenant) -> dict:
        """Quick overdue summary for dashboard."""
        tracker = DeadlineTrackerEngine.from_tenant(tenant)
        return {
            "overdue_count": tracker.overdue_count,
            "upcoming_30_days": len(tracker.get_upcoming(30)),
            "upcoming_7_days": len(tracker.get_upcoming(7)),
        }
