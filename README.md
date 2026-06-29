# TaxStox — ITR Auto-Filing & Stock Analytics Platform

> **2 documents. 5 yes/no questions. 2 minutes. Your ITR, done.**
>
> Born from 4 hours of manual ITR-2 filing with a 30-year CA and 25-year software engineer
> sitting side-by-side. Every pain point catalogued. Every fix automated.

---

## Project Structure

```
taxstox/
├── apps/
│   ├── api/              # Python FastAPI backend
│   │   ├── src/
│   │   │   ├── api/      # FastAPI routes
│   │   │   ├── builders/ # ITR JSON builder + validator
│   │   │   ├── engine/   # Classifier, regime optimizer, questions
│   │   │   ├── models/   # Pydantic v2 data models
│   │   │   ├── parsers/  # Form 16 + AIS PDF parsers
│   │   │   └── utils/    # Password resolver, session manager
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── web/              # Next.js frontend
│       ├── src/
│       │   ├── app/      # Pages (upload, questions, summary)
│       │   ├── components/ui/  # shadcn/ui components
│       │   └── lib/      # API client, store, utilities
│       └── package.json
├── docs/                 # Architecture & design documents
│   ├── ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   └── ITR_TYPES_QUESTIONS.md
├── design/               # UI design mockups (8 screens)
│   ├── design-system/    # Design tokens & style guide
│   ├── landing-page/
│   ├── secure-upload-portal/
│   ├── smart-questionnaire/
│   ├── tax-summary-review/
│   ├── post-export-instructions/
│   ├── auth-signup/
│   ├── user-dashboard/
│   └── error-edge-cases/
└── README.md
```

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

## Core Flow

```
Upload Form 16 + AIS + PAN + DOB
          │
          ▼
  PDF Parser Engine (pikepdf + pdfplumber)
          │
          ▼
  Classification Engine (AIS codes → ITR schedules)
          │
          ▼
  Regime Optimizer (Old vs New — always picks the winner)
          │
          ▼
  Smart Questions (0-5 yes/no, all others auto-detected)
          │
          ▼
  JSON Builder (ITR-1/2/3/4, all schedules, cross-validated)
          │
          ▼
  Download-ready JSON + 1-page Tax Summary
```

---

## What We Learned (The Hard Way)

| # | Lesson | Code Impact |
|---|---|---|
| 1 | Form 16 password is usually PAN (lowercase) | Auto-try. Ask only if all candidates fail. |
| 2 | AIS password = PAN(lower) + DOB(DDMMYYYY) — ALWAYS | Auto-compute. Never ask. |
| 3 | 80CCD(2) "eligible amount" locked at ₹0 in web portal | Auto-set in JSON. Cross-validate. |
| 4 | CG date ranges must sum EXACTLY to BFLA values | Auto-compute from sale dates. Never allow manual entry. |
| 5 | ISIN `INNOTREQUIRD` ≠ `INNOTAVAILAB` (schema enum) | Use correct enum per ITD schema spec. |
| 6 | `SecondaryAdd` = `""` fails schema validation | Always set to valid enum `"Y"` or `"N"`. |
| 7 | Multiple banks with `UseForRefund: true` = warning | Auto-select first validated account. |
| 8 | JSON hash prevents post-generation edits | Must output valid JSON from official utility templates. |
| 9 | 112A consolidated entries: Units=0 fails some validators | Auto-compute from total sale / weighted avg price. |
| 10 | STCG and LTCG must be date-split into 5 periods | Auto-group from AIS sale dates. |

---

## Technology

| Layer | Stack |
|---|---|
| Backend | Python 3.12+ + FastAPI + Pydantic v2 + pikepdf + pdfplumber |
| Frontend | Next.js 16 + Tailwind CSS 4 + shadcn/ui + Zustand |
| Mobile | React Native + Expo (Phase 2) |
| Database | PostgreSQL + Redis |
| Deployment | Docker + AWS/GCP |

---

## Project Status

- [x] Architecture design
- [x] Data model definitions
- [x] ITR-type question trees
- [x] Form 16 PDF parser (pikepdf + pdfplumber)
- [x] AIS PDF parser (pdfplumber table extraction)
- [x] Classification engine
- [x] Regime optimizer
- [x] JSON builder (ITR-2 with 15+ schedules)
- [x] Validation engine
- [x] Web frontend (upload → questions → summary → export)
- [x] Post-export ITR portal instructions
- [ ] Mobile app
