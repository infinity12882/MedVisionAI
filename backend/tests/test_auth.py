from __future__ import annotations


def test_register_and_login(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "password": "StrongPass1", "full_name": "Alice Test", "role": "patient"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["email"] == "alice@example.com"

    r = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "StrongPass1"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and "refresh_token" in body


def test_login_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "password": "StrongPass1", "full_name": "Bob Test", "role": "patient"},
    )
    r = client.post("/api/v1/auth/login", json={"email": "bob@example.com", "password": "WrongPassword"})
    assert r.status_code == 401


def test_duplicate_registration_rejected(client):
    payload = {"email": "carol@example.com", "password": "StrongPass1", "full_name": "Carol Test", "role": "patient"}
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409


def test_cannot_self_register_as_admin(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "wannabe-admin@example.com", "password": "StrongPass1", "full_name": "Wannabe Admin", "role": "admin"},
    )
    assert r.status_code == 201
    assert r.json()["role"] == "patient"  # silently downgraded — admins are promoted, never self-registered


def test_protected_endpoint_requires_auth(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_admin_only_endpoint_blocks_patient(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "dana@example.com", "password": "StrongPass1", "full_name": "Dana", "role": "patient"},
    )
    login = client.post("/api/v1/auth/login", json={"email": "dana@example.com", "password": "StrongPass1"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    r = client.post("/api/v1/diseases", json={"name": "Test Disease"}, headers=headers)
    assert r.status_code == 403
