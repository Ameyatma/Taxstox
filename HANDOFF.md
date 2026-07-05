# TaxStox ITR Platform — Engineering Handoff

> **For:** Prasoon (and all future engineers)
> **Date:** 2026-07-05
> **Status:** Modernization Wave 7 of 11 complete. M8 next.

---

## 1. Project Overview

TaxStox is an enterprise AI-powered Indian Tax Intelligence Platform. It automates ITR filing: users upload Form 16 + AIS PDFs, answer 0-5 adaptive questions, and download schema-compliant ITR JSON ready for the ITD portal.

**Production:** Live at `taxstox.com` (Next.js frontend on Vercel, FastAPI backend on Render, Neon PostgreSQL).

**Domain:** Indian Income Tax — all ITR types, Finance Act versioning, capital gains, business income, old/new regime optimization.

## 2. Repository Philosophy

This is an **AI Development Operating System (AI-DOS)** governed repository. Every decision is traceable. Every document has a purpose. Architecture is supreme. Code is subordinate.

**Core principle:** AI agents must produce consistent output across months. The governance framework ensures this.

## 3. Architecture Philosophy

1. **Domain-Driven Design** — Code organized by bounded context, not technical layer
2. **Clean Architecture** — Domain → Application → Infrastructure. Dependencies point inward.
3. **Rule-Engine Separation** — Tax rules are versioned data, not code. `RuleRepository` is the single source of truth.
4. **FinancialYear Everywhere** — No raw strings. `FinancialYear` value object is mandatory.
5. **Immutable Results** — Computation outputs are frozen dataclasses. Audit trails are append-only.
6. **Golden Vector Verification** — Known inputs → expected outputs. Any change that alters golden vectors is blocked.

## 4. Governance Hierarchy (Permanent)

```
1. docs/governance/00-Constitution.md          ← SUPREME (10 principles, 10 invariants)
2. docs/governance/01-Chief-Architect.md       ← ADR process, module boundaries
3. docs/architecture/ENTERPRISE_CAPABILITY_MODEL*.md ← FROZEN target (148 capabilities)
4. docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md ← Current state
5. docs/architecture/EnterpriseGapReport.md    ← Gap analysis
6. docs/architecture/EnterpriseModernizationRoadmap.md ← Execution blueprint
7. docs/adr/                                   ← Architecture Decision Records
8. docs/governance/03-Engineering-Standards.md ← Coding rules
```

**Higher levels override lower levels. No exceptions.**

## 5. Document Authority Hierarchy

| Level | Documents | Can Be Modified By |
|-------|-----------|--------------------|
| 1-3 (Supreme) | Constitution | CTO + Chief Architect + ADR |
| 4 (Architecture) | Chief Architect, ECM, Recovery, Gap, Roadmap | Chief Architect + ADR |
| 5-6 (Implementation) | Engineering Standards, Testing Standards, Wave Execution Plans | Tech Lead + Chief Architect |
| 7 (Decisions) | ADRs | Chief Architect |
| 8 (Reference) | Design docs, Project Memory | Any contributor |

## 6. Mandatory Reading Order

Every engineer and AI agent MUST read in this order:
1. `CLAUDE.md` — Agent bootstrap
2. `docs/governance/00-Constitution.md` — Supreme governance
3. `docs/governance/01-Chief-Architect.md` — Architecture governance
4. `docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md` — Target architecture (FROZEN)
5. `docs/architecture/EnterpriseModernizationRoadmap.md` — Execution blueprint (FROZEN)
6. `docs/handoff/PRASOON_ONBOARDING.md` — Onboarding guide
7. `docs/handoff/NEXT_WORK.md` — Exact next work item

## 7. Repository Structure

```
D:\IT_Returns\
├── CLAUDE.md                       ← Agent bootstrap — read first
├── HANDOFF.md                      ← THIS FILE
│
├── docs/
│   ├── governance/                 ← Supreme governance docs
│   ├── architecture/               ← FROZEN architecture (ECM, roadmap, gap, health, risk)
│   ├── ai-dos/memory/              ← Project Memory (living docs)
│   ├── ai-dos/archive/             ← Superseded docs (historical)
│   ├── adr/history/                ← Architecture Decision Records
│   ├── recovery/                   ← Navigation index → architecture docs
│   ├── gap-analysis/               ← Navigation index → architecture docs
│   ├── domain/                     ← Business rules reference
│   ├── roadmap/                    ← Placeholder
│   └── handoff/                    ← Engineer handoff docs
│
├── apps/
│   ├── api/                        ← FastAPI backend (Python 3.12+)
│   │   ├── src/
│   │   │   ├── engine/             ← Domain logic (tax computation, rules, audit)
│   │   │   │   ├── rules/          ← RuleRepository + RuleEvaluator (M1)
│   │   │   │   ├── audit.py        ← Audit trail (M6)
│   │   │   │   ├── explain.py      ← Explanation engine (M6)
│   │   │   │   ├── knowledge_graph.py ← Tax knowledge graph (M7)
│   │   │   │   └── ...             ← 15+ engine modules
│   │   │   ├── models/             ← Domain models (Pydantic)
│   │   │   ├── parsers/            ← Document parsing (Form16, AIS, 26AS)
│   │   │   ├── builders/           ← ITR JSON generation
│   │   │   └── api/                ← FastAPI routes
│   │   └── tests/                  ← 138 tests, all passing
│   └── web/                        ← Next.js frontend
│
├── design/                         ← Design specs + HTML prototypes
└── .github/workflows/              ← CI pipeline
```

