# Enterprise Risk Matrix — IT_Returns Platform

> **Date:** 2026-07-05
> **Context:** Risks identified from Enterprise Gap Analysis, Architecture Recovery Report, and source code audit

---

## Risk Severity Matrix

```
                     IMPACT →
                     Low      Medium    High      Critical
P                     │         │         │         │
R  Very High (81-100%)│         │  R09    │  R01    │
O                     │         │         │  R02    │
B  High (61-80%)      │  R11    │  R05    │  R03    │
A                     │         │  R07    │  R04    │
B  Medium (41-60%)    │  R13    │  R08    │  R06    │
I                     │         │  R15    │  R12    │
L  Low (21-40%)       │         │  R10    │         │
I                     │         │  R14    │         │
T  Very Low (0-20%)   │         │         │         │
Y                     │         │         │         │
```

---

## Critical Risks

### R01: Finance Act 2026 Obsolescence

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | Platform becomes functionally obsolete when FY2026-27 rules take effect (April 1, 2026). Entire computation pipeline hardcoded for FY2025-26. |
| **Probability** | Very High (95%) — Finance Act passed annually; FY2025-26 ends March 31, 2026 |
| **Impact** | Critical — Platform cannot compute tax for any other FY |
| **Severity** | Critical |
| **Affected Capabilities** | C6.1-C6.8 (Tax Computation), C7.1-C7.6 (Regime Optimization), C4.1-C4.8 (Income), C5.1-C5.7 (Deductions), C9.1-C9.7 (ITR Generation), C12.1-C12.7 (Rule Management) |
| **Affected Bounded Contexts** | BC4 (Income), BC5 (Tax Computation), BC6 (Compliance), BC8 (Knowledge & Rules) |
| **Business Consequence** | Platform becomes a single-FY tool instead of multi-year platform. Users cannot file for FY2026-27. Revenue loss. Market rejection. |
| **Mitigation** | Extract all hardcoded rules to versioned rule repository indexed by FinancialYear before FY2026-27 assessment cycle. Requires C12.1-C12.4 implementation as prerequisite. |
| **Confidence** | HIGH — Hardcoded AY/FY confirmed in 5+ files |

---

### R02: DPDP Act Non-Compliance

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | Digital Personal Data Protection Act 2023 comes into force. Platform lacks all required compliance capabilities (consent management, data principal rights, breach notification, DPIA, data retention/deletion). |
| **Probability** | Very High (90%) — DPDP Act is law; rules expected within 12-18 months |
| **Impact** | Critical — Penalties up to ₹250 Cr per violation; inability to legally operate |
| **Severity** | Critical |
| **Affected Capabilities** | C1.8 (Consent Management), C17.3 (Data Privacy), C17.4 (Access Control), C17.7 (Identity Proofing), C17.10 (Security Compliance) |
| **Affected Bounded Contexts** | BC1 (Identity & Access), BC13 (Security) |
| **Business Consequence** | Regulatory shutdown; financial penalties; reputational destruction; criminal liability for directors |
| **Mitigation** | Implement consent management bounded context; add data principal rights APIs (access, correction, erasure, portability); implement data retention/deletion policies; prepare DPIA; establish breach notification procedure |
| **Confidence** | HIGH — DPDP Act is external legal fact; zero consent infrastructure in codebase |

---

### R03: Security Breach via Plaintext PII

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | Database compromise exposes unencrypted PAN, salary data, capital gains, bank account details for all users. |
| **Probability** | High (70%) — No application-level encryption; dev JWT secret hardcoded; limited security controls |
| **Impact** | Critical — Data breach of RESTRICTED-classified taxpayer financial data |
| **Severity** | Critical |
| **Affected Capabilities** | C17.1 (Data Encryption), C17.2 (Vulnerability Management), C17.4 (Access Control), C17.8 (DLP) |
| **Affected Bounded Contexts** | BC1 (Identity), BC13 (Security), all contexts storing data |
| **Business Consequence** | IT Act and DPDP Act penalties; mandatory breach notification to all users; class-action lawsuits; irreversible reputational damage; potential platform shutdown |
| **Mitigation** | Implement application-level encryption for all PII columns; integrate KMS/HSM; rotate hardcoded JWT secret; implement RBAC; add database activity monitoring; encrypt existing data |
| **Confidence** | HIGH — Plaintext PAN confirmed in `db/database.py:182`; dev secret in `auth/jwt.py:12` |

