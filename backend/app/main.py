"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.routers import (
    alerts,
    analyze,
    auth,
    content,
    family,
    health,
    push,
    reports,
    scenarios,
    voice,
)
from app.config import get_settings, validate_settings
from app.db import SessionLocal, init_db
from app.logging import new_request_id, request_id_var, setup_logging
from app.models.entities import DrillSession, DrillTurn
from app.schemas.errors import error_detail
from app.services import llm_gateway, rate_limit

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_settings(get_settings())
    init_db()
    llm_gateway.load_prompt.cache_clear()
    result = llm_gateway.check_models_on_startup()
    logger.info("startup_llm_check result=%s", result)
    _cleanup_old_drills()
    _seed_demo_reports_if_empty()
    yield


app = FastAPI(
    title="Scam Shield API",
    version="0.4.0",
    description="Calm scam checker and practice drills for older adults.",
    lifespan=lifespan,
)

settings = get_settings()

MAX_BODY = 5 * 1024 * 1024
UNLIMITED_PATHS = {"/api/health", "/api/health/ready", "/api/health/groq", "/api/health/llm"}


def _too_large_response() -> JSONResponse:
    return JSONResponse(
        status_code=413,
        content=error_detail(
            "body_too_large",
            "That file or message is too large. Please try a smaller one.",
        ),
    )


def _server_error_response() -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_detail(
            "server_error",
            "Something went wrong on our side. Please try again in a minute.",
        ),
    )


class BodySizeLimitMiddleware:
    """Cap request bodies at MAX_BODY even when Content-Length is missing (chunked).

    The body is read up front (at most MAX_BODY bytes) and replayed to the app.
    """

    def __init__(self, app: ASGIApp, max_body: int = MAX_BODY) -> None:
        self.app = app
        self.max_body = max_body

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") in ("GET", "HEAD", "OPTIONS"):
            await self.app(scope, receive, send)
            return
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                if value.isdigit() and int(value) > self.max_body:
                    await _too_large_response()(scope, receive, send)
                    return
                break
        chunks: list[bytes] = []
        total = 0
        more = True
        while more:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body = message.get("body", b"")
            total += len(body)
            if total > self.max_body:
                await _too_large_response()(scope, receive, send)
                return
            chunks.append(body)
            more = message.get("more_body", False)
        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)


# Middleware order: the LAST one added is the OUTERMOST. Registration below is
# innermost-first so CORS wraps everything, including 413/429/500 responses.


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id") or new_request_id()
    token = request_id_var.set(rid)
    try:
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001
            # Handle here (inside CORS) so the browser can read the error body.
            logger.exception("unhandled_error type=%s", type(exc).__name__)
            response = _server_error_response()
        response.headers["x-request-id"] = rid
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        return response
    finally:
        request_id_var.reset(token)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    # CORS preflights must never spend the user's request budget.
    if request.method == "OPTIONS" or not path.startswith("/api/"):
        return await call_next(request)

    ip = rate_limit.client_ip(
        request.client.host if request.client else None,
        request.headers.get("x-forwarded-for"),
    )
    key = f"ip:{ip}"

    # Global API budget (generous) then tighter LLM budget on hot paths.
    if path not in UNLIMITED_PATHS:
        if not rate_limit.ip_limiter().allow(key):
            retry = rate_limit.ip_limiter().retry_after_seconds(key)
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(retry)},
                content=error_detail(
                    "rate_limited",
                    "Too many requests. Please wait a moment.",
                ),
            )

    hot = (
        path.startswith("/api/analyze")
        or path.startswith("/api/drills")
        or path.startswith("/api/voice/speak")
        or path.startswith("/api/voice/transcribe")
    )
    if hot:
        limiter = rate_limit.llm_limiter()
        if not limiter.allow(key):
            retry = limiter.retry_after_seconds(key)
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(retry)},
                content=error_detail(
                    "rate_limited",
                    "Too many requests. Please wait a moment.",
                ),
            )
    return await call_next(request)


app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_detail("error", str(exc.detail)),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    fields = sorted({str(e.get("loc", ["", ""])[-1]) for e in exc.errors()})
    body = error_detail(
        "invalid_input",
        "Please check what you typed and try again.",
    )
    body["error"]["fields"] = fields
    return JSONResponse(status_code=422, content=body)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("unhandled_error type=%s", type(exc).__name__)
    return _server_error_response()


def _cleanup_old_drills() -> None:
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    db = SessionLocal()
    try:
        old = list(db.scalars(select(DrillSession.id).where(DrillSession.created_at < cutoff)))
        if not old:
            return
        db.execute(delete(DrillTurn).where(DrillTurn.session_id.in_(old)))
        db.execute(delete(DrillSession).where(DrillSession.id.in_(old)))
        db.commit()
        logger.info("drill_ttl_cleanup removed=%s", len(old))
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("drill_ttl_cleanup_failed error=%s", type(exc).__name__)
    finally:
        db.close()


def _seed_demo_reports_if_empty() -> None:
    """Ensure Scams near me has something to show for judges and first-run demos."""
    from app.services.demo_seed import seed_reports

    db = SessionLocal()
    try:
        added = seed_reports(db, force=False)
        if added:
            logger.info("demo_reports_seeded count=%s", added)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("demo_seed_failed error=%s", type(exc).__name__)
    finally:
        db.close()


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(auth.router_me)
app.include_router(scenarios.router)
app.include_router(analyze.router)
app.include_router(voice.router)
app.include_router(family.router)
app.include_router(alerts.router)
app.include_router(push.router)
app.include_router(reports.router)
app.include_router(content.router)
