from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.prediction import MedicalHistory, Prediction, PredictionSource
from app.models.upload import VoiceRecord
from app.models.user import User
from app.schemas.diagnosis import VoiceDiagnosisOut
from app.services.ml.disease_predictor import overall_risk_level, predict_diseases
from app.services.nlp.symptom_extractor import extract_symptoms
from app.services.uploads import save_voice
from app.services.speech.transcribe import transcribe

router = APIRouter(prefix="/diagnosis/voice", tags=["Voice Diagnosis"])


@router.post("", response_model=VoiceDiagnosisOut)
def diagnose_voice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_path = save_voice(file)

    try:
        transcription = transcribe(file_path)
    except RuntimeError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))

    transcript_text = transcription["text"]
    matched_symptoms = extract_symptoms(db, transcript_text) if transcript_text else []

    record = VoiceRecord(
        user_id=current_user.id,
        file_path=file_path,
        transcript=transcript_text,
        extracted_symptoms=",".join(s.name for s in matched_symptoms),
    )
    db.add(record)
    db.flush()

    prediction_out = None
    if matched_symptoms:
        results = predict_diseases(db, matched_symptoms, top_n=5)
        if results:
            risk = overall_risk_level(results)
            top = results[0]
            feature_importance = {}
            for r in results:
                feature_importance.update(r.get("_feature_importance", {}))

            prediction = Prediction(
                user_id=current_user.id,
                source=PredictionSource.VOICE,
                source_record_id=record.id,
                input_summary=transcript_text,
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
                    event_type="voice",
                    title=f"Voice check: possible {top['disease_name']}",
                    detail=transcript_text,
                )
            )

            # Lazy import to avoid a circular import with diagnosis_text.py
            from app.api.v1.endpoints.diagnosis_text import _build_prediction_out

            db.commit()
            db.refresh(prediction)
            prediction_out = _build_prediction_out(prediction)
        else:
            db.commit()
    else:
        db.commit()

    db.refresh(record)
    return VoiceDiagnosisOut(
        id=record.id,
        transcript=record.transcript,
        extracted_symptoms=[s.name for s in matched_symptoms],
        prediction=prediction_out,
        created_at=record.created_at,
    )
