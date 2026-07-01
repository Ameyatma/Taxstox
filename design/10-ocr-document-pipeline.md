# 10 — OCR & Document Pipeline

> **Parent:** [00-README.md](00-README.md) | **Prev:** [09 Multi-Agent Architecture](09-multi-agent-architecture.md) | **Next:** [11 Entity Extraction](11-entity-extraction-pipeline.md)

---

## 1. Pipeline Overview

```
Document Upload
    │
    ▼
┌─────────────────────────────────────────────────────┐
│              DOCUMENT INGESTION LAYER                 │
│  • Virus scan (ClamAV)                               │
│  • Format validation (PDF/JPEG/PNG)                  │
│  • Size check (<10MB)                                │
│  • PDF password detection & removal                  │
│  • Content hash computation (SHA-256 for dedup)      │
│  • Store raw file to encrypted S3 bucket              │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              OCR / TEXT EXTRACTION LAYER              │
│  • Digital PDFs → pdf.js / PyMuPDF text extraction   │
│  • Scanned PDFs → Tesseract OCR / AWS Textract       │
│  • Images → AWS Textract / Google Document AI        │
│  • Preserve table structure (rows, columns)          │
│  • Preserve spatial layout (bounding boxes)          │
│  • Output: Structured text + layout metadata         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│            DOCUMENT CLASSIFICATION LAYER             │
│  • LLM-based classification (Haiku, fast/cheap)      │
│  • Rule-based feature extraction as fallback         │
│  • Multi-document detection (single PDF → multiple)  │
│  • Confidence scoring with fallback strategies       │
│  • Output: DocumentType + confidence + page ranges   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│            ENTITY EXTRACTION LAYER                    │
│  • See: 11-entity-extraction-pipeline.md             │
└─────────────────────────────────────────────────────┘
```

---

## 2. Document Ingest Service

### 2.1 Upload Flow

```
Client                          API Gateway                  Document Service              S3
  │                                  │                              │                       │
  │  POST /upload-url               │                              │                       │
  │  { filename, contentType }      │                              │                       │
  │ ─────────────────────────────►  │                              │                       │
  │                                  │  Generate presigned URL     │                       │
  │                                  │ ──────────────────────────► │                       │
  │                                  │                              │  presigned POST URL   │
  │                                  │ ◄────────────────────────── │                       │
  │  { uploadUrl, fields,            │                              │                       │
  │    documentId }                  │                              │                       │
  │ ◄─────────────────────────────  │                              │                       │
  │                                  │                              │                       │
  │  POST (multipart to S3)         │                              │                       │
  │ ──────────────────────────────────────────────────────────────►│                       │
  │                                  │                              │                       │
  │  POST /documents/{id}/confirm   │                              │                       │
  │ ─────────────────────────────►  │  Confirm upload              │                       │
  │                                  │ ──────────────────────────► │                       │
  │                                  │                              │  Trigger processing   │
  │                                  │                              │ ──────► SQS Queue     │
  │  202 Accepted                   │                              │                       │
  │ ◄─────────────────────────────  │                              │                       │
```

### 2.2 Virus Scanning

```typescript
interface VirusScanResult {
  clean: boolean;
  virusName?: string;
  scanDuration: number; // ms
}

// Implementation: Stream file through ClamAV daemon
// Infected files: Delete immediately, log, return error to user
// Clean files: Proceed to format validation
```

### 2.3 Format Validation

```typescript
const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/png',
];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

function validateFile(file: Buffer, mimeType: string, fileName: string): ValidationResult {
  // 1. Check MIME type by magic bytes (not file extension)
  const detectedType = detectMimeType(file);

  if (!ALLOWED_MIME_TYPES.includes(detectedType)) {
    return {
      valid: false,
      error: 'WRONG_FORMAT',
      message: `Detected format: ${detectedType}. Only PDF, JPEG, and PNG are supported.`,
      detectedType,
    };
  }

  // 2. Check file size
  if (file.length > MAX_FILE_SIZE) {
    return {
      valid: false,
      error: 'TOO_LARGE',
      message: `File is ${(file.length / 1024 / 1024).toFixed(1)}MB. Maximum is 10MB.`,
      fileSize: file.length,
    };
  }

  return { valid: true };
}
```

### 2.4 PDF Password Detection & Handling

