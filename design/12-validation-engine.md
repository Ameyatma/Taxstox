# 12 — Validation Engine

> **Parent:** [00-README.md](00-README.md) | **Prev:** [11 Entity Extraction](11-entity-extraction-pipeline.md) | **Next:** [13 Conversation Engine](13-conversation-engine.md)

---

## 1. Validation Philosophy

The Validation Engine performs 400+ algorithmic checks across extracted data, user answers, and tax computations. Its purpose:

1. **Prevent ITR rejection** — Catch schema/format errors before submission
2. **Prevent tax notices** — Identify mismatches that trigger ITD scrutiny
3. **Ensure correctness** — Data integrity across all documents and inputs
4. **Build trust** — Show users exactly what was validated and why

Every validation rule produces a structured result with severity, explanation, and resolution guidance.

---

## 2. Validation Rule Architecture

```typescript
interface ValidationRule {
  ruleId: string;                    // "V-TDS-001"
  category: ValidationCategory;
  name: string;                      // "TDS Amount Cross-Validation"
  description: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  appliesTo: (context: ValidationContext) => boolean;
  validate: (context: ValidationContext) => ValidationResult;
  resolution: (result: ValidationResult) => ResolutionStrategy[];
  references: string[];              // ITD circulars, sections
}

interface ValidationContext {
  sessionId: string;
  taxpayerProfile: TaxpayerProfile;
  extractedEntities: ExtractedEntity[];
  userAnswers: Record<string, any>;
  uploadedDocuments: DocumentRecord[];
  taxComputation?: TaxComputationResponse;
}

interface ValidationResult {
  ruleId: string;
  status: 'PASS' | 'WARN' | 'FAIL';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  message: string;                   // Human-readable
  details: {
    entities: string[];              // Entity IDs involved
    expected?: any;
    actual?: any;
    difference?: any;
    sourceDocuments: string[];
  };
  resolution: ResolutionStrategy[];
  noticeRisk: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';
  noticeType?: string;               // "CPC Intimation u/s 143(1)"
  falsePositiveProbability: number;  // 0.0-1.0
}
```

---

## 3. Validation Rule Categories (400+ Rules)

### Category 1: Personal & Identity Validation (V-ID-*)

| Rule ID | Description | Severity |
|---------|-------------|----------|
| V-ID-001 | PAN format validation (ABCDE1234F pattern) | CRITICAL |
| V-ID-002 | PAN consistency across all documents | CRITICAL |
| V-ID-003 | PAN-NSDL verification (if available) | HIGH |
| V-ID-004 | Name matches PAN card name | HIGH |
| V-ID-005 | DOB matches PAN record | HIGH |
| V-ID-006 | PAN-Aadhaar linkage status | CRITICAL |
| V-ID-007 | Aadhaar format validation | MEDIUM |
| V-ID-008 | Mobile number format (+91XXXXXXXXXX) | LOW |
| V-ID-009 | Email format validation | LOW |
| V-ID-010 | Gender consistency across documents | LOW |
| V-ID-011 | Father's name consistency | MEDIUM |
| V-ID-012 | Address consistency across documents | MEDIUM |
| V-ID-013 | Age matches taxpayer type (senior citizen ≥60) | HIGH |
| V-ID-014 | Super senior citizen age ≥80 check | HIGH |
| V-ID-015 | PAN is active (not deactivated) | CRITICAL |
| V-ID-016 | PAN is not a duplicate in system | MEDIUM |

### Category 2: Salary & Form 16 Validation (V-SAL-*)

