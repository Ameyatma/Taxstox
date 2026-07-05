# Documentation Topology Report

> **Date:** 2026-07-05
> **Status:** COMPLETE — Ready for git staging
> **Principle:** One canonical location per document. Index directories for navigation.

---

## 1. Final Directory Tree

```
D:\IT_Returns\
│
├── CLAUDE.md                                   [Agent bootstrap — updated]
├── README.md                                   [Project overview — updated]
├── HANDOFF.md                                  [Historical — dev log]
│
├── docs/
│   ├── governance/                             [CANONICAL — 2 types: docs + index]
│   │   ├── README.md                           ★ NEW — Governance index
│   │   ├── 00-Constitution.md                  (SUPREME)
│   │   ├── 01-Chief-Architect.md
│   │   └── 03-Engineering-Standards.md
│   │
│   ├── architecture/                           [CANONICAL — All enterprise architecture]
│   │   ├── README.md                           ★ NEW — Architecture index
│   │   ├── ENTERPRISE_CAPABILITY_MODEL.md      FROZEN Part 1
│   │   ├── ENTERPRISE_CAPABILITY_MODEL_PART2.md FROZEN Part 2
│   │   ├── ENTERPRISE_CAPABILITY_MODEL_PART3.md FROZEN Part 3
│   │   ├── ENTERPRISE_CAPABILITY_MODEL_PART4.md FROZEN Part 4
│   │   ├── ARCHITECTURE_RECOVERY_REPORT.md     Current state
│   │   ├── EnterpriseGapReport.md              Gap analysis
│   │   ├── ArchitectureHealthScore.md          Health score
│   │   ├── DomainMaturityMatrix.md             Maturity matrix
│   │   ├── TechnicalDebtHeatmap.md             CANONICAL DEBT REGISTER
│   │   ├── EnterpriseRiskMatrix.md             Risk matrix
│   │   ├── RepositoryConsolidationReport.md    Historical
│   │   ├── RepositoryConsolidationPlan.md      Historical
│   │   ├── CONSOLIDATION_COMPLETE.md           Historical
│   │   ├── GitAndDocAudit.md                   Historical
│   │   ├── CanonicalDocumentLayout.md          Design doc
│   │   └── DocumentationTopologyReport.md      THIS FILE
│   │
│   ├── recovery/                               [INDEX — Pointer to canonical]
│   │   └── README.md                           ★ NEW — Links to canonical recovery report
│   │
│   ├── gap-analysis/                           [INDEX — Pointer to canonical]
│   │   └── README.md                           ★ NEW — Links to 5 canonical diagnostics
│   │
│   ├── domain/                                 [CANONICAL — Domain knowledge]
│   │   ├── README.md                           ★ NEW — Domain index
│   │   └── BusinessRules.md
│   │
│   ├── adr/                                    [FUTURE — Decision records]
│   │   ├── README.md                           ★ NEW — ADR process
│   │   └── history/
│   │       └── README.md                       ★ NEW — ADR index placeholder
│   │
│   ├── roadmap/                                [FUTURE — Modernization roadmap]
│   │   └── README.md                           ★ NEW — Placeholder
│   │
│   ├── references/                             [FUTURE — External references]
│   │   └── README.md                           ★ NEW — Placeholder
│   │
│   ├── ai-dos/                                 [CANONICAL — Project memory]
│   │   ├── memory/
│   │   │   ├── README.md                       [UPDATED — New paths]
│   │   │   ├── CompletedFeatures.md
│   │   │   ├── Decisions.md
│   │   │   ├── FinanceAct.md
│   │   │   ├── FutureIdeas.md
│   │   │   ├── InterviewLogic.md
│   │   │   ├── KnownIssues.md
│   │   │   └── TaxRules.md
│   │   │
│   │   └── archive/
│   │       ├── README.md                       ★ NEW — Archive explanation
│   │       ├── Architecture-v0.1.md            (superseded)
│   │       └── TechnicalDebt-v0.1.md           (superseded)
│   │
│   ├── ARCHITECTURE.md                         [HISTORICAL — Original spec]
│   ├── DATA_MODEL.md
│   ├── ITR_TYPES_QUESTIONS.md
│   └── MASTER_PLAN.md
│
├── apps/
│   ├── api/                                    [PRODUCTION — unchanged]
│   └── web/                                    [PRODUCTION — unchanged]
│
├── design/                                     [DESIGN — unchanged]
├── infrastructure/                             [EMPTY — future]
├── packages/                                   [EMPTY — future]
├── scripts/                                    [EMPTY — future]
├── services/                                   [EMPTY — future]
├── tools/                                      [EMPTY — future]
└── .github/                                    [CI/CD — unchanged]
```

