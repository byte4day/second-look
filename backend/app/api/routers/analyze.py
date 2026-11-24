from fastapi import APIRouter, HTTPException

from app.schemas.analyze import (
    AnalyzeImageRequest,
    AnalyzeResult,
    AnalyzeTextRequest,
    OcrRequest,
    OcrResult,
)
from app.schemas.errors import error_detail
from app.services import analyzer_service, ocr_service

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


@router.post("/ocr", response_model=OcrResult)
def extract_text(body: OcrRequest):
    text = ocr_service.extract_text(body.image_base64, body.mime_type)
    return OcrResult(text=text, found=bool(text.strip()))


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
