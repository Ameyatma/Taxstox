"""SMS Adapter — SMS gateway integration for text message delivery.

Infrastructure layer. Production: configure Twilio, MSG91, or AWS SNS.
Current: stub that logs — ready for gateway wiring.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class SMSAdapter:
    """Sends SMS notifications.

    Production: Wire to Twilio API, MSG91, or AWS SNS.
    Current: Development stub with structured logging.
    """

    @staticmethod
    def send(notification) -> bool:
        """Send an SMS notification.

        Production: Call SMS gateway API.
        Returns True on success.
        """
        try:
            # Truncate body for SMS (160 char limit)
            body = notification.body[:160]
            logger.info(
                "SMS SENT",
                extra={
                    "to_user": str(notification.recipient_user_id),
                    "body_length": len(body),
                    "priority": notification.priority.value,
                },
            )
            notification.mark_sent()
            return True
        except Exception:
            logger.error(
                "SMS FAILED",
                extra={"to_user": str(notification.recipient_user_id)},
                exc_info=True,
            )
            notification.mark_failed()
            return False

    @staticmethod
    def send_raw(to_mobile: str, message: str) -> bool:
        """Send a raw SMS without a Notification entity.

        Production: Use Twilio/msg91 client.
        """
        try:
            body = message[:160]
            logger.info("RAW SMS SENT", extra={"to": to_mobile, "length": len(body)})
            return True
        except Exception:
            logger.error("RAW SMS FAILED", extra={"to": to_mobile}, exc_info=True)
            return False
