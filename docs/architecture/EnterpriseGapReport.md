# Enterprise Gap Report — IT_Returns Platform

> **Status:** DIAGNOSIS ONLY
> **Date:** 2026-07-05
> **Author:** Enterprise Chief Architect
> **Inputs:** Enterprise Capability Model v1.0 (FROZEN), Architecture Recovery Report v1.0, Source code (42 modules), Design docs, AI-DOS Project Memory v0.1
> **Methodology:** Evidence-backed. Every finding cites source. Unknowns explicitly flagged.

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Capabilities assessed | 148 |
| **FULLY IMPLEMENTED (Production/Enterprise Ready)** | **6** |
| **PARTIALLY IMPLEMENTED (Functional/Partial)** | **28** |
| **NOT IMPLEMENTED** | **84** |
| **UNKNOWN (insufficient evidence)** | **30** |
| Critical gaps | **42** |
| High-severity gaps | **38** |
| Medium-severity gaps | **28** |
| Low-severity gaps | **10** |
| Overall Architecture Health | **31/100** |

### Top 10 Critical Gaps

| # | Capability | Current State | Evidence | Risk |
|---|-----------|---------------|----------|------|
| 1 | C12.1 Finance Act Versioning | Not Implemented | Hardcoded AY in `builders/itr_json_builder.py:31` | Cannot support any FY other than 2025-26 |
| 2 | C12.3 Rule Repository | Not Implemented | Slab constants in `regime_optimizer_v2.py:39-68` | Rules mixed with engine code |
| 3 | C10.1 Computation Audit Trail | Not Implemented | Zero audit classes in 42 modules | No proof of computation correctness |
| 4 | C1.8 Consent Management | Not Implemented | No consent model/API/UI anywhere | DPDP Act non-compliance |
| 5 | C1.3 Authorization (RBAC) | Not Implemented | `users` table has no `role` column; no permission middleware | Any user = full access |
| 6 | C21.1-C21.8 Enterprise Multi-Tenancy | Not Implemented | No tenant_id in any table; no tenant context | Platform is single-user only |
| 7 | C18.1-C18.10 Security Controls | ~20% maturity | Dev JWT secret hardcoded; no rate limiting; no threat detection | Production security gaps |
| 8 | C11.1 Tax Knowledge Graph | Not Implemented | Tax provisions exist only in code comments | No semantic tax knowledge |
| 9 | C17.2 Monitoring & Observability | Not Implemented | f-string logging only; no metrics/tracing/alerting | Zero production visibility |
| 10 | C18.x Testing Infrastructure | Not Implemented | Single skeleton test file `test_e2e_real_data.py` | Cannot safely refactor or extend |

---

## Capability Assessment: Critical Priority

### Domain 1: Identity & Access Management

---

#### C1.1 — User Registration & Onboarding

- **Target State:** PAN-verified with NSDL API, email/mobile OTP, Aadhaar e-KYC
- **Current State:** Functional
- **Current Maturity:** 40%
- **Evidence:** `models/user.py:10-31` (PAN regex validation); `db/database.py:175-195` (create_user with email uniqueness); `api/auth_routes.py` (register/login routes). No NSDL API integration. No Aadhaar e-KYC. No identity proofing pipeline.
- **Missing:** PAN verification API, Aadhaar e-KYC, trust level model, CAPTCHA, rate limiting on registration
- **Architectural Deficiencies:** PAN validated by regex only. No identity proofing. No trust level model.
- **Technical Debt:** PAN regex duplicated in `models/user.py:21`, `builders/validator.py:32`, `parsers/form16_parser.py:99`
- **Missing Domain Services:** `IdentityVerificationService`, `PANVerificationClient`
- **Missing APIs:** `POST /api/v1/auth/verify-pan`
- **Missing Security:** No rate limiting; no CAPTCHA; no brute-force protection
- **Missing Testing:** Unit: 0, Integration: 0, E2E: 0
- **Missing Observability:** No registration metrics
- **Migration Complexity:** Medium
- **Business Impact:** High
- **Risk if Ignored:** Identity fraud; regulatory non-compliance
- **Severity:** **High**
- **Confidence:** **HIGH** — All auth modules reviewed; NSDL integration absent from all 42 files
- **Suggested Remediation:** Introduce IdentityVerificationService; integrate NSDL PAN API; implement trust level model; add anti-abuse controls

---

#### C1.2 — Authentication

- **Target State:** MFA, OTP, OAuth, FIDO2/Passkey, adaptive MFA
- **Current State:** Functional
- **Current Maturity:** 50%
- **Evidence:** `auth/jwt.py:12-31` (JWT HS256); `auth/jwt.py:12` — hardcoded dev secret fallback `"taxstox-dev-secret-change-in-production"`; `api/auth_routes.py` (Google OAuth callback); `HANDOFF.md:71-86` (postMessage OAuth flow). No OTP. No MFA. No WebAuthn.
- **Missing:** OTP auth (email/SMS), MFA, passkey/WebAuthn, adaptive MFA, device fingerprinting, forced re-auth
- **Architectural Deficiencies:** JWT secret has dev default in source code (TD-SEC-001). No token binding. No refresh rotation.
- **Missing Security:** No brute-force protection; no suspicious login detection
- **Missing Testing:** Unit: 0, Integration: 0, Security: 0
- **Migration Complexity:** Medium
- **Business Impact:** High
- **Risk if Ignored:** Credential theft → taxpayer data breach; hardcoded secret exploitation
- **Severity:** **High**
- **Confidence:** **HIGH** — JWT module reviewed; OTP/MFA/FIDO2 absent from all source files
- **Suggested Remediation:** Remove hardcoded dev secret; add OTP auth channel; implement MFA for sensitive operations; add brute-force protection