```typescript
async function handlePdfPassword(
  pdfBuffer: Buffer,
  pan?: string
): Promise<UnlockedPdfResult> {
  // 1. Check if PDF is encrypted
  const pdfDoc = await PDFDocument.load(pdfBuffer);

  if (!pdfDoc.isEncrypted) {
    return { encrypted: false, buffer: pdfBuffer };
  }

  // 2. Auto-attempt PAN (lowercase) as password
  if (pan) {
    try {
      const unlocked = await PDFDocument.load(pdfBuffer, {
        password: pan.toLowerCase(),
      });
      return { encrypted: true, autoUnlocked: true, buffer: await unlocked.save() };
    } catch {
      // PAN didn't work, continue
    }
  }

  // 3. If auto-unlock failed, request password from user
  return { encrypted: true, autoUnlocked: false, requiresPassword: true };
}
```

---

## 3. OCR / Text Extraction Layer

### 3.1 Technology Selection Matrix

| Document Type | Technology | Accuracy | Speed | Cost |
|---------------|-----------|----------|-------|------|
| Digital PDF (text embedded) | PyMuPDF (fitz) | 100% | < 1s/page | Free |
| Digital PDF (complex tables) | Camelot / Tabula | 95%+ | 2-5s/page | Free |
| Scanned PDF (clean) | Tesseract 5 + custom trained model | 92-98% | 3-8s/page | Free |
| Scanned PDF (noisy) | AWS Textract | 95-99% | 2-4s/page | $0.0015/page |
| Images (JPEG/PNG) | AWS Textract / Google Document AI | 95-99% | 1-3s/image | $0.0015/image |
| Handwritten text | AWS Textract (handwriting mode) | 85-92% | 3-6s/page | $0.015/page |

### 3.2 Extraction Strategy Decision Tree

```
Is the PDF digitally born (has embedded text)?
  ├── YES → Extract with PyMuPDF
  │   └── Does it contain complex tables?
  │       ├── YES → Also run Camelot for table extraction
  │       └── NO  → Use PyMuPDF text with layout preservation
  │
  └── NO  → It's a scanned document
      └── Is image quality good (>200 DPI, clean)?
          ├── YES → Tesseract 5 (cost optimization)
          └── NO  → AWS Textract (quality priority)
```

### 3.3 OCR Output Format

```typescript
interface OcrPage {
  pageNumber: number;
  width: number;  // in points
  height: number;
  blocks: OcrBlock[];
}

interface OcrBlock {
  blockId: number;
  blockType: 'text' | 'table' | 'image' | 'header' | 'footer';
  bbox: BoundingBox;  // { x, y, width, height }
  lines: OcrLine[];
  confidence: number;  // 0.0 - 1.0
}

interface OcrLine {
  text: string;
  bbox: BoundingBox;
  words: OcrWord[];
  confidence: number;
}

interface OcrWord {
  text: string;
  bbox: BoundingBox;
  confidence: number;
}
```

---

## 4. Document Classification Layer

### 4.1 Supported Document Types (V1)

| Category | Document Type | Key Identifiers |
|----------|--------------|-----------------|
| **Tax Core** | Form 16 (Part A) | "Form 16", "Certificate under section 203", "TDS", TAN, employer name |
| **Tax Core** | Form 16 (Part B) | Salary breakup, allowances, perquisites, "Part B" |
| **Tax Core** | Form 26AS | "Form 26AS", "Annual Tax Statement", TDS details, PAN |
| **Tax Core** | AIS (Annual Information Statement) | "Annual Information Statement", "AIS", multiple financial categories |
| **Tax Core** | TIS (Taxpayer Information Summary) | "Taxpayer Information Summary", "TIS" |
| **Income** | Salary Slip | Employer name, month/year, earnings, deductions, "Pay Slip" |
| **Income** | Bank Statement | Bank name, account number, transaction list, "Statement" |
| **Income** | Interest Certificate | "Interest Certificate", bank name, interest amounts |
| **Income** | Rent Receipt | "Rent Receipt", landlord name, PAN, address, amount |
| **Investment** | PPF Statement | "Public Provident Fund", "PPF", account number, deposits |
| **Investment** | NPS Statement | "National Pension System", "NPS", PRAN, contributions |
| **Investment** | ELSS Statement | "ELSS", "Equity Linked Savings Scheme", fund name, folio |
| **Investment** | LIC Premium Receipt | "Life Insurance Corporation", "LIC", policy number, premium |
| **Investment** | Home Loan Certificate | "Home Loan", "Housing Loan", "Interest Certificate", 80EEA |
| **Investment** | Mutual Fund Statement | "Mutual Fund", "CAMS", "Karvy", folio, transactions |
| **Capital Gains** | Broker Statement | "Zerodha", "Groww", "Upstox", trade list, P&L |
| **Capital Gains** | Demat Statement | "Demat", "NSDL", "CDSL", holdings, transactions |
| **Capital Gains** | Capital Gains Report | "Capital Gains", "Short Term", "Long Term", ISIN |
| **Health** | Insurance Receipt | "Health Insurance", policy number, premium, 80D |
| **Health** | Medical Bills | Hospital name, patient name, amount, dates |
| **Charity** | Donation Receipt | "Donation", "80G", organization name, PAN, amount |
| **Property** | Property Document | "Sale Deed", "Purchase Deed", property value, date |
| **Property** | Municipal Tax Receipt | "Municipal", "Property Tax", property ID |
| **Foreign** | Foreign Income Statement | Foreign employer, foreign salary, foreign tax paid |
| **Business** | GST Return | "GSTR", "GST", turnover, tax liability |
| **Business** | Business Statement | "Profit & Loss", "Income & Expenditure", business income |

