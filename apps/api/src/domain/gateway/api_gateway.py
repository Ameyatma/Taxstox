"""API Gateway — Rate limiting, API key management, gateway configuration.

Traceability: C16.1 (API Gateway — 40%→70%, P7)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class RateLimitWindow(str, Enum):
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass(frozen=True)
class RateLimitPolicy:
    """Rate limit configuration for an API endpoint. Value object."""

    endpoint: str                      # "/api/v1/upload"
    max_requests: int
    window: RateLimitWindow = RateLimitWindow.MINUTE
    per_tenant: bool = True            # If True, limit is per-tenant

    @property
    def window_seconds(self) -> int:
        return {
            RateLimitWindow.SECOND: 1, RateLimitWindow.MINUTE: 60,
            RateLimitWindow.HOUR: 3600, RateLimitWindow.DAY: 86400,
        }.get(self.window, 60)


@dataclass
class ApiKey:
    """API key for programmatic access. Entity."""

    key_id: UUID
    tenant_id: UUID
    name: str                          # "Production Key", "Development Key"
    key_prefix: str                    # "tsk_" — first 4 chars visible
    key_hash: str                      # SHA-256 hash of full key
    scopes: list[str] = field(default_factory=list)  # ["read:filings", "write:filings"]
    is_active: bool = True
    last_used: str = ""
    expires_at: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def revoke(self) -> None:
        self.is_active = False

    @staticmethod
    def create(tenant_id: UUID, name: str, scopes: list[str] | None = None) -> ApiKey:
        import secrets
        return ApiKey(
            key_id=uuid4(), tenant_id=tenant_id, name=name,
            key_prefix=f"tsk_{secrets.token_hex(4)}",
            key_hash=f"sha256:{secrets.token_hex(32)}",
            scopes=scopes or ["read:filings"],
        )


@dataclass
class ApiGatewayConfig:
    """API gateway configuration. Entity."""

    config_id: UUID
    rate_limits: list[RateLimitPolicy] = field(default_factory=list)
    global_rate_limit: int = 1000      # Requests per minute globally
    enabled: bool = True

    @staticmethod
    def create() -> ApiGatewayConfig:
        config = ApiGatewayConfig(config_id=uuid4())
        # Default rate limits for key endpoints
        config.rate_limits = [
            RateLimitPolicy("/api/v1/upload", 10, RateLimitWindow.MINUTE),
            RateLimitPolicy("/api/v1/process", 30, RateLimitWindow.MINUTE),
            RateLimitPolicy("/api/v1/export", 10, RateLimitWindow.MINUTE),
            RateLimitPolicy("/api/v1/auth/login", 20, RateLimitWindow.MINUTE),
            RateLimitPolicy("/api/v1/auth/register", 5, RateLimitWindow.MINUTE),
        ]
        return config

    def get_limit(self, endpoint: str) -> RateLimitPolicy | None:
        for rl in self.rate_limits:
            if rl.endpoint == endpoint:
                return rl
        return None
