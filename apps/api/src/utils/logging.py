"""Structured JSON logging with PII masking for TaxStox backend.

Replaces unstructured f-string logging with JSON-formatted structured logs.
All PII (PAN, Aadhaar, passwords, mobile, email) is automatically masked.

Usage:
    from src.utils.logging import get_logger
    logger = get_logger(__name__)
    logger.info("Tax computed", extra={"taxpayer_id": "...", "tax": "..."})
"""

from __future__ import annotations

import logging
import re
import sys
from typing import Any


# ── PII Masking ───────────────────────────────────────────────────────

def mask_pan(pan: str) -> str:
    """Mask PAN: ABCDE1234F → ABC**1234F."""
    if not pan or len(pan) < 10:
        return "***"
    return f"{pan[:3]}**{pan[5:]}"


def mask_aadhaar(aadhaar: str) -> str:
    """Mask Aadhaar: 123456789012 → ******789012."""
    if not aadhaar or len(aadhaar) < 12:
        return "***"
    return f"******{aadhaar[6:]}"


def mask_mobile(mobile: str) -> str:
    """Mask mobile: 9876543210 → 98****3210."""
    if not mobile or len(mobile) < 10:
        return "***"
    return f"{mobile[:2]}****{mobile[6:]}"


def mask_email(email: str) -> str:
    """Mask email: user@example.com → u***r@example.com."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"***@{domain}"
    return f"{local[0]}***{local[-1]}@{domain}"


PII_MASKERS: dict[str, Any] = {
    "pan": mask_pan,
    "aadhaar": mask_aadhaar,
    "mobile": mask_mobile,
    "email": mask_email,
    "password": lambda _: "***",
    "pwd": lambda _: "***",
}

PII_KEY_PATTERNS = re.compile(
    r"(pan|aadhaar|mobile|email|password|pwd|secret|token)",
    re.IGNORECASE,
)


def mask_pii_in_extra(extra: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask PII in logging extra dict."""
    if not extra:
        return extra
    masked: dict[str, Any] = {}
    for key, value in extra.items():
        if PII_KEY_PATTERNS.search(key) and isinstance(value, str):
            for pattern, masker in PII_MASKERS.items():
                if pattern in key.lower():
                    masked[key] = masker(value)
                    break
            else:
                masked[key] = "***"
        elif isinstance(value, dict):
            masked[key] = mask_pii_in_extra(value)
        else:
            masked[key] = value
    return masked


# ── Structured JSON Formatter ─────────────────────────────────────────

class JsonFormatter(logging.Formatter):
    """Emit logs as structured JSON with PII masking."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime, timezone

        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Correlation ID
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id

        # Extra fields (masked)
        if hasattr(record, "extra_fields") and record.extra_fields:
            log_entry["extra"] = mask_pii_in_extra(record.extra_fields)

        # Exception info
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, default=str)


# ── Logger Factory ────────────────────────────────────────────────────

_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with JSON formatter. Call once at startup."""
    global _configured
    if _configured:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger configured for structured JSON output."""
    if not _configured:
        setup_logging()
    return logging.getLogger(name)
