# Changelog

All notable changes to the TaxStox platform.

---

## v0.11.0-alpha (2026-08-18)

### Internal Alpha Release

**Programs Complete:**
- Enterprise Modernization Program (M0-M11): 12 waves, 189 tests
- Product Engineering Program (P1-P7): 7 waves, 201 tests

**Production Readiness:**
- Product Readiness Review completed (2026-07-07)
- Production Readiness Remediation Program established (6 waves: PR1-PR6)
- PR1 (Security Hardening) complete
- PR2 (Data Protection & Audit) complete
- PR3 (Financial Year Propagation) complete
- PR4 (Test Infrastructure & API Coverage) complete
- PR5 (Operational Readiness) complete

### Major Capabilities (390 total capabilities assessed)

**Enterprise Multi-Tenancy:** Tenant aggregate root, RBAC with 4-level role hierarchy, CA firm onboarding, client portfolio management, tenant context middleware, white-label branding, SSO configuration (SAML/OIDC), subscription tiers (Free/Professional/Enterprise), firm dashboard, bulk client import, supervision workflows.

**Security & Privacy:** Encryption service (Fernet), consent aggregate (DPDP Act), PII masking, security headers middleware, data classification.

**Integration & Ecosystem:** PAN/ITD/FI port interfaces, webhook dispatcher (HMAC-SHA256), API key management.

**AI Intelligence:** Tax knowledge graph (100+ nodes, 80+ edges), provision knowledge base (30+ provisions), tax glossary (50+ terms), CBDT circular database, taxpayer education content, finance act change analyzer, rule conflict detector, rule impact analyzer, adaptive interview personalization, offline interview pack, explainable AI engine (counterfactuals, feature contribution, sensitivity analysis).

**Customer Experience:** Multi-channel notification engine (email/SMS/in-app) with 4 standard templates, deadline reminders with configurable schedules, tax scenario simulator, loss harvesting engine (7 asset types), multi-year tax projection, refund tracker (8-stage timeline), data export/portability (DPDP-compliant).

**Operations:** Backup/DR plan (RPO 5min, RTO 30min), identity proofing (PAN/NSDL, Aadhaar e-KYC stubs), secrets management inventory (9 secrets), API gateway with rate limiting (token bucket), developer portal (5 API products), payment gateway adapter (Razorpay stub), operational monitoring with health checks and runbook.

### PR1 Security Improvements

- Google OAuth: full cryptographic ID token verification via google-auth library (JWKS, RSA signature, iss/aud/exp validation)
- Password reset: database-backed with SHA-256 hashed tokens, 15-min TTL, single-use enforcement
- Session IDs: 128-bit UUID4 (from 32-bit)
- Rate limiting: enforced on auth (20/min login, 5/min register), upload (10/min), export (10/min)
- Security headers: CSP (env-aware), HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, Cross-Origin-Opener-Policy, Cross-Origin-Resource-Policy
- PDF password removed from application logs

### PR2 Data Protection & Audit

- Encryption key enforcement at startup (fail-fast if TAXSTOX_ENCRYPTION_KEY missing)
- PAN encryption in database (Fernet)
- Audit trail infrastructure: AuditContext, AuditEvent, AuditTrail wired to computation pipeline
- Consent management (DPDP Act compliant)

### PR3 Financial Year Propagation

- Authoritative FY resolution from Form 16 Assessment Year (no hardcoded FY2025-26 default)
- FinancialYear value object with validation and AY↔FY mapping
- FY propagated through: ClassificationEngine, DeductionsComputer, SalaryComputer, RegimeOptimizerV2, ITR builders, ITRValidator
- 20 tests covering FY propagation end-to-end

### PR4 Test Infrastructure & API Coverage

- TestClient fixture without lifespan (no DB/encryption/scheduler at import)
- API auth, filing, parser, ITR builder, classifier, golden vector tests
- Pytest markers: unit, integration, api, e2e, db_required, jwt_required
- Real-data E2E test externalized (no PII committed)

### PR5 Operational Readiness

- **PR5.1 Global Redis Rate Limiting** (PRRP-DEFER-002): RedisRateLimitStore with atomic Lua INCR+EXPIRE, graceful in-memory fallback, 10 offline tests
- **PR5.2 Persistent Sessions**: SessionBackend Protocol, InMemorySessionBackend, RedisSessionBackend (pickle+TTL, sliding idle window), 10 offline tests
- **PR5.3 Health/Monitoring/Metrics**: MetricsMiddleware (latency, status, error rate, cardinality-bounded paths), /metrics and /health/detailed endpoints, 12 tests
- **PR5.4 Scheduler Reliability**: Idempotent start_scheduler(), removed dead trigger=None job, initial sync via call_later, 4 tests
- **PR5.5 Backup/DR**: Assessed out of scope (config-only value objects)
- **PR5.6 CI/Quality Gates**: Pytest markers added; 520 tests pass, 29 skipped

### Architecture

- 13 bounded contexts: Enterprise, Security, Integration, Taxation, Knowledge, Interview, Reporting, Notification, Tax Planning, Refund, Operations, Gateway, Payment
- Clean Architecture: domain layer pure (zero framework imports), infrastructure adapters implement domain protocols
- EAC Certified v1.0 (5 non-blocking observations)
- 520 tests, 9 golden vectors, CI pipeline (lint + typecheck + test + security)

### Known Limitations

- JWT: stored in localStorage (httpOnly cookie migration deferred: PRRP-DEFER-001)
- ITR-3/4/5/6/7: domain/engine layer only, no builders (post-beta)
- Form 26AS parser: not implemented (post-beta)

### Deferred Items

See `docs/architecture/PRRP-DeferredItems.md`
- PRRP-DEFER-001: JWT httpOnly cookie migration (post-PR6)

### Next Milestone

Closed Beta (PR6 complete, estimated ~6 weeks)

---

## Pre-v0.10.0

- Enterprise Modernization M0-M7: Core domain foundation, document intelligence, income/deduction engines, tax computation, compliance, audit/explainability, AI knowledge platform
- Initial MVP: JWT auth, SQLite DB, dashboard, calculators, broker import, 21 API endpoints
- Production deployment: Render + Vercel + Neon PostgreSQL
