import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_email(action: str, payload: dict) -> bool:
    """Send a request to the serverless email service.

    action: one of SIGNUP_WELCOME, BOOKING_CONFIRMATION, BOOKING_CANCELLATION
    payload: action-specific data (e.g., to_email, subject, template data)
    """
    url = settings.SERVERLESS_EMAIL_URL.rstrip("/") + "/send"
    body = {"action": action, "payload": payload}
    try:
        resp = requests.post(url, json=body, timeout=5)
        resp.raise_for_status()
        return True
    except Exception as exc:
        logger.exception("Failed to call email service: %s", exc)
        return False
