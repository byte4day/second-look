from fastapi import APIRouter, Query

from app.schemas.content import HelpNowOut
from app.services import content_service

router = APIRouter(prefix="/api/content", tags=["content"])


@router.get("/help-now", response_model=HelpNowOut)
def help_now(region: str | None = Query(default=None)):
    data = content_service.load_help_now(region)
    return HelpNowOut.model_validate(data)