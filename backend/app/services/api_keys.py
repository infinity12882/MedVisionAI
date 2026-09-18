"""
API keys for the Public Developer API. Keys are generated once, shown to
the user a single time, and stored only as a salted hash (same pattern as
passwords) — exactly like Stripe/GitHub/AWS key UX.
"""
from __future__ import annotations

import secrets

from app.core.security import hash_password, verify_password

KEY_PREFIX = "mva"


def generate_api_key() -> tuple[str, str, str]:
    """Returns (full_key_to_show_once, key_prefix_for_display, hashed_key_to_store)."""
    raw = secrets.token_urlsafe(32)
    full_key = f"{KEY_PREFIX}_{raw}"
    display_prefix = f"{KEY_PREFIX}_{raw[:6]}"
    hashed = hash_password(full_key)
    return full_key, display_prefix, hashed


def verify_api_key(provided_key: str, hashed_key: str) -> bool:
    return verify_password(provided_key, hashed_key)
