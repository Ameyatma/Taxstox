"""Redis-backed Rate Limit Store — Global, atomic rate limiting for production.

Implements RateLimitStore Protocol from domain. Uses Redis INCR + EXPIRE for
atomic check-and-increment with TTL-based expiry. Gracefully degrades to
in-memory store when Redis is unavailable.

Traceability: PRRP-DEFER-002 (Global Redis Rate Limiting → PR5)
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from src.domain.gateway.rate_limiter import RateLimitStore

if TYPE_CHECKING:
    import redis

logger = logging.getLogger(__name__)


class RedisRateLimitStore:
    """Redis-backed rate limit store implementing RateLimitStore Protocol.

    Uses Redis INCR for atomic counter increment and EXPIRE for TTL-based
    window management. Each key gets its own TTL aligned with the window.

    Semantics:
    - check_and_increment: INCR key → if > max_requests, return (False, 0)
                           else EXPIRE key window_seconds, return (True, remaining)
    - reset: DEL key
    - On Redis failure: logs error, falls back to in-memory behavior for the call
    """

    def __init__(
        self,
        redis_client: "redis.Redis | None" = None,
        *,
        key_prefix: str = "ratelimit:",
        fallback_store: "RateLimitStore | None" = None,
    ) -> None:
        """
        Args:
            redis_client: Pre-configured redis.Redis instance. If None, attempts
                to create one from REDIS_URL env var. If that fails, uses fallback.
            key_prefix: Prefix for all Redis keys (default "ratelimit:")
            fallback_store: In-memory store to use when Redis is unavailable.
                If None, creates a new InMemoryRateLimitStore internally.
        """
        self._key_prefix = key_prefix
        self._fallback = fallback_store
        self._redis = redis_client
        self._redis_available = False
        self._init_redis(redis_client)

    def _init_redis(self, redis_client: "redis.Redis | None") -> None:
        """Initialize Redis connection, test availability."""
        if redis_client is not None:
            self._redis = redis_client
            self._test_connection()
            return

        # Try to create from env
        import os
        redis_url = os.environ.get("REDIS_URL")
        if not redis_url:
            logger.info("REDIS_URL not set — rate limiter will use in-memory fallback")
            return

        try:
            import redis
            self._redis = redis.Redis.from_url(
                redis_url,
                socket_connect_timeout=2,
                socket_timeout=2,
                decode_responses=True,
            )
            self._test_connection()
        except Exception as e:
            logger.warning("Failed to initialize Redis for rate limiting: %s", e)
            self._redis = None

    def _test_connection(self) -> bool:
        """Test Redis connection with PING."""
        if self._redis is None:
            return False
        try:
            self._redis.ping()
            self._redis_available = True
            logger.info("Redis rate limiter connected and available")
            return True
        except Exception as e:
            logger.warning("Redis ping failed: %s — using in-memory fallback", e)
            self._redis_available = False
            self._redis = None
            return False

    def _get_fallback(self) -> "RateLimitStore":
        """Get or create the in-memory fallback store."""
        if self._fallback is not None:
            return self._fallback
        # Lazy import to avoid circular dependency
        from src.engine.gateway.rate_limiter import InMemoryRateLimitStore
        if not hasattr(self, "_internal_fallback"):
            self._internal_fallback = InMemoryRateLimitStore()
        return self._internal_fallback

    def _with_fallback(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        """Execute operation with Redis, falling back to in-memory on failure."""
        if self._redis_available and self._redis is not None:
            try:
                return self._redis_check_and_increment(key, max_requests, window_seconds)
            except Exception as e:
                logger.warning("Redis rate limit operation failed, falling back: %s", e)
                self._redis_available = False

        # Fallback path
        return self._get_fallback().check_and_increment(key, max_requests, window_seconds)

    def _redis_check_and_increment(
        self, key: str, max_requests: int, window_seconds: int
    ) -> tuple[bool, int]:
        """Atomic INCR + EXPIRE implementation.

        Uses a Lua script so the increment + conditional TTL is atomic and the
        window is a true fixed window (TTL is set once, on first request, and
        not extended by subsequent requests).
        """
        redis_key = f"{self._key_prefix}{key}"

        # Lua: incr key; if new (count==1) set expire; return count
        lua = """
        local count = redis.call('incr', KEYS[1])
        if count == 1 then
            redis.call('expire', KEYS[1], ARGV[1])
        end
        return count
        """
        current_count = self._redis.eval(lua, 1, redis_key, window_seconds)

        if current_count > max_requests:
            return False, 0

        remaining = max_requests - current_count
        return True, remaining

    def check_and_increment(
        self, key: str, max_requests: int, window_seconds: int
    ) -> tuple[bool, int]:
        """Check if request is within limit and increment counter.

        Returns (allowed: bool, remaining: int).
        """
        return self._with_fallback(key, max_requests, window_seconds)

    def reset(self, key: str) -> None:
        """Reset rate limit counter for a key."""
        if self._redis_available and self._redis is not None:
            try:
                redis_key = f"{self._key_prefix}{key}"
                self._redis.delete(redis_key)
                return
            except Exception as e:
                logger.warning("Redis reset failed, falling back: %s", e)
                self._redis_available = False

        self._get_fallback().reset(key)

    # Legacy API compatibility (delegate to fallback)
    def check(
        self, tenant_id, endpoint: str, policy, cost: int = 1
    ) -> bool:
        """Legacy check API — delegates to fallback."""
        from src.domain.gateway.api_gateway import RateLimitPolicy
        if isinstance(policy, RateLimitPolicy):
            key = f"{tenant_id}:{endpoint}" if tenant_id and policy.per_tenant else endpoint
            return self.check_and_increment(key, policy.max_requests, policy.window_seconds)[0]
        return self._get_fallback().check(tenant_id, endpoint, policy, cost)

    def remaining(
        self, tenant_id, endpoint: str, policy
    ) -> int:
        """Legacy remaining API — delegates to fallback."""
        from src.domain.gateway.api_gateway import RateLimitPolicy
        if isinstance(policy, RateLimitPolicy):
            key = f"{tenant_id}:{endpoint}" if tenant_id and policy.per_tenant else endpoint
            return self.check_and_increment(key, policy.max_requests, policy.window_seconds)[1]
        return self._get_fallback().remaining(tenant_id, endpoint, policy)