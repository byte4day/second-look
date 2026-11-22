from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class FamilyContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr


class FamilyContactOut(BaseModel):
    id: int
    name: str
    email: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InvitationAcceptBody(BaseModel):
    token: str