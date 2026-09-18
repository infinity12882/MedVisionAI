"""
Startup-platform infrastructure: a public developer API (with per-key
rate limiting), a referral/growth-loop system, a subscription/billing
scaffold (Stripe — works in a graceful "preview mode" without a real key,
same pattern as the Gemini integration), and TOTP-based two-factor auth.
"""
from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ApiKey(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "api_keys"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False, index=True)  # shown to user, e.g. "mva_3f9a"
    hashed_key: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requests_per_minute: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ReferralCode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "referral_codes"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    uses_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Referral(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "referrals"

    referrer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    referred_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    reward_granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


class Subscription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "subscriptions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    tier: Mapped[SubscriptionTier] = mapped_column(Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UsageCounter(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "usage_counters"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    chat_messages_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class TwoFactorAuth(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "two_factor_auth"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    totp_secret: Mapped[str] = mapped_column(String(64), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    backup_codes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
