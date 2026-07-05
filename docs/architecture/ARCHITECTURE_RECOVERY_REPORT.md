# Architecture Recovery Report — TaxStox ITR Platform

> **Date:** 2026-07-05
> **Audit By:** Enterprise Chief Architect
> **Repository:** D:\IT_Returns
> **Status:** Production — Live at taxstox.com / api.taxstox.com
> **Methodology:** Full source audit of all 52 Python modules, design docs, master plan, architecture spec, and HANDOFF.md session history.

---

## Executive Summary

TaxStox is a **production-deployed** modular monolith that automates Indian ITR filing. It takes Form 16 + AIS PDFs, auto-decrypts them, classifies capital gains, optimizes Old vs New Regime, asks 0-5 adaptive questions, builds schema-compliant ITR JSON, validates against 40+ rules, and provides step-by-step portal filing instructions.

The system was built iteratively by domain experts (a 25-year CA + 25-year software engineer) working alongside AI agents. It is live at `taxstox.com` with a Neon PostgreSQL backend on Render, a Next.js frontend on Vercel, and Google OAuth authentication.

**Core finding:** The system works correctly for its current scope (salaried ITR-2 filing for FY2025-26) but carries architectural debt that will compound if not addressed before expanding to all ITR types, multiple financial years, and enterprise features.

---

## 1. Current Architecture

### 1.1 Architecture Style

**Modular Monolith** — FastAPI single process. Each module is a Python file/package within `apps/api/src/`. The MASTER_PLAN explicitly states: "Every module CAN become a separate service later — starts as a Python file."