---

## 2. Canonical Document Map

### Enterprise Architecture

| Document | Canonical Location | Also Reachable Via |
|----------|-------------------|--------------------|
| Enterprise Capability Model (4 parts) | `docs/architecture/ENTERPRISE_CAPABILITY_MODEL*.md` | `docs/architecture/README.md` |
| Architecture Recovery Report | `docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md` | `docs/recovery/README.md` |
| Enterprise Gap Report | `docs/architecture/EnterpriseGapReport.md` | `docs/gap-analysis/README.md` |
| Architecture Health Score | `docs/architecture/ArchitectureHealthScore.md` | `docs/gap-analysis/README.md` |
| Domain Maturity Matrix | `docs/architecture/DomainMaturityMatrix.md` | `docs/gap-analysis/README.md` |
| Technical Debt Heatmap | `docs/architecture/TechnicalDebtHeatmap.md` | `docs/gap-analysis/README.md` |
| Enterprise Risk Matrix | `docs/architecture/EnterpriseRiskMatrix.md` | `docs/gap-analysis/README.md` |

### Governance

| Document | Canonical Location |
|----------|-------------------|
| Constitution | `docs/governance/00-Constitution.md` |
| Chief Architect | `docs/governance/01-Chief-Architect.md` |
| Engineering Standards | `docs/governance/03-Engineering-Standards.md` |

### Project Memory

| Document | Canonical Location |
|----------|-------------------|
| Memory Index | `docs/ai-dos/memory/README.md` |
| All 7 active memory files | `docs/ai-dos/memory/*.md` |
| 2 archived files | `docs/ai-dos/archive/*.md` |

### Domain Knowledge

| Document | Canonical Location |
|----------|-------------------|
| Business Rules | `docs/domain/BusinessRules.md` |

### Reference

| Document | Location |
|----------|----------|
| Original Architecture Spec | `docs/ARCHITECTURE.md` |
| Data Model | `docs/DATA_MODEL.md` |
| ITR Question Trees | `docs/ITR_TYPES_QUESTIONS.md` |
| Master Build Plan | `docs/MASTER_PLAN.md` |

---

## 3. Navigation Map

```
CLAUDE.md  ─────────────────────────────────────────────┐
  │                                                      │
  ├──→ docs/governance/00-Constitution.md                │
  ├──→ docs/ai-dos/memory/README.md                     │
  ├──→ docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md  │
  └──→ docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md │
                                                         │
README.md  ──────────────────────────────────────────────┤
  │                                                      │
  ├──→ docs/architecture/README.md                       │
  ├──→ docs/governance/README.md                         │
  └──→ docs/ai-dos/memory/                               │
                                                         │
docs/architecture/README.md  ────────────────────────────┤
  │                                                      │
  ├──→ All 14 architecture documents (1 step)            │
  └──→ docs/recovery/README.md (1 step)                  │
  └──→ docs/gap-analysis/README.md (1 step)              │
                                                         │
docs/recovery/README.md  ────────────────────────────────┤
  │                                                      │
  └──→ docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md │
                                                         │
docs/gap-analysis/README.md  ────────────────────────────┤
  │                                                      │
  └──→ docs/architecture/EnterpriseGapReport.md          │
  └──→ docs/architecture/ArchitectureHealthScore.md      │
  └──→ docs/architecture/DomainMaturityMatrix.md         │
  └──→ docs/architecture/TechnicalDebtHeatmap.md         │
  └──→ docs/architecture/EnterpriseRiskMatrix.md         │
```

