# Enterprise Modernization Roadmap

> **Status:** AUTHORITATIVE BLUEPRINT
> **Date:** 2026-07-05
> **Author:** Enterprise Chief Architect
> **Derived From:** Enterprise Capability Model (FROZEN), Architecture Recovery Report, Enterprise Gap Report, Architecture Health Score (31/100), Domain Maturity Matrix (14%), Technical Debt Heatmap (64 items), Enterprise Risk Matrix (15 risks)
> **Principle:** Every modernization action traces to a documented gap, debt item, or risk. Nothing invented.

---

## Executive Summary

The TaxStox ITR platform is a production-deployed modular monolith that handles ITR-1/2 filing for a single financial year (FY2025-26). The Enterprise Gap Analysis assessed 148 target capabilities: **6 are production-ready, 28 are partial, 84 are not implemented, and 30 are unknown**. Architecture health scores **31/100**.

This roadmap defines **12 modernization waves (M0-M11)** that transform the current platform into the enterprise target over an estimated **12-18 month** program. Every wave is traceable to specific gaps, debt items, and risks documented in the frozen architecture artifacts.

### Program at a Glance

| Wave | Name | Duration | Bounded Contexts | Key Outcome |
|------|------|----------|-----------------|-------------|
| **M0** | Engineering Foundation | 4 weeks | BC12 (Operations) | CI/CD, testing infrastructure, structured logging |
| **M1** | Core Domain Foundation | 8 weeks | BC8 (Knowledge & Rules), BC5 (Tax Computation) | Rule-engine separation, multi-FY architecture |
| **M2** | Document Intelligence | 6 weeks | BC3 (Document Processing) | OCR pipeline, 26AS parser, confidence scoring |
| **M3** | Income & Deduction Engines | 8 weeks | BC4 (Income) | Complete income heads, full deduction engine |
| **M4** | Tax Computation & Optimization | 6 weeks | BC5 (Tax Computation), BC7 (Regime) | Interest 234A/B/C, complete special rates |
| **M5** | Compliance & Filing | 8 weeks | BC6 (Compliance) | ITR-3/4 builders, tax credit reconciliation |
| **M6** | Audit & Explainability | 6 weeks | BC7 (Audit) | Immutable audit trail, explanation engine |
| **M7** | AI Knowledge Platform | 10 weeks | BC8 (Knowledge), BC9 (Interview) | Knowledge graph, enhanced interview, rule testing |
| **M8** | Enterprise Multi-Tenancy | 10 weeks | BC1, BC15 (Enterprise) | RBAC, tenant isolation, CA firm hierarchy |
| **M9** | Security & Privacy | 8 weeks | BC13 (Security) | Encryption, DPDP consent, threat detection |
| **M10** | Integration & Ecosystem | 8 weeks | BC11 (Integration) | External APIs, FI integration, dev portal |
| **M11** | Production Hardening | 6 weeks | BC12 (Operations), All | Scalability, penetration testing, certification |
| | **TOTAL** | **~88 weeks (~18 months)** | | |

---

## Wave 0: Engineering Foundation

### Objective

Establish the engineering practices, infrastructure, and safety nets required before any architectural modernization can safely proceed.

### Business Rationale

The platform currently has **zero automated tests**, no CI/CD pipeline, no structured logging, and no monitoring. Any modernization work carries unacceptable risk of introducing production regressions without these foundations. M0 reduces the risk of every subsequent wave.

### Traceability

| Source | Reference | Finding |
|--------|-----------|---------|
| Gap Report | Testing Gaps (Universal) | 0 unit tests, 0 integration tests, 1 skeleton E2E file |
| Gap Report | Observability Gaps | f-string logging, no metrics, no tracing |
| Health Score | Testability: 10/100 | Cannot safely refactor |
| Health Score | Observability: 10/100 | Zero production visibility |
| Debt Heatmap | TST-001 (Critical) | Zero automated tests |
| Debt Heatmap | OPS-001 (High) | No structured logging |
| Debt Heatmap | DEV-001 (High) | No CI/CD pipeline |
| Risk Matrix | R04 (Critical) | Zero testing → tax errors in production |

### Target Bounded Contexts

BC12 (Operations) — CI/CD, logging, monitoring infrastructure

### Capabilities Modernized

