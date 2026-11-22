"""Pydantic schemas for API request/response."""

from app.schemas.alert import AlertCreate, AlertOut
from app.schemas.analyze import (
    AnalyzeImageRequest,
    AnalyzeResult,
    AnalyzeTextRequest,
    ReasonItem,
    RedFlag,
)
from app.schemas.auth import RequestCodeBody, TokenResponse, UserOut, VerifyCodeBody
from app.schemas.content import HelpNowOut
from app.schemas.drill import (
    DebriefOut,
    DrillCreate,
    DrillFinishRequest,
    DrillSessionOut,
    DrillTurnOut,
    DrillTurnRequest,
    ScenarioOut,
)
from app.schemas.errors import ApiError, error_detail
from app.schemas.family import FamilyContactCreate, FamilyContactOut
from app.schemas.push import PushSubscribeBody, VapidKeyOut
from app.schemas.report import ReportCreate, ReportSummaryOut
from app.schemas.voice import VoiceTranscribeOut

__all__ = [
    "ApiError",
    "error_detail",
    "AnalyzeResult",
    "ReasonItem",
    "RedFlag",
    "AnalyzeTextRequest",
    "AnalyzeImageRequest",
    "RequestCodeBody",
    "VerifyCodeBody",
    "TokenResponse",
    "UserOut",
    "DrillCreate",
    "DrillTurnRequest",
    "DrillFinishRequest",
    "DrillSessionOut",
    "DrillTurnOut",
    "DebriefOut",
    "ScenarioOut",
    "FamilyContactCreate",
    "FamilyContactOut",
    "AlertCreate",
    "AlertOut",
    "PushSubscribeBody",
    "VapidKeyOut",
    "ReportCreate",
    "ReportSummaryOut",
    "VoiceTranscribeOut",
    "HelpNowOut",
]