```
┌─────────────────────────────────────────────────────────┐
│             Frontend (Next.js 16)                        │
│             apps/web/                                    │
│             Pages: Landing → Upload → Questions →        │
│                    Summary → Export                      │
└──────────────────────┬──────────────────────────────────┘
                       │ REST (JSON) + CORS
┌──────────────────────▼──────────────────────────────────┐
│          Backend (FastAPI — Single Process)              │
│          apps/api/src/                                   │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐ │
│  │ parsers/ │ │ engine/  │ │ builders/ │ │ models/  │ │
│  │          │ │          │ │           │ │          │ │
│  │ Form 16  │ │classifier│ │ ITR-1     │ │ form16   │ │
│  │ AIS      │ │optimizer │ │ ITR-2     │ │ ais      │ │
│  │ Broker   │ │ v1 + v2  │ │ Validator │ │ tax      │ │
│  │ AIS Code │ │questions │ │           │ │ api      │ │
│  │ Mapper   │ │salary    │ │           │ │ user     │ │
│  │          │ │deductions│ │           │ │          │ │
│  └──────────┘ └──────────┘ └───────────┘ └──────────┘ │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐ │
│  │ api/     │ │ auth/    │ │ db/       │ │providers/│ │
│  │          │ │          │ │           │ │          │ │
│  │ routes   │ │ JWT      │ │ PostgreSQL│ │ PIB      │ │
│  │ auth     │ │ Google   │ │ tax_queries│ │ CBDT    │ │
│  │ dashboard│ │ OAuth    │ │           │ │ ITD      │ │
│  │ tax_routes│ │          │ │           │ │ MoF      │ │
│  └──────────┘ └──────────┘ └───────────┘ └──────────┘ │
│                                                          │
│  Session: In-memory dict (SessionManager)                │
│  Database: Neon PostgreSQL (psycopg2, raw SQL)           │
│  Scheduler: APScheduler (tax updates every 8h)           │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack (Actual)

| Layer | Technology | Version | Status |
|-------|-----------|---------|--------|
| Backend | Python 3.12+ | 3.14 (installed) | Production |
| API Framework | FastAPI | Latest | Production |
| PDF Decryption | pikepdf | Latest | Production |
| PDF Text Extraction | pdfplumber | Latest | Production |
| Data Validation | Pydantic v2 | Latest | Production |
| Database Driver | psycopg2 (raw SQL) | Latest | Production |
| Database | Neon PostgreSQL | Serverless | Production |
| Auth | JWT (jose) + Google OAuth | — | Production |
| AI Summarizer | DeepSeek API | — | Production (optional) |
| Scheduler | APScheduler | Latest | Production |
| Web Scraping | httpx + BeautifulSoup4 + lxml | Latest | Production |
| Frontend | Next.js 16 + Tailwind CSS 4 + shadcn/ui | Latest | Production |
| State Management | Zustand | Latest | Production |
| Deployment (Backend) | Render | — | Production |
| Deployment (Frontend) | Vercel | — | Production |

---

## 2. Module Catalogue

### 2.1 Complete Module Inventory

| # | Module Path | Lines | Responsibility | Status |
|---|------------|-------|----------------|--------|
| 1 | `main.py` | ~80 | FastAPI app entry, CORS, lifespan, router mounting | Production |
| 2 | `models/form16.py` | ~220 | Form 16 domain model: Part A, Part B, Annexure, 12BA, Chapter VI-A, Tax Computation | Production |
| 3 | `models/ais.py` | ~145 | AIS domain model: TDS, SFT, Savings Interest, Equity MF Sales, Other Units, Refunds | Production |
| 4 | `models/tax.py` | ~160 | Unified tax model: CG entries, classification, regime results, user answers | Production |
| 5 | `models/api.py` | ~95 | API request/response schemas: Upload, Questions, Summary, Export, Validation | Production |
| 6 | `models/user.py` | ~65 | User model: registration, login, profile, token | Production |
| 7 | `parsers/form16_parser.py` | ~447 | Form 16 PDF parser: decrypt (pikepdf), extract (pdfplumber), structured parsing | Production |
| 8 | `parsers/ais_parser.py` | ~594 | AIS PDF parser: table extraction, TDS detail rows, equity MF, OTU, SFT, refunds | Production |
| 9 | `parsers/ais_code_mapper.py` | ~352 | AIS information code → ITR schedule mapper: 25+ TDS/SFT codes mapped | Production |
| 10 | `parsers/broker_statements/zerodha.py` | — | Zerodha tradebook + tax P&L CSV parser | Production |
| 11 | `parsers/broker_statements/generic.py` | — | Generic broker statement parser (Groww, Upstox, Angel One) | Production |
| 12 | `engine/classifier.py` | ~243 | Capital gains classifier: equity MF → 112A/111A, OTU → A5/B8, date ranges, 112A exemption | Production |
| 13 | `engine/regime_optimizer.py` | ~401 | Regime Optimizer v1: Old vs New tax computation, deductions, 87A, slabs (FY2025-26) | Production |
| 14 | `engine/regime_optimizer_v2.py` | ~360 | Regime Optimizer v2: ITD portal-matched computation, surcharge with marginal relief, HEC | Production |
| 15 | `engine/salary_computer.py` | ~198 | Salary computer: 17(1)+(2)+(3), S10 exemptions (HRA, LTA, child edu), S16 deductions | Production |
| 16 | `engine/deductions_computer.py` | ~199 | Chapter VI-A deductions: 80C, 80CCD(1B), 80CCD(2), 80D, 80TTA, 80TTB, 80GG, 80E | Production |
| 17 | `engine/questions.py` | ~285 | Adaptive question engine: rent, health insurance, 80C, home loan, other income (0-5 questions) | Production |
| 18 | `engine/recommendation_engine.py` | ~330 | Tax recommendation engine: regime reasoning, confidence scoring, optimization suggestions | Production |
| 19 | `engine/itr_selector.py` | ~134 | ITR form auto-selector: income source analysis → ITR-1/2/3/4 | Production |
| 20 | `engine/cross_validator.py` | ~50+ | Cross-validator: Form 16 ↔ AIS TDS reconciliation, salary matching, TAN verification | Production |
| 21 | `builders/itr_json_builder.py` | ~535 | ITR-2 JSON builder: General Info, Schedule S, 112A, CG, OS, CYLA, BFLA, SI, VI-A, TI, TTI, TaxPaid | Production |
| 22 | `builders/itr1.py` | ~315 | ITR-1 (SAHAJ) JSON builder: simplified structure for salaried individuals | Production |
| 23 | `builders/validator.py` | ~968 | ITR JSON validator: 40+ checks — PAN format, enum values, cross-consistency, TDS, 80C/80D limits | Production |
| 24 | `api/routes.py` | ~595 | Main API routes: upload, process, answers, export, broker statement upload, document upload | Production |
| 25 | `api/auth_routes.py` | — | Auth routes: register, login, Google OAuth callback, profile | Production |
| 26 | `api/dashboard.py` | — | Dashboard routes: filing history, user profile | Production |
| 27 | `api/calculators.py` | — | Standalone calculators | Production |
| 28 | `api/simulation.py` | — | Tax simulation/scenario endpoints | Production |
| 29 | `api/tax_routes.py` | — | Tax updates, deadlines, tips, facts API | Production |
| 30 | `auth/jwt.py` | ~73 | JWT token generation, verification, FastAPI dependency injection | Production |
| 31 | `db/database.py` | ~349 | PostgreSQL via psycopg2: users, filings, tax_updates, tax_deadlines, tax_tips, tax_facts, tax_sync_log | Production |
| 32 | `db/tax_queries.py` | — | Tax content CRUD: upsert, query, seed functions for deadlines/tips/facts | Production |
| 33 | `providers/__init__.py` | — | Provider framework: BaseProvider, RawUpdate, @register_provider decorator | Production |
| 34 | `providers/pib_provider.py` | — | PIB RSS feed scraper — finance/tax keyword filter | Production |
| 35 | `providers/incometax_provider.py` | — | incometaxindia.gov.in scraper | Production |
| 36 | `providers/cbdt_provider.py` | — | CBDT circulars scraper | Production |
| 37 | `providers/mof_provider.py` | — | Ministry of Finance press release scraper | Production |
| 38 | `providers/taxpayer_data.py` | — | Taxpayer data provider abstraction (PDF backend → ITD API future) | Production |
| 39 | `scheduler/__init__.py` | — | APScheduler: fetch→summarize→store pipeline every 8h | Production |
| 40 | `summarizer/__init__.py` | — | DeepSeek AI summarizer for tax updates (structured JSON extraction) | Production |
| 41 | `utils/password_resolver.py` | — | PDF password auto-resolution: PAN variants, AIS auto-compute | Production |
| 42 | `utils/session.py` | — | In-memory session manager: create, get, expire (24h TTL) | Production |

### 2.2 Module Grouping by Concern

| Concern | Modules | Cohesion | Coupling |
|---------|---------|----------|----------|
| **Domain Models** | `models/` (5 files) | High — single responsibility per model | Low — models reference each other explicitly |
| **Document Parsing** | `parsers/` (5 files) | High — shared PDF decrypt/extract patterns | Medium — depends on models for output types |
| **Tax Computation** | `engine/` (9 files) | Medium — 9 engines with overlapping concerns | High — classifier → optimizer → deductions → salary all cross-reference |
| **JSON Building** | `builders/` (3 files) | Medium — ITR-1 and ITR-2 share no base class | Medium — depends on models + engine results |
| **API Layer** | `api/` (6 files) | Medium — routes per domain area | High — orchestrates all other modules |
| **Infrastructure** | `db/`, `auth/`, `utils/` (5 files) | Low — separate concerns | Low — depended on by other modules |
| **External Data** | `providers/`, `scheduler/`, `summarizer/` (8 files) | High — provider framework well-abstracted | Low — only depends on db for storage |

---

## 3. Dependency Analysis

### 3.1 Dependency Graph (Recovered from Import Analysis)

```
main.py
├── api/routes.py ─────────────────────────────────────────────┐
│   ├── parsers/form16_parser.py → models/form16.py            │
│   ├── parsers/ais_parser.py → models/ais.py                  │
│   ├── engine/classifier.py → models/tax.py, models/ais.py    │
│   ├── engine/regime_optimizer_v2.py                          │
│   │   ├── engine/salary_computer.py → models/form16.py       │
│   │   ├── engine/deductions_computer.py → models/form16.py   │
│   │   └── engine/classifier.py (lazy import)                 │
│   ├── engine/questions.py → models/form16.py, models/api.py  │
│   ├── builders/itr_json_builder.py → models/tax.py           │
│   ├── builders/itr1.py → models/tax.py                       │
│   ├── builders/validator.py → models/api.py                  │
│   ├── engine/itr_selector.py                                 │
│   ├── utils/password_resolver.py                             │
│   └── utils/session.py                                       │
├── api/auth_routes.py → auth/jwt.py, db/database.py           │
├── api/dashboard.py → auth/jwt.py, db/database.py             │
├── api/calculators.py                                         │
├── api/simulation.py                                          │
├── api/tax_routes.py → db/tax_queries.py                      │
├── db/database.py (psycopg2, PostgreSQL)                      │
├── auth/jwt.py (jose)                                         │
├── providers/ (5 files) → scheduler/                          │
├── scheduler/ → summarizer/, db/tax_queries.py                │
└── summarizer/ (DeepSeek API)                                 │
```

### 3.2 Critical Dependency Findings

| Finding | Severity | Detail |
|---------|----------|--------|
| **Circular dependency risk** | Medium | `regime_optimizer_v2.py` lazily imports `engine/classifier.py` inside `_cg_summary()` method to avoid circular imports |
| **No base class for builders** | Low | `itr_json_builder.py` (ITR-2) and `itr1.py` (ITR-1) share no common interface/abstract class |
| **Dual optimizer versions** | High | `regime_optimizer.py` (v1) and `regime_optimizer_v2.py` (v2) both exist; routes.py uses v2 but v1 is still imported and available |
| **Model cross-references** | Low | `models/tax.py` imports from `models/form16.py` and `models/ais.py` — expected coupling for unified data model |
| **API routes as god orchestrator** | Medium | `api/routes.py` (595 lines) orchestrates parsers, classifiers, optimizers, question engine, ITR selector, and builders — wide coupling surface |

---

## 4. Domain Model

### 4.1 Core Entities

```
Taxpayer (inferred, not explicit)
├── PAN: str
├── Name: str
├── DOB: date
├── Mobile: str
└── Email: str

