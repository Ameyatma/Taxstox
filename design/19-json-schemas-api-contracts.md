# 19 — JSON Schemas & API Contracts

> **Parent:** [00-README.md](00-README.md) | **Prev:** [18 Compliance & Audit](18-compliance-audit-engine.md) | **Next:** [20 Function Calling](20-function-calling-retry-logic.md)

---

## 1. ITR JSON Schema (Output)

### 1.1 ITR-1 (Sahaj) JSON Schema

This is the schema for the JSON file the user downloads and uploads to the ITD e-filing portal. It must match the ITD's published JSON schema exactly.

```typescript
// ITR-1 JSON Schema — Assessment Year 2026-27 (FY 2025-26)
// Based on ITD JSON Schema version 1.0

interface ITR1JSON {
  // ===== HEADER =====
  header: {
    itrType: "ITR-1";
    assessmentYear: "2026-27";
    filingDate: string;              // ISO 8601 date: "2026-06-28"
    modeOfFiling: "OFFLINE";
    isRevised: boolean;
    originalFilingDate?: string;
    acknowledgementNo?: string;
    pan: string;                     // "CFFPM4503N"
    name: string;                    // As per PAN
    dob: string;                     // "DD/MM/YYYY"
    mobileNumber: string;
    emailAddress: string;
    aadhaarNumber?: string;         // Masked: "XXXX XXXX 1234"
    residenceStatus: "RES" | "NRI" | "RNOR";
    taxpayerType: "INDIVIDUAL" | "SENIOR_CITIZEN" | "SUPER_SENIOR_CITIZEN";
    filingSection: "139(1)" | "139(4)" | "139(5)";
    returnType: "ORIGINAL" | "REVISED" | "BELATED";
    employerCategory: "GOVT" | "PSU" | "PRIVATE" | "NOT_APPLICABLE";
    isPoliticalPartyMember: boolean;
  };

  // ===== PART A: GENERAL INFORMATION =====
  partA_GeneralInfo: {
    dateOfBirth: string;
    gender: "MALE" | "FEMALE" | "TRANSGENDER";
    pan: string;
    firstName: string;
    middleName?: string;
    lastName: string;
    flatNo?: string;
    buildingName?: string;
    road?: string;
    area?: string;
    city: string;
    state: string;                  // State code as per ITD
    pincode: string;
    country: "INDIA" | string;
    mobileNumber: string;
    email: string;
    aadhaarEnrolmentId?: string;
    isAadhaarLinked: boolean;

    // Bank Account Details (for refund)
    bankAccounts: BankAccountDetail[];

    // Representative Assessee (if applicable)
    representativeAssessee?: {
      pan: string;
      name: string;
      capacity: string;
    };

    // Return Filed in Response to Notice
    noticeDetails?: {
      noticeNumber: string;
      noticeDate: string;
      section: string;
    };
  };

  // ===== PART B: COMPUTATION OF TOTAL INCOME =====
  partB_TI: {
    // B1: Salary
    salary: {
      salaryExcludingAllowances: number;
      allowancesExempt: number;
      allowancesNotExempt: number;
      valueOfPerquisites: number;
      profitsInLieuOfSalary: number;
      deductionUS16_standardDeduction: number;    // 50000 or 75000
      deductionUS16_professionTax: number;
      deductionUS16_entertainmentAllowance: number;
      totalSalaryIncome: number;                   // Computed
    };

    // B2: House Property
    houseProperty: {
      isSelfOccupied: boolean;
      isLetOut: boolean;
      isDeemedLetOut: boolean;
      annualLettableValue: number;
      municipalTaxesPaid: number;
      annualValue: number;                         // Computed
      standardDeduction30Percent: number;          // Computed: 30% of annual value
      interestOnBorrowedCapital: number;
      totalHousePropertyIncome: number;            // Computed
    };

    // B3: Other Sources
    otherSources: {
      interestIncome: {
        fromSavingsBank: number;
        fromDeposits: number;
        fromOthers: number;
        deductionUS80TTA: number;                  // Max 10000
        deductionUS80TTB: number;                  // Max 50000 (senior)
        taxableInterest: number;                   // Computed
      };
      dividendIncome: {
        fromEquity: number;
        fromMutualFunds: number;
        fromOthers: number;
        deductionForInterest: number;
        taxableDividend: number;                   // Computed
      };
      otherIncome: {
        familyPension: number;
        deductionForFamilyPension: number;         // Min(15000, 1/3 of pension)
        giftsReceived: number;
        winnings: number;
        anyOtherIncome: number;
      };
      totalOtherSourcesIncome: number;             // Computed
    };

    grossTotalIncome: number;                      // Sum of all heads
  };

  // ===== PART C: DEDUCTIONS & TAXABLE INCOME =====
  partC_Deductions: {
    deductionsUnderChapterVIA: {
      section80C: Deduction80CEntry[];
      total80C: number;                           // Max 150000
      section80CCC: number;                       // Annuity — under 80C cap
      section80CCD_1: number;                     // NPS employee — under 80C cap
      section80CCD_1B: number;                    // Additional NPS — max 50000
      section80CCD_2: number;                     // Employer NPS
      section80D: Deduction80DEntry[];
      total80D: number;
      section80DD: number;
      section80DDB: number;
      section80E: number;
      section80EE: number;
      section80EEA: number;
      section80EEB: number;
      section80G: Deduction80GEntry[];
      total80G: number;
      section80GG: number;
      section80TTA: number;                       // Max 10000
      section80TTB: number;                       // Max 50000
      section80U: number;
      totalChapterVIADeductions: number;
    };
    taxableIncome: number;                         // GTI - Total Deductions
  };

  // ===== PART D: TAX COMPUTATION =====
  partD_TaxComputation: {
    regime: "OLD" | "NEW";
    taxOnTotalIncome: number;
    rebateUS87A: number;
    taxAfterRebate: number;
    surcharge: number;
    healthEducationCess: number;                  // 4%
    totalTaxAndCess: number;
    reliefUS89: number;
    reliefSection90_90A: number;
    reliefSection91: number;
    totalRelief: number;
    netTaxLiability: number;
    interestUS234A: number;
    interestUS234B: number;
    interestUS234C: number;
    totalInterest: number;
    lateFeeUS234F: number;
    totalTaxAndInterest: number;
    taxPaid: {
      tds: TaxPaidEntry[];
      totalTDS: number;
      tcs: TaxPaidEntry[];
      totalTCS: number;
      advanceTax: TaxPaidEntry[];
      totalAdvanceTax: number;
      selfAssessmentTax: number;
      totalTaxesPaid: number;
    };
    refundDue: number;                             // Computed
    taxPayable: number;                            // Computed
  };

  // ===== SCHEDULES =====
  scheduleTDS: TDSScheduleEntry[];
  scheduleTCS: TCSScheduleEntry[];
  scheduleIT: IncomeTaxPaymentEntry[];
  scheduleHP: HousePropertyDetail[];
  scheduleDI: DeductionDetail[];
  scheduleCG: CapitalGainDetail[];               // Not in ITR-1, included for ITR-2+
  scheduleOS: OtherSourceDetail[];
  scheduleTR: TaxReliefDetail[];
  scheduleFA: ForeignAssetDetail[];              // Not in ITR-1
  scheduleVDA: VirtualDigitalAssetDetail[];

  // ===== VERIFICATION =====
  verification: {
    declaration: boolean;                         // "I declare that..."
    capacity: "SELF" | "REPRESENTATIVE";
    place: string;
    date: string;
    name: string;
    fatherName: string;
  };
}
```

