# 13 — Conversation Engine

> **Parent:** [00-README.md](00-README.md) | **Prev:** [12 Validation Engine](12-validation-engine.md) | **Next:** [14 Memory Management](14-memory-management.md)

---

## 1. Conversation Philosophy

The AI should feel like **talking to an expert Chartered Accountant**, not filling a tax form. Every interaction follows three principles:

1. **Extract First** — Exhaust document extraction before asking anything
2. **Infer Second** — Use heuristics and patterns to infer missing data
3. **Validate Third** — Cross-check inferred data against multiple sources
4. **Ask Last** — Only ask the user what cannot be extracted or inferred

The user should never feel interrogated. Questions should be contextual, justified, and minimal.

---

## 2. Conversation State Machine

```
                         ┌──────────────────┐
                         │      IDLE         │
                         └────────┬─────────┘
                                  │ user initiates filing
                         ┌────────▼─────────┐
                         │  GREETING +       │
                         │  DOCUMENT PROMPT  │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┼──────────────┐
                    │ documents    │ no documents  │
                    │ uploaded     │               │
              ┌─────▼──────┐  ┌───▼────────────┐
              │ PROCESSING  │  │ MANUAL ENTRY   │
              │ (showing    │  │ MODE (full     │
              │  progress)  │  │ interview)     │
              └─────┬──────┘  └───┬────────────┘
                    │              │
              ┌─────▼──────┐       │
              │ EXTRACTED   │       │
              │ DATA REVIEW │◄──────┘
              └─────┬──────┘
                    │ data verified
              ┌─────▼──────┐
              │ ADAPTIVE    │
              │ QUESTIONS   │◄─────────┐
              └─────┬──────┘           │
                    │ answer           │ follow-up
              ┌─────▼──────┐     ┌─────┴──────┐
              │ VALIDATE    │────►│ CLARIFY     │
              │ ANSWER      │     │ AMBIGUITY   │
              └─────┬──────┘     └─────────────┘
                    │ valid
              ┌─────▼──────┐
              │ ALL Q's     │
              │ ANSWERED?   │──NO──► back to ADAPTIVE QUESTIONS
              └─────┬──────┘
                    │ YES
              ┌─────▼──────┐
              │ COMPUTE     │
              │ TAX         │
              └─────┬──────┘
                    │
              ┌─────▼──────┐
              │ PRESENT     │
              │ RESULTS +   │
              │ OPTIMIZE    │
              └─────┬──────┘
                    │ user confirms
              ┌─────▼──────┐
              │ GENERATE    │
              │ ITR JSON    │
              └─────┬──────┘
                    │
              ┌─────▼──────┐
              │ EXPORT +    │
              │ INSTRUCTIONS│
              └─────┬──────┘
                    │
              ┌─────▼──────┐
              │ COMPLETED   │
              └────────────┘
```

---

## 3. Question Generation Strategy

### 3.1 Question Priority Tiers

```typescript
enum QuestionPriority {
  CRITICAL = 1,  // Must ask — cannot infer, filing blocked without answer
  HIGH = 2,      // Should ask — significant tax impact if not answered
  MEDIUM = 3,    // Could ask — moderate tax optimization value
  LOW = 4,       // Nice-to-have — small optimization or informational
  SKIP = 5,      // Do not ask — can infer from documents or low value
}

interface QuestionTemplate {
  questionId: string;
  priority: QuestionPriority;
  category: string;                  // "hra", "80c", "capital_gains"
  trigger: QuestionTrigger;
  questionText: string;              // Primary question
  context: string;                   // Why we're asking
  answerType: 'boolean' | 'select' | 'number' | 'currency' | 'date' | 'text' | 'document';
  options?: QuestionOption[];
  validation?: AnswerValidation;
  followUps?: QuestionTemplate[];    // Conditional follow-ups
  defaultAnswer?: any;               // Inferred default
  canSkip: boolean;
  skipImpact?: string;               // "You may miss up to ₹X in deductions"
}

interface QuestionTrigger {
  // What conditions must be true for this question to fire?
  hasDocumentType?: DocumentType[];
  missingEntityTypes?: EntityType[];
  profileConditions?: ProfileCondition[];
  previousAnswerConditions?: AnswerCondition[];
  confidenceBelow?: number;          // Only ask if entity confidence < threshold
}
```

