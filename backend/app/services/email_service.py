"""Email delivery: console, SMTP, or Resend."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body_plain: str, settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    backend = settings.email_backend.lower()

    if backend == "console":
        logger.info("email_console to=%s subject=%s bytes=%s", to, subject, len(body_plain))
        return True

    if backend == "smtp":
        if not settings.smtp_host:
            logger.warning("smtp_not_configured")
            return False
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg.set_content(body_plain)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return True

    if backend == "resend":
        if not settings.resend_api_key:
            logger.warning("resend_not_configured")
            return False
        with httpx.Client(timeout=15.0) as client:
            r = client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={
                    "from": settings.resend_from,
                    "to": [to],
                    "subject": subject,
                    "text": body_plain,
                },
            )
            r.raise_for_status()
        return True

    logger.error("unknown_email_backend backend=%s", backend)
    return False