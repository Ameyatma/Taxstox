# Architecture Health Score — IT_Returns Platform

> **Date:** 2026-07-05
> **Assessment Basis:** Enterprise Capability Model (Target) vs Architecture Recovery Report (Current) vs Source Code

---

## Overall Architecture Health Score: **31/100**

**Grade:** D — Significant architectural debt requiring systematic remediation before expansion.

---

## Category Scores

### Domain Design: 15/100

**Justification:** The platform has no explicit domain model. Modules are organized by technical function (`parsers/`, `engine/`, `builders/`, `models/`, `api/`), not by business domain. There are no bounded contexts, no ubiquitous language enforcement, and no domain-driven design patterns. The `models/` directory contains Pydantic data transfer objects, not domain entities with behavior. Business logic is scattered across `engine/` modules without clear ownership boundaries.

**Evidence:** `models/tax.py:140-157` — `UnifiedTaxData` is a data bag, not a domain aggregate. `engine/regime_optimizer_v2.py:137-279` — computation logic mixed with orchestration. No bounded context separation.

**Key Concerns:**
- Taxpayer identity mixed with auth credentials in `users` table
- No separation between tax computation domain and document processing domain
- No aggregate roots enforcing consistency boundaries
- Domain rules embedded in procedural code, not domain objects

---

### DDD Adoption: 10/100

**Justification:** Zero DDD patterns applied. No entities with identity and behavior. No value objects (Decimal is used but without domain semantics). No aggregates. No repositories (raw SQL in `db/database.py` functions). No domain services (services are procedural engine functions). No domain events. No bounded context mapping.

**Evidence:** `db/database.py:175-195` — `create_user()` is a database function, not a repository. `engine/classifier.py:26-243` — `ClassificationEngine` is a procedural service, not a domain service within a bounded context.

---

### Clean Architecture: 15/100

**Justification:** Dependency rule is violated — domain logic in `engine/` depends directly on infrastructure (`db/database.py` for psycopg2, `parsers/` for PDF libraries). No interface/port layer. Use cases (application layer) are mixed with controllers in `api/routes.py`. No dependency injection.

**Evidence:** `api/routes.py:172-173` — `PDFDataProvider(session.form16, session.ais, session.pan, session.dob)` — direct instantiation in controller. `db/database.py:19-26` — `get_db()` returns raw psycopg2 connection, called directly.

---

### Layering: 25/100

**Justification:** Three identifiable layers exist (API → Engine → Models) but:
- API layer (`api/`) contains business logic (595 lines of orchestration in `routes.py`)
- Engine layer (`engine/`) contains infrastructure concerns (direct DB access patterns)
- Model layer (`models/`) contains only data structures, no behavior
- No clear dependency direction enforcement
- Cross-layer coupling via direct imports

**Evidence:** `api/routes.py:224-236` — API route directly orchestrates parser, classifier, optimizer, questions engine. `engine/regime_optimizer_v2.py:334-335` — lazy import from `engine/classifier.py` to avoid circular dependency.

---

### Maintainability: 35/100

**Justification:**
- **Strengths:** Well-named files and functions. Consistent use of Pydantic models. Reasonable module sizes (most under 500 lines). Clear separation between parsers and engines.
- **Weaknesses:** No tests = no safety net for refactoring. Hardcoded values prevent extension. Duplicate implementations (v1 and v2 optimizers) increase maintenance burden. No ADRs documenting architectural intent.

**Evidence:** `regime_optimizer.py` (401 lines) and `regime_optimizer_v2.py` (360 lines) — both must be maintained. `builders/validator.py` (968 lines) — god module. `api/routes.py` (595 lines) — god controller.

---

### Modularity: 45/100

**Justification:**
- **Strengths:** Good file-level modularity. Clear naming conventions. Modules have single-file responsibilities. Well-organized directory structure (`parsers/`, `engine/`, `builders/`, `models/`, `api/`, `auth/`, `db/`).
- **Weaknesses:** No module-level API contracts (no `__all__` or interface definitions). Implicit dependencies between modules. Circular dependency risk (lazy import workaround). No module isolation for testing.

