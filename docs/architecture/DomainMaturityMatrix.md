# Domain Maturity Matrix — IT_Returns Platform

> **Date:** 2026-07-05
> **Basis:** 15 bounded contexts from Enterprise Capability Model (FROZEN) vs Architecture Recovery Report

---

## Maturity Scale

| Level | Name | Criteria |
|-------|------|----------|
| 0 | **Absent** | No code, no design, no awareness |
| 1 | **Conceptual** | Design exists; no implementation |
| 2 | **Prototype** | Experimental code; not production-ready |
| 3 | **Partial** | Some capabilities implemented; significant gaps |
| 4 | **Functional** | Core capabilities work; missing advanced features |
| 5 | **Production Ready** | Complete for current scope; tested; deployed |
| 6 | **Enterprise Ready** | Complete for all capabilities; multi-tenant; audited; compliant |

---

## Bounded Context Maturity

### BC1: Identity & Access

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C1.1 Registration | 6 | 4 | 40% | 60% |
| C1.2 Authentication | 6 | 4 | 50% | 50% |
| C1.3 Authorization (RBAC) | 6 | 0 | 0% | 100% |
| C1.4 Session Management | 6 | 3 | 30% | 70% |
| C1.5 Credential Management | 6 | 3 | 40% | 60% |
| C1.6 Profile Management | 6 | 3 | 25% | 75% |
| C1.7 Account Recovery | 6 | 0 | 0% | 100% |
| C1.8 Consent Management | 6 | 0 | 0% | 100% |
| **BC1 Overall** | **6.0** | **2.1** | **23%** | **77%** |

**Confidence:** HIGH (all modules reviewed; missing capabilities confirmed by code absence)

---

### BC2: Taxpayer

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C2.1 Taxpayer Profile | 6 | 3 | 35% | 65% |
| C2.2 Residential Status | 6 | 0 | 5% | 95% |
| C2.3 Filing Status | 6 | 3 | 25% | 75% |
| C2.4 ITR Form Eligibility | 6 | 4 | 55% | 45% |
| C2.5 Historical Filing Record | 6 | 2 | 20% | 80% |
| C2.6 Family Unit Management | 6 | 0 | 0% | 100% |
| C2.7 Taxpayer Risk Profiling | 6 | 0 | 0% | 100% |
| **BC2 Overall** | **6.0** | **1.7** | **20%** | **80%** |

**Confidence:** HIGH (all taxpayer-related code reviewed)

---

### BC3: Document Processing

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C3.1 Multi-Format Ingestion | 6 | 4 | 40% | 60% |
| C3.2 PDF Password Resolution | 6 | 5 | 75% | 25% |
| C3.3 Form 16 Parser | 6 | 5 | 70% | 30% |
| C3.4 AIS Parser | 6 | 5 | 65% | 35% |
| C3.5 OCR Pipeline | 6 | 0 | 0% | 100% |
| C3.6 AIS Code Classification | 6 | 5 | 70% | 30% |
| C3.7 Form 26AS Parser | 6 | 0 | 0% | 100% |
| C3.8 Broker Statement Parser | 6 | 4 | 50% | 50% |
| C3.9 Investment Proof Parser | 6 | 0 | 0% | 100% |
| C3.10 Document Validation | 6 | 0 | 0% | 100% |
| **BC3 Overall** | **6.0** | **2.8** | **37%** | **63%** |

**Confidence:** HIGH (all parser code reviewed; OCR, 26AS, investment proof, validation absence confirmed)

---

### BC4: Income

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C4.1 Salary Income Engine | 6 | 4 | 60% | 40% |
| C4.2 House Property Engine | 6 | 2 | 20% | 80% |
| C4.3 Business Income Engine | 6 | 0 | 0% | 100% |
| C4.4 Capital Gains Engine | 6 | 4 | 50% | 50% |
| C4.5 Other Sources Engine | 6 | 3 | 30% | 70% |
| C4.6 Aggregation & Clubbing | 6 | 0 | 0% | 100% |
| C4.7 Previous Year Import | 6 | 0 | 0% | 100% |
| C4.8 Foreign Income Engine | 6 | 0 | 0% | 100% |
| **BC4 Overall** | **6.0** | **1.6** | **20%** | **80%** |

