"""Phase 1: Identity Unification & Auth Harmonization Tests.

Tests for the core Super-App identity unification requirements:
- Unified user ID format (12-character short UUID)
- Consistent JWT token structure (sub contains user ID, not email)
- Harmonized authentication dependencies (get_current_user returns dict)
- Cross-domain authentication compatibility (Taxstox token works for Market endpoints)
- Standardized cookie handling (taxstox_token as canonical)
"""

import pytest
from fastapi.testclient import TestClient
from tests._markers import db_required

pytestmark = [pytest.mark.api, db_required]


def test_token_sub_contains_user_id_not_email(client):
    """Test Case 1: JWT sub field contains 12-char user ID, not email."""
    # Register a user via Taxstox auth (canonical)
    register_payload = {
        "email": "testuser@example.com",
        "pan": "TESTP1234A",
        "name": "Test User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    register_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert register_resp.status_code == 201

    # Login to get token
    login_payload = {
        "email": register_payload["email"],
        "password": register_payload["password"]
    }
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200

    # Extract token from cookie (canonical Taxstox method)
    cookie = login_resp.cookies.get("taxstox_token")
    assert cookie is not None, "taxstox_token cookie should be set"

    # Decode token to verify sub field
    from src.auth.jwt import decode_token
    payload = decode_token(cookie)

    # Verify sub field is present and is a 12-character string (short UUID)
    assert "sub" in payload, "JWT must contain sub field"
    user_id = payload["sub"]
    assert isinstance(user_id, str), "sub field must be string"
    assert len(user_id) == 12, f"sub field must be 12 characters, got {len(user_id)}: {user_id}"
    assert user_id.isalnum(), "sub field should be alphanumeric (hex)"

    # Verify sub field is NOT the email
    assert user_id != register_payload["email"], "sub field must not contain email"


def test_market_endpoint_access_via_header(client):
    """Test Case 2: Taxstox JWT works for Market domain endpoints via Authorization header."""
    # Register and login via Taxstox auth
    register_payload = {
        "email": "marketuser@example.com",
        "pan": "MARK1234A",
        "name": "Market User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]}
    )
    assert login_resp.status_code == 200

    # Extract token from cookie
    token = login_resp.cookies.get("taxstox_token")
    assert token is not None

    # Test Market domain portfolio endpoint with Authorization header
    market_resp = client.get(
        "/api/v1/market/users/portfolio",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert market_resp.status_code == 200, f"Market endpoint failed: {market_resp.text}"

    # Should return empty list (no portfolio items yet)
    portfolio_data = market_resp.json()
    assert isinstance(portfolio_data, list), "Portfolio response should be list"
    assert len(portfolio_data) == 0, "New user should have empty portfolio"


def test_market_endpoint_access_via_cookie(client):
    """Test Case 3: Taxstox JWT works for Market domain endpoints via taxstox_token cookie."""
    # Register and login via Taxstox auth
    register_payload = {
        "email": "cookieuser@example.com",
        "pan": "COOK1234A",
        "name": "Cookie User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]}
    )
    assert login_resp.status_code == 200

    # Extract token from cookie
    token = login_resp.cookies.get("taxstox_token")
    assert token is not None

    # Test Market domain portfolio endpoint with cookie
    market_resp = client.get(
        "/api/v1/market/users/portfolio",
        cookies={"taxstox_token": token}
    )
    assert market_resp.status_code == 200, f"Market endpoint failed with cookie: {market_resp.text}"

    portfolio_data = market_resp.json()
    assert isinstance(portfolio_data, list), "Portfolio response should be list"


def test_portfolio_mutation_with_short_uuid(client):
    """Test Case 4: Portfolio mutations work with 12-character user ID."""
    # Register and login via Taxstox auth
    register_payload = {
        "email": "portfolio@example.com",
        "pan": "PORT1234A",
        "name": "Portfolio User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]}
    )
    assert login_resp.status_code == 200

    token = login_resp.cookies.get("taxstox_token")
    assert token is not None

    # Add a stock to portfolio via Market domain
    symbol = "RELIANCE"
    add_resp = client.post(
        f"/api/v1/market/users/portfolio/{symbol}",
        cookies={"taxstox_token": token}
    )
    assert add_resp.status_code == 201, f"Failed to add to portfolio: {add_resp.text}"

    # Verify the portfolio item was created
    get_resp = client.get(
        "/api/v1/market/users/portfolio",
        cookies={"taxstox_token": token}
    )
    assert get_resp.status_code == 200

    portfolio_data = get_resp.json()
    assert isinstance(portfolio_data, list)
    assert len(portfolio_data) == 1, "Should have exactly one portfolio item"

    item = portfolio_data[0]
    assert item["symbol"] == symbol.upper()
    assert "added_at" in item

    # Remove the stock from portfolio
    remove_resp = client.delete(
        f"/api/v1/market/users/portfolio/{symbol}",
        cookies={"taxstox_token": token}
    )
    assert remove_resp.status_code == 204, f"Failed to remove from portfolio: {remove_resp.text}"

    # Verify portfolio is now empty
    get_resp2 = client.get(
        "/api/v1/market/users/portfolio",
        cookies={"taxstox_token": token}
    )
    assert get_resp2.status_code == 200
    portfolio_data2 = get_resp2.json()
    assert isinstance(portfolio_data2, list)
    assert len(portfolio_data2) == 0, "Portfolio should be empty after removal"