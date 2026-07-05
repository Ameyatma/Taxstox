# Technical Debt Memory — ARCHIVED v0.1

> **⚠️ SUPERSEDED — This document is archived and no longer active.**
> **Superseded By:** [TechnicalDebtHeatmap.md](../../gap-analysis/TechnicalDebtHeatmap.md)
> **Supersession Date:** 2026-07-05
> **Reason:** This version tracked 15 conceptual debt items from pre-implementation planning. The Technical Debt Heatmap (15,279 bytes) provides 64 evidence-backed debt items across 9 categories, all sourced from a 42-module source code audit with file and line references.
> **Retention:** Preserved for historical reference only. All debt items have been transferred to the superseding document.
>
> ---
>
> **Original Purpose:** Complete register of all technical debt.
> **Original Updated By:** Architect Agent — every session.
> **Original Last Updated:** 2026-07-05
> **Original Session ID:** INIT
> **Cross-Refs:** [Architecture.md](Architecture.md), [KnownIssues.md](KnownIssues.md), [Decisions.md](Decisions.md)

---

## 1. Debt Classification

| Type | Marker | Severity | Max Age | Remediation Budget |
|------|--------|----------|---------|--------------------|
| **Constitutional** | `CONSTITUTIONAL_DEBT` | Critical | 2 sprints | 20% of sprint capacity |
| **Architectural** | `ARCHITECTURAL_DEBT` | High | 3 sprints | 20% of sprint capacity |
| **Code** | `CODE_DEBT` | Medium | 5 sprints | 10% of sprint capacity |
| **Test** | `TEST_DEBT` | Medium | 5 sprints | 10% of sprint capacity |
| **Documentation** | `DOC_DEBT` | Low | 8 sprints | 5% of sprint capacity |
| **Dependency** | `DEP_DEBT` | Varies by CVE | Per CVE severity | 5% of sprint capacity |

## 2. Active Debt Register

### 2.1 Constitutional Debt (Critical)

| Debt ID | Description | Module | Created | Deadline | Owner | Status |
|---------|-------------|--------|---------|----------|-------|--------|
| CD-001 | Hardcoded FY2025-26 rules violate I2 (Rule-Engine Separation) | All engine/ modules | 2026-07-05 | 2026-08-16 | Chief Architect | OPEN |
| CD-002 | Single FY architecture violates I1 (Multi-Year) | All modules | 2026-07-05 | 2026-08-16 | Chief Architect | OPEN |
| CD-003 | Zero audit trail violates I3 (Complete Audit Trail) | All engine/ modules | 2026-07-05 | 2026-09-01 | Chief Architect | OPEN |
| CD-004 | No explainability infrastructure violates I4 | All modules | 2026-07-05 | 2026-09-15 | Chief Architect | OPEN |
| CD-005 | Hardcoded config violates I8 (Configurable Everything) | engine/, builders/ | 2026-07-05 | 2026-08-16 | Chief Architect | OPEN |

### 2.2 Architectural Debt (High)

| Debt ID | Description | Module | Created | Deadline | Owner | Status |
|---------|-------------|--------|---------|----------|-------|--------|
| AD-001 | Dual optimizer implementations (v1 + v2) | engine/regime_optimizer*.py | 2026-07-05 | 2026-08-30 | Tech Lead | OPEN |
| AD-002 | No base class for ITR builders | builders/ | 2026-07-05 | 2026-09-15 | Tech Lead | OPEN |
| AD-003 | Tax slab computation duplicated in 3 locations | engine/, builders/ | 2026-07-05 | 2026-08-30 | Tech Lead | OPEN |
| AD-004 | Circular dependency (lazy import workaround) | engine/regime_optimizer_v2.py:334 | 2026-07-05 | 2026-08-16 | Tech Lead | OPEN |
| AD-005 | No bounded context separation | All modules | 2026-07-05 | 2026-12-31 | Chief Architect | OPEN |
| AD-006 | In-memory sessions prevent horizontal scaling | utils/session.py | 2026-07-05 | 2026-09-01 | DevOps Lead | OPEN |
| AD-007 | Deduction limits replicated across engine and validator | engine/deductions_computer.py, builders/validator.py | 2026-07-05 | 2026-08-30 | Tech Lead | OPEN |
| AD-008 | No feature flag infrastructure | All modules | 2026-07-05 | 2026-10-01 | DevOps Lead | OPEN |
| AD-009 | Raw SQL without migration framework | db/database.py | 2026-07-05 | 2026-09-15 | Tech Lead | OPEN |
| AD-010 | DTOs used as domain models — Pydantic serves dual purpose | models/ | 2026-07-05 | 2026-10-01 | Chief Architect | OPEN |

