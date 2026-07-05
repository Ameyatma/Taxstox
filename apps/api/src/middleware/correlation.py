"""Correlation ID middleware for request tracing.

Injects a unique correlation_id into every request. The ID is:
- Read from X-Request-ID header if present (for upstream propagation)
- Generated as UUID4 if not present
- Added to response headers for downstream propagation
- Available to all log statements via logging context
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware that ensures every request has a correlation ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get or generate correlation ID
        correlation_id = request.headers.get(
            "X-Request-ID",
            request.headers.get("x-request-id", str(uuid.uuid4())),
        )

        # Store in request state for access by route handlers
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add to response headers for downstream propagation
        response.headers["X-Request-ID"] = correlation_id

        return response