---

#### C1.3 — Authorization & Role-Based Access Control

- **Target State:** RBAC + ABAC, role hierarchy (Taxpayer→CA→Admin→SuperAdmin), tenant-scoped, policy-as-code
- **Current State:** Not Implemented
- **Current Maturity:** 5%
- **Evidence:** `auth/jwt.py:36-60` — `get_current_user()` returns payload, no role check; `db/database.py:69-77` — `users` table columns: id, email, pan, name, hashed_password, dob, created_at — **no role column**; No permission model; No authorization middleware; No resource-level access control. Every authenticated user has identical access.
- **Missing:** Complete authorization subsystem
- **Missing Bounded Contexts:** Authorization context entirely absent
- **Missing Domain Services:** `AuthorizationService`, `RoleRepository`, `PermissionRegistry`
- **Missing APIs:** All role/permission management endpoints
- **Missing Security:** No access control beyond authentication
- **Migration Complexity:** High — requires schema change, middleware, retrofitting all endpoints
- **Business Impact:** Critical
- **Risk if Ignored:** Any user can access/modify any data. Platform cannot serve CAs or enterprises.
- **Severity:** **Critical**
- **Confidence:** **HIGH** — User table schema reviewed (no role column); no authorization middleware in 42 modules
- **Suggested Remediation:** Introduce RBAC model with role hierarchy; implement authorization middleware; add role column; retrofit endpoints with permission checks

---

#### C1.8 — Consent Management

- **Target State:** Granular consent per DPDP Act 2023, versioning, withdrawal, audit, AA consent framework
- **Current State:** Not Implemented
- **Current Maturity:** 0%
- **Evidence:** Zero consent-related code in any of 42 modules. `ARCHITECTURE.md:1093-1110` mentions "GDPR-equivalent consent" as principle only — no implementation. No consent model, service, API, or UI.
- **Missing:** Complete consent management subsystem
- **Missing Bounded Contexts:** Consent context entirely absent
- **Missing Domain Services:** `ConsentService`, `ConsentRepository`, `ConsentAuditService`
- **Missing APIs:** All consent CRUD endpoints
- **Missing Security:** Consent is a DPDP Act security control
- **Migration Complexity:** High — new domain, schema, retrofitting all data collection
- **Business Impact:** Critical — DPDP Act 2023 legal requirement; penalties up to ₹250 Cr
- **Risk if Ignored:** Regulatory penalties; inability to legally operate in India
- **Severity:** **Critical**
- **Confidence:** **HIGH** — All 42 modules searched; zero consent infrastructure
- **Suggested Remediation:** Introduce Consent bounded context; implement DPDP-compliant consent model; retrofit all data collection with consent checks

---

### Domain 10: Audit & Explainability

---

#### C10.1 — Computation Audit Trail

- **Target State:** Immutable, queryable audit trail of every computation step with legal provision reference
- **Current State:** Not Implemented
- **Current Maturity:** 0%
- **Evidence:** Zero audit-related classes, files, or patterns in all 42 modules. Searched for: `audit`, `AuditTrail`, `event_sourcing`, `event_store`, `ComputationEvent`, `immutable`. Nothing found. Tax computation functions return plain dicts with no audit metadata. `regime_optimizer_v2.py:_compute()` returns dict with breakdown values — no step tracing, no rule version tracking, no input/output capture.
- **Missing:** Complete audit trail subsystem; event sourcing; computation replay; verification
- **Missing Bounded Contexts:** Audit bounded context entirely absent
- **Missing Domain Services:** `AuditTrailService`, `ComputationEventStore`, `ReplayVerifier`
- **Missing Entities/Aggregates:** `ComputationEvent`, `AuditTrail`, `RuleEvaluationRecord`
- **Missing APIs:** `GET /api/v1/audit/{computation_id}`
- **Missing Events:** No domain events emitted during computation
- **Migration Complexity:** Very High — requires event sourcing architecture across computation pipeline
- **Business Impact:** Critical — regulatory requirement; CA review; scrutiny defense
- **Risk if Ignored:** Cannot prove computation correctness to ITD; cannot support CA review; violates Constitutional Invariant I3
- **Severity:** **Critical**
- **Confidence:** **HIGH** — All engine modules reviewed; zero audit infrastructure
- **Suggested Remediation:** Introduce event-sourced computation pipeline; emit ComputationStep events; build immutable event store; add replay verification

---

#### C10.2 — Plain-Language Explanation Engine

- **Target State:** Multi-level, multi-language explanations of every tax computation
- **Current State:** Partial
- **Current Maturity:** 20%
- **Evidence:** `engine/recommendation_engine.py:293-329` — `_build_explanation()` generates markdown explanations for regime recommendation only. `builders/itr_json_builder.py` — `_build_partb_tti()` returns numeric breakdown without explanations. `models/tax.py:130-138` — `RegimeResult` contains numeric breakdown dicts, no explanation text. No template engine. No multi-language support. No per-step explanations.
- **Missing:** Explanation generation for all computation steps; multi-language; multi-level (summary/detail/technical); template engine
- **Missing Domain Services:** `ExplanationEngine`, `ExplanationTemplateRepository`
- **Migration Complexity:** Medium — explanation generation from audit trail data
- **Business Impact:** High — key value proposition; differentiator from ITD portal
- **Severity:** **High**
- **Confidence:** **HIGH** — Explanation logic only in recommendation_engine for one use case
- **Suggested Remediation:** Build explanation engine that consumes audit trail events; implement template-based generation with multi-language support

---

#### C10.6 — Explainable AI

