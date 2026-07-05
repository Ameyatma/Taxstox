# Domain Modernization Matrix

> **Date:** 2026-07-05
> **Derived From:** Domain Maturity Matrix (14% coverage), Enterprise Gap Report

---

## Per-Bounded-Context Modernization Plan

### BC1: Identity & Access

| Attribute | Value |
|-----------|-------|
| Current Maturity | 2.1/6.0 (23%) |
| Target Maturity | 5.0/6.0 |
| Primary Wave(s) | M0 (session), M8 (RBAC), M9 (MFA, consent) |
| Current Issues | No RBAC, no MFA, dev JWT secret, no consent |
| Preserve | JWT auth, Google OAuth flow, user model |
| Refactor | JWT secret management, session storage (→ Redis) |
| Replace | — |
| Retire | Hardcoded dev secret (SEC-001) |
| Migration Complexity | **High** |
| Business Priority | **Critical** |
| Risk Level | **Medium** |

### BC2: Taxpayer

| Attribute | Value |
|-----------|-------|
| Current Maturity | 1.7/6.0 (20%) |
| Target Maturity | 4.5/6.0 |
| Primary Wave(s) | M3 (residential status), M8 (multi-tenant profile) |
| Current Issues | Hardcoded "RES" status, no profile verification, no filing history |
| Preserve | User model basics |
| Refactor | Taxpayer profile separation from auth |
| Replace | — |
| Retire | — |
| Migration Complexity | **Medium** |
| Business Priority | **High** |
| Risk Level | **Low** |

### BC3: Document Processing

| Attribute | Value |
|-----------|-------|
| Current Maturity | 2.8/6.0 (37%) |
| Target Maturity | 5.0/6.0 |
| Primary Wave(s) | M2 |
| Current Issues | No OCR, no 26AS, limited broker support, no confidence scoring |
| Preserve | Form 16 parser, AIS parser, AIS code mapper |
| Refactor | Add confidence scoring layer |
| Replace | — |
| Retire | — |
| Migration Complexity | **Medium** |
| Business Priority | **High** |
| Risk Level | **Low** |

### BC4: Income

| Attribute | Value |
|-----------|-------|
| Current Maturity | 1.6/6.0 (20%) |
| Target Maturity | 4.5/6.0 |
| Primary Wave(s) | M3 |
| Current Issues | Only salary + partial CG; no house property, business, foreign income |
| Preserve | Salary computer, capital gains engine (classifier) |
| Refactor | Extract CG classification to use rule repository |
| Replace | — |
| Retire | — |
| Migration Complexity | **High** |
| Business Priority | **High** |
| Risk Level | **Medium** |

### BC5: Tax Computation

| Attribute | Value |
|-----------|-------|
| Current Maturity | 2.5/6.0 (32%) |
| Target Maturity | 5.0/6.0 |
| Primary Wave(s) | M1 (rule extraction), M4 (complete computation) |
| Current Issues | Hardcoded FY, duplicate optimizers, no interest 234A/B/C, limited special rates |
| Preserve | ITD portal-matched computation logic in v2 |
| Refactor | Extract rules → repository; unify optimizers |
| Replace | Hardcoded constants → rule repository |
| Retire | `regime_optimizer.py` (v1) |
| Migration Complexity | **Very High** |
| Business Priority | **Critical** |
| Risk Level | **High** |

### BC6: Compliance

| Attribute | Value |
|-----------|-------|
| Current Maturity | 1.4/6.0 (16%) |
| Target Maturity | 4.5/6.0 |
| Primary Wave(s) | M5 |
| Current Issues | Only ITR-1/2 builders; no tax credit reconciliation; limited validation |
| Preserve | ITR-1/2 builders, ITR validator (40+ checks) |
| Refactor | Extract base builder; validator → pluggable rules |
| Replace | — |
| Retire | — |
| Migration Complexity | **High** |
| Business Priority | **High** |
| Risk Level | **Medium** |

### BC7: Audit & Explanation

