"""Voice transcription via Groq STT."""

from __future__ import annotations

import json

from groq import Groq

from app.config import get_settings
from app.pathutil import FIXTURES_DIR

MAX_BYTES = 5 * 1024 * 1024


def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    settings = get_settings()
    if len(audio_bytes) > MAX_BYTES:
        raise ValueError("audio_too_large")
    if settings.demo_mode:
        path = FIXTURES_DIR / "voice_transcript.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["transcript"]
    if not settings.groq_api_key or not settings.groq_stt_model:
        raise RuntimeError("STT not configured")
    client = Groq(api_key=settings.groq_api_key, timeout=20.0)
    result = client.audio.transcriptions.create(
        model=settings.groq_stt_model,
        file=(filename, audio_bytes),
    )
    if not settings.store_transcripts:
        pass  # do not persist
    return (result.text or "").strip()