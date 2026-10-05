# Decisions Memory

> **Last Updated:** 2026-10-05

---

## Key Architecture Decisions

| ID | Date | Decision | Status |
|----|------|----------|--------|
| DEC-0001 | 2026-07-05 | AI-DOS as governance framework | ACTIVE |
| DEC-0008 | 2026-07-05 | Enterprise Capability Model ratified as FROZEN target (148 capabilities) | ACTIVE |
| DEC-0011 | 2026-07-05 | 15 enterprise risks identified, 4 Critical | ACTIVE |
| DEC-0012 | 2026-07-05 | Modular monolith: FastAPI + Next.js + Neon PostgreSQL | ACTIVE |
| DEC-0013 | 2026-07-05 | Enterprise Modernization Roadmap approved (M0-M11) | COMPLETE |
| DEC-0014 | 2026-07-05 | Product Engineering Roadmap approved (P1-P7) | COMPLETE |
| DEC-0015 | 2026-07-07 | Product Readiness Review: Ready for Internal Alpha | ACTIVE |
| DEC-0016 | 2026-07-07 | Production Readiness Remediation Program established (PR1-PR6) | ACTIVE |
| DEC-0017 | 2026-08-01 | PR1: Google OAuth uses google-auth library (not custom JWKS) | ACTIVE |
| DEC-0018 | 2026-08-01 | Password reset: database-backed with hashed tokens, not in-memory | ACTIVE |
| DEC-0019 | 2026-08-01 | Rate limiting: storage-agnostic Protocol pattern | ACTIVE |
| DEC-0020 | 2026-08-01 | JWT localStorage → httpOnly cookie migration deferred (PRRP-DEFER-001) | ACTIVE |
| DEC-0021 | 2026-08-01 | v0.10.0-alpha released — Internal Alpha | ACTIVE |
| DEC-0022 | 2026-10-05 | Beta release candidate validated (520 tests passed, 0 failures, 29 skipped, 9 golden vectors passed); JWT httpOnly migration (PRRP-DEFER-001) scheduled for post-PR6 | ACTIVE |