**Evidence:** Directory structure in `apps/api/src/` — 7 top-level packages with clear separation. But `engine/regime_optimizer_v2.py:334` — `from src.engine.classifier import ClassificationEngine` inside method to break cycle.

---

### Testability: 10/100

**Justification:** Zero unit tests. Zero integration tests. Single skeleton E2E test file. No test framework structure. No test fixtures. No mocking infrastructure. Hard dependencies on external services (pikepdf, pdfplumber, psycopg2, DeepSeek API) make isolated testing impossible without significant refactoring.

**Evidence:** `apps/api/tests/test_e2e_real_data.py` — only test file in entire repository. No `conftest.py`. No `pytest.ini`. No test fixtures directory.

---

### Security: 15/100

**Justification:**
- Dev JWT secret hardcoded in source
- PAN stored as plaintext in database
- No RBAC/authorization model
- No rate limiting
- No brute-force protection
- No application-level encryption for PII
- No consent management (DPDP Act)
- No security scanning in pipeline
- CORS reasonably configured
- JWT with 24h expiry (acceptable)
- bcrypt for password hashing (good)

**Evidence:** `auth/jwt.py:12` — `SECRET_KEY = os.getenv("TAXSTOX_JWT_SECRET", "taxstox-dev-secret-change-in-production")`. `db/database.py:175-195` — PAN stored as plaintext in INSERT statement. No RBAC middleware. No rate limiting decorators.

---

### Compliance: 5/100

**Justification:** No consent management (DPDP Act 2023 violation). No data retention policy implemented. No right-to-deletion API. No data processing records. No DPIA. No breach notification procedure implemented. Tax rules not versioned by Finance Act.

**Evidence:** Zero compliance-related code in all 42 modules. Design docs mention compliance as principle only. `ARCHITECTURE.md:1093-1110` — privacy principles stated but not implemented.

---

### Performance: 40/100

**Justification:**
- **Strengths:** In-memory processing (BytesIO, not disk). Single process = no network overhead. Computation is deterministic math (fast). No unnecessary external calls in computation path.
- **Weaknesses:** PDF parsing is synchronous (blocks event loop). No caching layer for rules or config. No database connection pooling configuration visible. No query optimization evidence. No performance testing.

**Evidence:** `api/routes.py:73-75` — PDF parsing in request thread with `tempfile.NamedTemporaryFile`. `db/database.py:19-26` — new connection per `get_db()` call, no pool sizing.

---

### Scalability: 15/100

**Justification:** In-memory sessions prevent horizontal scaling. Single process architecture. No async task queue for document processing. No database read replicas. No caching layer. No load balancing configuration.

**Evidence:** `utils/session.py` — `SessionManager` stores sessions in Python dict. Server restart = all sessions lost. No Redis/memcached integration.

---

### Reliability: 25/100

**Justification:**
- **Strengths:** Simple architecture = fewer failure modes. Single database = no distributed consistency issues.
- **Weaknesses:** No retry logic on external calls. No circuit breakers. No graceful degradation (if AIS fails, entire upload fails). In-memory state = crashes lose user progress. No health checks beyond basic endpoint.

**Evidence:** `api/routes.py:119-124` — AIS parsing failure is caught but session continues. `api/routes.py:93-98` — Form 16 password failures return `password_required` — good UX but no retry.

---

### Availability: 25/100

**Justification:** Deployed on managed platforms (Render, Vercel, Neon) providing basic availability. Keep-alive cron prevents Render free-tier sleep. But: single region, no failover, no redundancy, no load balancing, no auto-scaling.

**Evidence:** `render.yaml` — Render configuration present. `HANDOFF.md:68-69` — cron-job.org keep-alive configured. Single database instance with no replica.

---

### Observability: 10/100

