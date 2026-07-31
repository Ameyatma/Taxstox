"""Reporting bounded context — Firm dashboards, analytics, custom reports.

Domain layer. Zero framework imports. Pure Python.

Traceability: C21.4 (Firm Dashboard), C14.2 (Comparative Analytics),
             C14.5 (BI & Analytics), C14.6 (Custom Report Builder)
"""

from src.domain.reporting.dashboard import (
    FirmDashboard,
    DashboardMetric,
    MetricType,
)
from src.domain.reporting.analytics import (
    ComparativeAnalytics,
    CrossClientBenchmark,
    TrendData,
)
from src.domain.reporting.custom_report import (
    ReportTemplate,
    ReportSchedule,
    ReportFormat,
    ReportParameter,
)

__all__ = [
    "FirmDashboard",
    "DashboardMetric",
    "MetricType",
    "ComparativeAnalytics",
    "CrossClientBenchmark",
    "TrendData",
    "ReportTemplate",
    "ReportSchedule",
    "ReportFormat",
    "ReportParameter",
]
