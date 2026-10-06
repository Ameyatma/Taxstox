"""Shared test fixtures for TaxStox backend tests.

All fixtures use factory functions to create deterministic test data.
No real PDFs, no external dependencies, no network calls.
"""

import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

# Ensure backend source is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# PR4.3: The FastAPI app is imported lazily inside the `client` fixture (below)
# so that this conftest never triggers import-time side effects for the unit
# suite. `src.main` imports the auth router, whose `src.auth.jwt` module raises
# at import unless TAXSTOX_JWT_SECRET is set, so we provide a test-only secret
# before import. The app is constructed WITHOUT its lifespan context manager,
# which means init_db() / init_tax_tables() / FernetEncryptionService() /
# start_scheduler() never run — the API tests below do not require a database,
# a live encryption key, or the background scheduler.

os.environ.setdefault("TAXSTOX_JWT_SECRET", "test-secret-for-api-tests-only-0123456789")
os.environ.setdefault("TAXSTOX_ENCRYPTION_KEY", "-F5KHHwh7IbaUhTpjABbfkNTgHJQkTzlzacnBKS9EZU=")


@pytest.fixture
def reset_db():
    """Reset the database before each test."""
    from src.db.database import get_db
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM password_reset_tokens")
    cur.execute("DELETE FROM refresh_tokens")
    cur.execute("DELETE FROM filings")
    cur.execute("DELETE FROM users")
    cur.close()
    conn.commit()
    conn.close()
    yield
    # Cleanup after test
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM password_reset_tokens")
    cur.execute("DELETE FROM refresh_tokens")
    cur.execute("DELETE FROM filings")
    cur.execute("DELETE FROM users")
    cur.close()
    conn.commit()
    conn.close()


@pytest.fixture
def client(reset_db):
    """FastAPI TestClient over the real app, without lifespan/DB startup."""
    from fastapi.testclient import TestClient
    from src.main import app

    # Override rate limit store to allow all requests during tests
    from src.engine.gateway import rate_limit_dependency
    class AllowAllStore:
        def check_and_increment(self, key, max_requests, window_seconds):
            return True, max_requests
    rate_limit_dependency._rate_limit_store = AllowAllStore()

    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


from tests.factories import (  # noqa: E402
    make_ais_data,
    make_classified_cg_data,
    make_form16_data,
    make_user_answers,
)