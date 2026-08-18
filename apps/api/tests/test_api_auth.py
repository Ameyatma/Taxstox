"""API regression tests for authentication endpoints.

PR4.5: Exercises the real auth routes (register, login, me, password-change,
forgot-password) through the FastAPI TestClient. Requires a live DATABASE_URL
— gated behind the centralized db_required marker.
"""

import pytest

from tests._markers import db_required

pytestmark = [pytest.mark.api, db_required]


def test_register_creates_user_and_returns_token(client):
    """POST /api/v1/auth/register must create a user and return a JWT."""
    payload = {
        "email": "newuser@example.com",
        "pan": "NEWUS1234X",
        "name": "New User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "access_token" in body
    assert body["user"]["email"] == payload["email"]
    assert body["user"]["pan"] == payload["pan"].upper()


def test_register_rejects_duplicate_email(client):
    """POST /api/v1/auth/register must 409 on email collision."""
    payload = {
        "email": "dup@example.com",
        "pan": "DUPUS1234X",
        "name": "First",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    assert "already" in resp.json().get("detail", "").lower()


def test_login_returns_token_for_valid_credentials(client):
    """POST /api/v1/auth/login must return a JWT for correct credentials."""
    payload = {
        "email": "loginuser@example.com",
        "pan": "LOGIN1234X",
        "name": "Login User",
        "password": "CorrectPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "access_token" in body
    assert body["user"]["email"] == payload["email"]


def test_login_rejects_wrong_password(client):
    """POST /api/v1/auth/login must 401 on wrong password."""
    payload = {
        "email": "badpass@example.com",
        "pan": "BADPA1234X",
        "name": "Bad Pass User",
        "password": "CorrectPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": "WrongPass123!"})
    assert resp.status_code == 401


def test_me_returns_profile_for_valid_token(client):
    """GET /api/v1/auth/me must return the authenticated user's profile."""
    payload = {
        "email": "meuser@example.com",
        "pan": "MEUSE1234X",
        "name": "Me User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=payload)
    login = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = login.json()["access_token"]
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email"] == payload["email"]
    assert body["pan"] == payload["pan"].upper()
    assert body["name"] == payload["name"]


def test_me_rejects_missing_token(client):
    """GET /api/v1/auth/me must 401 without Authorization header."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_password_change_requires_current_password(client):
    """PUT /api/v1/auth/password must 400 if current password is wrong."""
    payload = {
        "email": "pwuser@example.com",
        "pan": "PWUSE1234X",
        "name": "Pw User",
        "password": "OldPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=payload)
    login = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = login.json()["access_token"]
    resp = client.put(
        "/api/v1/auth/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "WrongOldPass", "new_password": "NewPass456!"},
    )
    assert resp.status_code == 400


def test_forgot_password_accepts_email(client):
    """POST /api/v1/auth/forgot-password must accept a valid email (no leak)."""
    payload = {
        "email": "forgot@example.com",
        "pan": "FORGOT123X",
        "name": "Forgot User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/forgot-password", json={"email": payload["email"]})
    # Success is 200 with a generic message — no enumeration possible
    assert resp.status_code == 200
    assert "reset" in resp.json().get("detail", "").lower()