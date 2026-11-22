from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    message_plain: str = Field(min_length=1, max_length=500)
    contact_ids: list[int] = Field(default_factory=list)


class AlertOut(BaseModel):
    sent: int
    skipped: int