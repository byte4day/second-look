"""Anonymous scam reports."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import Report
from app.services import pii_scrubber


def _ip_hash(ip: str) -> str:
    salt = get_settings().jwt_secret
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()[:32]


def create_report(
    db: Session,
    scam_type: str,
    area: str,
    text: str | None,
    client_ip: str,
) -> Report:
    # Rate limit: 5 reports a day per IP hash
    since = datetime.now(UTC) - timedelta(days=1)
    ip_h = _ip_hash(client_ip)
    count = db.scalar(
        select(func.count()).select_from(Report).where(
            Report.ip_hash == ip_h, Report.created_at >= since
        )
    ) or 0
    if count >= 5:
        raise ValueError("rate_limited")

    scrubbed = None
    if text:
        scrubbed = pii_scrubber.scrub(text)[:200]
        if pii_scrubber.looks_like_personal_data(text):
            raise ValueError("personal_data")

    report = Report(
        scam_type=scam_type,
        area=area,
        text=scrubbed,
        ip_hash=ip_h,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def weekly_summary(db: Session, area: str | None = None) -> dict:
    settings = get_settings()
    since = datetime.now(UTC) - timedelta(days=7)
    stmt = select(Report.scam_type, func.count()).where(Report.created_at >= since)
    # "generic" / empty = all areas (matches frontend "All areas").
    if area and area not in {"generic", "all", "*"}:
        stmt = stmt.where(Report.area == area)
    stmt = stmt.group_by(Report.scam_type).order_by(func.count().desc())
    rows = db.execute(stmt).all()
    items = [{"scam_type": r[0], "count": r[1]} for r in rows]
    total = sum(i["count"] for i in items)
    min_show = settings.min_reports_to_show
    enough = total >= min_show
    return {
        "area": area,
        "items": items if enough else [],
        "total": total,
        "enough": enough,
        "message_plain": None
        if enough
        else "Not enough reports yet",
        "label": "reported by users, not verified",
        "period_days": 7,
    }
