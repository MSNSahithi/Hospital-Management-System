import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")


def send_smtp(to_email: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = SMTP_USER or "no-reply@example.com"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    if SMTP_USER and SMTP_PASS:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
    else:
        # fallback: print to logs when SMTP not configured
        print("SMTP not configured. Would send to:", to_email)
        print(subject)
        print(body)


def send(event, context):
    # Simple HTTP handler compatible with serverless-offline
    try:
        body = event.get("body") or event
        if isinstance(body, str):
            import json

            body = json.loads(body)

        action = body.get("action")
        payload = body.get("payload", {})

        if action == "SIGNUP_WELCOME":
            to = payload.get("to_email")
            username = payload.get("username", "")
            subject = f"Welcome to Mini-HMS, {username}!"
            text = f"Hi {username},\n\nWelcome to Mini Hospital Management System.\n\nThanks!"
            send_smtp(to, subject, text)
            return {"statusCode": 200, "body": "ok"}

        if action == "BOOKING_CONFIRMATION":
            to = payload.get("to_email")
            doc = payload.get("doctor")
            patient = payload.get("patient")
            date = payload.get("date")
            start = payload.get("start_time")
            end = payload.get("end_time")
            subject = f"Booking confirmed: {date} {start}-{end}"
            text = f"Appointment confirmed with Dr. {doc} for patient {patient} on {date} from {start} to {end}."
            send_smtp(to, subject, text)
            return {"statusCode": 200, "body": "ok"}

        if action == "BOOKING_CANCELLATION":
            to = payload.get("to_email")
            doc = payload.get("doctor")
            patient = payload.get("patient")
            date = payload.get("date")
            start = payload.get("start_time")
            end = payload.get("end_time")
            subject = f"Booking cancelled: {date} {start}-{end}"
            text = f"Appointment with Dr. {doc} for patient {patient} on {date} from {start} to {end} was cancelled."
            send_smtp(to, subject, text)
            return {"statusCode": 200, "body": "ok"}

        return {"statusCode": 400, "body": "unknown action"}

    except Exception as e:
        print("Error in handler:", e)
        return {"statusCode": 500, "body": "error"}