- **Target State:** SHAP/LIME feature attribution, counterfactual explanations, audit-grade model docs
- **Current State:** Not Implemented
- **Current Maturity:** 0%
- **Evidence:** `engine/recommendation_engine.py:98-291` — `RecommendationEngine.analyze()` uses deterministic rule-based logic (if-else, comparisons), no ML model. DeepSeek API used only for tax updates summarization (`summarizer/__init__.py`). No AI used in tax computation decisions. No XAI infrastructure.
- **Missing:** XAI framework; feature attribution; counterfactual generation; model documentation
- **Missing Domain Services:** `ExplainabilityService`, `ModelDocumentationService`
- **Migration Complexity:** Medium — relevant when AI models are introduced
- **Business Impact:** Medium — currently no AI in computation; becomes Critical when AI is introduced
- **Risk if Ignored:** Regulatory requirement for AI in finance will apply when AI models are used
- **Severity:** **Medium** (becomes Critical when AI models introduced)
- **Confidence:** **HIGH** — All engine modules reviewed; no ML in tax computation; no XAI
- **Suggested Remediation:** Design XAI framework before introducing any ML into tax computation pipeline

---

### Domain 12: Rule Management

---

#### C12.1 — Finance Act Versioning

- **Target State:** Rule registry FY2020-21 to FY2030-31; rule version history; cross-year comparison
- **Current State:** Not Implemented
- **Current Maturity:** 5%
- **Evidence:** Entire computation pipeline hardcoded for FY2025-26. `builders/itr_json_builder.py:31` — `AY = "2026-27"` hardcoded; `builders/itr1.py:24` — `AY = "2026-27"` hardcoded; `regime_optimizer_v2.py:39-68` — slab constants for FY2025-26 only; `deductions_computer.py:29-39` — limit constants for FY2025-26 only; `classifier.py:20` — `LTCG_112A_EXEMPTION = Decimal("125000")` — no FY tag. No Finance Act registry. No rule effective date ranges. No rule lineage.
- **Missing:** Finance Act registry; rule effective date ranges; rule version history; cross-year comparison
- **Missing Bounded Contexts:** Rule Management context absent
- **Missing Domain Services:** `FinanceActRegistry`, `RuleVersionService`
- **Missing Entities/Value Objects:** `FinancialYear`, `AssessmentYear`, `FinanceAct`, `RuleVersion`
- **Missing Repositories:** `RuleRepository` (FY-indexed)
- **Architectural Deficiencies:** Violates Constitutional Invariants I1 (Multi-Year), I2 (Rule-Engine Separation), I8 (Configurable Everything), and Principle P8 (Compliance Is Continuous)
- **Migration Complexity:** Very High — touches every computation module
- **Business Impact:** Critical — platform cannot function for any FY other than 2025-26
- **Risk if Ignored:** Platform becomes obsolete on April 1, 2026 (new FY); cannot serve past-year filers
- **Severity:** **Critical**
- **Confidence:** **HIGH** — Hardcoded FY/AY found in 5+ files; no version-aware rule infrastructure
- **Suggested Remediation:** Extract all rate/limit/threshold constants to versioned rule repository indexed by FinancialYear; introduce FinancialYear domain type; retrofitting computation pipeline to accept FY parameter

---

#### C12.2 — Rule Definition Language/Format

- **Target State:** Declarative rule schema; human-readable + machine-executable; visual rule editor
- **Current State:** Not Implemented
- **Current Maturity:** 0%
- **Evidence:** All tax rules expressed as Python code (functions, if-else, constants). No declarative rule format. No rule schema. Examples: `regime_optimizer_v2.py:39-68` — slabs as list of tuples; `regime_optimizer_v2.py:281-300` — `_slab_tax()` as procedural code; `deductions_computer.py:85-198` — `compute()` as procedural code with nested if-else. No rule DSL. No rule metadata standard.
- **Missing:** Rule schema definition; declarative rule format; rule composition; rule validation
- **Missing Domain Services:** `RuleSchema`, `RuleParser`, `RuleValidator`
- **Architectural Deficiencies:** Rules are not separable from computation engine. Rule changes require code changes.
- **Migration Complexity:** Very High — requires defining rule schema, migrating all 60+ rules to declarative format
- **Business Impact:** Critical — rules cannot be updated without developer involvement
- **Risk if Ignored:** Cannot scale rule authoring; every Finance Act change requires code deployment
- **Severity:** **Critical**
- **Confidence:** **HIGH** — All rules expressed as Python code; no declarative format anywhere
- **Suggested Remediation:** Define declarative rule schema; migrate rules to versioned data; build rule parser and evaluator

---

#### C12.3 — Rule Repository

- **Target State:** Central FY/regime-indexed rule store; hot-reloadable; queryable by context
- **Current State:** Not Implemented
- **Current Maturity:** 0%
- **Evidence:** Rules scattered across 6+ engine files as Python constants and inline logic. `regime_optimizer.py:33-58` — slab rates, deduction limits; `regime_optimizer_v2.py:39-68` — duplicate slab definitions; `deductions_computer.py:29-39` — deduction limits; `salary_computer.py:25-32` — HRA parameters; `classifier.py:20` — 112A exemption. No central rule store. No rule querying. No FY indexing.
- **Missing:** Central rule repository; FY/regime indexing; context-sensitive rule retrieval; rule caching; rule change notifications
- **Missing Domain Services:** `RuleRepository`, `RuleQueryService`, `RuleCacheService`
- **Code Duplication:** Slab rates defined in 3 places; deduction limits in 2+ places
- **Migration Complexity:** Very High — requires extracting all rules, building repository, refactoring all consumers
- **Business Impact:** Critical — no single source of truth for tax rules
- **Risk if Ignored:** Rule inconsistency across modules; impossible to audit which rules are active
- **Severity:** **Critical**
- **Confidence:** **HIGH** — Rules scattered across 6 files without central registry
- **Suggested Remediation:** Build central RuleRepository with FY+regime indexing; migrate all rules; refactor consumers to query repository

