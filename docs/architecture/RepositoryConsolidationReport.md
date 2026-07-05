# Repository Consolidation Report

> **Status:** DISCOVERY — No files moved
> **Date:** 2026-07-05
> **Author:** Enterprise Chief Architect
> **Phase:** Pre-consolidation inventory and classification

---

## Executive Summary

Two repository roots exist:

| Repository | Path | Role | Files (meaningful) |
|-----------|------|------|--------------------|
| **A: AI-DOS** | `D:\AI_DOS` | AI Development Operating System — governance, standards, project memory | 14 markdown files |
| **B: IT_Returns** | `D:\IT_Returns` | Production tax platform — source code, architecture docs, design specs | ~130 files |

**Consolidation Strategy:** Merge Repository A into Repository B. IT_Returns becomes the single enterprise repository. AI-DOS content moves into `docs/ai-dos/` within IT_Returns. No data loss. All governance authority preserved.

---

## 1. Repository A Inventory: D:\AI_DOS

### 1.1 Complete File Inventory

```
D:\AI_DOS\
│
├── ai-dos/
│   ├── 00-Constitution.md               (Governance — SUPREME authority)
│   ├── 01-Chief-Architect.md            (Governance — ADR process, module boundaries)
│   ├── 03-Engineering-Standards.md      (Governance — coding, security, patterns)
│   │
│   └── memory/
│       ├── README.md                     (Memory index + Architect session protocol)
│       ├── Architecture.md               (Current architecture state, module map, tech stack)
│       ├── BusinessRules.md              (All tax business rules, regimes, deductions)
│       ├── CompletedFeatures.md          (Feature registry, milestones, release history)
│       ├── Decisions.md                  (Chronological decision log — 11 decisions)
│       ├── FinanceAct.md                 (Finance Act registry FY2020-26, implementation tracker)
│       ├── FutureIdeas.md                (Idea backlog, horizon planning)
│       ├── InterviewLogic.md             (Adaptive interview engine design, state machine)
│       ├── KnownIssues.md                (Bug registry — 10 issues now registered)
│       ├── TaxRules.md                   (Rule catalog, metadata standard, computation pipeline)
│       └── TechnicalDebt.md              (Debt register — 15 items now registered)
│
└── (no other files)
```

### 1.2 File Classification

| # | File | Type | Role | Authority Level | Target After Consolidation |
|---|------|------|------|-----------------|---------------------------|
| 1 | `00-Constitution.md` | Governance | Supreme governance — non-negotiable principles | Level 1-3 | `docs/ai-dos/` |
| 2 | `01-Chief-Architect.md` | Governance | Architecture governance, ADR process, module boundaries | Level 4 | `docs/ai-dos/` |
| 3 | `03-Engineering-Standards.md` | Governance | Coding standards, security standards, naming | Level 5-6 | `docs/ai-dos/` |
| 4 | `memory/README.md` | Memory Index | Architect agent session protocol | Operational | `docs/ai-dos/memory/` |
| 5 | `memory/Architecture.md` | Memory | Current architecture state (planned) | Reference | MERGE into `docs/architecture/` |
| 6 | `memory/BusinessRules.md` | Memory | Tax business rules reference | Reference | MERGE into `docs/domain/` |
| 7 | `memory/CompletedFeatures.md` | Memory | Feature & milestone tracker | Reference | `docs/ai-dos/memory/` |
| 8 | `memory/Decisions.md` | Memory | Decision log (11 decisions) | Reference | `docs/ai-dos/memory/` |
| 9 | `memory/FinanceAct.md` | Memory | Finance Act version tracker | Reference | `docs/ai-dos/memory/` |
| 10 | `memory/FutureIdeas.md` | Memory | Idea backlog | Reference | `docs/ai-dos/memory/` |
| 11 | `memory/InterviewLogic.md` | Memory | Interview engine design | Reference | `docs/ai-dos/memory/` |
| 12 | `memory/KnownIssues.md` | Memory | Bug & issue registry | Reference | `docs/ai-dos/memory/` |
| 13 | `memory/TaxRules.md` | Memory | Tax rule catalog | Reference | `docs/ai-dos/memory/` |
| 14 | `memory/TechnicalDebt.md` | Memory | Debt register | Reference | MERGE with `docs/architecture/TechnicalDebtHeatmap.md` |

### 1.3 Gaps in AI-DOS (Missing Governance Documents)

