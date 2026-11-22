#!/usr/bin/env python3
"""List Groq models and warn if configured IDs are missing."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import httpx

from app.config import get_settings


def main() -> int:
    settings = get_settings()
    if settings.demo_mode and not settings.groq_api_key:
        print("DEMO_MODE=true and no GROQ_API_KEY — skipping live check.")
        return 0
    if not settings.groq_api_key:
        print("Set GROQ_API_KEY or keep DEMO_MODE=true.")
        return 1
    with httpx.Client(timeout=20.0) as http:
        r = http.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
        )
        r.raise_for_status()
        ids = sorted(m.get("id", "") for m in r.json().get("data", []))
    print(f"Available models ({len(ids)}):")
    for mid in ids:
        print(" ", mid)
    configured = {
        "GROQ_CHAT_MODEL": settings.groq_chat_model,
        "GROQ_FAST_MODEL": settings.groq_fast_model,
        "GROQ_VISION_MODEL": settings.groq_vision_model,
        "GROQ_STT_MODEL": settings.groq_stt_model,
    }
    missing = {k: v for k, v in configured.items() if v and v not in ids}
    if missing:
        print("Missing configured IDs:", missing)
        return 1
    print("All configured model IDs are available.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
