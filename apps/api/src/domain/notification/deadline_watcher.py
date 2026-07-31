"""Deadline Watcher — Configurable deadline reminders and schedules.

CA firms can configure when and how clients get reminded about
upcoming filing deadlines.

Traceability: C18.2 (Deadline Reminders — 0%→60%, P6)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class DeadlineType(str, Enum):
    ITR_FILING = "itr_filing"             # July 31
    TDS_RETURN = "tds_return"             # Quarterly
    AUDIT_REPORT = "audit_report"         # September 30
    BELATED_RETURN = "belated_return"     # December 31
    REVISED_RETURN = "revised_return"     # December 31
    ADVANCE_TAX = "advance_tax"           # Quarterly installments


@dataclass(frozen=True)
class ReminderSchedule:
    """When to send reminders before a deadline. Value object."""

    days_before: tuple[int, ...]          # e.g., (30, 14, 7, 3, 1)
    channels: tuple[str, ...]             # e.g., ("email", "sms")
    include_on_due_date: bool = True

    @staticmethod
    def default_itr() -> ReminderSchedule:
        return ReminderSchedule(
            days_before=(30, 14, 7, 3, 1),
            channels=("email",),
            include_on_due_date=True,
        )

    @staticmethod
    def aggressive() -> ReminderSchedule:
        return ReminderSchedule(
            days_before=(30, 21, 14, 7, 5, 3, 2, 1),
            channels=("email", "sms"),
            include_on_due_date=True,
        )


@dataclass
class DeadlineRule:
    """A deadline reminder rule configured per tenant. Entity."""

    rule_id: UUID
    tenant_id: UUID
    deadline_type: DeadlineType
    financial_year: str = ""
    schedule: ReminderSchedule = field(default_factory=ReminderSchedule.default_itr)
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def should_remind_today(self, deadline_date: date) -> bool:
        """Check if a reminder should be sent today."""
        today = date.today()
        days_left = (deadline_date - today).days
        if days_left < 0:
            return False  # Past deadline
        if days_left == 0:
            return self.schedule.include_on_due_date
        return days_left in self.schedule.days_before

    def get_reminder_dates(self, deadline_date: date) -> list[date]:
        """Get all dates when reminders should be sent."""
        dates = []
        for days in sorted(self.schedule.days_before, reverse=True):
            d = deadline_date
            from datetime import timedelta
            reminder_date = d - timedelta(days=days)
            dates.append(reminder_date)
        if self.schedule.include_on_due_date:
            dates.append(deadline_date)
        return dates

    @staticmethod
    def create_itr_reminder(
        tenant_id: UUID, financial_year: str = "FY2025-26",
        schedule: ReminderSchedule | None = None,
    ) -> DeadlineRule:
        return DeadlineRule(
            rule_id=uuid4(), tenant_id=tenant_id,
            deadline_type=DeadlineType.ITR_FILING,
            financial_year=financial_year,
            schedule=schedule or ReminderSchedule.default_itr(),
        )


# ── Standard Deadline Dates ───────────────────────────────────────────

def get_standard_deadline(deadline_type: DeadlineType, financial_year: str = "FY2025-26") -> date:
    """Get the standard deadline date for a given type and FY."""
    year_map = {
        "FY2025-26": 2026,
        "FY2024-25": 2025,
        "FY2023-24": 2024,
    }
    year = year_map.get(financial_year, 2026)

    deadlines = {
        DeadlineType.ITR_FILING: date(year, 7, 31),
        DeadlineType.AUDIT_REPORT: date(year, 9, 30),
        DeadlineType.BELATED_RETURN: date(year, 12, 31),
        DeadlineType.REVISED_RETURN: date(year, 12, 31),
        DeadlineType.TDS_RETURN: date(year, 7, 31),  # Q1
        DeadlineType.ADVANCE_TAX: date(year, 3, 15),  # Last installment
    }
    return deadlines.get(deadline_type, date(year, 7, 31))
