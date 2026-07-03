"""Multi-broker CSV parsers — Groww, Upstox, Angel One.

Each broker exports a slightly different CSV format. We auto-detect the
broker from column headers and parse accordingly. All return list[CGSaleEntry].
"""

import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from src.models.tax import CGSaleEntry


# ── Shared helpers ────────────────────────────────────────────────────

def _find_column(headers: list[str], candidates: list[str]) -> Optional[str]:
    for h in headers:
        h_lower = h.strip().lower()
        for c in candidates:
            if c in h_lower:
                return h
    for c in candidates:
        if c in headers:
            return c
    return None


def _parse_date(date_str: str) -> date:
    if not date_str:
        return date.today()
    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d-%b-%Y",
        "%d %b %Y", "%d/%m/%y", "%m/%d/%Y", "%d-%m-%y",
        "%Y/%m/%d", "%d %B %Y", "%b %d %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(date_str.strip())
    except (ValueError, TypeError):
        return date.today()


def _detect_asset_class(segment: str, exchange: str = "") -> str:
    s = (segment + " " + exchange).upper()
    if "MF" in s or "MUTUAL" in s:
        return "equity_mf"
    if "FNO" in s or "FUT" in s or "OPT" in s or "DERIVATIVE" in s:
        return "futures_options"
    if "COMMODITY" in s or "MCX" in s:
        return "commodity"
    if "CURRENCY" in s or "CDS" in s or "FOREX" in s:
        return "currency"
    if "DEBT" in s or "BOND" in s or "GILT" in s or "NCD" in s:
        return "debt"
    return "equity"


def _read_rows(content: bytes) -> tuple[list[str], list[dict]]:
    """Read CSV and return (headers, list of row dicts with lowercase keys)."""
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("Empty or invalid CSV — no headers found.")
    headers = [h.strip().lower() for h in reader.fieldnames]
    rows = []
    for r in reader:
        rows.append({k.strip().lower(): v.strip() for k, v in r.items()})
    return headers, rows


# ── Groww ─────────────────────────────────────────────────────────────

def parse_groww_tradebook(content: bytes, filename: str = "") -> list[CGSaleEntry]:
    """Parse Groww trade export CSV.

    Groww columns (typical): Stock/Name, ISIN, Trade Date, Transaction Type,
    Quantity, Price/avg_price, Exchange, Segment/Instrument
    """
    headers, rows = _read_rows(content)

    isin_col = _find_column(headers, ["isin", "isin code", "isin_code"])
    symbol_col = _find_column(headers, ["symbol", "stock", "name", "scrip", "company_name"])
    date_col = _find_column(headers, ["trade_date", "trade date", "date"])
    qty_col = _find_column(headers, ["quantity", "qty", "shares"])
    price_col = _find_column(headers, ["price", "avg_price", "average_price", "trade_price", "rate"])
    type_col = _find_column(headers, ["transaction_type", "transaction type", "type", "trade_type", "action"])
    segment_col = _find_column(headers, ["segment", "instrument", "exchange", "market", "instrument_type"])

    entries: list[CGSaleEntry] = []
    for row in rows:
        trade_type = row.get(type_col or "", "").upper()
        if not any(t in trade_type for t in ["SELL", "S"]):
            continue

        try:
            isin = row.get(isin_col or "", "INNOTAVAILAB") or "INNOTAVAILAB"
            symbol = row.get(symbol_col or "", "Unknown") or "Unknown"
            trade_date = _parse_date(row.get(date_col or "", ""))
            qty = Decimal(row.get(qty_col or "", "0") or "0")
            price = Decimal(row.get(price_col or "", "0") or "0")
            segment = row.get(segment_col or "", "")

            entries.append(CGSaleEntry(
                date=trade_date,
                isin=isin,
                security_name=symbol,
                quantity=qty,
                sale_price=price,
                consideration=qty * price,
                cost=Decimal("0"),  # Enrich with buy data or tax P&L
                stt_paid=("NSE" in segment.upper() or "BSE" in segment.upper()),
                term="",
                asset_class=_detect_asset_class(segment),
                gain=Decimal("0"),
            ))
        except (ValueError, KeyError):
            continue

    return entries


# ── Upstox ────────────────────────────────────────────────────────────

