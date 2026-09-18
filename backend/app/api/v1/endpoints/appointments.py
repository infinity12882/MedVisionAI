from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.care import Appointment, AppointmentStatus, DoctorTimeSlot
from app.models.user import User, UserRole
from app.schemas.extended import AppointmentCreate, AppointmentOut, AppointmentStatusUpdate, TimeSlotCreate, TimeSlotOut
from app.services.notify import notify

router = APIRouter(prefix="/appointments", tags=["Appointments & Telemedicine"])


@router.post("/slots", response_model=TimeSlotOut, status_code=status.HTTP_201_CREATED)
def create_time_slot(
    payload: TimeSlotCreate, db: Session = Depends(get_db), doctor: User = Depends(require_role(UserRole.DOCTOR))
):
    if payload.end_time <= payload.start_time:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "end_time must be after start_time")
    slot = DoctorTimeSlot(doctor_id=doctor.id, start_time=payload.start_time, end_time=payload.end_time)
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


@router.get("/slots/{doctor_id}", response_model=list[TimeSlotOut])
def list_available_slots(doctor_id: str, db: Session = Depends(get_db)):
    return (
        db.query(DoctorTimeSlot)
        .filter(DoctorTimeSlot.doctor_id == doctor_id, DoctorTimeSlot.is_booked.is_(False))
        .order_by(DoctorTimeSlot.start_time)
        .all()
    )


@router.delete("/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_time_slot(slot_id: str, db: Session = Depends(get_db), doctor: User = Depends(require_role(UserRole.DOCTOR))):
    slot = db.get(DoctorTimeSlot, slot_id)
    if slot is None or slot.doctor_id != doctor.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Slot not found")
    if slot.is_booked:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot delete a booked slot")
    db.delete(slot)
    db.commit()


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_appointment(
    payload: AppointmentCreate, db: Session = Depends(get_db), patient: User = Depends(require_role(UserRole.PATIENT))
):
    slot = db.get(DoctorTimeSlot, payload.slot_id)
    if slot is None or slot.doctor_id != payload.doctor_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Time slot not found")
    if slot.is_booked:
        raise HTTPException(status.HTTP_409_CONFLICT, "This time slot has already been booked")

    duration = int((slot.end_time - slot.start_time).total_seconds() // 60)
    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=payload.doctor_id,
        slot_id=slot.id,
        scheduled_at=slot.start_time,
        duration_minutes=duration,
        reason=payload.reason,
        status=AppointmentStatus.PENDING,
    )
    slot.is_booked = True
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    notify(
        db, user_id=payload.doctor_id, title="New appointment request",
        message=f"{patient.full_name} booked a slot on {slot.start_time.strftime('%Y-%m-%d %H:%M')}.",
    )
    return appointment


@router.get("/my", response_model=list[AppointmentOut])
def my_appointments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == UserRole.DOCTOR:
        return db.query(Appointment).filter(Appointment.doctor_id == current_user.id).order_by(Appointment.scheduled_at).all()
    return db.query(Appointment).filter(Appointment.patient_id == current_user.id).order_by(Appointment.scheduled_at).all()


@router.put("/{appointment_id}/status", response_model=AppointmentOut)
def update_appointment_status(
    appointment_id: str,
    payload: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    doctor: User = Depends(require_role(UserRole.DOCTOR)),
):
    appointment = db.get(Appointment, appointment_id)
    if appointment is None or appointment.doctor_id != doctor.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Appointment not found")
    appointment.status = payload.status
    if payload.doctor_notes is not None:
        appointment.doctor_notes = payload.doctor_notes
    db.commit()
    db.refresh(appointment)

    notify(
        db, user_id=appointment.patient_id, title="Appointment update",
        message=f"Your appointment is now {payload.status.value}.",
    )
    return appointment


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_appointment(appointment_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    appointment = db.get(Appointment, appointment_id)
    if appointment is None or current_user.id not in (appointment.patient_id, appointment.doctor_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Appointment not found")
    appointment.status = AppointmentStatus.CANCELLED
    if appointment.slot_id:
        slot = db.get(DoctorTimeSlot, appointment.slot_id)
        if slot:
            slot.is_booked = False
    db.commit()