| Rule ID | Description | Severity |
|---------|-------------|----------|
| V-SAL-001 | Gross salary = sum of all components | HIGH |
| V-SAL-002 | Basic + DA consistency with HRA computation | HIGH |
| V-SAL-003 | HRA received vs HRA exemption (HRA ≤ Basic*0.5 for metro) | MEDIUM |
| V-SAL-004 | Standard deduction claimed once only | HIGH |
| V-SAL-005 | Profession tax ≤ ₹2,500 | MEDIUM |
| V-SAL-006 | Entertainment allowance ≤ ₹5,000 (govt employee only) | LOW |
| V-SAL-007 | Employer TAN format validation | HIGH |
| V-SAL-008 | Form 16 Part A TDS matches Part B TDS | CRITICAL |
| V-SAL-009 | Perquisite value consistency (rent-free accommodation formula) | MEDIUM |
| V-SAL-010 | Salary from multiple employers — all Form 16s accounted for | HIGH |
| V-SAL-011 | Employer PF contribution ≤ 12% of basic (statutory limit) | LOW |
| V-SAL-012 | Leave encashment exemption ≤ ₹25L (non-govt) or unlimited (govt) | MEDIUM |
| V-SAL-013 | Gratuity exemption ≤ ₹20L (lifetime cap) | MEDIUM |
| V-SAL-014 | VRS compensation ≤ ₹5L | MEDIUM |
| V-SAL-015 | Allowances categorization (exempt vs taxable) correctness | HIGH |
| V-SAL-016 | Conveyance allowance exemption (actual expenditure only) | MEDIUM |
| V-SAL-017 | Children education allowance ≤ ₹100/child/month, max 2 | LOW |
| V-SAL-018 | Hostel allowance ≤ ₹300/child/month, max 2 | LOW |
| V-SAL-019 | Transport allowance — only for disabled/PwD | MEDIUM |
| V-SAL-020 | Uniform allowance — actual expenditure only | LOW |

### Category 3: TDS Validation (V-TDS-*)

| Rule ID | Description | Severity |
|---------|-------------|----------|
| V-TDS-001 | TDS in Form 16 matches TDS in Form 26AS/AIS | CRITICAL |
| V-TDS-002 | TDS amount matches (tax_rate × taxable_amount) | HIGH |
| V-TDS-003 | TDS certificate has valid TAN | HIGH |
| V-TDS-004 | TDS section code is valid | HIGH |
| V-TDS-005 | Total TDS claimed ≤ total TDS in 26AS | CRITICAL |
| V-TDS-006 | TDS claimed for correct AY | CRITICAL |
| V-TDS-007 | Unclaimed TDS from previous years flagged | HIGH |
| V-TDS-008 | TDS from interest — cross-check with bank statements | MEDIUM |
| V-TDS-009 | TDS on property purchase (194IA) — 1% of transaction | MEDIUM |
| V-TDS-010 | TDS on rent (194IB) — 5% if rent > ₹50K/month | MEDIUM |
| V-TDS-011 | TDS on professional fees (194J) — 10% | LOW |
| V-TDS-012 | TDS on contractor payments (194C) — 1%/2% | LOW |
| V-TDS-013 | Deductor TAN appears in 26AS for claimed amount | HIGH |
| V-TDS-014 | No duplicate TDS claims (same challan, different sections) | HIGH |
| V-TDS-015 | TDS credit proportion if income shared (spouse, etc.) | MEDIUM |

### Category 4: House Property Validation (V-HP-*)

| Rule ID | Description | Severity |
|---------|-------------|----------|
| V-HP-001 | Self-occupied property interest ≤ ₹2,00,000 | MEDIUM |
| V-HP-002 | Let-out property: municipal taxes ≤ Gross Annual Value | HIGH |
| V-HP-003 | Standard deduction (30%) only for let-out/deemed let-out | MEDIUM |
| V-HP-004 | Multiple self-occupied properties — only one allowed | HIGH |
| V-HP-005 | Joint ownership — income split per ownership ratio | HIGH |
| V-HP-006 | Home loan certificate interest matches claimed amount | HIGH |
| V-HP-007 | Pre-construction interest — 1/5th per year for 5 years | MEDIUM |
| V-HP-008 | 80EE/80EEA conditions: loan sanction date, property value limits | HIGH |
| V-HP-009 | Property co-owner PAN declared if deduction claimed | MEDIUM |
| V-HP-010 | Notional rent on second self-occupied property | MEDIUM |
| V-HP-011 | Arrears of rent — 30% standard deduction allowed | LOW |
| V-HP-012 | Vacancy allowance for let-out property | LOW |
| V-HP-013 | Unrealized rent deduction conditions | LOW |
| V-HP-014 | Property in foreign country — DTAA considerations | HIGH |

