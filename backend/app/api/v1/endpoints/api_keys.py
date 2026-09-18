from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.platform import ApiKey
from app.models.user import User
from app.schemas.extended import ApiKeyCreate, ApiKeyCreatedOut, ApiKeyOut
from app.services.api_keys import generate_api_key

router = APIRouter(prefix="/developer/api-keys", tags=["Developer API"])


@router.get("", response_model=list[ApiKeyOut])
def list_api_keys(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ApiKey).filter(ApiKey.user_id == current_user.id).all()


@router.post("", response_model=ApiKeyCreatedOut, status_code=status.HTTP_201_CREATED)
def create_api_key(payload: ApiKeyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    full_key, prefix, hashed = generate_api_key()
    record = ApiKey(user_id=current_user.id, name=payload.name, key_prefix=prefix, hashed_key=hashed)
    db.add(record)
    db.commit()
    db.refresh(record)
    return ApiKeyCreatedOut(id=record.id, name=record.name, key_prefix=prefix, full_key=full_key)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(key_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.get(ApiKey, key_id)
    if record is None or record.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found")
    record.is_active = False
    db.commit()
