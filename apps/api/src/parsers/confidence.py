"""Confidence scoring for document extraction — shared across all parsers.

Traceability: C3.3, C3.4 (confidence scoring), C3.5 (OCR quality assessment)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class ConfidenceLevel(str, Enum):
    """Confidence in an extracted field value."""
    HIGH = "HIGH"         # Extracted from structured data (JSON, well-formatted PDF)
    MEDIUM = "MEDIUM"     # Extracted by regex/OCR with good match
    LOW = "LOW"           # Extracted by OCR with poor match, or heuristics
    NONE = "NONE"         # Could not extract — user must provide


@dataclass
class ScoredField(Generic[T]):
    """A field value with extraction confidence.

    Usage:
        pan = ScoredField(value="ABCDE1234F", confidence=ConfidenceLevel.HIGH,
                          source="Form 16 Part A — regex match")
    """
    value: T
    confidence: ConfidenceLevel
    source: str = ""           # Which parser/extraction method produced this
    alternatives: list[T] = field(default_factory=list)  # Other candidates found

    @property
    def is_reliable(self) -> bool:
        """Field is reliable enough for auto-fill without user review."""
        return self.confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM)

    @property
    def needs_review(self) -> bool:
        """Field should be reviewed by user before accepting."""
        return self.confidence == ConfidenceLevel.LOW

    @property
    def is_missing(self) -> bool:
        """Field could not be extracted."""
        return self.confidence == ConfidenceLevel.NONE

    def __repr__(self) -> str:
        return f"ScoredField({self.value!r}, {self.confidence.value})"


def high(value: T, source: str = "") -> ScoredField[T]:
    """Factory for HIGH confidence field."""
    return ScoredField(value=value, confidence=ConfidenceLevel.HIGH, source=source)


def medium(value: T, source: str = "") -> ScoredField[T]:
    """Factory for MEDIUM confidence field."""
    return ScoredField(value=value, confidence=ConfidenceLevel.MEDIUM, source=source)


def low(value: T, source: str = "") -> ScoredField[T]:
    """Factory for LOW confidence field."""
    return ScoredField(value=value, confidence=ConfidenceLevel.LOW, source=source)


def missing() -> ScoredField[None]:
    """Factory for NONE confidence (could not extract)."""
    return ScoredField(value=None, confidence=ConfidenceLevel.NONE, source="")


@dataclass
class DocumentExtractionReport:
    """Overall extraction quality report for a parsed document.

    Summarizes how much was extracted and at what confidence level,
    so the UI can decide: auto-fill, highlight for review, or ask user.
    """
    document_type: str = ""               # "form16", "ais", "form26as"
    total_fields: int = 0
    fields_high: int = 0
    fields_medium: int = 0
    fields_low: int = 0
    fields_missing: int = 0

    @property
    def extraction_rate(self) -> float:
        """Percentage of fields extracted (HIGH + MEDIUM + LOW) / total."""
        if self.total_fields == 0:
            return 0.0
        extracted = self.fields_high + self.fields_medium + self.fields_low
        return extracted / self.total_fields

    @property
    def auto_fill_rate(self) -> float:
        """Percentage of fields reliable enough for auto-fill (HIGH + MEDIUM)."""
        if self.total_fields == 0:
            return 0.0
        return (self.fields_high + self.fields_medium) / self.total_fields

    @property
    def is_reliable(self) -> bool:
        """Document extraction is reliable enough for fully automated processing."""
        return self.auto_fill_rate >= 0.90 and self.fields_missing == 0

    def to_dict(self) -> dict:
        return {
            "document_type": self.document_type,
            "total_fields": self.total_fields,
            "fields_high": self.fields_high,
            "fields_medium": self.fields_medium,
            "fields_low": self.fields_low,
            "fields_missing": self.fields_missing,
            "extraction_rate": round(self.extraction_rate, 2),
            "auto_fill_rate": round(self.auto_fill_rate, 2),
            "is_reliable": self.is_reliable,
        }
