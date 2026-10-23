from django.conf import settings
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def create_calendar_event(refresh_token: str, summary: str, start_iso: str, end_iso: str, attendees: list = None, description: str = ""):
    """Create a Google Calendar event using a stored refresh token.

    refresh_token: user's refresh token
    start_iso, end_iso: RFC3339 timestamp strings (e.g., '2026-01-26T10:00:00')
    attendees: list of emails
    Returns event resource dict on success, None on failure.
    """
    if not refresh_token or not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        logger.info("Google credentials missing; skipping calendar event creation")
        return None

    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/calendar.events"],
        )

        request = Request()
        creds.refresh(request)

        service = build("calendar", "v3", credentials=creds)

        event_body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_iso},
            "end": {"dateTime": end_iso},
        }
        if attendees:
            event_body["attendees"] = [{"email": e} for e in attendees]

        event = service.events().insert(calendarId="primary", body=event_body, sendUpdates="all").execute()
        return event

    except Exception as exc:
        logger.exception("Failed creating calendar event: %s", exc)
        return None
