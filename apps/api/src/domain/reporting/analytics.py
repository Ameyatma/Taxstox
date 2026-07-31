"""Comparative Analytics — Cross-client benchmarks, trends, anonymized insights.

Enables CA firms to compare metrics across their client base and
see anonymized benchmarks against platform-wide averages.

Traceability: C14.2 (Comparative Analytics — 0%→40%, P5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class CrossClientBenchmark:
    """A benchmark metric computed across multiple clients. Value object."""

    benchmark_id: str
    label: str                            # "Average Effective Tax Rate"
    firm_average: Decimal
    firm_median: Decimal
    firm_min: Decimal
    firm_max: Decimal
    client_count: int
    unit: str = "%"

    @property
    def range_text(self) -> str:
        return f"₹{self.firm_min:,.0f} – ₹{self.firm_max:,.0f}"

    @property
    def summary(self) -> str:
        return (
            f"{self.label}: avg {self.firm_average:.1f}{self.unit}, "
            f"median {self.firm_median:.1f}{self.unit} "
            f"({self.client_count} clients)"
        )


@dataclass(frozen=True)
class TrendData:
    """Time-series trend data. Value object."""

    metric_name: str
    period: str                           # "monthly", "quarterly", "annual"
    data_points: tuple[dict, ...]         # [{"period": "2026-01", "value": "100"}, ...]

    @property
    def latest_value(self) -> Decimal:
        if self.data_points:
            return Decimal(str(self.data_points[-1].get("value", "0")))
        return Decimal("0")

    @property
    def percent_change(self) -> Decimal:
        if len(self.data_points) < 2:
            return Decimal("0")
        current = Decimal(str(self.data_points[-1].get("value", "0")))
        previous = Decimal(str(self.data_points[-2].get("value", "0")))
        if previous == 0:
            return Decimal("0")
        return ((current - previous) / previous * Decimal("100")).quantize(Decimal("0.1"))


@dataclass
class ComparativeAnalytics:
    """Comparative analytics across a tenant's client portfolio.

    Provides benchmarks, trends, and comparisons to help CA firms
    understand their practice performance.
    """

    tenant_id: UUID
    benchmarks: list[CrossClientBenchmark] = field(default_factory=list)
    trends: list[TrendData] = field(default_factory=list)

    # Client segmentation
    clients_by_regime: dict[str, int] = field(default_factory=dict)
    clients_by_itr_type: dict[str, int] = field(default_factory=dict)
    clients_by_income_range: dict[str, int] = field(default_factory=dict)
    clients_by_age_group: dict[str, int] = field(default_factory=dict)
    clients_by_tag: dict[str, int] = field(default_factory=dict)

    # Revenue analytics
    avg_revenue_per_client: Decimal = Decimal("0")
    revenue_by_month: list[dict] = field(default_factory=list)

    @property
    def total_clients_analyzed(self) -> int:
        """Deduplicated client count across all segmentation dimensions."""
        return sum(self.clients_by_regime.values())

    @property
    def dominant_regime(self) -> str:
        if not self.clients_by_regime:
            return "unknown"
        return max(self.clients_by_regime, key=self.clients_by_regime.get)

    @property
    def dominant_itr_type(self) -> str:
        if not self.clients_by_itr_type:
            return "unknown"
        return max(self.clients_by_itr_type, key=self.clients_by_itr_type.get)

    @property
    def summary(self) -> str:
        parts = [f"Analytics for {self.total_clients_analyzed} clients:"]
        parts.append(f"  Dominant regime: {self.dominant_regime}")
        parts.append(f"  Dominant ITR: {self.dominant_itr_type}")
        parts.append(f"  Avg revenue/client: ₹{self.avg_revenue_per_client:,.0f}")
        if self.benchmarks:
            parts.append(f"  Benchmarks: {len(self.benchmarks)} metrics")
        return "\n".join(parts)
