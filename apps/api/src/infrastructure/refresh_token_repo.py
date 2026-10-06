"""Refresh token repository — stores and validates refresh tokens."""

import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.extras

from src.db.database import get_db


class RefreshTokenRepository:
    """Manages refresh tokens in the database."""

    TOKEN_BYTES = 32
    TTL_HOURS = 24 * 7  # 7 days

    def __init__(self):
        self.conn = get_db()

    def _hash_token(self, token: str) -> str:
        """Hash a refresh token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def create_token(self, user_id: str) -> tuple[str, str]:
        """Create a new refresh token for the user.

        Returns (raw_token, token_id) where raw_token is the plain token
        (to be set in a cookie) and token_id is the database record id.
        """
        raw_token = os.urandom(self.TOKEN_BYTES).hex()
        token_hash = self._hash_token(raw_token)
        token_id = str(uuid.uuid4())[:12]
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.TTL_HOURS)

        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)
               VALUES (%s, %s, %s, %s)""",
            (token_id, user_id, token_hash, expires_at),
        )
        cur.close()
        return raw_token, token_id

    def verify_token(self, token: str) -> dict | None:
        """Verify a refresh token and return the associated user data if valid.

        Returns None if the token is invalid, expired, or revoked.
        """
        token_hash = self._hash_token(token)
        cur = self.conn.cursor()
        cur.execute(
            """SELECT rt.id, rt.user_id, rt.expires_at, rt.revoked, u.id as uid, u.email, u.pan, u.name
               FROM refresh_tokens rt
               JOIN users u ON rt.user_id = u.id
               WHERE rt.token_hash = %s""",
            (token_hash,),
        )
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        d = dict(row)
        if d["revoked"] or d["expires_at"] < datetime.now(timezone.utc):
            return None
        return d

    def revoke_token(self, token_id: str) -> None:
        """Mark a refresh token as revoked."""
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE refresh_tokens SET revoked = TRUE WHERE id = %s",
            (token_id,),
        )
        cur.close()

    def revoke_all_user_tokens(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user."""
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE refresh_tokens SET revoked = TRUE WHERE user_id = %s",
            (user_id,),
        )
        cur.close()

    def rotate_token(self, old_token: str) -> tuple[str, str] | None:
        """Rotate a refresh token: revoke the old one and issue a new one.

        Returns (new_raw_token, new_token_id) if the old token was valid,
        otherwise None.
        """
        token_data = self.verify_token(old_token)
        if token_data is None:
            return None
        self.revoke_token(token_data["id"])
        new_raw, new_id = self.create_token(token_data["user_id"])
        return new_raw, new_id


def init_refresh_tokens_table() -> None:
    """Create the refresh_tokens table if it doesn't exist."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id),
                token_hash TEXT NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                revoked BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.close()
        conn.commit()
    finally:
        conn.close()