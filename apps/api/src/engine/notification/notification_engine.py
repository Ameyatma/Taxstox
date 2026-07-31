"""Notification Engine — Dispatches notifications, evaluates deadlines.

Engine layer. Coordinates Notification domain with infrastructure adapters.
No framework imports.

Traceability: C18.1 (Notification Engine), C18.2 (Deadline Reminders),
             C18.3 (Filing Status Updates)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from uuid import UUID

from src.domain.notification.notification import (
    Notification,
    NotificationChannel,
    NotificationTemplate,
    NotificationPriority,
    NotificationPreference,
    STANDARD_TEMPLATES,
)
from src.domain.notification.deadline_watcher import (
    DeadlineRule,
    ReminderSchedule,
    DeadlineType,
    get_standard_deadline,
)


@dataclass
class NotificationBatch:
    """Result of a notification dispatch batch."""
    total: int = 0
    sent: int = 0
    failed: int = 0
    notifications: list[Notification] = field(default_factory=list)


class NotificationEngine:
    """Dispatches notifications across channels.

    Engine. Respects user preferences (opt-outs, quiet hours).
    Uses infrastructure adapters for actual delivery.
    """

    def __init__(self) -> None:
        self._email_sender = None
        self._sms_sender = None
        self._in_app_store: list[Notification] = []

    # ── Lifecycle ────────────────────────────────────────────────────

    def send(self, notification: Notification) -> bool:
        """Send a notification through its configured channel."""
        if notification.channel == NotificationChannel.IN_APP:
            self._in_app_store.append(notification)
            notification.mark_sent()
            return True
        elif notification.channel == NotificationChannel.EMAIL:
            return self._send_email(notification)
        elif notification.channel == NotificationChannel.SMS:
            return self._send_sms(notification)
        return False

    def send_batch(self, notifications: list[Notification]) -> NotificationBatch:
        """Send a batch of notifications. Returns results."""
        batch = NotificationBatch(total=len(notifications))
        for n in notifications:
            if self.send(n):
                batch.sent += 1
                batch.notifications.append(n)
            else:
                batch.failed += 1
        return batch

    def should_send(self, notification: Notification, preferences: NotificationPreference) -> bool:
        """Check if notification should be sent based on user preferences."""
        if not preferences.channel_enabled(notification.channel):
            return False
        # Quiet hours check
        if preferences.quiet_hours_start and preferences.quiet_hours_end:
            now = datetime.now(timezone.utc)
            hour = now.hour
            start_h = int(preferences.quiet_hours_start.split(":")[0])
            end_h = int(preferences.quiet_hours_end.split(":")[0])
            if start_h > end_h:  # Overnight quiet hours
                if hour >= start_h or hour < end_h:
                    return False
            else:
                if start_h <= hour < end_h:
                    return False
        return True

    # ── Template-based Methods ──────────────────────────────────────

    def notify_filing_completed(
        self, user_id: UUID, name: str, financial_year: str,
        ack_number: str, filing_date: str,
    ) -> Notification | None:
        """Send filing completed notification."""
        template = STANDARD_TEMPLATES["filing_completed"]
        notification = Notification.from_template(template, user_id, {
            "name": name, "financial_year": financial_year,
            "ack_number": ack_number, "filing_date": filing_date,
        })
        self.send(notification)
        return notification

    def notify_status_changed(
        self, user_id: UUID, new_status: str, itr_type: str,
        updated_by: str = "System",
    ) -> Notification:
        """Send filing status change notification."""
        template = STANDARD_TEMPLATES["filing_status_changed"]
        notification = Notification.from_template(template, user_id, {
            "new_status": new_status, "itr_type": itr_type,
            "updated_by": updated_by,
        })
        self._in_app_store.append(notification)
        notification.mark_sent()
        return notification

    def notify_refund_credited(
        self, user_id: UUID, name: str, financial_year: str,
        refund_amount: str, refund_reference: str, credit_date: str,
    ) -> Notification | None:
        """Send refund credited notification."""
        template = STANDARD_TEMPLATES["refund_credited"]
        notification = Notification.from_template(template, user_id, {
            "name": name, "financial_year": financial_year,
            "refund_amount": refund_amount, "refund_reference": refund_reference,
            "credit_date": credit_date,
        })
        self.send(notification)
        return notification

    # ── In-App Notifications ─────────────────────────────────────────

    def get_in_app_notifications(self, user_id: UUID, limit: int = 20) -> list[Notification]:
        """Get in-app notifications for a user."""
        user_notifications = [
            n for n in self._in_app_store
            if n.recipient_user_id == user_id
        ]
        return sorted(user_notifications, key=lambda n: n.created_at, reverse=True)[:limit]

    def get_unread_count(self, user_id: UUID) -> int:
        """Count unread in-app notifications."""
        return sum(
            1 for n in self._in_app_store
            if n.recipient_user_id == user_id and n.status == "sent"
        )

    # ── Private Delivery ─────────────────────────────────────────────

    def _send_email(self, notification: Notification) -> bool:
        """Send via email adapter."""
        from src.infrastructure.notifications.email_adapter import EmailAdapter
        return EmailAdapter.send(notification)

    def _send_sms(self, notification: Notification) -> bool:
        """Send via SMS adapter."""
        from src.infrastructure.notifications.sms_adapter import SMSAdapter
        return SMSAdapter.send(notification)


class DeadlineReminderEngine:
    """Evaluates deadline rules and generates reminders.

    Engine. For each active DeadlineRule, checks if today is a
    reminder day and generates Notification instances.
    """

    def __init__(self, notification_engine: NotificationEngine | None = None) -> None:
        self._engine = notification_engine or NotificationEngine()

    def evaluate(
        self, rules: list[DeadlineRule], now: date | None = None,
    ) -> list[Notification]:
        """Evaluate all rules and generate reminders for today."""
        today = now or date.today()
        reminders: list[Notification] = []

        for rule in rules:
            if not rule.is_active:
                continue
            deadline = get_standard_deadline(rule.deadline_type, rule.financial_year)
            if rule.should_remind_today(deadline):
                days_left = (deadline - today).days
                template = STANDARD_TEMPLATES["deadline_reminder"]
                notification = Notification.from_template(
                    template, UUID("00000000-0000-0000-0000-000000000000"), {
                        "name": "Taxpayer",
                        "financial_year": rule.financial_year,
                        "deadline_date": deadline.isoformat(),
                        "days_remaining": str(days_left),
                    },
                    tenant_id=rule.tenant_id,
                )
                reminders.append(notification)

        return reminders

    def generate_reminders_for_client(
        self, user_id: UUID, name: str, financial_year: str,
        deadline_type: DeadlineType = DeadlineType.ITR_FILING,
        schedule: ReminderSchedule | None = None,
    ) -> list[Notification]:
        """Generate all reminder notifications for a single client."""
        schedule = schedule or ReminderSchedule.default_itr()
        deadline = get_standard_deadline(deadline_type, financial_year)
        reminder_dates = DeadlineRule.create_itr_reminder(
            UUID("00000000-0000-0000-0000-000000000000"),
            financial_year, schedule,
        ).get_reminder_dates(deadline)

        notifications: list[Notification] = []
        for _ in reminder_dates:
            template = STANDARD_TEMPLATES["deadline_reminder"]
            days_left = (deadline - date.today()).days
            if days_left >= 0:
                n = Notification.from_template(template, user_id, {
                    "name": name, "financial_year": financial_year,
                    "deadline_date": deadline.isoformat(),
                    "days_remaining": str(days_left),
                })
                notifications.append(n)

        return notifications
