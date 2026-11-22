#!/usr/bin/env python3
"""Seed demo database with sample area reports."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import func, select

from app.db import SessionLocal, init_db
from app.models.entities import Report
from app.services.report_service import _ip_hash


def main() -> None:
    init_db()
    with SessionLocal() as db:
        count = db.scalar(select(func.count()).select_from(Report)) or 0
        if count == 0:
            samples = [
                ("bank_imposter", "north"),
                ("bank_imposter", "north"),
                ("bank_imposter", "north"),
                ("parcel_fee", "north"),
                ("tech_support", "south"),
                ("tech_support", "south"),
                ("tech_support", "south"),
            ]
            for scam_type, area in samples:
                db.add(
                    Report(
                        scam_type=scam_type,
                        area=area,
                        text="Anonymous demo report",
                        ip_hash=_ip_hash("127.0.0.1"),
                    )
                )
            db.commit()
            print(f"Seeded {len(samples)} demo reports.")
        else:
            print("Reports already present; skipped.")
    print("Database ready.")


if __name__ == "__main__":
    main()
