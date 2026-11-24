"""Region-specific help content packs."""

from __future__ import annotations

import json

from app.config import get_settings
from app.pathutil import REGIONS_DIR, safe_id


def load_help_now(region: str | None = None) -> dict:
    settings = get_settings()
    region = safe_id(region) or safe_id(settings.region_default) or "generic"
    path = REGIONS_DIR / f"{region}.json"
    if not path.exists():
        path = REGIONS_DIR / "generic.json"
    return json.loads(path.read_text(encoding="utf-8"))