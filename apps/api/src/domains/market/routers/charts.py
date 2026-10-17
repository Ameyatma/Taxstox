from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from sqlalchemy import asc, or_

from src.domains.market.storage.database import get_db_session
from src.domains.market.storage.models import EODCandle, NewsCatalyst, Stock

router = APIRouter()


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_stocks(
    q: str = Query(..., min_length=1, description="Search query (symbol or company name)"),
    limit: int = Query(10, ge=1, le=50, description="Max results to return"),
):
    """Search the stock universe by ticker or company name.

    Results are ranked best-match-first using a simple relevance score:
    exact ticker prefix match > ticker contains > name contains. The
    caller can cap the result set with `limit` (default 10, max 50).
    """
    needle = q.strip().upper()
    if not needle:
        return []

    with get_db_session() as session:
        # Pull a generous candidate pool, then rank in Python so the
        # ordering stays predictable and easy to tune.
        candidates = (
            session.query(Stock)
            .filter(
                or_(
                    Stock.ticker.ilike(f"{needle}%"),
                    Stock.ticker.ilike(f"%{needle}%"),
                    Stock.name.ilike(f"%{needle}%"),
                )
            )
            .all()
        )

    def _score(stock: Stock) -> int:
        ticker = (stock.ticker or "").upper()
        name = (stock.name or "").upper()
        if ticker == needle:
            return 0
        if ticker.startswith(needle):
            return 1
        if name.startswith(needle):
            return 2
        return 3

    ranked = sorted(candidates, key=_score)
    return [
        {
            "symbol": s.ticker,
            "company_name": s.name or s.ticker,
            "exchange": s.exchange,
            "sector": s.sector,
            "industry": s.industry,
        }
        for s in ranked[:limit]
    ]


@router.get("/{symbol}/chart")
async def get_chart_data(symbol: str) -> Dict[str, Any]:
    """
    Get chart data for a given stock symbol in TradingView format.
    Returns candlestick data, volume data, and news catalyst markers.
    """
    with get_db_session() as session:
        # Query OHLCV data for the symbol, ordered by timestamp (ascending)
        ohlcv_records = session.query(EODCandle).filter(
            EODCandle.symbol == symbol
        ).order_by(asc(EODCandle.timestamp)).all()

        # Build candles list in TradingView format (time as "YYYY-MM-DD HH:mm:ss")
        candles: List[Dict[str, Any]] = []
        for record in ohlcv_records:
            candles.append({
                "time": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "open": record.open,
                "high": record.high,
                "low": record.low,
                "close": record.close,
                "volume": record.volume
            })

        # Build markers list from news catalysts for this symbol
        markers: List[Dict[str, Any]] = []
        catalysts = session.query(NewsCatalyst).filter(
            NewsCatalyst.symbol == symbol
        ).all()

        for catalyst in catalysts:
            # Determine marker color based on sentiment_score
            color = "green" if catalyst.sentiment_score > 0.1 else "red"
            # Add marker with the headline as text, timestamp for placement, and sentiment score for color
            markers.append({
                "time": catalyst.publish_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "text": catalyst.headline,
                "color": color,
                "description": catalyst.content
            })

        # Return the chart data
        return {
            "symbol": symbol,
            "candles": candles,
            "markers": markers
        }