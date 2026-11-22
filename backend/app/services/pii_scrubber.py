"""Scrub PII from text before storage or logging."""

from __future__ import annotations

import re

PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}\b"
)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
URL_RE = re.compile(r"https?://[^\s]+|www\.[^\s]+", re.IGNORECASE)
DIGIT_RUN_RE = re.compile(r"\b\d{6,}\b")
CARD_LIKE_RE = re.compile(r"\b(?:\d{4}[\s-]?){3}\d{1,4}\b")

STILL_LOOKS_PERSONAL = re.compile(
    r"(@|\b\d{6,}\b|https?://|www\.|\b\d{4}[\s-]?\d{4}[\s-]?\d{4})",
    re.IGNORECASE,
)


def scrub(text: str) -> str:
    if not text:
        return text
    out = text
    out = EMAIL_RE.sub("[email-redacted]", out)
    out = URL_RE.sub("[url-redacted]", out)
    out = CARD_LIKE_RE.sub("[card-redacted]", out)
    out = PHONE_RE.sub("[phone-redacted]", out)
    out = DIGIT_RUN_RE.sub("[number-redacted]", out)
    return out


def looks_like_personal_data(text: str) -> bool:
    """True if text still appears to contain personal data after scrubbing."""
    cleaned = scrub(text)
    return bool(STILL_LOOKS_PERSONAL.search(cleaned))
