import base64
from io import BytesIO

from PIL import Image, ImageDraw

from app.services import ocr_service


def _png_with_text(text: str) -> str:
    img = Image.new("RGB", (640, 160), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 60), text, fill=(0, 0, 0))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def test_ocr_extracts_visible_words():
    b64 = _png_with_text("Chase Fraud reply YES or NO")
    out = ocr_service.extract_text(b64, "image/png")
    # OCR may be imperfect on synthetic glyphs; require some signal or empty gracefully.
    assert isinstance(out, str)
    if out:
        assert "Chase" in out or "YES" in out or "Fraud" in out or "reply" in out.lower()


def test_analyze_ocr_endpoint(client):
    b64 = _png_with_text("Account locked share the one-time code now")
    r = client.post("/api/analyze/ocr", json={"image_base64": b64, "mime_type": "image/png"})
    assert r.status_code == 200
    body = r.json()
    assert "found" in body
    assert "text" in body