**Reachability:** Every architecture document is reachable in ≤3 steps from any entry point.

---

## 4. Files Deleted (6)

| # | File | Canonical Replacement |
|---|------|----------------------|
| 1 | `docs/recovery/ARCHITECTURE_RECOVERY_REPORT.md` | `docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md` |
| 2 | `docs/gap-analysis/EnterpriseGapReport.md` | `docs/architecture/EnterpriseGapReport.md` |
| 3 | `docs/gap-analysis/ArchitectureHealthScore.md` | `docs/architecture/ArchitectureHealthScore.md` |
| 4 | `docs/gap-analysis/DomainMaturityMatrix.md` | `docs/architecture/DomainMaturityMatrix.md` |
| 5 | `docs/gap-analysis/TechnicalDebtHeatmap.md` | `docs/architecture/TechnicalDebtHeatmap.md` |
| 6 | `docs/gap-analysis/EnterpriseRiskMatrix.md` | `docs/architecture/EnterpriseRiskMatrix.md` |

## 5. Files Created (10)

| # | File | Type |
|---|------|------|
| 1 | `docs/governance/README.md` | Index |
| 2 | `docs/architecture/README.md` | Index |
| 3 | `docs/recovery/README.md` | Pointer |
| 4 | `docs/gap-analysis/README.md` | Pointer |
| 5 | `docs/domain/README.md` | Index |
| 6 | `docs/adr/README.md` | Index |
| 7 | `docs/adr/history/README.md` | Placeholder |
| 8 | `docs/roadmap/README.md` | Placeholder |
| 9 | `docs/references/README.md` | Placeholder |
| 10 | `docs/ai-dos/archive/README.md` | Index |

## 6. Files Updated (Cross-References) (3)

| # | File | Changes |
|---|------|---------|
| 1 | `CLAUDE.md` | 9 paths updated: `docs/recovery/` → `docs/architecture/`, `docs/gap-analysis/` → `docs/architecture/`; added architecture index and chronological navigation links |
| 2 | `README.md` | Governance section paths updated; added gap analysis and health score links |
| 3 | `docs/ai-dos/memory/README.md` | Paths updated during consolidation (previous step) |

## 7. Confirmation

- [x] **Every authoritative document exists in exactly one canonical location** — 0 duplicates remain
- [x] **`docs/architecture/` is the canonical location** for ECM, Recovery Report, Gap Report, Health Score, Maturity Matrix, Debt Heatmap, Risk Matrix
- [x] **`docs/recovery/` and `docs/gap-analysis/` are navigation directories** — contain only README.md with links to canonical documents
- [x] **6 duplicate files deleted** — all had identical canonical counterparts
- [x] **0 unique content files deleted**
- [x] **All internal references updated** — CLAUDE.md, README.md, memory README
- [x] **Every architecture document reachable in ≤3 navigation steps**
- [x] **Enterprise Capability Model unchanged** — FROZEN
- [x] **Architecture Recovery Report unchanged** — preserved at canonical location
- [x] **Project Memory intact** — all 8 active files preserved
- [x] **Source code untouched** — `apps/` unchanged
- [x] **Design documents untouched** — `design/` unchanged

## 8. Ready for Git Staging

The repository is internally consistent, free of duplicates, and ready for:
```
git add .
git commit -m "chore(repository): consolidate documentation, establish canonical layout"
git push origin main
```

---

*End of Documentation Topology Report v1.0*
