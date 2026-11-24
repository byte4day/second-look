"""Family contacts with double opt-in."""

from __future__ import annotations

import re
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import FamilyContact, Invitation, User
from app.services import auth_service, email_service


def list_contacts(db: Session, user: User) -> list[FamilyContact]:
    return list(db.scalars(select(FamilyContact).where(FamilyContact.user_id == user.id)))


INVITES_PER_DAY = 5
_URLISH = re.compile(r"(?:https?://|www\.)\S*|\b\S+\.(?:com|net|org|co|uk|io|xyz|info|ru|top)\S*", re.I)


class InviteLimitError(ValueError):
    pass


def clean_contact_name(name: str) -> str:
    """Names go into an email we send, so links and odd characters are removed."""
    name = _URLISH.sub("", name)
    name = re.sub(r"[^\w .'\-]", "", name, flags=re.UNICODE)
    name = re.sub(r"\s+", " ", name).strip()[:60]
    return name or "there"


def invite_contact(db: Session, user: User, name: str, email: str) -> FamilyContact:
    email = email.strip().lower()
    since = datetime.now(UTC) - timedelta(days=1)
    recent = db.scalar(
        select(func.count()).select_from(FamilyContact).where(
            FamilyContact.user_id == user.id, FamilyContact.created_at >= since
        )
    ) or 0
    if recent >= INVITES_PER_DAY:
        raise InviteLimitError("invite_limit")
    name = clean_contact_name(name)
    contact = FamilyContact(user_id=user.id, name=name, email=email, status="waiting")
    db.add(contact)
    db.flush()
    token = secrets.token_urlsafe(32)
    unsub = auth_service.generate_unsubscribe_token()
    inv = Invitation(
        contact_id=contact.id,
        token=token,
        expires_at=datetime.now(UTC) + timedelta(days=7),
        unsubscribe_token=unsub,
    )
    db.add(inv)
    db.commit()
    db.refresh(contact)
    base = get_settings().public_app_url.rstrip("/")
    accept_url = f"{base}/invite/{token}"
    body = (
        f"Hello {name},\n\n"
        f"{user.email} invited you to receive short Scam Shield alerts if they need help.\n\n"
        f"Open this link to accept (expires in 7 days):\n{accept_url}\n\n"
        "If this was a mistake, ignore this email. You will not get alerts until you accept."
    )
    email_service.send_email(email, "Scam Shield family alert invitation", body)
    return contact


def accept_invitation(db: Session, token: str) -> FamilyContact | None:
    inv = db.execute(select(Invitation).where(Invitation.token == token)).scalar_one_or_none()
    if not inv or inv.accepted_at is not None:
        return None
    exp = inv.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)
    if exp < datetime.now(UTC):
        return None
    inv.accepted_at = datetime.now(UTC)
    contact = db.get(FamilyContact, inv.contact_id)
    if contact:
        contact.status = "accepted"
    db.commit()
    return contact


def delete_contact(db: Session, user: User, contact_id: int) -> bool:
    contact = db.get(FamilyContact, contact_id)
    if not contact or contact.user_id != user.id:
        return False
    if contact.invitation:
        db.delete(contact.invitation)
    db.delete(contact)
    db.commit()
    return True