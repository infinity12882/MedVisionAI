from __future__ import annotations

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.health_tracking import SymptomDiaryEntry, Vaccination, WearableDataPoint
from app.models.user import User
from app.schemas.extended import (
    SymptomDiaryCreate,
    SymptomDiaryOut,
    VaccinationCreate,
    VaccinationOut,
    WearableDataPointCreate,
    WearableDataPointOut,
)

router = APIRouter(tags=["Health Tracking"])

VALID_METRICS = {"steps", "heart_rate", "sleep_hours", "calories", "weight_kg"}


# ---------- Symptom diary ----------
@router.get("/diary", response_model=list[SymptomDiaryOut])
def list_diary_entries(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(SymptomDiaryEntry)
        .filter(SymptomDiaryEntry.user_id == current_user.id)
        .order_by(SymptomDiaryEntry.entry_date.desc())
        .all()
    )


@router.post("/diary", response_model=SymptomDiaryOut, status_code=status.HTTP_201_CREATED)
def add_diary_entry(
    payload: SymptomDiaryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    existing = (
        db.query(SymptomDiaryEntry)
        .filter(SymptomDiaryEntry.user_id == current_user.id, SymptomDiaryEntry.entry_date == payload.entry_date)
        .first()
    )
    if existing:
        for field, value in payload.model_dump().items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    entry = SymptomDiaryEntry(user_id=current_user.id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


# ---------- Vaccinations ----------
@router.get("/vaccinations", response_model=list[VaccinationOut])
def list_vaccinations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Vaccination)
        .filter(Vaccination.user_id == current_user.id)
        .order_by(Vaccination.date_administered.desc())
        .all()
    )


@router.post("/vaccinations", response_model=VaccinationOut, status_code=status.HTTP_201_CREATED)
def add_vaccination(
    payload: VaccinationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    record = Vaccination(user_id=current_user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/vaccinations/{vaccination_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vaccination(vaccination_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.get(Vaccination, vaccination_id)
    if record is None or record.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vaccination record not found")
    db.delete(record)
    db.commit()


# ---------- Wearable data ----------
@router.get("/wearables", response_model=list[WearableDataPointOut])
def list_wearable_data(
    metric_type: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    query = db.query(WearableDataPoint).filter(WearableDataPoint.user_id == current_user.id)
    if metric_type:
        query = query.filter(WearableDataPoint.metric_type == metric_type)
    return query.order_by(WearableDataPoint.recorded_date.desc()).limit(180).all()


@router.post("/wearables", response_model=WearableDataPointOut, status_code=status.HTTP_201_CREATED)
def add_wearable_point(
    payload: WearableDataPointCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if payload.metric_type not in VALID_METRICS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"metric_type must be one of {sorted(VALID_METRICS)}")
    point = WearableDataPoint(user_id=current_user.id, source="manual", **payload.model_dump())
    db.add(point)
    db.commit()
    db.refresh(point)
    return point


@router.post("/wearables/import-csv")
def import_wearable_csv(
    file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Expects a CSV with columns: metric_type,value,recorded_date (YYYY-MM-DD).
    This is the manual-import path used until a production deployment adds
    real OAuth integrations for Fitbit / Apple Health / Google Fit.
    """
    content = file.file.read().decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(content))

    imported = 0
    errors = []
    for i, row in enumerate(reader, start=2):
        try:
            metric = row["metric_type"].strip()
            if metric not in VALID_METRICS:
                errors.append(f"Row {i}: unknown metric_type '{metric}'")
                continue
            point = WearableDataPoint(
                user_id=current_user.id,
                metric_type=metric,
                value=float(row["value"]),
                recorded_date=datetime.strptime(row["recorded_date"].strip(), '%Y-%m-%d').date(),
                source="csv_import",
            )
            db.add(point)
            imported += 1
        except (KeyError, ValueError) as exc:
            errors.append(f"Row {i}: {exc}")

    db.commit()
    return {"imported": imported, "errors": errors}
