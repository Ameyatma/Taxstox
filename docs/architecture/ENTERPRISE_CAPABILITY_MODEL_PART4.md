# Enterprise Capability Model — Part 4: Domains 17-20, Bounded Context Map, Cross-Cutting

> **Continuation of Parts 1-3**
> **Date:** 2026-07-05

---

## 17. Domain 16: Administration & Operations

### C17.1 — System Configuration Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Centralize all platform configuration with versioning, environment segregation, and audit trail. |
| **Responsibilities** | Environment-specific config (dev/staging/production); feature flags for gradual rollout; dynamic configuration (change without deployment); configuration schema validation; configuration change audit trail; secret management (external to config); configuration drift detection |
| **Dependencies** | C17.5 Secrets Management |
| **Priority** | **High** |
| **Maturity Target** | GitOps-based config; feature flag A/B testing; auto-rollback on config error |

### C17.2 — Monitoring & Observability

| Attribute | Value |
|-----------|-------|
| **Purpose** | Provide comprehensive visibility into system health, performance, and user experience. |
| **Responsibilities** | Infrastructure monitoring (CPU, memory, disk, network); application monitoring (error rates, latency, throughput); business monitoring (filings completed, revenue, conversion funnel); synthetic transaction monitoring; distributed tracing; log aggregation; alerting with on-call escalation; SLO/SLI tracking; dashboard generation |
| **Dependencies** | C17.3 Structured Logging |
| **Priority** | **Critical** |
| **Maturity Target** | OpenTelemetry-based observability; AI-powered anomaly detection; predictive alerting |

### C17.3 — Structured Logging & Audit Logging

| Attribute | Value |
|-----------|-------|
| **Purpose** | Capture all system events in structured, queryable logs with appropriate retention and PII protection. |
| **Responsibilities** | Structured JSON logging (all services); correlation ID propagation across services; log levels enforced; PII masking in logs (PAN, Aadhaar, mobile, email); separate audit log for all data access and mutations; log retention policies; log search and alerting; compliance log export |
| **Dependencies** | C17.6 Data Privacy |
| **Priority** | **High** |
| **Maturity Target** | ELK/Loki-based log platform; ML-based log anomaly detection; automated PII detection in logs |

### C17.4 — Deployment & CI/CD Pipeline

| Attribute | Value |
|-----------|-------|
| **Purpose** | Automate build, test, and deployment with zero-downtime releases and automated rollback. |
| **Responsibilities** | Automated build on PR; automated test execution in CI; security scanning in pipeline; container image building; database migration automation; blue-green/canary deployment; automated rollback on health check failure; deployment approval gates; release tagging and changelog generation |
| **Dependencies** | C18 Testing Infrastructure, C16.3 Security Scanning |
| **Priority** | **High** |
| **Maturity Target** | Fully automated CI/CD; zero-downtime deployments; automated canary analysis |

### C17.5 — Secrets Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Securely store, rotate, and audit access to all secrets (API keys, database credentials, signing keys). |
| **Responsibilities** | Centralized secrets storage (Vault/KMS/Secrets Manager); secrets never in code, config files, or environment variables; automatic credential rotation; access audit trail; just-in-time access; secret versioning; integration with CI/CD for deployment-time injection |
| **Dependencies** | C1.2 Authentication, C16 Security |
| **Priority** | **Critical** |
| **Maturity Target** | Dynamic secrets (short-lived, per-session); zero standing credentials |

### C17.6 — Backup, Disaster Recovery & Business Continuity

| Attribute | Value |
|-----------|-------|
| **Purpose** | Ensure data durability and service continuity through backup, replication, and DR planning. |
| **Responsibilities** | Automated database backups (daily full, continuous WAL); point-in-time recovery capability; cross-region replication; RPO ≤ 5 minutes; RTO ≤ 30 minutes; DR runbook with automated failover; quarterly DR testing; backup integrity verification |
| **Dependencies** | Database infrastructure |
| **Priority** | **High** |
| **Maturity Target** | Multi-region active-active; chaos engineering resilience testing |

### C17.7 — Rate Limiting & Abuse Prevention

