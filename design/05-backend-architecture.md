# Backend Architecture — TaxStox AI-Powered Indian Income Tax Assistant

> **Version:** 1.0  
> **Last Updated:** 2026-06-29  
> **Status:** Draft for Review

---

## Table of Contents

1. [System Topology](#1-system-topology)
2. [Core Services](#2-core-services)
3. [Technology Stack](#3-technology-stack)
4. [Interservice Communication Patterns](#4-interservice-communication-patterns)
5. [Data Flow Diagrams](#5-data-flow-diagrams)
6. [Caching Strategy](#6-caching-strategy)
7. [Background Job Processing](#7-background-job-processing)
8. [LLM Integration Architecture](#8-llm-integration-architecture)
9. [Multi-Tenancy Model](#9-multi-tenancy-model)
10. [Seasonal Capacity Planning](#10-seasonal-capacity-planning)

---

## 1. System Topology

### 1.1 Microservices Decomposition

TaxStox is decomposed into **15 microservices**, each owning a bounded context and a dedicated data store (shared-nothing except through API contracts).

| # | Service | Responsibility | Data Store | Sync/Async |
|---|---------|----------------|------------|-----------|
| 1 | **API Gateway** | Rate limiting, auth, request routing, TLS termination | Redis (config, rate counters) | Sync |
| 2 | **User Service** | Registration, login, profile, PAN verification, OTP | PostgreSQL (users), Redis (sessions) | Sync |
| 3 | **Document Ingestion Service** | Upload handling, virus scanning, format detection, chunking | MinIO/S3 (documents), PostgreSQL (metadata) | Async |
| 4 | **OCR Orchestration Service** | Document pipeline (preprocessing, OCR, postprocessing) | PostgreSQL (job status), Redis (queue) | Async |
| 5 | **Entity Extraction Service** | NER, schema mapping, confidence scoring | PostgreSQL (entities), Redis (cache) | Async |
| 6 | **Validation Engine Service** | 400+ rule execution, cross-field validation | PostgreSQL (results) | Sync/Async |
| 7 | **Tax Rule Engine** | Deterministic tax computation, regime comparison | PostgreSQL (computation results) | Sync |
| 8 | **Conversation Service** | Question generation, state management, turn tracking | PostgreSQL (turns), Redis (state) | Sync |
| 9 | **AI Orchestration Service** | LLM interaction, agent coordination, prompt management | Redis (conversation context) | Sync |
| 10 | **JSON Generation Service** | ITR schema compilation, JSON validation, S3 upload | PostgreSQL (ITR JSONs), S3 (output) | Sync |
| 11 | **Audit Service** | Event logging, compliance trail, tamper-proof storage | PostgreSQL (audit_log), immutable append | Async |
| 12 | **Notification Service** | Email, SMS, push notification dispatch | Redis (queue), PostgreSQL (templates) | Async |
| 13 | **Reporting Service** | Filing history, analytics dashboards, admin views | PostgreSQL (materialized views), ClickHouse (optional) | Sync |
| 14 | **Rate Limiter Service** | Token-bucket rate enforcement per-API-key per-user | Redis (counters) | Sync (sidecar) |
| 15 | **Admin Console Service** | Internal admin panel, user management, system health | PostgreSQL (admin models) | Sync |

### 1.2 Service Mesh / API Gateway Pattern

```
                          ┌─────────────────┐
                          │   CloudFront /   │
                          │   CDN (static)   │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │   API Gateway   │◄── WAF (AWS WAF / Cloudflare)
                          │   (Kong / Envoy)│
                          └────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
            ┌───────▼───────┐ ┌───▼────┐  ┌──────▼──────┐
            │  Auth Filter  │ │  Rate  │  │  Routing    │
            │  (JWT verify) │ │ Limiter│  │  Filter     │
            └───────┬───────┘ └────────┘  └──────┬──────┘
                    │                            │
                    └────────────────────────────┘
                                   │
                    ┌──────────────▼────────────────┐
                    │     Service Mesh (Istio /      │
                    │     Linkerd) — mTLS, traffic   │
                    │     control, observability     │
                    └──────────────┬────────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
    ┌───────▼───────┐     ┌───────▼───────┐     ┌───────▼───────┐
    │  User Svc     │     │ Document      │     │ AI Orchestr  │
    │  (2 replicas) │     │ Ingestion Svc │     │ (4 replicas) │
    └───────────────┘     │ (3 replicas)  │     └───────────────┘
                          └───────────────┘
```

**API Gateway Responsibilities:**
- **Kong** (preferred) or **Envoy** as the ingress gateway
- JWT validation at the edge (pre-decoded and passed via `x-user-id` header)
- Rate limiting per route, per user, per IP
- Request/response transformation (JSON:API envelope)
- Circuit breaking — upstream failure thresholds trigger graceful degradation
- Canary routing for blue-green deployments (via `x-canary` header match)

**Service Mesh (Istio) — why:**
- mTLS between all pods without application code changes
- Traffic splitting for canary releases
- Distributed tracing (Jaeger/Zipkin integration)
- Fine-grained telemetry (request volume, latency, error rate, saturation)

### 1.3 Event-Driven Architecture

```
                    ┌───────────────────────────┐
                    │  Event Bus (Kafka)        │
                    │                           │
                    │  Topics:                  │
                    │  ┌─────────────────────┐  │
                    │  │ document.uploaded   │  │
                    │  │ document.scanned    │  │
                    │  │ document.ocr.done   │  │
                    │  │ entities.extracted  │  │
                    │  │ validation.complete │  │
                    │  │ tax.computed        │  │
                    │  │ itr.generated       │  │
                    │  │ session.completed   │  │
                    │  │ notification.send   │  │
                    │  └─────────────────────┘  │
                    └───────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
   ┌──────▼──────┐    ┌───────▼───────┐    ┌───────▼───────┐
   │  Producer   │    │  Consumer     │    │  DLQ / Retry  │
   │  Services   │    │  Services     │    │  (Kafka DLQ)  │
   └─────────────┘    └───────────────┘    └───────────────┘
```

### 1.4 Message Queue Choices

| Use Case | Technology | Rationale |
|----------|-----------|-----------|
| Document processing pipeline events | **Apache Kafka** | Durable, replayable, high-throughput. Required for multi-stage OCR pipeline where each stage publishes and subsequent stages subscribe. Retention for 7 days for replay. |
| Task dispatch for OCR workers | **RabbitMQ** | Fine-grained ack/nack, per-message TTL, priority queues. Each OCR job needs exactly-once delivery tracking. |
| Notification dispatch | **RabbitMQ** | Lower throughput needs, DLX for failed notification retries (3 attempts, then dead-letter). |
| Audit event stream | **Kafka** | Append-only, immutable log with configurable retention. Enables compliance queries (who accessed what, when). |
| Background job processing | **Bull/BullMQ** (Redis-backed) | Node.js-native job queues with scheduling, rate limiting, concurrency control. Used for periodic tasks (purge, analytics refresh). |

### 1.5 Service Discovery and Load Balancing

- **Kubernetes-native:** Headless Services with DNS-based discovery (`service.namespace.svc.cluster.local`)
- **External:** Cloud DNS (Route53 / Cloudflare DNS) with weighted records for multi-region
- **Load balancer per service:** Round-robin within the mesh; least-connection for OCR workers (variable job duration)

---

## 2. Core Services

### 2.1 API Gateway Service (Kong)

```
Endpoints:
  POST   /api/v1/auth/register
  POST   /api/v1/auth/login
  POST   /api/v1/auth/verify-otp
  POST   /api/v1/auth/refresh

  POST   /api/v1/documents/upload          → Document Ingestion
  GET    /api/v1/sessions/:id               → User Service
  POST   /api/v1/sessions/:id/chat          → Conversation Service
  GET    /api/v1/sessions/:id/itr           → JSON Generation Service
  GET    /api/v1/profile                    → User Service
  GET    /api/v1/notifications              → Notification Service
  GET    /api/v1/status/:session_id         → Status polling endpoint
```

**Rate Limiting Configuration:**
- Anonymous: 10 req/min
- Authenticated: 60 req/min
- Upload endpoints: 5 req/min (file size limit 20 MB)
- AI conversation: 20 req/min (high cost per token)
- Admin: 200 req/min

### 2.2 User Service

```
Responsibilities:
  - User registration (name, email, phone, PAN)
  - PAN verification via Protean/TIN-NSDL API
  - Aadhaar OTP-based verification
  - JWT access/refresh token management
  - Profile management (preferences, ITR type defaults)
  - Passwordless login via OTP (email/SMS)
  - Device/browser tracking for fraud detection
  - Account deletion with anonymization (GDPR compliance)
```

**Endpoints (internal):**
- `POST /internal/users` — create user
- `GET /internal/users/:id` — get user profile
- `PATCH /internal/users/:id` — update profile
- `POST /internal/users/:id/verify-pan` — initiate PAN verification
- `POST /internal/users/:id/verify-aadhaar` — initiate Aadhaar OTP
- `DELETE /internal/users/:id` — soft delete + anonymize

**Data flow for registration:**
1. User submits PAN, name, email, phone
2. User Service calls PAN verification API (Protean)
3. PAN details cross-verified against user-provided name (fuzzy match)
4. OTP sent to registered mobile via Notification Service (async event)
5. User submits OTP → User Service verifies → JWT issued
6. PAN stored as SHA-256 hash (raw PAN never persisted)
7. PII encrypted at column level (AES-256-GCM with vault-managed key)

### 2.3 Document Ingestion Service

```
Responsibilities:
  - Multipart upload handling with progress tracking
  - Client-side virus scanning (ClamAV)
  - File type validation (PDF, JPG, PNG — max 20 MB)
  - Page count extraction for PDFs
  - Document classification (Form 16 / Bank Statement / Capital Gains / Rent Receipt / etc.)
  - Chunking large PDFs into page ranges for parallel OCR
  - S3/MinIO upload with server-side encryption
  - Pre-signed URL generation for direct client upload (for large files)
  - TTL-based auto-purge (24 hours for raw documents, 7 days for processed)
```

**Supported Document Types:**
| Document Type | Expected Fields | Priority |
|--------------|----------------|----------|
| Form 16 (Part A & B) | Salary, TDS, deductions | P0 |
| Bank Statement (Savings) | Interest income | P1 |
| Capital Gains Statement | LTCG, STCG, purchase/sale dates | P1 |
| Rent Receipts | HRA deduction | P1 |
| 80C Proofs (LIC, PPF, ELSS) | Investment deductions | P1 |
| 80D Proofs | Medical insurance premium | P2 |
| Home Loan Certificate | 24(b) interest deduction | P1 |
| Form 26AS / AIS | TDS, SFT, tax payments | P0 |
| Form 16A | TDS on interest/rent | P2 |

### 2.4 OCR Orchestration Service

```
Pipeline:
  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ Pre-     │ → │ OCR      │ → │ Post-    │ → │ Quality  │
  │ process  │   │ Engine   │   │ process  │   │ Check    │
  └──────────┘   └──────────┘   └──────────┘   └──────────┘

Pre-process:
  - Convert to 300 DPI (if PDF)
  - Deskew, denoise, binarize (OpenCV / ImageMagick)
  - Detect orientation and rotate
  - Mask sensitive PII regions (PAN, Aadhaar numbers) for privacy

OCR Engine (layered):
  Primary:  **Azure Document Intelligence** (formerly Form Recognizer) — best for Indian documents with Hindi/English mix
  Fallback: **Tesseract 5** (self-hosted) — for PDFs failing Azure confidence threshold
  Special:  **DocTR** (open-source) — for handwritten text in forms

Post-process:
  - Spelling correction (custom dictionary of 10K+ Indian financial terms)
  - Regex extraction for PAN, Aadhaar, IFSC, MICR
  - Key-value pair normalization (label alignment)

Quality Check:
  - Confidence scoring per extracted field
  - Fields below 0.7 confidence → flagged for user verification
  - Pages below 0.5 confidence → reprocess with fallback engine
```

**Kafka Topics consumed:** `document.scanned`  
**Kafka Topics produced:** `document.ocr.done`

### 2.5 Entity Extraction Service

```
Responsibilities:
  - Named Entity Recognition (NER) on OCR output
  - Financial entity classification (salary, deduction, income, tax)
  - Schema mapping: extracted text → ITR Schema fields
  - Cross-document entity merging (e.g., "salary" from Form 16 + "salary" from Form 26AS)
  - Confidence scoring with calibration
  - Provisional entity creation (marked unverified) for user review
```

**Entity Types:**
```
PAN              → { value, confidence, source }
SalaryIncome     → { amount, employer_name, tds_deducted, confidence }
InterestIncome   → { amount, bank_name, account_type, confidence }
CapitalGains     → { asset_type, purchase_date, sale_date, cost, proceeds, confidence }
Deduction80C     → { section, amount, investment_type, confidence }
Deduction80D     → { amount, insured_name, premium_type, confidence }
HRA             → { amount, employer_received, rent_paid, confidence }
HomeLoan        → { principal, interest, lender_name, confidence }
TDS             → { amount, section, deductor_name, confidence }
```

**Schema Mapping Strategy:**
```
OCR raw text → [NER Model] → Named entities → [Schema Mapper] → ITR schema JSON Paths
                                                                  e.g., /ITR1/ScheduleSalary/Salary/AmountReceived
```

**Confidence Calibration:**
- Unanimous from 2+ documents → confidence 0.95+
- Single source, high OCR confidence → confidence 0.85
- Single source, low OCR confidence → confidence 0.60 → flagged
- Conflicting values between sources → confidence 0.40 → user must resolve

### 2.6 Validation Engine Service

```
Responsibilities:
  - Execute 400+ cross-field validation rules
  - Schema compliance (ITR-1 vs ITR-2 vs ITR-3 applicability)
  - Consistency checks (salary from Form 16 vs Form 26AS)
  - Threshold checks (80C max 1.5L, 80D max 25K/50K)
  - Regime-specific rule enforcement (deductions not applicable in New Regime)
  - User override tracking with reason capture
```

**Rule Categories:**

| Category | Count | Example |
|----------|-------|---------|
| Schema Applicability | 10 | "Cannot claim HRA if using ITR-1 without Schedule House Property" |
| Cross-field Consistency | 80 | "Total 80C deductions exceed ₹1,50,000" |
| Cross-document Matching | 50 | "Salary in Form 16 differs from Form 26AS by > 10%" |
| Threshold/Limit | 100 | "Section 80D deduction exceeds ₹50,000 (above 60 age: ₹1,00,000)" |
| Regime Compatibility | 30 | "Section 80C claimed but user opted New Tax Regime" |
| Data Integrity | 50 | "PAN format invalid" |
| Mathematical | 40 | "Total income ≠ sum of all income heads" |
| Temporal | 30 | "Sale date is after 31-Mar-2025 for AY 2025-26" |
| Compliance | 30 | "Required schedule XYZ missing for claimed deduction" |

**Rule Engine Architecture:**
```
                        ┌─────────────────────────────┐
                        │  Rule Registry (DB)         │
                        │  ┌──────────────────────┐   │
                        │  │ Rule { id, category, │   │
                        │  │  severity, condition, │   │
                        │  │  message_template,   │   │
                        │  │  resolution_hint }   │   │
                        │  └──────────────────────┘   │
                        └─────────────┬───────────────┘
                                      │
                        ┌─────────────▼───────────────┐
                        │  Evaluation Engine          │
                        │  ┌───────────────────────┐  │
                        │  │ RuleContext            │  │
                        │  │ - session_id           │  │
                        │  │ - regime               │  │
                        │  │ - all entities         │  │
                        │  │ - tax computation      │  │
                        │  │ - prior validations    │  │
                        │  └───────────────────────┘  │
                        │  Expression evaluator        │
                        │  (JSON-logic / custom DSL)   │
                        └─────────────┬───────────────┘
                                      │
                        ┌─────────────▼───────────────┐
                        │  Results                    │
                        │  ┌───────────────────────┐  │
                        │  │ PASS │ FAIL │ WARN    │  │
                        │  │ PASS → no action      │  │
                        │  │ FAIL → blocked, must  │  │
                        │  │        resolve         │  │
                        │  │ WARN → advisory, can  │  │
                        │  │        proceed with    │  │
                        │  │        overridden_by   │  │
                        │  └───────────────────────┘  │
                        └─────────────────────────────┘
```

### 2.7 Tax Rule Engine — NEVER by AI

> **Critical constraint:** Tax computation must be **deterministic, rule-based, and auditable**. No LLM or AI model is involved in computing tax liability. AI is used only for user interaction, entity extraction, and interface.

```
Responsibilities:
  - Compute tax liability under both regimes (Old & New)
  - Apply income slabs (Old: 2.5L-5L-10L-...; New: 3L-6L-9L-12L-15L-...)
  - Apply cess (Health & Education Cess @ 4%)
  - Apply rebate under Section 87A
  - Compute Alternative Minimum Tax (AMT) if applicable
  - Compute Minimum Alternate Tax (MAT) for companies (ITR-6)
  - Generate computation sheet (breakdown by head, deduction, tax, cess)
  - Support agriculture income aggregation rules
  - Support clubbing provisions (minor income, spouse income)
  - Support set-off and carry-forward of losses
```

**Computation Flow:**
```
                 ┌────────────────────────┐
                 │  Validated Entities    │
                 └───────────┬────────────┘
                             │
                 ┌───────────▼────────────┐
                 │  Income Aggregation    │
                 │  ┌─────────────────┐   │
                 │  │ Salary Income   │   │
                 │  │ House Property  │   │
                 │  │ Business/Prof. │   │
                 │  │ Capital Gains  │   │
                 │  │ Other Sources  │   │
                 │  └─────────────────┘   │
                 │  Total Gross Income    │
                 └───────────┬────────────┘
                             │
                 ┌───────────▼────────────┐
                 │  Deductions (Old Regime)│
                 │  ┌─ 80C, 80CCC, 80CCD │
                 │  ├─ 80D, 80DD, 80DDB  │
                 │  ├─ 80E, 80EE, 80EEA  │
                 │  ├─ 80G               │
                 │  ├─ 80TTA, 80TTB      │
                 │  └─ 80U, 80RRB, etc.  │
                 │  Total Deductions     │
                 └───────────┬────────────┘
                             │
                 ┌───────────▼────────────┐
                 │  Taxable Income        │
                 │  = Gross - Deductions  │
                 └───────────┬────────────┘
                             │
                 ┌───────────▼────────────┐
                 │  Slab Calculator       │
                 │  (Old: 5 slabs)        │
                 │  (New: 6 slabs)        │
                 └───────────┬────────────┘
                             │
                 ┌───────────▼────────────┐
                 │  Rebate (87A)          │
                 │  Surcharge (>50L)      │
                 │  Cess @ 4%             │
                 └───────────┬────────────┘
                             │
                 ┌───────────▼────────────┐
                 │  Total Tax Liability   │
                 │  Compare Old vs New    │
                 │  Recommendation        │
                 └────────────────────────┘
```

**Implementation:**
- Pure TypeScript/Node.js module with zero external AI dependencies
- Tax slab rates defined as config (JSON), reloadable at runtime
- Computation logic covered by 1,000+ unit tests
- Each computation recorded as an immutable row in `tax_computations` with full input snapshot

### 2.8 Conversation Service

```
Responsibilities:
  - Manage multi-turn conversation state per filing session
  - Generate context-appropriate questions to fill missing data
  - Track answered questions and pending fields
  - Handle user corrections (e.g., "no, my salary is 12 lakhs")
  - Present tax computation results in natural language
  - Provide filing guidance (which ITR, which regime)
  - Escalate complex queries to human support (ticket creation)
```

**Conversation State Machine:**
```
GREETING → INITIAL_INFO → UPLOAD_DOCUMENTS → REVIEW_EXTRACTED
    → CLARIFICATION_LOOP (if low confidence) → TAX_COMPUTATION
    → REGIME_SELECTION → DEDUCTION_OPTIMIZATION → REVIEW_ITR
    → CONFIRM_AND_FILE → COMPLETED
```

**Question Generation Strategy:**
1. Identify missing mandatory fields from ITR schema
2. Prioritize by known dependency (ask salary before 80C deduction)
3. Use AI to generate natural language question with example
4. Validate response through entity extraction → if confidence > 0.9, accept; else ask again
5. For numeric responses, apply range validation (±20% of expected based on similar profiles)

### 2.9 AI Orchestration Service

```
Responsibilities:
  - Coordinate LLM interactions across use cases:
    a. Document classification (which form type?)
    b. Entity extraction from OCR text
    c. Question generation
    d. Natural language query answering ("What is my tax liability?")
    e. Filing guidance (which ITR/regime)
    f. Deduction optimization suggestions
  - Manage context windows (token budget allocation)
  - Handle LLM fallback (primary → secondary → fallback)
  - Rate limit LLM API calls
  - Log all LLM interactions for audit + prompt improvement
  - Cache identical LLM responses (semantic caching)
```

**Agent Architecture:**
```
                          ┌──────────────────────────┐
                          │  Anthropic Claude 4      │
                          │  (Primary, max_tokens    │
                          │   4096, temperature 0.1) │
                          └──────────┬───────────────┘
                                     │
                          ┌──────────▼───────────────┐
                          │  AI Orchestration Agent  │
                          │                          │
                          │  Tools:                  │
                          │  ┌────────────────────┐  │
                          │  │ classify_document  │  │
                          │  │ extract_entities   │  │
                          │  │ generate_question  │  │
                          │  │ get_tax_summary    │  │
                          │  │ get_filing_status  │  │
                          │  │ search_knowledge   │  │
                          │  │ escalate_support   │  │
                          │  └────────────────────┘  │
                          └──────────────────────────┘
```

**Fallback Chain:**
1. **Claude 4 Opus** (primary, complex reasoning, entity extraction)
2. **Claude 4 Sonnet** (cost-optimized, question generation, chat)
3. **GPT-4o** (secondary — if Anthropic rate-limited or down)
4. **Rule-based fallback** (when no LLM available — use template questions, basic regex extraction)

**Context Management:**
- Sliding window: last 20 conversation turns always in context
- Summary compression: every 5 turns, summarize older context into a condensed prompt
- Token budget: 80K tokens for document understanding, 4K for conversation, 16K for entity extraction
- PII masking: PAN/Aadhaar/mobile numbers are masked before sending to LLM API

### 2.10 JSON Generation Service

```
Responsibilities:
  - Compile validated entities into ITR schema JSON (ITR-1, ITR-2, ITR-3, ITR-4, ITR-5, ITR-6)
  - Schema versioning (current: ITR Schema v1.8 for AY 2025-26)
  - JSON validation against published XSD/schema
  - Generate ITR-XML for e-filing (required by Income Tax Portal)
  - Encrypt sensitive fields (PAN, name, bank account) per ITD guidelines
  - Upload to S3 for retention + user download
```

**Schema Pipeline:**
```
Entities (validated) → Schema Registry → Schema Mapper → JSON Builder
    → JSON Validator → XML Transformer → Encryptor → S3 Upload
```

**Schema Registry:**
- Supports AY 2023-24, 2024-25, 2025-26 (and future)
- Each version defines: validations, required fields, accepted values
- ITR type determines which schedules are included
- Regime flag determines deduction applicability

### 2.11 Audit Service

```
Responsibilities:
  - Immutable event log for all state-changing operations
  - Actor attribution (user, system, admin)
  - Tamper detection via SHA-256 hash chains
  - Compliance reporting (who accessed what data, when)
  - Retention: 7 years as per Income Tax Act
  - Anonymization after retention period
```

**Event Types:**
```
user.login, user.logout, user.profile.update
document.upload, document.view, document.delete
entity.extracted, entity.verified, entity.corrected
validation.pass, validation.fail, validation.override
tax.computed, tax.regime.selected
itr.generated, itr.viewed, itr.downloaded, itr.filed
session.created, session.completed, session.abandoned
```

**Tamper-Proof Log:**
```
Each audit entry includes:
  - `prev_hash`: SHA-256 of previous entry in this session's chain
  - `data_hash`: SHA-256 of the event payload
  - `entry_hash`: SHA-256(prev_hash || data_hash || created_at || nonce)

Verification: traverse chain, recompute entry_hash, compare stored value
```

### 2.12 Notification Service

```
Responsibilities:
  - Email dispatch via SendGrid/AWS SES
  - SMS dispatch via Twilio/MSG91
  - Push notifications via Firebase Cloud Messaging (FCM)
  - Template management (HTML email templates, SMS templates)
  - Delivery tracking (bounce, open, click)
  - Batch dispatch for bulk notifications (reminders)
  - User preference enforcement (opt-in/opt-out per channel)
```

**Notification Templates:**
| Template | Channel | Trigger |
|----------|---------|---------|
| Welcome Email | Email | Registration complete |
| OTP for Login | Email, SMS | Login attempt |
| Document Uploaded | Push | Upload success |
| Entities Ready for Review | Email, Push | OCR + extraction complete |
| Tax Computation Ready | Email, Push | Computation done |
| ITR Generated | Email | JSON generation complete |
| Filing Reminder (July) | Email, SMS | 10 days before July 31 deadline |
| Filing Reminder (Dec) | Email, SMS | 10 days before Dec 31 deadline |
| Session Abandoned | Email | No activity for 7 days |
| Account Deletion | Email | Anonymization complete |

### 2.13 Reporting Service

```
Responsibilities:
  - User-facing: filing history, tax summaries, deduction trends
  - Admin-facing: daily active users, filing volume, error rates, LLM costs
  - Scheduled report generation (daily, weekly, monthly)
  - Export to CSV/PDF
  - Materialized view refresh for dashboards
```

**Key Metrics:**
- Daily active users (DAU), weekly active users (WAU)
- Filing completion rate (sessions started → filed)
- Average session duration
- Document upload volume by type
- OCR success rate by document type
- Entity extraction confidence distribution
- Validation failure rate (top 10 failed rules)
- Regime preference ratio (Old vs New)
- LLM API cost per session
- Error rates by service

---

## 3. Technology Stack

### 3.1 Core Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Runtime** | Node.js 22 LTS (TypeScript 5.5) | Team expertise, strong typing, async-first. Single-language reduces cognitive overhead. |
| **Framework** | NestJS (microservices mode) | Opinionated structure, built-in DI, guards, interceptors, OpenAPI generation. TCP transport for interservice. |
| **API Gateway** | Kong (OSS, DB-less mode) | Battle-tested, Lua plugin system for custom auth/rate-limit, declarative config via YAML. |
| **Service Mesh** | Istio (ambient mode) | mTLS, traffic splitting, observability without sidecar resource overhead. |
| **Message Broker** | Apache Kafka + RabbitMQ | Kafka for event streaming/audit; RabbitMQ for task queues with ack semantics. |
| **Database** | PostgreSQL 16 + Redis 7 | PostgreSQL for relational data with JSONB; Redis for caching, session, rate limiting. |
| **Object Storage** | MinIO (self-hosted) → S3 (prod) | S3-compatible API. MinIO for dev/staging; AWS S3 or Scaleway for production. |
| **Container Runtime** | Docker + Kubernetes (k3s/K8s) | Scalability, self-healing, rolling deployments. k3s for edge/on-prem; EKS/GKE for cloud. |
| **Observability** | OpenTelemetry + Grafana + Loki + Tempo | Traces (Tempo), logs (Loki), metrics (Prometheus), all unified in Grafana. |

### 3.2 AI/ML Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **LLM Provider** | Anthropic Claude 4 (Opus + Sonnet) | Best-in-class for financial reasoning, Indian context understanding. |
| **LLM SDK** | Anthropic TypeScript SDK | Native streaming, token counting, tool use support. |
| **Embeddings** | `text-embedding-3-small` (OpenAI) | For semantic caching: embed user query → nearest neighbor match. |
| **Vector Store** | Redis Stack (RediSearch) | Unified with existing Redis infra; good enough for 100K embeddings. |
| **OCR Primary** | Azure Document Intelligence | Superior Indian document support (Devanagari, mixed scripts). |
| **OCR Fallback** | Tesseract 5 (self-hosted container) | Zero cost, offline capable, good for well-scanned English documents. |
| **NER** | Custom fine-tuned model (BERT-based) | Deployed as ONNX on CPU; 10ms inference time. Covers ITR-specific entities. |

### 3.3 Storage Strategy

| Data Type | Storage | Retention | Notes |
|-----------|---------|-----------|-------|
| User PII | PostgreSQL (encrypted) | Until account deletion | AES-256-GCM column-level encryption |
| PAN (hash) | PostgreSQL | 7 years post last filing | SHA-256 hash, raw never stored |
| Documents (raw) | MinIO/S3 | 24 hours | Auto-purge via lifecycle policy |
| Documents (processed) | MinIO/S3 | 7 days | Auto-purge after filing confirmation |
| Extracted entities | PostgreSQL | 7 years | Needed for re-filing, IT dept queries |
| Tax computations | PostgreSQL | 7 years | Immutable, audit requirement |
| ITR JSONs (final) | MinIO/S3 + PostgreSQL | 7 years | S3 as warm storage; PG for index |
| Conversation logs | PostgreSQL | 90 days (raw) → anonymized (7 years) | Privacy; retention per policy |
| Audit log | PostgreSQL | 7 years | Tamper-evident chain |
| Session state (Redis) | Redis | 24 hours TTL | Ephemeral |
| Rate limit counters | Redis | 1 hour TTL | Ephemeral |
| OTPs | Redis | 10 min TTL | Ephemeral |

### 3.4 Security Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| TLS Termination | Kong / CloudFront | HTTPS at edge |
| WAF | Cloudflare / AWS WAF | SQL injection, XSS, DDoS protection |
| Secret Management | HashiCorp Vault | API keys, DB credentials, encryption keys |
| Virus Scanning | ClamAV (sidecar) | Document upload scanning |
| PII Masking | Custom (regex + NER) | Mask PII before LLM API calls |
| Column Encryption | pgcrypto (PG) | PII fields encrypted at rest |
| Audit Trail | Audit Service | Tamper-evident log |

### 3.5 DevOps CI/CD

| Stage | Tool | Details |
|-------|------|---------|
| Code Repository | GitHub | Branch protection, PR reviews required |
| CI | GitHub Actions | Build, lint, test, security scan (Semgrep) |
| Container Registry | GitHub Container Registry | Versioned Docker images |
| CD | ArgoCD | GitOps for K8s, auto-sync from `main` |
| Infrastructure | Terraform | IaC for K8s, databases, networking |
| Secret Sync | External Secrets Operator | Sync Vault secrets to K8s secrets |
| DB Migration | Flyway | Versioned, idempotent, tested in CI |

---

## 4. Interservice Communication Patterns

### 4.1 Synchronous Calls (REST/gRPC)

| Caller | Callee | Protocol | When |
|--------|--------|----------|------|
| API Gateway | User Service | gRPC (internal) | Auth, profile CRUD |
| API Gateway | Conversation Service | gRPC | Chat interactions |
| API Gateway | Tax Rule Engine | gRPC | Tax computation requests |
| Conversation Service | AI Orchestrator | gRPC | LLM requests |
| Conversation Service | Entity Extraction | gRPC | Response parsing |
| Tax Rule Engine | Validation Engine | gRPC | Pre-computation validation |
| AI Orchestrator | Entity Extraction | gRPC | Entity queries during conversation |
| Reporting Service | All (read-only) | REST | Dashboard data aggregation |

**gRPC vs REST Decision:**
- **gRPC** for internal, high-frequency, low-latency calls (user auth, conversation turns, tax computation)
- **REST** for external-facing endpoints, read-heavy reporting, cross-service queries with varied payloads
- **gRPC** adopted for: strongly typed contracts (Protobuf), bidirectional streaming (conversation), native K8s DNS resolution

### 4.2 Asynchronous Events (Kafka/RabbitMQ)

| Emitter | Event | Consumer(s) | Queue |
|---------|-------|-------------|-------|
| Document Ingestion | `document.uploaded` | OCR Orchestration | Kafka |
| OCR Orchestration | `document.ocr.done` | Entity Extraction | Kafka |
| Entity Extraction | `entities.extracted` | Validation Engine, Conversation Service | Kafka |
| Validation Engine | `validation.complete` | Tax Rule Engine, Conversation Service | Kafka |
| Tax Rule Engine | `tax.computed` | JSON Generation, Notification, Conversation | Kafka |
| JSON Generation | `itr.generated` | Notification Service | Kafka |
| Audit Service | (consumes all events) | - | Kafka |
| Conversation Service | (consumes relevant events) | - | Kafka |
| Document Ingestion | `document.scan.req` | ClamAV worker | RabbitMQ |
| Notification Service | `notification.send` | Email/SMS worker | RabbitMQ |

### 4.3 Event Payload Schema

```
{
  "event_id": "uuid",
  "event_type": "document.uploaded",
  "version": 1,
  "source_service": "document-ingestion",
  "timestamp": "2026-06-29T10:30:00Z",
  "correlation_id": "session-uuid",
  "trace_id": "opentelemetry-trace-id",
  "actor_id": "user-uuid",
  "data": { /* event-specific payload */ },
  "metadata": {
    "retry_count": 0,
    "producer_timestamp": "2026-06-29T10:30:00.123Z"
  }
}
```

### 4.4 Error Handling / Retry / DLQ

```
Synchronous:
  - Circuit breaker (Opossum library): 5 failures → open for 30s
  - Retry: 3 attempts with exponential backoff (100ms, 500ms, 2s)
  - Fallback: cached response or graceful degradation

Asynchronous (Kafka):
  - Consumer retry: 3 attempts on `retry` topic partitions
  - DLQ after 3 failures: `document.ocr.done.dlq`
  - DLQ alert triggers PagerDuty notification

Asynchronous (RabbitMQ):
  - Basic NACK with re-queue for transient failures (max 3)
  - Dead Letter Exchange (DLX) for final failures
  - TTL-based delays for retry (30s → 2min → 10min)
```

---

## 5. Data Flow Diagrams

### 5.1 Document Upload → Extraction Pipeline

```
User                        API Gateway     Document         OCR              Entity
│                               │           Ingestion        Orchestration    Extraction
│  POST /documents/upload       │               │                 │               │
│──────────────────────────────►│               │                 │               │
│                               │  Validate JWT │                 │               │
│                               │  Check rate   │                 │               │
│                               │  limit        │                 │               │
│                               │──────────────►│                 │               │
│                               │               │  Virus scan     │               │
│                               │               │  (ClamAV)       │               │
│                               │               │  Classify doc   │               │
│                               │               │  Upload to S3   │               │
│                               │               │  Create metadata│               │
│                               │               │  Emit event     │               │
│                               │               │─ ─ ─ ─ ─ ─ ─ ─►│               │
│  { upload_id, status }        │               │  (document.     │               │
│◄──────────────────────────────│               │   uploaded)     │               │
│                               │               │                 │               │
│                               │               │                 │ Pre-process   │
│                               │               │                 │ Run OCR       │
│                               │               │                 │ Post-process  │
│                               │               │                 │ Quality check │
│                               │               │                 │ Emit event    │
│                               │               │                 │─ ─ ─ ─ ─ ─ ─►│
│                               │               │                 │ (document.   │
│                               │               │                 │  ocr.done)   │
│                               │               │                 │               │
│                               │               │                 │               │ Run NER
│                               │               │                 │               │ Map to schema
│                               │               │                 │               │ Score confidence
│                               │               │                 │               │ Emit event
│                               │               │                 │               │─ ─ ─ ─ ─ ─→
│                               │               │                 │               │(entities.
│                               │               │                 │               │ extracted)
│                               │               │                 │               │
```

### 5.2 Tax Computation Flow

```
Conversation     Entity           Validation       Tax Rule          JSON Gen     User
  Service      Extraction          Engine           Engine           Service
     │              │                 │                │                │           │
     │ "Compute my  │                 │                │                │           │
     │  taxes"      │                 │                │                │           │
     │──────────────┼────────────────►│                │                │           │
     │              │                 │                │                │           │
     │              │                 │ Fetch entities │                │           │
     │              │                 │────────────────►               │           │
     │              │                 │                │                │           │
     │              │                 │ 400+ rules     │                │           │
     │              │                 │ Validate        │                │           │
     │              │                 │◄───────────────│                │           │
     │              │                 │                │                │           │
     │              │                 │ Validation     │                │           │
     │              │                 │ results        │                │           │
     │◄─────────────┼─────────────────│                │                │           │
     │              │                 │                │                │           │
     │ "Old: ₹X    │                 │                │                │           │
     │  New: ₹Y"   │                 │                │                │           │
     │──────┐       │                 │                │                │           │
     │      │       │                 │                │                │           │
     │◄─────┘       │                 │ "Compute Old"  │                │           │
     │              │                 │────────────────►               │           │
     │              │                 │                │ Compute        │           │
     │              │                 │                │ Old regime     │           │
     │              │                 │ "Compute New"  │ Compute        │           │
     │              │                 │────────────────►               │           │
     │              │                 │                │ New regime     │           │
     │              │                 │                │                │           │
     │              │                 │                │ Emit event     │           │
     │              │                 │                │─ ─ ─ ─ ─ ─ ─ ►│           │
     │              │                 │                │ (tax.computed) │           │
     │              │                 │                │                │           │
     │              │                 │                │                │ Build ITR  │
     │              │                 │                │                │ JSON       │
     │              │                 │                │                │ Validate   │
     │              │                 │                │                │ Upload S3  │
     │              │                 │                │                │ Emit event │
     │              │                 │                │                │─ ─ ─ ─ ─► │
     │              │                 │                │                │(itr.       │
     │              │                 │                │                │ generated) │
     │              │                 │                │                │           │
```

### 5.3 Conversation + LLM Interaction Flow

```
User         Conversation         AI Orchestrator         LLM (Claude)     Entity Extraction
 │                  │                    │                     │                  │
 │ "What is my     │                    │                     │                  │
 │  HRA deduction?"│                    │                     │                  │
 │────────────────►│                    │                     │                  │
 │                  │ Build context      │                     │                  │
 │                  │ (session state +   │                     │                  │
 │                  │  last 10 turns +   │                     │                  │
 │                  │  extracted entities)│                     │                  │
 │                  │───────────────────►│                     │                  │
 │                  │                    │ Mask PII            │                  │
 │                  │                    │ Build prompt        │                  │
 │                  │                    │────────────────────►│                  │
 │                  │                    │                     │ Generate         │
 │                  │                    │   ◄─────────────────│ response          │
 │                  │                    │                     │                  │
 │                  │                    │ Parse response      │                  │
 │                  │                    │ Extract structured  │                  │
 │                  │                    │ data (if any)       │                  │
 │                  │◄───────────────────│                     │                  │
 │                  │                    │                     │                  │
 │                  │ Store conversation │                     │                  │
 │                  │ turn in DB         │                     │                  │
 │                  │ Update session     │                     │                  │
 │                  │ state in Redis     │                     │                  │
 │                  │                    │                     │                  │
 │ "Based on your  │                    │                     │                  │
 │  rent receipts  │                    │                     │                  │
 │  (₹15,000/mo),  │                    │                     │                  │
 │  HRA exemption  │                    │                     │                  │
 │  is ₹1,44,000"  │                    │                     │                  │
 │◄────────────────│                    │                     │                  │
 │                  │                    │                     │                  │
```

---

## 6. Caching Strategy

### 6.1 Redis Cache Layers

| Cache Name | Key Pattern | TTL | Size | Purpose |
|-----------|-------------|-----|------|---------|
| Session State | `session:{session_id}` | 24h | ~5 KB/turn | Serialized conversation state, current step, pending questions |
| Computation Cache | `computation:{regime}:{income_hash}:{deduction_hash}` | 7 days | ~2 KB | Cached tax results for identical inputs |
| Rate Limit | `ratelimit:{user_id}:{route}` | 1h sliding | ~100 B | Token bucket counters |
| OTP Store | `otp:{phone_or_email}` | 10 min | ~200 B | OTP code + attempt count |
| Refresh Token | `refresh:{token_hash}` | 30 days | ~100 B | Valid refresh tokens |
| Entity Cache | `entity:{session_id}:{doc_id}` | 1h | ~50 KB | Extracted entities per document (short-lived) |
| Document Status | `docjob:{upload_id}` | 2h | ~500 B | Processing status for polling |
| LLM Response (semantic) | `llm:sem:{embedding_hash}` | 24h | ~4 KB | Cache identical LLM queries |
| Abuse Prevention | `abuse:{user_id}:{action}` | 24h | ~100 B | Counter for suspicious actions |
| User Throttle | `throttle:{user_id}:{endpoint}` | 1s-60s | ~50 B | Per-endpoint sliding window |

### 6.2 Cache Invalidation Strategy

```
Session State:  Written on every turn; TTL refresh on activity. Expired = user needs to re-authenticate.
Computation:    Invalidated when entities are updated (user corrects a value) or regime changes.
Entity Cache:   Invalidated when re-OCR triggered or user explicitly corrects a field.
LLM Semantic:   Invalidated on prompt template change (bump version in key).
Rate Limit:     Automatic TTL expiry; never explicitly invalidated.
OTP:            Invalidated on successful verification or expiry.
```

### 6.3 Redis Configuration

```
Memory:
  - maxmemory: 4 GB (dedicated instance)
  - eviction-policy: allkeys-lru (volatile is fine too; session expiry handles cleanup)
  - Cluster mode: 3 primary + 3 replica (production)
  - Persistence: AOF with fsync every 1s (acceptable loss during failover)

High Availability:
  - Redis Sentinel (3 nodes) for automatic failover
  - Connection: ioredis with Sentinel integration
  - Read replicas for cache reads (if scale demands)
```

### 6.4 Application-Level Caching (In-Memory)

| Cache | Mechanism | TTL | Size Limit | When |
|-------|-----------|-----|------------|------|
| Tax slab config | Node.js Map (NestJS CacheModule) | 1h | ~10 KB | Loaded from DB on startup + periodic refresh |
| Rule definitions | Node.js Map | 5 min | ~1 MB | Validation rules rarely change |
| Document type classifiers | Node.js Map | 24h | ~5 MB | ML model weights loaded at boot |
| Schema definitions | NestJS CacheModule | 1h | ~500 KB | ITR schema versions (file system cached) |

---

## 7. Background Job Processing

### 7.1 Queue Architecture (Bull/BullMQ)

```
                    ┌──────────────────────────────────┐
                    │          Redis Backend            │
                    │  ┌────────────┐ ┌──────────────┐  │
                    │  │ Job Data   │ │ Job Events   │  │
                    │  └────────────┘ └──────────────┘  │
                    └────────────────┬─────────────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
    ┌───────▼───────┐        ┌───────▼───────┐        ┌──────▼───────┐
    │  Document     │        │  Notification │        │  Scheduled   │
    │  Processing   │        │  Dispatch     │        │  Tasks       │
    │  Queue        │        │  Queue        │        │  Queue       │
    └───────────────┘        └───────────────┘        └──────────────┘
         │  Concurrency: 5        │  Concurrency: 10       │  Concurrency: 1
         │  Priority: doc_type    │  Priority: channel     │  CRON-based
         │  Retry: 3              │  Retry: 3              │  Retry: 2
```

### 7.2 Job Definitions

| Queue | Job Type | Concurrency | Retry | Timeout | Description |
|-------|----------|-------------|-------|---------|-------------|
| Document Processing | `ocr-processing` | 5 | 3 | 300s | Full OCR pipeline per document |
| Document Processing | `virus-scan` | 3 | 2 | 60s | ClamAV scan |
| Document Processing | `document-classify` | 10 | 2 | 30s | ML-based type classification |
| Notification | `send-email` | 10 | 3 | 30s | Email dispatch with template |
| Notification | `send-sms` | 10 | 3 | 15s | SMS via Twilio/MSG91 |
| Notification | `send-push` | 10 | 2 | 15s | FCM push |
| Scheduled | `purge-expired-docs` | 1 | 2 | 300s | Daily S3 lifecycle enforcement |
| Scheduled | `anonymize-old-data` | 1 | 2 | 600s | Monthly GDPR/IT compliance |
| Scheduled | `refresh-materialized-views` | 1 | 2 | 120s | Daily reporting refresh |
| Scheduled | `session-reminder-batch` | 1 | 2 | 60s | Email abandoned sessions weekly |

### 7.3 Job Lifecycle

```
waiting → active → completed
                → failed → wait (retry) → active → completed / failed (DLQ)
waiting → delayed (scheduled future time) → waiting → ...
active → stalled (no progress heartbeat) → wait → retry
```

### 7.4 CRON Schedule Definitions

```yaml
# BullMQ repeatable jobs configuration
purge_expired_documents:     "0 2 * * *"     # Daily 2 AM
anonymize_old_data:          "0 3 1 * *"     # Monthly 1st, 3 AM
refresh_reporting_views:     "0 4 * * *"     # Daily 4 AM
sending_reminders_batch:     "0 10 * * 1"    # Weekly Monday 10 AM
regenerate_sitemap:          "0 5 * * 0"     # Weekly Sunday 5 AM
health_check_all_services:   "*/5 * * * *"   # Every 5 minutes
cache_warmup_popular:        "0 6 * * *"     # Daily 6 AM (pre-season peak)
```

---

## 8. LLM Integration Architecture

### 8.1 Provider Configuration

```typescript
// anthropic.config.ts
export const anthropicConfig = {
  primary: {
    model: 'claude-4-opus-20250514',
    maxTokens: 4096,
    temperature: 0.1,       // Low temperature for consistent extraction
    timeout: 60000,         // 60s timeout for complex extractions
    maxRetries: 2,
  },
  fallback: {
    model: 'claude-4-sonnet-20250514',
    maxTokens: 2048,
    temperature: 0.3,       // Slightly higher for creative question generation
    timeout: 30000,
    maxRetries: 3,
  },
  secondary: {
    provider: 'openai',
    model: 'gpt-4o-2026-05-15',
    maxTokens: 4096,
    temperature: 0.1,
    timeout: 60000,
    maxRetries: 2,
  },
  semanticCache: {
    enabled: true,
    provider: 'openai',
    embeddingModel: 'text-embedding-3-small',
    similarityThreshold: 0.92,
    ttl: 86400, // 24 hours
  },
};
```

### 8.2 Prompt Template Architecture

```
┌──────────────────────────────────────────────────┐
│                 Prompt Registry                   │
│                                                   │
│  document_classification/                         │
│    v1.txt  — "Classify the following document..." │
│    v2.txt  — Updated for AY 2025-26               │
│                                                   │
│  entity_extraction/                               │
│    v3.txt  — "Extract financial entities from..." │
│                                                   │
│  question_generation/                             │
│    v1.txt  — "Generate a question to ask the..."  │
│                                                   │
│  tax_guidance/                                    │
│    v2.txt  — "Based on the user's profile..."     │
│                                                   │
│  deduction_optimization/                          │
│    v1.txt  — "Suggest optimal deductions..."      │
└──────────────────────────────────────────────────┘
```

**Prompt Versioning Strategy:**
- Every prompt template is versioned in Git
- Prompts stored as `.txt` files in dedicated registry
- Version passed to LLM call and logged in audit trail
- A/B testing framework: serve v1 to 50% of users, v2 to 50% → measure extraction accuracy

### 8.3 PII Masking Layer

```
Before LLM call (AI Orchestration Service):
  Input:  "My PAN is ABCDE1234F and my salary is ₹12,00,000"
  Output: "My PAN is [REDACTED_PAN] and my salary is ₹12,00,000"

Mapping maintained in Redis (TTL = session duration):
  [REDACTED_PAN] → ABCDE1234F
  [REDACTED_AADHAAR] → 1234 5678 9012

After LLM response, reverse-map:
  LLM: "Your salary is ₹12,00,000 as per PAN [REDACTED_PAN]"
  →   "Your salary is ₹12,00,000 as per PAN ABCDE1234F"
```

### 8.4 Error Handling & Fallback

```
┌─────────────────┐
│  LLM Request    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Try Claude 4   │────►│  Rate Limited?  │
│  Opus (primary) │     └────────┬────────┘
└─────────────────┘              │ Yes
         │ No error              ▼
         ▼              ┌─────────────────┐
┌─────────────────┐     │  Try Claude 4   │
│  Return response│     │  Sonnet (bt)    │
└─────────────────┘     └────────┬────────┘
                                │ No error
                                ▼
                        ┌─────────────────┐
                        │  Return response│
                        └─────────────────┘
                                │ Error
                                ▼
                        ┌─────────────────┐
                        │  Try GPT-4o     │
                        │  (secondary)    │
                        └────────┬────────┘
                                │ Error
                                ▼
                        ┌─────────────────┐
                        │  Rule-based     │
                        │  fallback       │
                        │  (template)     │
                        └─────────────────┘
```

### 8.5 Token Budget Management

| Use Case | Max Input Tokens | Max Output Tokens | Cache Type |
|----------|-----------------|-------------------|------------|
| Document Classification | 8K | 500 | No cache (unique docs) |
| Entity Extraction | 64K | 2K | Semantic cache (similar docs) |
| Question Generation | 4K | 1K | Semantic cache (similar queries) |
| Tax Guidance | 8K | 1K | Full response cache (identical) |
| Deduction Optimization | 4K | 2K | No cache (personalized) |
| General Chat | 16K | 2K | Semantic cache (FAQ) |

### 8.6 Cost Tracking

```typescript
interface LLMCostRecord {
  session_id: string;
  turn_number: number;
  provider: 'anthropic' | 'openai';
  model: string;
  input_tokens: number;
  output_tokens: number;
  cache_hit: boolean;
  latency_ms: number;
  cost_usd: number;       // Computed after response
  cost_inr: number;       // Converted at daily rate
  prompt_template: string; // Version identifier
}

// Monthly budget: $5,000 (estimate at 1M sessions/month)
// Target: < $0.005 per session average
```

---

## 9. Multi-Tenancy Model

### 9.1 Architecture

TaxStox uses a **single-tenant model with logical data isolation** — each user's data is isolated through a combination of row-level access control and encryption.

```
Not multi-tenant in the SaaS sense (no organizations/sub-accounts).
Each "tenant" = end user who files their own taxes.

Isolation strategy:
  1. Every table has a user_id or session_id column
  2. All queries include WHERE user_id = current_user (enforced by RLS)
  3. PII encrypted at column level (different encryption key per user)
  4. No cross-user data access possible (except admin/support with audit)
```

### 9.2 Row-Level Security (PostgreSQL)

```sql
-- Enable RLS on all PII tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE taxpayer_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see their own data
CREATE POLICY user_isolation ON users
    FOR ALL
    USING (id = current_setting('app.current_user_id')::UUID);

-- Admin role bypasses RLS
CREATE POLICY admin_access ON users
    FOR ALL
    USING (current_setting('app.current_role') = 'admin');
```

### 9.3 Encryption Key Hierarchy

```
Master Key (Vault)
  ├── User Encryption Key (per user, derived from Master Key + user_id)
  │     └── Used for: user.name, user.dob, user.phone, user.email
  ├── Document Encryption Key (per session)
  │     └── Used for: S3 server-side encryption of uploaded documents
  └── API Key Encryption Key
        └── Used for: third-party API credentials if stored
```

---

## 10. Seasonal Capacity Planning

### 10.1 Traffic Patterns

```
               ║                                        ║
   Peak Load   ║  ████                                  ║  ████████████
               ║  ████        ████████████████████████  ║  ████████████
               ║  ████  ████  ████████████████████████  ║  ████████████
               ║  ████  ████  ████████████████████████  ║  ████████████
               ║  ████  ████  ████████████████████████  ║  ████████████
               ╚══════════════════════════════════════════════════════════
               Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec

               Note: ITR filing peaks (July 31 deadline, Dec 31 extension)
```

### 10.2 Scaling Strategy

| Resource | Baseline (Off-Peak) | Peak (Jul, Dec) | Multiplier |
|----------|--------------------|------------------|------------|
| API Gateway | 2 pods x 512 MB | 6 pods x 1 GB | 3x |
| User Service | 2 pods x 512 MB | 4 pods x 1 GB | 2x |
| Document Ingestion | 2 pods x 1 GB | 6 pods x 2 GB | 3x |
| OCR Orchestration | 3 pods x 2 GB | 12 pods x 4 GB | 4x |
| Entity Extraction | 2 pods x 1 GB | 6 pods x 2 GB | 3x |
| Validation Engine | 2 pods x 512 MB | 4 pods x 1 GB | 2x |
| Tax Rule Engine | 2 pods x 512 MB | 4 pods x 1 GB | 2x |
| Conversation Service | 4 pods x 1 GB | 12 pods x 2 GB | 3x |
| AI Orchestration | 4 pods x 2 GB | 12 pods x 4 GB | 3x |
| JSON Generation | 2 pods x 512 MB | 4 pods x 1 GB | 2x |
| Audit Service | 2 pods x 512 MB | 3 pods x 512 MB | 1.5x |
| Notification | 2 pods x 256 MB | 4 pods x 512 MB | 2x |
| Reporting | 1 pod x 512 MB | 2 pods x 1 GB | 2x |
| **Total CPU (est.)** | ~32 cores | ~96 cores | 3x |
| **Total RAM** | ~48 GB | ~144 GB | 3x |

### 10.3 Database Scaling

| Resource | Baseline | Peak | Strategy |
|----------|----------|------|----------|
| PostgreSQL CPU | 4 cores | 16 cores | Vertical scale during peak (RDS instance resize) |
| PostgreSQL RAM | 16 GB | 64 GB | Increase shared_buffers, effective_cache_size |
| PostgreSQL Storage | 100 GB | 500 GB | Pre-allocate during scale-up |
| Connections | 100 | 500 | PgBouncer connection pooling |
| Read Replicas | 0 | 2 | Reporting queries routed to replica during peak |
| Redis Memory | 2 GB | 8 GB | Scale up; add replicas for read-heavy workload |

### 10.4 Capacity Planning by Metric

| Metric | Off-Peak (Monthly) | Peak (Monthly) | Growth YoY |
|--------|-------------------|----------------|------------|
| New User Registrations | 5,000 | 50,000 | 3x |
| Active Filing Sessions | 2,000 | 100,000 | 5x |
| Documents Uploaded | 10,000 | 500,000 | 5x |
| OCR Pages Processed | 30,000 | 1,500,000 | 5x |
| LLM API Calls | 50,000 | 2,000,000 | 4x |
| Tax Computations | 2,000 | 100,000 | 5x |
| Storage (new) | 10 GB | 500 GB | 5x |
| Storage (audit) | 5 GB | 50 GB | — (cumulative) |

### 10.5 Auto-Scaling Rules (HPA)

```yaml
# Horizontal Pod Autoscaler configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-orchestration-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-orchestration
  minReplicas: 4
  maxReplicas: 12
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 75
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 100
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 2
          periodSeconds: 120
```

### 10.6 Pre-Season Preparation

| Action | Timeline | Owner |
|--------|----------|-------|
| Load test (10x peak estimated traffic) | T-30 days | QA Engineering |
| Scale infrastructure (provision resources) | T-14 days | DevOps |
| Database VACUUM, ANALYZE, index rebuild | T-7 days | DBA |
| CDN cache warm (static assets, tax slabs) | T-1 day | DevOps |
| Throttle thresholds review | T-7 days | Backend |
| LLM quota increase request (Anthropic) | T-14 days | Engineering |
| Support team onboarding + agent scripts | T-14 days | Product |
| Monitoring dashboards validation | T-7 days | SRE |
| Load shedding plan (graceful degradation) | T-30 days | Architecture |

### 10.7 Graceful Degradation Plan (Under Extreme Load)

```
Load Level 1 (2x peak):   → Reduce AI model complexity (Sonnet instead of Opus)
                            → Increase cache hit ratio (longer TTLs)
                            → Throttle non-critical endpoints (reporting)

Load Level 2 (5x peak):   → Disable deduction optimization AI
                            → Serve cached computation results
                            → Queue document processing (async only)
                            → Static "Please wait" pages for document upload

Load Level 3 (10x peak):  → Emergency mode: manual filing guidance only
                            → Disable AI chat entirely
                            → Basic form-based filing (no document upload)
                            → Queue all non-essential processing
```

---

## Appendix A: Infrastructure as Code (Terraform) Layout

```
terraform/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── staging/
│   │   ├── main.tf
│   │   └── ...
│   └── prod/
│       ├── main.tf
│       └── ...
├── modules/
│   ├── k8s-cluster/
│   ├── postgresql/
│   ├── redis/
│   ├── minio/
│   ├── kafka/
│   ├── rabbitmq/
│   └── monitoring/
└── global/
    ├── iam.tf
    ├── network.tf
    └── dns.tf
```

## Appendix B: Port Mapping

| Service | Internal Port | Protocol |
|---------|--------------|----------|
| API Gateway | 8080 (HTTP), 8443 (HTTPS) | HTTP/REST |
| User Service | 50051 | gRPC |
| Document Ingestion | 50052 | gRPC + REST (upload) |
| OCR Orchestration | 50053 | gRPC |
| Entity Extraction | 50054 | gRPC |
| Validation Engine | 50055 | gRPC |
| Tax Rule Engine | 50056 | gRPC |
| Conversation Service | 50057 | gRPC |
| AI Orchestration | 50058 | gRPC |
| JSON Generation | 50059 | gRPC |
| Audit Service | 50060 | gRPC (consumes Kafka) |
| Notification | 50061 | gRPC |
| Reporting | 8081 | REST |
| Admin Console | 8082 | REST |
| Rate Limiter | 50063 | gRPC |

## Appendix C: Monitoring Stack

```
Grafana Dashboards:
  ┌────────────────────────────────────────────────────┐
  │  1. Service Health (CPU, MEM, QPS, Error Rate)     │
  │  2. API Gateway (Latency P50/P95/P99, Rate Limits) │
  │  3. LLM Usage (Tokens, Cost, Latency, Fallback %)  │
  │  4. Document Pipeline (Upload → OCR → Extraction)  │
  │  5. Filing Pipeline (Session → Computation → ITR)  │
  │  6. Business Metrics (Registrations, Completions)  │
  │  7. Database (Connection pool, Slow queries)       │
  │  8. Redis (Memory, Hit rate, Evictions)            │
  │  9. Kafka (Consumer lag, Throughput, Errors)       │
  │ 10. Cost Dashboard (Infra + API costs)             │
  └────────────────────────────────────────────────────┘

Alerting (PagerDuty):
  - Service error rate > 1% over 5 min
  - P95 latency > 2s for any service
  - LLM provider unavailable (failover triggered)
  - Kafka consumer lag > 1000 messages
  - Disk usage > 80%
  - Redis memory > 80%
```
