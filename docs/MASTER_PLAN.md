# TaxStox — Master Build Plan

> **Single source of truth.** Give this file to any AI agent (DeepSeek, Claude, GPT) to build the system.
> **Principles:** Lowest complexity, lowest cost, zero unnecessary dependencies. Modular monolith.
> **Date:** 2026-06-29 | **Status:** Ready to build

---

## 0. Cost-Aware Engineering Rules

```
EVERY decision must optimize for:
  Lowest engineering complexity → Lowest infrastructure cost → Lowest AI inference cost

WITHOUT compromising: security, correctness, scalability, reliability.

RULES:
  • Prefer Modular Monolith over Microservices
  • No Kubernetes, Kafka, Redis, Vault unless MEASURABLY necessary
  • No separate services — keep as modules until scale demands extraction
  • Zero AI calls where deterministic code works
  • SQLite > PostgreSQL for MVP (swap when needed)
  • In-memory > Redis for MVP
  • BytesIO > S3 for file handling
  • Env vars > Vault/KMS for encryption keys
  • 3 frontend pages > 15 planned pages
  • 1 doc > 26 scattered docs
```

---

## 1. What TaxStox Does

**User flow:** Upload 2 PDFs (Form 16 + AIS) + PAN + DOB → Answer 0-5 yes/no questions → Download ITR JSON + 1-page tax summary → Upload to ITD portal.

**Core promise:** If data exists in Form 16 or AIS, the user never types it. If a deduction requires proof the user doesn't have, the system never suggests it.

**Time target:** < 2 minutes from upload to JSON download.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND                               │
│  Next.js 16 + Tailwind CSS + shadcn/ui                    │
│  Pages: Upload → Questions (0-5) → Summary → Export       │
│  State: Zustand (lightweight)                             │
└────────────────────────┬─────────────────────────────────┘
                         │ REST API
┌────────────────────────▼─────────────────────────────────┐
│              BACKEND (FastAPI — Single Process)            │
│                                                           │
│  modules/parsers/     → PDF → structured data             │
│  modules/classifier/  → AIS codes → ITR schedules         │
│  modules/optimizer/   → Old vs New regime (deterministic) │
│  modules/questions/   → Generate 0-5 adaptive questions   │
│  modules/builder/     → ITR JSON assembly                 │
│  modules/validator/   → 25+ cross-checks                  │
│                                                           │
│  Data: SQLite (single file, zero ops)                     │
│  Session: In-memory dict (24h TTL per session)            │
│  PDF processing: BytesIO (in-memory, never touches disk)  │
│  Encryption: Fernet key from env variable                 │
└──────────────────────────────────────────────────────────┘
```

**One process, one server.** Every module is a Python file. Every module CAN become a separate service later — but starts as a module.

---

## 3. Folder Structure

```
apps/
├── api/                          # FastAPI backend
│   ├── src/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── config.py             # Env config
│   │   ├── modules/
│   │   │   ├── parsers/
│   │   │   │   ├── form16.py     # Form 16 PDF parser
│   │   │   │   ├── ais.py        # AIS PDF parser
│   │   │   │   └── pdf_utils.py  # PDF password resolver, shared utilities
│   │   │   ├── classifier.py     # AIS code → ITR schedule mapper
│   │   │   ├── optimizer.py      # Old vs New regime (deterministic math)
│   │   │   ├── questions.py      # Adaptive questionnaire generator
│   │   │   ├── builder/
│   │   │   │   ├── itr1.py       # ITR-1 JSON builder
│   │   │   │   └── itr2.py       # ITR-2 JSON builder
│   │   │   └── validator.py      # 25+ cross-validation checks
│   │   ├── models/
│   │   │   ├── form16.py         # Form16Data pydantic model
│   │   │   ├── ais.py            # AISData pydantic model
│   │   │   └── tax.py            # UnifiedTaxData, regime result models
│   │   ├── api/
│   │   │   ├── upload.py         # POST /api/upload/form16, /api/upload/ais
│   │   │   ├── questions.py      # GET /api/questions/{session_id}
│   │   │   ├── compute.py        # GET /api/compute/{session_id}
│   │   │   └── export.py         # GET /api/export/{session_id}
│   │   ├── db.py                 # SQLite connection (swap to PostgreSQL later)
│   │   ├── session.py            # In-memory session store (swap to Redis later)
│   │   └── crypto.py             # Fernet encryption (swap to KMS later)
│   ├── tests/
│   │   └── fixtures/             # Sample PDFs + expected JSONs
│   └── pyproject.toml
│
└── web/                          # Next.js frontend (already built)
    └── src/
        ├── app/
        │   ├── page.tsx          # Upload screen (landing)
        │   ├── questions/        # Smart questionnaire
        │   └── summary/          # Tax summary + review + export
        ├── components/ui/        # shadcn/ui components
        └── lib/                  # API client, types, store