| Attribute | Value |
|-----------|-------|
| **Purpose** | Protect platform resources from abuse, DoS, and excessive consumption. |
| **Responsibilities** | Per-IP rate limiting; per-user rate limiting; per-endpoint rate limiting; graduated response (warn → throttle → block); CAPTCHA integration for suspicious activity; bot detection; API quota management for enterprise tiers |
| **Dependencies** | C1.2 Authentication, C16.1 API Gateway |
| **Priority** | **High** |
| **Maturity Target** | ML-based abuse detection; adaptive rate limiting based on user behavior |

### C17.8 — IT Asset & Dependency Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Track all technology assets, dependencies, and their lifecycle. |
| **Responsibilities** | Dependency inventory with versions; vulnerability scanning; license compliance checking; end-of-life tracking; upgrade planning; dependency graph analysis; SBOM (Software Bill of Materials) generation |
| **Dependencies** | C16.3 Security Scanning |
| **Priority** | **Medium** |
| **Maturity Target** | Automated dependency updates with CI verification; SBOM for every release |

---

## 18. Domain 17: Security & Privacy

### C18.1 — Data Encryption (At Rest & In Transit)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Protect all sensitive data through its entire lifecycle. |
| **Responsibilities** | TLS 1.3 for all data in transit; AES-256 for data at rest; database-level encryption (Transparent Data Encryption); application-level encryption for PAN, Aadhaar, financial data (even if DB is compromised); encrypted backups; key rotation; HSM for key storage (production); certificate management |
| **Dependencies** | C17.5 Secrets Management |
| **Priority** | **Critical** |
| **Maturity Target** | Customer-managed encryption keys (CMEK); quantum-resistant cryptography roadmap |

### C18.2 — Vulnerability Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Continuously identify, prioritize, and remediate security vulnerabilities. |
| **Responsibilities** | Automated vulnerability scanning (SAST, DAST, dependency scanning, container scanning); vulnerability prioritization (CVSS + business context); remediation SLAs by severity (Critical: 24h, High: 72h, Medium: 1 sprint, Low: 2 sprints); penetration testing (annual + per major release); bug bounty program |
| **Dependencies** | C17.4 CI/CD Pipeline |
| **Priority** | **Critical** |
| **Maturity Target** | Continuous automated pentesting; AI-assisted vulnerability triage; zero-day response playbook |

### C18.3 — Data Privacy & DPDP Act Compliance

