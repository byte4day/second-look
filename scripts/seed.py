#!/usr/bin/env python3
"""Seed demo database with sample area reports judges can show on stage."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db import SessionLocal, init_db
from app.services.demo_seed import seed_reports


def main() -> None:
    force = "--force" in sys.argv
    init_db()
    with SessionLocal() as db:
        added = seed_reports(db, force=force)
    if added:
        print(f"Seeded {added} demo reports.")
    else:
        print("Reports already present; skipped. Use --force to replace.")
    print("Database ready.")


if __name__ == "__main__":
    main()
