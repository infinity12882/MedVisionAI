"""
Public Developer API — authenticated via `X-API-Key` header instead of a
JWT, intended for third-party integrations (e.g. a hospital's internal
tools calling the symptom checker programmatically). Each key has its own
per-minute rate limit enforced via an in-memory sliding window (same
pattern as app/core/rate_limit.py — see that file's docstring about
swapping to Redis for multi-worker deployments).
"""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.disease import Disease
from app.models.platform import ApiKey
from app.schemas.diagnosis import SymptomCheckRequest
from app.schemas.knowledge import DiseaseListItem, DiseaseOut
from app.services.api_keys import verify_api_key
from app.services.ml.disease_predictor import predict_diseases
from app.services.nlp.symptom_extractor import extract_symptoms

router = APIRouter(prefix="/public", tags=["Public Developer API"])

_request_log: dict[str, list[float]] = defaultdict(list)


def require_api_key(x_api_key: str = Header(..., alias="X-API-Key"), db: Session = Depends(get_db)) -> ApiKey:
    if not x_api_key.startswith("mva_"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key format")

    prefix = x_api_key[:10]
    candidates = db.query(ApiKey).filter(ApiKey.key_prefix == prefix, ApiKey.is_active.is_(True)).all()
    matched = next((k for k in candidates if verify_api_key(x_api_key, k.hashed_key)), None)
    if matched is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or revoked API key")

    now = time.time()
    
    empty_keys = []
    for k, w in _request_log.items():
        while w and w[0] < now - 60:
            w.pop(0)
        if not w:
            empty_keys.append(k)
    for k in empty_keys:
        del _request_log[k]

    window = _request_log[matched.id]
    if len(window) >= matched.requests_per_minute:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "API key rate limit exceeded")
    window.append(now)

    matched.last_used_at = datetime.now(timezone.utc)
    matched.total_requests += 1
    db.commit()

    return matched


@router.get("/diseases", response_model=list[DiseaseListItem])
def public_list_diseases(db: Session = Depends(get_db), api_key: ApiKey = Depends(require_api_key)):
    return db.query(Disease).order_by(Disease.name).limit(200).all()


@router.get("/diseases/{disease_id}", response_model=DiseaseOut)
def public_get_disease(disease_id: str, db: Session = Depends(get_db), api_key: ApiKey = Depends(require_api_key)):
    disease = db.get(Disease, disease_id)
    if disease is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Disease not found")
    return disease


@router.post("/symptom-check")
def public_symptom_check(
    payload: SymptomCheckRequest, db: Session = Depends(get_db), api_key: ApiKey = Depends(require_api_key)
):
    matched_symptoms = extract_symptoms(db, payload.symptoms_text)
    if not matched_symptoms:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No recognized symptoms in input text")
    results = predict_diseases(db, matched_symptoms, top_n=5)
    return {
        "matched_symptoms": [s.name for s in matched_symptoms],
        "results": [{k: v for k, v in r.items() if not k.startswith("_")} for r in results],
    }