| Attribute | Value |
|-----------|-------|
| **Purpose** | Ensure full compliance with the Digital Personal Data Protection Act, 2023 and IT Act data protection provisions. |
| **Responsibilities** | Data minimization (collect only what's needed); purpose limitation (use only for stated purposes); consent management (granular, withdrawable); data principal rights (access, correction, erasure, portability); data protection impact assessment (DPIA); privacy by design reviews; data processing records; data breach notification (within 72 hours to Data Protection Board); data retention and deletion policies; cross-border data transfer controls |
| **Dependencies** | C1.8 Consent Management, C15.4 Export & Data Portability |
| **Priority** | **Critical** |
| **Maturity Target** | Automated DPDP Act compliance reporting; privacy engineering embedded in SDLC |

### C18.4 — Access Control & Privilege Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enforce least-privilege access across all systems and data. |
| **Responsibilities** | Role-based access control (RBAC); attribute-based access control (ABAC) for fine-grained policies; just-in-time access for privileged operations; access review (quarterly for all users, monthly for privileged); privilege separation (no single role can read AND modify financial data); break-glass emergency access with full audit |
| **Dependencies** | C1.3 Authorization, C1.2 Authentication |
| **Priority** | **Critical** |
| **Maturity Target** | Zero-trust architecture; policy-as-code; automated access reviews |

### C18.5 — Threat Detection & Response

| Attribute | Value |
|-----------|-------|
| **Purpose** | Detect and respond to security threats in real-time. |
| **Responsibilities** | SIEM integration; intrusion detection; anomaly-based threat detection; automated incident response playbooks; security operations center (SOC) — in-house or MSSP; threat intelligence feeds; security event correlation; forensic investigation capability |
| **Dependencies** | C17.2 Monitoring & Observability, C17.3 Logging |
| **Priority** | **High** |
| **Maturity Target** | AI-powered threat hunting; automated containment; threat intelligence sharing |

### C18.6 — Secure Development Lifecycle

| Attribute | Value |
|-----------|-------|
| **Purpose** | Embed security into every phase of the development lifecycle. |
| **Responsibilities** | Security requirements in feature specs; threat modeling for new features; secure code review; security testing in CI/CD; security champions program; developer security training; secure coding standards; third-party security assessment for major releases |
| **Dependencies** | C17.3 Development Standards, C17.4 CI/CD Pipeline |
| **Priority** | **High** |
| **Maturity Target** | Automated threat modeling; security unit tests; continuous security regression testing |

### C18.7 — Identity Proofing & KYC

| Attribute | Value |
|-----------|-------|
| **Purpose** | Verify taxpayer identity to appropriate assurance levels per regulatory requirements. |
| **Responsibilities** | PAN verification (NSDL); Aadhaar e-KYC (UIDAI); name matching across identity documents; face match (optional, for high-assurance tier); document verification (PAN card image, Aadhaar letter); identity assurance level assignment (IAL1/IAL2); periodic re-verification |
| **Dependencies** | C1.1 Registration, C15.2 External Tax Authority APIs |
| **Priority** | **High** |
| **Maturity Target** | Video KYC for high-assurance tier; blockchain-based identity; AA framework identity |

### C18.8 — Data Loss Prevention

| Attribute | Value |
|-----------|-------|
| **Purpose** | Prevent unauthorized exfiltration of sensitive taxpayer data. |
| **Responsibilities** | Data classification tagging; DLP policies (block PAN/Aadhaar in unauthorized channels); egress filtering; download controls; copy-paste restrictions on sensitive screens; watermarking on sensitive documents; unusual data access pattern detection |
| **Dependencies** | C18.3 Data Privacy, C18.5 Threat Detection |
| **Priority** | **High** |
| **Maturity Target** | ML-based exfiltration detection; automated DLP policy enforcement |

### C18.9 — Tenant Isolation (Enterprise)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Ensure strict data isolation between tenants in multi-tenant enterprise deployments. |
| **Responsibilities** | Database-level tenant isolation (row-level security or schema-per-tenant); query-level tenant filtering (every query includes tenant_id); tenant context propagation (never rely on client to specify tenant); cross-tenant access prevention; tenant data segregation testing; tenant-specific encryption keys (optional, for high-security tenants) |
| **Dependencies** | C20 Enterprise Multi-Tenancy, C18.4 Access Control |
| **Priority** | **Critical** |
| **Maturity Target** | Tenant-specific KMS keys; cryptographic tenant isolation; tenant boundary penetration testing |

### C18.10 — Security Compliance Framework

| Attribute | Value |
|-----------|-------|
| **Purpose** | Maintain compliance with applicable security standards and frameworks. |
| **Responsibilities** | ISO 27001 ISMS implementation; SOC 2 Type II controls; CERT-IN guidelines compliance; IT Act reasonable security practices; RBI guidelines (if payment integration); GDPR (if serving EU residents); annual external audit; continuous control monitoring; compliance evidence collection |
| **Dependencies** | All security capabilities |
| **Priority** | **Critical** |
| **Maturity Target** | Continuous compliance monitoring; automated evidence collection; ISO 27001 certification |

---

## 19. Domain 18: Notification & Communication

### C19.1 — Multi-Channel Notification Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Deliver timely, relevant notifications to taxpayers across their preferred channels. |
| **Responsibilities** | Channel support: email, SMS, push notification (web + mobile), in-app notification, WhatsApp (optional); template-based notification design; personalization (name, amounts, context); delivery status tracking; bounce/failure handling; channel preference management; notification frequency control; do-not-disturb scheduling |
| **Dependencies** | C1.6 Profile Management, Email/SMS/Push infrastructure |
| **Priority** | **High** |
| **Maturity Target** | ML-optimized send times; A/B tested notification templates; WhatsApp Business API |

### C19.2 — Deadline Reminder System

| Attribute | Value |
|-----------|-------|
| **Purpose** | Proactively remind taxpayers of upcoming and missed tax deadlines. |
| **Responsibilities** | Advance tax installment reminders (5 days before each due date); ITR filing deadline reminders (30, 15, 7, 3, 1 days before); belated/revised return deadline reminders; PAN-Aadhaar linking deadline; missed deadline alerts with consequence explanation; personalized based on taxpayer's applicable deadlines |
| **Dependencies** | C8.9 Compliance Calendar, C19.1 Notification Engine |
| **Priority** | **High** |
| **Maturity Target** | Personalized deadline calendar per taxpayer; multi-channel escalation for missed deadlines |

### C19.3 — Filing Status Updates

| Attribute | Value |
|-----------|-------|
| **Purpose** | Keep taxpayers informed about the status of their filing and refund. |
| **Responsibilities** | Filing submitted → ITD acknowledgement received → ITR processed → Refund issued → Refund credited; status change notifications; estimated timeline communication; delay notifications with context ("ITD typically takes 30-45 days"); action-required notifications ("E-Verify your return within 30 days") |
| **Dependencies** | C15.7 Refund Tracker, C19.1 Notification Engine |
| **Priority** | **Medium** |
| **Maturity Target** | Real-time ITD status integration; predictive timeline estimation |

### C19.4 — In-App Communication Center

| Attribute | Value |
|-----------|-------|
| **Purpose** | Central in-app hub for all platform communications, updates, and alerts. |
| **Responsibilities** | Notification history; message center with read/unread; priority inbox (action-required vs informational); platform announcements; tax law change notifications; feature update notifications; support message thread |
| **Dependencies** | C19.1 Notification Engine |
| **Priority** | **Medium** |
| **Maturity Target** | Rich-media notifications; interactive notifications (act directly from notification) |

### C19.5 — Regulatory Update Broadcast

| Attribute | Value |
|-----------|-------|
| **Purpose** | Proactively inform taxpayers about regulatory changes that affect them. |
| **Responsibilities** | Budget day summary (personalized by taxpayer profile); Finance Act changes that affect the taxpayer; CBDT circular/notification alerts; ITR form change announcements; due date extension announcements; personalized impact summary ("New tax slabs could save you ₹X") |
| **Dependencies** | C11.3 Finance Act Change Analyzer, C19.1 Notification Engine |
| **Priority** | **Medium** |
| **Maturity Target** | Personalized regulatory impact briefs; Budget day live analysis; proactive tax planning alerts |

---

## 20. Domain 19: Tax Planning & Scenario Simulation

### C20.1 — What-If Scenario Simulator

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable taxpayers to simulate the tax impact of different life and financial decisions. |
| **Responsibilities** | Simulate: job change (salary change), house purchase (home loan), investment changes (more/less 80C), regime switch, marriage (joint filing implications), child birth (additional deductions), relocation (metro vs non-metro, state change), retirement (pension income), business start; parameterized scenarios with slider-based adjustment; side-by-side scenario comparison; confidence intervals for projections |
| **Dependencies** | C6 Tax Computation Engine, C7 Regime Optimization, C19 Tax Planning |
| **Priority** | **Medium** |
| **Maturity Target** | ML-driven scenario suggestions; multi-year projections; "optimize for" goal-based planning |

### C20.2 — Tax-Loss Harvesting Advisor

| Attribute | Value |
|-----------|-------|
| **Purpose** | Identify and recommend tax-loss harvesting opportunities in the taxpayer's investment portfolio. |
| **Responsibilities** | Scan portfolio for unrealized losses; compute tax benefit of harvesting each loss; consider STT implications; consider wash-sale rules; consider holding period impact; recommend specific lots to sell; estimate net tax saving after transaction costs |
| **Dependencies** | C5.2 Capital Gains Engine, C16.3 Financial Institution Integration |
| **Priority** | **Medium** |
| **Maturity Target** | Direct broker integration for one-click harvesting; automated portfolio monitoring |

### C20.3 — Multi-Year Tax Projection

| Attribute | Value |
|-----------|-------|
| **Purpose** | Project tax liability across multiple future years based on income and life event assumptions. |
| **Responsibilities** | Income growth assumptions; inflation adjustments to limits and thresholds (where applicable); regime transition planning; major life event modeling; retirement tax planning; education expense planning; estate/inheritance tax implications; visualization of tax trajectory |
| **Dependencies** | C6 Tax Computation Engine, C20.1 Scenario Simulator |
| **Priority** | **Medium** |
| **Maturity Target** | 10-year projections; Monte Carlo simulation for uncertainty; retirement tax optimization |

### C20.4 — Investment Tax Optimization

| Attribute | Value |
|-----------|-------|
| **Purpose** | Optimize investment choices for tax efficiency across the taxpayer's portfolio. |
| **Responsibilities** | Asset location optimization (which assets in which account types); tax-efficient fund selection; holding period optimization (LTCG vs STCG tradeoffs); dividend vs growth option analysis; ELSS vs other 80C options analysis; NPS tier-1 vs tier-2 analysis; PPF vs EPF vs VPF comparison |
| **Dependencies** | C5.2 Capital Gains Engine, C6.1 Deduction Engine, C16.3 Financial Institution Integration |
| **Priority** | **Medium** |
| **Maturity Target** | Portfolio-aware tax optimization; automated tax-efficient rebalancing suggestions |

### C20.5 — Retirement Tax Planning

| Attribute | Value |
|-----------|-------|
| **Purpose** | Help taxpayers plan for tax-efficient retirement income and withdrawals. |
| **Responsibilities** | Retirement corpus projection; withdrawal strategy optimization (which account to draw from first); SWP (Systematic Withdrawal Plan) tax analysis; annuity vs lump-sum analysis; senior citizen tax benefit optimization; reverse mortgage tax implications; pension commutation analysis |
| **Dependencies** | C6 Tax Computation Engine, C20.3 Multi-Year Projection |
| **Priority** | **Low** |
| **Maturity Target** | Comprehensive retirement tax calculator; integration with retirement planning tools |

---

## 21. Domain 20: Enterprise Multi-Tenancy

### C21.1 — Tenant Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Manage the lifecycle of enterprise tenants (CA firms, corporations, tax consultancies). |
| **Responsibilities** | Tenant creation and configuration; tenant branding (logo, colors, domain); tenant-specific feature enablement; tenant billing plan management; tenant usage monitoring; tenant suspension/reactivation; tenant data export for offboarding |
| **Dependencies** | C1.3 Authorization, C18.9 Tenant Isolation |
| **Priority** | **Critical** |
| **Maturity Target** | Self-service tenant onboarding; tenant configuration templates; tenant health scoring |

### C21.2 — Multi-Role Hierarchy (CA Firm)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Model the organizational hierarchy of a CA firm with appropriate access controls. |
| **Responsibilities** | Role hierarchy: Firm Admin → Senior CA → Junior CA → Article Clerk → Support Staff; client assignment (CA ↔ clients); supervision workflows (Junior CA prepares, Senior CA reviews, Partner approves); activity tracking per staff member; workload distribution and balancing |
| **Dependencies** | C1.3 Authorization, C21.1 Tenant Management |
| **Priority** | **High** |
| **Maturity Target** | Org chart visualization; workload analytics; permission templates per role |

### C21.3 — Client Portfolio Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable CA firms to manage their client portfolio with bulk operations and oversight. |
| **Responsibilities** | Client onboarding (bulk import, individual invite); client categorization (ITR type, complexity, risk level); client status dashboard (not started, in progress, ready for review, filed, completed); bulk operations (send reminder to all unfiled clients, download all ITR JSONs); client communication log; client document vault |
| **Dependencies** | C2 Taxpayer Management, C21.2 Multi-Role Hierarchy |
| **Priority** | **Critical** |
| **Maturity Target** | AI-assisted client prioritization; deadline-based workload management; automated client reminders |

### C21.4 — Firm-Level Dashboard & Analytics

| Attribute | Value |
|-----------|-------|
| **Purpose** | Provide CA firm leadership with firm-wide analytics and operational metrics. |
| **Responsibilities** | Filing completion rate (overall and per staff); revenue analytics; client retention analytics; error/rejection rate analytics; staff productivity metrics; SLA compliance (promised vs actual filing dates); peak season capacity planning; year-over-year firm growth metrics |
| **Dependencies** | C14 Reporting, C21.1 Tenant Management, C21.3 Client Portfolio |
| **Priority** | **High** |
| **Maturity Target** | Predictive capacity planning; AI-assisted workload optimization; firm benchmarking |

### C21.5 — White-Label / Embedded Capability

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable the platform to be white-labeled or embedded within partner applications. |
| **Responsibilities** | White-label branding (partner logo, colors, domain); embedded iframe/widget mode; API-only mode (partner builds own UI on platform APIs); co-branded mode (partner + platform branding); partner-specific feature configuration; partner-specific pricing |
| **Dependencies** | C16.1 API Gateway, C21.1 Tenant Management |
| **Priority** | **Medium** |
| **Maturity Target** | Embedded tax filing widget; white-label mobile app; partner SDK |

### C21.6 — Enterprise SSO & Directory Integration

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable enterprise tenants to use their own identity provider for authentication. |
| **Responsibilities** | SAML 2.0 integration; OpenID Connect integration; Azure AD / Google Workspace integration; Okta / OneLogin / other IdP; Just-in-time user provisioning; SCIM for user lifecycle management; role mapping from IdP groups to platform roles |
| **Dependencies** | C1.2 Authentication, C1.3 Authorization |
| **Priority** | **High** |
| **Maturity Target** | Auto-provisioning from IdP; directory sync; IdP-initiated SSO |

### C21.7 — Enterprise Audit & Compliance Reports

| Attribute | Value |
|-----------|-------|
| **Purpose** | Provide enterprise-grade audit capabilities for tenant administrators. |
| **Responsibilities** | Full audit log of all actions within the tenant; user activity reports; data access reports; client data change log; export audit logs for external compliance; SIEM integration for tenant security monitoring |
| **Dependencies** | C10.1 Audit Trail, C17.3 Logging, C18.9 Tenant Isolation |
| **Priority** | **High** |
| **Maturity Target** | SOC 2-compliant audit reports; automated compliance evidence collection per tenant |

### C21.8 — Enterprise Billing & Subscription

| Attribute | Value |
|-----------|-------|
| **Purpose** | Manage enterprise billing with usage-based and subscription models. |
| **Responsibilities** | Subscription plan management; per-return pricing; per-client pricing; tiered pricing (by client count, return complexity); invoice generation; payment collection; usage tracking; plan upgrade/downgrade; free trial management |
| **Dependencies** | C21.1 Tenant Management, Payment gateway |
| **Priority** | **Medium** |
| **Maturity Target** | Usage-based billing; prepaid credit model; automated invoicing with GST compliance |

---

## 22. Bounded Context Map

### 22.1 Bounded Context Identification

The 148 capabilities group into the following bounded contexts, following Domain-Driven Design principles:

| # | Bounded Context | Domain | Capabilities | Core/Supporting/Generic |
|---|----------------|--------|-------------|------------------------|
| BC1 | **Identity & Access** | 1 | C1.1-C1.8 | Supporting |
| BC2 | **Taxpayer** | 2, 20 | C2.1-C2.7, C21.1-C21.3 | Core |
| BC3 | **Document Processing** | 3 | C3.1-C3.10 | Core |
| BC4 | **Income** | 4, 5 | C4.1-C4.8, C5.1-C5.7 | Core |
| BC5 | **Tax Computation** | 6, 7 | C6.1-C6.8, C7.1-C7.6 | Core |
| BC6 | **Compliance** | 8, 9 | C8.1-C8.9, C9.1-C9.7 | Core |
| BC7 | **Audit & Explanation** | 10 | C10.1-C10.6 | Core |
| BC8 | **Knowledge & Rules** | 11, 12 | C11.1-C11.6, C12.1-C12.7 | Core |
| BC9 | **Interview** | 13 | C13.1-C13.8 | Core |
| BC10 | **Reporting** | 14 | C14.1-C14.7 | Supporting |
| BC11 | **Integration** | 15 | C15.1-C15.8 | Supporting |
| BC12 | **Operations** | 16 | C16.1-C16.8 | Generic |
| BC13 | **Security** | 17 | C17.1-C17.10 | Generic |
| BC14 | **Notification** | 18 | C18.1-C18.5 | Generic |
| BC15 | **Tax Planning** | 19 | C19.1-C19.5 | Supporting |

### 22.2 Context Relationships

```
                          ┌─────────────────┐
                          │   Knowledge &    │
                          │   Rules (BC8)    │◄──────────┐
                          └────────┬────────┘           │
                                   │                     │
                    ┌──────────────┼──────────────┐      │
                    │              │              │      │
                    ▼              ▼              ▼      │
             ┌──────────┐  ┌────────────┐  ┌──────────┐ │
             │Document  │  │   Income   │  │   Tax    │ │
             │Processing│  │Management  │  │Computation│ │
             │  (BC3)   │  │   (BC4)    │  │  (BC5)   │ │
             └────┬─────┘  └─────┬──────┘  └────┬─────┘ │
                  │              │               │       │
                  └──────────────┼───────────────┘       │
                                 │                       │
                    ┌────────────┼──────────────┐        │
                    │            │              │        │
                    ▼            ▼              ▼        │
             ┌──────────┐  ┌──────────┐  ┌────────────┐ │
             │Interview │  │Compliance│  │  Audit &   │ │
             │  (BC9)   │  │  (BC6)   │  │Explanation │ │
             └────┬─────┘  └────┬─────┘  │  (BC7)     │ │
                  │             │        └─────┬──────┘ │
                  │             │              │        │
                  └─────────────┼──────────────┘        │
                                │                        │
                                ▼                        │
                         ┌────────────┐                  │
                         │   ITR Gen  │                  │
                         │  & Filing  │                  │
                         └─────┬──────┘                  │
                               │                         │
                               ▼                         │
                         ┌────────────┐                  │
                         │ Reporting  │                  │
                         │  (BC10)    │                  │
                         └────────────┘                  │
                                                        │
         Supporting & Generic Contexts:                  │
         ┌──────────┐ ┌──────────┐ ┌──────────┐         │
         │ Identity │ │Integration│ │Operations│         │
         │(BC1)     │ │(BC11)    │ │(BC12)   │         │
         └──────────┘ └──────────┘ └──────────┘         │
         ┌──────────┐ ┌──────────┐ ┌──────────┐         │
         │ Security │ │Notification│ │  Tax    │         │
         │(BC13)    │ │(BC14)    │ │Planning  │─────────┘
         └──────────┘ └──────────┘ │(BC15)    │
                                   └──────────┘
```

### 22.3 Context Communication Patterns

| From → To | Pattern | Data |
|-----------|---------|------|
| BC3 Document → BC4 Income | Synchronous (parsed data) | Form16Data, AISData |
| BC4 Income → BC5 Tax Computation | Synchronous (computation inputs) | Income per head, Deductions |
| BC8 Knowledge → BC4 Income | Synchronous (rule lookup) | Applicable rules, limits |
| BC8 Knowledge → BC5 Tax Computation | Synchronous (rule lookup) | Slabs, rates, thresholds |
| BC5 Tax Computation → BC6 Compliance | Synchronous (validation inputs) | Computation results |
| BC6 Compliance → BC9 Interview | Asynchronous (data gaps) | Missing data requirements |
| BC9 Interview → BC4 Income | Synchronous (user answers) | User-provided income/deduction data |
| BC3 Document → BC5 Tax Computation | Synchronous (salary, TDS data) | Extracted salary, deductions |
| BC5 Tax Computation → BC7 Audit | Event-driven (computation events) | ComputationStep events |
| BC7 Audit → BC8 Knowledge | Synchronous (provision lookup) | Legal provisions for explanation |
| BC4 Income → BC7 Audit | Event-driven (income events) | Income computation events |
| BC6 Compliance → BC7 Audit | Event-driven (validation events) | Validation results |
| BC3 Document → BC6 Compliance | Synchronous (cross-validation) | Document data for reconciliation |
| BC14 Notification → All contexts | Event-driven (notifications) | Deadline, status, alert events |
| BC13 Security → All contexts | Interceptor pattern | Auth, RBAC, audit, encryption |

---

## 23. Cross-Cutting Capabilities

These capabilities span multiple bounded contexts and must be implemented consistently across the platform:

### 23.1 Cross-Cutting Capability Map

| Cross-Cutting Capability | Touches BCs | Implementation Pattern |
|--------------------------|------------|----------------------|
| **Authentication & Authorization** | All | Interceptor/Middleware — every context checks auth before processing |
| **Audit Trail** | BC4, BC5, BC6, BC7, BC9 | Event-sourced — every domain event is recorded |
| **Structured Logging** | All | Standardized logger with correlation IDs, PII masking |
| **Error Handling** | All | Consistent error codes, domain exceptions, API error format |
| **Data Validation** | BC3, BC4, BC5, BC6, BC9 | Validation at every context boundary; Pydantic/JSON Schema |
| **Configuration Management** | All | Centralized config with context-specific schemas |
| **Feature Flags** | All | Per-tenant, per-context feature toggles |
| **Internationalization (i18n)** | BC9, BC10, BC14, BC7 | Translation service available to all contexts |
| **Rate Limiting** | BC11 (API Gateway) | Per-consumer, per-endpoint token bucket |
| **Encryption** | All (data at rest), BC11 (in transit) | Encryption service; PII encryption before persistence |
| **Tenant Isolation** | BC2, BC4, BC5, BC6, BC7, BC9, BC10 | Tenant context propagation; query-level filtering |
| **Correlation ID** | All | UUID per request; propagated across all context boundaries |
| **Health Check** | All | Standardized health endpoint per context |
| **Metrics** | All | Standard metrics (latency, errors, throughput) per context |

---

## 24. Capability Dependency Matrix

### 24.1 Critical Path Dependencies

```
C1.1 Registration ──── C2.1 Taxpayer Profile
    │                        │
    ├── C1.2 Auth             ├── C2.2 Residential Status
    ├── C1.3 RBAC             ├── C2.3 Filing Status
    └── C1.8 Consent          ├── C2.4 ITR Eligibility
                              │
C3.1 Doc Ingestion            │
    │                         │
    ├── C3.2 PDF Password     │
    ├── C3.3 Form 16 Parser ──┤
    ├── C3.4 AIS Parser ──────┤
    ├── C3.5 OCR ─────────────┤
    └── C3.6 AIS Code Class ──┤
                              │
C12.1 Finance Act Versioning  │
    │                         │
    ├── C12.2 Rule Definition  │
    ├── C12.3 Rule Repository  │
    └── C12.4 Rule Evaluation──┤
                              │
                              ▼
                    C4 Income Management ── C5 Deduction Engine
                              │
                              ▼
                    C6 Tax Computation ─── C7 Regime Optimization
                              │
                              ▼
                    C8 Compliance ───────── C9 ITR Generation
                              │
                              ▼
                    C10 Audit & Explain ─── C14 Reporting
```

### 24.2 Implementation Priority Matrix

| Wave | Capabilities | Rationale |
|------|-------------|-----------|
| **Wave 1: Foundation** | C1.1-C1.5, C12.1-C12.4, C17.1-C17.5 | Cannot build anything without auth + rules + platform |
| **Wave 2: Core Tax** | C3.1-C3.6, C4.1-C4.5, C5.1-C5.3, C6.1-C6.6, C7.1 | The minimum viable tax computation pipeline |
| **Wave 3: Filing** | C8.1-C8.5, C9.1-C9.3, C9.6, C10.1-C10.3 | Can compute tax → can generate ITR → can explain it |
| **Wave 4: Intelligence** | C7.2-C7.6, C8.6-C8.9, C10.4-C10.6, C11.1-C11.6, C13.1-C13.8 | AI interviews, knowledge graph, advanced optimization |
| **Wave 5: Enterprise** | C20.1-C20.8, C14.1-C14.7, C15.1-C15.8 | Multi-tenancy, reporting, integrations |
| **Wave 6: Ecosystem** | C16.1-C16.8, C18.18.5, C19.1-C19.5 | APIs, notifications, tax planning, SSO |

---

*End of Enterprise Capability Model*

*This document defines the complete target state. The Gap Analysis and Modernization Roadmap will use this as the benchmark against which the current platform (documented in the Architecture Recovery Report) is measured.*
