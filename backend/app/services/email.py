from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Iterable

from app.core.config import settings
from app.models.emergency import EmergencyContact
from app.models.user import User


class EmailNotConfigured(RuntimeError):
    pass


class EmailDeliveryError(RuntimeError):
    pass


def _require_smtp_settings() -> None:
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise EmailNotConfigured("SMTP is not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, and EMAILS_FROM_EMAIL.")


def send_email(*, recipients: list[str], subject: str, body: str) -> None:
    _require_smtp_settings()
    if not recipients:
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.EMAILS_FROM_EMAIL
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except smtplib.SMTPException as exc:
        raise EmailDeliveryError(f"Could not send email: {exc}") from exc
    except OSError as exc:
        raise EmailDeliveryError(f"Could not connect to SMTP server: {exc}") from exc


def send_sos_alert_emails(
    *,
    user: User,
    contacts: Iterable[EmergencyContact],
    latitude: float | None,
    longitude: float | None,
    message: str | None,
) -> int:
    recipients = [contact.email for contact in contacts if contact.email]
    if not recipients:
        return 0

    location_line = "Location: not provided"
    if latitude is not None and longitude is not None:
        maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
        location_line = f"Location: {latitude:.6f}, {longitude:.6f}\nMap: {maps_url}"

    body = (
        f"{user.full_name} triggered an SOS alert from MedVision AI.\n\n"
        f"User email: {user.email}\n"
        f"{location_line}\n\n"
        f"Message: {message or 'Immediate help requested.'}\n\n"
        "Please contact the user or local emergency services immediately."
    )

    send_email(
        recipients=recipients,
        subject=f"SOS alert from {user.full_name}",
        body=body,
    )
    return len(recipients)