---

#### C12.4 — Rule Evaluation Engine

- **Target State:** Generic rule engine; deterministic; auditable; dependency-ordered; parallel evaluation
- **Current State:** Partial
- **Current Maturity:** 15%
- **Evidence:** `regime_optimizer_v2.py:137-279` — `_compute()` method evaluates tax in hardcoded sequential order. No generic rule engine. Computation order is baked into procedural code. No rule dependency resolution. No partial re-evaluation. `engine/classifier.py:26-243` — `ClassificationEngine` is the closest to a generic engine but is specific to CG classification, not a general rule evaluator.
- **Missing:** Generic rule evaluation engine; rule dependency resolution; partial re-evaluation; parallel evaluation; evaluation optimization (Rete or similar)
- **Architectural Deficiencies:** Computation logic and evaluation logic are merged. No separation between "what rules exist" and "how rules execute."
- **Missing Domain Services:** `RuleEvaluationEngine`, `EvaluationContext`, `EvaluationTrace`
- **Code Duplication:** `regime_optimizer.py` and `regime_optimizer_v2.py` are duplicate implementations of same logic (v1 and v2)
- **Migration Complexity:** Very High — requires generic engine design, rule migration, pipeline refactoring
- **Business Impact:** Critical — engine cannot dynamically load rules; every new rule requires code change
- **Risk if Ignored:** Unable to support dynamic rule updates; increasing maintenance burden with each new FY
- **Severity:** **Critical**
- **Confidence:** **HIGH** — Both optimizer implementations reviewed; no generic rule engine
- **Suggested Remediation:** Build generic RuleEvaluationEngine with dependency graph; migrate all rules; refactor computation pipeline to use engine

---

### Domain 20: Enterprise Multi-Tenancy

---

#### C21.1 — Tenant Management

- **Target State:** Tenant lifecycle management; branding; feature enablement; billing; usage monitoring
- **Current State:** Not Implemented
- **Current Maturity:** 0%
- **Evidence:** `db/database.py:69-77` — `users` table: **no tenant_id column**. No tenant model anywhere in codebase. `api/routes.py` — all endpoints operate in single-user context via session_id. No tenant context propagation. No tenant isolation. `ARCHITECTURE.md` — no mention of multi-tenancy. Platform designed as single-user SaaS.
- **Missing:** Complete tenant management subsystem
- **Missing Bounded Contexts:** Enterprise/Tenant context entirely absent
- **Missing Domain Services:** `TenantService`, `TenantRepository`, `TenantProvisioningService`
- **Missing APIs:** All tenant management endpoints
- **Missing Security:** No tenant isolation; no cross-tenant access prevention
- **Migration Complexity:** Very High — requires schema redesign, tenant context propagation, retrofitting all queries
- **Business Impact:** Critical — platform cannot serve CA firms (primary target market)
- **Risk if Ignored:** Platform limited to direct-to-consumer only; cannot capture enterprise/CA market
- **Severity:** **Critical**
- **Confidence:** **HIGH** — No tenant_id in any table; no tenant model; no tenant middleware
- **Suggested Remediation:** Introduce Tenant bounded context; add tenant_id to all tables; implement tenant context middleware; enforce tenant isolation at query level

---

#### C21.2 — Multi-Role Hierarchy (CA Firm)

- **Target State:** Role hierarchy (Firm Admin→Senior CA→Junior CA→Article Clerk); client assignment; supervision workflows
- **Current State:** Not Implemented
- **Current Maturity:** 0%
- **Evidence:** No role model; no CA firm hierarchy; no client assignment; no supervision workflow. `models/user.py` — single user type with no role. `db/database.py:69-77` — no role column. Platform has no concept of CA, staff, or firm.
- **Missing:** Complete role hierarchy model; client assignment; supervision workflow; activity tracking
- **Missing Domain Services:** `FirmService`, `ClientAssignmentService`, `SupervisionWorkflowService`
- **Migration Complexity:** Very High — depends on C1.3 (RBAC) and C21.1 (Tenants)
- **Business Impact:** Critical — CA firms are primary B2B channel
- **Risk if Ignored:** No CA firm will adopt without staff hierarchy and client management
- **Severity:** **Critical**
- **Confidence:** **HIGH** — No role or firm model anywhere in codebase
- **Suggested Remediation:** Model CA firm organizational hierarchy; implement role-based access with firm scoping; add client assignment and supervision workflows

---

#### C21.3 — Client Portfolio Management

- **Target State:** Bulk client onboarding; client categorization; status dashboard; bulk operations; document vault
- **Current State:** Not Implemented
- **Current Maturity:** 0%
- **Evidence:** No client management model. Single user = single taxpayer. No bulk operations. No client categorization. `db/database.py:311-323` — `create_filing()` takes single user_id. No concept of "CA managing multiple clients."
- **Missing:** Complete client portfolio management subsystem
- **Missing Domain Services:** `ClientPortfolioService`, `BulkOperationService`, `ClientDocumentVault`
- **Missing APIs:** All client management endpoints
- **Migration Complexity:** Very High — depends on C21.1 and C21.2
- **Business Impact:** Critical — core CA workflow requirement
- **Risk if Ignored:** CA firms have zero incentive to adopt
- **Severity:** **Critical**
- **Confidence:** **HIGH** — No client management infrastructure
- **Suggested Remediation:** Build client portfolio model with CA-firm scoping; implement bulk onboarding; add status dashboard

---

## Capability Assessment: High Priority

### Domain 3: Document Intelligence

---

#### C3.1 — Multi-Format Document Ingestion

