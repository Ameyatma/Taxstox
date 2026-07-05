# M0 Wave Execution Plan — Engineering Foundation

> **Status:** EXECUTION PLAN — Awaiting approval before code changes
> **Date:** 2026-07-05
> **Wave:** M0 — Engineering Foundation
> **Roadmap Reference:** [EnterpriseModernizationRoadmap.md](EnterpriseModernizationRoadmap.md) §Wave 0
> **Prerequisites:** Repository consolidation (COMPLETE), Documentation topology (COMPLETE)

---

## 1. Wave Objective

Establish the engineering practices, testing infrastructure, CI/CD pipeline, structured logging, and safety nets required before any architectural modernization can safely proceed. This wave does NOT change business logic. It adds the guardrails that make all future waves safe.

## 2. Traceability

Every action in this wave traces to documented findings in frozen architecture artifacts.

### Gap IDs Addressed

| Gap | Current State | Target (Post-M0) |
|-----|---------------|------------------|
| Testing Gaps (Universal) | 0 unit tests, 0 integration tests, 1 skeleton E2E file | pytest framework, ≥100 unit tests, golden-vector framework |
| Observability Gaps (Universal) | f-string logging only; no metrics, tracing, or alerting | Structured JSON logging, basic metrics, health checks |
| DevOps Gaps (DEV-001, DEV-002) | No CI/CD; no migration framework | CI pipeline (lint+type+test+security); Alembic initialized |

### Capability IDs Addressed

| Capability | Current Maturity | Target Maturity |
|-----------|-----------------|-----------------|
| C17.4 CI/CD Pipeline | 20% | 60% |
| C17.2 Monitoring | 10% | 40% |
| C17.3 Structured Logging | 10% | 60% |
| C12.5 Rule Testing Framework | 0% | 30% |

### Technical Debt Addressed

| Debt ID | Description | Severity | Action |
|---------|-------------|----------|--------|
| TST-001 | Zero automated tests | Critical | Establish pytest + write initial test suite |
| TST-002 | No test framework structure | High | Create conftest.py, fixtures, parametrize patterns |
| DEV-001 | No CI/CD pipeline | High | Create GitHub Actions workflow |
| DEV-002 | No migration framework | High | Initialize Alembic |
| OPS-001 | No structured logging | High | Replace f-strings with JSON logging |
| SEC-001 | Dev JWT secret hardcoded | Critical | Remove hardcoded default; enforce env var |
| SEC-006 | PDF passwords logged | High | Mask passwords in log output |
| COD-007 | f-string logging throughout | Medium | Replace with structured logging |
| COD-009 | Bare except Exception | Low | Fix in modules touched by testing |

### Risks Mitigated

| Risk ID | Risk | Mitigation |
|---------|------|-----------|
| R04 | Zero testing → tax errors in production | M0 establishes test framework; all future changes tested |
| R03 | Security breach (PII) | SEC-001 fix removes hardcoded secret; SEC-006 fix masks passwords |

## 3. Scope

### In Scope

| # | Work Item | Type | Priority |
|---|-----------|------|----------|
| 1 | Initialize pytest framework with conftest, fixtures, parametrize patterns | **INFRA** | P0 |
| 2 | Write unit tests for `engine/salary_computer.py` | **TEST** | P0 |
| 3 | Write unit tests for `engine/deductions_computer.py` | **TEST** | P0 |
| 4 | Write unit tests for `engine/classifier.py` | **TEST** | P0 |
| 5 | Write unit tests for `models/form16.py` (validation logic) | **TEST** | P1 |
| 6 | Write unit tests for `models/tax.py` (CG classification logic) | **TEST** | P1 |
| 7 | Establish golden-test-vector framework for tax computation | **TEST** | P0 |
| 8 | Create 3 golden test vectors (known inputs → expected ITR JSON) | **TEST** | P0 |
| 9 | Create GitHub Actions CI workflow: lint → type-check → test → security | **CI** | P0 |
| 10 | Initialize Alembic for database migrations | **INFRA** | P1 |
| 11 | Implement structured JSON logging across all modules | **LOG** | P0 |
| 12 | Add correlation ID middleware (request_id propagation) | **LOG** | P0 |
| 13 | Add PII masking to all log statements (PAN, Aadhaar, passwords) | **LOG** | P0 |
| 14 | Enhance health check endpoint with DB connectivity status | **OPS** | P1 |
| 15 | Remove hardcoded JWT dev secret; enforce `TAXSTOX_JWT_SECRET` env var | **SEC** | P0 |
| 16 | Mask PDF passwords in log output (replace with `***`) | **SEC** | P0 |
| 17 | Verify `.gitignore` — no secrets, caches, or artifacts tracked | **OPS** | P1 |
| 18 | Add `ruff format` check to CI | **CI** | P1 |
| 19 | Add `mypy --strict` to CI | **CI** | P1 |
| 20 | Add `bandit` security scan to CI | **CI** | P1 |

