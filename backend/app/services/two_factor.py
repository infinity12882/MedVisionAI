"""
TOTP (RFC 6238) two-factor authentication — compatible with Google
Authenticator, Authy, 1Password, etc. Uses pyotp; no external service
required.
"""
from __future__ import annotations

import base64
import io
import json
import secrets

import pyotp
import qrcode

from app.core.config import settings


def generate_secret() -> str:
    return pyotp.random_base32()


def generate_backup_codes(count: int = 8) -> list[str]:
    return [secrets.token_hex(4) for _ in range(count)]


def get_provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=settings.APP_NAME)


def generate_qr_code_data_url(uri: str) -> str:
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


def verify_totp_code(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def verify_backup_code(backup_codes_json: str | None, code: str) -> tuple[bool, str | None]:
    """Returns (is_valid, updated_backup_codes_json_with_code_removed)."""
    if not backup_codes_json:
        return False, backup_codes_json
    codes: list[str] = json.loads(backup_codes_json)
    if code in codes:
        codes.remove(code)
        return True, json.dumps(codes)
    return False, backup_codes_json
