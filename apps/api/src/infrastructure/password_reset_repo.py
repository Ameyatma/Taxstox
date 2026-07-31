"""Password Reset Token repository — psycopg2 implementation.

Infrastructure layer. Uses the existing database connection pool.
Implements PasswordResetRepository from domain.

Traceability: PR1.2 (Forgot Password — database-backed persistence)
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from src.db.database import get_db, _exec_sql
from src.domain.auth.password_reset import PasswordResetRepository


class PsycopgPasswordResetRepository:
    """PostgreSQL-backed password reset token repository.

    Implements PasswordResetRepository Protocol using the existing
    psycopg2 connection from db/database.py.
    """

    TOKEN_TTL_MINUTES = 15

    @staticmethod
    def create_token(user_id: str) -> str:
        """Create a new reset token. Stores SHA-256 hash in DB.

        Returns the raw token (not the hash) for delivery to the user.
        """
        raw_token = secrets.token_urlsafe(32)  # 256-bit
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = (datetime.now(timezone.utc) + timedelta(
            minutes=PsycopgPasswordResetRepository.TOKEN_TTL_MINUTES
        )).isoformat()

        conn = get_db()
        try:
            _exec_sql(conn, """
                INSERT INTO password_reset_tokens
                    (id, user_id, token_hash, expires_at, used, created_at)
                VALUES (%s, %s, %s, %s, FALSE, %s)
            """, (str(uuid.uuid4()), user_id, token_hash, expires_at,
                  datetime.now(timezone.utc).isoformat()))
        finally:
            conn.close()

        return raw_token

    @staticmethod
    def verify_and_consume(user_id: str, raw_token: str) -> bool:
        """Verify a reset token and mark it as used (single-use).

        Returns True if the token exists, is unused, and has not expired.
        Returns False otherwise.
        """
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        conn = get_db()
        try:
            cur = conn.cursor()

            # Find valid token
            cur.execute("""
                SELECT id, expires_at, used FROM password_reset_tokens
                WHERE user_id = %s AND token_hash = %s
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, token_hash))
            row = cur.fetchone()
            cur.close()

            if not row:
                return False

            if row["used"]:
                return False

            # Check expiry
            expires = row["expires_at"]
            if isinstance(expires, str):
                expires = datetime.fromisoformat(expires)
            if datetime.now(timezone.utc) > expires:
                return False

            # Mark as used
            cur2 = conn.cursor()
            cur2.execute("""
                UPDATE password_reset_tokens SET used = TRUE WHERE id = %s
            """, (row["id"],))
            cur2.close()

            return True
        finally:
            conn.close()

    @staticmethod
    def invalidate_user_tokens(user_id: str) -> int:
        """Invalidate all unused tokens for a user. Returns count."""
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE password_reset_tokens
                SET used = TRUE
                WHERE user_id = %s AND used = FALSE
            """, (user_id,))
            count = cur.rowcount
            cur.close()
            return count
        finally:
            conn.close()

    @staticmethod
    def purge_expired() -> int:
        """Delete all expired or used tokens. Returns count."""
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM password_reset_tokens
                WHERE used = TRUE
                   OR expires_at < %s
            """, (datetime.now(timezone.utc).isoformat(),))
            count = cur.rowcount
            cur.close()
            return count
        finally:
            conn.close()
