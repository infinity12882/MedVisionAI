from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.platform import TwoFactorAuth
from app.models.user import User
from app.schemas.extended import TwoFactorSetupOut, TwoFactorStatusOut, TwoFactorVerifyRequest
from app.services.two_factor import (
    generate_backup_codes,
    generate_qr_code_data_url,
    generate_secret,
    get_provisioning_uri,
    verify_totp_code,
)

router = APIRouter(prefix="/2fa", tags=["Two-Factor Authentication"])


@router.get("/status", response_model=TwoFactorStatusOut)
def get_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == current_user.id).first()
    return TwoFactorStatusOut(is_enabled=bool(record and record.is_enabled))


@router.post("/setup", response_model=TwoFactorSetupOut)
def setup_2fa(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    secret = generate_secret()
    backup_codes = generate_backup_codes()

    record = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == current_user.id).first()
    if record is None:
        record = TwoFactorAuth(user_id=current_user.id, totp_secret=secret)
        db.add(record)
    else:
        record.totp_secret = secret
        record.is_enabled = False
    record.backup_codes_json = json.dumps(backup_codes)
    db.commit()

    uri = get_provisioning_uri(secret, current_user.email)
    return TwoFactorSetupOut(secret=secret, qr_code_data_url=generate_qr_code_data_url(uri), backup_codes=backup_codes)


@router.post("/enable")
def enable_2fa(
    payload: TwoFactorVerifyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    record = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == current_user.id).first()
    if record is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Run /2fa/setup first")
    if not verify_totp_code(record.totp_secret, payload.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid verification code")
    record.is_enabled = True
    db.commit()
    return {"detail": "Two-factor authentication enabled"}


@router.post("/disable")
def disable_2fa(
    payload: TwoFactorVerifyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    record = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == current_user.id).first()
    if record is None or not record.is_enabled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Two-factor authentication isn't enabled")
    if not verify_totp_code(record.totp_secret, payload.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid verification code")
    record.is_enabled = False
    db.commit()
    return {"detail": "Two-factor authentication disabled"}
