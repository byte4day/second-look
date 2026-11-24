from typing import Literal

from pydantic import BaseModel, Field

# Public summaries show these values, so they must come from a fixed list,
# never free text (a scammer could post "Call 0800... for refund" as a category).
ScamType = Literal["phone", "text", "email", "doorstep", "online", "other"]
Area = Literal["england", "scotland", "wales", "northern_ireland"]


class ReportCreate(BaseModel):
    scam_type: ScamType
    area: Area
    text: str | None = Field(default=None, max_length=200)


class ReportSummaryItem(BaseModel):
    scam_type: str
    count: int


class ReportSummaryOut(BaseModel):
    area: str | None = None
    items: list[ReportSummaryItem]
    total: int
    enough: bool = True
    message_plain: str | None = None
    label: str = "reported by users, not verified"
    period_days: int = 7
