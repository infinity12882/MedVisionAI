from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.prediction import MedicalHistory
from app.models.upload import LabReport
from app.models.user import User
from app.schemas.diagnosis import LabReportOut
from app.services.nlp.lab_report_parser import extract_text, parse_lab_values, summarize_findings
from app.services.uploads import save_lab_report

router = APIRouter(prefix="/diagnosis/lab-report", tags=["Lab Report Analysis"])


def _record_to_out(record: LabReport) -> LabReportOut:
    return LabReportOut(
        id=record.id,
        ocr_text=record.ocr_text,
        extracted_values=json.loads(record.extracted_values_json) if record.extracted_values_json else None,
        abnormal_findings=json.loads(record.abnormal_findings_json) if record.abnormal_findings_json else None,
        summary=record.summary,
        created_at=record.created_at,
    )


@router.post("", response_model=LabReportOut)
def analyze_lab_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_path = save_lab_report(file)

    try:
        raw_text = extract_text(file_path)
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Could not read this file: {exc}")

    if not raw_text.strip():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "No readable text was found in this file. If it's a scanned document, try uploading "
            "a clear photo of each page instead.",
        )

    values = parse_lab_values(raw_text)
    abnormal = [v for v in values if v["is_abnormal"]]
    summary = summarize_findings(values)

    record = LabReport(
        user_id=current_user.id,
        file_path=file_path,
        ocr_text=raw_text,
        extracted_values_json=json.dumps(values),
        abnormal_findings_json=json.dumps(abnormal),
        summary=summary,
    )
    db.add(record)
    db.flush()

    db.add(
        MedicalHistory(
            user_id=current_user.id,
            event_type="lab_report",
            title=f"Lab report analyzed ({len(abnormal)} abnormal values)",
            detail=summary,
        )
    )
    db.commit()
    db.refresh(record)
    return _record_to_out(record)


@router.get("/{report_id}", response_model=LabReportOut)
def get_lab_report(report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.get(LabReport, report_id)
    if record is None or (record.user_id != current_user.id and current_user.role.value != "admin"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lab report not found")
    return _record_to_out(record)
