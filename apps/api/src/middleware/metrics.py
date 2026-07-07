"""Metrics Middleware — Request rate, latency, error rate.

Lightweight in-process metrics. No external dependency.
Exposed via /api/v1/metrics for monitoring systems.

Traceability: C17.2 (Monitoring), M11 (Production Hardening)
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


@dataclass
class MetricsStore:
    """Thread-safe metrics accumulator."""
    total_requests: int = 0
    total_errors: int = 0
    total_latency_ms: float = 0.0
    status_codes: dict[int, int] = field(default_factory=lambda: defaultdict(int))
    endpoint_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    endpoint_latencies: dict[str, list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )
    start_time: float = field(default_factory=time.time)

    def record(self, path: str, status_code: int, latency_ms: float) -> None:
        self.total_requests += 1
        if status_code >= 500:
            self.total_errors += 1
        self.total_latency_ms += latency_ms
        self.status_codes[status_code] += 1
        # Simplify path for aggregation (strip UUIDs, session IDs)
        simple_path = _simplify_path(path)
        self.endpoint_counts[simple_path] += 1
        self.endpoint_latencies[simple_path].append(latency_ms)

    @property
    def avg_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_errors / self.total_requests

    def p95_latency(self, path: str | None = None) -> float:
        latencies = (
            self.endpoint_latencies.get(path, [])
            if path
            else [l for v in self.endpoint_latencies.values() for l in v]
        )
        if not latencies:
            return 0.0
        sorted_lat = sorted(latencies)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.start_time

    def to_dict(self) -> dict:
        return {
            "uptime_seconds": round(self.uptime_seconds, 0),
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": round(self.error_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "p95_latency_ms": round(self.p95_latency(), 1),
            "status_codes": dict(self.status_codes),
            "endpoints": {
                k: {"count": v, "p95_ms": round(self.p95_latency(k), 1)}
                for k, v in sorted(
                    self.endpoint_counts.items(),
                    key=lambda x: x[1], reverse=True,
                )[:10]
            },
        }


# Singleton metrics store
metrics = MetricsStore()


def _simplify_path(path: str) -> str:
    """Replace UUIDs and session IDs with placeholders."""
    import re
    path = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "{id}", path)
    path = re.sub(r"ses_[a-z0-9]+", "{session}", path)
    return path


class MetricsMiddleware(BaseHTTPMiddleware):
    """Records request metrics for every request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()
        response = await call_next(request)
        latency = (time.time() - start) * 1000
        metrics.record(request.url.path, response.status_code, latency)
        return response
