"""
Centralized application configuration.

All settings are loaded from environment variables (via a `.env` file in
local development, or real environment variables in production / Docker).
Nothing here is hardcoded — secrets must never be committed to source control.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]

def _find_env_files():
    candidates = [
        Path(__file__).resolve().parents[3] / '.env',
        Path(__file__).resolve().parents[3] / 'backend' / '.env',
        Path(__file__).resolve().parents[2] / '.env',  # /app/.env in Docker
        Path('/app/.env'),
        Path('/app/backend/.env'),
    ]
    return tuple(str(p) for p in candidates if p.exists()) or ()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "MedVision AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("DEBUG", mode="before")
    @classmethod
    def _parse_debug(cls, v):
        if isinstance(v, str) and v.lower() in {"release", "production", "prod"}:
            return False
        return v

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./medvision_dev.db"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # --- JWT ---
    JWT_SECRET_KEY: str = "dev-only-insecure-secret-change-me"
    JWT_REFRESH_SECRET_KEY: str = "dev-only-insecure-refresh-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # --- Gemini ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # --- Stripe billing (optional — preview mode without a key) ---
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # --- Free-tier usage limits ---
    FREE_TIER_DAILY_CHAT_LIMIT: int = 15

    # --- RAG ---
    FAISS_INDEX_DIR: str = "./app/ml_artifacts/faiss_index"
    EMBEDDING_BACKEND: str = "tfidf"

    # --- Storage ---
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 15

    # --- Vision demo model ---
    VISION_MODEL_PATH: str = "./app/ml_artifacts/vision_demo_model.joblib"

    # --- Maps / Yandex ---
    YANDEX_API_KEY: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    EMAILS_FROM_EMAIL: str = "no-reply@medvision.ai"

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
