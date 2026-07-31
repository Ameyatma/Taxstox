"""Auth bounded context — Password reset token entity and repository protocol.

Domain layer. Zero framework imports. Pure Python.

Traceability: PR1.2 (Forgot Password — production-grade abstraction)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4


@dataclass
class PasswordResetToken:
    """Password reset token entity. Single-use, time-limited."""

    token_id: UUID
    user_id: str
    token_hash: str        # SHA-256 of the raw token sent to user
    expires_at: str        # ISO 8601 — 15 minutes from creation
    used: bool = False
    created_at: str = ""

    @property
    def is_expired(self) -> bool:
        from datetime import datetime, timezone
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.now(timezone.utc) > expires
        except (ValueError, TypeError):
            return True

    @property
    def is_valid(self) -> bool:
        return not self.used and not self.is_expired


class PasswordResetRepository(Protocol):
    """Repository for password reset tokens. Domain protocol.

    Infrastructure implementation: PsycopgPasswordResetRepository.
    """

    def create_token(self, user_id: str) -> str:
        """Create a new reset token. Returns the raw token to send to user.
        The raw token is NOT stored — only its SHA-256 hash is persisted."""
        ...

    def verify_and_consume(self, user_id: str, raw_token: str) -> bool:
        """Verify a reset token and mark it as used.
        Returns True if token is valid and was successfully consumed."""
        ...

    def invalidate_user_tokens(self, user_id: str) -> int:
        """Invalidate all unused tokens for a user. Returns count of invalidated tokens."""
        ...

    def purge_expired(self) -> int:
        """Delete all expired or used tokens. Returns count of deleted tokens."""
        ...