### 3.2 Minimum Question Set (by Taxpayer Segment)

```
SALARIED EMPLOYEE (ITR-1, Form 16 only):
  Q1: "Do you live in rented accommodation?"  (if HRA in Form 16)
  Q2: "Do you have any investments under 80C beyond what's in your Form 16?"
  Q3: "Do you pay health insurance premiums?" (if not in Form 16)
  Q4: "Do you have any income besides your salary?" (if not in AIS)
  Q5: "Please confirm your bank account for any refund."
  → Total: 3-5 questions

SALARIED + CAPITAL GAINS (ITR-2):
  Q1: (HRA question if applicable)
  Q2: (80C question)
  Q3: (Health insurance question)
  Q4: "We see stock/mutual fund sales in your AIS. Do you have the purchase details?"
  Q5: "Any F&O trading or intraday transactions?" (if broker statement indicates)
  Q6: "Any foreign assets or foreign income?"
  Q7: (Bank account confirmation)
  → Total: 5-8 questions

FREELANCER (ITR-4, 44ADA):
  Q1: "What was your total gross receipts this year?"
  Q2: "Do you have a GST registration?"
  Q3: "Any business expenses beyond the presumptive 50%?"
  Q4: "Any other income besides your professional receipts?"
  Q5: "Did you pay any advance tax?"
  Q6: (80C, 80D questions)
  → Total: 6-8 questions

NRI TAXPAYER:
  Q1: "How many days were you in India during the financial year?"
  Q2: "Do you have any income accruing or arising in India?"
  Q3: "Any foreign assets or bank accounts?"
  Q4: "Have you paid any tax in your country of residence?"
  Q5: (DTAA-related questions)
  → Total: 5-8 questions
```

### 3.3 Dynamic Question Adaptation

```typescript
function generateQuestions(context: ConversationContext): Question[] {
  const questions: Question[] = [];

  // Phase 1: Check what we already know
  const knownEntities = new Set(
    context.extractedEntities
      .filter(e => e.confidence >= CONFIDENCE_THRESHOLD)
      .map(e => e.entityType)
  );

  const userAnswered = new Set(
    Object.keys(context.userAnswers)
  );

  // Phase 2: For each question template, check if it should fire
  for (const template of QUESTION_TEMPLATES) {
    // Skip if already answered
    if (userAnswered.has(template.questionId)) continue;

    // Skip if we can infer from extracted entities
    if (template.trigger.missingEntityTypes?.every(t => knownEntities.has(t))) continue;

    // Skip if trigger conditions not met
    if (!evaluateTrigger(template.trigger, context)) continue;

    // Skip if priority is LOW and question budget exhausted
    if (template.priority >= QuestionPriority.LOW && questions.length >= MAX_QUESTIONS) continue;

    questions.push(instantiateTemplate(template, context));
  }

  // Phase 3: Sort by priority, limit total
  return questions
    .sort((a, b) => a.priority - b.priority)
    .slice(0, MAX_QUESTIONS);
}
```

---

## 4. Clarification & Follow-Up Logic

### 4.1 When to Clarify

