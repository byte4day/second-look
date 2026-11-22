from fastapi import APIRouter, HTTPException, Query, Request

from app.deps import DbSession, client_ip
from app.schemas.errors import error_detail
from app.schemas.report import ReportCreate, ReportSummaryItem, ReportSummaryOut
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("")
def create_report(body: ReportCreate, db: DbSession, request: Request):
    ip = client_ip(request)
    try:
        report_service.create_report(db, body.scam_type, body.area, body.text, ip)
    except ValueError as exc:
        code = str(exc)
        if code == "rate_limited":
            raise HTTPException(
                status_code=429,
                detail=error_detail("rate_limited", "You have sent enough reports for today."),
            ) from None
        if code == "personal_data":
            raise HTTPException(
                status_code=400,
                detail=error_detail(
                    "personal_data",
                    "Please remove phone numbers, emails, or card numbers from the report.",
                ),
            ) from None
        raise
    return {"ok": True}


@router.get("/summary", response_model=ReportSummaryOut)
def report_summary(db: DbSession, area: str | None = Query(default=None)):
    data = report_service.weekly_summary(db, area=area)
    return ReportSummaryOut(
        area=data.get("area"),
        items=[ReportSummaryItem(**i) for i in data["items"]],
        total=data["total"],
        enough=data["enough"],
        message_plain=data.get("message_plain"),
        label=data.get("label", "reported by users, not verified"),
        period_days=data["period_days"],
    )
