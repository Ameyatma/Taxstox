"""Webhook Dispatcher — Infrastructure adapter.

Delivers webhook events to registered subscriber endpoints with
HMAC-SHA256 signature verification.

Traceability: C16.7 (Webhook System)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from uuid import UUID

import httpx

from src.domain.integration.ports import (
    WebhookEvent,
    WebhookSubscription,
    WebhookDispatcher,
)

logger = logging.getLogger(__name__)


class HttpxWebhookDispatcher:
    """Delivers webhooks via HTTP POST with HMAC signature."""

    def __init__(self, subscriptions: list[WebhookSubscription]) -> None:
        self._subscriptions = {s.subscription_id: s for s in subscriptions}

    async def dispatch(
        self, event: WebhookEvent, payload: dict, tenant_id: UUID,
    ) -> int:
        """Dispatch event to all matching subscriptions. Returns count delivered."""
        delivered = 0
        body = json.dumps({
            "event": event.value,
            "payload": payload,
            "tenant_id": str(tenant_id),
        })

        for sub in self._subscriptions.values():
            if not sub.is_active or sub.tenant_id != tenant_id:
                continue
            if event not in sub.events:
                continue

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    signature = self._sign(body, sub.secret)
                    response = await client.post(
                        sub.url,
                        content=body,
                        headers={
                            "Content-Type": "application/json",
                            "X-Webhook-Signature": signature,
                            "X-Webhook-Event": event.value,
                        },
                    )
                    if response.status_code < 300:
                        delivered += 1
                    else:
                        logger.warning(
                            "Webhook delivery failed",
                            extra={"url": sub.url, "status": response.status_code},
                        )
            except Exception as e:
                logger.error("Webhook delivery error", extra={"url": sub.url, "error": str(e)})

        return delivered

    @staticmethod
    def _sign(payload: str, secret: str) -> str:
        """HMAC-SHA256 signature."""
        return hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256,
        ).hexdigest()