```

---

## 4. Frontend (Already Built — 3 Pages)

**Tech:** Next.js 16, Tailwind CSS 4, shadcn/ui, Zustand

| Page | Route | What It Does |
|---|---|---|
| **Upload** | `/` | Drag & drop Form 16 + AIS PDF. PAN + DOB fields. Password auto-resolve. Progress indicator. |
| **Questions** | `/questions` | 0-5 adaptive yes/no cards. Generated by backend based on what's missing. Skip allowed. |
| **Summary** | `/summary` | 1-page tax overview. Old vs New regime comparison. Deduction breakdown. Download ITR-2 JSON button. Post-export 8-step portal instructions. |

**Design system** (from existing `design/DESIGN.md`):
- Colors: ITD deep blue (#003178), orange accent (#F57C00), success green (#166534)
- Typography: Hanken Grotesk (headings), Inter (body), JetBrains Mono (PAN/ISIN/amounts)
- Light mode only. Clean, fintech SaaS aesthetic. shadcn/ui components.

---

## 5. Backend API

### 5.1 Endpoints

```
POST /api/session/create           # Create session, returns session_id
POST /api/upload/form16            # Upload Form 16 PDF → Form16Data
POST /api/upload/ais               # Upload AIS PDF → AISData
GET  /api/questions/{session_id}   # Get 0-5 adaptive yes/no questions
POST /api/questions/{session_id}   # Submit answers
GET  /api/compute/{session_id}     # Run regime optimizer → TaxSummary
GET  /api/export/{session_id}      # Download ITR JSON
```

### 5.2 Key API Contracts

```python
# POST /api/upload/form16
# Request: multipart/form-data (file + optional password)
# Response:
{
    "status": "parsed" | "password_required" | "invalid_pdf",
    "data": Form16Data | None,
    "required_password": bool
}

# GET /api/questions/{session_id}
# Response:
{
    "itr_type": "ITR-2",
    "auto_detected": {
        "salary": 1796602,
        "capital_gains": {"ltcg_112a": 58273, "stcg_app_rate": 5194},
        "savings_interest": 757,
        "regime_recommended": "NEW",
        "regime_savings": 31809
    },
    "questions": [
        {
            "id": "rent",
            "text": "Do you pay rent for your accommodation?",
            "type": "yes_no",
            "if_yes": [...],
            "impact": "Could save up to ₹77,582"
        }
    ]
}

# GET /api/compute/{session_id}
# Response:
{
    "total_income": 1754687,
    "tax_liability": 156974,
    "tds_paid": 155738,
    "balance_payable": 1240,
    "regime": "NEW",
    "regime_comparison": {
        "old": {"tax": 188783, "deductions": 47869},
        "new": {"tax": 156974, "deductions": 0},
        "recommended": "NEW",
        "savings": 31809
    },
    "schedule_summary": {...}
}
```

---

## 6. Core Modules

### 6.1 PDF Parser Module (`modules/parsers/`)

**Tech:** pikepdf (decrypt password-protected PDFs) + pdfplumber (extract text/tables)

**Password auto-resolution (NEVER ask user unless all attempts fail):**
```python
# Form 16: Try PAN lowercase, PAN, PAN@DOB, PAN@123
FORM16_CANDIDATES = [
    "{pan_lower}",                    # cffpm4503n
    "{pan}",                          # CFFPM4503N
    "{pan_lower}@{dob_ddmm}",        # cffpm4503n@2504
    "{pan_lower}@123",               # cffpm4503n@123
]

