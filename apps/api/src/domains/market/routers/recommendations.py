from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import desc, func

from src.domains.market.storage.database import get_db_session
from src.domains.market.storage.models import RecommendationSignal, Stock, NewsCatalyst, EODCandle

router = APIRouter()

@router.get("/next-day")
async def get_next_day_recommendations():
    """
    Query the latest RecommendationSignal records for the upcoming session.
    Return sorted by composite_score descending.
    Includes nested news catalyst summaries and risk boundaries.
    """
    with get_db_session() as session:
        # Get today's date for filtering (assuming 'date' field is the date of the signal)
        today = datetime.now().date()
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today + timedelta(days=1), datetime.min.time())

        # Get the latest signal per symbol for today, sorted by composite_score descending.
        # This deduplicates repeated pipeline runs by taking the most recent date per symbol.
        latest_signals_subq = session.query(
            RecommendationSignal.symbol,
            func.max(RecommendationSignal.date).label('max_date'),
        ).filter(
            RecommendationSignal.date >= start,
            RecommendationSignal.date < end,
        ).group_by(RecommendationSignal.symbol).subquery()

        signals = session.query(RecommendationSignal).join(
            latest_signals_subq,
            (RecommendationSignal.symbol == latest_signals_subq.c.symbol) &
            (RecommendationSignal.date == latest_signals_subq.c.max_date),
        ).order_by(desc(RecommendationSignal.composite_score)).all()

        # Build response with nested news catalysts and risk boundaries
        result = []
        for signal in signals:
            # Get the stock info (optional)
            stock = session.query(Stock).filter_by(ticker=signal.symbol).first()

            # Get news catalysts for this symbol (for today's date)
            catalysts = session.query(NewsCatalyst).filter(
                NewsCatalyst.symbol == signal.symbol,
                NewsCatalyst.publish_timestamp >= datetime.combine(today, datetime.min.time()),
                NewsCatalyst.publish_timestamp < datetime.combine(today + timedelta(days=1), datetime.min.time())
            ).all()

            catalyst_summaries = [
                {
                    "headline": c.headline,
                    "sentiment_score": c.sentiment_score,
                    "confidence": c.confidence,
                    "catalyst_type": c.catalyst_type
                } for c in catalysts
            ]

            # Get latest EODCandle for the symbol to include current price (entry)
            latest_candle = session.query(EODCandle).filter(
                EODCandle.symbol == signal.symbol
            ).order_by(desc(EODCandle.timestamp)).first()

            entry_price = latest_candle.close if latest_candle else None

            result.append({
                "symbol": signal.symbol,
                "date": signal.date,
                "final_rating": signal.final_rating,
                "composite_score": signal.composite_score,
                "tech_score": signal.tech_score,
                "sentiment_score": signal.sentiment_score,
                "entry_price": entry_price,
                "stop_loss_price": signal.stop_loss_price,
                "target_price": signal.target_price,
                "news_catalysts": catalyst_summaries
            })

        return result