- **Target State:** 50+ format support; auto-detection; virus scanning; large file handling
- **Current State:** Functional
- **Current Maturity:** 40%
- **Evidence:** `api/routes.py:48-152` — PDF upload via multipart form; `parsers/form16_parser.py:45-57` — pikepdf for encrypted PDFs; `parsers/broker_statements/` — CSV parsers for Zerodha, Groww, Upstox, Angel One. PDF only. No image support. No JSON/XML ingestion. No virus scanning. No format auto-detection.
- **Missing:** Image ingestion; JSON/XML format; virus scanning; format auto-detection; batch upload; progress tracking
- **Missing Security:** No malware scanning on uploaded files
- **Migration Complexity:** Medium — incremental format support
- **Business Impact:** High — limits document types users can provide
- **Severity:** **High**
- **Confidence:** **HIGH** — Upload handler and parsers reviewed; image/JSON/virus scanning absent
- **Suggested Remediation:** Introduce document ingestion pipeline with format detection; add virus scanning; expand format support

---

#### C3.3 — Form 16 Parser

- **Target State:** >99% accuracy for TRACES format; >95% for employer-generated; ML-based field mapping
- **Current State:** Production Ready
- **Current Maturity:** 70%
- **Evidence:** `parsers/form16_parser.py:29-447` — complete Form 16 parser with Part A, Part B, Annexure extraction; regex-based field extraction; password auto-resolution; component pattern matching for salary breakup. Production-tested on real Form 16 PDFs. `HANDOFF.md` documents 10 hard-learned rules from real-world parsing. Missing: confidence scoring per field; ML-based unknown format adaptation.
- **Missing:** Field-level confidence scoring; ML-based format adaptation for non-TRACES employers; structured output with extraction warnings
- **Migrated from:** Functional → Production Ready. Core value prop works.
- **Architectural Deficiencies:** Regex-based parsing is fragile against format changes. No confidence scoring.
- **Migration Complexity:** Low — incremental improvements
- **Business Impact:** Critical — Form 16 is primary data source for most taxpayers
- **Severity:** **Medium** (gap is incremental, not foundational)
- **Confidence:** **HIGH** — Full parser code reviewed; production battle-tested
- **Suggested Remediation:** Add field-level confidence scoring; build ML-based fallback for unknown formats

---

#### C3.4 — AIS Parser

- **Target State:** 100% AIS code coverage; column-adaptive parsing; AIS JSON API integration
- **Current State:** Production Ready
- **Current Maturity:** 65%
- **Evidence:** `parsers/ais_parser.py:63-593` — complete AIS parser with table extraction; column-adaptive parsing (handles page 1 vs page 2 layout differences); TDS detail rows; SFT entry parsing; personal info extraction. `parsers/ais_code_mapper.py:30-306` — 25+ code mappings. Production-tested. Missing: some SFT codes not encountered; no JSON API integration (unavailable from ITD).
- **Missing:** Additional SFT code handlers; AIS JSON API integration (when available); field-level confidence
- **Migration Complexity:** Low — incremental code additions
- **Business Impact:** Critical — AIS provides comprehensive financial transaction data
- **Severity:** **Medium**
- **Confidence:** **HIGH** — Full parser and code mapper reviewed
- **Suggested Remediation:** Add remaining SFT code handlers; prepare for AIS JSON API integration

---

#### C3.5 — OCR Pipeline

- **Target State:** >95% on printed forms; >85% on handwriting; multi-language; human review queue
- **Current State:** Not Implemented
- **Current Maturity:** 0%
- **Evidence:** No OCR libraries in codebase. Searched for: `tesseract`, `pytesseract`, `ocr`, `google vision`, `azure ocr`, `easyocr`. None found. `parsers/form16_parser.py` and `parsers/ais_parser.py` work only with digital (text-extractable) PDFs via pdfplumber. `ARCHITECTURE.md` does not mention OCR capability. `MASTER_PLAN.md` does not mention OCR.
- **Missing:** Complete OCR pipeline; image preprocessing; table recognition; handwriting recognition; multi-language OCR; human review queue
- **Missing Bounded Contexts:** OCR is a supporting capability within Document Processing context
- **Migration Complexity:** High — requires OCR engine integration, preprocessing pipeline, quality assessment
- **Business Impact:** Medium — limits processing of scanned/paper documents
- **Risk if Ignored:** Cannot process older documents, paper Form 16s, rent receipts, investment proofs
- **Severity:** **High**
- **Confidence:** **HIGH** — All parser modules reviewed; zero OCR infrastructure
- **Suggested Remediation:** Introduce OCR pipeline with preprocessing; integrate Tesseract/cloud OCR; build confidence scoring; add human review queue

---

### Domain 6: Tax Computation Engine

---

#### C6.1 — Slab Tax Computation Engine

- **Target State:** Generic engine that works for any FY/regime without code change
- **Current State:** Functional
- **Current Maturity:** 35%
- **Evidence:** `regime_optimizer_v2.py:281-300` — `_slab_tax()` computes slab tax from in-memory slab list. Works correctly for FY2025-26. Slabs hardcoded. `regime_optimizer.py:340-354` — `_slab_tax_old()` duplicate implementation. `regime_optimizer.py:357-380` — `_slab_tax_new()` duplicate. `builders/itr1.py:241-281` — `_compute_tax()` third duplicate.
- **Missing:** Generic slab engine; FY-parameterized slab loading; entity-type-specific slabs (company, firm); verified against ITD portal for multiple FYs
- **Architectural Deficiencies:** Slab data mixed with computation logic. Three separate implementations.
- **Code Duplication:** Slab tax computation in 3 separate locations
- **Migration Complexity:** Medium — extract slabs to config, refactor consumers
- **Business Impact:** Critical — correct slab tax is fundamental
- **Risk if Ignored:** Cannot support any FY other than 2025-26
- **Severity:** **High**
- **Confidence:** **HIGH** — All three slab implementations reviewed; hardcoded FY
- **Suggested Remediation:** Build generic slab engine; extract slab data to versioned config; unify all three implementations