The following planned AI-DOS documents were never created (from original 20-file plan):

| # | Planned Document | Status | Priority for Completion |
|---|-----------------|--------|------------------------|
| 1 | `02-Development-Lifecycle.md` | NOT CREATED | High — needed for CI/CD and git workflow |
| 2 | `04-Testing-Standards.md` | NOT CREATED | Critical — zero tests exist; standards needed before test initiative |
| 3 | `05-Review-Standards.md` | NOT CREATED | High — needed for PR review process |
| 4 | `06-Documentation-Standards.md` | NOT CREATED | Medium |
| 5 | `07-Project-Memory.md` | REPLACED BY `memory/` directory | Complete |
| 6 | `08-Agent-System.md` | NOT CREATED | High — needed for AI agent governance |
| 7 | `09-Skills-System.md` | NOT CREATED | Medium |
| 8 | `10-Templates.md` | NOT CREATED | Medium |
| 9 | `11-Roadmap.md` | NOT CREATED | Critical — needed for modernization planning |
| 10 | `12-Enterprise-Architecture.md` | REPLACED BY ECM | Complete (in IT_Returns) |
| 11 | `13-Quality-Gates.md` | NOT CREATED | High |
| 12 | `14-Continuous-Improvement.md` | NOT CREATED | Medium |

---

## 2. Repository B Inventory: D:\IT_Returns

### 2.1 Directory Structure

```
D:\IT_Returns\
│
├── README.md                             (Project overview)
├── HANDOFF.md                            (Development handoff log — 60KB session history)
├── render.yaml                           (Render deployment config)
├── .gitignore
├── Signup-login--Prasoon.txt             (Auth design notes)
│
├── apps/
│   ├── api/                              (FastAPI backend — PRODUCTION)
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   ├── data/taxstox.db               (SQLite — pre-Neon migration artifact?)
│   │   ├── src/
│   │   │   ├── main.py                   (FastAPI entry point)
│   │   │   ├── api/                      (6 route files)
│   │   │   ├── auth/                     (JWT auth)
│   │   │   ├── builders/                 (ITR-1 + ITR-2 JSON builders, validator)
│   │   │   ├── db/                       (PostgreSQL via psycopg2)
│   │   │   ├── engine/                   (9 computation engines)
│   │   │   ├── models/                   (5 Pydantic model files)
│   │   │   ├── parsers/                  (Form 16, AIS, broker statements)
│   │   │   ├── providers/                (4 govt source providers)
│   │   │   ├── scheduler/                (APScheduler)
│   │   │   ├── summarizer/               (DeepSeek AI summarizer)
│   │   │   └── utils/                    (Password resolver, session manager)
│   │   └── tests/
│   │       └── test_e2e_real_data.py     (ONLY test file)
│   │
│   └── web/                              (Next.js frontend — PRODUCTION)
│       ├── package.json
│       ├── next.config.ts
│       ├── vercel.json
│       ├── src/
│       │   ├── app/                      (8 pages)
│       │   ├── components/               (UI components)
│       │   └── lib/                      (API client, auth, store, tax-data)
│       └── public/
│
├── docs/
│   ├── ARCHITECTURE.md                   (Original architecture spec — pre-ECM)
│   ├── DATA_MODEL.md                     (Data model definitions)
│   ├── ITR_TYPES_QUESTIONS.md            (Per-ITR question trees)
│   ├── MASTER_PLAN.md                    (Complete build spec — 2385 lines)
│   │
│   └── architecture/                     (Enterprise Architecture artifacts)
│       ├── ARCHITECTURE_RECOVERY_REPORT.md    (Current state documentation)
│       ├── ENTERPRISE_CAPABILITY_MODEL.md     (FROZEN target — Part 1 of 4)
│       ├── ENTERPRISE_CAPABILITY_MODEL_PART2.md
│       ├── ENTERPRISE_CAPABILITY_MODEL_PART3.md
│       ├── ENTERPRISE_CAPABILITY_MODEL_PART4.md
│       ├── EnterpriseGapReport.md              (Capability-by-capability gap analysis)
│       ├── ArchitectureHealthScore.md          (31/100 overall)
│       ├── DomainMaturityMatrix.md             (15 bounded contexts, 14% coverage)
│       ├── TechnicalDebtHeatmap.md             (64 items across 9 categories)
│       └── EnterpriseRiskMatrix.md             (15 risks)
│
├── design/                               (Design specifications & prototypes)
│   ├── 00-README.md
│   ├── 01-product-requirements.md
│   ├── 02-non-functional-requirements.md
│   ├── 04-information-architecture.md
│   ├── 05-backend-architecture.md
│   ├── 06-frontend-architecture.md
│   ├── 07-database-design.md
│   ├── 09-multi-agent-architecture.md
│   ├── 10-ocr-document-pipeline.md
│   ├── 12-validation-engine.md
│   ├── 13-conversation-engine.md
│   ├── 15-prompt-engineering.md
│   ├── 16-tax-optimization-engine.md
│   ├── 19-json-schemas-api-contracts.md
│   ├── DESIGN.md                         (Design tokens)
│   ├── tax-engine-enhancement.md
│   │
│   ├── auth-signup/code.html
│   ├── design-system/DESIGN.md
│   ├── error-edge-cases/code.html
│   ├── landing-page/code.html + screen.png
│   ├── post-export-instructions/code.html
│   ├── secure-upload-portal/code.html + screen.png
│   ├── smart-questionnaire/code.html + screen.png
│   ├── tax-summary-review/code.html + screen.png
│   └── user-dashboard/code.html
│
└── .claude/
    └── settings.local.json
```

