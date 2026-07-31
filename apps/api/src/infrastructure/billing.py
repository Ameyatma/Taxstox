"""Billing Infrastructure Adapter — Subscription management and invoice generation.

Implements billing domain interfaces with stub payment gateway.
For production: Integrate with Razorpay/Stripe for actual payments.

Traceability: C21.8 (Billing & Subscription — 0%→50%, P5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from src.domain.enterprise.billing import (
    Subscription,
    SubscriptionTier,
    BillingPeriod,
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    UsageRecord,
    TIER_CONFIG,
)


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class PaymentRecord:
    """A payment transaction record. Infrastructure entity."""

    payment_id: UUID
    invoice_id: UUID
    tenant_id: UUID
    amount: Decimal
    status: PaymentStatus = PaymentStatus.PENDING
    gateway_reference: str = ""          # Razorpay/Stripe payment ID
    paid_at: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class BillingGateway:
    """Abstract billing gateway interface.

    Production: Implement with Razorpay or Stripe API.
    Current: Stub with realistic behavior for development.
    """

    @staticmethod
    def create_payment(
        tenant_id: UUID, invoice: Invoice,
    ) -> PaymentRecord:
        """Create a payment for an invoice. Returns payment record."""
        # Stub: In production, create Razorpay order / Stripe PaymentIntent
        return PaymentRecord(
            payment_id=uuid4(), invoice_id=invoice.invoice_id,
            tenant_id=tenant_id, amount=invoice.total,
            gateway_reference=f"stub-payment-{uuid4().hex[:12]}",
        )

    @staticmethod
    def confirm_payment(payment: PaymentRecord) -> PaymentRecord:
        """Confirm a payment. Marks as completed."""
        # Stub: In production, verify payment status with gateway webhook
        payment.status = PaymentStatus.COMPLETED
        payment.paid_at = datetime.now(timezone.utc).isoformat()
        return payment


class SubscriptionManager:
    """Manages tenant subscription lifecycle.

    Infrastructure service. Coordinates between domain Subscription
    entity and billing gateway.
    """

    @staticmethod
    def create_subscription(
        tenant_id: UUID, tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Subscription:
        """Create a new subscription for a tenant."""
        return Subscription.create(tenant_id, tier)

    @staticmethod
    def upgrade(subscription: Subscription, new_tier: SubscriptionTier) -> bool:
        """Upgrade a subscription. Enterprise can't be downgraded (simplified)."""
        current_level = list(SubscriptionTier).index(subscription.tier)
        new_level = list(SubscriptionTier).index(new_tier)
        if new_level <= current_level:
            return False  # No downgrades without explicit cancellation
        subscription.upgrade(new_tier)
        return True

    @staticmethod
    def check_filing_limit(subscription: Subscription) -> bool:
        """Check if tenant can file another return. Returns True if within limits."""
        return subscription.can_file()

    @staticmethod
    def record_usage(subscription: Subscription, count: int = 1) -> bool:
        """Record usage. Returns True if within limits."""
        return subscription.record_filing(count)

    @staticmethod
    def generate_invoice(
        subscription: Subscription, tenant_id: UUID,
        usage_records: list[UsageRecord] | None = None,
    ) -> Invoice:
        """Generate an invoice for a subscription period.

        Args:
            subscription: Tenant's subscription
            tenant_id: Tenant UUID
            usage_records: Optional list of usage records this period

        Returns:
            Invoice with items calculated from tier pricing
        """
        items: list[InvoiceItem] = []
        tier_config = TIER_CONFIG.get(subscription.tier, TIER_CONFIG[SubscriptionTier.FREE])

        # Base subscription fee
        base_price = tier_config["price_per_month"]
        if base_price > 0:
            items.append(InvoiceItem(
                description=f"{subscription.tier.value.title()} Plan — {subscription.period.value}",
                quantity=1,
                unit_price=base_price,
                amount=base_price,
            ))

        # Per-filing charges
        price_per = tier_config["price_per_filing"]
        filing_count = subscription.filings_this_period
        if price_per > 0 and filing_count > 0:
            filing_total = price_per * filing_count
            items.append(InvoiceItem(
                description=f"Per-filing charges ({filing_count} filings)",
                quantity=filing_count,
                unit_price=price_per,
                amount=filing_total,
            ))

        subtotal = sum(item.amount for item in items)
        tax = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))  # 18% GST
        total = (subtotal + tax).quantize(Decimal("0.01"))

        return Invoice(
            invoice_id=uuid4(), tenant_id=tenant_id,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
            items=tuple(items), subtotal=subtotal, tax=tax, total=total,
        )


class UsageTracker:
    """Tracks and meters tenant usage for billing."""

    def __init__(self) -> None:
        self._records: dict[UUID, list[UsageRecord]] = {}

    def record(self, tenant_id: UUID, event_type: str, quantity: int = 1) -> UsageRecord:
        """Record a usage event."""
        record = UsageRecord(
            record_id=uuid4(), tenant_id=tenant_id,
            event_type=event_type, quantity=quantity,
        )
        if tenant_id not in self._records:
            self._records[tenant_id] = []
        self._records[tenant_id].append(record)
        return record

    def get_usage(self, tenant_id: UUID, event_type: str | None = None) -> list[UsageRecord]:
        """Get usage records for a tenant, optionally filtered by type."""
        records = self._records.get(tenant_id, [])
        if event_type:
            records = [r for r in records if r.event_type == event_type]
        return records

    def count_this_month(self, tenant_id: UUID, event_type: str = "filing_completed") -> int:
        """Count usage events this calendar month."""
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0).isoformat()
        records = self._records.get(tenant_id, [])
        return sum(
            1 for r in records
            if r.event_type == event_type and r.recorded_at >= month_start
        )
