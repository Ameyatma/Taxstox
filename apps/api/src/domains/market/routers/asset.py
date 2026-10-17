from fastapi import APIRouter, HTTPException, Path
from typing import Dict, Any
import yfinance as yf
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import or_

from src.domains.market.storage.database import get_db_session
from src.domains.market.storage.models import Stock

router = APIRouter()

# We'll use a thread pool to run yfinance calls because they are blocking
executor = ThreadPoolExecutor(max_workers=5)


def _score(candidate_ticker: str, candidate_name: str, needle: str) -> int:
    """Relevance score for a search candidate. Lower is better.

    Exact ticker > bare ticker == needle > bare ticker prefix > name prefix >
    name contains. The bare ticker is the part before the exchange suffix
    (e.g. "HDFCBANK" from "HDFCBANK.NS").
    """
    t = (candidate_ticker or "").upper()
    n = (candidate_name or "").upper()
    bare = t.split(".")[0]
    if t == needle:
        return 0
    if bare == needle:
        return 1
    if bare.startswith(needle):
        return 2
    if n.startswith(needle):
        return 3
    return 4


def _resolve_symbol(symbol: str) -> str:
    """Resolve a user-typed symbol to its canonical yfinance ticker.

    Users type short forms and company names — "HDFC", "MAHINDRA", "RELIANCE" —
    none of which are valid yfinance tickers on their own. Without this, the
    asset endpoint passes the raw string to yfinance, which returns 404 and
    the page shows "Could not load asset data".

    Resolution order:
      1. Already canonical (contains a dot or .NS/.BO suffix) — return as-is.
      2. Exact ticker match in the stocks table.
      3. Ticker stored with a suffix we can append ("HDFC" -> "HDFCBANK.NS").
      4. Company-name match ("MAHINDRA" -> "M&M.NS").
      5. No match — return the input unchanged so the caller can still try
         yfinance with it (US stocks, unseeded symbols, etc.).
    """
    needle = symbol.strip().upper()
    if not needle:
        return symbol

    # Already canonical — contains an exchange suffix or a dot.
    if "." in needle or needle.endswith("NS") or needle.endswith("BO"):
        return symbol

    with get_db_session() as session:
        # 2. Exact ticker match.
        exact = session.query(Stock).filter(Stock.ticker == needle).first()
        if exact:
            return exact.ticker

        # 3. Ticker stored with a suffix we can append.
        suffix_hits = (
            session.query(Stock)
            .filter(
                or_(
                    Stock.ticker == f"{needle}.NS",
                    Stock.ticker == f"{needle}.BO",
                )
            )
            .all()
        )
        if suffix_hits:
            suffix_hits.sort(key=lambda s: (_score(s.ticker, s.name, needle), len(s.ticker)))
            return suffix_hits[0].ticker

        # 4. Company-name match, ranked by relevance.
        name_hits = (
            session.query(Stock)
            .filter(Stock.name.ilike(f"%{needle}%"))
            .all()
        )
        if name_hits:
            name_hits.sort(key=lambda s: (_score(s.ticker, s.name, needle), len(s.ticker)))
            return name_hits[0].ticker

    return symbol

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

