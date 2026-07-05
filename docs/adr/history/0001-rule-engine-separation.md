# ADR-0001: Rule-Engine Separation Architecture

> **Status:** Accepted
> **Date:** 2026-07-05
> **Author:** Enterprise Chief Architect
> **Supersedes:** None
> **Constitutional Principles:** P2 (Architecture First), P8 (Compliance Is Continuous), P10 (Extensibility)
> **Architectural Invariants:** I1 (Multi-Year), I2 (Rule-Engine Separation), I8 (Configurable Everything)

---

## 1. Context

The TaxStox platform hardcoded all tax rules (slab rates, deduction limits, rebate thresholds, surcharge brackets) as Python constants within the computation engine modules. Six files contained duplicated or overlapping constants. Two optimizer implementations existed with inconsistent values (v1 had FY2024-25 rebate thresholds; v2 had FY2025-26). Surcharge brackets were incorrect (missing ₹50L-₹1Cr tier). Supporting a new financial year required code changes across multiple files.

This violated Constitutional Invariants I1, I2, and I8, and created Risk R01 (FY2026 obsolescence, 95% probability) and Risk R07 (silent tax errors from incorrect rule changes).

## 2. Decision

**Extract all tax rules into a centralized, versioned, FY-indexed RuleRepository with a generic RuleEvaluator that operates on rule data without domain knowledge.**

Three new components:

1. **`FinancialYear`** — Immutable value object replacing raw strings. Typesafe. Validated. Supports comparison, iteration, and AY derivation.

2. **`TaxYearConfig`** — Frozen dataclass holding all FY-specific constants for one financial year: slabs (Old + New), deduction limits (20 sections), surcharge thresholds, rebate config, cess rate, CG rates, professional tax cap, HRA percentages. Single source of truth. Immutable. Cacheable.

3. **`RuleEvaluator`** — Stateless, deterministic evaluation engine: slab tax, rebate, surcharge (with marginal relief), cess, final rounding. Zero FY-specific constants. Works with any `TaxYearConfig`.

4. **`RuleRepository`** — Central registry of `TaxYearConfig` instances indexed by `FinancialYear`. Pre-loaded with FY2025-26 and FY2024-25. Supports `register()` for new FYs.

The existing `RegimeOptimizerV2` was refactored to accept `FinancialYear` and delegate all rule-dependent computation to `RuleEvaluator` + `RuleRepository`. The v1 optimizer (`regime_optimizer.py`) was retired. The duplicate slab logic in `builders/itr1.py` was replaced with calls to `RuleEvaluator`.

## 3. Alternatives Considered

### Alternative A: Database-backed rule store

**Pros:** Hot-reloadable without deployment.  
**Cons:** Adds infrastructure dependency for core computation. Slower (network call for every computation). Over-engineered for current scale.  
**Why Rejected:** Premature infrastructure complexity. Config-file approach gives same benefits without operational overhead. Database can be introduced when rule count exceeds ~200 or hot-reload becomes a business requirement.

### Alternative B: Keep hardcoded constants, add FY parameter

**Pros:** Minimal code change. Familiar pattern.  
**Cons:** Rules still embedded in code. Adding FY still changes source files. Duplication persists. No single source of truth.  
**Why Rejected:** Does not satisfy Invariants I2 or I8. Perpetuates the root cause of Risk R01.

### Alternative C: Domain-specific rule language (DSL)

**Pros:** Non-programmer rule authoring. Visual editor potential.  
**Cons:** Massive upfront investment. Learning curve. Tooling maintenance.  
**Why Rejected:** Premature for current scale (60+ rules). Revisit when domain experts (CAs) need direct rule authoring capability (M7 — AI Knowledge Platform).

## 4. Consequences

### Positive

- **Multi-year support:** Adding FY2026-27 requires one new `TaxYearConfig` instance. No code changes.
- **Single source of truth:** All rates/limits/thresholds in one file (`engine/rules/config.py`).
- **Eliminated duplication:** Slabs no longer defined in 3+ files. Deduction limits unified.
- **Eliminated inconsistency:** v1/v2 divergence resolved. Surcharge brackets corrected.
- **Testability:** `RuleEvaluator` is pure functions testable in isolation. `TaxYearConfig` is immutable data verifiable by inspection.
- **Typesafe:** `FinancialYear` replaces error-prone string handling.
- **Resolved circular dependency:** Module-level import replaces lazy import workaround.

### Negative

- **Indirection:** One extra function call to resolve slab tax (negligible performance impact).
- **Learning curve:** Contributors must understand RuleRepository pattern.
- **Config size:** `TaxYearConfig` with 20 deduction limits is verbose but explicit.

### Mitigation

- Performance: `TaxYearConfig` instances are created once at import time. `RuleRepository.get()` is O(1) dict lookup. `RuleEvaluator` methods are stateless pure functions.
- Learning: ADR documents the pattern. Code comments explain the design.

## 5. Compliance

### Constitutional Alignment

| Principle | Alignment |
|-----------|-----------|
| P1: Consistency | All rule access through single repository — consistent across modules |
| P2: Architecture First | ADR written before implementation |
| P8: Compliance Is Continuous | New FY = new config, not code change |
| P10: Extensibility | New rules added via config, not engine modification |

### Architectural Invariants

- [x] I1: Multi-Year Architecture — FY2024-25 and FY2025-26 supported from day 1
- [x] I2: Rule-Engine Separation — Rules in `config.py`, engine in `evaluator.py`
- [x] I8: Configurable Everything — All rates/limits/thresholds in versioned config

## 6. References

- [Enterprise Modernization Roadmap](../architecture/EnterpriseModernizationRoadmap.md) §Wave 1
- [Architecture Recovery Report](../architecture/ARCHITECTURE_RECOVERY_REPORT.md) — identified hardcoded rules
- [Enterprise Gap Report](../architecture/EnterpriseGapReport.md) — C12.1-C12.4 (Critical)
- [Technical Debt Heatmap](../architecture/TechnicalDebtHeatmap.md) — ARC-001, ARC-002, ARC-005, ARC-007
- [Enterprise Risk Matrix](../architecture/EnterpriseRiskMatrix.md) — R01, R07
