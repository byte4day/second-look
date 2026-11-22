"""FastAPI application entrypoint."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from app.config import get_settings
from app.db import init_db
from app.logging import new_request_id, request_id_var, setup_logging
from app.schemas.errors import error_detail
from app.services import llm_gateway, rate_limit

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Scam Shield API", version="0.1.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id") or new_request_id()
    token = request_id_var.set(rid)
    try:
        response = await call_next(request)
        response.headers["x-request-id"] = rid
        return response
    finally:
        request_id_var.reset(token)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/analyze") or request.url.path.startswith("/api/drills"):
        ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        key = f"ip:{ip}"
        if not rate_limit.llm_limiter.allow(key):
            return JSONResponse(
                status_code=429,
                content=error_detail("rate_limited", "Too many requests. Please wait a moment."),
            )
    return await call_next(request)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_detail("error", str(exc.detail)),
    )


@app.on_event("startup")
def on_startup():
    init_db()
    result = llm_gateway.check_models_on_startup()
    logger.info("startup_groq_check result=%s", result)


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