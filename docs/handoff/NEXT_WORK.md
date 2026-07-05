# Next Work — Prasoon's Starting Point

> **Your first task:** M8 — Enterprise Multi-Tenancy
> **Roadmap reference:** `docs/architecture/EnterpriseModernizationRoadmap.md` §Wave 8

---

## Current Modernization Status

```
✅ M0  Engineering Foundation
✅ M1  Core Domain Foundation
✅ M2  Document Intelligence Enhancement
✅ M3  Income & Deduction Engines
✅ M4  Tax Computation & Optimization
✅ M5  Compliance & ITR Generation
✅ M6  Audit, Explainability & Traceability
✅ M7  AI Knowledge Platform
────────────────────────────────────
>>> M8  Enterprise Multi-Tenancy    ← YOU ARE HERE
⬜ M9  Security & Privacy
⬜ M10 Integration & Ecosystem
⬜ M11 Production Hardening
```

---

## M8: Enterprise Multi-Tenancy

### Objective

Implement tenant management, RBAC with role hierarchy, CA firm multi-role structure, client portfolio management, enterprise SSO, and tenant isolation.

### Why M8 Now

The dependency graph (`WaveDependencyMatrix.md`) shows M8 depends on M7 (knowledge graph for RBAC domain context). M7 is complete. M8 is unblocked.

### Capabilities to Implement

From the Enterprise Capability Model (FROZEN):

| Capability | Current | Target | Description |
|-----------|---------|--------|-------------|
| C21.1 Tenant Management | 0% | 60% | Tenant CRUD, branding, feature enablement |
| C21.2 CA Firm Hierarchy | 0% | 50% | Role hierarchy: Admin→Senior CA→Junior CA→Clerk |
| C21.3 Client Portfolio | 0% | 50% | Bulk client onboarding, status dashboard |
| C1.3 Authorization (RBAC) | 5% | 50% | Role-based access with tenant scoping |
| C21.4 Firm Dashboard | 0% | 30% | Firm-wide analytics and metrics |
| C21.6 Enterprise SSO | 0% | 30% | SAML/OIDC integration foundation |

### Gap IDs Addressed

- C1.3: Authorization — Critical gap (no RBAC exists)
- C21.1-C21.3: Enterprise Multi-Tenancy — Critical gaps (entire domain missing)
- Risk R06: CA/Enterprise market inaccessible — High risk

### Technical Debt Addressed

- ARC-011: No bounded context separation for enterprise
- AD-002: No authorization model

### What NOT to Build in M8

- Full billing/subscription (M10)
- Complete security compliance (M9)
- White-label embedding (M10)
- External API gateway (M10)

### Dependencies

- **Depends on:** M7 (knowledge graph — COMPLETE ✅)
- **Blocks:** M9 (security needs tenant model)

### Entry Criteria

- [x] M7 complete (✅)
- [x] M7 exit criteria satisfied (✅)
- [x] All 138 tests passing (✅)
- [ ] Read all governance and architecture docs (you)

### Key Modules to Create

```
src/engine/enterprise/
├── tenant.py             # Tenant model, TenantRepository
├── rbac.py               # Role, Permission, RoleHierarchy
├── client_portfolio.py   # Client-to-CA assignment, bulk operations
└── firm_dashboard.py     # Firm-level analytics queries
```

### Key Modules to Modify

- `src/auth/jwt.py` — Add role claims to JWT tokens
- `src/db/database.py` — Add tenants, roles, permissions tables; add tenant_id to users/filings
- `src/api/` — Add tenant-scoped middleware

### Architecture Constraints

- Tenant context must propagate through all requests
- Every database query must filter by tenant_id
- No cross-tenant data access (enforced at query level)
- RBAC must use the knowledge graph for domain context
- FinancialYear awareness must be maintained

### Expected Deliverables

1. Tenant management domain model
2. RBAC with role hierarchy
3. CA firm multi-role structure
4. Client portfolio management basics
5. Firm dashboard (basic analytics)
6. Enterprise SSO foundation
7. M8 Completion Report

### Quality Gates

All 9 gates from `QualityGateFramework.md` apply:
- G2: Code quality (lint + typecheck)
- G3: Security (no cross-tenant access, no privilege escalation)
- G4: Test coverage (must not decrease below current)
- G5: Regression (138 tests must pass, golden vectors unchanged)
- G7: Documentation updated
- G9: Staging deployment verified

### Success Metrics

- Tenant CRUD operations functional
- Roles assignable with correct permission scoping
- Client-to-CA assignment works with bulk import
- Queries are tenant-scoped (verified by test)
- 138 existing tests + new M8 tests all pass
- Golden vectors unchanged
- No breaking API changes

### Estimated Effort

Roadmap estimate: **10 weeks** for M8. This is the highest-complexity wave in the program due to database schema changes (tenant_id backfill).

---

## ABSOLUTE RULES

1. **DO NOT SKIP WAVES.** Execute M8. Nothing else.
2. **DO NOT REDESIGN THE ARCHITECTURE.** The ECM is frozen.
3. **FOLLOW THE FROZEN MODERNIZATION ROADMAP.** It is your blueprint.
4. **DO NOT MODIFY FROZEN DOCUMENTS.** ECM, Roadmap, Gap Report, Recovery Report are immutable.
5. **DO NOT START M9 UNTIL M8 IS COMPLETE.** Each wave gates the next.
6. **MAINTAIN BACKWARD COMPATIBILITY.** No breaking API changes.
7. **USE RULEREPOSITORY FOR ALL TAX RULES.** No hardcoded constants.
8. **USE FINANCIALYEAR EVERYWHERE.** No raw FY strings.
9. **GOLDEN VECTORS MUST PASS.** Any change altering golden vectors is blocked.
10. **PRODUCE A COMPLETION REPORT.** `docs/architecture/M8-CompletionReport.md`

---

*This is your exact starting point. Read the onboarding guide first, then start M8. Good luck.*
