# Canonical Document Layout — Analysis & Decision

> **Date:** 2026-07-05
> **Status:** PROPOSAL — Awaiting approval before execution
> **Principle:** One canonical location per document. Directories retained for organizational clarity with lightweight index/pointer docs.

---

## 1. Architectural Decision: Directory Purpose Model

### 1.1 Two Kinds of Directories

| Type | Purpose | Contains | Example |
|------|---------|----------|---------|
| **Canonical Storage** | Holds the authoritative copy of documents | Full documents | `docs/architecture/`, `docs/governance/` |
| **Organizational Index** | Provides logical navigation to canonical documents | README.md pointers + indexes | `docs/recovery/`, `docs/gap-analysis/` |

### 1.2 Rationale

The enterprise documentation architecture has **two audiences** with different navigation needs:

- **Chronological navigators** — "What happened during the Architecture Recovery phase?" → Look in `docs/recovery/`
- **Topical navigators** — "Where is the current architecture state?" → Look in `docs/architecture/`

Both navigation paths should work. The solution: canonical documents live in `docs/architecture/`. Organizational directories contain lightweight `README.md` files that explain the phase and link to the canonical documents.

---

## 2. Directory-by-Directory Decision

### 2.1 `docs/architecture/` — CANONICAL STORAGE

**Decision:** KEEP as the single canonical home for all enterprise architecture artifacts.

**Rationale:** This was the working directory where all architecture documents were authored. The ECM (FROZEN) lives here. All analysis documents reference each other and the ECM. Keeping them together preserves internal consistency and simplifies cross-reference maintenance.

**Canonical documents stored here:**

| Document | Role |
|----------|------|
| `ENTERPRISE_CAPABILITY_MODEL.md` (Part 1) | FROZEN target architecture |
| `ENTERPRISE_CAPABILITY_MODEL_PART2.md` | FROZEN target (Domains 6-9) |
| `ENTERPRISE_CAPABILITY_MODEL_PART3.md` | FROZEN target (Domains 10-16) |
| `ENTERPRISE_CAPABILITY_MODEL_PART4.md` | FROZEN target (Domains 17-20 + Bounded Contexts) |
| `ARCHITECTURE_RECOVERY_REPORT.md` | Current state — evidence-backed |
| `EnterpriseGapReport.md` | 148-capability gap analysis |
| `ArchitectureHealthScore.md` | 31/100 with 16 category scores |
| `DomainMaturityMatrix.md` | 15 bounded contexts, 14% coverage |
| `TechnicalDebtHeatmap.md` | **CANONICAL DEBT REGISTER** — 64 items |
| `EnterpriseRiskMatrix.md` | 15 risks (4 Critical) |
| `RepositoryConsolidationReport.md` | Discovery report (historical) |
| `RepositoryConsolidationPlan.md` | Execution plan (historical) |
| `CONSOLIDATION_COMPLETE.md` | Final consolidation report |
| `GitAndDocAudit.md` | This audit |
| `CanonicalDocumentLayout.md` | This document |

---

### 2.2 `docs/recovery/` — ORGANIZATIONAL INDEX

**Decision:** RETAIN directory. DELETE the duplicate `ARCHITECTURE_RECOVERY_REPORT.md`. CREATE `README.md` pointer.

**Rationale:** "Architecture Recovery" is a legitimate phase in the enterprise architecture process. A new team member asking "what did we learn during recovery?" should find a clear entry point. The directory provides chronological organization.

**After cleanup:**

```
docs/recovery/
└── README.md    ← Explains the recovery phase and links to:
                   docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md
```

**README.md content specification:**
```markdown
# Architecture Recovery — Phase Output

The Architecture Recovery phase (2026-07-05) produced a comprehensive,
evidence-backed documentation of the current platform state based on a
42-module source code audit.

## Canonical Document

[ARCHITECTURE_RECOVERY_REPORT.md](../architecture/ARCHITECTURE_RECOVERY_REPORT.md)
— Complete current state documentation including module catalogue, dependency
analysis, domain model, business flows, data flows, validation flows, strengths,
weaknesses, and technical debt register.

## Related Documents

- [Enterprise Capability Model](../architecture/ENTERPRISE_CAPABILITY_MODEL.md) — Target state against which recovery was measured
- [Enterprise Gap Report](../architecture/EnterpriseGapReport.md) — Gap analysis using recovery findings
```

---

### 2.3 `docs/gap-analysis/` — ORGANIZATIONAL INDEX

**Decision:** RETAIN directory. DELETE all 5 duplicate documents. CREATE `README.md` pointer.

**Rationale:** "Gap Analysis" is a legitimate phase. The directory provides chronological navigation to all diagnostics produced during this phase.

**After cleanup:**

```
docs/gap-analysis/
└── README.md    ← Explains the gap analysis phase and links to all 5 diagnostics:
                   docs/architecture/EnterpriseGapReport.md
                   docs/architecture/ArchitectureHealthScore.md
                   docs/architecture/DomainMaturityMatrix.md
                   docs/architecture/TechnicalDebtHeatmap.md
                   docs/architecture/EnterpriseRiskMatrix.md
```