| Capability | Current Maturity | Target Maturity |
|-----------|-----------------|-----------------|
| C17.4 CI/CD Pipeline | 20% (basic Render/Vercel deploy) | 60% (automated test + lint + security in CI) |
| C17.2 Monitoring | 10% (basic health endpoint) | 40% (metrics, basic alerting) |
| C17.3 Structured Logging | 10% (f-strings) | 60% (JSON structured logging) |
| C12.5 Rule Testing | 0% | 30% (framework established) |

### Entry Criteria

- [x] Repository consolidated (COMPLETE)
- [x] Documentation topology established (COMPLETE)
- [x] CLAUDE.md bootstrap created (COMPLETE)
- [ ] Git commit + push of consolidated repository (PENDING APPROVAL)

### Exit Criteria

- [ ] pytest framework established with fixtures and conftest
- [ ] Unit test coverage ≥ 30% on existing engine modules
- [ ] Golden-test-vector framework for tax computation verification
- [ ] CI pipeline executes: lint (Ruff) → type-check (MyPy) → unit tests → security scan (Bandit)
- [ ] All CI gates blocking on failure
- [ ] Structured JSON logging implemented across all modules
- [ ] Correlation ID propagation through request lifecycle
- [ ] PII masking in all log output (PAN, Aadhaar, passwords)
- [ ] Basic metrics: request rate, error rate, latency p50/p95
- [ ] Health check endpoint with dependency status (DB, Redis-ready)
- [ ] `.gitignore` verified — no secrets, caches, or artifacts tracked

### Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Unit test count | 0 | ≥ 100 |
| Test coverage | 0% | ≥ 30% |
| CI pipeline exists | No | Yes (lint + type + test + security) |
| Structured logging | No | Yes (JSON format, all modules) |
| PII in logs | Yes (passwords, PAN) | No (all masked) |
| Health check detail | Basic (200 OK) | Dependency-aware |

### Architectural Improvements

- Test harness enables safe refactoring in M1-M11
- Structured logging enables observability in M11
- CI pipeline enforces engineering standards from Constitution
- Correlation IDs enable distributed tracing when platform scales

### Risks

| Risk | Mitigation |
|------|-----------|
| Writing tests for untestable code | Refactor for testability only where necessary for safe testing; defer deep refactoring to M1 |
| CI pipeline slows development | Fast-fail for lint/type; parallelized test execution |
| Existing behavior undocumented | Golden-test-vector approach captures current behavior before changes |

### Estimated Complexity: **Medium**
### Estimated Duration: **4 weeks**
### Rollback: Revert CI config; tests are additive (no production code changed)

---

## Wave 1: Core Domain Foundation

### Objective

Extract hardcoded tax rules from the computation engine into a versioned, FY-indexed rule repository. Establish the FinancialYear domain type. Unify duplicate optimizer implementations. Break the circular dependency. This is the **blocking prerequisite** for multi-year support and all future tax rule changes.

### Business Rationale

The platform **cannot compute tax for any financial year other than FY2025-26**. The Finance Act changes annually. Without M1, the platform becomes functionally obsolete when FY2026-27 rules take effect. This is **Risk R01** (95% probability, Critical impact).

### Traceability

| Source | Reference | Finding |
|--------|-----------|---------|
| Gap Report | C12.1 (Critical) | Finance Act Versioning — Not Implemented (5%) |
| Gap Report | C12.3 (Critical) | Rule Repository — Not Implemented (0%) |
| Gap Report | C12.4 (Critical) | Rule Evaluation Engine — Partial (15%) |
| Gap Report | C6.1 (High) | Slab Tax — hardcoded FY2025-26 |
| Health Score | Domain Design: 15/100 | No domain types for FinancialYear |
| Debt Heatmap | ARC-001 (Critical) | Tax rules hardcoded in computation engine |
| Debt Heatmap | ARC-002 (Critical) | Single financial year architecture |
| Debt Heatmap | ARC-005 (High) | Dual optimizer implementations |
| Debt Heatmap | ARC-007 (High) | Slab computation in 3 locations |
| Debt Heatmap | ARC-008 (Medium) | Circular dependency |
| Risk Matrix | R01 (Critical) | FY2026 obsolescence |
| Risk Matrix | R07 (High) | Silent tax errors from rule changes |
| Risk Matrix | R12 (High) | Circular import runtime failure |

### Target Bounded Contexts

BC8 (Knowledge & Rules), BC5 (Tax Computation)

### Capabilities Modernized