---

### R04: Production Incident from Zero Testing

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | Code change introduces incorrect tax computation that is deployed to production without automated testing catching it. |
| **Probability** | High (75%) — Zero automated tests; manual QA only; frequent commits to production |
| **Impact** | Critical — Incorrect tax computation affects all users; ITD rejection; potential legal liability |
| **Severity** | Critical |
| **Affected Capabilities** | C12.5 (Rule Testing), all C6 (Tax Computation) capabilities |
| **Affected Bounded Contexts** | BC5 (Tax Computation), BC6 (Compliance), BC4 (Income) |
| **Business Consequence** | Wrong tax filed for users; ITD notices; loss of user trust; potential legal claims of professional negligence |
| **Mitigation** | Establish pytest framework; write unit tests for all computation engines; create golden-test-vector suite; implement CI with automated test execution; block merge on test failure |
| **Confidence** | HIGH — Zero tests confirmed; single skeleton file `test_e2e_real_data.py` |

---

### R05: Filing Season Scalability Failure

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | During peak filing season (July), in-memory sessions and single-process architecture fail under load, preventing users from filing by the July 31 deadline. |
| **Probability** | High (65%) — In-memory sessions; no load testing; no auto-scaling; filing season creates demand spike |
| **Impact** | High — Users miss ITR deadline; financial penalties for late filing |
| **Severity** | High |
| **Affected Capabilities** | C1.4 (Session Management), C16.2 (Monitoring), C16.7 (Rate Limiting) |
| **Affected Bounded Contexts** | BC1 (Identity), BC12 (Operations) |
| **Business Consequence** | Service degradation during critical revenue period; missed filing deadlines for users; support overload; reputational damage during peak visibility |
| **Mitigation** | Migrate sessions to Redis; add connection pooling; implement load testing before filing season; configure auto-scaling; add rate limiting |
| **Confidence** | HIGH — In-memory sessions confirmed; no load testing evidence |

---

## High-Impact Risks

### R06: CA/Enterprise Market Inaccessible

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | Platform cannot serve CA firms or enterprises because multi-tenancy, RBAC, client management, and enterprise SSO are not implemented. |
| **Probability** | Medium (55%) — B2C may be sufficient for initial traction; enterprise demand will grow |
| **Impact** | High — CA firms are primary distribution channel for tax filing in India |
| **Severity** | High |
| **Affected Capabilities** | C1.3 (RBAC), C21.1-C21.8 (Enterprise Multi-Tenancy) |
| **Affected Bounded Contexts** | BC1 (Identity), BC15 (Enterprise/Tenant — absent) |
| **Business Consequence** | Limited to D2C only; cannot access ₹10,000 Cr+ CA-mediated tax filing market |
| **Mitigation** | Implement RBAC model; add tenant context; design multi-tenant data isolation; build client portfolio management |
| **Confidence** | HIGH — Zero enterprise infrastructure confirmed |

---

### R07: Rule Change Introduces Silent Tax Errors

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | Tax rule update (new slab, changed deduction limit) is incorrectly implemented because rules are embedded in code with no testing framework, producing wrong tax computations that go undetected. |
| **Probability** | High (70%) — Rules are in code; no tests; human error in manual updates |
| **Impact** | High — Systemic tax errors for all users; regulatory consequences |
| **Severity** | High |
| **Affected Capabilities** | C12.1-C12.7 (Rule Management), C6.1-C6.8 (Tax Computation) |
| **Affected Bounded Contexts** | BC5 (Tax Computation), BC8 (Knowledge & Rules) |
| **Business Consequence** | Undetected tax errors erode trust; potential refund clawback for users; CPC notices |
| **Mitigation** | Extract rules to declarative format; build rule testing framework with golden vectors; add CI validation of rule changes |
| **Confidence** | HIGH — Rules in code confirmed in 6+ files; zero rule tests |

---

