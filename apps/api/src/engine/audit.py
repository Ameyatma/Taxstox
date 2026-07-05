"""Immutable Audit Trail — complete, replayable, FY-aware computation records.

Every significant domain event is captured as an immutable AuditEvent.
The AuditTrail enables: computation replay, explanation generation,
CA review, and regulatory compliance.

Traceability: C10.1 (Computation Audit Trail — 0%→60%),
             Constitution I3 (Complete Audit Trail invariant)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Optional


class AuditEventType(str, Enum):
    """Types of auditable domain events."""

    # Document Processing
    DOCUMENT_INGESTED = "document.ingested"
    FIELD_EXTRACTED = "field.extracted"

    # Income
    INCOME_COMPUTED = "income.computed"
    DEDUCTION_APPLIED = "deduction.applied"

    # Tax Computation
    RULE_EVALUATED = "rule.evaluated"
    SLAB_APPLIED = "slab.applied"
    REBATE_APPLIED = "rebate.applied"
    SURCHARGE_APPLIED = "surcharge.applied"
    CESS_APPLIED = "cess.applied"
    TAX_FINALIZED = "tax.finalized"

    # Regime
    REGIME_COMPARED = "regime.compared"

    # Validation
    VALIDATION_RUN = "validation.run"

    # Filing
    ITR_GENERATED = "itr.generated"


@dataclass(frozen=True)
class AuditEvent:
    """A single immutable audit record.

    Every significant domain action produces one AuditEvent.
    Together they form a complete, replayable computation history.
    """

    event_id: str
    event_type: AuditEventType
    timestamp: str                          # ISO 8601
    correlation_id: str                     # Ties events of one computation together
    financial_year: str                     # e.g., "FY2025-26"
    bounded_context: str                    # e.g., "tax_computation", "income"
    capability_id: str                      # e.g., "C6.1", "C4.1"

    # What happened
    description: str                        # Human-readable
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)

    # Rule metadata
    rule_reference: str = ""                # e.g., "Section 115BAC", "RuleRepository FY2025-26"
    rule_version: str = ""

    # Traceability
    source_document: str = ""               # e.g., "Form16_PartB", "AIS_SFT18"
    source_field: str = ""                  # e.g., "salary_171", "equity_mf_sales[0].consideration"

    @staticmethod
    def create(
        event_type: AuditEventType,
        correlation_id: str,
        financial_year: str,
        bounded_context: str,
        capability_id: str,
        description: str,
        input_data: dict | None = None,
        output_data: dict | None = None,
        rule_reference: str = "",
        source_document: str = "",
        source_field: str = "",
    ) -> AuditEvent:
        return AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            correlation_id=correlation_id,
            financial_year=financial_year,
            bounded_context=bounded_context,
            capability_id=capability_id,
            description=description,
            input_data=input_data or {},
            output_data=output_data or {},
            rule_reference=rule_reference,
            rule_version="",
            source_document=source_document,
            source_field=source_field,
        )


@dataclass(frozen=True)
class AuditTrail:
    """Immutable collection of audit events for one computation.

    Append-only. Replayable. The single source of truth for
    "how was this tax computed?"
    """

    correlation_id: str
    financial_year: str
    events: tuple[AuditEvent, ...] = ()

    def append(self, event: AuditEvent) -> AuditTrail:
        """Return a NEW AuditTrail with the event appended (immutable)."""
        return AuditTrail(
            correlation_id=self.correlation_id,
            financial_year=self.financial_year,
            events=self.events + (event,),
        )

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def timeline(self) -> list[dict]:
        """Chronological timeline of events."""
        return [
            {
                "sequence": i + 1,
                "event_type": e.event_type.value,
                "timestamp": e.timestamp,
                "description": e.description,
                "bounded_context": e.bounded_context,
                "capability_id": e.capability_id,
            }
            for i, e in enumerate(self.events)
        ]

    def events_by_type(self, event_type: AuditEventType) -> tuple[AuditEvent, ...]:
        """Filter events by type."""
        return tuple(e for e in self.events if e.event_type == event_type)

    def events_by_context(self, bounded_context: str) -> tuple[AuditEvent, ...]:
        """Filter events by bounded context."""
        return tuple(e for e in self.events if e.bounded_context == bounded_context)

    def to_replay_script(self) -> str:
        """Generate a human-readable replay of the computation."""
        lines = [
            f"Computation Audit Trail — {self.financial_year}",
            f"Correlation ID: {self.correlation_id}",
            f"Total Events: {self.event_count}",
            "",
        ]
        for i, e in enumerate(self.events, 1):
            lines.append(f"{i}. [{e.event_type.value}] {e.description}")
            if e.rule_reference:
                lines.append(f"   Rule: {e.rule_reference}")
            if e.source_document:
                lines.append(f"   Source: {e.source_document} > {e.source_field}")
            lines.append("")
        return "\n".join(lines)


class AuditContext:
    """Factory for creating correlated audit events within one computation.

    Usage:
        ctx = AuditContext("FY2025-26")
        trail = AuditTrail(ctx.correlation_id, ctx.financial_year)
        trail = trail.append(ctx.event(
            AuditEventType.RULE_EVALUATED, "tax_computation", "C6.1",
            "Applied slab rate: 5% on ₹4,00,000",
            input_data={"income": "925000"},
            output_data={"slab_tax": "32500"},
            rule_reference="Section 115BAC",
        ))
    """

    def __init__(self, financial_year: str) -> None:
        self.correlation_id = str(uuid.uuid4())
        self.financial_year = financial_year

    def event(
        self,
        event_type: AuditEventType,
        bounded_context: str,
        capability_id: str,
        description: str,
        input_data: dict | None = None,
        output_data: dict | None = None,
        rule_reference: str = "",
        source_document: str = "",
        source_field: str = "",
    ) -> AuditEvent:
        return AuditEvent.create(
            event_type=event_type,
            correlation_id=self.correlation_id,
            financial_year=self.financial_year,
            bounded_context=bounded_context,
            capability_id=capability_id,
            description=description,
            input_data=input_data,
            output_data=output_data,
            rule_reference=rule_reference,
            source_document=source_document,
            source_field=source_field,
        )
