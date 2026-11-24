from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.db import ping_db
from app.pathutil import REGIONS_DIR
from app.services import llm_gateway, ocr_service

router = APIRouter(tags=["health"])

APP_VERSION = "0.4.0"


@router.get("/api/health")
def health(settings: Settings = Depends(get_settings)):
    db_ok = ping_db()
    region = settings.region_default
    region_ok = (REGIONS_DIR / f"{region}.json").exists() or (REGIONS_DIR / "generic.json").exists()
    ocr_ok = True
    try:
        ocr_service._engine()  # warm / verify import path
    except Exception:  # noqa: BLE001
        ocr_ok = False

    status = "ok" if db_ok and region_ok else "degraded"
    body = {
        "status": status,
        "version": APP_VERSION,
        "demo_mode": settings.demo_mode,
        "region_default": region,
        "checks": {
            "database": db_ok,
            "region_pack": region_ok,
            "ocr": ocr_ok,
            "llm_provider": llm_gateway.active_provider(settings),
            "llm_key_present": bool(llm_gateway.provider_key(settings)),
            "groq_key_present": bool(settings.groq_api_key),
            "vision_model_configured": llm_gateway.vision_available(settings),
        },
        "features": {
            "analyze": True,
            "analyze_ocr": ocr_ok,
            "drills": True,
            "voice_stt": settings.demo_mode
            or bool(settings.unorouter_api_key and settings.unorouter_stt_model)
            or bool(settings.groq_api_key and settings.groq_stt_model),
            "voice_tts": True,
            "family": True,
            "reports": True,
        },
    }
    return JSONResponse(body, status_code=200 if status == "ok" else 503)


@router.get("/api/health/llm")
@router.get("/api/health/groq")
def health_llm(settings: Settings = Depends(get_settings)):
    return llm_gateway.check_models_on_startup(settings)


@router.get("/api/health/ready")
def ready(settings: Settings = Depends(get_settings)):
    """Readiness probe for demos and containers."""
    if not ping_db():
        return JSONResponse(
            {"ready": False, "reason": "database"},
            status_code=503,
        )
    if not settings.demo_mode and not llm_gateway.provider_key(settings):
        return JSONResponse(
            {"ready": False, "reason": "missing_llm_key"},
            status_code=503,
        )
    return {"ready": True, "version": APP_VERSION, "demo_mode": settings.demo_mode}
