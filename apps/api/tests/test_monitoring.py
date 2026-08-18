"""Tests for PR5.3 health / monitoring / metrics.

Verifies:
- /metrics endpoint exposes aggregated request metrics
- MetricsMiddleware records latency, status, error rate
- _simplify_path bounds cardinality (UUID, hex session, numeric id)
- /health/detailed uses existing ProductionHealthEngine and degrades gracefully
- /health still returns ok
All run through the real app via the `client` fixture (no DB required for
these endpoints — health checks catch exceptions and report UNHEALTHY).
"""

import pytest

from src.middleware.metrics import _simplify_path, MetricsStore, metrics


# ── 1. Path normalization / cardinality ─────────────────────────────

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("/api/v1/upload", "/api/v1/upload"),
        # 32-char hex session IDs (uuid4().hex)
        ("/api/v1/process/9f8e7d6c5b4a39281706f5e4d3c2b1a0", "/api/v1/process/{session}"),
        ("/api/v1/export/0a1b2c3d4e5f60718293a4b5c6d7e8f9", "/api/v1/export/{session}"),
        ("/api/v1/users/42/profile", "/api/v1/users/{id}/profile"),
        ("/api/v1/ses_abc123xyz", "/api/v1/{session}"),
        (
            "/api/v1/process/123e4567-e89b-12d3-a456-426614174000",
            "/api/v1/process/{id}",
        ),
    ],
)
def test_simplify_path_collapses_high_cardinality(raw, expected):
    assert _simplify_path(raw) == expected


def test_metrics_store_records_and_aggregates():
    store = MetricsStore()
    store.record("/api/v1/upload", 200, 12.5)
    store.record("/api/v1/upload", 200, 7.5)
    store.record("/api/v1/export", 500, 100.0)
    assert store.total_requests == 3
    assert store.total_errors == 1
    assert abs(store.error_rate - 1 / 3) < 1e-9
    assert abs(store.avg_latency_ms - 40.0) < 1e-9
    assert store.status_codes[200] == 2
    assert store.status_codes[500] == 1


def test_metrics_p95_isolated_per_endpoint():
    store = MetricsStore()
    for _ in range(20):
        store.record("/a", 200, 10.0)
    for _ in range(20):
        store.record("/b", 200, 100.0)
    assert store.p95_latency("/a") == 10.0
    assert store.p95_latency("/b") == 100.0


# ── 2. Endpoints via real app ───────────────────────────────────────

def test_health_basic(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("ok", "degraded")


def test_metrics_endpoint_exposes_data(client):
    # Generate at least one request so metrics are non-empty
    client.get("/api/v1/health")
    resp = client.get("/api/v1/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert "total_requests" in body
    assert "error_rate" in body
    assert body["total_requests"] >= 1


def test_metrics_records_error_rate(client):
    # /metrics may record; hit an unknown endpoint to produce a 404 (counted as
    # non-5xx error, but confirms middleware records status codes).
    client.get("/api/v1/health")
    client.get("/api/v1/does-not-exist")
    body = client.get("/api/v1/metrics").json()
    assert body["total_requests"] >= 2
    assert "404" in body["status_codes"]  # JSON serializes int keys to strings


def test_health_detailed_degrades_without_db(client):
    """With no DB configured, /health/detailed must report (not 500)."""
    resp = client.get("/api/v1/health/detailed")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert "dependencies" in body
    # Database check should report its failure rather than crash the endpoint
    db_deps = [d for d in body["dependencies"] if d["name"] == "database"]
    assert db_deps, "database dependency should always be present"