---

### 2.4 `docs/governance/` — CANONICAL STORAGE

**Decision:** KEEP as canonical home for governance documents. CREATE `README.md` index.

**Rationale:** Governance documents have a distinct authority level and audience. Separating them from architecture documents makes the authority hierarchy physically visible in the directory structure.

**After:**

```
docs/governance/
├── README.md                    ← Governance index with authority hierarchy
├── 00-Constitution.md           ← SUPREME (Level 1-3)
├── 01-Chief-Architect.md       ← Level 4
├── 03-Engineering-Standards.md  ← Level 5-6
├── 04-Testing-Standards.md      ← TO BE CREATED (P0)
├── 02-Development-Lifecycle.md  ← TO BE CREATED (P1)
└── ... (future governance docs)
```

---

### 2.5 `docs/ai-dos/memory/` — CANONICAL STORAGE

**Decision:** KEEP as canonical home for Project Memory. README already exists and has been updated.

**Status:** ✅ Complete. No changes needed.

---

### 2.6 `docs/ai-dos/archive/` — ARCHIVAL STORAGE

**Decision:** KEEP. CREATE `README.md` explaining why files are archived.

**After:**

```
docs/ai-dos/archive/
├── README.md                    ← Archive explanation
├── Architecture-v0.1.md         ← Superseded (header added)
└── TechnicalDebt-v0.1.md        ← Superseded (header added)
```

---

### 2.7 `docs/domain/` — CANONICAL STORAGE

**Decision:** KEEP. CREATE `README.md` index.

**Rationale:** Domain knowledge is distinct from architecture. As more domain documents are created, this directory grows.

---

### 2.8 `docs/adr/` — FUTURE CANONICAL STORAGE

**Decision:** KEEP. CREATE `README.md` explaining ADR process and linking to `docs/governance/01-Chief-Architect.md` for the ADR template.

**After:**

```
docs/adr/
├── README.md                    ← ADR process overview + template reference
└── history/                     ← Future ADR storage
    └── README.md                ← ADR index (to be populated)
```

---

### 2.9 `docs/roadmap/` — FUTURE CANONICAL STORAGE

**Decision:** KEEP. CREATE `README.md` placeholder.

**After:**

```
docs/roadmap/
└── README.md                    ← "Modernization Roadmap will be created here"
```

---

### 2.10 `docs/references/` — FUTURE INDEX

**Decision:** KEEP. CREATE `README.md` placeholder.

---

### 2.11 Legacy `docs/` files

| File | Location | Decision |
|------|----------|----------|
| `ARCHITECTURE.md` | `docs/ARCHITECTURE.md` | KEEP — Historical. Pre-ECM original spec (105 KB). Retain at current location. |
| `DATA_MODEL.md` | `docs/DATA_MODEL.md` | KEEP — Active reference for data model definitions. |
| `ITR_TYPES_QUESTIONS.md` | `docs/ITR_TYPES_QUESTIONS.md` | KEEP — Active reference for question decision trees. |
| `MASTER_PLAN.md` | `docs/MASTER_PLAN.md` | KEEP — Active reference for AI agents (build spec). |

These remain at `docs/` root because they predate the directory structure and are referenced by `README.md` at their current paths. Moving them would break references without adding organizational value.

---

## 3. Complete Revised Documentation Layout

