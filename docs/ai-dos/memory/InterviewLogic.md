# Interview Logic Memory

> **Purpose:** Design and evolution of the Adaptive Interview Engine — the question flow that gathers taxpayer data.
> **Updated By:** Architect Agent — every session when interview logic changes.
> **Last Updated:** 2026-07-05
> **Session ID:** INIT
> **Cross-Refs:** [BusinessRules.md](BusinessRules.md), [TaxRules.md](TaxRules.md), [Architecture.md](Architecture.md)

---

## 1. Interview Engine Philosophy

### 1.1 Core Principles

1. **Minimal Burden:** Ask the fewest questions necessary to compute correct tax
2. **Adaptive Path:** Questions adapt based on previous answers — no irrelevant questions
3. **Progressive Disclosure:** Start simple, reveal complexity only when needed
4. **Plain Language:** Tax concepts explained in everyday language, not legalese
5. **Confidence Building:** Explain WHY each question is being asked
6. **Error Prevention:** Validate as-you-type; prevent mistakes before submission
7. **Resume Anywhere:** Interview can be paused and resumed at any point
8. **Offline-First:** All questions and logic work without network connectivity
9. **Multi-lingual:** Questions and explanations in user's preferred language
10. **Accessibility:** Screen-reader compatible, keyboard-navigable, WCAG 2.1 AA minimum

### 1.2 What the Interview Engine Is NOT

- NOT a chatbot (structured question flow, not free-form conversation)
- NOT a tax advisor (it gathers data, computes tax, does not recommend tax avoidance)
- NOT a replacement for professional help (it clearly signals when professional consultation is recommended)

## 2. Interview Architecture (Planned)

### 2.1 Core Components

```
AdaptiveInterviewEngine
├── QuestionRegistry         # All possible questions, organized by domain
├── DecisionTree             # Logic that determines which question comes next
├── AnswerStore              # Immutable, versioned storage of user answers
├── ValidationEngine         # Real-time validation of each answer
├── PrefillEngine            # Auto-fill from uploaded documents (Form 16, 26AS, AIS)
├── ExplanationEngine        # "Why am I being asked this?" explanations
├── ProgressTracker          # Where am I in the process? What's left?
├── ResumeManager            # Save/restore interview state
├── LocalizationEngine       # Multi-language support
└── AccessibilityLayer       # Screen reader, keyboard navigation
```

### 2.2 Question Types

| Type | Description | Example |
|------|-------------|---------|
| `SINGLE_CHOICE` | Pick one from a list | "What is your residential status?" |
| `MULTI_CHOICE` | Pick multiple from a list | "Which deductions do you want to claim?" |
| `NUMERIC` | Enter a number | "What is your gross salary?" |
| `DATE` | Enter a date | "When did you purchase this property?" |
| `FILE_UPLOAD` | Upload a document | "Upload your Form 16" |
| `TABLE` | Fill a table/grid | "Enter details of each fixed deposit" |
| `CONFIRMATION` | Yes/No with explanation | "We computed X. Is this correct?" |
| `INFORMATION` | Display-only; no answer needed | "Here's a summary of capital gains rules..." |
| `COMPUTED` | Auto-computed; shown for confirmation | "Your taxable income is: Rs. X" |

## 3. Interview Flow (High-Level)

### 3.1 Standard Flow Sequence

