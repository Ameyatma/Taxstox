"""Security Headers Middleware — Infrastructure layer.

Adds security headers to all responses: CSP, HSTS, X-Content-Type-Options,
X-Frame-Options, Referrer-Policy, Permissions-Policy, Cross-Origin-Opener-Policy,
Cross-Origin-Resource-Policy.

CSP is environment-aware — connect-src is generated from runtime configuration
rather than hardcoded to production.

Headers intentionally omitted:
- Cross-Origin-Embedder-Policy: requires CORP headers on all third-party
  subresources (CDN scripts, Google Fonts). Not feasible without controlling
  those origins. Appropriate only for isolated web apps.

Traceability: C17.10 (Security Compliance), PR1.4 (Security Headers),
             PR1 R4 (environment-aware CSP)
"""

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


def _build_csp() -> str:
    """Build Content-Security-Policy from runtime configuration."""
    # Allow localhost for development, production URL for deployment
    api_origins = [
        "'self'",
    ]

    # Add development API if running locally
    if os.environ.get("ENVIRONMENT", "development") == "development":
        api_origins.append("http://localhost:8000")

    # Add production API if configured
    api_base = os.environ.get("API_BASE_URL", "")
    if api_base:
        api_origins.append(api_base)

    # Google OAuth endpoints (needed for token verification during sign-in)
    api_origins.append("https://accounts.google.com")
    api_origins.append("https://www.googleapis.com")

    connect_src = " ".join(api_origins)

    return (
        f"default-src 'self'; "
        f"script-src 'self'; "
        f"style-src 'self' 'unsafe-inline'; "
        f"img-src 'self' data: https:; "
        f"connect-src {connect_src}; "
        f"frame-ancestors 'none'; "
        f"base-uri 'self'; "
        f"form-action 'self'"
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard security headers to every response.

    CSP is environment-aware — built at middleware initialization
    from runtime configuration.
    """

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._csp = _build_csp()

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        headers = response.headers

        # Content Security Policy (environment-aware)
        headers.setdefault("Content-Security-Policy", self._csp)

        # Strict Transport Security (1 year)
        headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )

        # Prevent MIME type sniffing
        headers.setdefault("X-Content-Type-Options", "nosniff")

        # Prevent clickjacking (defense-in-depth with CSP frame-ancestors)
        headers.setdefault("X-Frame-Options", "DENY")

        # Referrer policy
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")

        # Permissions policy — tax platform needs no browser APIs
        headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=()",
        )

        # Cross-Origin isolation headers
        headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")

        # Cross-Origin-Embedder-Policy intentionally omitted
        # Requires CORP: cross-origin on all third-party subresources (CDNs,
        # Google Fonts, analytics). Not feasible without controlling those origins.

        return response
