"""Shared paths into app data and prompts."""

from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
DATA_ROOT = APP_ROOT / "data"
PROMPTS_ROOT = APP_ROOT / "prompts"
SCENARIOS_DIR = DATA_ROOT / "scenarios"
REGIONS_DIR = DATA_ROOT / "regions"
FIXTURES_DIR = DATA_ROOT / "demo_fixtures"
