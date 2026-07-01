# 02 — Non-Functional Requirements

> **Parent:** [00-README.md](00-README.md) | **Previous:** [01 Product & Functional Requirements](01-product-requirements.md) | **Next:** [03 User Personas & Journeys](03-user-personas-journeys.md)
> **Design System Reference:** [DESIGN.md](design-system/DESIGN.md)
> **Last Updated:** 2026-06-29

---

## Table of Contents

1. [Performance Requirements](#1-performance-requirements)
2. [Availability Requirements](#2-availability-requirements)
3. [Security Requirements](#3-security-requirements)
4. [Privacy Requirements](#4-privacy-requirements)
5. [Compliance Requirements](#5-compliance-requirements)
6. [Scalability Requirements](#6-scalability-requirements)
7. [Reliability Requirements](#7-reliability-requirements)
8. [Maintainability Requirements](#8-maintainability-requirements)
9. [Usability Requirements](#9-usability-requirements)
10. [Interoperability Requirements](#10-interoperability-requirements)
11. [Data Integrity Requirements](#11-data-integrity-requirements)
12. [Regulatory Requirements](#12-regulatory-requirements)
13. [Environmental & Operational Requirements](#13-environmental--operational-requirements)
14. [Cross-Cutting NFRs](#14-cross-cutting-nfrs)
15. [NFR Verification & Testing](#15-nfr-verification--testing)

---

## 1. Performance Requirements

### 1.1 Response Time Budgets

TaxStox is an interactive AI-powered tax filing system. Response times are categorized by operation type and user-facing criticality. All times are measured at the 95th percentile (P95) unless otherwise specified.

| Operation | Target (P95) | Hard Limit (P99) | Measured From | Criticality |
|-----------|-------------|-------------------|---------------|-------------|
| Page load (initial) | < 2 seconds | < 4 seconds | User click to interactive | Standard |
| Page load (subsequent, SPA) | < 500 ms | < 1.5 seconds | Route change to painted | Standard |
| Document upload (initiation) | < 1 second | < 3 seconds | Drop to upload start acknowledgement | Standard |
| Document upload (completion) | < 30 seconds per 10MB | < 60 seconds per 10MB | Upload start to server confirmation | Standard |
| Document classification | < 5 seconds | < 10 seconds | Upload complete to classified | Critical |
| Entity extraction (single PDF) | < 15 seconds | < 30 seconds | Classification done to entities ready | Critical |
| Entity extraction (bulk, 5 PDFs) | < 45 seconds | < 90 seconds | Last upload done to all entities ready | Critical |
| Cross-document validation | < 8 seconds | < 15 seconds | Entities ready to validation complete | Critical |
| Adaptive question generation | < 3 seconds | < 6 seconds | Answer submitted to next question rendered | Standard |
| Tax computation (single scenario) | < 2 seconds | < 5 seconds | Compute request to result | Critical |
| Tax optimization (all scenarios) | < 10 seconds | < 20 seconds | Optimize request to recommendation | Critical |
| ITR JSON generation | < 5 seconds | < 10 seconds | Generate request to file ready | Critical |
| JSON schema validation | < 3 seconds | < 5 seconds | JSON ready to validation result | Critical |
| Download ITR JSON | < 2 seconds | < 5 seconds | Click to save dialog | Standard |
| Search filing history | < 1 second | < 3 seconds | Query submitted to results | Standard |
| Dashboard load | < 2 seconds | < 4 seconds | Auth confirmed to dashboard painted | Standard |
| AI chat response (first token) | < 2 seconds | < 5 seconds | Message sent to first response token | Standard |
| AI chat response (full) | < 8 seconds | < 15 seconds | Message sent to complete response | Standard |
| AIS/26AS fetch (via ITD API) | < 10 seconds | < 30 seconds | Request initiated to data received | Standard |
| Login/OTP verification | < 3 seconds | < 8 seconds | Credentials submitted to dashboard | Standard |
| Profile save | < 2 seconds | < 4 seconds | Save clicked to confirmation | Standard |

### 1.2 Throughput Requirements

| Metric | Target | Peak Season Target | Measurement Period |
|--------|--------|-------------------|-------------------|
| Concurrent active filing sessions | 1,000 | 10,000 | Per minute |
| Concurrent logged-in users | 5,000 | 50,000 | Per minute |
| Document uploads per minute | 500 | 5,000 | Sustained over 1 hour |
| Document classifications per minute | 500 | 5,000 | Sustained over 1 hour |
| Entity extractions per minute | 200 | 2,000 | Sustained over 1 hour |
| Tax computations per minute | 1,000 | 10,000 | Sustained over 1 hour |
| JSON generations per minute | 300 | 3,000 | Sustained over 1 hour |
| AI chat completions per minute | 1,000 | 10,000 | Sustained over 1 hour |
| API requests per minute | 10,000 | 100,000 | Sustained over 1 hour |
| Concurrent WebSocket connections | 2,000 | 15,000 | Per minute |
| Database write operations per second | 500 | 5,000 | Sustained over 1 minute |
| Database read operations per second | 2,000 | 20,000 | Sustained over 1 minute |

### 1.3 Latency Budgets (End-to-End)

**Total Filing Session Time Budgets:**

| Filing Mode | Target | Acceptable | Maximum |
|-------------|--------|------------|---------|
| With Form 16 + AIS (documents ready) | < 2 minutes | < 4 minutes | < 8 minutes |
| With Form 16 only | < 3 minutes | < 5 minutes | < 10 minutes |
| With zero documents (interview mode) | < 5 minutes | < 8 minutes | < 15 minutes |
| Capital gains filing | < 5 minutes | < 8 minutes | < 15 minutes |
| NRI filing | < 6 minutes | < 10 minutes | < 18 minutes |
| Revised return | < 3 minutes | < 5 minutes | < 10 minutes |
| Belated return | < 4 minutes | < 6 minutes | < 12 minutes |
| CA bulk filing (per client) | < 2 minutes | < 3 minutes | < 5 minutes |

**Per-operation latency budget breakdown (for filing with documents):**

| Phase | Budget | Cumulative |
|-------|--------|------------|
| Upload & classify (2 PDFs) | 20 seconds | 20 seconds |
| Entity extraction (2 PDFs) | 25 seconds | 45 seconds |
| Cross-document validation | 8 seconds | 53 seconds |
| Adaptive questionnaire (5 Qs) | 40 seconds | 93 seconds |
| Tax computation + optimization | 12 seconds | 105 seconds |
| Review & confirm | 10 seconds | 115 seconds |
| JSON generation + validation | 5 seconds | 120 seconds |

### 1.4 Resource Utilization

| Resource | Normal Target | Peak Target | Measurement |
|----------|---------------|-------------|-------------|
| CPU (application servers) | < 50% utilization | < 80% utilization | Average over 5 minutes |
| CPU (AI inference servers) | < 60% utilization | < 85% utilization | Average over 5 minutes |
| Memory (application servers) | < 60% utilized | < 80% utilized | Average over 5 minutes |
| Memory (database) | < 70% utilized | < 85% utilized | Average over 5 minutes |
| Disk I/O (database) | < 40% capacity | < 70% capacity | Average over 5 minutes |
| Network bandwidth | < 30% capacity | < 60% capacity | Average over 5 minutes |
| GPU (if using self-hosted LLM) | < 70% utilization | < 90% utilization | Average over 5 minutes |

### 1.5 Performance Degradation Policy

| Degradation State | Trigger | Actions |
|-------------------|---------|---------|
| Warning | P95 response time exceeds 1.5x target | Alert monitoring, auto-scaling check |
| Critical | P95 exceeds 2x target for > 5 minutes | Scale up, degrade non-critical features, shed load |
| Emergency | P95 exceeds 3x target for > 2 minutes | Circuit break non-critical paths, serve degraded UI |
| Overload | System at > 80% capacity | Rate limit, queue non-interactive operations, show wait screen |

### 1.6 Caching Strategy for Performance

| Cache Layer | What | TTL | Hit Rate Target |
|-------------|------|-----|-----------------|
| CDN | Static assets (JS, CSS, images, fonts) | 1 year (immutable) | > 95% |
| CDN | Public landing pages, blog | 5 minutes | > 90% |
| In-memory (Redis) | Tax rule definitions | 1 hour (or on rule update) | > 99% |
| In-memory (Redis) | ITD schema definitions | 24 hours | > 99% |
| In-memory (Redis) | Session state | Session TTL | N/A |
| In-memory (Redis) | User profile (non-PII) | 15 minutes | > 85% |
| In-memory (Redis) | Computation results (idempotent) | 10 minutes | > 80% |
| Application cache | LLM response cache (non-PII) | Variable (semantic cache) | > 40% |
| Database query cache | Frequent read queries | 5 minutes | > 70% |

**Semantic caching for AI responses:** For identical or near-identical queries (e.g., "Explain section 80C" vs "What is 80C deduction?"), the system shall return cached responses with similarity above 0.95 threshold, reducing LLM calls and latency.

---

## 2. Availability Requirements

### 2.1 Uptime Targets

| Service Tier | Target Availability | Allowed Downtime (Monthly) | Allowed Downtime (Yearly) |
|-------------|-------------------|---------------------------|---------------------------|
| Core filing flow (upload to JSON) | 99.9% ("Three Nines") | 43.2 minutes | 8.76 hours |
| AI/chat services | 99.5% | 3.6 hours | 43.8 hours |
| Dashboard & history | 99.5% | 3.6 hours | 43.8 hours |
| API layer | 99.9% | 43.2 minutes | 8.76 hours |
| Database layer | 99.95% | 21.6 minutes | 4.38 hours |
| Document processing pipeline | 99.5% | 3.6 hours | 43.8 hours |
| Overall system (filing season: Jan-Mar) | 99.95% | 21.6 minutes | 4.38 hours (seasonal) |
| Overall system (non-filing season) | 99.0% | 7.2 hours | 87.6 hours |

**Filing Season (Peak):** January 1 to March 31 (also includes July 31 deadline period: July 1-31). During this period, maintenance windows must be scheduled for low-traffic hours (2:00 AM to 5:00 AM IST).

**Critical Filing Days:** Last 7 days before ITR deadline (typically July 25-31). During this period, maintenance windows are suspended entirely. All deployments must be frozen. System operates at maximum redundancy.

### 2.2 Recovery Point Objective (RPO)

| Data Category | RPO | Rationale |
|---------------|-----|-----------|
| User accounts & profiles | 5 minutes | Continuous streaming backup |
| Filing sessions (in-progress) | 1 minute | Near real-time event sourcing |
| Completed filings (ITR JSON + audit trail) | Zero (0) | Synchronous write to primary + standby |
| Uploaded documents | 5 minutes | Continuous replication |
| AI conversation history | 1 minute | Streamed to durable queue |
| Tax rule configurations | Zero (0) | Git-versioned, re-deployed |
| Audit logs | 5 minutes | Append-only stream |
| Analytics & metrics | 15 minutes | Batch exported |

### 2.3 Recovery Time Objective (RTO)

| Service | RTO | Target |
|---------|-----|--------|
| Core filing flow | < 5 minutes | Automatic failover |
| AI/chat services | < 10 minutes | Warm standby |
| Dashboard & history | < 5 minutes | Automatic failover |
| Document processing pipeline | < 15 minutes | Cold standby with queue redrive |
| Database (primary) | < 2 minutes | Automatic failover to replica |
| Database (with data loss) | < 15 minutes | Restore from backup |
| Static assets (CDN) | < 1 minute | Multi-region CDN |
| Full disaster recovery (region failover) | < 30 minutes | Active-passive multi-region |

### 2.4 Disaster Recovery Strategy

**Deployment Topology:**
- Primary region: AWS ap-south-1 (Mumbai) — serves all production traffic
- DR region: AWS ap-southeast-1 (Singapore) — warm standby, no production traffic
- Future: AWS me-central-1 (Hyderabad) for additional redundancy within India

**DR Activation Triggers:**
1. Primary region unavailable for > 5 minutes (automated health check)
2. Primary database unreachable for > 2 minutes
3. Planned DR drills (quarterly)
4. Human decision on degradation severity

**DR Activation Procedure:**
1. Route53 health check detects primary failure
2. DNS failover to DR region (TTL: 60 seconds, convergence within 5 minutes)
3. Read replicas in DR region promoted to primary
4. Application servers in DR region scaled up
5. Document processing queue in DR region activated
6. Users redirected to DR endpoint with banner: "Degraded mode — some features may be slower"
7. Full functionality expected within 15 minutes of DR activation

**DR Fallback (Restore to Primary):**
1. Verify primary region is fully operational
2. Sync data from DR to primary
3. Perform controlled DNS switchback
4. Monitor for 30 minutes before declaring recovery complete

**Backup Strategy:**
| Data | Backup Frequency | Retention | Method |
|------|-----------------|-----------|--------|
| Database (full) | Daily | 30 days | pg_dump to S3 with AES-256 encryption |
| Database (WAL) | Continuous | 7 days | Streaming WAL to S3 |
| Documents (S3) | Cross-region replication | Per retention policy | S3 CRR |
| Configuration | On every change | Git history | Infrastructure as Code |
| Audit logs | Real-time to append-only store | 7 years | Immutable log storage |

### 2.5 Service Level Agreements (External)

| Dependency | Required SLA | Penalty/Remedy |
|------------|-------------|----------------|
| Cloud provider (compute) | 99.9% | Credit or migration plan |
| Cloud provider (database) | 99.95% | Credit or migration plan |
| CDN provider | 99.9% | Contractual penalty clause |
| LLM API provider | 99.5% | Circuit breaker + fallback model |
| SMS/OTP provider | 99.5% | Alternate provider failover |
| Email delivery service | 99.0% | Queue + retry |
| ITD portal API (AIS/26AS) | Best effort | Graceful degradation |

---

## 3. Security Requirements

### 3.1 Encryption Standards

The design system (DESIGN.md) establishes a trust-first aesthetic with colors referencing institutional security. These are the enforceable encryption standards backing that visual promise.

**Data in Transit:**
| Requirement | Standard | Notes |
|-------------|----------|-------|
| All external traffic | TLS 1.3 only | TLS 1.2 accepted for legacy client compatibility; 1.0 and 1.1 blocked. Certificate from CA with minimum 2048-bit RSA key. |
| Internal service-to-service | mTLS 1.3 | Mutual TLS with short-lived certificates (24 hour expiry), auto-rotated by service mesh. |
| API endpoints | HTTPS only | HTTP requests redirected at load balancer level. HSTS header with max-age=63072000. |
| WebSocket connections | WSS (TLS 1.3) | All real-time channels encrypted. |
| Database connections | TLS 1.3 | Client-side verification of server certificate. |

**Data at Rest:**
| Requirement | Standard | Notes |
|-------------|----------|-------|
| Database (user data) | AES-256-GCM | Column-level encryption for PII fields. Key rotation every 90 days. |
| Database (all other) | AES-256 | Transparent Data Encryption (TDE) at storage layer. |
| S3 objects (documents) | AES-256 | Server-side encryption with customer-managed KMS keys. |
| S3 objects (backups) | AES-256 | Separate KMS key from production data. |
| Redis cache | AES-256 | For cached PII/near-PII data. Disabled for non-sensitive cache. |
| Logs (containing PII) | AES-256 | Encrypted before write; PII fields redacted where possible. |
| Queue messages (with PII) | AES-256 | Server-side encryption with KMS. |

**Key Management:**
- AWS KMS with automatic key rotation (annual for CMKs, 90 days for data keys)
- Separate KMS keys per environment (dev, staging, prod)
- Separate KMS key for documents, database, cache, logs
- Key access audited via CloudTrail
- HSM-backed key storage for root keys (AWS CloudHSM)

### 3.2 Authentication & Authorization

**Authentication:**
| Mechanism | Security Level | Notes |
|-----------|---------------|-------|
| Password-based | Standard | Argon2id hashing, min 8 chars, complexity requirements |
| OTP (SMS/Email) | Standard | 6-digit, 5-minute TTL, rate-limited to 3 attempts per PAN per hour |
| PAN-based lookup | High | PAN verified against PAN card + DOB; records linked to PAN hash |
| OAuth 2.0 / SSO | High | For enterprise/CA login; supports Azure AD, Google Workspace |
| Biometric (mobile) | Standard | Device-level biometric for session unlock, not primary auth |
| Session tokens | High | JWT with 15-minute access token + 7-day refresh token (HTTP-only, Secure, SameSite=Strict cookies) |

**Authorization (RBAC):**
| Role | Scope | Permissions |
|------|-------|-------------|
| Self-filer | Own account only | File own ITR, view own data, download own JSON |
| Family-filer (P2) | Linked family accounts | File for dependents, view dependent data |
| CA Professional | Client accounts (with consent) | File for multiple clients, review mode, bulk download |
| CA Admin | Firm-wide | Manage team, assign clients, audit team filings |
| Support Agent | Escalated cases | View case data (masked PII), run diagnostics |
| System Admin | System | Infrastructure management, no data access |
| Auditor | Read-only logs | View audit logs, no PII access |

**Session Management:**
- Access token expiry: 15 minutes
- Refresh token expiry: 7 days (renewable)
- Maximum concurrent sessions: 5 per user
- Session invalidation on password change
- Force logout on suspicious activity detection
- Session timeout (idle): 30 minutes
- Persistent session across filing steps (state preserved in encrypted cookies + server-side session)

### 3.3 Application Security

| Control | Requirement |
|---------|-------------|
| OWASP Top 10 | Zero known vulnerabilities in production. Annual penetration testing. |
| Input validation | Server-side validation for ALL inputs. Client-side validation is UX only. |
| SQL injection | Parameterized queries exclusively. ORM layer enforces prepared statements. |
| XSS prevention | Content-Security-Policy header. Output encoding. Strict CSP with nonce-based script loading. |
| CSRF protection | Anti-CSRF tokens on all state-changing requests. SameSite cookies. |
| Rate limiting | Per-IP: 100 requests/minute. Per-PAN: 30 requests/minute. Per-endpoint: configurable. |
| File upload validation | MIME check, magic byte verification, AV scan, size limit (10MB), content sanitization |
| API security | API keys for external integrations. JWT for user APIs. OAuth 2.0 for third-party. |
| Dependency scanning | Weekly automated scans. Critical CVEs patched within 48 hours. |
| Secrets management | AWS Secrets Manager / HashiCorp Vault. No secrets in code or environment variables. |
| Audit logging | All security events logged: logins, logouts, failed auth, permission changes, data access, role changes. |

### 3.4 Infrastructure Security

| Control | Requirement |
|---------|-------------|
| Network segmentation | VPC with public, private, and isolated subnets. Database in isolated subnet with no direct internet access. |
| WAF | AWS WAF blocking SQL injection, XSS, known bad IPs, rate-based rules. |
| DDoS protection | AWS Shield Advanced. Auto-scaling absorbs traffic spikes. |
| Bastion hosts | SSH access via bastion only. No direct SSH to production instances. |
| Security groups | Least-privilege model. Database security group allows traffic only from application security group. |
| OS hardening | CIS benchmark-compliant AMIs. Automated patching with 7-day SLA for critical patches. |
| Container security | Image scanning in CI/CD pipeline. No privileged containers. Read-only root filesystem. |
| Secrets rotation | Database credentials rotated every 90 days. API keys rotated every 180 days. |

### 3.5 Security Incident Response

| Phase | Actions | Timeline |
|-------|---------|----------|
| Detection | Automated alerts from GuardDuty, WAF, intrusion detection, anomaly detection | Real-time |
| Triage | Security engineer assesses severity (Critical/High/Medium/Low) | < 15 minutes for Critical |
| Containment | Isolate affected resources, revoke compromised credentials, block IPs | < 30 minutes for Critical |
| Eradication | Remove threat, patch vulnerability, rotate keys | < 4 hours for Critical |
| Recovery | Restore from clean backup, verify integrity | < 8 hours for Critical |
| Post-mortem | Root cause analysis, preventive measures, report | < 48 hours |

**Incident Severity Definitions:**
- **Critical:** Confirmed data breach, unauthorized PII access, system compromise. Immediate notification to CISO.
- **High:** Attempted breach detected, vulnerability in production, credential compromise suspected. Notification within 1 hour.
- **Medium:** Vulnerability in non-production, suspicious activity pattern, policy violation. Notification within 24 hours.
- **Low:** Failed scan, configuration drift, minor policy violation. Normal ticket process.

---

## 4. Privacy Requirements

### 4.1 Data Minimization

| Principle | Implementation |
|-----------|---------------|
| Collect only what is needed | System collects only PAN, name, DOB, contact info (email/phone), and income/deduction data necessary for ITR filing. No biometric data, no location data, no device identifiers, no browsing history. |
| Minimal AI context | AI agents receive only the data necessary for their specific task. The conversation agent does not see raw document text. The extraction agent does not see user contact information. |
| Purpose limitation | Data collected for ITR filing is used exclusively for that purpose. No secondary use, no data selling, no analytics on PII. |
| Progressive disclosure | System requests additional data only when a specific deduction or exemption is identified. No bulk data collection upfront. |
| Default privacy | Privacy-preserving defaults: documents auto-purged, data auto-deleted, no data retained beyond necessity. |

### 4.2 Data Retention Policy

| Data Category | Retention Period | Rationale | Purge Mechanism |
|---------------|-----------------|-----------|-----------------|
| Uploaded documents (PDFs, images) | 24 hours after ITR JSON generation | Time window for verification, then risk of exposure exceeds utility | Automated deletion job runs hourly. S3 lifecycle policy enforces 24h expiry. |
| Extracted financial entities | 24 hours after ITR JSON generation | Sufficient for session completion and download | Same as above. Deleted with session cleanup. |
| ITR JSON (generated) | 6 years + current AY (statutory requirement) | IT Act requires records for 6 years for assessment/re-assessment | Manual deletion on account closure with legal hold check. |
| Audit trail | 7 years | Compliance and potential litigation | Append-only during retention; destroyed after 7 years. |
| User profile (name, PAN, email, phone) | Until account deletion | Account functionality | Immediate deletion with 30-day grace period for recovery. |
| Session data | Session end + 1 hour | Grace period for reconnection | Session store TTL. |
| AI conversation logs | 24 hours after session ends | Model improvement only with explicit consent. Anonymized after 24h. | Anonymization pipeline strips all PII. Anonymized logs retained 90 days. |
| Usage analytics (non-PII) | 24 months | Product improvement | Aggregated and stored without identifiers. |
| Billing records | 7 years | Statutory requirement | Encrypted at rest with limited access. |
| Support tickets | 3 years after resolution | Reference and compliance | Automated purge after 3 years. |
| Error logs | 90 days | Debugging | Automated rotation. PII redacted before logging. |

### 4.3 Data Purging Procedure

**Automatic Purge (Standard):**
1. Session completion triggers 24-hour countdown for document/data deletion
2. Hourly cron job scans for expired data across all stores (PostgreSQL, S3, Redis, logs)
3. Expired data is securely deleted:
   - Database: `DELETE` with `VACUUM FULL` for sensitive tables (or soft-delete with hard-delete on schedule)
   - S3: Object deletion + lifecycle policy for additional enforcement
   - Redis: Key eviction with TTL
   - Logs: Log rotation with deletion of old log groups
4. Deletion confirmation logged to audit trail

**Account Deletion (User-Initiated):**
1. User requests deletion from account settings
2. System prompts for confirmation with warning about data loss
3. 30-day grace period begins: account disabled, no new filings possible
4. During grace period: user can cancel deletion by re-authenticating
5. After 30 days: all data purged as above, plus profile data
6. Exceptions:
   - ITR JSONs retained for statutory period (under legal hold flag)
   - Billing records retained for 7 years
   - Audit logs retained for 7 years
7. User receives email confirmation after purge completes

**Emergency Purge (Security Incident):**
1. Security team initiates emergency purge from admin console
2. All user data deleted immediately (documents, extracted data, session, cache)
3. ITR JSONs placed under legal hold (no deletion during investigation)
4. Full audit trail preserved for forensic analysis
5. User notified of data deletion after incident containment

### 4.4 Data Subject Rights (DPDP Act 2023)

| Right | Implementation |
|-------|---------------|
| Right to know | Privacy policy accessible from every page. Data processing purposes listed in plain language. |
| Right to access | DSAR (Data Subject Access Request) portal returns all personal data within 72 hours. |
| Right to correction | User can edit profile data at any time. Correction of extracted data allowed during session. |
| Right to erasure | Account deletion (section 4.3) within 30 days. DSAR erasure request processed within 7 days. |
| Right to grievance | Dedicated Data Protection Officer (DPO) contact. Grievance redressed within 30 days. |
| Right to nominate | User can nominate a person to exercise rights after incapacitation. |

### 4.5 Privacy by Design

| Measure | Implementation |
|---------|---------------|
| PAN hashing | PAN stored as SHA-256 hash with unique salt per user. Raw PAN only in encrypted column with restricted access. |
| PII masking | All PII masked in support interfaces, logs, and analytics. Support agents see only last 4 digits of PAN, masked name. |
| Data segmentation | PII stored separately from financial data. Different encryption keys for different data categories. |
| Privacy impact assessment | PIA required before any new feature that processes personal data. Reviewed by DPO. |
| Training | All employees complete privacy training annually. Developers complete secure coding + privacy training. |
| Vendor assessment | All sub-processors (cloud, LLM, SMS, email) undergo privacy assessment. DPAs executed with all vendors. |
| Anonymization | Anonymization pipeline removes all direct and quasi-identifiers before data used for analytics or model improvement. |

---

## 5. Compliance Requirements

### 5.1 Income Tax Act, 1961

| Section/Requirement | How TaxStox Ensures Compliance |
|--------------------|-------------------------------|
| Section 139(1) — Due date for ITR filing | System enforces due date awareness. Filing sessions opened after deadline trigger appropriate ITR type (belated/revised). |
| Section 139(4) — Belated return | System identifies when user is filing belated and applies correct filing type with late fee (234F) computation. |
| Section 139(5) — Revised return | System supports revised returns within the statutory window. Cross-validates against previously filed data. |
| Section 44AD/44ADA — Presumptive taxation | System identifies eligibility and applies presumptive scheme with correct income declaration rate (6%/8% or 50%). |
| Section 115BAC — New tax regime | System compares both regimes and recommends the optimal one. Compliant with section 115BAC(6) requirements for regime selection. |
| Chapter VI-A deductions (80C through 80U) | System validates all deduction claims. Does not fabricate deductions without evidence. Provides supporting section reference. |
| Section 87A — Rebate | Automatically computed for eligible taxpayers (net income threshold). |
| Section 192 — TDS on salary | Cross-validates TDS from Form 16 against 26AS/AIS. |
| Section 194 — TDS on other payments | Matches TDS across all documents. Flags discrepancies. |
| Section 234A/B/C — Interest | Computes interest on default, advance tax shortfall, and late payment according to prescribed rates. |
| Section 234F — Late filing fee | Computes fee based on filing date. |
| Rule 21AA — Form 12BAA | Supports New Regime declaration format. |

### 5.2 ITD E-Return Intermediary (ERI) Guidelines

| Guideline | Compliance |
|-----------|-----------|
| ERI registration and licensing | TaxStox operates as an ERI or partners with an ERI for direct submission (V2). For V1, generates ITR JSON for manual ITD portal upload. |
| Data security standards | AES-256-GCM for all data at rest, TLS 1.3 for all data in transit. Document processing in isolated environment. |
| Audit trail requirements | Complete audit trail of all data processed. Timestamped, user-attributed, tamper-evident. |
| ITR schema compliance | Generated JSON validated against ITD published XSD schemas before delivery. Schema version managed per assessment year. |
| API rate limiting | If direct ITD API integration in V2, respects ITD rate limits and throttling requirements. |
| Taxpayer consent | Explicit consent obtained before data processing. Consent recorded in audit trail. Withdrawal mechanism available. |
| Data localization | All data stored and processed within India (AWS ap-south-1). |
| Grievance mechanism | Grievance officer details published. 30-day resolution mandate. |

### 5.3 Digital Personal Data Protection (DPDP) Act, 2023

| Requirement | Compliance |
|-------------|-----------|
| Consent | Explicit, informed, specific consent obtained for each processing purpose. Consent record maintained. Withdrawal mechanism equally easy as giving consent. |
| Notice | Privacy notice at point of collection. Specifies purpose, data categories, retention, rights, grievance mechanism. Available in English and Hindi. |
| Data fiduciary obligations | TaxStox acts as Data Fiduciary. All obligations under Chapter II fulfilled. |
| Data processor agreements | All vendors (cloud, LLM, SMS, email) bound by DPDP-compliant DPAs. |
| Data localization | All personal data stored within India. No cross-border transfer of personal data except as permitted under DPDP Act. |
| Data breach notification | DPA, affected data principals notified within 72 hours of breach discovery. |
| Data Protection Officer | DPO appointed. Contact details published. |
| Consent manager (P2) | For V2: integration with proposed consent management framework per Section 6. |
| Significant Data Fiduciary | If applicable, additional obligations under Section 10 fulfilled: Data Protection Impact Assessment, audit, data audit. |

### 5.4 ISO 27001:2022 Compliance

| Domain | Controls Implemented |
|--------|---------------------|
| A.5 — Information security policies | Comprehensive ISMS policy. Annual review. Board-level oversight. |
| A.6 — Organization of information security | CISO appointed. Security team with defined roles. Cross-functional security committee. |
| A.7 — Human resource security | Background checks for all employees. Security training. Contractor agreements. |
| A.8 — Asset management | Asset inventory. Classification (Confidential/Internal/Public). Handling procedures. |
| A.9 — Access control | RBAC. JIT access for admin. Quarterly access review. MFA for all privileged access. |
| A.10 — Cryptography | Encryption policy. Key management. Algorithm standards (AES-256, TLS 1.3, Argon2id). |
| A.11 — Physical security | Data center security via cloud provider (AWS). Office security. Device encryption. |
| A.12 — Operations security | Change management. Capacity management. Malware protection. Backup. Logging. |
| A.13 — Communications security | Network security. TLS. mTLS. Segmentation. |
| A.14 — System acquisition, development | Secure SDLC. Code review. Security testing. Change management. |
| A.15 — Supplier relationships | Vendor assessment. DPA. SLA monitoring. Vendor audit rights. |
| A.16 — Incident management | Incident response plan. Severity matrix. Escalation. Post-mortem. |
| A.17 — Business continuity | DR plan (section 2.4). BCP. Annual drills. |
| A.18 — Compliance | Legal/regulatory compliance. IPR protection. Records retention. Privacy. |

### 5.5 SOC 2 Type II Compliance

| Trust Service Criteria | Implementation |
|-----------------------|---------------|
| Security | All security controls from Section 3. Penetration testing (annual). Vulnerability scanning (continuous). WAF, IDS/IPS. |
| Availability | Uptime targets (Section 2.1). Monitoring, alerting, DR. Incident response. |
| Processing Integrity | Processing is complete, valid, accurate, timely, and authorized. Validation engine ensures data correctness. |
| Confidentiality | AES-256 encryption. Access controls. Data classification. Confidentiality agreements. |
| Privacy | Privacy controls from Section 4. DPDP compliance. PIA. Notice and consent. |

### 5.6 Additional Compliance Frameworks

| Framework | Applicability | Implementation |
|-----------|---------------|----------------|
| PCI DSS | If payment card data processed (payment gateway integration) | Out of scope for V1. If payment added, PCI DSS Level 4 compliance. |
| IT Act 2000 (Section 43A) | Compensation for failure to protect data | Insurance coverage for data breach liability. |
| IT (Reasonable Security Practices) Rules 2011 | Security practices for body corporate | Implemented as part of ISMS. |
| SEBI (LODR) Regulations | If platform processes capital market data for listed companies | Not directly applicable (user-facing tax platform). SEBI data used only for capital gains computation. |
| RBI Guidelines on Digital Lending | If linking to any loan/tax-saver investment products | Out of scope for V1. Applicable if recommendation engine suggests tax-saving investments. |
| ICDS (Income Computation and Disclosure Standards) | For business income computation | Applicable for ITR-3/ITR-4 filing. Computation engine must comply with ICDS. |
| Aadhaar Act 2016 | If Aadhaar used for e-verification | Aadhaar never stored. Used only for OTP-based e-verification (if user opts in). Temporary token discarded after verification. |

---

## 6. Scalability Requirements

### 6.1 Traffic Profile & Seasonality

TaxStox experiences extreme seasonal traffic variation aligned with the Indian financial year cycle.

| Period | Traffic Level | Relative to Baseline | Description |
|--------|--------------|---------------------|-------------|
| April — June | Low | 0.5x | Post-deadline lull |
| July 1 — July 25 | Extreme Peak | 20x | Deadline rush |
| July 26 — July 31 | Critical Peak | 50x | Final days before deadline |
| August — November | Low-Medium | 0.5x — 1x | Normal operation |
| December | Medium | 2x | Early planning (next year) |
| January — March | Medium-High | 3x — 5x | Advance tax planning, early filing |

**Key Traffic Assumptions:**
- Baseline DAU: 1,000 active users
- Peak DAU (July 31): 50,000 active users
- Filing sessions started per day (peak): 100,000
- Upload throughput peak (July 31): 5,000 uploads/minute
- Concurrent LLM calls (peak): 500+
- Peak bandwidth: 10 Gbps (document uploads)
- Peak DB writes: 5,000 writes/second

### 6.2 Horizontal Scaling Strategy

**Application Layer:**
| Component | Scaling Trigger | Min Instances | Max Instances | Scaling Metric |
|-----------|----------------|---------------|---------------|----------------|
| Web frontend (Next.js) | CPU > 60% or request latency > 500ms | 3 (multi-AZ) | 30 | Request count + CPU |
| API server | CPU > 60% or latency > 300ms | 3 (multi-AZ) | 30 | Request count + CPU |
| Document processing workers | Queue depth > 100 | 2 | 20 | Queue depth |
| AI orchestration server | Queue depth > 50 or latency > 2s | 2 | 15 | Queue depth + latency |
| LLM proxy/inference | Tokens per second nearing capacity | 2 | 10 | Token throughput |
| WebSocket server | Concurrent connections > 2000 | 2 | 8 | Connection count |

**Data Layer:**
| Component | Scaling Strategy |
|-----------|-----------------|
| PostgreSQL (primary) | Vertical scale up (compute-intensive during peak). Read replicas for reporting queries. |
| PostgreSQL (read replicas) | 2 replicas during normal, 8 during peak. |
| Redis (cache + session) | Cluster mode with sharding. 3 shards normal, 10 during peak. |
| Redis (rate limiting) | Standalone, auto-failover. |
| S3 | Scales automatically. Lifecycle policies manage document expiry. |
| Queue (document processing) | FIFO queue with auto-scaling consumers. |

### 6.3 Auto-scaling Configuration

| Policy | Configuration |
|--------|--------------|
| Step scaling (CPU) | Add 2 instances when CPU > 60% for 3 minutes. Remove 1 when CPU < 30% for 10 minutes. |
| Step scaling (queue) | Add 3 workers when queue depth > 500. Remove 1 when queue depth < 100. |
| Scheduled scaling (July) | Scale to 80% of max on July 1. Scale to 100% on July 25. |
| Scheduled scaling (deadline week) | Max instances with no scale-in from July 25 to August 1. |
| Cooldown period | 5 minutes between scale-out actions. 10 minutes between scale-in actions. |
| Surge protection | Hard limit on concurrent sessions per instance. New sessions queued with estimated wait time displayed. |

### 6.4 Database Scaling

| Operation | Normal | Peak | Strategy |
|-----------|--------|------|----------|
| Connections | 100 | 500 | Connection pooling (PgBouncer) |
| Read throughput | 2,000 qps | 20,000 qps | Read replicas (2 -> 8) |
| Write throughput | 500 qps | 5,000 qps | Vertical scale (db.r6g.2xlarge -> db.r6g.8xlarge) |
| Storage | 50 GB | 200 GB | Auto-scaling storage (up to 16TB) |
| Backup window | 1 hour | 30 minutes | Increased frequency during peak |

### 6.5 LLM Scaling

| Strategy | Implementation |
|----------|---------------|
| Model tiering | Complex extraction tasks: powerful model (Claude Opus). Simple classification: fast model (Claude Haiku). Routing via model router. |
| Request batching | Non-urgent LLM calls (e.g., deduction discovery) batched for throughput efficiency. |
| Semantic caching | Cache frequently asked questions and common extraction patterns. Estimated 40% cache hit rate. |
| Context window optimization | Minimize prompt size by retrieving only relevant context. 80% reduction in context tokens vs naive approach. |
| Fallback model | If primary model unavailable, fall back to faster/cheaper model with reduced capability. Degradation mode with clear user communication. |
| Token budget per session | Hard limit of 50,000 output tokens per filing session. Monitoring and alerts on high-consumption sessions. |
| Pre-warming | On July scheduler trigger, pre-warm LLM connections to reduce cold-start latency. |

### 6.6 Content Delivery & Static Assets

| Asset | CDN Strategy | Cache Control |
|-------|-------------|---------------|
| JS/CSS bundles | CDN (CloudFront/Akamai) | Immutable caching (1 year) |
| Fonts (Hanken Grotesk, Inter, JetBrains Mono) | CDN | 1 year |
| Images/icons | CDN with WebP conversion | 1 month |
| Landing page (SSR) | CDN with TTL | 5 minutes |
| Public documentation | CDN | 1 day |
| User-uploaded documents | Origin (S3) only | No CDN caching (security) |

---

## 7. Reliability Requirements

### 7.1 Error Budgets

| Service | SLO | Error Budget (Monthly) | Error Budget (Quarterly) |
|---------|-----|----------------------|-------------------------|
| Core filing flow | 99.9% | 43.2 minutes downtime | 2.16 hours |
| AI/chat services | 99.5% | 3.6 hours downtime | 10.8 hours |
| Document processing | 99.5% | 3.6 hours degradation | 10.8 hours |
| API layer | 99.9% | 43.2 minutes | 2.16 hours |
| Database | 99.95% | 21.6 minutes | 1.08 hours |
| Overall (peak season) | 99.95% | 21.6 minutes | 1.08 hours |

**Error Budget Policy:**
- When error budget consumption > 50%: deployments slow down, require manual approval
- When error budget consumption > 75%: all deployments frozen except critical security patches
- When error budget consumption > 90%: incident response activated, full retrospective required
- Unused error budget: can be "spent" on experimentation and faster deployments

### 7.2 Graceful Degradation

**Degradation Modes:**

| Mode | When | What Works | What Degrades | User Experience |
|------|------|------------|---------------|-----------------|
| AI-Light | LLM API unavailable or high latency | Document upload, manual data entry, tax computation, JSON generation | AI extraction, AI chat, deduction discovery, regime optimization | "Smart features temporarily unavailable. You can still file manually." Banner shown. |
| Document-Light | Document processing pipeline overloaded | Manual data entry, JSON generation | Document upload, extraction, classification | "Upload is slower than usual. You can enter data manually." Enhanced manual form. |
| Offline Mode | Network interruption on client side | All cached operations | Server-dependent operations | "You're offline. We'll save your progress and resume when connected." Local-first state saves. |
| Read-Only | Database primary unavailable | Dashboard, history viewing, JSON download | New filings, edits, saves | "New filings temporarily disabled. Your data is safe." |
| Queue Backup | Document processing queue full | User interface, data entry | Document processing delays | "Documents are queued for processing. Estimated wait: X minutes." Real-time queue position. |

**Degradation Implementation:**
1. Circuit breakers on all external dependencies (LLM API, ITD API, cloud services)
2. Feature flags to disable specific AI capabilities independently
3. Progressive enhancement: core filing always works, AI features are value-add
4. Monitoring triggers automatic degradation when P99 latency exceeds 2x threshold for 5 minutes
5. Manual override: operations team can trigger degradation for planned maintenance

### 7.3 Fault Tolerance

| Failure Scenario | Tolerance Mechanism | Recovery |
|-----------------|-------------------|----------|
| Single application instance failure | Load balancer health check removes instance | Auto-scaling group replaces within 2 minutes |
| Single AZ failure | Multi-AZ deployment (min 2 AZs) | Traffic routed to remaining AZ(s) |
| Database primary failure | Automatic failover to replica | RDS Multi-AZ failover < 2 minutes |
| Redis primary failure | Redis Cluster auto-failover | < 30 seconds |
| Queue service failure | SQS cross-region replication | Manual failover if > 5 minutes |
| LLM API failure | Circuit breaker + fallback model | Automatic after 3 consecutive failures |
| CDN failure | Origin serving with cache | DNS failover to alternate CDN |
| S3 failure | Cross-region replication | Failover to DR region |
| DNS failure | Multiple DNS providers | TTL-based convergence |

### 7.4 Retry & Backoff Strategy

| Operation | Max Retries | Initial Backoff | Backoff Multiplier | Max Backoff | Retry on Status |
|-----------|-------------|-----------------|-------------------|-------------|-----------------|
| LLM API call | 3 | 1 second | 2x (exponential) | 30 seconds | 429, 500, 502, 503, 504 |
| Database write | 2 | 100ms | 2x | 1 second | Deadlock, serialization |
| Document upload (S3) | 3 | 500ms | 2x | 10 seconds | Network error, 5xx |
| ITD API call | 2 | 5 seconds | 2x | 30 seconds | 429, 503 |
| Email sending | 3 | 1 minute | 4x | 1 hour | Any failure |
| SMS sending | 3 | 30 seconds | 2x | 5 minutes | Any failure |
| OCR processing | 2 | 2 seconds | 3x | 30 seconds | Processing error |

**Jitter:** All retry backoffs include ±25% random jitter to prevent thundering herd.
**Idempotency:** All retriable operations have idempotency keys. Duplicate requests (exact same idempotency key) return the original response without executing the operation again.

### 7.5 Data Durability

| Data | Durability Guarantee | Mechanism |
|------|---------------------|-----------|
| ITR JSON (completed) | 99.999999999% (11 nines) | S3 Standard + CRR to DR region |
| User accounts | 99.999999999% | PostgreSQL with Multi-AZ + daily backups + WAL archiving |
| Audit logs | Append-only, immutable | Write-once-read-many (WORM) S3 bucket |
| Uploaded documents | 99.999999999% | S3 Standard |
| In-progress filings | 99.99% | Event sourcing with stream persistence |

### 7.6 Monitoring & Alerting for Reliability

| Metric | Threshold | Alert Severity | Action |
|--------|-----------|----------------|--------|
| Overall session error rate | > 1% | High | Page engineering on-call |
| Document processing error rate | > 3% | High | Page ML/document team |
| API P99 latency | > 3 seconds | Medium | Investigate performance |
| API error rate | > 0.5% | High | Page backend team |
| LLM API error rate | > 5% | Medium | Check LLM provider status |
| Queue depth growth | > 100/minute sustained | Medium | Scale workers |
| Database connections | > 80% of max | Critical | Scale or optimize connections |
| Disk space | > 85% | Critical | Immediate cleanup or scale |
| Memory utilization | > 90% | Critical | Restart or scale |
| SSL certificate expiry | < 30 days | Medium | Renew certificate |
| Failed health checks | 3 consecutive | High | Replace instance |

---

## 8. Maintainability Requirements

### 8.1 Modular Architecture Principles

| Principle | Implementation |
|-----------|---------------|
| Separation of concerns | System decomposed into distinct modules: document ingestion, extraction, validation, conversation, computation, generation, compliance. Each module has defined boundaries via API contracts. |
| Single responsibility | Each microservice/agent handles exactly one domain concern. The Tax Rule Engine only computes tax. The Extraction Agent only extracts entities. The Conversation Agent only manages dialogue. |
| Loose coupling | Inter-module communication via message queues (SQS) and event bus (EventBridge). No direct service-to-service calls except through API gateway. Schema versioning ensures independent deployability. |
| High cohesion | Related functionality grouped within the same module. All deduction-related logic (discovery, validation, claiming) within the Tax Optimization Engine. |
| Domain-driven design | Modules aligned to business domains: Document Intelligence, Tax Computation, Compliance, User Management. Ubiquitous language maintained across all modules (e.g., "deduction" means the same thing everywhere). |

### 8.2 Documentation Standards

| Documentation Type | Location | Standard | Update Trigger |
|-------------------|----------|----------|----------------|
| API contracts | OpenAPI 3.1 specs in `/api/` | MUST include: endpoint, method, request/response schemas, error codes, rate limits, auth | Schema change, new endpoint |
| Architecture decisions | ADRs in `/docs/adr/` | MUST include: context, decision, consequences, alternatives considered | New architectural decision |
| Database schema | `/docs/DATA_MODEL.md` + migration files | MUST include: table descriptions, column types, indexes, foreign keys, migration strategy | Schema change |
| Infrastructure as Code | Terraform in `/infra/` | MUST include: resource descriptions, purpose comments, output values | Infrastructure change |
| Runbooks | `/docs/runbooks/` | MUST include: symptom, diagnosis steps, resolution steps, verification | New incident pattern |
| Code documentation | In-code docstrings | Functions: purpose, params, return, exceptions. Modules: purpose, key classes. No "obvious" comments. | Code change |
| README per service | `apps/<service>/README.md` | MUST include: purpose, setup, local dev, tests, deployment, health check | Service change |
| API changelog | `CHANGELOG.md` | MUST include: version, date, changes (added/changed/deprecated/removed), migration guide | API change |

### 8.3 Code Quality Standards

| Metric | Target | Enforcement |
|--------|--------|-------------|
| Test coverage (unit) | > 85% | CI pipeline fails below 80% |
| Test coverage (integration) | > 70% | CI pipeline fails below 60% |
| Code duplication | < 5% | SonarQube gate |
| Cyclomatic complexity | < 15 per function | ESLint/SonarQube |
| Maximum function length | < 60 lines | ESLint |
| Maximum file length | < 400 lines | ESLint |
| Comment density | 10-20% | SonarQube |
| Documentation coverage (API) | 100% | OpenAPI validator |
| Vulnerability density | Zero critical/high | Snyk/Trivy |
| Dependency freshness | No deps > 6 months outdated | Renovate bot |
| Formatting | Auto-formatted | Prettier/Black/Rustfmt |

### 8.4 Deployment & Release Management

| Practice | Standard |
|----------|----------|
| CI/CD pipeline | GitHub Actions. Build -> Test -> Security Scan -> Deploy to Staging -> Integration Tests -> Deploy to Production (rolling). |
| Branch strategy | Trunk-based development. Short-lived feature branches (max 2 days). Main branch always deployable. |
| Release cadence | Weekly during normal periods. Bi-weekly during peak. Only critical fixes during deadline week. |
| Deployment strategy | Rolling update with 20% step increments. Health check between each step. Auto-rollback on failure. |
| Feature flags | All new features behind feature flags. Gradual rollout: 1% -> 10% -> 50% -> 100%. |
| Database migrations | Forward-only migrations. Backward-compatible for 2 releases. Rollback via forward migration (not revert). |
| Versioning | Semantic versioning for APIs. Git tag for releases. Docker image tag matches Git tag. |
| Blue-green deployment | For critical services (API, computation engine). Full environment swap with traffic switch. |
| Canary deployment | For AI model changes. Route 5% traffic to new model for 1 hour, then 20%, then full. |

### 8.5 Configuration Management

| Configuration Type | Storage | Change Process |
|-------------------|---------|---------------|
| Environment variables | AWS Parameter Store / Secrets Manager | Terraform-managed. PR + apply. |
| Feature flags | LaunchDarkly / AppConfig | UI-based, no deployment needed. |
| Tax rules | Git repository (JSON/YAML) | PR review + automated tests. Deployed via CI. |
| AI prompts | Git repository (Markdown) | PR review + prompt evaluation suite. |
| Rate limits | Terraform + Parameter Store | Infrastructure change. |
| UI content | Localization files (JSON) | PR review. |

---

## 9. Usability Requirements

### 9.1 Accessibility (WCAG 2.1 AA)

| Guideline | Requirement | Implementation |
|-----------|-------------|----------------|
| Perceivable (A/AA) | All content perceivable through at least one sense. | Text alternatives for all non-text content. Captions for video. Content can be presented without loss of information when simplified. |
| Operable (A/AA) | All UI operable through multiple input methods. | Full keyboard navigation. No keyboard traps. Focus indicators visible (3px outline, high contrast). Focus order follows visual order. Touch targets at least 44x44px. Enough time to read/use content (adjustable timeouts). |
| Understandable (A/AA) | Content and UI understandable. | English/Hindi language specified on page. Consistent navigation across pages. Input assistance: clear labels, error suggestions, undo options. |
| Robust (A/AA) | Content compatible with current and future user agents. | Proper HTML semantics. ARIA landmarks. ARIA labels where native semantics insufficient. Valid HTML. |

**Specific Requirements:**
| Item | Requirement |
|------|-------------|
| Color contrast | Minimum 4.5:1 for normal text, 3:1 for large text (18px+ or 14px+ bold). Design system colors validated against this. |
| Focus indicators | Visible focus ring (3px solid `primary` color, offset 2px) on all interactive elements. |
| Screen reader compatibility | All forms have proper labels, fieldset/legend for groups, error messages linked to fields via aria-describedby. |
| Keyboard navigation | Tab order follows visual order. No tab traps. All interactions accessible via keyboard. |
| Zoom and scaling | Page functional at 200% zoom. Content not cut off or overlapping. |
| Error identification | Error described in text. Input in error identified. Suggestion provided. |
| Headings | Proper heading hierarchy (h1 -> h2 -> h3). No skipping levels. |
| Alternative text | All informative images have alt text. Decorative images have alt="". |
| Skip navigation | "Skip to main content" link as first focusable element. |
| Reduced motion | `prefers-reduced-motion` respected. Animations disabled or reduced. |

### 9.2 Mobile Responsiveness

| Breakpoint | Target Devices | Layout Strategy |
|------------|---------------|-----------------|
| < 640px (Mobile) | Phones (portrait) | Single column, full-width cards, stacked navigation, bottom sheet for filters/modals. |
| 640px — 1024px (Tablet) | Phones (landscape), tablets | Two-column where appropriate, side panels, condensed data tables. |
| 1024px+ (Desktop) | Desktop, laptops | Full 12-column grid, sidebars, complex data tables, multi-panel layouts. |

**Design System Compliance:** Per the design system in DESIGN.md, on mobile display sizes are reduced to prevent currency values wrapping. The system uses a single-column fluid layout on mobile with 16px side margins. Tabular data switches to "Card-based List" views on small screens.

**Mobile-Specific Requirements:**
| Requirement | Standard |
|-------------|----------|
| Touch targets | Minimum 44x44 px (recommended 48x48) |
| Input fields | Proper input types (tel, email, number, text) for appropriate keyboard |
| File upload | Camera capture option for document upload (plus gallery selection) |
| Scrolling | Infinite scroll not used for critical data. Pagination or "load more" for history. |
| Navigation | Bottom navigation bar for key sections on mobile |
| Data tables | Horizontal scroll allowed for wide tables with sticky first column |
| Gestures | Swipe for common actions (delete, archive). Pinch-to-zoom for document preview. |
| Performance | Same performance targets as desktop (Section 1). No degradation for mobile. |

### 9.3 Multi-Language Support

**V1 Languages:**
| Language | Support Level | Notes |
|----------|--------------|-------|
| English | Full | Default UI language |
| Hindi | Full | Complete translation of all UI, help text, error messages |
| English + Hindi (Hinglish) | Input support | Users can type in mixed language; AI conversation agent trained to understand |

**V2+ Languages (Planned):**
- Tamil
- Telugu
- Kannada
- Malayalam
- Marathi
- Gujarati
- Bengali
- Punjabi
- Odia
- Assamese

**Language Requirements:**
| Aspect | Requirement |
|--------|-------------|
| UI text | All static UI text from localization files. No hardcoded strings. |
| RTL support | Not required for Indian languages (all LTR), but architecture should not preclude RTL for future. |
| Number formatting | Indian number system (lakh, crore) for financial displays. User preference option for international format. |
| Date formats | DD/MM/YYYY or DD-Month-YYYY based on language. |
| Currency formatting | ₹ symbol prefix. INR code in spaces. |
| AI conversation | AI agent detects and responds in user's language. Mixed-language input understood. |
| Document parsing | OCR and extraction support for English + Hindi text in documents. Numbers in any Indian language digit format parsed. |

### 9.4 Error Message Standards

| Element | Standard |
|---------|----------|
| Tone | Helpful, not alarming. Use "we couldn't process this" not "error occurred." |
| Content | What happened, why, what user can do, how to get help. |
| Placement | Inline validation errors below the field. Toast for system errors. Page-level for critical failures. |
| Persistence | Inline errors persist until corrected. Toast errors auto-dismiss after 8 seconds. Page errors persist until resolved. |
| Actionability | Every error message includes a clear next step. "Try again" button for transient errors. Contact support link for persistent errors. |
| Accessibility | Error messages linked to form fields via aria-describedby. Screen reader announcement on error. |
| Logging | Every error message has a unique error code for support reference. |

**Error Message Templates:**
| Scenario | Message Pattern |
|----------|----------------|
| Validation error | "Please enter a valid [field name]. [Hint about correct format]." |
| System error | "We hit a snag processing your [operation]. Your data is safe. Please try again. (Error: TAX-XXXX)" |
| Upload error | "We couldn't process [filename]. [Reason — e.g., password protected, too large, corrupted]. [Action]." |
| Network error | "Connection lost. Your progress is saved. We'll resume when you're back online." |
| Session timeout | "For your security, your session timed out due to inactivity. Your progress is saved. Please log in again." |

### 9.5 Onboarding & Learnability

| Requirement | Implementation |
|-------------|----------------|
| First-time user guidance | Welcome wizard for first filing. Optional walkthrough highlights key features. Tooltips on complex concepts. |
| Progressive disclosure | Advanced features (regime comparison details, audit trail) hidden behind expandable sections. Core flow: upload -> review -> download shown prominently. |
| Contextual help | "Why am I being asked this?" link on every wizard question. Opens tooltip with plain-English explanation. |
| Tax terminology glossary | Searchable glossary of tax terms. Accessible from anywhere via ? icon in header. Terms explained in plain language with examples. |
| Undo/redo | All user actions reversible. "Back" in wizard preserves previous answers. Deleted documents recoverable within session. |
| Saving progress | Auto-save after every wizard step. Session resumable from last completed step. "You're X% done" progress indicator always visible. |

---

## 10. Interoperability Requirements

### 10.1 ITD Portal Compatibility

| Interface | Compatibility Requirement | Notes |
|-----------|-------------------------|-------|
| ITR JSON schema | 100% compliant with ITD published schema for the assessment year | Schema validated before download. Version-specific schema per AY. |
| ITR XML (legacy) | Not supported for V1 | ITD now primary accepts JSON format. XML considered deprecated. |
| Form 16 format | Part A and Part B of Form 16 (both old and new format). Also Form 16 for non-salaried. | System detects Form 16 version and adapts extraction accordingly. |
| 26AS / AIS format | AIS (Annual Information Statement) JSON/PDF downloaded from ITD portal. Also supports TIS (Taxpayer Information Summary). | Multiple format support. System identifies format from content. |
| ITD e-filing portal | No direct API integration for V1 | User manually uploads generated JSON. Post-export instructions generated per ITR type. |
| ITD ERI API (V2) | For direct filing submission | Integration planned for V2. Must comply with ERI technical specifications. |

### 10.2 JSON Schema Versioning

| Requirement | Implementation |
|-------------|----------------|
| Schema versioning | Every ITR JSON schema versioned with MAJOR.MINOR format. MINOR changes are backward-compatible. MAJOR changes require migration. |
| Assessment Year mapping | Schema per AY (e.g., `itr-1-ay-2025-26-v2.json`). System automatically selects correct schema based on AY. |
| Schema registry | Central registry of all supported schemas. Registry includes: schema name, version, AY, validation rules, effective date, deprecated date. |
| Backward compatibility | Generated JSON from earlier schema version accepted during transition period (2 months from new schema release). |
| Deprecation policy | Schema deprecation announced 6 months in advance. Deprecated schemas still accepted but logged. |
| Custom JSON extensions | TaxStox-specific metadata in JSON (e.g., `_taxstoxAuditId`, `_taxstoxVersion`) namespaced with underscore prefix. ITD portal ignores unknown fields. |

### 10.3 API Compatibility

| API | Standard | Versioning | Deprecation |
|-----|----------|------------|-------------|
| Public REST APIs | OpenAPI 3.1, JSON | URL versioning (`/api/v1/...`). | 6-month deprecation notice. Version header required. |
| Internal service APIs | gRPC with protobuf | Protobuf package versioning. | 3-month internal deprecation. |
| GraphQL (future) | Apollo Federation | Schema versioning via directives. | N/A (V2). |
| WebSocket events | JSON over WSS | Event type versioning. | 3-month deprecation. |

### 10.4 External System Integration

| System | Integration Method | Data Format | Frequency | Dependency |
|--------|-------------------|-------------|-----------|------------|
| ITD AIS portal | PDF download (manual user action) | PDF/JSON | Per filing session | User action |
| ITD e-filing portal | Generated JSON upload (manual) | JSON | Per filing session | User action |
| PAN verification (NSDL) | API (planned V2) | JSON | Per registration | NSDL API availability |
| Aadhaar e-verification | UIDAI API (planned V2) | XML/JSON | Per verification | UIDAI API |
| Payment gateway (V2) | REST API | JSON | Per payment | Payment provider |
| Email delivery | SES/SendGrid API | SMTP/API | Per notification | Email provider |
| SMS delivery | AWS SNS / Twilio | API | Per notification | SMS provider |
| CA/bulk filing portal | Custom API (V2) | JSON | Per batch | Internal |

### 10.5 Data Exchange Formats

| Format | Usage | Validation |
|--------|-------|------------|
| ITR JSON (ITD format) | Final output for upload | XSD/JSON Schema validation |
| TaxStox Session JSON | Internal transfer of filing state | Internal schema |
| Extracted Entities JSON | Between extraction and validation pipeline | Internal schema |
| Audit Event JSON | Audit trail entries | Internal schema |
| Computation Result JSON | Between TRE and frontend | Internal schema |
| AIS JSON (ITD format) | Import from ITD portal | ITD schema |
| Form 16 PDF | Input document | Content-based validation |
| CSV (for CA bulk import, V2) | Input for batch filing | Header validation |
| PDF/A (long-term archive) | Archival format | PDF/A compliance |

---

## 11. Data Integrity Requirements

### 11.1 Cryptographic Verification

| Integrity Check | Where Applied | Method |
|-----------------|---------------|--------|
| ITR JSON integrity | Generated JSON file | SHA-256 hash embedded in JSON metadata field. Hash also stored in audit trail. User can verify hash independently. |
| Document authenticity | Uploaded documents | SHA-256 content hash computed on upload. Duplicate detection by content hash. Tampering detection by comparing with user-provided hash (if available). |
| Audit trail integrity | All audit entries | Hash chain: each audit entry contains SHA-256 hash of previous entry. Tampering detectable by recomputing chain. |
| Data at rest integrity | Database records | Each sensitive record has a checksum column. Periodic batch verification. |
| API request integrity | All state-changing API calls | HMAC-SHA256 signature in request header. Prevents request tampering. |
| Session data integrity | Session tokens | JWT with RS256 signature. Tampered tokens rejected. |

### 11.2 Audit Trails

**What is Audited:**
| Category | Events |
|----------|--------|
| Authentication | Login, logout, failed login, OTP request, password change, session expiry |
| Data access | Document view, extraction result view, JSON download, profile data access |
| Data modification | Profile update, data entry/edit, deduction add/remove, regime selection |
| Filing lifecycle | Filing start, step completion, JSON generation, JSON download, filing amendment |
| Document operations | Upload, classify, extract, delete, purge |
| AI decisions | Extraction result, validation finding, deduction discovery, regime recommendation |
| Administrative | Role change, permission change, data access by support, account actions |
| Compliance | Consent given/withdrawn, DSAR request, data deletion, data export |
| Error events | System errors, validation errors, AI failures, API failures |

**Audit Record Structure:**
```json
{
  "auditId": "aud_8f7a3b2c1d9e4f5a",
  "timestamp": "2026-06-29T14:30:00Z",
  "eventType": "filing.json_generated",
  "userId": "usr_sha256:abc123...",
  "panHash": "sha256:def456...",
  "sessionId": "sess_7a8b9c0d1e2f",
  "dataRef": "json/ay2025-26/itr-1/usr_sha256.../1678901234.json",
  "action": "create",
  "before": null,
  "after": {
    "taxAmount": 45000,
    "refundAmount": 12000,
    "regime": "new",
    "itrType": "ITR-1"
  },
  "sourceIp": "masked:103.x.x.x",
  "userAgent": "Mozilla/5.0...",
  "integrityChain": {
    "previousHash": "sha256:abc...",
    "hash": "sha256:def..."
  },
  "metadata": {
    "version": "1.0",
    "environment": "production"
  }
}
```

**Audit Requirements:**
| Requirement | Standard |
|-------------|----------|
| Immutability | Audit logs stored in append-only WORM storage (S3 Object Lock). No edits or deletes. |
| Retention | 7 years minimum. After 7 years, destroyed with verified deletion. |
| Accessibility | Searchable by user, session, event type, timeframe. Access restricted to compliance team. |
| Tamper evidence | Hash chain ensures tampering is detectable. Daily batch verification. |
| Real-time alerting | Suspicious audit events trigger immediate alert (e.g., multiple failed logins, unusual data access patterns). |
| Export | Audit logs exportable in CSV/JSON format for compliance reporting. |

### 11.3 Reconciliation & Verification

| Verification | Method | Frequency |
|-------------|--------|-----------|
| Internal consistency | Cross-validate extracted data against source documents for random sample | Weekly |
| Computation accuracy | Compare TRE results against manual computation for test cases | Every deployment |
| JSON schema compliance | Validate all generated JSONs against ITD schema | Every generation |
| Audit chain integrity | Recompute hash chain from first entry | Daily |
| Data purge verification | Verify documents marked for deletion are actually deleted | Hourly |
| Backup integrity | Test restore from random backup | Monthly |
| Cross-document reconciliation | Compare Final ITR values vs. extracted values from all documents | Every filing |
| AIS reconciliation | Compare declared income vs. AIS-reported income | Every filing |

### 11.4 Fraud Detection

| Pattern | Detection Method | Action |
|---------|-----------------|--------|
| Duplicate PAN filings in same AY | Query existing records for same PAN hash | Warn user, block if duplicate confirmed |
| Income mismatch > 20% vs AIS | Cross-document validation | Flag for review, require explanation |
| Unusually large deductions (> 50% of income) | Statistical outlier detection | Flag for review, require documentation |
| Multiple accounts from same IP/device | Pattern analysis | Flag for manual review |
| Document reuse across users | Content hash comparison | Flag as potential fraud |
| Fictitious employer TAN | TAN verification against ITD database | Flag as invalid, require verification |
| Suspicious refund patterns | ML anomaly detection (V2) | Flag for manual review |

---

## 12. Regulatory Requirements

### 12.1 Income Tax Act & IT Rules

All IT Act requirements are covered in [Section 5.1](#51-income-tax-act-1961) above. Additional regulatory requirements:

| Regulation | Requirement |
|------------|-------------|
| IT Rules 1962 (particularly Schedule III) | Compliance with tax return form specifications |
| CBDT circulars on e-filing | Adherence to procedural requirements for electronic filing |
| Form ITR-V (acknowledgment) | Instructions for ITR-V verification (within 120 days of filing) |
| E-verification methods | Support for Aadhaar OTP, net banking, bank account, demat account, EVC |
| Offline utility compliance | Generated JSON must be compatible with ITD offline utility for re-import |

### 12.2 RBI Guidelines

| Guideline | Applicability | Compliance |
|-----------|---------------|------------|
| Foreign Exchange Management Act (FEMA) | For NRI users and foreign income reporting | System must correctly classify income under FEMA categories (NRE, NRO, FCNR accounts). Reporting of foreign assets under Schedule FA. |
| RBI Master Directions on Digital Payments | If TaxStox processes payments for premium features | Payment Aggregator authorization if applicable (V2). Data localization for payment data. 2-factor authentication for payments. |
| RBI outsourcing guidelines | If core tax processing activities are outsourced to any third party | Not applicable (self-operated). |
| Prevention of Money Laundering (PML) Rules, 2005 | Client due diligence for financial transactions | PAN verification mandatory for any paid transactions. Transaction monitoring for suspicious patterns. Record retention for 5 years. |

### 12.3 SEBI Requirements

| Requirement | Applicability | Compliance |
|-------------|---------------|------------|
| Capital gains classification | Long-term vs short-term as per SEBI categorization | System correctly classifies securities holding period based on SEBI/IT Act definitions (equity: >12 months LTCG, debt: >36 months for funds). |
| Securities transaction tax (STT) | STT computation for equity trades | STT paid considered in cost of acquisition. Correct regime applied for equity vs non-equity. |
| Mutual fund classification | Growth vs dividend, debt vs equity, listed vs unlisted | System uses correct tax treatment per SEBI mutual fund categorization. Grandfathering rules applied for pre-2018 investments. |
| Demat account integration (V2) | Auto-fetch holdings from CDSL/NSDL for capital gains computation | API integration with depositories for accurate cost basis. |
| Sections 111A, 112A compliance | Short-term capital gains on listed equity, LTCG on listed equity/mutual funds | System correctly applies Section 111A (15% STCG) and Section 112A (10% LTCG over Rs 1 lakh) with grandfathering provisions. |

### 12.4 Company Law & GST

| Regulation | Applicability | Status |
|------------|---------------|--------|
| Companies Act 2013 | If TaxStox operates as a private limited entity | Board-approved privacy policy. Annual compliance with data protection requirements. |
| GST Act 2017 | For TaxStox services (tax filing platform) | GST registration required. 18% GST on platform fees. GST invoicing for paid plans. |
| Professional Tax | State-specific PT for CA/TRP users | Not directly applicable. Users advised of state PT requirements. |

### 12.5 Information Technology Act, 2000

| Section | Requirement | Compliance |
|---------|-------------|------------|
| Section 43A | Compensation for failure to protect data | Data breach insurance of Rs 5 crore minimum. Security practices as per Section 3/4 of this document. |
| Section 66A (struck down — reference only) | Not applicable | Not implemented. |
| Section 66B-66F | Computer-related offences | IDS/IPS monitoring. Anomaly detection. Access logging. |
| Section 67-67C | Obscene content | Not applicable to tax documents. |
| Section 69 | Decryption of information | Authority to decrypt only with legal warrant. Logged and audited. |
| Section 70 | Protected systems | Critical infrastructure protection if designated as protected system. |
| Section 72 | Breach of confidentiality | All employees sign NDA. Confidentiality clause in all contracts. |
| Section 79 | Safe harbor for intermediaries | TaxStox qualifies as intermediary for user-generated content. Takedown mechanism for any illegal content. |
| IT (Reasonable Security Practices) Rules 2011 | ISO 27001 compliance | Certification targeted within 12 months of launch. |

### 12.6 Industry Standards & Certifications

| Standard/Certification | Target Timeline | Notes |
|------------------------|----------------|-------|
| ISO 27001:2022 | Within 12 months of V1 launch | Comprehensive ISMS required |
| SOC 2 Type II | Within 18 months of V1 launch | Trust Service Criteria: Security, Availability, Confidentiality, Privacy |
| DPDP Act compliance | At V1 launch (mandatory) | Based on law enactment timeline |
| ITD ERI certification | V2 (direct filing) | Required for direct ITR submission |
| PCI DSS (if applicable) | Before payment processing | Level 4 compliance |
| WCAG 2.1 AA | At V1 launch | Accessibility compliance |
| GDPR compliance (if serving EU NRIs) | V1 if EU users expected | Data processing addendum for NRIs in EU |

### 12.7 Regulatory Reporting

| Report | Frequency | Authority | Content |
|--------|-----------|-----------|---------|
| Data breach report | Within 72 hours of discovery | DPA, affected users | Nature, extent, impact, remediation |
| Audit report (SOC 2) | Annual | Customers (CAs, enterprises) | Controls effectiveness |
| ISO surveillance audit | Annual | Certifying body | ISMS compliance |
| Internal compliance report | Quarterly | Management | Regulatory changes, incidents, audit findings |
| DPDP compliance report | Annual | DPA | Data processing activities, DSARs, breaches |

---

## 13. Environmental & Operational Requirements

### 13.1 Infrastructure & Cloud Requirements

| Resource | Specification |
|----------|---------------|
| Cloud provider | AWS (Primary: ap-south-1 Mumbai, DR: ap-southeast-1 Singapore) |
| Compute | ECS Fargate (serverless containers) for stateless services. EC2 for GPU workloads (if self-hosted LLM). |
| Database | AWS RDS PostgreSQL 16 (Multi-AZ). Aurora for read replicas. |
| Cache | AWS ElastiCache Redis 7 (cluster mode). |
| Storage | AWS S3 (documents, backups, audit logs, generated JSONs). |
| CDN | AWS CloudFront with multi-region edge. |
| Queue | AWS SQS (FIFO for document processing, standard for events). |
| Monitoring | AWS CloudWatch + Grafana + PagerDuty. |
| Container registry | AWS ECR with vulnerability scanning. |
| Secrets | AWS Secrets Manager with automatic rotation. |
| DNS | AWS Route53 with health checks and failover. |

### 13.2 CI/CD Requirements

| Stage | Tools | Gates |
|-------|-------|-------|
| Code linting | ESLint, Prettier | Zero errors |
| Unit tests | Vitest/Jest/PyTest | > 80% coverage, zero failures |
| Integration tests | Playwright/Supertest | All critical paths pass |
| Security scan | Snyk/Trivy | Zero critical/high vulnerabilities |
| Build | Next.js build, Docker build | Successful build |
| Deploy to staging | GitHub Actions | All smoke tests pass |
| E2E tests | Playwright | All user journeys pass |
| Performance tests | k6/Artillery | All NFRs met |
| Deploy to production | GitHub Actions (manual approval) | All above + load test results |
| Post-deploy monitoring | 30-minute observation window | Error rate < 0.1%, no P99 regression |

### 13.3 Logging & Monitoring

| Log Type | Destination | Retention | Format |
|----------|-------------|-----------|--------|
| Application logs | CloudWatch Logs | 90 days | Structured JSON |
| API access logs | CloudWatch Logs / S3 | 1 year | Combined log format |
| Security events | CloudWatch Logs + SIEM (V2) | 7 years | CEF format |
| AI model logs | CloudWatch Logs (separate log group) | 90 days | Structured JSON |
| Document processing logs | CloudWatch Logs | 90 days | Structured JSON |
| Audit logs | S3 (WORM) | 7 years | Structured JSON |
| Infrastructure logs | CloudTrail + Config | 1 year | JSON (native) |

### 13.4 Dashboards & Alerts

| Dashboard | Metrics | Refresh | Audience |
|-----------|---------|---------|----------|
| Executive dashboard | DAU, filings completed, revenue, NPS, error rate | Live | Management |
| Operations dashboard | Latency P50/P95/P99, error rates, queue depths, DB connections | Real-time | Ops team |
| AI dashboard | LLM latency, token usage, cache hit rate, model error rate | Live | ML/AI team |
| Security dashboard | Auth failures, suspicious IPs, WAF blocks, vulnerability count | Real-time | Security team |
| Business dashboard | Filing volume, regime selection stats, deduction patterns, refund stats | Daily | Product team |

---

## 14. Cross-Cutting NFRs

### 14.1 Internationalization (i18n)

| Aspect | Requirement |
|--------|-------------|
| Locale detection | Automatic based on browser Accept-Language header. User override in settings. |
| Number formatting | Indian number system (lakh, crore) as default. User preference for international. |
| Currency formatting | ₹ symbol. INR for international contexts. |
| Date formatting | DD/MM/YYYY (default), configurable. |
| Timezone | All times in IST (UTC+5:30). User's local timezone displayed in tooltip. |
| Text direction | LTR only (Indian languages). Architecture should support RTL for future. |
| Pluralization | ICU MessageFormat for plural rules across languages. |

### 14.2 Observability

| Pillar | Tools | Key Metrics |
|--------|-------|-------------|
| Logging | Structured JSON logs -> CloudWatch -> Grafana | Log volume, error rate, error distribution |
| Metrics | CloudWatch custom metrics -> Grafana | Request rate, latency, error rate, saturation |
| Tracing | AWS X-Ray (or OpenTelemetry) | Service dependency latency, bottleneck identification |
| Alerting | CloudWatch Alarms -> PagerDuty | Mean time to detect (MTTD): < 5 minutes for critical |
| Dashboards | Grafana | Real-time + historical views per service |

### 14.3 Cost Optimization

| Area | Strategy | Target Savings |
|------|----------|----------------|
| LLM costs | Semantic caching, prompt compression, model tiering | 60% reduction vs naive approach |
| Compute | Auto-scaling, spot instances for batch processing, right-sizing | 40% reduction vs always-on |
| Storage | S3 lifecycle policies, data retention enforcement, compression | 50% reduction in storage costs |
| Database | Read replicas for reporting, connection pooling, query optimization | 30% reduction per query |
| CDN | High cache hit rate, compression, image optimization | 80% bandwidth reduction |
| Monitoring | Log sampling for non-critical logs, metric aggregation | 70% reduction in logging costs |

### 14.4 Ethical AI Requirements

| Principle | Implementation |
|-----------|---------------|
| Transparency | AI decisions explained in plain language. Confidence scores shown for extractions. |
| Fairness | No demographic bias in tax recommendations. Equally effective for all income levels. |
| Accountability | Every AI decision traceable to responsible agent and version. Human override always possible. |
| Privacy | AI agents operate on need-to-know basis. No training on user data without explicit consent. |
| Reliability | AI never fabricates financial data. "I don't know" preferred over hallucination. |
| Human oversight | Critical decisions (tax liability > Rs 10 lakh) require human review flag. |

---

## 15. NFR Verification & Testing

### 15.1 Performance Testing

| Test Type | Tools | Frequency | Success Criteria |
|-----------|-------|-----------|-----------------|
| Load testing | k6 / Artillery | Monthly, and before every peak season | All endpoints meet P95 latency targets under 2x normal load. |
| Stress testing | k6 / Artillery | Quarterly | System degrades gracefully at 5x normal load. No crash. |
| Endurance testing | k6 / Artillery | Quarterly | No memory leak or performance degradation over 24 hours at 2x load. |
| Spike testing | k6 / Artillery | Quarterly | System recovers within 5 minutes after 10x traffic spike. |
| Soak testing | k6 / Artillery | Annual (pre-deadline) | 48-hour sustained peak load with zero degradation. |

### 15.2 Availability Testing

| Test Type | Frequency | Success Criteria |
|-----------|-----------|-----------------|
| Failover test | Monthly | Database failover < 2 minutes. Application failover < 1 minute. |
| DR drill | Quarterly | Full region failover < 30 minutes. All critical services operational in DR region. |
| Backup restore test | Monthly | Random backup restored and verified for integrity within 4 hours. |
| Chaos engineering | Bi-annual | Random instance termination: no user impact, auto-recovery within 5 minutes. |

### 15.3 Security Testing

| Test Type | Frequency | Success Criteria |
|-----------|-----------|-----------------|
| SAST (Static Analysis) | Every commit | Zero critical/high findings. |
| DAST (Dynamic Analysis) | Weekly | Zero critical/high findings. |
| Dependency scan | Weekly | All critical CVEs patched within 48 hours. |
| Penetration test | Annual (external vendor) | Zero critical findings. All findings remediated within SLA. |
| Bug bounty | Continuous | Max 90-day fix window for reported issues. |
| Authentication test | Every release | All auth flows pass. Zero bypass vectors. |
| Authorization test | Every release | RBAC enforced. No privilege escalation. |

### 15.4 Accessibility Testing

| Test Type | Frequency | Success Criteria |
|-----------|-----------|-----------------|
| Automated accessibility audit | Every PR | Zero WCAG 2.1 AA violations. |
| Screen reader test | Every major release | All user flows navigable with NVDA/JAWS. |
| Keyboard navigation test | Every major release | All functionality accessible without mouse. |
| Color contrast verification | Every design change | All new colors meet 4.5:1 ratio. |
| User testing with disabled users | Annual | Feedback incorporated. |

### 15.5 NFR Compliance Matrix

| NFR Category | Verification Method | Acceptance Criteria |
|-------------|-------------------|-------------------|
| Performance (latency) | Automated load tests | All P95 targets met |
| Performance (throughput) | Automated load tests | All throughput targets met |
| Availability | Uptime monitoring | 99.9% (core) / 99.5% (AI) |
| Security | Penetration + SAST + DAST | Zero critical/high findings |
| Privacy | DPDP compliance audit | Full compliance |
| Scalability | Load + stress tests | Linear scaling up to 50x baseline |
| Reliability | Error budget monitoring | Error rate < SLO |
| Accessibility | Automated + manual audit | WCAG 2.1 AA |
| Interoperability | Schema validation | 100% ITD schema compliance |
| Data integrity | Hash verification + audit chain | Zero integrity breaches |

---

## Appendices

### A. NFR Change Log

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0 | 2026-06-29 | Initial comprehensive NFR document | TaxStox Engineering |

### B. Reference Documents

| Document | Link |
|----------|------|
| Design System | [DESIGN.md](design-system/DESIGN.md) |
| Product Requirements | [01-product-requirements.md](01-product-requirements.md) |
| Security & Privacy | [22-security-privacy.md](22-security-privacy.md) |
| Performance & Scaling | [25-performance-scaling-deployment.md](25-performance-scaling-deployment.md) |
| Testing Strategy | [26-testing-strategy.md](26-testing-strategy.md) |

### C. Key Stakeholders for NFRs

| NFR Area | Approver |
|----------|----------|
| Performance | Engineering Lead |
| Availability | DevOps Lead |
| Security | CISO |
| Privacy | DPO |
| Compliance | Legal & Compliance Lead |
| Scalability | Chief Architect |
| Reliability | Engineering Lead |
| Accessibility | Product Design Lead |
| Interoperability | API Architect |
| Regulatory | Legal & Compliance Lead |

---

*Next: [03 User Personas & Journeys](03-user-personas-journeys.md)*
