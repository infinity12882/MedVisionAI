from __future__ import annotations

import pyotp
import pytest


@pytest.fixture()
def patient_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "ext-patient@example.com", "password": "StrongPass1", "full_name": "Ext Patient", "role": "patient"},
    )
    login = client.post("/api/v1/auth/login", json={"email": "ext-patient@example.com", "password": "StrongPass1"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture()
def doctor_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "ext-doctor@example.com", "password": "StrongPass1", "full_name": "Ext Doctor", "role": "doctor"},
    )
    login = client.post("/api/v1/auth/login", json={"email": "ext-doctor@example.com", "password": "StrongPass1"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_family_member_crud(client, patient_headers):
    r = client.post(
        "/api/v1/family", json={"full_name": "Test Child", "relationship": "child"}, headers=patient_headers
    )
    assert r.status_code == 201
    member_id = r.json()["id"]

    r = client.get("/api/v1/family", headers=patient_headers)
    assert len(r.json()) == 1

    r = client.delete(f"/api/v1/family/{member_id}", headers=patient_headers)
    assert r.status_code == 204


def test_care_connection_and_messaging_flow(client, patient_headers, doctor_headers):
    doctor_id = client.get("/api/v1/auth/me", headers=doctor_headers).json()["id"]

    r = client.post(f"/api/v1/care-connections/{doctor_id}", headers=patient_headers)
    assert r.status_code == 201
    connection_id = r.json()["id"]
    assert r.json()["status"] == "pending"

    r = client.put(f"/api/v1/care-connections/{connection_id}/accept", headers=doctor_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "active"

    r = client.post(f"/api/v1/messages/with/{doctor_id}", json={"content": "Hi doctor"}, headers=patient_headers)
    assert r.status_code == 200

    r = client.get("/api/v1/messages/conversations", headers=doctor_headers)
    assert len(r.json()) == 1
    assert r.json()[0]["last_message"] == "Hi doctor"


def test_appointment_booking_flow(client, patient_headers, doctor_headers):
    doctor_id = client.get("/api/v1/auth/me", headers=doctor_headers).json()["id"]

    r = client.post(
        "/api/v1/appointments/slots",
        json={"start_time": "2026-08-01T09:00:00Z", "end_time": "2026-08-01T09:30:00Z"},
        headers=doctor_headers,
    )
    assert r.status_code == 201
    slot_id = r.json()["id"]

    r = client.post(
        "/api/v1/appointments", json={"doctor_id": doctor_id, "slot_id": slot_id}, headers=patient_headers
    )
    assert r.status_code == 201
    appointment_id = r.json()["id"]
    assert r.json()["status"] == "pending"

    # Booking the same slot again should fail — it's now booked.
    r = client.post(
        "/api/v1/appointments", json={"doctor_id": doctor_id, "slot_id": slot_id}, headers=patient_headers
    )
    assert r.status_code == 409

    r = client.put(f"/api/v1/appointments/{appointment_id}/status", json={"status": "confirmed"}, headers=doctor_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "confirmed"


def test_emergency_hospital_search_sorted_by_distance(client):
    from app.models.emergency import Hospital
    from tests.conftest import TestSessionLocal

    db = TestSessionLocal()
    db.add(Hospital(name="Near Hospital", address="A", latitude=41.31, longitude=69.28, has_emergency_room=True))
    db.add(Hospital(name="Far Hospital", address="B", latitude=41.50, longitude=69.50, has_emergency_room=True))
    db.commit()
    db.close()

    r = client.get("/api/v1/emergency/hospitals", params={"latitude": 41.3111, "longitude": 69.2797, "radius_km": 200})
    assert r.status_code == 200
    hospitals = r.json()
    assert len(hospitals) >= 2
    distances = [h["distance_km"] for h in hospitals]
    assert distances == sorted(distances)
    assert hospitals[0]["name"] == "Near Hospital"


def test_sos_requires_emergency_contact_first(client, patient_headers):
    r = client.post("/api/v1/emergency/sos", json={"latitude": 41.3, "longitude": 69.2}, headers=patient_headers)
    assert r.status_code == 400

    client.post(
        "/api/v1/emergency/contacts", json={"name": "Friend", "phone": "+998900000000"}, headers=patient_headers
    )
    r = client.post("/api/v1/emergency/sos", json={"latitude": 41.3, "longitude": 69.2}, headers=patient_headers)
    assert r.status_code == 201


def test_two_factor_auth_full_cycle(client, patient_headers):
    r = client.post("/api/v1/2fa/setup", headers=patient_headers)
    assert r.status_code == 200
    secret = r.json()["secret"]

    code = pyotp.TOTP(secret).now()
    r = client.post("/api/v1/2fa/enable", json={"code": code}, headers=patient_headers)
    assert r.status_code == 200

    # Login without code should now be rejected.
    r = client.post("/api/v1/auth/login", json={"email": "ext-patient@example.com", "password": "StrongPass1"})
    assert r.status_code == 401
    assert r.json()["detail"] == "2FA_REQUIRED"

    # Login with a valid code should succeed.
    code2 = pyotp.TOTP(secret).now()
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "ext-patient@example.com", "password": "StrongPass1", "totp_code": code2},
    )
    assert r.status_code == 200

    # Clean up: disable 2FA so other tests using this account aren't affected.
    code3 = pyotp.TOTP(secret).now()
    client.post("/api/v1/2fa/disable", json={"code": code3}, headers=patient_headers)


def test_public_api_key_auth_and_rate_limit_field(client, patient_headers):
    r = client.post("/api/v1/developer/api-keys", json={"name": "test key"}, headers=patient_headers)
    assert r.status_code == 201
    full_key = r.json()["full_key"]

    r = client.get("/api/v1/public/diseases", headers={"X-API-Key": full_key})
    assert r.status_code == 200

    r = client.get("/api/v1/public/diseases", headers={"X-API-Key": "mva_totally_invalid_key_value"})
    assert r.status_code == 401

    r = client.get("/api/v1/public/diseases")
    assert r.status_code == 422  # missing required header


def test_billing_preview_mode_without_stripe_key(client, patient_headers):
    r = client.get("/api/v1/billing/subscription", headers=patient_headers)
    assert r.status_code == 200
    assert r.json()["tier"] == "free"
    assert r.json()["is_stripe_configured"] is False

    r = client.post("/api/v1/billing/checkout", headers=patient_headers)
    assert r.status_code == 200
    assert r.json()["preview_mode"] is True


def test_referral_code_generation_and_redemption(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "referrer@example.com", "password": "StrongPass1", "full_name": "Referrer", "role": "patient"},
    )
    login = client.post("/api/v1/auth/login", json={"email": "referrer@example.com", "password": "StrongPass1"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    r = client.get("/api/v1/referrals/my-code", headers=headers)
    assert r.status_code == 200
    code = r.json()["code"]
    assert len(code) == 8

    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "referred@example.com",
            "password": "StrongPass1",
            "full_name": "Referred User",
            "role": "patient",
            "referral_code": code,
        },
    )
    assert r.status_code == 201

    r = client.get("/api/v1/referrals/my-code", headers=headers)
    assert r.json()["uses_count"] == 1


def test_privacy_data_export(client, patient_headers):
    r = client.get("/api/v1/privacy/export", headers=patient_headers)
    assert r.status_code == 200
    data = r.json()
    assert "user" in data
    assert data["user"]["email"] == "ext-patient@example.com"
