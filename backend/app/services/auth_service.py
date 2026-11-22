"""Passwordless 6-digit code auth and JWT."""

from __future__ import annotations

import random
import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import AuthCode, User
from app.services import email_service

ALGORITHM = "HS256"
CODE_TTL_MINUTES = 15


def _hash_email(email: str) -> str:
    return email.strip().lower()


def request_code(db: Session, email: str) -> None:
    email = _hash_email(email)
    code = f"{random.randint(0, 999999):06d}"
    expires = datetime.now(UTC) + timedelta(minutes=CODE_TTL_MINUTES)
    db.add(AuthCode(email=email, code=code, expires_at=expires, used=False))
    db.commit()
    body = (
        f"Your Scam Shield sign-in code is: {code}\n\n"
        "It expires in 15 minutes. If you did not request this, ignore this email."
    )
    email_service.send_email(email, "Your Scam Shield sign-in code", body)


def verify_code(db: Session, email: str, code: str) -> str | None:
    email = _hash_email(email)
    now = datetime.now(UTC)
    row = db.execute(
        select(AuthCode)
        .where(AuthCode.email == email, AuthCode.code == code, AuthCode.used.is_(False))
        .order_by(AuthCode.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    exp = row.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)
    if not row or exp < now:
        return None
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
    except (JWTError, KeyError, ValueError):
        return None
    return db.get(User, user_id)


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()


def generate_unsubscribe_token() -> str:
    return secrets.token_urlsafe(32)