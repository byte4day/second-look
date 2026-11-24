"""Passwordless 6-digit code auth and JWT."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from threading import Lock

from jose import JWTError, jwt
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import AlertLog, AuthCode, FamilyContact, PushSubscription, User
from app.services import email_service

ALGORITHM = "HS256"
CODE_TTL_MINUTES = 15
MAX_FAILED_ATTEMPTS = 5

# Failed guesses per email since the last code was issued (in memory; resets on restart).
_failed_lock = Lock()
_failed: dict[str, int] = {}


def _record_failure(email: str) -> int:
    with _failed_lock:
        _failed[email] = _failed.get(email, 0) + 1
        return _failed[email]


def _reset_failures(email: str) -> None:
    with _failed_lock:
        _failed.pop(email, None)


def _too_many_failures(email: str) -> bool:
    with _failed_lock:
        return _failed.get(email, 0) >= MAX_FAILED_ATTEMPTS


def _hash_email(email: str) -> str:
    return email.strip().lower()


def request_code(db: Session, email: str) -> None:
    email = _hash_email(email)
    code = f"{secrets.randbelow(10**6):06d}"
    expires = datetime.now(UTC) + timedelta(minutes=CODE_TTL_MINUTES)
    # Only the newest code is valid: retire older unused codes for this email.
    db.execute(
        update(AuthCode)
        .where(AuthCode.email == email, AuthCode.used.is_(False))
        .values(used=True)
    )
    _reset_failures(email)
    db.add(AuthCode(email=email, code=code, expires_at=expires, used=False))
    db.commit()
    body = (
        f"Your Scam Shield sign-in code is: {code}\n\n"
        "It expires in 15 minutes. If you did not request this, ignore this email."
    )
    try:
        email_service.send_email(email, "Your Scam Shield sign-in code", body)
    except Exception as exc:  # noqa: BLE001
        raise EmailSendError() from exc


class EmailSendError(RuntimeError):
    """The sign-in email could not be sent."""


def verify_code(db: Session, email: str, code: str) -> str | None:
    email = _hash_email(email)
    now = datetime.now(UTC)
    if _too_many_failures(email):
        return None
    row = db.execute(
        select(AuthCode)
        .where(AuthCode.email == email, AuthCode.used.is_(False))
        .order_by(AuthCode.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if row is None:
        _record_failure(email)
        return None
    exp = row.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)
    if exp < now or not secrets.compare_digest(row.code, (code or "").strip()):
        if _record_failure(email) >= MAX_FAILED_ATTEMPTS:
            row.used = True
            db.commit()
        return None
    _reset_failures(email)
    row.used = True
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        user = User(email=email)
        db.add(user)
        db.flush()
    db.commit()
    return create_access_token(user.id, user.email)


def create_access_token(user_id: int, email: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(days=30)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def user_from_token(db: Session, token: str) -> User | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
        token_email = str(payload["email"])
    except (JWTError, KeyError, ValueError, TypeError):
        return None
    user = db.get(User, user_id)
    # A deleted user's id can be reused; the email claim must still match.
    if user is None or user.email != token_email:
        return None
    return user


def delete_user(db: Session, user: User) -> None:
    email = user.email
    user_id = user.id
    db.execute(delete(AlertLog).where(AlertLog.user_id == user_id))
    db.execute(delete(PushSubscription).where(PushSubscription.user_id == user_id))
    for contact in db.scalars(select(FamilyContact).where(FamilyContact.user_id == user_id)):
        db.delete(contact)
    db.execute(delete(AuthCode).where(AuthCode.email == email))
    db.delete(user)
    db.commit()
    _reset_failures(email)


def generate_unsubscribe_token() -> str:
    return secrets.token_urlsafe(32)