# TaxStox Product Engineering Roadmap v1.0

> **Program:** Product Engineering Program (PEP)
> **Baseline:** Certified Architecture v1.0 (EAC)
> **Predecessor:** Enterprise Modernization Roadmap M0–M11 (COMPLETE)
> **Status:** PLAN — Awaiting approval before P1 execution

---

## Executive Summary

The Enterprise Modernization Program (M0-M11) established the architecture foundation. This Product Engineering Roadmap (P1-P7) systematically implements every remaining business capability defined in the frozen Enterprise Capability Model.

| Metric | Current | Target (Post-P7) |
|--------|---------|-------------------|
| Capability coverage | ~30% | ~85% |
| ITR types supported | ITR-1, ITR-2 | ITR-1 through ITR-7 |
| Taxpayer types supported | Salaried individuals | Individuals, HUF, Business, LLP, Company, Trust |
| AI capabilities | Knowledge graph, audit trail, rule testing | Complete AI interview, explanations, recommendations |
| Enterprise features | Multi-tenancy, RBAC, consent | CA workflows, firm dashboards, billing, white-label |

---

## P1 — Complete Individual Tax Filing

### Objective

Make ITR-1 and ITR-2 filing production-complete for all individual taxpayer scenarios. This is the core value proposition and the largest addressable market.

### Business Capabilities

| Capability ID | Capability | Current | Target |
|--------------|-----------|---------|--------|
| C2.2 | Residential Status Determination | 5% | 80% |
| C4.8 | Foreign Income & Asset Engine | 0% | 60% |
| C4.1 | Salary Income (multiple employers) | 60% | 85% |
| C4.4 | Capital Gains (all asset classes) | 50% | 80% |
| C5.2 | Section 10 Exemption Engine | 35% | 70% |
| C8.4 | AIS Completeness Checker | 10% | 60% |
| C8.6 | Anomaly Detection | 0% | 40% |
| C9.2 | ITR-2 Builder (completion) | 60% | 85% |
| C10.3 | Legal Provision Tracer | 40% | 70% |
| C14.1 | Tax Summary Dashboard | 30% | 70% |

### Dependencies

P1 has no product-wave dependencies. Builds directly on M0-M11 architecture.

### Entry Criteria

- [x] Architecture certified (EAC v1.0)
- [x] M0-M11 complete
- [x] 189 tests passing
- [x] RuleRepository supports multi-FY

### Exit Criteria

- [ ] ITR-2 supports all individual taxpayer scenarios (NRI, multiple employers, crypto, unlisted shares)
- [ ] Residential status engine operational
- [ ] Foreign asset (Schedule FA) builder complete
- [ ] All 80C components individually selectable with limit enforcement
- [ ] AIS completeness check warns on missing income
- [ ] 250+ tests passing
- [ ] Golden vectors expanded to cover NRI, multiple employer, crypto scenarios

### Risks

| Risk | Mitigation |
|------|-----------|
| Residential status rules are complex (RNOR, deemed resident) | Domain expert review per Section 6 |
| Schedule FA is verbose (country-by-country) | Schema-driven generation from FIAccount model |
| Crypto VDA taxation (115BBH) — evolving law | Isolate in special rate engine |

### Estimated Effort: **10 weeks**

---

## P2 — Business & Professional Taxation

### Objective

Support ITR-3 (business income) and ITR-4 (presumptive taxation). Unlock the self-employed, freelancer, and small business market.

### Business Capabilities

| Capability ID | Capability | Current | Target |
|--------------|-----------|---------|--------|
| C4.3 | Business Income Engine | 0% | 60% |
| C4.6 | Income Aggregation & Clubbing | 0% | 50% |
| C4.7 | Previous Year Data Import | 0% | 40% |
| C5.5 | Donation (80G) Engine | 0% | 60% |
| C6.8 | Fee & Penalty Engine | 0% | 50% |
| C8.5 | Regulatory Limit Validator | 35% | 70% |
| C8.8 | GST Reconciliation | 0% | 40% |
| C9.3 | ITR-3 Builder | 0% | 60% |
| C9.4 | ITR-4 Builder | 0% | 60% |

### Dependencies

- **P1** — ITR-2 completion provides the base builder enhancements

### Entry Criteria

