"""API regression tests for authentication endpoints.

PR4.5: Exercises the real auth routes (register, login, me, password-change,
forgot-password) through the FastAPI TestClient. Requires a live DATABASE_URL
— gated by the centralized db_required marker.

PRRP-DEFER-001: Updated to use httpOnly cookies instead of Authorization header.
"""

import pytest

from tests._markers import db_required

pytestmark = [pytest.mark.api, db_required]


def test_register_creates_user_and_sets_cookie(client):
    """POST /api/v1/auth/register must create a user and set httpOnly cookie."""
    payload = {
        "email": "newuser2@example.com",
        "pan": "NEWUS1234X",
        "name": "New User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user"]["email"] == payload["email"]
    assert body["user"]["pan"] == payload["pan"].upper()
    # Cookie must be set on the response, and flagged HttpOnly
    assert "taxstox_token" in resp.cookies
    set_cookie = resp.headers.get("set-cookie", "")
    assert "taxstox_token=" in set_cookie
    assert "httponly" in set_cookie.lower()


def test_register_rejects_duplicate_email(client):
    """POST /api/v1/auth/register must 409 on email collision."""
    payload = {
        "email": "dup2@example.com",
        "pan": "DUPUS1234X",
        "name": "First",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    assert "already" in resp.json().get("detail", "").lower()


def test_login_returns_token_via_cookie(client):
    """POST /api/v1/auth/login must return a JWT via httpOnly cookie."""
    payload = {
        "email": "loginuser2@example.com",
        "pan": "LOGIN1234X",
        "name": "Login User",
        "password": "CorrectPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["email"] == payload["email"]
    # Cookie must be set on the response, and flagged HttpOnly
    assert "taxstox_token" in resp.cookies
    set_cookie = resp.headers.get("set-cookie", "")
    assert "taxstox_token=" in set_cookie
    assert "httponly" in set_cookie.lower()


def test_login_rejects_wrong_password(client):
    """POST /api/v1/auth/login must 401 on wrong password."""
    payload = {
        "email": "badpass2@example.com",
        "pan": "BADPA1234X",
        "name": "Bad Pass User",
        "password": "CorrectPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": "WrongPass123!"})
    assert resp.status_code == 401


def test_me_returns_profile_for_valid_cookie(client):
    """GET /api/v1/auth/me must return the authenticated user's profile using cookie."""
    payload = {
        "email": "meuser2@example.com",
        "pan": "MEUSE1234X",
        "name": "Me User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=payload)
    login = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    # Extract the cookie value from the login response
    cookie = login.cookies.get("taxstox_token")
    # Make request with cookie
    resp = client.get("/api/v1/auth/me", cookies={"taxstox_token": cookie})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email"] == payload["email"]
    assert body["pan"] == payload["pan"].upper()
    assert body["name"] == payload["name"]


def test_me_rejects_missing_cookie(client):
    """GET /api/v1/auth/me must 401 without cookie."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_password_change_requires_current_password(client):
    """POST /api/v1/auth/change-password must 400 if current password is wrong."""
    payload = {
        "email": "pwuser2@example.com",
        "pan": "PWUSE1234X",
        "name": "Pw User",
        "password": "OldPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=payload)
    login = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    cookie = login.cookies.get("taxstox_token")
    resp = client.post(
        "/api/v1/auth/change-password",
        cookies={"taxstox_token": cookie},
        json={"current_password": "WrongOldPass", "new_password": "NewPass456!"},
    )
    assert resp.status_code == 400


def test_forgot_password_accepts_email(client):
    """POST /api/v1/auth/forgot-password must accept a valid email (no leak)."""
    payload = {
        "email": "forgot2@example.com",
        "pan": "FORGOT123X",
        "name": "Forgot User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/forgot-password", json={"email": payload["email"]})
    # Success is 200 with a generic message — no enumeration possible
    assert resp.status_code == 200
    assert "reset" in resp.json().get("message", "").lower()