| Capability | Current | Target | Approach |
|-----------|---------|--------|----------|
| C12.1 Finance Act Versioning | 5% | 50% | FinanceActRegistry with FY-indexed rule storage |
| C12.2 Rule Definition Language | 0% | 40% | Declarative rule schema (JSON/YAML-based, version-controlled) |
| C12.3 Rule Repository | 0% | 50% | Central rule store with FY+regime indexing |
| C12.4 Rule Evaluation Engine | 15% | 50% | Generic rule evaluator; extract from procedural code |
| C6.1 Slab Tax Engine | 35% | 60% | FY-parameterized; rules loaded from repository |

### Components to Preserve

| Component | Reason |
|-----------|--------|
| `engine/regime_optimizer_v2.py` — computation logic | Correct ITD portal-matched computation. Extract rules FROM it, preserve logic. |
| `engine/salary_computer.py` | Correct salary computation. Parameterize constants. |
| `engine/deductions_computer.py` | Correct deduction logic. Extract limits to rules. |
| `engine/classifier.py` | Correct CG classification. Extract rates/exemptions to rules. |
| All `models/` | Domain models are sound. Add FinancialYear value object. |

### Components to Refactor

| Component | Action |
|-----------|--------|
| `engine/regime_optimizer.py` (v1) | **RETIRE** — v2 contains all v1 logic and more. Remove after confirming no consumers. |
| `engine/regime_optimizer_v2.py` | **EXTRACT** rules to repository; keep computation pipeline |
| `builders/itr1.py:_compute_tax()` | **REMOVE** duplicate slab logic; call shared engine |
| `engine/classifier.py` | **RESOLVE** circular dependency with optimizer via dependency inversion |
| Multiple files with hardcoded constants | **EXTRACT** all constants to rule repository |

### Components to Create

| Component | Purpose |
|-----------|---------|
| `engine/rules/repository.py` | `RuleRepository` — FY+regime-indexed rule store |
| `engine/rules/schema.py` | Rule definition schema (declarative format) |
| `engine/rules/evaluator.py` | Generic `RuleEvaluator` — dependency-ordered rule execution |
| `models/financial_year.py` | `FinancialYear` value object — typesafe, validates ranges |
| `models/tax_year_config.py` | `TaxYearConfig` — single source for FY-specific constants |
| `engine/pipeline.py` | `TaxComputationPipeline` — explicit step ordering |

### Exit Criteria

- [ ] All hardcoded rates, limits, thresholds extracted to versioned rule repository
- [ ] Rule repository supports at minimum FY2025-26 and FY2024-25 (proves multi-year)
- [ ] `FinancialYear` value object used throughout codebase (no raw strings)
- [ ] `RegimeOptimizer` v1 retired; v2 is single canonical optimizer
- [ ] Circular dependency resolved via interface
- [ ] Slab tax computed from rule repository, not hardcoded constants
- [ ] All existing tests pass (M0 tests) — computation output identical
- [ ] Golden-test-vector comparison: M1 output = pre-M1 output for FY2025-26
- [ ] FY2024-25 rules configurable and produce correct tax (verified against ITD portal)
- [ ] ADR written for rule-engine separation architecture

### Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Hardcoded constants in engine code | ~60 | 0 |
| Financial years supported | 1 (FY2025-26) | ≥ 2 (FY2024-25 + FY2025-26) |
| Rule repository exists | No | Yes |
| Duplicate optimizer implementations | 2 (v1+v2) | 1 (v2 canonical) |
| Circular dependencies | 1 | 0 |
| Slab computation locations | 3 | 1 |

### Risks

| Risk | Mitigation |
|------|-----------|
| Rule extraction introduces computation differences | Golden-test-vector comparison gates every change |
| v1 retirement breaks undiscovered consumers | Code search + import audit before removal; deprecation warning period |
| Incorrect FY2024-25 rules | Domain expert verification against ITD portal for FY2024-25 |

### Estimated Complexity: **Very High**
### Estimated Duration: **8 weeks**
### Rollback: Rule repository is additive. Computation pipeline can revert to hardcoded constants (preserved in git history) if M1 output doesn't match golden vectors.

---

## Wave 2: Document Intelligence Enhancement

### Objective

Expand document processing capabilities: OCR pipeline for scanned documents, Form 26AS parser for TDS reconciliation, broker statement parser expansion, confidence scoring, and investment proof parsing.

