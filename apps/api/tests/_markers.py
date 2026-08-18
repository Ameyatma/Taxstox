"""Centralized pytest markers and infrastructure-gating skips.

PR4.2: Single source of truth for tier markers and the env-gated skips used
across the suite, so individual test modules don't re-declare inline
`skipif(reason=...)` blocks. All skip conditions are derived from the same
environment variables the production code reads.
"""

import os

import pytest

# ── Tier markers (registered in pyproject.toml) ──────────────────────────
# Used as `@pytest.mark.unit`, `@pytest.mark.api`, etc. Not applied globally
# here — each module opts in so `pytest -m unit` selects by tier.

# ── Infrastructure gating ────────────────────────────────────────────────
# db_required: exercises the real psycopg2 repository against a live DB.
db_required = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not configured — requires PostgreSQL connection",
)

# jwt_required: imports src.auth.jwt, which raises at import time unless the
# secret is present.
jwt_required = pytest.mark.skipif(
    not os.environ.get("TAXSTOX_JWT_SECRET"),
    reason="TAXSTOX_JWT_SECRET not configured — JWT signing/verification requires it",
)