```
PHASE 1: IDENTIFICATION
  ├── Personal Information (Name, PAN, DOB)
  ├── Contact Information (Mobile, Email)
  └── Filing Status (Individual, HUF, Senior Citizen?)

PHASE 2: INCOME PROFILE (ADAPTIVE)
  ├── Do you have salary income?
  │   └── YES → Salary details (Form 16 upload or manual entry)
  ├── Do you own house property?
  │   └── YES → House property details (let out/self-occupied, loan, etc.)
  ├── Do you have business/profession income?
  │   └── YES → Business details (presumptive or regular)
  ├── Did you sell any assets? (shares, property, gold, etc.)
  │   └── YES → Capital gains details for each asset
  └── Do you have other income? (interest, dividend, etc.)
      └── YES → Other sources details

PHASE 3: DEDUCTIONS (ADAPTIVE BY REGIME)
  └── [If OLD REGIME]
      ├── Investments (80C): PF, PPF, LIC, ELSS, tuition, home loan principal, etc.
      ├── NPS (80CCD)
      ├── Medical Insurance (80D)
      ├── Home Loan Interest (80EE/80EEA)
      ├── Education Loan (80E)
      ├── Donations (80G)
      ├── Savings Interest (80TTA/80TTB)
      └── Any other deductions?

PHASE 4: TAXES PAID
  ├── TDS from salary (Form 16)
  ├── TDS from interest (Form 26AS)
  ├── TDS from other sources
  ├── Advance Tax paid
  └── Self-Assessment Tax paid

PHASE 5: COMPUTATION & REVIEW
  ├── Compute tax under selected regime(s)
  ├── Display summary (income, deductions, tax, TDS, net payable/refund)
  ├── Explain each component
  ├── Compare Old vs New (if applicable)
  └── Confirm and finalize

PHASE 6: OUTPUT
  ├── Generate ITR JSON/XML
  ├── Generate computation summary (PDF)
  ├── Generate audit trail
  └── Provide filing instructions
```

### 3.2 Decision Tree Logic (Pseudocode)

```python
def next_question(current_question_id: str, answers: AnswerStore) -> Question | None:
    """
    Determine the next question based on the answer just given
    and the complete answer history.
    """
    context = InterviewContext(
        financial_year=answers.financial_year,
        itr_type=answers.itr_type,  # May be auto-determined
        regime=answers.regime,      # May be auto-determined
        previous_answers=answers,
    )

    tree = DecisionTree.for_context(context)

    # The decision tree evaluates conditions:
    # - Is a certain income head applicable?
    # - Has a threshold been crossed?
    # - Is a certain deduction available?
    # - Has the user opted for a specific regime?

    next_node = tree.evaluate(current_question_id, answers)

    if next_node.is_terminal:
        return None  # Interview complete

    return next_node.question
```

## 4. Adaptive Branching Logic

### 4.1 ITR Type Auto-Determination

```
START:
  Q: Are you an individual or HUF?
    ├── Individual/HUF
    │   Q: Do you have business/profession income?
    │   ├── YES → ITR-3 (or ITR-4 if presumptive)
    │   └── NO
    │       Q: Is your total income > 50 lakh?
    │       ├── YES → ITR-2
    │       └── NO
    │           Q: Do you have capital gains?
    │           ├── YES → ITR-2
    │           └── NO
    │               Q: Do you have foreign income/assets?
    │               ├── YES → ITR-2
    │               └── NO
    │                   Q: Are you a company director?
    │                   ├── YES → ITR-2
    │                   └── NO → ITR-1
    └── Other Entity Type → [Phase 2]
```

### 4.2 Regime Recommendation Triggers

The engine should prompt the user for regime comparison when:

1. User is a salaried individual with deductions > Rs. 2,00,000
2. User has income above Rs. 15,00,000 (where surcharge differences matter)
3. User has multiple deduction sources
4. User explicitly asks "which regime is better for me?"

## 5. Question Metadata Standard

```python
@dataclass
class Question:
    question_id: str                    # Unique: "SALARY_GROSS_001"
    question_type: QuestionType         # SINGLE_CHOICE, NUMERIC, etc.
    text: dict[str, str]                # Language → text, e.g., {"en": "...", "hi": "..."}
    help_text: dict[str, str]           # Language → help text
    why_asked: dict[str, str]           # "We ask this because..."
    options: Optional[list[Option]]     # For choice questions
    validation_rules: list[ValidationRule]
    default_value: Optional[Any]        # Pre-filled if available
    prefill_source: Optional[str]       # "FORM16", "AIS", "PREVIOUS_YEAR"
    required: bool                      # Can this be skipped?
    applicable_conditions: list[Condition]  # When should this question be asked?
    answer_format: str                  # "decimal", "date", "string", "file"
    min_value: Optional[Decimal]
    max_value: Optional[Decimal]
    related_sections: list[str]         # Legal provisions
    related_questions: list[str]        # Question IDs that may follow
    tags: list[str]                     # For search/filtering
```

## 6. Document Prefill Logic (Planned)

### 6.1 Supported Documents

