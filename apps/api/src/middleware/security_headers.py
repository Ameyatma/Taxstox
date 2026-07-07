"""Security Headers Middleware — Infrastructure layer.

Adds security headers to all responses: CSP, HSTS, X-Content-Type-Options,
X-Frame-Options, Referrer-Policy, Permissions-Policy.

Traceability: C17.10 (Security Compliance), R03 (PII breach prevention)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard security headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        headers = response.headers

        # Prevent MIME type sniffing
        headers.setdefault("X-Content-Type-Options", "nosniff")

        # Prevent clickjacking
        headers.setdefault("X-Frame-Options", "DENY")

        # Strict Transport Security (1 year)
        headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )

        # Referrer policy
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")

        # Permissions policy — restrict sensitive APIs
        headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )

        # Content Security Policy
        headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self' https://api.taxstox.com; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )

        return response