# AIS: ALWAYS PAN(lowercase) + DOB(DDMMYYYY)
AIS_PASSWORD = "{pan_lower}{dob_ddmmyyyy}"  # cffpm4503n25041995
```

**Form 16 extracts:** PAN, employee name, employer name/TAN, assessment year, quarterly TDS, gross salary, perquisites, exemptions (HRA, LTA), deductions (80C, 80CCD, 80D), total tax, regime choice.

**AIS extracts:** PAN, name, DOB, address; TDS entries (salary + other); SFT entries (savings interest, equity MF sales, other unit sales, dividends, purchases); tax payments; refunds.

### 6.2 Classifier Module (`modules/classifier.py`)

Maps AIS SFT codes → ITR schedules:

| AIS Code | Term | ITR Schedule | Tax Rate |
|---|---|---|---|
| TDS-192 | — | ScheduleS (Salary) | Slab |
| SFT-016(SB) | — | ScheduleOS (Interest) | Slab |
| SFT-18-EMF(M) | Long + STT paid | Schedule112A | 12.5% |
| SFT-18-EMF(M) | Short + STT paid | ScheduleCG_A2 (111A) | 15% |
| SFT-17-OTU(M) | Long | ScheduleCG_B8 | 12.5% + indexation |
| SFT-17-OTU(M) | Short | ScheduleCG_A5 | Slab rate |
| SFT-015 | — | ScheduleOS (Dividends) | Slab |

**Auto-compute CG date ranges** into 5 ITR periods:
```
Period 1: Apr 1 – Jun 15  →  Upto15Of6
Period 2: Jun 16 – Sep 15  →  Upto15Of9
Period 3: Sep 16 – Dec 15  →  Up16Of9To15Of12
Period 4: Dec 16 – Mar 15  →  Up16Of12To15Of3
Period 5: Mar 16 – Mar 31  →  Up16Of3To31Of3
```

### 6.3 Regime Optimizer (`modules/optimizer.py`)

**DETERMINISTIC MATH — NO AI CALLS.**

```
def compute_both_regimes(income, deductions):
    old = compute_old_regime(salary, deductions, other_income)
    new = compute_new_regime(salary, other_income)  # minimal deductions
    
    return {
        "recommended": "OLD" if old.tax < new.tax else "NEW",
        "savings": abs(old.tax - new.tax),
        "old_breakdown": old,
        "new_breakdown": new
    }
