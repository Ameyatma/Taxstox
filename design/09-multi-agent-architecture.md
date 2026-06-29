# Multi-Agent AI Architecture: TaxStox

> **Version:** 1.0  
> **Last Updated:** 2026-06-29  
> **Status:** Approved for Implementation  
> **Design Authority:** Principal AI Architect, TaxStox Engineering

---

## Table of Contents

1. [Architecture Philosophy](#1-architecture-philosophy)
2. [Core Principle: AI Orchestrates, Engine Calculates](#2-core-principle-ai-orchestrates-engine-calculates)
3. [Agent Topology: Complete Inventory](#3-agent-topology-complete-inventory)
   - 3.1 [Orchestrator Agent (Master)](#31-orchestrator-agent-master)
   - 3.2 [Document Understanding Agent](#32-document-understanding-agent)
   - 3.3 [Conversation Agent](#33-conversation-agent)
   - 3.4 [Tax Optimization Agent](#34-tax-optimization-agent)
   - 3.5 [Validation & Compliance Agent](#35-validation--compliance-agent)
   - 3.6 [JSON Generation Agent](#36-json-generation-agent)
   - 3.7 [Explainability Agent](#37-explainability-agent)
   - 3.8 [Security & Privacy Agent](#38-security--privacy-agent)
4. [Inter-Agent Communication Protocol](#4-inter-agent-communication-protocol)
5. [Agent Invocation Patterns](#5-agent-invocation-patterns)
6. [Model Selection Strategy](#6-model-selection-strategy)
7. [Agent State Management](#7-agent-state-management)
8. [Tax Rule Engine Integration](#8-tax-rule-engine-integration)
9. [Error Handling & Recovery](#9-error-handling--recovery)
10. [Observability & Monitoring](#10-observability--monitoring)
11. [Performance Budgets & SLAs](#11-performance-budgets--slas)

---

## 1. Architecture Philosophy

TaxStox is designed to deliver an experience indistinguishable from sitting across the desk from a top-tier Chartered Accountant. The architecture rests on four pillars:

1. **AI Orchestrates, Never Calculates**: No LLM ever performs tax computation. All tax math is delegated to a deterministic, auditable Tax Rule Engine. The AI layers exist for judgment, conversation, document understanding, and explanation -- never for arithmetic.
2. **Extract First, Infer Second, Validate Third, Ask Last**: The system exhaustively extracts data from documents before inferring anything. It validates inferences against rules before asking the user. The user is the last resort, not the first.
3. **Explain Everything, Always**: Every tax decision, every deduction claimed, every regime recommendation comes with a plain-English explanation citing specific sections of the Income Tax Act, 1961.
4. **Privacy by Design**: All PII is detected, logged, and access-controlled at the agent level. No agent has unfettered access to all data.

### Design Tenets

| Tenet | Description |
|-------|-------------|
| **Determinism where it matters** | Tax computation, schema generation, validation rules -- deterministic code paths, not LLM outputs |
| **Judgment where it matters** | Document entity extraction confidence, deduction discovery, explanation phrasing -- LLM-powered |
| **Auditability at every step** | Every agent action is logged, traceable, and explainable |
| **Graceful degradation** | If any agent fails, the system degrades gracefully with clear user communication |
| **Cost proportionality** | Expensive model calls (Opus) reserved for the most complex reasoning tasks |

---

## 2. Core Principle: AI Orchestrates, Engine Calculates

This principle is the non-negotiable foundation of the architecture.

### What the AI Layer Does

- Understands natural language tax questions
- Classifies and extracts data from uploaded documents
- Discovers potential deductions based on taxpayer profile
- Generates personalized questions to fill data gaps
- Validates extracted data against known rules
- Explains tax concepts and computations in plain English
- Orchestrates the end-to-end filing flow
- Detects anomalies and potential compliance risks

### What the AI Layer NEVER Does

- Performs arithmetic of any kind
- Calculates tax liability
- Computes rebates or relief
- Generates ITR JSON directly (this is the engine's job, though the AI validates the engine's output)
- Recommends numerical values without engine verification
- Modifies financial data unilaterally

### The Tax Rule Engine

The Tax Rule Engine is a separate, deterministic system that:

- Receives structured query requests from agents via function calls
- Returns structured, typed responses
- Maintains its own audit trail
- Is version-controlled for every assessment year
- Has 100% test coverage for all computation paths
- Is implemented in a separate service with its own deployment lifecycle

### Integration Contract

```typescript
// Every agent-to-engine interaction follows this contract:

interface TaxRuleEngineRequest {
  requestId: string;          // Unique, traceable
  agentId: string;            // Which agent is asking
  sessionId: string;          // Which session
  operationType: TaxOperation; // Enum: COMPUTE_TAX, VALIDATE_DEDUCTION, COMPARE_REGIMES, etc.
  parameters: Record<string, unknown>; // Structured, typed parameters
  timestamp: string;          // ISO 8601
  idempotencyKey: string;     // For safe retries
}

interface TaxRuleEngineResponse {
  requestId: string;
  success: boolean;
  data: Record<string, unknown>; // Always structured, never free text from engine
  computationTrace: ComputationStep[]; // Every intermediate step
  error?: EngineError;
  warnings?: string[];
  timestamp: string;
}
```

---

## 3. Agent Topology: Complete Inventory

### 3.1 Orchestrator Agent (Master)

**Role**: The central nervous system of TaxStox. Every user message, every agent completion, every system event flows through the Orchestrator. It is responsible for session lifecycle, agent routing, conversation flow control, and final response assembly.

**Persona**: The managing partner of a CA firm who knows every client's file, every team member's expertise, and when to step in personally.

#### Core Responsibilities

| Responsibility | Description | Criticality |
|----------------|-------------|-------------|
| Session Management | Initialize, maintain, and terminate user sessions | Critical |
| Intent Classification | Determine what the user needs (file return, ask question, check status) | Critical |
| Agent Routing | Select and invoke the correct sub-agent for each task | Critical |
| Conversation Flow Control | Manage the state machine of the filing process | Critical |
| Context Aggregation | Collect and structure context from all sub-agents | High |
| Final Response Assembly | Compose the user-facing response from agent outputs | Critical |
| Error Handling | Detect agent failures and orchestrate recovery | Critical |
| Escalation | Decide when human intervention is needed | High |
| Token Budget Management | Track and manage context window across the session | High |

#### Tools

| Tool Name | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `route_to_agent` | `agentId: string, task: TaskPayload, context: SessionContext` | `AgentResult` | Routes a task to a specific sub-agent and awaits completion |
| `route_to_agents_parallel` | `tasks: AgentTask[]` | `AgentResult[]` | Fans out multiple tasks to different agents concurrently |
| `get_session_context` | `sessionId: string, scope?: ContextScope` | `SessionContext` | Retrieves current session state from shared context bus |
| `update_session_state` | `sessionId: string, updates: Partial<SessionState>` | `void` | Updates session state (stage, status, flags) |
| `escalate_to_human` | `reason: EscalationReason, context: SessionContext` | `EscalationTicket` | Creates a ticket for human CA intervention |
| `call_tax_engine` | `request: TaxRuleEngineRequest` | `TaxRuleEngineResponse` | Direct line to Tax Rule Engine for the Orchestrator's own needs |
| `detect_intent` | `message: string, history: Message[]` | `UserIntent` | Classifies what the user is trying to do |
| `manage_context_window` | `strategy: CompressionStrategy` | `void` | Compresses or prunes context to stay within token limits |

#### Decision Logic: Agent Routing

The Orchestrator uses a hierarchical intent-to-agent mapping:

```
User Message
  |
  v
[Intent Classification]
  |
  ├── "file_return" ──────> Check filing stage:
  |                            ├── NEW ──────────────> Conversation Agent (onboarding)
  |                            ├── DOCUMENTS_NEEDED ──> Conversation Agent + Document Agent
  |                            ├── DOCUMENTS_UPLOADED ─> Document Understanding Agent
  |                            ├── EXTRACTION_DONE ───> Validation Agent (parallel) + Tax Optimization Agent
  |                            ├── OPTIMIZATION_DONE ─> Orchestrator (manual review) → JSON Generation Agent
  |                            └── JSON_READY ────────> Validation Agent → Explainability Agent → User
  |
  ├── "ask_question" ─────> Tax Optimization Agent (tax questions) OR Document Agent (document questions)
  |                            (based on question classification)
  |
  ├── "check_status" ─────> get_session_context → direct response (no agent needed)
  |
  ├── "explain_something" ─> Explainability Agent
  |
  ├── "upload_document" ──> Document Understanding Agent
  |
  └── "escalate" ─────────> escalate_to_human (direct)
```

#### Session State Machine

```
                    ┌─────────────────────────────────────────────────────┐
                    |                  INITIALIZED                        |
                    |  (User identified, session created, prev context    |
                    |   loaded if returning user)                         |
                    └──────────┬──────────────────────────────────────────┘
                               |
                               v
                    ┌─────────────────────────────────────────────────────┐
                    |                  ONBOARDING                         |
                    |  (Collect basic info: PAN, name, contact,          |
                    |   filing history, employment type)                  |
                    └──────────┬──────────────────────────────────────────┘
                               |
                               v
                    ┌─────────────────────────────────────────────────────┐
               ┌───>|              DOCUMENT_COLLECTION                   |<──┐
               |    |  (Upload portal active, document tracking,         |    |
               |    |   auto-classification on upload)                   |    |
               |    └──────────┬──────────────────────────────────────────┘    |
               |               |                                              |
               |               v                                              |
               |    ┌─────────────────────────────────────────────────────┐    |
               |    |              EXTRACTION_IN_PROGRESS                 |    |
               |    |  (Documents being processed, entities extracted,    |    |
               |    |   confidence scoring)                               |    |
               |    └──────────┬──────────────────────────────────────────┘    |
               |               |                                              |
               |               v                                              |
               |    ┌─────────────────────────────────────────────────────┐    |
               |    |              DATA_VALIDATION                        |────┘ (if validation fails,
               |    |  (Cross-doc validation, rule checks,                |     re-request docs)
               |    |   mismatch detection)                               |
               |    └──────────┬──────────────────────────────────────────┘
               |               |
               |               v
               |    ┌─────────────────────────────────────────────────────┐
               |    |              GATHERING                              |
               |    |  (Conversation Agent asks questions for             |
               |    |   missing/incomplete data, deduces where safe)      |
               |    └──────────┬──────────────────────────────────────────┘
               |               |
               |               v
               |    ┌─────────────────────────────────────────────────────┐
               |    |              OPTIMIZATION                           |
               |    |  (Tax Optimization Agent runs regime comparison,    |
               |    |   deduction discovery, scenario analysis)           |
               |    └──────────┬──────────────────────────────────────────┘
               |               |
               |               v
               |    ┌─────────────────────────────────────────────────────┐
               |    |              REVIEW                                 |
               |    |  (User reviews all data, recommendations,           |
               |    |   explanations; can edit, approve, reject)          |
               |    └──────────┬──────────────────────────────────────────┘
               |               |
               |               v
               |    ┌─────────────────────────────────────────────────────┐
               |    |              JSON_GENERATION                        |
               |    |  (ITR JSON built, schema validated, hash computed)  |
               |    └──────────┬──────────────────────────────────────────┘
               |               |
               |               v
               |    ┌─────────────────────────────────────────────────────┐
               |    |              FINAL_VALIDATION                       |
               |    |  (Full validation suite re-run on generated JSON,   |
               |    |   compliance check, notice prediction)              |
               |    └──────────┬──────────────────────────────────────────┘
               |               |
               |               v
               |    ┌─────────────────────────────────────────────────────┐
               |    |              EXPORT_READY                           |
               |    |  (Filed or exported; summary generated;             |
               |    |   session closed or parked for future)              |
               |    └─────────────────────────────────────────────────────┘
```

#### Orchestrator Prompt Strategy

The Orchestrator uses a tiered prompt approach:

1. **System Prompt** (compressed, high-level): Defines role, core principles, available tools, security boundaries. Never changes within a session.
2. **Session Context** (dynamic, appended): Current stage, user profile summary, key data points, recent conversation history. Updated every turn.
3. **Agent Results** (per-turn, injected): Results from sub-agents formatted as structured summaries.
4. **Compression Trigger**: When total context exceeds 80% of the model's limit, the Orchestrator triggers context compression: it summarizes older conversation turns and prunes low-value context.

---

### 3.2 Document Understanding Agent

**Role**: The document expert. This agent processes every uploaded document, classifies its type, extracts all relevant entities with confidence scores, and cross-references information across multiple documents.

**Persona**: A senior audit senior who has reviewed thousands of tax documents and can spot inconsistencies at a glance.

#### Core Responsibilities

| Responsibility | Description | Criticality |
|----------------|-------------|-------------|
| Document Classification | Identify document type (Form 16, AIS, 26AS, bank statement, etc.) | Critical |
| Entity Extraction | Extract all tax-relevant fields with confidence scores | Critical |
| OCR Error Handling | Detect and flag low-confidence OCR regions | High |
| Cross-Document Validation | Compare extracted entities across documents for consistency | High |
| Format Normalization | Standardize extracted data (dates, amounts, names) | Medium |

#### Document Type Registry

The agent maintains a registry of every supported document type with extraction schemas:

**Form 16 (Part A & Part B)**

| Field | Type | Source | Validation Rule |
|-------|------|--------|-----------------|
| PAN of Employer | String | Part A header | Must match format [A-Z]{5}[0-9]{4}[A-Z] |
| TAN of Employer | String | Part A header | Must match format [A-Z]{4}[0-9]{5}[A-Z] |
| PAN of Employee | String | Part A header | Must match user-provided PAN |
| Name of Employee | String | Part A header | Should match user-provided name |
| Period of Employment | DateRange | Part A | From-To dates logical |
| Gross Salary | Amount | Part B, Section 1 | Must be positive |
| Standard Deduction | Amount | Part B | As per section 16(ia) |
| Professional Tax | Amount | Part B | Must be <= state limit |
| TDS Deducted | Amount | Part B | Must be positive |
| Total Income Chargeable | Amount | Part B | Cross-referenced with AIS |

**AIS (Annual Information Statement)**

| Field | Type | Source | Validation Rule |
|-------|------|--------|-----------------|
| Financial Year | Year | Header | Must be current or past AY |
| PAN | String | Header | Must match user PAN |
| SFT Code | Code | Each entry | Known SFT codes list |
| Transaction Description | String | Each entry | Known descriptions |
| Transaction Amount | Amount | Each entry | Must be positive |
| Reported By | String | Each entry | Known reporting entities |
| AIS Type | Enum | Header | "D" (demand), "PI" (personal info), or "T" (tax) |

**Bank Statements**

| Field | Type | Source | Validation Rule |
|-------|------|--------|-----------------|
| Account Number | String | Header | Masked for privacy |
| IFSC Code | String | Header | Must match format [A-Z]{4}0[A-Z0-9]{6} |
| Account Holder Name | String | Header | Should match user name |
| Period | DateRange | Header | Within filing year |
| Opening Balance | Amount | Header | Check for negative |
| Closing Balance | Amount | Header | Opening + Credits - Debits |
| Interest Income | Amount | Aggregated | Cross-ref with AIS/Schedule |
| Large Deposits | Transaction[] | Filtered | > Rs. 10,00,000 flagged |
| Cash Deposits | Transaction[] | Filtered | > Rs. 50,00,000 flagged for 80G |

**Form 26AS / Tax Credit Statement**

| Field | Type | Source | Validation Rule |
|-------|------|--------|-----------------|
| PAN | String | Header | Must match user PAN |
| TDS/TCS Details | Transaction[] | Each row | Cross-ref with Form 16 |
| SFT Transactions | Transaction[] | Part E | Cross-ref with AIS |
| Tax Paid by Assessee | Amount | Part C | Cross-ref with challans |
| Refund Details | Amount | Part D | Cross-ref with previous returns |

**Rent Receipts / Rent Agreement**

| Field | Type | Source | Validation Rule |
|-------|------|--------|-----------------|
| Landlord Name | String | Agreement | |
| Landlord PAN | String | Agreement | If rent > Rs. 1,00,000/yr, PAN required |
| Tenant Name | String | Agreement | Must match user |
| Monthly Rent | Amount | Agreement | Must be consistent across months |
| Agreement Period | DateRange | Agreement | Must cover at least 1 month in FY |
| Rent Paid Total | Amount | Receipts | Cross-ref with agreement |
| TDS on Rent (if applicable) | Amount | Receipts | Section 194-I |

**Investment Proof Documents**

| Sub-Type | Fields | Deduction Section |
|----------|--------|-------------------|
| Life Insurance Premium | Policy No, Insurer, Premium Amount, Sum Assured | 80C |
| PPF Passbook | PPF Account No, Deposit Amount, Balance | 80C |
| ELSS Statement | Folio No, Investment Amount, Date | 80C |
| NSC Certificate | Certificate No, Investment Amount, Maturity Amount | 80C |
| Tuition Fees | Institution Name, Student Name, Fees Paid, PAN of Institution | 80C |
| Home Loan Statement | Lender Name, Loan Account No, Principal Repaid, Interest Paid | 80C (principal) + 24(b) (interest) |
| Mediclaim Premium | Policy No, Insurer, Premium Amount, Insured Persons | 80D |
| Medical Bills (Senior Citizen) | Hospital Name, Patient Name, Amount, Date | 80D |
| NPS Statement | PRAN, Contribution Amount, Employer Contribution | 80CCD(1B) |
| Education Loan Statement | Lender, Loan Amount, Interest Paid | 80E |
| Donation Receipt | Donee Name, Donee PAN, Amount, Section | 80G |
| Savings Account Interest | Bank, Account No, Interest Amount | TDS on interest |
| Fixed Deposit Certificate | Bank, FD No, Interest Amount, TDS | 80TTA/80TTB |

#### Tools

| Tool Name | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `classify_document` | `fileHash, fileType, ocrText: string` | `DocumentClassification[]` | Returns document type(s) with confidence scores |
| `extract_entities` | `documentId, documentType, ocrText: string` | `ExtractedEntity[]` | Returns all extracted fields with confidence |
| `validate_extraction` | `entities: ExtractedEntity[], docType: string` | `ValidationResult` | Checks internal consistency of extraction |
| `cross_reference_documents` | `documents: ExtractedDocument[]` | `CrossReferenceResult` | Compares entities across all documents |
| `detect_ocr_anomaly` | `ocrText: string, extraction: ExtractedEntity[]` | `OCRAnomaly[]` | Flags regions with potential OCR errors |

#### Entity Extraction Confidence Scoring

| Confidence Level | Threshold | Meaning | Action |
|-----------------|-----------|---------|--------|
| HIGH | >= 95% | System is certain | Auto-accept, no user confirmation needed |
| MEDIUM | 80-94% | System is reasonably sure | Flag for user review, suggest verification |
| LOW | 50-79% | System is uncertain | Ask user to verify, show extracted value vs alternatives |
| CRITICAL_LOW | < 50% | System is guessing | Reject extraction, ask user to input manually, suggest re-upload |

#### Cross-Document Validation

The agent performs these cross-document checks:

| Check | Primary Document | Secondary Document | Action on Mismatch |
|-------|-----------------|-------------------|-------------------|
| PAN Consistency | Form 16 | AIS, 26AS, User Profile | Flag CRITICAL mismatch |
| Gross Salary | Form 16 Part B | AIS (Salary SFT), Form 26AS | Flag MEDIUM if difference > 5% |
| TDS Amount | Form 16 Part B | 26AS (TDS row) | Flag HIGH if TDS not matched |
| Interest Income | AIS | Bank Statements, Form 26AS | Flag MEDIUM |
| Rent Paid | Rent Agreement | AIS (if reported), Bank Statement | Flag MEDIUM |
| Property Sold | AIS | Bank Statement, User Input | Flag MEDIUM |
| Dividend Income | AIS | Form 26AS, Bank Statement | Flag LOW |

---

### 3.3 Conversation Agent

**Role**: The user-facing conversational layer. This agent manages all direct interaction with the taxpayer. It asks questions, clarifies ambiguities, detects confusion, and maintains a natural, empathetic conversation.

**Persona**: A friendly, patient CA who has been doing this for 20 years. Knows when to push and when to back off. Explains complex things simply.

#### Core Responsibilities

| Responsibility | Description | Criticality |
|----------------|-------------|-------------|
| Question Generation | Formulate questions to fill data gaps | Critical |
| Dynamic Adaptation | Adjust question style/depth based on taxpayer profile | High |
| Confusion Detection | Detect when user is confused or frustrated | High |
| Clarification | Resolve ambiguous or incomplete answers | Critical |
| Multi-Language Support | English and Hinglish (Hindi-English mix) | Medium |
| Empathy & Tone | Maintain professional, helpful demeanor | High |
| Stop Condition | Know when enough data has been collected | Critical |

#### Tools

| Tool Name | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `generate_question` | `dataGap: DataGap, userProfile: UserProfile, conversationHistory: Message[]` | `Question` | Generates a question to fill a specific data gap |
| `validate_answer` | `question: Question, answer: string` | `AnswerValidation` | Validates the user's answer (format, consistency, plausibility) |
| `resolve_ambiguity` | `ambiguousAnswer: string, context: SessionContext` | `ResolvedAnswer` | Tries to resolve an ambiguous answer from context |
| `detect_user_confusion` | `message: string, conversationHistory: Message[]` | `ConfusionAssessment` | Detects if user is confused or frustrated |
| `detect_sensitive_topic` | `message: string` | `SensitivityAssessment` | Flags if conversation touches sensitive areas (marital status, health, etc.) |
| `suggest_upload` | `missingDataTypes: DataType[]` | `UploadSuggestion[]` | Suggests documents that would fill multiple data gaps |

#### Conversation Strategy: Extract First, Infer Second, Validate Third, Ask Last

This is the core conversation strategy implemented by this agent:

```typescript
enum ConversationStrategy {
  // Step 1: Try to extract from already-available documents
  EXTRACT_FROM_DOCUMENTS = "extract_from_documents",
  
  // Step 2: Infer from known data patterns and rules
  INFER_FROM_CONTEXT = "infer_from_context",
  
  // Step 3: Validate the inference against rules
  VALIDATE_INFERENCE = "validate_inference",
  
  // Step 4: Ask user (last resort)
  ASK_USER = "ask_user",
}
```

For every data gap, the agent follows this decision tree:

```
Data Gap Identified
  |
  ├── Can this be extracted from an uploaded document?
  |     ├── YES ──> Call Document Agent to extract
  |     |             └── Confidence >= HIGH? ──> Auto-accept
  |     |             └── Confidence MEDIUM? ──> Flag for review
  |     |             └── Confidence LOW? ──> Try inference or ask
  |     └── NO ──> Continue
  |
  ├── Can this be inferred from existing data + tax rules?
  |     ├── YES ──> Call Tax Optimization Agent to infer
  |     |             └── Confidence >= HIGH? ──> Auto-accept with explanation
  |     |             └── Confidence MEDIUM? ──> Present with "Is this correct?"
  |     |             └── Confidence LOW? ──> Ask user
  |     └── NO ──> Continue
  |
  ├── Can this be validated against Tax Rule Engine rules?
  |     ├── YES ──> Validate
  |     |             └── Passes validation? ──> Accept
  |     |             └── Fails validation? ──> Ask user
  |     └── NO ──> Continue
  |
  └── ASK USER ──> Generate question, ask, validate answer
```

#### Question Generation Strategy

Questions follow a tiered approach:

| Tier | Context | Example |
|------|---------|---------|
| **Tier 1: Confirmation** | System is >= 90% confident | "I can see from your Form 16 that your gross salary is Rs. 12,50,000. Is that correct?" |
| **Tier 2: Information** | System has partial data | "I see you have a home loan from SBI. Could you confirm the interest paid during the year?" |
| **Tier 3: Discovery** | System has no data | "Do you have any investments in Public Provident Fund (PPF) or Life Insurance this year?" |
| **Tier 4: Alert** | Potential issue detected | "I noticed a mismatch between the TDS shown on your Form 16 (Rs. 45,000) and Form 26AS (Rs. 42,500). Should we investigate this?" |

#### Dynamic Question Adaptation

The agent adjusts its questioning strategy based on:

1. **Taxpayer Sophistication**: Based on previous filings, occupation, and conversation signals
   - *Salaried first-timer*: More detailed explanations, simpler language, more confirmation questions
   - *Experienced filer*: More efficient, skip basics, focus on changes
   - *Business owner*: More focus on presumptive taxation, advance tax, GST correlation
   - *Senior citizen*: More emphasis on senior citizen benefits, slower pace, patience

2. **Question Fatigue**: After 5+ questions, the agent
   - Offers to batch remaining questions into a checklist
   - Suggests document upload as a faster alternative
   - Provides a "I'll come back to this" option

3. **Session Context**: 
   - First session of the year: Comprehensive
   - Follow-up session: Focus on changes since last session
   - Pre-deadline: Urgency-aware, prioritize critical data

#### Conversation State Machine

```
IDLE ──> QUESTION_SENT ──> AWAITING_ANSWER ──> VALIDATING ──> COMPLETE
                            |                    |
                            v                    v
                         CLARIFICATION      ADJUSTING_QUESTION
                            |
                            v
                         RE_ASK
```

States:
- **IDLE**: Ready for next question or input
- **QUESTION_SENT**: Question displayed to user
- **AWAITING_ANSWER**: Waiting for user response
- **VALIDATING**: Checking user response for validity
- **CLARIFICATION**: User asked for clarification on the question
- **ADJUSTING_QUESTION**: Modifying question based on validation failure
- **RE_ASK**: Re-asking with adjusted framing
- **COMPLETE**: All data gaps filled, ready for next stage

#### Empathy & Tone Guidelines

The agent follows these tone rules:

1. **Use "I" and "we"**: "I can see from your documents..." / "We found a way to save more tax..."
2. **Avoid judgment**: Never say "You should have..." Instead say "For next year, consider..."
3. **Acknowledge emotions**: "I understand tax can be confusing. Let me explain in a simpler way."
4. **Be transparent about AI**: "Based on my analysis of your documents..."
5. **Offer control**: "Would you like me to explain this in detail, or shall we move on?"
6. **Handle sensitive topics carefully**: When asking about health (for 80D), dependents, marital status, use softer framing: "For the purpose of your tax filing, could you let me know..."
7. **Never use emojis in the conversation**: Maintain professional tone.

#### Multi-Language Support Strategy

Hinglish mode is activated when:
- User types in Hinglish (e.g., "Mera PAN card number hai...")
- User's profile indicates Hindi/regional language preference
- User explicitly asks for Hindi or Hinglish

When in Hinglish mode:
- System prompts remain in English (for consistency)
- User-facing questions in Hinglish
- Document extraction results shown bilingually
- Tax terms (section numbers, form names) kept in English for precision

---

### 3.4 Tax Optimization Agent

**Role**: The strategic tax planner. This agent discovers every possible deduction, identifies applicable exemptions, compares tax regimes, generates optimization scenarios, and provides recommendations -- all through function calls to the Tax Rule Engine.

**Persona**: A tax planning specialist who knows every section, every circular, every judgment. Thinks in terms of scenarios and outcomes, not just rules.

#### Core Responsibilities

| Responsibility | Description | Criticality |
|----------------|-------------|-------------|
| Deduction Discovery | Exhaustively find all applicable deductions | Critical |
| Exemption Identification | Identify income exempt under various sections | High |
| Regime Comparison | Old vs New tax regime analysis | Critical |
| Scenario Generation | Create "what-if" scenarios for tax planning | High |
| Recommendation | Provide ranked recommendations with reasoning | High |
| Forward Planning | Suggest tax-saving steps for next year | Medium |

#### Tools

| Tool Name | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `discover_deductions` | `taxpayerProfile: TaxpayerProfile, financialData: FinancialData` | `DeductionDiscovery[]` | Finds all potentially applicable deductions |
| `verify_deduction_eligibility` | `deduction: Deduction, profile: TaxpayerProfile` | `EligibilityResult` | Checks if taxpayer qualifies for a deduction |
| `compare_regimes` | `financialData: FinancialData, ay: string` | `RegimeComparison` | Old vs New regime with break-even analysis |
| `compute_scenario` | `scenario: ScenarioDefinition` | `ScenarioResult` | Computes tax for a specific scenario via engine |
| `generate_recommendation` | `scenarios: ScenarioResult[], profile: TaxpayerProfile` | `Recommendation[]` | Ranks and explains recommendations |
| `detect_missed_deductions` | `historyFinancialData[]` | `MissedDeduction[]` | Flags deductions missed in previous years |
| `apply_alternate_minimum_tax` | `scenario: ScenarioDefinition` | `AMTResult` | Checks AMT applicability via engine |

#### Algorithm for Exhaustive Deduction Discovery

The deduction discovery algorithm follows a systematic, exhaustive approach organized by category:

**Phase 1: Category Enumeration**

For each deduction category, the agent enumerates all possible sections:

```
SECTION 80 FAMILY (80C, 80CCC, 80CCD)
  ├── 80C: PPF, EPF, LIC, ELSS, NSC, Tuition Fees, Principal on Home Loan,
  |        5-year FDs, Sukanya Samriddhi, Senior Citizen Savings Scheme,
  |        Post Office Time Deposit, ULIP, Contribution to Pension Fund,
  |        Stamp duty on house property, NABARD bonds
  ├── 80CCC: Pension fund contributions
  └── 80CCD(1): NPS employee contribution (up to 10% of salary)
     80CCD(1B): Additional NPS (up to Rs. 50,000)
     80CCD(2): Employer NPS contribution

SECTION 80D: HEALTH INSURANCE
  ├── Self + Family: Premium up to Rs. 25,000 (Rs. 50,000 for senior citizens)
  ├── Parents: Premium up to Rs. 25,000 (Rs. 50,000 for senior citizens)
  └── Preventive Health Checkup: Up to Rs. 5,000 (within overall limit)

SECTION 80E: EDUCATION LOAN INTEREST
  └── No upper limit, for higher education, only interest component

SECTION 80EE/80EEA: HOME LOAN (FIRST TIME)
  ├── 80EE: Interest on home loan for first-time buyers (up to Rs. 50,000)
  └── 80EEA: Interest on home loan for affordable housing (up to Rs. 1,50,000)

SECTION 80G: DONATIONS
  ├── 50% without restriction (e.g., PM Relief Fund)
  ├── 100% without restriction (e.g., PM CARES)
  ├── 50% with restriction (eligible funds)
  └── 100% with restriction (specified funds)

SECTION 80GG: RENT (NO HRA)
  └── Minimum of: Rs. 5,000/month, 25% of total income, excess of rent over 10% of income

SECTION 80TTA/80TTB: SAVINGS ACCOUNT INTEREST
  ├── 80TTA: Up to Rs. 10,000 (general)
  └── 80TTB: Up to Rs. 50,000 (senior citizens)

SECTION 80U: DISABILITY
  ├── 40-80% disability: Rs. 75,000
  └── 80%+ disability: Rs. 1,25,000

OTHER KEY SECTIONS
  ├── 24(b): Home loan interest (up to Rs. 2,00,000 for self-occupied)
  ├── 54: Capital gains exemption on sale of house (reinvestment)
  ├── 54F: Capital gains exemption on sale of other assets (house purchase)
  ├── 54EC: Capital gains exemption via bonds (up to Rs. 50,00,000)
  ├── 10(13A): HRA exemption
  ├── 10(14): Special allowance (LTA, conveyance, etc.)
  └── 16(ia): Standard deduction (Rs. 50,000)
```

**Phase 2: Eligibility Checking**

For each discovered deduction, the agent:

1. Checks if the taxpayer profile matches the deduction's eligibility criteria (income type, age, etc.)
2. Checks if supporting documents exist or need to be requested
3. Checks if the deduction is applicable under the chosen regime (many 80-series deductions don't apply to New Regime)
4. Assigns a priority score based on tax impact

**Phase 3: Regime-Appropriate Filtering**

Documents which deductions apply under CURRENT regime selection (or computes both for comparison):
- New Regime (FY 2025-26): Only standard deduction, 80CCD(2), and some specific deductions apply
- Old Regime: All deductions apply

**Phase 4: Optimization Discovery**

The agent generates scenarios:
1. **Maximum savings scenario**: Old regime with all possible deductions claimed
2. **Simplest scenario**: New regime with minimal deduction tracking
3. **Hybrid scenarios**: Mix of both (income types eligible for both can be split)
4. **Forward-looking scenarios**: "If you invest X in NPS, your tax could be Y"

#### Regime Comparison Methodology

The comparison between Old and New Tax Regimes involves:

1. **Data Collection**: Gather all income heads, all potential deductions
2. **Engine Query (Old Regime)**: 
   - Compute total income (all heads)
   - Apply all eligible deductions (Chapter VI-A, Section 24, etc.)
   - Compute tax as per old regime slabs
   - Apply rebate under Section 87A
   - Add surcharge and cess
3. **Engine Query (New Regime)**:
   - Compute total income (all heads, no deductions except standard + 80CCD(2))
   - Compute tax as per new regime slabs (FY 2025-26 slabs)
   - Apply rebate under Section 87A (if applicable per regime)
   - Add surcharge and cess
4. **Comparison**:
   - Net tax payable under both regimes
   - Break-even analysis (how much deduction needed to match new regime)
   - Compliance burden comparison (documentation needed for old regime)
   - Recommendation with rationale

#### How the Agent Uses the Tax Rule Engine

The Tax Optimization Agent **never calculates** anything. Every computation follows this pattern:

```typescript
// WRONG: Agent calculates
const tax = (income - deductions) * slabRate; // NEVER DO THIS

// RIGHT: Agent queries engine
const response = await call_tax_engine({
  requestId: generateUUID(),
  agentId: "tax_optimization_agent",
  sessionId: sessionId,
  operationType: TaxOperation.COMPUTE_TAX,
  parameters: {
    regime: "old",
    ay: "2025-26",
    incomeHeads: { salary: 1250000, houseProperty: 0, ... },
    deductions: { section80C: 150000, section80D: 25000, ... },
    exemptions: { hra: 240000, lta: 50000, ... },
  },
  idempotencyKey: `compute_old_${sessionId}_v1`,
});

// Use the response for analysis and recommendation
```

---

### 3.5 Validation & Compliance Agent

**Role**: The quality and compliance guardian. This agent runs over 400 validation rules across all extracted data, detects mismatches, computes risk scores, and predicts potential notice scenarios.

**Persona**: An IRS (Income Tax Department) audit veteran who has seen every mistake, every mismatch, and every red flag that triggers a scrutiny notice.

#### Core Responsibilities

| Responsibility | Description | Criticality |
|----------------|-------------|-------------|
| Validation Rule Execution | Run all applicable validation rules against taxpayer data | Critical |
| Mismatch Detection | Identify inconsistencies across data sources | Critical |
| Risk Scoring | Compute overall and category-wise risk scores | High |
| Notice Prediction | Predict which mismatches could trigger department notices | High |
| Compliance Flagging | Flag non-compliance with specific provisions | High |
| Data Quality Assessment | Assess overall quality and completeness of data | Medium |

#### Tools

| Tool Name | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `run_validation_rule` | `ruleId: string, data: TaxpayerData, context: ValidationContext` | `ValidationRuleResult` | Execute a single validation rule |
| `run_validation_category` | `category: ValidationCategory, data: TaxpayerData` | `ValidationCategoryResult` | Run all rules in a category |
| `run_all_validations` | `data: TaxpayerData` | `ValidationSuiteResult` | Run all applicable rules |
| `detect_mismatch` | `dataPoints: DataPoint[]` | `MismatchResult[]` | Check for cross-data inconsistencies |
| `compute_risk_score` | `validations: ValidationResult[], mismatches: MismatchResult[], profile: TaxpayerProfile` | `RiskScore` | Compute overall risk of audit/notice |
| `generate_notice_prediction` | `risks: RiskScore, mismatches: MismatchResult[]` | `NoticePrediction[]` | Predict specific notices that may be issued |

#### Validation Rule Categories

The agent maintains 400+ validation rules organized into these categories:

**Category 1: Personal Information (Rules 1-25)**

| Rule ID | Description | Severity |
|---------|-------------|----------|
| PI001 | PAN format validation (5 letters + 4 numbers + 1 letter) | CRITICAL |
| PI002 | PAN status check against NSDL database (active/suspended/inactive) | CRITICAL |
| PI003 | Name consistency across all documents | HIGH |
| PI004 | Date of birth format and consistency | HIGH |
| PI005 | Aadhaar format validation (12 digits) | MEDIUM |
| PI006 | Address consistency across documents | MEDIUM |
| PI007 | Mobile number format verification | LOW |
| PI008 | Email format verification | LOW |
| PI009 | Bank account IFSC code validation | MEDIUM |
| PI010 | Bank account number format validation | MEDIUM |

**Category 2: Income Consistency (Rules 26-80)**

| Rule ID | Description | Severity |
|---------|-------------|----------|
| IC001 | Gross Salary matches across Form 16 and AIS | HIGH |
| IC002 | TDS matches across Form 16 and 26AS | CRITICAL |
| IC003 | All AIS entries are accounted for in return | HIGH |
| IC004 | Interest income from savings matches Form 26AS | MEDIUM |
| IC005 | Rent income matches AIS reported rent | MEDIUM |
| IC006 | Capital gains from AIS match bank statement | HIGH |
| IC007 | Dividend income from AIS is reported | MEDIUM |
| IC008 | Income from other sources fully declared | HIGH |
| IC009 | Business income consistent with ITR history | MEDIUM |
| IC010 | Salary income less than max employer exemption limit per PAN | HIGH |

**Category 3: Deduction Validation (Rules 81-150)**

| Rule ID | Description | Severity |
|---------|-------------|----------|
| DV001 | 80C total within Rs. 1,50,000 limit | HIGH |
| DV002 | 80C sub-limits checked (EPF, PPF, etc. are within individual limits) | MEDIUM |
| DV003 | 80CCD(1B) within Rs. 50,000 limit | HIGH |
| DV004 | 80CCD(2) computed correctly (10% of salary) | HIGH |
| DV005 | 80D self+family within Rs. 25,000 limit | HIGH |
| DV006 | 80D parents within Rs. 25,000/50,000 limit | HIGH |
| DV007 | 80D preventive health checkup within Rs. 5,000 sub-limit | MEDIUM |
| DV008 | 80E only interest component claimed | HIGH |
| DV009 | 80EE/80EEA eligibility verified (first-time, loan date, etc.) | HIGH |
| DV010 | 24(b) home loan interest within Rs. 2,00,000 for self-occupied | HIGH |
| DV011 | 80G donee PAN verified against approved list | HIGH |
| DV012 | 80G eligible percentage applied correctly | HIGH |
| DV013 | HRA exemption under 10(13A) computed correctly | HIGH |
| DV014 | Standard deduction under 16(ia) is Rs. 50,000 | MEDIUM |
| DV015 | Professional tax limited to state ceiling | MEDIUM |
| DV016 | LTA exemption supported by travel proof (at least 2 journeys in block) | MEDIUM |
| DV017 | 80TTA within Rs. 10,000 (non-senior) | MEDIUM |
| DV018 | 80TTB within Rs. 50,000 (senior citizen) | MEDIUM |
| DV019 | Deductions claimed under New Regime flagged (invalid) | CRITICAL |
| DV020 | Deductible donations cross-referenced with 80G receipt amounts | HIGH |

**Category 4: TDS/TCS Validation (Rules 151-200)**

| Rule ID | Description | Severity |
|---------|-------------|----------|
| TD001 | All TDS entries in 26AS are claimed as credit | CRITICAL |
| TD002 | TDS rate matches section (194C vs 194J, etc.) | MEDIUM |
| TD003 | TDS on salary matches Form 16 Part B | CRITICAL |
| TD004 | TDS on interest matches bank certificate | HIGH |
| TD005 | TDS on rent matches 194I provisions | MEDIUM |
| TD006 | TDS on professional fees matches 194J provisions | MEDIUM |
| TD007 | TCS entries properly accounted | MEDIUM |
| TD008 | TDS refund claimed correctly | HIGH |
| TD009 | Section 206AA (30% TDS if no PAN) checked | MEDIUM |

**Category 5: Capital Gains (Rules 201-240)**

| Rule ID | Description | Severity |
|---------|-------------|----------|
| CG001 | All asset sales from AIS are reported | CRITICAL |
| CG002 | Holding period correctly classified (short vs long term) | HIGH |
| CG003 | Indexation applied correctly for long-term assets | HIGH |
| CG004 | Section 54 exemption valid (new house purchased/constructed) | HIGH |
| CG005 | Section 54F exemption valid (all conditions met) | HIGH |
| CG006 | Section 54EC investment within Rs. 50,00,000 and 6 months | HIGH |
| CG007 | Capital gains on shares match brokerage statement | MEDIUM |
| CG008 | STT paid verified for listed securities | MEDIUM |

**Category 6: Business/Professional Income (Rules 241-280)**

| Rule ID | Description | Severity |
|---------|-------------|----------|
| BP001 | Gross receipts consistent with AIS/GST returns | HIGH |
| BP002 | Presumptive taxation (44ADA/44AD) eligibility verified | HIGH |
| BP003 | Audit requirement under 44AB checked (threshold: Rs. 1 cr/50L) | HIGH |
| BP004 | Advance tax payments matched | HIGH |
| BP005 | GST turnover matches income declared | MEDIUM |
| BP006 | Expense claims proportional to industry standards | MEDIUM |

**Category 7: Regime-Specific (Rules 281-310)**

| Rule ID | Description | Severity |
|---------|-------------|----------|
| RS001 | No 80-series deductions claimed under New Regime | CRITICAL |
| RS002 | HRA not claimed under New Regime | HIGH |
| RS003 | LTA not claimed under New Regime | HIGH |
| RS004 | Home loan interest under 24(b) not claimed under New Regime | HIGH |
| RS005 | Form 10-IEA filed if opting for New Regime | MEDIUM |
| RS006 | Opt-out filed correctly if switching back to Old Regime | MEDIUM |

**Category 8: Data Quality (Rules 311-350)**

| Rule ID | Description | Severity |
|---------|-------------|----------|
| DQ001 | All required fields are present | CRITICAL |
| DQ002 | No negative values in income fields | HIGH |
| DQ003 | Dates are within the correct financial year | HIGH |
| DQ004 | No duplicate entries | MEDIUM |
| DQ005 | Rounding rules applied correctly | LOW |
| DQ006 | Currency in INR and consistent format | LOW |

**Category 9: Cross-Year Consistency (Rules 351-380)**

| Rule ID | Description | Severity |
|---------|-------------|----------|
| CY001 | Income trend is consistent (no unexplained 300% jump) | MEDIUM |
| CY002 | Deductions claimed are consistent with pattern | MEDIUM |
| CY003 | Regime choice is consistent or change is explained | MEDIUM |
| CY004 | No double claim of same deduction across years | HIGH |
| CY005 | Capital loss carried forward correctly applied | HIGH |

**Category 10: Compliance & Filing (Rules 381-400)**

| Rule ID | Description | Severity |
|---------|-------------|----------|
| CF001 | Filing deadline check (July 31 / extended) | HIGH |
| CF002 | Belated return applicability (Section 139(4)) check | HIGH |
| CF003 | Revised return window (Section 139(5)) checked | MEDIUM |
| CF004 | Audit report (10BB/10BD) attached if required | CRITICAL |
| CF005 | Form 12BB submitted for HRA/LTA claims | MEDIUM |
| CF006 | Form 56F filed for capital gains exemptions | MEDIUM |
| CF007 | Schedule VDA for virtual digital assets declared | HIGH |
| CF008 | Schedule AL for assets > Rs. 50 lakhs | MEDIUM |

#### Severity Classification

| Severity | Meaning | User Impact | System Action |
|----------|---------|-------------|---------------|
| **CRITICAL** | Definitely wrong, will cause notice/rejection | Blocking | Cannot proceed without resolution |
| **HIGH** | Likely wrong, high chance of notice | Must address | Must be resolved before filing |
| **MEDIUM** | Probably wrong, should be reviewed | Should address | Recommend resolution, allow proceeding |
| **LOW** | Minor issue, unlikely to cause problem | Informational | Inform user, proceed automatically |
| **INFO** | Recommendation for future | Not actionable | Log for next year planning |

#### Risk Scoring Methodology

The risk score is computed as:

```
Overall Risk = BaseRisk × CategoryMultiplier × AnomalyFactor × VolumeAdjustment

Where:
  BaseRisk = Σ(ValidationWeight × SeverityWeight × (1 - MismatchResolutionProbability))
             for all failed validations
  
  CategoryMultiplier = Σ(CategoryWeight) based on which categories have failures
  
  AnomalyFactor = 1.0 + 0.1 × NumberOfCRITICALFailures + 0.05 × NumberOfHIGHFailures
  
  VolumeAdjustment = log10(TotalIncome/100000) × 0.1  (higher income = higher scrutiny risk)
```

Risk score is normalized to 0-100 and classified as:

| Score Range | Classification | Meaning |
|-------------|---------------|---------|
| 0-15 | LOW | No concern, file normally |
| 16-35 | MODERATE | Some mismatches, probably minor |
| 36-60 | ELEVATED | Multiple issues, review recommended |
| 61-80 | HIGH | Significant issues, resolution critical before filing |
| 81-100 | VERY HIGH | Near-certain notice, professional CA consultation recommended |

#### Notice Prediction Logic

The agent predicts potential Income Tax Department notices based on:

1. **Common Scrutiny Triggers**:
   - Large mismatch between Form 26AS TDS and claimed TDS
   - High-value property transactions not matching income profile
   - Large cash deposits not aligned with reported income
   - Foreign remittances without proper disclosure
   - 80G donations to non-approved institutions
   - HRA claims without supporting rent agreement

2. **Departmental Focus Areas** (updated per AY based on CBDT instructions):
   - Specific SFT codes flagged for high-value transactions
   - Industry-specific scrutiny patterns
   - Geographical patterns of non-compliance

3. **Predictive Output**:
   - Notice type (Scrutiny under 143(2), Intimation under 143(1), etc.)
   - Probability score (LOW/MEDIUM/HIGH)
   - Reasons for prediction
   - Mitigation steps (specific actions to reduce risk)

---

### 3.6 JSON Generation Agent

**Role**: The ITR schema specialist. This agent compiles all validated data into the correct ITR form (ITR-1, ITR-2, ITR-3, ITR-4, etc.), constructs the JSON following the Income Tax Department schema exactly, validates the output, and generates export-ready files.

**Persona**: The meticulous tax return preparer who has memorized every schema field, every ITR form rule, and every validation requirement of the Income Tax Department's e-filing portal.

#### Core Responsibilities

| Responsibility | Description | Criticality |
|----------------|-------------|-------------|
| ITR Form Selection | Determine the correct ITR form based on taxpayer profile | Critical |
| JSON Construction | Build the ITR JSON payload per department schema | Critical |
| Schema Validation | Validate JSON against the official ITR schema | Critical |
| Computation Integration | Integrate Tax Rule Engine computations into JSON | Critical |
| Hash & Integrity | Compute and embed integrity hashes | High |
| Export Instructions | Generate filing instructions for the user | Medium |

#### Tools

| Tool Name | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `select_itr_form` | `profile: TaxpayerProfile, incomeSources: IncomeSource[]` | `ITRFormSelection` | Determines correct ITR form |
| `build_itr_json` | `formType: ITRForm, data: StructuredTaxData, computations: EngineComputation[]` | `ITRJSON` | Builds the JSON payload |
| `validate_against_schema` | `json: ITRJSON, formType: ITRForm` | `SchemaValidationResult` | Validates JSON against schema |
| `compute_hash` | `json: ITRJSON` | `string` | Computes integrity hash |
| `generate_export_instructions` | `formType: ITRForm, filingMethod: FilingMethod` | `ExportInstructions` | Step-by-step filing guide |

#### ITR Form Selection Logic

```typescript
function selectITRForm(profile: TaxpayerProfile, incomeSources: IncomeSource[]): ITRForm {
  if (incomeSources.capitalGains || incomeSources.foreignAssets) {
    if (profile.hasBusinessIncome) return ITRForm.ITR_3;
    if (profile.hasCryptocurrency) return ITRForm.ITR_2; // Schedule VDA
    return ITRForm.ITR_2;
  }
  
  if (profile.hasBusinessIncome) {
    if (profile.isPresumptiveTaxation && profile.businessReceipts <= 2000000) {
      return ITRForm.ITR_4;
    }
    return ITRForm.ITR_3;
  }
  
  if (profile.isSalaried && 
      incomeSources.propertyIncome <= 0 && 
      !incomeSources.capitalGains &&
      incomeSources.otherSources <= 50000) {
    return ITRForm.ITR_1;
  }
  
  return ITRForm.ITR_2;
}
```

#### JSON Construction Rules

1. **Schema Fidelity**: The JSON must exactly match the official Income Tax Department schema for the AY
2. **Schema Version**: Tracked per AY; agent is initialized with the correct schema version
3. **Field Ordering**: Fields must follow schema ordering
4. **Optional Fields**: Omitted if not applicable (never populate with null or empty string)
5. **Amount Fields**: Always in whole rupees (no paise), rounded per Section 288A
6. **String Truncation**: Schema-defined max lengths enforced
7. **Enum Validation**: Only schema-defined enum values accepted
8. **Date Formats**: Strict ISO date format (YYYY-MM-DD)
9. **PAN Format**: Uppercase, no spaces, no special characters

#### Data Compilation Process

```
All Validated Data
  |
  v
[Schema Field Mapping]
  |  Maps each data point to the correct JSONPath in the schema
  |
  v
[Computation Integration]
  |  Inserts Tax Rule Engine results into the correct schema fields
  |  (tax payable, rebate, interest, etc.)
  |
  v
[Rules Engine]
  |  Applies schema-level rules (conditional fields, etc.)
  |
  v
[JSON Assembly]
  |  Builds the complete JSON object
  |
  v
[Schema Validation]
  |  Validates against official schema (using JSON Schema validator)
  |  If FAILS ──> Debug, fix, re-validate
  |
  v
[Hash & Seal]
  |  Computes integrity hash, prepares export
```

---

### 3.7 Explainability Agent

**Role**: The translator of tax complexity to human understanding. This agent takes every tax computation, every deduction, every recommendation, and every validation finding and converts it into plain English explanations that any taxpayer can understand.

**Persona**: A chartered accountant who also happens to be a brilliant teacher. Can explain the most complex tax provisions in a way that makes perfect sense to a first-time filer.

#### Core Responsibilities

| Responsibility | Description | Criticality |
|----------------|-------------|-------------|
| Computation Explanation | Explain how each tax figure was derived | Critical |
| Deduction Rationale | Explain why each deduction is valid and its tax impact | Critical |
| Regime Choice Explanation | Explain why one regime is better than another | Critical |
| Recommendation Justification | Justify each recommendation with evidence | High |
| Risk Explanation | Explain validation findings and notice predictions | High |
| Audit Trail Generation | Create a complete audit trail for CA review | Medium |
| Forward Planning Advice | Suggest tax-saving measures for next year | Medium |

#### Tools

| Tool Name | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `explain_computation` | `computation: EngineComputation, userLevel: UserKnowledgeLevel` | `Explanation` | Plain-English computation explanation |
| `explain_deduction` | `deduction: Deduction, savings: Amount, context: TaxContext` | `Explanation` | Deduction rationale and impact |
| `explain_regime_choice` | `comparison: RegimeComparison` | `Explanation` | Why one regime was chosen |
| `explain_validation_result` | `result: ValidationResult` | `Explanation` | What a validation means and its impact |
| `generate_audit_summary` | `session: SessionContext` | `AuditSummary` | Complete audit-ready summary |
| `generate_forward_planning` | `profile: TaxpayerProfile, missedDeductions: MissedDeduction[]` | `PlanningAdvice[]` | Next year tax planning tips |

#### Explanation Generation Principles

1. **Start with the bottom line**: "You will save Rs. 15,000 in taxes by claiming this deduction."
2. **Then explain the "why"**: "This is because Section 80C allows you to deduct up to Rs. 1,50,000 of your eligible investments from your total income."
3. **Then the "how"**: "Your investment of Rs. 1,50,000 in PPF reduces your taxable income from Rs. 10,00,000 to Rs. 8,50,000."
4. **Adapt to user knowledge level**:
   - *First-timer*: Simple examples, avoid jargon
   - *Regular filer*: Standard terminology
   - *CA/lawyer*: Technical depth, section references
5. **Use tables and comparisons** for numerical explanations
6. **Always cite specific sections** of the Income Tax Act, 1961
7. **Avoid absolute certainty** about legal judgments: "Based on current interpretation..."
8. **Distinguish between tax saved vs. tax refunded**: "You paid Rs. 50,000 as TDS, but your actual tax is only Rs. 35,000, so you get a refund of Rs. 15,000."

#### Audit Trail Components

The audit summary includes:

1. **Data Sources**: Every document used, with upload timestamp and extraction confidence
2. **Computations**: Every computation performed by the Tax Rule Engine, with parameters and results
3. **Decisions Made**: Every regime choice, deduction selection, with rationale
4. **Validation Results**: All validation rules run, with pass/fail and severity
5. **User Verifications**: Every data point verified by the user
6. **Agent Actions**: All agent invocations with inputs and outputs
7. **Exported Files**: JSON hash, form type, export timestamp

---

### 3.8 Security & Privacy Agent

**Role**: The guardian of taxpayer data. This agent monitors every data access, detects potential PII leaks, flags anomalous behavior, and ensures GDPR-quality privacy handling for Indian tax data.

**Persona**: The vigilant data protection officer who reviews every access request, checks every data flow, and ensures no sensitive information leaves its authorized boundary.

#### Core Responsibilities

| Responsibility | Description | Criticality |
|----------------|-------------|-------------|
| PII Detection | Identify Personal Identifiable Information in all data flows | Critical |
| Data Access Logging | Log every access to taxpayer data by any agent | Critical |
| Anomaly Detection | Flag unusual patterns of data access or conversation | High |
| Access Control Verification | Verify agents only access data they're authorized for | Critical |
| Data Masking | Ensure PII is masked in logs and non-essential displays | High |
| Encryption Verification | Verify data is encrypted at rest and in transit | Critical |

#### Tools

| Tool Name | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `detect_pii_leak` | `data: any, context: AccessContext` | `PIIAssessment` | Scans data for PII exposure |
| `log_data_access` | `accessRecord: AccessRecord` | `void` | Logs every data access |
| `flag_suspicious_activity` | `activity: Activity, sessionContext: SessionContext` | `SecurityAlert` | Flags suspicious behavior |
| `verify_agent_authorization` | `agentId: string, dataCategory: DataCategory` | `AuthorizationResult` | Verifies agent is authorized |
| `mask_pii` | `data: any, piiFields: PIICategory[]` | `MaskedData` | Masks PII fields for non-essential contexts |
| `generate_privacy_summary` | `sessionId: string` | `PrivacySummary` | Reports all data access during session |

#### PII Categories

| Category | Examples | Masking Rule |
|----------|----------|--------------|
| **Identity PII** | PAN, Aadhaar, Name, DOB | Full mask in logs (PAN: ****1234) |
| **Financial PII** | Bank accounts, credit cards, investment details | Mask account numbers (XXXX1234) |
| **Contact PII** | Phone, email, address | Mask partially (phone: ******7890) |
| **Biographical PII** | Employment history, education | Full access only to authorized agents |
| **Sensitive PII** | Medical records (80D), disability (80U), marital status | Minimal access, never to LLM if avoidable |

#### Anomaly Detection Rules

The agent monitors for:

1. **Rapid-fire data access**: Multiple different agents accessing data in quick succession
2. **Unusual data volume**: Single agent requesting much more data than typical for its function
3. **Strange hours access**: Agent activity outside normal patterns
4. **Escalation pattern**: Multiple escalations to human in short period (could indicate adversarial testing)
5. **Prompt injection attempts**: User messages containing prompt manipulation patterns
6. **Data exfiltration patterns**: Repetitive queries that seem to be extracting data systematically

---

## 4. Inter-Agent Communication Protocol

### 4.1 Message Format

All inter-agent communication follows a standardized message envelope:

```typescript
interface AgentMessage {
  messageId: string;           // UUID v4
  correlationId: string;       // Ties together related messages across agents
  sourceAgentId: string;       // Agent ID of sender
  targetAgentId: string;       // Agent ID of receiver (or "orchestrator" for routing)
  messageType: MessageType;    // REQUEST, RESPONSE, ERROR, EVENT, INFO
  payload: unknown;            // Type-specific payload
  priority: MessagePriority;   // LOW, MEDIUM, HIGH, CRITICAL
  timestamp: string;           // ISO 8601
  contextSnapshot?: SessionContextSnapshot;  // Lightweight context reference
  traceFlags: TraceFlag[];     // For observability
  expiresAt?: string;          // TTL for time-sensitive messages
}
```

### 4.2 Shared Context Bus

All agents share context through a centralized Context Bus that maintains:

1. **Session State**: Current stage, status, flags (immutable history + mutable current)
2. **Extracted Data**: All document extractions with confidence scores
3. **User Profile**: Taxpayer demographic and filing profile
4. **Financial Data**: All financial data points organized by income head and deduction category
5. **Validation Results**: All validation rule results
6. **Conversation History**: Recent conversation (last N turns, summarized beyond that)
7. **Computation Results**: All Tax Rule Engine computation results
8. **Risk Assessment**: Current risk score and notice predictions

**Access Pattern**: Agents READ from the context bus and WRITE back to it. The Orchestrator is the only agent that can invalidate context. All writes are append-only to maintain audit trail.

### 4.3 Conflict Resolution Protocol

When agents disagree on data or interpretation:

| Scenario | Resolution Strategy | Escalation |
|----------|-------------------|------------|
| Document Agent and Conversation Agent disagree on entity value | Rule Engine is consulted as tiebreaker | If still disagree, flag for user |
| Tax Optimization Agent recommends both regimes equally | Validation Agent checks compliance for both; user decides | Explain both, let user choose |
| Validation Agent flags error that Tax Optimization Agent says is fine | Orchestrator runs independent validation | If still conflicting, escalate to human |
| Explainability Agent gives unclear explanation | Orchestrator asks Conversation Agent to rephrase | After 3 attempts, escalate |

### 4.4 Escalation Paths

```typescript
enum EscalationLevel {
  LEVEL_1 = "agent_review",        // Another agent reviews and resolves
  LEVEL_2 = "orchestrator_review",  // Orchestrator decides
  LEVEL_3 = "user_review",          // User is asked to decide
  LEVEL_4 = "human_ca_review",      // Human CA via dashboard
  LEVEL_5 = "engineering_review",   // Platform engineers (bug/system issue)
}
```

Escalation triggers:
- **LEVEL_1**: Minor validation conflict between agents
- **LEVEL_2**: Data that doesn't fit any known pattern; multiple agent conflicts
- **LEVEL_3**: User data verification; regime choice; confirmation of unusual scenarios
- **LEVEL_4**: Tax position that requires professional judgment; potential fraud indicators; taxpayer request for human CA
- **LEVEL_5**: System errors; unexpected LLM behavior; agent crashes

---

## 5. Agent Invocation Patterns

### 5.1 Sequential Chains

Used when steps have strict dependencies:

```
Document Uploaded
  → classify_document
  → extract_entities
  → validate_extraction
  → [return to Orchestrator]
```

```
Tax Optimization Flow
  → discover_deductions
  → verify_deduction_eligibility (for each candidate)
  → compare_regimes
  → compute_scenario (for each relevant scenario)
  → generate_recommendation
```

### 5.2 Parallel Fan-Out

Used when multiple independent checks can run simultaneously:

```
After Extraction Complete:
  ┌── Validation Agent: run_all_validations
  ├── Security Agent: detect_pii_leak
  ├── Tax Optimization Agent: discover_deductions
  └── Conversation Agent: identify_data_gaps
  └── [all results collated by Orchestrator]
```

```
After JSON Generation:
  ┌── Validation Agent: re-run critical validations
  ├── Schema validation
  └── Security Agent: final PII scan
```

### 5.3 Conditional Branching

Based on taxpayer profile:

```
If user.isSalaried:
  → Conversation (salary-specific questions)
  → Tax Opt (80C, 80D focus)
  → ITR-1 or ITR-2

If user.hasBusinessIncome:
  → Conversation (business-specific questions, 44AD/44ADA)
  → Document (ledger, balance sheet)
  → Tax Opt (business deductions)
  → ITR-3 or ITR-4

If user.hasCapitalGains:
  → Document (brokerage statements, sale deeds)
  → Tax Opt (54, 54F, 54EC analysis)
  → ITR-2 or ITR-3

If user.hasForeignAssets:
  → Conversation (foreign income, foreign accounts)
  → Document (foreign bank statements)
  → Tax Opt (FEMA, double taxation relief)
  → Schedule FA, ITR-2 or ITR-3
```

### 5.4 Retry Patterns

| Failure Type | Retry Strategy | Max Retries |
|-------------|----------------|-------------|
| Tax Rule Engine timeout | Exponential backoff: 1s, 2s, 4s, 8s | 4 |
| LLM model unavailability | Fallback to next cheaper model | 3 (across models) |
| JSON schema validation failure | Rebuild JSON with debug log | 2 (escalate on 3rd) |
| Document extraction low confidence | Re-extract with different OCR preprocessing | 2 |
| Agent response validation failure | Regenerate agent response with stricter constraints | 2 |
| Network timeout | Exponential backoff + circuit breaker | 3 |

---

## 6. Model Selection Strategy

### 6.1 Model-to-Agent Mapping

| Agent | Primary Model | Fallback Model | Rationale |
|-------|--------------|----------------|-----------|
| Orchestrator | Claude Opus (claude-opus-4) | Claude Sonnet + stricter routing | Maximizes judgment quality for routing decisions |
| Document Understanding | Claude Haiku (claude-haiku-3) | Claude Sonnet for low-confidence cases | Speed + cost; only complex cases need bigger model |
| Conversation | Claude Sonnet (claude-sonnet-4) | Claude Haiku (simplified questions) | Balance of quality and latency for real-time interaction |
| Tax Optimization | Claude Opus (claude-opus-4) | Claude Sonnet + reduced scenario count | Most complex reasoning task; quality critical |
| Validation & Compliance | Claude Sonnet (claude-sonnet-4) | Claude Haiku (basic rules only) | Good judgment at good cost |
| JSON Generation | Claude Haiku (claude-haiku-3) | Claude Sonnet | Mostly deterministic; LLM is for schema mapping |
| Explainability | Claude Sonnet (claude-sonnet-4) | Claude Opus for complex explanations | Good language quality at moderate cost |
| Security & Privacy | Claude Haiku (claude-haiku-3) | Claude Sonnet for suspicious cases | Pattern matching, fast classification |

### 6.2 Cost Optimization Strategy

1. **Classification first, reasoning second**: Use Haiku for classification tasks, only invoke Opus for reasoning
2. **Progressive model escalation**: Start with cheaper model, escalate to expensive only on low confidence
3. **Context window management**: Systematically prune context to minimize token usage
4. **Response caching**: Cache deterministic operations (document classification of known file types)
5. **Batch processing**: Group independent agent calls to benefit from model batching where available

### 6.3 Fallback Chain

For each agent, if the primary model is unavailable:

1. **Primary → Fallback 1**: Try next tier down (Opus → Sonnet, Sonnet → Haiku)
2. **Fallback 1 → Fallback 2**: If still unavailable, try next model variant (e.g., claude-3-sonnet vs claude-3.5-sonnet)
3. **Fallback 2 → Degraded Mode**: If all Claude models unavailable:
   - Cache previously computed results
   - Offer reduced functionality with clear user communication
   - Queue intensive tasks for when models recover

---

## 7. Agent State Management

### 7.1 Per-Agent Memory

Each agent maintains:

1. **Working Memory**: Current task inputs, intermediate reasoning, outputs (short-lived, cleared after task completion)
2. **Episodic Memory**: Key decisions and their rationales from the current session (maintained for session duration)
3. **Semantic Memory**: Tax knowledge, schema knowledge, document type knowledge (long-lived, updated per AY)

### 7.2 Shared Session State

```typescript
interface SessionState {
  sessionId: string;
  userId: string;
  status: SessionStatus;
  currentStage: FilingStage;
  userProfile: UserProfile;
  financialData: FinancialData;
  documents: DocumentRecord[];
  extractions: ExtractionRecord[];
  validations: ValidationRecord[];
  computations: ComputationRecord[];
  conversationHistory: ConversationSummary;
  selectedRegime: TaxRegime | null;
  selectedRecommendations: string[]; // Deduction IDs
  riskAssessment: RiskAssessment;
  jsonOutput: ITRJSON | null;
  escalationTickets: EscalationTicket[];
  createdAt: string;
  lastActiveAt: string;
  expiresAt: string;  // Auto-expire at session TTL
}
```

### 7.3 Stateless vs Stateful Design

| Agent | Design | Reason |
|-------|--------|--------|
| Orchestrator | Stateful | Maintains session state machine |
| Document Understanding | Stateless | Each document processed independently |
| Conversation | Stateless (context from Orchestrator) | Each turn is independent; context passed |
| Tax Optimization | Stateless | Each computation query is independent |
| Validation & Compliance | Stateless | Each rule execution is independent |
| JSON Generation | Stateless | Each JSON build is fresh |
| Explainability | Stateless | Each explanation from scratch |
| Security & Privacy | Stateful (logging) | Audit log append-only; anomaly detection needs state |

### 7.4 Context Window Management

| Strategy | Description | When Applied |
|----------|-------------|--------------|
| **Sliding Window** | Keep last N conversation turns, discard oldest | After every 5 turns in Conversation Agent |
| **Semantic Compression** | Summarize older context segments using language model | When total context > 60% of model limit |
| **Key-Value Pruning** | Remove low-value context (system messages, repetitive confirmations) | Continuously |
| **Structured Chunking** | Convert freeform context to structured key-value pairs | When passing between agents |
| **Hierarchical Summarization** | Maintain separate short-term (detailed) and long-term (summarized) memories | Session-level management |

---

## 8. Tax Rule Engine Integration

### 8.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        TAXSTOX PLATFORM                         │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │Orchestrator│   │Document │   │Tax Opt   │   │Validation│   │
│  │ Agent    │   │ Agent   │   │ Agent    │   │ Agent    │   │
│  └─────┬────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘   │
│        │              │              │              │          │
│  ┌─────┴──────────────┴──────────────┴──────────────┴──────┐   │
│  │                  Agent Communication Bus                  │   │
│  └─────┬─────────────────────────────────────────────┬──────┘   │
│        │                                              │          │
│  ┌─────┴────┐                                ┌───────┴──────┐  │
│  │  Context  │                                │  Engine      │  │
│  │  Bus      │                                │  Gateway     │  │
│  └──────────┘                                └───────┬──────┘  │
│                                                        │        │
└────────────────────────────────────────────────────────┼────────┘
                                                         │
                                                         │ HTTPS/TLS
                                                         │
┌────────────────────────────────────────────────────────┼────────┐
│                   TAX RULE ENGINE SERVICE               │        │
│                                                        │        │
│  ┌──────────────────────────────────────────────────────┐│        │
│  │                  API Gateway                         ││        │
│  └────────────────────┬─────────────────────────────────┘│        │
│                       │                                  │        │
│  ┌────────────────────┼─────────────────────────────────┐│        │
│  │        ┌───────────┴───────────┐                    ││        │
│  │        │   Request Validator   │                     ││        │
│  │        └───────────┬───────────┘                     ││        │
│  │                    │                                  ││        │
│  │        ┌───────────┴───────────┐                     ││        │
│  │        │ Computation Router   │                     ││        │
│  │        └──┬─────┬──────┬──────┘                     ││        │
│  │           │     │      │                              ││        │
│  │  ┌────────┴┐ ┌──┴───┐ ┌┴────────┐                   ││        │
│  │  │Tax Slab │ │Rebate│ │Deduction│                    ││        │
│  │  │Engine   │ │Engine│ │Engine   │                    ││        │
│  │  └─────────┘ └──────┘ └─────────┘                   ││        │
│  │           │     │      │                              ││        │
│  │  ┌────────┴┐ ┌──┴───┐ ┌┴────────┐                   ││        │
│  │  │Surcharge│ │Cess  │ │AMT      │                    ││        │
│  │  │Engine   │ │Engine│ │Engine   │                    ││        │
│  │  └─────────┘ └──────┘ └─────────┘                   ││        │
│  │                    │                                  ││        │
│  │        ┌───────────┴───────────┐                     ││        │
│  │        │   Audit Trail Writer  │                     ││        │
│  │        └───────────────────────┘                     ││        │
│  └──────────────────────────────────────────────────────┘│        │
│                                                          │        │
└──────────────────────────────────────────────────────────┘────────┘
```

### 8.2 Integration Boundaries

| Boundary | What's Allowed | What's Not Allowed |
|----------|---------------|-------------------|
| Agent → Engine | Structured queries with typed parameters | Free-text questions, prompts, natural language |
| Engine → Agent | Structured responses with typed data | Arbitrary text generated by LLM |
| Agent → Context Bus | Write computed context updates | Write engine-level data (must go through engine) |
| Engine → Context Bus | Read-only (reference data) | Write directly to session context |

### 8.3 Idempotency and Caching

- All engine requests carry an `idempotencyKey`
- Engine caches responses for 24 hours per key
- Identical requests within the TTL return cached response
- This ensures that repeated scenario comparisons don't re-compute

---

## 9. Error Handling & Recovery

### 9.1 Agent Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Agent timeout | Orchestrator timeout monitoring | Retry with fallback model; if still fails, notify user |
| Agent hallucination | Output validation against expected schema | Regenerate with stricter constraints; escalate if persistent |
| Agent crash | Orchestrator heartbeat monitoring | Restart agent; restore last known good state from context bus |
| Tool execution failure | Tool returns error | Retry with backoff; escalate if tool is critical |

### 9.2 Graceful Degradation

| Degraded Component | Impact | User Experience |
|-------------------|--------|-----------------|
| Tax Optimization Agent | Standard deductions only, no optimization scenarios | "We're running in basic mode. You can revisit optimization later." |
| Document Agent | Manual data entry instead of auto-extraction | "Upload is temporarily limited. You can enter data manually." |
| Conversation Agent | Predefined question sets instead of dynamic | "We're using our standard questionnaire." |
| Explainability Agent | No detailed explanations | "Detailed explanations are temporarily unavailable." |

### 9.3 Circuit Breaker

Each agent has a circuit breaker that:

1. **Closed** (normal operation): Requests flow normally
2. **Open** (failure threshold exceeded): All requests to this agent are immediately failed
3. **Half-Open** (after cooldown): Test request is allowed; if successful, close; if failed, re-open

Thresholds:
- 5 consecutive failures → circuit opens
- 30-second cooldown → circuit half-opens
- 3 consecutive successes in half-open → circuit closes

---

## 10. Observability & Monitoring

### 10.1 Key Metrics Per Agent

| Metric | Description | Target | Alert Threshold |
|--------|-------------|--------|-----------------|
| Response Time | P50/P95/P99 time per agent invocation | < 2s P95 | > 5s P95 |
| Error Rate | % of agent invocations that error | < 1% | > 3% |
| Token Usage | Avg tokens consumed per invocation | Optimized per model | > 2x expected |
| Retry Rate | % of invocations requiring retry | < 5% | > 10% |
| Hallucination Rate | % of outputs failing validation | < 0.5% | > 2% |
| User Satisfaction | Post-interaction rating | > 4.5/5 | < 4.0/5 |

### 10.2 Logging Requirements

Every agent action is logged with:
1. Agent ID and model used
2. Input payload (condensed)
3. Output payload (condensed)
4. Latency breakdown
5. Token count (input + output)
6. Tool calls made
7. Validation results
8. Any errors or retries

Logs are stored in structured format (JSON) in a centralized logging system with:
- 90-day hot retention
- 1-year warm retention
- 7-year cold retention (for audit compliance)

---

## 11. Performance Budgets & SLAs

### 11.1 End-to-End Filing Flow

| Stage | Target Duration | User Perception |
|-------|----------------|-----------------|
| Document Upload & Process | < 30 seconds for 3 documents | "Processing documents..." |
| Data Extraction & Validation | < 10 seconds | "Validating your data..." |
| Conversation (per question) | < 3 seconds | Chat-like response |
| Tax Optimization | < 15 seconds | "Analyzing opportunities..." |
| JSON Generation | < 5 seconds | "Preparing your return..." |
| Final Validation | < 10 seconds | "Final checks..." |
| **Total** | **< 2 minutes** (excluding user thinking time) | |

### 11.2 Individual Agent SLAs

| Agent | P95 Response Time | Max Tokens (Output) | Max Tokens (Input) |
|-------|-------------------|---------------------|--------------------|
| Orchestrator | 3s | 1500 | 8000 |
| Document Understanding | 8s | 4000 | 12000 |
| Conversation | 3s | 2000 | 6000 |
| Tax Optimization | 12s | 6000 | 15000 |
| Validation & Compliance | 8s | 3000 | 10000 |
| JSON Generation | 5s | 4000 | 8000 |
| Explainability | 5s | 4000 | 8000 |
| Security & Privacy | 3s | 1000 | 6000 |

---

## Appendix A: Agent Tools Quick Reference

| Agent | Tools |
|-------|-------|
| Orchestrator | route_to_agent, route_to_agents_parallel, get_session_context, update_session_state, escalate_to_human, call_tax_engine, detect_intent, manage_context_window |
| Document Understanding | classify_document, extract_entities, validate_extraction, cross_reference_documents, detect_ocr_anomaly |
| Conversation | generate_question, validate_answer, resolve_ambiguity, detect_user_confusion, detect_sensitive_topic, suggest_upload |
| Tax Optimization | discover_deductions, verify_deduction_eligibility, compare_regimes, compute_scenario, generate_recommendation, detect_missed_deductions, apply_alternate_minimum_tax |
| Validation & Compliance | run_validation_rule, run_validation_category, run_all_validations, detect_mismatch, compute_risk_score, generate_notice_prediction |
| JSON Generation | select_itr_form, build_itr_json, validate_against_schema, compute_hash, generate_export_instructions |
| Explainability | explain_computation, explain_deduction, explain_regime_choice, explain_validation_result, generate_audit_summary, generate_forward_planning |
| Security & Privacy | detect_pii_leak, log_data_access, flag_suspicious_activity, verify_agent_authorization, mask_pii, generate_privacy_summary |

## Appendix B: Session Context Schema

```typescript
interface SessionContextSnapshot {
  sessionId: string;
  stage: FilingStage;
  userProfile: { pan: string; maskedPan: string; name: string; ... };
  financialSummary: { totalIncome: number; totalDeductions: number; taxLiability: number; ... };
  currentQuestion: string | null;
  pendingVerifications: number;
  riskScore: number;
  lastAgentActivity: string;
}
```

## Appendix C: Tax Rule Engine Operation Catalog

```typescript
enum TaxOperation {
  // Core Tax Computation
  COMPUTE_TAX = "compute_tax",
  COMPUTE_TAX_OLD_REGIME = "compute_tax_old_regime",
  COMPUTE_TAX_NEW_REGIME = "compute_tax_new_regime",
  
  // Deduction-Related
  COMPUTE_SECTION_80C = "compute_section_80c",
  COMPUTE_SECTION_80D = "compute_section_80d",
  COMPUTE_SECTION_24B = "compute_section_24b",
  COMPUTE_HRA_EXEMPTION = "compute_hra_exemption",
  COMPUTE_LTA_EXEMPTION = "compute_lta_exemption",
  
  // Capital Gains
  COMPUTE_CAPITAL_GAINS = "compute_capital_gains",
  COMPUTE_INDEXATION = "compute_indexation",
  COMPUTE_SECTION_54_EXEMPTION = "compute_section_54_exemption",
  
  // Regime Comparison
  COMPARE_OLD_NEW_REGIMES = "compare_old_new_regimes",
  COMPUTE_BREAK_EVEN_DEDUCTION = "compute_break_even_deduction",
  
  // Validation
  VALIDATE_TDS_CREDIT = "validate_tds_credit",
  VALIDATE_DEDUCTION_LIMITS = "validate_deduction_limits",
  
  // Alternate Minimum Tax
  COMPUTE_AMT = "compute_amt",
  COMPUTE_ALTERNATE_MINIMUM_TAX = "compute_alternate_minimum_tax",
  
  // Interest
  COMPUTE_INTEREST_234A = "compute_interest_234a",
  COMPUTE_INTEREST_234B = "compute_interest_234b",
  COMPUTE_INTEREST_234C = "compute_interest_234c",
  
  // Rebate
  COMPUTE_REBATE_87A = "compute_rebate_87a",
  
  // Surcharge and Cess
  COMPUTE_SURCHARGE = "compute_surcharge",
  COMPUTE_HEALTH_CESS = "compute_health_cess",
  
  // Tax Payable
  COMPUTE_NET_TAX_PAYABLE = "compute_net_tax_payable",
  COMPUTE_REFUND = "compute_refund",
}
```

---

*This architecture document is a living specification. All agent behaviors, tools, and integration contracts are subject to iterative refinement as implementation progresses. Any deviation from the core principle "AI Orchestrates, Engine Calculates" requires Principal Architect approval.*