def fetch_asset_data(symbol: str) -> Dict[str, Any]:
    """
    Fetch asset data from yfinance.
    This function is blocking and will be run in a thread.
    """
    # Normalize symbol for Indian stocks: if no dot and not already suffixed, add .NS
    # But for US stocks, keep as-is (e.g., AAPL, not AAPL.NS)
    final_symbol = symbol

    # First, determine the best symbol to use
    if '.' not in symbol and not symbol.endswith('.NS') and not symbol.endswith('.BO'):
        # Try with .NS first (Indian stock convention)
        symbol_with_suffix = f"{symbol}.NS"

        # Create ticker with .NS suffix to check if it's an Indian stock
        try:
            # Use the session properly as the second argument to yf.Ticker
            session_obj = _get_yf_session()
            ticker_with_suffix = yf.Ticker(symbol_with_suffix, session=session_obj)
            info_with_suffix = ticker_with_suffix.info
            # log the symbols for debugging
            print(f"DEBUG: Created ticker_with_suffix for {symbol_with_suffix}: {ticker_with_suffix.info.get('symbol', 'unknown')}")

            # If it's an Indian stock (has proper name and currency INR), use it
            # If not, try without the .NS suffix for US stocks
            if info_with_suffix.get('currency') == 'INR' and info_with_suffix.get('longName'):
                final_symbol = symbol_with_suffix
            # else keep symbol as is (US stock)
        except Exception:
            # If .NS suffix fails, use the original symbol
            final_symbol = symbol
    else:
        # Symbol already has suffix or contains dot, use as-is
        final_symbol = symbol

    # Create the ticker with the final symbol
    session_obj = _get_yf_session()
    ticker = yf.Ticker(final_symbol, session=session_obj)
    print(f"DEBUG: Created ticker for {final_symbol}: {ticker.info.get('symbol', 'unknown')}")

    # Get basic info
    print(f"DEBUG: About to fetch info for symbol {final_symbol}")
    info = ticker.info
    print(f"DEBUG: Fetched info, keys: {list(info.keys())}")
    # Clean the info dict: replace NaN with None
    import math
    cleaned_info = {}
    for key, value in info.items():
        if isinstance(value, float) and math.isnan(value):
            cleaned_info[key] = None
        else:
            cleaned_info[key] = value
    info = cleaned_info

    # Get historical data for performance calculation
    hist = ticker.history(period="1y")

    # Strip timezone awareness from index to avoid issues with timezone-aware timestamps
    if not hist.empty:
        hist.index = hist.index.tz_localize(None)

    # Calculate returns for different periods
    # We'll calculate the percentage change from the price at the start of the period to the last valid price
    # If we don't have enough data, we'll return None for that period

    def get_last_valid_price(series, end_idx):
        """Get the last valid (non-NaN) price from series up to end_idx."""
        for i in range(end_idx, -1, -1):
            price = series.iloc[i]
            if not (isinstance(price, float) and math.isnan(price)):
                return float(price)  # Convert to regular Python float
        return None

    def calculate_return(days):
        if len(hist) < days:
            return None
        # We'll take the last 'days' trading days using ordinal indexing
        # Start from (days-1) positions ago to get the period of exactly 'days' trading days
        start_idx = len(hist) - days
        end_idx = len(hist) - 1

        # Ensure we have valid indices
        if start_idx < 0 or end_idx < 0:
            return None

        start_price = hist["Close"].iloc[start_idx]
        # Find the last valid price (not NaN) from end_idx backwards
        end_price = get_last_valid_price(hist["Close"], end_idx)

        # Check for NaN values
        if isinstance(start_price, float) and math.isnan(start_price):
            return None
        if end_price is None or (isinstance(end_price, float) and math.isnan(end_price)):
            return None

        # Calculate and round to 2 decimal places
        return_pct = ((end_price - start_price) / start_price) * 100
        return round(float(return_pct), 2)  # Ensure regular Python float

    returns = {
        "1W": calculate_return(5),   # Approximately 5 trading days
        "1M": calculate_return(21),  # Approximately 21 trading days
        "6M": calculate_return(126), # Approximately 126 trading days
        "1Y": calculate_return(len(hist)) # Full period
    }

    # Get analyst recommendations
    # Try to get from info first
    recommendation_key = info.get('recommendationKey')
    number_of_analyst_opinions = info.get('numberOfAnalystOpinions')
    target_mean_price = info.get('targetMeanPrice')

    # If not in info, try to get from recommendations_summary
    if recommendation_key is None:
        try:
            rec_summary = ticker.recommendations_summary
            if not rec_summary.empty:
                # Get the latest recommendation
                latest = rec_summary.iloc[-1]
                recommendation_key = latest.get('To Grade')
                # Note: The column might be 'To Grade' or something else, we'll adjust if needed
                # For now, we'll assume it's in the info as above
        except Exception:
            pass

    # Map recommendation_key to our consensus (raw)
    consensus_map = {
        'strong_buy': 'STRONG_BUY',
        'buy': 'BUY',
        'hold': 'HOLD',
        'sell': 'SELL',
        'underperform': 'SELL',  # Treat underperform as sell
        'outperform': 'BUY'      # Treat outperform as buy
    }
    raw_consensus = consensus_map.get(recommendation_key, 'HOLD').upper() if recommendation_key else 'HOLD'

    # Get current price for the guardrail
    current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
    # Apply guardrail: if current price is above or equal to target price, downgrade BUY/STRONG_BUY to HOLD
    final_consensus = raw_consensus
    if target_mean_price and current_price and current_price != 0:
        implied_return = (target_mean_price - current_price) / current_price
        if raw_consensus in ["BUY", "STRONG_BUY"] and implied_return <= 0:
            final_consensus = "HOLD"

    # Build the response
    data = {
        "symbol": symbol,
        "company_name": info.get('longName', 'N/A'),
        "current_price": info.get('currentPrice', info.get('regularMarketPrice', 0)),
        "currency": info.get('currency', 'USD'),
        "day_change_pct": info.get('regularMarketChangePercent', 0),
        "market_cap": info.get('marketCap', 0),
        "pe_ratio": info.get('trailingPE', info.get('forwardPE', 0)),
        "dividend_yield": info.get('dividendYield', 0),
        "fifty_two_week_high": info.get('fiftyTwoWeekHigh', 0),
        "fifty_two_week_low": info.get('fiftyTwoWeekLow', 0),
        "performance": returns,
        "analyst_consensus": {
            "consensus": final_consensus,
            "target_price": target_mean_price,
            "total_analysts": number_of_analyst_opinions
        }
    }

    return data

@router.get("/{symbol}")
async def get_asset(
    symbol: str = Path(..., description="Stock symbol (e.g., RELIANCE.NS or AAPL)")
):
    """
    Get asset data including price, fundamentals, performance, and analyst consensus.

    Accepts both canonical tickers ("HDFCBANK.NS") and the short forms / company
    names users actually type ("HDFC", "MAHINDRA"). The latter are resolved to
    their canonical ticker against the stocks table before yfinance is called,
    so a direct URL like /terminal/asset/HDFC works instead of 404-ing.
    """
    try:
        canonical = _resolve_symbol(symbol)
        # Run the blocking yfinance call in a thread
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(executor, fetch_asset_data, canonical)
        # Surface the canonical ticker the caller typed in the response, so the
        # UI breadcrumb shows "HDFC" rather than the resolved "HDFCBANK.NS".
        if canonical != symbol:
            data["requested_symbol"] = symbol
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Asset data not found for symbol '{symbol}': {str(e)}")