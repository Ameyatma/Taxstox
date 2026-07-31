"""Refund Tracker Engine — Tracks ITR refund status with stage progression.

Engine layer. Manages refund timelines, estimate calculations, and
stage transitions.

Traceability: C14.7 (Refund Tracker — 0%→50%, P6)
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from src.domain.refund.refund_tracker import (
    RefundTimeline,
    RefundStatus,
    RefundStage,
    TimelineEntry,
)


class RefundTrackerEngine:
    """Manages refund tracking lifecycle.

    Engine. Tracks refund from ITR filing to bank credit.
    Provides estimated dates and status summaries.
    """

    @staticmethod
    def create_timeline(
        user_id: UUID, financial_year: str,
        acknowledgement_number: str, expected_refund: Decimal,
    ) -> RefundTimeline:
        """Create a new refund timeline when ITR is filed."""
        timeline = RefundTimeline.create(
            user_id=user_id, financial_year=financial_year,
            acknowledgement_number=acknowledgement_number,
            expected_amount=expected_refund,
        )
        timeline.set_current_stage(RefundStage.ITR_FILED)
        from datetime import date
        timeline.add_entry(
            RefundStage.ITR_FILED, date.today().isoformat(),
            "ITR filed successfully", acknowledgement_number,
        )
        return timeline

    @staticmethod
    def advance_stage(timeline: RefundTimeline, stage: RefundStage,
                      description: str = "", reference: str = "") -> None:
        """Advance refund to a new stage."""
        from datetime import date
        timeline.set_current_stage(stage)
        timeline.add_entry(stage, date.today().isoformat(), description, reference)

    @staticmethod
    def get_status_summary(timeline: RefundTimeline) -> dict:
        """Generate a status summary for API/UI display."""
        status = timeline.current_status
        if not status:
            return {"status": "unknown", "message": "No refund status available"}

        return {
            "acknowledgement_number": status.acknowledgement_number,
            "financial_year": status.financial_year,
            "expected_refund": str(status.expected_refund),
            "current_stage": status.current_stage.value,
            "stage_label": RefundTrackerEngine.stage_label(status.current_stage),
            "progress_percent": status.progress_percent,
            "is_complete": status.is_complete,
            "estimated_days": timeline.estimated_days_to_credit,
            "last_updated": timeline.last_updated,
            "timeline": [
                {"stage": e.stage.value, "date": e.date, "description": e.description}
                for e in timeline.entries
            ],
        }

    @staticmethod
    def stage_label(stage: RefundStage) -> str:
        labels = {
            RefundStage.ITR_FILED: "ITR Filed — Awaiting Processing",
            RefundStage.ITR_PROCESSED: "ITR Processed by CPC",
            RefundStage.REFUND_DETERMINED: "Refund Amount Determined",
            RefundStage.REFUND_ISSUED: "Refund Issued to Bank",
            RefundStage.REFUND_CREDITED: "Refund Credited to Account",
            RefundStage.REFUND_FAILED: "Refund Failed — Bank Validation",
            RefundStage.UNDER_SCRUTINY: "Under Scrutiny — May Delay Refund",
            RefundStage.ADJUSTED: "Refund Adjusted Against Demand",
        }
        return labels.get(stage, stage.value)