---

## 3. Overlap Analysis

### 3.1 Direct Overlaps (Redundancy)

| AI-DOS File | IT_Returns Equivalent | Overlap | Resolution |
|-------------|----------------------|---------|------------|
| `memory/Architecture.md` | `docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md` + `ENTERPRISE_CAPABILITY_MODEL.md` | HIGH — AI-DOS version is pre-recovery planning; IT_Returns version is actual + target | **Discard AI-DOS version.** IT_Returns versions are evidence-backed and authoritative. |
| `memory/BusinessRules.md` | `docs/DATA_MODEL.md` + `docs/ARCHITECTURE.md` | MEDIUM — AI-DOS has structured rule reference; IT_Returns has implementation-embedded rules | **Merge.** AI-DOS business rules supplement IT_Returns domain docs. |
| `memory/TechnicalDebt.md` | `docs/architecture/TechnicalDebtHeatmap.md` | HIGH — AI-DOS tracks 15 items (conceptual); IT_Returns tracks 64 items (evidence-backed) | **Discard AI-DOS version.** IT_Returns heatmap is comprehensive and evidence-backed. |
| `memory/FinanceAct.md` | (No equivalent in IT_Returns) | NONE — IT_Returns lacks FY version tracking | **Keep AI-DOS version.** Critical gap in IT_Returns. |
| `memory/TaxRules.md` | (No equivalent in IT_Returns) | NONE — IT_Returns lacks rule catalog | **Keep AI-DOS version.** Critical gap in IT_Returns. |
| `memory/InterviewLogic.md` | `design/13-conversation-engine.md` + `docs/ITR_TYPES_QUESTIONS.md` | MEDIUM — AI-DOS is conceptual architecture; IT_Returns is implementation-adjacent design | **Merge.** AI-DOS architecture supplements IT_Returns design docs. |

### 3.2 Unique AI-DOS Assets (No IT_Returns Equivalent)

| AI-DOS File | Value | Consolidation Priority |
|-------------|-------|----------------------|
| `00-Constitution.md` | Supreme governance — no equivalent exists | **Critical** — must be preserved with Level 1 authority |
| `01-Chief-Architect.md` | ADR process, module boundaries — no equivalent | **Critical** — ADR process not established in IT_Returns |
| `03-Engineering-Standards.md` | Coding standards — no equivalent | **Critical** — needed before code expansion |
| `memory/Decisions.md` | Decision log (11 decisions) — no equivalent | **High** — IT_Returns has no decision tracking |
| `memory/CompletedFeatures.md` | Feature/milestone tracker — no equivalent | **High** |
| `memory/FutureIdeas.md` | Idea backlog — no equivalent | **Medium** |
| `memory/KnownIssues.md` | Bug registry (10 items) — no equivalent | **High** |
| `memory/README.md` | Architect session protocol | **High** — operational asset |

### 3.3 Unique IT_Returns Assets (No AI-DOS Equivalent)

