"""Web Push (optional VAPID)."""

from __future__ import annotations

import json
import logging

from pywebpush import webpush
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import PushSubscription, User

logger = logging.getLogger(__name__)


def vapid_public_key() -> str | None:
    settings = get_settings()
    key = settings.vapid_public_key.strip()
    return key or None


def subscribe(db: Session, user: User, endpoint: str, keys: dict[str, str]) -> PushSubscription:
    sub = PushSubscription(
        user_id=user.id,
        endpoint=endpoint,
        p256dh=keys.get("p256dh", ""),
        auth=keys.get("auth", ""),
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def send_push(sub: PushSubscription, payload: dict) -> bool:
    settings = get_settings()
    if not settings.vapid_private_key or not settings.vapid_public_key:
        logger.info("push_skipped vapid_not_configured")
        return False
    try:
        webpush(
            subscription_info={
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            },
            data=json.dumps(payload),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_subject},
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("push_failed error=%s", type(exc).__name__)
        return False