**Confidence:** HIGH (all engine code reviewed; missing income heads confirmed)

---

### BC5: Tax Computation

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C6.1 Slab Tax Engine | 6 | 3 | 35% | 65% |
| C6.2 Special Rate Engine | 6 | 3 | 40% | 60% |
| C6.3 Surcharge Engine | 6 | 4 | 50% | 50% |
| C6.4 HEC Engine | 6 | 4 | 60% | 40% |
| C6.5 Tax Liability Aggregator | 6 | 4 | 55% | 45% |
| C6.6 Pipeline Orchestrator | 6 | 2 | 15% | 85% |
| C6.7 Interest 234A/B/C | 6 | 0 | 0% | 100% |
| C6.8 Fee & Penalty | 6 | 0 | 0% | 100% |
| **BC5 Overall** | **6.0** | **2.5** | **32%** | **68%** |

**Confidence:** HIGH (all computation code reviewed; interest/penalty engines absent)

---

### BC6: Compliance

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C8.1 Tax Credit Reconciliation | 6 | 2 | 15% | 85% |
| C8.2 Cross-Document Validation | 6 | 2 | 20% | 80% |
| C8.3 ITR Schema Validation | 6 | 5 | 60% | 40% |
| C8.4 AIS Completeness Check | 6 | 1 | 10% | 90% |
| C8.5 Regulatory Limit Validator | 6 | 3 | 35% | 65% |
| C8.6 Anomaly Detection | 6 | 0 | 0% | 100% |
| C8.7 Audit Readiness | 6 | 0 | 0% | 100% |
| C8.8 GST Reconciliation | 6 | 0 | 0% | 100% |
| C8.9 Compliance Calendar | 6 | 0 | 0% | 100% |
| **BC6 Overall** | **6.0** | **1.4** | **16%** | **84%** |

**Confidence:** HIGH (validation code reviewed; reconciliation, anomaly, audit readiness absent)

---

### BC7: Audit & Explanation

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C10.1 Computation Audit Trail | 6 | 0 | 0% | 100% |
| C10.2 Explanation Engine | 6 | 2 | 20% | 80% |
| C10.3 Legal Provision Tracer | 6 | 0 | 0% | 100% |
| C10.4 Computation Verification | 6 | 0 | 0% | 100% |
| C10.5 CA Review Mode | 6 | 0 | 0% | 100% |
| C10.6 Explainable AI | 6 | 0 | 0% | 100% |
| **BC7 Overall** | **6.0** | **0.3** | **3%** | **97%** |

**Confidence:** HIGH (no audit/explanation infrastructure found in any module)

---

### BC8: Knowledge & Rules

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C11.1 Tax Knowledge Graph | 6 | 0 | 0% | 100% |
| C11.2 Tax Provision KB | 6 | 0 | 0% | 100% |
| C11.3 Finance Act Change Analyzer | 6 | 0 | 0% | 100% |
| C11.4 Tax Concept Glossary | 6 | 0 | 0% | 100% |
| C11.5 CBDT Circular Database | 6 | 0 | 0% | 100% |
| C11.6 Taxpayer Education Content | 6 | 0 | 0% | 100% |
| C12.1 Finance Act Versioning | 6 | 0 | 5% | 95% |
| C12.2 Rule Definition Language | 6 | 0 | 0% | 100% |
| C12.3 Rule Repository | 6 | 0 | 0% | 100% |
| C12.4 Rule Evaluation Engine | 6 | 2 | 15% | 85% |
| C12.5 Rule Testing Framework | 6 | 0 | 0% | 100% |
| C12.6 Rule Conflict Detection | 6 | 0 | 0% | 100% |
| C12.7 Rule Change Impact Analysis | 6 | 0 | 0% | 100% |
| **BC8 Overall** | **6.0** | **0.2** | **2%** | **98%** |

