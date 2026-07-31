# TaxStox — AI-Powered Indian Tax Intelligence Platform

> **Release:** v0.10.0-alpha (Internal Alpha)
> **2 documents. Minimal questions. Your ITR, done.**

---

## For AI Agents

Start at **[CLAUDE.md](CLAUDE.md)** for bootstrap instructions. Every session begins there.

## For Engineers

Start at **[HANDOFF.md](HANDOFF.md)** for full project status, authority hierarchy, and the mandatory session bootstrap prompt.

---

## Quick Start

```bash
# Backend
cd apps/api
pip install -e ".[dev]"
TAXSTOX_JWT_SECRET="dev-secret" uvicorn src.main:app --reload

# Frontend
cd apps/web
npm install
npm run dev
```

| Service | URL |
|----------|-----|
| Frontend | `http://localhost:3000` |
| Backend API | `http://localhost:8000` |
| API Docs | `http://localhost:8000/docs` |

---

## Project Status

| Metric | Value |
|--------|-------|
| Release | v0.10.0-alpha |
| Stage | Internal Alpha |
| Tests | 407 passing |
| Golden vectors | 9 |
| Architecture | EAC Certified v1.0 |

---

## Architecture

```
apps/api/src/
├── domain/         13 bounded contexts (pure Python, zero framework imports)
├── engine/         44 modules (tax computation, AI, enterprise, reporting)
├── infrastructure/ Adapters (encryption, SSO, billing, notifications, payments)
├── middleware/     Security headers, correlation, metrics, tenant context
├── api/            26 REST endpoints (auth, filing pipeline, dashboard, calculators)
├── auth/           JWT + Google OAuth
├── builders/       ITR-1 + ITR-2 JSON builders + 28-rule validator
├── parsers/        Form 16 + AIS PDF parsers + AIS code mapper
├── models/         Pydantic v2 domain models
└── db/             PostgreSQL (Neon) via psycopg2
```

---

## Key Documents

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | AI agent bootstrap |
| [HANDOFF.md](HANDOFF.md) | Engineering handoff |
| [docs/governance/00-Constitution.md](docs/governance/00-Constitution.md) | Supreme governance |
| [docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md](docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md) | FROZEN target (148 capabilities) |
| [docs/architecture/ProductReadinessReview.md](docs/architecture/ProductReadinessReview.md) | Production readiness assessment |
| [docs/architecture/ProductionReadinessRemediationRoadmap.md](docs/architecture/ProductionReadinessRemediationRoadmap.md) | Execution plan (PR1-PR6) |
| [CHANGELOG.md](CHANGELOG.md) | Release history |

---

*Version v0.10.0-alpha — Internal Alpha*