### R08: Key Person Dependency (Bus Factor)

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | Domain expertise (25-year CA + 25-year engineer) concentrated in founders. Tax knowledge embedded in code comments and implementation, not in knowledge graph or documentation. Loss of key person = loss of tax domain understanding. |
| **Probability** | Medium (45%) — Founders currently active; no immediate departure risk |
| **Impact** | High — Loss of tax domain knowledge stalls all feature development |
| **Severity** | High |
| **Affected Capabilities** | C11.1-C11.6 (Knowledge Management), C12.1-C12.4 (Rule Management) |
| **Affected Bounded Contexts** | BC8 (Knowledge & Rules) |
| **Business Consequence** | Development velocity drops to near-zero for tax rule changes; incorrect implementations without domain review |
| **Mitigation** | Build Tax Knowledge Graph (C11.1); formalize tax rules in declarative format (C12.2); document all tax domain decisions; train multiple domain reviewers |
| **Confidence** | MEDIUM — Bus factor observed in HANDOFF.md session history; domain knowledge in code comments only |

---

### R09: ITD Portal Schema Change Breaks JSON Generation

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | ITD changes ITR JSON schema without notice. Current JSON builders produce invalid JSON that the portal rejects. |
| **Probability** | Medium (50%) — ITD changes schemas annually with new ITR forms |
| **Impact** | High — All users unable to file via generated JSON |
| **Severity** | High |
| **Affected Capabilities** | C9.1-C9.5 (ITR Builders), C8.3 (Schema Validation) |
| **Affected Bounded Contexts** | BC6 (Compliance) |
| **Business Consequence** | Platform unusable for filing during schema transition; all users affected simultaneously |
| **Mitigation** | Abstract ITD schema versioning; build schema compatibility layer; add schema change detection; maintain backward compatibility |
| **Confidence** | MEDIUM — ITD schema changes are annual; platform has no schema versioning |

---

### R10: Neon PostgreSQL Free Tier Limit

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | Production database reaches Neon free tier limits, causing service degradation or data access failure. |
| **Probability** | Low (30%) — Current usage likely within limits; monitoring absent |
| **Impact** | Medium — Temporary service disruption; data remains safe on Neon infrastructure |
| **Severity** | Medium |
| **Affected Capabilities** | C16.6 (Backup & DR — UNKNOWN status) |
| **Affected Bounded Contexts** | BC12 (Operations) |
| **Business Consequence** | Brief outage; users unable to access filing data during disruption |
| **Mitigation** | Monitor database usage; set up alerts before limits; upgrade Neon plan before limits reached; implement backup verification |
| **Confidence** | LOW — Neon usage metrics not available for review |

---

### R11: PDF Parser Breakage on New Format

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | Employer or ITD changes PDF format (new TRACES version, new AIS layout). Regex-based parsers fail to extract data. |
| **Probability** | Medium (40%) — TRACES format is stable; employer formats vary widely |
| **Impact** | Low-Medium — Affected users cannot upload documents; workaround exists (manual entry) |
| **Severity** | Medium |
| **Affected Capabilities** | C3.3 (Form 16 Parser), C3.4 (AIS Parser) |
| **Affected Bounded Contexts** | BC3 (Document Processing) |
| **Business Consequence** | Parsing failures for subset of users; support burden; manual fallback degrades UX |
| **Mitigation** | Add field-level confidence scoring; implement ML-based fallback parser; monitor parse failure rates; build format version detection |
| **Confidence** | MEDIUM — Regex fragility observed in parser code; TRACES format stability is external assumption |

---

### R12: Circular Dependency Causes Runtime Failure

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | The lazy import workaround in `regime_optimizer_v2.py` breaks when module initialization order changes, causing ImportError at runtime. |
| **Probability** | Medium (40%) — Currently working; fragile to import order changes |
| **Impact** | High — Regime optimizer fails; core computation path broken |
| **Severity** | High |
| **Affected Capabilities** | C6.6 (Pipeline Orchestrator), C7.1 (Regime Comparison) |
| **Affected Bounded Contexts** | BC5 (Tax Computation) |
| **Business Consequence** | Tax computation fails for all users; P0 incident |
| **Mitigation** | Resolve circular dependency properly through dependency inversion; introduce interface between optimizer and classifier |
| **Confidence** | HIGH — Lazy import confirmed at `regime_optimizer_v2.py:334-335` |

---

### R13: DeepSeek API Dependency for Tax Updates

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | DeepSeek API becomes unavailable, rate-limited, or changes pricing. Tax updates summarization degrades. |
| **Probability** | Medium (35%) — Third-party API dependency |
| **Impact** | Low — Fallback exists (raw title); tax updates are non-critical feature |
| **Severity** | Low |
| **Affected Capabilities** | C11.3 (Finance Act Change Analyzer — indirectly via summarizer) |
| **Affected Bounded Contexts** | BC8 (Knowledge & Rules) |
| **Business Consequence** | Tax updates section shows degraded content; no impact on core filing functionality |
| **Mitigation** | Already has fallback (raw title); consider multi-provider AI strategy; monitor API health |
| **Confidence** | HIGH — DeepSeek dependency confirmed in `summarizer/__init__.py`; fallback exists |

