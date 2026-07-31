"""Payment Gateway Adapter — Razorpay/Stripe integration stub.

Production: Integrate with Razorpay API for Indian payments.
Current: Stub with documented integration path.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from src.domain.payment.payment_gateway import (
    PaymentTransaction, PaymentGatewayType, PaymentStatus,
)

logger = logging.getLogger(__name__)


class PaymentGatewayAdapter:
    """Payment gateway abstraction. Production: Razorpay SDK."""

    @staticmethod
    def create_order(
        transaction: PaymentTransaction, receipt: str = "",
    ) -> dict:
        """Create a payment order with the gateway.

        Production: Razorpay `client.order.create()`
        Returns: {order_id, amount, currency, ...}
        """
        import secrets
        order_id = f"order_{secrets.token_hex(12)}"
        transaction.gateway_order_id = order_id

        logger.info("PAYMENT ORDER CREATED", extra={
            "order_id": order_id,
            "amount": str(transaction.amount),
            "tenant_id": str(transaction.tenant_id),
        })

        return {
            "order_id": order_id,
            "amount": int(transaction.amount * 100),  # Paisa
            "currency": transaction.currency,
            "receipt": receipt or f"rcpt_{transaction.transaction_id.hex[:12]}",
        }

    @staticmethod
    def verify_payment(
        gateway_payment_id: str, gateway_order_id: str, gateway_signature: str,
    ) -> bool:
        """Verify payment signature from gateway webhook.

        Production: Razorpay `client.utility.verify_payment_signature()`
        """
        logger.info("PAYMENT VERIFIED", extra={
            "payment_id": gateway_payment_id,
            "order_id": gateway_order_id,
        })
        return True

    @staticmethod
    def process_refund(
        transaction: PaymentTransaction, amount: Decimal | None = None,
    ) -> dict:
        """Process a refund through the gateway.

        Production: Razorpay `client.payment.refund()`
        """
        import secrets
        refund_id = f"rfnd_{secrets.token_hex(12)}"
        refund_amount = amount or transaction.amount

        logger.info("REFUND PROCESSED", extra={
            "refund_id": refund_id,
            "amount": str(refund_amount),
            "original_transaction": str(transaction.transaction_id),
        })

        transaction.refund(refund_id)
        return {"refund_id": refund_id, "amount": str(refund_amount), "status": "processed"}
