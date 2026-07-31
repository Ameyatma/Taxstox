"""Comparative Analytics Engine — Cross-client benchmarks and trend analysis.

Computes anonymized benchmarks across a firm's client portfolio.

Traceability: C14.2 (Comparative Analytics — 0%→40%, P5)
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from src.domain.reporting.analytics import (
    ComparativeAnalytics,
    CrossClientBenchmark,
    TrendData,
)
from src.domain.enterprise.tenant import Tenant, TenantRepository


class ComparativeAnalyticsEngine:
    """Computes cross-client benchmarks and comparative analytics.

    Engine layer. All client data is scoped to the tenant —
    no cross-tenant data access.
    """

    def __init__(self, repo: TenantRepository) -> None:
        self._repo = repo

    def compute(self, tenant_id: UUID) -> ComparativeAnalytics:
        """Compute comparative analytics for a tenant's client portfolio."""
        tenant = self._repo.get(tenant_id)
        analytics = ComparativeAnalytics(tenant_id=tenant_id)

        if not tenant:
            return analytics

        portfolio = getattr(tenant, 'portfolio', None)
        if not portfolio:
            return analytics

        # Client segmentation
        analytics.clients_by_tag = {
            tag: len(tenant.get_clients_by_tag(tag))
            for tag in tenant.unique_tags
        }

        # Filing status breakdown
        analytics.clients_by_itr_type = portfolio.clients_by_status or {}

        # Compute ITR type distribution
        itr_counts: dict[str, int] = {}
        for fs in portfolio.filing_statuses:
            if fs.itr_type:
                itr_counts[fs.itr_type] = itr_counts.get(fs.itr_type, 0) + 1
        analytics.clients_by_itr_type = itr_counts

        # Revenue analytics
        sub = getattr(tenant, 'subscription', None)
        if sub:
            price_per = getattr(sub, 'price_per_filing', Decimal("0"))
            filing_count = len(portfolio.filing_statuses)
            analytics.avg_revenue_per_client = (
                (Decimal(str(filing_count)) * price_per).quantize(Decimal("0.01"))
                if filing_count > 0 and price_per > 0
                else Decimal("0")
            )

        return analytics

    @staticmethod
    def compute_tax_benchmarks(
        tax_data: list[dict],  # [{"total_income": "1000000", "final_tax": "50000", "regime": "new"}, ...]
    ) -> list[CrossClientBenchmark]:
        """Compute tax-related benchmarks across clients.

        Args:
            tax_data: List of per-client tax summaries (anonymized)

        Returns:
            List of CrossClientBenchmark metrics
        """
        if not tax_data:
            return []

        benchmarks: list[CrossClientBenchmark] = []

        # Effective tax rates
        rates = []
        incomes = []
        taxes = []
        for d in tax_data:
            income = Decimal(str(d.get("total_income", "0")))
            tax = Decimal(str(d.get("final_tax", "0")))
            if income > 0:
                rates.append(float((tax / income) * 100))
                incomes.append(income)
                taxes.append(tax)

        if rates:
            sorted_rates = sorted(rates)
            n = len(sorted_rates)
            benchmarks.append(CrossClientBenchmark(
                benchmark_id="effective_tax_rate",
                label="Effective Tax Rate",
                firm_average=Decimal(str(round(sum(rates) / n, 1))),
                firm_median=Decimal(str(round(sorted_rates[n // 2], 1))),
                firm_min=Decimal(str(round(sorted_rates[0], 1))),
                firm_max=Decimal(str(round(sorted_rates[-1], 1))),
                client_count=n,
                unit="%",
            ))

        # Average income
        if incomes:
            sorted_inc = sorted(incomes, key=lambda d: float(d))
            ni = len(sorted_inc)
            benchmarks.append(CrossClientBenchmark(
                benchmark_id="avg_income",
                label="Average Total Income",
                firm_average=Decimal(str(round(float(sum(incomes)) / ni, 0))),
                firm_median=sorted_inc[ni // 2],
                firm_min=sorted_inc[0],
                firm_max=sorted_inc[-1],
                client_count=ni,
                unit="₹",
            ))

        return benchmarks

    @staticmethod
    def compute_regime_distribution(
        regime_data: list[str],  # ["new", "old", "new", ...]
    ) -> dict[str, int]:
        """Compute regime distribution across clients."""
        dist: dict[str, int] = {}
        for r in regime_data:
            dist[r] = dist.get(r, 0) + 1
        return dist
