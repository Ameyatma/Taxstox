"""P7 Tests — Commercial Launch: Operations, API Gateway, Payments, Identity.

Tests: 28
"""

import pytest
from decimal import Decimal
from uuid import uuid4

# ── Operations ──

from src.domain.operations.backup_dr import BackupConfig, DRPlan, DRTestResult
from src.domain.operations.identity_proofing import (
    IdentityVerification, KYCStatus, VerificationMethod,
)
from src.domain.operations.secrets import SecretMetadata, RotationSchedule, RotationFrequency


class TestBackupDR:
    def test_backup_config_creation(self):
        config = BackupConfig.create()
        assert config.retention_days == 90
        assert config.frequency.value == "daily"

    def test_dr_plan_compliance(self):
        plan = DRPlan.create()
        assert plan.rpo_minutes <= 5
        assert plan.rto_minutes <= 30
        assert plan.failover_procedure != ""
        assert plan.rollback_procedure != ""

    def test_dr_test_recording(self):
        plan = DRPlan.create()
        plan.record_dr_test(DRTestResult.PASSED)
        assert plan.dr_test_result == DRTestResult.PASSED
        assert plan.last_dr_test != ""


class TestIdentityProofing:
    def test_create_verification(self):
        v = IdentityVerification.create(uuid4())
        assert v.trust_level == 0
        assert v.kyc_status == KYCStatus.NOT_STARTED

    def test_trust_level_computation(self):
        v = IdentityVerification.create(uuid4())
        v.email_verified = True
        v.mobile_verified = True
        v.verify_pan()
        assert v.trust_level == 50  # 10 + 10 + 30
        assert v.can_file

    def test_kyc_completion(self):
        v = IdentityVerification.create(uuid4())
        v.email_verified = True
        v.mobile_verified = True
        v.verify_pan()
        v.complete_kyc(VerificationMethod.PAN_NSDL)
        assert v.kyc_status == KYCStatus.VERIFIED
        assert v.trust_level == 70  # 10 + 10 + 30 + 20
        assert v.can_use_enterprise_features

    def test_kyc_failure(self):
        v = IdentityVerification.create(uuid4())
        v.fail_kyc(VerificationMethod.MANUAL, "Document mismatch")
        assert v.kyc_status == KYCStatus.REJECTED

    def test_cannot_file_without_pan(self):
        v = IdentityVerification.create(uuid4())
        assert not v.can_file


class TestSecrets:
    def test_secret_metadata_creation(self):
        s = SecretMetadata.create("TEST_KEY", "Test secret")
        assert s.name == "TEST_KEY"
        assert s.version == 1

    def test_secret_rotation_schedule(self):
        s = SecretMetadata.create("ROTATING_KEY")
        s.set_rotation(RotationFrequency.QUARTERLY, auto=True)
        assert s.rotation is not None
        assert s.rotation.frequency == RotationFrequency.QUARTERLY

    def test_production_secrets_inventory(self):
        from src.domain.operations.secrets import PRODUCTION_SECRET_MANIFEST
        assert len(PRODUCTION_SECRET_MANIFEST) >= 8

    def test_encryption_key_marked(self):
        from src.domain.operations.secrets import PRODUCTION_SECRET_MANIFEST
        enc_key = [s for s in PRODUCTION_SECRET_MANIFEST if s.name == "TAXSTOX_ENCRYPTION_KEY"]
        assert len(enc_key) == 1
        assert enc_key[0].is_encryption_key


# ── API Gateway ──

from src.domain.gateway.api_gateway import (
    ApiGatewayConfig, RateLimitPolicy, RateLimitWindow, ApiKey,
)
from src.domain.gateway.developer_portal import (
    DeveloperRegistration, ApiProduct, API_PRODUCTS,
)
from src.engine.gateway.rate_limiter import InMemoryRateLimitStore, ApiKeyManager


