import os
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# Try to import openai, but we'll make it optional
try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)

class FinGPTSentimentEngine:
    """
    FinGPT-style LLM sentiment engine for financial news.
    Supports live mode (via LLM API) and fallback/local mode (lexicon-based).
    """

    def __init__(self, config: dict):
        self.config = config
        self.api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.use_live = bool(self.api_key and openai is not None)
        if self.use_live:
            # Set up the OpenAI client (assuming OpenAI-compatible API for DeepSeek)
            openai.api_key = self.api_key
            # Optionally set base URL for DeepSeek if needed
            # openai.api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
            logger.info("FinGPTSentimentEngine initialized in LIVE mode.")
        else:
            logger.info("FinGPTSentimentEngine initialized in FALLBACK mode.")
            # Initialize a simple financial lexicon for fallback
            self.positive_words = {
                'beat', 'exceed', 'surpass', 'outperform', 'strong', 'growth', 'profit', 'gain',
                'up', 'rise', 'increase', 'positive', 'bullish', 'buy', 'outlook', 'upgrade',
                'raise', 'higher', 'best', 'win', 'success', 'efficiency', 'margin', 'revenue'
            }
            self.negative_words = {
                'miss', 'underperform', 'weak', 'loss', 'decline', 'down', 'fall', 'decrease',
                'negative', 'bearish', 'sell', 'downgrade', 'lower', 'worst', 'fail', 'risk',
                'concern', 'challenge', 'pressure', 'margin', 'revenue'  # Note: revenue can be both, but we'll handle context
            }

    def _extract_ticker(self, text: str) -> Optional[str]:
        """Extract ticker from text (simple version: look for known tickers or patterns)."""
        # In a real implementation, we might use NER or a list of tickers.
        # For now, we'll return None and let the caller provide the ticker.
        return None

    def _simple_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Fallback sentiment analysis using a financial lexicon.
        Returns a dict with sentiment_score, confidence, catalyst_type, and rationale.
        """
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        pos_count = len(words.intersection(self.positive_words))
        neg_count = len(words.intersection(self.negative_words))
        total = pos_count + neg_count
        if total == 0:
            score = 0.0
            confidence = 0.5
        else:
            score = (pos_count - neg_count) / total  # Range [-1, 1]
            confidence = min(0.5 + 0.5 * (total / 20), 1.0)  # More words -> higher confidence, cap at 1.0

        # Determine catalyst type based on keywords (simplified)
        catalyst_type = "NEUTRAL"
        if any(word in text_lower for word in ['earnings', 'profit', 'revenue', 'sales']):
            if score > 0.2:
                catalyst_type = "EARNINGS_BEAT"
            elif score < -0.2:
                catalyst_type = "EARNINGS_MISS"
        elif any(word in text_lower for word in ['product', 'launch', 'innovation']):
            catalyst_type = "PRODUCT_NEWS"
        elif any(word in text_lower for word in ['merger', 'acquisition', 'm&a']):
            catalyst_type = "M_AND_A"
        elif any(word in text_lower for word in ['dividend', 'buyback']):
            catalyst_type = "SHAREHOLDER_RETURN"

        # Rationale: a simple summary
        rationale = f"Found {pos_count} positive and {neg_count} negative financial keywords."

        return {
            "sentiment_score": max(-1.0, min(1.0, score)),
            "confidence": confidence,
            "catalyst_type": catalyst_type,
            "rationale": rationale
        }

    def analyze(self, text: str, ticker: str) -> Dict[str, Any]:
        """
        Analyze the given text for sentiment and return structured output.
        :param text: The news text (title + content) to analyze.
        :param ticker: The stock ticker symbol.
        :return: Dict with keys: ticker, sentiment_score, confidence, catalyst_type, rationale.
        """
        if self.use_live:
            return self._live_analysis(text, ticker)
        else:
            result = self._simple_sentiment(text)
            result["ticker"] = ticker
            return result

    def _live_analysis(self, text: str, ticker: str) -> Dict[str, Any]:
        """
        Call the LLM API (OpenAI/DeepSeek) to get sentiment analysis.
        """
        system_prompt = """You are a financial analyst expert. Analyze the given financial news text and provide:
        - A sentiment score between -1.0 (very negative) and 1.0 (very positive).
        - A confidence score between 0.0 and 1.0.
        - A catalyst type (e.g., EARNINGS_BEAT, EARNINGS_MISS, PRODUCT_LAUNCH, M_AND_A, SHAREHOLDER_RETURN, MACROECONOMIC, REGULATORY, etc.).
        - A brief rationale for your assessment.
        Output must be a valid JSON object with the following keys: ticker, sentiment_score, confidence, catalyst_type, rationale.
        Do not include any extra text."""
        user_prompt = f"Ticker: {ticker}\n\nNews Text: {text}"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # or "deepseek-chat" if using DeepSeek
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                max_tokens=200,
                response_format={"type": "json_object"}  # Ensure JSON output
            )
            result = json.loads(response.choices[0].message.content)
            # Ensure the ticker is set correctly
            result["ticker"] = ticker
            # Validate and clamp scores
            result["sentiment_score"] = max(-1.0, min(1.0, result.get("sentiment_score", 0.0)))
            result["confidence"] = max(0.0, min(1.0, result.get("confidence", 0.5)))
            return result
        except Exception as e:
            logger.error(f"Error in live sentiment analysis: {e}")
            # Fallback to simple sentiment on error
            result = self._simple_sentiment(text)
            result["ticker"] = ticker
            return result