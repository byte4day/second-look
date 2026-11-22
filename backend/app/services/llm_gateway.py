"""Single gateway for Groq API calls. No hardcoded model IDs."""

from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from collections import OrderedDict
from functools import lru_cache
from threading import Lock, Semaphore
from typing import Any, TypeVar

import httpx
from groq import Groq
from pydantic import BaseModel, ValidationError

from app.config import Settings, get_settings
from app.pathutil import FIXTURES_DIR, PROMPTS_ROOT

logger = logging.getLogger(__name__)

TIMEOUT_S = 20.0
MAX_RETRIES = 4
BACKOFF_BASE = 0.5
CACHE_SIZE = 64

T = TypeVar("T", bound=BaseModel)

_concurrency: Semaphore | None = None
_cache_lock = Lock()
_analyzer_cache: OrderedDict[str, str] = OrderedDict()


def _client(settings: Settings) -> Groq | None:
    if not settings.groq_api_key:
        return None
    return Groq(api_key=settings.groq_api_key, timeout=TIMEOUT_S)


def _get_semaphore(settings: Settings) -> Semaphore:
    global _concurrency
    if _concurrency is None:
        _concurrency = Semaphore(max(1, min(8, settings.rate_limit_llm_per_minute)))
    return _concurrency


def _retry_after_seconds(headers: Any, attempt: int) -> float:
    raw = None
    if headers is not None:
        try:
            raw = headers.get("retry-after")
        except Exception:  # noqa: BLE001
            raw = None
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return BACKOFF_BASE * (2**attempt) + random.uniform(0, 0.25)


def check_models_on_startup(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    if settings.demo_mode:
        return {"ok": True, "demo": True}
    if not settings.groq_api_key:
        logger.warning("GROQ_API_KEY missing; real AI calls will fail")
        return {"ok": False, "error": "missing_api_key"}
    configured = {
        "chat": settings.groq_chat_model,
        "fast": settings.groq_fast_model,
        "vision": settings.groq_vision_model,
        "stt": settings.groq_stt_model,
    }
    try:
        with httpx.Client(timeout=TIMEOUT_S) as http:
            r = http.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            )
            r.raise_for_status()
            ids = {m.get("id") for m in r.json().get("data", [])}
        missing = {role: mid for role, mid in configured.items() if mid and mid not in ids}
        if missing:
            logger.warning("configured_models_missing %s", missing)
        return {"ok": not missing, "missing": missing, "available_count": len(ids)}
    except Exception as exc:  # noqa: BLE001
        logger.warning("groq_startup_check_failed error=%s", type(exc).__name__)
        return {"ok": False, "error": type(exc).__name__}


def _models_chain(settings: Settings, role: str) -> list[str]:
    if role == "fast":
        return [m for m in (settings.groq_fast_model, settings.groq_chat_model) if m]
    if role == "vision":
        return [m for m in (settings.groq_vision_model, settings.groq_chat_model) if m]
    return [m for m in (settings.groq_chat_model, settings.groq_fast_model) if m]


def _parse_json_content(raw: str) -> dict[str, Any] | list[Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)