### 1.2 Supporting Sub-Schemas

```typescript
interface BankAccountDetail {
  bankName: string;
  branch: string;
  accountNumber: string;
  accountType: "SAVINGS" | "CURRENT" | "NRE" | "NRO";
  ifscCode: string;
  isPrimaryForRefund: boolean;
  isPreValidated: boolean;
}

interface Deduction80CEntry {
  type: "LIC_PREMIUM" | "PPF" | "EPF" | "NSC" | "ELSS" | "HOME_LOAN_PRINCIPAL"
       | "TUITION_FEE" | "SSY" | "SCSS" | "FD_5YR" | "INFRA_BONDS"
       | "STAMP_DUTY" | "PENSION_FUND" | "OTHER";
  description: string;
  amount: number;
  proofReference?: string;
}

interface Deduction80DEntry {
  category: "SELF_SPOUSE_CHILDREN" | "PARENTS" | "PREVENTIVE_CHECKUP";
  amount: number;
  isSeniorCitizen: boolean;
  insurerName?: string;
  policyNumber?: string;
}

interface Deduction80GEntry {
  institutionName: string;
  institutionPAN: string;
  amount: number;
  deductionRate: 100 | 50;                      // Percentage deductible
  isWithLimit: boolean;
  qualifyingLimit?: number;
}

interface TaxPaidEntry {
  tan?: string;
  nameOfDeductor?: string;
  section: string;
  dateOfPayment: string;
  amount: number;
  challanSerialNumber?: string;
  bsrCode?: string;
}

interface TDSScheduleEntry {
  tan: string;
  nameOfDeductor: string;
  section: string;
  grossAmount: number;
  tdsAmount: number;
  claimedThisYear: number;
}

interface CapitalGainDetail {
  assetType: string;
  isinCode?: string;
  purchaseDate: string;
  saleDate: string;
  purchaseCost: number;
  indexedCost?: number;
  saleValue: number;
  expenses: number;
  ltcgOrStcg: "LTCG" | "STCG";
  gainAmount: number;
  exemptionSection?: string;
  exemptAmount?: number;
  taxableGain: number;
  taxRate: number;
  taxPayable: number;
}
```

