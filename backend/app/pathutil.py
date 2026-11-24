"""Shared paths into app data and prompts."""

import re
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
DATA_ROOT = APP_ROOT / "data"
PROMPTS_ROOT = APP_ROOT / "prompts"
SCENARIOS_DIR = DATA_ROOT / "scenarios"
REGIONS_DIR = DATA_ROOT / "regions"
FIXTURES_DIR = DATA_ROOT / "demo_fixtures"


_SAFE_ID = re.compile(r"^[a-z0-9_-]{1,64}$")


def safe_id(value: str | None) -> str | None:
    """Return value only if it is a plain slug (no paths), else None."""
    if value is None:
        return None
    value = value.strip().lower()
    return value if _SAFE_ID.fullmatch(value) else None