| Attribute | Value |
|-----------|-------|
| Current Maturity | 0.3/6.0 (3%) |
| Target Maturity | 4.0/6.0 |
| Primary Wave(s) | M6 |
| Current Issues | No audit trail, no explanation engine, no legal tracer |
| Preserve | Recommendation engine (regime explanation) |
| Refactor | — (entirely new context) |
| Replace | — |
| Retire | — |
| Migration Complexity | **High** |
| Business Priority | **Critical** |
| Risk Level | **Medium** |

### BC8: Knowledge & Rules

| Attribute | Value |
|-----------|-------|
| Current Maturity | 0.2/6.0 (2%) |
| Target Maturity | 4.0/6.0 |
| Primary Wave(s) | M1 (rules), M7 (knowledge graph) |
| Current Issues | No rule repository, no knowledge graph, no provision KB |
| Preserve | AIS code mapper (becomes part of knowledge graph) |
| Refactor | — (entirely new context) |
| Replace | — |
| Retire | — |
| Migration Complexity | **Very High** |
| Business Priority | **Critical** |
| Risk Level | **High** |

### BC9: Interview

| Attribute | Value |
|-----------|-------|
| Current Maturity | 2.4/6.0 (27%) |
| Target Maturity | 4.5/6.0 |
| Primary Wave(s) | M7 |
| Current Issues | Hardcoded questions, no personalization, no offline |
| Preserve | Question engine, auto-detection engine |
| Refactor | Extract questions to configurable library |
| Replace | — |
| Retire | — |
| Migration Complexity | **Medium** |
| Business Priority | **Medium** |
| Risk Level | **Low** |

### BC10: Reporting

| Attribute | Value |
|-----------|-------|
| Current Maturity | 0.9/6.0 (9%) |
| Target Maturity | 3.5/6.0 |
| Primary Wave(s) | M5 (tax summary), M8 (firm dashboard) |
| Migration Complexity | **Medium** |
| Business Priority | **Medium** |

### BC11: Integration

| Attribute | Value |
|-----------|-------|
| Current Maturity | 0.6/6.0 (6%) |
| Target Maturity | 3.5/6.0 |
| Primary Wave(s) | M10 |
| Migration Complexity | **High** |
| Business Priority | **Medium** |

### BC12: Operations

| Attribute | Value |
|-----------|-------|
| Current Maturity | 1.1/6.0 (11%) |
| Target Maturity | 4.5/6.0 |
| Primary Wave(s) | M0 (CI/CD, logging), M11 (observability, DR) |
| Migration Complexity | **Medium** |
| Business Priority | **High** |

### BC13: Security

| Attribute | Value |
|-----------|-------|
| Current Maturity | 0.3/6.0 (4%) |
| Target Maturity | 4.5/6.0 |
| Primary Wave(s) | M9 |
| Migration Complexity | **Very High** |
| Business Priority | **Critical** |

### BC14: Notification

| Attribute | Value |
|-----------|-------|
| Current Maturity | 0.0/6.0 (0%) |
| Target Maturity | 3.0/6.0 |
| Primary Wave(s) | M10 (alongside integration) |
| Migration Complexity | **Medium** |
| Business Priority | **Medium** |

### BC15: Tax Planning

| Attribute | Value |
|-----------|-------|
| Current Maturity | 0.0/6.0 (0%) |
| Target Maturity | 2.5/6.0 |
| Primary Wave(s) | Post-M11 (future) |
| Migration Complexity | **Medium** |
| Business Priority | **Low** |

---

## Maturity Trajectory

| Checkpoint | Overall Maturity | Best BC | Worst BC |
|-----------|-----------------|---------|----------|
| Pre-M0 (current) | 14% (1.2/6.0) | BC3: 2.8 | BC8: 0.2 |
| After M1 | 22% | BC3: 2.8 | BC14: 0.0 |
| After M5 | 40% | BC3: 5.0 | BC14: 0.0 |
| After M8 | 58% | BC3: 5.0 | BC15: 0.0 |
| After M11 | 72% | BC3: 5.0 | BC15: 2.5 |

---

*End of Domain Modernization Matrix v1.0*
