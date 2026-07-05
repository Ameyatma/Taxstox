# AI-DOS Chief Architect v1.0.0

> **Status:** GOVERNANCE DOCUMENT — Level 4 Authority
> **Supersedes:** Nothing
> **Ratified:** 2026-07-05
> **Last Amended:** 2026-07-05
> **Next Review:** 2026-10-05
> **Author:** Chief Architect
> **Applies To:** All architecture decisions, all ADRs, all module boundaries
> **Parent Document:** [00-Constitution.md](00-Constitution.md)

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Scope](#2-scope)
3. [Role of the Chief Architect](#3-role-of-the-chief-architect)
4. [Architecture Decision Records (ADRs)](#4-architecture-decision-records-adrs)
5. [ADR Template](#5-adr-template)
6. [ADR Lifecycle](#6-adr-lifecycle)
7. [Architecture Review Board](#7-architecture-review-board)
8. [Module Boundary Enforcement](#8-module-boundary-enforcement)
9. [Technology Stack Governance](#9-technology-stack-governance)
10. [Cross-Cutting Concerns](#10-cross-cutting-concerns)
11. [Technical Debt Management](#11-technical-debt-management)
12. [Architecture Documentation](#12-architecture-documentation)
13. [Architecture Evolution](#13-architecture-evolution)
14. [Architecture Quality Metrics](#14-architecture-quality-metrics)
15. [Failure Cases and Remedies](#15-failure-cases-and-remedies)
16. [ADR Index](#16-adr-index)
17. [Appendices](#17-appendices)

---

## 1. Purpose

### 1.1 Why This Document Exists

The Constitution ([00-Constitution.md](00-Constitution.md)) establishes Principle P2: **Architecture First, Code Second**. This document operationalizes that principle. It defines:

- **Who** makes architecture decisions and under what authority
- **How** architecture decisions are recorded, reviewed, and enforced
- **What** constitutes an architecture decision vs. an implementation detail
- **Where** architecture knowledge lives and how it is retrieved
- **When** architecture must be reviewed and how it evolves

### 1.2 Relationship to Constitution

This document is Level 4 authority under the Constitution's Decision Hierarchy (§7). It derives its authority from Constitutional Principles P2 (Architecture First), P9 (Knowledge Preservation), and P10 (Extensibility Without Modification).

When this document conflicts with any Level 5-8 document, this document wins. When this document conflicts with Levels 1-3 (Legal, Constitutional Principles, Architectural Invariants), the higher level wins.

---

## 2. Scope

### 2.1 What Falls Under Architecture Governance

| Decision Type | Architecture? | ADR Required? | Who Decides? |
|---------------|---------------|---------------|--------------|
| New microservice / module | ✅ Yes | ✅ Yes | Chief Architect |
| Module boundary change | ✅ Yes | ✅ Yes | Chief Architect |
| New external dependency | ✅ Yes | ✅ Yes | Chief Architect + Security Lead |
| API contract definition | ✅ Yes | ✅ Yes (if cross-module) | Tech Lead + Chief Architect |
| Data model that spans modules | ✅ Yes | ✅ Yes | Chief Architect |
| New integration pattern | ✅ Yes | ✅ Yes | Chief Architect |
| Security architecture change | ✅ Yes | ✅ Yes | Security Lead + Chief Architect |
| Technology stack change | ✅ Yes | ✅ Yes | Chief Architect |
| Performance architecture | ✅ Yes | ✅ Yes | Chief Architect |
| Deployment architecture | ✅ Yes | ✅ Yes | DevOps Lead + Chief Architect |
| Code organization within module | ❌ No | ❌ No | Tech Lead |
| Algorithm choice within function | ❌ No | ❌ No | Developer/Agent |
| Variable naming | ❌ No | ❌ No | Developer/Agent |
| Test framework choice | ✅ Yes (if new) | ✅ Yes | Tech Lead + Chief Architect |
| CI/CD pipeline design | ✅ Yes | ✅ Yes | DevOps Lead + Chief Architect |
| Database schema within module | ❌ No | ❌ No (unless shared) | Tech Lead |
| Logging format | ✅ Yes | ✅ Yes | Chief Architect |
| Error handling pattern | ✅ Yes | ✅ Yes | Chief Architect |

### 2.2 The Architecture Boundary Test

Ask: "If this decision is made differently by two different teams, does it cause integration problems, inconsistency that violates P1, or prevent future extensibility (P10)?"

If YES → Architecture decision → ADR required.
If NO → Implementation detail → Module autonomy.

---

## 3. Role of the Chief Architect

### 3.1 Authority and Accountability

The Chief Architect is the ultimate authority on all architecture decisions below the Constitutional level. They are accountable for:

1. **Architecture Integrity:** The system's architecture remains coherent, documented, and aligned with the Constitution
2. **ADR Quality:** Every ADR is thorough, considers alternatives, and documents consequences
3. **Module Boundaries:** Boundaries are clear, enforced, and respected
4. **Technical Debt:** Debt is visible, measured, and systematically reduced
5. **Technology Stack:** The stack is appropriate, current, and secure
6. **Cross-Cutting Quality:** Performance, security, reliability, observability — designed in, not bolted on

### 3.2 Responsibilities

| Responsibility | Cadence | Output |
|----------------|---------|--------|
| ADR approval | Per ADR | Approved/Rejected/Needs Revision |
| Architecture review board chair | Weekly | Meeting minutes, action items |
| Architecture documentation maintenance | Continuous | Updated `12-Enterprise-Architecture.md` |
| Technical debt review | Bi-weekly | Updated debt register |
| Technology stack review | Quarterly | Stack health report |
| Architecture evolution planning | Quarterly | Evolution roadmap |
| Cross-module conflict resolution | As needed | Resolution decision |
| Mentoring tech leads | Continuous | — |

### 3.3 What the Chief Architect Does NOT Do

- Write production code (except reference implementations)
- Make product decisions (those belong to Product Director)
- Dictate implementation details within modules
- Override security decisions made by Security Lead
- Approve tax rule correctness (that belongs to Domain Experts)

---

## 4. Architecture Decision Records (ADRs)

### 4.1 What Is an ADR?

An Architecture Decision Record is a structured document that captures:

- **Context:** The situation that demands a decision
- **Decision:** What was decided
- **Alternatives:** What other options were considered and why they were rejected
- **Consequences:** What becomes easier, harder, or different because of this decision
- **Status:** Proposed, Accepted, Deprecated, Superseded

### 4.2 When Is an ADR Required?

An ADR is required BEFORE implementation begins for any decision listed in §2.1 as requiring an ADR.

**Trigger Events:**

- Starting a new module or service
- Changing a module's public API
- Adding a new external dependency
- Changing the way modules communicate
- Changing the data model in a way that affects multiple modules
- Introducing a new technology
- Deprecating an existing technology
- Changing the deployment architecture
- Changing the security architecture
- Any decision where two reasonable engineers could disagree

### 4.3 When Is an ADR NOT Required?

- Bug fixes (even complex ones, unless they change architecture)
- Adding a function within an existing module
- Refactoring within a module that doesn't change its public API
- Updating a dependency to a compatible version
- Adding tests
- Documentation changes
- Configuration changes (unless they change system behavior at the architectural level)

### 4.4 ADR File Naming and Storage

```
ai-dos/adr/
├── README.md                  # ADR index with status
├── template.md                # ADR template
├── 0001-use-postgresql.md     # ADRs in sequence
├── 0002-use-event-sourcing.md
├── 0003-tax-rule-engine.md
├── ...
└── superseded/                # Deprecated/superseded ADRs
    ├── 0001-old-decision.md
    └── ...
```

**Naming Convention:** `NNNN-brief-slug.md`

- `NNNN`: Zero-padded sequential number (0001, 0002, ...)
- `slug`: Lowercase, hyphen-separated, describes the decision in 3-6 words

### 4.5 ADR Commitment

Once an ADR is **Accepted**, all code must conform to it. Code that violates an active ADR is architectural debt. Code that implements an architecture without a corresponding ADR is also architectural debt.

---

## 5. ADR Template

Every ADR must use this exact template. No sections may be omitted.

```markdown
# ADR-NNNN: [Brief Title of Decision]

> **Status:** [Proposed | Accepted | Deprecated | Superseded]
> **Date:** YYYY-MM-DD
> **Author:** [Name/Role]
> **Reviewers:** [Name/Role, Name/Role]
> **Supersedes:** [ADR-NNNN or None]
> **Superseded By:** [ADR-NNNN or None]
> **Applies To:** [Module names or "All modules"]
> **Constitutional Principles:** [P1-P10 that this ADR primarily serves]

---

## 1. Context

### 1.1 Problem Statement

[Describe the problem or opportunity in 2-4 sentences. What situation demands a decision?]

### 1.2 Background

[Provide relevant background: current architecture, constraints, business requirements, technical limitations.]

### 1.3 Stakeholders

| Stakeholder | Role | Interest |
|-------------|------|----------|
| [Name/Role] | [Role] | [What they care about] |

### 1.4 Constraints

- [Constraint 1: e.g., "Must support FY2020-21 through FY2030-31"]
- [Constraint 2: e.g., "Must work offline"]
- [Constraint 3: e.g., "Must comply with DPDP Act 2023"]

---

## 2. Decision

### 2.1 Decision Statement

[State the decision clearly in 1-3 sentences. Use active voice. Be specific.]

### 2.2 Decision Details

[Explain the decision in detail. Include diagrams if helpful. Describe the architecture pattern, technology choice, or design approach.]

### 2.3 Implementation Outline

[High-level outline of how this decision will be implemented. Not detailed code, but the approach.]

---

## 3. Alternatives Considered

### 3.1 Alternative A: [Name]

**Description:** [What this alternative is]

**Pros:**
- [Pro 1]
- [Pro 2]

**Cons:**
- [Con 1]
- [Con 2]

**Why Rejected:** [1-2 sentences explaining why this alternative was not chosen]

### 3.2 Alternative B: [Name]

[Same structure. At minimum, 2 alternatives must be documented.]

### 3.3 Alternative C: [Name]

[If applicable. More than 3 alternatives suggests over-analysis; fewer than 2 suggests under-analysis.]

---

## 4. Consequences

### 4.1 Positive Consequences

- [What becomes easier, better, or faster]
- [What risks are mitigated]

### 4.2 Negative Consequences

- [What becomes harder, slower, or more complex]
- [What new risks are introduced]
- [What trade-offs are being accepted]

### 4.3 Mitigation of Negative Consequences

[For each negative consequence, how will it be mitigated?]

---

## 5. Compliance

### 5.1 Constitutional Alignment

| Principle | How This Decision Aligns |
|-----------|--------------------------|
| P1: Consistency | [Explanation] |
| P2: Architecture First | [Explanation] |
| ... | ... |

### 5.2 Architectural Invariants

- [ ] I1: Multi-Year Architecture — [Does this decision support multi-year?]
- [ ] I2: Rule-Engine Separation — [Does this decision maintain separation?]
- [ ] I3: Complete Audit Trail — [Does this decision support audit trails?]
- [ ] I4: Explainability — [Does this decision support explainability?]
- [ ] I5: Data Isolation — [Does this decision maintain data isolation?]
- [ ] I6: Idempotency — [Does this decision support idempotency?]
- [ ] I7: Zero Data Loss — [Does this decision support zero data loss?]
- [ ] I8: Configurable Everything — [Does this decision support configurability?]
- [ ] I9: Graceful Degradation — [Does this decision support graceful degradation?]
- [ ] I10: Offline Capability — [Does this decision support offline operation?]

### 5.3 Security Considerations

[Security impact of this decision. Must be reviewed by Security Lead if the decision touches authentication, authorization, data access, or network boundaries.]

---

## 6. Migration Plan

### 6.1 If This Is a Change to Existing Architecture

- [ ] Migration steps defined
- [ ] Backward compatibility plan
- [ ] Deprecation timeline for old approach
- [ ] Rollback plan if migration fails

### 6.2 If This Is a New Addition

- [ ] Integration points with existing architecture identified
- [ ] Existing modules that need to be aware of this decision listed

---

## 7. References

- [Related ADR-NNNN: Title]
- [Relevant documentation]
- [External references]
```

---

## 6. ADR Lifecycle

### 6.1 State Machine

```
                    ┌──────────┐
                    │ Proposed │
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
        ┌─────────┐ ┌────────┐ ┌──────────┐
        │Accepted │ │Rejected│ │  Needs    │
        └────┬────┘ └────────┘ │ Revision  │
             │                  └─────┬─────┘
             │                        │
             │              (author revises)
             │                        │
             │                        ▼
             │                  ┌──────────┐
             │                  │ Proposed │
             │                  └──────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
┌───────────┐ ┌───────────┐
│Deprecated │ │Superseded │
│(no longer │ │(replaced  │
│ relevant) │ │ by newer  │
└───────────┘ │ ADR)      │
              └───────────┘
```

### 6.2 Status Definitions

| Status | Meaning | When Used |
|--------|---------|-----------|
| **Proposed** | Under review, not yet accepted | Initial submission |
| **Accepted** | Approved and in effect | After review board approval |
| **Rejected** | Not approved, will not be implemented | After review board rejection |
| **Needs Revision** | Feedback provided, author must revise | During review |
| **Deprecated** | No longer relevant (technology removed, module decommissioned) | When the decision is no longer applicable |
| **Superseded** | Replaced by a newer ADR | When a new ADR explicitly replaces this one |

### 6.3 ADR Review Process

```
1. AUTHOR: Write ADR using template in §5
   └── Mark status as "Proposed"

2. AUTHOR: Submit ADR as a PR to ai-dos/adr/
   └── Include "ADR:" prefix in PR title
   └── No code changes in the ADR PR (code comes in a separate PR)

3. REVIEW BOARD: Review ADR within 2 business days
   ├── Check: Problem is clearly stated
   ├── Check: At least 2 alternatives are considered
   ├── Check: Consequences are documented (positive and negative)
   ├── Check: Constitutional alignment is verified
   ├── Check: Security considerations are addressed
   ├── Check: Invariant compliance is checked
   └── Decision: Accept / Reject / Needs Revision

4. If ACCEPTED:
   ├── Merge ADR PR
   ├── Update ADR index (adr/README.md)
   ├── Create implementation issues linked to ADR
   └── Status: Accepted

5. If NEEDS REVISION:
   ├── Reviewer adds comments to PR
   ├── Author revises and re-submits
   └── Review cycle repeats

6. If REJECTED:
   ├── PR is closed (not merged)
   ├── Rationale for rejection is documented in the closed PR
   └── ADR file moved to adr/rejected/ for historical record
```

### 6.4 ADR Review Timebox

| ADR Complexity | Max Review Time | Reviewer Allocation |
|----------------|-----------------|--------------------|
| Simple (single module, well-understood problem) | 1 business day | 1 reviewer minimum |
| Medium (cross-module, new pattern) | 2 business days | 2 reviewers minimum |
| Complex (system-wide, new technology) | 3 business days | 3 reviewers including Chief Architect |
| Critical (security, data model, core architecture) | 5 business days | Full Architecture Review Board |

---

## 7. Architecture Review Board

### 7.1 Composition

| Seat | Role | Voting? |
|------|------|---------|
| Chief Architect | Chair, tiebreaker vote | ✅ Yes |
| Principal Engineer (Backend) | Backend architecture expertise | ✅ Yes |
| Principal Engineer (Frontend) | Frontend architecture expertise | ✅ Yes |
| Security Lead | Security architecture expertise | ✅ Yes |
| DevOps Lead | Infrastructure architecture expertise | ✅ Yes |
| Product Director | Product context (non-voting) | ❌ Advisory only |
| Domain Expert (as needed) | Tax domain context (non-voting) | ❌ Advisory only |

### 7.2 Meeting Cadence

- **Weekly:** 1-hour standing meeting to review proposed ADRs
- **Emergency:** On-call for critical architecture decisions (P0 incidents)
- **Quarterly:** 2-hour architecture review to assess health, debt, evolution

### 7.3 Voting Rules

- Quorum: At least 3 voting members present (including Chair or designated alternate)
- Decision: Simple majority of voting members
- Tiebreaker: Chief Architect (or designated alternate)
- Veto: Security Lead may veto any decision on security grounds (must provide written rationale within 24 hours)
- Override: CTO may override any board decision (must provide written rationale)

### 7.4 Meeting Output

Every Architecture Review Board meeting produces:

1. **Minutes:** Decisions made, rationale, action items
2. **ADR Status Update:** Which ADRs were reviewed, accepted, rejected
3. **Action Items:** Assigned to specific people with deadlines
4. **Decision Log:** Archived in `ai-dos/decisions/YYYY-MM-DD.md`

---

## 8. Module Boundary Enforcement

### 8.1 What Is a Module?

A module is the fundamental unit of architecture in this system. A module:

- Has a **single, well-defined responsibility**
- Has a **clearly documented public API**
- Has **explicit dependencies** on other modules (declared, not implicit)
- Is **independently testable**
- Is **independently deployable** (for services) or **independently versioned** (for libraries)
- Has a **single team/owner** responsible for its quality

### 8.2 Module Boundary Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| **MB-1: Explicit API** | All inter-module communication must go through the module's public API | Architecture linting in CI |
| **MB-2: No Internal Imports** | No module may import from another module's internal/private packages | Architecture linting in CI |
| **MB-3: Declared Dependencies** | Module dependencies must be declared, not discovered at runtime | Dependency check in CI |
| **MB-4: No Circular Dependencies** | Module dependency graph must be a DAG | Circular dependency check in CI |
| **MB-5: API Versioning** | Breaking API changes require a new major version | API compatibility check in CI |
| **MB-6: API Backward Compatibility** | Non-breaking changes must not break existing consumers | Integration test suite |
| **MB-7: Module Ownership** | Each module has exactly one owning team/lead | Module registry |
| **MB-8: Cross-Module Changes** | Changes affecting multiple modules require an ADR | PR check for multi-module changes |

### 8.3 Module Dependency Rules by Layer

```
┌─────────────────────────────────────┐
│           PRESENTATION LAYER         │
│  (Web App, Mobile App, API Gateway)  │
└──────────────┬──────────────────────┘
               │ depends on
               ▼
┌─────────────────────────────────────┐
│           APPLICATION LAYER          │
│  (ITR Processing, Tax Computation,   │
│   Validation, Reporting, etc.)       │
└──────────────┬──────────────────────┘
               │ depends on
               ▼
┌─────────────────────────────────────┐
│             DOMAIN LAYER             │
│  (Tax Rules, Tax Entities,           │
│   Compliance Rules, Knowledge Graph) │
└──────────────┬──────────────────────┘
               │ depends on
               ▼
┌─────────────────────────────────────┐
│         INFRASTRUCTURE LAYER         │
│  (Database, Message Queue, Cache,    │
│   File Storage, Secrets Manager)     │
└─────────────────────────────────────┘
```

**Layer Dependency Rules:**

1. Dependencies must flow downward only (Presentation → Application → Domain → Infrastructure)
2. No upward dependencies (Infrastructure must not import from Domain)
3. No horizontal dependencies within the same layer without ADR approval
4. Domain layer has zero external framework dependencies (pure Python/TypeScript)
5. Infrastructure layer implements interfaces defined by the Domain layer (Dependency Inversion)

### 8.4 Module Boundary Violation Response

```
VIOLATION DETECTED (by CI or review)
    │
    ├── Is it a P0 incident fix?
    │   └── Yes → Allow with EXCEPTION marker → Schedule remediation within 1 sprint
    │
    └── Is it intentional (new module relationship)?
        ├── Yes → Write ADR first → Get approval → Then implement
        └── No → Reject PR → Refactor to respect boundaries → Resubmit
```

---

## 9. Technology Stack Governance

### 9.1 Stack Principles

1. **Boring Technology:** Prefer proven, stable technologies over cutting-edge. The tax domain is complex enough without novel technology risks.
2. **Fewer Technologies:** Each new technology is a permanent maintenance burden. Default to using what we already have.
3. **Open Source Preferred:** Prefer open-source over proprietary unless there's a compelling reason (and an ADR justifying it).
4. **Managed Services Preferred:** Prefer managed services (PaaS, SaaS) over self-hosted infrastructure unless constraints (offline, data sovereignty) apply.
5. **Explicit Versions:** Every technology must declare its supported version range. "Latest" is not a version.

### 9.2 Technology Addition Process

```
1. PROPOSAL: Engineer/Agent identifies need for new technology
2. JUSTIFICATION: Why can't existing stack technologies solve this?
3. ADR: Write ADR following template, focusing on alternatives
4. SECURITY REVIEW: Security Lead evaluates supply chain risks
5. LICENSE REVIEW: Ensure license compatibility
6. MAINTENANCE PLAN: Who will keep this dependency updated?
7. BOARD APPROVAL: Architecture Review Board decision
8. REGISTRATION: Add to technology registry in 12-Enterprise-Architecture.md
```

### 9.3 Technology Removal Criteria

A technology must be removed or replaced when:

- It has known critical vulnerabilities with no patch available
- It is end-of-life / no longer maintained
- It is blocking an upgrade to a critical dependency
- It is used in only one place and a simpler alternative exists
- It is causing more maintenance burden than value provided

### 9.4 Technology Stack Registry

The current technology stack is maintained in [12-Enterprise-Architecture.md](12-Enterprise-Architecture.md) §Technology Stack. Each entry includes:

- Technology name and version
- Purpose (why we use it)
- ADR reference (which ADR approved it)
- Owner (who maintains it)
- End-of-life date (if applicable)
- Upgrade cadence

---

## 10. Cross-Cutting Concerns

### 10.1 Mandatory Cross-Cutting Concerns

Every module must address these concerns. Solutions must be consistent across modules (P1: Consistency).

| Concern | Owner | Standard | Enforcement |
|---------|-------|----------|-------------|
| **Authentication** | Security Lead | Centralized auth service, JWT-based, MFA support | Security review |
| **Authorization** | Security Lead | RBAC + ABAC, policy-as-code | Security review |
| **Logging** | Chief Architect | Structured JSON, correlation IDs, PII-free | Log format check in CI |
| **Monitoring** | DevOps Lead | Metrics + Traces + Alerts, OpenTelemetry | Deployment check |
| **Error Handling** | Chief Architect | Consistent error codes, domain exceptions, no stack trace leaks | Code review |
| **Configuration** | Chief Architect | Environment-agnostic config, schema-validated, secrets external | Config validation in CI |
| **Data Validation** | Chief Architect | Input validation at boundary, domain validation in core | Code review |
| **Caching** | Chief Architect | Explicit cache keys, TTL documented, invalidation strategy | Code review |
| **Rate Limiting** | DevOps Lead | Token bucket, per-tenant limits, 429 responses | Integration test |
| **Internationalization** | Chief Architect | i18n from day 1, translation files, locale-aware formatting | Code review |
| **Observability** | DevOps Lead | Health check, readiness check, metrics endpoint | Deployment check |

### 10.2 Cross-Cutting Concern Checklist

Before any module is accepted into the architecture, it must demonstrate:

- [ ] Authentication is integrated (or explicit "no auth" decision documented)
- [ ] Authorization is integrated (or explicit "no auth" decision documented)
- [ ] Logging follows project standard
- [ ] Metrics are emitted
- [ ] Errors follow project standard
- [ ] Configuration is validated at startup
- [ ] Health check endpoint exists
- [ ] Input validation is implemented at all entry points
- [ ] PII is not logged
- [ ] Secrets are not in code, config, or env

---

## 11. Technical Debt Management

### 11.1 Debt Classification

| Debt Type | Marker | Severity | Remediation Timeline |
|-----------|--------|----------|---------------------|
| **Constitutional Debt** | `CONSTITUTIONAL_DEBT` | Critical | 2 sprints max |
| **Architectural Debt** | `ARCHITECTURAL_DEBT` | High | 3 sprints max |
| **Code Debt** | `CODE_DEBT` | Medium | 5 sprints max |
| **Test Debt** | `TEST_DEBT` | Medium | 5 sprints max |
| **Documentation Debt** | `DOC_DEBT` | Low | 8 sprints max |
| **Dependency Debt** | `DEP_DEBT` | Varies | Based on vulnerability severity |

### 11.2 Debt Markers (Code Annotations)

```python
# CONSTITUTIONAL_DEBT(2026-07-05, P2): This module was built before ADR-0012 was accepted.
# Must refactor to use the event-driven pattern by 2026-09-01.
# Owner: @tech-lead-backend
# ADR: ADR-0012-event-driven-architecture.md

# ARCHITECTURAL_DEBT(2026-07-05): Direct database access from presentation layer.
# Must introduce repository pattern by 2026-09-15.
# Owner: @module-owner

# CODE_DEBT(2026-07-05): Nested if-else chain for ITR type dispatch.
# Must refactor to registry pattern by 2026-10-01.
# Owner: @developer-name
```

### 11.3 Debt Register

A consolidated debt register is maintained in the project memory at `ai-dos/memory/risks/debt-register.md`. It tracks:

- Total debt items by severity
- Total debt items by module
- Debt age (items past their remediation deadline)
- Debt trend (is debt growing or shrinking?)

### 11.4 Debt Budget

Every sprint allocates capacity for debt reduction:

| Sprint Type | Debt Reduction Budget |
|-------------|----------------------|
| Feature sprint | 20% of capacity |
| Maintenance sprint (every 6th sprint) | 100% of capacity |
| Pre-release sprint | 50% of capacity |

### 11.5 Debt Ceiling (The Limit)

If any of these thresholds are exceeded, feature development stops until debt is reduced:

- Constitutional debt: > 5 items
- Architectural debt: > 20 items
- Total code debt: > 100 items
- Any debt item past its remediation deadline by > 1 sprint

---

## 12. Architecture Documentation

### 12.1 Required Architecture Artifacts

| Artifact | Location | Update Cadence | Owner |
|----------|----------|----------------|-------|
| System Context Diagram | `12-Enterprise-Architecture.md` | On architecture change | Chief Architect |
| Container Diagram | `12-Enterprise-Architecture.md` | On module add/remove | Chief Architect |
| Module Dependency Graph | Generated from code | On every build | CI tool |
| API Catalog | Per-module OpenAPI/GraphQL specs | On API change | Module owner |
| Data Model (cross-module) | `12-Enterprise-Architecture.md` | On schema change | Chief Architect |
| ADR Index | `ai-dos/adr/README.md` | On every ADR | ADR author |
| Technology Stack Registry | `12-Enterprise-Architecture.md` | On technology change | Chief Architect |
| Module Registry | `ai-dos/memory/context/modules/` | On module change | Module owner |
| Architecture Decision Log | `ai-dos/decisions/` | Weekly | Architecture Review Board |

### 12.2 Diagram Standards

All architecture diagrams must:

- Use C4 model (Context, Container, Component, Code)
- Be generated from text (PlantUML, Mermaid, or Structurizr DSL) — no hand-drawn images
- Be version-controlled alongside the code
- Include a legend
- Include a last-updated date
- Be referenced from the relevant ADR or module README

### 12.3 Architecture Documentation Review

Architecture documentation is reviewed quarterly. The review checks:

- [ ] Do diagrams match the actual system?
- [ ] Are all ADRs consistent with each other?
- [ ] Is the module dependency graph a DAG?
- [ ] Are all modules listed in the module registry?
- [ ] Are all technologies listed in the stack registry?
- [ ] Are all APIs documented?
- [ ] Is the data model current?

---

## 13. Architecture Evolution

### 13.1 Evolution Principles

1. **Incremental Over Big Bang:** Evolve architecture incrementally. No rewrites.
2. **Strangler Fig Pattern:** Replace old architecture by gradually building around it, not by tearing it down.
3. **Backward Compatibility:** New architecture must coexist with old during transition.
4. **Prove Before Propagating:** Prove a new pattern in one module before applying it to all.
5. **Document the Journey:** Every architecture evolution gets an ADR explaining what changed and why.

### 13.2 Architecture Evolution Process

```
1. SIGNAL: Metric, incident, or review identifies architecture weakness
2. ANALYSIS: Chief Architect analyzes root cause and scope
3. PROPOSAL: ADR written proposing architectural change
4. EXPERIMENT: If high-risk, prove the new approach in a non-critical path
5. DECISION: Architecture Review Board approves/rejects
6. MIGRATION PLAN: Detailed migration steps with rollback plan
7. GRADUAL MIGRATION: Modules migrate one at a time
8. DEPRECATION: Old approach deprecated after all consumers migrated
9. REMOVAL: Old approach removed after deprecation period (2 sprints minimum)
10. POST-EVOLUTION REVIEW: What worked, what didn't, lessons learned
```

### 13.3 Evolution Triggers

| Trigger | Example |
|---------|---------|
| New constitutional interpretation | P10 extensibility requirement reveals rigid design |
| Scale challenge | Monolith can't handle filing season load |
| New tax requirement | Finance Act introduces new ITR type that breaks current model |
| Security finding | Penetration test reveals architectural vulnerability |
| Technology obsolescence | Critical dependency reaches end-of-life |
| Team feedback | Developers consistently struggle with a pattern |
| Incident post-mortem | Production outage traced to architectural flaw |

---

## 14. Architecture Quality Metrics

### 14.1 Metrics That Are Tracked

| Metric | Target | Measurement | Frequency |
|--------|--------|-------------|-----------|
| ADR completeness | 100% of architectural decisions have ADRs | Manual audit | Monthly |
| ADR freshness | 95% of ADRs reviewed within last quarter | ADR index last-reviewed dates | Quarterly |
| Module boundary violations | 0 | Architecture linting tool | Every PR |
| Circular dependencies | 0 | Dependency graph analysis | Every PR |
| Module coupling (afferent) | ≤ 5 incoming dependencies per module | Dependency graph analysis | Monthly |
| Module coupling (efferent) | ≤ 5 outgoing dependencies per module | Dependency graph analysis | Monthly |
| Abstractness vs. Instability | Within main sequence | Tool analysis | Monthly |
| Technical debt ratio | < 10% of total issues are debt | Debt register | Per sprint |
| Technology stack age | No dependency > 2 major versions behind | Dependency scan | Weekly |
| API breaking changes | 0 per minor version | API compatibility check | Every release |
| Dead code | < 2% of codebase | Static analysis | Monthly |
| Architecture documentation accuracy | 100% match between docs and code | Quarterly audit | Quarterly |

### 14.2 Architecture Health Dashboard

A dashboard (visible to all contributors) displays:

- Module dependency graph (DAG visualization)
- ADR timeline (when each ADR was last reviewed)
- Technical debt trend (growing/shrinking)
- Module health scores (test coverage, debt count, boundary violations)
- Architecture metric trends over last 4 quarters

---

## 15. Failure Cases and Remedies

### 15.1 Architecture Anti-Patterns

| Anti-Pattern | Description | Detection | Remedy |
|-------------|-------------|-----------|--------|
| **Distributed Monolith** | Services that must be deployed together | High coupling metrics, deployment dependencies | Extract interfaces, introduce async communication |
| **God Module** | Module that does too many things | > 10 public API methods, > 5 dependencies | Split into focused modules |
| **Architecture by Accident** | Architecture that emerged without decisions | Missing ADRs for current architecture | Retroactive ADRs, deliberate architecture review |
| **Ivory Tower Architecture** | Architecture disconnected from implementation reality | ADRs that don't match code | Either update ADRs or refactor code |
| **Architecture Astronautics** | Over-engineered for problems we don't have | ADRs solving hypothetical future problems | Reject ADR, implement when actually needed |
| **Sinkhole Module** | Module that receives many dependencies but never calls out | High afferent coupling, zero efferent coupling | Extract to library or merge into consumers |
| **Tangled Dependencies** | Modules with bidirectional dependencies | Circular dependency detection | Break cycle with dependency inversion |
| **Leaky Abstraction** | Module exposes internal implementation details | Internal types in public API | Fix API to hide internals |
| **Vendor Lock-In** | Architecture depends on proprietary, un-replaceable service | Technology stack review | Abstract behind interface, plan migration path |
| **Shadow Architecture** | Architecture exists but no one follows it | ADRs contradicted by code | Enforce through CI, or update ADRs |

### 15.2 Architecture Crisis Response

```
ARCHITECTURE CRISIS DECLARED WHEN:
- Architecture dashboard shows RED in 3+ metrics for 2+ consecutive months
- OR: A P0 incident is traced to an architectural flaw
- OR: Module boundary violations exceed 20% of PRs

CRISIS RESPONSE:
1. Chief Architect declares architecture crisis
2. All non-critical feature development halts
3. Architecture Review Board convenes emergency session
4. Root cause analysis within 2 business days
5. Recovery plan with weekly milestones within 5 business days
6. Crisis lifted when metrics return to YELLOW or better
7. Post-crisis review: How did we get here? How do we prevent recurrence?
```

---

## 16. ADR Index

### 16.1 Current ADRs

| ADR # | Title | Status | Date | Supersedes |
|-------|-------|--------|------|------------|
| — | *No ADRs yet — project initialization phase* | — | — | — |

### 16.2 ADR Index Maintenance

The ADR index (`ai-dos/adr/README.md`) must be updated every time an ADR status changes. This is a mandatory step in the ADR merge checklist.

---

## 17. Appendices

### Appendix A: ADR Review Checklist

```
ADR REVIEWER CHECKLIST:

□ Problem is clearly stated and I understand the context
□ At least 2 alternatives are documented with pros/cons
□ The chosen alternative has clear rationale
□ Both positive and negative consequences are documented
□ Negative consequences have mitigation plans
□ Constitutional alignment table is complete and honest
□ Architectural invariant compliance is verified (all 10 checked)
□ Security considerations are addressed
□ Migration plan is documented (if applicable)
□ References to related ADRs are correct
□ The ADR uses the correct template with no omitted sections
□ I would defend this decision to a new team member in 6 months
```

### Appendix B: ADR Author Pre-Submission Checklist

```
ADR AUTHOR CHECKLIST:

□ I have stated the problem clearly in 2-4 sentences
□ I have provided sufficient background context
□ I have identified all stakeholders
□ I have listed all relevant constraints
□ I have documented at least 2 alternatives seriously considered
□ I have explained why each alternative was rejected
□ I have documented positive consequences
□ I have documented negative consequences honestly (not minimized)
□ I have proposed mitigation for each negative consequence
□ I have completed the constitutional alignment table
□ I have checked all 10 architectural invariants
□ I have addressed security considerations
□ I have defined a migration plan (if applicable)
□ I have linked related ADRs
□ I have followed the template exactly
□ This ADR would be understandable to a new team member in 12 months
```

### Appendix C: Reference Architecture Decisions

The following architecture decisions are pre-ordained by the Constitution and do not require separate ADRs:

| Decision | Constitutional Basis |
|----------|---------------------|
| Tax rules must be versioned by financial year | P8: Compliance Is Continuous |
| Tax rules are stored separately from the computation engine | I2: Rule-Engine Separation |
| Every computation produces an audit trail | I3: Complete Audit Trail |
| Every computation is explainable | I4: Explainability |
| Data is isolated by tenant | I5: Data Isolation |
| All writes are idempotent | I6: Idempotency |
| All mutations are logged (event sourcing) | I7: Zero Data Loss |
| Rates and thresholds are configurable | I8: Configurable Everything |
| System degrades gracefully | I9: Graceful Degradation |
| Core computation works offline | I10: Offline Capability |

### Appendix D: Cross-Reference Map

| This Section | References | Is Referenced By |
|--------------|-----------|------------------|
| §4-6 ADRs | — | `02-Development-Lifecycle.md`, `08-Agent-System.md` |
| §7 Architecture Review Board | `00-Constitution.md` §6 | — |
| §8 Module Boundaries | `00-Constitution.md` §5 | `03-Engineering-Standards.md`, `12-Enterprise-Architecture.md` |
| §9 Technology Stack | — | `12-Enterprise-Architecture.md` |
| §10 Cross-Cutting Concerns | `00-Constitution.md` §4 | `03-Engineering-Standards.md` |
| §11 Technical Debt | — | `02-Development-Lifecycle.md`, `13-Quality-Gates.md` |
| §12 Architecture Documentation | — | `06-Documentation-Standards.md` |
| §13 Architecture Evolution | `00-Constitution.md` §12 | `14-Continuous-Improvement.md` |
| §14 Quality Metrics | `00-Constitution.md` §9 | `13-Quality-Gates.md` |
| §15 Failure Cases | — | `14-Continuous-Improvement.md` |

### Appendix E: Future Improvements

1. **Automated Architecture Linting:** Tools that parse the module dependency graph and flag boundary violations, circular dependencies, and coupling violations automatically in CI.
2. **Architecture Fitness Functions:** Automated tests that verify architectural characteristics (e.g., "domain layer has zero framework imports," "no module has > 5 dependencies").
3. **ADR Generation from Code:** Semi-automated ADR drafting based on code changes that cross module boundaries.
4. **Architecture Decision Graph:** Visualization showing how ADRs relate to each other, which ADRs supersede which, and which components are affected by which decisions.
5. **Module Health Score Automation:** Automated calculation of module health scores from CI data (coverage, debt count, boundary violations, dependency freshness).
6. **Architecture Change Impact Analysis:** Tool that, given a proposed architecture change, identifies all affected modules and estimates migration effort.

---

*End of AI-DOS Chief Architect v1.0.0*

*When architecture decisions are made, they live here. When they are not, the project dies slowly.*
