"""Integration Ports — Domain interfaces for external system adapters.

Clean Architecture: domain defines WHAT integrations do.
Infrastructure implements HOW they connect.

Traceability: C16.2 (External Tax APIs), C16.3 (FI Integration),
             C16.5 (CA Software), C16.7 (Webhooks)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, Protocol
from uuid import UUID, uuid4


# ── API Key Management ───────────────────────────────────────────────

class ApiKeyScope(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


@dataclass(frozen=True)
class ApiKey:
    """API key for external system access."""
    key_id: UUID
    tenant_id: UUID
    name: str
    scope: ApiKeyScope
    key_prefix: str        # First 8 chars for identification
    created_at: str
    expires_at: Optional[str] = None
    is_active: bool = True


# ── PAN Verification ──────────────────────────────────────────────────

@dataclass(frozen=True)
class PANVerificationResult:
    """Result from NSDL PAN verification API."""
    pan: str
    name: str
    is_valid: bool
    aadhaar_linked: bool = False
    category: str = ""
    last_updated: str = ""


class PANVerificationPort(Protocol):
    """Port for PAN verification service."""
    async def verify(self, pan: str) -> PANVerificationResult: ...


# ── ITD e-Filing ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class FilingSubmissionResult:
    """Result of ITD e-filing submission."""
    acknowledgement_number: str
    status: str          # "accepted", "rejected", "pending"
    message: str
    submitted_at: str


class ITDFilingPort(Protocol):
    """Port for ITD e-Filing API integration."""
    async def submit(self, itr_json: dict, pan: str, ay: str) -> FilingSubmissionResult: ...
    async def get_status(self, ack_number: str) -> FilingSubmissionResult: ...


# ── Webhook System ────────────────────────────────────────────────────

class WebhookEvent(str, Enum):
    FILING_COMPLETE = "filing.complete"
    FILING_REJECTED = "filing.rejected"
    REFUND_CREDITED = "refund.credited"
    DEADLINE_REMINDER = "deadline.reminder"
    CONSENT_EXPIRING = "consent.expiring"


@dataclass(frozen=True)
class WebhookSubscription:
    """A registered webhook endpoint."""
    subscription_id: UUID
    tenant_id: UUID
    url: str
    events: frozenset[WebhookEvent]
    secret: str                     # HMAC secret for signature verification
    is_active: bool = True
    created_at: str = ""

    @staticmethod
    def create(tenant_id: UUID, url: str, events: list[WebhookEvent]) -> WebhookSubscription:
        import secrets
        return WebhookSubscription(
            subscription_id=uuid4(),
            tenant_id=tenant_id,
            url=url,
            events=frozenset(events),
            secret=secrets.token_hex(32),
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class WebhookDispatcher(Protocol):
    """Port for webhook delivery."""
    async def dispatch(self, event: WebhookEvent, payload: dict, tenant_id: UUID) -> int: ...


# ── Financial Institution Integration ─────────────────────────────────

@dataclass(frozen=True)
class FIAccount:
    """Linked financial institution account."""
    account_id: UUID
    tenant_id: UUID
    user_id: UUID
    institution: str         # "zerodha", "groww", "hdfc_bank"
    account_type: str        # "demat", "savings", "trading"
    linked_at: str
    last_synced_at: str = ""
    is_active: bool = True


class FIDataPort(Protocol):
    """Port for financial institution data access."""
    async def fetch_capital_gains(self, account: FIAccount, fy: str) -> list[dict]: ...
    async def fetch_interest_certificate(self, account: FIAccount, fy: str) -> dict: ...
