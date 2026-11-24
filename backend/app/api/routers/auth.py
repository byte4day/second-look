from fastapi import APIRouter, Depends, HTTPException

from app.deps import DbSession, require_user
from app.models.entities import User
from app.schemas.auth import RequestCodeBody, TokenResponse, UserOut, VerifyCodeBody
from app.schemas.errors import error_detail
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/request-code")
def request_code(body: RequestCodeBody, db: DbSession):
    try:
        auth_service.request_code(db, body.email)
    except auth_service.EmailSendError:
        raise HTTPException(
            status_code=502,
            detail=error_detail(
                "email_failed",
                "We could not send the email just now. Please try again in a minute.",
            ),
        ) from None
    return {"ok": True}


@router.post("/verify-code", response_model=TokenResponse)
def verify_code(body: VerifyCodeBody, db: DbSession):
    token = auth_service.verify_code(db, body.email, body.code)
    if not token:
        raise HTTPException(status_code=400, detail=error_detail("invalid_code", "That code is not valid."))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me_wrong():
    raise HTTPException(status_code=404, detail=error_detail("not_found", "Use GET /api/me"))


router_me = APIRouter(tags=["me"])


@router_me.get("/api/me", response_model=UserOut)
def me(user: User = Depends(require_user)):
    return UserOut.model_validate(user)


@router_me.delete("/api/me")
def delete_me(db: DbSession, user: User = Depends(require_user)):
    auth_service.delete_user(db, user)
    return {"ok": True}