- [ ] P1 complete
- [ ] ITR-2 production-ready for all individuals

### Exit Criteria

- [ ] ITR-3 builder supports full P&L, depreciation schedule, presumptive taxation
- [ ] ITR-4 builder supports 44AD/44ADA/44AE
- [ ] Business income engine handles audit requirements (44AB)
- [ ] GST reconciliation with turnover validation
- [ ] 300+ tests passing

### Estimated Effort: **12 weeks**

---

## P3 — Entity Taxation

### Objective

Extend to ITR-5 (LLP, Partnership), ITR-6 (Company), and ITR-7 (Trust). Support CA firms filing for entity clients.

### Business Capabilities

| Capability ID | Capability | Current | Target |
|--------------|-----------|---------|--------|
| C9.5 | ITR-5 Builder | 0% | 60% |
| C9.6 | ITR-6 Builder | 0% | 60% |
| C9.7 | ITR-7 Builder | 0% | 50% |
| C6.3 | Surcharge (entity types) | 60% | 85% |
| C6.4 | HEC Engine | 60% | 80% |

### Dependencies

- **P2** — Business income engine required for ITR-5/6/7

### Entry Criteria

- [ ] P2 complete
- [ ] Business income engine operational

### Exit Criteria

- [ ] ITR-5/6/7 builders generate schema-compliant JSON
- [ ] Entity-specific schedules implemented
- [ ] 350+ tests passing

### Estimated Effort: **10 weeks**

---

## P4 — AI Intelligence

### Objective

Complete the AI capabilities: adaptive interview, knowledge graph, tax explanations, intelligent recommendations. This is the key differentiator from traditional tax software.

### Business Capabilities

| Capability ID | Capability | Current | Target |
|--------------|-----------|---------|--------|
| C11.1 | Tax Knowledge Graph | 50% | 80% |
| C11.2 | Tax Provision KB | 40% | 70% |
| C11.3 | Finance Act Change Analyzer | 0% | 50% |
| C11.4 | Tax Concept Glossary | 0% | 60% |
| C11.5 | CBDT Circular Database | 0% | 50% |
| C11.6 | Taxpayer Education Content | 0% | 50% |
| C12.6 | Rule Conflict Detection | 0% | 50% |
| C12.7 | Rule Change Impact Analysis | 0% | 50% |
| C13.2 | Adaptive Question Engine | 55% | 80% |
| C13.5 | Real-Time Validation | 15% | 60% |
| C13.6 | Interview Personalization | 10% | 50% |
| C13.8 | Offline Interview | 0% | 40% |
| C10.2 | Explanation Engine | 60% | 80% |
| C10.6 | Explainable AI | 0% | 30% |

### Dependencies

- **P1** — Individual tax completion provides the data foundation

### Entry Criteria

- [ ] P1 complete
- [ ] Knowledge graph foundation (M7) operational

### Exit Criteria

- [ ] Knowledge graph covers 80% of Income Tax Act provisions relevant to individuals
- [ ] Adaptive interview reduces average questions to ≤3
- [ ] Finance Act change analyzer detects slab/limit changes automatically
- [ ] 400+ tests passing

### Estimated Effort: **14 weeks**

---

## P5 — Enterprise Platform

### Objective

Complete the enterprise multi-tenancy platform: CA firm workflows, dashboards, billing, white-label, client portfolio management.

### Business Capabilities

| Capability ID | Capability | Current | Target |
|--------------|-----------|---------|--------|
| C21.1 | Tenant Management | 60% | 85% |
| C21.2 | CA Firm Hierarchy | 50% | 80% |
| C21.3 | Client Portfolio | 50% | 80% |
| C21.4 | Firm Dashboard | 30% | 70% |
| C21.5 | Bulk Operations | 0% | 60% |
| C21.6 | Enterprise SSO | 30% | 60% |
| C21.7 | White-Label/Branding | 0% | 50% |
| C21.8 | Billing & Subscription | 0% | 50% |
| C14.2 | Comparative Analytics | 0% | 40% |
| C14.5 | BI & Analytics | 0% | 30% |
| C14.6 | Custom Report Builder | 0% | 30% |

### Dependencies

- **P1, P2** — ITR-1 through ITR-4 filing must be production-ready

### Entry Criteria

