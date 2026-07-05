# Quality Gate Framework

> **Date:** 2026-07-05
> **Derived From:** Constitution §9 (Quality Imperatives), Engineering Standards, Testing Standards (to be created), Gap Report

---

## Gate Definitions

### G1: Architecture Review

| Attribute | Value |
|-----------|-------|
| **When** | Before any wave begins; after wave output stabilizes |
| **Who** | Chief Architect + Architecture Review Board |
| **Criteria** | Wave output aligns with ECM target; no new constitutional violations; ADRs written for all architecture decisions |
| **Blocking** | Yes — cannot proceed to next wave |

### G2: Code Quality

| Attribute | Value |
|-----------|-------|
| **When** | Every PR; final verification before wave exit |
| **Who** | CI pipeline (automated) + peer reviewer |
| **Criteria** | Ruff lint: 0 errors; MyPy strict: 0 errors; Radon complexity: CC ≤ 10 per function; No `import *`; No bare `except:` |
| **Blocking** | Yes — PR cannot merge |

### G3: Security Review

| Attribute | Value |
|-----------|-------|
| **When** | Every PR touching auth, data access, API, file upload, dependency |
| **Who** | CI pipeline (Bandit) + Security Lead (for sensitive changes) |
| **Criteria** | Bandit: 0 HIGH/MEDIUM; No secrets in code; No new dependencies without security review; Input validated at every trust boundary |
| **Blocking** | Yes |

### G4: Test Coverage

| Attribute | Value |
|-----------|-------|
| **When** | Every PR; wave exit |
| **Who** | CI pipeline (pytest-cov) |
| **Criteria** | Coverage does not decrease from previous wave; New code ≥ 85% coverage; All golden-test-vectors pass |
| **Blocking** | Yes |

### G5: Regression Testing

| Attribute | Value |
|-----------|-------|
| **When** | Wave exit |
| **Who** | CI pipeline |
| **Criteria** | Full test suite passes; Golden vectors: M1+ output = pre-M1 output for FY2025-26; No existing functionality broken |
| **Blocking** | Yes |

### G6: Performance Validation

| Attribute | Value |
|-----------|-------|
| **When** | Wave exit (waves with computation changes) |
| **Who** | DevOps Lead |
| **Criteria** | p95 latency ≤ 110% of baseline; No N+1 queries introduced; Memory usage within baseline |
| **Blocking** | Yes (warning for M0-M2; blocking from M3+) |

### G7: Documentation Review

| Attribute | Value |
|-----------|-------|
| **When** | Every PR; wave exit |
| **Who** | Peer reviewer |
| **Criteria** | Module README updated; ADR written if architecture changed; API docs updated; Project memory updated |
| **Blocking** | Yes |

### G8: Domain Review

| Attribute | Value |
|-----------|-------|
| **When** | Any tax rule change, new deduction, new income head |
| **Who** | Domain Expert (CA) |
| **Criteria** | Tax computation verified against ITD portal reference; Legal provision referenced; Edge cases reviewed |
| **Blocking** | Yes (tax waves M1-M5 only) |

### G9: Deployment Readiness

| Attribute | Value |
|-----------|-------|
| **When** | Wave exit |
| **Who** | DevOps Lead |
| **Criteria** | Successful staging deploy; Smoke test passed; Rollback plan documented; Database migrations tested (forward + rollback); Feature flags configured (if gradual rollout) |
| **Blocking** | Yes |

---

## Wave-by-Wave Gate Applicability

| Wave | G1 | G2 | G3 | G4 | G5 | G6 | G7 | G8 | G9 |
|------|----|----|----|----|----|----|----|----|----|
| M0 | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | — | ✅ |
| M1 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| M2 | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | — | ✅ |
| M3 | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ |
| M4 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| M5 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| M6 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| M7 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| M8 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| M9 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| M10 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| M11 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |

---

## CI Pipeline Configuration (M0 establishes)

```yaml
# Conceptual — not implementation
gates:
  - lint:        { tool: ruff, blocking: true }
  - typecheck:   { tool: mypy --strict, blocking: true }
  - complexity:  { tool: radon, max_cc: 10, blocking: false }
  - security:    { tool: bandit, blocking: true }
  - unit_test:   { tool: pytest, min_coverage: 85, blocking: true }
  - golden_test: { tool: pytest, blocking: true }
```

---

*End of Quality Gate Framework v1.0*
