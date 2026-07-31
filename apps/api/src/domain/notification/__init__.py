"""Notification bounded context — Email, SMS, and in-app notifications.

Domain layer. Zero framework imports. Pure Python.

Traceability: C18.1 (Notification Engine), C18.2 (Deadline Reminders),
             C18.3 (Filing Status Updates), C18.4 (In-App Communication)
"""

from src.domain.notification.notification import (
    Notification,
    NotificationChannel,
    NotificationTemplate,
    NotificationPreference,
)
from src.domain.notification.deadline_watcher import (
    DeadlineRule,
    ReminderSchedule,
    DeadlineType,
)

__all__ = [
    "Notification",
    "NotificationChannel",
    "NotificationTemplate",
    "NotificationPreference",
    "DeadlineRule",
    "ReminderSchedule",
    "DeadlineType",
]
