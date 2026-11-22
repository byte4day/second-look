from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    scam_type: str = Field(min_length=1, max_length=64)
    area: str = Field(min_length=1, max_length=64)
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
