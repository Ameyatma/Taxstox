"""Fernet Encryption Adapter — Infrastructure implementation of EncryptionService.

Traceability: C17.1 (Data Encryption), R03 (PII breach)
"""

from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet

from src.domain.security.encryption import (
    DataClassification,
    EncryptionResult,
    EncryptionService,
    mask_pan,
    mask_aadhaar,
    mask_mobile,
    mask_email,
)


class FernetEncryptionService:
    """AES-256 encryption via Fernet. Implements EncryptionService protocol.

    Key from TAXSTOX_ENCRYPTION_KEY env var. Generated once:
        python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
    """

    def __init__(self) -> None:
        key = os.getenv("TAXSTOX_ENCRYPTION_KEY")
        if not key:
            raise RuntimeError(
                "TAXSTOX_ENCRYPTION_KEY environment variable is required. "
                "Generate: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        self._key_id = "fernet-v1"

    def encrypt(self, plaintext: str, classification: DataClassification) -> EncryptionResult:
        if not plaintext:
            return EncryptionResult(ciphertext=b"", key_id=self._key_id)
        ciphertext = self._fernet.encrypt(plaintext.encode("utf-8"))
        return EncryptionResult(ciphertext=ciphertext, key_id=self._key_id)

    def decrypt(self, ciphertext: bytes, key_id: str = "") -> str:
        if not ciphertext:
            return ""
        return self._fernet.decrypt(ciphertext).decode("utf-8")

    def mask(self, value: str, classification: DataClassification) -> str:
        """Mask value based on type detection."""
        if classification != DataClassification.RESTRICTED:
            return value

        if len(value) == 10 and value[:5].isalpha() and value[5:9].isdigit():
            return mask_pan(value)
        if len(value) == 12 and value.isdigit():
            return mask_aadhaar(value)
        if len(value) >= 10 and value.isdigit():
            return mask_mobile(value[:10])
        if "@" in value:
            return mask_email(value)
        return "***"
