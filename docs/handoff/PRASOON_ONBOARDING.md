# Prasoon Onboarding Guide

> **For:** Prasoon — Senior Engineer joining the IT_Returns modernization program
> **Assume:** You just cloned this repo. You have zero context about this project.

---

## Your First 60 Minutes

### Step 1: Read CLAUDE.md (2 min)

Start at `CLAUDE.md` in the repository root. It tells you what this repo is and what to read first.

### Step 2: Read the Constitution (10 min)

`docs/governance/00-Constitution.md`

This is the supreme governance document. It defines:
- 10 non-negotiable principles (Consistency, Architecture First, Security by Design, etc.)
- 10 architectural invariants (Multi-Year, Rule-Engine Separation, Audit Trail, etc.)
- The decision hierarchy (Constitution > Architecture > Standards > Code)
- What AI agents MUST and MUST NOT do

### Step 3: Read the Chief Architect Guide (5 min)

`docs/governance/01-Chief-Architect.md`

This defines:
- How architecture decisions are made (ADR process)
- Module boundary rules
- Technology stack governance

### Step 4: Understand the Target Architecture (10 min)

`docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md` (4 parts)

This is the FROZEN target — 148 capabilities across 15 bounded contexts. You don't need to memorize it. You need to know it exists and that every modernization wave traces back to specific capabilities in this model.

### Step 5: Read the Modernization Roadmap (10 min)

`docs/architecture/EnterpriseModernizationRoadmap.md`

This is your execution blueprint. It defines 12 waves (M0-M11). Waves M0-M7 are complete. **Your first task is M8.**

### Step 6: Read HANDOFF.md (5 min)

`HANDOFF.md` at the repository root. This is the primary reference for all engineers.

### Step 7: Read NEXT_WORK.md (5 min)

`docs/handoff/NEXT_WORK.md` — This tells you exactly what M8 is and what to build.

### Step 8: Explore the Codebase (10 min)

Key directories to understand:
- `apps/api/src/engine/` — Domain logic. This is where you'll add most new code.
- `apps/api/src/engine/rules/` — RuleRepository + RuleEvaluator (M1). You'll use these.
- `apps/api/src/models/` — Domain models.
- `apps/api/tests/` — 138 tests. Run `pytest` to verify.

### Step 9: Run the Tests (3 min)

```bash
cd apps/api
pip install -e ".[dev]"
pytest tests/ --ignore=tests/test_e2e_real_data.py -v
```

You should see: `138 passed`.

---

## Why Each Document Exists

| Document | Why It Exists | When To Read |
|----------|--------------|--------------|
| `00-Constitution.md` | Prevents architectural chaos over time | Before any code |
| `01-Chief-Architect.md` | Governs architecture decisions | Before any architecture change |
| `ENTERPRISE_CAPABILITY_MODEL.md` | Defines what "done" looks like | Reference during implementation |
| `EnterpriseModernizationRoadmap.md` | Defines the execution order | Before starting any work |
| `HANDOFF.md` | Single reference for all engineers | Onboarding |
| `PRASOON_ONBOARDING.md` | This file | Onboarding |
| `NEXT_WORK.md` | Your exact next task | Before M8 |
| `SESSION_SUMMARY.md` | What happened today | Context |

## How The Modernization Program Works

1. The roadmap defines 12 waves (M0-M11)
2. Each wave has specific capabilities to implement
3. Each wave has entry criteria, exit criteria, and quality gates
4. Waves must be executed in order — dependencies are defined in `WaveDependencyMatrix.md`
5. After each wave, produce a completion report in `docs/architecture/M{X}-CompletionReport.md`
6. Never skip waves. Never combine waves.

## How Implementation Decisions Are Made

1. Does the ECM say this capability is needed? → Implement it
2. Is the implementation approach ambiguous? → Write an ADR
3. Does it violate the Constitution? → Don't do it
4. Is there a gap/debt/risk document that covers this? → Follow the remediation
5. None of the above? → Use your engineering judgment, document the decision

## How Architecture Decisions Are Governed

- Architecture changes require an ADR (`docs/adr/history/`)
- ADRs follow the template in `docs/governance/01-Chief-Architect.md` §5
- ADRs must be approved before implementation
- The ECM, Roadmap, and Gap Report are FROZEN — never modify them

## How Quality Gates Work

Every wave has mandatory gates (see `QualityGateFramework.md`):
- Code must pass lint + type check + test + security scan
- Golden vectors must not change
- Documentation must be updated
- Coverage must not decrease

If a gate fails, fix the issue before proceeding to the next wave.

## How Testing Works

- Unit tests for every new module (pytest)
- Golden vectors for tax computation (known inputs → ITD-verified outputs)
- Coverage must not decrease from wave to wave
- CI pipeline runs on every push: lint → typecheck → test → security

## How Traceability Works

Every change must trace to one or more:
- Capability ID (e.g., C8.1) from the ECM
- Debt ID (e.g., ARC-001) from the Debt Heatmap
- Risk ID (e.g., R01) from the Risk Matrix
- Gap finding from the Gap Report

Include these in your completion reports.

---

## Key People (Conceptual)

- **Chief Architect** — Approves ADRs, governs architecture
- **Domain Expert (CA)** — Reviews tax rule changes
- **Tech Lead** — Module-level technical decisions
- **You (Prasoon)** — Implementation within the governance framework

---

*Welcome to the team. Start with M8. Follow the roadmap. Don't skip gates. Good luck.*
