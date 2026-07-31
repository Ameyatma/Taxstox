"""Secrets Management — Metadata, rotation schedules, and compliance.

Traceability: C17.5 (Secrets Management — 40%→70%, P7)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class RotationFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


@dataclass(frozen=True)
class RotationSchedule:
    """Secret rotation schedule. Value object."""

    frequency: RotationFrequency
    last_rotated: str = ""
    next_rotation: str = ""
    auto_rotate: bool = False


@dataclass
class SecretMetadata:
    """Metadata for a managed secret. Entity — the actual secret value
    is stored in the secrets manager (AWS/Azure/HashiCorp)."""

    secret_id: UUID
    name: str                          # "TAXSTOX_JWT_SECRET", "DB_PASSWORD"
    description: str = ""
    rotation: RotationSchedule | None = None
    created_at: str = ""
    version: int = 1
    environment: str = "production"    # "development", "staging", "production"
    is_encryption_key: bool = False    # Special handling for FERNET_KEY

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @staticmethod
    def create(name: str, description: str = "", environment: str = "production") -> SecretMetadata:
        return SecretMetadata(
            secret_id=uuid4(), name=name, description=description,
            environment=environment,
        )

    def set_rotation(self, frequency: RotationFrequency, auto: bool = False) -> None:
        self.rotation = RotationSchedule(frequency=frequency, auto_rotate=auto)

    @property
    def needs_rotation(self) -> bool:
        if not self.rotation or not self.rotation.next_rotation:
            return False
        return datetime.now(timezone.utc).isoformat() >= self.rotation.next_rotation


# ── Required Secrets Inventory ───────────────────────────────────────

REQUIRED_SECRETS = [
    ("TAXSTOX_JWT_SECRET", "JWT signing key — HS256, min 256 bits"),
    ("TAXSTOX_ENCRYPTION_KEY", "Fernet encryption key for PII at rest"),
    ("DB_PASSWORD", "Neon PostgreSQL connection password"),
    ("GOOGLE_CLIENT_ID", "Google OAuth client ID"),
    ("GOOGLE_CLIENT_SECRET", "Google OAuth client secret"),
    ("DEEPSEEK_API_KEY", "DeepSeek AI API key for tax updates summarization"),
    ("RENDER_API_KEY", "Render deploy API key"),
    ("SMTP_PASSWORD", "Email notification SMTP password"),
    ("SMS_GATEWAY_KEY", "SMS gateway API key"),
]

PRODUCTION_SECRET_MANIFEST = [
    SecretMetadata.create(name, desc, "production")
    for name, desc in REQUIRED_SECRETS
]
# Encryption key needs special handling
for s in PRODUCTION_SECRET_MANIFEST:
    if s.name == "TAXSTOX_ENCRYPTION_KEY":
        s.is_encryption_key = True
        s.set_rotation(RotationFrequency.ANNUALLY)
    elif s.name in ("TAXSTOX_JWT_SECRET", "DB_PASSWORD"):
        s.set_rotation(RotationFrequency.QUARTERLY)
