# Technical Debt Heatmap — IT_Returns Platform

> **Date:** 2026-07-05
> **Method:** All debt items identified from source code audit, Architecture Recovery Report, and Gap Analysis

---

## Debt Summary by Category

| Category | Critical | High | Medium | Low | Total Items |
|----------|----------|------|--------|-----|-------------|
| Domain | 3 | 4 | 3 | 0 | 10 |
| Architecture | 6 | 5 | 4 | 0 | 15 |
| Code | 0 | 3 | 6 | 2 | 11 |
| Infrastructure | 1 | 2 | 2 | 0 | 5 |
| Security | 3 | 4 | 2 | 1 | 10 |
| Testing | 1 | 1 | 0 | 0 | 2 |
| DevOps | 0 | 2 | 1 | 1 | 4 |
| Operations | 0 | 1 | 2 | 1 | 4 |
| Documentation | 0 | 1 | 1 | 1 | 3 |
| **TOTAL** | **14** | **23** | **21** | **6** | **64** |

---

## Domain Debt

| ID | Item | Severity | Business Impact | Est. Effort | Evidence |
|----|------|----------|-----------------|-------------|----------|
| DOM-001 | Taxpayer identity mixed with auth credentials in `users` table | High | Cannot evolve taxpayer profile independently of auth | M | `db/database.py:69-77` — users table combines identity + credentials |
| DOM-002 | No FinancialYear domain type — strings used everywhere | Critical | Every module hardcodes "FY2025-26"; no type safety | L | `builders/itr_json_builder.py:32` — `FY = "2025-26"` |
| DOM-003 | No separation of Old vs New Regime as domain concept — booleans used | High | Adding third regime (DTC) requires rewriting all conditionals | M | `regime_optimizer_v2.py:148` — `is_new_regime: bool` parameter |
| DOM-004 | Capital gains term field is free-text string, not enum | Medium | "Long term" vs "Long" matching fragile | L | `classifier.py:55-56` — `sale.term.lower() == "long"` string comparison |
| DOM-005 | UserAnswers model mixes concerns (rent + health + 80C + home loan + other) | Medium | No separation of deduction domains in user input | L | `models/tax.py:82-102` — single UserAnswers class |
| DOM-006 | No domain events for any business action | Critical | Cannot implement audit trail or cross-context communication | XL | Zero event classes in entire codebase |
| DOM-007 | Regime selection uses string comparison, not domain logic | Medium | Fragile; "new"/"old" strings scattered | L | `api/routes.py:292` — `is_new = session.regime_result.recommended.value == "new"` |
| DOM-008 | No aggregate roots enforcing consistency boundaries | High | Any code can modify any model without invariant checks | L | No aggregate pattern in any module |
| DOM-009 | No ubiquitous language — "taxable_income" vs "total_income" used interchangeably | Medium | Confusion between domain experts and developers | L | `models/tax.py:153-154` — `final_total_income` and `final_tax_liability` alongside `taxable_income` in Form 16 |
| DOM-010 | Missing Value Objects for PAN, Aadhaar, IFSC — raw strings used | Critical | No domain validation encapsulated; validation scattered | L | `models/user.py:21` — PAN regex in model; `builders/validator.py:32` — duplicate PAN regex |

---

## Architecture Debt

| ID | Item | Severity | Business Impact | Est. Effort | Evidence |
|----|------|----------|-----------------|-------------|----------|
| ARC-001 | Tax rules hardcoded in computation engine — violates I2 (Rule-Engine Separation) | Critical | Cannot support any FY without code change | XL | `regime_optimizer_v2.py:39-68` — slab constants in code |
| ARC-002 | Single financial year architecture — violates I1 (Multi-Year) | Critical | Platform obsolete April 1, 2026 | XL | Hardcoded AY in `builders/itr_json_builder.py:31` |
| ARC-003 | No audit trail for computations — violates I3 (Complete Audit Trail) | Critical | Cannot prove computation correctness | XL | Zero audit infrastructure |
| ARC-004 | No explainability infrastructure — violates I4 (Explainability) | Critical | Cannot explain tax to users or auditors | L | `recommendation_engine.py` only; no general explanation engine |
| ARC-005 | Dual optimizer implementations (v1 + v2) — violates P1 (Consistency) | High | Maintenance burden; risk of divergence | M | `regime_optimizer.py` (401 lines) and `regime_optimizer_v2.py` (360 lines) |
| ARC-006 | No base class/interface for ITR builders — violates P10 (Extensibility) | High | Adding ITR-3 requires duplicating ITR-2 builder pattern | M | `builders/itr1.py` and `builders/itr_json_builder.py` — no shared base |
| ARC-007 | Tax slab computation duplicated in 3 locations | High | Slab changes must be made in 3 places | S | `regime_optimizer.py`, `regime_optimizer_v2.py`, `builders/itr1.py` |
| ARC-008 | Circular dependency between optimizer and classifier | Medium | Fragile lazy import; breaks if call order changes | S | `regime_optimizer_v2.py:334-335` — lazy import inside method |
| ARC-009 | API routes as god orchestrator (595 lines) | Medium | Tight coupling; hard to test; multiple responsibilities | M | `api/routes.py` — orchestrates 7+ engines directly |
| ARC-010 | In-memory session state prevents horizontal scaling | High | Cannot scale beyond single process | M | `utils/session.py` — dict-based SessionManager |
| ARC-011 | No bounded context separation — modules organized by layer, not domain | High | Cross-domain coupling increases with each feature | XL | Directory structure: `parsers/`, `engine/`, `builders/` — not `taxpayer/`, `income/`, `computation/` |
| ARC-012 | DTOs used as domain models — Pydantic models serve dual purpose | Medium | Domain logic leaks into API layer; validation scattered | M | `models/tax.py` — UnifiedTaxData is both domain model and API response |
| ARC-013 | Raw SQL throughout without migration framework | Medium | Schema changes are manual and risky | M | `db/database.py:64-101` — `CREATE TABLE IF NOT EXISTS` pattern |
| ARC-014 | Deduction limits replicated across engine and validator | Medium | Changing a limit requires updating multiple files | S | `deductions_computer.py:29-39` and `builders/validator.py:37-46` |
| ARC-015 | No feature flag / toggle infrastructure — all changes are binary deploy | Medium | Cannot gradually roll out features | M | Zero feature flag code in codebase |

