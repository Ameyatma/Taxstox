"""Shared decimal conversion utility.

PR3: Single source of truth for parsing monetary strings into ``Decimal``.
Consolidates the three previously-duplicated ``_to_decimal`` helpers from the
AIS, Form 16, and Form 26AS parsers. Preserves the union of their edge-case
behaviors: ``None``/empty → ``Decimal("0")``, comma + space stripping, and a
graceful fallback (never raises) on malformed input.
"""

from decimal import Decimal
from typing import Optional


def to_decimal(value_str: Optional[str]) -> Decimal:
    """Convert a numeric string like ``'1,23,456.78'`` to ``Decimal``.

    Edge cases (preserved from the original parser helpers):
      - ``None`` / ``""`` / whitespace → ``Decimal("0")``
      - Commas and spaces are stripped before parsing
      - Malformed input → ``Decimal("0")`` (never raises)
    """
    if not value_str:
        return Decimal("0")
    cleaned = value_str.replace(",", "").replace(" ", "").strip()
    try:
        return Decimal(cleaned)
    except Exception:
        return Decimal("0")
