"""Zerodha Tradebook CSV parser.

Zerodha's tradebook export (CSV) columns:
  symbol, isin, trade_date, exchange, segment, trade_type, quantity, price, ...

We extract: ISIN, security name, date, quantity, buy/sell price, and compute P&L.
"""

import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from src.models.tax import CGSaleEntry


def parse_zerodha_tradebook(content: bytes, filename: str = "") -> list[CGSaleEntry]:
    """Parse a Zerodha tradebook CSV export.

    Returns a list of CGSaleEntry objects for all SELL transactions.
    """
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise ValueError("Empty or invalid CSV — no headers found.")

    # Normalize header names (lowercase, strip)
    headers = [h.strip().lower() for h in reader.fieldnames]

    # Detect column mapping
    isin_col = _find_column(headers, ["isin", "isin code", "isin_code"])
    symbol_col = _find_column(headers, ["symbol", "scrip", "scrip_name", "tradingsymbol"])
    date_col = _find_column(headers, ["trade_date", "trade date", "date"])
    qty_col = _find_column(headers, ["quantity", "qty"])
    price_col = _find_column(headers, ["price", "trade_price", "rate", "average_price"])
    type_col = _find_column(headers, ["trade_type", "trade type", "buy/sell", "action", "segment"])
    segment_col = _find_column(headers, ["segment", "instrument", "instrument_type"])

    entries: list[CGSaleEntry] = []

    for row in reader:
        # Normalize row keys
        row_lower = {k.strip().lower(): v.strip() for k, v in row.items()}

        trade_type = row_lower.get(type_col, "").upper() if type_col else ""

        # Only process SELL transactions
        if not any(t in trade_type for t in ["SELL", "S"]):
            continue

        try:
            isin = row_lower.get(isin_col, "INNOTAVAILAB") if isin_col else "INNOTAVAILAB"
            if isin == "INNOTAVAILAB":
                # Try to find ISIN from symbol mapping (simplified)
                pass

            symbol = row_lower.get(symbol_col, "Unknown") if symbol_col else "Unknown"

            # Parse date
            date_str = row_lower.get(date_col, "") if date_col else ""
            trade_date = _parse_date(date_str)

            qty = Decimal(row_lower.get(qty_col, "0")) if qty_col else Decimal("0")
            price = Decimal(row_lower.get(price_col, "0")) if price_col else Decimal("0")

            consideration = qty * price

            # We don't have cost basis in a sell-only tradebook —
            # the user needs to provide buy details or we use ₹0 as placeholder
            # In practice, Zerodha's tax P&L statement has both buy and sell
            entry = CGSaleEntry(
                date=trade_date,
                isin=isin,
                security_name=symbol,
                quantity=qty,
                sale_price=price,
                consideration=consideration,
                cost=Decimal("0"),  # Will be enriched from buy-side data or user input
                stt_paid=True,  # Equity trades on NSE/BSE have STT
                term="",  # Determined by classifier based on holding period
                asset_class=_detect_asset_class(row_lower.get(segment_col, "")) if segment_col else "equity",
                gain=Decimal("0"),  # Computed when cost basis is available
            )

            # Determine term based on common patterns
            if "EQ" in trade_type or "DELIVERY" in trade_type:
                entry.term = ""  # Classifier will determine based on dates

            entries.append(entry)

        except (ValueError, KeyError) as e:
            # Skip malformed rows
            continue

    return entries


