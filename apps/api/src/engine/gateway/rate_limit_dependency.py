"""Rate Limit FastAPI Dependency — Storage-agnostic rate limit enforcement.

Engine layer. Provides FastAPI Depends-compatible functions for route-level
rate limiting. Uses RateLimitStore Protocol from domain.

Traceability: PR1.3 (Rate Limiting — wired to endpoints)
"""

from __future__ import annotations

import logging

from fastapi import Request, HTTPException, status

from src.domain.gateway.rate_limiter import RateLimitStore
from src.engine.gateway.rate_limiter import InMemoryRateLimitStore

logger = logging.getLogger(__name__)

# Singleton rate limit store. Uses Redis-backed store in production (PR5),
# transparently falling back to in-memory when Redis is unavailable.
try:
    from src.engine.gateway.redis_rate_limiter import RedisRateLimitStore

    _rate_limit_store: RateLimitStore = RedisRateLimitStore()
except Exception as e:  # pragma: no cover — defensive init guard
    logger.warning("Redis rate limiter unavailable, using in-memory: %s", e)
    _rate_limit_store = InMemoryRateLimitStore()


def get_rate_limit_store() -> RateLimitStore:
    """Expose the rate limit store for dependency injection/testing."""
    return _rate_limit_store


def require_rate_limit(endpoint: str, max_requests: int, window_seconds: int):
    """FastAPI dependency factory. Enforces rate limit on a route.

    Usage:
        @router.post("/login")
        async def login(
            _: None = Depends(require_rate_limit("/auth/login", 20, 60)),
        ):

    Args:
        endpoint: Logical endpoint name for rate limit key
        max_requests: Maximum requests allowed in the window
        window_seconds: Window duration in seconds
    """
    async def _check(request: Request) -> None:
        store = get_rate_limit_store()
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{endpoint}"

        allowed, remaining = store.check_and_increment(
            key, max_requests, window_seconds,
        )

        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "endpoint": endpoint,
                    "client_ip": client_ip[:7] + "***",
                    "max_requests": max_requests,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={
                    "Retry-After": str(window_seconds),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Attach rate limit info to response headers via request.state
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_max = max_requests

    return _check