Form16Data (from PDF parsing)
├── Part A: Employer/Taxpayer identity, quarterly TDS, totals
├── Part B: Salary breakup, exemptions S10, deductions S16, Chapter VI-A, Tax computation
├── Annexure: Salary components with amounts
└── Form 12BA: Perquisites detail (21 types)

AISData (from PDF parsing)
├── Personal Info: PAN, Aadhaar(masked), Name, DOB, Mobile, Email
├── TDS Entries: Salary (TDS-192) + Other (194A, 194I, 194J, ...)
├── SFT Entries:
│   ├── Savings Interest (SFT-016(SB))
│   ├── Equity MF Sales (SFT-18-EMF(M)): ISIN, date, qty, price, cost, STT, term
│   ├── Other Unit Sales (SFT-17-OTU(M)): Gold ETF, Debt funds
│   └── Securities Purchases (SFT-17(Pur))
├── Tax Payments
├── Refunds (Part B4)
└── Annexure II Salary

UnifiedTaxData (assembled for JSON building)
├── PAN, DOB
├── Form16Data
├── AISData
├── UserAnswers (0-5 questions)
├── ClassifiedCGData (classification output)
│   ├── Schedule 112A entries (Equity LTCG)
│   ├── CG A2 entries (Equity STCG 15%)
│   ├── CG A5 entries (Non-equity STCG slab)
│   ├── CG B8 entries (Non-equity LTCG 12.5%)
│   └── CGDateRanges (5-period segmentation)
├── RegimeResult (optimizer output)
│   ├── old_tax, new_tax
│   ├── recommended regime
│   ├── savings
│   └── breakdowns (old + new)
└── Final computation values
```

### 4.2 Value Objects

| Value Object | Type | Validation |
|-------------|------|------------|
| PAN | `str` (10 chars, regex) | Pydantic field_validator |
| Aadhaar | `str` (12 digits) | Masked in AIS (XXXX XXXX NNNN) |
| Monetary amounts | `Decimal` (18,2 precision) | Pydantic Decimal |
| Dates | `date` | Multiple format parsing (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD) |
| ISIN | `str` (12 chars) | "INNOTAVAILAB", "INNOTREQUIRD" enum validation |
| Financial Year | `str` ("FY2025-26") | Currently hardcoded |
| Assessment Year | `str` ("2026-27") | Currently hardcoded |
| Tax Regime | `Enum` (OLD, NEW) | `Regime` enum in form16.py |
| ITR Type | `Enum` (ITR-1, ITR-2, ITR-3, ITR-4) | `ITRForm` enum in itr_selector.py |

### 4.3 Aggregates

| Aggregate Root | Internal Entities | Consistency Boundary |
|----------------|-------------------|---------------------|
| `Form16Data` | PartA, PartB, Annexure, Form12BA, ChapterVIADeductions, TaxComputation, Section10Exemptions, QuarterlyTDS | Single employer, single FY |
| `AISData` | AISTDSEntry[], AISEquityMFSale[], AISOtherUnitSale[], AISSavingsInterest[], AISRefund[] | All financial transactions for one PAN |
| `ClassifiedCGData` | CGSaleEntry[], CGDateRanges, Schedule buckets (112A, A2, A5, B8) | All capital gains for one filing |
| `RegimeResult` | Old breakdown dict, New breakdown dict | Single regime comparison |

---

## 5. Business Flow (Recovered)

### 5.1 Primary Flow: Upload to JSON Export

```
STEP 1: User Authentication
  ├── Register (email, password, PAN, name, DOB) → JWT token
  ├── Login (email, password) → JWT token
  └── Google OAuth → JWT token

STEP 2: Document Upload
  ├── POST /api/v1/upload (PAN + DOB + Form16 PDF + AIS PDF)
  ├── PasswordResolver auto-tries Form 16 passwords (PAN variants)
  ├── AIS password auto-computed: PAN(lower) + DOB(DDMMYYYY)
  ├── Form16Parser → Form16Data (Part A + B + Annexure)
  ├── AISParser → AISData (TDS + SFT + Interest + Refunds)
  └── Session created (24h TTL, in-memory)

STEP 3: Processing & Classification
  ├── POST /api/v1/process/{session_id}
  ├── ITRSelector: auto-selects ITR-1/2/3/4 from income sources
  ├── ClassificationEngine: AIS entries → ITR schedule buckets
  │   ├── Equity MF Long → Schedule 112A (12.5% tax)
  │   ├── Equity MF Short → CG A2/111A (15% tax)
  │   ├── Other Units Short → CG A5 (slab rate)
  │   └── Other Units Long → CG B8 (12.5% tax)
  ├── RegimeOptimizerV2:
  │   ├── SalaryComputer: Gross → S10 exemptions → S16 deductions → Income from salary
  │   ├── DeductionsComputer: 80C, 80CCD(1B), 80CCD(2), 80D, 80TTA, 80TTB
  │   ├── Slab tax computation (Old + New)
  │   ├── Special rate CG tax (112A, 111A)
  │   ├── 87A Rebate
  │   ├── Surcharge (with marginal relief)
  │   ├── HEC @ 4%
  │   └── Final rounded tax
  └── QuestionEngine: generates 0-5 adaptive questions

STEP 4: User Answers Questions
  ├── POST /api/v1/answers/{session_id}
  ├── User answers: rent, health insurance, 80C, home loan, other income
  └── Regime recomputed with user answers → TaxSummaryResponse

STEP 5: Export ITR JSON
  ├── POST /api/v1/export/{session_id}
  ├── ITRJSONBuilder (ITR-2) or ITR1Builder (ITR-1)
  │   ├── PartA_GeneralInfo (PAN, Name, DOB, AY, Regime, Bank)
  │   ├── ScheduleS (Salary)
  │   ├── Schedule112A (Equity LTCG)
  │   ├── ScheduleCG (A2, A5, B8, SecF)
  │   ├── ScheduleOS (Interest income)
  │   ├── ScheduleVIA (Deductions)
  │   ├── PartB-TI (Total Income)
  │   ├── PartB-TTI (Tax Computation)
  │   └── ScheduleTaxPaid (TDS, Self-Assessment Tax)
  ├── ITRValidator: 40+ cross-validation checks
  └── Download JSON + Portal filing instructions
