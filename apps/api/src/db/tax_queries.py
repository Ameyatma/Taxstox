"""Tax content database layer — CRUD for tax_updates, deadlines, tips, facts, sync_log."""

from __future__ import annotations

from src.db.database import get_db, _exec_sql, _uid, _now_iso, _row_to_dict


# ── Tax Updates ───────────────────────────────────────────────────────

def upsert_tax_update(
    title: str,
    summary_short: str,
    source: str,
    source_url: str,
    published_date: str,
    category: str = "Compliance",
    what_changed: str = "",
    who_affected: str = "",
    action_required: str = "",
    effective_date: str = "",
    raw_content: str = "",
) -> str:
    """Insert or update a tax update (dedup by source_url). Returns the id."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM tax_updates WHERE source_url = %s", (source_url,))
        existing = cur.fetchone()
        cur.close()

        if existing:
            update_id = dict(existing)["id"]
            _exec_sql(conn,
                """UPDATE tax_updates SET
                    title=%s, summary_short=%s, what_changed=%s, who_affected=%s,
                    action_required=%s, category=%s, effective_date=%s,
                    published_date=%s, source=%s, raw_content=%s, updated_at=%s
                WHERE id=%s""",
                (title, summary_short, what_changed, who_affected, action_required,
                 category, effective_date, published_date, source, raw_content,
                 _now_iso(), update_id),
            )
            return update_id
        else:
            update_id = _uid()
            now = _now_iso()
            _exec_sql(conn,
                """INSERT INTO tax_updates
                    (id, title, summary_short, what_changed, who_affected,
                     action_required, category, effective_date, published_date,
                     source, source_url, raw_content, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (update_id, title, summary_short, what_changed, who_affected,
                 action_required, category, effective_date, published_date,
                 source, source_url, raw_content, now, now),
            )
            return update_id
    finally:
        conn.close()


def get_tax_updates(limit: int = 20, category: str | None = None) -> list[dict]:
    """Get active tax updates, newest first. Optionally filter by category."""
    conn = get_db()
    try:
        cur = conn.cursor()
        if category:
            cur.execute(
                """SELECT * FROM tax_updates
                WHERE is_active = TRUE AND category = %s
                ORDER BY published_date DESC LIMIT %s""",
                (category, limit),
            )
        else:
            cur.execute(
                """SELECT * FROM tax_updates
                WHERE is_active = TRUE
                ORDER BY published_date DESC LIMIT %s""",
                (limit,),
            )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Tax Deadlines ─────────────────────────────────────────────────────

def seed_tax_deadlines() -> list[str]:
    """Insert default deadlines if none exist. Returns list of created ids."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM tax_deadlines")
        count = dict(cur.fetchone())["cnt"]
        cur.close()
        if count > 0:
            return []

        defaults = [
            ("dl-itr-non-audit", "ITR Filing (Non-Audit Cases)",
             "2025-07-31", "Last date to file ITR for individuals, HUFs, and non-audit taxpayers for FY 2024-25 (AY 2025-26). Penalty up to Rs 5,000 under Section 234F for late filing.", "ITR"),
            ("dl-advance-tax-2", "Advance Tax — 2nd Instalment",
             "2025-09-15", "Pay at least 45% of total advance tax liability by this date to avoid interest under Section 234C.", "Advance Tax"),
            ("dl-tds-q1", "TDS Return — Q1 FY 2025-26",
             "2025-07-31", "Deadline for filing quarterly TDS/TCS return (Form 24Q/26Q/27Q) for April-June 2025 quarter. Penalty under Section 271H for late filing.", "TDS"),
            ("dl-advance-tax-3", "Advance Tax — 3rd Instalment",
             "2025-12-15", "Pay at least 75% of total advance tax liability by this date to avoid interest under Section 234C.", "Advance Tax"),
            ("dl-advance-tax-4", "Advance Tax — 4th Instalment",
             "2026-03-15", "Pay 100% of total advance tax liability by this date. Final instalment for FY 2025-26.", "Advance Tax"),
            ("dl-itr-audit", "ITR Filing (Audit Cases)",
             "2025-10-31", "Last date to file ITR for taxpayers whose accounts require audit under Section 44AB for FY 2024-25.", "ITR"),
            ("dl-belated", "Belated / Revised Return Deadline",
             "2025-12-31", "Last date to file a belated return under Section 139(4) or a revised return under Section 139(5) for FY 2024-25.", "ITR"),
        ]
        ids = []
        for did, title, date, desc, cat in defaults:
            _exec_sql(conn,
                "INSERT INTO tax_deadlines (id, title, date, description, category) VALUES (%s,%s,%s,%s,%s)",
                (did, title, date, desc, cat),
            )
            ids.append(did)
        return ids
    finally:
        conn.close()


def get_tax_deadlines() -> list[dict]:
    """Get all active deadlines, ordered by date ascending."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM tax_deadlines WHERE is_active = TRUE ORDER BY date ASC"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Tax Tips ──────────────────────────────────────────────────────────

