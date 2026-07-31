"""Notification Infrastructure — Email and SMS delivery adapters.

Infrastructure layer. Framework-aware.
"""

from src.infrastructure.notifications.email_adapter import EmailAdapter
from src.infrastructure.notifications.sms_adapter import SMSAdapter

__all__ = ["EmailAdapter", "SMSAdapter"]
