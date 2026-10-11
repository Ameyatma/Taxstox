from fastapi import APIRouter, HTTPException, Path
from typing import Dict, Any
import yfinance as yf
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor

router = APIRouter()

# We'll use a thread pool to run yfinance calls because they are blocking
executor = ThreadPoolExecutor(max_workers=5)

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
            ticker_with_suffix = _get_yf_session().Ticker(symbol_with_suffix)
            info_with_suffix = ticker_with_suffix.info

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
    ticker = _get_yf_session().Ticker(final_symbol)

    # Get basic info
    info = ticker.info
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
    """
    try:
        # Run the blocking yfinance call in a thread
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(executor, fetch_asset_data, symbol)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Asset data not found for symbol '{symbol}': {str(e)}")