def seed_tax_tips() -> list[str]:
    """Insert default tips if none exist. Returns list of created ids."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM tax_tips")
        count = dict(cur.fetchone())["cnt"]
        cur.close()
        if count > 0:
            return []

        defaults = [
            ("Keep your Form 16 and AIS ready and cross-checked before you start filing. "
             "Any mismatch can trigger a notice from the IT Department."),
            ("Verify your bank account is linked and pre-validated on the IT e-filing portal. "
             "Refunds are only credited to validated bank accounts — unvalidated accounts cause delays."),
            ("Match your AIS and Form 26AS before filing. Discrepancies in TDS, interest income, "
             "or high-value transactions are the #1 cause of defective return notices under Section 139(9)."),
            ("Claim all eligible deductions — Section 80C (Rs 1.5L), 80D (health insurance up to Rs 1L), "
             "80CCD(1B) (NPS Rs 50K), and home loan interest under Section 24(b) (Rs 2L)."),
            ("If you traded stocks or mutual funds, download your Capital Gains statement from "
             "Zerodha, Groww, or CAMS. LTCG above Rs 1.25L is taxed at 12.5% — don't miss reporting it."),
            ("File early. The IT e-filing portal slows down in the last week of July. "
             "Filing by mid-July gives you buffer time to fix any rejection or mismatch issues."),
            ("E-verify your ITR within 30 days of filing. An unverified return is treated as "
             "'not filed' and can result in penalties and delayed refunds."),
        ]
        ids = []
        for i, text in enumerate(defaults):
            tid = f"tip-{i + 1}"
            _exec_sql(conn,
                "INSERT INTO tax_tips (id, text, sort_order) VALUES (%s,%s,%s)",
                (tid, text, i),
            )
            ids.append(tid)
        return ids
    finally:
        conn.close()


def get_tax_tips() -> list[dict]:
    """Get all active tips, ordered by sort_order."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM tax_tips WHERE is_active = TRUE ORDER BY sort_order ASC"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Tax Facts ─────────────────────────────────────────────────────────

def seed_tax_facts() -> list[str]:
    """Insert default facts if none exist. Returns list of created ids."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM tax_facts")
        count = dict(cur.fetchone())["cnt"]
        cur.close()
        if count > 0:
            return []

        defaults = [
            ("filing-benefits", "Filing ITR even with zero tax liability has benefits",
             "A filed ITR serves as official proof of income — required for visa applications, "
             "loan approvals, credit card applications, and carrying forward capital losses for up to 8 years.",
             "description"),
            ("regime-switch", "Old vs New Tax Regime — you can switch every year",
             "Salaried taxpayers can choose between Old and New regimes each financial year. "
             "The New Regime offers lower slab rates with fewer deductions, while the Old Regime "
             "rewards investments with exemptions under 80C, 80D, and more.",
             "compare_arrows"),
            ("everify", "E-verification is mandatory — don't skip it",
             "Filing your ITR is not complete until you e-verify it within 30 days. Unverified returns "
             "are treated as 'not filed,' which can lead to penalties, delayed refunds, and loss of "
             "carried-forward losses.",
             "verified_user"),
            ("common-mistakes", "Common filing mistakes that trigger notices",
             "The top mistakes: not reporting savings bank interest (even if below Rs 10K), missing TDS "
             "entries from Form 26AS, incorrect personal details, and wrong assessment year selection.",
             "warning"),
            ("belated-return", "You can still file a belated return until December 31",
             "Missed the July 31 deadline? You can file a belated return under Section 139(4) until "
             "December 31 of the assessment year, though a late fee of up to Rs 5,000 applies.",
             "update"),
        ]
        ids = []
        for i, (fid, title, desc, icon) in enumerate(defaults):
            _exec_sql(conn,
                "INSERT INTO tax_facts (id, title, description, icon, sort_order) VALUES (%s,%s,%s,%s,%s)",
                (fid, title, desc, icon, i),
            )
            ids.append(fid)
        return ids
    finally:
        conn.close()


def get_tax_facts() -> list[dict]:
    """Get all active facts, ordered by sort_order."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM tax_facts WHERE is_active = TRUE ORDER BY sort_order ASC"
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Sync Log ──────────────────────────────────────────────────────────

def start_sync_log() -> int:
    """Start a new sync run, return its id."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tax_sync_log (started_at, status) VALUES (%s, 'running') RETURNING id",
            (_now_iso(),),
        )
        sync_id = dict(cur.fetchone())["id"]
        cur.close()
        return sync_id
    finally:
        conn.close()


def complete_sync_log(sync_id: int, sources_checked: int, updates_found: int, updates_new: int, error: str = ""):
    """Mark a sync run as completed (or failed if error provided)."""
    conn = get_db()
    try:
        status = "failed" if error else "completed"
        _exec_sql(conn,
            """UPDATE tax_sync_log SET
                completed_at=%s, sources_checked=%s, updates_found=%s,
                updates_new=%s, status=%s, error_message=%s
            WHERE id=%s""",
            (_now_iso(), sources_checked, updates_found, updates_new, status, error, sync_id),
        )
    finally:
        conn.close()


def get_last_sync_time() -> str | None:
    """Return ISO timestamp of the last successful sync, or None."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT completed_at FROM tax_sync_log WHERE status='completed' ORDER BY completed_at DESC LIMIT 1"
        )
        row = cur.fetchone()
        cur.close()
        return dict(row)["completed_at"] if row else None
    finally:
        conn.close()
