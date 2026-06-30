"""Channel-specific Pydantic types for the whatsapp adapter."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MetaParsed(BaseModel):
    from_id: str
    text: str | None
    message_id: str
    timestamp: str
    profile_name: str | None


class TwilioParsed(BaseModel):
    from_id: str
    text: str | None
    message_id: str | None
    timestamp: datetime
    profile_name: str | None


class MetaSendText(BaseModel):
    body: str


class MetaSendPayload(BaseModel):
    messaging_product: str = "whatsapp"
    to: str
    type: str = "text"
    text: MetaSendText


class TwilioSendPayload(BaseModel):
    To: str
    From: str
    Body: str
