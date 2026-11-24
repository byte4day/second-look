"""Family alerts with rate limits."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import AlertLog, FamilyContact, User
from app.services import email_service

ALERTS_PER_HOUR = 3


def _recent_count(db: Session, user_id: int) -> int:
    since = datetime.now(UTC) - timedelta(hours=1)
    return db.scalar(
        select(func.count()).select_from(AlertLog).where(
            AlertLog.user_id == user_id, AlertLog.created_at >= since
        )
    ) or 0


def send_alerts(
    db: Session,
    user: User,
    message_plain: str,
    contact_ids: list[int] | None = None,
) -> tuple[int, int]:
    if _recent_count(db, user.id) >= ALERTS_PER_HOUR:
        raise ValueError("rate_limited")
    q = select(FamilyContact).where(
        FamilyContact.user_id == user.id,
        FamilyContact.status == "accepted",
    )
    if contact_ids:
        q = q.where(FamilyContact.id.in_(contact_ids))
    contacts = list(db.scalars(q))
    if not contacts:
        return 0, 0
    # One log row per alert (not per email), committed BEFORE sending so a
    # partial SMTP failure still counts against the hourly limit.
    db.add(AlertLog(user_id=user.id, alert_type="family", channel="email"))
    db.commit()
    sent = 0
    skipped = 0
    help_url = get_settings().public_app_url.rstrip("/") + "/help"
    for c in contacts:
        body = (
            f"{user.email} asked us to notify you:\n\n{message_plain}\n\n"
            f"Calm steps you can go through together: {help_url}"
        )
        try:
            ok = email_service.send_email(c.email, "Scam Shield family alert", body)
        except Exception:  # noqa: BLE001
            ok = False
        if ok:
            sent += 1
        else:
            skipped += 1
    return sent, skipped


def send_test_alert(db: Session, user: User) -> bool:
    sent, _ = send_alerts(db, user, "This is a test alert from Scam Shield.", contact_ids=[])
    return True