### Out of Scope (Deferred to Later Waves)

- Refactoring production code for testability beyond minimal dependency injection
- Extracting tax rules to repository (M1)
- Adding Redis for sessions (M11)
- Adding Prometheus/Grafana monitoring stack (M11)
- Adding alerting (M11)
- Writing integration/E2E tests beyond golden vectors (M5+)
- Adding new business logic or features
- Changing any computation logic

## 5. Required Code Changes

### 5.1 New Files

| File | Purpose | Lines (est.) |
|------|---------|-------------|
| `apps/api/tests/conftest.py` | Shared fixtures: sample Form16Data, AISData, UserAnswers | ~80 |
| `apps/api/tests/test_salary_computer.py` | Unit tests for SalaryComputer | ~200 |
| `apps/api/tests/test_deductions_computer.py` | Unit tests for DeductionsComputer | ~200 |
| `apps/api/tests/test_classifier.py` | Unit tests for ClassificationEngine | ~200 |
| `apps/api/tests/test_models_form16.py` | Unit tests for Form 16 model validation | ~100 |
| `apps/api/tests/test_models_tax.py` | Unit tests for CG classification models | ~100 |
| `apps/api/tests/test_golden_vectors.py` | Golden-test-vector framework + 3 vectors | ~150 |
| `apps/api/tests/fixtures/sample_form16_data.py` | Factory for sample Form16Data | ~100 |
| `apps/api/tests/fixtures/sample_ais_data.py` | Factory for sample AISData | ~80 |
| `apps/api/src/utils/logging.py` | Structured JSON logging setup + PII masker | ~100 |
| `apps/api/src/middleware/correlation.py` | Correlation ID middleware | ~40 |
| `apps/api/alembic.ini` | Alembic configuration | ~60 |
| `apps/api/alembic/env.py` | Alembic environment | ~80 |
| `apps/api/alembic/versions/001_initial.py` | Initial migration (current schema) | ~40 |
| `.github/workflows/ci.yml` | CI pipeline: lint, type, test, security | ~80 |

### 5.2 Modified Files

| File | Change | Risk |
|------|--------|------|
| `apps/api/src/main.py` | Add correlation middleware; enhance health check; structured logging init | Low |
| `apps/api/src/auth/jwt.py:12` | Remove hardcoded default `SECRET_KEY`; raise if env var missing | Low |
| All `*.py` files (~42) | Replace `logger.info(f"...")` with `logger.info("...", extra={...})` | Low |
| `apps/api/src/api/routes.py:92` | Mask password in log: `pwd=***` instead of `pwd={pwd}` | Low |

### 5.3 No-Change Modules

| Module | Reason |
|--------|--------|
| All `engine/*.py` (computation logic) | Business logic unchanged. Tests verify, don't modify. |
| All `models/*.py` (domain models) | Tests verify validation; models unchanged. |
| All `parsers/*.py` | Unchanged. |
| All `builders/*.py` | Unchanged. |
| `apps/web/` (frontend) | No changes this wave. |

## 6. Required Database Changes

**None.** M0 does not modify the database schema.

Alembic is initialized with the current schema as the baseline migration (`001_initial.py`). This captures the existing state without changing it.

## 7. Required API Changes

**None.** All existing API endpoints, contracts, and responses are preserved.

The health check endpoint (`GET /api/v1/health`) is enhanced to include DB connectivity status — this is an additive change (new fields) that does not break existing consumers.

## 8. Required Test Changes

### 8.1 Test Framework Setup

