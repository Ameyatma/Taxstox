# Architecture Memory — ARCHIVED v0.1

> **⚠️ SUPERSEDED — This document is archived and no longer active.**
> **Superseded By:** [ARCHITECTURE_RECOVERY_REPORT.md](../../recovery/ARCHITECTURE_RECOVERY_REPORT.md) and [ENTERPRISE_CAPABILITY_MODEL.md](../../architecture/ENTERPRISE_CAPABILITY_MODEL.md)
> **Supersession Date:** 2026-07-05
> **Reason:** This was a pre-recovery planning document. The Architecture Recovery Report (50,983 bytes) provides evidence-backed current state from a 42-module code audit. The Enterprise Capability Model (178,013 bytes) provides the FROZEN target architecture with 148 capabilities across 15 bounded contexts.
> **Retention:** Preserved for historical reference only. All knowledge has been transferred to the superseding documents.
>
> ---
>
> **Original Purpose:** Single source of truth for the current system architecture state.
> **Original Updated By:** Architect Agent — every session.
> **Original Last Updated:** 2026-07-05
> **Original Session ID:** INIT
> **Cross-Refs:** [Decisions.md](Decisions.md), [TechnicalDebt.md](TechnicalDebt.md)

---

## 1. Architecture Style

| Attribute | Decision | Rationale |
|-----------|----------|-----------|
| Primary Style | Modular Monolith → Event-Driven Microservices | Start monolithic for velocity; extract services at proven boundaries |
| Communication | Synchronous REST (internal) → Async Events (cross-boundary) | REST for queries; events for commands crossing module boundaries |
| Data Storage | One logical DB, schema-per-module → eventual DB-per-service | Schema isolation from day one; physical separation when needed |
| API Style | REST (primary), gRPC (internal high-throughput) | REST for external; gRPC for service-to-service when latency matters |
| Event Bus | PostgreSQL LISTEN/NOTIFY → Kafka/RabbitMQ at scale | Start simple; upgrade when throughput demands it |

## 2. Module Map

### 2.1 Current Modules

| Module | Status | Owner | Description |
|--------|--------|-------|-------------|
| *No modules yet — project initialization phase* | — | — | — |

### 2.2 Planned Modules (Phase 1)

| Module | Priority | Dependencies | Description |
|--------|----------|--------------|-------------|
| `core-domain` | P0 | None | Core tax domain entities, value objects, aggregates |
| `tax-year-registry` | P0 | `core-domain` | Financial year definitions, FY-aware data structures |
| `rule-engine` | P0 | `core-domain` | Generic rule evaluation engine (no tax rules yet) |
| `tax-rules-fy2025-26` | P0 | `rule-engine`, `tax-year-registry` | Tax slabs, deductions, surcharges for FY2025-26 |
| `itr-schema` | P0 | `core-domain` | ITR form schema definitions (ITR-1 through ITR-7) |
| `computation-engine` | P0 | `rule-engine`, `itr-schema` | Tax liability computation orchestrator |
| `audit-trail` | P0 | `computation-engine` | Immutable computation audit log |
| `explain-engine` | P1 | `computation-engine` | Plain-language explanation generator |
| `validation-engine` | P1 | `itr-schema` | Input validation, cross-field validation, AIS reconciliation |
| `regime-optimizer` | P1 | `computation-engine` | Old vs New regime comparison and optimization |
| `user-api` | P1 | `computation-engine`, `validation-engine` | REST API for tax computation |
| `document-parser` | P1 | `core-domain` | OCR and structured extraction from Form 16, Form 26AS |

### 2.3 Module Dependency Graph

```
[To be rendered as Mermaid diagram once modules are created]
```

## 3. Technology Stack (Planned)

| Layer | Technology | Version | Status | ADR |
|-------|-----------|---------|--------|-----|
| Backend Language | Python 3.12+ | 3.12 | Planned | Pending |
| Web Framework | FastAPI | latest stable | Planned | Pending |
| Database | PostgreSQL 16 | 16 | Planned | Pending |
| ORM | SQLAlchemy 2.0 | 2.0 | Planned | Pending |
| Migration Tool | Alembic | latest | Planned | Pending |
| Cache | Redis | 7.x | Planned (Phase 2) | Pending |
| Message Queue | PostgreSQL LISTEN/NOTIFY | — | Planned (Phase 2) | Pending |
| Task Queue | Celery | latest | Planned (Phase 2) | Pending |
| Search | PostgreSQL Full-Text Search | — | Planned (Phase 2) | Pending |
| File Storage | Local FS → S3-compatible | — | Planned | Pending |
| Container Runtime | Docker + Docker Compose | latest | Planned | Pending |
| CI/CD | GitHub Actions | — | Planned | Pending |

## 4. Data Architecture (Planned)

### 4.1 Core Entities

```
FinancialYear (FY2020-21, FY2021-22, ...)
  └── TaxRegime (OLD_REGIME, NEW_REGIME)
       └── TaxSlab (income_from, income_to, rate, surcharge_threshold, ...)
            └── Surcharge (income_threshold, rate)
            └── Cess (rate, applies_to)

Taxpayer
  ├── PersonalInfo (name, dob, pan, aadhaar, ...)
  ├── FilingStatus (individual, HUF, senior_citizen, super_senior_citizen)
  ├── ResidencyStatus (resident, RNOR, non_resident)
  └── IncomeProfile
       ├── SalaryIncome (Form 16 data)
       ├── HousePropertyIncome
       ├── BusinessIncome
       ├── CapitalGains (short_term, long_term, listed, unlisted, ...)
       └── OtherSources (interest, dividend, ...)

ITR (abstract)
  ├── ITR1 (Sahaj)
  ├── ITR2
  ├── ITR3
  ├── ITR4 (Sugam)
  ├── ITR5
  ├── ITR6
  └── ITR7

TaxComputation
  ├── GrossTotalIncome
  ├── Deductions (80C, 80D, 80CCD, 80TTA, 80TTB, ...)
  ├── TotalIncome
  ├── TaxOnTotalIncome
  ├── Rebate (87A)
  ├── Surcharge
  ├── Cess
  ├── TotalTaxLiability
  ├── TDS
  ├── AdvanceTax
  ├── SelfAssessmentTax
  └── NetTaxPayable

AuditTrail
  └── ComputationStep[]
       ├── step_id
       ├── rule_applied (provision reference)
       ├── input_values
       ├── output_values
       ├── explanation
       └── timestamp
```

### 4.2 Database Principles

1. Schema-per-module from day one
2. No cross-module foreign keys (use logical references)
3. Every table has: `id`, `created_at`, `updated_at`, `tenant_id`
4. Append-only for financial data (event sourcing for computations)
5. Soft deletes only — no hard deletes
6. All monetary values stored as `DECIMAL(18,2)` — never floats
7. All dates stored as `DATE` — never strings

## 5. API Design Principles (Planned)

1. RESTful URLs: `/api/v1/itr/{itr_type}/compute`
2. Versioned: `/api/v1/`, `/api/v2/`
3. Consistent error format: `{ "error": { "code": "...", "message": "...", "details": [...] } }`
4. Pagination: cursor-based for lists
5. Idempotency keys: required for all POST/PUT
6. Rate limiting: per-tenant, per-endpoint
7. All responses include `request_id` for tracing

## 6. Deployment Architecture (Planned)

```
[Phase 1 — Development]
Docker Compose
├── api (FastAPI + Uvicorn)
├── db (PostgreSQL 16)
├── cache (Redis) — Phase 2
└── worker (Celery) — Phase 2

[Phase 3 — Production]
Kubernetes
├── api (3+ replicas, HPA)
├── worker (2+ replicas)
├── db (managed PostgreSQL, multi-AZ)
├── cache (managed Redis, cluster mode)
├── ingress (NGINX, TLS termination)
└── monitoring (Prometheus + Grafana)
```

---

## Session Log

| Date | Session ID | Changes Made | Agent |
|------|-----------|--------------|-------|
| 2026-07-05 | INIT | Memory system initialized. Architecture planned. | Architect |

---

*This file is the single source of truth for architecture. When the architecture changes, this file changes first.*
