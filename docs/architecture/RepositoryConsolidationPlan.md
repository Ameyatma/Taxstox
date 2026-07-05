# Repository Consolidation Plan

> **Status:** EXECUTION PLAN — No moves performed
> **Date:** 2026-07-05
> **Author:** Enterprise Chief Architect
> **Phase:** Pre-consolidation planning
> **Inputs:** Complete file inventory (`find` + metadata), Architecture Recovery Report, Enterprise Capability Model, Enterprise Gap Report

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [File Classification Matrix](#2-file-classification-matrix)
3. [Final Enterprise Repository Structure](#3-final-enterprise-repository-structure)
4. [Duplicate & Superseded Document Report](#4-duplicate--superseded-document-report)
5. [Missing Governance Documents Report](#5-missing-governance-documents-report)
6. [Migration Risk Assessment](#6-migration-risk-assessment)
7. [Consolidation Checklist](#7-consolidation-checklist)
8. [Final Execution Plan](#8-final-execution-plan)

---

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| Files in AI-DOS | 14 (all markdown) |
| Files in IT_Returns (meaningful) | 125 |
| Files classified KEEP | 107 |
| Files classified MOVE | 11 |
| Files classified MERGE | 2 |
| Files classified ARCHIVE | 2 |
| Files classified DELETE | 0 |
| Files classified CREATE NEW | 12 |
| Duplicates identified | 2 |
| Missing governance docs | 12 |
| Migration risks | 6 |

**Net effect:** AI-DOS governance and memory move into IT_Returns as `docs/ai-dos/`. No production code touched. All authority preserved. Two redundant files archived. Twelve missing governance documents identified for creation.

---

## 2. File Classification Matrix

### 2.1 Repository A: D:\AI_DOS — Complete Classification

| # | File | Size | Last Modified | Classification | Destination | Justification |
|---|------|------|---------------|----------------|-------------|---------------|
| 1 | `ai-dos/00-Constitution.md` | 64,306 | 2026-07-05 | **MOVE** | `docs/ai-dos/00-Constitution.md` | Supreme governance — no IT_Returns equivalent. Must be in single repo as Level 1 authority. |
| 2 | `ai-dos/01-Chief-Architect.md` | 40,753 | 2026-07-05 | **MOVE** | `docs/ai-dos/01-Chief-Architect.md` | ADR process + module boundaries — no IT_Returns equivalent. Level 4 authority. |
| 3 | `ai-dos/03-Engineering-Standards.md` | 35,797 | 2026-07-05 | **MOVE** | `docs/ai-dos/03-Engineering-Standards.md` | Coding/security standards — no IT_Returns equivalent. Level 5-6 authority. |
| 4 | `ai-dos/memory/README.md` | 4,944 | 2026-07-05 | **MOVE** | `docs/ai-dos/memory/README.md` | Architect session protocol — operational asset, no IT_Returns equivalent. |
| 5 | `ai-dos/memory/Architecture.md` | 6,770 | 2026-07-05 | **ARCHIVE** | `docs/ai-dos/memory/archive/Architecture-v0.1.md` | **SUPERSEDED** by `ARCHITECTURE_RECOVERY_REPORT.md` (50,983 bytes, evidence-backed) and `ENTERPRISE_CAPABILITY_MODEL.md` (178,013 bytes total, FROZEN target). AI-DOS version was pre-recovery planning; IT_Returns versions are authoritative. Preserve for historical reference only. |
| 6 | `ai-dos/memory/BusinessRules.md` | 8,256 | 2026-07-05 | **MERGE** | `docs/domain/BusinessRules.md` | Contains structured Indian tax domain rules (regimes, deductions, income heads). IT_Returns `docs/DATA_MODEL.md` has data structures but not the comprehensive business rule reference. MERGE: AI-DOS content as primary reference, supplemented by IT_Returns implementation notes. |
| 7 | `ai-dos/memory/CompletedFeatures.md` | 5,234 | 2026-07-05 | **MOVE** | `docs/ai-dos/memory/CompletedFeatures.md` | Feature and milestone tracker — no IT_Returns equivalent. Living document. |
| 8 | `ai-dos/memory/Decisions.md` | 5,298 | 2026-07-05 | **MOVE** | `docs/ai-dos/memory/Decisions.md` | Decision log (11 decisions) — no IT_Returns equivalent. Living document. |
| 9 | `ai-dos/memory/FinanceAct.md` | 6,084 | 2026-07-05 | **MOVE** | `docs/ai-dos/memory/FinanceAct.md` | Finance Act registry FY2020-26 — no IT_Returns equivalent. Unique asset. |
| 10 | `ai-dos/memory/FutureIdeas.md` | 5,343 | 2026-07-05 | **MOVE** | `docs/ai-dos/memory/FutureIdeas.md` | Idea backlog — no IT_Returns equivalent. Living document. |
| 11 | `ai-dos/memory/InterviewLogic.md` | 14,163 | 2026-07-05 | **MOVE** | `docs/ai-dos/memory/InterviewLogic.md` | Interview engine design + state machine — IT_Returns `design/13-conversation-engine.md` (18,013 bytes) has overlapping content but different focus. Not a duplicate: AI-DOS is architecture; IT_Returns is implementation design. Both preserved. |
| 12 | `ai-dos/memory/KnownIssues.md` | 6,673 | 2026-07-05 | **MOVE** | `docs/ai-dos/memory/KnownIssues.md` | Bug registry (10 issues) — updated with gap analysis findings. No IT_Returns equivalent. |
| 13 | `ai-dos/memory/TaxRules.md` | 7,066 | 2026-07-05 | **MOVE** | `docs/ai-dos/memory/TaxRules.md` | Rule catalog + metadata standard — no IT_Returns equivalent. Unique asset. |
| 14 | `ai-dos/memory/TechnicalDebt.md` | 7,597 | 2026-07-05 | **ARCHIVE** | `docs/ai-dos/memory/archive/TechnicalDebt-v0.1.md` | **SUPERSEDED** by `TechnicalDebtHeatmap.md` (15,279 bytes, 64 evidence-backed items vs 15 conceptual items). IT_Returns heatmap is comprehensive and sourced from code audit. Preserve for historical reference. |

### 2.2 Repository B: D:\IT_Returns — Complete Classification

#### 2.2.1 Root Files

| # | File | Size | Last Modified | Classification | Notes |
|---|------|------|---------------|----------------|-------|
| 1 | `README.md` | 4,553 | 2026-07-02 | **KEEP** | Project overview — update cross-references after consolidation |
| 2 | `HANDOFF.md` | 60,649 | 2026-07-05 | **KEEP** | Session-by-session development history — operational asset |
| 3 | `render.yaml` | 1,052 | 2026-07-05 | **KEEP** | Render deployment config |
| 4 | `.gitignore` | 309 | 2026-07-01 | **KEEP** | Update to include consolidated paths |
| 5 | `Signup-login--Prasoon.txt` | 5,082 | 2026-06-29 | **KEEP** | Auth design notes — historical reference |

#### 2.2.2 Source Code: apps/api/src/ (42 Python files)

| # | File | Size | Classification | Notes |
|---|------|------|----------------|-------|
| 1-42 | All `apps/api/src/**/*.py` | Various | **KEEP** | Production backend — NO CHANGES. All source code paths unchanged. |

#### 2.2.3 Source Code: apps/api/ config files

| # | File | Size | Classification | Notes |
|---|------|------|----------------|-------|
| 43 | `apps/api/pyproject.toml` | 835 | **KEEP** | Python project config |
| 44 | `apps/api/requirements.txt` | 300 | **KEEP** | Dependencies |
| 45 | `apps/api/Dockerfile` | 640 | **KEEP** | Container config |
| 46 | `apps/api/.env.example` | 275 | **KEEP** | Environment template |
| 47 | `apps/api/data/taxstox.db` | 40,960 | **KEEP** | SQLite artifact — pre-Neon migration; preserve for reference |

#### 2.2.4 Source Code: apps/api/tests/

| # | File | Size | Classification | Notes |
|---|------|------|----------------|-------|
| 48 | `apps/api/tests/test_e2e_real_data.py` | 14,463 | **KEEP** | Only test file — preserve; tests/ structure needed |

#### 2.2.5 Frontend: apps/web/ (26 source files)

| # | File | Size | Classification | Notes |
|---|------|------|----------------|-------|
| 49-74 | All `apps/web/src/**/*.{tsx,ts,css}` + config files | Various | **KEEP** | Production frontend — NO CHANGES |

#### 2.2.6 Documentation: docs/

| # | File | Size | Last Modified | Classification | Notes |
|---|------|------|---------------|----------------|-------|
| 75 | `docs/ARCHITECTURE.md` | 104,658 | 2026-06-29 | **KEEP** | Original architecture spec — pre-ECM. Historical + implementation detail. Preserve as reference. |
| 76 | `docs/DATA_MODEL.md` | 21,305 | 2026-06-28 | **KEEP** | Data model definitions — supplements domain docs |
| 77 | `docs/ITR_TYPES_QUESTIONS.md` | 10,443 | 2026-06-28 | **KEEP** | Per-ITR question decision trees |
| 78 | `docs/MASTER_PLAN.md` | 19,650 | 2026-07-02 | **KEEP** | Complete build spec — operational reference for agents |

#### 2.2.7 Enterprise Architecture: docs/architecture/ (10 files)

| # | File | Size | Last Modified | Classification | Notes |
|---|------|------|---------------|----------------|-------|
| 79 | `ARCHITECTURE_RECOVERY_REPORT.md` | 50,983 | 2026-07-05 | **KEEP** | Current state — authoritative |
| 80 | `ENTERPRISE_CAPABILITY_MODEL.md` | 44,610 | 2026-07-05 | **KEEP** | FROZEN target Part 1 |
| 81 | `ENTERPRISE_CAPABILITY_MODEL_PART2.md` | 33,553 | 2026-07-05 | **KEEP** | FROZEN target Part 2 |
| 82 | `ENTERPRISE_CAPABILITY_MODEL_PART3.md` | 50,046 | 2026-07-05 | **KEEP** | FROZEN target Part 3 |
| 83 | `ENTERPRISE_CAPABILITY_MODEL_PART4.md` | 36,804 | 2026-07-05 | **KEEP** | FROZEN target Part 4 |
| 84 | `EnterpriseGapReport.md` | 45,278 | 2026-07-05 | **KEEP** | Gap analysis — authoritative |
| 85 | `ArchitectureHealthScore.md` | 13,016 | 2026-07-05 | **KEEP** | Health score — authoritative |
| 86 | `DomainMaturityMatrix.md` | 13,341 | 2026-07-05 | **KEEP** | Maturity tracking — authoritative |
| 87 | `TechnicalDebtHeatmap.md` | 15,279 | 2026-07-05 | **KEEP** | Canonical debt register |
| 88 | `EnterpriseRiskMatrix.md` | 18,760 | 2026-07-05 | **KEEP** | Risk register — authoritative |

#### 2.2.8 Design Documents: design/ (29 files)

| # | Files | Classification | Notes |
|---|-------|----------------|-------|
| 89-117 | All `design/**/*.{md,html,png}` | **KEEP** | Design specs + HTML prototypes — NO CHANGES |

#### 2.2.9 Infrastructure Config

| # | File | Classification | Notes |
|---|------|----------------|-------|
| 118 | `.claude/settings.local.json` | **KEEP** | Claude Code local config |

### 2.3 Files to CREATE NEW

| # | File | Purpose | Priority | Target Path |
|---|------|---------|----------|-------------|
| CREATE-01 | `CLAUDE.md` | Agent bootstrap — first file any AI agent reads | **P0 — Before any other action** | `D:\IT_Returns\CLAUDE.md` |
| CREATE-02 | `docs/ai-dos/04-Testing-Standards.md` | Testing philosophy, test pyramid, coverage requirements | **P0 — Before writing any tests** | `docs/ai-dos/04-Testing-Standards.md` |
| CREATE-03 | `docs/ai-dos/11-Roadmap.md` | Enterprise Modernization Roadmap M0-M12 | **P0 — Next architecture phase** | `docs/ai-dos/11-Roadmap.md` |
| CREATE-04 | `docs/ai-dos/02-Development-Lifecycle.md` | Git workflow, CI/CD, PR process, branches | **P1** | `docs/ai-dos/02-Development-Lifecycle.md` |
| CREATE-05 | `docs/ai-dos/05-Review-Standards.md` | Code review process, reviewer checklist | **P1** | `docs/ai-dos/05-Review-Standards.md` |
| CREATE-06 | `docs/ai-dos/08-Agent-System.md` | AI agent governance, delegation rules, communication protocol | **P1** | `docs/ai-dos/08-Agent-System.md` |
| CREATE-07 | `docs/ai-dos/13-Quality-Gates.md` | Quality gate definitions, CI enforcement, metrics | **P1** | `docs/ai-dos/13-Quality-Gates.md` |
| CREATE-08 | `docs/ai-dos/06-Documentation-Standards.md` | Doc standards, templates, review process | **P2** | `docs/ai-dos/06-Documentation-Standards.md` |
| CREATE-09 | `docs/ai-dos/09-Skills-System.md` | Skill definitions, registry, agent capabilities | **P2** | `docs/ai-dos/09-Skills-System.md` |
| CREATE-10 | `docs/ai-dos/10-Templates.md` | Document templates, code templates, ADR template | **P2** | `docs/ai-dos/10-Templates.md` |
| CREATE-11 | `docs/ai-dos/14-Continuous-Improvement.md` | Improvement process, feedback loops, retrospectives | **P2** | `docs/ai-dos/14-Continuous-Improvement.md` |
| CREATE-12 | `docs/domain/BusinessRules.md` | Merged business rules from AI-DOS + IT_Returns | **P1** | `docs/domain/BusinessRules.md` |

---

## 3. Final Enterprise Repository Structure

### 3.1 Complete Target Hierarchy

```
D:\IT_Returns\                                    [ENTERPRISE REPOSITORY ROOT]
│
├── CLAUDE.md                                     [CREATE: Agent bootstrap]
├── README.md                                     [UPDATE: Cross-references]
├── HANDOFF.md                                    [KEEP: Development history]
├── render.yaml                                   [KEEP: Render config]
├── .gitignore                                    [UPDATE: Include new paths]
│
├── docs/                                         [ENTERPRISE DOCUMENTATION]
│   │
│   ├── ai-dos/                                   [AI DEVELOPMENT OPERATING SYSTEM]
│   │   │
│   │   ├── 00-Constitution.md                    [MOVE: Supreme governance — Level 1-3]
│   │   ├── 01-Chief-Architect.md                 [MOVE: Architecture governance — Level 4]
│   │   ├── 02-Development-Lifecycle.md           [CREATE: Git workflow, CI/CD]
│   │   ├── 03-Engineering-Standards.md           [MOVE: Coding, security — Level 5-6]
│   │   ├── 04-Testing-Standards.md               [CREATE: Testing framework]
│   │   ├── 05-Review-Standards.md                [CREATE: Code review process]
│   │   ├── 06-Documentation-Standards.md         [CREATE: Doc standards]
│   │   ├── 08-Agent-System.md                    [CREATE: AI agent governance]
│   │   ├── 09-Skills-System.md                   [CREATE: Skill definitions]
│   │   ├── 10-Templates.md                       [CREATE: Templates library]
│   │   ├── 11-Roadmap.md                         [CREATE: Modernization roadmap]
│   │   ├── 13-Quality-Gates.md                   [CREATE: Quality gate definitions]
│   │   ├── 14-Continuous-Improvement.md          [CREATE: Improvement process]
│   │   │
│   │   └── memory/                               [PROJECT MEMORY — Living documents]
│   │       ├── README.md                         [MOVE: Architect session protocol]
│   │       ├── CompletedFeatures.md              [MOVE: Feature tracker]
│   │       ├── Decisions.md                      [MOVE: Decision log]
│   │       ├── FinanceAct.md                     [MOVE: FY version tracker]
│   │       ├── FutureIdeas.md                    [MOVE: Idea backlog]
│   │       ├── InterviewLogic.md                 [MOVE: Interview architecture]
│   │       ├── KnownIssues.md                    [MOVE: Bug registry]
│   │       ├── TaxRules.md                       [MOVE: Rule catalog]
│   │       │
│   │       └── archive/                          [HISTORICAL — Not active]
│   │           ├── Architecture-v0.1.md          [ARCHIVE: Pre-recovery planning]
│   │           └── TechnicalDebt-v0.1.md         [ARCHIVE: Pre-heatmap version]
│   │
│   ├── architecture/                             [ENTERPRISE ARCHITECTURE]
│   │   ├── ENTERPRISE_CAPABILITY_MODEL.md       [KEEP: FROZEN target Part 1]
│   │   ├── ENTERPRISE_CAPABILITY_MODEL_PART2.md [KEEP: FROZEN target Part 2]
│   │   ├── ENTERPRISE_CAPABILITY_MODEL_PART3.md [KEEP: FROZEN target Part 3]
│   │   ├── ENTERPRISE_CAPABILITY_MODEL_PART4.md [KEEP: FROZEN target Part 4]
│   │   ├── ARCHITECTURE_RECOVERY_REPORT.md      [KEEP: Current state]
│   │   ├── EnterpriseGapReport.md               [KEEP: Gap analysis]
│   │   ├── ArchitectureHealthScore.md           [KEEP: Health scoring]
│   │   ├── DomainMaturityMatrix.md              [KEEP: Maturity tracking]
│   │   ├── TechnicalDebtHeatmap.md              [KEEP: Canonical debt register]
│   │   ├── EnterpriseRiskMatrix.md              [KEEP: Risk register]
│   │   └── RepositoryConsolidationReport.md     [KEEP: Discovery report]
│   │
│   ├── domain/                                   [DOMAIN KNOWLEDGE]
│   │   └── BusinessRules.md                     [MERGE: Combined business rules]
│   │
│   ├── ARCHITECTURE.md                           [KEEP: Original spec — historical]
│   ├── DATA_MODEL.md                             [KEEP: Data model definitions]
│   ├── ITR_TYPES_QUESTIONS.md                    [KEEP: Question decision trees]
│   └── MASTER_PLAN.md                            [KEEP: Build spec]
│
├── design/                                       [DESIGN SPECIFICATIONS]
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
│   ├── DESIGN.md
│   ├── tax-engine-enhancement.md
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
├── apps/                                         [PRODUCTION APPLICATIONS]
│   ├── api/                                      [FastAPI Backend — UNCHANGED]
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── api/        (6 route files)
│   │   │   ├── auth/       (JWT auth)
│   │   │   ├── builders/   (ITR-1, ITR-2, validator)
│   │   │   ├── db/         (PostgreSQL)
│   │   │   ├── engine/     (9 computation engines)
│   │   │   ├── models/     (5 Pydantic models)
│   │   │   ├── parsers/    (Form 16, AIS, brokers)
│   │   │   ├── providers/  (4 govt sources)
│   │   │   ├── scheduler/  (APScheduler)
│   │   │   ├── summarizer/ (DeepSeek AI)
│   │   │   └── utils/      (password, session)
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── requirements.txt
│   │
│   └── web/                                      [Next.js Frontend — UNCHANGED]
│       └── ...
│
├── packages/                                     [FUTURE: Shared libraries]
│   └── (empty — created by modernization)
│
├── infra/                                        [FUTURE: Infrastructure as Code]
│   └── (empty — created by modernization)
│
├── scripts/                                      [FUTURE: Dev/ops scripts]
│   └── (empty — created by modernization)
│
├── tools/                                        [FUTURE: Developer tooling]
│   └── (empty — created by modernization)
│
├── .github/                                      [CI/CD WORKFLOWS]
│   └── workflows/         (existing)
│
└── .claude/                                      [CLAUDE CODE CONFIG]
    └── settings.local.json
```

### 3.2 Directory Purpose Reference

| Directory | Purpose | Contents |
|-----------|---------|----------|
| `docs/ai-dos/` | AI Development Operating System — governance framework for AI agents and humans | Constitution, standards, agent rules, missing docs (to be created) |
| `docs/ai-dos/memory/` | Project Memory — living documents updated every session by Architect Agent | Feature tracker, decision log, FY tracker, issue registry, rule catalog |
| `docs/ai-dos/memory/archive/` | Historical versions of superseded documents | Pre-recovery Architecture, pre-heatmap TechnicalDebt |
| `docs/architecture/` | Enterprise Architecture — FROZEN target + current state + gap analysis | ECM, Recovery Report, Gap Report, Health Score, Maturity Matrix, Debt Heatmap, Risk Matrix |
| `docs/domain/` | Domain Knowledge — tax business rules, concepts, terminology | Merged BusinessRules.md |
| `docs/` (root) | Legacy reference documentation | Original ARCHITECTURE.md, DATA_MODEL.md, ITR_TYPES_QUESTIONS.md, MASTER_PLAN.md |
| `design/` | Design specifications and HTML prototypes | Product requirements, NFRs, architecture designs, UI prototypes |
| `apps/` | Production applications | FastAPI backend, Next.js frontend |
| `packages/` | Shared libraries (future) | Domain models, shared utilities, API clients |
| `infra/` | Infrastructure as Code (future) | Terraform, Docker Compose, Kubernetes manifests |
| `scripts/` | Development and operations scripts (future) | Database migrations, seed data, deployment scripts |
| `tools/` | Developer tooling (future) | Linting configs, git hooks, code generation |
| `.github/` | CI/CD workflows | GitHub Actions for testing, linting, deployment |

---

## 4. Duplicate & Superseded Document Report

### 4.1 Confirmed Duplicates/Supersessions

| # | Original | Replacement | Evidence | Action | Risk if Removed |
|---|---------|-------------|----------|--------|-----------------|
| 1 | `ai-dos/memory/Architecture.md` (6,770 bytes) | `docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md` (50,983 bytes) + `docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md` (178,013 bytes total) | AI-DOS Architecture.md is pre-recovery planning document describing PLANNED architecture. IT_Returns documents describe ACTUAL architecture (evidence-backed from 42-module code audit) and TARGET architecture (148 capabilities, 15 bounded contexts). Content comparison: AI-DOS version has no evidence references; IT_Returns versions cite specific files at line level. | **ARCHIVE** — Move to `docs/ai-dos/memory/archive/Architecture-v0.1.md`. Add header: "SUPERSEDED by ARCHITECTURE_RECOVERY_REPORT.md and ENTERPRISE_CAPABILITY_MODEL.md on 2026-07-05." | None. All knowledge preserved in superior documents. Historical value retained in archive. |
| 2 | `ai-dos/memory/TechnicalDebt.md` (7,597 bytes) | `docs/architecture/TechnicalDebtHeatmap.md` (15,279 bytes) | AI-DOS version: 15 debt items (5 constitutional, 10 architectural) from pre-implementation planning. IT_Returns version: 64 items across 9 categories, all evidence-backed from source code audit with file+line references. Content comparison: 0 items in AI-DOS version not covered by IT_Returns version. IT_Returns version adds 49 items from actual code. | **ARCHIVE** — Move to `docs/ai-dos/memory/archive/TechnicalDebt-v0.1.md`. Add header: "SUPERSEDED by TechnicalDebtHeatmap.md on 2026-07-05." Update `TechnicalDebtHeatmap.md` to become the single canonical debt register. | None. Heatmap is comprehensive and evidence-backed. |

### 4.2 Assessed But NOT Duplicates

| Pair | Assessment | Rationale |
|------|-----------|-----------|
| `ai-dos/memory/InterviewLogic.md` vs `design/13-conversation-engine.md` | **NOT duplicates** | AI-DOS is architectural framework (state machine, question types, branching logic). IT_Returns is implementation-adjacent design (specific conversation flows, UX patterns). Complementary, not redundant. Both preserved. |
| `ai-dos/memory/BusinessRules.md` vs `docs/DATA_MODEL.md` | **NOT duplicates** | AI-DOS is comprehensive Indian tax business rule reference (regimes, deductions, income heads, compliance calendar). IT_Returns is data model definitions (schemas, types, structures). Different purpose. Will be MERGED into combined `docs/domain/BusinessRules.md`. |
| `ai-dos/memory/Decisions.md` vs `docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md` | **NOT duplicates** | Decisions.md is a chronological decision log (11 decisions). Recovery Report is a comprehensive architecture documentation. Decisions.md captures WHY; Recovery Report captures WHAT. Both needed. |
| `ai-dos/03-Engineering-Standards.md` vs `docs/ARCHITECTURE.md` | **NOT duplicates** | Engineering Standards is enforceable coding rules (naming, error handling, logging, types). ARCHITECTURE.md is system design (components, flows, APIs). Standards govern HOW to write; Architecture describes WHAT exists. |

---

## 5. Missing Governance Documents Report

### 5.1 Original AI-DOS Plan vs Actual

The original AI-DOS plan specified 20 documents. Current state:

| # | Planned Document | Status | Priority | Recommended Path |
|---|-----------------|--------|----------|------------------|
| 1 | `00-Constitution.md` | ✅ EXISTS (AI-DOS) | — | MOVE to `docs/ai-dos/` |
| 2 | `01-Chief-Architect.md` | ✅ EXISTS (AI-DOS) | — | MOVE to `docs/ai-dos/` |
| 3 | `02-Development-Lifecycle.md` | ❌ MISSING | **P1 — High** | CREATE at `docs/ai-dos/02-Development-Lifecycle.md`. Content: git branching strategy, PR process, CI/CD pipeline design, release process, environment management, sprint methodology. |
| 4 | `03-Engineering-Standards.md` | ✅ EXISTS (AI-DOS) | — | MOVE to `docs/ai-dos/` |
| 5 | `04-Testing-Standards.md` | ❌ MISSING | **P0 — Critical** | CREATE at `docs/ai-dos/04-Testing-Standards.md`. Required before any test initiative begins. Content: test pyramid, unit/integration/e2e standards, coverage targets, test data management, mocking strategy. |
| 6 | `05-Review-Standards.md` | ❌ MISSING | **P1 — High** | CREATE at `docs/ai-dos/05-Review-Standards.md`. Content: PR size limits, reviewer checklist, review timebox, approval requirements, AI agent review participation. |
| 7 | `06-Documentation-Standards.md` | ❌ MISSING | **P2 — Medium** | CREATE at `docs/ai-dos/06-Documentation-Standards.md`. Content: doc types, templates, mandatory sections, review process, maintenance cadence. |
| 8 | `07-Project-Memory.md` | ✅ REPLACED by `memory/` directory | — | Memory system operational. Index at `memory/README.md`. |
| 9 | `08-Agent-System.md` | ❌ MISSING | **P1 — High** | CREATE at `docs/ai-dos/08-Agent-System.md`. Content: AI agent types, delegation rules, agent communication protocol, session bootstrap, task assignment, quality gates for agent output. |
| 10 | `09-Skills-System.md` | ❌ MISSING | **P2 — Medium** | CREATE at `docs/ai-dos/09-Skills-System.md`. Content: skill definition format, skill registry, skill creation process, skill testing, skill discovery. |
| 11 | `10-Templates.md` | ❌ MISSING | **P2 — Medium** | CREATE at `docs/ai-dos/10-Templates.md`. Content: ADR template, PR template, issue template, module README template, architecture document template. |
| 12 | `11-Roadmap.md` | ❌ MISSING | **P0 — Critical** | CREATE at `docs/ai-dos/11-Roadmap.md`. Next architecture phase. Content: Enterprise Modernization Roadmap M0-M12 based on Gap Analysis findings. |
| 13 | `12-Enterprise-Architecture.md` | ✅ REPLACED by ECM | — | FROZEN ECM in `docs/architecture/` is authoritative target. |
| 14 | `13-Quality-Gates.md` | ❌ MISSING | **P1 — High** | CREATE at `docs/ai-dos/13-Quality-Gates.md`. Content: quality gate definitions per phase, CI enforcement, metric thresholds, blocking vs warning gates. |
| 15 | `14-Continuous-Improvement.md` | ❌ MISSING | **P2 — Medium** | CREATE at `docs/ai-dos/14-Continuous-Improvement.md`. Content: improvement process, feedback collection, retrospective format, metric review cadence, experiment tracking. |

### 5.2 Additional Missing Documents (Not in Original Plan)

| # | Document | Purpose | Priority | Recommended Path |
|---|---------|---------|----------|------------------|
| 16 | `docs/domain/BusinessRules.md` | Merged business rules reference | P1 | MERGE from AI-DOS `memory/BusinessRules.md` + IT_Returns domain knowledge |
| 17 | `CLAUDE.md` (root) | Agent bootstrap file | P0 — Before any other action | CREATE at repo root. Content: pointer to `docs/ai-dos/00-Constitution.md` as first read; session protocol reference. |
| 18 | `docs/ai-dos/memory/archive/README.md` | Archive index explaining why files were archived | P2 | CREATE |

---

## 6. Migration Risk Assessment

| # | Risk | Probability | Impact | Mitigation |
|---|------|------------|--------|------------|
| R1 | **Cross-reference link breakage** — Moved files (`MOVE` operations) contain relative links to other AI-DOS files that will change paths. | High | Low | Before moving, audit all internal links in AI-DOS files. Update to new paths after move. `00-Constitution.md` has Appendix A cross-reference map. `01-Chief-Architect.md` references `00-Constitution.md`. All memory files reference each other via `[[name]]` wiki links. |
| R2 | **Git history loss** — Simple `mv` outside git loses file history. | Medium | Medium | Files moving from AI-DOS to IT_Returns: use `git format-patch` + `git am` to preserve history, OR accept history reset (files were created same-day, 2026-07-05, so history is minimal). Within IT_Returns: use `git mv` for all moves to preserve history. |
| R3 | **CI/CD path dependency** — If any CI configuration references specific paths that change. | Low | Medium | Audit `.github/workflows/` for hardcoded paths. `render.yaml` references `apps/api/` — unchanged. `vercel.json` references `apps/web/` — unchanged. |
| R4 | **Agent bootstrap failure** — After consolidation, existing AI agents may not find AI-DOS content at old paths. | High | Medium | CREATE `CLAUDE.md` at root BEFORE moving files. CLAUDE.md is the bootstrap entry point that agents read first. It should have the new paths. Until CLAUDE.md exists, agents may look at old AI-DOS path. |
| R5 | **Import path breakage** — Python imports in `apps/api/` reference `src.*` paths (unchanged). | None | None | All source code paths are unchanged. Zero risk to running application. |
| R6 | **Memory update inconsistency** — AI-DOS memory files reference paths that change during consolidation. | Medium | Low | Update `memory/README.md` with new paths after consolidation. Update session log in every moved memory file. |

**Overall Risk Assessment:** LOW — Consolidation moves only markdown documentation files. No source code paths change. Git history is minimal (all files created same-day). Primary risk is link breakage in cross-references, which is mechanical to fix.

---

## 7. Consolidation Checklist

### 7.1 Pre-Consolidation

- [ ] **C01:** Verify both repositories have no uncommitted changes (`git status` clean in both)
- [ ] **C02:** Verify all AI-DOS files are committed (`git log --oneline` in D:\AI_DOS)
- [ ] **C03:** Verify all IT_Returns files are committed
- [ ] **C04:** Create backup branches in both repos (`git branch backup/pre-consolidation-2026-07-05`)
- [ ] **C05:** Audit all cross-reference links in AI-DOS files (Constitution Appendix A, Chief Architect appendices, memory README)
- [ ] **C06:** Produce complete list of links that will break and their new targets
- [ ] **C07:** Verify IT_Returns `apps/api/` runs successfully (`pytest` or manual smoke test)

### 7.2 Phase 1: Create Root Bootstrap

- [ ] **C08:** CREATE `D:\IT_Returns\CLAUDE.md` with agent bootstrap content
- [ ] **C09:** Verify CLAUDE.md correctly points to `docs/ai-dos/00-Constitution.md`

### 7.3 Phase 2: Create Target Directories

- [ ] **C10:** CREATE `docs/ai-dos/` directory
- [ ] **C11:** CREATE `docs/ai-dos/memory/` directory
- [ ] **C12:** CREATE `docs/ai-dos/memory/archive/` directory
- [ ] **C13:** CREATE `docs/domain/` directory
- [ ] **C14:** CREATE `packages/` directory (empty, for future)
- [ ] **C15:** CREATE `infra/` directory (empty, for future)
- [ ] **C16:** CREATE `scripts/` directory (empty, for future)
- [ ] **C17:** CREATE `tools/` directory (empty, for future)

### 7.4 Phase 3: Move Governance Documents

- [ ] **C18:** MOVE `D:\AI_DOS\ai-dos\00-Constitution.md` → `docs/ai-dos/00-Constitution.md`
- [ ] **C19:** MOVE `D:\AI_DOS\ai-dos\01-Chief-Architect.md` → `docs/ai-dos/01-Chief-Architect.md`
- [ ] **C20:** MOVE `D:\AI_DOS\ai-dos\03-Engineering-Standards.md` → `docs/ai-dos/03-Engineering-Standards.md`

### 7.5 Phase 4: Move Active Memory Files

- [ ] **C21:** MOVE `D:\AI_DOS\ai-dos\memory\README.md` → `docs/ai-dos/memory/README.md`
- [ ] **C22:** MOVE `D:\AI_DOS\ai-dos\memory\FinanceAct.md` → `docs/ai-dos/memory/FinanceAct.md`
- [ ] **C23:** MOVE `D:\AI_DOS\ai-dos\memory\TaxRules.md` → `docs/ai-dos/memory/TaxRules.md`
- [ ] **C24:** MOVE `D:\AI_DOS\ai-dos\memory\Decisions.md` → `docs/ai-dos/memory/Decisions.md`
- [ ] **C25:** MOVE `D:\AI_DOS\ai-dos\memory\CompletedFeatures.md` → `docs/ai-dos/memory/CompletedFeatures.md`
- [ ] **C26:** MOVE `D:\AI_DOS\ai-dos\memory\FutureIdeas.md` → `docs/ai-dos/memory/FutureIdeas.md`
- [ ] **C27:** MOVE `D:\AI_DOS\ai-dos\memory\KnownIssues.md` → `docs/ai-dos/memory/KnownIssues.md`
- [ ] **C28:** MOVE `D:\AI_DOS\ai-dos\memory\InterviewLogic.md` → `docs/ai-dos/memory/InterviewLogic.md`

### 7.6 Phase 5: Archive Superseded Files

- [ ] **C29:** MOVE `D:\AI_DOS\ai-dos\memory\Architecture.md` → `docs/ai-dos/memory/archive/Architecture-v0.1.md`
- [ ] **C30:** ADD supersession header to `Architecture-v0.1.md`
- [ ] **C31:** MOVE `D:\AI_DOS\ai-dos\memory\TechnicalDebt.md` → `docs/ai-dos/memory/archive/TechnicalDebt-v0.1.md`
- [ ] **C32:** ADD supersession header to `TechnicalDebt-v0.1.md`

### 7.7 Phase 6: Merge Documents

- [ ] **C33:** CREATE `docs/domain/BusinessRules.md` — merge AI-DOS `memory/BusinessRules.md` + IT_Returns `docs/DATA_MODEL.md` business content
- [ ] **C34:** VERIFY merged BusinessRules.md is comprehensive

### 7.8 Phase 7: Fix Cross-References

- [ ] **C35:** UPDATE all internal links in moved AI-DOS files to new paths
- [ ] **C36:** UPDATE `docs/ai-dos/memory/README.md` with new directory structure
- [ ] **C37:** UPDATE `README.md` (root) to reference `docs/ai-dos/`
- [ ] **C38:** UPDATE `HANDOFF.md` to reference consolidated paths
- [ ] **C39:** UPDATE `.gitignore` to include new paths

### 7.9 Phase 8: Validate

- [ ] **C40:** Verify all moved files are readable at new paths
- [ ] **C41:** Verify all internal links resolve correctly
- [ ] **C42:** Verify `apps/api/` still runs (no path changes to code)
- [ ] **C43:** Verify `apps/web/` still builds
- [ ] **C44:** Verify CLAUDE.md bootstraps correctly
- [ ] **C45:** Verify `git status` shows expected changes only

### 7.10 Phase 9: Decommission Repository A

- [ ] **C46:** CREATE `D:\AI_DOS\README.md` with pointer to `D:\IT_Returns\docs\ai-dos\`
- [ ] **C47:** COMMIT all changes in IT_Returns with message: `consolidation: merge AI-DOS governance and memory into docs/ai-dos/`
- [ ] **C48:** Final verification — agent reads CLAUDE.md → Constitution → memory README in a test session

---

## 8. Final Execution Plan

### 8.1 Execution Order

```
EXECUTION SEQUENCE: TOP-TO-BOTTOM, EACH PHASE GATED

Phase 1: PRE-CONSOLIDATION (5 min)
  ├── git status clean in both repos
  ├── Create backup branches
  └── Audit cross-reference links

Phase 2: CREATE DIRECTORIES (1 min)
  └── Create all new directories in IT_Returns

Phase 3: CREATE ROOT BOOTSTRAP (5 min)
  └── Write CLAUDE.md (P0 — critical for agent continuity)

Phase 4: MOVE GOVERNANCE (2 min)
  ├── 00-Constitution.md
  ├── 01-Chief-Architect.md
  └── 03-Engineering-Standards.md

Phase 5: MOVE ACTIVE MEMORY (3 min)
  └── 8 active memory files

Phase 6: ARCHIVE SUPERSEDED (2 min)
  └── 2 files to archive with supersession headers

Phase 7: MERGE & CREATE (15 min)
  ├── CREATE merged BusinessRules.md
  └── (Missing governance docs created LATER, not during consolidation)

Phase 8: FIX CROSS-REFERENCES (10 min)
  └── Update all internal links

Phase 9: VALIDATE (5 min)
  ├── Verify all files readable
  ├── Verify links resolve
  └── Verify apps still work

Phase 10: DECOMMISSION REPO A (2 min)
  └── Add pointer README to D:\AI_DOS

TOTAL ESTIMATED EXECUTION: ~50 minutes
```

### 8.2 Git Commands (To Be Executed)

```bash
# Phase 1
cd D:\IT_Returns && git status
cd D:\AI_DOS && git status
cd D:\IT_Returns && git branch backup/pre-consolidation-2026-07-05

# Phase 2
cd D:\IT_Returns
mkdir -p docs/ai-dos/memory/archive
mkdir -p docs/domain
mkdir -p packages infra scripts tools

# Phases 4-6: All moves
cd D:\IT_Returns
cp D:\AI_DOS\ai-dos\00-Constitution.md docs/ai-dos/00-Constitution.md
cp D:\AI_DOS\ai-dos\01-Chief-Architect.md docs/ai-dos/01-Chief-Architect.md
# ... (all cp commands)
# Then commit in IT_Returns, then delete originals in AI_DOS

# Phase 10
echo "# AI-DOS has moved" > D:\AI_DOS\README.md
echo "All governance and memory documents now live at:" >> D:\AI_DOS\README.md
echo "D:\IT_Returns\docs\ai-dos\" >> D:\AI_DOS\README.md
```

### 8.3 Rollback Plan

If consolidation fails:
1. `git checkout backup/pre-consolidation-2026-07-05` in IT_Returns
2. Restore AI-DOS files from backup
3. Root cause the failure
4. Re-execute

### 8.4 What Does NOT Change

| Unchanged | Reason |
|-----------|--------|
| `apps/api/` — all 42 Python files | Production code paths untouched |
| `apps/web/` — all TypeScript/React files | Production code paths untouched |
| `docs/architecture/` — all 10 ECM/analysis files | Enterprise architecture untouched |
| `design/` — all 29 design files | Design specs untouched |
| `render.yaml`, `Dockerfile`, `pyproject.toml` | Deployment configs untouched |
| Python import paths (`from src.*`) | Unchanged — no code modification |
| Database schema, connections, credentials | Unchanged |
| Environment variables | Unchanged |
| CI/CD pipeline (`.github/workflows/`) | Unchanged |

---

## Appendix A: CLAUDE.md Content Specification

```markdown
# CLAUDE.md — Agent Bootstrap

> This is the first file every AI agent reads before taking any action in this repository.

## Mandatory Read Order

1. **`docs/ai-dos/00-Constitution.md`** — Supreme governance. Read before ANY action.
2. **`docs/ai-dos/memory/README.md`** — Architect session protocol. Read to understand how project memory works.
3. **`docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md`** — FROZEN target architecture.
4. **`docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md`** — Current architecture state.

## Quick Reference

- **Governance:** `docs/ai-dos/` — All standards, principles, agent rules
- **Architecture:** `docs/architecture/` — Target state, current state, gap analysis
- **Memory:** `docs/ai-dos/memory/` — Living documents updated every session
- **Domain:** `docs/domain/` — Business rules and tax domain knowledge
- **Code:** `apps/api/` (backend), `apps/web/` (frontend)

## Before Any Code Change

1. Read the Constitution (always first)
2. Read relevant memory files for context
3. Read the ECM for target state
4. Read existing code in the affected modules
5. Follow engineering standards in `docs/ai-dos/03-Engineering-Standards.md`

## Authority Order

Constitution > Chief Architect > ECM > Recovery Report > Gap Report > ADRs > Design Docs > Code > Memory
```

---

*End of Repository Consolidation Plan v1.0*
*This is an EXECUTION PLAN. No files have been moved, archived, or deleted. Execution occurs only after explicit approval of this plan.*
