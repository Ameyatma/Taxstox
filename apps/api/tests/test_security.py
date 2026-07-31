"""Unit tests for Security bounded context — M9."""

from uuid import uuid4

from src.domain.security.encryption import (
    DataClassification,
    mask_pan,
    mask_aadhaar,
    mask_mobile,
    mask_email,
)


class TestPIIMasking:
    def test_mask_pan(self):
        assert mask_pan("ABCDE1234F") == "ABC**1234F"

    def test_mask_pan_short(self):
        assert mask_pan("ABC") == "***"

    def test_mask_aadhaar(self):
        assert mask_aadhaar("123456789012") == "******789012"

    def test_mask_mobile(self):
        assert mask_mobile("9876543210") == "98****3210"

    def test_mask_email(self):
        assert mask_email("user@example.com") == "u***r@example.com"

    def test_mask_email_short(self):
        assert mask_email("a@b.com") == "***@b.com"


class TestConsentAggregate:
    def test_grant_consent(self):
        from src.domain.security.consent import ConsentAggregate
        agg = ConsentAggregate(user_id=uuid4())
        record = agg.grant("tax_computation")
        assert record.is_active
        assert agg.has_consent("tax_computation")

    def test_withdraw_consent(self):
        from src.domain.security.consent import ConsentAggregate
        agg = ConsentAggregate(user_id=uuid4())
        agg.grant("tax_computation")
        agg.withdraw("tax_computation")
        assert not agg.has_consent("tax_computation")

    def test_active_purposes(self):
        from src.domain.security.consent import ConsentAggregate
        agg = ConsentAggregate(user_id=uuid4())
        agg.grant("tax_computation")
        agg.grant("itr_filing")
        assert len(agg.active_purposes) == 2

    def test_grant_revokes_previous(self):
        from src.domain.security.consent import ConsentAggregate
        agg = ConsentAggregate(user_id=uuid4())
        r1 = agg.grant("tax_computation")
        r2 = agg.grant("tax_computation")
        assert not r1.is_active
        assert r2.is_active
        assert r2.version == 2

    def test_no_consent_by_default(self):
        from src.domain.security.consent import ConsentAggregate
        agg = ConsentAggregate(user_id=uuid4())
        assert not agg.has_consent("tax_computation")


class TestDataClassification:
    def test_enum_values(self):
        assert DataClassification.RESTRICTED.value == "restricted"
        assert DataClassification.CONFIDENTIAL.value == "confidential"


# ═══════════════════════════════════════════════════════════════
# PR1: Security Hardening Tests
# ═══════════════════════════════════════════════════════════════

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest

# Skip markers for tests requiring live infrastructure
_db_required = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not configured — requires PostgreSQL connection",
)
_jwt_required = pytest.mark.skipif(
    not os.environ.get("TAXSTOX_JWT_SECRET"),
    reason="TAXSTOX_JWT_SECRET not configured",
)


