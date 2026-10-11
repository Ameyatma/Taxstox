import os
import re

# HF_HOME must be set BEFORE transformers/huggingface_hub are imported: huggingface_hub
# resolves and caches its cache directory at import time, so assigning it after
# `from transformers import pipeline` (as this module used to) had no effect and every
# model silently landed in ~/.cache/huggingface instead of the configured directory.
# `setdefault` lets an explicit environment variable (e.g. the Dockerfile) win.
# Use the configured cache directory from environment, falling back to default.
HF_CACHE_DIR = os.environ.get("HF_CACHE_DIR", "data/models/finbert")
os.environ.setdefault("HF_HOME", HF_CACHE_DIR)

from transformers import pipeline  # noqa: E402  (must follow the HF_HOME assignment)

class InbuiltSentimentEngine:
    """
    Local NLP engine using FinBERT for sentiment analysis.
    """

    def __init__(self):
        # Initialize the huggingface pipeline, enforce CPU
        self.classifier = pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            return_all_scores=True,
            device="cpu",  # -1 for CPU, but device="cpu" also works
            top_k=None
        )

    def _categorize_catalyst(self, headline: str) -> str:
        """
        Categorize the headline into a catalyst type based on keywords.
        """
        headline_lower = headline.lower()

        # Earnings Beat
        if re.search(r'\b(beat|profit\s+jump|raised\s+guidance|record\s+revenue|eps)\b', headline_lower):
            return "EARNINGS_BEAT"
        # Earnings Miss
        if re.search(r'\b(miss|lowered|margin\s+compression|revenue\s+fall)\b', headline_lower):
            return "EARNINGS_MISS"
        # Mergers & Acquisitions
        if re.search(r'\b(buyout|acquisition|merger|takeover|stake)\b', headline_lower):
            return "MERGERS_ACQUISITIONS"
        # Regulatory / Legal
        if re.search(r'\b(sec|antitrust|lawsuit|probe|penalty|approval)\b', headline_lower):
            return "REGULATORY_LEGAL"
        # Product / Macro
        if re.search(r'\b(trial|interest\s+rate|tariff|fda|launch)\b', headline_lower):
            return "PRODUCT_MACRO"
        # General Momentum (fallback)
        return "GENERAL_MOMENTUM"

    def analyze(self, headline: str, ticker: str) -> dict:
        """
        Analyze the headline for sentiment and catalyst.
        """
        # Get probabilities for each label
        results = self.classifier(headline)  # returns list of list of dicts when top_k=None
        # Extract the list of scores for the first (and only) input
        results = results[0]
        # Map label to score
        score_map = {item['label']: item['score'] for item in results}
        # Extract probabilities
        pos = score_map.get('positive', 0.0)
        neg = score_map.get('negative', 0.0)
        neu = score_map.get('neutral', 0.0)

        # Polarity score: P(positive) - P(negative)
        sentiment_score = pos - neg
        # Confidence: max of the three probabilities
        confidence = max(pos, neg, neu)

        catalyst_type = self._categorize_catalyst(headline)
        rationale = f"{catalyst_type.replace('_', ' ').title()} detected with {confidence:.1%} confidence."

        return {
            "ticker": ticker,
            "sentiment_score": round(sentiment_score, 4),
            "confidence": round(confidence, 4),
            "catalyst_type": catalyst_type,
            "rationale": rationale
        }


if __name__ == "__main__":
        # Smoke test
        engine = InbuiltSentimentEngine()
        test_headline = "Apple reports record Q3 revenue, beating EPS estimates."
        result = engine.analyze(test_headline, "AAPL")
        print(result)