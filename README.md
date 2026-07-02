# TaxStox — ITR Auto-Filing Platform

> **2 documents. 5 yes/no questions. 2 minutes. Your ITR, done.**
>
> Born from 4 hours of manual ITR-2 filing with a 30-year CA and 25-year software engineer
> sitting side-by-side. Every pain point catalogued. Every fix automated.

---

## 🎯 Single Source of Truth

> **👉 [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) — Give this file to any AI agent to build the system.**

This README is a quick reference. The master plan contains the complete build specification:
architecture, folder structure, API contracts, core modules, data privacy rules,
edge cases, build order, and cost-aware engineering principles.

---

## Quick Start

```bash
# Backend
cd apps/api
pip install -e ".[dev]"
uvicorn src.main:app --reload

# Frontend
cd apps/web
npm install
npm run dev
```

| Service | URL |
|---|---|
| Frontend | `http://localhost:3000` |
| Backend API | `http://localhost:8000` |
| API Docs | `http://localhost:8000/docs` |

---

## Architecture (Cost-Aware)

```
Frontend (Next.js)  ←→  Backend (FastAPI — single process)
   3 pages               6 modules (Python files, not services)
                          ├── parsers/   (Form 16 + AIS PDF)
                          ├── classifier (AIS → ITR schedules)
                          ├── optimizer  (Old vs New — deterministic math)
                          ├── questions  (0-5 adaptive yes/no)
                          ├── builder    (ITR JSON assembly)
                          └── validator  (25+ cross-checks)

Data: SQLite → PostgreSQL when needed
Session: In-memory → Redis when needed
Files: BytesIO (in-memory, never touches disk)
```

**Principles:** Modular monolith. Zero AI calls for deterministic work.
No Kubernetes, no Kafka, no Redis, no separate services for MVP.
Every module CAN become a service later — starts as a Python file.

---

## Core Flow

```
Upload Form 16 + AIS + PAN + DOB
          │
          ▼
  PDF Parser (pikepdf + pdfplumber) — auto-decrypts passwords
          │
          ▼
  Classifier (AIS codes → ITR schedules + CG date ranges)
          │
          ▼
  Regime Optimizer (Old vs New — deterministic math, always picks winner)
          │
          ▼
  Smart Questions (0-5 yes/no, everything else auto-detected)
          │
          ▼
  JSON Builder (ITR-1/2/3/4, all schedules, cross-validated)
          │
          ▼
  Download-ready JSON + 1-page Tax Summary + Portal Instructions
```

---

## The 10 Hard-Learned Rules

| # | Lesson | Implementation |
|---|---|---|
| 1 | Form 16 password is usually PAN (lowercase) | Auto-try. Ask only if all fail. |
| 2 | AIS password = PAN(lower) + DOB(DDMMYYYY) | Auto-compute. Never ask. |
| 3 | 80CCD(2) locked at ₹0 in portal | Auto-set correct value. |
| 4 | CG date ranges must sum to BFLA | Auto-compute from dates. |
| 5 | ISIN `INNOTREQUIRD` ≠ `INNOTAVAILAB` | Use correct enum. |
| 6 | `SecondaryAdd`="" fails schema | Always "Y" or "N". |
| 7 | Multiple banks with refund flag | Auto-select first. |
| 8 | JSON hash prevents post-edit | Valid utility template output. |
| 9 | 112A Units=0 fails | Auto-compute from sale/price. |
| 10 | STCG/LTCG date-split into 5 periods | Auto-group from AIS dates. |

---

## Technology

| Layer | Stack |
|---|---|
| Backend | Python 3.12+ + FastAPI + Pydantic v2 + pikepdf + pdfplumber |
| Frontend | Next.js 16 + Tailwind CSS 4 + shadcn/ui + Zustand |
| Database | SQLite (→ PostgreSQL when needed) |
| Session | In-memory (→ Redis when needed) |
| Deployment | Render (backend) + Vercel (frontend) |

---

## Docs

| File | Purpose |
|---|---|
| **[docs/MASTER_PLAN.md](docs/MASTER_PLAN.md)** | **Complete build spec (give to AI agent)** |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Detailed architecture reference |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Pydantic v2 data model definitions |
| [docs/ITR_TYPES_QUESTIONS.md](docs/ITR_TYPES_QUESTIONS.md) | Per-ITR question decision trees |
| [design/DESIGN.md](design/DESIGN.md) | Design tokens (colors, typography, components) |

---

## Project Status

- [x] Architecture & build plan
- [x] Design system (tokens + HTML prototypes)
- [x] Data model definitions (Pydantic v2)
- [x] ITR-type question trees
- [x] Web frontend (3 pages: upload, questions, summary)
- [ ] Backend pipeline (parsers → classifier → optimizer → builder → validator)
- [ ] API integration (wire frontend to backend)
- [ ] End-to-end testing with real PDFs
- [ ] Deployment
