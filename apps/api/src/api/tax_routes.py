"""Tax Updates & Insights API — serves processed tax content to the frontend."""

from __future__ import annotations

import logging
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import requests

from src.db.tax_queries import (
    get_last_sync_time,
    get_tax_deadlines,
    get_tax_facts,
    get_tax_tips,
    get_tax_updates,
    seed_tax_deadlines,
    seed_tax_facts,
    seed_tax_tips,
)
from src.models.tax import ClassifiedCGData, CGSaleEntry
from src.utils.session import Session, session_manager

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# Create a session with browser headers to avoid yfinance blocking
_yf_session = None
def _get_yf_session():
    global _yf_session
    if _yf_session is None:
        _yf_session = requests.Session()
        _yf_session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        })
    return _yf_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tax", tags=["Tax Updates"])


def _ensure_seeded():
    """Seed default tips/facts/deadlines if the tables are empty."""
    try:
        seed_tax_tips()
        seed_tax_facts()
        seed_tax_deadlines()
    except Exception as e:
        logger.warning("Seed check failed (DB may not be ready): %s", e)


@router.get("/insights")
async def get_tax_insights():
    """Get aggregated tax insights: updates, deadlines, tips, and facts."""
    _ensure_seeded()

    try:
        updates = get_tax_updates(limit=8)
    except Exception as e:
        logger.warning("Failed to fetch updates: %s", e)
        updates = []

    try:
        deadlines = get_tax_deadlines()
    except Exception as e:
        logger.warning("Failed to fetch deadlines: %s", e)
        deadlines = []

    try:
        tips = get_tax_tips()
    except Exception as e:
        logger.warning("Failed to fetch tips: %s", e)
        tips = []

    try:
        facts = get_tax_facts()
    except Exception as e:
        logger.warning("Failed to fetch facts: %s", e)
        facts = []

    last_synced = get_last_sync_time()

    return {
        "updates": updates,
        "deadlines": deadlines,
        "tips": tips,
        "facts": facts,
        "last_synced": last_synced,
    }


@router.get("/updates")
async def list_tax_updates(category: str | None = None, limit: int = 20):
    """Get latest tax updates, optionally filtered by category."""
    _ensure_seeded()
    return get_tax_updates(limit=limit, category=category)


@router.get("/deadlines")
async def list_tax_deadlines():
    """Get all active tax deadlines."""
    _ensure_seeded()
    return get_tax_deadlines()


@router.get("/tips")
async def list_tax_tips():
    """Get tax-saving tips."""
    _ensure_seeded()
    return get_tax_tips()


@router.get("/facts")
async def list_tax_facts():
    """Get educational tax facts."""
    _ensure_seeded()
    return get_tax_facts()


# ────────────────────────────────────────────────────────────────────────
# Cross-Domain: Tax-Loss Harvesting Engine (Phase 10)
# ────────────────────────────────────────────────────────────────────────
# MISSION: SUPER-APP PHASE 10 — CROSS-DOMAIN TAX-LOSS HARVESTING &
# SESSION REHYDRATION
# Goal: Unify Tax Engine and Market Terminal (Zero OPEX).
#
# This endpoint bridges the tax filing session with live market data via
# yfinance. It compares realized short-term capital gains (STCG taxed at
# 15% under Section 111A) against unrealized losses in the user's traded
# holdings, and computes the tax savings available by harvesting those
# losses before the March 31 year-end.
#
# Schema:
# {
#   "realized_stcg": 50000.0,
#   "total_potential_savings": 6000.0,
#   "opportunities": [
#     {
#       "symbol": "HDFCBANK.NS",
#       "quantity": 50,
#       "buy_price": 1720.0,
#       "current_price": 1640.0,
#       "unrealized_loss": -4000.0,
#       "potential_tax_savings": 600.0,
#       "action": "Harvest loss before March 31 to offset Schedule 111A gains"
#     }
#   ]
# }
# ────────────────────────────────────────────────────────────────────────


class HarvestOpportunity(BaseModel):
    """A single loss-harvesting opportunity."""
    symbol: str
    isin: str
    quantity: float
    buy_price: float
    current_price: float
    unrealized_loss: float
    potential_tax_savings: float
    action: str = "Harvest loss before March 31 to offset Schedule 111A gains"


class HoldingPosition(BaseModel):
    """A single ingested broker holding with live market data."""
    symbol: str
    isin: str
    quantity: float
    buy_price: float
    current_price: float
    day_change_pct: float
    unrealized_pnl: float


class HarvestSummary(BaseModel):
    """Tax-loss harvesting summary for a filing session."""
    realized_stcg: float
    total_potential_savings: float
    opportunities: list[HarvestOpportunity] = []
    holdings: list[HoldingPosition] = []


def _resolve_session(session_id: str) -> Session:
    """Resolve a filing session or raise 404."""
    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    return session


def _build_ticker(isin_or_symbol: str) -> str:
    """Normalize an ISIN/symbol into a yfinance-friendly ticker.

    Indian equities trade as '<isin>.NS' on the NSE or '<isin>.BO' on
    the BSE. Fallbacks: strip a trailing .NS/.BO, append .NS for any
    12-char ISIN, else return the raw symbol.
    """
    s = isin_or_symbol.strip().upper()
    for suffix in (".BO", ".NS"):
        if s.endswith(suffix):
            return s
    # Indian ISINs are 12 alphanumeric characters starting with a letter
    if s.startswith("INE") and len(s) >= 10:
        return f"{s}.NS"
    if len(s) == 12:
        return f"{s}.NS"
    return s


