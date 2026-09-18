from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.emergency import EmergencyAlert, EmergencyContact, Hospital, Pharmacy
from app.models.user import User
from app.schemas.extended import (
    EmergencyAlertCreate,
    EmergencyAlertOut,
    EmergencyContactCreate,
    EmergencyContactOut,
    HospitalOut,
    PharmacyOut,
    RouteInfo,
)
from app.services.geo import haversine_km
from app.services.yandex_maps import get_yandex_client

router = APIRouter(prefix="/emergency", tags=["Emergency & Locator"])


@router.get("/hospitals", response_model=list[HospitalOut])
def find_hospitals(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=20, gt=0, le=1000),
    emergency_only: bool = False,
    include_route: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Hospital)
    if emergency_only:
        query = query.filter(Hospital.has_emergency_room.is_(True))

    results = []
    yandex_client = get_yandex_client()
    
    for h in query.all():
        distance = haversine_km(latitude, longitude, h.latitude, h.longitude)
        if distance <= radius_km:
            item = HospitalOut.model_validate(h)
            item.distance_km = round(distance, 2)
            
            # Add Yandex routing if enabled
            if include_route:
                route = yandex_client.get_route(latitude, longitude, h.latitude, h.longitude)
                if route:
                    map_url = yandex_client.get_static_map_url(
                        latitude, longitude, h.latitude, h.longitude
                    )
                    item.route_info = RouteInfo(
                        distance_km=route["distance_km"],
                        duration_minutes=route["duration_minutes"],
                        map_image_url=map_url,
                        polyline=route.get("polyline"),
                    )
            results.append(item)

    return sorted(results, key=lambda x: x.distance_km or 0)


@router.get("/pharmacies", response_model=list[PharmacyOut])
def find_pharmacies(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=10, gt=0, le=1000),
    open_24h_only: bool = False,
    include_route: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Pharmacy)
    if open_24h_only:
        query = query.filter(Pharmacy.is_24h.is_(True))

    results = []
    yandex_client = get_yandex_client()
    
    for p in query.all():
        distance = haversine_km(latitude, longitude, p.latitude, p.longitude)
        if distance <= radius_km:
            item = PharmacyOut.model_validate(p)
            item.distance_km = round(distance, 2)
            
            # Add Yandex routing if enabled
            if include_route:
                route = yandex_client.get_route(latitude, longitude, p.latitude, p.longitude)
                if route:
                    map_url = yandex_client.get_static_map_url(
                        latitude, longitude, p.latitude, p.longitude
                    )
                    item.route_info = RouteInfo(
                        distance_km=route["distance_km"],
                        duration_minutes=route["duration_minutes"],
                        map_image_url=map_url,
                        polyline=route.get("polyline"),
                    )
            results.append(item)

    return sorted(results, key=lambda x: x.distance_km or 0)


@router.get("/contacts", response_model=list[EmergencyContactOut])
def list_emergency_contacts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).all()


@router.post("/contacts", response_model=EmergencyContactOut, status_code=status.HTTP_201_CREATED)
def add_emergency_contact(
    payload: EmergencyContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    contact = EmergencyContact(user_id=current_user.id, **payload.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_emergency_contact(contact_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.get(EmergencyContact, contact_id)
    if contact is None or contact.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Emergency contact not found")
    db.delete(contact)
    db.commit()


@router.post("/sos", response_model=EmergencyAlertOut, status_code=status.HTTP_201_CREATED)
def trigger_sos(
    payload: EmergencyAlertCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Triggers an SOS alert. In this build, "notifying" emergency contacts
    means logging them against the alert and pushing an in-app
    notification to the user's own account as a confirmation receipt —
    a production deployment would wire this to actual SMS/email delivery
    (e.g. via Twilio) using the same EmergencyContact records.
    """
    contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == current_user.id).all()
    if not contacts:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "You haven't added any emergency contacts yet. Add at least one before using SOS.",
        )

    import json

    alert = EmergencyAlert(
        user_id=current_user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        message=payload.message,
        notified_contacts_json=json.dumps([{"name": c.name, "phone": c.phone} for c in contacts]),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    import logging
    from app.services.email import send_sos_alert_emails
    try:
        send_sos_alert_emails(
            user=current_user,
            contacts=contacts,
            latitude=payload.latitude,
            longitude=payload.longitude,
            message=payload.message,
        )
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to send SOS emails: {e}")

    return alert


@router.put("/sos/{alert_id}/resolve", response_model=EmergencyAlertOut)
def resolve_sos(alert_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import datetime, timezone

    alert = db.get(EmergencyAlert, alert_id)
    if alert is None or alert.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    alert.resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert
