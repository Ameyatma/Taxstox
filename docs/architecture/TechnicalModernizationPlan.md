# Technical Modernization Plan

> **Date:** 2026-07-05
> **Principle:** High-level technical direction only. No implementation code.

---

## 1. Module Disposition Map

### Modules to PRESERVE (production-proven)

| Module | Reason | Wave Touched |
|--------|--------|-------------|
| `parsers/form16_parser.py` | Production-tested on real Form 16s | M2 (confidence scoring) |
| `parsers/ais_parser.py` | Production-tested on real AIS PDFs | M2 (additional SFT codes) |
| `parsers/ais_code_mapper.py` | 25+ code mappings, well-structured | M1 (→ rule repository) |
| `engine/salary_computer.py` | ITD-matched salary computation | M1 (parameterize constants) |
| `engine/deductions_computer.py` | Correct deduction logic | M1 (extract limits) |
| `engine/classifier.py` | Correct CG classification | M1 (extract rates, resolve circular dep) |
| `engine/questions.py` | Working adaptive question engine | M7 (configurable library) |
| `models/` (all 5 files) | Sound domain models | M1 (add FinancialYear) |
| `auth/jwt.py` | Working JWT (fix secret) | M0 (remove hardcoded default) |
| `builders/itr_json_builder.py` | ITR-2 production-tested | M5 (extract base builder) |
| `builders/itr1.py` | ITR-1 production-tested | M5 (extract base builder) |
| `builders/validator.py` | 40+ validation rules | M5 (pluggable rule refactor) |

### Modules to REFACTOR

| Module | Target State | Wave |
|--------|-------------|------|
| `engine/regime_optimizer_v2.py` | Computation pipeline uses rule repository; constants extracted | M1 |
| `api/routes.py` (595 lines) | Split by concern: upload, process, export | M5 |
| `builders/validator.py` (968 lines) | Pluggable validation rule registry | M5 |
| `utils/session.py` | Redis-backed with serialization | M11 |

### Modules to EXTRACT (new packages from existing code)

| Source | New Package | Wave |
|--------|------------|------|
| `engine/regime_optimizer_v2.py` constants | `engine/rules/` | M1 |
| `builders/itr_json_builder.py` base logic | `builders/base.py` | M5 |
| `builders/validator.py` rules | `builders/validation_rules/` | M5 |

### Modules to RETIRE

| Module | Reason | Wave |
|--------|--------|------|
| `engine/regime_optimizer.py` (v1) | Superseded by v2. Duplicate. | M1 |
| `apps/api/data/taxstox.db` | Pre-Neon SQLite artifact. | M0 |

### Modules to CREATE

| Module | Purpose | Wave |
|--------|---------|------|
| `engine/rules/repository.py` | FY-indexed rule store | M1 |
| `engine/rules/schema.py` | Declarative rule format | M1 |
| `engine/rules/evaluator.py` | Generic rule evaluation engine | M1 |
| `engine/pipeline.py` | Explicit computation pipeline | M1 |
| `models/financial_year.py` | FinancialYear value object | M1 |
| `engine/audit/` | Audit trail event store | M6 |
| `engine/explain/` | Explanation generation engine | M6 |
| `engine/knowledge/` | Knowledge graph | M7 |
| `auth/rbac.py` | Role-based access control | M8 |
| `enterprise/tenant.py` | Tenant context management | M8 |
| `security/encryption.py` | Application-level PII encryption | M9 |
| `security/consent.py` | DPDP Act consent management | M9 |

---

## 2. Cross-Cutting Technical Improvements

| Concern | Current State | Target State | Wave |
|---------|---------------|-------------|------|
| **Logging** | f-strings | Structured JSON with correlation IDs | M0 |
| **Error Handling** | Inconsistent (some bare except) | Domain exception hierarchy per Engineering Standards §5 | M0 |
| **Type Safety** | Partial (Pydantic models only) | Full MyPy strict; FinancialYear newtype | M1 |
| **Configuration** | Env vars + hardcoded defaults | Schema-validated config; secrets external | M0 |
| **API Versioning** | None | `/api/v1/` preserved; `/api/v2/` for breaking changes | M5 |
| **Database** | Raw psycopg2 SQL | Alembic migrations; connection pooling config | M0 |
| **Sessions** | In-memory dict | Redis-backed with serialization | M11 |
| **Caching** | None | Rule/config cache layer | M1 |
| **Feature Flags** | None | Per-tenant boolean + percentage flags | M0 |

---

## 3. Database Evolution

| Wave | Tables Added | Tables Modified | Migration Risk |
|------|-------------|-----------------|----------------|
| M0 | `alembic_version` | None | None |
| M1 | `rule_definitions`, `rule_versions`, `finance_acts` | None | None |
| M6 | `computation_events`, `audit_trails`, `explanation_templates` | None | None |
| M7 | `knowledge_nodes`, `knowledge_edges`, `tax_provisions` | None | None |
| M8 | `tenants`, `roles`, `permissions`, `client_assignments` | `users` (+tenant_id), `filings` (+tenant_id) | **High** |
| M9 | `consent_records`, `encryption_keys` | `users` (encrypt pan column) | **High** |

---

## 4. Infrastructure Evolution

| Wave | Infrastructure Change |
|------|----------------------|
| M0 | CI/CD pipeline (GitHub Actions); structured logging |
| M1 | None (code-only changes) |
| M2 | None (code-only changes) |
| M5 | API versioning via gateway |
| M8 | Redis for session storage |
| M11 | Horizontal scaling (multiple API workers); load balancer; Redis cluster; database read replicas; auto-scaling configuration |

---

*End of Technical Modernization Plan v1.0*