| Document | Extraction Method | Data Extracted |
|----------|------------------|----------------|
| Form 16 (Part A) | OCR + Structured Parsing | Employer details, TDS, TAN |
| Form 16 (Part B) | OCR + Structured Parsing | Salary breakup, allowances, deductions, perquisites |
| Form 26AS | Structured (TRACES JSON/PDF) | All TDS entries, tax paid, refunds |
| AIS | Structured (ITD JSON) | All financial transactions reported |
| Form 12BB | OCR | Investment declarations |
| Capital Gains Statement | Structured (broker CSV/PDF) | Trade details, P&L, holding periods |
| Bank Statement | OCR | Interest earned, large transactions |
| Rent Receipts | OCR | Rent paid, landlord details |
| Previous Year ITR | Structured (ITD JSON) | Carry-forward losses, brought-forward data |

### 6.2 Prefill Confidence Levels

| Confidence | Meaning | Action |
|------------|---------|--------|
| `HIGH` | Extracted from structured data (JSON, well-formatted PDF) | Auto-fill, show for confirmation |
| `MEDIUM` | Extracted by OCR with good confidence | Auto-fill, highlight for review |
| `LOW` | Extracted by OCR with low confidence | Suggest value, user must confirm/edit |
| `NONE` | Could not extract | User must enter manually |

## 7. Validation Rules (Planned)

### 7.1 Validation Categories

| Category | Examples | When Applied |
|----------|----------|--------------|
| `TYPE` | Is this a valid number? Date? | On input |
| `RANGE` | Is salary between 0 and 100 crore? | On input |
| `FORMAT` | Is PAN format correct? Is Aadhaar 12 digits? | On input |
| `LOGIC` | Is TDS < Gross Salary? Is 80C ≤ 1,50,000? | On input |
| `CROSS_FIELD` | Does total match sum of parts? | On section complete |
| `CROSS_DOCUMENT` | Does Form 16 match Form 26AS? | On document upload |
| `CROSS_YEAR` | Is this consistent with last year's data? | On section complete |
| `REGULATORY` | Does this comply with section limits? | On section complete |

### 7.2 Validation Severity

| Severity | Meaning | Blocks Submission? |
|----------|---------|--------------------|
| `ERROR` | Definitely wrong; must fix | Yes |
| `WARNING` | Probably wrong; needs review | No, but flagged |
| `INFO` | FYI; may be correct | No |

## 8. Interview State Machine

```
           ┌──────────┐
           │  NEW     │
           └────┬─────┘
                │ start
                ▼
           ┌──────────┐
    ┌─────>│IN_PROGRESS│
    │      └────┬─────┘
    │           │
    │           ├── pause ──> ┌──────────┐
    │           │             │  PAUSED  │── resume ──┐
    │           │             └──────────┘            │
    │           │                                     │
    │           ├── complete ──> ┌──────────┐         │
    │           │                │ COMPLETE │         │
    │           │                └────┬─────┘         │
    │           │                     │               │
    │           │                     ├── compute ──> ┌──────────────┐
    │           │                     │               │ COMPUTING    │
    │           │                     │               └──────┬───────┘
    │           │                     │                      │
    │           │                     │          ┌───────────┼───────────┐
    │           │                     │          │           │           │
    │           │                     │          ▼           ▼           ▼
    │           │                     │     ┌────────┐ ┌────────┐ ┌──────────┐
    │           │                     │     │RESULT  │ │ERROR   │ │CLARIFY   │
    │           │                     │     │READY   │ │        │ │NEEDED    │
    │           │                     │     └───┬────┘ └────┬───┘ └─────┬─────┘
    │           │                     │         │           │           │
    │           │                     │         │           │           │
    │           │                     │         ▼           ▼           │
    │           │                     │     ┌────────┐ ┌────────┐      │
    │           │                     │     │FILED   │ │REVIEW  │◄─────┘
    │           │                     │     │        │ │NEEDED  │
    │           │                     │     └────────┘ └────────┘
    │           │                     │
    │           └── review needed ────┘ (go back to IN_PROGRESS)
    │
    └── (any state can transition to ABANDONED after 90 days inactive)
```

---

## Session Log

| Date | Session ID | Changes Made | Agent |
|------|-----------|--------------|-------|
| 2026-07-05 | INIT | Interview logic memory initialized. Architecture, flow, and standards defined. | Architect |

---

*This file governs the adaptive interview. Every question, every branch, every validation lives here.*