```
D:\IT_Returns\
│
├── CLAUDE.md                                   [CANONICAL — Agent bootstrap]
├── README.md                                   [CANONICAL — Project overview]
├── HANDOFF.md                                  [HISTORICAL — Dev handoff log]
│
├── docs/
│   │
│   ├── governance/                             [CANONICAL STORAGE]
│   │   ├── README.md                           [CREATE — Governance index]
│   │   ├── 00-Constitution.md                  [SUPREME]
│   │   ├── 01-Chief-Architect.md               [Level 4]
│   │   └── 03-Engineering-Standards.md         [Level 5-6]
│   │
│   ├── architecture/                           [CANONICAL STORAGE — Enterprise Architecture]
│   │   ├── README.md                           [CREATE — Architecture index]
│   │   ├── ENTERPRISE_CAPABILITY_MODEL.md      [FROZEN Part 1]
│   │   ├── ENTERPRISE_CAPABILITY_MODEL_PART2.md [FROZEN Part 2]
│   │   ├── ENTERPRISE_CAPABILITY_MODEL_PART3.md [FROZEN Part 3]
│   │   ├── ENTERPRISE_CAPABILITY_MODEL_PART4.md [FROZEN Part 4]
│   │   ├── ARCHITECTURE_RECOVERY_REPORT.md     [Current state]
│   │   ├── EnterpriseGapReport.md              [Gap analysis]
│   │   ├── ArchitectureHealthScore.md          [Health scoring]
│   │   ├── DomainMaturityMatrix.md             [Maturity tracking]
│   │   ├── TechnicalDebtHeatmap.md             [CANONICAL DEBT REGISTER]
│   │   ├── EnterpriseRiskMatrix.md             [Risk register]
│   │   ├── RepositoryConsolidationReport.md    [Historical]
│   │   ├── RepositoryConsolidationPlan.md      [Historical]
│   │   ├── CONSOLIDATION_COMPLETE.md           [Historical]
│   │   ├── GitAndDocAudit.md                   [Historical]
│   │   └── CanonicalDocumentLayout.md          [THIS DOCUMENT — Active until executed]
│   │
│   ├── recovery/                               [ORGANIZATIONAL INDEX]
│   │   └── README.md                           [CREATE — Links to canonical recovery docs]
│   │
│   ├── gap-analysis/                           [ORGANIZATIONAL INDEX]
│   │   └── README.md                           [CREATE — Links to 5 canonical diagnostics]
│   │
│   ├── domain/                                 [CANONICAL STORAGE]
│   │   ├── README.md                           [CREATE — Domain knowledge index]
│   │   └── BusinessRules.md                    [Business rules reference]
│   │
│   ├── adr/                                    [FUTURE CANONICAL STORAGE]
│   │   ├── README.md                           [CREATE — ADR process + template ref]
│   │   └── history/
│   │       └── README.md                       [CREATE — ADR index placeholder]
│   │
│   ├── roadmap/                                [FUTURE CANONICAL STORAGE]
│   │   └── README.md                           [CREATE — Placeholder]
│   │
│   ├── references/                             [FUTURE INDEX]
│   │   └── README.md                           [CREATE — Placeholder]
│   │
│   ├── ai-dos/                                 [CANONICAL STORAGE]
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
│   │       ├── README.md                       [CREATE — Archive explanation]
│   │       ├── Architecture-v0.1.md
│   │       └── TechnicalDebt-v0.1.md
│   │
│   ├── ARCHITECTURE.md                         [HISTORICAL — Original spec]
│   ├── DATA_MODEL.md                           [CANONICAL — Data model]
│   ├── ITR_TYPES_QUESTIONS.md                  [CANONICAL — Question trees]
│   └── MASTER_PLAN.md                          [CANONICAL — Build spec]
│
├── apps/                                       [SOURCE CODE — unchanged]
├── design/                                     [DESIGN SPECS — unchanged]
└── ... (infrastructure/, packages/, scripts/, services/, tools/)
```

---

## 4. Execution Plan

### 4.1 Files to DELETE (7 duplicates)

| # | File | Reason |
|---|------|--------|
| 1 | `docs/recovery/ARCHITECTURE_RECOVERY_REPORT.md` | Duplicate. Replaced by pointer README. |
| 2 | `docs/gap-analysis/EnterpriseGapReport.md` | Duplicate. Replaced by pointer README. |
| 3 | `docs/gap-analysis/ArchitectureHealthScore.md` | Duplicate. Replaced by pointer README. |
| 4 | `docs/gap-analysis/DomainMaturityMatrix.md` | Duplicate. Replaced by pointer README. |
| 5 | `docs/gap-analysis/TechnicalDebtHeatmap.md` | Duplicate. Replaced by pointer README. |
| 6 | `docs/gap-analysis/EnterpriseRiskMatrix.md` | Duplicate. Replaced by pointer README. |

### 4.2 Files to CREATE (10 index/pointer READMEs)

| # | File | Type |
|---|------|------|
| 1 | `docs/governance/README.md` | Governance index with authority hierarchy |
| 2 | `docs/architecture/README.md` | Architecture index listing all artifacts |
| 3 | `docs/recovery/README.md` | Pointer to canonical recovery report |
| 4 | `docs/gap-analysis/README.md` | Pointer to 5 canonical diagnostics |
| 5 | `docs/domain/README.md` | Domain knowledge index |
| 6 | `docs/adr/README.md` | ADR process + template reference |
| 7 | `docs/adr/history/README.md` | ADR index placeholder |
| 8 | `docs/roadmap/README.md` | Placeholder |
| 9 | `docs/references/README.md` | Placeholder |
| 10 | `docs/ai-dos/archive/README.md` | Archive explanation |

### 4.3 References to UPDATE

| File | Change |
|------|--------|
| `CLAUDE.md` | Update paths to reflect canonical layout |
| `README.md` | Update governance section paths |
| `docs/ai-dos/memory/README.md` | Already updated during consolidation — verify consistency |

### 4.4 Execution Order

```
Phase A: DELETE 6 duplicate files (not the READMEs)
Phase B: CREATE 10 index/pointer READMEs
Phase C: UPDATE references in CLAUDE.md, README.md
Phase D: VERIFY all links resolve
Phase E: GIT ADD all changes
Phase F: GIT COMMIT
Phase G: GIT PUSH
```

---

*End of Canonical Document Layout v1.0*
*Awaiting approval. No deletions, commits, or pushes executed.*