## 8. Current Modernization Status

| Wave | Name | Status | Date |
|------|------|--------|------|
| M0 | Engineering Foundation | ✅ COMPLETE | 2026-07-05 |
| M1 | Core Domain Foundation | ✅ COMPLETE | 2026-07-05 |
| M2 | Document Intelligence Enhancement | ✅ COMPLETE | 2026-07-05 |
| M3 | Income & Deduction Engines | ✅ COMPLETE | 2026-07-05 |
| M4 | Tax Computation & Optimization | ✅ COMPLETE | 2026-07-05 |
| M5 | Compliance & ITR Generation | ✅ COMPLETE | 2026-07-05 |
| M6 | Audit, Explainability & Traceability | ✅ COMPLETE | 2026-07-05 |
| M7 | AI Knowledge Platform | ✅ COMPLETE | 2026-07-05 |
| **M8** | **Enterprise Multi-Tenancy** | **← NEXT WAVE** | — |
| M9 | Security & Privacy | PENDING | — |
| M10 | Integration & Ecosystem | PENDING | — |
| M11 | Production Hardening | PENDING | — |

## 9. Architecture Health

| Metric | Score | Trend |
|--------|-------|-------|
| Overall | **31→~45** | Improving |
| Domain Design | 15→25 | Improving |
| Testability | 10→35 | Improving (138 tests) |
| Modularity | 45→55 | Improving |
| AI Readiness | 10→25 | Improving |

## 10. Testing Status

- **138 tests, all passing**
- 0 failures, 0 skipped
- Coverage: ~38% (engine modules well-covered, API routes not yet)
- Golden vectors: 8 vectors, all passing, unchanged through M0-M7
- CI pipeline: lint (ruff) + typecheck (mypy) + test (pytest) + security (bandit)

## 11. Key Engineering Rules

### Non-Negotiable
- **FinancialYear is mandatory** — never use raw strings for FY
- **RuleRepository is the sole rule source** — no hardcoded tax constants
- **RuleEvaluator performs all rule evaluation** — no duplicated computation
- **Golden vectors must pass** — any change altering golden vectors is blocked
- **Backward compatible** — no breaking API changes
- **Additive preferred** — new modules over modifying existing ones
- **No circular dependencies** — resolved via dependency inversion
- **No Finance Act values outside RuleRepository**

### Definition of Done
- [ ] All tests pass (138 minimum)
- [ ] Golden vectors unchanged
- [ ] Lint passes (ruff)
- [ ] Type checking passes (mypy strict)
- [ ] Security scan passes (bandit)
- [ ] No hardcoded tax constants
- [ ] FinancialYear used everywhere applicable
- [ ] ADR written if architecture changed
- [ ] Completion report in `docs/architecture/`

## 12. Quality Gate Process

Every wave exit requires:
1. **G2: Code Quality** — Lint + type check
2. **G3: Security** — Bandit scan
3. **G4: Test Coverage** — No decrease
4. **G5: Regression** — Golden vectors pass
5. **G7: Documentation** — Updated
6. **G9: Deployment** — Staging verified

See `docs/architecture/QualityGateFramework.md` for full details.

## 13. Stop Conditions

**STOP and escalate if:**
- Constitution is violated
- Architectural invariant is broken
- Golden vectors change unexpectedly
- Circular dependency is introduced
- Finance Act constant appears outside RuleRepository
- ECM requires modification

## 14. Common Mistakes to Avoid

1. **Hardcoding a tax rate** — use `config.get_deduction_limit()` or `RuleEvaluator`
2. **Using raw FY strings** — use `FinancialYear.from_string("FY2025-26")`
3. **Modifying frozen documents** — ECM, Roadmap, Gap Report are FROZEN
4. **Skipping waves** — follow the dependency graph exactly
5. **Starting M9 before M8** — each wave depends on the previous
6. **Creating circular imports** — use dependency inversion
7. **Adding business logic to API routes** — keep it in engine/

## 15. Golden Vector Policy

Golden vectors are test cases with known inputs and ITD-verified expected outputs. They are the primary defense against silent tax computation errors.

- **Location:** `tests/test_golden_vectors.py`
- **Modification:** Only when explicitly correcting a verified defect
- **Blocking:** Any change that alters golden vector output blocks deployment

## 16. Branch Strategy

- **main** — Production. Deploy on merge.
- **feature/m{X}-{description}** — Feature branches per wave
- **No direct commits to main** — PR required, CI must pass

## 17. Commit Conventions

```
chore(wave): complete M{X} — {brief description}
feat(engine): add {module} — {capability reference}
fix(engine): correct {issue} — {evidence}
docs: update {document}
```

## 18. Expected Engineering Behaviour

1. Read the governance docs before writing code
2. Follow the modernization roadmap exactly
3. Complete one wave before starting the next
4. Write tests with every new module
5. Update the completion report
6. Never modify frozen documents
7. Maintain backward compatibility
8. Use the RuleRepository for all tax rules
9. Produce completion reports after every wave

---

*This HANDOFF.md is the primary reference for all future engineers. When in doubt, return here.*
