"""SQLite database layer for TaxStox — users, filings, documents."""

import os
import uuid
import sqlite3
from datetime import datetime, timezone
import bcrypt

# ── Password hashing ─────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # bcrypt has a 72-byte limit
    return bcrypt.hashpw(password[:72].encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password[:72].encode(), hashed.encode())

# ── Database path ────────────────────────────────────────────────────

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "taxstox.db")


def get_db() -> sqlite3.Connection:
    """Get a synchronous SQLite connection."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── Schema ───────────────────────────────────────────────────────────

def init_db() -> None:
    """Create tables if they don't exist."""
    conn = get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                pan TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS filings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id),
                assessment_year TEXT NOT NULL,
                itr_type TEXT NOT NULL DEFAULT 'ITR-2',
                regime TEXT,
                gross_income TEXT,
                tax_paid TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_filings_user ON filings(user_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_pan ON users(pan);
        """)
        conn.commit()
    finally:
        conn.close()


# ── User CRUD ────────────────────────────────────────────────────────

def create_user(email: str, pan: str, name: str, password: str) -> dict:
    """Create a new user. Returns user dict. Raises ValueError on duplicate."""
    conn = get_db()
    try:
        user_id = str(uuid.uuid4())[:12]
        hashed = hash_password(password)
        conn.execute(
            "INSERT INTO users (id, email, pan, name, hashed_password, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, email, pan, name, hashed, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return {"id": user_id, "email": email, "pan": pan, "name": name}
    except sqlite3.IntegrityError as e:
        msg = str(e).lower()
        if "email" in msg:
            raise ValueError("An account with this email already exists.")
        if "pan" in msg:
            raise ValueError("An account with this PAN already exists.")
        raise ValueError("Account creation failed.")
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> dict | None:
    """Verify credentials and return user dict, or None."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, email, pan, name, hashed_password FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if row is None:
            return None
        if not verify_password(password, row["hashed_password"]):
            return None
        return {"id": row["id"], "email": row["email"], "pan": row["pan"], "name": row["name"]}
    finally:
        conn.close()


def get_user_by_id(user_id: str) -> dict | None:
    """Get user by ID."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, email, pan, name, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ── Filing CRUD ──────────────────────────────────────────────────────

def create_filing(user_id: str, assessment_year: str = "2026-27", itr_type: str = "ITR-2") -> str:
    """Create a new filing record. Returns filing_id."""
    conn = get_db()
    try:
        filing_id = str(uuid.uuid4())[:12]
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO filings (id, user_id, assessment_year, itr_type, status, created_at, updated_at) VALUES (?, ?, ?, ?, 'draft', ?, ?)",
            (filing_id, user_id, assessment_year, itr_type, now, now),
        )
        conn.commit()
        return filing_id
    finally:
        conn.close()


def update_filing_status(filing_id: str, status: str, gross_income: str = "", tax_paid: str = "", regime: str = "") -> None:
    """Update filing status and financial summary."""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE filings SET status = ?, gross_income = ?, tax_paid = ?, regime = ?, updated_at = ? WHERE id = ?",
            (status, gross_income, tax_paid, regime, datetime.now(timezone.utc).isoformat(), filing_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_filings(user_id: str) -> list[dict]:
    """Get all filings for a user, newest first."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM filings WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
