# TaxStox Backend — Test Suite Contract (PR4)

This document is the **authoritative execution contract** for the backend test
suite. It was established during PR4 (Test Infrastructure). Follow it when
running, extending, or triaging the tests.

## 1. How to run

From `apps/api`:

```bash
# Full suite (default markers; no DB / no E2E PDFs required)
python -m pytest

# By tier
python -m pytest -m unit      # fast, in-memory, synthetic data
python -m pytest -m integration
python -m pytest -m api       # real app via TestClient (no DB needed by default)
python -m pytest -m e2e       # real-data filing flow

# With a live database (enables db_required tests)
DATABASE_URL=postgresql://... python -m pytest -m db_required

# With a JWT secret (enables jwt_required tests)
TAXSTOX_JWT_SECRET=$(python -c 'import secrets;print(secrets.token_hex(32))') python -m pytest
```

**The whole suite must collect with zero errors** without `--ignore`. The
real-data E2E (`test_e2e_real_data.py`) is *gated*, not ignored — it skips
cleanly when its prerequisites are absent (see §4).

## 2. Test tiers (markers)

| Marker | Meaning | Requires |
|--------|---------|----------|
| `unit` | Fast in-memory logic, synthetic fixtures | nothing |
| `integration` | Interaction between internal domain components | nothing |
| `api` | HTTP endpoints / middleware via `TestClient` (real app) | `TAXSTOX_JWT_SECRET` (auto-set by conftest) |
| `e2e` | End-to-end, including the real-data filing flow | real PDFs + env vars (see §4) |
| `db_required` | Hits the real PostgreSQL repository | `DATABASE_URL` |
| `jwt_required` | Imports JWT module (raises without secret) | `TAXSTOX_JWT_SECRET` |

Markers are registered in `pyproject.toml` under `[tool.pytest.ini_options]`.
Centralized env-gated skips live in `tests/_markers.py`.

## 3. Fixtures (conftest.py)

- **Synthetic data fixtures** (`sample_form16_data`, `sample_ais_data`,
  `sample_user_answers`, `sample_classified_cg_data`, …) are built from
  `tests/factories.py`. They contain **no real PII** and no PDFs.
- **`client`** — a `fastapi.testclient.TestClient` over the *real* app object,
  created **without** the lifespan context manager. This means `init_db()`,
  `init_tax_tables()`, `FernetEncryptionService()`, and `start_scheduler()`
  never run during tests. The System Under Test is the genuine app wiring; we
  do not mock away the app, only its startup side effects.
- `conftest.py` sets a test-only `TAXSTOX_JWT_SECRET` so the auth router
  imports cleanly. It does **not** set `DATABASE_URL`.

## 4. Real-data E2E (`test_e2e_real_data.py`)

Disabled by default. To run it, set **all** of:

```bash
export TAXSTOX_E2E_FORM16_PATH=/path/to/Form16.pdf
export TAXSTOX_E2E_AIS_PATH=/path/to/AIS.pdf
export TAXSTOX_E2E_PAN=<PAN>            # also the Form 16 PDF password
export TAXSTOX_E2E_DOB=DDMMYYYY         # derives the AIS PDF password
export TAXSTOX_E2E_FORM16_PASSWORD=<PAN>  # optional; defaults to PAN
```

If any is missing, or the PDFs don't exist, the **entire module skips** with an
explicit reason — it never reports a fake pass and never aborts collection.
Golden values in `EXPECTED` are for one specific historical filing; the
assertions fail loudly on drift.

## 5. Rules (do not violate)

- **Do not restore `src/engine/regime_optimizer` (v1).** `RegimeOptimizerV2` is
  the canonical implementation. The retired v1 optimizer must remain retired.
- **No real PII** in the repo. PANs/DOBs in tests are synthetic.
- **Don't mock the SUT to make a test pass.** API tests use the real app; only
  startup side effects are bypassed.
- **Don't weaken an assertion** to obtain a green run. Fix the root cause.
- **Don't modify production tax/business logic** for test convenience. If a
  genuine PR4-scoped defect is found, document it and escalate.

## 6. Skips are expected, not failures

- `db_required` tests skip unless `DATABASE_URL` is set.
- `jwt_required` tests skip unless `TAXSTOX_JWT_SECRET` is set.
- The real-data E2E skips unless §4 env vars + PDFs are present.
- `test_export` in `test_api_filing.py` asserts structural completeness, **not**
  `validation_passed` — the seeded session's `unified_data` has `dob=None`, so
  the DOB check legitimately fails (that is production behavior). Fileability
  is covered in `test_itr_builders.py` with a populated DOB.

## 7. Golden vectors

`test_golden_vectors.py` holds 9 ITD-verified expected values. These must not
change without an explicit, documented tax-rule change.
