"""Local OCR so photo Check works without a Groq vision model."""

from __future__ import annotations

import base64
import io
import logging
import re
from functools import lru_cache

logger = logging.getLogger(__name__)

_MIN_CHARS = 12
# Refuse decompression bombs: a tiny PNG can claim a huge canvas.
MAX_PIXELS = 25_000_000


@lru_cache(maxsize=1)
def _engine():
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR()


def extract_text(image_base64: str, mime_type: str = "image/jpeg") -> str:
    """Return visible text from an image, or empty string on failure."""
    try:
        import numpy as np
        from PIL import Image

        raw = base64.b64decode(image_base64, validate=False)
        img = Image.open(io.BytesIO(raw))  # lazy: reads the header only
        w, h = img.size
        if w * h > MAX_PIXELS:
            logger.warning("ocr_rejected reason=too_many_pixels w=%s h=%s", w, h)
            return ""
        # Cap long screenshots so OCR stays snappy on phones.
        max_side = 1600
        img.draft("RGB", (max_side, max_side))  # JPEG: decode at reduced size
        img.thumbnail((max_side, max_side))
        img = img.convert("RGB")
        result, _elapse = _engine()(np.array(img))
        if not result:
            return ""
        lines = [str(item[1]).strip() for item in result if item and item[1]]
        lines = [_clean_line(ln) for ln in lines]
        lines = [ln for ln in lines if ln and not _is_chrome(ln)]
        text = "\n".join(lines)
        text = re.sub(r"[ \t]+", " ", text).strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        if len(re.sub(r"\s+", "", text)) < _MIN_CHARS:
            return ""
        return text
    except Exception as exc:  # noqa: BLE001
        logger.warning("ocr_failed error=%s", type(exc).__name__)
        return ""


_CHROME = re.compile(
    r"^(text message|report junk|today\b.*|space|return|the sender is not in your contact list\.?|"
    r"i'?m|the|123|[0-9]{1,2}:[0-9]{2}|[<>]|msg & data rates may apply\.?)$",
    re.IGNORECASE,
)


def _clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip(" \t\r\n>|")


def _is_chrome(line: str) -> bool:
    return bool(_CHROME.match(line.strip()))
