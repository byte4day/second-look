#!/usr/bin/env python3
"""Check the active AI provider (Unorouter first, Groq fallback) and its model IDs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.config import get_settings  # noqa: E402
from app.services.llm_gateway import active_provider, check_models_on_startup  # noqa: E402


def main() -> int:
    settings = get_settings().model_copy(update={"demo_mode": False})
    print(f"provider: {active_provider(settings)}")
    result = check_models_on_startup(settings)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
