"""Identity Proofing — KYC verification, PAN verification, trust levels.

Traceability: C17.7 (Identity Proofing — 0%→50%, P7)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class KYCStatus(str, Enum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class VerificationMethod(str, Enum):
    PAN_NSDL = "pan_nsdl"              # NSDL PAN verification API
    AADHAAR_EKYC = "aadhaar_ekyc"      # UIDAI Aadhaar e-KYC
    DIGILOCKER = "digilocker"          # DigiLocker document verification
    VIDEO_KYC = "video_kyc"            # Video-based KYC
    MANUAL = "manual"                   # Manual document review


@dataclass(frozen=True)
class VerificationAttempt:
    """A single KYC verification attempt. Value object."""

    attempt_id: UUID
    method: VerificationMethod
    status: KYCStatus
    attempted_at: str
    reference_id: str = ""             # External verification reference
    failure_reason: str = ""


@dataclass
class IdentityVerification:
    """Tracks identity verification status for a user. Entity."""

    user_id: UUID
    pan_verified: bool = False
    pan_verified_at: str = ""
    aadhaar_verified: bool = False
    email_verified: bool = False
    mobile_verified: bool = False
    kyc_status: KYCStatus = KYCStatus.NOT_STARTED
    kyc_completed_at: str = ""
    trust_level: int = 0               # 0-100; determines access to features
    attempts: list[VerificationAttempt] = field(default_factory=list)

    def verify_pan(self, reference_id: str = "") -> None:
        self.pan_verified = True
        self.pan_verified_at = datetime.now(timezone.utc).isoformat()
        self._recompute_trust()

    def complete_kyc(self, method: VerificationMethod, reference_id: str = "") -> None:
        self.kyc_status = KYCStatus.VERIFIED
        self.kyc_completed_at = datetime.now(timezone.utc).isoformat()
        self.attempts.append(VerificationAttempt(
            attempt_id=uuid4(), method=method, status=KYCStatus.VERIFIED,
            attempted_at=datetime.now(timezone.utc).isoformat(),
            reference_id=reference_id,
        ))
        self._recompute_trust()

    def fail_kyc(self, method: VerificationMethod, reason: str) -> None:
        self.kyc_status = KYCStatus.REJECTED
        self.attempts.append(VerificationAttempt(
            attempt_id=uuid4(), method=method, status=KYCStatus.REJECTED,
            attempted_at=datetime.now(timezone.utc).isoformat(),
            failure_reason=reason,
        ))

    def _recompute_trust(self) -> None:
        """Compute trust level based on verified credentials."""
        level = 0
        if self.email_verified:
            level += 10
        if self.mobile_verified:
            level += 10
        if self.pan_verified:
            level += 30
        if self.aadhaar_verified:
            level += 30
        if self.kyc_status == KYCStatus.VERIFIED:
            level += 20
        self.trust_level = min(100, level)

    @property
    def can_file(self) -> bool:
        """Minimum trust to file ITR: PAN verified."""
        return self.pan_verified

    @property
    def can_use_enterprise_features(self) -> bool:
        """Enterprise features require KYC completion."""
        return self.trust_level >= 70

    @staticmethod
    def create(user_id: UUID) -> IdentityVerification:
        return IdentityVerification(user_id=user_id)
