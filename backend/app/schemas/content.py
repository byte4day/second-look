from pydantic import BaseModel, Field


class ContactEntry(BaseModel):
    name: str
    how: str
    url: str | None = None
    phone: str | None = None


class HelpNowOut(BaseModel):
    id: str
    label: str
    help_now_steps: list[str] = Field(default_factory=list)
    who_to_contact: list[ContactEntry] = Field(default_factory=list)
