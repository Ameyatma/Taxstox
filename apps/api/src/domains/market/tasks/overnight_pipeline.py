import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd

# UNIVERSE_SIZE defaults to 25 if not set via environment
UNIVERSE_SIZE = int(os.environ.get("UNIVERSE_SIZE", "25"))

# HF_TOKEN for external sentiment engine (optional)
HF_TOKEN = os.environ.get("HF_TOKEN", "")

from tasks.celery_app import celery_app
from ingestion.yfinance_ingester import YFinanceIngester
from ingestion.news_ingester import NewsIngester
from hygiene.jesse_processor import JesseHygieneProcessor
from features.technical import TechnicalFeatureEngine
from nlp.sentiment_factory import SentimentFactory
from storage.database import get_db_session
from storage.models import Stock, EODCandle, RecommendationSignal, NewsCatalyst, AlphaFactor
from core.notifications import NotificationService
import logging

logger = logging.getLogger(__name__)

# Initialize sentiment engine with fallback
try:
    sentiment_engine = SentimentFactory.get_engine()
    logger.info(f"Sentiment engine initialized: {sentiment_engine.__class__.__name__}")
except Exception as e:
    logger.error(f"Failed to initialize sentiment engine: {e}")
    logger.info("Falling back to HeuristicSentimentEngine")
    from nlp.sentiment_factory import HeuristicSentimentEngine
    sentiment_engine = HeuristicSentimentEngine()

# How much weight an autonomously mined factor score carries in the composite.
# The remaining (1 - ALPHA_BLEND_WEIGHT) stays with the hand-tuned score below.
ALPHA_BLEND_WEIGHT = 0.30

def calculate_composite_score(technical_score: float, sentiment_score: float, volume_momentum: float) -> float:
    """
    Calculate composite recommendation score.
    Weights: technical 0.50, sentiment 0.35, volume_momentum 0.15
    """
    return 0.50 * technical_score + 0.35 * sentiment_score + 0.15 * volume_momentum

def load_active_factors(session) -> List[Dict[str, Any]]:
    """
    Load every factor the RD-Agent deployed (is_active=True) and compile it to a callable.

    A factor that no longer compiles (schema drift, hand-edited row) is skipped with a
    warning rather than aborting the whole pipeline run.
    """
    from research.validation_unit import ValidationUnit, FactorSandboxError

    factors = session.query(AlphaFactor).filter(AlphaFactor.is_active == True).all()  # noqa: E712
    compiled = []
    for factor in factors:
        try:
            fn = ValidationUnit.compile_factor_code(factor.python_code)
        except FactorSandboxError as exc:
            print(f"Skipping active factor '{factor.name}': {exc}")
            continue
        compiled.append({"name": factor.name, "fn": fn, "ic": factor.information_coefficient})
    return compiled