def parse_upstox_tradebook(content: bytes, filename: str = "") -> list[CGSaleEntry]:
    """Parse Upstox trade export CSV.

    Upstox columns (typical): symbol, isin, trade_date, exchange, segment,
    quantity, avg_price, trade_type/action
    """
    headers, rows = _read_rows(content)

    isin_col = _find_column(headers, ["isin", "isin_code"])
    symbol_col = _find_column(headers, ["symbol", "tradingsymbol", "scrip", "name", "instrument"])
    date_col = _find_column(headers, ["trade_date", "date", "order_execution_time", "trade_time"])
    qty_col = _find_column(headers, ["quantity", "qty", "traded_qty", "filled_quantity"])
    price_col = _find_column(headers, ["avg_price", "average_price", "price", "avg_traded_price", "rate"])
    type_col = _find_column(headers, ["trade_type", "type", "transaction_type", "action", "buy_sell"])
    segment_col = _find_column(headers, ["segment", "exchange", "product", "market_type"])

    entries: list[CGSaleEntry] = []
    for row in rows:
        trade_type = row.get(type_col or "", "").upper()
        if not any(t in trade_type for t in ["SELL", "S"]):
            continue

        try:
            isin = row.get(isin_col or "", "INNOTAVAILAB") or "INNOTAVAILAB"
            symbol = row.get(symbol_col or "", "Unknown") or "Unknown"
            trade_date = _parse_date(row.get(date_col or "", ""))
            qty = Decimal(row.get(qty_col or "", "0") or "0")
            price = Decimal(row.get(price_col or "", "0") or "0")
            segment = row.get(segment_col or "", "")

            entries.append(CGSaleEntry(
                date=trade_date,
                isin=isin,
                security_name=symbol,
                quantity=qty,
                sale_price=price,
                consideration=qty * price,
                cost=Decimal("0"),
                stt_paid=True,
                term="",
                asset_class=_detect_asset_class(segment),
                gain=Decimal("0"),
            ))
        except (ValueError, KeyError):
            continue

    return entries


# ── Angel One ─────────────────────────────────────────────────────────

def parse_angel_one_tradebook(content: bytes, filename: str = "") -> list[CGSaleEntry]:
    """Parse Angel One (Angel Broking) trade export CSV.

    Angel One columns (typical): symbol, isin, trade_date, exchange,
    quantity, avg_traded_price, transaction_type, segment
    """
    headers, rows = _read_rows(content)

    isin_col = _find_column(headers, ["isin", "isin_code", "isin code"])
    symbol_col = _find_column(headers, ["symbol", "scrip", "scrip_name", "tradingsymbol", "name"])
    date_col = _find_column(headers, ["trade_date", "trade date", "date", "order_date"])
    qty_col = _find_column(headers, ["quantity", "qty", "shares", "traded_qty"])
    price_col = _find_column(headers, ["avg_traded_price", "avg_price", "price", "rate", "average_price"])
    type_col = _find_column(headers, ["transaction_type", "trans_type", "trade_type", "type", "action"])
    segment_col = _find_column(headers, ["segment", "exchange", "market", "instrument_type"])

    entries: list[CGSaleEntry] = []
    for row in rows:
        trade_type = row.get(type_col or "", "").upper()
        if not any(t in trade_type for t in ["SELL", "S", "SALE"]):
            continue

        try:
            isin = row.get(isin_col or "", "INNOTAVAILAB") or "INNOTAVAILAB"
            symbol = row.get(symbol_col or "", "Unknown") or "Unknown"
            trade_date = _parse_date(row.get(date_col or "", ""))
            qty = Decimal(row.get(qty_col or "", "0") or "0")
            price = Decimal(row.get(price_col or "", "0") or "0")
            segment = row.get(segment_col or "", "")

            entries.append(CGSaleEntry(
                date=trade_date,
                isin=isin,
                security_name=symbol,
                quantity=qty,
                sale_price=price,
                consideration=qty * price,
                cost=Decimal("0"),
                stt_paid=True,
                term="",
                asset_class=_detect_asset_class(segment),
                gain=Decimal("0"),
            ))
        except (ValueError, KeyError):
            continue

    return entries


# ── Unified entry point ───────────────────────────────────────────────

def parse_broker_statement(content: bytes, filename: str, broker: str = "") -> list[CGSaleEntry]:
    """Auto-detect broker and parse. Falls back to trying all known formats.

    Args:
        content: Raw CSV bytes
        filename: Original filename (used for broker hint)
        broker: Optional broker hint (groww, upstox, angel_one, zerodha)

    Returns list[CGSaleEntry] from the first parser that succeeds.
    """
    broker_lower = broker.lower()

    parsers: list[tuple[str, callable]] = [
        ("groww", parse_groww_tradebook),
        ("upstox", parse_upstox_tradebook),
        ("angel_one", parse_angel_one_tradebook),
    ]

    # Try specific broker first
    for name, parser in parsers:
        if name in broker_lower:
            return parser(content, filename)

    # Auto-detect: try all
    errors = []
    for name, parser in parsers:
        try:
            result = parser(content, filename)
            if result:
                return result
        except Exception as e:
            errors.append(f"{name}: {e}")
            continue

    raise ValueError(f"No parser could handle this file. Errors: {'; '.join(errors)}")
