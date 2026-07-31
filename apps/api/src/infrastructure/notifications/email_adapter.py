"""Email Adapter — SMTP / provider-based email delivery.

Infrastructure layer. Production: configure SMTP or SendGrid/Mailgun.
Current: stub that logs — ready for SMTP wiring.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class EmailAdapter:
    """Sends email notifications.

    Production: Wire to SMTP (smtplib), SendGrid API, or AWS SES.
    Current: Development stub with structured logging.
    """

    @staticmethod
    def send(notification) -> bool:
        """Send an email notification.

        Returns True on success, False on failure.
        """
        try:
            logger.info(
                "EMAIL SENT",
                extra={
                    "to_user": str(notification.recipient_user_id),
                    "subject": notification.subject,
                    "priority": notification.priority.value,
                    "template": notification.template_id or "none",
                },
            )
            notification.mark_sent()
            return True
        except Exception:
            logger.error(
                "EMAIL FAILED",
                extra={"to_user": str(notification.recipient_user_id)},
                exc_info=True,
            )
            notification.mark_failed()
            return False

    @staticmethod
    def send_raw(to_email: str, subject: str, body: str) -> bool:
        """Send a raw email without a Notification entity.

        Production: Use smtplib.SMTP or provider API.
        """
        try:
            logger.info("RAW EMAIL SENT", extra={"to": to_email, "subject": subject})
            return True
        except Exception:
            logger.error("RAW EMAIL FAILED", extra={"to": to_email}, exc_info=True)
            return False
