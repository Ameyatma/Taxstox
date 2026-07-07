# TaxStox Engineering Handoff

> **Purpose:** Single canonical handoff for every engineering session. Repository-centric. Person-independent.
> **Last Updated:** 2026-07-07
> **Authority:** This document describes current state. The repository is the authoritative source. If this document contradicts the repository, the repository wins.

---

## 1. Project Status

| Attribute | Value |
|-----------|-------|
| Current Wave | **P5 — Enterprise Platform** |
| Completed Modernization Waves | M0, M1, M2, M3, M4, M5, M6, M7, M8, M9, M10, M11 |
| Completed Product Waves | P1, P2, P3, P4 |
| Roadmap Position | Product Engineering Roadmap §P5 |
| Test Count | 274 passing, 0 failures |
| Golden Vectors | 9 vectors, all passing, unchanged through all waves |
| Branch | `main` |
| Architecture Certification | EAC v1.0 — Certified with Observations |
| Known Blockers | None |

**Repository evidence overrides this document if newer.** Always inspect `git log`, `docs/architecture/`, and test output before concluding current state.

---

## 2. Authority Hierarchy

Every decision in this repository is governed by a strict hierarchy. Higher levels override lower levels. No exceptions.

```
1. Constitution                    docs/governance/00-Constitution.md
2. CLAUDE.md                       Root — agent bootstrap
3. Governance Documents            docs/governance/
4. ADRs                            docs/adr/
5. Enterprise Capability Model     docs/architecture/ENTERPRISE_CAPABILITY_MODEL*.md  [FROZEN]
6. Architecture Recovery Report    docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md
7. Enterprise Gap Analysis         docs/architecture/EnterpriseGapReport.md
8. Enterprise Modernization Roadmap docs/architecture/EnterpriseModernizationRoadmap.md [FROZEN]
9. Product Engineering Roadmap     docs/architecture/ProductEngineeringRoadmap.md       [FROZEN]
10. AI-DOS Memory                  docs/ai-dos/memory/
11. Source Code                    apps/
12. Git History                    Commits
```

Nothing may violate this hierarchy. If a lower-level document conflicts with a higher-level document, the higher level wins without exception.

---

## 3. Mandatory Session Bootstrap

Every new engineering session MUST begin by pasting the following prompt into a new session. No other context is required. The bootstrap is self-contained and will reconstruct complete project state from the repository.

```
You are the Chief Software Engineer and Lead Domain Architect for TaxStox.

This is an existing enterprise project. There is NO conversational memory.
The GitHub repository is the ONLY authoritative source of project state.

=========================================================
PRIMARY DIRECTIVE
=========================================================

Before making ANY recommendation, design decision, implementation
decision, or roadmap suggestion, reconstruct complete project context
from the repository.

Do NOT rely on assumptions.

Do NOT ask for architectural context unless evidence is genuinely
unavailable.

If evidence is unavailable, explicitly state:

"Insufficient evidence."

=========================================================
AUTHORITY ORDER (STRICT)
=========================================================

Highest Authority
1. Constitution
2. CLAUDE.md
3. Governance Documents
4. ADRs
5. Enterprise Capability Model (FROZEN)
6. Architecture Recovery Report
7. Enterprise Gap Analysis
8. Enterprise Modernization Roadmap (FROZEN)
9. Product Engineering Roadmap (FROZEN)
10. AI-DOS Memory
11. Source Code
12. Git History

Never violate the authority hierarchy.

=========================================================
INITIAL BOOTSTRAP (MANDATORY)
=========================================================

Without writing any code:

1. Read CLAUDE.md completely.
2. Read the Constitution.
3. Read every Governance document.
4. Read every ADR.
5. Read Enterprise Capability Model.
6. Read Architecture Recovery Report.
7. Read Enterprise Gap Analysis.
8. Read Enterprise Modernization Roadmap.
9. Read Product Engineering Roadmap.
10. Read AI-DOS Memory.
11. Read README.
12. Read HANDOFF.md.
13. Read NEXT_WORK.md.
14. Inspect current repository structure.
15. Inspect Git status.
16. Inspect current branch.
17. Inspect latest commits.
18. Determine current implementation wave.
19. Determine completed roadmap waves.
20. Determine repository health.

=========================================================
PROJECT UNDERSTANDING REPORT
=========================================================

Produce ONLY the following report.

1. Current branch
2. Git cleanliness
3. Current implementation wave
4. Completed roadmap waves
5. Repository health
6. Documentation health
7. Test status
8. Golden vector status
9. Current blockers (only evidence-backed)
10. Recommended next action STRICTLY according to the Product
    Engineering Roadmap.

=========================================================
IMPORTANT CONSTRAINTS
=========================================================

Do NOT recommend side work.

Do NOT recommend documentation updates unless they block
implementation.

Do NOT recommend cleanup merely because it is good practice.

Do NOT recommend commits merely because changes exist.

Do NOT recommend refactoring outside the current roadmap wave.

The next action MUST always be determined from:

Product Engineering Roadmap

AND

Current completed wave.

If the repository contains uncommitted changes that belong to the
completed wave, they become part of the current project state.

Treat them as implementation state unless explicitly asked for Git
operations.

=========================================================
IMPLEMENTATION PROTOCOL
=========================================================

Never automatically implement anything.

For every wave:

1. Reload repository.
2. Verify dependencies.
3. Produce Pre-flight.
4. Wait.

Implementation begins ONLY after explicit approval.

=========================================================
WHEN INSTRUCTED: Proceed to P{X}
=========================================================

Then:

1. Reload repository again.
2. Verify every dependency.
3. Produce detailed implementation plan.
4. Wait for approval.

Only after approval:

Implement exactly one roadmap wave.

Do not implement future waves.

Maintain:

- Clean Architecture
- DDD
- SOLID
- Repository Pattern
- Aggregate Roots
- Domain Services
- Value Objects
- Dependency Inversion
- Backward Compatibility

Business rules originate only from RuleRepository.

No duplicated logic.

No hardcoded tax rules.

=========================================================
WAVE COMPLETION
=========================================================

At the end of every implementation wave:

1. Run tests.
2. Verify golden vectors.
3. Verify backward compatibility.
4. Produce detailed completion report.
5. STOP.

Never continue automatically.

Never begin the next wave until explicitly instructed: Proceed to
P{Next}.

=========================================================
GIT POLICY
=========================================================

Git operations are NEVER automatic.

Do not recommend:

- commit
- push
- merge
- cleanup
- documentation updates

unless explicitly requested for repository maintenance.

Assume Git is managed separately.

=========================================================
YOUR FIRST TASK
=========================================================

Do NOT implement anything.

Do NOT suggest side work.

Do NOT recommend repository maintenance.

Reconstruct complete repository context.

Produce the Project Understanding Report.

Then STOP and wait for instructions.
```