### Category 5: Capital Gains Validation (V-CG-*)

| Rule ID | Description | Severity |
|---------|-------------|----------|
| V-CG-001 | Holding period correctly determines STCG vs LTCG | CRITICAL |
| V-CG-002 | Cost Inflation Index (CII) year matches sale year | HIGH |
| V-CG-003 | Indexed cost of acquisition computation correct | HIGH |
| V-CG-004 | Grandfathering (31-Jan-2018 FMV) applied correctly | HIGH |
| V-CG-005 | ₹1 Lakh LTCG exemption (112A) applied correctly | HIGH |
| V-CG-006 | Section 54 exemption: new property within 2 years / 3 years construction | HIGH |
| V-CG-007 | Section 54EC: investment ≤ ₹50L in specified bonds within 6 months | HIGH |
| V-CG-008 | Section 54F: net consideration (not just gain) invested | HIGH |
| V-CG-009 | Capital gains account scheme — unused funds after deadline | MEDIUM |
| V-CG-010 | ISIN code format validation | MEDIUM |
| V-CG-011 | STT paid verification for 111A/112A rates | HIGH |
| V-CG-012 | Stock split / bonus / rights issue — adjusted cost basis | MEDIUM |
| V-CG-013 | Crypto/VDAs taxed at 30% (no deductions except cost) | HIGH |
| V-CG-014 | Sale of agricultural land — rural vs urban classification | HIGH |
| V-CG-015 | Depreciable assets — capital gains computation (50C, 50CA) | MEDIUM |
| V-CG-016 | Stamp duty value vs sale consideration (50C) — if variance > 10% | HIGH |

### Category 6: Deduction Validation (V-DED-*)

| Rule ID | Description | Severity |
|---------|-------------|----------|
| V-DED-001 | 80C aggregate ≤ ₹1,50,000 | CRITICAL |
| V-DED-002 | 80CCC + 80CCD(1) within 80C cap | CRITICAL |
| V-DED-003 | 80CCD(1B) — NPS additional, max ₹50,000, separate from 80C | HIGH |
| V-DED-004 | 80CCD(2) — employer NPS, 10%/14% of salary | MEDIUM |
| V-DED-005 | 80D: Self/family ≤ ₹25K (₹50K senior), Parents ≤ ₹25K (₹50K senior) | HIGH |
| V-DED-006 | 80D preventive checkup ≤ ₹5,000 (within overall limits) | LOW |
| V-DED-007 | 80DD: disability certificate required, severity ≥40% | HIGH |
| V-DED-008 | 80DDB: specified disease certificate required | HIGH |
| V-DED-009 | 80E: max 8 years from loan start, only interest | MEDIUM |
| V-DED-010 | 80EE: first-time home buyer, loan ≤ ₹35L, property ≤ ₹50L | HIGH |
| V-DED-011 | 80EEA: stamp duty value ≤ ₹45L, loan sanctioned in specific period | HIGH |
| V-DED-012 | 80EEB: EV loan sanctioned in specific period | MEDIUM |
| V-DED-013 | 80G: qualifying limit = 10% of Adjusted GTI | HIGH |
| V-DED-014 | 80G: correct deduction rate (50% or 100%) per institution type | HIGH |
| V-DED-015 | 80G: donation receipt has institution PAN and 80G registration | HIGH |
| V-DED-016 | 80GG: rent paid conditions (no HRA, no self-owned property) | HIGH |
| V-DED-017 | 80TTA: only savings account interest, max ₹10,000 | MEDIUM |
| V-DED-018 | 80TTB: only senior citizens, deposits interest, max ₹50,000 | MEDIUM |
| V-DED-019 | 80U: disability certificate required | HIGH |
| V-DED-020 | No double-claiming same expense under multiple sections | CRITICAL |
| V-DED-021 | Deduction source document verification | HIGH |
| V-DED-022 | Deduction payment mode (cash > ₹2,000 → not eligible for some) | MEDIUM |
| V-DED-023 | Deduction not claimed in both regimes (if New Regime chosen) | HIGH |
| V-DED-024 | ELSS lock-in period verification (3 years) | LOW |

### Category 7: Income Validation (V-INC-*)

