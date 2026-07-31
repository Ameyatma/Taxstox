"""Notification domain — Entities and value objects for multi-channel notifications.

Traceability: C18.1 (Notification Engine — 0%→60%, P6),
             C18.3 (Filing Status Updates — 0%→60%, P6),
             C18.4 (In-App Communication — 0%→40%, P6)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass(frozen=True)
class NotificationTemplate:
    """A reusable notification template. Value object."""

    template_id: str
    channel: NotificationChannel
    subject_template: str              # "Your ITR for {financial_year} has been filed"
    body_template: str                 # "Dear {name}, your ITR for {financial_year}..."
    priority: NotificationPriority = NotificationPriority.NORMAL


@dataclass
class Notification:
    """A notification instance ready for delivery. Entity."""

    notification_id: UUID
    recipient_user_id: UUID
    tenant_id: UUID | None
    channel: NotificationChannel
    subject: str
    body: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    status: str = "pending"            # pending, sent, failed, read
    template_id: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: str = ""
    sent_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def mark_sent(self) -> None:
        self.status = "sent"
        self.sent_at = datetime.now(timezone.utc).isoformat()

    def mark_failed(self) -> None:
        self.status = "failed"

    @staticmethod
    def create(
        recipient_user_id: UUID, channel: NotificationChannel,
        subject: str, body: str, tenant_id: UUID | None = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        template_id: str = "",
    ) -> Notification:
        return Notification(
            notification_id=uuid4(), recipient_user_id=recipient_user_id,
            tenant_id=tenant_id, channel=channel, subject=subject, body=body,
            priority=priority, template_id=template_id,
        )

    @staticmethod
    def from_template(
        template: NotificationTemplate, recipient_user_id: UUID,
        variables: dict[str, str], tenant_id: UUID | None = None,
    ) -> Notification:
        """Create a notification by rendering a template with variables."""
        subject = template.subject_template
        body = template.body_template
        for key, val in variables.items():
            subject = subject.replace(f"{{{key}}}", str(val))
            body = body.replace(f"{{{key}}}", str(val))
        return Notification.create(
            recipient_user_id=recipient_user_id, channel=template.channel,
            subject=subject, body=body, tenant_id=tenant_id,
            priority=template.priority, template_id=template.template_id,
        )


@dataclass
class NotificationPreference:
    """Per-user notification preferences. Entity."""

    user_id: UUID
    email_enabled: bool = True
    sms_enabled: bool = True
    in_app_enabled: bool = True
    push_enabled: bool = False
    deadline_reminders: bool = True
    filing_status_updates: bool = True
    marketing: bool = False
    quiet_hours_start: str = ""        # "22:00"
    quiet_hours_end: str = ""          # "07:00"

    def channel_enabled(self, channel: NotificationChannel) -> bool:
        mapping = {
            NotificationChannel.EMAIL: self.email_enabled,
            NotificationChannel.SMS: self.sms_enabled,
            NotificationChannel.IN_APP: self.in_app_enabled,
            NotificationChannel.PUSH: self.push_enabled,
        }
        return mapping.get(channel, False)

    @staticmethod
    def default(user_id: UUID) -> NotificationPreference:
        return NotificationPreference(user_id=user_id)


# ── Standard Templates ────────────────────────────────────────────────

STANDARD_TEMPLATES = {
    "filing_completed": NotificationTemplate(
        template_id="filing_completed", channel=NotificationChannel.EMAIL,
        subject_template="Your ITR for {financial_year} has been filed successfully",
        body_template=(
            "Dear {name},\n\n"
            "Your Income Tax Return for {financial_year} has been successfully filed.\n"
            "Acknowledgement Number: {ack_number}\n"
            "Date of Filing: {filing_date}\n\n"
            "Next Steps:\n"
            "- Verify your ITR within 30 days on the ITD portal\n"
            "- Track your refund status at https://taxstox.com/dashboard\n\n"
            "Powered by TaxStox"
        ),
        priority=NotificationPriority.HIGH,
    ),
    "deadline_reminder": NotificationTemplate(
        template_id="deadline_reminder", channel=NotificationChannel.EMAIL,
        subject_template="Reminder: ITR filing deadline in {days_remaining} days",
        body_template=(
            "Dear {name},\n\n"
            "The ITR filing deadline for {financial_year} is {deadline_date} "
            "({days_remaining} days remaining).\n\n"
            "Please upload your Form 16 and AIS to complete your filing.\n"
            "Start now: https://taxstox.com/upload\n\n"
            "Powered by TaxStox"
        ),
        priority=NotificationPriority.HIGH,
    ),
    "filing_status_changed": NotificationTemplate(
        template_id="filing_status_changed", channel=NotificationChannel.IN_APP,
        subject_template="Filing Status Updated",
        body_template=(
            "Your filing status has changed to: {new_status}.\n"
            "ITR Type: {itr_type}\n"
            "Updated by: {updated_by}"
        ),
        priority=NotificationPriority.NORMAL,
    ),
    "refund_credited": NotificationTemplate(
        template_id="refund_credited", channel=NotificationChannel.EMAIL,
        subject_template="Refund of ₹{refund_amount} credited for {financial_year}",
        body_template=(
            "Dear {name},\n\n"
            "Your income tax refund of ₹{refund_amount} for {financial_year} "
            "has been credited to your bank account.\n\n"
            "Refund Reference: {refund_reference}\n"
            "Date Credited: {credit_date}\n\n"
            "Powered by TaxStox"
        ),
        priority=NotificationPriority.HIGH,
    ),
}