```typescript
function needsClarification(answer: any, question: Question): ClarificationResult {
  // 1. Answer contradicts extracted data
  if (contradictsExtraction(answer, question)) {
    return {
      needsClarification: true,
      type: 'CONTRADICTION',
      message: `You mentioned ₹${answer} for ${question.label}, but your Form 16 shows ₹${extractedValue}. Which amount should we use?`,
      options: [
        { label: `Use Form 16 amount (₹${extractedValue})`, value: extractedValue },
        { label: `Use my amount (₹${answer})`, value: answer },
        { label: "Let me check and come back", value: 'defer' },
      ],
    };
  }

  // 2. Amount seems unusually high or low
  if (isAnomalous(answer, question)) {
    return {
      needsClarification: true,
      type: 'ANOMALY',
      message: `₹${answer} is ${isHigh ? 'higher' : 'lower'} than typical ${question.label}. Can you confirm this is correct?`,
    };
  }

  // 3. Answer requires evidence but none provided
  if (question.requiresEvidence && !hasSupportingDocument(answer)) {
    return {
      needsClarification: true,
      type: 'MISSING_EVIDENCE',
      message: `To claim ₹${answer} under ${question.section}, you'll need supporting documents. Do you have ${question.requiredDocuments}?`,
    };
  }

  // 4. Ambiguous answer
  if (isAmbiguous(answer)) {
    return {
      needsClarification: true,
      type: 'AMBIGUITY',
      message: "I want to make sure I understand correctly. Could you clarify?",
    };
  }

  return { needsClarification: false };
}
```

### 4.2 Clarification Limit

To prevent endless loops:
- Maximum 2 clarification rounds per question
- After 2 rounds, accept user's latest answer with a note
- Flag for human review if answer has high tax impact

---

## 5. Conversation Tone & Style Guide

### 5.1 Voice Principles

| Principle | Description |
|-----------|-------------|
| **Professional** | Expert but not condescending. Use precise tax terminology with inline explanation. |
| **Empathetic** | Acknowledge that taxes are stressful. "We'll get through this together." |
| **Concise** | Respect the user's time. No fluff. Every sentence serves a purpose. |
| **Confident** | State facts definitively when certain. Be transparent when uncertain. |
| **Reassuring** | When errors occur, immediately provide the path forward. Never leave user stranded. |

### 5.2 Message Templates

```
// GREETING (documents available)
"Welcome back, Aman! I can see your Form 16 and AIS from last year.
 Ready to file for AY 2026-27? Upload your latest documents and I'll handle the rest."

// GREETING (new user)
"Welcome to TaxStox! I'm your AI tax assistant.
 To get started, simply upload your Form 16 and AIS PDF.
 If you don't have them handy, we can do this manually — it'll just take a few more questions."

// ASKING A QUESTION
"We found HRA in your Form 16. Do you live in rented accommodation?
[This helps us calculate your HRA exemption — potentially saving you thousands.]"

// EXPLAINING A RECOMMENDATION
"Based on your income of ₹14.5L and deductions of ₹2.5L, the New Regime saves you ₹42,500.
 Here's why: Under New Regime, your tax rate drops because of wider slabs,
 even though you lose the 80C/80D deductions."

// ERROR RECOVERY
"It looks like your Form 16 PDF is password-protected.
 We tried your PAN as the password (which works for most people), but it didn't work here.
 Could you enter the password? It's usually your date of birth or employer code."

// BAD NEWS (refund less than expected, or tax payable)
"Based on everything we've analyzed, you owe ₹12,400 this year.
 This is because your employer deducted less TDS than required.
 The good news: we've identified ₹15,000 in deductions you can still claim
 by investing in NPS before the filing deadline."

