# Changelog

All notable changes to the TaxStox platform.

---

## v0.10.0-alpha (2026-08-01)

### Internal Alpha Release

**Programs Complete:**
- Enterprise Modernization Program (M0-M11): 12 waves, 189 tests
- Product Engineering Program (P1-P7): 7 waves, 201 tests

**Production Readiness:**
- Product Readiness Review completed (2026-07-07)
- Production Readiness Remediation Program established (6 waves: PR1-PR6)
- PR1 (Security Hardening) complete

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

### Architecture

- 13 bounded contexts: Enterprise, Security, Integration, Taxation, Knowledge, Interview, Reporting, Notification, Tax Planning, Refund, Operations, Gateway, Payment
- Clean Architecture: domain layer pure (zero framework imports), infrastructure adapters implement domain protocols
- EAC Certified v1.0 (5 non-blocking observations)
- 407 tests, 9 golden vectors, CI pipeline (lint + typecheck + test + security)

### Known Limitations

- Sessions: in-memory (Redis migration in PR5)
- Rate limiter: per-worker (Redis global in PR5)
- JWT: stored in localStorage (httpOnly cookie migration deferred: PRRP-DEFER-001)
- PAN: plaintext in database (encryption in PR2)
- Audit trail: not wired to computation pipeline (PR2)
- ITR builders: FY/AY hardcoded (PR3)
- ITR-3/4/5/6/7: domain/engine layer only, no builders (post-beta)
- Form 26AS parser: not implemented (post-beta)
- No API/integration/E2E tests (PR4)

### Deferred Items

See `docs/architecture/PRRP-DeferredItems.md`
- PRRP-DEFER-001: JWT httpOnly cookie migration
- PRRP-DEFER-002: Global Redis rate limiting

### Next Milestone

Closed Beta (PR2-PR6 complete, estimated ~18 weeks)

---

## Pre-v0.10.0

- Enterprise Modernization M0-M7: Core domain foundation, document intelligence, income/deduction engines, tax computation, compliance, audit/explainability, AI knowledge platform
- Initial MVP: JWT auth, SQLite DB, dashboard, calculators, broker import, 21 API endpoints
- Production deployment: Render + Vercel + Neon PostgreSQL
