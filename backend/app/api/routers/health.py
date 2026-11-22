from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.services import llm_gateway

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health():
    return {"status": "ok"}


@router.get("/api/health/groq")
def health_groq(settings: Settings = Depends(get_settings)):
    return llm_gateway.check_models_on_startup(settings)