# Project Memory — Index

> **Purpose:** Navigation index for the Project Memory system. Every session, the Architect Agent reads this first.
> **Last Updated:** 2026-07-05
> **Session ID:** INIT

---

## Memory File Map

```
D:\IT_Returns\
│
├── CLAUDE.md                    ← Agent bootstrap — READ FIRST
│
├── docs/
│   ├── governance/
│   │   ├── 00-Constitution.md   ← SUPREME governance
│   │   ├── 01-Chief-Architect.md
│   │   └── 03-Engineering-Standards.md
│   │
│   ├── architecture/
│   │   └── ENTERPRISE_CAPABILITY_MODEL*.md  ← FROZEN target
│   │
│   ├── recovery/
│   │   └── ARCHITECTURE_RECOVERY_REPORT.md  ← Current state
│   │
│   ├── gap-analysis/
│   │   ├── EnterpriseGapReport.md
│   │   ├── ArchitectureHealthScore.md
│   │   ├── DomainMaturityMatrix.md
│   │   ├── TechnicalDebtHeatmap.md          ← CANONICAL debt register
│   │   └── EnterpriseRiskMatrix.md
│   │
│   ├── domain/
│   │   └── BusinessRules.md
│   │
│   └── ai-dos/
│       ├── memory/                            ← YOU ARE HERE (Project Memory)
│       │   ├── README.md
│       │   ├── CompletedFeatures.md
│       │   ├── Decisions.md
│       │   ├── FinanceAct.md
│       │   ├── FutureIdeas.md
│       │   ├── InterviewLogic.md
│       │   ├── KnownIssues.md
│       │   ├── TaxRules.md
│       │   └── feedback-false-positive-pr4.md  ← CRITICAL: never declare complete without running verification
│       │
│       └── archive/                           ← SUPERSEDED documents
│           ├── Architecture-v0.1.md
│           └── TechnicalDebt-v0.1.md
```

---

## Architect Agent — Session Protocol

Every session, the Architect Agent:

### On Session Start

1. **Read this index** (memory/README.md)
2. **Read recent Decisions** (Decisions.md — last 10 decisions)
3. **Read Architecture** (Architecture.md — current state)
4. **Check Known Issues** (KnownIssues.md — any new P0/P1?)
5. **Check Technical Debt** (TechnicalDebt.md — any items past deadline?)
6. **Determine what changed** since last session

### During Session

7. **Update relevant files** as work happens
8. **Add decisions** to Decisions.md as they're made
9. **Register new issues** in KnownIssues.md as they're found
10. **Register new debt** in TechnicalDebt.md as it's incurred
11. **Update Architecture.md** if architecture changes
12. **Update BusinessRules.md** if business understanding evolves
13. **Update TaxRules.md** when rules are implemented or changed
14. **Update InterviewLogic.md** when interview flow changes
15. **Update CompletedFeatures.md** when features ship
16. **Capture future ideas** in FutureIdeas.md

### On Session End

17. **Update session log** at the bottom of every changed file
18. **Write session summary** to sessions/YYYY-MM-DD/session-N.md
19. **Commit all memory changes** with message: `memory: session update YYYY-MM-DD`

---

## File Dependencies

```
Architecture.md ──── defines system structure
    │
    ├── BusinessRules.md ──── business logic that architecture must support
    │   ├── FinanceAct.md ──── legal versioning of business rules
    │   └── TaxRules.md ────── implemented rules catalog
    │
    ├── InterviewLogic.md ──── UX architecture for data collection
    │
    ├── CompletedFeatures.md ─ what's built (output of architecture)
    ├── KnownIssues.md ─────── what's broken (feedback loop)
    ├── TechnicalDebt.md ───── what's owed (architecture violations)
    ├── Decisions.md ───────── why we chose this way (architecture rationale)
    └── FutureIdeas.md ─────── where we're going (architecture evolution)
```

---

## Consistency Rules

1. **Architecture.md is the source of truth.** All other files must be consistent with it.
2. **Decisions.md explains Architecture.md.** Every architecture choice should have a decision record.
3. **BusinessRules.md drives TaxRules.md.** Business understanding precedes implementation.
4. **CompletedFeatures.md + KnownIssues.md + TechnicalDebt.md = current project health.** These three files together give a complete picture.
5. **No contradictions.** If two memory files disagree, Architecture.md wins, and the contradiction must be resolved.

---

## Quick Reference: Which File to Update?

| When You... | Update This File |
|-------------|-----------------|
| Make an architecture decision | Architecture.md + Decisions.md |
| Implement a tax rule | TaxRules.md |
| Discover a new business rule | BusinessRules.md |
| Implement a Finance Act change | FinanceAct.md + TaxRules.md + BusinessRules.md |
| Design an interview question | InterviewLogic.md |
| Ship a feature | CompletedFeatures.md |
| Find a bug | KnownIssues.md |
| Take a shortcut | TechnicalDebt.md |
| Have an idea | FutureIdeas.md |
| Change your mind about a decision | Decisions.md (mark as REVERSED) |
| Fix a bug | KnownIssues.md (mark RESOLVED) |
| Repay debt | TechnicalDebt.md (mark RESOLVED) |

---

*This index is the map. When lost, return here.*
