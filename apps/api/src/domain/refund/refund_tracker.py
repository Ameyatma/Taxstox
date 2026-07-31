"""Refund Tracker — ITR refund status with stage-by-stage timeline.

Traceability: C14.7 (Refund Tracker — 0%→50%, P6)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class RefundStage(str, Enum):
    ITR_FILED = "itr_filed"                    # Return submitted
    ITR_PROCESSED = "itr_processed"            # CPC processed
    REFUND_DETERMINED = "refund_determined"    # Refund amount computed
    REFUND_ISSUED = "refund_issued"            # Refund sent to bank
    REFUND_CREDITED = "refund_credited"        # In taxpayer's account
    REFUND_FAILED = "refund_failed"            # Bank validation failed
    UNDER_SCRUTINY = "under_scrutiny"          # Return picked for scrutiny
    ADJUSTED = "adjusted"                      # Refund adjusted against demand


@dataclass(frozen=True)
class RefundStatus:
    """Current refund status snapshot. Value object."""

    acknowledgement_number: str
    financial_year: str
    expected_refund: Decimal
    current_stage: RefundStage
    last_updated: str = ""
    refund_reference: str = ""                 # ITD refund reference number
    credited_amount: Decimal = Decimal("0")

    @property
    def is_complete(self) -> bool:
        return self.current_stage == RefundStage.REFUND_CREDITED

    @property
    def is_processing(self) -> bool:
        return self.current_stage in (
            RefundStage.ITR_FILED, RefundStage.ITR_PROCESSED,
            RefundStage.REFUND_DETERMINED, RefundStage.REFUND_ISSUED,
        )

    @property
    def progress_percent(self) -> float:
        """Progress through the refund pipeline (0-100)."""
        stage_order = [
            RefundStage.ITR_FILED, RefundStage.ITR_PROCESSED,
            RefundStage.REFUND_DETERMINED, RefundStage.REFUND_ISSUED,
            RefundStage.REFUND_CREDITED,
        ]
        try:
            idx = stage_order.index(self.current_stage)
            return (idx + 1) / len(stage_order) * 100
        except ValueError:
            return 0.0


@dataclass(frozen=True)
class TimelineEntry:
    """A single entry in the refund timeline. Value object."""

    stage: RefundStage
    date: str
    description: str
    reference: str = ""


@dataclass
class RefundTimeline:
    """Complete refund timeline for a filing. Entity."""

    timeline_id: UUID
    user_id: UUID
    financial_year: str
    acknowledgement_number: str
    expected_amount: Decimal
    entries: list[TimelineEntry] = field(default_factory=list)
    current_status: RefundStatus | None = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def add_entry(self, stage: RefundStage, date: str, description: str, reference: str = "") -> None:
        self.entries.append(TimelineEntry(stage=stage, date=date, description=description, reference=reference))

    def set_current_stage(self, stage: RefundStage) -> None:
        self.current_status = RefundStatus(
            acknowledgement_number=self.acknowledgement_number,
            financial_year=self.financial_year,
            expected_refund=self.expected_amount,
            current_stage=stage,
        )

    @property
    def last_updated(self) -> str:
        if self.entries:
            return self.entries[-1].date
        return self.created_at

    @property
    def estimated_days_to_credit(self) -> int | None:
        """Estimated days until refund is credited, based on current stage."""
        stage_days = {
            RefundStage.ITR_FILED: 45,
            RefundStage.ITR_PROCESSED: 21,
            RefundStage.REFUND_DETERMINED: 14,
            RefundStage.REFUND_ISSUED: 7,
            RefundStage.REFUND_CREDITED: 0,
        }
        if self.current_status:
            return stage_days.get(self.current_status.current_stage)
        return None

    @staticmethod
    def create(
        user_id: UUID, financial_year: str,
        acknowledgement_number: str, expected_amount: Decimal,
    ) -> RefundTimeline:
        return RefundTimeline(
            timeline_id=uuid4(), user_id=user_id,
            financial_year=financial_year,
            acknowledgement_number=acknowledgement_number,
            expected_amount=expected_amount,
        )
