"""API tests for tenant context isolation (middleware layer).

PR4.5: Regression coverage for the tenant-context middleware. The middleware
must resolve a tenant only from an explicit X-Tenant-ID header (or JWT claim,
exercised elsewhere) and must never leak an unparseable header into the
response. This guards the multi-tenant boundary without touching the database.
"""

import uuid

import pytest

from tests._markers import db_required  # noqa: F401  (marker import; no DB hit here)

pytestmark = pytest.mark.api


def test_valid_tenant_header_is_echoed_in_response(client):
    """A valid UUID tenant id is echoed on the response for downstream tracing."""
    tenant = str(uuid.uuid4())
    resp = client.get("/api/v1/health", headers={"X-Tenant-ID": tenant})
    assert resp.status_code == 200
    assert resp.headers.get("X-Tenant-ID") == tenant


def test_malformed_tenant_header_is_not_propagated(client):
    """An unparseable tenant id must be ignored (no echo), not echoed verbatim."""
    resp = client.get("/api/v1/health", headers={"X-Tenant-ID": "not-a-uuid"})
    assert resp.status_code == 200
    assert resp.headers.get("X-Tenant-ID") is None


def test_no_tenant_header_does_not_emit_tenant_response_header(client):
    """Public requests without a tenant must not receive a tenant response header."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Tenant-ID") is None