### 4.2 Classification Pipeline

```typescript
interface ClassificationPipeline {
  // Phase 1: Rule-based feature extraction (fast pre-filter)
  ruleBasedPreFilter(ocrOutput: OcrPage[]): DocumentFeatures;

  // Phase 2: LLM-based classification (primary)
  llmClassify(features: DocumentFeatures, ocrSample: string): ClassificationResult;

  // Phase 3: Consensus & confidence
  resolveClassification(results: ClassificationResult[]): FinalClassification;
}

interface DocumentFeatures {
  // Keywords found
  exactMatches: string[];      // "Form 16", "26AS"
  partialMatches: string[];    // "Annual", "TDS"
  regexMatches: RegexMatch[];  // PAN pattern, TAN pattern, date patterns

  // Structural features
  hasTables: boolean;
  tableCount: number;
  hasLetterhead: boolean;
  hasDigitalSignature: boolean;
  hasBarcode: boolean;

  // Metadata
  pageCount: number;
  hasEmbeddedText: boolean;
  fileSize: number;
  producer?: string;           // PDF producer metadata
  author?: string;

  // Content statistics
  totalWords: number;
  uniqueWords: number;
  numericDensity: number;      // Ratio of numbers to text
  currencySymbolCount: number;
  panMentions: number;
  dateMentions: number;
}
```

### 4.3 LLM Classification Prompt Template

```
You are a document classification system for Indian tax documents.

Analyze the following text from a financial document and classify it.

Document text sample:
```
{documentTextSample}
```

Document features:
- Page count: {pageCount}
- Has tables: {hasTables}
- Contains PAN-like patterns: {panMentions}
- Contains TAN-like patterns: {tanMentions}
- Contains ₹ symbols: {currencySymbolCount}
- Keywords found: {keywords}

Classify this document into ONE of the following types:
- form_16_part_a
- form_16_part_b
- form_26as
- ais_statement
- salary_slip
- bank_statement
- interest_certificate
- rent_receipt
- ppf_statement
- nps_statement
- elss_statement
- lic_receipt
- home_loan_certificate
- mutual_fund_statement
- broker_statement
- demat_statement
- capital_gains_report
- health_insurance_receipt
- donation_receipt
- property_document
- gst_return
- business_statement
- foreign_income_statement
- unknown

Respond with JSON:
{
  "document_type": "form_16_part_a",
  "confidence": 0.97,
  "reasoning": "Contains 'Form 16', TAN number, employer details, TDS summary",
  "alternative_types": ["salary_slip"],
  "issuing_entity": "Tata Consultancy Services Ltd",
  "financial_year": "2025-26",
  "assessment_year": "2026-27"
}
```

---

## 5. Processing Pipeline Orchestration

### 5.1 Queue Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Document    │────►│  Document     │────►│  Entity       │
│  Ingest      │     │  Processing   │     │  Extraction   │
│  Queue       │     │  Queue        │     │  Queue        │
│  (SQS)       │     │  (SQS)        │     │  (SQS)        │
└──────────────┘     └──────────────┘     └──────────────┘
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Ingest      │     │  OCR +       │     │  Entity       │
│  Worker      │     │  Classify    │     │  Extract      │
│  (ECS Task)  │     │  Worker      │     │  Worker       │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                     │
                            └─────────┬───────────┘
                                      │
                                      ▼
                            ┌──────────────┐
                            │  Validation   │
                            │  Queue (SQS)  │
                            └──────────────┘
                                      │
                                      ▼
                            ┌──────────────┐
                            │  Validation   │
                            │  Worker       │
                            └──────────────┘