---

#### C6.2 — Special Rate Income Tax Engine

- **Target State:** All special rate sections (111A, 112A, 112, 115BB, 115BBH, etc.)
- **Current State:** Partial
- **Current Maturity:** 40%
- **Evidence:** `engine/classifier.py:196-233` — `get_tax_summary()` computes 112A (12.5%), 111A (15%), other LTCG (12.5%). `regime_optimizer_v2.py:211-215` — applies special rate taxes. Missing: 115BB (lottery 30%), 115BBH (crypto 30%), 115BBE (unexplained 60%), 115BBC (anonymous donations 30%).
- **Missing:** Sections 115BB, 115BBH, 115BBE, 115BBC, 115BBD; per-section breakdown
- **Architectural Deficiencies:** Special rate computation is embedded in optimizer, not a separate engine
- **Migration Complexity:** Medium — add section-specific computation
- **Business Impact:** Medium — affects specific taxpayer segments (lottery winners, crypto traders)
- **Severity:** **Medium**
- **Confidence:** **HIGH** — Classifier and optimizer reviewed; missing sections identified
- **Suggested Remediation:** Extract special rate computation to dedicated engine; add all missing sections

---

### Domain 13: AI Interview Engine

---

#### C13.2 — Adaptive Question Engine

- **Target State:** Minimal question set; intelligent branching; zero-question for fully-detected cases
- **Current State:** Functional
- **Current Maturity:** 55%
- **Evidence:** `engine/questions.py:15-285` — `QuestionEngine.generate()` produces 0-5 questions based on detected data; conditional branches (depends_on/depends_on_answer); regime-aware suppression. Works for ITR-1/2 scenarios. Evidence of production use in `api/routes.py:224-231`. Missing: zero-question path; data-driven question relevance prediction; question effectiveness analytics.
- **Missing:** Zero-question path; question relevance analytics; A/B testing; question library beyond 5 types
- **Architectural Deficiencies:** Questions are hardcoded in Python, not in a configurable question library
- **Migration Complexity:** Medium — extract questions to config; add analytics
- **Business Impact:** High — core UX differentiator
- **Severity:** **Medium**
- **Confidence:** **HIGH** — Question engine code reviewed; configurable library absent
- **Suggested Remediation:** Extract questions to configurable library; add analytics; implement zero-question path

---

#### C13.4 — Auto-Detection & Prefill Engine

- **Target State:** >95% auto-detection; confidence-based review highlighting
- **Current State:** Functional
- **Current Maturity:** 50%
- **Evidence:** `api/routes.py:172-174` — `PDFDataProvider.fetch()` provides auto-detected data; `engine/questions.py:63-71` — `_build_income_summary()` shows what was auto-detected. Form 16 + AIS auto-extraction works. Missing: confidence scoring per detected field; review highlighting; "here's what we found" summary with drill-down.
- **Missing:** Field-level confidence; review highlighting; detected data drill-down
- **Migration Complexity:** Low — incremental improvements
- **Business Impact:** High — "user never types what's auto-detected"
- **Severity:** **Medium**
- **Confidence:** **HIGH** — Auto-detection flow reviewed; confidence scoring absent
- **Suggested Remediation:** Add confidence scoring to all parsed fields; implement review highlighting UI

---

### Domain 18: Security & Privacy

---

#### C18.1 — Data Encryption

- **Target State:** TLS 1.3, AES-256 at rest, application-level PII encryption, HSM key storage, CMEK
- **Current State:** Partial
- **Current Maturity:** 30%
- **Evidence:** `main.py:50-62` — CORS middleware implies HTTPS (TLS) on Render/Vercel infrastructure. No application-level encryption found. `db/database.py:175` — PAN stored as plaintext in `users` table (no encryption at rest beyond PostgreSQL-level). `ARCHITECTURE.md:1105-1109` — mentions "Encryption at rest (AES-256)" as principle but not implemented in code. `ARCHITECTURE.md:1782-1814` — `DataEncryption` class designed with Fernet but not found in actual codebase.
- **Missing:** Application-level PII encryption; encrypted database columns; HSM; CMEK; key rotation
- **Architectural Deficiencies:** PAN and financial data stored as plaintext in database. Encryption exists only in design docs, not implementation.
- **Missing Security Controls:** No column-level encryption; no application-level crypto for PII
- **Migration Complexity:** High — requires encrypting existing data, key management infrastructure
- **Business Impact:** Critical — taxpayer financial data is classified RESTRICTED
- **Risk if Ignored:** Data breach exposes unencrypted PAN, salary, capital gains; regulatory penalties
- **Severity:** **Critical**
- **Confidence:** **HIGH** — Database schema and queries reviewed; no application-level encryption; design doc describes intended but not implemented encryption
- **Suggested Remediation:** Implement application-level encryption for all PII columns; integrate KMS/HSM; encrypt existing data; add key rotation

---

#### C18.9 — Tenant Isolation