```

### 5.2 Secondary Flow: Broker Statement Upload

```
POST /api/v1/upload/broker-statement/{session_id}
  ├── Broker detection: zerodha, groww, upstox, angel_one
  ├── Zerodha: tax P&L CSV → tradebook CSV fallback
  ├── Generic: parse_broker_statement()
  ├── Convert to AIS-compatible format
  ├── Merge with existing AIS data
  └── Reclassify capital gains
```

### 5.3 Background Flow: Tax Updates Sync

```
APScheduler (every 8 hours)
  ├── PIB Provider: RSS feed → finance/tax keywords → 60-day recency
  ├── CBDT Provider: Circulars + Notifications scraping
  ├── ITD Provider: incometaxindia.gov.in scraping
  ├── MoF Provider: finmin.gov.in press releases
  ├── DeepSeek AI Summarizer: structured JSON extraction
  │   ├── summary_short, what_changed, who_affected
  │   ├── action_required, category, effective_date
  │   └── Falls back to raw title if DEEPSEEK_API_KEY missing
  ├── DB: upsert_tax_update() (dedup by source_url UNIQUE)
  └── Tax sync log recorded
```

---

## 6. Data Flow

```
PDF Bytes (Form 16 + AIS)
  │
  ├── pikepdf (decrypt with password)
  ├── pdfplumber (extract text/tables)
  ├── Regex-based structured parsing
  └── Pydantic v2 validation → Domain Models

Domain Models
  │
  ├── ClassificationEngine → ClassifiedCGData
  │   ├── CGSaleEntry[] (per-transaction classified entries)
  │   └── CGDateRanges (5-period ITR segmentation)
  │
  ├── RegimeOptimizerV2 → RegimeResult
  │   ├── SalaryComputer → SalaryBreakdown
  │   ├── DeductionsComputer → DeductionsBreakdown
  │   └── Slab tax + Special rate CG tax + Rebate + Surcharge + Cess
  │
  └── UnifiedTaxData (all data assembled)

UnifiedTaxData
  │
  ├── ITRJSONBuilder.build() → dict (ITR JSON structure)
  ├── ITRValidator.validate() → ValidationReport (40+ checks)
  └── ExportResponse (JSON + filename + validation results)

Session (in-memory dict)
  ├── session_id (UUID)
  ├── pan, dob
  ├── form16: Form16Data
  ├── ais: AISData
  ├── classified_cg: ClassifiedCGData
  ├── regime_result: RegimeResult
  ├── user_answers: UserAnswers
  ├── itr_json: dict
  └── status: str (parsed → classified → questions_answered → built)

Database (Neon PostgreSQL)
  ├── users (id, email, pan, name, hashed_password, dob, created_at)
  ├── filings (id, user_id, assessment_year, itr_type, regime, status)
  ├── tax_updates (AI-summarized govt updates)
  ├── tax_deadlines (seeded)
  ├── tax_tips (seeded)
  ├── tax_facts (seeded)
  └── tax_sync_log (sync run history)
```

---

## 7. Tax Computation Flow (Detailed)

### 7.1 ITD Portal-Matched Computation Pipeline (v2)

```
INPUTS:
  Form16Data (parsed PDF)
  ClassifiedCGData (AIS classification)
  UserAnswers (0-5 questions)
  Savings interest (Decimal)
  Other interest (Decimal)

STEP 1-4: SALARY INCOME
  Gross Salary = 17(1) + 17(2) + 17(3)
  Less: Section 10 Exemptions
    - HRA: min(actual HRA, rent-10% basic, 40%/50% basic)
    - LTA: from Form 16 Part B Section 10
    - Child Edu: ₹100/mo/child, max 2 children
    - Gratuity, Leave Encashment, Commuted Pension, Other
  Less: Section 16 Deductions
    - Standard Deduction: ₹75K (New) / ₹50K (Old)
    - Professional Tax: min(actual, ₹2,500)
  = Income under head "Salaries"

STEP 5: HOUSE PROPERTY INCOME
  If home loan + self-occupied:
    Loss = min(home_loan_interest, ₹2,00,000)
  (Let-out not yet implemented)

STEP 6: CAPITAL GAINS
  Classification Engine categorizes:
    - Schedule 112A: Equity LTCG (held >12mo, STT paid)
      → ₹1,25,000 exemption (FIFO)
      → Tax @ 12.5% on excess
    - CG A2/111A: Equity STCG (held ≤12mo, STT paid)
      → Tax @ 15%
    - CG A5: Non-equity STCG
      → Added to slab income → Tax at slab rate
    - CG B8: Non-equity LTCG
      → Tax @ 12.5% (without indexation)

STEP 7: OTHER SOURCES
  = Savings interest + Term deposit interest + Other interest
  (From AIS SFT-016(SB) + SFT-016(TD) entries)

STEP 8: GROSS TOTAL INCOME
  Slab Income = Salary + STCG(slab) + Interest - Home Loan Loss
  Special Rate Income = LTCG(112A) + STCG(15%) + LTCG(Other)
  GTI = Slab Income + Special Rate Income

STEP 9: CHAPTER VI-A DEDUCTIONS
  NEW REGIME: Only 80CCD(2) (Employer NPS)
  OLD REGIME:
    - 80C: min(EPF + additional, ₹1,50,000)
    - 80CCD(1B): Additional NPS, max ₹50,000
    - 80CCD(2): Employer NPS (available in BOTH regimes)
    - 80D: Health Insurance (₹25K self + ₹25K/50K parents)
    - 80TTA: Savings interest, max ₹10,000 (non-senior)
    - 80TTB: Interest, max ₹50,000 (senior citizen)
    - 80GG: Rent without HRA, max ₹60,000
    - 80E: Education loan interest (unlimited)

STEP 10: TOTAL INCOME
  = max(0, GTI - Total Deductions)

STEP 11: TAX ON SLAB INCOME
  NEW REGIME (FY2025-26):
    0-4L: 0% | 4-8L: 5% | 8-12L: 10% | 12-16L: 15%
    16-20L: 20% | 20-24L: 25% | >24L: 30%
  OLD REGIME (FY2025-26):
    0-2.5L: 0% | 2.5-5L: 5% | 5-10L: 20% | >10L: 30%

STEP 12: TAX ON SPECIAL RATE INCOME
  = 112A Tax (12.5%) + 111A Tax (15%) + Other LTCG Tax (12.5%)

STEP 13: TAX BEFORE REBATE
  = Slab Tax + Special Rate Tax