---

## Code Debt

| ID | Item | Severity | Business Impact | Est. Effort | Evidence |
|----|------|----------|-----------------|-------------|----------|
| COD-001 | `builders/validator.py` at 968 lines — god module | High | Hard to maintain; hard to extend with new validation rules | M | `builders/validator.py` — 968 lines, 40+ validation methods |
| COD-002 | `api/routes.py` at 595 lines — god controller | High | Mixes upload, processing, answers, export, broker statements | M | `api/routes.py` |
| COD-003 | PAN regex duplicated in 3 files | Medium | Changing PAN validation requires 3 edits | S | `models/user.py:21`, `builders/validator.py:32`, `parsers/form16_parser.py:99` |
| COD-004 | `_to_decimal()` utility duplicated in 3 parser files | Medium | Identical function in `form16_parser.py`, `ais_parser.py`, and `broker_statements/generic.py` | S | `parsers/form16_parser.py:424-432` |
| COD-005 | Lazy imports to break circular dependencies | Medium | Fragile; hides architecture problem | S | `regime_optimizer_v2.py:334` |
| COD-006 | `Decimal(str(value))` conversion pattern repeated 100+ times | Low | Error-prone; no centralized conversion | S | Throughout engine/ and builders/ modules |
| COD-007 | F-string logging throughout — no structured logging | Medium | Cannot search/aggregate logs; PII risk (passwords logged) | M | Every `logger.info(f"...")` call |
| COD-008 | Hardcoded assessment year in multiple builder files | Medium | Must edit source to change AY | S | `builders/itr_json_builder.py:31` and `builders/itr1.py:24` |
| COD-009 | Exception handling with bare `except Exception` in some places | Low | Swallows errors; loses debugging context | S | `parsers/ais_parser.py:60-61` — `except Exception: return None` |
| COD-010 | Monolithic session object accumulates all state | Medium | Session becomes dumping ground for all request data | M | `utils/session.py` — Session object with 10+ attributes |
| COD-011 | Regime comparison uses string dict key access throughout | Medium | Typo in dict key silently returns wrong value | M | `api/routes.py:303-304` — `breakdown.get("income_salary", "0")` |

---

## Infrastructure Debt

| ID | Item | Severity | Business Impact | Est. Effort | Evidence |
|----|------|----------|-----------------|-------------|----------|
| INF-001 | In-memory sessions — lost on restart, prevents horizontal scaling | Critical | Server restart = all user sessions lost | M | `utils/session.py` |
| INF-002 | No database connection pooling configuration | High | Connection exhaustion under load | S | `db/database.py:23-26` — new connection per get_db() |
| INF-003 | No caching layer for tax rules or configuration | Medium | Repeated computation or config loading | M | All rule constants recomputed per request |
| INF-004 | PDF processing in request thread (no background workers) | Medium | Blocks event loop for large PDFs | M | `api/routes.py:73-105` — synchronous PDF parsing in route |
| INF-005 | No Redis/memcached integration | Medium | Sessions and cache are in-process only | M | No Redis client in any module |

---

## Security Debt