### 1.3 JSON Validation & Hash

```typescript
interface SignedITRJSON {
  itr: ITR1JSON;
  signature: {
    algorithm: "SHA256-RSA2048";
    hash: string;                                 // SHA256 hash of JSON content
    generatedBy: "TAXSTOX_V1";
    generatedAt: string;                          // ISO 8601
    warnings: string[];                           // "DO NOT EDIT THIS FILE MANUALLY"
  };
}
```

---

## 2. Internal Data Schemas

### 2.1 Extracted Entity

```typescript
interface ExtractedEntity {
  entityId: string;                               // UUID
  sessionId: string;
  documentId: string;
  source: {
    documentType: DocumentType;
    page: number;
    boundingBox?: BoundingBox;
    rawText: string;                              // Original text from document
    excerptContext: string;                       // Surrounding text for context
  };
  entityType: EntityType;
  normalizedValue: NormalizedValue;
  confidence: number;                             // 0.0 - 1.0
  validationStatus: 'unvalidated' | 'verified' | 'mismatched' | 'user_corrected';
  userOverride?: {
    originalValue: NormalizedValue;
    newValue: NormalizedValue;
    reason: string;
    timestamp: string;
  };
  metadata: Record<string, any>;                  // Entity-specific metadata
}

type EntityType =
  | 'pan' | 'name' | 'dob' | 'aadhaar' | 'gender'
  | 'salary_basic' | 'salary_grade_pay' | 'salary_da'
  | 'salary_hra' | 'salary_lta' | 'salary_conveyance'
  | 'salary_medical' | 'salary_children_education'
  | 'salary_other_allowance' | 'salary_gross'
  | 'salary_profession_tax' | 'salary_standard_deduction'
  | 'perquisite_rent_free' | 'perquisite_car'
  | 'perquisite_other'
  | 'tds_amount' | 'tds_section' | 'tds_tan' | 'tds_deductor_name'
  | 'rent_paid' | 'rent_landlord_name' | 'rent_landlord_pan'
  | 'rent_address' | 'rent_period'
  | 'ppf_deposit' | 'ppf_account_number' | 'ppf_bank'
  | 'nps_contribution' | 'nps_pran'
  | 'elss_investment' | 'elss_folio' | 'elss_fund_name'
  | 'lic_premium' | 'lic_policy_number'
  | 'home_loan_interest' | 'home_loan_principal'
  | 'home_loan_lender' | 'home_loan_property_address'
  | 'health_insurance_premium' | 'health_insurance_insurer'
  | 'health_insurance_policy_number'
  | 'donation_amount' | 'donation_institution' | 'donation_institution_pan'
  | 'savings_interest' | 'fd_interest' | 'rd_interest'
  | 'dividend_amount' | 'dividend_company'
  | 'capital_gain_stcg' | 'capital_gain_ltcg'
  | 'capital_gain_isin' | 'capital_gain_purchase_date'
  | 'capital_gain_sale_date' | 'capital_gain_purchase_price'
  | 'capital_gain_sale_price' | 'capital_gain_expenses'
  | 'bank_account_number' | 'bank_ifsc' | 'bank_name'
  | 'foreign_income_amount' | 'foreign_tax_paid' | 'foreign_country'
  | 'agricultural_income'
  | 'business_turnover' | 'business_presumptive_income'
  | 'gstin' | 'gst_turnover'
  ;

interface NormalizedValue {
  type: 'string' | 'number' | 'date' | 'currency' | 'pan' | 'tan' | 'ifsc' | 'boolean';
  stringValue?: string;
  numberValue?: number;
  dateValue?: string;                            // ISO 8601
  currencyValue?: { amount: number; currency: 'INR' };
}
```

