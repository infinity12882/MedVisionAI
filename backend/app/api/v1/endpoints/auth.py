from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import DoctorProfile, PatientProfile, User, UserRole
from app.schemas.auth import (
    EmailVerifyRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    # Self-registration as ADMIN is never allowed — admins are promoted by an existing admin.
    role = UserRole.PATIENT if payload.role == UserRole.ADMIN else payload.role

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=role,
        email_verification_token=secrets.token_urlsafe(32),
    )
    db.add(user)
    db.flush()  # get user.id before creating the profile row

    if role == UserRole.DOCTOR:
        db.add(DoctorProfile(user_id=user.id))
    else:
        db.add(PatientProfile(user_id=user.id))

    if payload.referral_code:
        from app.models.platform import Referral, ReferralCode

        ref_code = db.query(ReferralCode).filter(ReferralCode.code == payload.referral_code.upper()).first()
        if ref_code and ref_code.user_id != user.id:
            db.add(Referral(referrer_id=ref_code.user_id, referred_user_id=user.id))
            ref_code.uses_count += 1

    db.commit()
    db.refresh(user)

    write_audit_log(
        db, user_id=user.id, action="auth.register", resource_type="user", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    # In production this token would be emailed via the SMTP service (app/services/email.py).
    return user


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated")

    from app.models.platform import TwoFactorAuth
    from app.services.two_factor import verify_backup_code, verify_totp_code

    two_fa = db.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user.id).first()
    if two_fa and two_fa.is_enabled:
        if not payload.totp_code:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "2FA_REQUIRED")
        valid = verify_totp_code(two_fa.totp_secret, payload.totp_code)
        if not valid:
            valid, updated_codes = verify_backup_code(two_fa.backup_codes_json, payload.totp_code)
            if valid:
                two_fa.backup_codes_json = updated_codes
                db.commit()
        if not valid:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid two-factor authentication code")

    write_audit_log(
        db, user_id=user.id, action="auth.login", resource_type="user", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return TokenPair(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id, user.role.value),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token, token_type="refresh")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    user = db.get(User, decoded.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    return TokenPair(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id, user.role.value),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/verify-email")
def verify_email(payload: EmailVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email_verification_token == payload.token).first()
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid verification token")
    user.is_email_verified = True
    user.email_verification_token = None
    db.commit()
    return {"detail": "Email verified successfully"}


@router.post("/password-reset/request")
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    from datetime import datetime, timedelta, timezone

    user = db.query(User).filter(User.email == payload.email).first()
    # Always return 200 regardless of whether the email exists, to avoid account enumeration.
    if user is not None:
        user.password_reset_token = secrets.token_urlsafe(32)
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
        # In production: send user.password_reset_token via email.
    return {"detail": "If that email is registered, a reset link has been sent."}


@router.post("/password-reset/confirm")
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    from datetime import datetime, timezone

    user = db.query(User).filter(User.password_reset_token == payload.token).first()
    if user is None or user.password_reset_expires is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token")
    if user.password_reset_expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reset token has expired")

    user.hashed_password = hash_password(payload.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    return {"detail": "Password has been reset successfully"}
