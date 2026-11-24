"""Fast local red-flag detection — never depends on the model being perfect."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.analyze import RedFlag


@dataclass(frozen=True)
class HeuristicHit:
    flag: RedFlag
    quote: str
    why: str
    weight: int  # higher = stronger signal


# (flag, why, weight, patterns) — quotes taken from the first regex match in the text
RULES: list[tuple[RedFlag, str, int, list[re.Pattern[str]]]] = [
    (
        RedFlag.ASKS_FOR_CODE_OR_PASSWORD,
        "Asks for a code or password.",
        5,
        [
            re.compile(r".{0,40}\b(?:one[-\s]?time|otp|verification|security)\s+code\b.{0,40}", re.I),
            re.compile(r".{0,30}\b(?:password|pin|passcode)\b.{0,30}", re.I),
            re.compile(r".{0,40}\bshare\s+the\s+code\b.{0,20}", re.I),
            re.compile(r".{0,40}\b\d\s*-?\s*digit\s+code\b.{0,40}", re.I),
            re.compile(r".{0,40}\b(?:reply|send|give|tell)\b.{0,20}\bcode\b.{0,40}", re.I),
        ],
    ),
    (
        RedFlag.UNUSUAL_PAYMENT,
        "Asks for an unusual payment method.",
        5,
        [
            re.compile(r".{0,40}\b(?:gift\s*cards?|itunes|google\s*play)\b.{0,40}", re.I),
            re.compile(r".{0,40}\b(?:bitcoin|crypto|cryptocurrency|usdt|wire\s+transfer)\b.{0,40}", re.I),
            re.compile(r".{0,40}\b(?:cash\s+app|western\s+union|moneygram|zelle)\b.{0,40}", re.I),
            re.compile(r".{0,50}\b(?:write|wrote|writing)\s+a\s+check\s+for\s+\$?\d[\d,]*\b.{0,20}", re.I),
        ],
    ),
    (
        RedFlag.UNUSUAL_PAYMENT,
        "Asks you to send money.",
        4,
        [
            re.compile(
                r".{0,40}\b(?:send|transfer|lend|pay|wire)\s+(?:me\s+|us\s+)?(?:£|\$|€)\s?\d[\d,.]*.{0,40}",
                re.I,
            ),
            re.compile(
                r".{0,40}\b(?:send|transfer|lend)\s+(?:me\s+)?(?:some\s+)?money\b.{0,40}", re.I
            ),
        ],
    ),
    (
        RedFlag.REMOTE_ACCESS,
        "Asks for remote access to your device.",
        5,
        [
            re.compile(r".{0,40}\b(?:anydesk|teamviewer|remote\s+access|remote\s+tool)\b.{0,40}", re.I),
            re.compile(r".{0,40}\blet\s+me\s+(?:connect|access)\s+(?:your|the)\s+(?:computer|pc|device)\b.{0,20}", re.I),
        ],
    ),
    (
        RedFlag.SECRECY,
        "Asks you to keep a secret.",
        4,
        [
            re.compile(r".{0,40}\bdo\s+not\s+tell\s+anyone\b.{0,40}", re.I),
            re.compile(r".{0,40}\bkeep\s+(?:this|it)\s+(?:a\s+)?secret\b.{0,40}", re.I),
            re.compile(r".{0,40}\bdon'?t\s+tell\s+(?:anyone|mum|mom|family)\b.{0,40}", re.I),
        ],
    ),
    (
        RedFlag.THREAT,
        "Uses threats or fear.",
        4,
        [
            re.compile(r".{0,40}\b(?:arrest|warrant|police|jail|prison)\b.{0,40}", re.I),
            re.compile(
                r".{0,40}\baccount\b.{0,30}\b(?:closed|locked|suspended|frozen|blocked)\b.{0,30}",
                re.I,
            ),
            re.compile(r".{0,40}\b(?:account\s+will\s+be\s+(?:closed|locked|frozen)|legal\s+action)\b.{0,40}", re.I),
        ],
    ),
    (
        RedFlag.URGENCY,
        "Pushes you to act fast.",
        3,
        [
            re.compile(r".{0,40}\b(?:immediately|right\s+now|within\s+\d+\s+minutes?|urgent|asap)\b.{0,40}", re.I),
            re.compile(r".{0,40}\b(?:act\s+now|hurry|before\s+it(?:'s|\s+is)\s+too\s+late)\b.{0,40}", re.I),
        ],
    ),
    (
        RedFlag.AUTHORITY_CLAIM,
        "Pretends to be a bank, government, or company.",
        3,
        [
            re.compile(
                r".{0,50}\b(?:fraud\s+(?:unit|department|alert)|hmrc|irs|revenue|tax\s+office|"
                r"microsoft|apple\s+support|chase|wells\s+fargo|bank\s+of\s+america|bofa|"
                r"citibank|metro\s+trust)\b.{0,40}",
                re.I,
            ),
            re.compile(r".{0,40}\bthis\s+is\s+(?:your\s+)?(?:bank|metro\s+trust)\b.{0,40}", re.I),
        ],
    ),
    (
        RedFlag.LINK_OR_CALLBACK_NUMBER,
        "Pushes a strange link or callback number.",
        3,
        [
            re.compile(
                r".{0,40}\b(?:click\s+(?:here|this\s+link)|visit\s+this\s+link|\[fake\s+link\])\b.{0,40}",
                re.I,
            ),
            re.compile(r"(?:https?://|www\.)\S+", re.I),
            re.compile(r"\b[a-z0-9-]+\.(?:com|net|org)/\S+", re.I),
            re.compile(r".{0,40}\bcall\s+(?:us\s+)?(?:back\s+)?(?:on|at)\b.{0,40}", re.I),
            re.compile(r".{0,40}\breply\s+yes\s+or\s+no\b.{0,40}", re.I),
        ],
    ),
    (
        RedFlag.EMOTIONAL_STORY,
        "Uses an emotional story to rush you.",
        3,
        [
            re.compile(r".{0,50}\b(?:gran|grandma|grandson|granddaughter|in\s+trouble|hospital|stuck\s+abroad|emergency)\b.{0,50}", re.I),
            re.compile(
                r".{0,40}\b(?:new\s+(?:phone\s+)?number|lost\s+my\s+phone|broke\s+my\s+phone|"
                r"changed\s+my\s+number|phone\s+(?:is\s+)?broken)\b.{0,40}",
                re.I,
            ),
        ],
    ),
    (
        RedFlag.TOO_GOOD_TO_BE_TRUE,
        "Offers something that sounds too good to be true.",
        2,
        [
            re.compile(r".{0,40}\b(?:you\s+have\s+won|lottery|prize|free\s+money|claim\s+your)\b.{0,40}", re.I),
        ],
    ),
    (
        RedFlag.UNEXPECTED_CONTACT,
        "This contact was unexpected.",
        2,
        [
            re.compile(r".{0,40}\b(?:unsolicited|we\s+detected|unusual\s+activity|suspicious\s+login)\b.{0,40}", re.I),
        ],
    ),
]


def _clip_quote(match: str, limit: int = 90) -> str:
    q = re.sub(r"\s+", " ", match).strip()
    if len(q) <= limit:
        return q
    return q[: limit - 1].rstrip() + "…"


def _is_word(ch: str) -> bool:
    return ch.isalnum() or ch in "'’"


def _word_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    """Grow a regex match so it never starts or ends in the middle of a word."""
    while start > 0 and _is_word(text[start - 1]) and _is_word(text[start]):
        start -= 1
    while end < len(text) and _is_word(text[end]) and _is_word(text[end - 1]):
        end += 1
    return start, end


def trim_to_words(quote: str, limit: int) -> str:
    """Cut a long quote at the last whole word so it still appears verbatim in the text."""
    if len(quote) <= limit:
        return quote
    cut = quote[:limit]
    space = cut.rfind(" ")
    return (cut[:space] if space > limit // 2 else cut).rstrip(" ,.;:")


def scan(text: str) -> list[HeuristicHit]:
    hits: list[HeuristicHit] = []
    seen: set[RedFlag] = set()
    for flag, why, weight, patterns in RULES:
        if flag in seen:
            continue
        for pat in patterns:
            m = pat.search(text)
            if not m:
                continue
            start, end = _word_bounds(text, m.start(), m.end())
            quote = trim_to_words(text[start:end].strip(), 120)
            if not quote or quote not in text:
                continue
            hits.append(HeuristicHit(flag=flag, quote=quote, why=why, weight=weight))
            seen.add(flag)
            break
    return hits


def score(hits: list[HeuristicHit]) -> int:
    return sum(h.weight for h in hits)


# Words that mean "we cannot vouch for this" even when no rule matched.
_NOT_BENIGN = re.compile(
    r"https?://|www\.|\b[a-z0-9-]+\.(?:com|net|org|co|uk|io|xyz|info)\b|[£$€]\s?\d|\d{5,}|"
    r"\b(?:pay|payment|paid|money|account|bank|code|verify|verification|click|link|card|"
    r"transfer|password|log\s?in|login|refund|invoice|delivery|parcel|prize|fee|fine|"
    r"tax|loan|invest|investment|wallet|urgent|confirm|suspend|suspended|locked)\b",
    re.I,
)


def looks_benign(text: str) -> bool:
    """A short, everyday message with no money, links, numbers or account words."""
    return len(text) <= 400 and not _NOT_BENIGN.search(text)


def risk_from_score(total: int, text: str | None = None) -> str:
    """Score → risk. With no signals we only say "probably fine" for clearly everyday
    text; otherwise we say we cannot tell, because absence of keywords is not safety."""
    if total >= 8:
        return "likely_scam"
    if total >= 1:
        return "suspicious"
    if text is not None and looks_benign(text):
        return "probably_ok"
    return "cannot_tell"
