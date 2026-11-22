"""Analyzer request/response schemas."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    LIKELY_SCAM = "likely_scam"
    SUSPICIOUS = "suspicious"
    PROBABLY_OK = "probably_ok"
    CANNOT_TELL = "cannot_tell"


class RedFlag(str, Enum):
    UNEXPECTED_CONTACT = "UNEXPECTED_CONTACT"
    URGENCY = "URGENCY"
    SECRECY = "SECRECY"
    THREAT = "THREAT"
    AUTHORITY_CLAIM = "AUTHORITY_CLAIM"
    ASKS_FOR_CODE_OR_PASSWORD = "ASKS_FOR_CODE_OR_PASSWORD"
    UNUSUAL_PAYMENT = "UNUSUAL_PAYMENT"
    LINK_OR_CALLBACK_NUMBER = "LINK_OR_CALLBACK_NUMBER"
    REMOTE_ACCESS = "REMOTE_ACCESS"
    EMOTIONAL_STORY = "EMOTIONAL_STORY"
    TOO_GOOD_TO_BE_TRUE = "TOO_GOOD_TO_BE_TRUE"


PLAIN_FLAG_LABELS: dict[str, str] = {
    "UNEXPECTED_CONTACT": "Unexpected contact",
    "URGENCY": "Pushes you to act fast",
    "SECRECY": "Asks you to keep a secret",
    "THREAT": "Uses threats or fear",
    "AUTHORITY_CLAIM": "Pretends to be an authority",
    "ASKS_FOR_CODE_OR_PASSWORD": "Asks for a code or password",
    "UNUSUAL_PAYMENT": "Unusual payment method",
    "LINK_OR_CALLBACK_NUMBER": "Strange link or callback number",
    "REMOTE_ACCESS": "Asks for remote access",
    "EMOTIONAL_STORY": "Emotional story to rush you",
    "TOO_GOOD_TO_BE_TRUE": "Too good to be true",
}


class ReasonItem(BaseModel):
    flag: RedFlag
    quote: str
    why: str


class AnalyzeResult(BaseModel):
    risk_level: Literal["likely_scam", "suspicious", "probably_ok", "cannot_tell"]
    headline: str
    reasons: list[ReasonItem] = Field(default_factory=list)
    what_to_do_now: list[str] = Field(default_factory=list)
    what_not_to_do: list[str] = Field(default_factory=list)
    note: str = "If you are unsure, contact them using a number you already know."

    @field_validator("what_to_do_now")
    @classmethod
    def cap_do(cls, v: list[str]) -> list[str]:
        return v[:4]

    @field_validator("what_not_to_do")
    @classmethod
    def cap_dont(cls, v: list[str]) -> list[str]:
        return v[:3]


class AnalyzeTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class AnalyzeImageRequest(BaseModel):
    image_base64: str = Field(min_length=1)
    mime_type: str = Field(default="image/jpeg", pattern=r"^image/")
