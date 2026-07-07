"""DPDP Act Consent Management — Aggregate Root.

Consent is a first-class domain concept per the Digital Personal Data
Protection Act, 2023. Every data collection purpose requires granular,
versioned, withdrawable consent with audit trail.

Traceability: C1.8 (Consent Management — Critical), C17.3 (DPDP),
             R02 (DPDP Act non-compliance — Critical)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Protocol
from uuid import UUID, uuid4


class ConsentStatus(str, Enum):
    GRANTED = "granted"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


@dataclass(frozen=True)
class ConsentPurpose:
    """A specific purpose for which data is collected."""
    purpose_id: str         # e.g., "tax_computation", "itr_filing"
    description: str        # Plain-language description
    legal_basis: str        # e.g., "Consent under DPDP Act 2023 §5"
    retention_days: int     # How long data is retained for this purpose


@dataclass
class ConsentRecord:
    """A single consent grant from a data principal (user)."""
    record_id: UUID
    user_id: UUID
    purpose_id: str
    status: ConsentStatus = ConsentStatus.GRANTED
    version: int = 1
    granted_at: str = ""
    withdrawn_at: str = ""
    tenant_id: Optional[UUID] = None
    ip_address: str = ""     # For audit trail, not stored persistently in domain

    def __post_init__(self) -> None:
        if not self.granted_at:
            self.granted_at = datetime.now(timezone.utc).isoformat()

    def withdraw(self) -> None:
        self.status = ConsentStatus.WITHDRAWN
        self.withdrawn_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_active(self) -> bool:
        return self.status == ConsentStatus.GRANTED


@dataclass
class ConsentAggregate:
    """All consent records for a data principal (user)."""
    user_id: UUID
    records: list[ConsentRecord] = field(default_factory=list)

    def grant(self, purpose_id: str, tenant_id: Optional[UUID] = None) -> ConsentRecord:
        """Grant consent for a purpose. Revokes previous version if exists."""
        # Withdraw any existing consent for this purpose
        for r in self.records:
            if r.purpose_id == purpose_id and r.is_active:
                r.withdraw()

        record = ConsentRecord(
            record_id=uuid4(), user_id=self.user_id, purpose_id=purpose_id,
            version=len([r for r in self.records if r.purpose_id == purpose_id]) + 1,
            tenant_id=tenant_id,
        )
        self.records.append(record)
        return record

    def withdraw(self, purpose_id: str) -> bool:
        """Withdraw consent for a purpose. Returns True if consent was active."""
        for r in self.records:
            if r.purpose_id == purpose_id and r.is_active:
                r.withdraw()
                return True
        return False

    def has_consent(self, purpose_id: str) -> bool:
        """Check if active consent exists for a purpose."""
        return any(
            r.purpose_id == purpose_id and r.is_active
            for r in self.records
        )

    @property
    def active_purposes(self) -> list[str]:
        return [r.purpose_id for r in self.records if r.is_active]


class ConsentRepository(Protocol):
    """Repository for consent records. Infrastructure implements."""
    def get_by_user(self, user_id: UUID) -> ConsentAggregate: ...
    def save(self, aggregate: ConsentAggregate) -> None: ...


# ── Standard DPDP Purposes ───────────────────────────────────────────

TAX_COMPUTATION_PURPOSE = ConsentPurpose(
    purpose_id="tax_computation",
    description="Process your financial data to compute income tax liability",
    legal_basis="Consent under DPDP Act 2023 §5 — necessary for service provision",
    retention_days=365 * 7,  # 7 years per IT Act
)

ITR_FILING_PURPOSE = ConsentPurpose(
    purpose_id="itr_filing",
    description="Generate and validate ITR JSON for filing with ITD",
    legal_basis="Consent under DPDP Act 2023 §5 — necessary for service provision",
    retention_days=365 * 7,
)

ANALYTICS_PURPOSE = ConsentPurpose(
    purpose_id="analytics",
    description="Anonymized usage analytics to improve the platform",
    legal_basis="Consent under DPDP Act 2023 §5 — optional",
    retention_days=365 * 2,
)

ALL_PURPOSES = [TAX_COMPUTATION_PURPOSE, ITR_FILING_PURPOSE, ANALYTICS_PURPOSE]