| IT_Returns Asset | Value | AI-DOS Gap |
|-----------------|-------|------------|
| `docs/architecture/ENTERPRISE_CAPABILITY_MODEL*.md` (4 parts) | FROZEN target architecture — 148 capabilities, 15 bounded contexts | AI-DOS has no target architecture definition |
| `docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md` | Evidence-backed current state | AI-DOS has only planned architecture |
| `docs/architecture/EnterpriseGapReport.md` | 148-capability gap analysis | AI-DOS has no gap analysis |
| `docs/architecture/ArchitectureHealthScore.md` | 31/100 with 16 categories | AI-DOS has no health scoring |
| `docs/architecture/DomainMaturityMatrix.md` | 15 bounded contexts, 14% coverage | AI-DOS has no maturity tracking |
| `docs/architecture/EnterpriseRiskMatrix.md` | 15 risks, 4 Critical | AI-DOS has no risk matrix |
| `apps/api/` (42 Python modules) | Production backend | AI-DOS has no code |
| `apps/web/` (Next.js frontend) | Production frontend | AI-DOS has no code |
| `design/` (15+ specs + 7 HTML prototypes) | Design documentation | AI-DOS has no design docs |
| `docs/MASTER_PLAN.md` | Complete build spec | AI-DOS has no build spec |
| `HANDOFF.md` | Session-by-session development history | AI-DOS has no operational history |

---

## 4. Target Consolidated Repository Structure

### 4.1 Proposed Layout

```
D:\IT_Returns\                              (Consolidated Enterprise Repository)
│
├── README.md                               (Updated: references AI-DOS governance)
├── HANDOFF.md                              (Preserved)
├── CLAUDE.md                               (NEW: agent bootstrap — points to ai-dos/)
│
├── apps/                                   (Production applications — UNCHANGED)
│   ├── api/                                (FastAPI backend)
│   └── web/                                (Next.js frontend)
│
├── docs/                                   (Enterprise documentation)
│   │
│   ├── ai-dos/                             (AI Development Operating System)
│   │   ├── 00-Constitution.md              ← FROM AI-DOS (SUPREME)
│   │   ├── 01-Chief-Architect.md           ← FROM AI-DOS
│   │   ├── 03-Engineering-Standards.md     ← FROM AI-DOS
│   │   ├── 02-Development-Lifecycle.md     ← TO BE CREATED
│   │   ├── 04-Testing-Standards.md         ← TO BE CREATED
│   │   ├── 05-Review-Standards.md          ← TO BE CREATED
│   │   ├── 08-Agent-System.md              ← TO BE CREATED
│   │   ├── 11-Roadmap.md                   ← TO BE CREATED (Modernization Roadmap)
│   │   ├── 13-Quality-Gates.md             ← TO BE CREATED
│   │   │
│   │   └── memory/                         (Project Memory — living documents)
│   │       ├── README.md                   ← FROM AI-DOS
│   │       ├── FinanceAct.md               ← FROM AI-DOS (unique asset)
│   │       ├── TaxRules.md                 ← FROM AI-DOS (unique asset)
│   │       ├── Decisions.md                ← FROM AI-DOS
│   │       ├── CompletedFeatures.md        ← FROM AI-DOS
│   │       ├── FutureIdeas.md              ← FROM AI-DOS
│   │       ├── KnownIssues.md              ← FROM AI-DOS (updated)
│   │       ├── InterviewLogic.md           ← FROM AI-DOS
│   │       └── BusinessRules.md            ← FROM AI-DOS (merged)
│   │
│   ├── architecture/                       (Enterprise Architecture — UNCHANGED)
│   │   ├── ENTERPRISE_CAPABILITY_MODEL*.md (FROZEN)
│   │   ├── ARCHITECTURE_RECOVERY_REPORT.md
│   │   ├── EnterpriseGapReport.md
│   │   ├── ArchitectureHealthScore.md
│   │   ├── DomainMaturityMatrix.md
│   │   ├── TechnicalDebtHeatmap.md         (canonical debt register)
│   │   └── EnterpriseRiskMatrix.md
│   │
│   ├── domain/                             (NEW: Domain knowledge)
│   │   └── BusinessRules.md                ← MERGED from AI-DOS + IT_Returns
│   │
│   ├── ARCHITECTURE.md                     (Original — keep as historical reference)
│   ├── DATA_MODEL.md
│   ├── ITR_TYPES_QUESTIONS.md
│   └── MASTER_PLAN.md
│
├── design/                                 (Design specs — UNCHANGED)
│   └── ...
│
└── .claude/                                (Claude Code config — UNCHANGED)
    └── settings.local.json
```

