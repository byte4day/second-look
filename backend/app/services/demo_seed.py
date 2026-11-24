"""First-run demo reports so Scams near me is not empty for judges."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import Report
from app.services.report_service import _ip_hash

SAMPLES: list[tuple[str, str, str]] = [
    ("phone", "england", "Someone pretended to be my bank on the phone."),
    ("phone", "england", "Caller said my account was at risk and asked for a code."),
    ("text", "england", "Text claimed my card was locked and gave a strange link."),
    ("text", "england", "Fake parcel fee text with a payment link."),
    ("email", "england", "Email looked like HMRC and asked me to pay a fine."),
    ("phone", "scotland", "Tech support call asked me to install remote software."),
    ("phone", "scotland", "Caller said they were from my broadband company."),
    ("online", "scotland", "Online advert offered a prize that needed a fee."),
    ("doorstep", "wales", "Someone at the door asked for bank details."),
    ("text", "wales", "Message said a grandchild was in trouble and needed money."),
    ("phone", "northern_ireland", "Government imposter call about a tax bill."),
    ("email", "northern_ireland", "Password reset email from a lookalike address."),
]


def seed_reports(db: Session, *, force: bool = False) -> int:
    count = db.scalar(select(func.count()).select_from(Report)) or 0
    if count > 0 and not force:
        return 0
    if force and count > 0:
        db.query(Report).delete()
        db.commit()
    for scam_type, area, text in SAMPLES:
        db.add(
            Report(
                scam_type=scam_type,
                area=area,
                text=text,
                ip_hash=_ip_hash("demo-seed"),
            )
        )
    db.commit()
    return len(SAMPLES)