**Justification:** No structured logging (f-strings only). No metrics collection. No distributed tracing. No alerting. Basic health check endpoint. No log aggregation. No dashboard.

**Evidence:** `api/routes.py:92` — `logger.info(f"PARSED with pwd={pwd}: salary=...")` — unstructured, PII-exposing (password logged). `api/routes.py:568-571` — health check endpoint exists. No Prometheus/Grafana. No Sentry/error tracking.

---

### AI Readiness: 10/100

**Justification:** DeepSeek API used for tax updates summarization only. No AI in core computation pipeline. No ML model management. No feature store. No model monitoring. No XAI infrastructure. No training data pipeline. AI is peripheral, not integral.

**Evidence:** `summarizer/__init__.py` — DeepSeek API integration. `providers/` — provider framework for government sources. No AI in `engine/` modules.

---

### Cloud Readiness: 25/100

**Justification:** Deployed on cloud platforms. Environment variables for config. But: no containerization (no Dockerfile found in `apps/api/`). No infrastructure-as-code. No CI/CD pipeline evidence. No cloud resource orchestration. In-memory state is anti-cloud pattern.

**Evidence:** `render.yaml` — basic Render config. `.github/workflows/` — workflows directory exists but contents not reviewed. No Dockerfile. No Terraform/CloudFormation.

---

## Score Trend Analysis

| Category | Score | Trend Rationale |
|----------|-------|-----------------|
| Domain Design | 15 | Will decline without DDD adoption as more features are added |
| DDD | 10 | Cannot improve without architectural intervention |
| Clean Architecture | 15 | Currently stable but fragile |
| Layering | 25 | Degrading — `api/routes.py` growing with each feature |
| Maintainability | 35 | Declining — duplicate optimizer, growing validator |
| Modularity | 45 | Best current strength; at risk from tight coupling |
| Testability | 10 | Will not improve without dedicated investment |
| Security | 15 | Degrading as platform grows without security review |
| Compliance | 5 | Critical risk — DPDP Act timeline unknown |
| Performance | 40 | Adequate for current scale; will degrade without caching |
| Scalability | 15 | Will fail at filing season peak without changes |
| Reliability | 25 | Adequate for current users; not enterprise-grade |
| Availability | 25 | Dependent on platform SLAs; no internal redundancy |
| Observability | 10 | Zero visibility in production |
| AI Readiness | 10 | Infrastructure absent for AI integration |
| Cloud Readiness | 25 | On cloud but not cloud-native |

---

## Heat Map Visualization

```
Category               Score   0         25        50        75       100
Domain Design           15     ████░░░░░░░░░░░░░░░░░░
DDD                     10     ███░░░░░░░░░░░░░░░░░░░
Clean Architecture      15     ████░░░░░░░░░░░░░░░░░░
Layering                25     ██████░░░░░░░░░░░░░░░░
Maintainability         35     █████████░░░░░░░░░░░░░
Modularity              45     ███████████░░░░░░░░░░░
Testability             10     ███░░░░░░░░░░░░░░░░░░░
Security                15     ████░░░░░░░░░░░░░░░░░░
Compliance               5     █░░░░░░░░░░░░░░░░░░░░░
Performance             40     ██████████░░░░░░░░░░░░
Scalability             15     ████░░░░░░░░░░░░░░░░░░
Reliability             25     ██████░░░░░░░░░░░░░░░░
Availability            25     ██████░░░░░░░░░░░░░░░░
Observability           10     ███░░░░░░░░░░░░░░░░░░░
AI Readiness            10     ███░░░░░░░░░░░░░░░░░░░
Cloud Readiness         25     ██████░░░░░░░░░░░░░░░░
                        ──     ─────────────────────────
                  OVERALL 31   ████████░░░░░░░░░░░░░░
```

---

*End of Architecture Health Score v1.0*
*Score reflects current state as of 2026-07-05. All scores evidence-backed from Architecture Recovery Report and source code audit.*
