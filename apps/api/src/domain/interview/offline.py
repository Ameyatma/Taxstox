"""Offline Interview — Serializable question pack for offline-capable tax interview.

Enables the interview to be conducted without server round-trips.
Question tree is serialized with embedded validation rules.
Responses are validated on reconnection.

Traceability: C13.8 (Offline Interview — 0%→40%, P4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional


class QuestionType(str, Enum):
    YES_NO = "yes_no"
    NUMBER = "number"
    TEXT = "text"
    DROPDOWN = "dropdown"


@dataclass(frozen=True)
class OfflineValidationRule:
    """A validation rule embedded in an offline question."""
    rule_id: str
    rule_type: str                     # "range", "regex", "required", "max_length"
    parameters: dict[str, Any] = field(default_factory=dict)
    error_message: str = ""


@dataclass(frozen=True)
class OfflineQuestion:
    """A single question in the offline interview pack."""

    question_id: str
    text: str
    question_type: QuestionType
    impact: str = ""
    order: int = 0
    depends_on: str = ""               # question_id this depends on
    depends_on_answer: str = ""        # answer required to show this question
    sub_questions: tuple[OfflineQuestion, ...] = ()
    validation_rules: tuple[OfflineValidationRule, ...] = ()
    default_value: str = ""
    help_text: str = ""
    provision_reference: str = ""


@dataclass(frozen=True)
class OfflineInterviewPack:
    """Complete serializable interview pack.

    Contains all questions, branching logic, and validation rules.
    Can be downloaded and executed client-side without network.
    """

    pack_id: str
    financial_year: str
    generated_at: str                  # ISO timestamp
    expires_at: str                    # ISO timestamp (pack is valid until)
    regime: str
    questions: tuple[OfflineQuestion, ...]
    total_questions: int = 0

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dict."""
        return {
            "pack_id": self.pack_id,
            "financial_year": self.financial_year,
            "generated_at": self.generated_at,
            "expires_at": self.expires_at,
            "regime": self.regime,
            "total_questions": self.total_questions,
            "questions": [self._question_to_dict(q) for q in self.questions],
        }

    def _question_to_dict(self, q: OfflineQuestion) -> dict:
        return {
            "question_id": q.question_id,
            "text": q.text,
            "type": q.question_type.value,
            "impact": q.impact,
            "order": q.order,
            "depends_on": q.depends_on,
            "depends_on_answer": q.depends_on_answer,
            "default_value": q.default_value,
            "help_text": q.help_text,
            "provision_reference": q.provision_reference,
            "validation": [
                {"rule": r.rule_type, "params": r.parameters, "error": r.error_message}
                for r in q.validation_rules
            ],
            "sub_questions": [self._question_to_dict(sq) for sq in q.sub_questions],
        }


@dataclass
class OfflineResponse:
    """A response collected offline, to be validated on reconnect."""

    pack_id: str
    question_id: str
    answer: str
    answered_at: str = ""              # ISO timestamp

    def validate(self, question: OfflineQuestion) -> dict[str, Any]:
        """Validate this response against the question's rules.

        Returns dict with 'valid' (bool) and 'errors' (list[str]).
        """
        errors: list[str] = []

        for rule in question.validation_rules:
            if rule.rule_type == "required":
                if not self.answer.strip():
                    errors.append(rule.error_message or "This field is required")
            elif rule.rule_type == "range":
                try:
                    val = float(self.answer)
                    lo = rule.parameters.get("min", float("-inf"))
                    hi = rule.parameters.get("max", float("inf"))
                    if val < lo or val > hi:
                        errors.append(rule.error_message or f"Value must be between {lo} and {hi}")
                except ValueError:
                    errors.append("Please enter a valid number")
            elif rule.rule_type == "regex":
                import re
                pattern = rule.parameters.get("pattern", "")
                if pattern and not re.match(pattern, self.answer):
                    errors.append(rule.error_message or "Invalid format")
            elif rule.rule_type == "max_length":
                max_len = rule.parameters.get("max", 255)
                if len(self.answer) > max_len:
                    errors.append(rule.error_message or f"Maximum {max_len} characters")

        return {"valid": len(errors) == 0, "errors": errors}


def pack_interview(
    financial_year: str,
    regime: str,
    questions: list[OfflineQuestion],
    pack_id: str = "",
    ttl_hours: int = 24,
) -> OfflineInterviewPack:
    """Create an offline interview pack from a list of questions.

    Args:
        financial_year: e.g., "FY2025-26"
        regime: "old" or "new"
        questions: Ordered list of OfflineQuestion objects
        pack_id: Optional pack ID (auto-generated if empty)
        ttl_hours: How long the pack is valid

    Returns:
        OfflineInterviewPack ready for serialization
    """
    import uuid

    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=ttl_hours)

    # Count total questions including sub-questions
    def count_questions(qs: tuple[OfflineQuestion, ...]) -> int:
        total = len(qs)
        for q in qs:
            total += count_questions(q.sub_questions)
        return total

    return OfflineInterviewPack(
        pack_id=pack_id or f"offline-{uuid.uuid4().hex[:12]}",
        financial_year=financial_year,
        generated_at=now.isoformat(),
        expires_at=expires.isoformat(),
        regime=regime,
        questions=tuple(questions),
        total_questions=count_questions(tuple(questions)),
    )
