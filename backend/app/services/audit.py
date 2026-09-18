from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.system import AuditLog


def write_audit_log(
    db: Session,
    *,
    user_id: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    detail: str | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            detail=detail,
        )
    )
    db.commit()
