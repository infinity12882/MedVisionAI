from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.family import FamilyMember
from app.models.user import User
from app.schemas.extended import FamilyMemberCreate, FamilyMemberOut

router = APIRouter(prefix="/family", tags=["Family Accounts"])


@router.get("", response_model=list[FamilyMemberOut])
def list_family_members(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(FamilyMember).filter(FamilyMember.guardian_user_id == current_user.id).all()


@router.post("", response_model=FamilyMemberOut, status_code=status.HTTP_201_CREATED)
def add_family_member(
    payload: FamilyMemberCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    member = FamilyMember(guardian_user_id=current_user.id, **payload.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.put("/{member_id}", response_model=FamilyMemberOut)
def update_family_member(
    member_id: str,
    payload: FamilyMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = db.get(FamilyMember, member_id)
    if member is None or member.guardian_user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Family member not found")
    for field, value in payload.model_dump().items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_family_member(
    member_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    member = db.get(FamilyMember, member_id)
    if member is None or member.guardian_user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Family member not found")
    db.delete(member)
    db.commit()
