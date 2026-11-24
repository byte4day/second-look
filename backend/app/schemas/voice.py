from typing import Literal

from pydantic import BaseModel, Field


class VoiceTranscribeOut(BaseModel):
    transcript: str


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=600)
    persona: Literal["caller", "victim"] = "caller"