- [ ] P1 and P2 complete
- [ ] Multi-tenancy foundation (M8) operational

### Exit Criteria

- [ ] CA firm can manage 100+ clients with role-based staff access
- [ ] White-label subdomain with firm branding
- [ ] Usage-based billing with invoice generation
- [ ] 430+ tests passing

### Estimated Effort: **12 weeks**

---

## P6 — Customer Experience

### Objective

Notifications, mobile readiness, tax planning, self-service portal, and performance optimization.

### Business Capabilities

| Capability ID | Capability | Current | Target |
|--------------|-----------|---------|--------|
| C18.1 | Notification Engine | 0% | 60% |
| C18.2 | Deadline Reminders | 0% | 60% |
| C18.3 | Filing Status Updates | 0% | 60% |
| C18.4 | In-App Communication | 0% | 40% |
| C19.1 | Scenario Simulator | 0% | 40% |
| C19.2 | Tax-Loss Harvesting | 0% | 30% |
| C19.3 | Multi-Year Projection | 0% | 30% |
| C14.4 | Export & Portability | 30% | 60% |
| C14.7 | Refund Tracker | 0% | 50% |

### Dependencies

- **P1-P5** — Core filing must be complete before UX enhancements

### Entry Criteria

- [ ] P1-P5 complete

### Exit Criteria

- [ ] Email/SMS notifications for deadlines and filing status
- [ ] Tax planning scenario simulator
- [ ] Refund status tracker
- [ ] 460+ tests passing

### Estimated Effort: **8 weeks**

---

## P7 — Commercial Launch

### Objective

Production deployment hardening, monitoring, operational readiness, beta program, and commercial launch.

### Business Capabilities

| Capability ID | Capability | Current | Target |
|--------------|-----------|---------|--------|
| C17.2 | Monitoring | 60% | 85% |
| C17.4 | CI/CD (completion) | 70% | 85% |
| C17.5 | Secrets Management | 40% | 70% |
| C17.6 | Backup & DR | 0% | 60% |
| C17.7 | Identity Proofing | 0% | 50% |
| C17.8 | IT Asset Management | 0% | 40% |
| C16.1 | API Gateway | 40% | 70% |
| C16.4 | Employer/Enterprise Integration | 0% | 30% |
| C16.6 | Payment Gateway | 0% | 50% |
| C16.8 | Developer Portal | 0% | 30% |

### Dependencies

- **P1-P6** — All product features complete

### Entry Criteria

- [ ] P1-P6 complete
- [ ] 460+ tests passing
- [ ] Architecture health ≥ 55/100

### Exit Criteria

- [ ] Production deployment with auto-scaling
- [ ] DR/BCP plan documented and tested
- [ ] Penetration test completed
- [ ] Beta program launched with ≥50 CA firms
- [ ] Operational runbooks published
- [ ] 480+ tests passing
- [ ] Architecture health ≥ 60/100

### Estimated Effort: **8 weeks**

---

## Program Summary

| Wave | Name | Effort | Key Deliverable |
|------|------|--------|----------------|
| P1 | Complete Individual Tax Filing | 10 weeks | ITR-2 production-complete for all individuals |
| P2 | Business & Professional Taxation | 12 weeks | ITR-3 + ITR-4 filing |
| P3 | Entity Taxation | 10 weeks | ITR-5/6/7 filing |
| P4 | AI Intelligence | 14 weeks | Complete AI-powered interview + explanations |
| P5 | Enterprise Platform | 12 weeks | CA firm multi-tenant platform |
| P6 | Customer Experience | 8 weeks | Notifications, tax planning, mobile |
| P7 | Commercial Launch | 8 weeks | Production deployment, beta, launch |
| | **TOTAL** | **~74 weeks** | |

### Dependency Graph

```
P1 ──────► P2 ──────► P3
  │          │
  │          └──────► P5 ──────► P6 ──────► P7
  │
  └──────► P4 ──────────────────┘
```

- P1 is the prerequisite for all other waves
- P4 can parallel with P2
- P3 and P5 depend on P2
- P6 needs P1-P5
- P7 needs all preceding waves

---

*End of Product Engineering Roadmap v1.0*
*This roadmap is the plan. No implementation has begun. Awaiting approval for P1.*