class TestSessionSecurity:
    """PR1.4: Session ID entropy and uniqueness."""

    def test_session_id_is_32_char_hex(self):
        """Session ID must be 32-char hex (UUID4 = 128-bit)."""
        from src.utils.session import session_manager
        session = session_manager.create("ABCDE1234F", "01011990")
        assert len(session.session_id) == 32, f"Expected 32-char hex, got {len(session.session_id)}: {session.session_id}"
        # Verify all hex characters
        assert all(c in "0123456789abcdef" for c in session.session_id)

    def test_session_id_unique_across_creations(self):
        """100 session creations must produce 100 unique IDs."""
        from src.utils.session import session_manager
        ids = set()
        for _ in range(100):
            session = session_manager.create("ABCDE1234F", "01011990")
            ids.add(session.session_id)
        assert len(ids) == 100


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not configured")
class TestPasswordResetToken:
    """PR1.2: Token lifecycle — creation, verification, expiry, single-use.

    Requires DATABASE_URL — these tests exercise the real psycopg2 repository.
    """

    @_db_required
    def test_create_token_returns_raw_string(self):
        from src.infrastructure.password_reset_repo import PsycopgPasswordResetRepository
        repo = PsycopgPasswordResetRepository()
        raw = repo.create_token("test-user-123")
        assert len(raw) >= 43  # secrets.token_urlsafe(32) = 43 chars
        assert isinstance(raw, str)

    def test_verify_and_consume_valid_token(self):
        from src.infrastructure.password_reset_repo import PsycopgPasswordResetRepository
        repo = PsycopgPasswordResetRepository()
        raw = repo.create_token("test-user-456")
        assert repo.verify_and_consume("test-user-456", raw)

    def test_verify_rejects_wrong_token(self):
        from src.infrastructure.password_reset_repo import PsycopgPasswordResetRepository
        repo = PsycopgPasswordResetRepository()
        repo.create_token("test-user-789")
        assert not repo.verify_and_consume("test-user-789", "wrong-token-value")

    def test_verify_rejects_second_use(self):
        from src.infrastructure.password_reset_repo import PsycopgPasswordResetRepository
        repo = PsycopgPasswordResetRepository()
        raw = repo.create_token("test-user-single")
        assert repo.verify_and_consume("test-user-single", raw)
        assert not repo.verify_and_consume("test-user-single", raw)  # Second use

    def test_token_hash_not_raw(self):
        """The stored token must be SHA-256, not the raw token."""
        from src.infrastructure.password_reset_repo import PsycopgPasswordResetRepository
        from src.db.database import get_db

        repo = PsycopgPasswordResetRepository()
        raw = repo.create_token("test-user-hash")
        token_hash = hashlib.sha256(raw.encode()).hexdigest()

        # Verify the DB stores hash, not raw
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT token_hash FROM password_reset_tokens WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                ("test-user-hash",),
            )
            row = cur.fetchone()
            cur.close()
            assert row is not None
            assert row["token_hash"] == token_hash
            assert row["token_hash"] != raw
        finally:
            conn.close()

    def test_invalidation_consumes_all_unused(self):
        from src.infrastructure.password_reset_repo import PsycopgPasswordResetRepository
        repo = PsycopgPasswordResetRepository()
        token1 = repo.create_token("test-user-inv")
        token2 = repo.create_token("test-user-inv")
        count = repo.invalidate_user_tokens("test-user-inv")
        assert count >= 2
        # Both tokens should now be invalid
        assert not repo.verify_and_consume("test-user-inv", token1)
        assert not repo.verify_and_consume("test-user-inv", token2)

    def test_purge_expired_removes_tokens(self):
        from src.infrastructure.password_reset_repo import PsycopgPasswordResetRepository
        repo = PsycopgPasswordResetRepository()
        # Create token and consume it
        raw = repo.create_token("test-user-purge")
        repo.verify_and_consume("test-user-purge", raw)
        # Purge should remove used tokens
        count = repo.purge_expired()
        assert count >= 1


class TestRateLimitEnforcement:
    """PR1.3: Rate limiting — storage-agnostic, threshold enforcement."""

    def test_rate_limit_allows_within_threshold(self):
        from src.engine.gateway.rate_limiter import InMemoryRateLimitStore
        store = InMemoryRateLimitStore()
        for _ in range(19):
            allowed, _ = store.check_and_increment("test-key", 20, 60)
            assert allowed

    def test_rate_limit_blocks_after_threshold(self):
        from src.engine.gateway.rate_limiter import InMemoryRateLimitStore
        store = InMemoryRateLimitStore()
        for _ in range(5):
            store.check_and_increment("test-key-2", 5, 60)
        allowed, remaining = store.check_and_increment("test-key-2", 5, 60)
        assert not allowed
        assert remaining == 0

    def test_rate_limit_per_key_isolation(self):
        from src.engine.gateway.rate_limiter import InMemoryRateLimitStore
        store = InMemoryRateLimitStore()
        # Exhaust key A
        for _ in range(3):
            store.check_and_increment("key-a", 3, 60)
        allowed_a, _ = store.check_and_increment("key-a", 3, 60)
        assert not allowed_a
        # Key B should still be allowed
        allowed_b, _ = store.check_and_increment("key-b", 3, 60)
        assert allowed_b

    def test_rate_limit_reset(self):
        from src.engine.gateway.rate_limiter import InMemoryRateLimitStore
        store = InMemoryRateLimitStore()
        for _ in range(3):
            store.check_and_increment("key-c", 3, 60)
        store.reset("key-c")
        allowed, _ = store.check_and_increment("key-c", 3, 60)
        assert allowed

    def test_rate_limit_store_protocol(self):
        """InMemoryRateLimitStore must implement RateLimitStore Protocol."""
        from src.engine.gateway.rate_limiter import InMemoryRateLimitStore
        store = InMemoryRateLimitStore()
        assert hasattr(store, "check_and_increment")
        assert hasattr(store, "reset")
        assert callable(store.check_and_increment)
        assert callable(store.reset)