### Traceability

| Source | Reference | Finding |
|--------|-----------|---------|
| Gap Report | C3.5 (High) | OCR Pipeline — Not Implemented |
| Gap Report | C3.7 (High) | Form 26AS Parser — Not Implemented |
| Gap Report | C3.8 (Medium) | Broker Statement — Partial (4 brokers, no CAMS PDF) |
| Gap Report | C3.9 (Medium) | Investment Proof Parser — Not Implemented |
| Gap Report | C3.10 (Medium) | Document Validation — Not Implemented |
| Debt Heatmap | ARC-011 (High) | No bounded context separation |
| Risk Matrix | R11 (Medium) | PDF parser breakage on new formats |

### Target Bounded Contexts

BC3 (Document Processing)

### Capabilities Modernized

| Capability | Current | Target |
|-----------|---------|--------|
| C3.1 Multi-Format Ingestion | 40% | 60% (image formats added) |
| C3.5 OCR Pipeline | 0% | 50% (basic OCR, printed forms) |
| C3.7 Form 26AS Parser | 0% | 60% (PDF parsing) |
| C3.8 Broker Statement | 50% | 70% (CAMS, KFintech added) |
| C3.9 Investment Proof Parser | 0% | 40% (receipt parsing) |
| C3.10 Document Validation | 0% | 30% (tampering detection) |

### Estimated Complexity: **High**
### Estimated Duration: **6 weeks**

---

## Wave 3: Income & Deduction Engines

### Objective

Complete all income heads and deduction sections. Add house property engine, business income engine (ITR-3/4 prerequisite), foreign income engine, complete Chapter VI-A deduction engine with all sections, and NPS/retirement optimization.

### Traceability

| Source | Reference | Finding |
|--------|-----------|---------|
| Gap Report | C4.2 (High) | House Property — Partial (20%) |
| Gap Report | C4.3 (High) | Business Income — Not Implemented |
| Gap Report | C4.8 (Medium) | Foreign Income — Not Implemented |
| Gap Report | C5.4 (Medium) | Deduction Optimization — Partial (20%) |
| Gap Report | C5.6 (Medium) | Home Loan Deduction — Partial (30%) |

### Target Bounded Contexts

BC4 (Income), BC5 (Deduction portions)

### Capabilities Modernized

| Capability | Current | Target |
|-----------|---------|--------|
| C4.2 House Property | 20% | 70% |
| C4.3 Business Income | 0% | 50% (presumptive + basic P&L) |
| C4.8 Foreign Income | 0% | 40% (Schedule FA basics) |
| C5.1 Chapter VI-A | 55% | 80% (all sections) |
| C5.6 Home Loan | 30% | 70% |
| C5.7 NPS & Retirement | 40% | 70% |

### Estimated Complexity: **High**
### Estimated Duration: **8 weeks**

---

## Wave 4: Tax Computation & Optimization

### Objective

Complete tax computation engine with interest 234A/B/C, all special rate sections, surcharge with marginal relief for all entity types, regime lock-in advisor, and marginal tax rate analyzer.

### Traceability

| Source | Reference | Finding |
|--------|-----------|---------|
| Gap Report | C6.7 (High) | Interest 234A/B/C — Not Implemented |
| Gap Report | C6.2 (Medium) | Special Rate — Partial (40%) |
| Gap Report | C6.3 (Medium) | Surcharge — Partial (entity types missing) |
| Gap Report | C7.2 (High) | Regime Lock-in Advisor — Not Implemented |
| Gap Report | C7.4 (Medium) | Marginal Rate Analyzer — Not Implemented |

### Estimated Complexity: **Medium**
### Estimated Duration: **6 weeks**

---

## Wave 5: Compliance & Filing

### Objective

Complete ITR generation for all form types, tax credit reconciliation engine, AIS income completeness checker, and audit readiness engine.

### Traceability

| Source | Reference | Finding |
|--------|-----------|---------|
| Gap Report | C9.4 (High) | ITR-3 Builder — Not Implemented |
| Gap Report | C9.5 (High) | ITR-4 Builder — Not Implemented |
| Gap Report | C8.1 (Critical) | Tax Credit Reconciliation — Partial (15%) |
| Gap Report | C8.4 (Critical) | AIS Completeness — Not Implemented (10%) |
| Gap Report | C8.7 (Medium) | Audit Readiness — Not Implemented |

