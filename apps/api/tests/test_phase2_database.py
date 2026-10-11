"""Phase 2: Database Schema Unification Tests.

Tests for the core Super-App database unification requirements:
- Unified database connection (both domains use same DATABASE_URL)
- Unified initialization sequence (lifespan boot creates both Tax and Market tables)
- Cross-domain data existence (Taxstox user can have Market portfolio items)
- Table protection (Market User model doesn't overwrite Taxstox users table)
"""

import pytest
from fastapi.testclient import TestClient
from tests._markers import db_required

# Temporarily remove markers for testing
# pytestmark = [pytest.mark.api, db_required]


def test_unified_database_initialization(client):
    """Test Case 1: Unified initialization - both Tax and Market tables created without exceptions."""
    # This test passes if the client fixture can be created successfully,
    # which means both Taxstox and Market domain initialization succeeded
    # without throwing exceptions during table creation.

    # We can verify this by checking that we can make basic API calls
    # that depend on both domains' tables being present

    # Test that we can access Taxstox auth endpoints (depends on users table)
    register_payload = {
        "email": "dbtest@example.com",
        "pan": "ABCDE1234F",
        "name": "DB Test User",
        "password": "StrongPass123!",
        "dob": "25041995",
    }
    resp = client.post("/api/v1/auth/register", json=register_payload)
    assert resp.status_code == 201, f"Taxstox registration failed: {resp.text}"

    # Test that we can access Market domain endpoints (depends on market tables)
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": register_payload["email"], "password": register_payload["password"]}
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"

    token = login_resp.cookies.get("taxstox_token")
    assert token is not None, "taxstox_token cookie should be set"

    # Test Market portfolio endpoint (depends on portfolios table)
    market_resp = client.get(
        "/api/v1/market/users/portfolio",
        cookies={"taxstox_token": token}
    )
    assert market_resp.status_code == 200, f"Market portfolio endpoint failed: {market_resp.text}"

    # Should return empty list (no portfolio items yet)
    portfolio_data = market_resp.json()
    assert isinstance(portfolio_data, list), "Portfolio response should be list"


def test_cross_domain_data_existence(client):
    """Test Case 2: Cross-domain data existence - Taxstox user can have Market portfolio items."""
    # Register a user via Taxstox (psycopg2 method)
    register_payload = {
        "email": "crossdomain@example.com",
        "pan": "CROSS1234F",
        "name": "Cross Domain User",
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

    # Insert a Portfolio item for that user using Market domain (SQLAlchemy method)
    symbol = "RELIANCE"
    add_resp = client.post(
        f"/api/v1/market/users/portfolio/{symbol}",
        cookies={"taxstox_token": token}
    )
    assert add_resp.status_code == 201, f"Failed to add to portfolio: {add_resp.text}"

    # Query the portfolio and assert that the relationship holds
    get_resp = client.get(
        "/api/v1/market/users/portfolio",
        cookies={"taxstox_token": token}
    )
    assert get_resp.status_code == 200, f"Failed to get portfolio: {get_resp.text}"

    portfolio_data = get_resp.json()
    assert isinstance(portfolio_data, list)
    assert len(portfolio_data) == 1, "Should have exactly one portfolio item"

    item = portfolio_data[0]
    assert item["symbol"] == symbol.upper()
    assert "added_at" in item

    # Verify we can still access Taxstox user data
    me_resp = client.get(
        "/api/v1/auth/me",
        cookies={"taxstox_token": token}
    )
    assert me_resp.status_code == 200, f"Failed to get user profile: {me_resp.text}"

    user_data = me_resp.json()
    assert user_data["email"] == register_payload["email"]
    assert user_data["pan"] == register_payload["pan"].upper()


def test_market_user_model_does_not_overwrite_taxstox_users_table(client):
    """Test Case 3: Table protection - Market User model doesn't overwrite Taxstox users table."""
    # This test verifies that the Market domain's User model with
    # __table_args__ = {'extend_existing': True} doesn't interfere with
    # the Taxstox users table management.

    # Register multiple users to ensure the Taxstox users table is working correctly
    users = [
        {
            "email": "user1@example.com",
            "pan": "ABCDE1234F",
            "name": "User 1",
            "password": "StrongPass123!",
            "dob": "25041995",
        },
        {
            "email": "user2@example.com",
            "pan": "BCDEF5678G",
            "name": "User 2",
            "password": "StrongPass123!",
            "dob": "25041995",
        },
        {
            "email": "user3@example.com",
            "pan": "CDEFG9012H",
            "name": "User 3",
            "password": "StrongPass123!",
            "dob": "25041995",
        }
    ]

    for user_data in users:
        resp = client.post("/api/v1/auth/register", json=user_data)
        assert resp.status_code == 201, f"Registration failed for {user_data['email']}: {resp.text}"

    # Verify all users can log in and access their data
    for index, user_data in enumerate(users, start=1):
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": user_data["email"], "password": user_data["password"]}
        )
        assert login_resp.status_code == 200, f"Login failed for {user_data['email']}"

        token = login_resp.cookies.get("taxstox_token")
        assert token is not None

        # Verify user profile is correct
        me_resp = client.get(
            "/api/v1/auth/me",
            cookies={"taxstox_token": token}
        )
        assert me_resp.status_code == 200, f"Failed to get profile for {user_data['email']}"

        user_data_returned = me_resp.json()
        assert user_data_returned["email"] == user_data["email"]
        assert user_data_returned["pan"] == user_data["pan"].upper()

        # Verify each user can have independent Market portfolio data
        symbol = f"TEST{index}"
        add_resp = client.post(
            f"/api/v1/market/users/portfolio/{symbol}",
            cookies={"taxstox_token": token}
        )
        assert add_resp.status_code == 201, f"Failed to add portfolio for {user_data['email']}"

    # Final verification: each user should have exactly one portfolio item
    for user_data in users:
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": user_data["email"], "password": user_data["password"]}
        )
        assert login_resp.status_code == 200

        token = login_resp.cookies.get("taxstox_token")
        assert token is not None

        get_resp = client.get(
            "/api/v1/market/users/portfolio",
            cookies={"taxstox_token": token}
        )
        assert get_resp.status_code == 200

        portfolio_data = get_resp.json()
        assert isinstance(portfolio_data, list)
        assert len(portfolio_data) == 1, f"User {user_data['email']} should have exactly one portfolio item"