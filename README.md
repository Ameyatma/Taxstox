# TaxStox — ITR Auto-Filing & Stock Analytics Platform

> **2 documents. 5 yes/no questions. 2 minutes. Your ITR, done.**
>
> Born from 4 hours of manual ITR-2 filing with a 30-year CA and 25-year software engineer
> sitting side-by-side. Every pain point catalogued. Every fix automated.

---

## The Problem

Filing an ITR-2 in India requires a user to navigate 15+ schedules, understand ISIN codes,
CG date ranges, AIS code mappings, form 112A vs CG B3, 80CCD(2) eligible-amount bugs,
and a JSON schema with undocumented enum values.

For FY 2025-26, a single salaried individual with some mutual fund redemptions and ETF
trades needed **4 hours of expert guidance** to file correctly.

## The Solution

Upload 2 PDFs. Answer at most 5 yes/no questions. Download a validated, regime-optimized,
upload-ready ITR JSON.

**Every piece of data that exists in Form 16 or AIS is machine-extracted.**
**Every computation a CA does manually is automated.**

---

## Quick Start

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
uvicorn src.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## Project Documents

| Document | Description |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Full system architecture — parsers, classifiers, regime engine, JSON builder, validators, deployment |
| [DATA_MODEL.md](DATA_MODEL.md) | Complete Pydantic v2 type definitions for Form 16, AIS, unified tax data, CG classifier, and API contracts |
| [ITR_TYPES_QUESTIONS.md](ITR_TYPES_QUESTIONS.md) | Per-ITR-type decision trees — the exact yes/no questions, suppression logic, and auto-detection rules |

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

## Supported ITR Types

| ITR | Status | Auto-Detection |
|---|---|---|
| ITR-1 (Sahaj) | Phase 1 | Salary + Interest + 1 House Property |
| ITR-2 | Phase 1 | + Capital Gains, Foreign Assets |
| ITR-3 | Phase 2 | + Business/Professional Income |
| ITR-4 (Sugam) | Phase 2 | + Presumptive Income |

---

## Technology

| Layer | Stack |
|---|---|
| Backend | Python 3.12 + FastAPI + Pydantic v2 + pikepdf + pdfplumber |
| Frontend | Next.js 14 + Tailwind CSS + shadcn/ui + Zustand |
| Mobile | React Native + Expo (Phase 2) |
| Database | PostgreSQL + Redis |
| Deployment | Docker + AWS/GCP |

---

## Project Status

- [x] Architecture design
- [x] Data model definitions
- [x] ITR-type question trees
- [ ] Form 16 PDF parser implementation
- [ ] AIS PDF parser implementation
- [ ] Classification engine
- [ ] Regime optimizer
- [ ] JSON builder (ITR-2 first)
- [ ] Validation engine
- [ ] Web frontend
- [ ] Mobile app