def _load_fixture(name: str) -> Any:
    path = FIXTURES_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def chat_structured(
    messages: list[dict[str, Any]],
    schema_model: type[T],
    *,
    settings: Settings | None = None,
    role: str = "chat",
    temperature: float = 0.2,
    demo_fixture_name: str | None = None,
    cache_key: str | None = None,
) -> T:
    settings = settings or get_settings()

    if settings.demo_mode and demo_fixture_name:
        return schema_model.model_validate(_load_fixture(demo_fixture_name))

    if cache_key:
        with _cache_lock:
            if cache_key in _analyzer_cache:
                _analyzer_cache.move_to_end(cache_key)
                return schema_model.model_validate_json(_analyzer_cache[cache_key])

    models = _models_chain(settings, role)
    if not models:
        raise RuntimeError("No Groq models configured. Set GROQ_CHAT_MODEL or use DEMO_MODE=true.")

    client = _client(settings)
    if client is None:
        raise RuntimeError("GROQ_API_KEY is not set.")

    schema = schema_model.model_json_schema()
    last_err: Exception | None = None
    sem = _get_semaphore(settings)
    schema_hint = (
        "Return JSON only that matches this schema:\n" + json.dumps(schema)[:4000]
    )

    for model in models:
        for attempt in range(MAX_RETRIES):
            started = time.monotonic()
            try:
                with sem:
                    try:
                        response = client.chat.completions.create(
                            model=model,
                            messages=messages,
                            temperature=temperature,
                            timeout=TIMEOUT_S,
                            response_format={
                                "type": "json_schema",
                                "json_schema": {
                                    "name": schema_model.__name__,
                                    "schema": schema,
                                    "strict": True,
                                },
                            },
                        )
                    except Exception:  # noqa: BLE001
                        response = client.chat.completions.create(
                            model=model,
                            messages=messages
                            + [{"role": "user", "content": schema_hint}],
                            temperature=temperature,
                            timeout=TIMEOUT_S,
                            response_format={"type": "json_object"},
                        )
                content = response.choices[0].message.content or "{}"
                elapsed = time.monotonic() - started
                logger.info(
                    "llm_call model=%s attempt=%s latency_s=%.3f status=ok",
                    model,
                    attempt,
                    elapsed,
                )
                try:
                    parsed = _parse_json_content(content)
                    result = schema_model.model_validate(parsed)
                except (json.JSONDecodeError, ValidationError):
                    response2 = client.chat.completions.create(
                        model=model,
                        messages=messages
                        + [
                            {
                                "role": "user",
                                "content": "Your previous reply was invalid. "
                                + schema_hint,
                            }
                        ],
                        temperature=0,
                        timeout=TIMEOUT_S,
                        response_format={"type": "json_object"},
                    )
                    content2 = response2.choices[0].message.content or "{}"
                    parsed = _parse_json_content(content2)
                    result = schema_model.model_validate(parsed)

                if cache_key:
                    blob = result.model_dump_json()
                    with _cache_lock:
                        _analyzer_cache[cache_key] = blob
                        _analyzer_cache.move_to_end(cache_key)
                        while len(_analyzer_cache) > CACHE_SIZE:
                            _analyzer_cache.popitem(last=False)
                return result
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                status = getattr(exc, "status_code", None)
                logger.info(
                    "llm_call model=%s attempt=%s status=%s",
                    model,
                    attempt,
                    status or "error",
                )
                if status in (429, 500, 502, 503, 504) or "rate" in str(exc).lower():
                    headers = getattr(getattr(exc, "response", None), "headers", {})
                    time.sleep(_retry_after_seconds(headers, attempt))
                    continue
                break
        logger.warning("llm_fallback model=%s failed", model)

    raise RuntimeError(
        "The checker is busy. Please try again in a minute."
        if last_err
        else "The checker is busy. Please try again in a minute."
    )


def chat_text(
    messages: list[dict[str, Any]],
    *,
    settings: Settings | None = None,
    role: str = "chat",
    temperature: float = 0.4,
) -> str:
    settings = settings or get_settings()
    if settings.demo_mode:
        return "I need you to stay on the line. This is urgent."
    models = _models_chain(settings, role)
    if not models:
        raise RuntimeError("No Groq chat models configured.")
    client = _client(settings)
    if client is None:
        raise RuntimeError("GROQ_API_KEY is not set.")
    sem = _get_semaphore(settings)
    last_err: Exception | None = None
    for model in models:
        for attempt in range(MAX_RETRIES):
            try:
                with sem:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        timeout=TIMEOUT_S,
                    )
                return (response.choices[0].message.content or "").strip()
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                status = getattr(exc, "status_code", None)
                if status in (429, 500, 502, 503, 504):
                    time.sleep(_retry_after_seconds({}, attempt))
                    continue
                break
    raise RuntimeError(f"LLM text failed: {last_err}")


def analyzer_cache_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@lru_cache(maxsize=16)
def load_prompt(name: str) -> str:
    path = PROMPTS_ROOT / name
    return path.read_text(encoding="utf-8")


# Test helpers
def _clear_cache_for_tests() -> None:
    with _cache_lock:
        _analyzer_cache.clear()
