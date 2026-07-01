# Database Design — TaxStox AI-Powered Indian Income Tax Assistant

> **Version:** 1.0  
> **Last Updated:** 2026-06-29  
> **Status:** Draft for Review  
> **Database:** PostgreSQL 16 + Redis 7 + MinIO/S3

---

## Table of Contents

1. [PostgreSQL Schema](#1-postgresql-schema)
   - [1.1 `users`](#11-users)
   - [1.2 `taxpayer_profiles`](#12-taxpayer_profiles)
   - [1.3 `filing_sessions`](#13-filing_sessions)
   - [1.4 `documents`](#14-documents)
   - [1.5 `extracted_entities`](#15-extracted_entities)
   - [1.6 `validation_results`](#16-validation_results)
   - [1.7 `tax_computations`](#17-tax_computations)
   - [1.8 `deductions_claimed`](#18-deductions_claimed)
   - [1.9 `itr_jsons`](#19-itr_jsons)
   - [1.10 `audit_log`](#110-audit_log)
   - [1.11 `conversation_turns`](#111-conversation_turns)
   - [1.12 `recommendations`](#112-recommendations)
   - [1.13 `notification_log`](#113-notification_log)
   - [1.14 `user_consent_log`](#114-user_consent_log)
   - [1.15 `rule_definitions`](#115-rule_definitions)
   - [1.16 `prompt_templates`](#116-prompt_templates)
   - [1.17 `entity_type_master`](#117-entity_type_master)
   - [1.18 `document_type_master`](#118-document_type_master)
   - [1.19 `admin_users`](#119-admin_users)
   - [1.20 `data_purge_log`](#120-data_purge_log)
2. [Complete DDL](#2-complete-ddl)
3. [Index Justification](#3-index-justification)
4. [Redis Data Models](#4-redis-data-models)
5. [S3/MinIO Document Storage](#5-s3minio-document-storage)
6. [Data Retention and Purging](#6-data-retention-and-purging)
7. [Migration Strategy](#7-migration-strategy)

---

## 1. PostgreSQL Schema

### 1.1 `users`

Core user identity table. Stores only hashed/encrypted PII. Raw PAN is **never** stored.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | Primary identifier |
| `pan_hash` | `VARCHAR(64)` | `UNIQUE NOT NULL` | SHA-256 hash of PAN (uppercase, no spaces) |
| `pan_salt` | `VARCHAR(32)` | `NOT NULL` | Per-user salt for PAN hashing |
| `pan_last_four` | `VARCHAR(4)` | `NOT NULL` | Last 4 chars of PAN (for display: "XXXX1234F") |
| `email_hash` | `VARCHAR(64)` | `NOT NULL` | SHA-256 hash of email |
| `email_encrypted` | `BYTEA` | | AES-256-GCM encrypted email (for sending emails) |
| `phone_hash` | `VARCHAR(64)` | `NOT NULL` | SHA-256 hash of mobile number |
| `phone_encrypted` | `BYTEA` | | AES-256-GCM encrypted phone (for sending SMS) |
| `phone_country_code` | `VARCHAR(5)` | `DEFAULT '+91'` | Country code for SMS |
| `name_encrypted` | `BYTEA` | | Encrypted full name as per PAN |
| `name_hash` | `VARCHAR(64)` | | SHA-256 hash of name (for dedup check) |
| `dob_encrypted` | `BYTEA` | | Encrypted date of birth |
| `dob_hash` | `VARCHAR(64)` | | SHA-256 hash of DOB (for dedup) |
| `pan_verified_at` | `TIMESTAMPTZ` | | When PAN was verified via Protean API |
| `pan_verification_ref` | `VARCHAR(64)` | | Protean/TIN-NSDL transaction reference |
| `aadhaar_hash` | `VARCHAR(64)` | | SHA-256 hash of Aadhaar (last 4 digits stored separately) |
| `aadhaar_last_four` | `VARCHAR(4)` | | Last 4 digits of Aadhaar |
| `aadhaar_verified_at` | `TIMESTAMPTZ` | | When Aadhaar OTP was verified |
| `preferred_language` | `VARCHAR(10)` | `DEFAULT 'en'` | Language preference (en/hi/ta/te/bn/gu/mr) |
| `preferred_regime` | `VARCHAR(10)` | `DEFAULT 'new'` | Default tax regime (new/old) |
| `is_active` | `BOOLEAN` | `DEFAULT true` | Soft-delete flag |
| `is_onboarded` | `BOOLEAN` | `DEFAULT false` | Has completed initial onboarding |
| `onboarding_step` | `VARCHAR(50)` | `DEFAULT 'created'` | Current onboarding step |
| `last_login_at` | `TIMESTAMPTZ` | | Last successful login timestamp |
| `failed_login_attempts` | `INTEGER` | `DEFAULT 0` | Consecutive failed login count |
| `locked_until` | `TIMESTAMPTZ` | | Account lockout until (if failed attempts > 5) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |
| `deleted_at` | `TIMESTAMPTZ` | | Soft-delete timestamp |
| `anonymized_at` | `TIMESTAMPTZ` | | When PII was permanently anonymized |

**Indexes:**
- `PK` on `id`
- `UNIQUE` on `pan_hash` — fast login/lookup by PAN
- `UNIQUE` on `email_hash` — prevent duplicate email registration
- `UNIQUE` on `phone_hash` — prevent duplicate phone registration
- `INDEX` on `created_at` — cohort analysis
- `INDEX` on `last_login_at` — active user identification
- `INDEX` on `is_active WHERE is_active = true` — filtered index for active user queries

### 1.2 `taxpayer_profiles`

Extended taxpayer profile, one per user per assessment year. Contains aggregated profile data used for prefilling and AI context.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | |
| `user_id` | `UUID` | `FK → users.id NOT NULL` | |
| `pan_hash` | `VARCHAR(64)` | `NOT NULL` | Denormalized for query convenience |
| `assessment_years` | `TEXT[]` | `NOT NULL DEFAULT '{}'` | Array of AYs filed (e.g., {"2024-25","2025-26"}) |
| `current_ay` | `VARCHAR(7)` | | Current active assessment year (e.g., "2025-26") |
| `occupation_type` | `VARCHAR(50)` | | salaried/business/profession/retired/other |
| `employer_category` | `VARCHAR(50)` | | government/private/mnc/startup/self |
| `has_multiple_employers` | `BOOLEAN` | `DEFAULT false` | Changed jobs during the year |
| `has_business_income` | `BOOLEAN` | `DEFAULT false` |
| `has_capital_gains` | `BOOLEAN` | `DEFAULT false` |
| `has_house_property` | `BOOLEAN` | `DEFAULT false` |
| `has_foreign_assets` | `BOOLEAN` | `DEFAULT false` | Schedule FA required |
| `has_agriculture_income` | `BOOLEAN` | `DEFAULT false` |
| `regime_preference` | `VARCHAR(10)` | | new/old/undecided |
| `filing_category` | `VARCHAR(10)` | | individual/huf/firm/company/other |
| `profile_data` | `JSONB` | `NOT NULL DEFAULT '{}'` | Extended profile: address, bank accounts, employer details, nominee |
| `consent_flags` | `JSONB` | `DEFAULT '{}'` | Consent tracking: data_retention, marketing, ai_processing |
| `risk_profile` | `VARCHAR(20)` | `DEFAULT 'low'` | low/medium/high (for audit selection) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `id`
- `UNIQUE` on `(user_id)` — one profile per user (current profile; historical in filing_sessions)
- `INDEX` on `pan_hash` — admin lookup
- `INDEX` on `assessment_years USING GIN` — query users who filed in specific years
- `INDEX` on `regime_preference` — regime preference analysis
- `INDEX` on `filing_category` — demographic analysis

**Check Constraints:**
- `CHECK (occupation_type IN ('salaried','business','profession','retired','other'))`
- `CHECK (regime_preference IN ('new','old','undecided'))`
- `CHECK (filing_category IN ('individual','huf','firm','company','other'))`
- `CHECK (risk_profile IN ('low','medium','high'))`

### 1.3 `filing_sessions`

Represents a single tax filing session — from document upload through ITR generation. Each user can have multiple sessions per AY (e.g., started and abandoned; corrected filing).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | |
| `user_id` | `UUID` | `FK → users.id NOT NULL` | |
| `ay` | `VARCHAR(7)` | `NOT NULL` | Assessment year (e.g., "2025-26") |
| `itr_type` | `VARCHAR(10)` | | ITR form type (ITR-1, ITR-2, ITR-3, ITR-4, ITR-5, ITR-6) |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'initiated'` | initiated/documents_uploading/documents_processing/entities_review/computing/regime_selection/review_itr/generated/filed/abandoned/error |
| `regime` | `VARCHAR(10)` | | new/old |
| `current_step` | `VARCHAR(50)` | | Current conversation/flow step identifier |
| `current_step_data` | `JSONB` | | Serialized state for the current step |
| `progress_pct` | `SMALLINT` | `DEFAULT 0 CHECK (progress_pct >= 0 AND progress_pct <= 100)` | Progress percentage |
| `last_ai_context` | `TEXT` | | Compressed conversation summary for LLM context window |
| `llm_calls_count` | `INTEGER` | `DEFAULT 0` | Total LLM calls in this session |
| `llm_total_cost_inr` | `NUMERIC(10,2)` | `DEFAULT 0` | Accumulated LLM cost in paise (×100) |
| `error_details` | `JSONB` | | Last error details if status = error |
| `is_test_data` | `BOOLEAN` | `DEFAULT false` | Flag for test/internal filings |
| `started_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |
| `completed_at` | `TIMESTAMPTZ` | | Filing completion timestamp |
| `filed_at` | `TIMESTAMPTZ` | | When actually submitted to IT portal |
| `abandoned_at` | `TIMESTAMPTZ` | | When session was abandoned |
| `last_activity_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Updated on any activity |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `id`
- `FK_INDEX` on `user_id` — all sessions for a user
- `INDEX` on `(user_id, ay)` — find user's sessions for a year
- `INDEX` on `status` — aggregate session statuses
- `INDEX` on `created_at` — filing volume over time
- `INDEX` on `itr_type` — ITR type distribution
- `INDEX` on `last_activity_at` — find stale sessions for reminders
- `INDEX` on `(status, last_activity_at)` — abandoned sessions filter
- `INDEX` on `llm_total_cost_inr` — cost analysis
- `PARTIAL INDEX` on `completed_at WHERE completed_at IS NOT NULL` — completed sessions

**Check Constraints:**
- `CHECK (status IN ('initiated','documents_uploading','documents_processing','entities_review','computing','regime_selection','review_itr','generated','filed','abandoned','error'))`
- `CHECK (regime IN ('new','old'))`
- `CHECK (itr_type IN ('ITR-1','ITR-2','ITR-3','ITR-4','ITR-5','ITR-6'))`

### 1.4 `documents`

Metadata for every uploaded document. Raw files stored in S3 with 24h TTL; metadata retained for audit.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | |
| `session_id` | `UUID` | `FK → filing_sessions.id NOT NULL` | |
| `user_id` | `UUID` | `FK → users.id NOT NULL` | Denormalized for RLS |
| `document_type` | `VARCHAR(50)` | | Classified document type |
| `original_filename` | `VARCHAR(255)` | `NOT NULL` | Original user filename |
| `sanitized_filename` | `VARCHAR(255)` | | Server-generated safe filename |
| `file_size_bytes` | `INTEGER` | `NOT NULL` | File size |
| `mime_type` | `VARCHAR(100)` | `NOT NULL` | Detected MIME type |
| `s3_bucket` | `VARCHAR(100)` | | S3 bucket name |
| `s3_key` | `VARCHAR(500)` | | S3 object key |
| `s3_etag` | `VARCHAR(64)` | | S3 ETag for integrity verification |
| `s3_version_id` | `VARCHAR(100)` | | S3 version ID (if versioning enabled) |
| `encryption_key_id` | `VARCHAR(100)` | | KMS key identifier for this document |
| `page_count` | `SMALLINT` | | Number of pages (PDFs) |
| `file_hash_sha256` | `VARCHAR(64)` | | SHA-256 of file content for dedup |
| `classification_method` | `VARCHAR(20)` | | ai/rule_based/manual |
| `classification_confidence` | `NUMERIC(4,3)` | | ML classification confidence (0-1) |
| `classification_metadata` | `JSONB` | | Classifier output details |
| `virus_scan_status` | `VARCHAR(20)` | `DEFAULT 'pending'` | pending/scanned/clean/infected/error |
| `virus_scan_result` | `VARCHAR(255)` | | ClamAV output |
| `virus_scanned_at` | `TIMESTAMPTZ` | | |
| `ocr_status` | `VARCHAR(20)` | `DEFAULT 'pending'` | pending/processing/completed/failed |
| `ocr_engine` | `VARCHAR(50)` | | azure_document_intelligence/tesseract_5/doctr |
| `ocr_confidence` | `NUMERIC(4,3)` | | Average confidence across all pages |
| `ocr_completed_at` | `TIMESTAMPTZ` | | |
| `ocr_failure_reason` | `TEXT` | | Error details if ocr_status = failed |
| `ocr_retry_count` | `SMALLINT` | `DEFAULT 0` | Number of OCR retries |
| `parsed_at` | `TIMESTAMPTZ` | | When entity extraction completed |
| `purge_at` | `TIMESTAMPTZ` | | Auto-purge timestamp (24h from upload, or 7d if processed) |
| `purged_at` | `TIMESTAMPTZ` | | Actual purge timestamp |
| `is_deleted` | `BOOLEAN` | `DEFAULT false` | Soft delete |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `id`
- `FK_INDEX` on `session_id` — all documents in a session
- `FK_INDEX` on `user_id` — all documents for a user
- `INDEX` on `document_type` — document type distribution
- `INDEX` on `ocr_status` — pending OCR jobs
- `INDEX` on `file_hash_sha256` — deduplication check
- `INDEX` on `purge_at` — purge scheduler query
- `INDEX` on `created_at` — upload volume over time
- `PARTIAL INDEX` on `(session_id) WHERE ocr_status = 'pending'` — pending OCR jobs per session

**Check Constraints:**
- `CHECK (file_size_bytes > 0 AND file_size_bytes <= 20971520)` — max 20 MB
- `CHECK (mime_type IN ('application/pdf','image/jpeg','image/png','image/tiff'))`
- `CHECK (virus_scan_status IN ('pending','scanned','clean','infected','error'))`
- `CHECK (ocr_status IN ('pending','processing','completed','failed'))`

### 1.5 `extracted_entities`

All entities extracted from documents via OCR/NER pipeline. Supports multiple values per field from different sources; confidence-based ranking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | |
| `session_id` | `UUID` | `FK → filing_sessions.id NOT NULL` | |
| `user_id` | `UUID` | `FK → users.id NOT NULL` | Denormalized |
| `source_document_id` | `UUID` | `FK → documents.id` | Document this entity was extracted from |
| `entity_type` | `VARCHAR(50)` | `NOT NULL` | From entity_type_master |
| `entity_path` | `VARCHAR(200)` | | JSON Path in ITR schema (e.g., "ITR1.ScheduleSalary.Salary.AmountReceived") |
| `entity_label` | `VARCHAR(200)` | | Human-readable label (e.g., "Gross Salary") |
| `raw_value` | `TEXT` | `NOT NULL` | Raw extracted text |
| `normalized_value` | `TEXT` | | Cleaned/standardized value |
| `numeric_value` | `NUMERIC(18,2)` | | Parsed numeric amount (if applicable) |
| `currency` | `VARCHAR(3)` | `DEFAULT 'INR'` | Currency code |
| `unit` | `VARCHAR(20)` | | Unit for non-currency fields (e.g., percentage, count) |
| `confidence` | `NUMERIC(4,3)` | `NOT NULL` | Extraction confidence (0-1) |
| `is_user_verified` | `BOOLEAN` | `DEFAULT false` | User confirmed this value |
| `verified_by_user_at` | `TIMESTAMPTZ` | | When user verified this entity |
| `user_corrected_value` | `TEXT` | | User-provided correction |
| `user_correction_reason` | `VARCHAR(100)` | | Why user corrected (ocr_error/wrong_field/missing_doc) |
| `conflict_group` | `VARCHAR(100)` | | Group ID for conflicting values from different sources |
| `is_selected_in_conflict` | `BOOLEAN` | `DEFAULT true` | Which value is selected when conflicts resolved |
| `extraction_method` | `VARCHAR(20)` | `NOT NULL` | ocr_ner/llm_extraction/manual_entry/rule_based |
| `extraction_metadata` | `JSONB` | | Engine-specific metadata (model version, prompt template) |
| `is_active` | `BOOLEAN` | `DEFAULT true` | Soft delete (superseded by correction) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `id`
- `FK_INDEX` on `session_id` — all entities in session
- `FK_INDEX` on `source_document_id` — entities from specific document
- `FK_INDEX` on `user_id` — all entities for user
- `INDEX` on `entity_type` — entity distribution
- `INDEX` on `(session_id, entity_type)` — find specific entity type in session
- `INDEX` on `entity_path` — schema path lookup
- `INDEX` on `(session_id, is_user_verified)` — pending verification count
- `INDEX` on `conflict_group` — conflict resolution queries
- `INDEX` on `(session_id, entity_path, is_active)` — active entities for computation
- `INDEX` on `confidence` — low-confidence entity identification
- `PARTIAL INDEX` on `(session_id) WHERE is_user_verified = false AND is_active = true` — unverified active entities

**Foreign Keys:**
- `session_id → filing_sessions(id) ON DELETE CASCADE`
- `source_document_id → documents(id) ON DELETE SET NULL`
- `user_id → users(id) ON DELETE CASCADE`

### 1.6 `validation_results`

Results from the Validation Engine (400+ rules). Each rule execution produces one or more results per session.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | |
| `session_id` | `UUID` | `FK → filing_sessions.id NOT NULL` | |
| `rule_id` | `VARCHAR(20)` | `NOT NULL` | Rule identifier (e.g., "V001", "C045") |
| `rule_name` | `VARCHAR(200)` | | Human-readable rule name |
| `rule_category` | `VARCHAR(50)` | | schema/cross_field/cross_document/threshold/regime/data_integrity/math/temporal/compliance |
| `severity` | `VARCHAR(10)` | `NOT NULL` | error/warning/info |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'active'` | active/overridden/resolved/waived |
| `entity_a_id` | `UUID` | `FK → extracted_entities.id` | Primary entity involved |
| `entity_b_id` | `UUID` | `FK → extracted_entities.id` | Secondary entity (if cross-field) |
| `expected_value` | `TEXT` | | Expected value or threshold |
| `actual_value` | `TEXT` | | Actual extracted value |
| `difference` | `NUMERIC(18,2)` | | Difference amount (for numeric comparisons) |
| `message_template` | `VARCHAR(500)` | | Internationalized message template key |
| `message_params` | `JSONB` | | Parameters for message template |
| `resolution_hint` | `TEXT` | | Suggested resolution |
| `resolution_action` | `VARCHAR(50)` | | user_correction/re_upload/ignore/re_ocr |
| `overridden_by_user` | `BOOLEAN` | `DEFAULT false` | User explicitly overrode this validation |
| `override_reason` | `TEXT` | | User's reason for override |
| `overridden_at` | `TIMESTAMPTZ` | | |
| `evaluation_context` | `JSONB` | | Full context snapshot at evaluation time |
| `evaluation_duration_ms` | `INTEGER` | | Rule evaluation time |
| `evaluated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `id`
- `FK_INDEX` on `session_id` — all validations for a session
- `INDEX` on `rule_id` — rule failure frequency analysis
- `INDEX` on `(session_id, severity)` — count errors vs warnings
- `INDEX` on `(session_id, status)` — pending vs resolved
- `INDEX` on `rule_category` — which category has most failures
- `INDEX` on `entity_a_id` — which entity triggered most failures
- `INDEX` on `evaluated_at` — temporal analysis of validation runs
- `PARTIAL INDEX` on `(session_id) WHERE status = 'active' AND severity = 'error'` — blocking errors

**Check Constraints:**
- `CHECK (severity IN ('error','warning','info'))`
- `CHECK (status IN ('active','overridden','resolved','waived'))`
- `CHECK (rule_category IN ('schema','cross_field','cross_document','threshold','regime','data_integrity','math','temporal','compliance'))`

### 1.7 `tax_computations`

Immutable records of every tax computation. One session may have multiple computations (regime comparison, re-computation after correction).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | |
| `session_id` | `UUID` | `FK → filing_sessions.id NOT NULL` | |
| `user_id` | `UUID` | `FK → users.id NOT NULL` | Denormalized |
| `regime` | `VARCHAR(10)` | `NOT NULL` | new/old |
| `ay` | `VARCHAR(7)` | `NOT NULL` | Assessment year for the rate slabs used |
| `computation_version` | `VARCHAR(20)` | `NOT NULL` | Tax rule engine version (e.g., "1.2.0") |
| `computation_json` | `JSONB` | `NOT NULL` | Full computation breakdown (see schema below) |
| `entity_snapshot_hash` | `VARCHAR(64)` | | SHA-256 hash of all entities used in this computation |
| `validation_snapshot_hash` | `VARCHAR(64)` | | SHA-256 hash of active validation results |
| `is_final` | `BOOLEAN` | `DEFAULT false` | Is this the final computation for the session? |
| `triggered_by` | `VARCHAR(20)` | | auto/user_request/entity_update/regime_change |
| `computation_duration_ms` | `INTEGER` | | Time to compute |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**computation_json Structure:**
```json
{
  "gross_total_income": 1200000.00,
  "income_breakdown": {
    "salary": 1100000.00,
    "house_property": 0,
    "business_profession": 0,
    "capital_gains": 50000.00,
    "other_sources": 50000.00
  },
  "total_deductions": 150000.00,
  "deductions_breakdown": {
    "80C": 100000.00,
    "80D": 25000.00,
    "80E": 25000.00,
    "80TTA": 0,
    "80G": 0
  },
  "taxable_income": 1050000.00,
  "tax_on_income": 107250.00,
  "slab_breakdown": [
    {"slab": "0-250000", "rate": 0, "amount": 0},
    {"slab": "250000-500000", "rate": 0.05, "amount": 12500},
    {"slab": "500000-1000000", "rate": 0.20, "amount": 100000},
    {"slab": "1000000+", "rate": 0.30, "amount": 0}
  ],
  "rebate_87a": 0,
  "surcharge": 0,
  "health_cess": 4290.00,
  "total_tax_liability": 111540.00,
  "total_tds": 110000.00,
  "tax_payable": 1540.00,
  "tax_refundable": 0,
  "regime_difference": {
    "old_regime_total": 111540.00,
    "new_regime_total": 125000.00,
    "recommendation": "old",
    "savings": 13460.00
  }
}
```

**Indexes:**
- `PK` on `id`
- `FK_INDEX` on `session_id` — computations for a session
- `FK_INDEX` on `user_id` — all user computations
- `INDEX` on `(session_id, is_final) WHERE is_final = true` — final computation lookup
- `INDEX` on `(session_id, regime)` — regime comparison lookup
- `INDEX` on `created_at` — computation history

**Check Constraints:**
- `CHECK (regime IN ('new','old'))`
- `CHECK (triggered_by IN ('auto','user_request','entity_update','regime_change'))`

### 1.8 `deductions_claimed`

Line-item details for every deduction claimed. Links to source entity and supporting document.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | |
| `tax_computation_id` | `UUID` | `FK → tax_computations.id NOT NULL` | |
| `session_id` | `UUID` | `FK → filing_sessions.id NOT NULL` | Denormalized |
| `section` | `VARCHAR(10)` | `NOT NULL` | Tax section (80C, 80D, 80E, 80G, 24(b), etc.) |
| `subsection` | `VARCHAR(20)` | | Sub-category within section (e.g., for 80C: LIC/PPF/ELSS) |
| `description` | `VARCHAR(255)` | | Human-readable description |
| `amount` | `NUMERIC(18,2)` | `NOT NULL` | Claimed amount |
| `max_allowed` | `NUMERIC(18,2)` | | Maximum allowable under this section |
| `is_capped` | `BOOLEAN` | `DEFAULT false` | Whether capped by maximum limit |
| `capped_amount` | `NUMERIC(18,2)` | | Amount after cap |
| `source_entity_id` | `UUID` | `FK → extracted_entities.id` | Entity this deduction was derived from |
| `evidence_document_id` | `UUID` | `FK → documents.id` | Supporting document |
| `is_user_confirmed` | `BOOLEAN` | `DEFAULT false` | User confirmed this deduction |
| `is_ai_suggested` | `BOOLEAN` | `DEFAULT false` | AI-suggested optimization |
| `optimization_note` | `TEXT` | | AI note explaining optimization |
| `regime_applicable` | `VARCHAR(10)` | | new/old/both — which regime(s) this deduction applies to |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `id`
- `FK_INDEX` on `tax_computation_id` — deductions for a computation
- `FK_INDEX` on `session_id` — deductions in a session
- `INDEX` on `section` — section usage analysis
- `INDEX` on `(tax_computation_id, section)` — section-level grouping

**Check Constraints:**
- `CHECK (amount >= 0)`
- `CHECK (regime_applicable IN ('new','old','both'))`

### 1.9 `itr_jsons`

Generated ITR JSON/XML files. JSON stored in S3 with metadata in PostgreSQL. Supports schema versioning for multiple AYs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | |
| `session_id` | `UUID` | `FK → filing_sessions.id NOT NULL` | |
| `user_id` | `UUID` | `FK → users.id NOT NULL` | Denormalized |
| `itr_type` | `VARCHAR(10)` | `NOT NULL` | ITR-1 through ITR-6 |
| `ay` | `VARCHAR(7)` | `NOT NULL` | Assessment year |
| `regime` | `VARCHAR(10)` | `NOT NULL` | new/old |
| `schema_version` | `VARCHAR(10)` | `NOT NULL` | ITR schema version (e.g., "1.8") |
| `json_content_hash` | `VARCHAR(64)` | `NOT NULL` | SHA-256 of final JSON content |
| `xml_content_hash` | `VARCHAR(64)` | | SHA-256 of generated XML |
| `s3_bucket_final` | `VARCHAR(100)` | | S3 bucket for the final JSON |
| `s3_key_final` | `VARCHAR(500)` | | S3 key for final JSON |
| `s3_bucket_xml` | `VARCHAR(100)` | | S3 bucket for the ITR-XML |
| `s3_key_xml` | `VARCHAR(500)` | | S3 key for ITR-XML |
| `s3_bucket_user_copy` | `VARCHAR(100)` | | S3 bucket for user-downloadable copy |
| `s3_key_user_copy` | `VARCHAR(500)` | | S3 key for user copy |
| `file_size_bytes` | `INTEGER` | | JSON file size |
| `is_filed` | `BOOLEAN` | `DEFAULT false` | Has been submitted to IT portal |
| `filing_ack_number` | `VARCHAR(50)` | | IT portal acknowledgment number |
| `filing_transaction_id` | `VARCHAR(100)` | | IT portal transaction ID |
| `filed_at` | `TIMESTAMPTZ` | | When filed to IT portal |
| `filing_mode` | `VARCHAR(20)` | | online/offline (via IT portal) |
| `generated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |
| `purge_at` | `TIMESTAMPTZ` | | Retention-based purge date (7 years) |
| `purged_at` | `TIMESTAMPTZ` | | Actual purge date |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `id`
- `FK_INDEX` on `session_id` — ITR for a session
- `FK_INDEX` on `user_id` — all user ITRs
- `INDEX` on `(user_id, ay)` — user's filing history per year
- `INDEX` on `json_content_hash` — deduplication check
- `INDEX` on `is_filed` — filed vs generated-only
- `INDEX` on `purge_at` — purge scheduler

### 1.10 `audit_log`

Immutable, tamper-evident audit trail. All state-changing operations are logged here.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | Sequential (ordering preserved) |
| `event_id` | `UUID` | `UNIQUE NOT NULL DEFAULT gen_random_uuid()` | Globally unique event ID |
| `session_id` | `UUID` | `FK → filing_sessions.id` | |
| `user_id` | `UUID` | `FK → users.id` | |
| `actor_type` | `VARCHAR(20)` | `NOT NULL` | user/system/admin/ai |
| `actor_id` | `VARCHAR(100)` | `NOT NULL` | User UUID or service name or admin UUID |
| `event_type` | `VARCHAR(50)` | `NOT NULL` | See event types in table above |
| `event_category` | `VARCHAR(30)` | `NOT NULL` | auth/document/entity/validation/tax/itr/session/admin |
| `severity` | `VARCHAR(10)` | `DEFAULT 'info'` | info/warning/error/critical |
| `resource_type` | `VARCHAR(50)` | | Affected resource type (e.g., "document", "entity") |
| `resource_id` | `UUID` | | Affected resource ID |
| `details_json` | `JSONB` | `NOT NULL DEFAULT '{}'` | Event-specific payload |
| `ip_address` | `INET` | | Originating IP |
| `user_agent` | `TEXT` | | User-Agent header |
| `trace_id` | `VARCHAR(32)` | | OpenTelemetry trace ID |
| `span_id` | `VARCHAR(16)` | | OpenTelemetry span ID |
| `prev_entry_hash` | `VARCHAR(64)` | | SHA-256 hash of the previous audit entry's entry_hash |
| `data_hash` | `VARCHAR(64)` | `NOT NULL` | SHA-256 of (event_type || actor_id || details_json || created_at) |
| `entry_hash` | `VARCHAR(64)` | `NOT NULL` | SHA-256(prev_entry_hash || data_hash || nonce) |
| `nonce` | `VARCHAR(16)` | `NOT NULL` | Random nonce for hash chain |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `id` (BIGSERIAL, clustered)
- `UNIQUE` on `event_id`
- `INDEX` on `session_id` — audit trail for a session
- `INDEX` on `user_id` — all events for a user
- `INDEX` on `event_type` — filter by event
- `INDEX` on `event_category` — category analysis
- `INDEX` on `created_at` — temporal queries
- `INDEX` on `actor_id` — actions by specific actor
- `INDEX` on `resource_type, resource_id` — changes to specific resource
- `BRIN_INDEX` on `(created_at, id)` — for time-range scans (compressed index, efficient for append-only)

**Check Constraints:**
- `CHECK (actor_type IN ('user','system','admin','ai'))`
- `CHECK (event_category IN ('auth','document','entity','validation','tax','itr','session','admin'))`
- `CHECK (severity IN ('info','warning','error','critical'))`

**Tamper Verification Query:**
```sql
-- Verify chain integrity for a session
SELECT
  id, entry_hash,
  LAG(entry_hash) OVER (ORDER BY id) AS prev_stored_hash,
  prev_entry_hash,
  CASE
    WHEN LAG(entry_hash) OVER (ORDER BY id) = prev_entry_hash
      OR (LAG(entry_hash) OVER (ORDER BY id) IS NULL AND prev_entry_hash IS NULL)
    THEN 'OK'
    ELSE 'TAMPERED'
  END AS chain_status
FROM audit_log
WHERE session_id = $1
ORDER BY id;
```

### 1.11 `conversation_turns`

Every turn in a conversation between user and TaxStox AI. Used for context building, audit, and training data (anonymized).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | Sequential per session |
| `session_id` | `UUID` | `FK → filing_sessions.id NOT NULL` | |
| `turn_number` | `SMALLINT` | `NOT NULL` | Monotonically increasing per session |
| `role` | `VARCHAR(10)` | `NOT NULL` | user/assistant/system |
| `message_type` | `VARCHAR(30)` | `NOT NULL` | question/answer/clarification/confirmation/error/system_prompt/computation_result/greeting/farewell |
| `content` | `TEXT` | `NOT NULL` | Message content (PII masked before LLM) |
| `pii_masked_content` | `TEXT` | | Content with PII redacted (stored for training) |
| `metadata_json` | `JSONB` | `DEFAULT '{}'` | See metadata schema below |
| `tokens_input` | `INTEGER` | | LLM input token count (assistant turns) |
| `tokens_output` | `INTEGER` | | LLM output token count (assistant turns) |
| `llm_latency_ms` | `INTEGER` | | LLM response time (assistant turns) |
| `llm_model` | `VARCHAR(50)` | | Model used for generation |
| `llm_cost_inr` | `NUMERIC(10,2)` | | Cost of this LLM call in INR paise |
| `prompt_template_used` | `VARCHAR(100)` | | Prompt template ID and version |
| `user_rating` | `SMALLINT` | | User feedback on this turn (1-5) |
| `user_rating_comment` | `TEXT` | | Optional user comment on rating |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**metadata_json Schema:**
```json
{
  "intent": "provide_salary_info",
  "entities_mentioned": ["salary_amount", "employer_name"],
  "entities_updated": ["ITR1.ScheduleSalary.Salary.AmountReceived"],
  "conversation_state": "entities_review",
  "ai_confidence": 0.92,
  "requires_user_action": false,
  "action_taken": "entity_updated",
  "has_pii": false,
  "languages_detected": ["en", "hi"]
}
```

**Indexes:**
- `PK` on `(session_id, id)` — clustered, sequential per session
- `INDEX` on `session_id` — all turns in a session
- `INDEX` on `(session_id, turn_number)` — ordered turn lookup
- `INDEX` on `role` — user vs assistant analysis
- `INDEX` on `message_type` — interaction type analysis
- `INDEX` on `user_rating WHERE user_rating IS NOT NULL` — rated turns
- `INDEX` on `created_at` — temporal analysis

**Check Constraints:**
- `CHECK (role IN ('user','assistant','system'))`
- `CHECK (user_rating >= 1 AND user_rating <= 5 OR user_rating IS NULL)`

### 1.12 `recommendations`

AI-generated recommendations shown to the user (deduction optimization, regime selection, ITR type).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | |
| `session_id` | `UUID` | `FK → filing_sessions.id NOT NULL` | |
| `user_id` | `UUID` | `FK → users.id NOT NULL` | Denormalized |
| `recommendation_type` | `VARCHAR(50)` | `NOT NULL` | regime_selection/deduction_optimization/itr_selection/document_suggestion/filing_reminder/error_resolution |
| `title` | `VARCHAR(200)` | `NOT NULL` | Short title for display |
| `description` | `TEXT` | | Detailed recommendation |
| `details_json` | `JSONB` | `NOT NULL DEFAULT '{}'` | Structured details (see below) |
| `potential_benefit_amount` | `NUMERIC(18,2)` | | Estimated tax savings (if applicable) |
| `confidence` | `NUMERIC(4,3)` | | AI confidence in this recommendation |
| `user_accepted` | `BOOLEAN` | | Did user accept? null = not yet shown |
| `user_accepted_at` | `TIMESTAMPTZ` | | When user acted on it |
| `user_rejected_reason` | `VARCHAR(100)` | | Why rejected |
| `applied_automatically` | `BOOLEAN` | `DEFAULT false` | Applied without user action |
| `expires_at` | `TIMESTAMPTZ` | | Recommendation expiry |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**details_json Structure per type:**
```json
// regime_selection
{
  "regime_old": {"tax": 111540, "deductions_applied": 150000},
  "regime_new": {"tax": 125000, "deductions_applied": 0},
  "savings": 13460,
  "recommended": "old",
  "reasoning": "You have significant 80C deductions that are not available in new regime"
}

// deduction_optimization
{
  "section": "80C",
  "current_amount": 100000,
  "max_allowed": 150000,
  "remaining_capacity": 50000,
  "suggested_investments": [
    {"type": "ELSS", "amount": 50000, "liquidity": "3yr lock-in"}
  ],
  "potential_savings": 7500
}

// itr_selection
{
  "current_itr": "ITR-1",
  "recommended_itr": "ITR-2",
  "reason": "Capital gains reported; ITR-1 does not support Schedule CG",
  "conditions_met": ["Has capital gains > 0"],
  "conditions_not_met": []
}
```

**Indexes:**
- `PK` on `id`
- `FK_INDEX` on `session_id`
- `FK_INDEX` on `user_id`
- `INDEX` on `recommendation_type` — type analysis
- `INDEX` on `(session_id, recommendation_type)` — recommendations by type per session
- `INDEX` on `user_accepted` — acceptance rate analysis

### 1.13 `notification_log`

Log of all dispatched notifications for delivery tracking and audit.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | |
| `user_id` | `UUID` | `FK → users.id` | |
| `session_id` | `UUID` | `FK → filing_sessions.id` | |
| `channel` | `VARCHAR(10)` | `NOT NULL` | email/sms/push |
| `template_name` | `VARCHAR(100)` | `NOT NULL` | Notification template identifier |
| `recipient` | `VARCHAR(255)` | `NOT NULL` | Masked recipient (e.g., "a***@gmail.com") |
| `subject` | `VARCHAR(500)` | | Email subject / SMS preview |
| `status` | `VARCHAR(20)` | `NOT NULL DEFAULT 'queued'` | queued/sent/delivered/bounced/failed/clicked |
| `provider_message_id` | `VARCHAR(255)` | | Provider's message ID for tracking |
| `provider_response` | `JSONB` | | Raw provider response |
| `delivery_attempts` | `SMALLINT` | `DEFAULT 0` | Number of delivery attempts |
| `last_attempt_at` | `TIMESTAMPTZ` | | Last delivery attempt |
| `delivered_at` | `TIMESTAMPTZ` | | |
| `bounce_reason` | `TEXT` | | Bounce/failure reason |
| `opened_at` | `TIMESTAMPTZ` | | Email open timestamp |
| `clicked_at` | `TIMESTAMPTZ` | | Link click timestamp |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `id`
- `INDEX` on `user_id` — user notification history
- `INDEX` on `session_id` — session notification history
- `INDEX` on `channel` — channel usage analysis
- `INDEX` on `status` — delivery monitoring
- `INDEX` on `created_at` — temporal dispatch analysis
- `INDEX` on `(status, created_at) WHERE status IN ('queued','failed')` — pending/failed notifications

### 1.14 `user_consent_log`

Records of user consent for various processing activities (GDPR/DPDP Act compliance).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | |
| `user_id` | `UUID` | `FK → users.id NOT NULL` | |
| `consent_type` | `VARCHAR(50)` | `NOT NULL` | data_retention/ai_processing/marketing/third_party_share/pan_verification/aadhaar_verification/training_data_use |
| `granted` | `BOOLEAN` | `NOT NULL` | true = granted, false = revoked |
| `ip_address` | `INET` | | IP at time of consent |
| `user_agent` | `TEXT` | | User-Agent at time of consent |
| `consent_version` | `VARCHAR(10)` | `NOT NULL` | Version of consent form shown |
| `revoked_at` | `TIMESTAMPTZ` | | When consent was revoked |
| `expires_at` | `TIMESTAMPTZ` | | Consent expiry (if applicable) |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `id`
- `INDEX` on `user_id` — all consents for a user
- `INDEX` on `(user_id, consent_type)` — specific consent lookup
- `INDEX` on `consent_type` — consent type analysis

### 1.15 `rule_definitions`

Registry of all validation rules. Loaded into the Validation Engine at startup and refreshed periodically.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `rule_id` | `VARCHAR(20)` | `PK` | Unique rule code (e.g., "V001") |
| `rule_name` | `VARCHAR(200)` | `NOT NULL` | Human-readable name |
| `category` | `VARCHAR(50)` | `NOT NULL` | See validation_results categories |
| `severity` | `VARCHAR(10)` | `NOT NULL` | error/warning/info |
| `engine_type` | `VARCHAR(20)` | `NOT NULL` | json_logic/custom_function/sql_query |
| `condition_expression` | `JSONB` | `NOT NULL` | Rule condition in specified engine format |
| `message_template_en` | `VARCHAR(500)` | `NOT NULL` | English message with {placeholders} |
| `message_template_hi` | `VARCHAR(500)` | | Hindi translation |
| `resolution_hint` | `TEXT` | | How to resolve this validation failure |
| `resolution_action` | `VARCHAR(50)` | | user_correction/re_upload/ignore/re_ocr |
| `enabled` | `BOOLEAN` | `DEFAULT true` | Is rule active? |
| `applicable_itr_types` | `VARCHAR(50)[]` | | Which ITR types this applies to |
| `applicable_regimes` | `VARCHAR(10)[]` | | Which regimes this applies to (new/old/both) |
| `effective_from_ay` | `VARCHAR(7)` | | First AY this rule applies |
| `effective_to_ay` | `VARCHAR(7)` | | Last AY this rule applies |
| `dependencies` | `VARCHAR(20)[]` | | Rules that must pass before this one runs |
| `version` | `INTEGER` | `DEFAULT 1` | Rule version |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `rule_id`
- `INDEX` on `category` — rule category queries
- `INDEX` on `enabled WHERE enabled = true` — active rules only
- `INDEX` on `applicable_itr_types USING GIN` — ITR type filter
- `INDEX` on `effective_from_ay` — versioning queries

### 1.16 `prompt_templates`

Version-controlled LLM prompt templates. Stored as rows for easy A/B testing and hot-reload.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `VARCHAR(100)` | `PK` | Template ID (e.g., "entity_extraction/v3") |
| `name` | `VARCHAR(200)` | `NOT NULL` | Human-readable name |
| `use_case` | `VARCHAR(50)` | `NOT NULL` | document_classification/entity_extraction/question_generation/tax_guidance/deduction_optimization/general_chat |
| `template_text` | `TEXT` | `NOT NULL` | Prompt template with {placeholder} variables |
| `model` | `VARCHAR(50)` | `NOT NULL` | Target LLM model |
| `max_tokens` | `INTEGER` | `NOT NULL` | Max output tokens |
| `temperature` | `NUMERIC(3,2)` | `NOT NULL DEFAULT 0.1` | LLM temperature |
| `version` | `INTEGER` | `NOT NULL` | Monotonically increasing |
| `is_active` | `BOOLEAN` | `DEFAULT false` | Currently active version |
| `ab_test_pct` | `SMALLINT` | `DEFAULT 0` | Percentage of traffic for A/B test (0-100) |
| `metadata` | `JSONB` | | Version notes, author, change reason |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `id`
- `INDEX` on `use_case` — filter by use case
- `INDEX` on `is_active WHERE is_active = true` — active templates

### 1.17 `entity_type_master`

Master list of all entity types that can be extracted and mapped to ITR schemas.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `entity_type` | `VARCHAR(50)` | `PK` | Entity type code |
| `label` | `VARCHAR(200)` | `NOT NULL` | Display label |
| `data_type` | `VARCHAR(20)` | `NOT NULL` | string/numeric/date/boolean/percentage |
| `category` | `VARCHAR(30)` | `NOT NULL` | income/deduction/tax/personal/bank/asset |
| `itr_path_template` | `VARCHAR(200)` | | Template for JSON path in ITR schema |
| `validation_rules` | `JSONB` | | Client-side validation rules |
| `min_value` | `NUMERIC(18,2)` | | Minimum allowed value (if numeric) |
| `max_value` | `NUMERIC(18,2)` | | Maximum allowed value (if numeric) |
| `regex_validation` | `VARCHAR(200)` | | Regex pattern for string validation |
| `examples` | `JSONB` | | Example values for LLM in-context learning |
| `is_active` | `BOOLEAN` | `DEFAULT true` | |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `entity_type`
- `INDEX` on `category` — category queries

### 1.18 `document_type_master`

Master list of supported document types with classification hints.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `document_type` | `VARCHAR(50)` | `PK` | Document type code |
| `label` | `VARCHAR(200)` | `NOT NULL` | Display label |
| `expected_entities` | `VARCHAR(50)[]` | | Entity types expected in this document |
| `classifier_keywords` | `TEXT[]` | | Keywords for rule-based classification fallback |
| `priority` | `VARCHAR(5)` | `DEFAULT 'P2'` | P0/P1/P2 processing priority |
| `max_pages` | `SMALLINT` | | Maximum expected pages |
| `is_active` | `BOOLEAN` | `DEFAULT true` | |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

### 1.19 `admin_users`

Internal admin accounts for TaxStox operations team.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PK DEFAULT gen_random_uuid()` | |
| `email` | `VARCHAR(255)` | `UNIQUE NOT NULL` | Admin email |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | bcrypt hash |
| `name` | `VARCHAR(200)` | `NOT NULL` | Full name |
| `role` | `VARCHAR(20)` | `NOT NULL DEFAULT 'support'` | super_admin/admin/support/analytics |
| `permissions` | `TEXT[]` | | Fine-grained permissions list |
| `mfa_secret` | `VARCHAR(32)` | | TOTP secret for MFA |
| `mfa_enabled` | `BOOLEAN` | `DEFAULT false` | |
| `last_login_at` | `TIMESTAMPTZ` | | |
| `is_active` | `BOOLEAN` | `DEFAULT true` | |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

**Indexes:**
- `PK` on `id`
- `UNIQUE` on `email`
- `INDEX` on `role` — role-based queries

**Check Constraints:**
- `CHECK (role IN ('super_admin','admin','support','analytics'))`

### 1.20 `data_purge_log`

Audit trail for automated data purging operations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `BIGSERIAL` | `PK` | |
| `purge_job_name` | `VARCHAR(100)` | `NOT NULL` | e.g., "purge_expired_documents", "anonymize_old_data" |
| `affected_table` | `VARCHAR(50)` | `NOT NULL` | Table affected |
| `records_purged` | `INTEGER` | `NOT NULL` | Number of records |
| `purge_criteria` | `JSONB` | | Criteria used |
| `total_size_freed_bytes` | `BIGINT` | | Storage freed |
| `s3_objects_deleted` | `INTEGER` | | S3 objects deleted |
| `s3_size_freed_bytes` | `BIGINT` | | S3 storage freed |
| `status` | `VARCHAR(20)` | `NOT NULL` | success/partial/failed |
| `error_details` | `TEXT` | | If failed |
| `started_at` | `TIMESTAMPTZ` | `NOT NULL` | |
| `completed_at` | `TIMESTAMPTZ` | | |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | |

---

## 2. Complete DDL

```sql
-- ============================================================================
-- TaxStox Database Schema
-- PostgreSQL 16
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;        -- gen_random_uuid(), encrypt/decrypt
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";     -- UUID generation
CREATE EXTENSION IF NOT EXISTS btree_gin;       -- GIN index on scalar types
CREATE EXTENSION IF NOT EXISTS pg_stat_statements; -- Query performance monitoring

-- ============================================================================
-- 1.1 users
-- ============================================================================
CREATE TABLE users (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    pan_hash            VARCHAR(64) NOT NULL,
    pan_salt            VARCHAR(32) NOT NULL,
    pan_last_four       VARCHAR(4)  NOT NULL,
    email_hash          VARCHAR(64) NOT NULL,
    email_encrypted     BYTEA,
    phone_hash          VARCHAR(64) NOT NULL,
    phone_encrypted     BYTEA,
    phone_country_code  VARCHAR(5)  DEFAULT '+91',
    name_encrypted      BYTEA,
    name_hash           VARCHAR(64),
    dob_encrypted       BYTEA,
    dob_hash            VARCHAR(64),
    pan_verified_at     TIMESTAMPTZ,
    pan_verification_ref VARCHAR(64),
    aadhaar_hash        VARCHAR(64),
    aadhaar_last_four   VARCHAR(4),
    aadhaar_verified_at TIMESTAMPTZ,
    preferred_language  VARCHAR(10) DEFAULT 'en',
    preferred_regime    VARCHAR(10) DEFAULT 'new',
    is_active           BOOLEAN     DEFAULT true,
    is_onboarded        BOOLEAN     DEFAULT false,
    onboarding_step     VARCHAR(50) DEFAULT 'created',
    last_login_at       TIMESTAMPTZ,
    failed_login_attempts INTEGER   DEFAULT 0,
    locked_until        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    anonymized_at       TIMESTAMPTZ,

    CONSTRAINT uq_users_pan_hash UNIQUE (pan_hash),
    CONSTRAINT uq_users_email_hash UNIQUE (email_hash),
    CONSTRAINT uq_users_phone_hash UNIQUE (phone_hash),
    CONSTRAINT chk_users_preferred_language CHECK (preferred_language IN ('en','hi','ta','te','bn','gu','mr')),
    CONSTRAINT chk_users_preferred_regime CHECK (preferred_regime IN ('new','old')),
    CONSTRAINT chk_users_onboarding_step CHECK (onboarding_step IN (
        'created','pan_verified','aadhaar_verified','profile_completed','onboarded'
    ))
);

CREATE INDEX idx_users_created_at ON users (created_at);
CREATE INDEX idx_users_last_login_at ON users (last_login_at);
CREATE INDEX idx_users_active ON users (is_active) WHERE is_active = true;

COMMENT ON TABLE users IS 'Core user identity. PAN and PII stored as hashes/encrypted.';

-- ============================================================================
-- 1.2 taxpayer_profiles
-- ============================================================================
CREATE TABLE taxpayer_profiles (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pan_hash            VARCHAR(64) NOT NULL,
    assessment_years    TEXT[]      NOT NULL DEFAULT '{}',
    current_ay          VARCHAR(7),
    occupation_type     VARCHAR(50),
    employer_category   VARCHAR(50),
    has_multiple_employers BOOLEAN  DEFAULT false,
    has_business_income BOOLEAN     DEFAULT false,
    has_capital_gains   BOOLEAN     DEFAULT false,
    has_house_property  BOOLEAN     DEFAULT false,
    has_foreign_assets  BOOLEAN     DEFAULT false,
    has_agriculture_income BOOLEAN  DEFAULT false,
    regime_preference   VARCHAR(10),
    filing_category     VARCHAR(10),
    profile_data        JSONB       NOT NULL DEFAULT '{}',
    consent_flags       JSONB       DEFAULT '{}',
    risk_profile        VARCHAR(20) DEFAULT 'low',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_taxpayer_profiles_user UNIQUE (user_id),
    CONSTRAINT chk_taxpayer_profiles_occupation CHECK (occupation_type IN ('salaried','business','profession','retired','other')),
    CONSTRAINT chk_taxpayer_profiles_regime CHECK (regime_preference IN ('new','old','undecided')),
    CONSTRAINT chk_taxpayer_profiles_filing_category CHECK (filing_category IN ('individual','huf','firm','company','other')),
    CONSTRAINT chk_taxpayer_profiles_risk CHECK (risk_profile IN ('low','medium','high'))
);

CREATE INDEX idx_taxpayer_profiles_pan_hash ON taxpayer_profiles (pan_hash);
CREATE INDEX idx_taxpayer_profiles_ay ON taxpayer_profiles USING GIN (assessment_years);
CREATE INDEX idx_taxpayer_profiles_regime ON taxpayer_profiles (regime_preference);
CREATE INDEX idx_taxpayer_profiles_filing_category ON taxpayer_profiles (filing_category);

COMMENT ON TABLE taxpayer_profiles IS 'Extended taxpayer data per user. One row per user (current view).';

-- ============================================================================
-- 1.3 filing_sessions
-- ============================================================================
CREATE TABLE filing_sessions (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ay                  VARCHAR(7)  NOT NULL,
    itr_type            VARCHAR(10),
    status              VARCHAR(20) NOT NULL DEFAULT 'initiated',
    regime              VARCHAR(10),
    current_step        VARCHAR(50),
    current_step_data   JSONB,
    progress_pct        SMALLINT    DEFAULT 0,
    last_ai_context     TEXT,
    llm_calls_count     INTEGER     DEFAULT 0,
    llm_total_cost_inr  NUMERIC(10,2) DEFAULT 0,
    error_details       JSONB,
    is_test_data        BOOLEAN     DEFAULT false,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    filed_at            TIMESTAMPTZ,
    abandoned_at        TIMESTAMPTZ,
    last_activity_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_filing_sessions_status CHECK (status IN (
        'initiated','documents_uploading','documents_processing','entities_review',
        'computing','regime_selection','review_itr','generated','filed','abandoned','error'
    )),
    CONSTRAINT chk_filing_sessions_regime CHECK (regime IN ('new','old')),
    CONSTRAINT chk_filing_sessions_itr_type CHECK (itr_type IN ('ITR-1','ITR-2','ITR-3','ITR-4','ITR-5','ITR-6')),
    CONSTRAINT chk_filing_sessions_progress CHECK (progress_pct >= 0 AND progress_pct <= 100)
);

CREATE INDEX idx_filing_sessions_user_id ON filing_sessions (user_id);
CREATE INDEX idx_filing_sessions_user_ay ON filing_sessions (user_id, ay);
CREATE INDEX idx_filing_sessions_status ON filing_sessions (status);
CREATE INDEX idx_filing_sessions_created_at ON filing_sessions (created_at);
CREATE INDEX idx_filing_sessions_itr_type ON filing_sessions (itr_type);
CREATE INDEX idx_filing_sessions_last_activity ON filing_sessions (last_activity_at);
CREATE INDEX idx_filing_sessions_status_last_activity ON filing_sessions (status, last_activity_at);
CREATE INDEX idx_filing_sessions_llm_cost ON filing_sessions (llm_total_cost_inr);
CREATE INDEX idx_filing_sessions_completed ON filing_sessions (completed_at) WHERE completed_at IS NOT NULL;

COMMENT ON TABLE filing_sessions IS 'One tax filing session per user per assessment year attempt.';

-- ============================================================================
-- 1.4 documents
-- ============================================================================
CREATE TABLE documents (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id              UUID        NOT NULL REFERENCES filing_sessions(id) ON DELETE CASCADE,
    user_id                 UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_type           VARCHAR(50),
    original_filename       VARCHAR(255) NOT NULL,
    sanitized_filename      VARCHAR(255),
    file_size_bytes         INTEGER     NOT NULL,
    mime_type               VARCHAR(100) NOT NULL,
    s3_bucket               VARCHAR(100),
    s3_key                  VARCHAR(500),
    s3_etag                 VARCHAR(64),
    s3_version_id           VARCHAR(100),
    encryption_key_id       VARCHAR(100),
    page_count              SMALLINT,
    file_hash_sha256        VARCHAR(64),
    classification_method   VARCHAR(20),
    classification_confidence NUMERIC(4,3),
    classification_metadata JSONB,
    virus_scan_status       VARCHAR(20) DEFAULT 'pending',
    virus_scan_result       VARCHAR(255),
    virus_scanned_at        TIMESTAMPTZ,
    ocr_status              VARCHAR(20) DEFAULT 'pending',
    ocr_engine              VARCHAR(50),
    ocr_confidence          NUMERIC(4,3),
    ocr_completed_at        TIMESTAMPTZ,
    ocr_failure_reason      TEXT,
    ocr_retry_count         SMALLINT    DEFAULT 0,
    parsed_at               TIMESTAMPTZ,
    purge_at                TIMESTAMPTZ,
    purged_at               TIMESTAMPTZ,
    is_deleted              BOOLEAN     DEFAULT false,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_documents_size CHECK (file_size_bytes > 0 AND file_size_bytes <= 20971520),
    CONSTRAINT chk_documents_mime CHECK (mime_type IN ('application/pdf','image/jpeg','image/png','image/tiff')),
    CONSTRAINT chk_documents_virus_scan CHECK (virus_scan_status IN ('pending','scanned','clean','infected','error')),
    CONSTRAINT chk_documents_ocr_status CHECK (ocr_status IN ('pending','processing','completed','failed')),
    CONSTRAINT chk_documents_classification_method CHECK (classification_method IN ('ai','rule_based','manual'))
);

CREATE INDEX idx_documents_session_id ON documents (session_id);
CREATE INDEX idx_documents_user_id ON documents (user_id);
CREATE INDEX idx_documents_document_type ON documents (document_type);
CREATE INDEX idx_documents_ocr_status ON documents (ocr_status);
CREATE INDEX idx_documents_file_hash ON documents (file_hash_sha256);
CREATE INDEX idx_documents_purge_at ON documents (purge_at);
CREATE INDEX idx_documents_created_at ON documents (created_at);
CREATE INDEX idx_documents_pending_ocr ON documents (session_id) WHERE ocr_status = 'pending';

COMMENT ON TABLE documents IS 'Uploaded document metadata. Files stored in S3 with 24h TTL.';

-- ============================================================================
-- 1.5 extracted_entities
-- ============================================================================
CREATE TABLE extracted_entities (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id              UUID        NOT NULL REFERENCES filing_sessions(id) ON DELETE CASCADE,
    user_id                 UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_document_id      UUID        REFERENCES documents(id) ON DELETE SET NULL,
    entity_type             VARCHAR(50) NOT NULL,
    entity_path             VARCHAR(200),
    entity_label            VARCHAR(200),
    raw_value               TEXT        NOT NULL,
    normalized_value        TEXT,
    numeric_value           NUMERIC(18,2),
    currency                VARCHAR(3)  DEFAULT 'INR',
    unit                    VARCHAR(20),
    confidence              NUMERIC(4,3) NOT NULL,
    is_user_verified        BOOLEAN     DEFAULT false,
    verified_by_user_at     TIMESTAMPTZ,
    user_corrected_value    TEXT,
    user_correction_reason  VARCHAR(100),
    conflict_group          VARCHAR(100),
    is_selected_in_conflict BOOLEAN     DEFAULT true,
    extraction_method       VARCHAR(20) NOT NULL,
    extraction_metadata     JSONB,
    is_active               BOOLEAN     DEFAULT true,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_entities_extraction_method CHECK (extraction_method IN (
        'ocr_ner','llm_extraction','manual_entry','rule_based'
    )),
    CONSTRAINT chk_entities_user_correction_reason CHECK (user_correction_reason IN (
        'ocr_error','wrong_field','missing_doc'
    )),
    CONSTRAINT chk_entities_confidence CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE INDEX idx_entities_session_id ON extracted_entities (session_id);
CREATE INDEX idx_entities_source_doc ON extracted_entities (source_document_id);
CREATE INDEX idx_entities_user_id ON extracted_entities (user_id);
CREATE INDEX idx_entities_entity_type ON extracted_entities (entity_type);
CREATE INDEX idx_entities_session_type ON extracted_entities (session_id, entity_type);
CREATE INDEX idx_entities_entity_path ON extracted_entities (entity_path);
CREATE INDEX idx_entities_verified ON extracted_entities (session_id, is_user_verified);
CREATE INDEX idx_entities_conflict ON extracted_entities (conflict_group);
CREATE INDEX idx_entities_active_path ON extracted_entities (session_id, entity_path, is_active);
CREATE INDEX idx_entities_confidence ON extracted_entities (confidence);
CREATE INDEX idx_entities_unverified_active ON extracted_entities (session_id)
    WHERE is_user_verified = false AND is_active = true;

COMMENT ON TABLE extracted_entities IS 'Extracted financial entities from documents and user input.';

-- ============================================================================
-- 1.6 validation_results
-- ============================================================================
CREATE TABLE validation_results (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID          NOT NULL REFERENCES filing_sessions(id) ON DELETE CASCADE,
    rule_id             VARCHAR(20)   NOT NULL,
    rule_name           VARCHAR(200),
    rule_category       VARCHAR(50),
    severity            VARCHAR(10)   NOT NULL,
    status              VARCHAR(20)   NOT NULL DEFAULT 'active',
    entity_a_id         UUID          REFERENCES extracted_entities(id) ON DELETE SET NULL,
    entity_b_id         UUID          REFERENCES extracted_entities(id) ON DELETE SET NULL,
    expected_value      TEXT,
    actual_value        TEXT,
    difference          NUMERIC(18,2),
    message_template    VARCHAR(500),
    message_params      JSONB,
    resolution_hint     TEXT,
    resolution_action   VARCHAR(50),
    overridden_by_user  BOOLEAN       DEFAULT false,
    override_reason     TEXT,
    overridden_at       TIMESTAMPTZ,
    evaluation_context  JSONB,
    evaluation_duration_ms INTEGER,
    evaluated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_validations_severity CHECK (severity IN ('error','warning','info')),
    CONSTRAINT chk_validations_status CHECK (status IN ('active','overridden','resolved','waived')),
    CONSTRAINT chk_validations_category CHECK (rule_category IN (
        'schema','cross_field','cross_document','threshold','regime',
        'data_integrity','math','temporal','compliance'
    )),
    CONSTRAINT chk_validations_resolution_action CHECK (resolution_action IN (
        'user_correction','re_upload','ignore','re_ocr'
    ))
);

CREATE INDEX idx_validations_session_id ON validation_results (session_id);
CREATE INDEX idx_validations_rule_id ON validation_results (rule_id);
CREATE INDEX idx_validations_session_severity ON validation_results (session_id, severity);
CREATE INDEX idx_validations_session_status ON validation_results (session_id, status);
CREATE INDEX idx_validations_rule_category ON validation_results (rule_category);
CREATE INDEX idx_validations_entity_a ON validation_results (entity_a_id);
CREATE INDEX idx_validations_evaluated_at ON validation_results (evaluated_at);
CREATE INDEX idx_validations_blocking ON validation_results (session_id)
    WHERE status = 'active' AND severity = 'error';

COMMENT ON TABLE validation_results IS 'Results per validation rule per session.';

-- ============================================================================
-- 1.7 tax_computations
-- ============================================================================
CREATE TABLE tax_computations (
    id                      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id              UUID          NOT NULL REFERENCES filing_sessions(id) ON DELETE CASCADE,
    user_id                 UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    regime                  VARCHAR(10)   NOT NULL,
    ay                      VARCHAR(7)    NOT NULL,
    computation_version     VARCHAR(20)   NOT NULL,
    computation_json        JSONB         NOT NULL,
    entity_snapshot_hash    VARCHAR(64),
    validation_snapshot_hash VARCHAR(64),
    is_final                BOOLEAN       DEFAULT false,
    triggered_by            VARCHAR(20),
    computation_duration_ms INTEGER,
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_computations_regime CHECK (regime IN ('new','old')),
    CONSTRAINT chk_computations_triggered_by CHECK (triggered_by IN (
        'auto','user_request','entity_update','regime_change'
    ))
);

CREATE INDEX idx_computations_session_id ON tax_computations (session_id);
CREATE INDEX idx_computations_user_id ON tax_computations (user_id);
CREATE INDEX idx_computations_session_final ON tax_computations (session_id, is_final) WHERE is_final = true;
CREATE INDEX idx_computations_session_regime ON tax_computations (session_id, regime);
CREATE INDEX idx_computations_created_at ON tax_computations (created_at);

COMMENT ON TABLE tax_computations IS 'Immutable tax computation records. NEVER generated by AI.';

-- ============================================================================
-- 1.8 deductions_claimed
-- ============================================================================
CREATE TABLE deductions_claimed (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    tax_computation_id  UUID          NOT NULL REFERENCES tax_computations(id) ON DELETE CASCADE,
    session_id          UUID          NOT NULL REFERENCES filing_sessions(id) ON DELETE CASCADE,
    section             VARCHAR(10)   NOT NULL,
    subsection          VARCHAR(20),
    description         VARCHAR(255),
    amount              NUMERIC(18,2) NOT NULL,
    max_allowed         NUMERIC(18,2),
    is_capped           BOOLEAN       DEFAULT false,
    capped_amount       NUMERIC(18,2),
    source_entity_id    UUID          REFERENCES extracted_entities(id) ON DELETE SET NULL,
    evidence_document_id UUID         REFERENCES documents(id) ON DELETE SET NULL,
    is_user_confirmed   BOOLEAN       DEFAULT false,
    is_ai_suggested     BOOLEAN       DEFAULT false,
    optimization_note   TEXT,
    regime_applicable   VARCHAR(10),
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_deductions_amount CHECK (amount >= 0),
    CONSTRAINT chk_deductions_regime CHECK (regime_applicable IN ('new','old','both'))
);

CREATE INDEX idx_deductions_computation_id ON deductions_claimed (tax_computation_id);
CREATE INDEX idx_deductions_session_id ON deductions_claimed (session_id);
CREATE INDEX idx_deductions_section ON deductions_claimed (section);
CREATE INDEX idx_deductions_computation_section ON deductions_claimed (tax_computation_id, section);

COMMENT ON TABLE deductions_claimed IS 'Line-item deductions per computation. Links to source entity and evidence.';

-- ============================================================================
-- 1.9 itr_jsons
-- ============================================================================
CREATE TABLE itr_jsons (
    id                      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id              UUID          NOT NULL REFERENCES filing_sessions(id) ON DELETE CASCADE,
    user_id                 UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    itr_type                VARCHAR(10)   NOT NULL,
    ay                      VARCHAR(7)    NOT NULL,
    regime                  VARCHAR(10)   NOT NULL,
    schema_version          VARCHAR(10)   NOT NULL,
    json_content_hash       VARCHAR(64)   NOT NULL,
    xml_content_hash        VARCHAR(64),
    s3_bucket_final         VARCHAR(100),
    s3_key_final            VARCHAR(500),
    s3_bucket_xml           VARCHAR(100),
    s3_key_xml              VARCHAR(500),
    s3_bucket_user_copy     VARCHAR(100),
    s3_key_user_copy        VARCHAR(500),
    file_size_bytes         INTEGER,
    is_filed                BOOLEAN       DEFAULT false,
    filing_ack_number       VARCHAR(50),
    filing_transaction_id   VARCHAR(100),
    filed_at                TIMESTAMPTZ,
    filing_mode             VARCHAR(20),
    generated_at            TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    purge_at                TIMESTAMPTZ,
    purged_at               TIMESTAMPTZ,
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_itr_type CHECK (itr_type IN ('ITR-1','ITR-2','ITR-3','ITR-4','ITR-5','ITR-6')),
    CONSTRAINT chk_itr_regime CHECK (regime IN ('new','old')),
    CONSTRAINT chk_itr_filing_mode CHECK (filing_mode IN ('online','offline'))
);

CREATE INDEX idx_itr_session_id ON itr_jsons (session_id);
CREATE INDEX idx_itr_user_id ON itr_jsons (user_id);
CREATE INDEX idx_itr_user_ay ON itr_jsons (user_id, ay);
CREATE INDEX idx_itr_json_hash ON itr_jsons (json_content_hash);
CREATE INDEX idx_itr_is_filed ON itr_jsons (is_filed);
CREATE INDEX idx_itr_purge_at ON itr_jsons (purge_at);

COMMENT ON TABLE itr_jsons IS 'Generated ITR JSON/XML files. S3 for content, metadata in PG.';

-- ============================================================================
-- 1.10 audit_log
-- ============================================================================
CREATE TABLE audit_log (
    id              BIGSERIAL     PRIMARY KEY,
    event_id        UUID          NOT NULL DEFAULT gen_random_uuid(),
    session_id      UUID          REFERENCES filing_sessions(id) ON DELETE SET NULL,
    user_id         UUID          REFERENCES users(id) ON DELETE SET NULL,
    actor_type      VARCHAR(20)   NOT NULL,
    actor_id        VARCHAR(100)  NOT NULL,
    event_type      VARCHAR(50)   NOT NULL,
    event_category  VARCHAR(30)   NOT NULL,
    severity        VARCHAR(10)   DEFAULT 'info',
    resource_type   VARCHAR(50),
    resource_id     UUID,
    details_json    JSONB         NOT NULL DEFAULT '{}',
    ip_address      INET,
    user_agent      TEXT,
    trace_id        VARCHAR(32),
    span_id         VARCHAR(16),
    prev_entry_hash VARCHAR(64),
    data_hash       VARCHAR(64)   NOT NULL,
    entry_hash      VARCHAR(64)   NOT NULL,
    nonce           VARCHAR(16)   NOT NULL,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_audit_event_id UNIQUE (event_id),
    CONSTRAINT chk_audit_actor_type CHECK (actor_type IN ('user','system','admin','ai')),
    CONSTRAINT chk_audit_category CHECK (event_category IN (
        'auth','document','entity','validation','tax','itr','session','admin'
    )),
    CONSTRAINT chk_audit_severity CHECK (severity IN ('info','warning','error','critical'))
);

CREATE INDEX idx_audit_session_id ON audit_log (session_id);
CREATE INDEX idx_audit_user_id ON audit_log (user_id);
CREATE INDEX idx_audit_event_type ON audit_log (event_type);
CREATE INDEX idx_audit_event_category ON audit_log (event_category);
CREATE INDEX idx_audit_created_at ON audit_log (created_at);
CREATE INDEX idx_audit_actor_id ON audit_log (actor_id);
CREATE INDEX idx_audit_resource ON audit_log (resource_type, resource_id);
CREATE INDEX idx_audit_time_brin ON audit_log USING BRIN (created_at, id) WITH (pages_per_range = 32);

COMMENT ON TABLE audit_log IS 'Tamper-evident audit trail with SHA-256 hash chain.';

-- ============================================================================
-- 1.11 conversation_turns
-- ============================================================================
CREATE TABLE conversation_turns (
    id                  BIGSERIAL     PRIMARY KEY,
    session_id          UUID          NOT NULL REFERENCES filing_sessions(id) ON DELETE CASCADE,
    turn_number         SMALLINT      NOT NULL,
    role                VARCHAR(10)   NOT NULL,
    message_type        VARCHAR(30)   NOT NULL,
    content             TEXT          NOT NULL,
    pii_masked_content  TEXT,
    metadata_json       JSONB         DEFAULT '{}',
    tokens_input        INTEGER,
    tokens_output       INTEGER,
    llm_latency_ms      INTEGER,
    llm_model           VARCHAR(50),
    llm_cost_inr        NUMERIC(10,2),
    prompt_template_used VARCHAR(100),
    user_rating         SMALLINT,
    user_rating_comment TEXT,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_turns_role CHECK (role IN ('user','assistant','system')),
    CONSTRAINT chk_turns_message_type CHECK (message_type IN (
        'question','answer','clarification','confirmation','error',
        'system_prompt','computation_result','greeting','farewell'
    )),
    CONSTRAINT chk_turns_rating CHECK (
        (user_rating >= 1 AND user_rating <= 5) OR user_rating IS NULL
    )
);

CREATE INDEX idx_turns_session_id ON conversation_turns (session_id);
CREATE INDEX idx_turns_session_turn ON conversation_turns (session_id, turn_number);
CREATE INDEX idx_turns_role ON conversation_turns (role);
CREATE INDEX idx_turns_message_type ON conversation_turns (message_type);
CREATE INDEX idx_turns_rated ON conversation_turns (user_rating) WHERE user_rating IS NOT NULL;
CREATE INDEX idx_turns_created_at ON conversation_turns (created_at);

COMMENT ON TABLE conversation_turns IS 'Conversation turns between user and TaxStox AI assistant.';

-- ============================================================================
-- 1.12 recommendations
-- ============================================================================
CREATE TABLE recommendations (
    id                      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id              UUID          NOT NULL REFERENCES filing_sessions(id) ON DELETE CASCADE,
    user_id                 UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recommendation_type     VARCHAR(50)   NOT NULL,
    title                   VARCHAR(200)  NOT NULL,
    description             TEXT,
    details_json            JSONB         NOT NULL DEFAULT '{}',
    potential_benefit_amount NUMERIC(18,2),
    confidence              NUMERIC(4,3),
    user_accepted           BOOLEAN,
    user_accepted_at        TIMESTAMPTZ,
    user_rejected_reason    VARCHAR(100),
    applied_automatically   BOOLEAN       DEFAULT false,
    expires_at              TIMESTAMPTZ,
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_recommendations_type CHECK (recommendation_type IN (
        'regime_selection','deduction_optimization','itr_selection',
        'document_suggestion','filing_reminder','error_resolution'
    ))
);

CREATE INDEX idx_recommendations_session_id ON recommendations (session_id);
CREATE INDEX idx_recommendations_user_id ON recommendations (user_id);
CREATE INDEX idx_recommendations_type ON recommendations (recommendation_type);
CREATE INDEX idx_recommendations_session_type ON recommendations (session_id, recommendation_type);
CREATE INDEX idx_recommendations_accepted ON recommendations (user_accepted);

COMMENT ON TABLE recommendations IS 'AI-generated recommendations for tax optimization and guidance.';

-- ============================================================================
-- 1.13 notification_log
-- ============================================================================
CREATE TABLE notification_log (
    id                  BIGSERIAL     PRIMARY KEY,
    user_id             UUID          REFERENCES users(id) ON DELETE SET NULL,
    session_id          UUID          REFERENCES filing_sessions(id) ON DELETE SET NULL,
    channel             VARCHAR(10)   NOT NULL,
    template_name       VARCHAR(100)  NOT NULL,
    recipient           VARCHAR(255)  NOT NULL,
    subject             VARCHAR(500),
    status              VARCHAR(20)   NOT NULL DEFAULT 'queued',
    provider_message_id VARCHAR(255),
    provider_response   JSONB,
    delivery_attempts   SMALLINT      DEFAULT 0,
    last_attempt_at     TIMESTAMPTZ,
    delivered_at        TIMESTAMPTZ,
    bounce_reason       TEXT,
    opened_at           TIMESTAMPTZ,
    clicked_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_notification_channel CHECK (channel IN ('email','sms','push')),
    CONSTRAINT chk_notification_status CHECK (status IN (
        'queued','sent','delivered','bounced','failed','clicked'
    ))
);

CREATE INDEX idx_notification_user_id ON notification_log (user_id);
CREATE INDEX idx_notification_session_id ON notification_log (session_id);
CREATE INDEX idx_notification_channel ON notification_log (channel);
CREATE INDEX idx_notification_status ON notification_log (status);
CREATE INDEX idx_notification_created_at ON notification_log (created_at);
CREATE INDEX idx_notification_pending ON notification_log (status, created_at)
    WHERE status IN ('queued','failed');

COMMENT ON TABLE notification_log IS 'Dispatched notification tracking and delivery audit.';

-- ============================================================================
-- 1.14 user_consent_log
-- ============================================================================
CREATE TABLE user_consent_log (
    id              BIGSERIAL     PRIMARY KEY,
    user_id         UUID          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type    VARCHAR(50)   NOT NULL,
    granted         BOOLEAN       NOT NULL,
    ip_address      INET,
    user_agent      TEXT,
    consent_version VARCHAR(10)   NOT NULL,
    revoked_at      TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_consent_type CHECK (consent_type IN (
        'data_retention','ai_processing','marketing','third_party_share',
        'pan_verification','aadhaar_verification','training_data_use'
    ))
);

CREATE INDEX idx_consent_user_id ON user_consent_log (user_id);
CREATE INDEX idx_consent_user_type ON user_consent_log (user_id, consent_type);
CREATE INDEX idx_consent_type ON user_consent_log (consent_type);

COMMENT ON TABLE user_consent_log IS 'User consent records for GDPR/DPDP Act compliance.';

-- ============================================================================
-- 1.15 rule_definitions
-- ============================================================================
CREATE TABLE rule_definitions (
    rule_id               VARCHAR(20)   PRIMARY KEY,
    rule_name             VARCHAR(200)  NOT NULL,
    category              VARCHAR(50)   NOT NULL,
    severity              VARCHAR(10)   NOT NULL,
    engine_type           VARCHAR(20)   NOT NULL,
    condition_expression  JSONB         NOT NULL,
    message_template_en   VARCHAR(500)  NOT NULL,
    message_template_hi   VARCHAR(500),
    resolution_hint       TEXT,
    resolution_action     VARCHAR(50),
    enabled               BOOLEAN       DEFAULT true,
    applicable_itr_types  VARCHAR(10)[],
    applicable_regimes    VARCHAR(10)[],
    effective_from_ay     VARCHAR(7),
    effective_to_ay       VARCHAR(7),
    dependencies          VARCHAR(20)[],
    version               INTEGER       DEFAULT 1,
    created_at            TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_rules_severity CHECK (severity IN ('error','warning','info')),
    CONSTRAINT chk_rules_engine CHECK (engine_type IN ('json_logic','custom_function','sql_query')),
    CONSTRAINT chk_rules_category CHECK (category IN (
        'schema','cross_field','cross_document','threshold','regime',
        'data_integrity','math','temporal','compliance'
    ))
);

CREATE INDEX idx_rules_category ON rule_definitions (category);
CREATE INDEX idx_rules_enabled ON rule_definitions (enabled) WHERE enabled = true;
CREATE INDEX idx_rules_itr_types ON rule_definitions USING GIN (applicable_itr_types);
CREATE INDEX idx_rules_effective_from ON rule_definitions (effective_from_ay);

COMMENT ON TABLE rule_definitions IS 'Validation rule registry. Hot-reloadable by the Validation Engine.';

-- ============================================================================
-- 1.16 prompt_templates
-- ============================================================================
CREATE TABLE prompt_templates (
    id              VARCHAR(100)  PRIMARY KEY,
    name            VARCHAR(200)  NOT NULL,
    use_case        VARCHAR(50)   NOT NULL,
    template_text   TEXT          NOT NULL,
    model           VARCHAR(50)   NOT NULL,
    max_tokens      INTEGER       NOT NULL,
    temperature     NUMERIC(3,2)  NOT NULL DEFAULT 0.1,
    version         INTEGER       NOT NULL,
    is_active       BOOLEAN       DEFAULT false,
    ab_test_pct     SMALLINT      DEFAULT 0,
    metadata        JSONB,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_prompt_use_case CHECK (use_case IN (
        'document_classification','entity_extraction','question_generation',
        'tax_guidance','deduction_optimization','general_chat'
    ))
);

CREATE INDEX idx_prompt_use_case ON prompt_templates (use_case);
CREATE INDEX idx_prompt_active ON prompt_templates (is_active) WHERE is_active = true;

COMMENT ON TABLE prompt_templates IS 'Versioned LLM prompt templates. Supports A/B testing.';

-- ============================================================================
-- 1.17 entity_type_master
-- ============================================================================
CREATE TABLE entity_type_master (
    entity_type         VARCHAR(50)   PRIMARY KEY,
    label               VARCHAR(200)  NOT NULL,
    data_type           VARCHAR(20)   NOT NULL,
    category            VARCHAR(30)   NOT NULL,
    itr_path_template   VARCHAR(200),
    validation_rules    JSONB,
    min_value           NUMERIC(18,2),
    max_value           NUMERIC(18,2),
    regex_validation    VARCHAR(200),
    examples            JSONB,
    is_active           BOOLEAN       DEFAULT true,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_entity_data_type CHECK (data_type IN ('string','numeric','date','boolean','percentage')),
    CONSTRAINT chk_entity_category CHECK (category IN ('income','deduction','tax','personal','bank','asset'))
);

CREATE INDEX idx_entity_category ON entity_type_master (category);

COMMENT ON TABLE entity_type_master IS 'Master list of extractable entity types and their properties.';

-- ============================================================================
-- 1.18 document_type_master
-- ============================================================================
CREATE TABLE document_type_master (
    document_type       VARCHAR(50)   PRIMARY KEY,
    label               VARCHAR(200)  NOT NULL,
    expected_entities   VARCHAR(50)[],
    classifier_keywords TEXT[],
    priority            VARCHAR(5)    DEFAULT 'P2',
    max_pages           SMALLINT,
    is_active           BOOLEAN       DEFAULT true,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_doc_type_priority CHECK (priority IN ('P0','P1','P2'))
);

COMMENT ON TABLE document_type_master IS 'Supported document types with classification hints.';

-- ============================================================================
-- 1.19 admin_users
-- ============================================================================
CREATE TABLE admin_users (
    id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255)  NOT NULL,
    password_hash   VARCHAR(255)  NOT NULL,
    name            VARCHAR(200)  NOT NULL,
    role            VARCHAR(20)   NOT NULL DEFAULT 'support',
    permissions     TEXT[],
    mfa_secret      VARCHAR(32),
    mfa_enabled     BOOLEAN       DEFAULT false,
    last_login_at   TIMESTAMPTZ,
    is_active       BOOLEAN       DEFAULT true,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_admin_email UNIQUE (email),
    CONSTRAINT chk_admin_role CHECK (role IN ('super_admin','admin','support','analytics'))
);

CREATE INDEX idx_admin_role ON admin_users (role);

COMMENT ON TABLE admin_users IS 'Internal admin/staff accounts. Separate from end-user auth.';

-- ============================================================================
-- 1.20 data_purge_log
-- ============================================================================
CREATE TABLE data_purge_log (
    id                  BIGSERIAL     PRIMARY KEY,
    purge_job_name      VARCHAR(100)  NOT NULL,
    affected_table      VARCHAR(50)   NOT NULL,
    records_purged      INTEGER       NOT NULL,
    purge_criteria      JSONB,
    total_size_freed_bytes BIGINT,
    s3_objects_deleted  INTEGER,
    s3_size_freed_bytes BIGINT,
    status              VARCHAR(20)   NOT NULL,
    error_details       TEXT,
    started_at          TIMESTAMPTZ   NOT NULL,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_purge_status CHECK (status IN ('success','partial','failed'))
);

COMMENT ON TABLE data_purge_log IS 'Audit log for automated data purging operations.';

-- ============================================================================
-- Trigger: auto-update updated_at timestamp
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_taxpayer_profiles_updated_at
    BEFORE UPDATE ON taxpayer_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_filing_sessions_updated_at
    BEFORE UPDATE ON filing_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_extracted_entities_updated_at
    BEFORE UPDATE ON extracted_entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Row Level Security
-- ============================================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE taxpayer_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE filing_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_entities ENABLE ROW LEVEL SECURITY;

CREATE POLICY rls_users_isolation ON users
    FOR ALL
    USING (id = current_setting('app.current_user_id')::UUID);

CREATE POLICY rls_taxpayer_profiles_isolation ON taxpayer_profiles
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY rls_filing_sessions_isolation ON filing_sessions
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY rls_documents_isolation ON documents
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY rls_entities_isolation ON extracted_entities
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID);

-- Admin bypass
CREATE POLICY rls_admin_bypass ON users
    FOR ALL
    USING (current_setting('app.current_role') = 'admin');
```

---

## 3. Index Justification

### 3.1 B-Tree Indexes

| Index | Table | Column(s) | Justification |
|-------|-------|-----------|---------------|
| `idx_users_created_at` | users | `created_at` | Cohort analysis, registration rate monitoring. Range scan for "users registered this week". |
| `idx_users_last_login_at` | users | `last_login_at` | Active user identification for engagement metrics and abandoned account cleanup. |
| `idx_users_active` | users | `is_active` (partial) | 99% of queries only need active users. Partial index saves 90% size vs full column index. |
| `idx_filing_sessions_user_id` | filing_sessions | `user_id` | Foreign key lookup. Every session query starts with user. |
| `idx_filing_sessions_user_ay` | filing_sessions | `user_id, ay` | Composite covering index. "Show all sessions for this user in AY 2025-26" — covers WHERE + avoids table heap access. |
| `idx_filing_sessions_status` | filing_sessions | `status` | Dashboard aggregation "count sessions by status". Also status-monitoring queries. |
| `idx_filing_sessions_last_activity` | filing_sessions | `last_activity_at` | Stale session detection for reminder emails. |
| `idx_filing_sessions_status_last_activity` | filing_sessions | `status, last_activity_at` | Composite index for "find abandoned sessions" query: WHERE status = 'initiated' AND last_activity_at < NOW() - INTERVAL '7 days'. |
| `idx_filing_sessions_completed` | filing_sessions | `completed_at` (partial) | Only 30% of sessions complete; partial index for completion metrics. |
| `idx_documents_session_id` | documents | `session_id` | FK lookup. All document queries filtered by session. |
| `idx_documents_ocr_status` | documents | `ocr_status` | OCR worker pool picks pending documents: WHERE ocr_status = 'pending'. |
| `idx_documents_purge_at` | documents | `purge_at` | Purge scheduler: WHERE purge_at < NOW(). Critical for compliance. |
| `idx_entities_session_id` | extracted_entities | `session_id` | FK lookup. Primary access pattern: all entities in session. |
| `idx_entities_session_type` | extracted_entities | `session_id, entity_type` | Composite. "Find salary entity for this session" — covers the most common entity query. |
| `idx_entities_active_path` | extracted_entities | `session_id, entity_path, is_active` | Composite covering index for computation queries. Must be fast — called per computation. |
| `idx_entities_confidence` | extracted_entities | `confidence` | Identify low-confidence entities for user verification prompt. |
| `idx_entities_unverified_active` | extracted_entities | `session_id` (partial) | "Count unverified entities for progress tracking" — filtered index on frequently queried subset. |
| `idx_validations_session_id` | validation_results | `session_id` | FK lookup. All validations per session. |
| `idx_validations_session_severity` | validation_results | `session_id, severity` | "Count errors in this session" — progress bar and blocking status. |
| `idx_validations_blocking` | validation_results | `session_id` (partial) | "Are there blocking errors?" — partial index WHERE status='active' AND severity='error'. Critical path. |
| `idx_computations_session_final` | tax_computations | `session_id, is_final` (partial) | "Get the final computation" — the single most common computation query. |
| `idx_itr_user_ay` | itr_jsons | `user_id, ay` | "User's filing history by year". Composite covers the user+year filter used in dashboard. |
| `idx_audit_session_id` | audit_log | `session_id` | "Show audit trail for this session" — compliance officer query. |
| `idx_audit_resource` | audit_log | `resource_type, resource_id` | "What events happened to this specific document?" — incident investigation. |
| `idx_turns_session_turn` | conversation_turns | `session_id, turn_number` | Composite for ordered conversation replay. Turn_number is the sort key. |
| `idx_notification_pending` | notification_log | `status, created_at` (partial) | Notification worker picks pending jobs: WHERE status IN ('queued','failed'). |

### 3.2 GIN Indexes

| Index | Table | Column | Justification |
|-------|-------|--------|---------------|
| `idx_taxpayer_profiles_ay` | taxpayer_profiles | `assessment_years` (TEXT[]) | Query: "all users who filed in AY 2024-25". GIN supports array containment operators (`@>`). |
| `idx_rules_itr_types` | rule_definitions | `applicable_itr_types` (VARCHAR[]) | "Which rules apply to ITR-2?" — array overlap query. |

### 3.3 BRIN Indexes

| Index | Table | Column(s) | Justification |
|-------|-------|-----------|---------------|
| `idx_audit_time_brin` | audit_log | `(created_at, id)` | Audit log is append-only, 100M+ rows. BRIN index is 1% the size of B-Tree and excellent for time-range scans. `pages_per_range=32` balances accuracy vs size. |

### 3.4 Unique Constraints (enforced via unique index)

| Constraint | Table | Column(s) | Justification |
|------------|-------|-----------|---------------|
| `uq_users_pan_hash` | users | `pan_hash` | No duplicate PAN registrations. Critical for tax compliance — one PAN per user. |
| `uq_users_email_hash` | users | `email_hash` | One account per email for deduplication. |
| `uq_users_phone_hash` | users | `phone_hash` | One account per phone for OTP-based login. |
| `uq_taxpayer_profiles_user` | taxpayer_profiles | `user_id` | One current profile per user. |
| `uq_audit_event_id` | audit_log | `event_id` | Event ID must be globally unique for cross-system correlation. |
| `uq_admin_email` | admin_users | `email` | Admin login uniqueness. |

---

## 4. Redis Data Models

### 4.1 Connection Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Instance Type | c6g.large (2 vCPU, 4 GB RAM) | Cost-effective, ARM-based |
| Cluster | 3 primary + 3 replica | HA across AZs |
| Maxmemory | 4 GB | Sufficient for session + cache |
| Eviction Policy | `allkeys-lru` | Volatile keys with LRU eviction |
| Persistence | AOF with `appendfsync everysec` | Balance durability vs performance |

### 4.2 Key Patterns and TTL

#### Session State
```
Key:    session:{session_id}
Type:   HASH
Fields: user_id, status, current_step, progress_pct, turn_count,
        regime, itr_type, ay, compressed_context, last_activity
TTL:    86400 (24 hours from last write), refreshed on each turn
Size:   ~10 KB per active session
Purpose: Hot session state for Conversation Service. Avoids PG query per turn.

Example:
  HSET session:a1b2c3-d4e5 user_id "f6g7h8i9" status "entities_review" \
        current_step "verify_salary" progress_pct 45 turn_count 12 \
        regime "new" itr_type "ITR-1" ay "2025-26"

Read pattern (per conversation turn):
  HGETALL session:{session_id}
  → Update fields, refresh TTL
```

#### Computation Cache
```
Key:    computation:{regime}:{income_level}:{deduction_profile_hash}
Type:   STRING (JSON)
TTL:    604800 (7 days — tax slabs don't change mid-season)
Size:   ~2 KB per cached computation
Purpose: Cache tax results for identical income/deduction profiles across users
         or within same user's session (regime comparison).

Example:
  SET computation:old:10-15L:abc123def456 '{...computation_json...}' EX 604800

Read pattern:
  EXISTS computation:{regime}:{income_hash}:{deduction_hash}
  → Cache hit: return cached result (avoid recomputation)
  → Cache miss: compute, then SET with TTL

Invalidation: On slab rate changes (rare); or manual admin flush.
```

#### Rate Limiting (Token Bucket)
```
Key:    ratelimit:{user_id}:{route_pattern}
Type:   STRING (counter with TTL)
TTL:    Sliding window — key expires 1s after window end
Size:   ~50 bytes per counter

Pattern (Sliding Window):
  For each request:
    1. current_count = GET ratelimit:{user_id}:documents_upload
    2. IF current_count >= limit → REJECT (429)
    3. INCR ratelimit:{user_id}:documents_upload
    4. EXPIRE ratelimit:{user_id}:documents_upload 60 (first INCR sets TTL)

Lua script for atomicity:
  local current = redis.call("INCR", KEYS[1])
  if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
  end
  return current
```

#### OTP / Token Storage
```
Key:    otp:{identifier}         (identifier = phone or email hash)
Type:   STRING (JSON)
TTL:    600 (10 minutes)
Size:   ~200 bytes

Fields: { code: "438291", attempts: 0, verified: false, created_at: "..." }

Operations:
  SET otp:{phone_hash} '{"code":"438291","attempts":0,"verified":false}' EX 600 NX
  GET otp:{phone_hash} → increment attempts, check if expired
  DEL otp:{phone_hash} (on successful verification)

Limits:
  - Max 3 attempts per OTP (increment attempts field)
  - Max 5 OTP requests per phone per hour (using another rate limit key)
  - Cooldown: 30s between OTP requests (key: otp_cooldown:{phone_hash}, TTL: 30)
```

#### Refresh Token Store
```
Key:    refresh:{token_hash}
Type:   STRING (JSON)
TTL:    2592000 (30 days)
Size:   ~100 bytes

Fields: { user_id: "...", device_id: "...", created_at: "...", expires_at: "..." }

Operations:
  SET refresh:{sha256_of_token} '{"user_id":"...","device_id":"..."}' EX 2592000
  GET refresh:{sha256_of_token} → validate, issue new access token
  DEL refresh:{sha256_of_token} (on logout / token rotation)

Rotation: On every refresh, old token DEL'd and new token SET (token rotation prevents reuse).
```

#### Entity Cache (Short-lived)
```
Key:    entity:{session_id}:{document_id}
Type:   STRING (JSON array)
TTL:    3600 (1 hour — entities may be updated by user)
Size:   ~50 KB per document (all entities)

Purpose: Cache extracted entities per document during review phase.
         User frequently re-queries entity list during verification.

Invalidation: DEL on entity update, user correction, or re-OCR.
```

#### Document Processing Status
```
Key:    docjob:{upload_id}
Type:   STRING (JSON)
TTL:    7200 (2 hours — max expected processing time)
Size:   ~500 bytes

Fields: { status: "processing"|"completed"|"failed",
          progress_pct: 45,
          stages: { virus_scan: "done", ocr: "processing", extraction: "pending" },
          error: null }

Purpose: Polling endpoint for client-side progress bar.
         Avoids PG query for every progress poll (can be 10+ polls per upload).

Operations:
  SET docjob:{upload_id} '{"status":"processing","progress_pct":30,...}' EX 7200
  GET docjob:{upload_id} (polling — GET returns quickly from Redis)
  DEL docjob:{upload_id} (on session completion)
```

#### LLM Response Semantic Cache
```
Key:    llm:sem:{embedding_hash_prefix}
Type:   STRING (JSON)
TTL:    86400 (24 hours)
Size:   ~4 KB per cached response

Structure:
  llm:sem:cache_index → SET of {embedding_hash_prefix} keys (for bulk flush)
  llm:sem:{hash_prefix} → { prompt_hash, response, model, template_version, created_at }

Lookup:
  1. Generate embedding for user query (text-embedding-3-small)
  2. Nearest neighbor search across existing cache keys (cosine similarity > 0.92)
  3. If found: return cached response
  4. If not: call LLM, store response with hash_prefix

Limitations: Not a full vector DB. Use Redis Stack with RediSearch for proper vector similarity.
For production: use pgvector in PostgreSQL or a dedicated vector DB (Qdrant/Pinecone).
```

#### Abuse Prevention
```
Key:    abuse:{user_id}:{action}
Type:   STRING (counter)
TTL:    86400 (24 hours)
Size:   ~50 bytes

Actions tracked:
  - rapid_upload: > 10 documents in 5 minutes → flag
  - rapid_chat: > 30 messages in 1 minute → throttle
  - multiple_pan: same IP, different PAN attempts → block
  - concurrent_sessions: > 3 active sessions → warn

Example:
  INCR abuse:{user_id}:rapid_upload
  IF count > 10 → log abuse event, rate-limit further uploads
  EXPIRE abuse:{user_id}:rapid_upload 300 (reset after 5 min cooldown)
```

#### User Throttle (Fine-Grained)
```
Key:    throttle:{user_id}:{endpoint}
Type:   Sorted Set (timestamp per request)
TTL:    Varies per endpoint (sliding window)

Pattern:
  ZADD throttle:{user_id}:ai_chat {timestamp} {request_id}
  ZREMRANGEBYSCORE throttle:{user_id}:ai_chat 0 {now - window_ms}
  ZCARD throttle:{user_id}:ai_chat → count in window

  IF count > limit → REJECT
  EXPIRE throttle:{user_id}:ai_chat {window_seconds + 1}

Per-endpoint limits:
  ai_chat:     20 req / min window
  entities:   100 req / min window
  documents:    5 req / min window
```

### 4.3 Redis Stack Extensions (Optional)

If using Redis Stack (or RediSearch module):

```
# Vector index for semantic cache
FT.CREATE llm_cache_idx ON HASH PREFIX 1 "llm:sem:" SCHEMA
  embedding VECTOR FLAT 6 TYPE FLOAT32 DIM 1536 DISTANCE_METRIC COSINE
  prompt_hash TAG
  model TAG
  template_version TAG

# Search: find the most similar cached response
FT.SEARCH llm_cache_idx "*=>[KNN 1 @embedding $vec AS score]"
  SORTBY score
  RETURN 3 response model score
  PARAMS 2 vec $user_query_embedding
```

### 4.4 Redis High Availability

```
Sentinel Configuration:
  sentinel monitor taxstox-redis {master-ip} 6379 2
  sentinel down-after-milliseconds taxstox-redis 5000
  sentinel failover-timeout taxstox-redis 10000
  sentinel parallel-syncs taxstox-redis 1

Connection (ioredis):
  new Redis({
    sentinels: [
      { host: 'sentinel-1', port: 26379 },
      { host: 'sentinel-2', port: 26379 },
      { host: 'sentinel-3', port: 26379 },
    ],
    name: 'taxstox-redis',
    role: 'master',  // reads from master; use 'slave' for read replica
    retryStrategy: (times) => Math.min(times * 50, 2000),
  });
```

---

## 5. S3/MinIO Document Storage

### 5.1 Bucket Structure

```
Buckets (in MinIO for dev/staging, AWS S3 for production):

taxstox-uploads/
  ├── raw/{user_id}/{session_id}/{document_id}.pdf
  │     (original upload, 24h TTL)
  ├── processed/{user_id}/{session_id}/{document_id}/
  │     ├── page-001.png          (converted pages)
  │     ├── page-001-ocr.json     (per-page OCR output)
  │     └── combined-ocr.json     (full document OCR)
  │     (7 day TTL)
  └── quarantine/{document_id}/
        (virus-infected files, 7 day TTL, manual review)

taxstox-itr-outputs/
  ├── json/{user_id}/{session_id}/ITR-{type}-{ay}.json
  │     (final generated JSON, 7 year retention)
  ├── xml/{user_id}/{session_id}/ITR-{type}-{ay}.xml
  │     (XML for e-filing, 7 year retention)
  └── user-copy/{user_id}/{session_id}/ITR-{type}-{ay}.pdf
        (user-downloadable copy, 7 year retention)

taxstox-audit/
  └── exports/{year}/{month}/
        (periodic audit exports, 7 year retention)
```

### 5.2 Lifecycle Policies

```json
{
  "Rules": [
    {
      "Id": "purge-raw-uploads-24h",
      "Status": "Enabled",
      "Filter": { "Prefix": "raw/" },
      "Expiration": { "Days": 1 }
    },
    {
      "Id": "purge-processed-7d",
      "Status": "Enabled",
      "Filter": { "Prefix": "processed/" },
      "Expiration": { "Days": 7 }
    },
    {
      "Id": "purge-quarantine-7d",
      "Status": "Enabled",
      "Filter": { "Prefix": "quarantine/" },
      "Expiration": { "Days": 7 }
    },
    {
      "Id": "purge-itr-outputs-7yr",
      "Status": "Enabled",
      "Filter": { "Prefix": "" },
      "Expiration": { "Days": 2555 }
    }
  ]
}
```

### 5.3 Server-Side Encryption

```javascript
// AWS S3 SSE-KMS configuration
const s3Config = {
  bucket: 'taxstox-uploads',
  serverSideEncryption: 'aws:kms',
  sseKmsKeyId: 'arn:aws:kms:ap-south-1:ACCOUNT:key/TAXSTOX-DOCS-KEY',
  bucketKeyEnabled: true,
};

// MinIO SSE-S3 (encrypts with S3-managed keys; simpler for self-hosted)
const minioConfig = {
  bucket: 'taxstox-uploads',
  serverSideEncryption: 'AES256',
};

// Per-object encryption (for sensitive documents)
const putObjectParams = {
  Bucket: 'taxstox-uploads',
  Key: `raw/${userId}/${sessionId}/${documentId}.pdf`,
  Body: fileBuffer,
  ServerSideEncryption: 'aws:kms',
  SSEKMSKeyId: 'arn:aws:kms:ap-south-1:ACCOUNT:key/TAXSTOX-DOCS-KEY',
  Metadata: {
    'x-amz-meta-user-id': userId,
    'x-amz-meta-session-id': sessionId,
    'x-amz-meta-document-id': documentId,
    'x-amz-meta-uploaded-at': new Date().toISOString(),
  },
};
```

### 5.4 Pre-Signed URL Generation

```javascript
// Generate pre-signed upload URL (client uploads directly)
const getPresignedUploadUrl = async (userId, sessionId, documentId, filename) => {
  const key = `raw/${userId}/${sessionId}/${documentId}_${filename}`;
  const url = await s3.getSignedUrlPromise('putObject', {
    Bucket: 'taxstox-uploads',
    Key: key,
    Expires: 300,           // 5 minutes
    ContentType: mimetype,  // application/pdf, image/jpeg, etc.
  });
  return { url, key };
};

// Generate pre-signed download URL (user downloads ITR copy)
const getPresignedDownloadUrl = async (userId, sessionId, itrType) => {
  const key = `user-copy/${userId}/${sessionId}/ITR-${itrType}.pdf`;
  const url = await s3.getSignedUrlPromise('getObject', {
    Bucket: 'taxstox-itr-outputs',
    Key: key,
    Expires: 3600,          // 1 hour
    ResponseContentDisposition: `attachment; filename="ITR-${itrType}-AY2025-26.pdf"`,
  });
  return url;
};
```

### 5.5 Direct Upload Flow (Large Files)

```
1. Client requests pre-signed URL from Document Ingestion Service
2. Service validates: auth, rate limit, file size estimate
3. Service generates pre-signed PUT URL (5 min TTL)
4. Client uploads directly to S3 using pre-signed URL
5. Client notifies server: "upload complete, key: {s3_key}"
6. Server verifies upload (HEAD object → check ETag matches)
7. Server creates documents row in PostgreSQL
8. Server emits document.uploaded event to Kafka
```

### 5.6 Automatic Purge Enforcement

Beyond S3 lifecycle policies, a scheduled job runs daily to:

```typescript
// Daily purge job (BullMQ, CRON: "0 2 * * *")
async function purgeExpiredDocuments() {
  const expired = await db.query(`
    UPDATE documents
    SET purged_at = NOW(), is_deleted = true
    WHERE purge_at < NOW() AND purged_at IS NULL
    RETURNING id, s3_bucket, s3_key
  `);

  for (const doc of expired.rows) {
    await s3.deleteObject({
      Bucket: doc.s3_bucket,
      Key: doc.s3_key,
    });
  }

  await db.query(`
    INSERT INTO data_purge_log (purge_job_name, affected_table, records_purged, status, started_at, completed_at)
    VALUES ('purge_expired_documents', 'documents', $1, 'success', $2, NOW())
  `, [expired.rowCount, new Date()]);
}
```

---

## 6. Data Retention and Purging

### 6.1 Retention Schedule

| Data Category | Retention Period | Purge Action | Legal Basis |
|--------------|-----------------|--------------|-------------|
| User PII (name, DOB, email, phone) | Until account deletion + 90 days | Anonymize (zero out encrypted fields, keep hashes for dedup) | DPDP Act 2023 |
| PAN hash | 7 years after last filing | Delete from active; archive to cold storage | Income Tax Act 1961 (Sec 139) |
| Uploaded documents (raw) | 24 hours after upload | Hard delete from S3 | Internal policy |
| Processed documents (OCR output) | 7 days after processing | Hard delete from S3 | Internal policy |
| Extracted entities | 7 years after filing | Anonymize (remove raw values, keep counts) | Income Tax Act 1961 |
| Tax computations | 7 years | Hard delete from PG; keep in audit log | Income Tax Act 1961 |
| ITR JSON/XML | 7 years | Archive to Glacier, delete from active S3 | Income Tax Act 1961 |
| Conversation turns (raw) | 90 days | Delete content, keep metadata only | DPDP Act 2023 |
| Conversation turns (PII-masked) | 7 years | Retain (for model improvement, anonymized) | DPDP Act 2023 (anonymized data exempt) |
| Audit log | 7 years | Hard delete | Income Tax Act 1961 |
| Session state (Redis) | 24 hours | Automatic TTL expiry | Ephemeral |
| OTPs (Redis) | 10 minutes | Automatic TTL expiry | Ephemeral |

### 6.2 Soft-Delete Patterns

Most tables use `is_deleted` or `is_active` boolean for soft delete. This allows:

1. Undelete within 30 days (user accidentally deleted account)
2. Compliance hold (prevent deletion during active investigation)
3. Referential integrity (foreign keys remain valid)

```typescript
// Soft-delete a user
async function softDeleteUser(userId: string, reason: string) {
  const tx = await db.begin();

  await tx.query(`
    UPDATE users SET
      is_active = false,
      deleted_at = NOW(),
      updated_at = NOW()
    WHERE id = $1
  `, [userId]);

  // Anonymize PII (replace with "[DELETED]")
  await tx.query(`
    UPDATE users SET
      name_encrypted = pgp_sym_encrypt('[DELETED]', get_encryption_key()),
      email_encrypted = pgp_sym_encrypt('[DELETED]@deleted.in', get_encryption_key()),
      phone_encrypted = pgp_sym_encrypt('0000000000', get_encryption_key()),
      dob_encrypted = NULL
    WHERE id = $1
  `, [userId]);

  await tx.query(`
    INSERT INTO audit_log (event_id, actor_type, actor_id, event_type, event_category,
      resource_type, resource_id, details_json, data_hash, entry_hash, nonce)
    VALUES (gen_random_uuid(), 'user', $1, 'user.account.deleted', 'auth',
      'user', $1, $2, $3, $4, $5)
  `, [userId, JSON.stringify({reason}), ...computeHashChain()]);

  await tx.commit();
}
```

### 6.3 Hard-Delete Schedule

```typescript
// Monthly job: "0 3 1 * *" (1st of every month at 3 AM)
async function hardDeleteAnonymizedData() {
  // Delete users anonymized > 90 days ago
  await db.query(`
    DELETE FROM users
    WHERE anonymized_at IS NOT NULL
      AND anonymized_at < NOW() - INTERVAL '90 days'
  `);

  // Hard-delete soft-deleted documents purged > 30 days ago
  await db.query(`
    DELETE FROM documents
    WHERE is_deleted = true
      AND purged_at IS NOT NULL
      AND purged_at < NOW() - INTERVAL '30 days'
  `);
}
```

### 6.4 Anonymization for Analytics

When user data is anonymized:

```typescript
// Keep for analytics but remove PII
await db.query(`
  UPDATE users
  SET
    name_encrypted = NULL,
    email_encrypted = NULL,
    phone_encrypted = NULL,
    dob_encrypted = NULL,
    aadhaar_hash = NULL,
    aadhaar_last_four = NULL,
    pan_last_four = NULL,     -- keep pan_hash for dedup
    anonymized_at = NOW()
  WHERE id = $1
    AND deleted_at IS NOT NULL     -- already soft-deleted
    AND deleted_at < NOW() - INTERVAL '90 days'  -- 90 day grace period
`);
```

---

## 7. Migration Strategy

### 7.1 Tool: Flyway

```shell
# Why Flyway over Liquibase?
# 1. Simpler — SQL-only migrations, no XML/YAML config files
# 2. Checksum-based change detection (tamper-proof)
# 3. Repeatable migrations support for views/functions
# 4. Node.js compatible via flyway-connector or JDBC wrapper
```

### 7.2 Migration Directory Structure

```
src/main/resources/db/migration/
├── V1__initial_schema.sql
├── V2__add_document_type_classification.sql
├── V3__add_recommendations_table.sql
├── V4__add_rule_definitions.sql
├── V5__add_indexes_for_performance.sql
├── V6__add_row_level_security.sql
├── V7__add_prompt_templates.sql
├── V8__add_entity_type_master.sql
├── V9__add_notification_log.sql
├── V10__add_user_consent_log.sql
├── V11__add_data_purge_log.sql
├── V12__add_tax_computation_indexes.sql
│
├── R__view_active_sessions.sql        (repeatable — creates view)
├── R__view_filing_summary.sql          (repeatable — creates materialized view)
├── R__function_update_updated_at.sql   (repeatable — trigger function)
│
└── afterMigrate__seed_data.sql         (always executed after migration)
```

### 7.3 Migration Naming Convention

```
{V} | {Prefix} | {Version} | __ | {Description} | .sql
 V   |          1          |  _  | initial_schema  | .sql
 V   |          2          |  __ | add_document_type_classification | .sql
 V   |         12          |  __ | add_tax_computation_indexes | .sql

Version: Sequential integer. No gaps.
Description: Snake_case, max 10 words, describes the change.
```

### 7.4 Blue-Green Deployment Compatibility

Rules for zero-downtime migrations:

```
1. NEVER ALTER COLUMN with NOT NULL without providing a default
   - Wrong:  ALTER TABLE users ADD COLUMN new_col VARCHAR NOT NULL
   - Right:  ALTER TABLE users ADD COLUMN new_col VARCHAR
             UPDATE users SET new_col = 'default' WHERE new_col IS NULL
             ALTER TABLE users ALTER COLUMN new_col SET NOT NULL

2. NEVER rename or delete a column in the same migration that adds it
   - Old code may still reference old column name during rolling update

3. Add indexes CONCURRENTLY for production tables
   - CREATE INDEX CONCURRENTLY idx_name ON table (column)
   - Note: Cannot run in transaction; use separate migration step

4. Wrap in transaction only if:
   - DDL on a single table (ALTER TABLE ... ADD COLUMN)
   - Adding comments, constraints
   - Not for: CREATE INDEX CONCURRENTLY, VACUUM, CLUSTER

5. Version backward compatibility:
   - Blue (old) and Green (new) run simultaneously during cutover
   - Schema changes must be compatible with both code versions
   - New columns must have defaults or be nullable
   - Removed columns must be deprecated (marked in comment) for 1 release cycle before dropping

6. Data migration:
   - Run as background job, not inline in migration
   - Add column → background job backfills data → then add NOT NULL constraint
```

### 7.5 Example: Adding a New Column with Backfill

```sql
-- V12__add_preferred_contact_time.sql

-- Step 1: Add nullable column (compatible with blue deployment)
ALTER TABLE users ADD COLUMN preferred_contact_time VARCHAR(10);

-- Step 2: Add constraint (validation, not enforcement — blue may not set it)
-- Note: No NOT NULL yet

-- Step 3: (Separate deployment step) Backfill via background job
-- This is done via BullMQ job, not in migration:

async function backfillPreferredContactTime() {
  await db.query(`
    UPDATE users
    SET preferred_contact_time = 'morning'
    WHERE preferred_contact_time IS NULL
  `);
}

-- Step 4: (Next release) Add NOT NULL constraint
-- ALTER TABLE users ALTER COLUMN preferred_contact_time SET NOT NULL;
```

### 7.6 Flyway Configuration

```properties
# flyway.conf
flyway.url=jdbc:postgresql://taxstox-db:5432/taxstox
flyway.user=flyway_migrator
flyway.password=${FLYWAY_PASSWORD}
flyway.schemas=public
flyway.locations=filesystem:src/main/resources/db/migration
flyway.baseline-on-migrate=true
flyway.out-of-order=false
flyway.validate-on-migrate=true
flyway.clean-disabled=true              # NEVER allow clean in production
flyway.target=latest
flyway.connect-retries=10
flyway.lock-retry-count=10
```

### 7.7 CI/CD Integration

```yaml
# .github/workflows/db-migration.yml
name: Database Migration
on:
  push:
    branches: [main]
    paths:
      - 'src/main/resources/db/migration/**'

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate migrations (dry-run)
        run: |
          flyway -configFiles=flyway.conf migrate -dryRunOutput=dry-run.sql
          # Review dry-run.sql for destructive operations

      - name: Run migrations (staging)
        run: |
          flyway -configFiles=flyway-staging.conf migrate

      - name: Run migrations (production)
        if: github.ref == 'refs/heads/main'
        run: |
          # Production migrations are manual-approve step in ArgoCD
          echo "Migrations to be applied via ArgoCD Sync"
```

### 7.8 Rollback Strategy

```sql
-- Flyway does NOT support automatic rollback.
-- Rolling back a DDL change requires a new migration:

-- V13__rollback_V12_preferred_contact_time.sql

-- Revert: Drop the column added in V12
-- Note: Ensure no code references this column before deploying
ALTER TABLE users DROP COLUMN IF EXISTS preferred_contact_time;

-- For data loss scenarios, restore from backup:
-- pg_restore -d taxstox -Fc taxstox_backup_before_V12.dump
-- Re-run migrations from V12 onward

-- Backup schedule:
--   - Full backup: Daily at 1 AM (WAL archiving continuous)
--   - Pre-migration backup: Automatic before any DDL migration
--   - Retention: 30 days daily, 12 months monthly
```
