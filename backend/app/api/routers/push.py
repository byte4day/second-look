from fastapi import APIRouter, Depends

from app.deps import DbSession, require_user
from app.models.entities import User
from app.schemas.push import PushSubscribeBody, VapidKeyOut
from app.services import push_service

router = APIRouter(prefix="/api/push", tags=["push"])


@router.get("/vapid-key", response_model=VapidKeyOut)
def vapid_key():
    return VapidKeyOut(public_key=push_service.vapid_public_key())


@router.post("/subscribe")
def subscribe(body: PushSubscribeBody, db: DbSession, user: User = Depends(require_user)):
    push_service.subscribe(db, user, body.endpoint, body.keys)
    return {"ok": True}