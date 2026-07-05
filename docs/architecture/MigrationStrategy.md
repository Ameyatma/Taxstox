# Migration Strategy

> **Date:** 2026-07-05
> **Principle:** Incremental modernization. Platform deployable after every wave. No big-bang rewrites.

---

## 1. Migration Principles

1. **Strangler Fig Pattern** — Replace old architecture by building around it, not tearing it down. Old and new coexist during transition.
2. **Backward Compatibility** — Existing APIs and ITR JSON output preserved. Breaking changes require deprecation period.
3. **Incremental Deployment** — Every wave produces a deployable, tested increment.
4. **Golden Vector Verification** — Every computation change verified against pre-change output.
5. **Rollback-Ready** — Every deployment has documented rollback procedure.

## 2. Wave-by-Wave Migration Actions

### M0 — Additive Only

| Action | Type | Risk |
|--------|------|------|
| Add pytest framework | **ADD** | None — new files |
| Add CI configuration (.github/workflows/) | **ADD** | None |
| Add structured logging (replace f-strings with JSON) | **MODIFY** | Low — log output changes, not behavior |
| Add health check detail | **MODIFY** | None |
| Add PII masking to existing log statements | **MODIFY** | None |

### M1 — Extract Rules (Highest Risk Wave)

| Action | Type | Risk |
|--------|------|------|
| Create `engine/rules/` package | **ADD** | None |
| Extract slab rates → rule repository | **EXTRACT** | High — must verify identical output |
| Extract deduction limits → rule repository | **EXTRACT** | Medium |
| Extract surcharge thresholds → rule repository | **EXTRACT** | Medium |
| Create `FinancialYear` value object | **ADD** | None |
| Unify optimizer (retire v1) | **REMOVE** | Medium — verify no undiscovered consumers |
| Resolve circular dependency | **REFACTOR** | Medium |
| Remove duplicate slab logic from `builders/itr1.py` | **REFACTOR** | Low |
| Add FY2024-25 rule configuration | **ADD** | Low — additive |

### M2-M11 — Follow Same Pattern

Each subsequent wave follows: ADD new → MODIFY existing → REMOVE deprecated.

## 3. Database Migration Strategy

| Wave | Schema Change | Strategy |
|------|--------------|----------|
| M0 | No changes | — |
| M1 | Add `rule_repository` tables | New tables; no existing data migration |
| M6 | Add `audit_trail`, `computation_events` tables | New tables; append-only |
| M8 | Add `tenant_id` to all tables; create `tenants`, `roles`, `permissions` | **Highest risk migration.** Requires: (1) default tenant for existing users, (2) backfill tenant_id, (3) add NOT NULL constraint after backfill |
| M9 | Add encrypted columns; create `consent_records` | Existing PAN column → encrypted column migration |

### Database Migration Rules

- All schema changes via Alembic migrations (introduced in M0)
- Forward + rollback scripts tested before deploy
- No `ALTER TABLE ... DROP COLUMN` without deprecation period (1 wave minimum)
- Backfill scripts idempotent
- Database backups verified before migration execution

## 4. API Evolution Strategy

| Principle | Implementation |
|-----------|---------------|
| Additive changes | New endpoints, new optional fields |
| Breaking changes | New API version (`/api/v2/`); old version supported for 2 waves |
| Deprecation | `Deprecation` + `Sunset` headers; 2-wave grace period |
| Existing `/api/v1/` endpoints | Preserved throughout M0-M11 |

## 5. Rollback Strategy Per Wave

| Wave | Rollback Method |
|------|----------------|
| M0 | Revert CI config; remove test files (additive) |
| M1 | **Most critical rollback.** Rule repository is additive. Computation pipeline can revert to hardcoded constants in git history. Golden vectors gate prevents incorrect output from ever deploying. |
| M2-M7 | Revert to previous deploy; feature flags off |
| M8 | **Complex rollback.** Tenant migration requires: (1) revert code, (2) drop tenant tables, (3) drop tenant_id columns. Staged over 2 deploys. |
| M9-M11 | Standard rollback; feature flags off |

---

*End of Migration Strategy v1.0*
