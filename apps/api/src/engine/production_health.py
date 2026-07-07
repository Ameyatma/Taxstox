"""Production Health Engine — Readiness, resilience, graceful degradation.

Provides comprehensive health assessment for production operations.
Graceful degradation: non-critical failures don't block core tax computation.

Traceability: C17.2 (Monitoring), M11 (Production Hardening)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class DependencyHealth:
    """Health status of a single dependency."""
    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    message: str = ""
    is_critical: bool = False

    @property
    def is_blocking(self) -> bool:
        return self.is_critical and self.status == HealthStatus.UNHEALTHY


@dataclass
class ProductionHealthReport:
    """Complete production health assessment."""
    service: str = "TaxStox ITR Engine"
    version: str = "0.1.0"
    status: HealthStatus = HealthStatus.HEALTHY
    timestamp: str = ""
    uptime_seconds: float = 0.0
    dependencies: list[DependencyHealth] = field(default_factory=list)
    checks_passed: int = 0
    checks_total: int = 0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def is_ready(self) -> bool:
        """System is ready to serve traffic."""
        return self.status != HealthStatus.UNHEALTHY

    @property
    def degraded_services(self) -> list[str]:
        return [d.name for d in self.dependencies if d.status == HealthStatus.DEGRADED]

    def to_dict(self) -> dict:
        return {
            "service": self.service,
            "version": self.version,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "uptime_seconds": self.uptime_seconds,
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
            "dependencies": [
                {
                    "name": d.name,
                    "status": d.status.value,
                    "latency_ms": d.latency_ms,
                    "message": d.message,
                    "critical": d.is_critical,
                }
                for d in self.dependencies
            ],
            "degraded_services": self.degraded_services,
            "ready": self.is_ready,
        }


class ProductionHealthEngine:
    """Assesses production health across all dependencies.

    Graceful degradation: non-critical failures are reported but don't
    block the ready check. Core tax computation continues even if
    auxiliary services are down.
    """

    def __init__(self, start_time: float) -> None:
        self._start_time = start_time
        self._checks: list[Callable[[], DependencyHealth]] = []

    def add_check(self, check: Callable[[], DependencyHealth]) -> None:
        self._checks.append(check)

    def assess(self) -> ProductionHealthReport:
        """Run all health checks and produce report."""
        import time
        report = ProductionHealthReport(
            uptime_seconds=time.time() - self._start_time,
        )
        report.checks_total = len(self._checks)

        for check_fn in self._checks:
            dep = check_fn()
            report.dependencies.append(dep)
            if dep.status == HealthStatus.HEALTHY:
                report.checks_passed += 1

        # Determine overall status
        if any(d.is_blocking for d in report.dependencies):
            report.status = HealthStatus.UNHEALTHY
        elif any(d.status == HealthStatus.DEGRADED for d in report.dependencies):
            report.status = HealthStatus.DEGRADED

        return report


# ── Built-in Health Checks ───────────────────────────────────────────

def check_database() -> DependencyHealth:
    """Check database connectivity."""
    import time
    start = time.time()
    try:
        from src.db.database import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return DependencyHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=round((time.time() - start) * 1000, 1),
            message="Connected",
            is_critical=True,
        )
    except Exception as e:
        return DependencyHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=str(e)[:200],
            is_critical=True,
        )


def check_rule_repository() -> DependencyHealth:
    """Verify rule repository is loaded and has at least one FY."""
    try:
        from src.engine.rules.config import rule_repository
        years = rule_repository.supported_years
        if len(years) >= 1:
            return DependencyHealth(
                name="rule_repository",
                status=HealthStatus.HEALTHY,
                message=f"{len(years)} FYs loaded: {[str(y) for y in years]}",
                is_critical=True,
            )
        return DependencyHealth(
            name="rule_repository",
            status=HealthStatus.UNHEALTHY,
            message="No financial years configured",
            is_critical=True,
        )
    except Exception as e:
        return DependencyHealth(
            name="rule_repository",
            status=HealthStatus.UNHEALTHY,
            message=str(e)[:200],
            is_critical=True,
        )


def check_encryption() -> DependencyHealth:
    """Verify encryption key is configured."""
    import os
    key = os.getenv("TAXSTOX_ENCRYPTION_KEY")
    if key:
        return DependencyHealth(
            name="encryption",
            status=HealthStatus.HEALTHY,
            message="Encryption key configured",
            is_critical=False,
        )
    return DependencyHealth(
        name="encryption",
        status=HealthStatus.DEGRADED,
        message="TAXSTOX_ENCRYPTION_KEY not set — PII encryption unavailable",
        is_critical=False,
    )