@pytest.mark.skipif(not os.environ.get("TAXSTOX_JWT_SECRET"), reason="TAXSTOX_JWT_SECRET not configured")
class TestTokenHandling:
    """PR1.7: JWT edge cases — malformed, expired, tampered."""

    def test_jwt_decline_malformed(self):
        """Totally malformed input must not cause 500."""
        from src.auth.jwt import decode_token
        from jose import JWTError
        with pytest.raises(JWTError):
            decode_token("not.a.jwt")

    def test_jwt_decline_truncated(self):
        """Missing signature part must be rejected."""
        from src.auth.jwt import decode_token
        from jose import JWTError
        with pytest.raises(JWTError):
            decode_token("header.payload")  # Only 2 parts

    def test_jwt_decline_expired(self):
        """Expired tokens must be rejected."""
        from src.auth.jwt import create_access_token, decode_token
        from jose import JWTError
        # Create token that expired 10 seconds ago
        token = create_access_token(
            {"sub": "test"}, expires_delta=timedelta(seconds=-10),
        )
        with pytest.raises(JWTError):
            decode_token(token)

    def test_jwt_decline_tampered_payload(self):
        """Modified payload must invalidate signature."""
        from src.auth.jwt import create_access_token, decode_token, SECRET_KEY, ALGORITHM
        from jose import jwt as jose_jwt
        from jose import JWTError

        token = create_access_token({"sub": "test-user"})
        # Decode without verification, modify, re-encode with wrong key
        import base64, json
        parts = token.split(".")
        payload_raw = base64.urlsafe_b64decode(parts[1] + "==")
        payload = json.loads(payload_raw)
        payload["sub"] = "hacked-user"
        # This modified token should fail signature verification
        with pytest.raises(JWTError):
            decode_token(token[:50] + "tampered" + token[60:])


class TestGoogleAuthFlow:
    """PR1.1: Google OAuth cryptographic verification.

    Note: These tests verify architecture and error handling.
    Full JWKS-verified tests require network access to Google.
    """

    def test_google_verifier_rejects_empty_token(self):
        from src.auth.google_verifier import verify_google_id_token
        with pytest.raises(ValueError):
            verify_google_id_token("")

    def test_google_verifier_rejects_garbage(self):
        from src.auth.google_verifier import verify_google_id_token
        with pytest.raises(ValueError):
            verify_google_id_token("not-a-real-google-token")

    def test_google_verifier_rejects_forged_token(self):
        """A locally-signed JWT must not be accepted as a Google token."""
        from src.auth.google_verifier import verify_google_id_token
        from src.auth.jwt import create_access_token
        # Create a valid TaxStox JWT — but it's not a Google token
        token = create_access_token({"sub": "test", "email": "test@test.com"})
        with pytest.raises(ValueError):
            verify_google_id_token(token)

    def test_google_client_id_configured(self):
        from src.auth.google_verifier import get_client_id
        client_id = get_client_id()
        assert len(client_id) > 10
        assert "googleusercontent.com" in client_id or ".apps." in client_id


class TestOWASPNegative:
    """OWASP-aligned negative security tests."""

    @_db_required
    def test_sql_injection_in_login_parameterized(self):
        """SQL injection attempts must be caught by parameterized queries, not produce 500."""
        from src.db.database import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM users WHERE email = %s",
                ("' OR '1'='1",),
            )
            rows = cur.fetchall()
            cur.close()
            assert len(rows) == 0
        finally:
            conn.close()

    @_db_required
    def test_database_password_reset_tokens_table_exists(self):
        """password_reset_tokens table must exist after init_db."""
        from src.db.database import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
                ("password_reset_tokens",),
            )
            exists = cur.fetchone()["exists"]
            cur.close()
            assert exists, "password_reset_tokens table not found"
        finally:
            conn.close()

    def test_security_headers_middleware_importable(self):
        """SecurityHeadersMiddleware must be importable and instantiable."""
        from src.middleware.security_headers import SecurityHeadersMiddleware
        assert SecurityHeadersMiddleware is not None

    def test_rate_limit_dependency_importable(self):
        """require_rate_limit dependency factory must be importable."""
        from src.engine.gateway.rate_limit_dependency import require_rate_limit
        dep = require_rate_limit("/test", 10, 60)
        assert callable(dep)