```

**Tax Slabs FY 2025-26:**

Old Regime:
| Slab | Rate |
|---|---|
| 0 – 2,50,000 | 0% |
| 2,50,001 – 5,00,000 | 5% |
| 5,00,001 – 10,00,000 | 20% |
| 10,00,001+ | 30% |

New Regime:
| Slab | Rate |
|---|---|
| 0 – 4,00,000 | 0% |
| 4,00,001 – 8,00,000 | 5% |
| 8,00,001 – 12,00,000 | 10% |
| 12,00,001 – 16,00,000 | 15% |
| 16,00,001 – 20,00,000 | 20% |
| 20,00,001 – 24,00,000 | 25% |
| 24,00,001+ | 30% |

Standard deduction: ₹50,000 (old) / ₹75,000 (new)

### 6.4 Smart Questions (`modules/questions.py`)

**Principle:** Extract everything possible from PDFs first. Only ask what CAN'T be auto-detected.

**ITR-2 Max Questions (5):**
1. 🏠 Paying rent? → Metro/non-metro? → Monthly amount? → Landlord PAN? (if Form 16 has HRA)
2. 🏥 Health insurance premium? → Self + Parents? → Senior citizen?
3. 💰 Additional 80C investments beyond EPF in Form 16? (if 80C < ₹1.5L)
4. 🎓 Education loan interest?
5. 🏦 Home loan? → Self-occupied or let-out? → Interest paid?

**Everything else is auto-detected from AIS:**
- All capital gains → correct schedules automatically
- Dividend income → Schedule OS
- Savings interest → Schedule OS + 80TTA deduction
- Foreign assets → Schedule FA (if any AIS entry)
- Crypto/VDAs → Schedule VDA (if any SFT entry)

### 6.5 JSON Builder (`modules/builder/`)

Takes parsed + classified data → produces schema-compliant ITR JSON.

**Critical rules learned from real filing:**
- CG date ranges must sum EXACTLY to BFLA values (auto-compute, never manual)
- ISIN: Use "INNOTAVAILAB" (not "INNOTREQUIRD") per ITD schema
- SecondaryAdd: Always "Y" if no secondary address
- Bank refund: Only ONE account with UseForRefund=true
- 112A consolidated entries: Units must be > 0 (compute from sale/price)
- STCG and LTCG must be date-split into 5 periods
- JSON hash must pass official utility validation

### 6.6 Validator (`modules/validator.py`)

25+ cross-checks:
- CG date ranges sum = BFLA
- Gross salary = sum of components
- TDS total = sum of quarterly
- Enum values correct (SecondaryAdd, ISIN, nature_of_employment, etc.)
- At most one bank for refund
- 112A exemption limit applied (₹1.25L)
- Std deduction applied correctly
- Salary in AIS matches Form 16
- TDS in AIS matches Form 16
- All CG entries in AIS reported in JSON
- All savings interest in AIS reported

---

## 7. The 10 Hard-Learned Rules

These came from a real CA + engineer filing ITR-2 manually. Every one is automated:

| # | Lesson | Implementation |
|---|---|---|
| 1 | Form 16 password is usually PAN (lowercase) | Auto-try 5 candidates. Ask only if all fail. |
| 2 | AIS password = PAN(lower) + DOB(DDMMYYYY) | Auto-compute. NEVER ask. |
| 3 | 80CCD(2) eligible amount locked at ₹0 in portal | Auto-set correct value. |
| 4 | CG date ranges must sum EXACTLY to BFLA | Auto-compute from sale dates. No manual entry. |
| 5 | ISIN INNOTREQUIRD ≠ INNOTAVAILAB | Always use INNOTAVAILAB. |
| 6 | SecondaryAdd="" fails schema | Always set to "Y" or "N". |
| 7 | Multiple banks with UseForRefund=true = warning | Auto-select first validated. |
| 8 | JSON hash prevents post-generation edits | Output valid JSON from utility templates. |
| 9 | 112A consolidated: Units=0 fails | Auto-compute from sale/price. |
| 10 | STCG and LTCG date-split into 5 periods | Auto-group from AIS sale dates. |

---

## 8. Data Privacy (Critical — Indian IT Act)

| Data | Storage | Retention |
|---|---|---|
| Email, Name, masked PAN | SQLite (encrypted) | Until user deletes |
| Full PAN, DOB | Encrypted (Fernet) | Until user deletes |
| Form 16 PDF | BytesIO (memory only) | Destroyed after parsing |
| AIS PDF | BytesIO (memory only) | Destroyed after parsing |
| Parsed tax data | In-memory session dict | 24-hour TTL |
| Generated ITR JSON | Streamed to client | NEVER stored on server |

PAN masking: `CFFPM4503N` → `CFFPM****N` in all logs and UI.

---

## 9. Key Edge Cases to Handle

1. **ITR portal rejects JSON** → Parse error message (regex), match to known fix, regenerate JSON, user downloads again. Zero re-entry.
2. **No Form 16 available** → Extract salary from AIS TDS-192 entries. Less detail but functional.
3. **Multiple Form 16s (job change)** → Detect different TANs. Merge salary. Standard deduction only once (₹75K).
4. **Form 16 / AIS / 26AS TDS mismatch** → Flag to user. AIS is authoritative source for TDS credit.
5. **PAN-Aadhaar not linked** → Block filing. Guide to link. ₹1,000 late fee warning.
6. **Capital losses** → Warn: file by July 31 or lose carry-forward right FOREVER.
7. **Previous year refund pending** → Flag from AIS Part B4. Guide to refund reissue.

---

## 10. Technology Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI (Python 3.12+) | Async, auto-docs, type-safe with Pydantic |
| PDF Parsing | pikepdf + pdfplumber | Decrypt + extract text from password-protected PDFs |
| Data Models | Pydantic v2 | Single source of truth for all data structures |
| Frontend | Next.js 16 + Tailwind + shadcn/ui | Already built. SSR, lightweight. |
| State | Zustand | No boilerplate, fits 3-page app |
| Database | SQLite (→ PostgreSQL later) | Zero ops for MVP. Single file. |
| Sessions | In-memory dict (→ Redis later) | Zero dependencies for MVP |
| Encryption | cryptography.fernet (→ KMS later) | Env variable key. Battle-tested. |
| Deployment | Render (backend) + Vercel (frontend) | Free dev tier, one-click scale to $7/mo at launch |

---

## 11. What NOT To Build (Cost-Aware Cuts)

| Feature | Why Cut |
|---|---|
| 8 AI agents with communication bus | Deterministic code handles everything except questions |
| Separate Tax Rule Engine service | 200-line Python module, not a service |
| Redis, PostgreSQL, S3 (MVP) | SQLite + in-memory + BytesIO sufficient |
| HashiCorp Vault / AWS KMS | Env variable Fernet key sufficient |
| PWA, React Native mobile app | Web mobile-responsive is enough |
| Admin dashboard, analytics, blog | Phase 2 at earliest |
| Multi-language (Hindi/Hinglish) | Phase 2 |
| 26 design documents | This single MASTER_PLAN.md replaces all |
| Landing page, pricing, about, support pages | Single upload page is the landing page |
| Kubernetes, Docker Swarm, multi-region | One VPS. Vertical scale until it breaks. |

---

## 12. Build Order (What to Build First)

```
PHASE 1 — Core Pipeline (Week 1-2)
  [ ] models/form16.py — Form16Data pydantic model
  [ ] models/ais.py — AISData pydantic model
  [ ] models/tax.py — UnifiedTaxData, RegimeResult models
  [ ] modules/parsers/pdf_utils.py — Password resolver
  [ ] modules/parsers/form16.py — Form 16 parser (pikepdf + pdfplumber)
  [ ] modules/parsers/ais.py — AIS parser
  [ ] modules/classifier.py — AIS code → ITR schedule mapper
  [ ] modules/optimizer.py — Old vs New regime (deterministic)
  [ ] Tests: Parse real Form 16 + AIS PDFs, verify extracted values

