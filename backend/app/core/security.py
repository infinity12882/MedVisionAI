"""
Security primitives: password hashing and JWT access/refresh token handling.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(subject: str, role: str, expires_delta: timedelta, token_type: TokenType, secret: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, role: str) -> str:
    return _create_token(
        subject=user_id,
        role=role,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
        secret=settings.JWT_SECRET_KEY,
    )


def create_refresh_token(user_id: str, role: str) -> str:
    return _create_token(
        subject=user_id,
        role=role,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
        secret=settings.JWT_REFRESH_SECRET_KEY,
    )


def decode_token(token: str, token_type: TokenType) -> dict[str, Any]:
    """Decode and validate a JWT. Raises jose.JWTError on any failure."""
    secret = settings.JWT_SECRET_KEY if token_type == "access" else settings.JWT_REFRESH_SECRET_KEY
    payload = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != token_type:
        raise JWTError(f"Expected a {token_type} token but got {payload.get('type')}")
    return payload