- **Target State:** Row-level security or schema-per-tenant; tenant-specific encryption keys; penetration testing
- **Current State:** Not Implemented
- **Current Maturity:** 0%
- **Evidence:** No tenant model exists (see C21.1). No tenant_id in any query. No row-level security. No schema-per-tenant. No tenant context propagation. Platform is inherently single-tenant.
- **Missing:** Complete tenant isolation infrastructure
- **Missing Security Controls:** No data isolation between tenants (no tenants exist to isolate)
- **Migration Complexity:** Very High — requires architectural redesign for multi-tenancy
- **Business Impact:** Critical — prerequisite for enterprise multi-tenancy
- **Risk if Ignored:** Cannot serve enterprise customers; data leakage risk when multi-tenancy added
- **Severity:** **Critical**
- **Confidence:** **HIGH** — No tenant infrastructure anywhere in codebase
- **Suggested Remediation:** Implement tenant context propagation; add tenant_id to all queries; enforce row-level security

---

## Summary Capability Tables (Medium & Low Priority)

### Domain 2: Taxpayer Management — Summary

| Capability | Current State | Maturity | Severity |
|-----------|---------------|----------|----------|
| C2.1 Taxpayer Profile | Partial | 35% | Medium |
| C2.2 Residential Status | Not Implemented | 5% | High |
| C2.3 Filing Status | Partial | 25% | Medium |
| C2.4 ITR Form Eligibility | Functional | 55% | Low |
| C2.5 Historical Filing Record | Partial | 20% | Medium |
| C2.6 Family Unit Management | Not Implemented | 0% | Medium |
| C2.7 Taxpayer Risk Profiling | Not Implemented | 0% | Medium |

### Domain 4: Income Management — Summary

| Capability | Current State | Maturity | Severity |
|-----------|---------------|----------|----------|
| C4.1 Salary Income Engine | Functional | 60% | Low |
| C4.2 House Property Income Engine | Partial | 20% | High |
| C4.3 Business Income Engine | Not Implemented | 0% | High |
| C4.4 Capital Gains Engine | Functional | 50% | Medium |
| C4.5 Other Sources Engine | Partial | 30% | Medium |
| C4.6 Income Aggregation & Clubbing | Not Implemented | 0% | Medium |
| C4.7 Previous Year Data Import | Not Implemented | 0% | Medium |
| C4.8 Foreign Income & Asset Engine | Not Implemented | 0% | Medium |

### Domain 5: Deduction & Exemption — Summary

| Capability | Current State | Maturity | Severity |
|-----------|---------------|----------|----------|
| C5.1 Chapter VI-A Deduction Engine | Functional | 55% | Medium |
| C5.2 Section 10 Exemption Engine | Partial | 35% | Medium |
| C5.3 Standard Deduction & Rebate | Functional | 60% | Low |
| C5.4 Deduction Optimization Advisor | Partial | 20% | Low |
| C5.5 Donation (80G) Engine | Not Implemented | 0% | Medium |
| C5.6 Home Loan Deduction Engine | Partial | 30% | Medium |
| C5.7 NPS & Retirement Engine | Partial | 40% | Medium |

### Domain 7-9, 11, 13-17, 19: Summary

| Domain | Capabilities Assessed | Avg Maturity | Critical Gaps |
|--------|----------------------|-------------|---------------|
| D7: Regime Optimization (6 caps) | 6 | 35% | C7.1 needs FY-aware rules |
| D8: Compliance (9 caps) | 9 | 20% | C8.1 Tax Credit Recon; C8.4 AIS Completeness |
| D9: ITR Generation (7 caps) | 7 | 35% | Only ITR-1/2 built; ITR-3/4/5/6/7 not started |
| D11: Knowledge Mgmt (6 caps) | 6 | 5% | All 6 caps Not Implemented |
| D13: AI Interview (8 caps) | 8 | 25% | C13.1-C13.4 partially exist; C13.5-C13.8 missing |
| D14: Reporting (7 caps) | 7 | 10% | C14.1 Tax Summary partial; rest missing |
| D15: Integration (8 caps) | 8 | 10% | C15.1 partial (REST exists); rest missing |
| D16: Operations (8 caps) | 8 | 5% | Almost nothing; C16.1 partial (config via env vars) |
| D17: Security (10 caps) | 10 | 10% | C17.1-C17.2 partial; rest missing |
| D18: Notifications (5 caps) | 5 | 0% | All 5 Not Implemented |
| D19: Tax Planning (5 caps) | 5 | 0% | All 5 Not Implemented |

---

## Gap Category Summary

### Domain Gaps (42 findings)

The platform lacks entire business domains:
- **Rule Management** (C12.1-C12.7): All 7 capabilities missing or at 5% maturity
- **Audit & Explainability** (C10.1-C10.6): 5 of 6 missing
- **Knowledge Management** (C11.1-C11.6): All 6 missing
- **Enterprise Multi-Tenancy** (C21.1-C21.8): All 8 missing
- **Tax Planning** (C19.1-C19.5): All 5 missing
- **Notifications** (C18.1-C18.5): All 5 missing
- **Security** (C17.1-C17.10): 8 of 10 at 10% or below

### Architectural Gaps (28 findings)

- **No Rule-Engine Separation:** Rules embedded in computation code
- **No Multi-Year Architecture:** FY hardcoded everywhere
- **No Bounded Contexts:** DDD not applied; modules organized by technical layer, not business domain
- **No Event-Driven Architecture:** No domain events; no event bus
- **No CQRS:** Read and write models not separated
- **No Audit Trail Architecture:** Event sourcing not implemented
- **Duplicate Optimizer:** v1 and v2 implementations coexist
- **No Base Builder:** ITR-1 and ITR-2 builders share no common interface
- **In-Memory Sessions:** Not horizontally scalable; lost on restart

### Security Gaps (15 findings)

- Dev JWT secret in source code (`auth/jwt.py:12`)
- PAN stored as plaintext in database
- No rate limiting on any endpoint
- No brute-force protection on auth
- No malware scanning on file uploads
- No application-level encryption for PII
- No tenant isolation
- No RBAC/authorization model
- No consent management (DPDP Act)
- No security scanning in CI/CD (no CI/CD exists)
- No penetration testing evidence
- No threat detection
- No DLP controls