```
apps/api/tests/
├── conftest.py                    # Shared fixtures
├── fixtures/
│   ├── sample_form16_data.py      # Test data factories
│   └── sample_ais_data.py
├── test_salary_computer.py        # 15-20 tests
├── test_deductions_computer.py    # 15-20 tests
├── test_classifier.py             # 15-20 tests
├── test_models_form16.py          # 10 tests
├── test_models_tax.py             # 10 tests
├── test_golden_vectors.py         # 3 golden vectors
└── golden_vectors/
    ├── input_fy2025_26_salaried.json
    ├── expected_itr2_fy2025_26_salaried.json
    ├── input_fy2025_26_capital_gains.json
    ├── expected_itr2_fy2025_26_capital_gains.json
    ├── input_fy2025_26_both.json
    └── expected_itr2_fy2025_26_both.json
```

### 8.2 Test Coverage Targets

| Module | Target Coverage | Test Count (est.) |
|--------|----------------|-------------------|
| `engine/salary_computer.py` | ≥ 85% | 15-20 |
| `engine/deductions_computer.py` | ≥ 85% | 15-20 |
| `engine/classifier.py` | ≥ 85% | 15-20 |
| `models/form16.py` | ≥ 90% | 10 |
| `models/tax.py` | ≥ 90% | 10 |
| **Overall** | ≥ 30% | ~100 |

### 8.3 Golden Test Vectors

Three golden vectors capturing known-good behavior:

| Vector | Input | Expected Output | Covers |
|--------|-------|-----------------|--------|
| GV-1 | Salaried individual, Form 16 only, Old Regime | Known tax liability from ITD portal | Salary + deductions + slab tax |
| GV-2 | Salaried + capital gains, Form 16 + AIS, New Regime | Known tax liability from ITD portal | CG classification + 112A exemption + special rates |
| GV-3 | Salaried + capital gains, both regimes compared | Known optimal regime from ITD portal | Regime comparison + optimizer output |

Golden vectors are based on anonymous real-world tax computations verified against the ITD portal. They serve as regression tests: if any future change alters the output, the CI pipeline blocks it.

## 9. Required Documentation Updates

| Document | Update |
|----------|--------|
| `docs/ai-dos/memory/CompletedFeatures.md` | Log M0 completion with acceptance evidence |
| `docs/ai-dos/memory/Decisions.md` | Log decisions: test framework selection, CI tooling, logging format |
| `docs/ai-dos/memory/TechnicalDebt.md` | Mark resolved debt items (TST-001, TST-002, DEV-001, DEV-002, SEC-001, SEC-006, COD-007) |
| `docs/architecture/ArchitectureHealthScore.md` | Update scores: Testability 10→35, Observability 10→35, Security 15→25 |
| `README.md` | Update test/CI badges; add quick-start for test execution |
| `HANDOFF.md` | Session log entry for M0 completion |

## 10. Required Migration Steps

**No data migration required.** M0 is additive only.

The only "migration" is Alembic initialization:
1. `alembic init` — creates `alembic/` directory
2. `alembic revision --autogenerate -m "initial"` — captures current schema as baseline
3. `alembic upgrade head` — marks baseline as applied (no schema change)

## 11. Quality Gates

Per [QualityGateFramework.md](QualityGateFramework.md), the following gates apply:

| Gate | Criteria | Blocking? |
|------|----------|-----------|
| **G2: Code Quality** | Ruff: 0 errors; MyPy strict: 0 errors; No new lint violations | Yes |
| **G3: Security Review** | Bandit: 0 HIGH/MEDIUM; SEC-001 resolved; SEC-006 resolved | Yes |
| **G4: Test Coverage** | ≥ 30% overall; ≥ 85% on new code; all golden vectors pass | Yes |
| **G7: Documentation** | All 6 docs updated per §9 | Yes |
| **G9: Deployment** | Staging deploy successful; smoke test passed | Yes |

**Gates NOT applicable to M0:** G1 (Architecture Review — no architectural changes), G5 (Regression — no existing tests to regress), G6 (Performance — no computation changes), G8 (Domain Review — no tax rule changes)

## 12. Acceptance Criteria

