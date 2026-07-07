"""Unit tests for Production Health Engine — M11."""

import time

from src.engine.production_health import (
    ProductionHealthEngine,
    ProductionHealthReport,
    HealthStatus,
    DependencyHealth,
)


class TestDependencyHealth:
    def test_healthy_dependency(self):
        dep = DependencyHealth(
            name="database", status=HealthStatus.HEALTHY,
            message="Connected", is_critical=True,
        )
        assert dep.is_blocking is False

    def test_unhealthy_critical_blocks(self):
        dep = DependencyHealth(
            name="database", status=HealthStatus.UNHEALTHY,
            message="Connection refused", is_critical=True,
        )
        assert dep.is_blocking is True

    def test_degraded_non_critical_no_block(self):
        dep = DependencyHealth(
            name="encryption", status=HealthStatus.DEGRADED,
            message="Key not set", is_critical=False,
        )
        assert dep.is_blocking is False


class TestProductionHealthReport:
    def test_healthy_report(self):
        report = ProductionHealthReport(
            status=HealthStatus.HEALTHY,
            checks_passed=3,
            checks_total=3,
        )
        assert report.is_ready

    def test_unhealthy_report(self):
        report = ProductionHealthReport(
            status=HealthStatus.UNHEALTHY,
        )
        assert not report.is_ready

    def test_to_dict(self):
        report = ProductionHealthReport(
            dependencies=[
                DependencyHealth("db", HealthStatus.HEALTHY, is_critical=True),
            ],
            checks_passed=1,
            checks_total=1,
        )
        d = report.to_dict()
        assert d["status"] == "healthy"
        assert d["checks_passed"] == 1


class TestProductionHealthEngine:
    def test_assess_with_checks(self):
        engine = ProductionHealthEngine(start_time=time.time())
        engine.add_check(lambda: DependencyHealth(
            "test", HealthStatus.HEALTHY, message="OK", is_critical=True,
        ))
        report = engine.assess()
        assert report.status == HealthStatus.HEALTHY
        assert report.checks_passed == 1

    def test_assess_detects_unhealthy(self):
        engine = ProductionHealthEngine(start_time=time.time())
        engine.add_check(lambda: DependencyHealth(
            "critical", HealthStatus.UNHEALTHY, is_critical=True,
        ))
        report = engine.assess()
        assert report.status == HealthStatus.UNHEALTHY


class TestMetricsStore:
    def test_record_and_stats(self):
        from src.middleware.metrics import MetricsStore
        store = MetricsStore()
        store.record("/api/v1/health", 200, 5.0)
        store.record("/api/v1/health", 200, 15.0)
        assert store.total_requests == 2
        assert store.avg_latency_ms == 10.0
        assert store.error_rate == 0.0

    def test_error_recording(self):
        from src.middleware.metrics import MetricsStore
        store = MetricsStore()
        store.record("/api/v1/compute", 500, 100.0)
        assert store.total_errors == 1
        assert store.error_rate == 1.0

    def test_simplify_path_session(self):
        from src.middleware.metrics import _simplify_path
        result = _simplify_path("/api/v1/session/ses_abc123def456")
        assert "{session}" in result

    def test_simplify_path_uuid(self):
        from src.middleware.metrics import _simplify_path
        result = _simplify_path("/api/v1/process/550e8400-e29b-41d4-a716-446655440000")
        assert "{id}" in result

    def test_to_dict(self):
        from src.middleware.metrics import MetricsStore
        store = MetricsStore()
        store.record("/api/v1/health", 200, 10.0)
        d = store.to_dict()
        assert "uptime_seconds" in d
        assert "error_rate" in d
