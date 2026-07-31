"""Rate Limiter Engine — Token bucket-based rate limiting.

Implements RateLimitStore Protocol from domain. In-memory storage.
Redis-backed implementation will implement the same Protocol (PR5).

Traceability: C16.1 (API Gateway — 40%→70%, P7), PR1.3 (storage-agnostic interface)
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.domain.gateway.rate_limiter import RateLimitStore
from src.domain.gateway.api_gateway import RateLimitPolicy, RateLimitWindow


class InMemoryRateLimitStore:
    """Token bucket rate limiter. Implements RateLimitStore Protocol.

    In-memory (per-process). Suitable for development and single-worker
    deployment. Redis replacement planned for PR5.
    """

    def __init__(self) -> None:
        self._buckets: dict[str, dict] = {}  # key → {tokens, last_refill, max, refill_rate}

    def check_and_increment(
        self, key: str, max_requests: int, window_seconds: int,
    ) -> tuple[bool, int]:
        """Check if request is within rate limit. True = allowed.

        Returns (allowed: bool, remaining: int).
        """
        bucket = self._get_or_create_bucket(key, max_requests, window_seconds)
        self._refill(bucket, max_requests, window_seconds)

        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True, int(bucket["tokens"])
        return False, 0

    def reset(self, key: str) -> None:
        """Reset rate limit counter."""
        self._buckets.pop(key, None)

    # Legacy methods — preserved for backward compatibility with existing callers
    def check(
        self, tenant_id: UUID | None, endpoint: str,
        policy: RateLimitPolicy, cost: int = 1,
    ) -> bool:
        """Check if request is within rate limit. True = allowed. [Legacy API]"""
        key = f"{tenant_id}:{endpoint}" if tenant_id and policy.per_tenant else endpoint
        allowed, _ = self.check_and_increment(key, policy.max_requests, policy.window_seconds)
        return allowed

    def remaining(
        self, tenant_id: UUID | None, endpoint: str, policy: RateLimitPolicy,
    ) -> int:
        """Get remaining requests in current window. [Legacy API]"""
        key = f"{tenant_id}:{endpoint}" if tenant_id and policy.per_tenant else endpoint
        bucket = self._get_or_create_bucket(key, policy.max_requests, policy.window_seconds)
        self._refill(bucket, policy.max_requests, policy.window_seconds)
        return int(bucket["tokens"])

    def _get_or_create_bucket(
        self, key: str, max_requests: int, window_seconds: int,
    ) -> dict:
        if key not in self._buckets:
            self._buckets[key] = {
                "tokens": float(max_requests),
                "max": max_requests,
                "refill_rate": max_requests / window_seconds,
                "last_refill": datetime.now(timezone.utc).timestamp(),
            }
        return self._buckets[key]

    def _refill(
        self, bucket: dict, max_requests: int, window_seconds: int,
    ) -> None:
        now = datetime.now(timezone.utc).timestamp()
        elapsed = now - bucket["last_refill"]
        refill_rate = max_requests / window_seconds
        new_tokens = elapsed * refill_rate
        bucket["tokens"] = min(float(max_requests), bucket["tokens"] + new_tokens)
        bucket["last_refill"] = now


class ApiKeyManager:
    """Manages API key lifecycle — creation, validation, revocation."""

    @staticmethod
    def validate_scopes(key_scopes: list[str], required_scope: str) -> bool:
        """Check if key has the required scope."""
        return required_scope in key_scopes

    @staticmethod
    def generate_key() -> tuple[str, str]:
        """Generate a new API key. Returns (key_prefix, full_key)."""
        import secrets
        prefix = f"tsk_{secrets.token_hex(4)}"
        full = f"{prefix}_{secrets.token_hex(32)}"
        return prefix, full
