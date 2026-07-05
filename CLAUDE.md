# CLAUDE.md — TaxStox ITR Platform

> **Repository:** D:\IT_Returns
> **Purpose:** Enterprise AI-Powered Indian Tax Intelligence Platform
> **This file:** Bootstrap for all AI agents. Read before any action.

---

## Mandatory Reading Order

Every AI agent MUST read these documents in this exact order before taking any action:

1. **[docs/governance/00-Constitution.md](docs/governance/00-Constitution.md)** — Supreme governance. Non-negotiable principles. Decision hierarchy. Architectural invariants.
2. **[docs/ai-dos/memory/README.md](docs/ai-dos/memory/README.md)** — Architect session protocol. How project memory works. Which files to update when.
3. **[docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md](docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md)** — FROZEN target architecture. 148 capabilities. 15 bounded contexts. Do NOT modify.
4. **[docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md](docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md)** — Current architecture state. Evidence-backed from 42-module code audit.

---

## Authority Hierarchy (Permanent)

```
1. Constitution                    ← SUPREME (docs/governance/)
2. Chief Architect                 ← Architecture governance (docs/governance/)
3. Enterprise Capability Model     ← FROZEN target (docs/architecture/)
4. Architecture Recovery Report    ← Current state (docs/architecture/)
5. Enterprise Gap Report           ← Diagnostics (docs/architecture/)
6. ADRs                            ← Decision records (docs/adr/)
7. Engineering Standards           ← Coding rules (docs/governance/)
8. Design Documents                ← Specs (design/)
9. Source Code                     ← Implementation (apps/)
10. Project Memory                  ← Living docs (docs/ai-dos/memory/)
```

Higher levels override lower levels. No exceptions.

---

## Governance Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Constitution | `docs/governance/00-Constitution.md` | 10 non-negotiable principles, 10 architectural invariants, decision hierarchy |
| Chief Architect | `docs/governance/01-Chief-Architect.md` | ADR process, module boundaries, technology stack governance |
| Engineering Standards | `docs/governance/03-Engineering-Standards.md` | Coding standards, naming conventions, error handling, logging, security |
| Testing Standards | `docs/governance/04-Testing-Standards.md` | NOT YET CREATED — test pyramid, coverage requirements, test patterns |
| Review Standards | `docs/governance/05-Review-Standards.md` | NOT YET CREATED — PR process, reviewer checklist |
| Quality Gates | `docs/governance/13-Quality-Gates.md` | NOT YET CREATED — quality gate definitions per phase |

---

## Architecture Documents

| Document | Location | Status |
|----------|----------|--------|
| Enterprise Capability Model | `docs/architecture/ENTERPRISE_CAPABILITY_MODEL*.md` (4 parts) | **FROZEN** — Do not modify |
| Architecture Recovery Report | `docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md` | Current state authority |
| Enterprise Gap Report | `docs/architecture/EnterpriseGapReport.md` | 148-capability gap analysis |
| Architecture Health Score | `docs/architecture/ArchitectureHealthScore.md` | Overall 31/100 |
| Domain Maturity Matrix | `docs/architecture/DomainMaturityMatrix.md` | 15 bounded contexts, 14% coverage |
| Technical Debt Heatmap | `docs/architecture/TechnicalDebtHeatmap.md` | Canonical debt register (64 items) |
| Enterprise Risk Matrix | `docs/architecture/EnterpriseRiskMatrix.md` | 15 risks (4 Critical) |
| ADRs | `docs/adr/` | Architecture Decision Records |
| Architecture Index | `docs/architecture/README.md` | Full architecture document listing |
| Chronological Navigation | `docs/recovery/README.md`, `docs/gap-analysis/README.md` | Phase-based entry points |

---

## Project Memory (Living Documents)

**Location:** `docs/ai-dos/memory/`
**Updated:** By Architect Agent every session

| File | Purpose |
|------|---------|
| `README.md` | Memory index + Architect session protocol |
| `CompletedFeatures.md` | Feature registry, milestones, release history |
| `Decisions.md` | Chronological decision log |
| `FinanceAct.md` | Finance Act version tracker FY2020-26 |
| `FutureIdeas.md` | Idea backlog, horizon planning |
| `InterviewLogic.md` | Adaptive interview engine architecture |
| `KnownIssues.md` | Bug & issue registry |
| `TaxRules.md` | Tax rule catalog, metadata standards |
| `BusinessRules.md` (→ `docs/domain/BusinessRules.md`) | Tax business rules reference |

---

## Domain Knowledge

| Document | Location |
|----------|----------|
| Business Rules | `docs/domain/BusinessRules.md` |
| Data Model | `docs/DATA_MODEL.md` |
| ITR Question Trees | `docs/ITR_TYPES_QUESTIONS.md` |

---

## Design Specifications

**Location:** `design/`
- Product requirements, NFRs, architecture designs
- UI prototypes (HTML + screenshots)
- Design tokens and design system

