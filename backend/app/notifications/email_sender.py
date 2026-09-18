"""
Lightweight SMTP email sender for match alerts.

Uses the standard library only. If SMTP_HOST is not configured,
send_email() returns False and logs a skip message — the app still works.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import (
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
)

logger = logging.getLogger(__name__)


def email_configured() -> bool:
    return bool(SMTP_HOST and SMTP_FROM)


def send_email(to: str, subject: str, body: str) -> bool:
    """Send a plain-text email. Returns True on success."""
    to = (to or "").strip()
    if not to or "@" not in to:
        return False

    if not email_configured():
        logger.info(
            "SMTP not configured — skipped email to %s (subject: %s)",
            to,
            subject,
        )
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USER:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Sent match alert email to %s", to)
        return True
    except Exception as exc:
        logger.warning("Failed to send email to %s: %s", to, exc)
        return False