---

### R14: Render Free Tier Cold Start

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | Keep-alive cron fails; Render free tier puts backend to sleep; users experience 30-60s cold start on first request. |
| **Probability** | Low (25%) — Keep-alive cron is running (cron-job.org every 5 min) |
| **Impact** | Medium — Poor UX during cold start; potential request timeout |
| **Severity** | Medium |
| **Affected Capabilities** | C16.2 (Monitoring — degraded) |
| **Affected Bounded Contexts** | BC12 (Operations) |
| **Business Consequence** | Slow first request; user perception of unreliability |
| **Mitigation** | Monitor keep-alive cron health; upgrade Render plan before filing season |
| **Confidence** | MEDIUM — Keep-alive confirmed in HANDOFF.md; Render free tier sleep behavior is platform-known |

---

### R15: Data Loss from In-Memory State

| Dimension | Assessment |
|-----------|-----------|
| **Risk** | Server restart or crash during active user session loses all parsed document data and computation state. User must restart from upload. |
| **Probability** | Medium (35%) — Render restarts on deploy; Python process can crash |
| **Impact** | Medium — User loses progress; frustration; support requests |
| **Severity** | Medium |
| **Affected Capabilities** | C1.4 (Session Management), C13.1 (Interview Session Manager) |
| **Affected Bounded Contexts** | BC1 (Identity), BC9 (Interview) |
| **Business Consequence** | Poor UX during deploys/crashes; user churn; support burden |
| **Mitigation** | Migrate sessions to Redis with persistence; implement session state recovery |
| **Confidence** | HIGH — In-memory sessions confirmed in `utils/session.py` |

---

## Risk Summary

| # | Risk | Probability | Impact | Severity | Mitigation Type |
|---|------|------------|--------|----------|-----------------|
| R01 | FY2026 Obsolescence | Very High | Critical | Critical | Architectural — Rule versioning |
| R02 | DPDP Act Non-Compliance | Very High | Critical | Critical | Domain — Consent management |
| R03 | Security Breach (PII) | High | Critical | Critical | Security — Encryption + RBAC |
| R04 | Zero Testing → Tax Errors | High | Critical | Critical | Testing — Test framework |
| R05 | Filing Season Scalability | High | High | High | Infrastructure — Redis + scaling |
| R06 | CA/Enterprise Market Loss | Medium | High | High | Domain — Multi-tenancy |
| R07 | Silent Tax Errors | High | High | High | Architecture — Rule testing |
| R08 | Key Person Dependency | Medium | High | High | Knowledge — Knowledge graph |
| R09 | ITD Schema Change | Medium | High | High | Architecture — Schema versioning |
| R10 | Neon DB Limit | Low | Medium | Medium | Operations — Monitoring |
| R11 | PDF Parser Breakage | Medium | Low-Medium | Medium | Architecture — ML fallback |
| R12 | Circular Import Failure | Medium | High | High | Code — Dependency inversion |
| R13 | DeepSeek API Failure | Medium | Low | Low | Architecture — Fallback exists |
| R14 | Render Cold Start | Low | Medium | Medium | Operations — Plan upgrade |
| R15 | In-Memory Data Loss | Medium | Medium | Medium | Infrastructure — Redis |

---

## Risk Concentration by Bounded Context

```
BC5  (Tax Computation)    ████████████ R01, R04, R07, R12
BC8  (Knowledge & Rules)  ████████████ R01, R07, R08, R13
BC13 (Security)           ██████████   R02, R03
BC1  (Identity)           ████████     R02, R03, R05, R15
BC12 (Operations)         ██████       R05, R10, R14
BC6  (Compliance)         ██████       R01, R09
BC4  (Income)             ██████       R01, R04
BC3  (Document)           ████         R11
BC15 (Enterprise)         ████         R06
BC9  (Interview)          ███          R15
```

---

*End of Enterprise Risk Matrix v1.0*
*All risks identified from architectural analysis. Probabilities are estimates based on current evidence. Mitigations are high-level architectural directions, not implementation plans.*