STEP 14: REBATE u/s 87A
  New Regime: if total_income ≤ ₹12L → max ₹60K rebate
  Old Regime: if total_income ≤ ₹5L → max ₹12.5K rebate

STEP 15: SURCHARGE (with marginal relief)
  > ₹50L: 10% | > ₹1Cr: 15% | > ₹2Cr: 25% | > ₹5Cr: 37%
  Marginal relief: surcharge ≤ (income - threshold)

STEP 16: HEALTH & EDUCATION CESS
  = (Tax After Rebate + Surcharge) × 4%

STEP 17: FINAL TAX
  = Round to nearest ₹1
```

---

## 8. Document Processing Flow

### 8.1 Form 16 PDF Pipeline

```
PDF File
  ↓
Open with pikepdf (try without password first)
  ↓ (if encrypted)
Try password candidates:
  1. User-provided password (if any)
  2. PAN(lowercase) → "cffpm4503n"
  3. PAN(uppercase) → "CFFPM4503N"
  4. PAN(lower)@DDMM → "cffpm4503n@2504"
  5. PAN(lower)@123 → "cffpm4503n@123"
  6. PAN(lower)DDMM → "cffpm4503n2504"
  ↓ (on success)
Decrypt with pikepdf → save to BytesIO → read bytes
  ↓
Extract text with pdfplumber (all pages)
  ↓
Regex-based structured parsing:
  Part A:
    - PAN: regex "[A-Z]{5}[0-9]{4}[A-Z]"
    - TAN: regex "[A-Z]{4}[0-9]{5}[A-Z]"
    - Employer name: first meaningful line
    - Certificate number
    - Assessment Year
    - TDS totals: "Total (Rs.) XXXXX.XX XXXXX.XX XXXXX.XX"
    - Quarterly TDS: "Q1 QWBOIUDA XXXXX.00 XXXXX.00 XXXXX.00"
  Part B:
    - 115BAC opt-out: "opting out...? Yes/No"
    - 17(1) Salary, 17(2) Perquisites, 17(3) Profits
    - Total gross salary
    - S10 exemptions (HRA, LTA, etc.)
    - S16 deductions (Std Ded, Entertainment, Prof Tax)
    - Income under head salaries
    - Chapter VI-A deductions (80C, 80CCD(2), etc.)
    - Tax computation (tax, rebate, cess, net tax)
  Annexure:
    - Salary component lines: "Component Name 1,23,456.00"
    - Classified into: basic, hra, special_allowance, lta, lunch_coupons,
      broadband, special_award, nps_employer, dbip_bonus
  ↓
Pydantic v2 model validation → Form16Data
```

### 8.2 AIS PDF Pipeline

```
PDF File
  ↓
Password computed: PAN(lower) + DOB(DDMMYYYY)
  → "cffpm4503n25041995"
  ↓
Decrypt with pikepdf → extract tables with pdfplumber
  ↓
Table-based parsing (all pages, all tables):
  Part A: Personal Info
    - Name: after PAN + masked Aadhaar pattern
    - DOB: "Date of Birth DD/MM/YYYY"
    - Mobile: "Mobile Number XXXXXXXXXX"
    - Email: regex match
    - Aadhaar: "XXXX XXXX NNNN" pattern
  Part B1: TDS Entries
    - Info code detection: "TDS-192", "TDS-194A", etc.
    - Source name extraction
    - Quarterly detail rows: Q1-Q4 with date, amount, TDS
  Part B2: SFT Entries
    - SFT-016(SB): Savings interest → bank name, account, interest
    - SFT-18-EMF(M): Equity MF sales → column-adaptive parsing
      (Page 1 and Page 2 have different layouts)
    - SFT-17-OTU(M): Other unit sales → column-position based
    - SFT-17(Pur): Securities purchases
  Part B4: Refunds
    - ECS/RTGS/NEFT detection
    - FY, mode, amount, date extraction
  Part B7: Annexure II Salary
    - Gross salary, perquisites, profits in lieu
  ↓
AIS Code Mapper:
  TDS-192 → ScheduleTDS1 (Salary TDS)
  TDS-194A → ScheduleTDS2 (Interest TDS)
  TDS-194I → ScheduleTDS2 (Rent TDS)
  ... (25+ code mappings)
  SFT codes → income type classification
  ↓
Pydantic v2 model validation → AISData
```

---

## 9. Validation Flow

### 9.1 ITR JSON Validator (40+ Checks)

```
VALIDATION CATEGORIES:

1. IDENTITY (V-ID-001 to V-ID-004)
   ├── PAN format: regex [A-Z]{5}[0-9]{4}[A-Z]
   ├── PAN consistency across schedules
   ├── DOB validity
   └── Personal info completeness

2. MANDATORY FIELDS
   ├── PartA_GeneralInfo, ScheduleS, PartB-TI, PartB-TTI, ScheduleTaxPaid
   └── Assessment Year validity

3. SCHEMA & ENUMS
   ├── SecondaryAdd must be "Y" or "N" (not empty string)
   ├── ISIN "INNOTREQUIRD" → should be "INNOTAVAILAB"
   ├── Filing status (ReturnType, ReturnFileMode)
   └── Bank account IFSC format

4. CROSS-SCHEDULE CONSISTENCY
   ├── CG SecF LTCG total = B8 total + 112A total (within ₹1)
   ├── CG SecF STCG AppRate total = A5 total (within ₹1)
   ├── Total income = sum of income heads
   └── Salary consistency (TDS > 0 → gross salary > 0)

5. CAPITAL GAINS (V-CG-001 to V-CG-020)
   ├── 112A exemption ≤ ₹1,25,000
   ├── CG date range totals match BFLA
   ├── STT=No entries should be in A5 (not A2)
   └── CG date range segmentation valid

6. DEDUCTIONS (V-DED-001 to V-DED-010)
   ├── 80C total ≤ ₹1,50,000
   ├── 80D self ≤ ₹25,000 (₹50,000 if senior)
   ├── 80D parents ≤ ₹25,000 (₹50,000 if senior)
   ├── 80CCD(1B) ≤ ₹50,000
   └── Home loan interest ≤ ₹2,00,000 (self-occupied)

7. TAX COMPUTATION
   ├── Independent recalculation of tax
   ├── TDS consistency across schedules
   ├── 87A rebate eligibility check
   └── Surcharge applicability

8. DATA QUALITY
   ├── Negative values detection
   ├── Unrealistic values (> ₹10 Cr flagged)
   └── Empty schedules detection