### 4.2 Files to DISCARD (Redundant)

| File | Reason for Discard |
|------|--------------------|
| `d:\AI_DOS\ai-dos\memory\Architecture.md` | Superseded by `ARCHITECTURE_RECOVERY_REPORT.md` + ECM |
| `d:\AI_DOS\ai-dos\memory\TechnicalDebt.md` | Superseded by `TechnicalDebtHeatmap.md` (64 evidence-backed items vs 15 conceptual) |

### 4.3 Files to MERGE

| AI-DOS File | Merge Into IT_Returns File | Merge Strategy |
|-------------|---------------------------|----------------|
| `memory/BusinessRules.md` | New `docs/domain/BusinessRules.md` | Combine AI-DOS rule reference with IT_Returns domain knowledge |
| `memory/InterviewLogic.md` | `design/13-conversation-engine.md` | AI-DOS provides architectural framework; IT_Returns provides implementation detail |

---

## 5. Consolidation Actions (For Future Phase)

### 5.1 Phase 1: Move AI-DOS Governance

| Action | From | To | Notes |
|--------|------|----|-------|
| MOVE | `D:\AI_DOS\ai-dos\00-Constitution.md` | `D:\IT_Returns\docs\ai-dos\00-Constitution.md` | Preserve as SUPREME authority |
| MOVE | `D:\AI_DOS\ai-dos\01-Chief-Architect.md` | `D:\IT_Returns\docs\ai-dos\01-Chief-Architect.md` | Level 4 authority |
| MOVE | `D:\AI_DOS\ai-dos\03-Engineering-Standards.md` | `D:\IT_Returns\docs\ai-dos\03-Engineering-Standards.md` | Level 5-6 authority |

### 5.2 Phase 2: Move AI-DOS Memory

| Action | From | To | Notes |
|--------|------|----|-------|
| MOVE | `D:\AI_DOS\ai-dos\memory\README.md` | `D:\IT_Returns\docs\ai-dos\memory\README.md` | Architect protocol |
| MOVE | `D:\AI_DOS\ai-dos\memory\FinanceAct.md` | `D:\IT_Returns\docs\ai-dos\memory\FinanceAct.md` | Unique asset |
| MOVE | `D:\AI_DOS\ai-dos\memory\TaxRules.md` | `D:\IT_Returns\docs\ai-dos\memory\TaxRules.md` | Unique asset |
| MOVE | `D:\AI_DOS\ai-dos\memory\Decisions.md` | `D:\IT_Returns\docs\ai-dos\memory\Decisions.md` | Updated with ECM decisions |
| MOVE | `D:\AI_DOS\ai-dos\memory\CompletedFeatures.md` | `D:\IT_Returns\docs\ai-dos\memory\CompletedFeatures.md` | |
| MOVE | `D:\AI_DOS\ai-dos\memory\FutureIdeas.md` | `D:\IT_Returns\docs\ai-dos\memory\FutureIdeas.md` | |
| MOVE | `D:\AI_DOS\ai-dos\memory\KnownIssues.md` | `D:\IT_Returns\docs\ai-dos\memory\KnownIssues.md` | Updated with gap findings |
| MOVE | `D:\AI_DOS\ai-dos\memory\InterviewLogic.md` | `D:\IT_Returns\docs\ai-dos\memory\InterviewLogic.md` | |
| MERGE | `D:\AI_DOS\ai-dos\memory\BusinessRules.md` | `D:\IT_Returns\docs\domain\BusinessRules.md` | Combined domain knowledge |

### 5.3 Phase 3: Create Missing Governance Documents

| Action | File | Priority |
|--------|------|----------|
| CREATE | `docs/ai-dos/04-Testing-Standards.md` | Critical |
| CREATE | `docs/ai-dos/11-Roadmap.md` (Modernization Roadmap) | Critical |
| CREATE | `docs/ai-dos/02-Development-Lifecycle.md` | High |
| CREATE | `docs/ai-dos/05-Review-Standards.md` | High |
| CREATE | `docs/ai-dos/08-Agent-System.md` | High |
| CREATE | `docs/ai-dos/13-Quality-Gates.md` | High |
| CREATE | `docs/ai-dos/06-Documentation-Standards.md` | Medium |
| CREATE | `docs/ai-dos/09-Skills-System.md` | Medium |
| CREATE | `docs/ai-dos/10-Templates.md` | Medium |
| CREATE | `docs/ai-dos/14-Continuous-Improvement.md` | Medium |