**Confidence:** HIGH (largest gap domain; almost entirely absent)

---

### BC9: Interview

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C13.1 Session Manager | 6 | 4 | 50% | 50% |
| C13.2 Adaptive Question Engine | 6 | 4 | 55% | 45% |
| C13.3 Question Design Framework | 6 | 2 | 20% | 80% |
| C13.4 Auto-Detection Engine | 6 | 4 | 50% | 50% |
| C13.5 Real-Time Validation | 6 | 2 | 15% | 85% |
| C13.6 Interview Personalization | 6 | 1 | 10% | 90% |
| C13.7 Document-Guided Interview | 6 | 2 | 15% | 85% |
| C13.8 Offline Interview | 6 | 0 | 0% | 100% |
| **BC9 Overall** | **6.0** | **2.4** | **27%** | **73%** |

**Confidence:** HIGH (interview engine code reviewed; advanced features absent)

---

### BC10: Reporting

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C14.1 Tax Summary Dashboard | 6 | 3 | 30% | 70% |
| C14.2 Comparative Analytics | 6 | 0 | 0% | 100% |
| C14.3 Regulatory Reporting | 6 | 0 | 0% | 100% |
| C14.4 Export & Portability | 6 | 3 | 30% | 70% |
| C14.5 BI & Analytics | 6 | 0 | 0% | 100% |
| C14.6 Custom Report Builder | 6 | 0 | 0% | 100% |
| C14.7 Refund Tracker | 6 | 0 | 0% | 100% |
| **BC10 Overall** | **6.0** | **0.9** | **9%** | **91%** |

**Confidence:** MEDIUM (limited reporting code reviewed; some may exist in unread dashboard/simulation modules)

---

### BC11: Integration

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C15.1 API Gateway | 6 | 3 | 30% | 70% |
| C15.2 External Tax APIs | 6 | 0 | 0% | 100% |
| C15.3 Financial Institution Integration | 6 | 2 | 15% | 85% |
| C15.4 Employer Integration | 6 | 0 | 0% | 100% |
| C15.5 CA Software Integration | 6 | 0 | 0% | 100% |
| C15.6 Payment Gateway | 6 | 0 | 0% | 100% |
| C15.7 Webhook System | 6 | 0 | 0% | 100% |
| C15.8 Developer Portal | 6 | 0 | 0% | 100% |
| **BC11 Overall** | **6.0** | **0.6** | **6%** | **94%** |

**Confidence:** LOW-MEDIUM (some integration endpoints may exist in unread modules; external API integrations are UNKNOWN)

---

### BC12: Operations

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C16.1 Config Management | 6 | 3 | 25% | 75% |
| C16.2 Monitoring | 6 | 1 | 10% | 90% |
| C16.3 Structured Logging | 6 | 1 | 10% | 90% |
| C16.4 CI/CD Pipeline | 6 | 2 | 20% | 80% |
| C16.5 Secrets Management | 6 | 1 | 15% | 85% |
| C16.6 Backup & DR | 6 | Unknown | — | — |
| C16.7 Rate Limiting | 6 | 0 | 0% | 100% |
| C16.8 IT Asset Management | 6 | 0 | 0% | 100% |
| **BC12 Overall** | **6.0** | **1.1** | **11%** | **89%** |

**Confidence:** MEDIUM (CI/CD and backup status uncertain; Render/Neon may provide some)

---

### BC13: Security

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C17.1 Data Encryption | 6 | 2 | 30% | 70% |
| C17.2 Vulnerability Management | 6 | Unknown | — | — |
| C17.3 Data Privacy (DPDP) | 6 | 0 | 5% | 95% |
| C17.4 Access Control | 6 | 0 | 5% | 95% |
| C17.5 Threat Detection | 6 | 0 | 0% | 100% |
| C17.6 Secure SDLC | 6 | Unknown | — | — |
| C17.7 Identity Proofing | 6 | 0 | 0% | 100% |
| C17.8 Data Loss Prevention | 6 | 0 | 0% | 100% |
| C17.9 Tenant Isolation | 6 | 0 | 0% | 100% |
| C17.10 Security Compliance | 6 | 0 | 0% | 100% |
| **BC13 Overall** | **6.0** | **0.3** | **4%** | **96%** |

