# Wave Dependency Matrix

> **Date:** 2026-07-05
> **Derived From:** Enterprise Capability Model, Gap Report, Technical Debt Heatmap

---

## 1. Dependency Graph

```
M0 ────────► M1 ────────┬────────► M3 ───► M4 ───► M5 ───► M6
  (4wk)       (8wk)     │          (8wk)   (6wk)   (8wk)   (6wk)
                         │
                         ├────────► M2 (6wk) ─── can parallel with M3
                         │
                         └────────► M7 (10wk) ───► M8 (10wk) ───► M9 (8wk) ───► M10 (8wk) ───► M11 (6wk)
                                      │
                                      └── depends on M1 rule extraction
```

## 2. Dependency Matrix

| Wave | Depends On | Blocks | Can Parallel With |
|------|-----------|--------|-------------------|
| M0 | — (prerequisite for all) | M1-M11 | Nothing (must be first) |
| M1 | M0 | M2, M3, M4, M5, M6, M7 | Nothing (shared dependency) |
| M2 | M1 | — (not on critical path) | M3 |
| M3 | M1 | M4, M5 | M2 |
| M4 | M3 | M5 | — |
| M5 | M4 | M6 | — |
| M6 | M5 | — | — |
| M7 | M1 | M8 | — |
| M8 | M7 | M9 | — |
| M9 | M8 | M10 | — |
| M10 | M9 | M11 | — |
| M11 | M10 | — | — |

## 3. Critical Path

**M0 → M1 → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10 → M11**

Total critical path: 4 + 8 + 8 + 6 + 8 + 6 + 10 + 10 + 8 + 8 + 6 = **82 weeks**

## 4. Parallelizable Work

| Pair | Overlap | Saved Time |
|------|---------|------------|
| M2 ∥ M3 | 6 weeks of M2 runs alongside M3 | 6 weeks |
| **Optimized total** | | **76 weeks** |

## 5. Blocking Dependencies (Detailed)

| Blocker | Blocks | Reason |
|---------|--------|--------|
| No test framework (M0 incomplete) | M1-M11 | Cannot safely refactor without tests |
| No rule repository (M1 incomplete) | M2-M7 | All domain work requires multi-FY rule support |
| No business income engine (M3 incomplete) | M5 (ITR-3 builder) | ITR-3 requires business income computation |
| No complete tax computation (M4 incomplete) | M5 (compliance) | Tax credit reconciliation needs complete tax |
| No audit trail (M6 incomplete) | — (end of critical path fork) | M6 is terminal for core tax path |
| No knowledge graph (M7 incomplete) | M8 | Enterprise RBAC needs domain context from KG |
| No tenant model (M8 incomplete) | M9 | Security controls need tenant boundaries |
| No security controls (M9 incomplete) | M10 | External APIs need auth/rate-limiting |
| No integrations (M10 incomplete) | M11 | Production hardening needs full system |

## 6. Sequencing Rationale

| Decision | Rationale |
|----------|-----------|
| M0 before everything | Zero tests = cannot safely change anything. Constitution Principle P5. |
| M1 immediately after M0 | Risk R01 (FY2026 obsolescence) has 95% probability. Must be first domain change. |
| M2 not on critical path | Document parsing is self-contained; can improve independently of income/computation work. |
| M3 before M4 | Income heads must exist before you can compute tax on them. |
| M7 before M8 | Knowledge graph provides domain context for enterprise RBAC design. |
| M9 before M10 | External API security depends on authentication/authorization infrastructure. |
| M11 last | Production hardening validates everything built in M0-M10. |

---

*End of Wave Dependency Matrix v1.0*