- [ ] **AC-1:** `pytest` executes successfully; ≥ 100 tests; 0 failures
- [ ] **AC-2:** `pytest --cov` reports ≥ 30% overall coverage
- [ ] **AC-3:** All 3 golden test vectors pass with output matching expected JSON byte-for-byte
- [ ] **AC-4:** `ruff check .` returns 0 errors
- [ ] **AC-5:** `mypy . --strict` returns 0 errors
- [ ] **AC-6:** `bandit -c pyproject.toml .` returns 0 HIGH/MEDIUM findings
- [ ] **AC-7:** CI pipeline executes on push to `main`; all steps pass
- [ ] **AC-8:** CI pipeline blocks merge on any step failure
- [ ] **AC-9:** All log statements produce structured JSON (verified by sampling)
- [ ] **AC-10:** Correlation ID present in all request log lines
- [ ] **AC-11:** No PAN, Aadhaar, or password values in log output
- [ ] **AC-12:** `TAXSTOX_JWT_SECRET` env var mandatory; startup fails without it
- [ ] **AC-13:** Health check returns DB connectivity status
- [ ] **AC-14:** `alembic upgrade head` completes without error
- [ ] **AC-15:** `.gitignore` prevents tracking of `__pycache__`, `.venv`, `.env`, `*.pyc`, `apps/api/data/`
- [ ] **AC-16:** All existing API endpoints return identical responses to pre-M0
- [ ] **AC-17:** Frontend (`apps/web/`) builds and functions unchanged
- [ ] **AC-18:** All documentation updated per §9

## 13. Rollback Criteria

**Automatic rollback triggers:**
- Any existing API endpoint returns a different response than pre-M0
- Frontend fails to build or function
- CI pipeline prevents deployment (gate failure)

**Rollback procedure:**
1. Revert the M0 commit: `git revert <M0-commit>`
2. Verify staging: run smoke test
3. Deploy the reverted version
4. All M0 changes are additive — rollback simply removes new files and reverts modified files

**Rollback is safe because:** M0 does not change business logic, API contracts, database schema, or frontend code. All changes are either new files (tests, CI config, logging utilities) or cosmetic modifications to existing files (logging format).

## 14. Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Writing tests reveals bugs in existing code | Medium | Low — beneficial | Fix bugs as separate PRs; do not block M0 on pre-existing bugs |
| Logging changes accidentally change log levels | Low | Low | Log level preserved; only format changes |
| CI pipeline too slow | Low | Medium | Parallelize test execution; fast-fail lint/type before tests |
| Hardcoded JWT secret removal breaks Render deploy | Low | High | Coordinate with Render env var configuration before deploy; verify in staging |
| Golden vector JSON mismatches due to Decimal serialization | Medium | Medium | Use `Decimal`-aware JSON comparison; normalize before comparison |

## 15. Estimated Effort

| Activity | Effort |
|----------|--------|
| Test framework setup + conftest + fixtures | 2 days |
| Unit tests (5 modules, ~100 tests) | 5 days |
| Golden vector framework + 3 vectors | 2 days |
| CI pipeline (GitHub Actions) | 1 day |
| Alembic initialization | 0.5 days |
| Structured logging conversion (42 files) | 2 days |
| Correlation ID middleware | 0.5 days |
| PII masking | 1 day |
| Health check enhancement | 0.5 days |
| JWT secret fix | 0.5 days |
| Documentation updates | 1 day |
| Staging verification + bug fixes | 2 days |
| **TOTAL** | **~18 days (~3.5 weeks)** |

Fit within the roadmap estimate of **4 weeks**.

## 16. Execution Order

```
DAY 1-2:   Test framework setup (conftest, fixtures, factories)
DAY 3-7:   Write unit tests (5 modules, ~100 tests)
DAY 8-9:   Golden vector framework + 3 vectors
DAY 10:    CI pipeline (GitHub Actions)
DAY 10:    Alembic initialization
DAY 11-12: Structured logging conversion (all 42 files)
DAY 13:    Correlation ID middleware
DAY 13:    PII masking
DAY 14:    Health check enhancement
DAY 14:    JWT secret fix (coordinate with Render)
DAY 15:    Documentation updates
DAY 16-18: Staging verification + bug fixes + final gate checks
```

---

*End of M0 Wave Execution Plan v1.0*
*Awaiting approval before any code changes begin.*

*This plan does NOT contain implementation code. It defines WHAT will be done, not HOW.*