**Confidence:** MEDIUM (some security practices may exist in deployment config; no code evidence)

---

### BC14: Notification

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C18.1 Notification Engine | 6 | 0 | 0% | 100% |
| C18.2 Deadline Reminders | 6 | 0 | 0% | 100% |
| C18.3 Filing Status Updates | 6 | 0 | 0% | 100% |
| C18.4 In-App Communication | 6 | 0 | 0% | 100% |
| C18.5 Regulatory Broadcast | 6 | 0 | 0% | 100% |
| **BC14 Overall** | **6.0** | **0.0** | **0%** | **100%** |

**Confidence:** HIGH (zero notification infrastructure in 42 modules)

---

### BC15: Tax Planning

| Capability | Target Maturity | Current Maturity | Coverage % | Gap % |
|-----------|----------------|-----------------|------------|-------|
| C19.1 Scenario Simulator | 6 | 0 | 0% | 100% |
| C19.2 Tax-Loss Harvesting | 6 | 0 | 0% | 100% |
| C19.3 Multi-Year Projection | 6 | 0 | 0% | 100% |
| C19.4 Investment Tax Optimization | 6 | 0 | 0% | 100% |
| C19.5 Retirement Tax Planning | 6 | 0 | 0% | 100% |
| **BC15 Overall** | **6.0** | **0.0** | **0%** | **100%** |

**Confidence:** HIGH (no tax planning infrastructure; regime recommendation is optimization, not planning)

---

## Summary Matrix

| # | Bounded Context | Target | Current | Coverage | Gap | Confidence |
|---|----------------|--------|---------|----------|-----|------------|
| BC1 | Identity & Access | 6.0 | 2.1 | 23% | 77% | HIGH |
| BC2 | Taxpayer | 6.0 | 1.7 | 20% | 80% | HIGH |
| BC3 | Document Processing | 6.0 | 2.8 | 37% | 63% | HIGH |
| BC4 | Income | 6.0 | 1.6 | 20% | 80% | HIGH |
| BC5 | Tax Computation | 6.0 | 2.5 | 32% | 68% | HIGH |
| BC6 | Compliance | 6.0 | 1.4 | 16% | 84% | HIGH |
| BC7 | Audit & Explanation | 6.0 | 0.3 | 3% | 97% | HIGH |
| BC8 | Knowledge & Rules | 6.0 | 0.2 | 2% | 98% | HIGH |
| BC9 | Interview | 6.0 | 2.4 | 27% | 73% | HIGH |
| BC10 | Reporting | 6.0 | 0.9 | 9% | 91% | MEDIUM |
| BC11 | Integration | 6.0 | 0.6 | 6% | 94% | LOW-MED |
| BC12 | Operations | 6.0 | 1.1 | 11% | 89% | MEDIUM |
| BC13 | Security | 6.0 | 0.3 | 4% | 96% | MEDIUM |
| BC14 | Notification | 6.0 | 0.0 | 0% | 100% | HIGH |
| BC15 | Tax Planning | 6.0 | 0.0 | 0% | 100% | HIGH |
| **OVERALL** | **6.0** | **1.2** | **14%** | **86%** | — |

---

## Maturity Distribution

```
Maturity Level 0 (Absent):          ████████████████████████ 6 contexts
Maturity Level 1 (Conceptual):      ███████ 3 contexts
Maturity Level 2 (Prototype):       █████ 2 contexts
Maturity Level 3 (Partial):         ███ 2 contexts
Maturity Level 4 (Functional):      █ 1 context (BC3 Document Processing)
Maturity Level 5 (Production Ready): 0 contexts
Maturity Level 6 (Enterprise Ready): 0 contexts
```

---

*End of Domain Maturity Matrix v1.0*
*All maturity assessments evidence-backed from Architecture Recovery Report. UNKNOWN items marked explicitly.*
