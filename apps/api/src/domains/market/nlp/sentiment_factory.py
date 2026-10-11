"""
Pluggable sentiment analysis factory as per mission requirements.
Supports three backends: local (FinBERT), external (HF API), heuristic (rule-based).
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np

from config.settings import settings

logger = logging.getLogger(__name__)


class BaseSentimentEngine(ABC):
    """Abstract base class for sentiment engines."""

    @abstractmethod
    def analyze(self, texts: List[str]) -> List[float]:
        """Analyze sentiment for a list of texts.

        Args:
            texts: List of text strings to analyze.

        Returns:
            List of sentiment scores between -1.0 (negative) and 1.0 (positive).
        """
        pass


class LocalBertEngine(BaseSentimentEngine):
    """Local FinBERT engine using PyTorch model."""

    def __init__(self):
        # Lazy load the model to avoid import errors if not needed
        try:
            from transformers import pipeline
            self.classifier = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                return_all_scores=True,
                device="cpu",
                top_k=None
            )
            logger.info("LocalBertEngine initialized with FinBERT model")
        except Exception as e:
            logger.error(f"Failed to initialize LocalBertEngine: {e}")
            raise

    def analyze(self, texts: List[str]) -> List[float]:
        """Analyze sentiment using FinBERT model."""
        try:
            # Process texts in batches if needed (but for simplicity, we process all at once)
            results = self.classifier(texts)  # List of list of dicts
            scores = []
            for result in results:
                # Map label to score
                score_map = {item['label']: item['score'] for item in result}
                pos = score_map.get('positive', 0.0)
                neg = score_map.get('negative', 0.0)
                # Sentiment score: P(positive) - P(negative)
                sentiment_score = pos - neg
                scores.append(float(sentiment_score))
            return scores
        except Exception as e:
            logger.error(f"Error in LocalBertEngine analyze: {e}")
            # Return neutral scores on error
            return [0.0] * len(texts)


class ApiSentimentEngine(BaseSentimentEngine):
    """External sentiment engine using HuggingFace Inference API."""

    def __init__(self):
        self.api_token = os.getenv("HF_TOKEN") or getattr(settings, 'HF_TOKEN', None)
        self.api_url = "https://api-inference.huggingface.co/models/ProsusAI/finbert"
        if not self.api_token:
            logger.warning("HF_TOKEN not configured, ApiSentimentEngine will fail")

    def analyze(self, texts: List[str]) -> List[float]:
        """Analyze sentiment using HuggingFace Inference API."""
        if not self.api_token:
            logger.error("HF_TOKEN missing, returning neutral scores")
            return [0.0] * len(texts)

        import httpx
        try:
            with httpx.Client(timeout=15.0) as client:  # 15-second timeout as per mission
                # The HF API expects a list of inputs
                response = client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json"
                    },
                    json={"inputs": texts}
                )

                if response.status_code != 200:
                    logger.error(f"HF API error: {response.status_code} - {response.text}")
                    return [0.0] * len(texts)

                result = response.json()

                # Handle HF API response format: list of list of dicts
                scores = []
                if isinstance(result, list) and len(result) == len(texts):
                    for item_list in result:
                        if isinstance(item_list, list) and len(item_list) > 0:
                            score_map = {item['label']: item['score'] for item in item_list}
                            pos = score_map.get('positive', 0.0)
                            neg = score_map.get('negative', 0.0)
                            sentiment_score = pos - neg
                            scores.append(float(sentiment_score))
                        else:
                            logger.warning("Unexpected item in HF API response")
                            scores.append(0.0)
                else:
                    logger.error(f"Unexpected HF API response format: {result}")
                    return [0.0] * len(texts)

                return scores
        except Exception as e:
            logger.error(f"Error calling HF API: {e}")
            return [0.0] * len(texts)


class HeuristicSentimentEngine(BaseSentimentEngine):
    """Lightweight rule-based sentiment engine."""

    def __init__(self):
        self.positive_words = {
            'beat', 'exceed', 'surpass', 'outperform', 'strong', 'growth', 'profit', 'gain',
            'up', 'rise', 'increase', 'positive', 'bullish', 'buy', 'outlook', 'upgrade',
            'raise', 'higher', 'best', 'win', 'success', 'efficiency', 'margin', 'revenue',
            'surge', ' rally', 'jump', 'gain', 'outperform', 'upbeat'
        }
        self.negative_words = {
            'miss', 'underperform', 'weak', 'loss', 'decline', 'down', 'fall', 'decrease',
            'negative', 'bearish', 'sell', 'downgrade', 'lower', 'worst', 'fail', 'risk',
            'concern', 'challenge', 'pressure', 'surge', 'default', 'bankruptcy'
        }

    def analyze(self, texts: List[str]) -> List[float]:
        """Analyze sentiment using heuristic rule-based approach."""
        scores = []
        for text in texts:
            text_lower = text.lower()
            words = set(text_lower.split())  # Simple split, not perfect but fast

            pos_count = len(words.intersection(self.positive_words))
            neg_count = len(words.intersection(self.negative_words))
            total = pos_count + neg_count

            if total == 0:
                score = 0.0
            else:
                score = (pos_count - neg_count) / total  # Range [-1, 1]

            scores.append(float(score))
        return scores


class SentimentFactory:
    """Factory for creating sentiment analysis engines."""

    _engines = {}

    @classmethod
    def get_engine(cls) -> BaseSentimentEngine:
        """Get a sentiment engine instance based on SENTIMENT_DRIVER setting."""
        driver = getattr(settings, 'SENTIMENT_DRIVER', 'heuristic').lower()

        if driver in cls._engines:
            return cls._engines[driver]

        engine = None
        if driver == "local":
            try:
                engine = LocalBertEngine()
                logger.info("Using LocalBertEngine (FinBERT)")
            except Exception as e:
                logger.error(f"Failed to create LocalBertEngine: {e}")
                logger.info("Falling back to HeuristicSentimentEngine")
                engine = HeuristicSentimentEngine()
        elif driver == "api":
            engine = ApiSentimentEngine()
            logger.info("Using ApiSentimentEngine (HF API)")
        else:  # default to heuristic
            engine = HeuristicSentimentEngine()
            logger.info("Using HeuristicSentimentEngine (rule-based)")

        # Cache the engine
        cls._engines[driver] = engine
        return engine