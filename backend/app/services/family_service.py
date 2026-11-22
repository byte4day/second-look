"""Family contacts with double opt-in."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import FamilyContact, Invitation, User
from app.services import auth_service, email_service


def list_contacts(db: Session, user: User) -> list[FamilyContact]:
    return list(db.scalars(select(FamilyContact).where(FamilyContact.user_id == user.id)))


def invite_contact(db: Session, user: User, name: str, email: str) -> FamilyContact:
    email = email.strip().lower()
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
    body = (
        f"{user.email} invited you to receive Scam Shield alerts for them.\n\n"
        f"Accept: use token {token} in the app (POST /api/family/invitations/{token}/accept).\n"
        "If this was a mistake, ignore this email."
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