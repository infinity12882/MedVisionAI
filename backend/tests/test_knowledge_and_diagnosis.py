from __future__ import annotations

import pytest


@pytest.fixture()
def admin_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "admin-test@example.com", "password": "StrongPass1", "full_name": "Admin", "role": "admin"},
    )
    # Force-promote via DB since self-registration as admin is blocked.
    from app.models.user import User, UserRole
    from tests.conftest import TestSessionLocal

    db = TestSessionLocal()
    user = db.query(User).filter(User.email == "admin-test@example.com").first()
    user.role = UserRole.ADMIN
    db.commit()
    db.close()

    login = client.post("/api/v1/auth/login", json={"email": "admin-test@example.com", "password": "StrongPass1"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture()
def patient_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "patient-test@example.com", "password": "StrongPass1", "full_name": "Patient", "role": "patient"},
    )
    login = client.post("/api/v1/auth/login", json={"email": "patient-test@example.com", "password": "StrongPass1"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_create_symptom_and_disease_with_links(client, admin_headers):
    r = client.post("/api/v1/symptoms", json={"name": "Test Fever", "body_system": "general"}, headers=admin_headers)
    assert r.status_code == 201, r.text
    symptom_id = r.json()["id"]

    r = client.post(
        "/api/v1/diseases",
        json={
            "name": "Test Flu",
            "severity": "moderate",
            "recommended_specialist": "General Physician",
            "symptoms": [{"symptom_id": symptom_id, "importance_score": 0.9}],
        },
        headers=admin_headers,
    )
    assert r.status_code == 201, r.text
    disease = r.json()
    assert disease["name"] == "Test Flu"
    assert len(disease["symptom_links"]) == 1
    assert disease["symptom_links"][0]["symptom"]["name"] == "Test Fever"


def test_symptom_checker_predicts_seeded_disease(client, admin_headers, patient_headers):
    # Build a tiny, deterministic knowledge base.
    s1 = client.post("/api/v1/symptoms", json={"name": "Bright Spots"}, headers=admin_headers).json()
    s2 = client.post("/api/v1/symptoms", json={"name": "Glowing Skin"}, headers=admin_headers).json()

    client.post(
        "/api/v1/diseases",
        json={
            "name": "Glowtest Syndrome",
            "severity": "mild",
            "recommended_specialist": "Dermatologist",
            "avg_recovery_days": 5,
            "symptoms": [
                {"symptom_id": s1["id"], "importance_score": 0.9},
                {"symptom_id": s2["id"], "importance_score": 0.8},
            ],
        },
        headers=admin_headers,
    )

    r = client.post(
        "/api/v1/diagnosis/text",
        json={"symptoms_text": "I have bright spots and glowing skin"},
        headers=patient_headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["top_disease"] == "Glowtest Syndrome"
    assert set(data["explainability"]["matched_symptoms"]) == {"Bright Spots", "Glowing Skin"}
    assert data["recovery_estimate_days"] == 5


def test_symptom_checker_unrecognized_symptoms_returns_422(client, patient_headers):
    r = client.post(
        "/api/v1/diagnosis/text",
        json={"symptoms_text": "asdkjaslkdjalksjd nonsense text with no symptoms"},
        headers=patient_headers,
    )
    assert r.status_code == 422


def test_chat_falls_back_gracefully_without_gemini_key(client, admin_headers, patient_headers):
    client.post("/api/v1/symptoms", json={"name": "Chat Test Symptom"}, headers=admin_headers)
    client.post(
        "/api/v1/diseases",
        json={"name": "Chat Test Disease", "description": "A disease used purely for chat RAG testing."},
        headers=admin_headers,
    )

    r = client.post("/api/v1/chat/send", json={"message": "Tell me about Chat Test Disease"}, headers=patient_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["assistant_message"]["used_fallback"] is True  # no GEMINI_API_KEY in test env
    assert len(body["assistant_message"]["retrieved_sources"]) > 0


def test_disease_list_and_delete(client, admin_headers):
    r = client.post("/api/v1/diseases", json={"name": "Deletable Disease"}, headers=admin_headers)
    disease_id = r.json()["id"]

    r = client.get("/api/v1/diseases")
    assert any(d["name"] == "Deletable Disease" for d in r.json())

    r = client.delete(f"/api/v1/diseases/{disease_id}", headers=admin_headers)
    assert r.status_code == 204

    r = client.get(f"/api/v1/diseases/{disease_id}")
    assert r.status_code == 404