### 2.2 Conversation Memory

```typescript
interface ConversationMemory {
  sessionId: string;
  turns: ConversationTurn[];
  extractedFacts: ExtractedFact[];
  pendingQuestions: PendingQuestion[];
  answeredQuestions: AnsweredQuestion[];
  state: ConversationState;
  metadata: {
    startedAt: string;
    lastActivityAt: string;
    turnCount: number;
    totalUserMessages: number;
    totalSystemMessages: number;
  };
}

interface ConversationTurn {
  turnId: string;
  timestamp: string;
  role: 'system' | 'user' | 'assistant' | 'agent';
  agentType?: AgentType;
  messageType: 'text' | 'question' | 'answer' | 'clarification'
              | 'error' | 'system_notification' | 'data_display';
  content: string;
  structuredData?: Record<string, any>;          // For data_display messages
  metadata?: {
    tokensUsed?: number;
    latencyMs?: number;
    confidenceScore?: number;
    triggeredValidation?: boolean;
  };
}

type ConversationState =
  | 'idle'
  | 'uploading_documents'
  | 'processing_documents'
  | 'reviewing_extracted_data'
  | 'asking_questions'
  | 'computing_tax'
  | 'presenting_results'
  | 'generating_json'
  | 'completed'
  | 'error';
```

### 2.3 Taxpayer Profile

```typescript
interface TaxpayerProfile {
  // Identity
  pan: string;
  firstName: string;
  middleName?: string;
  lastName: string;
  dateOfBirth: string;
  gender: 'MALE' | 'FEMALE' | 'TRANSGENDER';
  aadhaarLinked: boolean;

  // Contact
  email: string;
  mobileNumber: string;
  address: Address;

  // Tax Status
  taxpayerType: TaxpayerType;
  residenceStatus: ResidenceStatus;
  isPoliticallyExposed: boolean;

  // Employment
  employmentType: 'SALARIED' | 'SELF_EMPLOYED' | 'PROFESSIONAL'
                  | 'BUSINESS' | 'PENSIONER' | 'NOT_EMPLOYED';
  hasMultipleEmployers: boolean;

  // Bank
  bankAccounts: BankAccountDetail[];

  // Historical
  previousYearITRType?: string;
  previousYearRegime?: 'old' | 'new';
  previousYearFilingStatus?: string;

  // Preferences
  preferredRegime?: 'old' | 'new';
  preferredLanguage: 'en' | 'hi';
  optedForNewRegimePreviousYear: boolean;
}

type TaxpayerType = 'INDIVIDUAL' | 'SENIOR_CITIZEN' | 'SUPER_SENIOR_CITIZEN';
type ResidenceStatus = 'RESIDENT' | 'NON_RESIDENT' | 'RESIDENT_BUT_NOT_ORDINARILY_RESIDENT';
```

---

## 3. REST API Contracts

### 3.1 Base URL & Headers

```
Base URL: https://api.taxstox.com/v1

Headers:
  Authorization: Bearer <jwt_token>
  Content-Type: application/json
  X-Request-ID: <uuid>
  X-Client-Version: <semver>
```

### 3.2 Authentication APIs

