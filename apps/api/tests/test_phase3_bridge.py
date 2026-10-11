"""Phase 3: Data Bridge Implementation Tests.

Tests for the core Super-App data bridge requirements:
- Capital gains bridge endpoint
- Tax results webhook endpoint
- User sync endpoint
"""

import pytest
from fastapi.testclient import TestClient
from tests._markers import db_required

# Temporarily remove markers for testing
# pytestmark = [pytest.mark.api, db_required]


def test_capital_gains_bridge(client):
    """Test Case 1: Capital Gains Bridge"""
    # Register a test user via Taxstox auth (canonical)
    register_payload = {
        "email": "bridgetest@example.com",
        "pan": "ABCDE1234F",  # Valid PAN format: 5 letters, 4 digits, 1 letter
        "name": "Bridge Test User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    register_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert register_resp.status_code == 201, f"Registration failed: {register_resp.text}"

    # Login to get token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]}
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"

    # Extract token from cookies
    token = login_resp.cookies.get("taxstox_token")
    assert token is not None, "taxstox_token cookie should be set"

    # Get user info to get the canonical user_id (short_uid)
    me_resp = client.get(
        "/api/v1/auth/me",
        cookies={"taxstox_token": token}
    )
    assert me_resp.status_code == 200, f"Failed to get user profile: {me_resp.text}"
    user_info = me_resp.json()
    expected_user_id = user_info["id"]  # This is the short_uid from JWT sub

    # Add 'RELIANCE.NS' to user's Market portfolio
    portfolio_resp = client.post(
        "/api/v1/market/users/portfolio/RELIANCE.NS",
        cookies={"taxstox_token": token}
    )
    assert portfolio_resp.status_code == 201, f"Failed to add to portfolio: {portfolio_resp.text}"

    # Call the capital gains bridge endpoint
    cg_resp = client.get(
        "/api/v1/market/bridge/capital-gains",
        cookies={"taxstox_token": token}
    )
    assert cg_resp.status_code == 200, f"Capital gains bridge failed: {cg_resp.text}"

    # Parse and validate the response
    cg_data = cg_resp.json()

    # Assert response contains required fields per Section 2.3.1 of Blueprint
    assert "filing_session_id" in cg_data
    assert "user_id" in cg_data
    assert "capital_gains" in cg_data
    assert "summary" in cg_data

    # Assert user_id matches our test user's canonical id (short_uid)
    assert cg_data["user_id"] == expected_user_id

    # Assert capital_gains array contains RELIANCE.NS
    symbols = [item["symbol"] for item in cg_data["capital_gains"]]
    assert "RELIANCE.NS" in symbols, f"Expected RELIANCE.NS in capital gains, got {symbols}"

    # Validate the structure of the capital gains item
    reliance_item = next(item for item in cg_data["capital_gains"] if item["symbol"] == "RELIANCE.NS")
    assert "gross_gain" in reliance_item
    assert "taxable_gain" in reliance_item
    assert "is_long_term" in reliance_item
    assert "buy_price" in reliance_item
    assert "sell_price" in reliance_item
    assert "quantity" in reliance_item
    assert "buy_date" in reliance_item
    assert "sell_date" in reliance_item

    # Validate summary structure
    summary = cg_data["summary"]
    assert "total_gross_gain" in summary
    assert "total_taxable_gain" in summary
    assert "long_term_count" in summary
    assert "short_term_count" in summary
    assert "total_holdings" in summary

    print(f"Capital gains response: {cg_data}")


def test_tax_results_webhook(client):
    """Test Case 2: Tax Results Webhook"""
    # Register a test user
    register_payload = {
        "email": "taxresultstest@example.com",
        "pan": "TAXST1234F",  # Valid PAN format: 5 letters, 4 digits, 1 letter
        "name": "Tax Results Test User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    register_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert register_resp.status_code == 201

    # Login to get token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]}
    )
    assert login_resp.status_code == 200

    token = login_resp.cookies.get("taxstox_token")
    assert token is not None

    # POST mock tax result to the bridge endpoint
    tax_payload = {
        "total_income": 1000000.0,
        "capital_gains_tax": 150000.0,
        "effective_tax_rate": 0.15
    }

    tax_resp = client.post(
        "/api/v1/market/bridge/tax-results",
        json=tax_payload,
        cookies={"taxstox_token": token}
    )
    assert tax_resp.status_code == 200, f"Tax results endpoint failed: {tax_resp.text}"

    # Validate response
    tax_data = tax_resp.json()
    assert tax_data["status"] == "success"
    assert "message" in tax_data
    assert "Tax results synced" in tax_data["message"]

    print(f"Tax results response: {tax_data}")


def test_sync_user_endpoint(client):
    """Additional test: User Sync Endpoint"""
    # Register a test user
    register_payload = {
        "email": "synctest@example.com",
        "pan": "SYNCU1234F",  # Valid PAN format: 5 letters, 4 digits, 1 letter
        "name": "Sync Test User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    register_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert register_resp.status_code == 201

    # Login to get token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]}
    )
    assert login_resp.status_code == 200

    token = login_resp.cookies.get("taxstox_token")
    assert token is not None

    # Get the canonical user_id (short_uid) from /me
    me_resp = client.get("/api/v1/auth/me", cookies={"taxstox_token": token})
    assert me_resp.status_code == 200, f"Failed to get user profile: {me_resp.text}"
    user_info = me_resp.json()
    expected_user_id = user_info["id"]

    # POST to sync-user endpoint
    sync_payload = {
        "user_id": expected_user_id,  # Must match JWT sub (canonical short_uid)
        "email": register_payload["email"],
        "name": register_payload["name"]
    }

    sync_resp = client.post(
        "/api/v1/market/bridge/sync-user",
        json=sync_payload,
        cookies={"taxstox_token": token}
    )
    assert sync_resp.status_code == 200, f"Sync user endpoint failed: {sync_resp.text}"

    # Validate response
    sync_data = sync_resp.json()
    assert sync_data["status"] == "success"
    assert sync_data["user_id"] == expected_user_id

    print(f"Sync user response: {sync_data}")