class TestRateLimiting:
    def test_rate_limit_allowed(self):
        engine = InMemoryRateLimitStore()
        policy = RateLimitPolicy("/test", 5, RateLimitWindow.MINUTE)
        for _ in range(5):
            assert engine.check(None, "/test", policy)

    def test_rate_limit_blocked(self):
        engine = InMemoryRateLimitStore()
        policy = RateLimitPolicy("/test", 2, RateLimitWindow.MINUTE)
        assert engine.check(None, "/test", policy)
        assert engine.check(None, "/test", policy)
        assert not engine.check(None, "/test", policy)

    def test_remaining_count(self):
        engine = InMemoryRateLimitStore()
        policy = RateLimitPolicy("/test", 100, RateLimitWindow.MINUTE)
        engine.check(None, "/test", policy, cost=4)
        remaining = engine.remaining(None, "/test", policy)
        # Allow for small refill due to time elapsed
        assert 95.8 < remaining < 100.2


class TestApiGateway:
    def test_gateway_config_creation(self):
        config = ApiGatewayConfig.create()
        assert len(config.rate_limits) == 5
        assert config.global_rate_limit == 1000

    def test_get_endpoint_limit(self):
        config = ApiGatewayConfig.create()
        limit = config.get_limit("/api/v1/upload")
        assert limit is not None
        assert limit.max_requests == 10

    def test_api_key_creation(self):
        key = ApiKey.create(uuid4(), "Production Key")
        assert key.key_prefix.startswith("tsk_")
        assert key.is_active

    def test_api_key_revocation(self):
        key = ApiKey.create(uuid4(), "Temp Key")
        key.revoke()
        assert not key.is_active


class TestDeveloperPortal:
    def test_registration(self):
        reg = DeveloperRegistration.create("Acme Corp", "dev@acme.com")
        assert reg.status == "pending"

    def test_approval_flow(self):
        reg = DeveloperRegistration.create("Acme Corp", "dev@acme.com")
        reg.approve()
        assert reg.status == "approved"

    def test_subscribe_to_product(self):
        reg = DeveloperRegistration.create("Acme Corp", "dev@acme.com")
        reg.subscribe("itr-filing")
        assert "itr-filing" in reg.subscribed_products

    def test_api_product_catalog(self):
        assert len(API_PRODUCTS) == 5


# ── Payment Gateway ──

from src.domain.payment.payment_gateway import (
    PaymentTransaction, PaymentGatewayType, PaymentStatus,
)
from src.infrastructure.payment_gateway import PaymentGatewayAdapter


class TestPayments:
    def test_create_transaction(self):
        txn = PaymentTransaction.create(uuid4(), uuid4(), Decimal("999"))
        assert txn.status == PaymentStatus.CREATED
        assert txn.gateway == PaymentGatewayType.RAZORPAY

    def test_mark_completed(self):
        txn = PaymentTransaction.create(uuid4(), uuid4(), Decimal("999"))
        txn.mark_completed("pay_ABC123")
        assert txn.status == PaymentStatus.COMPLETED

    def test_refund(self):
        txn = PaymentTransaction.create(uuid4(), uuid4(), Decimal("999"))
        txn.mark_completed("pay_ABC123")
        txn.refund("rfnd_XYZ789")
        assert txn.status == PaymentStatus.REFUNDED

    def test_gateway_create_order(self):
        txn = PaymentTransaction.create(uuid4(), uuid4(), Decimal("1499"))
        order = PaymentGatewayAdapter.create_order(txn)
        assert "order_id" in order
        assert txn.gateway_order_id != ""


# ── Identity Proofing Infrastructure ──

from src.infrastructure.identity_proofing import PANVerificationAdapter


class TestPANVerificationAdapter:
    def test_valid_pan(self):
        result = PANVerificationAdapter.verify("ABCPE1234F", "Test User")
        assert result["verified"]

    def test_invalid_pan_format(self):
        result = PANVerificationAdapter.verify("INVALID", "")
        assert not result["verified"]

    def test_invalid_pan_category(self):
        result = PANVerificationAdapter.verify("ABCDX1234F", "")
        assert not result["verified"]
        assert "category" in result.get("error", "")


# ── Operations Engine ──

from src.engine.operations.monitoring_engine import MonitoringEngine, HealthStatus


class TestMonitoringEngine:
    def test_health_check(self):
        engine = MonitoringEngine()
        health = engine.check_health()
        assert health.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)

    def test_runbook_generation(self):
        engine = MonitoringEngine()
        runbook = engine.generate_runbook()
        assert "Health Check" in runbook
        assert "Escalation" in runbook
