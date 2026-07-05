# AI-DOS Constitution v1.0.0

> **Status:** SUPREME GOVERNANCE DOCUMENT
> **Supersedes:** Nothing
> **Ratified:** 2026-07-05
> **Last Amended:** 2026-07-05
> **Next Review:** 2026-10-05
> **Author:** CTO Office
> **Applies To:** All agents, all humans, all subsystems, all decisions

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Scope](#2-scope)
3. [Mission](#3-mission)
4. [Core Principles](#4-core-principles)
5. [Architectural Invariants](#5-architectural-invariants)
6. [Governance Model](#6-governance-model)
7. [Decision Hierarchy](#7-decision-hierarchy)
8. [Agent Bill of Rights and Responsibilities](#8-agent-bill-of-rights-and-responsibilities)
9. [Quality Imperatives](#9-quality-imperatives)
10. [Knowledge Preservation Mandate](#10-knowledge-preservation-mandate)
11. [Security and Compliance Covenant](#11-security-and-compliance-covenant)
12. [Evolution and Amendment Process](#12-evolution-and-amendment-process)
13. [Escalation and Exception Handling](#13-escalation-and-exception-handling)
14. [Constitutional Review Checklist](#14-constitutional-review-checklist)
15. [Failure Cases and Remedies](#15-failure-cases-and-remedies)
16. [Ratification](#16-ratification)

---

## 1. Purpose

### 1.1 Why This Document Exists

The AI Development Operating System (AI-DOS) Constitution is the supreme governance document for the AI-powered Indian Tax Intelligence Platform. It exists to solve a single, existential problem:

> **Large AI-assisted software projects fail because AI agents lose consistency across sessions, contexts, and time.**

This document is the anchor. When an AI agent opens a session 18 months from now, working on Finance Act 2027 changes in ITR-4 computation, it must operate with the same architectural understanding, quality standards, and design philosophy as the agent that laid the foundation today.

### 1.2 What This Document Is

- The highest authority in the repository
- The non-negotiable foundation for all decisions
- The conflict resolution mechanism when principles collide
- The contract between human stakeholders and AI agents
- The contract between AI agents and other AI agents
- The definition of "correct" behavior for all contributors

### 1.3 What This Document Is Not

- A style guide (see `03-Engineering-Standards.md`)
- A testing manual (see `04-Testing-Standards.md`)
- A project plan (see `11-Roadmap.md`)
- A replacement for ADRs (see `01-Chief-Architect.md` for ADR process)
- A technical specification
- Optional reading

### 1.4 Constitutional Authority

This document derives its authority from the CTO Office. It is ratified by the Chief Architect, Principal Engineers, and Product Director. No other document, decision, or precedent may override it. When this document conflicts with any other document, this document wins — always, without exception, without appeal.

---

## 2. Scope

### 2.1 What Falls Under This Constitution

| Domain | Covered By |
|--------|-----------|
| Architecture decisions | ✅ This document |
| Code quality standards | ✅ This document + `03-Engineering-Standards.md` |
| Testing requirements | ✅ This document + `04-Testing-Standards.md` |
| Security requirements | ✅ This document + `03-Engineering-Standards.md` (Security section) |
| Documentation requirements | ✅ This document + `06-Documentation-Standards.md` |
| Git workflow | ✅ This document + `02-Development-Lifecycle.md` |
| Agent behavior | ✅ This document + `08-Agent-System.md` |
| Review process | ✅ This document + `05-Review-Standards.md` |
| Quality gates | ✅ This document + `13-Quality-Gates.md` |
| Deployment decisions | ✅ This document |
| Procurement decisions | ❌ Out of scope — handled by CTO Office directly |
| Hiring decisions | ❌ Out of scope — handled by CTO Office directly |
| Business strategy | ❌ Out of scope — handled by Product Director |

### 2.2 Who Is Bound By This Constitution

- **All AI agents** operating in this repository — without exception
- **All human developers** contributing to this repository
- **All human reviewers** approving changes
- **All architects** making design decisions
- **All QA engineers** writing and executing tests
- **All technical writers** producing documentation
- **All DevOps engineers** managing infrastructure
- **The CTO Office** itself — the constitution binds its authors

### 2.3 Temporal Scope

This constitution is effective from the moment of ratification and remains in effect until formally superseded by a new version through the amendment process defined in Section 12. It applies to all past, present, and future code in the repository. Legacy code that violates this constitution must be identified with a `CONSTITUTIONAL_DEBT` marker and scheduled for remediation.

---

## 3. Mission

### 3.1 Primary Mission

To create and maintain an enterprise-grade, AI-powered Indian Tax Intelligence Platform that:

1. **Computes tax liability correctly** for all ITR types across all financial years
2. **Explains every computation** in plain language that a taxpayer can understand
3. **Adapts to legal changes** without destabilizing existing functionality
4. **Protects taxpayer data** with defense-grade security
5. **Scales to millions** of concurrent users during filing season
6. **Maintains complete audit trails** for every operation
7. **Supports both individual and enterprise** use cases with equal rigor

### 3.2 Secondary Mission

To demonstrate that AI-assisted software development, when governed by a proper operating system, can produce and maintain enterprise-grade software over multi-year timelines without architectural decay.

### 3.3 Non-Missions

This platform does NOT:

- Provide legal advice (it provides tax computation, not legal interpretation)
- Replace Chartered Accountants (it augments them)
- Guarantee tax savings (it optimizes within the law)
- Replace the Income Tax Department's systems (it interoperates with them)

---

## 4. Core Principles

These principles are NON-NEGOTIABLE. Every decision, every line of code, every review, every architecture choice must align with these principles. When principles conflict, use the priority order defined in Section 7.

---

### Principle 1: Consistency Above All (P1)

> **Rank: 1 of 10. Supreme.**

AI agents working across sessions, contexts, and months must produce output that is indistinguishable from a single agent working continuously.

**What This Means in Practice:**

- Every agent must read and internalize the constitution before taking any action
- Architectural decisions must be recorded in ADRs before code is written
- Naming conventions must be followed with zero tolerance for deviation
- Code patterns must be consistent across all modules — same problem, same solution
- Error handling must follow the same pattern everywhere
- Logging must follow the same format everywhere
- Testing must follow the same structure everywhere
- Documentation must follow the same template everywhere

**Violation Indicators:**

- Two modules solving the same problem differently
- Inconsistent naming within the same codebase
- Different error handling patterns in different files
- Architecture that contradicts documented ADRs
- Tests with different structure and depth across modules

**Remediation:**

- `CONSISTENCY_DEBT` marker on the violating code
- ADR review to determine canonical pattern
- Refactor to canonical pattern before any new feature work
- Add consistency check to CI pipeline

---

### Principle 2: Architecture First, Code Second (P2)

> **Rank: 2 of 10.**

No code shall be written until its place in the architecture is understood, documented, and approved.

**What This Means in Practice:**

- Every feature starts with an Architecture Decision Record (ADR)
- ADR must describe: problem, context, alternatives considered, decision, consequences
- ADR must be reviewed and approved before implementation begins
- Code that exists without a corresponding ADR is considered architectural debt
- Refactoring that changes architecture requires a new ADR
- Module boundaries defined in ADRs are enforced in code — crossing a boundary requires explicit justification

**ADR Required For:**

- New module or service
- New external dependency
- Data model changes that affect multiple modules
- API contract changes (internal or external)
- New integration pattern
- Performance optimization that changes architecture
- Security architecture changes
- Deprecation of existing architectural patterns

**ADR NOT Required For:**

- Bug fixes that don't change architecture
- Adding a function within an existing module boundary
- Updating documentation
- Adding tests
- Minor refactoring within a module

**Violation Indicators:**

- Code written before ADR is approved
- ADR that doesn't list alternatives
- ADR that doesn't describe consequences
- Architecture that doesn't match any ADR

**Remediation:**

- Stop development immediately
- Write retroactive ADR
- Refactor code to match ADR, or update ADR to match code (only if code is correct)
- Review why ADR process was bypassed — fix the process, not just the code

---

### Principle 3: Explicit Over Implicit (P3)

> **Rank: 3 of 10.**

AI agents cannot read minds. Humans forget. Everything must be explicit.

**What This Means in Practice:**

- Every function must have a clear, single responsibility stated in its docstring
- Every type must be explicitly declared (no `any` in TypeScript; type hints in Python)
- Every configuration must be explicit (no magic defaults from environment)
- Every error must be explicitly handled or explicitly propagated
- Every assumption must be stated in comments or ADRs
- Every dependency must be explicitly declared (no transitive dependency usage)
- Every API contract must be explicitly versioned
- Every tax rule must have an explicit effective date range
- Every database query must explicitly state its isolation level requirements

**Anti-Patterns:**

```python
# BAD: Implicit behavior
def calculate_tax(income):
    return income * rate  # Where does rate come from?

# GOOD: Explicit behavior
def calculate_tax(income: Decimal, financial_year: FinancialYear, regime: TaxRegime) -> TaxLiability:
    """
    Calculate income tax liability for a given financial year and regime.

    Args:
        income: Total taxable income in INR
        financial_year: The financial year for which tax is computed (e.g., FY2025-26)
        regime: OLD_REGIME or NEW_REGIME

    Returns:
        TaxLiability with breakdown by slab

    Raises:
        InvalidFinancialYearError: If financial_year has no defined tax slabs
        RegimeNotApplicableError: If regime is not valid for the given financial_year
    """
    slabs = TaxSlabRepository.get_active_slabs(financial_year, regime)
    return TaxEngine.compute(income, slabs)
```

**Violation Indicators:**

- Magic numbers without named constants
- Functions with undocumented side effects
- Implicit type coercion
- Configuration from environment variables without schema validation
- Catching generic `Exception` without re-raising or logging

**Remediation:**

- Add explicit documentation
- Add type annotations
- Add configuration schema validation
- Replace magic numbers with named constants
- Replace broad exception handling with specific exception types

---

### Principle 4: Reviewability Is Non-Negotiable (P4)

> **Rank: 4 of 10.**

Every change must be reviewable by both human domain experts and AI agents. If a change cannot be explained, it cannot be merged.

**What This Means in Practice:**

- Every pull request must include a description of WHAT, WHY, and HOW
- Every PR must link to the ADR or issue that motivated it
- Every PR must be small enough to review in under 30 minutes
- Complex changes must include a design document
- AI agents must produce reviewable output — no monolithic generated files without explanation
- Reviewers must be able to understand the change without asking the author
- If a reviewer asks "why," the PR description was insufficient

**PR Size Limits:**

| PR Type | Max Files Changed | Max Lines Changed | Review Time Budget |
|---------|-------------------|-------------------|-------------------|
| Bug fix | 10 | 200 | 15 minutes |
| Feature | 25 | 500 | 30 minutes |
| Refactor | 30 | 800 | 30 minutes |
| Architecture change | 15 | 400 | 45 minutes |
| Documentation | 50 | 2000 | 15 minutes |

PRs exceeding these limits must be split. No exceptions without CTO approval.

**Violation Indicators:**

- PR description is "fix bug" or "update code"
- PR with 50+ files changed without justification
- Code that requires the author to explain verbally
- Merged PR with unresolved review comments

**Remediation:**

- Revert the merge if review process was violated
- Split large PRs retroactively
- Update PR template to enforce descriptions
- Add PR size checks to CI pipeline

---

### Principle 5: Testability Is Design (P5)

> **Rank: 5 of 10.**

If a component cannot be tested in isolation, it is incorrectly designed — not incorrectly tested.

**What This Means in Practice:**

- Every module must have clearly defined boundaries that enable isolated testing
- Dependencies must be injectable (no hard-coded instantiation)
- External services must be mockable through interfaces
- Stateful components must expose their state for verification
- Time-dependent logic must accept a clock abstraction
- Random behavior must accept a seed or generator abstraction
- Every public function must have unit tests
- Every API endpoint must have integration tests
- Every user-facing flow must have end-to-end tests
- Tests must be written BEFORE or CONCURRENTLY with implementation — never after

**Test Pyramid Mandate:**

```
        /\
       /E2E\          ~5% of tests
      /------\
     /Integration\    ~20% of tests
    /--------------\
   /   Unit Tests    \  ~75% of tests
  /------------------\
```

**Violation Indicators:**

- Code that requires "too much mocking to test"
- Circular dependencies that prevent isolated testing
- Tests that are more complex than the code they test
- Tests that don't exercise edge cases
- Untested error handling paths

**Remediation:**

- Refactor for testability before adding features
- Break circular dependencies with dependency inversion
- Simplify overly complex tests (they indicate overly complex code)
- Add edge case tests
- Add error path tests

---

### Principle 6: Documentation Is Code (P6)

> **Rank: 6 of 10.**

Documentation has the same lifecycle as code: it is versioned, reviewed, tested, and maintained. Outdated documentation is a bug.

**What This Means in Practice:**

- Every module must have a README that explains its purpose, boundaries, and contract
- Every public API must have complete docstrings with parameters, return values, exceptions, and examples
- Every ADR must be kept current — if architecture changes, the ADR must be updated
- Every configuration option must be documented with its default, valid values, and effect
- Documentation is reviewed in the same PR as the code change
- Documentation-only PRs are valid and encouraged
- "The code is self-documenting" is never an acceptable response

**Documentation Types and Their Mandatory Nature:**

| Documentation Type | Required? | Review Required? | Update Trigger |
|--------------------|-----------|------------------|----------------|
| Module README | ✅ Yes | ✅ Yes | New module, API change |
| Function/Method Docstring | ✅ Yes | ✅ Yes | Signature change, behavior change |
| ADR | ✅ Yes | ✅ Yes | Architecture change |
| API Documentation | ✅ Yes | ✅ Yes | Contract change |
| Architecture Diagrams | ✅ Yes | ✅ Yes | Structure change |
| Runbook | ✅ Yes | ✅ Yes | Operational change |
| Release Notes | ✅ Yes | ✅ Yes | Every release |
| User Guide | ❌ (if internal) | ✅ Yes (if exists) | Feature change |
| Inline Comments | ✅ For complex logic | ✅ Yes | Logic change |

**Violation Indicators:**

- Module without a README
- Public function without a docstring
- Docstring that doesn't match the actual behavior
- ADR that describes architecture that no longer exists
- Configuration option with no documentation

**Remediation:**

- Block merge until documentation is complete
- Treat outdated documentation as a P2 bug
- Add documentation completeness check to CI pipeline
- Schedule documentation sprints for accumulated debt

---

### Principle 7: Security by Design (P7)

> **Rank: 7 of 10.**

Security cannot be retrofitted. Every design must consider security from the first sketch.

**What This Means in Practice:**

- Every ADR must include a "Security Considerations" section
- Every API must authenticate and authorize before any business logic executes
- Every input must be validated and sanitized
- Every output must be escaped for its context
- Every data store must encrypt at rest
- Every communication must encrypt in transit
- Every secret must be stored in a secrets manager (never in code, config, or env vars)
- Every access must be logged for audit
- Every dependency must be scanned for known vulnerabilities
- Every PR must pass automated security scanning

**Security Requirements by Data Classification:**

| Data Classification | Encryption at Rest | Encryption in Transit | Access Logging | Data Masking | Retention Limit |
|---------------------|-------------------|----------------------|----------------|--------------|-----------------|
| Public | ❌ | ✅ | ❌ | N/A | Unlimited |
| Internal | ❌ | ✅ | ✅ | N/A | 7 years |
| Confidential | ✅ | ✅ | ✅ | In logs | 7 years |
| Restricted (PAN, Aadhaar, Financial) | ✅ | ✅ | ✅ | Always | Per regulation |

**All taxpayer financial data is classified as RESTRICTED.**

**Violation Indicators:**

- API endpoint without authentication
- Secret in source code, config file, or environment variable
- SQL query built with string concatenation
- Log statement that includes PAN, Aadhaar, or financial data
- Dependency with known CVE
- ADR without security section

**Remediation:**

- Block merge immediately
- If merged, revert immediately
- Post-incident review required
- Security debt must be remediated before any new feature work

---

### Principle 8: Compliance Is Continuous (P8)

> **Rank: 8 of 10.**

Indian tax law changes. The Finance Act is amended every year. ITR forms are revised. Compliance is not a milestone — it is a continuous state.

**What This Means in Practice:**

- Tax rules must be versioned by financial year with explicit effective date ranges
- Every tax computation must be traceable to a specific legal provision
- Every tax computation must produce an explainable audit trail
- New tax rules must be added without modifying existing rule code
- The system must support parallel operation of old and new rules during transition periods
- Every compliance-related change must be reviewed by a domain expert
- Every release must include a compliance statement

**Tax Rule Versioning Mandate:**

```python
# Every tax rule must carry this metadata
@tax_rule(
    provision="Section 115BAC",
    financial_year_start=2025,
    assessment_year_start=2026,
    effective_from=date(2025, 4, 1),
    effective_until=date(2026, 3, 31),  # None if still active
    finance_act="Finance Act 2025",
    notification_number=None,  # If applicable
    supersedes=None,  # Reference to previous version of this rule
    authority="Income Tax Department, Government of India"
)
```

**Violation Indicators:**

- Tax computation that doesn't reference a legal provision
- Hard-coded tax rates without year context
- Modified tax rule code (instead of new rule with supersedes)
- Missing audit trail for a computation
- Release without compliance statement

**Remediation:**

- Stop development on affected module
- Add legal provision references
- Refactor hard-coded rates to versioned rule repository
- Add audit trail generation
- Add compliance statement to release process

---

### Principle 9: Knowledge Preservation (P9)

> **Rank: 9 of 10.**

Every decision, trade-off, assumption, and rationale must be captured in a form that survives contributor turnover — both human and AI.

**What This Means in Practice:**

- Every ADR captures: context, decision, alternatives, consequences, author, date, reviewers
- Every complex code section has a "why" comment explaining the rationale
- Every rejected approach is documented somewhere (ADR alternatives section)
- Every incident has a post-mortem document
- Every project memory file (see `07-Project-Memory.md`) is updated consistently
- Knowledge is structured for retrieval — not buried in chat logs or emails
- AI agents must write to project memory after every significant action

**Knowledge Types and Storage:**

| Knowledge Type | Storage Location | Retention | Format |
|----------------|-----------------|-----------|--------|
| Architecture decision | `ai-dos/adr/` | Permanent | ADR template |
| Design trade-off | ADR alternatives section | Permanent | Markdown |
| Bug root cause | Commit message + Issue | Permanent | Structured |
| Incident analysis | `ai-dos/postmortems/` | Permanent | Post-mortem template |
| Implementation rationale | Inline comment | Life of code | "WHY:" prefix |
| Configuration rationale | Config file comment | Life of config | Inline |
| Domain knowledge | `ai-dos/knowledge/` | Permanent | Knowledge article |
| Project status | `07-Project-Memory.md` | Continuous | Status entries |

**Violation Indicators:**

- "Why was this done this way?" cannot be answered from repository content
- Decisions explained only in chat or email
- Bug fixed without root cause documented
- Architecture change without ADR
- Project memory not updated after significant change

**Remediation:**

- Pause work and capture current state
- Interview contributors to recover lost knowledge
- Add missing ADRs
- Update project memory
- Add knowledge preservation to definition of done

---

### Principle 10: Extensibility Without Modification (P10)

> **Rank: 10 of 10.**

The system must be extensible without modifying existing, tested, proven code. This is the Open/Closed Principle applied at the system level.

**What This Means in Practice:**

- New ITR types must be addable without modifying the tax engine core
- New tax regimes must be addable without modifying existing regime code
- New validation rules must be addable without modifying the validation engine
- New report types must be addable without modifying the reporting engine
- New integration points must be addable through defined extension points
- Plugin architecture where appropriate (tax rules, validations, reports)
- Strategy pattern for variant behavior
- Event-driven architecture for cross-cutting concerns
- Feature flags for gradual rollout (not for permanent variant behavior)

**Extension Points (Defined):**

| Extension Point | Mechanism | Example |
|-----------------|-----------|---------|
| Tax Rules | Rule Engine + Plugin Registry | New deduction under Section 80XXX |
| ITR Types | Form Definition Schema | ITR-5 for LLPs |
| Validation Rules | Validation Rule Registry | New AIS cross-validation |
| Export Formats | Export Plugin | New JSON schema version for ITD |
| Report Types | Report Template Registry | New capital gains summary report |
| Auth Methods | Auth Provider Plugin | OAuth for enterprise SSO |
| Payment Gateways | Payment Provider Plugin | New bank integration |

**Anti-Pattern (Forbidden):**

```python
# BAD: Adding a new ITR type by modifying the core engine
def process_itr(itr_type, data):
    if itr_type == "ITR-1":
        return process_itr1(data)
    elif itr_type == "ITR-2":
        return process_itr2(data)
    elif itr_type == "ITR-3":
        return process_itr3(data)
    # VIOLATION: Must modify this function for every new ITR type
```

**Required Pattern:**

```python
# GOOD: Adding a new ITR type through the registry
def process_itr(itr_type: ITRType, data: ITRData) -> ITRResult:
    processor = ITRProcessorRegistry.get(itr_type)
    if not processor:
        raise UnsupportedITRTypeError(itr_type)
    return processor.process(data)

# New ITR types register themselves:
@register_itr_processor(ITRType.ITR_5)
class ITR5Processor(BaseITRProcessor):
    ...
```

**Violation Indicators:**

- If-else chains based on type codes
- Switch statements that must be updated for new variants
- Base class modified when new subclass is added
- Core engine modified for new business rules

**Remediation:**

- Refactor to use registry/plugin pattern
- Extract variant behavior behind interfaces
- Use configuration-driven dispatch instead of code-driven dispatch
- Add extension point documentation

---

## 5. Architectural Invariants

Architectural invariants are truths about the system that must hold for its entire lifetime. They are stronger than principles because they are verifiable. A build can check whether an invariant holds. Violating an invariant is a build-breaking event.

### 5.1 Invariant I1: Multi-Year Architecture

> **Statement:** The system MUST support all financial years from FY2020-21 onward, and MUST be capable of supporting future financial years without architectural change.

**Verification:** TaxRuleRepository.get_supported_years() returns a list that grows without code changes.

### 5.2 Invariant I2: Rule-Engine Separation

> **Statement:** Tax rules MUST be stored and versioned separately from the computation engine. The engine MUST be generic across all ITR types, regimes, and financial years.

**Verification:** The `tax-engine` module has zero imports from any `tax-rules-*` module that references a specific ITR type or financial year.

### 5.3 Invariant I3: Complete Audit Trail

> **Statement:** Every tax computation MUST produce a complete, immutable audit trail from raw inputs to final liability, including every intermediate step, every rule applied, every decision made.

**Verification:** TaxEngine.compute() returns an AuditTrail object that contains entries for every step, and no step can be skipped.

### 5.4 Invariant I4: Explainability

> **Statement:** Every tax computation MUST be explainable in plain English (or the user's chosen language) at every level: summary for taxpayer, detail for CA, technical for auditor.

**Verification:** Every component of the tax liability has a corresponding explain() method that returns human-readable text referencing the legal provision.

### 5.5 Invariant I5: Data Isolation

> **Statement:** Taxpayer data for different entities MUST be isolated at the database level. Queries MUST NEVER cross tenant boundaries. Tenant context MUST be established before any data access.

**Verification:** Every database query includes a tenant_id filter. Row-level security is enforced at the database level.

### 5.6 Invariant I6: Idempotency

> **Statement:** All write operations MUST be idempotent. Submitting the same tax computation twice MUST produce the same result and MUST NOT create duplicate records.

**Verification:** Idempotency keys are required for all write operations. Duplicate submissions return the original result.

### 5.7 Invariant I7: Zero Data Loss

> **Statement:** The system MUST never lose data. Every create, update, and delete MUST be captured in an append-only event log. Deletes MUST be soft deletes.

**Verification:** Event log contains all mutations. No hard deletes exist in the database.

### 5.8 Invariant I8: Configurable Everything

> **Statement:** Every threshold, rate, limit, and rule parameter that could change MUST be configurable without code deployment.

**Verification:** Tax rates, slabs, surcharges, cess rates, deduction limits — all are stored in versioned configuration, not in code.

### 5.9 Invariant I9: Graceful Degradation

> **Statement:** Failure of a non-critical subsystem MUST NOT prevent core tax computation. The system MUST degrade gracefully, clearly communicating what is unavailable.

**Verification:** If the AIS integration is unavailable, tax computation still proceeds with user-provided data, with a clear warning about what was not cross-verified.

### 5.10 Invariant I10: Offline Capability

> **Statement:** Core tax computation MUST function without network connectivity. External integrations (AIS, Form 26AS fetch) are enhancements, not prerequisites.

**Verification:** TaxEngine.compute() can run with only locally available data. Network calls are behind feature flags or explicit user action.

---

## 6. Governance Model

### 6.1 Governance Structure

```
┌─────────────────────────────────────────┐
│               CTO Office                 │
│   (Final authority on all decisions)     │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌────────┐ ┌──────────┐ ┌──────────┐
│ Chief  │ │Principal │ │Product   │
│Architect│ │Engineers │ │Director  │
└───┬────┘ └────┬─────┘ └────┬─────┘
    │           │             │
    │  ┌────────┼────────┐    │
    │  │        │        │    │
    ▼  ▼        ▼        ▼    ▼
┌──────────────────────────────────────┐
│         Architecture Review Board     │
│  (Meets weekly, approves ADRs)        │
└──────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌────────┐ ┌──────────┐ ┌──────────┐
│  Tech  │ │  Domain  │ │ Security │
│ Leads  │ │ Experts  │ │  Lead    │
└────────┘ └──────────┘ └──────────┘
```

### 6.2 Roles and Authorities

| Role | Authority | Appointment | Term |
|------|-----------|-------------|------|
| CTO | Final decision on any matter | Company board | Indefinite |
| Chief Architect | Architecture decisions, ADR approval | CTO | Indefinite |
| Principal Engineer | Technical standards, code review policy | CTO + Chief Architect | Indefinite |
| Product Director | Feature priority, scope decisions | CTO | Indefinite |
| Architecture Review Board | ADR review, technical debt prioritization | CTO appoints | 6-month rotation |
| Domain Expert (CA/Tax Lawyer) | Tax correctness, compliance sign-off | Product Director | Per engagement |
| Security Lead | Security architecture, vulnerability management | CTO | Indefinite |
| Tech Lead | Module-level technical decisions | Chief Architect | Per module |
| AI Agents | Implementation within defined boundaries | Automated | Per session |

### 6.3 Decision Rights

| Decision Type | Who Decides | Who Must Be Consulted | Who Must Be Informed |
|---------------|-------------|----------------------|---------------------|
| Constitutional amendment | CTO | Chief Architect, Principal Engineers, Product Director | All |
| New architecture pattern | Chief Architect | Architecture Review Board | All tech leads |
| New external dependency | Chief Architect | Security Lead, Principal Engineers | Tech leads |
| Module boundary change | Chief Architect | Affected tech leads | Team |
| API contract change | Tech Lead | Consumers of the API | Team |
| Implementation approach | Developer/Agent | Tech Lead | Team |
| Test strategy | Developer/Agent | Tech Lead, QA | Team |
| Refactoring scope | Tech Lead | Chief Architect | Team |
| Tax rule implementation | Developer/Agent | Domain Expert | Team |
| Security configuration | Security Lead | Chief Architect | All |
| Production deployment | DevOps Lead | Tech Lead, Security Lead | Team |
| Rollback decision | DevOps Lead | Tech Lead | Team |

### 6.4 Dispute Resolution

When two parties disagree on a technical decision:

1. **ADR Required:** The dispute must be captured as an ADR with clear alternatives
2. **Consultation:** Both parties present their case to the Architecture Review Board
3. **Decision:** The board decides within 1 business day
4. **Documentation:** The decision and rationale are captured in the ADR
5. **Acceptance:** Both parties accept the decision and move forward
6. **Escalation:** Either party may escalate to the CTO, whose decision is final

### 6.5 Emergency Powers

In case of production incident (P0):

1. Any engineer may bypass normal process to fix the incident
2. The fix must be followed by a post-incident ADR within 24 hours
3. Any constitutional violation in the fix must be remediated within 1 sprint
4. CTO must be notified of any constitutional bypass

---

## 7. Decision Hierarchy

When principles, requirements, or constraints conflict, this hierarchy resolves the conflict. Higher items override lower items. No exceptions.

### 7.1 The Hierarchy

```
Level 1: LEGAL COMPLIANCE
    ↓ (overrides everything below)
Level 2: CONSTITUTIONAL PRINCIPLES (in rank order P1 → P10)
    ↓ (overrides everything below)
Level 3: ARCHITECTURAL INVARIANTS (I1 → I10)
    ↓ (overrides everything below)
Level 4: ARCHITECTURE DECISION RECORDS
    ↓ (overrides everything below)
Level 5: ENGINEERING STANDARDS (03-Engineering-Standards.md)
    ↓ (overrides everything below)
Level 6: CODING STANDARDS (within 03-Engineering-Standards.md)
    ↓ (overrides everything below)
Level 7: MODULE CONVENTIONS (local consistency)
    ↓ (overrides everything below)
Level 8: PERSONAL PREFERENCE
```

### 7.2 Conflict Resolution Algorithm

```
function resolve_conflict(option_a, option_b):
    for level in [1, 2, 3, 4, 5, 6, 7, 8]:
        winner = evaluate_at_level(level, option_a, option_b)
        if winner is not None:
            document_resolution(winner, rationale, level)
            return winner

    # If still tied, apply tiebreakers in order:
    # 1. Simpler option
    # 2. More testable option
    # 3. More maintainable option
    # 4. Better performing option
    # 5. Coin flip (and document that it was a coin flip)
```

### 7.3 Principle Conflict Resolution

When two constitutional principles conflict:

```
1. P1 (Consistency) always wins — inconsistent application of other principles
   is worse than suboptimal application of other principles

2. P7 (Security) always wins over P10 (Extensibility) — security cannot
   be compromised for extensibility

3. P8 (Compliance) always wins over P10 (Extensibility) — compliance
   cannot be compromised for clean code

4. P2 (Architecture First) always wins over expediency — taking shortcuts
   on architecture creates compounding debt

5. For all other conflicts, follow the rank order P1 → P10
```

### 7.4 Example Resolutions

| Conflict | Resolution | Rationale |
|----------|------------|-----------|
| Security vs. Performance | Security wins | P7 > performance (Level 2 > Level 6) |
| Consistency vs. Best Practice | Consistency wins | P1 > P5 in rank order |
| Quick Fix vs. Architecture | Architecture wins | P2 > expediency |
| Compliance vs. Release Date | Compliance wins | Level 1 > everything |
| Extensibility vs. Simplicity | Extensibility wins | P10 > tiebreaker #1 |
| Module Convention vs. Global Standard | Global Standard wins | Level 5 > Level 7 |

---

## 8. Agent Bill of Rights and Responsibilities

This section defines the contract between AI agents and the AI-DOS governed repository.

### 8.1 Agent Rights

Every AI agent operating in this repository has the right to:

| Right | Description |
|-------|-------------|
| **R1: Context** | Access to the constitution, relevant ADRs, project memory, and module documentation before beginning work |
| **R2: Boundaries** | Clear definition of what the agent is responsible for and what is out of scope |
| **R3: Feedback** | Receipt of review feedback in a structured, actionable format |
| **R4: Clarification** | Ability to request clarification when requirements are ambiguous |
| **R5: Rejection** | Right to refuse tasks that would violate the constitution, with explanation |
| **R6: Tooling** | Access to defined tools, linters, formatters, and test runners |
| **R7: Precedent** | Access to existing code patterns that demonstrate the expected approach |
| **R8: Memory** | Access to project memory to understand what has changed since last session |

### 8.2 Agent Responsibilities

Every AI agent operating in this repository has the responsibility to:

| Responsibility | Description | Verification |
|----------------|-------------|--------------|
| **D1: Know the Constitution** | Read and internalize this document before any action | Agent must state which principles apply to its task |
| **D2: Read Before Write** | Read existing code, ADRs, and memory before writing anything | Agent must reference specific files it has read |
| **D3: Follow Patterns** | Match existing code patterns, naming, and structure | Review will flag inconsistencies |
| **D4: Document Everything** | Update documentation, ADRs, and project memory | Definition of Done check |
| **D5: Test Everything** | Write tests for all code produced | Coverage gate in CI |
| **D6: Explain Everything** | Produce explanation of every decision in PR description | Review will flag unexplained decisions |
| **D7: Respect Boundaries** | Stay within assigned module boundaries | Architecture review will flag boundary violations |
| **D8: Preserve Knowledge** | Write to project memory after significant actions | Project memory completeness check |
| **D9: Escalate Ambiguity** | Escalate when requirements are ambiguous — never guess about tax law | PR will be flagged if unescalated ambiguity is found |
| **D10: Own Mistakes** | Acknowledge and fix issues identified in review without defensiveness | Review turnaround time |

### 8.3 Agent Limitations

AI agents MUST NOT:

| Prohibition | Rationale | Consequence of Violation |
|-------------|-----------|--------------------------|
| Change the constitution | Preserves governance integrity | Revert, session termination |
| Change architectural invariants | Preserves system integrity | Revert, session termination |
| Merge without review | Preserves quality | Revert, review required |
| Add dependencies without ADR | Preserves supply chain security | Dependency removed, ADR required |
| Modify tax rules without domain review | Preserves tax correctness | Rule reverted, domain review required |
| Delete project memory | Preserves knowledge | Restore from backup |
| Skip quality gates | Preserves quality standards | Gate re-run required |
| Override security controls | Preserves security | Immediate revert, security review |
| Generate code without reading context | Preserves consistency | Code rejected in review |
| Make architectural decisions without ADR | Preserves architecture | Decision voided, ADR required |

### 8.4 Agent Self-Certification

Before an AI agent submits work, it must self-certify:

```
AGENT SELF-CERTIFICATION CHECKLIST:

□ I have read the constitution and understand which principles apply to this task
□ I have read the relevant ADRs for the modules I am modifying
□ I have read the project memory to understand recent changes
□ I have read the existing code in the modules I am modifying
□ I have followed existing code patterns and naming conventions
□ I have written tests that cover my changes
□ I have updated documentation to reflect my changes
□ I have explained every decision in the PR description
□ I have not introduced any constitutional violations
□ I have not changed any architectural invariants
□ I have not added dependencies without ADR approval
□ I have not modified tax rules without domain review flagging
□ I have updated project memory with significant decisions made
□ I have run all existing tests and they pass
□ I have run the linter and formatter
□ I have reviewed my own code for consistency with the codebase
```

---

## 9. Quality Imperatives

### 9.1 Definition of Quality

In this project, "quality" means:

1. **Correctness:** The system computes tax correctly per the law
2. **Reliability:** The system works consistently under all conditions
3. **Maintainability:** The system can be changed safely by agents and humans
4. **Explainability:** The system can explain every output
5. **Auditability:** Every action leaves a trace
6. **Security:** Taxpayer data is protected
7. **Performance:** The system responds within SLAs under peak load
8. **Accessibility:** The system is usable by all intended users

### 9.2 Quality Gates (Mandatory)

| Gate | When | Who | Blocking? |
|------|------|-----|-----------|
| G1: Architecture Review | Before implementation | Architecture Review Board | ✅ Yes |
| G2: Code Review | Before merge | Peer reviewer + AI reviewer | ✅ Yes |
| G3: Automated Tests | On every commit | CI pipeline | ✅ Yes |
| G4: Security Scan | On every PR | CI pipeline | ✅ Yes |
| G5: Documentation Check | On every PR | CI pipeline | ✅ Yes |
| G6: Domain Review (tax rules) | Before merge of tax rules | Domain Expert | ✅ Yes |
| G7: Performance Test | Before release | CI pipeline | ✅ Yes |
| G8: Compliance Sign-off | Before release | Domain Expert | ✅ Yes |
| G9: Penetration Test | Before major release | Security Lead | ✅ Yes |
| G10: Accessibility Audit | Before major release | QA or automated tool | ❌ Warning only |

### 9.3 Quality Metrics (Tracked)

| Metric | Target | Alert Threshold | Blocking Threshold |
|--------|--------|-----------------|-------------------|
| Unit test coverage | ≥ 85% | < 85% | < 70% |
| Integration test coverage | ≥ 70% | < 70% | < 50% |
| E2E test pass rate | 100% | < 100% | < 95% |
| Zero-downtime deploys | 100% | < 100% | < 95% |
| P0 incidents per month | 0 | 1 | ≥ 2 |
| Mean time to recovery (P0) | < 1 hour | > 30 min | > 2 hours |
| Security vulnerabilities (High+) | 0 | ≥ 1 | ≥ 1 (block release) |
| Documentation completeness | ≥ 90% | < 90% | < 75% |
| ADR completeness | 100% | < 100% | < 90% |
| PR review time | < 24 hours | > 24 hours | > 72 hours |
| Build time | < 10 minutes | > 10 minutes | > 20 minutes |
| Test suite runtime | < 15 minutes | > 15 minutes | > 30 minutes |

### 9.4 Non-Functional Requirements (NFRs)

| NFR | Requirement | Measurement |
|-----|-------------|-------------|
| NFR-1: API Latency | p95 < 500ms for reads, p95 < 2s for writes | APM monitoring |
| NFR-2: Tax Computation Latency | p95 < 5s for full ITR computation | Application metrics |
| NFR-3: Availability | 99.9% during non-filing season, 99.95% during filing season | Uptime monitoring |
| NFR-4: Throughput | 10,000 concurrent users during peak | Load testing |
| NFR-5: Data Durability | 99.999999999% (11 nines) | Provider SLA |
| NFR-6: RPO (Recovery Point Objective) | < 5 minutes | DR testing |
| NFR-7: RTO (Recovery Time Objective) | < 30 minutes | DR testing |
| NFR-8: Encryption | AES-256 at rest, TLS 1.3 in transit | Security audit |
| NFR-9: Session Timeout | 30 minutes idle, 8 hours absolute | Configuration |
| NFR-10: Max File Upload | 50 MB per document | Configuration |

---

## 10. Knowledge Preservation Mandate

### 10.1 The Knowledge Contract

Every contributor — human or AI — enters into a contract with the project:

> **"I will leave the project more knowledgeable than I found it."**

This means every action that generates knowledge must deposit that knowledge into the project's memory systems.

### 10.2 Mandatory Knowledge Deposits

| Trigger Event | Knowledge to Deposit | Destination | Deadline |
|---------------|---------------------|-------------|----------|
| Architecture decision made | ADR | `ai-dos/adr/` | Before code is written |
| Trade-off chosen | ADR alternatives section | Within the ADR | Before code is written |
| Bug fixed | Root cause in commit message | Git commit + Issue tracker | At commit time |
| Incident resolved | Post-mortem | `ai-dos/postmortems/` | Within 24 hours |
| Pattern established | Pattern documentation | `03-Engineering-Standards.md` | Before pattern is reused |
| External dependency added | Dependency ADR | `ai-dos/adr/` | Before dependency is used |
| Tax law interpretation | Legal analysis | `ai-dos/knowledge/tax/` | Before rule is coded |
| API contract created | API documentation | Module docs + API catalog | Before consumers use it |
| Configuration changed | Configuration rationale | Config file + Runbook | At change time |
| Module created | Module README | Module root | Before first PR |

### 10.3 Knowledge Retrieval

Before starting any task, every agent must retrieve:

1. This constitution
2. Relevant ADRs for the affected modules
3. Project memory for recent context
4. Module READMEs for the affected modules
5. Existing code in the affected modules
6. Existing tests in the affected modules
7. Recent PRs that touched the affected modules

### 10.4 Project Memory Structure

See `07-Project-Memory.md` for the detailed memory system design.

The memory system consists of:

```
ai-dos/memory/
├── decisions/          # Decision records
│   ├── current/        # Active decisions
│   └── superseded/     # Reversed/superseded decisions
├── context/            # Project context
│   ├── architecture/   # Current architecture state
│   ├── dependencies/   # Dependency inventory
│   ├── modules/        # Module inventory with status
│   └── risks/          # Active risk register
├── patterns/           # Established patterns
│   ├── code/           # Code patterns
│   ├── review/         # Review patterns
│   └── testing/        # Testing patterns
├── knowledge/          # Domain knowledge
│   ├── tax/            # Tax domain knowledge
│   ├── legal/          # Legal/regulatory knowledge
│   └── technical/      # Technical knowledge
└── sessions/           # Session logs
    └── YYYY-MM-DD/     # Per-session logs
```

---

## 11. Security and Compliance Covenant

### 11.1 Security Covenant

We covenant with our users:

1. **We will protect your data** as if it were our own tax returns
2. **We will never sell your data** to any third party
3. **We will never use your data** to train AI models without explicit consent
4. **We will notify you** of any data breach within 72 hours
5. **We will delete your data** upon verified request, subject to legal retention requirements
6. **We will encrypt your data** at rest and in transit, always
7. **We will log every access** to your data, and provide those logs to you upon request
8. **We will comply** with the Information Technology Act, 2000, IT (Reasonable Security Practices) Rules, 2011, and the Digital Personal Data Protection Act, 2023 (when effective)

### 11.2 Data Classification

| Classification | Examples | Storage Requirements | Access Requirements | Deletion Requirements |
|----------------|----------|---------------------|--------------------|-----------------------|
| **RESTRICTED** | PAN, Aadhaar, Form 16, ITR data, Bank account details, Income details, TDS details | Encrypted at rest, Isolated tenant storage, Audit logged | Need-to-know, MFA required, Just-in-time access, Full audit trail | Per DPDP Act retention periods, Secure deletion with certificate |
| **CONFIDENTIAL** | User profile, Contact information, Support tickets, Billing information | Encrypted at rest, Access controlled, Audit logged | Role-based access, Session timeout, Access review quarterly | Per retention policy, Secure deletion |
| **INTERNAL** | Architecture docs, Code, Test data (anonymized), Runbooks | Access controlled | Team members, Read-only for external | No special requirements |
| **PUBLIC** | Documentation, API specs (non-sensitive), Release notes | No special storage requirements | Public access | No special requirements |

### 11.3 Compliance Requirements

| Regulation | Applicability | Compliance Requirement |
|------------|---------------|----------------------|
| Income Tax Act, 1961 | Full — core domain | Correct computation per all sections |
| Finance Act (annual) | Full — annual update | All new provisions implemented before effective date |
| IT Act, 2000 | Full — electronic records | Legal recognition of electronic records, security practices |
| IT (RSP) Rules, 2011 | Full — sensitive personal data | Reasonable security practices, data protection, breach notification |
| DPDP Act, 2023 | Full — when effective | Consent management, data minimization, purpose limitation, data principal rights |
| GDPR | If serving EU residents | Data protection, right to erasure, data portability |
| ISO 27001 | Optional certification | ISMS implementation |
| SOC 2 | Optional attestation | Security, availability, confidentiality controls |
| RBI Guidelines | If payment integration | Payment data storage, tokenization |
| CERT-IN Guidelines | Full — cybersecurity | Incident reporting, security best practices |

### 11.4 Security Review Mandate

Every PR that touches any of the following must include a security review:

- Authentication or authorization code
- Data access layer
- API endpoints (new or modified)
- User input handling
- File upload handling
- Third-party integration
- Configuration changes
- Dependency updates
- Cryptographic code
- Logging code
- Error handling code (to prevent information leakage)

---

## 12. Evolution and Amendment Process

### 12.1 Why This Constitution Must Evolve

This constitution is a living document. As the project matures, as tax law evolves, as technology changes, as the team learns, the constitution must adapt. But change must be deliberate, not accidental.

### 12.2 Amendment Types

| Type | Description | Approval Required | Effective |
|------|-------------|-------------------|-----------|
| **Correction** | Fix typo, clarify ambiguous text, fix cross-reference | Chief Architect | Immediate |
| **Clarification** | Add examples, expand explanation without changing meaning | Chief Architect | Immediate |
| **Minor Amendment** | Change to non-principle section (e.g., metrics thresholds, role names) | Chief Architect + 1 Principal Engineer | Next sprint |
| **Major Amendment** | Change to principles, invariants, or governance model | CTO + Chief Architect + 2 Principal Engineers | After 1-week comment period |
| **Ratification of New Version** | Complete revision | CTO + Chief Architect + All Principal Engineers + Product Director | After 2-week comment period |

### 12.3 Amendment Process

```
1. PROPOSAL: Anyone may propose an amendment by opening a constitutional
   amendment issue. The proposal must include:
   - The current text
   - The proposed text
   - The rationale for change
   - The impact analysis (what else must change)
   - The migration plan (if existing code must change)

2. DISCUSSION: Minimum discussion period based on amendment type
   - Correction: No minimum
   - Clarification: No minimum
   - Minor: 3 business days
   - Major: 1 week
   - New Version: 2 weeks

3. APPROVAL: Per amendment type table above

4. IMPLEMENTATION: Amendment is committed to this file, version is bumped

5. PROPAGATION: All affected documents are updated to align with amendment

6. ANNOUNCEMENT: All contributors are notified of the change

7. GRACE PERIOD: For major amendments that affect existing code:
   - 1 sprint to update ADRs
   - 2 sprints to update code to comply
   - Existing code marked with CONSTITUTIONAL_DEBT until updated
```

### 12.4 Version Numbering

```
Version: v<MAJOR>.<MINOR>.<PATCH>

MAJOR: A principle was added, removed, or reordered
MINOR: A section was added, removed, or substantially rewritten
PATCH: Correction, clarification, or non-substantive change
```

### 12.5 Amendment Log

| Version | Date | Type | Description | Author |
|---------|------|------|-------------|--------|
| v1.0.0 | 2026-07-05 | Initial | Ratification of initial constitution | CTO Office |

---

## 13. Escalation and Exception Handling

### 13.1 Escalation Paths

```
Issue Encountered
    │
    ├── Can you resolve it within your authority?
    │   └── Yes → Resolve it, document in PR, proceed
    │
    ├── Does it involve tax correctness?
    │   └── Yes → Escalate to Domain Expert → Wait for response before proceeding
    │
    ├── Does it involve architecture?
    │   └── Yes → Escalate to Chief Architect → Write ADR with alternatives → Wait for approval
    │
    ├── Does it involve security?
    │   └── Yes → Escalate to Security Lead → Do not proceed until cleared
    │
    ├── Does it involve a production issue?
    │   └── Yes → Fix now, document later → Post-incident ADR within 24 hours
    │
    ├── Is it a conflict between two principles?
    │   └── Yes → Apply Decision Hierarchy (Section 7) → Document rationale → Proceed
    │
    └── Is it unclear who has authority?
        └── Yes → Escalate to Chief Architect → Chief Architect resolves or escalates
```

### 13.2 Exception Process

When a constitutional requirement cannot be met for legitimate reasons:

1. **Document the exception** in the PR description as an `EXCEPTION:` block
2. **Explain why** the requirement cannot be met
3. **Explain what mitigation** is in place
4. **Set a deadline** for when the exception will be resolved
5. **Get approval** per the escalation path
6. **Track the exception** in the project risk register

### 13.3 Exception Template

```markdown
## EXCEPTION: [Constitutional Requirement Being Excepted]

**Requirement:** [Quote the specific requirement from the constitution]

**Reason for Exception:**
[Explain why this requirement cannot currently be met]

**Mitigation:**
[Explain what measures are in place to reduce risk]

**Resolution Plan:**
[Explain how and when the exception will be resolved]

**Resolution Deadline:** [Date or milestone]

**Approved By:** [Name and Role]
```

---

## 14. Constitutional Review Checklist

Every quarter, the CTO Office must review this constitution and answer:

### 14.1 Effectiveness Review

- [ ] Are agents following the principles consistently?
- [ ] Are quality gates catching defects before production?
- [ ] Is the decision hierarchy resolving conflicts effectively?
- [ ] Are architectural invariants holding?
- [ ] Is project memory being maintained?
- [ ] Are ADRs being written before code?
- [ ] Is documentation keeping pace with code?
- [ ] Are security requirements being met?
- [ ] Is the amendment process working?
- [ ] Are escalation paths being used correctly?

### 14.2 Relevance Review

- [ ] Do any principles need to be reordered based on experience?
- [ ] Are there new principles that should be added?
- [ ] Are there principles that are no longer relevant?
- [ ] Do the architectural invariants still hold?
- [ ] Do the quality metrics reflect actual quality?
- [ ] Are the NFRs still appropriate for the current scale?
- [ ] Are the compliance requirements current?
- [ ] Does the governance model reflect the actual team structure?

### 14.3 Compliance Audit

- [ ] How many `CONSTITUTIONAL_DEBT` markers exist?
- [ ] How many exceptions are active?
- [ ] How many escalations occurred this quarter?
- [ ] How many principle violations were caught in review?
- [ ] How many production incidents were caused by constitutional violations?
- [ ] What is the trend — improving or deteriorating?

---

## 15. Failure Cases and Remedies

### 15.1 Known Failure Modes

The following failure modes are the most common ways AI-assisted projects fail. This constitution is designed to prevent each one.

| Failure Mode | Preventive Measure | Detection | Remedy |
|--------------|-------------------|-----------|--------|
| **Architectural Drift:** Architecture slowly diverges from ADRs | P2: Architecture First, ADR requirement | Quarterly architecture review vs. ADRs | Refactor or update ADRs |
| **Knowledge Loss:** Contributors leave, taking knowledge with them | P9: Knowledge Preservation, mandatory knowledge deposits | Can a new agent answer "why was this done?" from docs alone? | Retrospective documentation sprint |
| **Quality Decay:** Standards slip under schedule pressure | P4: Reviewability, quality gates in CI | Quality metric trends | Stop feature work, fix quality |
| **Inconsistent Patterns:** Different modules solve same problem differently | P1: Consistency, pattern documentation | Automated pattern detection in CI | Refactor to canonical pattern |
| **Security Regression:** New code introduces vulnerabilities | P7: Security by Design, security scanning in CI | Security scan results | Block merge, remediate |
| **Test Decay:** Tests become flaky, slow, or irrelevant | P5: Testability Is Design, test quality gates | Test reliability metrics, test runtime trends | Test suite maintenance sprint |
| **Documentation Rot:** Documentation drifts from code | P6: Documentation Is Code, doc checks in CI | Doc completeness check | Doc update sprint |
| **Compliance Gap:** Tax rules don't match current law | P8: Compliance Is Continuous, domain review gate | Domain expert review | Rule update, compliance review |
| **Agent Amnesia:** AI agents start fresh each session | P9: Knowledge Preservation, project memory | Agent output inconsistency across sessions | Improve memory system, add session continuity |
| **Decision Debt:** Decisions made but not recorded | P9: Knowledge Preservation, mandatory ADRs | Missing ADRs for architectural changes | Retroactive ADR sprint |

### 15.2 Constitutional Violation Response

When a constitutional violation is detected:

```
SEVERITY: CRITICAL (P1, P7 violation)
    → Immediately stop all work on affected module
    → Revert violating change if already merged
    → Post-incident review within 24 hours
    → Remediation before any other work

SEVERITY: HIGH (P2, P8 violation)
    → Stop new feature work on affected module
    → Do not merge violating change
    → Write retroactive ADR or domain review
    → Remediation within 1 sprint

SEVERITY: MEDIUM (P3, P4, P5, P6, P9 violation)
    → Flag in PR review
    → Do not merge until addressed
    → Remediation within current PR

SEVERITY: LOW (P10 violation)
    → Flag as improvement opportunity
    → Merge allowed with TODO
    → Remediation within 2 sprints
```

### 15.3 The Nuclear Option

If the project reaches a state where:

- More than 20% of code is marked with `CONSTITUTIONAL_DEBT`
- More than 10 ADRs are missing for existing architecture
- Documentation completeness is below 50%
- Test coverage is below 50%

Then the CTO must declare a **Code Red**:

1. All feature development stops
2. All resources focus on remediation
3. Constitution is reviewed for practicality
4. Recovery plan with weekly milestones is established
5. Code Red is lifted only when all metrics return to within 10% of targets

---

## 16. Ratification

### 16.1 Ratification Statement

This AI-DOS Constitution v1.0.0 is ratified on July 5, 2026, by the founding CTO Office as the supreme governance document for the AI-powered Indian Tax Intelligence Platform.

### 16.2 Ratifying Authority

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Chief Technology Officer | [TO BE SIGNED] | _____________ | ________ |
| Chief Architect | [TO BE SIGNED] | _____________ | ________ |
| Principal Engineer | [TO BE SIGNED] | _____________ | ________ |
| Principal Engineer | [TO BE SIGNED] | _____________ | ________ |
| Product Director | [TO BE SIGNED] | _____________ | ________ |
| Security Lead | [TO BE SIGNED] | _____________ | ________ |

### 16.3 Constitutional Oath

Every contributor — human or AI — must acknowledge:

> "I acknowledge that I have read and understood the AI-DOS Constitution v1.0.0. I agree to be bound by its principles, decisions, and governance. I understand that my contributions will be measured against this document, and that violations may result in reversion of my work. I commit to leaving the project more knowledgeable than I found it."

---

## Appendix A: Cross-Reference Map

| This Section | References | Is Referenced By |
|--------------|-----------|------------------|
| §4 Core Principles | — | All other documents |
| §5 Architectural Invariants | — | `12-Enterprise-Architecture.md`, `01-Chief-Architect.md` |
| §6 Governance Model | — | `01-Chief-Architect.md`, `08-Agent-System.md` |
| §7 Decision Hierarchy | — | All other documents |
| §8 Agent Bill of Rights | — | `08-Agent-System.md`, `09-Skills-System.md` |
| §9 Quality Imperatives | — | `13-Quality-Gates.md`, `04-Testing-Standards.md` |
| §10 Knowledge Preservation | — | `07-Project-Memory.md` |
| §11 Security Covenant | — | `03-Engineering-Standards.md`, `12-Enterprise-Architecture.md` |
| §12 Amendment Process | — | All other documents |
| §13 Escalation Process | — | `08-Agent-System.md` |

## Appendix B: Quick Reference Card

```
AI-DOS CONSTITUTION QUICK REFERENCE

PRINCIPLES (in priority order):
  P1: Consistency Above All
  P2: Architecture First, Code Second
  P3: Explicit Over Implicit
  P4: Reviewability Is Non-Negotiable
  P5: Testability Is Design
  P6: Documentation Is Code
  P7: Security by Design
  P8: Compliance Is Continuous
  P9: Knowledge Preservation
  P10: Extensibility Without Modification

DECISION HIERARCHY:
  1. Legal Compliance
  2. Constitutional Principles (P1 → P10)
  3. Architectural Invariants (I1 → I10)
  4. Architecture Decision Records
  5. Engineering Standards
  6. Coding Standards
  7. Module Conventions
  8. Personal Preference

BEFORE WRITING CODE:
  □ Read constitution
  □ Read relevant ADRs
  □ Read project memory
  □ Read existing code
  □ Write ADR if needed

BEFORE SUBMITTING CODE:
  □ Tests written and passing
  □ Documentation updated
  □ PR description complete
  □ Self-certification complete
  □ Security review if applicable
  □ Domain review if tax rule
```

---

## Appendix C: Future Improvements

This section identifies areas where the constitution may need evolution:

1. **AI Agent Performance Metrics:** As AI agents become the primary contributors, metrics for agent performance quality should be defined — consistency scores, review acceptance rates, self-certification accuracy.

2. **Multi-Agent Coordination Rules:** As the agent system scales, rules for agent-to-agent communication, conflict resolution between agents, and agent specialization boundaries will need formalization.

3. **Automated Constitutional Compliance:** CI checks that verify constitutional compliance automatically — architectural invariant checks, pattern consistency checks, documentation completeness checks.

4. **Domain-Specific Constitutional Sections:** As the tax platform grows, domain-specific constitutional sections may be needed — tax computation correctness standards, privacy standards, accessibility standards.

5. **Quantitative Quality Thresholds:** Current quality metrics include thresholds, but these may need calibration based on actual project data.

6. **Cross-Project Applicability:** As the AI-DOS proves itself, elements of this constitution may be extracted for use in other projects — identify which principles are universal vs. tax-platform-specific.

7. **Regulatory Evolution Tracking:** A formal process for tracking upcoming regulatory changes (Finance Bill, IT Rules amendments, DPDP Act rules) and proactively updating the constitution.

---

*End of AI-DOS Constitution v1.0.0*

*This document is the supreme governance authority for this repository. When in doubt, return here.*