| Rule ID | Description | Severity |
|---------|-------------|----------|
| V-INC-001 | Salary in Form 16 matches salary slip totals | HIGH |
| V-INC-002 | AIS-reported interest vs bank statement interest | HIGH |
| V-INC-003 | All AIS-reported income accounted for in return | CRITICAL |
| V-INC-004 | Dividend income ≥ AIS reported amount | HIGH |
| V-INC-005 | Agricultural income documentation if > ₹5,000 | MEDIUM |
| V-INC-006 | Foreign income — DTAA relief computation | HIGH |
| V-INC-007 | Family pension — ₹15,000 or 1/3rd deduction (whichever lower) | MEDIUM |
| V-INC-008 | Gift tax — > ₹50,000 from non-relatives is taxable | MEDIUM |
| V-INC-009 | Clubbing provisions (minor child income, spouse gift) | HIGH |
| V-INC-010 | Business turnover vs GST returns (if applicable) | HIGH |
| V-INC-011 | Presumptive income ≥ 6%/8% of turnover (44AD) | HIGH |
| V-INC-012 | Cash receipts > ₹2 crore — 44AD ineligible | MEDIUM |
| V-INC-013 | Interest income from all bank accounts aggregated | MEDIUM |
| V-INC-014 | FD interest — accrued vs received (if following mercantile) | LOW |

### Category 8: Tax Computation Validation (V-TAX-*)

| Rule ID | Description | Severity |
|---------|-------------|----------|
| V-TAX-001 | Tax slab application correct for regime + age | CRITICAL |
| V-TAX-002 | Surcharge rates correct (10%/15%/25%/37%) | HIGH |
| V-TAX-003 | Marginal relief computation correct | HIGH |
| V-TAX-004 | HEC @ 4% on (tax + surcharge) | HIGH |
| V-TAX-005 | 87A rebate: income ≤ ₹5L (old) / ₹7L (new) → max ₹12,500/₹25,000 | HIGH |
| V-TAX-006 | 87A rebate not available for LTCG u/s 112A | MEDIUM |
| V-TAX-007 | Interest 234A: 1% per month on unpaid tax from due date | HIGH |
| V-TAX-008 | Interest 234B: 1% if advance tax < 90% of total tax | HIGH |
| V-TAX-009 | Interest 234C: deferment of advance tax installments | HIGH |
| V-TAX-010 | Late fee 234F: ₹5,000 if filed after due date | HIGH |
| V-TAX-011 | Late fee 234F: ₹1,000 if income ≤ ₹5L and filed late | MEDIUM |
| V-TAX-012 | Relief u/s 89 — Form 10E filed for arrears | MEDIUM |
| V-TAX-013 | Foreign Tax Credit — Form 67 filed | HIGH |
| V-TAX-014 | Total tax paid (TDS+TCS+AdvTax+SAT) ≤ total tax liability | HIGH |
| V-TAX-015 | Refund > ₹50,000 — higher scrutiny risk flag | MEDIUM |
| V-TAX-016 | Refund > ₹1,00,000 — possible ITD verification | HIGH |
| V-TAX-017 | Carry-forward loss correctly set off in order | HIGH |

### Category 9: ITR Form Validation (V-ITR-*)

| Rule ID | Description | Severity |
|---------|-------------|----------|
| V-ITR-001 | Correct ITR form selected based on income types | CRITICAL |
| V-ITR-002 | ITR-1: no capital gains, no business income, no foreign assets | CRITICAL |
| V-ITR-003 | ITR-2: allowed for capital gains, house property, foreign assets | CRITICAL |
| V-ITR-004 | ITR-3: required if business/profession income (non-presumptive) | CRITICAL |
| V-ITR-005 | ITR-4: presumptive income only, turnover limits | CRITICAL |
| V-ITR-006 | All required schedules present in JSON | CRITICAL |
| V-ITR-007 | JSON schema validation against ITD XSD | CRITICAL |
| V-ITR-008 | Mandatory fields not empty | CRITICAL |
| V-ITR-009 | Field lengths within ITD limits | HIGH |
| V-ITR-010 | Enum values match ITD allowed values | HIGH |
| V-ITR-011 | Numeric fields non-negative (where applicable) | HIGH |
| V-ITR-012 | Date formats match ITD specification (DD/MM/YYYY) | MEDIUM |
| V-ITR-013 | PAN format uppercase in JSON | MEDIUM |
| V-ITR-014 | JSON file size within ITD portal limits | LOW |
| V-ITR-015 | Bank account IFSC format and validation | HIGH |