```

---

## 10. Rule Processing Flow

### 10.1 Current Rule Implementation

Tax rules are currently **hardcoded as Python constants and logic** within the engine modules:

| Rule Category | Implementation | Location | Versioned? |
|---------------|---------------|----------|------------|
| Tax Slabs (Old) | Constants in `_slab_tax_old()` | `regime_optimizer.py`, `regime_optimizer_v2.py` | FY2025-26 only |
| Tax Slabs (New) | Constants in `_slab_tax_new()` | `regime_optimizer.py`, `regime_optimizer_v2.py` | FY2025-26 only |
| Surcharge rates | `SURCHARGE_SLABS` constant | `regime_optimizer_v2.py` | FY2025-26 only |
| Rebate thresholds | `REBATE_*` constants | Both optimizers | FY2025-26 only |
| Deduction limits | `LIMIT_80C`, `LIMIT_80D_*`, etc. | `deductions_computer.py`, `regime_optimizer.py` | FY2025-26 only |
| HRA computation | `HRA_METRO_PCT`, `HRA_NON_METRO_PCT` | `salary_computer.py` | Not versioned |
| 112A exemption | `LTCG_112A_EXEMPTION = 125000` | `classifier.py` | Not versioned |
| Standard deduction | `STD_DEDUCTION_OLD = 50000`, `STD_DEDUCTION_NEW = 75000` | Multiple files | FY2025-26 only |

**Key Gap:** There is no rule repository, no rule versioning by financial year, and no separation between the computation engine and tax rule data. To add FY2024-25 or FY2026-27 rules, code must be modified — violating Constitutional Principle P8 (Compliance Is Continuous) and Architectural Invariant I2 (Rule-Engine Separation).

---

## 11. Existing Strengths

| Strength | Evidence | Business Impact |
|----------|----------|-----------------|
| **Production-proven PDF parsing** | Real Form 16 + AIS PDFs parsed successfully; 10 hard-learned rules documented | Core value prop works |
| **ITD portal-matched computation** | v2 optimizer matches portal step-by-step including marginal relief, HEC, rounding | Tax correctness |
| **Deep domain expertise embedded** | 25-year CA + 25-year engineer designed the system; lesson log captures edge cases | Reduces error risk |
| **Password auto-resolution** | Smart password guessing for Form 16; auto-compute for AIS | Eliminates user friction |
| **40+ validation rules** | Covers PAN, enums, cross-schedule consistency, TDS, deduction limits, CG, tax math | Prevents ITD portal rejection |
| **Cost-aware engineering** | Modular monolith; SQLite→PostgreSQL; in-memory→Redis; BytesIO not disk; zero AI for math | Low operating cost |
| **Provider framework well-abstracted** | BaseProvider + @register_provider pattern; 4 govt sources; graceful failure | Extensible for future data sources |
| **Production deployment** | Live at taxstox.com with Render+Vercel+Neon; keep-alive cron; auto-deploy | Real users |
| **Google OAuth + JWT auth** | Popup flow with postMessage; JWT with 24h expiry; optional user dependency | Security |
| **Broker statement support** | Zerodha, Groww, Upstox, Angel One parsers | Expands user base to traders |
| **AIS code mapper** | 25+ TDS/SFT codes mapped to ITR schedules | Completeness of income capture |

---

## 12. Existing Weaknesses

| Weakness | Location | Impact | Severity |
|----------|----------|--------|----------|
| **Hardcoded FY2025-26** | All engine modules | Cannot file for any other financial year without code changes | Critical |
| **No rule-engine separation** | `regime_optimizer*.py`, `deductions_computer.py`, `salary_computer.py` | Rules mixed with computation logic; cannot add rules without code changes | Critical |
| **Duplicate optimizer implementations** | `regime_optimizer.py` (v1) + `regime_optimizer_v2.py` (v2) | Maintenance burden; risk of inconsistency between versions | High |
| **No test suite** | `tests/` directory has only `test_e2e_real_data.py` | Regression risk on every change; cannot refactor safely | High |
| **No multi-year support** | All modules | Architecture must change to support historical + future FYs | High |
| **In-memory sessions** | `utils/session.py` | Server restart loses all sessions; no horizontal scaling | Medium |
| **Raw SQL (psycopg2)** | `db/database.py` | No migration framework; manual schema changes; SQL injection risk if params misused | Medium |
| **No API versioning** | `api/routes.py` | All routes at `/api/v1/`; breaking changes affect all clients | Medium |
| **Limited ITR type support** | Builders only for ITR-1 + ITR-2 | ITR-3 (business), ITR-4 (presumptive), ITR-5/6/7 missing | Medium |
| **No audit trail** | All computation modules | Cannot explain "how was this tax computed?" without code inspection | Medium |
| **No structured logging** | `logging.info(f"PARSED with pwd=...")` | Logs use f-strings, not structured JSON; hard to search/alert on | Low |
| **Hardcoded secrets fallback** | `auth/jwt.py`: `SECRET_KEY = os.getenv("TAXSTOX_JWT_SECRET", "taxstox-dev-secret-change-in-production")` | Dev secret in code; no enforcement of production override | Low |
| **Lazy imports to break cycles** | `regime_optimizer_v2.py`: `from src.engine.classifier import ClassificationEngine` inside method | Fragile; can break if method order changes | Low |

---

## 13. Technical Debt Register

| ID | Type | Description | Location | Priority |
|----|------|-------------|----------|----------|
| TD-001 | Constitutional | Hardcoded FY2025-26 tax rules — violates I2 (Rule-Engine Separation) | engine/*.py | P0 |
| TD-002 | Constitutional | No multi-year architecture — violates I1 (Multi-Year) | All modules | P0 |
| TD-003 | Architectural | Dual optimizer versions (v1 + v2) — violates P1 (Consistency) | engine/regime_optimizer*.py | P1 |
| TD-004 | Architectural | No base class/interface for ITR builders — violates P10 (Extensibility) | builders/*.py | P1 |
| TD-005 | Architectural | Tax computation constants duplicated across files | engine/*.py | P1 |
| TD-006 | Code | `api/routes.py` at 595 lines — god module | api/routes.py | P2 |
| TD-007 | Code | `builders/validator.py` at 968 lines — god module | builders/validator.py | P2 |
| TD-008 | Code | Lazy imports to break circular dependency | engine/regime_optimizer_v2.py:335 | P2 |
| TD-009 | Test | Single test file with no test framework structure | tests/test_e2e_real_data.py | P1 |
| TD-010 | Test | No unit tests for any module | All modules | P1 |
| TD-011 | Dependency | Dev JWT secret hardcoded as default parameter | auth/jwt.py:12 | P2 |
| TD-012 | Documentation | No ADRs for architecture decisions | N/A | P2 |
| TD-013 | Code | No structured logging — f-strings instead of JSON | Multiple files | P3 |
| TD-014 | Code | Hardcoded AY "2026-27" in builders | builders/*.py:31 | P2 |
| TD-015 | Code | Hardcoded FY "2025-26" across all computation modules | engine/*.py | P0 |

---

## 14. Architectural Debt Register

| ID | Debt | Current State | Target State | Migration Risk |
|----|------|---------------|--------------|----------------|
| AD-001 | Hardcoded tax rules → Rule repository | Constants in code | Versioned rule config (FY-indexed JSON/database) | Low — rule extraction is mechanical |
| AD-002 | Monolithic computation → Pipeline with pluggable rules | Single function per regime | Computation pipeline with registered rule evaluators | Medium — must preserve exact ITD portal behavior |
| AD-003 | Direct PDF parsing → Provider abstraction | `AISParser.parse()` called directly | DataProvider interface with PDF/API/AA backends | Low — TaxpayerDataProvider already exists |
| AD-004 | Single FY → Multi-FY architecture | FY hardcoded everywhere | FY-aware repositories, versioned rules, cross-year compatibility | High — touches every module |
| AD-005 | In-memory sessions → Redis | `SessionManager` dict | Redis-backed session store with serialization | Low — SessionManager already has get/create interface |
| AD-006 | Raw SQL → Migration framework | Manual `CREATE TABLE IF NOT EXISTS` | Alembic migrations with version history | Medium — must preserve existing data |
| AD-007 | ITR-1/2 builders → Common builder framework | Separate builder classes with no shared base | Abstract base builder with ITR-type-specific subclasses | Low — builders are output-only |
| AD-008 | v1 + v2 optimizers → Single optimizer | Two duplicate implementations | Retire v1; v2 becomes canonical; add rule config | Low — v2 already used in routes.py |

---

## 15. Duplicated Logic

| Duplication | Locations | Risk |
|-------------|-----------|------|
| Tax slab computation | `regime_optimizer.py::_slab_tax_old/_slab_tax_new`, `regime_optimizer_v2.py::_slab_tax`, `builders/itr1.py::_compute_tax` | Changes to slabs must be made in 3+ places |
| Rebate 87A logic | `regime_optimizer.py::_compute_old_regime/_compute_new_regime`, `regime_optimizer_v2.py::_compute`, `builders/itr1.py::_build_partb_tti` | Rebate thresholds scattered |
| Deduction limits | `regime_optimizer.py`, `deductions_computer.py`, `builders/validator.py` | Same limits defined in 3 files |
| Standard deduction amounts | `salary_computer.py`, `regime_optimizer.py`, `regime_optimizer_v2.py` | ₹50K/₹75K values in 3 files |
| CG classification call | `regime_optimizer_v2.py::_cg_summary` lazy-imports classifier; `api/routes.py` also calls classifier directly | Dual instantiation paths |
| 112A exemption application | `classifier.py::apply_112a_exemption`, `builders/itr_json_builder.py::_build_schedule_112a` | Exemption logic in two places |

---

## 16. Missing Abstractions

| Missing Abstraction | Why Needed | Where It Would Live |
|--------------------|------------|---------------------|
| `TaxRule` base class/interface | Extensibility for new FYs, regimes, rule types | `engine/rules/` |
| `RuleRepository` | FY/regime-indexed rule lookup | `engine/rules/repository.py` |
| `BaseITRBuilder` | Common interface for ITR-1 through ITR-7 builders | `builders/base.py` |
| `TaxComputationPipeline` | Explicit step ordering with pluggable stages | `engine/pipeline.py` |
| `DataProvider` (formalized) | Abstract over PDF vs API vs AA data sources | `providers/base.py` (partially exists) |
| `FinancialYear` domain type | Typesafe FY handling throughout | `models/tax.py` |
| `TaxYearConfig` | Single source for FY-specific constants | `config/tax_years/` |
| `AuditTrail` | Immutable computation record | `engine/audit.py` |
| `ValidationRule` registry | Pluggable validation rules | `builders/validation_rules.py` (refactor from validator.py) |

---

## 17. Scalability Risks

| Risk | Current State | Threshold | Mitigation |
|------|---------------|-----------|------------|
| In-memory sessions | Python dict, 24h TTL | ~10K concurrent sessions → memory exhaustion | Migrate to Redis (AD-005) |
| Single process | One Uvicorn worker | Filing season traffic spike | Add workers; containerize with auto-scaling |
| Raw SQL | No connection pooling config visible | High concurrency → connection exhaustion | Add connection pool sizing; migrate to SQLAlchemy |
| No caching | Tax slab constants computed per request | Trivial now; matters at scale | Add FY config cache layer |
| PDF processing in request thread | Synchronous pikepdf/pdfplumber in route handler | Large PDFs (>5MB) block the event loop | Offload to background task queue (Celery) |

---

## 18. Security Risks

| Risk | Severity | Detail |
|------|----------|--------|
| Dev JWT secret default | Medium | `taxstox-dev-secret-change-in-production` — if env var not set in prod |
| PDFs written to disk temporarily | Low | `tempfile.NamedTemporaryFile` used; `unlink(missing_ok=True)` called |
| No rate limiting on upload | Medium | Upload endpoint unprotected; could be abused |
| PAN in logs | Low | `logger.info(f"PARSED with pwd={pwd}")` — password logged, which may be PAN-based |
| SQL injection via raw SQL | Low | All queries use parameterized `%s` placeholders correctly |
| CORS wide open | Low | Methods `["*"]`, headers `["*"]` — standard for API; origins are restricted |

---

## 19. Testing Gaps

| Gap | Current State | Required State |
|-----|---------------|----------------|
| Unit tests | 0 unit tests | pytest for every engine, parser, builder module |
| Integration tests | 0 integration tests | Test pipeline: parse real PDFs → classify → optimize → build → validate |
| Regression tests | 0 regression tests | Golden-file tests: known inputs → expected ITR JSON |
| Tax computation tests | 0 | Deterministic test vectors: known income → known tax per regime |
| Edge case tests | 0 | Multi-employer, capital losses, carry-forward, NRI, senior citizen |
| Validation tests | 0 | Each of the 40+ validation rules should have pass + fail cases |
| API tests | 0 | HTTPX TestClient for all endpoints |
| E2E tests | 1 file (skeleton) | Full flow: upload PDFs → answer questions → download JSON |

---

## 20. Missing Capabilities

### 20.1 Missing Tax Components

- ITR-3 builder (business/profession income, full P&L, audit)
- ITR-4 builder (presumptive taxation 44AD/44ADA/44AE)
- ITR-5/6/7 builders (LLP, Company, Trust)
- Schedule FA (Foreign Assets) — needed for NRIs
- Schedule AL (Assets & Liabilities) — for high-income taxpayers
- Form 26AS parser (separate from AIS)
- Advance Tax + Interest 234A/B/C computation
- Capital loss carry-forward and set-off logic
- Agricultural income integration
- Crypto/VDA income (115BBH, 194S)
- Multiple Form 16s (job change mid-year)
- Belated + Revised return handling
- Senior citizen special provisions
- Presumptive taxation (44AD/44ADA/44AE)
- GST integration for business income

### 20.2 Missing Enterprise Components

- Multi-tenancy (CA firm managing multiple clients)
- Role-based access control (Taxpayer vs CA vs Admin)
- Audit trail (who changed what, when, why)
- API rate limiting
- API key management for enterprise clients
- Bulk filing (CA uploads 50+ client returns)
- White-label / embedded iframe
- Webhook notifications (filing status, refund credited)
- SLA monitoring
- DR/BCP plan

### 20.3 Missing AI Components

- Explainable AI: natural-language explanation of every computation
- AI-assisted document prefill beyond PDF parsing (OCR for scanned docs)
- Intelligent anomaly detection (unusual deductions, missing income)
- Predictive tax planning (what to do THIS year to save tax NEXT year)
- Natural language Q&A ("Should I switch to new regime?")
- Adaptive interview improvements (learn from user behavior patterns)
- Knowledge Graph of tax provisions, relationships, and conditions

### 20.4 Missing Platform Components

- Configuration management (feature flags, dynamic tax rates)
- Health check dashboard
- Monitoring + alerting (Prometheus/Grafana)
- CI/CD pipeline (automated tests on PR)
- Schema migration framework (Alembic)
- API versioning strategy
- Internationalization (Hindi + regional languages)
- Accessibility compliance (WCAG 2.1)

---

## 21. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Filing season surge crashes server | Medium (Jul-Sep) | High — users can't file | Horizontal scaling before Jul 2026 |
| Finance Act 2026 changes break hardcoded rules | High (Feb 2026 budget) | High — system produces wrong tax | Extract rules to versioned config before Feb 2026 |
| ITD portal changes schema | Medium | Medium — JSON rejected | Monitor ITD notifications; schema versioning |
| Neon PostgreSQL free tier limit reached | Low (current usage) | Medium — service disruption | Monitor usage; upgrade plan before limits hit |
| Render free tier sleep | Low (keep-alive cron active) | Low — cold start delay | Cron is working; upgrade if it fails |
| Dependency vulnerability (pikepdf, pdfplumber) | Low | Medium | Regular dependency scanning; update cadence |
| Single developer bus factor | High | Critical — knowledge concentrated | Documentation, tests, multiple contributors |

---

## 22. Unknowns

1. **Actual user count and usage patterns:** No analytics integration visible
2. **Production error rate:** No Sentry/error tracking configured
3. **PDF format variations:** Form 16/AIS formats vary by employer/issuer — unknown coverage
4. **ITR-3/4 demand:** Unknown how many users need business income support
5. **Schedule CG Section F exact portal behavior:** The date range sum validation is learned empirically
6. **25+ additional AIS codes:** Not all SFT codes have been encountered in real PDFs
7. **DeepSeek API reliability:** Used for tax updates summarization; fallback exists but quality drops

---

## 23. Assumptions

1. **AIS PDF password is always PAN(lower) + DOB(DDMMYYYY):** True for ITD-generated PDFs; may not hold for other issuers
2. **Form 16 follows standard TRACES format:** Employer-generated PDFs may deviate
3. **Single employer per FY:** The current implementation assumes one Form 16
4. **No business income:** ITR-3/4 not yet built
5. **Indian resident taxpayers only:** No NRI-specific handling
6. **English language only:** No i18n infrastructure
7. **FY2025-26 tax rules are stable:** Finance Act 2025 has been passed; rules won't change mid-year

---

## 24. Questions Requiring Clarification

1. **ERI License Status:** Does TaxStox have or plan to obtain an e-Return Intermediary license from ITD? This affects direct API access to ITD systems.

2. **Account Aggregator FIU Registration:** Is TaxStox registered as a Financial Information User under the AA framework? This determines whether AIS/26AS can be fetched via API.

3. **Data Retention Policy:** What is the legal basis for storing PAN/Aadhaar/Financial data? DPDP Act 2023 requirements?

4. **Business Model:** B2C (direct to taxpayers), B2B (CA firms), or both? This determines multi-tenancy and enterprise feature priorities.

5. **Mobile App Priority:** The ARCHITECTURE.md mentions React Native — is this an active initiative?

6. **Production Database Backup Strategy:** Is the Neon PostgreSQL database being backed up? Point-in-time recovery configured?

7. **Incident Response Plan:** Is there a documented process for security incidents or data breaches?

8. **Geographic Scope:** India-only or does the platform plan to support NRIs in other countries (US, UAE, UK, etc.)?

---

## 25. Module Health Scores

| Module | Completeness | Test Coverage | Documentation | Debt Count | Health |
|--------|-------------|---------------|---------------|------------|--------|
| `models/` | 🟢 High | 🔴 None | 🟢 Good (docstrings) | 0 | 🟡 Fair |
| `parsers/` | 🟢 High | 🔴 None | 🟡 Partial | 1 | 🟡 Fair |
| `engine/classifier.py` | 🟢 High | 🔴 None | 🟢 Good | 0 | 🟡 Fair |
| `engine/regime_optimizer*.py` | 🟢 High (v2) | 🔴 None | 🟡 Partial | 3 | 🔴 Poor |
| `engine/salary_computer.py` | 🟢 High | 🔴 None | 🟢 Good | 0 | 🟡 Fair |
| `engine/deductions_computer.py` | 🟢 High | 🔴 None | 🟢 Good | 0 | 🟡 Fair |
| `engine/questions.py` | 🟢 High | 🔴 None | 🟢 Good | 0 | 🟡 Fair |
| `engine/recommendation_engine.py` | 🟢 High | 🔴 None | 🟢 Good | 0 | 🟡 Fair |
| `builders/` | 🟢 ITR-1+2 done | 🔴 None | 🟡 Partial | 2 | 🟡 Fair |
| `api/routes.py` | 🟢 Complete | 🔴 None | 🟡 Partial | 1 | 🟡 Fair |
| `auth/` | 🟢 Complete | 🔴 None | 🟢 Good | 1 | 🟡 Fair |
| `db/` | 🟢 Complete | 🔴 None | 🟡 Partial | 1 | 🟡 Fair |
| `providers/` | 🟢 Complete | 🔴 None | 🟢 Good | 0 | 🟢 Good |
| `utils/` | 🟢 Complete | 🔴 None | 🟡 Partial | 0 | 🟡 Fair |

---

*End of Architecture Recovery Report v1.0*

*This report captures the system as it exists on 2026-07-05. No recommendations are made in this document — those follow in the Gap Analysis and Modernization Roadmap.*
