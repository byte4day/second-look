from pydantic import BaseModel, Field


class VapidKeyOut(BaseModel):
    public_key: str | None


class PushSubscribeBody(BaseModel):
    endpoint: str
    keys: dict[str, str] = Field(description="p256dh and auth keys")