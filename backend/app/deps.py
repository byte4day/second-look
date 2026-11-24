"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.services import auth_service

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_optional_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
):
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    user = auth_service.user_from_token(db, token)
    return user


def require_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
):
    user = get_optional_user(db, authorization)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "auth_required",
                    "message_plain": "Please sign in to use this feature.",
                }
            },
        )
    return user


def client_ip(request: Request) -> str:
    from app.services.rate_limit import client_ip as _client_ip

    return _client_ip(
        request.client.host if request.client else None,
        request.headers.get("x-forwarded-for"),
    )
