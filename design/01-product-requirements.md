# 01 — Product & Functional Requirements

> **Parent:** [00-README.md](00-README.md) | **Next:** [02 Non-Functional Requirements](02-non-functional-requirements.md)

---

## 1. Product Requirements Document (PRD)

### 1.1 Problem Statement

Filing Income Tax Returns in India is painful. The average salaried taxpayer spends 4-6 hours gathering documents, understanding forms, manually entering data, and navigating the ITD e-filing portal. Even with existing "tax filing" software (ClearTax, TaxBuddy, etc.), users still fill lengthy forms, manually classify income, and miss deductions worth thousands of rupees.

Existing tools are **form-fillers with a UI wrapper** — they don't understand documents, don't optimize taxes, don't validate intelligently, and don't converse naturally. They are digital versions of paper forms.

### 1.2 Solution Overview

TaxStox is an AI-native tax platform where:

1. User uploads **2 PDFs** (Form 16 + AIS) — or as few as zero documents
2. AI **extracts** all financial data automatically
3. AI **validates** against 26AS/TIS/other sources
4. AI **asks** only the ~5 most critical clarifying questions
5. AI **optimizes** by comparing every legal tax scenario
6. AI **generates** a filing-ready ITR JSON
7. User **downloads** and uploads to ITD portal in < 10 minutes

The experience should feel like **chatting with an expert Chartered Accountant** — not filling a form.

### 1.3 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time-to-file (with documents) | < 120 seconds | Median from upload start to JSON download |
| Questions per filing session | ≤ 8 questions | Median across all completed filings |
| Deduction coverage rate | 100% of legally applicable | % of deductions the system can discover |
| User satisfaction | NPS ≥ 60 | Post-filing survey |
| Error rate (JSON rejection by ITD) | < 0.5% | % of generated JSONs rejected on upload |
| Refund accuracy | ±₹500 vs CA-prepared | Comparison study |
| Abandonment rate | < 15% | % of started filings not completed |
| Support tickets per filing | < 0.2 | Tickets / completed filings |

### 1.4 Scope Boundaries

**IN SCOPE:**
- Individual (non-business) taxpayers — ITR-1, ITR-2, ITR-3, ITR-4
- Salary income, house property, capital gains, other sources
- All Chapter VI-A deductions (80C, 80D, 80E, 80G, 80TTA, 80TTB, etc.)
- Old vs New regime comparison
- Exemptions (HRA, LTA, etc.)
- Carry-forward losses
- Advance tax and self-assessment tax
- Foreign income (for ITR-2/3)
- Agricultural income
- Presumptive income (44AD, 44ADA)
- Revised returns (139(5))
- Belated returns (139(4))

**OUT OF SCOPE (V1):**
- Business/profession income with P&L (full ITR-3 complexity)
- Audit cases (44AB)
- Trusts, HUFs, companies, LLPs
- International taxation (DTAA, FTC)
- Transfer pricing
- GST filing
- Tax notice legal representation
- Physically disabled taxpayer special provisions (80U, 80DD — can be added later)

### 1.5 Competitive Differentiation

| Feature | ClearTax | TaxBuddy | Quicko | **TaxStox** |
|---------|----------|----------|--------|-------------|
| Document auto-extraction | Partial | No | Partial | **Full AI — all document types** |
| AI conversation | No | No | No | **Natural language, adaptive** |
| Regime optimization | Manual | Manual | Basic | **Exhaustive scenario analysis** |
| Cross-document validation | No | No | No | **Multi-source reconciliation** |
| Deduction discovery | Checklist | Checklist | Checklist | **Proactive AI discovery** |
| Minimum questions | 30-50 | 40-60 | 25-40 | **≤ 8 adaptive questions** |
| ITR JSON generation | Yes | Yes | Yes | **Yes + schema validation** |
| Error explanation | Generic | Generic | Generic | **Plain-English with root cause** |
| Audit support | No | No | No | **Audit trail + notice response** |

---

## 2. Functional Requirements

### FR-1: Document Ingestion

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | System shall accept PDF uploads via drag-and-drop or file browser | P0 |
| FR-1.2 | System shall accept JPEG/PNG uploads (scanned documents) with automatic OCR | P1 |
| FR-1.3 | System shall validate file format and reject unsupported types with clear error | P0 |
| FR-1.4 | System shall enforce file size limits (10MB per file, configurable) | P0 |
| FR-1.5 | System shall detect and handle password-protected PDFs | P0 |
| FR-1.6 | System shall auto-attempt PAN (lowercase) as PDF password | P1 |
| FR-1.7 | System shall allow manual password entry for PDFs | P0 |
| FR-1.8 | System shall handle multi-page PDFs (up to 100 pages) | P0 |
| FR-1.9 | System shall accept bulk upload (multiple PDFs simultaneously) | P1 |
| FR-1.10 | System shall show upload progress with estimated processing time | P1 |
| FR-1.11 | System shall support resume of interrupted uploads | P2 |
| FR-1.12 | System shall detect duplicate document uploads by content hash | P1 |

