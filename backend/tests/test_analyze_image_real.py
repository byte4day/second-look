"""Photo Check path: OCR on a real smishing screenshot when present."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

SHOTS = [
    Path.home() / "Downloads" / "scammer-message.png",
    Path(__file__).resolve().parents[2] / "docs" / "samples" / "scammer-message.png",
]


def _load_b64() -> tuple[str, str, Path] | None:
    for path in SHOTS:
        if path.exists() and path.stat().st_size > 1000:
            return base64.b64encode(path.read_bytes()).decode(), "image/png", path
    return None


@pytest.mark.skipif(_load_b64() is None, reason="No screenshot available for OCR integration")
def test_analyze_image_reads_scam_screenshot(client):
    loaded = _load_b64()
    assert loaded is not None
    b64, mime, path = loaded
    r = client.post("/api/analyze/image", json={"image_base64": b64, "mime_type": mime})
    assert r.status_code == 200
    body = r.json()
    assert body["risk_level"] in {"likely_scam", "suspicious"}
    assert body["reasons"]
    assert "scammer-message" in path.name


def test_ocr_endpoint_contract(client):
    # 1x1 png
    tiny = base64.b64encode(
        bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
            "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
        )
    ).decode()
    r = client.post("/api/analyze/ocr", json={"image_base64": tiny, "mime_type": "image/png"})
    assert r.status_code == 200
    assert set(r.json()) >= {"text", "found"}
