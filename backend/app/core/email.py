import logging
import threading
import time
from dataclasses import dataclass

import httpx

from app.core.config import Settings

RESEND_URL = "https://api.resend.com/emails"
HOUR_SECONDS = 3600
DAY_SECONDS = 86400

logger = logging.getLogger("examslot.email")


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str


class MemoryEmailSender:
    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> bool:
        self.messages.append(message)
        return True


class ResendEmailSender:
    def __init__(self, client: httpx.Client, settings: Settings) -> None:
        self._client = client
        self._api_key = settings.RESEND_API_KEY
        self._sender = settings.EMAIL_FROM
        self._reply_to = settings.EMAIL_REPLY_TO

    def send(self, message: EmailMessage) -> bool:
        try:
            response = self._client.post(
                RESEND_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "from": self._sender,
                    "to": [message.to],
                    "subject": message.subject,
                    "text": message.text,
                    "html": message.html,
                    "reply_to": self._reply_to,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return False
        return True


class EmailGate:
    def __init__(self, sender: MemoryEmailSender | ResendEmailSender, settings: Settings) -> None:
        self._sender = sender
        self._allowlist = tuple(
            entry.strip().lower()
            for entry in settings.EMAIL_RECIPIENT_ALLOWLIST.split(",")
            if entry.strip()
        )
        self._hourly_cap = settings.EMAIL_HOURLY_CAP
        self._daily_cap = settings.EMAIL_DAILY_CAP
        self._lock = threading.Lock()
        self._sent_at: list[float] = []

    def send(self, kind: str, message: EmailMessage) -> str:
        if not self._allowed(message.to):
            logger.info("email", extra={"kind": kind, "result": "blocked"})
            return "failed"
        if not self._reserve():
            logger.info("email", extra={"kind": kind, "result": "capped"})
            return "failed"
        result = "sent" if self._sender.send(message) else "failed"
        logger.info("email", extra={"kind": kind, "result": result})
        return result

    def _allowed(self, recipient: str) -> bool:
        if not self._allowlist:
            return True
        address = recipient.lower()
        domain = address.partition("@")[2]
        return address in self._allowlist or f"@{domain}" in self._allowlist

    def _reserve(self) -> bool:
        now = time.monotonic()
        with self._lock:
            self._sent_at = [sent for sent in self._sent_at if now - sent < DAY_SECONDS]
            recent = sum(1 for sent in self._sent_at if now - sent < HOUR_SECONDS)
            if recent >= self._hourly_cap or len(self._sent_at) >= self._daily_cap:
                return False
            self._sent_at.append(now)
        return True


def build_email_sender(
    settings: Settings, client: httpx.Client | None
) -> MemoryEmailSender | ResendEmailSender:
    if settings.EMAIL_BACKEND == "resend" and client is not None:
        return ResendEmailSender(client, settings)
    return MemoryEmailSender()