| ID | Item | Severity | Business Impact | Est. Effort | Evidence |
|----|------|----------|-----------------|-------------|----------|
| SEC-001 | Dev JWT secret hardcoded as default parameter | Critical | Token forgery if env var not set in production | S | `auth/jwt.py:12` — `"taxstox-dev-secret-change-in-production"` |
| SEC-002 | PAN stored as plaintext in database | Critical | Data breach exposes unencrypted PAN | M | `db/database.py:182` — PAN in plaintext INSERT |
| SEC-003 | No RBAC/authorization model — all authenticated users equal | Critical | Any user can access any data | L | No role model; no authorization middleware |
| SEC-004 | No rate limiting on any API endpoint | High | Upload/brute-force abuse possible | M | No rate limiting middleware |
| SEC-005 | No brute-force protection on login | High | Credential stuffing attacks possible | S | No login attempt tracking |
| SEC-006 | PDF passwords logged in plaintext | High | PAN-based passwords exposed in logs | S | `api/routes.py:92` — `logger.info(f"PARSED with pwd={pwd}")` |
| SEC-007 | No malware/virus scanning on file uploads | Medium | Malicious PDFs could be uploaded | M | No virus scanning in upload flow |
| SEC-008 | No CAPTCHA on registration or login | Medium | Bot account creation possible | S | No CAPTCHA integration |
| SEC-009 | `tempfile.NamedTemporaryFile` could leave PDFs on disk if crash | Low | Temporary file cleanup not guaranteed | S | `api/routes.py:76` — `delete=False` with manual unlink |
| SEC-010 | No CSP/security headers configuration visible | Low | XSS/clickjacking risk on frontend | S | No security header middleware in `main.py` |

---

## Testing Debt

| ID | Item | Severity | Business Impact | Est. Effort | Evidence |
|----|------|----------|-----------------|-------------|----------|
| TST-001 | Zero automated tests across entire backend | Critical | Cannot safely refactor; every change is manual QA | XL | `tests/test_e2e_real_data.py` — only test file; no pytest fixtures |
| TST-002 | No test framework structure (no conftest, no fixtures, no parametrize) | High | Cannot scale testing even when started | M | No `conftest.py` or `pytest.ini` in `tests/` |

---

## DevOps Debt

| ID | Item | Severity | Business Impact | Est. Effort | Evidence |
|----|------|----------|-----------------|-------------|----------|
| DEV-001 | No CI/CD pipeline evidence for automated testing/deployment | High | Manual deployment; no automated quality gates | M | No CI config for tests in `.github/workflows/` (may exist but not reviewed) |
| DEV-002 | No database migration framework (Alembic or similar) | High | Manual schema changes; no rollback | M | `db/database.py:64-101` — manual `CREATE TABLE IF NOT EXISTS` |
| DEV-003 | No containerization (no Dockerfile found in `apps/api/`) | Medium | Environment inconsistency risk | M | No Dockerfile in `apps/api/` |
| DEV-004 | No environment parity enforcement (dev vs prod) | Low | "Works on my machine" problems | S | Development uses local; production uses Render |

---

## Operations Debt

| ID | Item | Severity | Business Impact | Est. Effort | Evidence |
|----|------|----------|-----------------|-------------|----------|
| OPS-001 | No structured logging — f-strings only | High | Cannot search, aggregate, or alert on logs | M | All `logger.info(f"...")` in codebase |
| OPS-002 | No metrics/monitoring/alerting | High | Zero production visibility | L | No Prometheus/Grafana/Sentry |
| OPS-003 | No health check beyond basic endpoint | Medium | Cannot detect degraded state | S | `api/routes.py:568-571` — simple 200 OK |
| OPS-004 | No log levels enforced consistently | Low | DEBUG logs in production possible | S | `main.py:24-25` — logging set to INFO at startup |

---

## Documentation Debt

| ID | Item | Severity | Business Impact | Est. Effort | Evidence |
|----|------|----------|-----------------|-------------|----------|
| DOC-001 | No ADRs for any architecture decision | High | Architectural intent lost; cannot onboard new developers | M | Zero ADR files in `ai-dos/adr/` or `docs/architecture/` |
| DOC-002 | No API documentation beyond FastAPI auto-generated Swagger | Medium | API consumers must read code to understand contracts | M | FastAPI `/docs` only |
| DOC-003 | No module READMEs beyond top-level docs | Low | Module-level understanding requires code reading | M | No README.md in any `src/` subdirectory |

---

## Effort Legend

| Code | Meaning | Typical Range |
|------|---------|---------------|
| S | Small | 1-3 days |
| M | Medium | 1-2 weeks |
| L | Large | 2-4 weeks |
| XL | Extra Large | 1-3 months |

---

## Debt Concentration Heatmap

```
Category        Critical  High  Medium  Low   TOTAL  HEAT
──────────────────────────────────────────────────────────
Architecture       6        5      4      0     15    ████████████████
Security           3        4      2      1     10    ██████████
Domain             3        4      3      0     10    ██████████
Code               0        3      6      2     11    ███████████
Infrastructure     1        2      2      0      5    █████
Testing            1        1      0      0      2    ██
DevOps             0        2      1      1      4    ████
Operations         0        1      2      1      4    ████
Documentation      0        1      1      1      3    ███
──────────────────────────────────────────────────────────
TOTAL             14       23     21      6     64
```

---

*End of Technical Debt Heatmap v1.0*
*All debt items identified from source code audit and architectural analysis. Estimation in effort categories, not person-hours.*