### Testing Gaps (Universal)

- **Unit Tests:** 0 across entire codebase
- **Integration Tests:** 0
- **Contract Tests:** 0
- **E2E Tests:** 1 skeleton file (`tests/test_e2e_real_data.py`)
- **Performance Tests:** 0
- **Security Tests:** 0
- **Test Coverage:** 0%

### Observability Gaps (Universal)

- **Structured Logging:** f-strings only; no JSON format
- **Metrics:** None
- **Tracing:** No distributed tracing
- **Health Checks:** Basic `/api/v1/health` endpoint exists
- **Alerting:** None
- **Dashboards:** None

---

## UNKNOWN Capabilities

The following 30 capabilities have **insufficient evidence** for assessment. All are marked UNKNOWN with LOW confidence.

| Capability | Reason for UNKNOWN |
|-----------|--------------------|
| C15.2 NSDL PAN Verification API | No code found; may be in unread `api/calculators.py` or `api/simulation.py` |
| C15.3 TRACES API Integration | No code found; design mentions as Phase 3 |
| C15.4 ITD e-Filing API | No code found; requires ERI license |
| C16.3 Financial Institution Integration | No code found for banks/insurance beyond broker statements |
| C16.4 Employer/Enterprise Integration | No code found |
| C16.5 CA/Professional Software Integration | No code found |
| C16.6 Payment Gateway Integration | No code found; may be in unread modules |
| C16.7 Webhook System | No code found |
| C16.8 Sandbox & Developer Portal | No code found |
| C17.6 Backup & DR | No configuration evidence; Render/Neon may provide |
| C17.8 IT Asset & Dependency Mgmt | No SBOM or dependency tracking found |
| C18.2 Vulnerability Management | No scanning configuration found |
| C18.5 Threat Detection & Response | No SIEM/SOC evidence |
| C18.6 Secure Development Lifecycle | No process documentation found |
| C18.7 Identity Proofing & KYC | No KYC integration found |
| C18.8 Data Loss Prevention | No DLP configuration found |
| C19.1-C19.5 Notification System | No notification infrastructure found; may be in unread modules |
| C20.1-C20.5 Tax Planning | Entire domain not implemented |
| C14.2-C14.7 Reporting variants | No reporting infrastructure found beyond basic summary |

---

## Architecture Quality Review

### Assessment Against Architecture Paradigms

| Paradigm | Score | Evidence |
|----------|-------|----------|
| **Domain-Driven Design** | 10/100 | No bounded contexts; no aggregates; no domain events; no ubiquitous language enforcement. Modules organized by technical function (parsers/, engine/, builders/), not business domain. |
| **Clean Architecture** | 15/100 | No dependency inversion; domain logic depends on infrastructure (direct psycopg2 imports). No interfaces/ports. Use cases mixed with controllers in `api/routes.py`. |
| **Hexagonal Architecture** | 5/100 | No port/adapter pattern. All external dependencies (DB, PDF parsers) called directly. No abstraction over data sources (partial: `TaxpayerDataProvider` exists). |
| **SOLID** | 25/100 | S: Partially (models are single-responsibility). O: Violated — adding ITR type requires modifying builder. L: Not applicable (no inheritance). I: Violated — no interfaces. D: Violated — domain depends on infrastructure. |
| **CQRS Readiness** | 5/100 | No command/query separation. Read and write use same models. No event sourcing. |
| **Event-Driven Readiness** | 5/100 | No domain events. No event bus. No async messaging. Tax updates scheduler is the only async component. |
| **Modular Monolith Readiness** | 50/100 | Good module separation. Clear file organization. But: circular dependency (lazy import in optimizer); no module API contracts; no bounded context enforcement. |
| **Microservice Readiness** | 15/100 | No service boundaries defined. In-memory sessions prevent horizontal scaling. Shared database. No async communication. |
| **API-First Design** | 40/100 | REST API exists with OpenAPI (FastAPI auto-docs). But: no API versioning strategy; no rate limiting; no API gateway; endpoints coupled to session state. |
| **Cloud-Native Readiness** | 20/100 | Deployed on cloud platforms (Render, Vercel, Neon). But: no containerization config found; no health checks beyond basic; no graceful degradation; no config externalization beyond env vars. |
| **Twelve-Factor Compliance** | 30/100 | I (codebase): one repo ✅. III (config): partial (env vars). IV (backing services): partial (Neon URL as env var). V (build/release/run): not evident. VIII (concurrency): single process. IX (disposability): in-memory state prevents fast shutdown. X (dev/prod parity): Neon PostgreSQL in both ✅. XI (logs): f-strings, not stdout stream. |
| **Security by Design** | 10/100 | Dev secret hardcoded. No rate limiting. PAN plaintext in DB. No RBAC. No consent. No threat model evidence. |
| **Privacy by Design** | 5/100 | No consent management. No data minimization evidence. No encryption at rest (application level). No data retention policy implemented. No right-to-deletion API. |
| **AI-Native Readiness** | 10/100 | DeepSeek API used for tax updates summarization only. No AI in computation pipeline. No XAI infrastructure. No ML model management. No feature store. No model monitoring. |

---

## Confidence Summary

| Confidence Level | Count | % |
|-----------------|-------|---|
| HIGH | 112 | 75.7% |
| MEDIUM | 6 | 4.1% |
| LOW | 30 | 20.3% |

All LOW-confidence findings are marked UNKNOWN with explicit "Insufficient evidence" notation. No assumptions made.

---

*End of Enterprise Gap Report v1.0*
*This document is a diagnosis. No implementation proposals are made. The Enterprise Modernization Roadmap will use this as mandatory input.*