def parse_zerodha_tax_pnl(content: bytes, filename: str = "") -> list[CGSaleEntry]:
    """Parse Zerodha's Tax P&L statement (CSV with both buy and sell data).

    This is the preferred format — it includes cost basis, holding period,
    and explicitly states Long Term / Short Term.
    """
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise ValueError("Empty or invalid CSV.")

    headers = [h.strip().lower() for h in reader.fieldnames]

    # Column detection for Tax P&L format
    isin_col = _find_column(headers, ["isin", "isin code"])
    symbol_col = _find_column(headers, ["symbol", "scrip", "stock", "name"])
    buy_date_col = _find_column(headers, ["buy_date", "buy date", "purchase_date", "purchase date", "acquisition_date"])
    sell_date_col = _find_column(headers, ["sell_date", "sell date", "sale_date", "sale date"])
    qty_col = _find_column(headers, ["quantity", "qty", "shares", "units"])
    buy_price_col = _find_column(headers, ["buy_price", "buy rate", "purchase_price", "cost_per_share", "buy_average"])
    sell_price_col = _find_column(headers, ["sell_price", "sell rate", "sale_price", "sell_average"])
    term_col = _find_column(headers, ["term", "holding", "holding_period", "ltcg/stcg", "type"])
    segment_col = _find_column(headers, ["segment", "instrument", "market"])

    entries: list[CGSaleEntry] = []

    for row in reader:
        row_lower = {k.strip().lower(): v.strip() for k, v in row.items()}

        try:
            isin = row_lower.get(isin_col, "INNOTAVAILAB") if isin_col else "INNOTAVAILAB"
            symbol = row_lower.get(symbol_col, "Unknown") if symbol_col else "Unknown"

            sell_date = _parse_date(row_lower.get(sell_date_col, "")) if sell_date_col else date.today()
            qty = Decimal(row_lower.get(qty_col, "0")) if qty_col else Decimal("0")
            sell_price = Decimal(row_lower.get(sell_price_col, "0")) if sell_price_col else Decimal("0")
            buy_price = Decimal(row_lower.get(buy_price_col, "0")) if buy_price_col else Decimal("0")

            consideration = qty * sell_price
            cost = qty * buy_price
            gain = consideration - cost

            # Term detection
            term = ""
            if term_col:
                term_str = row_lower.get(term_col, "").upper()
                if "LONG" in term_str or "LT" in term_str:
                    term = "Long"
                elif "SHORT" in term_str or "ST" in term_str:
                    term = "Short"

            segment = row_lower.get(segment_col, "") if segment_col else ""
            asset_class = _detect_asset_class(segment)

            entry = CGSaleEntry(
                date=sell_date,
                isin=isin,
                security_name=symbol,
                quantity=qty,
                sale_price=sell_price,
                consideration=consideration,
                cost=cost,
                stt_paid="EQ" in segment.upper() or "equity" in segment.lower(),
                term=term,
                asset_class=asset_class,
                gain=gain,
            )

            entries.append(entry)

        except (ValueError, KeyError):
            continue

    return entries


# ── Helpers ──────────────────────────────────────────────────────────

def _find_column(headers: list[str], candidates: list[str]) -> Optional[str]:
    """Find the first matching column header from candidates."""
    for h in headers:
        for c in candidates:
            if c in h:
                return h
    # If no match, try exact match on first candidate
    for c in candidates:
        if c in headers:
            return c
    return None


def _parse_date(date_str: str) -> date:
    """Parse a date string in various common formats."""
    if not date_str:
        return date.today()

    formats = [
        "%Y-%m-%d",     # 2026-01-15
        "%d/%m/%Y",     # 15/01/2026
        "%d-%m-%Y",     # 15-01-2026
        "%d-%b-%Y",     # 15-Jan-2026
        "%d %b %Y",     # 15 Jan 2026
        "%d/%m/%y",     # 15/01/26
        "%m/%d/%Y",     # 01/15/2026
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue

    # Last resort: try ISO format
    try:
        return date.fromisoformat(date_str.strip())
    except (ValueError, TypeError):
        return date.today()


def _detect_asset_class(segment: str) -> str:
    """Detect asset class from segment/market identifier."""
    s = segment.upper()
    if "EQ" in s or "EQUITY" in s:
        return "equity"
    if "MF" in s or "MUTUAL" in s:
        return "equity_mf"
    if "FNO" in s or "FUT" in s or "OPT" in s:
        return "futures_options"
    if "COMMODITY" in s or "MCX" in s:
        return "commodity"
    if "CURRENCY" in s or "CDS" in s:
        return "currency"
    if "DEBT" in s or "BOND" in s or "GILT" in s:
        return "debt"
    return "equity"