// CELEBRATION
"🎉 Done! Your ITR JSON is ready and you're getting a refund of ₹14,500.
 Just upload the file to the ITD portal (8 simple steps — I'll guide you through each one)."
```

---

## 6. Decision Trees (Key Flows)

### 6.1 HRA Decision Tree

```
Is HRA present in Form 16?
├── NO → Skip HRA questions
└── YES
    └── "Do you live in rented accommodation?"
        ├── NO → Skip HRA. Note: HRA becomes fully taxable.
        └── YES
            └── "What's your monthly rent?"
                ├── Amount entered
                │   └── "Do you live in Mumbai, Delhi, Chennai, or Kolkata?"
                │       ├── YES → Metro: 50% rule applies
                │       └── NO → Non-metro: 40% rule applies
                │
                └── "Do you have a rent agreement and rent receipts?"
                    ├── YES → Great, those serve as evidence
                    ├── NO → "We'll still compute HRA, but keep documents ready in case of scrutiny"
                    └── Rent > ₹83,333/month?
                        └── YES → "You'll need your landlord's PAN for rent above ₹1L/month.
                              Can you provide it?"

    └── HRA exemption computed
        ├── HRA fully exempt → "Your HRA is fully optimized. No further action needed."
        └── HRA partially taxable → "₹{taxable} of your HRA is taxable.
             To reduce this, you could increase your rent (within reason)
             or check if you should be in the metro category."
```

### 6.2 Capital Gains Decision Tree

```
Are capital gains present in AIS/broker statement?
├── NO → Skip capital gains questions. Recommend ITR-1.
└── YES
    └── Classify gains:
        ├── Only listed equity MF/Stocks → ITR-2
        ├── Includes unlisted shares/property → ITR-2/ITR-3
        └── Includes crypto/VDAs → ITR-2/ITR-3

    └── For each gain:
        ├── "We found a sale of {ISIN/scrip} on {date}. Is this correct?"
        ├── "What was the purchase date?"
        │   └── Before 31-Jan-2018?
        │       └── "What was the FMV on 31-Jan-2018?" (Grandfathering applies)
        ├── "What was the purchase price?" (incl. brokerage)
        ├── "Any sale expenses?"
        └── "Did you reinvest the gains?"
            ├── YES → "In residential property?" → Section 54
            │       └── "In specified bonds?" → Section 54EC
            └── NO → Compute tax

    └── Loss harvesting check:
        └── "Do you have any stocks sitting at a loss that you can sell
             before the year-end to offset these gains?"
```

---

## 7. Handling Edge Cases in Conversation

### 7.1 User Confusion

```
DETECTION SIGNALS:
- "I don't understand"
- "What do you mean?"
- User changes answer 3+ times on same question
- User takes unusually long to answer (>60 seconds)
- User gives "I don't know" response

RESPONSE STRATEGY:
1. Simplify: Rephrase question in plain language, drop tax jargon
2. Contextualize: Show why the answer matters (with ₹ impact)
3. Example: "For example, if you pay ₹20,000/month rent in Bangalore..."
4. Assist mode: "Would you like me to make an assumption based on typical values?"
5. Escalate: "I can have a human tax expert help you with this question."
```

### 7.2 User Frustration

```
DETECTION SIGNALS:
- ALL CAPS responses
- Negative sentiment ("this is confusing", "too many questions")
- Repeated "No" or "Skip" answers
- "Just do it for me"

RESPONSE STRATEGY:
1. Acknowledge: "I understand this is a lot. We're almost done."
2. Show progress: "Only 2 questions left!"
3. Accelerate: Skip LOW priority questions
4. Assume defaults: "I'll use typical values for the rest — you can review before filing."
5. Summarize and proceed: Jump to review step with whatever data is available
```

### 7.3 Multi-Language / Hinglish

```
Users may mix English and Hindi:
- "Mera rent 20,000 per month hai"
- "Salary mein HRA hai kya?"
- "Mujhe samajh nahi aaya"

STRATEGY:
- Detect language and respond in same language/mix
- Hinglish is expected and normal — don't correct the user
- Tax terms in English (HRA, PAN, 80C) remain in English even in Hindi context
- Pure Hindi support for users who prefer it
```

---

## 8. Conversation Budget Management

```typescript
interface ConversationBudget {
  maxQuestions: number;              // 8
  maxClarificationsPerQuestion: number; // 2
  maxTotalTurns: number;             // 30
  maxSessionDuration: number;        // 30 minutes
  turnCount: number;
  questionCount: number;
  clarificationCount: Map<string, number>;  // Per question
  sessionStartTime: Date;

  // Budget checks
  canAskQuestion(): boolean;
  canClarify(questionId: string): boolean;
  hasExceededBudget(): boolean;
  remainingQuestions(): number;
}
```

---

## 9. Conversation Metrics

| Metric | Target | Why |
|--------|--------|-----|
| Avg questions per session | < 6 | Minimize user effort |
| Avg turns per session | < 15 | Efficient flow |
| Clarification rate | < 10% of questions | Good question design |
| User confusion events | < 1 per session | Clear communication |
| Skip rate | < 20% of questions | Questions are relevant |
| Session completion rate | > 85% | Good UX |
| Avg session duration | < 5 minutes | Fast filing |
| User satisfaction score | > 4.5/5 | Happy users |

---

*Next: [14 Memory Management](14-memory-management.md)*