```yaml
# POST /auth/signup
Request:
  pan: string               # "ABCDE1234F"
  fullName: string          # "Aman Mishra"
  dob: string               # "DD/MM/YYYY"
  email: string
  password: string          # (min 8 chars, hashed client-side)
  acceptedTerms: boolean

Response (201):
  userId: string
  message: string
  requiresEmailVerification: boolean

# POST /auth/login
Request:
  pan: string
  password: string

Response (200):
  accessToken: string       # JWT, 15min expiry
  refreshToken: string      # 30-day expiry
  user: UserProfile

# POST /auth/refresh
Request:
  refreshToken: string

Response (200):
  accessToken: string
  expiresIn: number

# POST /auth/logout
Response (204)
```

### 3.3 Filing Session APIs

```yaml
# POST /filing/sessions
# Create a new filing session
Request:
  assessmentYear: string    # "2026-27"
  itrType?: string         # Optional: "ITR-1", "ITR-2" — auto-detect if omitted

Response (201):
  sessionId: string
  assessmentYear: string
  itrType: string
  currentStep: string       # "upload"
  createdAt: string

# GET /filing/sessions/{sessionId}
Response (200):
  sessionId: string
  userId: string
  assessmentYear: string
  itrType: string
  status: FilingStatus
  currentStep: WizardStep
  uploadedDocuments: DocumentSummary[]
  extractedEntityCount: number
  validationResultCount: number
  questionsAnswered: number
  questionsRemaining: number
  regimeSelected: string | null
  taxComputed: boolean
  jsonGenerated: boolean
  createdAt: string
  updatedAt: string

# POST /filing/sessions/{sessionId}/documents/upload-url
Request:
  fileName: string
  contentType: string       # "application/pdf"
  fileSize: number

Response (200):
  uploadUrl: string         # Presigned S3 URL
  fields: Record<string, string>  # Form fields for S3 POST
  documentId: string
  expiresAt: string

# POST /filing/sessions/{sessionId}/documents/{documentId}/confirm
Response (200):
  documentId: string
  status: "uploaded" | "processing" | "processed"

# GET /filing/sessions/{sessionId}/documents/status
# Long-polling endpoint for processing status
Response (200):
  documents: DocumentStatus[]

# GET /filing/sessions/{sessionId}/entities
# Get all extracted entities (after processing)
Response (200):
  entities: ExtractedEntity[]
  summary: {
    totalEntities: number
    highConfidence: number
    mediumConfidence: number
    lowConfidence: number
    entitiesNeedingReview: ExtractedEntity[]
  }

# PATCH /filing/sessions/{sessionId}/entities/{entityId}
# User correction of an entity
Request:
  newValue: NormalizedValue
  reason?: string

Response (200):
  entity: ExtractedEntity   # Updated

# GET /filing/sessions/{sessionId}/questions
# Get next adaptive question
Response (200):
  questions: Question[]
  remainingEstimated: number
  canSkip: boolean

# POST /filing/sessions/{sessionId}/answers
Request:
  questionId: string
  value: any
  skipped?: boolean

Response (200):
  accepted: boolean
  followUpQuestion?: Question
  conflicts?: ValidationConflict[]

# POST /filing/sessions/{sessionId}/compute-tax
# Trigger tax computation
Response (202):
  computationId: string
  status: "queued"

# GET /filing/sessions/{sessionId}/tax-computation
Response (200):
  oldRegime?: TaxComputationResponse
  newRegime?: TaxComputationResponse
  recommendation: RegimeRecommendation

# POST /filing/sessions/{sessionId}/select-regime
Request:
  regime: "old" | "new"

Response (200):
  sessionId: string
  selectedRegime: string

# POST /filing/sessions/{sessionId}/generate-json
Response (202):
  status: "generating"

# GET /filing/sessions/{sessionId}/json
Response (200):
  downloadUrl: string       # Presigned download URL
  fileName: string          # "ITR1_CFFPM4503N_2025-26.json"
  fileSize: number
  hash: string
  expiresAt: string
  exportInstructions: ExportInstructions
```

### 3.4 Dashboard APIs

