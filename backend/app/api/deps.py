"""
Reusable FastAPI dependencies: DB session (re-exported), current-user
extraction from the Authorization header, and role-based access guards.
"""
from __future__ import annotations

from collections.abc import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_token(credentials.credentials, token_type="access")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    user = db.get(User, payload.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


def require_role(*allowed_roles: UserRole):
    """Dependency factory: `Depends(require_role(UserRole.ADMIN))`."""

    def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in set(allowed_roles):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"This action requires one of roles: {', '.join(r.value for r in allowed_roles)}",
            )
        return user

    return _guard


require_admin = require_role(UserRole.ADMIN)
require_doctor_or_admin = require_role(UserRole.DOCTOR, UserRole.ADMIN)
require_any_role = require_role(UserRole.ADMIN, UserRole.DOCTOR, UserRole.PATIENT)
