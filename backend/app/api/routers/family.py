from fastapi import APIRouter, Depends, HTTPException

from app.deps import DbSession, require_user
from app.models.entities import User
from app.schemas.errors import error_detail
from app.schemas.family import FamilyContactCreate, FamilyContactOut
from app.services import family_service

router = APIRouter(prefix="/api/family", tags=["family"])


@router.get("", response_model=list[FamilyContactOut])
def list_family(db: DbSession, user: User = Depends(require_user)):
    return [FamilyContactOut.model_validate(c) for c in family_service.list_contacts(db, user)]


@router.post("", response_model=FamilyContactOut)
def add_family(body: FamilyContactCreate, db: DbSession, user: User = Depends(require_user)):
    contact = family_service.invite_contact(db, user, body.name, body.email)
    return FamilyContactOut.model_validate(contact)


@router.post("/invitations/{token}/accept", response_model=FamilyContactOut)
def accept_invite(token: str, db: DbSession):
    contact = family_service.accept_invitation(db, token)
    if not contact:
        raise HTTPException(
            status_code=400,
            detail=error_detail("invalid_invitation", "This invitation is not valid."),
        )
    return FamilyContactOut.model_validate(contact)


@router.delete("/{contact_id}")
def remove_family(contact_id: int, db: DbSession, user: User = Depends(require_user)):
    if not family_service.delete_contact(db, user, contact_id):
        raise HTTPException(status_code=404, detail=error_detail("not_found", "Contact not found."))
    return {"ok": True}