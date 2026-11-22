from fastapi import APIRouter, Depends, HTTPException

from app.deps import DbSession, require_user
from app.models.entities import User
from app.schemas.alert import AlertCreate, AlertOut
from app.schemas.errors import error_detail
from app.services import alert_service

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.post("", response_model=AlertOut)
def send_alert(body: AlertCreate, db: DbSession, user: User = Depends(require_user)):
    try:
        sent, skipped = alert_service.send_alerts(db, user, body.message_plain, body.contact_ids)
    except ValueError as exc:
        if str(exc) == "rate_limited":
            raise HTTPException(
                status_code=429,
                detail=error_detail(
                    "alert_rate_limited",
                    "You can send at most 3 alerts per hour.",
                ),
            ) from exc
        raise
    return AlertOut(sent=sent, skipped=skipped)


@router.post("/test")
def test_alert(db: DbSession, user: User = Depends(require_user)):
    try:
        alert_service.send_alerts(
            db,
            user,
            "This is a test alert from Scam Shield.",
            contact_ids=None,
        )
    except ValueError as exc:
        if str(exc) == "rate_limited":
            raise HTTPException(
                status_code=429,
                detail=error_detail("alert_rate_limited", "You can send at most 3 alerts per hour."),
            ) from exc
    return {"ok": True}