### Estimated Complexity: **High**
### Estimated Duration: **8 weeks**

---

## Wave 6: Audit & Explainability

### Objective

Implement immutable computation audit trail, multi-level explanation engine, legal provision tracer, and CA professional review mode.

### Traceability

| Source | Reference | Finding |
|--------|-----------|---------|
| Gap Report | C10.1 (Critical) | Audit Trail — Not Implemented (0%) |
| Gap Report | C10.2 (High) | Explanation Engine — Partial (20%) |
| Gap Report | C10.3 (High) | Legal Provision Tracer — Not Implemented |
| Gap Report | C10.4 (High) | Computation Verification — Not Implemented |
| Gap Report | C10.5 (Medium) | CA Review Mode — Not Implemented |
| Constitution | I3 | Complete Audit Trail invariant violation |
| Constitution | I4 | Explainability invariant violation |

### Estimated Complexity: **High**
### Estimated Duration: **6 weeks**

---

## Wave 7: AI Knowledge Platform

### Objective

Build the tax knowledge graph, tax provision knowledge base, Finance Act change analyzer, enhanced adaptive interview engine with personalization and offline capability, and rule testing framework.

### Traceability

| Source | Reference | Finding |
|--------|-----------|---------|
| Gap Report | C11.1 (Critical) | Tax Knowledge Graph — Not Implemented |
| Gap Report | C11.2 (Critical) | Tax Provision KB — Not Implemented |
| Gap Report | C11.3 (High) | Finance Act Change Analyzer — Not Implemented |
| Gap Report | C12.5 (High) | Rule Testing Framework — Not Implemented |
| Gap Report | C13.5 (High) | Real-Time Validation — Partial |
| Gap Report | C13.6 (Medium) | Interview Personalization — Not Implemented |
| Gap Report | C13.8 (Medium) | Offline Interview — Not Implemented |
| Risk Matrix | R08 (High) | Key person dependency (bus factor) |

### Estimated Complexity: **Very High**
### Estimated Duration: **10 weeks**

---

## Wave 8: Enterprise Multi-Tenancy

### Objective

Implement tenant management, RBAC with role hierarchy, CA firm multi-role structure, client portfolio management, enterprise SSO, and tenant isolation.

### Traceability

| Source | Reference | Finding |
|--------|-----------|---------|
| Gap Report | C1.3 (Critical) | RBAC — Not Implemented |
| Gap Report | C21.1 (Critical) | Tenant Management — Not Implemented |
| Gap Report | C21.2 (Critical) | CA Firm Hierarchy — Not Implemented |
| Gap Report | C21.3 (Critical) | Client Portfolio — Not Implemented |
| Gap Report | C21.4 (High) | Firm Dashboard — Not Implemented |
| Gap Report | C21.6 (High) | Enterprise SSO — Not Implemented |
| Gap Report | C18.9 (Critical) | Tenant Isolation — Not Implemented |
| Risk Matrix | R06 (High) | CA/Enterprise market inaccessible |

### Estimated Complexity: **Very High**
### Estimated Duration: **10 weeks**

---

## Wave 9: Security & Privacy

### Objective

Implement application-level PII encryption, DPDP Act consent management, RBAC enforcement, threat detection, DLP, and security compliance framework.

### Traceability

| Source | Reference | Finding |
|--------|-----------|---------|
| Gap Report | C17.1 (Critical) | Data Encryption — Partial (30%) |
| Gap Report | C1.8 (Critical) | Consent Management — Not Implemented |
| Gap Report | C17.3 (Critical) | Data Privacy DPDP — Not Implemented |
| Gap Report | C17.4 (Critical) | Access Control — Not Implemented |
| Debt Heatmap | SEC-001 (Critical) | Dev JWT secret hardcoded |
| Debt Heatmap | SEC-002 (Critical) | PAN plaintext in DB |
| Risk Matrix | R02 (Critical) | DPDP Act non-compliance |
| Risk Matrix | R03 (Critical) | Security breach via plaintext PII |

### Estimated Complexity: **Very High**
### Estimated Duration: **8 weeks**

---

## Wave 10: Integration & Ecosystem

### Objective

Build API gateway with management, external tax authority API integration, financial institution integration, CA software integration, payment gateway integration, and developer portal.

### Estimated Complexity: **High**
### Estimated Duration: **8 weeks**

---

## Wave 11: Production Hardening

### Objective

