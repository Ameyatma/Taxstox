"""API tests for the security-headers middleware.

PR4.5: Regression coverage for the response security headers. The middleware
must attach the standard hardening headers on every response and must build a
Content-Security-Policy that is environment-aware (development includes the
local API origin). Assertions fail loudly if any header regresses.
"""

import pytest

from tests._markers import db_required  # noqa: F401  (marker import; no DB hit here)

pytestmark = pytest.mark.api

EXPECTED_PRESENT = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def test_security_headers_present_on_response(client):
    """All mandated hardening headers must be present with correct values."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    for header, value in EXPECTED_PRESENT.items():
        assert resp.headers.get(header) == value, (
            f"Missing/incorrect header {header}: "
            f"{resp.headers.get(header)!r} != {value!r}"
        )


def test_hsts_header_present(client):
    """HSTS must be enabled (max-age >= 1 year, with subdomains + preload)."""
    resp = client.get("/api/v1/health")
    hsts = resp.headers.get("Strict-Transport-Security", "")
    assert "max-age=" in hsts, "HSTS missing max-age"
    # 31536000 = 1 year minimum
    age = int(hsts.split("max-age=", 1)[1].split(";", 1)[0])
    assert age >= 31536000, f"HSTS max-age too short: {age}"


def test_csp_is_environment_aware_in_development(client, monkeypatch):
    """In development mode the CSP connect-src must include the local API origin."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    resp = client.get("/api/v1/health")
    csp = resp.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp, f"CSP default-src missing: {csp}"
    assert "http://localhost:8000" in csp, f"Dev CSP missing localhost origin: {csp}"