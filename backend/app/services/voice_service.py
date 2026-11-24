"""Voice transcription (STT) and speech synthesis (TTS)."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

from groq import Groq

from app.config import get_settings
from app.pathutil import FIXTURES_DIR

logger = logging.getLogger(__name__)

MAX_BYTES = 5 * 1024 * 1024
ORPHEUS_CHAR_LIMIT = 200
DIRECTION_CALLER = "[authoritatively] "
DIRECTION_VICTIM = "[worried] "

# Microsoft neural voices via edge-tts (natural, not robotic espeak).
EDGE_VOICE_CALLER = "en-US-ChristopherNeural"
EDGE_VOICE_VICTIM = "en-US-JennyNeural"


def _stt_client(settings):
    """Speech-to-text goes through the active LLM provider (Unorouter first)."""
    from app.services.llm_gateway import active_provider

    if active_provider(settings) == "unorouter" and settings.unorouter_api_key:
        if not settings.unorouter_stt_model:
            raise RuntimeError("STT not configured")
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.unorouter_api_key,
            base_url=settings.unorouter_base_url,
            timeout=20.0,
            max_retries=1,
        )
        return client, settings.unorouter_stt_model
    if not settings.groq_api_key or not settings.groq_stt_model:
        raise RuntimeError("STT not configured")
    return Groq(api_key=settings.groq_api_key, timeout=20.0), settings.groq_stt_model


def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    settings = get_settings()
    if len(audio_bytes) > MAX_BYTES:
        raise ValueError("audio_too_large")
    if settings.demo_mode:
        path = FIXTURES_DIR / "voice_transcript.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["transcript"]
    client, model = _stt_client(settings)
    result = client.audio.transcriptions.create(
        model=model,
        file=(filename, audio_bytes),
    )
    return (result.text or "").strip()


def _plain_for_speech(text: str) -> str:
    out = text.replace("[fake link]", "a web link")
    out = out.replace("[fake number]", "a phone number")
    out = out.replace("[hidden]", "")
    out = re.sub(r"\s+", " ", out).strip()
    return out


def _chunk_text(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text] if text else []
    parts: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            parts.append(remaining)
            break
        cut = remaining.rfind(" ", 0, limit)
        if cut < 40:
            cut = limit
        parts.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    return [p for p in parts if p]


def _merge_wavs(chunks: list[bytes]) -> bytes:
    if len(chunks) == 1:
        return chunks[0]
    frames = []
    params = None
    for blob in chunks:
        with wave.open(io.BytesIO(blob), "rb") as wf:
            if params is None:
                params = wf.getparams()
            frames.append(wf.readframes(wf.getnframes()))
    assert params is not None
    buf = io.BytesIO()
    with wave.open(buf, "wb") as out:
        out.setparams(params)
        for f in frames:
            out.writeframes(f)
    return buf.getvalue()


def _phone_filter(wav_path: Path, out_path: Path) -> None:
    """Light telephone EQ so it feels like a call, without killing natural voice."""
    if not shutil.which("ffmpeg"):
        out_path.write_bytes(wav_path.read_bytes())
        return
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(wav_path),
            "-af",
            "highpass=f=200,lowpass=f=3800,acompressor=threshold=-18dB:ratio=3,volume=1.25",
            str(out_path),
        ],
        check=True,
        capture_output=True,
    )


def _edge_neural_wav(text: str, persona: str) -> bytes:
    """Natural neural TTS (Microsoft Edge voices)."""
    import edge_tts

    voice = EDGE_VOICE_VICTIM if persona == "victim" else EDGE_VOICE_CALLER
    # Slightly slower / lower for a pushy phone caller.
    rate = "-5%" if persona == "caller" else "+2%"
    pitch = "-8Hz" if persona == "caller" else "+0Hz"

    async def _gen(mp3_path: Path) -> None:
        communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
        await communicate.save(str(mp3_path))

    with tempfile.TemporaryDirectory() as tmp:
        mp3 = Path(tmp) / "speech.mp3"
        wav = Path(tmp) / "speech.wav"
        phone = Path(tmp) / "phone.wav"
        asyncio.run(_gen(mp3))
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp3), str(wav)],
            check=True,
            capture_output=True,
        )
        _phone_filter(wav, phone)
        return phone.read_bytes()


def _espeak_phone_wav(text: str, persona: str) -> bytes:
    """Last-resort local voice if neural TTS is offline."""
    if not shutil.which("espeak-ng") and not shutil.which("espeak"):
        raise RuntimeError("TTS fallback not installed")
    espeak = "espeak-ng" if shutil.which("espeak-ng") else "espeak"
    voice = "en-us+f3" if persona == "victim" else "en-us+m3"
    speed = "145" if persona == "victim" else "125"
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.wav"
        phone = Path(tmp) / "phone.wav"
        subprocess.run(
            # Text goes on stdin so a line starting with "-" can never become an option.
            [espeak, "-v", voice, "-s", speed, "-w", str(raw), "--stdin"],
            input=text.encode("utf-8"),
            check=True,
            capture_output=True,
        )
        _phone_filter(raw, phone)
        return phone.read_bytes()


def _orpheus_wav(text: str, persona: str) -> bytes:
    settings = get_settings()
    if not settings.groq_api_key or not settings.groq_tts_model:
        raise RuntimeError("TTS not configured")
    voice = (
        settings.groq_tts_voice_victim
        if persona == "victim"
        else settings.groq_tts_voice_caller
    )
    direction = DIRECTION_VICTIM if persona == "victim" else DIRECTION_CALLER
    room = ORPHEUS_CHAR_LIMIT - len(direction)
    chunks = _chunk_text(text, max(40, room))
    client = Groq(api_key=settings.groq_api_key, timeout=60.0)
    wavs: list[bytes] = []
    for chunk in chunks:
        spoken = f"{direction}{chunk}"[:ORPHEUS_CHAR_LIMIT]
        response = client.audio.speech.create(
            model=settings.groq_tts_model,
            voice=voice,
            input=spoken,
            response_format="wav",
        )
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            response.write_to_file(tmp.name)
            wavs.append(Path(tmp.name).read_bytes())
    return _merge_wavs(wavs)


def synthesize(text: str, persona: str = "caller") -> tuple[bytes, str]:
    """
    Return (wav_bytes, engine).
    Preference: Groq Orpheus -> Edge neural -> espeak.
    """
    plain = _plain_for_speech(text)
    if not plain:
        raise ValueError("empty_text")
    settings = get_settings()

    if not settings.demo_mode and settings.groq_api_key and settings.groq_tts_model:
        try:
            return _orpheus_wav(plain, persona), "orpheus"
        except Exception as exc:  # noqa: BLE001
            logger.warning("orpheus_tts_failed error=%s", type(exc).__name__)

    try:
        return _edge_neural_wav(plain, persona), "neural"
    except Exception as exc:  # noqa: BLE001
        logger.warning("edge_tts_failed error=%s", type(exc).__name__)

    return _espeak_phone_wav(plain, persona), "phone_fallback"
