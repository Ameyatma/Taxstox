"""Unit tests for Integration bounded context — M10."""

from uuid import uuid4

from src.domain.integration.ports import (
    ApiKey,
    ApiKeyScope,
    WebhookEvent,
    WebhookSubscription,
    PANVerificationResult,
)


class TestApiKey:
    def test_create_api_key(self):
        key = ApiKey(
            key_id=uuid4(),
            tenant_id=uuid4(),
            name="Test Key",
            scope=ApiKeyScope.READ,
            key_prefix="tax_abc12",
            created_at="2026-07-05T00:00:00Z",
        )
        assert key.scope == ApiKeyScope.READ
        assert key.is_active


class TestWebhookSubscription:
    def test_create_subscription(self):
        sub = WebhookSubscription.create(
            tenant_id=uuid4(),
            url="https://example.com/webhook",
            events=[WebhookEvent.FILING_COMPLETE, WebhookEvent.REFUND_CREDITED],
        )
        assert WebhookEvent.FILING_COMPLETE in sub.events
        assert len(sub.secret) == 64  # hex token_hex(32)
        assert sub.is_active

    def test_event_not_in_subscription(self):
        sub = WebhookSubscription.create(
            tenant_id=uuid4(),
            url="https://example.com/webhook",
            events=[WebhookEvent.FILING_COMPLETE],
        )
        assert WebhookEvent.REFUND_CREDITED not in sub.events


class TestPANVerificationResult:
    def test_valid_pan(self):
        result = PANVerificationResult(
            pan="ABCDE1234F", name="TEST USER", is_valid=True,
            aadhaar_linked=True,
        )
        assert result.is_valid
        assert result.aadhaar_linked

    def test_invalid_pan(self):
        result = PANVerificationResult(
            pan="INVALID", name="", is_valid=False,
        )
        assert not result.is_valid


class TestWebhookDispatcher:
    def test_signature_is_deterministic(self):
        from src.infrastructure.integrations.webhooks import HttpxWebhookDispatcher
        sig1 = HttpxWebhookDispatcher._sign("test", "secret")
        sig2 = HttpxWebhookDispatcher._sign("test", "secret")
        assert sig1 == sig2

    def test_different_secret_different_signature(self):
        from src.infrastructure.integrations.webhooks import HttpxWebhookDispatcher
        sig1 = HttpxWebhookDispatcher._sign("test", "secret1")
        sig2 = HttpxWebhookDispatcher._sign("test", "secret2")
        assert sig1 != sig2
