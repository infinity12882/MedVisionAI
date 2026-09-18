from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware
from app.db.session import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure upload directories exist.
    for sub in ("images", "voice", "lab_reports", "articles", "reports"):
        Path(settings.UPLOAD_DIR, sub).mkdir(parents=True, exist_ok=True)

    # Warm up the RAG engine: load a persisted index if present, otherwise build one
    # from whatever is already in the database (no-op on a freshly seeded empty DB).
    try:
        from app.services.rag.engine import get_rag_engine
        from app.services.rag.indexer import reindex_all

        engine = get_rag_engine()
        if not engine.is_ready:
            db = SessionLocal()
            try:
                reindex_all(db)
            finally:
                db.close()
    except Exception as exc:  # never block app startup over RAG warmup issues
        print(f"[startup] RAG warmup skipped: {exc}")

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "MedVision AI — an AI-powered healthcare education platform combining image, voice, "
        "and text understanding with a Retrieval-Augmented Generation medical knowledge base. "
        "AI output is informational only and is not a substitute for a licensed physician."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
