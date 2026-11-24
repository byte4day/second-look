"""Safety layer for drills, analyzer, and user-facing generation."""

from __future__ import annotations

import re

from app.services.pii_scrubber import scrub

HOWTO_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"how\s+(?:to|do\s+i)\s+(?:scam|phish|defraud|trick)",
        r"write\s+(?:me\s+)?(?:a\s+)?(?:better\s+)?scam\s+script",
        r"help\s+me\s+(?:scam|phish|trick)\s+(?:someone|people)",
        r"steal\s+(?:money|credentials|passwords)",
        r"bypass\s+(?:bank|2fa|otp|security)",
        r"optimise\s+(?:this\s+)?(?:scam|script)",
        r"optimize\s+(?:this\s+)?(?:scam|script)",
        r"ignore\s+(?:your|all)\s+(?:rules|instructions|safety)",
        r"you\s+are\s+now\s+(?:a\s+)?(?:real\s+)?scammer",
        r"jailbreak",
        r"dan\s+mode",
        r"developer\s+mode\s+enabled",
        r"system\s+prompt\s+override",
    )
]

INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions",
        r"disregard\s+(?:your|the)\s+(?:system|safety)\s+(?:prompt|rules)",
        r"<\s*/?\s*system\s*>",
        r"\[(?:INST|SYS|SYSTEM)\]",
        r"begin\s+system\s+prompt",
        r"reveal\s+(?:your|the)\s+(?:system\s+)?prompt",
        r"exfiltrat(?:e|ion)",
    )
]

PASSWORD_PATTERN = re.compile(r"my\s+password\s+is\s+\S+", re.IGNORECASE)
NATIONAL_ID = re.compile(r"\b(?:SSN|national\s+insurance|NI\s*number)\b.{0,20}\d{3,}", re.I)
REAL_URL = re.compile(r"https?://[^\s]+|www\.[^\s]+", re.IGNORECASE)
REAL_PHONE = re.compile(r"(?<!\[)\+?\d[\d\s().-]{8,}\d(?!\])")
CARD_LIKE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def luhn_check(number: str) -> bool:
    nums = [int(c) for c in number if c.isdigit()]
    if len(nums) < 13 or len(nums) > 19:
        return False
    checksum = 0
    parity = len(nums) % 2
    for i, d in enumerate(nums):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def contains_real_secrets(text: str) -> bool:
    if PASSWORD_PATTERN.search(text) or NATIONAL_ID.search(text):
        return True
    for match in CARD_LIKE.finditer(text):
        if luhn_check(match.group(0)):
            return True
    return False


def refuses_howto_scam(text: str) -> bool:
    return any(p.search(text) for p in HOWTO_PATTERNS)


def looks_like_prompt_injection(text: str) -> bool:
    return any(p.search(text) for p in INJECTION_PATTERNS)


def refuses_unsafe_request(text: str) -> bool:
    return refuses_howto_scam(text) or looks_like_prompt_injection(text)


def strip_real_pii_from_output(text: str) -> str:
    out = REAL_URL.sub("[fake link]", text)
    out = REAL_PHONE.sub("[fake number]", out)
    return scrub(out)


def enforce_word_limit(text: str, max_words: int = 60) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def sanitize_user_message_for_display(text: str) -> str:
    if contains_real_secrets(text):
        return "[hidden]"
    return scrub(text)


def sanitize_model_output(text: str, max_words: int = 60) -> str:
    text = strip_real_pii_from_output(text)
    return enforce_word_limit(text, max_words)


def evaluate_adversarial(prompt: str) -> dict[str, bool | str]:
    """Used by scripts/eval_safety.py."""
    if refuses_howto_scam(prompt) or looks_like_prompt_injection(prompt):
        return {"pass": True, "action": "refuse"}
    if contains_real_secrets(prompt):
        return {"pass": True, "action": "hide"}
    cleaned = sanitize_model_output(prompt)
    if "http://" in cleaned.lower() or "https://" in cleaned.lower():
        return {"pass": False, "action": "leak_url"}
    return {"pass": True, "action": "allow_sanitized"}