### 5.4 Phase 4: Create Root CLAUDE.md

| Action | File | Purpose |
|--------|------|---------|
| CREATE | `D:\IT_Returns\CLAUDE.md` | Agent bootstrap: points to `docs/ai-dos/00-Constitution.md` as first read |

### 5.5 Phase 5: Discard Redundant Files

| Action | File | Reason |
|--------|------|--------|
| ARCHIVE | `D:\AI_DOS\ai-dos\memory\Architecture.md` | Superseded |
| ARCHIVE | `D:\AI_DOS\ai-dos\memory\TechnicalDebt.md` | Superseded by heatmap |

### 5.6 Phase 6: Decommission Repository A

| Action | Notes |
|--------|-------|
| Git commit all moves in IT_Returns | "consolidation: merge AI-DOS governance and memory into docs/ai-dos/" |
| Archive D:\AI_DOS | Add README pointing to D:\IT_Returns\docs\ai-dos\ |
| Optional: make AI-DOS a git submodule | If independent versioning of governance is desired |

---

## 6. Authority Preservation

Critical requirement: The AI-DOS Constitution (`00-Constitution.md`) is the SUPREME governance document (Decision Hierarchy Level 1-3). This authority must be preserved in the consolidated repository.

### 6.1 Authority Chain After Consolidation

```
docs/ai-dos/00-Constitution.md          ← SUPREME (Level 1-3)
    │
    ├── docs/ai-dos/01-Chief-Architect.md   ← Level 4
    ├── docs/ai-dos/03-Engineering-Standards.md ← Level 5-6
    │
    └── docs/architecture/
        ├── ENTERPRISE_CAPABILITY_MODEL.md   ← FROZEN (Level 4 reference)
        ├── ARCHITECTURE_RECOVERY_REPORT.md  ← Current state (Level 5 reference)
        └── EnterpriseGapReport.md           ← Diagnostics (Level 5 reference)
```

### 6.2 No Authority Loss

| Document | Current Authority | Post-Consolidation Authority | Change |
|----------|------------------|------------------------------|--------|
| 00-Constitution.md | Supreme | Supreme | None |
| 01-Chief-Architect.md | Level 4 | Level 4 | None |
| 03-Engineering-Standards.md | Level 5-6 | Level 5-6 | None |
| ECM (4 parts) | FROZEN target | FROZEN target | None |
| Architecture Recovery Report | Current state ref | Current state ref | None |

---

## 7. Pre-Consolidation Validation Checklist

Before any files are moved:

- [ ] All files in both repositories are committed to git
- [ ] No uncommitted changes in either repository
- [ ] Git history is preserved (use `git mv` for moves within IT_Returns)
- [ ] Cross-reference links updated in all moved files
- [ ] README.md in IT_Returns updated to reference `docs/ai-dos/`
- [ ] CLAUDE.md created at root for agent bootstrap
- [ ] All relative links verified after consolidation
- [ ] AI-DOS archived with pointer README
- [ ] CI/CD unaffected (no path changes to `apps/`)

---

## 8. Post-Consolidation State

### 8.1 Single Repository

```
D:\IT_Returns\    ← SINGLE ENTERPRISE REPOSITORY
│
├── Governed by: docs/ai-dos/00-Constitution.md
├── Architecture target: docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md (FROZEN)
├── Architecture current: docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md
├── Project memory: docs/ai-dos/memory/ (11 files, living)
├── Production code: apps/api/ + apps/web/
├── Design specs: design/
└── Agent bootstrap: CLAUDE.md
```

### 8.2 Agent Bootstrap Flow

```
Agent starts session
    ↓
1. Read CLAUDE.md → points to docs/ai-dos/00-Constitution.md
    ↓
2. Read 00-Constitution.md → understand principles, invariants, decision hierarchy
    ↓
3. Read docs/ai-dos/memory/README.md → Architect session protocol
    ↓
4. Read relevant memory files for task context
    ↓
5. Read docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md for target state
    ↓
6. Begin work
```

---

*End of Repository Consolidation Report v1.0*
*This is a discovery document. No files have been moved. Consolidation actions are scheduled for a future phase.*
