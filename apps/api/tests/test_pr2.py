"""PR2 Tests — Data Protection & Audit: PAN encryption, audit trail, startup key.

Tests: 12
"""

import os
import pytest
from decimal import Decimal
from uuid import uuid4

from src.domain.security.encryption import DataClassification
from src.infrastructure.encryption import FernetEncryptionService
from src.engine.audit import AuditContext, AuditTrail, AuditEventType
from src.engine.regime_optimizer_v2 import RegimeOptimizerV2
from src.engine.rules.config import rule_repository
from src.models.financial_year import FinancialYear


# ═══════════════════════════════════════════════════════════════
# PAN Encryption Tests
# ═══════════════════════════════════════════════════════════════

class TestPANEncryption:
    """PR2.1: Application-level PAN encryption round-trip."""

    @pytest.mark.skipif(
        not os.environ.get("TAXSTOX_ENCRYPTION_KEY"),
        reason="TAXSTOX_ENCRYPTION_KEY not configured",
    )
    def test_encrypt_decrypt_round_trip(self):
        """Encrypt then decrypt must produce the original PAN."""
        svc = FernetEncryptionService()
        pan = "ABCDE1234F"
        result = svc.encrypt(pan, DataClassification.RESTRICTED)
        assert result.ciphertext != b"", "Ciphertext must not be empty"
        assert result.key_id == "fernet-v1"
        decrypted = svc.decrypt(result.ciphertext, result.key_id)
        assert decrypted == pan

    @pytest.mark.skipif(
        not os.environ.get("TAXSTOX_ENCRYPTION_KEY"),
        reason="TAXSTOX_ENCRYPTION_KEY not configured",
    )
    def test_encrypt_empty_pan(self):
        """Empty PAN must produce empty ciphertext."""
        svc = FernetEncryptionService()
        result = svc.encrypt("", DataClassification.RESTRICTED)
        assert result.ciphertext == b""

    @pytest.mark.skipif(
        not os.environ.get("TAXSTOX_ENCRYPTION_KEY"),
        reason="TAXSTOX_ENCRYPTION_KEY not configured",
    )
    def test_decrypt_empty_ciphertext(self):
        """Empty ciphertext must produce empty string."""
        svc = FernetEncryptionService()
        result = svc.decrypt(b"", "")
        assert result == ""

    @pytest.mark.skipif(
        not os.environ.get("TAXSTOX_ENCRYPTION_KEY"),
        reason="TAXSTOX_ENCRYPTION_KEY not configured",
    )
    def test_encrypt_produces_different_ciphertext(self):
        """Same PAN encrypted twice must produce different ciphertext (nonce)."""
        svc = FernetEncryptionService()
        r1 = svc.encrypt("ABCDE1234F", DataClassification.RESTRICTED)
        r2 = svc.encrypt("ABCDE1234F", DataClassification.RESTRICTED)
        assert r1.ciphertext != r2.ciphertext, "Fernet must use unique IV per encryption"

    @pytest.mark.skipif(
        not os.environ.get("TAXSTOX_ENCRYPTION_KEY"),
        reason="TAXSTOX_ENCRYPTION_KEY not configured",
    )
    def test_base64_encoding_round_trip(self):
        """Base64-encoded ciphertext must survive TEXT column storage."""
        import base64
        svc = FernetEncryptionService()
        pan = "ABCDE1234F"
        result = svc.encrypt(pan, DataClassification.RESTRICTED)
        b64 = base64.b64encode(result.ciphertext).decode("utf-8")
        decoded = base64.b64decode(b64)
        decrypted = svc.decrypt(decoded, result.key_id)
        assert decrypted == pan


# ═══════════════════════════════════════════════════════════════
# Audit Trail Tests
# ═══════════════════════════════════════════════════════════════

class TestAuditTrailWiring:
    """PR2.2: Audit trail emits events during computation."""

    def test_audit_context_accumulates_events(self):
        """AuditContext must accumulate events internally. PR2."""
        ctx = AuditContext("FY2025-26")
        ctx.event(AuditEventType.INCOME_COMPUTED, "income", "C4.1",
                  "Salary income computed", rule_reference="sec_171")
        ctx.event(AuditEventType.DEDUCTION_APPLIED, "deduction", "C5.1",
                  "80C deduction applied", rule_reference="sec_80c")
        assert ctx.event_count == 2

    def test_build_trail_produces_immutable_trail(self):
        """build_trail() must produce immutable AuditTrail. PR2."""
        ctx = AuditContext("FY2025-26")
        ctx.event(AuditEventType.SLAB_APPLIED, "tax", "C6.1",
                  "Slab tax applied", rule_reference="sec_115bac")
        trail = ctx.build_trail()
        assert isinstance(trail, AuditTrail)
        assert trail.event_count == 1
        assert trail.correlation_id == ctx.correlation_id

    def test_computation_emits_audit_events(self, sample_form16_data):
        """RegimeOptimizerV2 must emit audit events when context provided. PR2."""
        fy = FinancialYear.from_string("FY2025-26")

        optimizer = RegimeOptimizerV2()
        audit_ctx = AuditContext("FY2025-26")

        result = optimizer.optimize(
            form16=sample_form16_data,
            classified_cg=None,
            savings_interest=Decimal("0"),
            other_interest=Decimal("0"),
            financial_year=fy,
            audit_context=audit_ctx,
        )

        assert audit_ctx.event_count >= 14, (
            f"Expected 14+ audit events (7 steps × 2 regimes), got {audit_ctx.event_count}"
        )
        assert result.old_tax >= 0
        assert result.new_tax >= 0

    def test_audit_events_contain_rule_references(self, sample_form16_data):
        """Audit events must include provision references. PR2."""
        optimizer = RegimeOptimizerV2()
        audit_ctx = AuditContext("FY2025-26")

        optimizer.optimize(
            form16=sample_form16_data,
            classified_cg=None,
            savings_interest=Decimal("0"),
            other_interest=Decimal("0"),
            financial_year=FinancialYear.from_string("FY2025-26"),
            audit_context=audit_ctx,
        )

        trail = audit_ctx.build_trail()
        rule_refs = [e.rule_reference for e in trail.events if e.rule_reference]
        assert len(rule_refs) >= 5, f"Expected 5+ events with rule refs, got {len(rule_refs)}"


# ═══════════════════════════════════════════════════════════════
# Encryption Key Enforcement Tests
# ═══════════════════════════════════════════════════════════════

class TestEncryptionKeyEnforcement:
    """PR2.3: Encryption key validated at startup."""

    def test_fernet_service_raises_without_key(self):
        """FernetEncryptionService must raise RuntimeError without key."""
        import os
        saved = os.environ.pop("TAXSTOX_ENCRYPTION_KEY", None)
        try:
            with pytest.raises(RuntimeError, match="TAXSTOX_ENCRYPTION_KEY"):
                FernetEncryptionService()
        finally:
            if saved:
                os.environ["TAXSTOX_ENCRYPTION_KEY"] = saved

    @pytest.mark.skipif(
        not os.environ.get("TAXSTOX_ENCRYPTION_KEY"),
        reason="TAXSTOX_ENCRYPTION_KEY not configured",
    )
    def test_fernet_service_initializes_with_key(self):
        """FernetEncryptionService must initialize when key is set."""
        svc = FernetEncryptionService()
        assert svc._key_id == "fernet-v1"
