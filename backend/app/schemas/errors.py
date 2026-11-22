"""Consistent API error shapes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message_plain: str


class ErrorEnvelope(BaseModel):
    error: ApiError


def error_detail(code: str, message_plain: str) -> dict[str, Any]:
    return {"error": {"code": code, "message_plain": message_plain}}