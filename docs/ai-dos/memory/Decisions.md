# Decisions Memory

> **Purpose:** Chronological log of all significant decisions made during the project — architecture, design, process, and strategy.
> **Updated By:** Architect Agent — every session when decisions are made.
> **Last Updated:** 2026-07-05
> **Session ID:** INIT
> **Cross-Refs:** [Architecture.md](Architecture.md), [BusinessRules.md](BusinessRules.md), [TechnicalDebt.md](TechnicalDebt.md)

---

## 1. Decision Registry

### 1.1 Decision Categories

| Category | Description | ADR Required? |
|----------|-------------|---------------|
| `ARCHITECTURE` | Architecture pattern, module boundary, technology choice | ✅ Yes |
| `DESIGN` | API contract, data model, algorithm choice | ✅ If cross-module |
| `PROCESS` | Workflow, methodology, tooling | ❌ No (but log here) |
| `TAX_INTERPRETATION` | How a tax provision is interpreted for implementation | ✅ Domain review |
| `STRATEGY` | Priority, roadmap, scope | ❌ No (but log here) |
| `RISK_ACCEPTANCE` | Conscious decision to accept a known risk | ✅ Chief Architect |

## 2. Decision Log

### 2.1 Latest Decisions

| Decision ID | Date | Category | Title | By | Status | ADR |
|-------------|------|----------|-------|-----|--------|-----|
| DEC-0001 | 2026-07-05 | ARCHITECTURE | AI-DOS as governance framework for entire project | CTO | ACTIVE | Pending |
| DEC-0002 | 2026-07-05 | PROCESS | Project Memory system with 10 files updated every session | CTO | ACTIVE | N/A |
| DEC-0003 | 2026-07-05 | STRATEGY | Build AI-DOS first, then IT_Returns, evolving AI-DOS alongside | CTO | ACTIVE | N/A |
| DEC-0004 | 2026-07-05 | DESIGN | Modular monolith start with schema-per-module isolation | Chief Architect | ACTIVE | Pending |
| DEC-0005 | 2026-07-05 | STRATEGY | FY2025-26 as initial target FY with backward extension | Chief Architect | ACTIVE | N/A |
| DEC-0006 | 2026-07-05 | ARCHITECTURE | Python 3.12+ / FastAPI / PostgreSQL as initial stack | Chief Architect | PROPOSED | Pending |
| DEC-0007 | 2026-07-05 | PROCESS | Architecture Recovery phase completed — 42 modules audited, 15 bounded contexts identified | Chief Architect | ACTIVE | N/A |
| DEC-0008 | 2026-07-05 | ARCHITECTURE | Enterprise Capability Model ratified as FROZEN target architecture — 148 capabilities, 20 domains, 15 bounded contexts | Chief Architect | ACTIVE | N/A |
| DEC-0009 | 2026-07-05 | ARCHITECTURE | Enterprise Gap Analysis completed — 6 fully implemented, 28 partial, 84 not implemented, 30 UNKNOWN; Architecture Health Score 31/100 | Chief Architect | ACTIVE | N/A |
| DEC-0010 | 2026-07-05 | STRATEGY | Platform ready for Enterprise Modernization Roadmap planning | Chief Architect | ACTIVE | N/A |
| DEC-0011 | 2026-07-05 | RISK_ACCEPTANCE | 15 enterprise risks identified: 4 Critical, 5 High, 5 Medium, 1 Low. Top risk: FY2026 obsolescence (95% probability, Critical impact) | Chief Architect | ACTIVE | N/A |

### 2.2 Decision Template

```markdown
### DEC-XXXX: [Title]

**Date:** YYYY-MM-DD
**Category:** [ARCHITECTURE | DESIGN | PROCESS | TAX_INTERPRETATION | STRATEGY | RISK_ACCEPTANCE]
**Made By:** [Name/Role]
**Consulted:** [Names/Roles]
**Informed:** [Names/Roles]
**ADR:** [ADR-NNNN or N/A]
**Status:** [PROPOSED | ACTIVE | SUPERSEDED | REVERSED]

**Context:**
[What situation prompted this decision?]

**Decision:**
[What was decided, clearly and specifically.]

**Rationale:**
[Why was this option chosen over alternatives?]

**Alternatives Considered:**
- [Alternative 1:] [Why not chosen]
- [Alternative 2:] [Why not chosen]

**Consequences:**
- Positive: [What becomes better/easier]
- Negative: [What becomes harder/riskier; what we're accepting]

**Related Decisions:**
- [DEC-XXXX:] [Relationship]
```

## 3. Reversed Decisions

| Decision ID | Original Date | Reversed Date | Reason for Reversal |
|-------------|---------------|---------------|---------------------|
| *No reversed decisions yet* | — | — | — |

## 4. Pending Decisions (To Be Made)

| Priority | Decision Needed | Context | Deadline | Who Decides |
|----------|----------------|---------|----------|-------------|
| P0 | Python vs. TypeScript for backend | Stack selection for Phase 1 | Before first code | Chief Architect |
| P0 | Database schema design approach | ORM vs. raw SQL vs. query builder | Before first migration | Chief Architect |
| P0 | Test framework selection | pytest vs. unittest vs. other | Before first test | Tech Lead |
| P1 | API spec format | OpenAPI vs. GraphQL vs. both | Before API module | Chief Architect |
| P1 | Event bus selection | PostgreSQL LISTEN/NOTIFY vs. Kafka vs. RabbitMQ | Before async work (Phase 2) | Chief Architect |
| P1 | Container orchestration | Docker Compose vs. k8s for development | Before multi-service work | DevOps Lead |
| P2 | Monitoring stack | Prometheus+Grafana vs. SaaS (Datadog/etc.) | Before production deployment | DevOps Lead |
| P2 | CI/CD platform | GitHub Actions vs. GitLab CI vs. Jenkins | Before CI setup | DevOps Lead |

---

## Session Log

| Date | Session ID | Changes Made | Agent |
|------|-----------|--------------|-------|
| 2026-07-05 | INIT | Decisions memory initialized. 6 foundational decisions recorded. | Architect |

---

*This file is the decision journal. When the team asks "why did we do it this way?", the answer is here.*