### Category 10: Compliance & Filing Validation (V-COMP-*)

| Rule ID | Description | Severity |
|---------|-------------|----------|
| V-COMP-001 | Filing deadline check (July 31) | HIGH |
| V-COMP-002 | Belated return deadline (December 31) | HIGH |
| V-COMP-003 | Revised return allowed only for original/belated (not revised) | HIGH |
| V-COMP-004 | Previous year return filed status check | MEDIUM |
| V-COMP-005 | Refund bank account pre-validation on ITD portal | HIGH |
| V-COMP-006 | E-verification within 30 days of filing | HIGH |
| V-COMP-007 | Aadhaar-PAN linkage deadline not passed | CRITICAL |
| V-COMP-008 | No outstanding demand from previous years (with tolerance) | HIGH |
| V-COMP-009 | Form 26AS TDS matches claimed TDS within 5% tolerance | HIGH |
| V-COMP-010 | High-value transactions flag (SFT reporting) | MEDIUM |
| V-COMP-011 | Cash deposits > ₹10L (non-senior) — reporting requirement | MEDIUM |
| V-COMP-012 | Foreign travel expenditure > ₹2L — reporting | LOW |
| V-COMP-013 | Credit card payments > ₹1L cash — reporting | LOW |
| V-COMP-014 | Immovable property transaction > ₹30L — reporting | MEDIUM |

---

## 4. Validation Execution Engine

### 4.1 Execution Strategy

```typescript
class ValidationEngine {
  private rules: ValidationRule[] = [];
  private results: Map<string, ValidationResult> = new Map();

  async validateAll(context: ValidationContext): Promise<ValidationReport> {
    // Phase 1: CRITICAL rules — execute first, fail-fast
    const criticalRules = this.rules.filter(r => r.severity === 'CRITICAL');
    const criticalResults = await this.executeRules(criticalRules, context);

    const criticalFailures = criticalResults.filter(r => r.status === 'FAIL');
    if (criticalFailures.length > 0) {
      return this.buildReport(criticalResults, context, 'BLOCKED');
    }

    // Phase 2: HIGH severity rules
    const highRules = this.rules.filter(r => r.severity === 'HIGH');
    const highResults = await this.executeRules(highRules, context);

    // Phase 3: MEDIUM & LOW severity rules (parallel, lower priority)
    const mediumRules = this.rules.filter(r => r.severity === 'MEDIUM');
    const lowRules = this.rules.filter(r => r.severity === 'LOW' || r.severity === 'INFO');
    const [mediumResults, lowResults] = await Promise.all([
      this.executeRules(mediumRules, context),
      this.executeRules(lowRules, context),
    ]);

    const allResults = [...criticalResults, ...highResults, ...mediumResults, ...lowResults];
    return this.buildReport(allResults, context, this.determineOverallStatus(allResults));
  }

  private async executeRules(
    rules: ValidationRule[],
    context: ValidationContext
  ): Promise<ValidationResult[]> {
    // Each rule execution:
    // 1. Check if rule applies to this context (appliesTo)
    // 2. Execute validation logic (validate)
    // 3. Attach resolution strategies
    // 4. Timebox: 500ms timeout per rule, then mark as WARN with timeout reason

    return Promise.all(
      rules.map(async (rule) => {
        if (!rule.appliesTo(context)) return null;
        try {
          const result = await Promise.race([
            rule.validate(context),
            this.timeout(500, { status: 'WARN', message: `Rule ${rule.ruleId} timed out` }),
          ]);
          return { ...result, ruleId: rule.ruleId };
        } catch (error) {
          return {
            ruleId: rule.ruleId,
            status: 'WARN' as const,
            severity: rule.severity,
            message: `Validation error: ${error.message}`,
            details: { entities: [], sourceDocuments: [] },
            resolution: [{ strategy: 'RETRY', description: 'Re-run validation' }],
            noticeRisk: 'NONE',
            falsePositiveProbability: 0.5,
          };
        }
      })
    ).then(results => results.filter(Boolean) as ValidationResult[]);
  }
}
```

