"""
Shared file-upload handling: extension/size validation and safe storage
under UPLOAD_DIR, organized by category and user.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".webm", ".ogg"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}


def _validate_and_save(file: UploadFile, subdir: str, allowed_extensions: set[str]) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed_extensions:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unsupported file type '{suffix}'. Allowed: {', '.join(sorted(allowed_extensions))}",
        )

    contents = file.file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"File exceeds the {settings.MAX_UPLOAD_MB}MB upload limit")
    if len(contents) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uploaded file is empty")

    # Hook: in production, run `contents` through a malware/AV scanner (e.g. ClamAV) here
    # before writing to disk, and reject on a positive match.

    target_dir = Path(settings.UPLOAD_DIR) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    target_path = target_dir / filename
    target_path.write_bytes(contents)

    return str(target_path)


def save_image(file: UploadFile) -> str:
    return _validate_and_save(file, "images", ALLOWED_IMAGE_EXTENSIONS)


def save_voice(file: UploadFile) -> str:
    return _validate_and_save(file, "voice", ALLOWED_AUDIO_EXTENSIONS)


def save_lab_report(file: UploadFile) -> str:
    return _validate_and_save(file, "lab_reports", ALLOWED_IMAGE_EXTENSIONS | {".pdf"})


def save_article(file: UploadFile) -> str:
    return _validate_and_save(file, "articles", ALLOWED_DOCUMENT_EXTENSIONS)
