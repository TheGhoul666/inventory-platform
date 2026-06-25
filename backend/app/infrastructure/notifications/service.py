"""
Notification Service — delivers alerts to recipients via SMS and/or email.

Design
------
The service is provider-agnostic. It resolves a delivery channel from
settings and falls back to a console/log provider when no real provider
is configured (the default in development).

Providers implemented:
  - ConsoleProvider  : logs the message (always available; dev/test default)
  - TwilioSMSProvider : real SMS via Twilio REST API (if TWILIO_* set)
  - SMTPEmailProvider : real email via SMTP (if SMTP_* set)

Delivery never raises into the caller — a notification failure must never
break the inventory operation that triggered it. All failures are logged
and returned as a NotificationResult with success=False.
"""
from __future__ import annotations

import asyncio
import logging
import smtplib
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from functools import lru_cache
from typing import Optional

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    channel: str
    recipient: str
    success: bool
    detail: str = ""


@dataclass
class Recipient:
    """A person to notify."""
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


# --------------------------------------------------------------------------
# Providers
# --------------------------------------------------------------------------

class ConsoleProvider:
    """Logs notifications. Always-available fallback for dev / when no SMS
    or SMTP provider is configured."""

    channel = "console"

    async def send_sms(self, phone: str, message: str) -> NotificationResult:
        logger.warning("[SMS:console] -> %s | %s", phone, message)
        return NotificationResult("sms", phone, True, "logged to console")

    async def send_email(self, email: str, subject: str, body: str) -> NotificationResult:
        logger.warning("[EMAIL:console] -> %s | %s | %s", email, subject, body)
        return NotificationResult("email", email, True, "logged to console")


class TwilioSMSProvider:
    """Sends SMS via the Twilio REST API (no SDK dependency — raw HTTP)."""

    channel = "twilio"

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self._sid = account_sid
        self._token = auth_token
        self._from = from_number

    async def send_sms(self, phone: str, message: str) -> NotificationResult:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self._sid}/Messages.json"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    url,
                    auth=(self._sid, self._token),
                    data={"To": phone, "From": self._from, "Body": message},
                )
            if resp.status_code in (200, 201):
                return NotificationResult("sms", phone, True, "sent via twilio")
            return NotificationResult("sms", phone, False, f"twilio {resp.status_code}: {resp.text[:200]}")
        except Exception as e:  # noqa: BLE001
            logger.error("Twilio SMS send failed: %s", e)
            return NotificationResult("sms", phone, False, str(e))


class SMTPEmailProvider:
    """Sends email via a standard SMTP server."""

    channel = "smtp"

    def __init__(self, host: str, port: int, username: str, password: str, sender: str, use_tls: bool):
        self._host = host
        self._port = port
        self._user = username
        self._pass = password
        self._sender = sender
        self._tls = use_tls

    def _send_blocking(self, email: str, subject: str, body: str) -> None:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = self._sender
        msg["To"] = email
        with smtplib.SMTP(self._host, self._port, timeout=10) as server:
            if self._tls:
                server.starttls()
            if self._user:
                server.login(self._user, self._pass)
            server.sendmail(self._sender, [email], msg.as_string())

    async def send_email(self, email: str, subject: str, body: str) -> NotificationResult:
        try:
            await asyncio.to_thread(self._send_blocking, email, subject, body)
            return NotificationResult("email", email, True, "sent via smtp")
        except Exception as e:  # noqa: BLE001
            logger.error("SMTP email send failed: %s", e)
            return NotificationResult("email", email, False, str(e))


# --------------------------------------------------------------------------
# Service
# --------------------------------------------------------------------------

class NotificationService:
    """Resolves providers from settings and dispatches notifications.

    Channels are chosen by what is configured. The console provider is the
    universal fallback so notifications are always observable in logs.
    """

    def __init__(self) -> None:
        s = get_settings()
        self._console = ConsoleProvider()

        # SMS provider
        self._sms = None
        if getattr(s, "TWILIO_ACCOUNT_SID", "") and getattr(s, "TWILIO_AUTH_TOKEN", "") and getattr(s, "TWILIO_FROM_NUMBER", ""):
            self._sms = TwilioSMSProvider(s.TWILIO_ACCOUNT_SID, s.TWILIO_AUTH_TOKEN, s.TWILIO_FROM_NUMBER)
            logger.info("NotificationService: SMS provider = Twilio")
        else:
            logger.info("NotificationService: SMS provider = Console (mock)")

        # Email provider
        self._email = None
        if getattr(s, "SMTP_HOST", "") and getattr(s, "SMTP_SENDER", ""):
            self._email = SMTPEmailProvider(
                s.SMTP_HOST, s.SMTP_PORT, s.SMTP_USERNAME, s.SMTP_PASSWORD, s.SMTP_SENDER, s.SMTP_USE_TLS
            )
            logger.info("NotificationService: Email provider = SMTP")
        else:
            logger.info("NotificationService: Email provider = Console (mock)")

    @property
    def sms_enabled(self) -> bool:
        return self._sms is not None

    @property
    def email_enabled(self) -> bool:
        return self._email is not None

    async def send_sms(self, phone: str, message: str) -> NotificationResult:
        provider = self._sms or self._console
        return await provider.send_sms(phone, message)

    async def send_email(self, email: str, subject: str, body: str) -> NotificationResult:
        provider = self._email or self._console
        return await provider.send_email(email, subject, body)

    async def notify(
        self,
        recipient: Recipient,
        subject: str,
        message: str,
    ) -> list[NotificationResult]:
        """Send to all available channels for a recipient (SMS + email).

        SMS is the primary channel for the SuperAdmin's phone. Email is a
        secondary channel when an address is present.
        """
        results: list[NotificationResult] = []
        if recipient.phone:
            results.append(await self.send_sms(recipient.phone, f"{subject}\n{message}"))
        if recipient.email:
            results.append(await self.send_email(recipient.email, subject, message))
        if not results:
            # No contact info — log so it is still observable
            results.append(
                NotificationResult("none", recipient.user_id, False, "recipient has no phone or email")
            )
        return results


@lru_cache
def get_notification_service() -> NotificationService:
    return NotificationService()
