from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from app.schemas.errors import error_detail
from app.schemas.voice import SpeakRequest, VoiceTranscribeOut
from app.services import voice_service

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/transcribe", response_model=VoiceTranscribeOut)
async def transcribe(file: UploadFile = File(...)):
    data = await file.read()
    try:
        # The provider SDK call is blocking; keep it off the event loop.
        text = await run_in_threadpool(
            voice_service.transcribe, data, filename=file.filename or "audio.webm"
        )
    except ValueError as exc:
        if str(exc) == "audio_too_large":
            raise HTTPException(
                status_code=413,
                detail=error_detail(
                    "audio_too_large",
                    "Recording is too large. Try a shorter clip.",
                ),
            ) from exc
        raise
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=error_detail("stt_unavailable", "Transcription is not available."),
        ) from exc
    return VoiceTranscribeOut(transcript=text)


@router.post("/speak")
def speak(body: SpeakRequest):
    try:
        audio, engine = voice_service.synthesize(body.text, body.persona)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=error_detail("empty_text", "There is nothing to read aloud."),
        ) from None
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail=error_detail(
                "tts_unavailable",
                "Caller voice is not available right now.",
            ),
        ) from None
    return Response(
        content=audio,
        media_type="audio/wav",
        headers={
            "X-Scam-Shield-TTS-Engine": engine,
            "Cache-Control": "no-store",
        },
    )