### FR-2: Document Classification

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | System shall automatically classify uploaded documents into known categories | P0 |
| FR-2.2 | System shall classify documents even when filename is non-descriptive | P0 |
| FR-2.3 | System shall detect if a document contains multiple document types (e.g., combined PDF) | P1 |
| FR-2.4 | System shall ask user to confirm classification when confidence < 95% | P0 |
| FR-2.5 | System shall support manual document type override | P1 |
| FR-2.6 | System shall detect the issuing entity from document content | P2 |
| FR-2.7 | System shall verify document belongs to the logged-in taxpayer | P0 |
| FR-2.8 | System shall flag documents that appear tampered or modified | P1 |

### FR-3: Entity Extraction

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | System shall extract all financial entities from classified documents | P0 |
| FR-3.2 | System shall extract identity entities: PAN, Name, DOB, Aadhaar (masked) | P0 |
| FR-3.3 | System shall extract income entities: Salary, Allowances, Perquisites, Other income | P0 |
| FR-3.4 | System shall extract deduction entities: All 80C/80D/80G/etc. components | P0 |
| FR-3.5 | System shall extract TDS entities: TAN, amount, section, challan details | P0 |
| FR-3.6 | System shall extract capital gains: ISIN, purchase/sale date, cost, sale value | P0 |
| FR-3.7 | System shall extract interest income from all sources | P0 |
| FR-3.8 | System shall extract rental income and municipal tax details | P0 |
| FR-3.9 | System shall assign confidence scores to every extracted entity | P0 |
| FR-3.10 | System shall flag entities with confidence < 90% for user verification | P0 |
| FR-3.11 | System shall extract tabular data from PDFs (e.g., salary breakup tables) | P0 |
| FR-3.12 | System shall handle multi-language documents (English + Hindi numeric) | P2 |

### FR-4: Cross-Document Validation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | System shall cross-validate PAN across all uploaded documents | P0 |
| FR-4.2 | System shall cross-validate name and DOB across documents | P0 |
| FR-4.3 | System shall cross-validate TDS amounts: Form 16 vs Form 26AS/AIS | P0 |
| FR-4.4 | System shall cross-validate salary figures across Form 16 and salary slips | P1 |
| FR-4.5 | System shall cross-validate interest income against bank statements | P1 |
| FR-4.6 | System shall detect and flag mismatches with severity levels | P0 |
| FR-4.7 | System shall recommend resolution strategies for each mismatch | P0 |
| FR-4.8 | System shall reconcile AIS/TIS data with user-provided documents | P0 |
| FR-4.9 | System shall detect unreported income present in AIS but not in Form 16 | P0 |

### FR-5: Adaptive Questionnaire

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | System shall generate questions only for information not extractable from documents | P0 |
| FR-5.2 | System shall adapt questions based on taxpayer profile and extracted data | P0 |
| FR-5.3 | System shall present questions one at a time with progress indication | P0 |
| FR-5.4 | System shall minimize total questions — target ≤ 8 per session | P0 |
| FR-5.5 | System shall never ask questions already answered by documents | P0 |
| FR-5.6 | System shall allow user to skip non-critical questions | P1 |
| FR-5.7 | System shall allow user to go back and revise previous answers | P0 |
| FR-5.8 | System shall save progress and allow session resumption | P0 |
| FR-5.9 | System shall explain WHY each question is being asked (context) | P1 |
| FR-5.10 | System shall support free-text answers in addition to structured options | P1 |
| FR-5.11 | System shall validate answers in real-time (e.g., PAN format, amount ranges) | P0 |
| FR-5.12 | System shall detect contradictory answers and flag for resolution | P0 |

### FR-6: Tax Computation & Optimization

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-6.1 | System shall compute tax under BOTH Old Regime and New Regime (115BAC) | P0 |
| FR-6.2 | System shall compute tax for every permutation of deduction choices | P1 |
| FR-6.3 | System shall identify all applicable deductions based on extracted data | P0 |
| FR-6.4 | System shall identify all applicable exemptions (HRA, LTA, etc.) | P0 |
| FR-6.5 | System shall identify all applicable rebates (87A) | P0 |
| FR-6.6 | System shall identify all applicable credits (TDS, TCS, Advance Tax, FTC) | P0 |
| FR-6.7 | System shall compute carry-forward and set-off of losses | P0 |
| FR-6.8 | System shall compute interest under sections 234A, 234B, 234C | P0 |
| FR-6.9 | System shall compute late filing fees under 234F | P0 |
| FR-6.10 | System shall recommend the optimal regime with tax saved | P0 |
| FR-6.11 | System shall explain every component of the tax computation | P0 |
| FR-6.12 | System shall provide side-by-side regime comparison | P0 |
| FR-6.13 | System shall simulate "what-if" scenarios (e.g., "What if I invest ₹50K more in 80C?") | P1 |
| FR-6.14 | ALL tax calculations shall be performed by the deterministic Tax Rule Engine, not the AI | P0 |