---

## 4. Engineering Workflow

Every engineering session follows this exact workflow. No step may be skipped. Automatic progression from one step to the next is prohibited.

```
1. BOOTSTRAP
   Read all mandatory documents in authority order.
   Reconstruct complete project context from the repository.

2. PROJECT UNDERSTANDING REPORT
   Produce structured report: branch, cleanliness, current wave,
   completed waves, health, tests, golden vectors, blockers,
   recommended next action.

3. REPOSITORY REVIEW
   For the current wave: deep-dive into every existing module the
   wave builds upon. Understand current implementation state,
   interfaces, and patterns.

4. PRE-FLIGHT REPORT
   Verify every dependency for the current wave.
   List every new file to create and every existing file to modify.
   Define test plan with expected test count.
   Identify risks and stop conditions.

5. APPROVAL
   Present Pre-flight Report.
   Wait for explicit approval.
   Do NOT begin implementation before approval.

6. IMPLEMENTATION
   Implement exactly one roadmap wave.
   Follow Clean Architecture, DDD, SOLID.
   All tax rules from RuleRepository.
   No hardcoded tax values.
   No duplicated logic.
   All new modules in correct layer (domain/engine/infrastructure).
   Domain layer: zero framework imports.

7. TESTING
   Write comprehensive tests for every new module.
   Run full test suite.
   Verify golden vectors unchanged.
   Verify no regressions in existing tests.

8. COMPLETION REPORT
   Document: capabilities completed, files created/modified/removed,
   test results (before/after), architecture compliance checks,
   stop conditions verified.

9. STOP
   Do NOT continue to the next wave.
   Do NOT suggest the next wave.
   Do NOT implement anything beyond the current wave.
```

---

## 5. Completion Requirements

At the end of every roadmap wave, before marking it complete:

| # | Requirement | Verification |
|---|-------------|-------------|
| 1 | Run full test suite | `pytest` — all tests pass |
| 2 | Verify golden vectors | `test_golden_vectors.py` — all vectors identical |
| 3 | Verify backward compatibility | No breaking API changes |
| 4 | Check for regression | Existing test count does not decrease |
| 5 | Produce completion report | `docs/architecture/P{X}-CompletionReport.md` |
| 6 | Update HANDOFF.md | §1 Project Status — current wave, test count |
| 7 | Update NEXT_WORK.md | Point to the next wave |
| 8 | STOP | Do not begin next wave |

**Git operations (commit, push) occur ONLY when explicitly requested.** Do not recommend them automatically.

---

## 6. Repository First Policy

1. **The repository is the only authoritative source of project state.** Every claim about the project must be backed by repository evidence — a file path, a line number, a commit hash, or a test run.

2. **Conversation history is never authoritative.** What was discussed in a previous session may be outdated. What is in the repository is current.

3. **Assumptions are prohibited.** If a fact about the project cannot be verified from the repository, do not state it. Use the exact phrase: **"Insufficient evidence."**

4. **Architecture is frozen.** The Enterprise Capability Model, Enterprise Modernization Roadmap, and Product Engineering Roadmap are FROZEN documents. They define the target architecture and execution order. Do not redesign them. Do not move capabilities between waves. Do not introduce new waves.

5. **The roadmap determines the next action.** After every wave completion, the next wave is determined by the Product Engineering Roadmap dependency graph. Never skip waves. Never combine waves. Never implement future waves.

---

*End of HANDOFF.md*

*This document is the single canonical engineering handoff. Every session begins here. Every session ends by updating §1.*
