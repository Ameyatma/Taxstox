"""Tenant Context Middleware — Infrastructure layer.

Resolves tenant_id once per request from JWT claims or header.
Stores in request.state for downstream consumption.
Framework-aware (FastAPI/Starlette). Domain layer consumes via abstraction.

Traceability: C21.1 (Tenant Management — middleware)
"""

from __future__ import annotations

from uuid import UUID, uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Resolves tenant context per request.

    Priority:
    1. X-Tenant-ID header (explicit tenant selection)
    2. JWT tenant_id claim (user's default tenant)
    3. None (public endpoints, individual taxpayer)

    Tenant ID is stored in request.state.tenant_id for downstream use.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id = self._resolve_tenant(request)
        request.state.tenant_id = tenant_id
        response = await call_next(request)
        if tenant_id:
            response.headers["X-Tenant-ID"] = str(tenant_id)
        return response

    def _resolve_tenant(self, request: Request) -> UUID | None:
        """Resolve tenant from header or JWT."""
        # 1. Explicit header override
        header = request.headers.get("X-Tenant-ID")
        if header:
            try:
                return UUID(header)
            except ValueError:
                pass

        # 2. JWT claim (from context var, set by get_current_user)
        from src.auth.jwt import _current_claims
        claims = _current_claims.get({})
        tenant_str = claims.get("tenant_id")
        if tenant_str:
            try:
                return UUID(tenant_str)
            except (ValueError, AttributeError):
                pass

        return None
