from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.errors import error_detail
from app.schemas.voice import VoiceTranscribeOut
from app.services import voice_service

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/transcribe", response_model=VoiceTranscribeOut)
async def transcribe(file: UploadFile = File(...)):
    data = await file.read()
    try:
        text = voice_service.transcribe(data, filename=file.filename or "audio.webm")
    except ValueError as exc:
        if str(exc) == "audio_too_large":
            raise HTTPException(
                status_code=413,
                detail=error_detail("audio_too_large", "Recording is too large. Try a shorter clip."),
            ) from exc
        raise
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=error_detail("stt_unavailable", "Transcription is not available."),
        ) from exc
    return VoiceTranscribeOut(transcript=text)