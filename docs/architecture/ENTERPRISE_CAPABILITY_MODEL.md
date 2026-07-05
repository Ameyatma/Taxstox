# Enterprise Capability Model — AI-Powered Indian Tax Intelligence Platform

> **Status:** TARGET STATE DEFINITION
> **Date:** 2026-07-05
> **Author:** Enterprise Chief Architect
> **Purpose:** Define the complete set of capabilities an enterprise-grade tax platform must possess. This is the target against which the current platform will be measured in the Gap Analysis.
> **Principle:** First-principles design. No reference to current implementation.

---

## Table of Contents

1. [Capability Domains Overview](#1-capability-domains-overview)
2. [Domain 1: Identity & Access Management](#2-domain-1-identity--access-management)
3. [Domain 2: Taxpayer Management](#3-domain-2-taxpayer-management)
4. [Domain 3: Document Intelligence](#4-domain-3-document-intelligence)
5. [Domain 4: Income Management](#5-domain-4-income-management)
6. [Domain 5: Deduction & Exemption Management](#6-domain-5-deduction--exemption-management)
7. [Domain 6: Tax Computation Engine](#7-domain-6-tax-computation-engine)
8. [Domain 7: Regime Optimization](#8-domain-7-regime-optimization)
9. [Domain 8: Compliance & Validation](#9-domain-8-compliance--validation)
10. [Domain 9: ITR Generation & Filing](#10-domain-9-itr-generation--filing)
11. [Domain 10: Audit & Explainability](#11-domain-10-audit--explainability)
12. [Domain 11: Knowledge Management](#12-domain-11-knowledge-management)
13. [Domain 12: Rule Management](#13-domain-12-rule-management)
14. [Domain 13: AI Interview Engine](#14-domain-13-ai-interview-engine)
15. [Domain 14: Reporting & Analytics](#15-domain-14-reporting--analytics)
16. [Domain 15: Integration & External APIs](#16-domain-15-integration--external-apis)
17. [Domain 16: Administration & Operations](#17-domain-16-administration--operations)
18. [Domain 17: Security & Privacy](#18-domain-17-security--privacy)
19. [Domain 18: Notification & Communication](#19-domain-18-notification--communication)
20. [Domain 19: Tax Planning & Scenario Simulation](#20-domain-19-tax-planning--scenario-simulation)
21. [Domain 20: Enterprise Multi-Tenancy](#21-domain-20-enterprise-multi-tenancy)
22. [Bounded Context Map](#22-bounded-context-map)
23. [Cross-Cutting Capabilities](#23-cross-cutting-capabilities)
24. [Capability Dependency Matrix](#24-capability-dependency-matrix)

---

## 1. Capability Domains Overview

### 1.1 Domain Map

```
┌────────────────────────────────────────────────────────────────────┐
│                 ENTERPRISE TAX INTELLIGENCE PLATFORM                │
│                                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │IDENTITY &│  │TAXPAYER  │  │ DOCUMENT │  │     INCOME       │  │
│  │ ACCESS   │  │MANAGEMENT│  │INTELLIGENCE│  │   MANAGEMENT    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬──────────┘  │
│       │             │             │                  │             │
│  ┌────┴─────────────┴─────────────┴──────────────────┴──────────┐ │
│  │                    TAX COMPUTATION ENGINE                     │ │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐   │ │
│  │  │ SLAB TAX │  │ CAPITAL GAINS│  │ REGIME OPTIMIZATION  │   │ │
│  │  └──────────┘  └──────────────┘  └──────────────────────┘   │ │
│  └──────────────────────┬───────────────────────────────────────┘ │
│                         │                                         │
│  ┌──────────────────────┼───────────────────────────────────────┐ │
│  │          COMPLIANCE & VALIDATION         ┌──────────────┐    │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┤  ITR GEN &   │    │ │
│  │  │VALIDATION│  │   AIS    │  │   FORM   │   FILING     │    │ │
│  │  │  ENGINE  │  │RECONCILE │  │ 26AS VAL │              │    │ │
│  │  └──────────┘  └──────────┘  └──────────┘              │    │ │
│  └─────────────────────────────────────────────────────────┘    │ │
│                                                                  │ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │ │
│  │AUDIT &   │  │KNOWLEDGE │  │  RULE    │  │  AI INTERVIEW    │ │ │
│  │EXPLAIN   │  │  GRAPH   │  │MANAGEMENT│  │     ENGINE       │ │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │ │
│                                                                  │ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │ │
│  │REPORTING │  │INTEGRATION│  │  ADMIN & │  │   SECURITY &    │ │ │
│  │& ANALYTICS│ │ & APIs   │  │OPERATIONS│  │    PRIVACY      │ │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │ │
│                                                                  │ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │ │
│  │NOTIFICATN│  │TAX PLAN &│  │ENTERPRISE│  │                  │ │ │
│  │  SYSTEM  │  │SIMULATION│  │MULTI-TEN.│  │                  │ │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │ │
└────────────────────────────────────────────────────────────────────┘
```

### 1.2 Capability Count by Domain

| Domain | Capabilities | Critical | High | Medium | Low |
|--------|-------------|----------|------|--------|-----|
| Identity & Access Management | 8 | 4 | 2 | 2 | 0 |
| Taxpayer Management | 7 | 2 | 3 | 2 | 0 |
| Document Intelligence | 10 | 4 | 4 | 2 | 0 |
| Income Management | 8 | 3 | 3 | 2 | 0 |
| Deduction & Exemption Management | 7 | 2 | 3 | 2 | 0 |
| Tax Computation Engine | 8 | 4 | 3 | 1 | 0 |
| Regime Optimization | 6 | 2 | 2 | 2 | 0 |
| Compliance & Validation | 9 | 4 | 3 | 2 | 0 |
| ITR Generation & Filing | 7 | 3 | 2 | 2 | 0 |
| Audit & Explainability | 6 | 3 | 2 | 1 | 0 |
| Knowledge Management | 6 | 2 | 2 | 2 | 0 |
| Rule Management | 7 | 3 | 2 | 2 | 0 |
| AI Interview Engine | 8 | 2 | 3 | 3 | 0 |
| Reporting & Analytics | 7 | 1 | 3 | 3 | 0 |
| Integration & External APIs | 8 | 2 | 3 | 3 | 0 |
| Administration & Operations | 8 | 2 | 3 | 3 | 0 |
| Security & Privacy | 10 | 5 | 3 | 2 | 0 |
| Notification & Communication | 5 | 1 | 2 | 2 | 0 |
| Tax Planning & Simulation | 5 | 0 | 2 | 3 | 0 |
| Enterprise Multi-Tenancy | 8 | 2 | 3 | 3 | 0 |
| **TOTAL** | **148** | **50** | **51** | **43** | **0** |

---

## 2. Domain 1: Identity & Access Management

### C1.1 — User Registration & Onboarding

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable taxpayers and professionals to create and verify accounts with identity proofing against government databases. |
| **Responsibilities** | Collect PAN, name, DOB, email, mobile; validate PAN format; verify identity against NSDL PAN API; verify email via OTP; verify mobile via OTP; establish initial trust level; prevent duplicate registrations; handle PAN-Aadhaar link verification |
| **Inputs** | PAN, Name, DOB, Email, Mobile, Password or OAuth token, Consent flags |
| **Outputs** | Verified user account, Initial trust level, Session token |
| **Dependencies** | NSDL PAN Verification API, Aadhaar e-KYC (UIDAI), Email service, SMS gateway, OAuth providers (Google, etc.) |
| **Business Value** | Foundation of trust; ensures only legitimate taxpayers use the system; reduces fraud |
| **Priority** | **Critical** |
| **Maturity Target** | PAN verification mandatory before any tax data processing; Aadhaar-based e-KYC for high-trust tier; Account Aggregator consent framework integration |

### C1.2 — Authentication

| Attribute | Value |
|-----------|-------|
| **Purpose** | Securely authenticate users across all access channels with appropriate strength based on action sensitivity. |
| **Responsibilities** | Password-based auth; OTP-based auth (email/SMS); OAuth 2.0 / OpenID Connect federation (Google, etc.); MFA for sensitive operations; session management with configurable TTL; token refresh; forced re-auth for high-risk actions; device fingerprinting |
| **Inputs** | Credentials (password/OTP/OAuth token), Device context, IP address, Action context |
| **Outputs** | JWT access token, Refresh token, Session context with claims |
| **Dependencies** | Email service, SMS gateway, OAuth providers, Token signing infrastructure |
| **Business Value** | Primary security control; protects taxpayer financial data from unauthorized access |
| **Priority** | **Critical** |
| **Maturity Target** | FIDO2/WebAuthn passkey support; biometric auth on mobile; adaptive MFA based on risk scoring |

### C1.3 — Authorization & Role-Based Access Control

| Attribute | Value |
|-----------|-------|
| **Purpose** | Control what each authenticated principal can see and do based on their role, tenant, and context. |
| **Responsibilities** | Define role hierarchy (Taxpayer, CA, CA-Staff, Admin, Super Admin); permission-to-role mapping; resource-level authorization; tenant-scoped access; just-in-time privilege elevation; audit of all authorization decisions |
| **Inputs** | User identity, Role assignments, Resource identifier, Action type, Tenant context |
| **Outputs** | Allow/Deny decision, Authorization context for downstream services |
| **Dependencies** | C1.2 Authentication, C20.1 Tenant Context |
| **Business Value** | Enables multi-stakeholder platform; prevents data leakage between taxpayers or CA firms |
| **Priority** | **Critical** |
| **Maturity Target** | Attribute-Based Access Control (ABAC) for fine-grained policies; policy-as-code with versioning |

### C1.4 — Session & Token Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Manage the lifecycle of user sessions and access tokens securely. |
| **Responsibilities** | Token issuance with appropriate TTL; refresh token rotation; token revocation on logout/password change/suspicious activity; session concurrency limits; device/session inventory for user visibility; forced session termination |
| **Inputs** | Authentication result, Device fingerprint, Session policy |
| **Outputs** | Access token, Refresh token, Session record, Token metadata |
| **Dependencies** | C1.2 Authentication, Token signing infrastructure |
| **Business Value** | Reduces window of token abuse; provides user visibility and control over active sessions |
| **Priority** | **High** |
| **Maturity Target** | OAuth 2.0 Token Binding; DPoP (Demonstration of Proof-of-Possession) tokens |

### C1.5 — Password & Credential Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Securely manage user credentials throughout their lifecycle. |
| **Responsibilities** | Password policy enforcement; secure password hashing (bcrypt/argon2); password reset flow with time-limited tokens; credential history to prevent reuse; breach notification on credential compromise; account lockout after threshold failures |
| **Inputs** | Password change/reset requests, Breach database feeds |
| **Outputs** | Updated credentials, Reset tokens, Security notifications |
| **Dependencies** | Email service, SMS gateway |
| **Business Value** | Defends against credential attacks; maintains user trust |
| **Priority** | **High** |
| **Maturity Target** | Passkey/FIDO2 as primary; password as fallback; breach credential monitoring via HaveIBeenPwned API |

### C1.6 — Profile Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable users to manage their own profile information. |
| **Responsibilities** | View/edit personal info (name, email, mobile, address); PAN change (requires re-verification); communication preferences; notification settings; language preference; theme preference; account linking (Google, etc.) |
| **Inputs** | Profile update requests, Verification documents for sensitive changes |
| **Outputs** | Updated profile, Audit log entry, Verification triggers |
| **Dependencies** | C1.1 Registration, C1.2 Authentication, C18 Notification System |
| **Business Value** | Reduces support burden; enables user self-service |
| **Priority** | **Medium** |
| **Maturity Target** | Self-service data export; account deletion with compliance holds |

### C1.7 — Account Recovery

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable legitimate users to regain access to their accounts securely. |
| **Responsibilities** | Email-based recovery; SMS-based recovery; knowledge-based verification; identity re-verification via PAN; recovery code generation; recovery attempt rate limiting; notification of recovery to primary contact |
| **Inputs** | Recovery request, Identity proof, Verification codes |
| **Outputs** | Account access restored, Audit log, Security notification |
| **Dependencies** | C1.1 Registration verification, Email service, SMS gateway |
| **Business Value** | Prevents permanent lockout; maintains platform accessibility |
| **Priority** | **Medium** |
| **Maturity Target** | Social recovery (trusted contacts); hardware token recovery |

### C1.8 — Consent Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Capture, store, and honor user consent for data processing per DPDP Act 2023 and IT Act requirements. |
| **Responsibilities** | Granular consent collection (purpose-specific); consent versioning; consent withdrawal; consent audit trail; consent expiry and renewal; proof of consent for regulatory compliance |
| **Inputs** | Consent choices, Purpose specifications, Regulatory requirements |
| **Outputs** | Consent records, Consent token, Compliance reports |
| **Dependencies** | C17.3 Data Privacy, C17.8 Compliance Framework |
| **Business Value** | Legal requirement under DPDP Act 2023; builds user trust; prevents regulatory penalties |
| **Priority** | **Critical** |
| **Maturity Target** | AA (Account Aggregator) consent framework; machine-readable consent receipts; consent dashboard |

---

## 3. Domain 2: Taxpayer Management

### C2.1 — Taxpayer Profile

| Attribute | Value |
|-----------|-------|
| **Purpose** | Maintain a comprehensive, verified taxpayer profile that serves as the single source of truth for all tax computations. |
| **Responsibilities** | Store and manage: PAN, name (as per PAN), DOB, gender, father's name, Aadhaar (masked), residential address, mobile, email; track verification status of each field; maintain profile version history; support profile data from multiple sources (user, PAN API, AIS, previous ITRs) |
| **Inputs** | Registration data, PAN verification response, AIS personal info section, Previous year ITR data |
| **Outputs** | VerifiedTaxpayerProfile, Field-level verification status, Profile change history |
| **Dependencies** | C1.1 Registration, C15.2 PAN Verification API, C4.7 Previous Year Data |
| **Business Value** | Eliminates re-entry; ensures consistency across filings; foundation for all downstream computation |
| **Priority** | **Critical** |
| **Maturity Target** | Auto-sync with PAN/Aadhaar databases; profile completeness scoring; change detection |

### C2.2 — Residential Status Determination

| Attribute | Value |
|-----------|-------|
| **Purpose** | Determine the taxpayer's residential status (ROR, RNOR, NR) per Section 6 of the Income Tax Act for each financial year. |
| **Responsibilities** | Evaluate days-in-India criteria; evaluate deemed resident criteria (new from FY2020-21); determine ROR/RNOR/NR status; apply tie-breaker rules for dual residents; store determination with evidence and rationale; flag borderline cases for professional review |
| **Inputs** | Travel history (passport/dates), Citizenship status, India-source income, Foreign tax residency proof |
| **Outputs** | ResidentialStatus determination, Detailed reasoning, Flag for professional review |
| **Dependencies** | C2.1 Taxpayer Profile, C11.2 Tax Provision Knowledge Base (Section 6) |
| **Business Value** | Critical — determines scope of taxable income; wrong status = fundamentally wrong return |
| **Priority** | **Critical** |
| **Maturity Target** | Automated passport/travel data ingestion; DTAA tie-breaker analysis; multi-year status comparison |

### C2.3 — Filing Status Determination

| Attribute | Value |
|-----------|-------|
| **Purpose** | Determine filing status: Individual, HUF, Senior Citizen (60-80), Super Senior Citizen (80+), Representative Assessee. |
| **Responsibilities** | Age-based senior citizen determination; HUF identification and Karta linking; representative assessee designation; filing status change detection year-over-year; applicable benefits based on filing status (higher basic exemption, deduction limits) |
| **Inputs** | DOB, HUF details, Representative assessee documentation |
| **Outputs** | FilingStatus, Applicable benefits (higher exemption limits, deduction thresholds) |
| **Dependencies** | C2.1 Taxpayer Profile, C11.2 Tax Provision Knowledge Base |
| **Business Value** | Determines applicable tax slabs, deduction limits, and ITR form eligibility |
| **Priority** | **High** |
| **Maturity Target** | Auto-detection from previous year filings; age auto-computation |

### C2.4 — ITR Form Eligibility

| Attribute | Value |
|-----------|-------|
| **Purpose** | Determine which ITR form(s) the taxpayer is eligible to file based on income sources, amount, and residency. |
| **Responsibilities** | Evaluate ITR-1 through ITR-7 eligibility criteria; detect disqualifying income types; auto-select most advantageous eligible form; explain why each ineligible form is unavailable; detect if taxpayer is filing wrong form (from previous year pattern) |
| **Inputs** | Income sources, Total income, Residential status, Business income type, Foreign assets |
| **Outputs** | Eligible ITR types, Recommended ITR type, Disqualification reasons per type |
| **Dependencies** | C2.2 Residential Status, C2.3 Filing Status, C4 Income Management, C11.2 Tax Provision Knowledge Base |
| **Business Value** | Prevents wrong-form rejection; optimizes for simplest eligible form |
| **Priority** | **High** |
| **Maturity Target** | Proactive form eligibility notification before filing season; ITR form rule change detection |

### C2.5 — Historical Filing Record

| Attribute | Value |
|-----------|-------|
| **Purpose** | Maintain a complete history of all tax filings for the taxpayer across financial years. |
| **Responsibilities** | Record each filing: FY, AY, ITR type, regime chosen, total income, tax paid, refund received, filing date, acknowledgement number; link returns across years; detect gaps (years not filed); detect amended/revised returns; provide filing history timeline |
| **Inputs** | Filing data from each completed return, ITD acknowledgement, Refund credit data |
| **Outputs** | FilingHistory, Unfiled year alerts, Carry-forward data (losses, unabsorbed depreciation) |
| **Dependencies** | C2.1 Taxpayer Profile, C9 ITR Generation & Filing, C4.7 Previous Year Data |
| **Business Value** | Enables carry-forward computations; demonstrates compliance history; annual re-filing accelerator |
| **Priority** | **High** |
| **Maturity Target** | Auto-import from ITD e-filing portal; cross-year analytics; compliance scoring |

### C2.6 — Family Unit Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Link related taxpayers (spouse, children, HUF members) for coordinated tax planning while maintaining individual filing. |
| **Responsibilities** | Define family relationships; enable shared view for CA managing family; support clubbing of income rules; coordinate deduction optimization across family members; support HUF partition scenarios |
| **Inputs** | Relationship declarations, PAN of related persons, Marriage/ birth records |
| **Outputs** | FamilyUnit, Shared dashboard (authorized), Clubbing recommendations |
| **Dependencies** | C2.1 Taxpayer Profile, C1.3 Authorization |
| **Business Value** | Enables holistic family tax planning; standard CA practice for HNI clients |
| **Priority** | **Medium** |
| **Maturity Target** | Automated clubbing detection; cross-member deduction optimization |

### C2.7 — Taxpayer Risk Profiling

| Attribute | Value |
|-----------|-------|
| **Purpose** | Assess risk level of taxpayer for compliance purposes — not for discrimination, but for appropriate due diligence and support. |
| **Responsibilities** | Analyze income patterns for anomalies; detect sudden income changes; identify high-risk indicators (large cash deposits, foreign transactions, crypto); compute risk score; flag for professional review when risk exceeds threshold |
| **Inputs** | Income history, AIS data, Transaction patterns, Previous scrutiny history |
| **Outputs** | RiskScore, RiskFactors, ProfessionalReviewFlag |
| **Dependencies** | C2.5 Historical Filing Record, C4 Income Management, C8.6 AIS Anomaly Detection |
| **Business Value** | Proactive compliance; reduces scrutiny risk for taxpayer; appropriate support escalation |
| **Priority** | **Medium** |
| **Maturity Target** | ML-based risk scoring trained on ITD scrutiny patterns; explainable risk factors |

---

## 4. Domain 3: Document Intelligence

### C3.1 — Multi-Format Document Ingestion

| Attribute | Value |
|-----------|-------|
| **Purpose** | Accept tax documents in any format (PDF, scanned image, JSON, CSV, XML) from any source (upload, email, API, AA framework). |
| **Responsibilities** | File type detection and validation; format conversion to canonical representation; multi-file batch upload; large file handling (>50MB); password-protected file detection; file integrity verification; virus/malware scanning |
| **Inputs** | Files in various formats, Upload metadata (source, purpose, taxpayer context) |
| **Outputs** | Canonical document representation, Format metadata, Password requirement flag |
| **Dependencies** | C17.4 Data Encryption, C17.7 Malware Scanning |
| **Business Value** | Eliminates format friction; accepts documents however the taxpayer has them |
| **Priority** | **Critical** |
| **Maturity Target** | 50+ format support; auto-format detection without file extension reliance |

### C3.2 — PDF Password Resolution

| Attribute | Value |
|-----------|-------|
| **Purpose** | Intelligently decrypt password-protected PDFs without burdening the user. |
| **Responsibilities** | Knowledge base of common password patterns (PAN variants, DOB variants, employer defaults); automatic password derivation from taxpayer profile (PAN + DOB); multi-candidate trial with rate limiting; user prompt only when all candidates fail; password hint extraction from document metadata |
| **Inputs** | Encrypted PDF, Taxpayer PAN, Taxpayer DOB, Employer information |
| **Outputs** | Decrypted PDF bytes, Password used (for session reuse), PasswordRequired flag |
| **Dependencies** | C2.1 Taxpayer Profile, C3.1 Document Ingestion |
| **Business Value** | Major UX win — AIS password is formulaic; users should never type it |
| **Priority** | **High** |
| **Maturity Target** | ML-based password pattern learning from successful resolutions; employer-specific password databases |

### C3.3 — Form 16 Parser

| Attribute | Value |
|-----------|-------|
| **Purpose** | Extract all structured data from Form 16 PDFs (TRACES-generated and employer-generated) with high accuracy. |
| **Responsibilities** | Parse Part A (employer/employee identity, TDS, quarterly breakdown); parse Part B (salary breakup, Section 10 exemptions, Section 16 deductions, Chapter VI-A, tax computation); parse Annexure (salary components with amounts); parse Form 12BA (perquisites detail — 21 categories); handle multi-page Form 16; handle TRACES format variations; handle employer-generated non-standard formats; confidence scoring per extracted field |
| **Inputs** | Decrypted Form 16 PDF |
| **Outputs** | Structured Form16Data with field-level confidence scores, Extraction warnings |
| **Dependencies** | C3.2 PDF Password Resolution, C3.5 OCR Pipeline (for scanned Form 16) |
| **Business Value** | Eliminates manual salary data entry; captures employer-computed deductions that taxpayer may not know |
| **Priority** | **Critical** |
| **Maturity Target** | >99% field extraction accuracy for TRACES format; >95% for employer-generated; ML-based field mapping for unknown formats |

### C3.4 — AIS Parser

| Attribute | Value |
|-----------|-------|
| **Purpose** | Extract all financial transaction data from Annual Information Statement PDF with complete coverage of all TDS and SFT codes. |
| **Responsibilities** | Parse Part A (personal info); parse Part B1 (TDS entries — all 20+ information codes); parse Part B2 (SFT entries — savings interest, term deposits, equity MF sales, other unit sales, securities purchases, dividends, immovable property, cash deposits, foreign remittance, etc.); parse Part B3 (tax payments); parse Part B4 (refunds); parse Part B7 (Annexure II salary); handle table extraction with column-adaptive parsing; handle multi-page SFT tables with merged cells |
| **Inputs** | Decrypted AIS PDF |
| **Outputs** | Structured AISData with all financial transactions, Field-level confidence scores, Unrecognized code warnings |
| **Dependencies** | C3.2 PDF Password Resolution, C3.6 AIS Code Classification |
| **Business Value** | Captures ALL reported financial transactions; eliminates manual AIS review; catches income taxpayer may have forgotten |
| **Priority** | **Critical** |
| **Maturity Target** | 100% AIS information code coverage; AIS JSON API integration (when available from ITD); automatic quarterly AIS refresh |

### C3.5 — OCR Pipeline

| Attribute | Value |
|-----------|-------|
| **Purpose** | Extract text and structured data from non-digital documents (scanned PDFs, photographs, paper documents). |
| **Responsibilities** | Image pre-processing (deskew, denoise, contrast enhancement); OCR engine integration (Tesseract, Google Vision, Azure OCR); table structure recognition; handwriting recognition for manual entries; multi-language OCR (English, Hindi, regional languages on government forms); confidence scoring per extracted segment; human review queue for low-confidence extractions |
| **Inputs** | Scanned images, Non-searchable PDFs, Photographs of documents |
| **Outputs** | Extracted text with positional data, Structured fields, Confidence scores, Review flags |
| **Dependencies** | C3.1 Document Ingestion, C17.4 Data Encryption (documents contain PII) |
| **Business Value** | Enables processing of older documents, paper Form 16s, rent receipts, investment proofs that lack digital equivalents |
| **Priority** | **High** |
| **Maturity Target** | >95% accuracy on printed Indian government forms; >85% on handwriting; continuous model improvement from review feedback |

### C3.6 — AIS Code Classification

| Attribute | Value |
|-----------|-------|
| **Purpose** | Map every AIS information code to its correct ITR schedule, field, and tax treatment. |
| **Responsibilities** | Maintain complete code-to-schedule mapping for all TDS codes (192, 194A, 194I, 194J, 194H, 194C, 194D, 194G, 194K, 195, 192A, 194B, 194BB, 194IA, 194IB, 194N, 194O, 194S, etc.); maintain SFT code mapping (001-018); determine income type (salary, interest, capital gains, rent, professional, other); determine whether TDS is claimable; determine applicable ITR schedule and field; handle code variants and format differences across AIS versions |
| **Inputs** | AIS information codes, Transaction metadata |
| **Outputs** | ITR schedule assignment, Income type classification, TDS claimability flag |
| **Dependencies** | C12.3 Rule Repository (code mapping rules by FY), C3.4 AIS Parser |
| **Business Value** | Ensures every reported transaction flows to the correct ITR schedule; completeness of income capture |
| **Priority** | **Critical** |
| **Maturity Target** | Auto-updating code map from ITD schema changes; coverage of 100% of known codes; unknown code alerting |

### C3.7 — Form 26AS Parser

| Attribute | Value |
|-----------|-------|
| **Purpose** | Extract tax credit data from Form 26AS (TRACES) for TDS reconciliation. |
| **Responsibilities** | Parse Form 26AS PDF/JSON; extract all TDS entries by deductor; extract TCS entries; extract advance tax payments; extract self-assessment tax payments; extract refund details; reconcile tax credits against claimed amounts |
| **Inputs** | Form 26AS PDF/JSON, TRACES API data (when available) |
| **Outputs** | Structured Form26ASData, TDS credit summary, Unmatched entries |
| **Dependencies** | C3.2 PDF Password Resolution, C15.3 TRACES API Integration |
| **Business Value** | Three-way TDS reconciliation (Form 16 ↔ AIS ↔ 26AS); prevents CPC TDS credit denial |
| **Priority** | **High** |
| **Maturity Target** | Direct TRACES API integration; automatic 26AS fetch; real-time TDS credit verification |

### C3.8 — Broker Statement Parser

| Attribute | Value |
|-----------|-------|
| **Purpose** | Parse capital gains trade statements from all major Indian brokerages and mutual fund platforms. |
| **Responsibilities** | Support Zerodha (tradebook CSV, tax P&L CSV); Support Groww, Upstox, Angel One, ICICI Direct, HDFC Securities, Kotak Securities, 5paisa; Support CAMS, KFintech (mutual fund statements); extract trade date, ISIN, security name, quantity, buy price, sell price, STT, charges; classify holding period (short/long term); compute capital gain/loss per trade; handle corporate actions (bonus, split, merger) |
| **Inputs** | Broker CSV/PDF statements, CAMS/KFintech statement PDFs |
| **Outputs** | Standardized TradeEntry list, Computed gains/losses, Holding period classification |
| **Dependencies** | C3.1 Document Ingestion, C5.2 Capital Gains Classification |
| **Business Value** | Eliminates manual capital gains computation; critical for active traders and investors |
| **Priority** | **High** |
| **Maturity Target** | 15+ broker support; auto-detection of broker from file format; corporate action handling |

### C3.9 — Investment Proof Parser

| Attribute | Value |
|-----------|-------|
| **Purpose** | Extract deduction-related information from investment proof documents. |
| **Responsibilities** | Parse PPF passbook/passbook entries; parse LIC premium receipts; parse ELSS statements; parse health insurance premium receipts; parse rent receipts; parse home loan interest certificates; parse tuition fee receipts; parse donation receipts (80G); parse NPS contribution statements |
| **Inputs** | Investment proof documents (PDF, image, scanned) |
| **Outputs** | Structured deduction evidence, Amount extracted, Date range, Issuing institution |
| **Dependencies** | C3.5 OCR Pipeline, C6 Deduction & Exemption Management |
| **Business Value** | Reduces manual entry of deduction proofs; creates digital evidence trail for potential scrutiny |
| **Priority** | **Medium** |
| **Maturity Target** | 10+ document type support; direct integration with financial institutions for auto-fetch |

### C3.10 — Document Validation & Fraud Detection

| Attribute | Value |
|-----------|-------|
| **Purpose** | Validate document authenticity and detect potential tampering or fraud. |
| **Responsibilities** | Digital signature verification on PDFs; metadata analysis (creation date, modification history); consistency check (document PAN matches taxpayer PAN, employer TAN valid format); structural validation (known TRACES/ITD template matching); tampering detection (font inconsistencies, image manipulation); duplicate document detection |
| **Inputs** | Uploaded documents, Document metadata, Known-good templates |
| **Outputs** | AuthenticityScore, TamperingFlags, ValidationWarnings |
| **Dependencies** | C3.1 Document Ingestion, C17 Security & Privacy |
| **Business Value** | Reduces fraud risk; protects platform from being used to file with forged documents |
| **Priority** | **Medium** |
| **Maturity Target** | ML-based forgery detection; integration with issuing authority verification APIs |

---

## 5. Domain 4: Income Management

### C4.1 — Salary Income Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute income under the head "Salaries" per Sections 15-17 for any financial year. |
| **Responsibilities** | Compute gross salary (17(1) + 17(2) + 17(3)); apply Section 10 exemptions (HRA 10(13A), LTA 10(5), gratuity 10(10), leave encashment 10(10AA), commuted pension 10(10A), child education 10(14), hostel allowance 10(14), special allowances 10(14)); apply Section 16 deductions (standard deduction 16(ia), entertainment allowance 16(ii), professional tax 16(iii)); handle multi-employer scenario (job change during FY); handle salary from foreign employer (for RNOR/NR); compute perquisite valuation per Rule 3 |
| **Inputs** | Form 16 data (per employer), Salary slips, AIS TDS-192 data, Residential status, FY |
| **Outputs** | IncomeUnderHeadSalaries, PerEmployer breakdown, Exemption details, Perquisite valuation |
| **Dependencies** | C2.2 Residential Status, C3.3 Form 16 Parser, C12.3 Rule Repository (S10, S16, Rule 3) |
| **Business Value** | Most common income head; must be computed correctly for vast majority of taxpayers |
| **Priority** | **Critical** |
| **Maturity Target** | All 21 perquisite types valued per Rule 3; multi-employer auto-merge; foreign salary handling |

### C4.2 — House Property Income Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute income under the head "Income from House Property" per Sections 22-27. |
| **Responsibilities** | Determine property type (self-occupied, let-out, deemed let-out); compute Gross Annual Value for let-out properties; compute municipal taxes deduction; compute standard deduction (30% of NAV); compute interest deduction (Section 24(b) — ₹2L self-occupied, unlimited let-out); handle pre-construction interest (5-year amortization); handle co-ownership scenarios; handle vacancy allowance; handle unrealized rent; handle arrears of rent |
| **Inputs** | Property details (address, ownership share, type), Rental income, Municipal tax paid, Home loan interest certificate, Loan sanction date, Possession date |
| **Outputs** | IncomeFromHouseProperty (per property), Loss from house property, Carry-forward loss |
| **Dependencies** | C2.1 Taxpayer Profile, C3.9 Investment Proof Parser, C12.3 Rule Repository (S22-27) |
| **Business Value** | Second most common income/loss head; home loan deduction is major tax planning tool |
| **Priority** | **High** |
| **Maturity Target** | Multi-property portfolio management; automated Section 24 optimization; co-ownership split computation |

### C4.3 — Business & Profession Income Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute income under the head "Profits and Gains of Business or Profession" per Sections 28-44DB. |
| **Responsibilities** | Support regular books of accounts (full P&L + balance sheet); support presumptive taxation (44AD — 8%/6% of turnover, 44ADA — 50% of gross receipts, 44AE — per-tonne for transport); compute depreciation per Section 32 (block of assets, WDV method, additional depreciation); handle disallowances (40A(2), 40A(3), 40(a)(ia), 43B); compute deduction for SEZ units (10AA); handle inventory valuation; handle audit requirement determination (44AB turnover threshold); GST reconciliation with turnover |
| **Inputs** | P&L statement, Balance sheet, Turnover/Gross receipts, Asset register, GST returns, TDS details |
| **Outputs** | IncomeFromBusinessProfession, Depreciation schedule, Disallowance details, Audit requirement flag |
| **Dependencies** | C12.3 Rule Repository (S28-44DB), C8.4 GST Reconciliation |
| **Business Value** | Required for ITR-3 and ITR-4; serves self-employed professionals, freelancers, small businesses |
| **Priority** | **High** |
| **Maturity Target** | Full presumptive + regular computation; auto-depreciation schedule from asset register; GST auto-reconciliation |

### C4.4 — Capital Gains Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute capital gains for all asset classes with correct holding period, indexation, exemption, and tax rate per Sections 45-55A. |
| **Responsibilities** | Classify assets (listed equity, unlisted equity, equity MF, debt MF, gold ETF, silver ETF, REIT/InVIT, immovable property, bonds/debentures, crypto/VDAs, foreign assets, ESOP/RSU); determine holding period (listed equity: 12mo, unlisted equity: 24mo, immovable: 24mo, others: 36mo); compute cost of acquisition; compute indexed cost (CII table by FY, only for specified assets); compute cost of improvement; apply exemptions (54 — residential property, 54EC — specified bonds, 54F — other than residential property); compute Section 112A ₹1.25L exemption with FIFO; determine tax rate (equity LTCG 12.5%, equity STCG 15% 111A, non-equity STCG slab rate, non-equity LTCG 12.5%, debt LTCG slab or 20% with indexation, crypto 30% 115BBH); determine ITR schedule placement (112A, CG A2, CG A5, CG B8); compute CG date ranges for Schedule CG Section F |
| **Inputs** | AIS SFT entries (equity MF sales, OTU sales, immovable property, securities purchases), Broker trade statements, Purchase/acquisition records, Sale deed, Improvement cost proofs, FY |
| **Outputs** | CapitalGainsBreakdown (per asset, per schedule), Taxable gains, Exempted gains, Losses for carry-forward, Schedule CG Section F date ranges |
| **Dependencies** | C3.4 AIS Parser, C3.8 Broker Statement Parser, C12.3 Rule Repository (S45-55A, CII tables) |
| **Business Value** | Most complex income head; wrong classification = wrong tax; a key value proposition |
| **Priority** | **Critical** |
| **Maturity Target** | All asset classes; all exemptions; grandfathered LTCG (pre-31-Jan-2018 equity); corporate actions cost adjustment |

### C4.5 — Other Sources Income Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute income under the head "Income from Other Sources" per Sections 56-59. |
| **Responsibilities** | Savings bank interest aggregation; fixed deposit interest (accrual basis); recurring deposit interest; bond/debenture interest; dividend income (taxable from FY2020-21); gift taxation (56(2)(x) — >₹50,000 from non-relatives); family pension (1/3rd or ₹15,000 deduction); lottery/game show winnings (30% 115BB); interest on income tax refund; share of profit from partnership firm |
| **Inputs** | AIS SFT entries (savings interest, term deposit interest, dividends), Bank statements, Interest certificates, FY |
| **Outputs** | IncomeFromOtherSources, InterestBreakdown, TaxableGifts, DividendBreakdown |
| **Dependencies** | C3.4 AIS Parser, C12.3 Rule Repository (S56-59) |
| **Business Value** | Catch-all income head; ensures complete income capture beyond salary and capital gains |
| **Priority** | **High** |
| **Maturity Target** | Auto-accrual interest computation from bank statements; gift aggregation with relationship mapping |

### C4.6 — Income Aggregation & Clubbing

| Attribute | Value |
|-----------|-------|
| **Purpose** | Aggregate income across all heads and apply clubbing provisions where applicable. |
| **Responsibilities** | Sum income across all 5 heads; apply clubbing provisions (Section 60 — transfer of income without asset, Section 61 — revocable transfers, Section 64(1A) — minor child's income); apply set-off rules (intra-head set-off, inter-head set-off restrictions); determine Gross Total Income |
| **Inputs** | Per-head income computations, Clubbing triggers (minor child, spouse, HUF) |
| **Outputs** | GrossTotalIncome, ClubbedIncomeBreakdown, Set-offApplied |
| **Dependencies** | C4.1-C4.5 Income engines, C2.6 Family Unit Management, C12.3 Rule Repository (S60-64) |
| **Business Value** | Ensures legal completeness; prevents omission of clubbed income that could trigger notice |
| **Priority** | **High** |
| **Maturity Target** | Auto-detection of clubbing scenarios from family profile; minor child income threshold monitoring |

### C4.7 — Previous Year Data Import

| Attribute | Value |
|-----------|-------|
| **Purpose** | Import previous year tax data for carry-forward computations, comparison, and prefill. |
| **Responsibilities** | Import previous year ITR data (filed JSON or data extract); extract brought-forward losses (house property, business, capital gains, speculation, depreciation); extract unabsorbed depreciation; extract TDS credit brought forward; detect year-over-year changes; prefill current year data from previous year where applicable |
| **Inputs** | Previous year ITR JSON, Filing history, AIS historical data |
| **Outputs** | BroughtForwardData, PrefillSuggestions, YearOverYearComparison |
| **Dependencies** | C2.5 Historical Filing Record, C7.2 Carry-Forward & Set-Off Engine |
| **Business Value** | Major UX win — eliminates re-entry of recurring data; ensures carry-forward accuracy |
| **Priority** | **Medium** |
| **Maturity Target** | Direct import from ITD e-filing portal; auto-carry-forward of all eligible losses |

### C4.8 — Foreign Income & Asset Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Handle foreign income, foreign assets, and foreign tax credit for NRIs and residents with overseas economic activity. |
| **Responsibilities** | Track foreign assets (bank accounts, immovable property, securities, trusts, insurance, loans) for Schedule FA; compute foreign income by source country; apply DTAA provisions for each country pair; compute foreign tax credit (Form 67, Section 90/90A/91); handle foreign exchange conversion (SBI TTBR as on specified dates); determine reporting requirements per asset value threshold |
| **Inputs** | Foreign bank statements, Foreign tax returns, Foreign asset details, DTAA for relevant country |
| **Outputs** | ScheduleFA, ForeignIncomeBreakdown, ForeignTaxCredit, Form67Data |
| **Dependencies** | C2.2 Residential Status, C12.3 Rule Repository (DTAA database), C11.2 Tax Provision Knowledge Base |
| **Business Value** | Critical for NRI users; mandatory disclosure; significant penalties for non-disclosure |
| **Priority** | **Medium** |
| **Maturity Target** | DTAA database for 90+ countries; automated Form 67 generation; multi-currency support |

---

*[Document continues with Domains 6-20, Bounded Context Map, Cross-Cutting Capabilities, and Dependency Matrix. See Part 2.]*