### FR-7: ITR JSON Generation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-7.1 | System shall generate ITR JSON compliant with ITD schema for the relevant AY | P0 |
| FR-7.2 | System shall support ITR-1, ITR-2, ITR-3, ITR-4 JSON schemas | P0 |
| FR-7.3 | System shall validate generated JSON against ITD XSD/schema before download | P0 |
| FR-7.4 | System shall embed a cryptographic hash to detect tampering | P0 |
| FR-7.5 | System shall generate a human-readable computation summary alongside JSON | P0 |
| FR-7.6 | System shall provide JSON download with proper filename convention | P0 |
| FR-7.7 | System shall regenerate JSON when user revises data | P0 |
| FR-7.8 | System shall version ITR JSONs and retain last N versions | P1 |
| FR-7.9 | System shall provide post-export instructions specific to ITR type | P0 |

### FR-8: User Account & Profile

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-8.1 | System shall support PAN-based account creation | P0 |
| FR-8.2 | System shall verify PAN against NSDL/ITD database | P1 |
| FR-8.3 | System shall support email+password and OTP-based authentication | P0 |
| FR-8.4 | System shall maintain taxpayer profile across filing years | P0 |
| FR-8.5 | System shall allow profile data import from previous year's ITR JSON | P1 |
| FR-8.6 | System shall support multiple taxpayer profiles under one login (family) | P2 |
| FR-8.7 | System shall provide filing history with status tracking | P0 |
| FR-8.8 | System shall support account deletion with full data purge | P0 |

### FR-9: Compliance & Audit

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-9.1 | System shall generate a complete audit trail of all AI decisions | P0 |
| FR-9.2 | System shall log every data extraction with source document and confidence | P0 |
| FR-9.3 | System shall log every deduction claimed with supporting section and evidence | P0 |
| FR-9.4 | System shall flag high-risk positions (e.g., large refunds, unusual deductions) | P0 |
| FR-9.5 | System shall provide plain-English explanation of every tax position | P0 |
| FR-9.6 | System shall maintain compliance with ITD ERI guidelines | P0 |
| FR-9.7 | System shall generate notice-response assistance for common notices | P2 |

### FR-10: Security & Privacy

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-10.1 | All data in transit shall be encrypted with TLS 1.3 | P0 |
| FR-10.2 | All data at rest shall be encrypted with AES-256-GCM | P0 |
| FR-10.3 | PAN shall be stored using irreversible hashing (with salt) for indexing | P0 |
| FR-10.4 | All uploaded documents shall be purged within 24 hours of ITR generation | P0 |
| FR-10.5 | Extracted financial data shall be purged within 24 hours of ITR generation | P0 |
| FR-10.6 | System shall never store plaintext PAN-Aadhaar linkage data | P0 |
| FR-10.7 | System shall implement row-level encryption for PII fields in database | P0 |
| FR-10.8 | System shall maintain complete data processing logs for compliance | P0 |
| FR-10.9 | System shall support Data Subject Access Requests (DSAR) | P1 |

---

## 3. Feature Catalog (V1)

### Core Filing Flow
- F-001: Document Upload (FR-1.*)
- F-002: Document Classification (FR-2.*)
- F-003: Entity Extraction (FR-3.*)
- F-004: Cross-Document Validation (FR-4.*)
- F-005: Adaptive Questionnaire (FR-5.*)
- F-006: Tax Computation (FR-6.*)
- F-007: Regime Optimization (FR-6.*)
- F-008: ITR JSON Generation (FR-7.*)
- F-009: Post-Export Instructions (FR-7.9)

### Account & History
- F-010: User Registration & Auth (FR-8.*)
- F-011: Filing History Dashboard (FR-8.7)
- F-012: Taxpayer Profile (FR-8.4)

### Intelligence
- F-013: Deduction Discovery Engine (FR-6.3, 16-*)
- F-014: Scenario Simulator (FR-6.13)
- F-015: Compliance Risk Detection (FR-9.4)
- F-016: Audit Trail Generation (FR-9.1)

### Support
- F-017: Plain-English Tax Explanation (FR-9.5)
- F-018: Error Recovery (FR-1.7, 20-*)
- F-019: Expert Chat (P2)
- F-020: Notice Response Assistant (P2)

---

## 4. V2+ Feature Candidates

These are explicitly descoped for V1 but documented for future planning:

- Auto-filing via ERI API (submit directly to ITD without manual portal upload)
- Real-time AIS/26AS fetching via ITD API integration
- Advance tax planning and reminders
- Investment recommendations for tax saving
- Tax-loss harvesting for capital gains
- Multi-year tax planning
- Business/P&L income full support
- GST filing integration
- International taxation (DTAA claims, Foreign Tax Credit)
- Mobile native apps (iOS, Android)
- Voice-based tax assistant
- WhatsApp-based filing
- Family tax optimization (joint filing strategies)
- Tax notice legal response automation

---

*Next: [02 Non-Functional Requirements](02-non-functional-requirements.md)*
