"""Data Encryption — Domain interface + value objects.

Traceability: C17.1 (Data Encryption), SEC-001 (dev secret), R03 (PII breach)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass(frozen=True)
class EncryptionResult:
    """Result of an encryption operation."""
    ciphertext: bytes
    key_id: str = ""  # Which key was used (for key rotation)


class EncryptionService(Protocol):
    """Domain interface for data encryption. Infrastructure provides implementation.

    Clean Architecture: domain defines WHAT, infrastructure provides HOW.
    """

    def encrypt(self, plaintext: str, classification: DataClassification) -> EncryptionResult: ...

    def decrypt(self, ciphertext: bytes, key_id: str) -> str: ...

    def mask(self, value: str, classification: DataClassification) -> str: ...


# ── PII Masking (pure domain — no infrastructure needed) ─────────────

def mask_pan(pan: str) -> str:
    """Mask PAN: ABCDE1234F → ABC**1234F."""
    if not pan or len(pan) < 10:
        return "***"
    return f"{pan[:3]}**{pan[5:]}"


def mask_aadhaar(aadhaar: str) -> str:
    """Mask Aadhaar: 123456789012 → ******789012."""
    if not aadhaar or len(aadhaar) < 12:
        return "***"
    return f"******{aadhaar[6:]}"


def mask_mobile(mobile: str) -> str:
    """Mask mobile: 9876543210 → 98****3210."""
    if not mobile or len(mobile) < 10:
        return "***"
    return f"{mobile[:2]}****{mobile[6:]}"


def mask_email(email: str) -> str:
    """Mask email: user@example.com → u***r@example.com."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"***@{domain}"
    return f"{local[0]}***{local[-1]}@{domain}"
