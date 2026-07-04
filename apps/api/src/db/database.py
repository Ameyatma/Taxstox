"""Database layer for TaxStox — Neon PostgreSQL via psycopg2."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import bcrypt
import psycopg2
import psycopg2.extras
import psycopg2.errors as pg_errors

# ── Connection ───────────────────────────────────────────────────────

_DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_db():
    """Return a psycopg2 connection with RealDictCursor."""
    if not _DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    conn = psycopg2.connect(_DATABASE_URL)
    conn.autocommit = True
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


# ── SQL helpers ──────────────────────────────────────────────────────

def _exec_sql(conn, sql: str, params: tuple | None = None):
    """Execute a single SQL statement."""
    cur = conn.cursor()
    cur.execute(sql, params or ())
    cur.close()


def _uid() -> str:
    """Return a short unique id."""
    return str(uuid.uuid4())[:12]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row) -> dict | None:
    """Normalise a psycopg2 RealDictRow to a plain dict."""
    return dict(row) if row is not None else None


# ── Password hashing ─────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password[:72].encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password[:72].encode(), hashed.encode())


# ── Schema ───────────────────────────────────────────────────────────

def init_db() -> None:
    """Create tables if they don't exist (idempotent)."""
    conn = get_db()
    try:
        _exec_sql(conn, """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                pan TEXT UNIQUE,
                name TEXT NOT NULL,
                hashed_password TEXT NOT NULL,
                dob TEXT DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        _exec_sql(conn, """
            CREATE TABLE IF NOT EXISTS filings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id),
                assessment_year TEXT NOT NULL,
                itr_type TEXT NOT NULL DEFAULT 'ITR-2',
                regime TEXT,
                gross_income TEXT,
                tax_paid TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        _exec_sql(conn, "CREATE INDEX IF NOT EXISTS idx_filings_user ON filings(user_id, created_at DESC)")
        _exec_sql(conn, "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        _exec_sql(conn, "CREATE INDEX IF NOT EXISTS idx_users_pan ON users(pan)")
        _exec_sql(conn, "ALTER TABLE users ADD COLUMN IF NOT EXISTS dob TEXT DEFAULT ''")
        # Allow NULL pan for Google OAuth users who haven't provided PAN yet
        _exec_sql(conn, "ALTER TABLE users ALTER COLUMN pan DROP NOT NULL")
    finally:
        conn.close()


# ── User CRUD ────────────────────────────────────────────────────────

def create_user(email: str, pan: str, name: str, password: str, dob: str = "") -> dict:
    conn = get_db()
    try:
        user_id = _uid()
        hashed = hash_password(password)
        now = _now_iso()
        _exec_sql(conn,
            "INSERT INTO users (id, email, pan, name, hashed_password, dob, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (user_id, email, pan, name, hashed, dob, now),
        )
        return {"id": user_id, "email": email, "pan": pan, "name": name, "dob": dob}
    except pg_errors.UniqueViolation as e:
        msg = str(e).lower()
        if "email" in msg:
            raise ValueError("An account with this email already exists.")
        if "pan" in msg:
            raise ValueError("An account with this PAN already exists.")
        raise ValueError("Account creation failed.")
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> dict | None:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, pan, name, hashed_password FROM users WHERE email = %s",
            (email,),
        )
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        d = dict(row)
        if not verify_password(password, d["hashed_password"]):
            return None
        return {"id": d["id"], "email": d["email"], "pan": d.get("pan") or "", "name": d["name"]}
    finally:
        conn.close()


def get_user_by_id(user_id: str) -> dict | None:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, pan, name, dob, created_at FROM users WHERE id = %s",
            (user_id,),
        )
        return _row_to_dict(cur.fetchone())
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, pan, name FROM users WHERE email = %s",
            (email,),
        )
        return _row_to_dict(cur.fetchone())
    finally:
        conn.close()


def create_user_google(email: str, name: str, google_id: str) -> dict:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, email, pan, name FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        if row:
            cur.close()
            d = dict(row)
            return {"id": d["id"], "email": d["email"], "pan": d.get("pan") or "", "name": d["name"]}

        # Create new user
        user_id = _uid()
        now = _now_iso()
        hashed = hash_password(google_id)
        cur.execute(
            "INSERT INTO users (id, email, pan, name, hashed_password, dob, created_at) "
            "VALUES (%s, %s, NULL, %s, %s, %s, %s)",
            (user_id, email, name, hashed, "", now),
        )
        cur.close()
        return {"id": user_id, "email": email, "pan": "", "name": name}
    finally:
        conn.close()


def user_exists(email: str) -> bool:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        cur.close()
        return row is not None
    finally:
        conn.close()


def update_user_profile(user_id: str, name: str) -> dict | None:
    conn = get_db()
    try:
        _exec_sql(conn, "UPDATE users SET name = %s WHERE id = %s", (name, user_id))
        return get_user_by_id(user_id)
    finally:
        conn.close()


def change_user_password(user_id: str, current_password: str, new_password: str) -> bool:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT hashed_password FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return False
        if not verify_password(current_password, dict(row)["hashed_password"]):
            return False
        _exec_sql(conn, "UPDATE users SET hashed_password = %s WHERE id = %s",
                  (hash_password(new_password), user_id))
        return True
    finally:
        conn.close()


# ── Filing CRUD ──────────────────────────────────────────────────────

def create_filing(user_id: str, assessment_year: str = "2026-27", itr_type: str = "ITR-2") -> str:
    conn = get_db()
    try:
        filing_id = _uid()
        now = _now_iso()
        _exec_sql(conn,
            "INSERT INTO filings (id, user_id, assessment_year, itr_type, status, created_at, updated_at) "
            "VALUES (%s, %s, %s, %s, 'draft', %s, %s)",
            (filing_id, user_id, assessment_year, itr_type, now, now),
        )
        return filing_id
    finally:
        conn.close()


def update_filing_status(filing_id: str, status: str, gross_income: str = "", tax_paid: str = "", regime: str = "") -> None:
    conn = get_db()
    try:
        _exec_sql(conn,
            "UPDATE filings SET status = %s, gross_income = %s, tax_paid = %s, regime = %s, "
            "updated_at = %s WHERE id = %s",
            (status, gross_income, tax_paid, regime, _now_iso(), filing_id),
        )
    finally:
        conn.close()


def get_user_filings(user_id: str) -> list[dict]:
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM filings WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
