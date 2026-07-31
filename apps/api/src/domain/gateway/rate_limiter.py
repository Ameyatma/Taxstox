"""Rate Limiting — Storage-agnostic rate limit backend protocol.

Domain layer. Zero framework imports. Pure Python.

Enables future Redis-backed implementation without upstream code changes.

Traceability: PR1.3 (Rate Limiting — storage-agnostic interface)
"""

from __future__ import annotations

from typing import Protocol


class RateLimitStore(Protocol):
    """Storage-agnostic rate limit backend.

    In-memory implementation for development (InMemoryRateLimitStore).
    Redis implementation for production (PR5).
    """

    def check_and_increment(
        self, key: str, max_requests: int, window_seconds: int,
    ) -> tuple[bool, int]:
        """Check if request is within limit and increment counter.

        Returns (allowed: bool, remaining: int).
        """
        ...

    def reset(self, key: str) -> None:
        """Reset rate limit counter for a key."""
        ...
