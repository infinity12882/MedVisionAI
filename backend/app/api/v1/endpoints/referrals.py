from __future__ import annotations

import secrets
import string

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.platform import ReferralCode
from app.models.user import User
from app.schemas.extended import ReferralCodeOut

router = APIRouter(prefix="/referrals", tags=["Referrals"])


def _generate_code() -> str:
    return "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


@router.get("/my-code", response_model=ReferralCodeOut)
def get_my_referral_code(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(ReferralCode).filter(ReferralCode.user_id == current_user.id).first()
    if record is None:
        record = ReferralCode(user_id=current_user.id, code=_generate_code())
        db.add(record)
        db.commit()
        db.refresh(record)
    return ReferralCodeOut(code=record.code, uses_count=record.uses_count)
