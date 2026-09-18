from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.medication import Medication
from app.models.prediction import MedicalHistory, Prediction, PredictionSource
from app.models.user import User
from app.schemas.diagnosis import (
    DiseasePredictionItem,
    ExplainabilityInfo,
    PredictionOut,
    SymptomCheckRequest,
)
from app.services.ml.disease_predictor import overall_risk_level, predict_diseases
from app.services.nlp.symptom_extractor import extract_symptoms

router = APIRouter(prefix="/diagnosis", tags=["Diagnosis"])


def _attach_medicine_category(db: Session, results: list[dict]) -> None:
    for item in results:
        if not item.get("disease_name"):
            continue
        match = (
            db.query(Medication)
            .filter(Medication.linked_disease_tags.ilike(f"%{item['disease_name']}%"))
            .first()
        )
        if match:
            item["medicine_category"] = match.drug_category


def _build_prediction_out(prediction: Prediction) -> PredictionOut:
    results_raw = json.loads(prediction.results_json)
    detected = json.loads(prediction.detected_symptoms_json or "[]")
    importance = json.loads(prediction.feature_importance_json or "{}")

    return PredictionOut(
        id=prediction.id,
        source=prediction.source,
        family_member_id=prediction.family_member_id,
        input_summary=prediction.input_summary,
        results=[DiseasePredictionItem(**{k: v for k, v in r.items() if not k.startswith("_")}) for r in results_raw],
        top_disease=prediction.top_disease,
        top_probability=prediction.top_probability,
        risk_level=prediction.risk_level,
        recommended_specialist=prediction.recommended_specialist,
        recovery_estimate_days=prediction.recovery_estimate_days,
        explainability=ExplainabilityInfo(
            matched_symptoms=detected,
            feature_importance=importance,
            confidence_note=(
                "Higher probability means more of your reported symptoms, weighted by how "
                "specific they are, matched this condition in the knowledge base."
            ),
        ),
        created_at=prediction.created_at,
    )


@router.post("/text", response_model=PredictionOut)
def check_symptoms(
    payload: SymptomCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    matched_symptoms = extract_symptoms(db, payload.symptoms_text)
    if not matched_symptoms:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "We couldn't recognize any known symptoms in what you wrote. Try describing them more "
            "specifically (e.g. 'fever', 'headache', 'sore throat').",
        )

    if payload.family_member_id:
        from app.models.family import FamilyMember

        member = db.get(FamilyMember, payload.family_member_id)
        if member is None or member.guardian_user_id != current_user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Family member not found")

    results = predict_diseases(db, matched_symptoms, top_n=5)
    if not results:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Your symptoms were recognized, but no matching conditions were found in the knowledge "
            "base yet. An admin may need to expand the disease database.",
        )
    _attach_medicine_category(db, results)

    risk = overall_risk_level(results)
    top = results[0]
    feature_importance = {}
    for r in results:
        feature_importance.update(r.get("_feature_importance", {}))

    prediction = Prediction(
        user_id=current_user.id,
        family_member_id=payload.family_member_id,
        source=PredictionSource.TEXT,
        input_summary=payload.symptoms_text,
        results_json=json.dumps(results),
        top_disease=top["disease_name"],
        top_probability=top["probability"],
        risk_level=risk,
        recommended_specialist=top.get("recommended_specialist"),
        recovery_estimate_days=top.get("recovery_time_days"),
        detected_symptoms_json=json.dumps([s.name for s in matched_symptoms]),
        feature_importance_json=json.dumps(feature_importance),
    )
    db.add(prediction)
    db.flush()

    db.add(
        MedicalHistory(
            user_id=current_user.id,
            prediction_id=prediction.id,
            event_type="prediction",
            title=f"Symptom check: possible {top['disease_name']}",
            detail=payload.symptoms_text,
        )
    )
    db.commit()
    db.refresh(prediction)

    return _build_prediction_out(prediction)


@router.get("/predictions/{prediction_id}", response_model=PredictionOut)
def get_prediction(
    prediction_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    prediction = db.get(Prediction, prediction_id)
    if prediction is None or (prediction.user_id != current_user.id and current_user.role.value != "admin"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Prediction not found")
    return _build_prediction_out(prediction)