---

## Source Code

| Component | Location | Technology |
|-----------|----------|------------|
| Backend API | `apps/api/` | Python 3.12+ / FastAPI / psycopg2 / Pydantic v2 |
| Frontend | `apps/web/` | Next.js 16 / Tailwind CSS 4 / shadcn/ui / Zustand |

---

## Architectural Constraints

### Non-Negotiable
- **P1: Consistency Above All** — Same solution for same problem everywhere
- **P2: Architecture First** — ADR before code
- **P7: Security by Design** — Security cannot be retrofitted
- **P8: Compliance Is Continuous** — Tax law changes annually; platform must adapt
- **I1: Multi-Year Architecture** — Must support any FY without code change
- **I2: Rule-Engine Separation** — Tax rules are data, not code
- **I3: Complete Audit Trail** — Every computation must be traceable
- **I5: Data Isolation** — Taxpayer data isolated at database level

### Current State Constraints
- Modular monolith — FastAPI single process
- PostgreSQL (Neon) via psycopg2 (raw SQL)
- In-memory sessions (24h TTL)
- FY2025-26 hardcoded — single FY only (critical gap)
- NO tests — zero unit/integration/e2e (critical gap)
- 42 Python modules organized by technical layer (not business domain)

---

## Forbidden Actions

AI agents MUST NOT:
- Change the Constitution or Enterprise Capability Model
- Change architectural invariants
- Merge code without review
- Add dependencies without ADR
- Modify tax rules without domain expert review
- Skip quality gates
- Override security controls
- Delete project memory
- Generate code without reading context (Constitution, ADRs, memory, existing code)

---

## Required Workflow

Before ANY code change:
1. Read Constitution
2. Read relevant ADRs for affected modules
3. Read project memory for recent context
4. Read existing code in affected modules
5. Write ADR if architectural decision needed
6. Write tests BEFORE or WITH implementation
7. Update documentation in same PR
8. Update project memory with significant decisions
9. Self-certify using checklist in Constitution §8.4

---

## Quick Reference

```
Constitution violation?      → Stop. Escalate.
Architecture decision?        → Write ADR first.
Tax rule change?             → Domain expert review required.
New dependency?              → ADR + security review.
Found a bug?                 → Register in KnownIssues.md
Took a shortcut?             → Register in TechnicalDebtHeatmap.md
Made a decision?             → Log in Decisions.md
Feature complete?            → Update CompletedFeatures.md
Had an idea?                 → Capture in FutureIdeas.md
Session ended?               → Update session log in all changed memory files
```

---

## Engineer Transition (2026-07-05)

> This section added at handoff. Read before taking any action.

### Current State

The modernization program has completed waves M0 through M7. **M8 (Enterprise Multi-Tenancy) is the next wave.** See [docs/handoff/NEXT_WORK.md](docs/handoff/NEXT_WORK.md).

### Mandatory Session Start

Every new Claude session in this repository MUST:

1. **Read all governance documents first:**
   - [docs/governance/00-Constitution.md](docs/governance/00-Constitution.md)
   - [docs/governance/01-Chief-Architect.md](docs/governance/01-Chief-Architect.md)
   - [docs/governance/03-Engineering-Standards.md](docs/governance/03-Engineering-Standards.md)

2. **Read all frozen architecture documents:**
   - [docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md](docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md) (4 parts)
   - [docs/architecture/EnterpriseModernizationRoadmap.md](docs/architecture/EnterpriseModernizationRoadmap.md)

3. **Read the handoff documents:**
   - [HANDOFF.md](HANDOFF.md)
   - [docs/handoff/PRASOON_ONBOARDING.md](docs/handoff/PRASOON_ONBOARDING.md)
   - [docs/handoff/NEXT_WORK.md](docs/handoff/NEXT_WORK.md)

4. **Determine the current modernization wave** before writing any code.

### Non-Negotiable Rules for All Future Sessions

- **Never regenerate architecture.** ECM, Roadmap, Gap Report are FROZEN.
- **Never redesign bounded contexts.** They are defined in the ECM.
- **Never skip roadmap waves.** Follow the dependency graph exactly.
- **Never modify frozen documents.** Constitution, ECM, Roadmap, Recovery, Gap, Risk, Debt.
- **Never implement work from a future wave.** Complete one wave before starting the next.
- **Never hardcode a tax rule.** Use RuleRepository.
- **Never use raw FY strings.** Use FinancialYear.
- **Never break golden vectors.** Any change altering golden vectors is blocked.
- **Always produce a completion report.** After every wave.
- **Always maintain backward compatibility.** No breaking API changes.

### Current Metrics

- **138 tests, all passing**
- **8 golden vectors, all passing**
- **Architecture health: ~45/100** (target: 80 after M11)
- **Waves complete: 8 of 12**
- **Next wave: M8 — Enterprise Multi-Tenancy**
