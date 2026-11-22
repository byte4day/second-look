from fastapi import APIRouter, HTTPException

from app.schemas.analyze import AnalyzeImageRequest, AnalyzeResult, AnalyzeTextRequest
from app.schemas.errors import error_detail
from app.services import analyzer_service

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post("/text", response_model=AnalyzeResult)
def analyze_text(body: AnalyzeTextRequest):
    try:
        return analyzer_service.analyze_text(body.text)
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail=error_detail(
                "checker_busy",
                "The checker is busy. Please try again in a minute.",
            ),
        ) from None


@router.post("/image", response_model=AnalyzeResult)
def analyze_image(body: AnalyzeImageRequest):
    try:
        return analyzer_service.analyze_image(body.image_base64, body.mime_type)
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail=error_detail(
                "checker_busy",
                "The checker is busy. Please try again in a minute.",
            ),
        ) from None
