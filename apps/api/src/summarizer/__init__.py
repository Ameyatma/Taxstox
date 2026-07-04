"""AI Summarizer — uses DeepSeek API to process raw government notifications.

DeepSeek API is OpenAI-compatible, so we use the `openai` Python SDK pointed
at DeepSeek's endpoint (https://api.deepseek.com/v1).
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

from openai import OpenAI

from src.providers import RawUpdate

logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"

# Maximum raw content chars to send for summarization
MAX_CONTENT_CHARS = 3000


@dataclass
class ProcessedUpdate:
    """An AI-processed tax update ready for storage."""

    title: str
    summary_short: str
    what_changed: str
    who_affected: str
    action_required: str
    category: str  # Budget | ITR | TDS | GST | CBDT | Compliance
    effective_date: str
    published_date: str
    source: str
    source_url: str
    raw_content: str


SUMMARIZATION_PROMPT = """You are a tax expert analyzing an official Government of India notification.
Extract and summarize the following notification in a structured JSON format.

Rules:
- Never fabricate information. If a field is not mentioned in the notification, use an empty string.
- Keep summary_short to 2-3 concise sentences.
- what_changed should describe what rule/policy/procedure changed.
- who_affected should describe which taxpayers are impacted.
- action_required should describe what taxpayers must do (if anything).
- Category must be one of: Budget, ITR, TDS, GST, CBDT, Compliance.
- effective_date should be in YYYY-MM-DD format if mentioned, otherwise empty string.

Respond with ONLY a JSON object, no other text:

{
  "summary_short": "...",
  "what_changed": "...",
  "who_affected": "...",
  "action_required": "...",
  "category": "Compliance",
  "effective_date": ""
}

Notification title: {title}

Notification content:
{content}"""


def _get_client() -> OpenAI | None:
    """Get a configured DeepSeek client, or None if no API key."""
    if not DEEPSEEK_API_KEY:
        logger.warning("DEEPSEEK_API_KEY not set — AI summarization disabled")
        return None
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


def _extract_json(text: str) -> dict:
    """Extract JSON object from LLM response, handling markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        # Remove markdown code fences
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    return json.loads(text)


def summarize_update(update: RawUpdate) -> ProcessedUpdate:
    """Summarize a single raw update using DeepSeek AI.

    Falls back gracefully: if AI is unavailable, returns a basic
    ProcessedUpdate with the original title as summary.
    """
    client = _get_client()

    if client is None:
        return ProcessedUpdate(
            title=update.title,
            summary_short=update.title,
            what_changed="",
            who_affected="",
            action_required="",
            category="Compliance",
            effective_date="",
            published_date=update.published_date,
            source=update.source,
            source_url=update.url,
            raw_content=update.raw_content,
        )

    content = update.raw_content[:MAX_CONTENT_CHARS]
    prompt = SUMMARIZATION_PROMPT.format(title=update.title, content=content)

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise tax analyst. Respond with only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,  # Low temperature for factual accuracy
            max_tokens=500,
        )

        raw_output = response.choices[0].message.content or "{}"
        data = _extract_json(raw_output)

        return ProcessedUpdate(
            title=update.title,
            summary_short=data.get("summary_short", update.title),
            what_changed=data.get("what_changed", ""),
            who_affected=data.get("who_affected", ""),
            action_required=data.get("action_required", ""),
            category=data.get("category", "Compliance"),
            effective_date=data.get("effective_date", ""),
            published_date=update.published_date,
            source=update.source,
            source_url=update.url,
            raw_content=update.raw_content,
        )

    except Exception as e:
        logger.warning("AI summarization failed for '%s': %s", update.title[:60], e)
        # Graceful fallback
        return ProcessedUpdate(
            title=update.title,
            summary_short=update.title,
            what_changed="",
            who_affected="",
            action_required="",
            category="Compliance",
            effective_date="",
            published_date=update.published_date,
            source=update.source,
            source_url=update.url,
            raw_content=update.raw_content,
        )


def summarize_batch(updates: list[RawUpdate]) -> list[ProcessedUpdate]:
    """Summarize a batch of raw updates. Each is processed individually for reliability."""
    processed: list[ProcessedUpdate] = []
    for i, update in enumerate(updates):
        logger.info("Summarizing %d/%d: %s...", i + 1, len(updates), update.title[:60])
        result = summarize_update(update)
        processed.append(result)
    return processed