```

### 5.2 Worker Implementation Pattern

```typescript
interface DocumentProcessingJob {
  jobId: string;
  sessionId: string;
  documentId: string;
  s3Key: string;
  documentType?: string;  // If manually specified by user
  retryCount: number;
  maxRetries: number;
  createdAt: Date;
}

// Worker main loop
async function processDocument(job: DocumentProcessingJob): Promise<void> {
  try {
    // 1. Download from S3 (streaming, don't load entire file in memory)
    const fileStream = await s3.getObject({ Bucket, Key: job.s3Key }).createReadStream();

    // 2. Virus scan (stream through ClamAV)
    const scanResult = await virusScan(fileStream);
    if (!scanResult.clean) throw new VirusDetectedError(scanResult);

    // 3. Extract text (OCR)
    const ocrOutput = await extractText(job);

    // 4. Classify
    const classification = await classifyDocument(ocrOutput, job);

    // 5. Extract entities
    const entities = await extractEntities(ocrOutput, classification);

    // 6. Store results
    await updateDocumentRecord(job.documentId, {
      status: 'processed',
      classification,
      pageCount: ocrOutput.length,
      entitiesExtracted: entities.length,
    });

    // 7. Enqueue validation
    await enqueueValidation(job.sessionId);

    // 8. Notify client via WebSocket
    await notifyClient(job.sessionId, {
      type: 'DOCUMENT_PROCESSED',
      documentId: job.documentId,
      documentType: classification.documentType,
      confidence: classification.confidence,
    });

  } catch (error) {
    if (job.retryCount < job.maxRetries) {
      await requeueWithBackoff(job);
    } else {
      await markAsFailed(job.documentId, error);
      await notifyClient(job.sessionId, {
        type: 'DOCUMENT_FAILED',
        documentId: job.documentId,
        error: getUserFacingError(error),
      });
    }
  }
}
```

### 5.3 Retry & Backoff Strategy

```
Attempt 1: Immediate
Attempt 2: 5 second delay
Attempt 3: 25 second delay (exponential: 5^2)
Attempt 4: 125 second delay (exponential: 5^3)
Attempt 5: 625 second delay + mark as failed
```

See [20-function-calling-retry-logic.md](20-function-calling-retry-logic.md) for complete retry logic.

---

## 6. Multi-Document Handling

### 6.1 Detecting Multiple Documents in One PDF

```typescript
function splitMultiDocumentPdf(ocrOutput: OcrPage[]): DocumentSplit[] {
  const splits: DocumentSplit[] = [];
  let currentStart = 0;

  for (let i = 1; i < ocrOutput.length; i++) {
    const prevPage = ocrOutput[i - 1];
    const currPage = ocrOutput[i];

    // Detection signals:
    // 1. Page contains a new header/letterhead
    // 2. Sharp change in document structure
    // 3. New PAN/TAN that differs from previous pages
    // 4. "Page 1 of N" pattern restart

    if (isNewDocumentBoundary(prevPage, currPage)) {
      splits.push({
        pageRange: { start: currentStart, end: i - 1 },
        pages: ocrOutput.slice(currentStart, i),
      });
      currentStart = i;
    }
  }

  // Add final split
  splits.push({
    pageRange: { start: currentStart, end: ocrOutput.length - 1 },
    pages: ocrOutput.slice(currentStart),
  });

  return splits;
}
```

---

## 7. Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| File upload (10MB) | < 30s on 10Mbps | P95 latency |
| Virus scan | < 2s | P95 latency |
| Text extraction (digital PDF, 10 pages) | < 3s | P95 latency |
| Text extraction (scanned PDF, 10 pages) | < 15s | P95 latency |
| Document classification | < 2s | P95 latency |
| Total pipeline (single typical Form 16) | < 10s | P95 latency |
| Total pipeline (Form 16 + AIS, both PDF) | < 20s | P95 latency |

---

## 8. Cost Optimization

| Strategy | Implementation |
|----------|----------------|
| Digital-first extraction | Use free PyMuPDF for 90%+ of documents (most are digital PDFs) |
| Tesseract for clean scans | Free, handles ~80% of scanned documents |
| Textract only for complex scans | Pay only for the 5-10% that need it |
| LLM model selection | Haiku for classification (cheap/fast), Sonnet for complex extraction |
| Batch processing | Group document processing during off-peak hours |
| Caching | Cache OCR results by content hash (SHA-256) |

---

*Next: [11 Entity Extraction Pipeline](11-entity-extraction-pipeline.md)*