| Debt ID | Description | Module | Created | Deadline | Owner | Status |
|---------|-------------|--------|---------|----------|-------|--------|
| *No architectural debt yet* | — | — | — | — | — | — |

### 2.3 Code Debt (Medium)

| Debt ID | Description | Module | Created | Deadline | Owner | Status |
|---------|-------------|--------|---------|----------|-------|--------|
| *No code debt yet* | — | — | — | — | — | — |

### 2.4 Test Debt (Medium)

| Debt ID | Description | Module | Created | Deadline | Owner | Status |
|---------|-------------|--------|---------|----------|-------|--------|
| *No test debt yet* | — | — | — | — | — | — |

### 2.5 Documentation Debt (Low)

| Debt ID | Description | Module | Created | Deadline | Owner | Status |
|---------|-------------|--------|---------|----------|-------|--------|
| *No documentation debt yet* | — | — | — | — | — | — |

### 2.6 Dependency Debt

| Debt ID | Dependency | Current Version | Target Version | CVE (if any) | Deadline | Owner | Status |
|---------|------------|-----------------|----------------|--------------|----------|-------|--------|
| *No dependency debt yet* | — | — | — | — | — | — | — |

## 3. Debt Ceiling (Hard Limits)

If these limits are exceeded, ALL feature development stops until debt is reduced:

| Metric | Limit | Current | Status |
|--------|-------|---------|--------|
| Constitutional debt items | ≤ 5 | 0 | ✅ OK |
| Architectural debt items | ≤ 20 | 0 | ✅ OK |
| Total code debt items | ≤ 100 | 0 | ✅ OK |
| Items past deadline | 0 | 0 | ✅ OK |
| Dependency CVEs (High+) | 0 | 0 | ✅ OK |

## 4. Debt Incurrence Process

When creating necessary debt (knowingly taking a shortcut):

```
DEBT INCURRENCE:
1. Add debt marker comment in code (see template below)
2. Register debt in this file
3. Get approval from Tech Lead or Chief Architect
4. Set a firm remediation deadline (not "someday")
5. Add remediation task to sprint backlog

DEBT MARKER TEMPLATE:

# CONSTITUTIONAL_DEBT(YYYY-MM-DD, P#):
# [Brief description of the violation]
# Must remediate by: YYYY-MM-DD
# Owner: @github-handle
# ADR: [if applicable]
# Issue: ISS-XXXX

# ARCHITECTURAL_DEBT(YYYY-MM-DD):
# [Brief description]
# Must remediate by: YYYY-MM-DD
# Owner: @github-handle

# CODE_DEBT(YYYY-MM-DD):
# [Brief description]
# Must remediate by: YYYY-MM-DD
# Owner: @github-handle
```

## 5. Debt Repayment Strategy

### 5.1 Regular Repayment

Every sprint allocates capacity for debt reduction:

| Sprint Type | Debt Budget |
|-------------|-------------|
| Feature sprint | 20% of total capacity |
| Maintenance sprint (every 6th sprint) | 100% of capacity |
| Pre-release sprint | 50% of capacity |

### 5.2 Repayment Priority

When choosing which debt to repay, prioritize in this order:

1. **P0:** Debt causing active incidents or blocking critical work
2. **P1:** Constitutional debt (must be resolved within 2 sprints per Constitution)
3. **P2:** Architectural debt past or near deadline
4. **P3:** Code/test debt that blocks feature development in active modules
5. **P4:** Dependency debt with known CVEs
6. **P5:** All other debt, oldest first

### 5.3 Debt Sprint (Every 6th Sprint)

The maintenance sprint is dedicated to:
- Resolving all constitutional and architectural debt
- Upgrading dependencies
- Improving test coverage in weak areas
- Updating documentation
- Refactoring high-churn modules
- No new features (except P0 bug fixes)

## 6. Debt Metrics (Tracked Per Sprint)

| Metric | Current | Target | Trend |
|--------|---------|--------|-------|
| Total debt items | 0 | < 50 | — |
| Constitutional debt | 0 | 0 | — |
| Architectural debt | 0 | ≤ 5 | — |
| Past-deadline items | 0 | 0 | — |
| Average debt age (days) | 0 | < 30 | — |
| Debt resolution rate (per sprint) | N/A | ≥ 5 items | — |
| Debt incurrence rate (per sprint) | N/A | < resolution rate | — |

---

## Session Log

| Date | Session ID | Changes Made | Agent |
|------|-----------|--------------|-------|
| 2026-07-05 | INIT | Technical debt memory initialized. | Architect |

---

*This file is the debt ledger. Every shortcut taken is recorded here, with a deadline for repayment.*
