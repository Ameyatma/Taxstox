"""Enterprise Billing — Subscription plans and usage-based billing.

CA firms subscribe to plans: Free (limited), Professional (per-filing),
Enterprise (unlimited). Usage is metered per filing.

Traceability: C21.8 (Billing & Subscription — 0%→50%, P5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class SubscriptionTier(str, Enum):
    FREE = "free"                      # Up to 10 filings/month
    PROFESSIONAL = "professional"      # Pay-per-filing, unlimited clients
    ENTERPRISE = "enterprise"          # Unlimited filings, white-label, SSO


class BillingPeriod(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


# ── Tier Limits ───────────────────────────────────────────────────────

TIER_CONFIG = {
    SubscriptionTier.FREE: {
        "max_clients": 10,
        "max_filings_per_month": 10,
        "max_staff": 2,
        "white_label": False,
        "sso": False,
        "price_per_month": Decimal("0"),
        "price_per_filing": Decimal("0"),
    },
    SubscriptionTier.PROFESSIONAL: {
        "max_clients": 500,
        "max_filings_per_month": 999999,
        "max_staff": 20,
        "white_label": False,
        "sso": False,
        "price_per_month": Decimal("999"),
        "price_per_filing": Decimal("149"),
    },
    SubscriptionTier.ENTERPRISE: {
        "max_clients": 999999,
        "max_filings_per_month": 999999,
        "max_staff": 999999,
        "white_label": True,
        "sso": True,
        "price_per_month": Decimal("4999"),
        "price_per_filing": Decimal("0"),
    },
}


@dataclass(frozen=True)
class UsageRecord:
    """A single usage event for per-filing billing."""

    record_id: UUID
    tenant_id: UUID
    event_type: str                      # "filing_completed", "client_added"
    quantity: int = 1
    recorded_at: str = ""

    def __post_init__(self) -> None:
        if not self.recorded_at:
            object.__setattr__(self, "recorded_at",
                              datetime.now(timezone.utc).isoformat())

    @staticmethod
    def filing(tenant_id: UUID, count: int = 1) -> UsageRecord:
        return UsageRecord(
            record_id=uuid4(), tenant_id=tenant_id,
            event_type="filing_completed", quantity=count,
        )


@dataclass(frozen=True)
class Invoice:
    """A billing invoice for a tenant. Immutable value object."""

    invoice_id: UUID
    tenant_id: UUID
    period_start: str                    # ISO date
    period_end: str
    items: tuple[InvoiceItem, ...]
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    status: InvoiceStatus = InvoiceStatus.PENDING
    issued_at: str = ""
    paid_at: str = ""

    def __post_init__(self) -> None:
        if not self.issued_at:
            object.__setattr__(self, "issued_at",
                              datetime.now(timezone.utc).isoformat())

    @property
    def is_paid(self) -> bool:
        return self.status == InvoiceStatus.PAID


@dataclass(frozen=True)
class InvoiceItem:
    """A single line item on an invoice."""

    description: str
    quantity: int
    unit_price: Decimal
    amount: Decimal


@dataclass
class Subscription:
    """Tenant subscription. Entity within Tenant aggregate."""

    subscription_id: UUID
    tenant_id: UUID
    tier: SubscriptionTier = SubscriptionTier.FREE
    period: BillingPeriod = BillingPeriod.MONTHLY
    status: str = "active"               # active, past_due, cancelled
    current_period_start: str = ""
    current_period_end: str = ""
    filings_this_period: int = 0
    clients_this_period: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.current_period_start:
            self.current_period_start = self.created_at

    @staticmethod
    def create(tenant_id: UUID, tier: SubscriptionTier = SubscriptionTier.FREE) -> Subscription:
        return Subscription(
            subscription_id=uuid4(), tenant_id=tenant_id, tier=tier,
        )

    @property
    def tier_config(self) -> dict:
        return TIER_CONFIG.get(self.tier, TIER_CONFIG[SubscriptionTier.FREE])

    @property
    def max_clients(self) -> int:
        return self.tier_config["max_clients"]

    @property
    def max_filings_per_month(self) -> int:
        return self.tier_config["max_filings_per_month"]

    @property
    def max_staff(self) -> int:
        return self.tier_config["max_staff"]

    @property
    def can_white_label(self) -> bool:
        return self.tier_config["white_label"]

    @property
    def can_sso(self) -> bool:
        return self.tier_config["sso"]

    @property
    def price_per_filing(self) -> Decimal:
        return self.tier_config["price_per_filing"]

    def can_add_client(self, current_count: int) -> bool:
        return current_count < self.max_clients

    def can_file(self) -> bool:
        return self.filings_this_period < self.max_filings_per_month

    def record_filing(self, count: int = 1) -> bool:
        """Record a filing. Returns True if within limits."""
        if self.filings_this_period + count > self.max_filings_per_month:
            return False
        self.filings_this_period += count
        self._touch()
        return True

    def upgrade(self, tier: SubscriptionTier) -> None:
        """Upgrade subscription tier."""
        self.tier = tier
        self._touch()

    def cancel(self) -> None:
        self.status = "cancelled"
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()