def calculate_alpha_score(df: pd.DataFrame, active_factors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply every active mined factor to the symbol's OHLCV and average their latest output.

    Each factor returns a Series in [0, 1]; we take the most recent bar's value from each
    and average them into a single alpha score. Factors that raise are skipped.
    """
    from research.validation_unit import ValidationUnit, FactorSandboxError

    scores = {}
    for factor in active_factors:
        try:
            series = ValidationUnit.apply_factor(factor["fn"], df)
        except FactorSandboxError as exc:
            print(f"  Factor '{factor['name']}' failed on this symbol: {exc}")
            continue
        scores[factor["name"]] = float(series.iloc[-1])

    if not scores:
        return {"alpha_score": None, "factor_scores": {}}
    return {"alpha_score": sum(scores.values()) / len(scores), "factor_scores": scores}

def determine_rating(composite_score: float) -> str:
    """Determine final rating from composite score."""
    if composite_score >= 0.75:
        return "STRONG_BUY"
    elif composite_score >= 0.60:
        return "BUY"
    elif composite_score >= 0.40:
        return "HOLD"
    elif composite_score >= 0.25:
        return "SELL"
    else:
        return "STRONG_SELL"

def calculate_risk_levels(current_price: float, atr: float) -> Dict[str, float]:
    """
    Calculate dynamic risk parameters.
    Dynamic Entry: Latest close price.
    ATR Trailing Stop-Loss Floor: Close - (2.0 * ATR).
    Target Price: Close + (3.0 * ATR).
    """
    stop_loss_price = current_price - (2.0 * atr)
    target_price = current_price + (3.0 * atr)
    return {
        "stop_loss_price": stop_loss_price,
        "target_price": target_price
    }

def calculate_volume_momentum(df: pd.DataFrame) -> float:
    """
    Calculate volume momentum as normalized ratio of today's volume to average volume of past 20 days (excluding today).
    Returns a value in [0, 1].
    """
    if len(df) < 21:
        # Not enough data, return neutral
        return 0.5
    # Average volume of the past 20 days (excluding today)
    past_vol_avg = df['volume'].iloc[-21:-1].mean()
    if past_vol_avg == 0:
        return 0.5
    volume_ratio = (df['volume'].iloc[-1] - past_vol_avg) / past_vol_avg
    # Clamp to [-1, 1]
    volume_ratio = max(-1.0, min(1.0, volume_ratio))
    # Normalize to [0, 1]
    return (volume_ratio + 1.0) / 2.0

@celery_app.task(bind=True, name="tasks.overnight_pipeline.run_overnight_pipeline")
def run_overnight_pipeline(self, universe=None, limit=None):
    """Celery task to run the overnight pipeline."""
    # This task will be scheduled to run overnight
    asyncio.run(_run_pipeline_async(universe, limit))

async def _run_pipeline_async(universe=None, limit=None):
    """Async implementation of the overnight pipeline."""
    # Determine which universe to process
    if universe is None:
        watchlist = settings.DEFAULT_UNIVERSE
    else:
        watchlist = universe

    # Apply safety cap: default to UNIVERSE_SIZE, but not exceeding 500
    process_limit = min(limit or settings.UNIVERSE_SIZE, 500)
    # Slice the universe to strictly enforce the limit
    tickers_to_process = watchlist[:process_limit]

    # If we are processing more than 50 tickers, sleep between each to avoid rate limits
    sleep_between_ticks = process_limit > 50

    # Initialize components
    yf_ingester = YFinanceIngester(config={})
    news_ingester = NewsIngester(config={})
    hygiene_processor = JesseHygieneProcessor(config={'timeframe': '1d', 'validate_ohlcv': True})

    # Load the autonomously mined factors once for the whole run.
    with get_db_session() as session:
        active_factors = load_active_factors(session)
    if active_factors:
        print(f"Loaded {len(active_factors)} active mined factor(s): "
              f"{', '.join(f['name'] for f in active_factors)}")
    else:
        print("No active mined factors deployed; using the hand-tuned composite only.")

    for i, symbol in enumerate(tickers_to_process):
        try:
            # 1. Ingest historical data (minimum 120 bars for EMA-200/RSI-14 warm-up)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=250)  # ~250 trading days

            ohlcv_batch = await yf_ingester.ingest(symbol, start_date, end_date)

            if not ohlcv_batch or len(ohlcv_batch.data) < 50:
                print(f"Insufficient data for {symbol}, skipping")
                if sleep_between_ticks and i < len(tickers_to_process) - 1:
                    await asyncio.sleep(0.5)
                continue

            # 2. Ingest news for the symbol
            news_batch = await news_ingester.ingest(symbol)

            # 3. Validate OHLCV data with JesseProcessor
            cleaned_batch = await hygiene_processor.process(ohlcv_batch)

            if not cleaned_batch.data:
                print(f"Data validation failed for {symbol}, skipping")
                if sleep_between_ticks and i < len(tickers_to_process) - 1:
                    await asyncio.sleep(0.5)
                continue

            # 4. Convert to DataFrame for technical analysis
            df = pd.DataFrame([{
                'timestamp': c.timestamp,
                'open': c.open,
                'high': c.high,
                'low': c.low,
                'close': c.close,
                'volume': c.volume
            } for c in cleaned_batch.data])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)

            # 5. Calculate vectorized technical features
            tech_engine = TechnicalFeatureEngine()
            df['rsi_14'] = tech_engine.rsi(df['close'], period=14)
            df['ema_20'] = tech_engine.ema(df['close'], period=20)
            df['ema_50'] = tech_engine.ema(df['close'], period=50)
            df['ema_200'] = tech_engine.ema(df['close'], period=200)
            macd_line, signal_line, histogram = tech_engine.macd(df['close'])
            df['macd'] = macd_line
            df['macd_signal'] = signal_line
            df['macd_hist'] = histogram
            df['atr_14'] = tech_engine.atr(df, period=14)
            upper, middle, lower = tech_engine.bollinger_bands(df['close'])
            df['bb_upper'] = upper
            df['bb_middle'] = middle
            df['bb_lower'] = lower

            # Get latest values
            latest = df.iloc[-1]
            current_price = latest['close']
            rsi = latest['rsi_14']
            macd_val = latest['macd']
            atr = latest['atr_14']

            # 6. Process news and get aggregate sentiment
            news_sentiments = []
            news_catalysts_to_save = []
            if news_batch and news_batch.articles:
                # Collect all texts for batch analysis
                texts = [f"{article.title}. {article.content}" for article in news_batch.articles]
                try:
                    sentiment_scores = sentiment_engine.analyze(texts)
                except Exception as e:
                    logger.error(f"Sentiment analysis failed: {e}")
                    sentiment_scores = [0.0] * len(news_batch.articles)

                for i, article in enumerate(news_batch.articles):
                    sentiment_score = sentiment_scores[i] if i < len(sentiment_scores) else 0.0
                    news_sentiments.append(sentiment_score)
                    # Prepare NewsCatalyst for saving
                    # Note: analyze() returns scores only. We use default values
                    # for confidence/catalyst_type/rationale to maintain DB compatibility.
                    catalyst = NewsCatalyst(
                        symbol=symbol,
                        publish_timestamp=article.published_at,
                        headline=article.title,
                        content=article.content,
                        sentiment_score=sentiment_score,
                        confidence=0.5,
                        catalyst_type="UNKNOWN",
                        rationale="Sentiment analysis via pluggable engine"
                    )
                    news_catalysts_to_save.append(catalyst)

            # Aggregate news sentiment: average if we have news, else neutral
            if news_sentiments:
                sentiment_score = sum(news_sentiments) / len(news_sentiments)
            else:
                sentiment_score = 0.0  # neutral

            # 7. Calculate technical score (using RSI and MACD)
            # RSI: 30-70 normalized to 0-1
            rsi_score = max(0.0, min(1.0, (rsi - 30.0) / 40.0))
            # MACD: we'll use the sign and magnitude? Let's use a simple bullish/bearish.
            # We'll normalize MACD by a typical range? For simplicity, we'll use:
            #   macd_score = 1 if macd > 0 else 0
            # But we can also normalize by the price? Let's keep it simple for now.
            macd_score = 1.0 if macd_val > 0 else 0.0
            technical_score = (rsi_score + macd_score) / 2.0

            # 8. Calculate volume momentum
            volume_momentum = calculate_volume_momentum(df)

            # 9. Composite score, blended with the autonomous alpha factors
            base_score = calculate_composite_score(technical_score, sentiment_score, volume_momentum)
            alpha = calculate_alpha_score(df, active_factors)
            alpha_score = alpha["alpha_score"]

            if alpha_score is None:
                composite_score = base_score
            else:
                composite_score = (1.0 - ALPHA_BLEND_WEIGHT) * base_score + ALPHA_BLEND_WEIGHT * alpha_score
                detail = ", ".join(f"{k}={v:.3f}" for k, v in alpha["factor_scores"].items())
                print(f"  [{symbol}] base={base_score:.4f} alpha_avg={alpha_score:.4f} ({detail})")

            final_rating = determine_rating(composite_score)

            # 10. Risk levels
            risk_levels = calculate_risk_levels(current_price, atr)

            # 11. Persist to database
            with get_db_session() as session:
                # Ensure stock exists
                stock = session.query(Stock).filter_by(ticker=symbol).first()
                if not stock:
                    stock = Stock(ticker=symbol)
                    session.add(stock)
                    session.flush()

                # Save news catalysts
                for catalyst in news_catalysts_to_save:
                    session.add(catalyst)

                # Save recommendation signal
                signal = RecommendationSignal(
                    date=datetime.now(),
                    symbol=symbol,
                    final_rating=final_rating,
                    composite_score=composite_score,
                    tech_score=technical_score,
                    sentiment_score=sentiment_score,
                    stop_loss_price=risk_levels['stop_loss_price'],
                    target_price=risk_levels['target_price']
                )
                session.add(signal)
                session.commit()

                print(f"Saved recommendation for {symbol}: {final_rating} (composite={composite_score:.4f})")
                print(f"  Saved {len(news_catalysts_to_save)} news catalysts.")

        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            if sleep_between_ticks and i < len(tickers_to_process) - 1:
                await asyncio.sleep(0.5)
            continue

        # Sleep between tickers if we are processing more than 50 to avoid rate limits
        if sleep_between_ticks and i < len(tickers_to_process) - 1:
            await asyncio.sleep(0.5)

    # --- Trigger user notifications (STRONG_BUY signals / high-confidence catalysts) ---
    print("Checking for push notifications to trigger...")
    try:
        with get_db_session() as session:
            NotificationService.check_and_trigger_alerts(session)
    except Exception as e:
        print(f"Error during notification check: {e}")

if __name__ == "__main__":
    # For testing without Celery
    asyncio.run(_run_pipeline_async())