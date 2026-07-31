"""Payment Gateway — Payment methods, transactions, gateway types.

Traceability: C16.6 (Payment Gateway — 0%→50%, P7)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class PaymentGatewayType(str, Enum):
    RAZORPAY = "razorpay"
    STRIPE = "stripe"
    PHONEPE = "phonepe"


class PaymentStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class PaymentMethod:
    """A saved payment method. Value object."""

    method_id: UUID
    method_type: str                   # "card", "upi", "net_banking", "wallet"
    last_four: str = ""                # Last 4 digits (card) or VPA (UPI)
    is_default: bool = False


@dataclass
class PaymentTransaction:
    """A payment transaction. Entity."""

    transaction_id: UUID
    tenant_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str = "INR"
    gateway: PaymentGatewayType = PaymentGatewayType.RAZORPAY
    gateway_order_id: str = ""
    gateway_payment_id: str = ""
    status: PaymentStatus = PaymentStatus.CREATED
    description: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: str = ""
    completed_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def mark_completed(self, gateway_payment_id: str) -> None:
        self.status = PaymentStatus.COMPLETED
        self.gateway_payment_id = gateway_payment_id
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def mark_failed(self, reason: str = "") -> None:
        self.status = PaymentStatus.FAILED
        self.metadata["failure_reason"] = reason

    def refund(self, gateway_refund_id: str) -> None:
        self.status = PaymentStatus.REFUNDED
        self.metadata["refund_id"] = gateway_refund_id

    @staticmethod
    def create(
        tenant_id: UUID, user_id: UUID, amount: Decimal,
        description: str = "", gateway: PaymentGatewayType = PaymentGatewayType.RAZORPAY,
    ) -> PaymentTransaction:
        return PaymentTransaction(
            transaction_id=uuid4(), tenant_id=tenant_id, user_id=user_id,
            amount=amount, description=description, gateway=gateway,
        )
