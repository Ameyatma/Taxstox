from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from sqlalchemy import asc

from src.domains.market.storage.database import get_db_session
from src.domains.market.storage.models import EODCandle, NewsCatalyst

router = APIRouter()

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