### 4.2 Severity Classification

| Severity | Meaning | User Action | Blocks Filing? |
|----------|---------|-------------|----------------|
| **CRITICAL** | ITR will be rejected by ITD | Must fix before generating JSON | YES |
| **HIGH** | Likely to trigger ITD notice | Strongly recommended to fix | YES (warned) |
| **MEDIUM** | Potential issue, may or may not trigger notice | Review and decide | NO |
| **LOW** | Minor issue, informational | Can ignore safely | NO |
| **INFO** | Informational only | None needed | NO |

### 4.3 Resolution Strategies

```typescript
interface ResolutionStrategy {
  strategy: 'AUTO_CORRECT' | 'USER_CHOICE' | 'USER_INPUT'
          | 'RE_UPLOAD' | 'IGNORE' | 'RETRY' | 'CONTACT_SUPPORT';
  description: string;
  autoFix?: () => Promise<void>;     // For AUTO_CORRECT
  options?: ResolutionOption[];      // For USER_CHOICE
}

interface ResolutionOption {
  label: string;
  value: any;
  consequence: string;               // "Using Form 16 amount will result in ₹X refund"
}
```

---

## 5. Validation Report Structure

```typescript
interface ValidationReport {
  reportId: string;
  sessionId: string;
  generatedAt: string;
  overallStatus: 'PASS' | 'WARN' | 'FAIL' | 'BLOCKED';

  summary: {
    totalRules: number;
    applicableRules: number;
    passed: number;
    warnings: number;
    failed: number;
    criticalFailures: number;
    byCategory: Record<ValidationCategory, { total: number; passed: number; failed: number }>;
  };

  results: ValidationResult[];

  blockingIssues: ValidationResult[];     // Must fix
  recommendedFixes: ValidationResult[];   // Should fix
  informationalItems: ValidationResult[]; // FYI

  riskScore: number;                       // 0-100
  noticeProbability: 'LOW' | 'MEDIUM' | 'HIGH';
  estimatedRefundAdjustment: number;       // If issues fixed

  timeline: {
    validationStartedAt: string;
    validationCompletedAt: string;
    durationMs: number;
  };
}
```

---

## 6. Cross-Document Validation Matrix

| Document A | Document B | Validations |
|------------|------------|-------------|
| Form 16 Part A | Form 16 Part B | TDS amounts, PAN, employer name |
| Form 16 | Form 26AS/AIS | TDS per quarter, salary reported |
| Form 16 | Salary Slips | Monthly salary × 12 ≈ annual salary |
| AIS | Bank Statements | Interest income amounts |
| AIS | Broker Statement | Capital gains, dividend |
| Broker Statement | Demat Statement | Holdings match transactions |
| Form 16 | Rent Receipts | HRA, rent paid, landlord PAN |
| Home Loan Cert | Bank Statement | EMI payments, interest/principal split |
| PPF Statement | Bank Statement | PPF contribution debits |
| Insurance Receipt | Bank Statement | Premium payment |
| Form 16 | Previous Year ITR | Salary progression, employer change |
| All documents | PAN Card / Aadhaar | Identity consistency |

---

## 7. Real-Time Validation Hooks

Validation is NOT just a batch process at the end. It runs at these hooks:

```
1. ON_DOCUMENT_UPLOAD:     Validate file format, size, password
2. ON_EXTRACTION_COMPLETE: Validate extracted entities (format, range)
3. ON_ENTITY_REVIEW:       Validate entity consistency as user reviews
4. ON_ANSWER_SUBMIT:       Validate user answer against extracted data
5. ON_ALL_ANSWERS_DONE:    Full cross-document validation
6. ON_TAX_COMPUTED:        Validate tax computation correctness
7. ON_JSON_GENERATED:      Validate JSON against ITD schema
8. PRE_EXPORT:             Final comprehensive validation pass
```

---

*Next: [13 Conversation Engine](13-conversation-engine.md)*