```yaml
# GET /dashboard/stats
Response (200):
  totalFilings: number
  totalRefunds: number      # Sum of all refunds
  totalTaxSaved: number     # Sum saved via optimization
  currentYearFilings: number
  nextDeadline: {
    date: string
    daysRemaining: number
    description: string
  }

# GET /dashboard/filings
Query:
  assessmentYear?: string
  status?: string
  page?: number
  limit?: number

Response (200):
  filings: FilingSummary[]
  total: number
  page: number
  totalPages: number

# GET /dashboard/profile
Response (200):
  profile: TaxpayerProfile

# PATCH /dashboard/profile
Request:
  email?: string
  mobileNumber?: string
  address?: Address
  bankAccounts?: BankAccountDetail[]

Response (200):
  profile: TaxpayerProfile
```

### 3.5 Tool APIs

```yaml
# POST /tools/regime-compare
Request:
  assessmentYear: string
  grossSalary: number
  hraReceived?: number
  rentPaid?: number
  metroCity?: boolean
  deductions80C?: number
  deductions80D?: number
  homeLoanInterest?: number
  otherIncome?: number
  # ... any subset of income/deduction fields

Response (200):
  oldRegime: TaxComputationResponse
  newRegime: TaxComputationResponse
  recommendation: RegimeRecommendation

# POST /tools/hra-calculate
Request:
  basicSalary: number
  da: number
  hraReceived: number
  rentPaidPerMonth: number
  metroCity: boolean

Response (200):
  exemption: number
  taxable: number
  breakdown: HRABreakdown
```

### 3.6 Support APIs

```yaml
# POST /support/chat
Request:
  message: string
  sessionId?: string       # Filing session context

Response (200):
  reply: string
  references?: Reference[]
```

---

## 4. WebSocket Events

### 4.1 Event Stream

```
ws://api.taxstox.com/v1/ws?token=<jwt>
```

### 4.2 Event Types

```typescript
type WSEvent =
  // Document Events
  | { type: 'DOCUMENT_UPLOADED'; documentId: string; fileName: string }
  | { type: 'DOCUMENT_PROCESSING'; documentId: string; progress: number }
  | { type: 'DOCUMENT_PROCESSED'; documentId: string; documentType: string; confidence: number }
  | { type: 'DOCUMENT_FAILED'; documentId: string; error: string; recoverable: boolean }

  // Entity Events
  | { type: 'ENTITIES_EXTRACTED'; count: number; needsReview: number }

  // Validation Events
  | { type: 'VALIDATION_STARTED'; totalRules: number }
  | { type: 'VALIDATION_COMPLETED'; passed: number; warnings: number; critical: number }
  | { type: 'MISMATCH_DETECTED'; mismatch: ValidationConflict }

  // Tax Computation Events
  | { type: 'TAX_COMPUTATION_STARTED' }
  | { type: 'TAX_COMPUTATION_COMPLETED'; regime: string }
  | { type: 'TAX_COMPUTATION_FAILED'; error: string }

  // JSON Generation Events
  | { type: 'JSON_GENERATION_STARTED' }
  | { type: 'JSON_GENERATION_COMPLETED'; downloadReady: boolean }
  | { type: 'JSON_GENERATION_FAILED'; error: string }

  // Session Events
  | { type: 'SESSION_EXPIRING'; minutesRemaining: number }
  | { type: 'SESSION_EXPIRED' }
  | { type: 'ERROR'; code: string; message: string; details?: any };
```

---

## 5. Error Response Format

```typescript
interface APIError {
  error: {
    code: string;                     // Machine-readable: "PAN_VALIDATION_FAILED"
    message: string;                  // Human-readable: "Invalid PAN format. Use: ABCDE1234F"
    details?: any;                    // Additional context
    requestId: string;                // For support correlation
    timestamp: string;
  };
}

// Standard HTTP status codes:
// 400: Bad Request (validation)
// 401: Unauthorized
// 403: Forbidden
// 404: Not Found
// 409: Conflict (duplicate, state mismatch)
// 422: Unprocessable Entity (business logic error)
// 429: Too Many Requests
// 500: Internal Server Error
// 503: Service Unavailable
```

---

## 6. Versioning Strategy

- API version in URL path: `/v1/`, `/v2/`
- ITR JSON schema versioning: Each AY has a specific schema version
- Backward compatibility: V1 APIs supported for 12 months after V2 release
- Deprecation: `Sunset` header with deprecation date
- Schema migration: Automatic migration of saved sessions to latest AY schema

---

*Next: [20 Function Calling & Retry Logic](20-function-calling-retry-logic.md)*