Performance optimization for filing season scale, horizontal scaling (Redis sessions), penetration testing, compliance certification readiness, DR/BCP implementation, and full observability.

### Traceability

| Source | Reference | Finding |
|--------|-----------|---------|
| Risk Matrix | R05 (High) | Filing season scalability failure |
| Debt Heatmap | INF-001 (Critical) | In-memory sessions |
| Health Score | Scalability: 15/100 | No horizontal scaling |

### Estimated Complexity: **Medium**
### Estimated Duration: **6 weeks**

---

## Dependency Graph

```
M0 (Engineering Foundation)
 │
 ├──► M1 (Core Domain Foundation) ───── MUST COME FIRST after M0
 │     │
 │     ├──► M2 (Document Intelligence) ─── can parallel with M3
 │     ├──► M3 (Income & Deduction) ────── can parallel with M2
 │     │     │
 │     │     └──► M4 (Tax Computation) ──── depends on M3 income heads
 │     │           │
 │     │           └──► M5 (Compliance) ─── depends on M4 complete computation
 │     │                 │
 │     │                 └──► M6 (Audit) ─── depends on M5 for complete ITR data
 │     │
 │     └──► M7 (AI Knowledge Platform) ─── depends on M1 rule extraction
 │           │
 │           └──► M8 (Enterprise) ───────── depends on M7 knowledge graph
 │                 │
 │                 └──► M9 (Security) ───── depends on M8 tenant model
 │                       │
 │                       └──► M10 (Integration) ── depends on M9 security
 │                             │
 │                             └──► M11 (Production) ── depends on all
```

### Parallel Workstreams

| Workstream | Waves | Can Run Concurrently With |
|-----------|-------|--------------------------|
| **Core Tax** | M1 → M3 → M4 → M5 → M6 | M2 (Document) can parallel M3 |
| **Platform** | M0 → M7 → M8 → M9 → M10 → M11 | Sequential |
| **Quick Wins** | Security fixes (SEC-001, SEC-002) | Any wave (P0 fixes, not full wave) |

### Critical Path

**M0 → M1 → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10 → M11**

M2 (Document Intelligence) is NOT on the critical path and can run in parallel with M3.

---

## Quality Gates Between Waves

Every wave transition requires:

| Gate | Description | Blocking? |
|------|-------------|-----------|
| **G1: Architecture Review** | Chief Architect verifies wave output aligns with ECM target | Yes |
| **G2: Test Coverage** | Coverage does not decrease from previous wave | Yes |
| **G3: Regression Suite** | All existing tests pass; golden vectors match | Yes |
| **G4: Security Scan** | Zero new HIGH/CRITICAL vulnerabilities | Yes |
| **G5: Performance** | p95 latency does not degrade >10% from baseline | Yes |
| **G6: Documentation** | Affected module READMEs, ADRs, and memory updated | Yes |
| **G7: Code Review** | All PRs reviewed per Review Standards | Yes |
| **G8: Domain Review** | Tax rule changes reviewed by domain expert | Yes (tax waves only) |
| **G9: Deployment** | Successful deploy to staging; smoke test passed | Yes |

---

## Program Estimates

| Metric | Estimate |
|--------|----------|
| Total waves | 12 (M0-M11) |
| Total duration | 68-88 weeks (~14-18 months) |
| Critical path duration | M0+M1+M3+M4+M5+M6+M7+M8+M9+M10+M11 (~76 weeks) |
| Parallelizable savings | M2 runs alongside M3 (~6 weeks overlap) |
| Team size recommendation | 4-6 engineers + 1 domain expert (CA) + 1 architect |
| Highest-risk wave | M1 (Core Domain Foundation) — extracting rules without breaking computation |
| Highest-value wave | M1 (unblocks all FYs) + M6 (audit trail — compliance requirement) |

### Architectural Checkpoints

| After Wave | Checkpoint |
|------------|-----------|
| M1 | Architecture Health Score re-assessed. Target: ≥ 45/100 |
| M5 | First complete ITR-3 filing (business income). Target: ≥ 55/100 |
| M8 | First multi-tenant CA firm onboarded. Target: ≥ 65/100 |
| M11 | Production certification ready. Target: ≥ 80/100 |

---

*End of Enterprise Modernization Roadmap v1.0*
*This roadmap is the authoritative blueprint. All future development traces to waves defined herein. Supporting documents follow.*