def _fetch_live_price(ticker: str) -> tuple[float, float] | None:
    """Fetch the latest close price and day-change % for a ticker.

    Returns a (current_price, day_change_pct) tuple, or None if the
    ticker cannot be resolved. The day change is computed against the
    previous trading day's close so the holdings table always shows a
    live delta even when the market is closed.
    """
    if not YFINANCE_AVAILABLE:
        return None
    try:
        stock = _get_yf_session().Ticker(ticker)
        info = stock.info
        if info is None:
            return None
        # Prefer the last two trading days so we can compute a day delta
        hist = stock.history(period="5d")
        if hist.empty:
            return None
        closes = hist["Close"].dropna()
        if closes.empty:
            return None
        current = float(closes.iloc[-1])
        if len(closes) >= 2:
            prev = float(closes.iloc[-2])
            day_change_pct = 0.0 if prev == 0 else ((current - prev) / prev) * 100.0
        else:
            day_change_pct = 0.0
        return current, day_change_pct
    except Exception:
        # Market data fetch failures are non-fatal — skip this holding
        return None


@router.get("/harvesting/{session_id}", response_model=HarvestSummary)
async def get_tax_harvesting(
    session_id: str,
    session: Session = Depends(_resolve_session),
):
    """
    Calculate unrealized loss-harvesting opportunities against realized
    capital gains for a filing session.

    Methodology:
      1. Retrieve session.classified_cg and aggregate all traded securities
         (both short- and long-term buckets) by ISIN, computing a
         blended buy-average cost basis.
      2. Extract realized STCG (taxed at 15% under Section 111A).
      3. For each holding with an open position, fetch the live price via
         yfinance and compute Unrealized P&L =
         (Current Price - Buy Average) x Quantity.
      4. Identify loss positions (unrealized P&L < 0).
      5. Compute Tax Savings = min(Realized STCG, |Unrealized Loss|) x 0.15.

    Returns a summary containing realized STCG, total potential tax savings,
    and a ranked list of harvesting opportunities.
    """
    # ── Step 1: Retrieve classified capital gains ────────────────────
    classified_cg = session.classified_cg or ClassifiedCGData()

    # ── Step 2: Aggregate holdings by ISIN + compute buy average ─────
    # Collect every traded security regardless of tax bucket so that
    # long-held positions still qualify as "open positions" for
    # unrealized-loss monitoring.
    all_entries: list[CGSaleEntry] = (
        classified_cg.cg_a2_stcg_111a
        + classified_cg.cg_a5_stcg_app_rate
        + classified_cg.schedule_112a
        + classified_cg.cg_b8_ltcg_other
    )

    holdings: dict[str, dict] = {}
    for entry in all_entries:
        if not entry.isin:
            continue
        key = entry.isin
        if key not in holdings:
            holdings[key] = {
                "isin": entry.isin,
                "security_name": entry.security_name or entry.isin,
                "total_qty": Decimal(0),
                "total_cost": Decimal(0),
            }
        holdings[key]["total_qty"] += entry.quantity
        holdings[key]["total_cost"] += entry.cost

    # ── Step 3: Realized STCG (Section 111A, 15%) ───────────────────
    realized_stcg = float(classified_cg.total_stcg)

    # ── Step 4: Live prices + unrealized P&L ─────────────────────────
    opportunities: list[dict] = []
    holdings_out: list[dict] = []
    total_potential_savings = 0.0

    for key, hold in holdings.items():
        qty = float(hold["total_qty"])
        if qty <= 0:
            continue

        buy_avg = float(hold["total_cost"]) / qty
        ticker = _build_ticker(hold["isin"])
        live = _fetch_live_price(ticker)
        if live is None:
            # No live price — skip; price data is best-effort
            continue
        current_price, day_change_pct = live

        unrealized_pnl = (current_price - buy_avg) * qty

        # Full holdings table (every ingested position, not just losses)
        holdings_out.append({
            "symbol": hold["security_name"],
            "isin": hold["isin"],
            "quantity": round(qty, 2),
            "buy_price": round(buy_avg, 2),
            "current_price": round(current_price, 2),
            "day_change_pct": round(day_change_pct, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
        })

        # ── Step 5: Loss positions → tax savings ───────────────────
        if unrealized_pnl < 0:
            potential_tax_savings = min(realized_stcg, abs(unrealized_pnl)) * 0.15
            total_potential_savings += potential_tax_savings
            opportunities.append({
                "symbol": hold["security_name"],
                "isin": hold["isin"],
                "quantity": round(qty, 2),
                "buy_price": round(buy_avg, 2),
                "current_price": round(current_price, 2),
                "unrealized_loss": round(unrealized_pnl, 2),
                "potential_tax_savings": round(potential_tax_savings, 2),
            })

    # Rank by tax savings, highest first
    opportunities.sort(key=lambda o: o["potential_tax_savings"], reverse=True)
    # Holdings table ordered by unrealized P&L (worst first) so losses lead
    holdings_out.sort(key=lambda h: h["unrealized_pnl"])

    return HarvestSummary(
        realized_stcg=round(realized_stcg, 2),
        total_potential_savings=round(total_potential_savings, 2),
        opportunities=[HarvestOpportunity(**o) for o in opportunities],
        holdings=[HoldingPosition(**h) for h in holdings_out],
    )
