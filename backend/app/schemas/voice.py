from pydantic import BaseModel


class VoiceTranscribeOut(BaseModel):
    transcript: str