PHASE 2 — JSON Builder + Validator (Week 3)
  [ ] modules/builder/itr2.py — ITR-2 JSON builder
  [ ] modules/validator.py — 25+ cross-checks
  [ ] Tests: Generate JSON, validate against schema, verify sums

PHASE 3 — Questions + API (Week 4)
  [ ] modules/questions.py —Adaptive question generator
  [ ] api/upload.py, api/questions.py, api/compute.py, api/export.py
  [ ] main.py — FastAPI entry point, session management
  [ ] db.py — SQLite schema (users table only)

PHASE 4 — Integration + Polish (Week 5)
  [ ] Wire frontend to backend API
  [ ] End-to-end test: upload 2 PDFs → download JSON
  [ ] Test against ITD portal utility
  [ ] Export screen: 8-step portal instructions

PHASE 5 — Edge Cases + Launch (Week 6)
  [ ] Handle: no Form 16, multiple Form 16s, revised returns, capital losses
  [ ] JSON rejection auto-fix (regex match → regenerate)
  [ ] Deploy to Render (backend) + Vercel (frontend)
```

---

## 13. Deployment

**Single server.** No Kubernetes. No Docker unless you want it.

```
Option A: Render (recommended)
  → Connect GitHub repo → Render auto-detects render.yaml
  → Backend on Render (free / $7/mo), Frontend on Vercel (free)
  → Custom domains: api.taxstox.com → Render, taxstox.com → Vercel

Option B: Single VPS (₹500-1000/month)
  $ git clone && pip install && npm install
  $ uvicorn main:app --host 0.0.0.0 --port 8000
  $ cd web && npm run build && npm start
  → Nginx reverse proxy → single domain
```

Scale vertically until you can't. Then extract modules into services one at a time.

---

*This is the only document an AI agent needs. Build from top to bottom. Every module is a Python file. Every decision optimizes for simplicity and cost without compromising correctness.*

