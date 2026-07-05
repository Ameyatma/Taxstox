# Modernization Risk Plan

> **Date:** 2026-07-05
> **Derived From:** Enterprise Risk Matrix (15 risks), Gap Report, Technical Debt Heatmap

---

## Risk Registry — Modernization Phase

### MR-1: Rule Extraction Introduces Computation Errors

| Dimension | Assessment |
|-----------|-----------|
| **Parent Risk** | R07 (Silent Tax Errors — High) |
| **Probability** | Medium (40%) — Rules are embedded in procedural code; extraction may miss edge cases |
| **Impact** | Critical — Wrong tax for all users |
| **Affected Waves** | M1 |
| **Mitigation** | Golden-test-vector suite gates every extraction. Before/after output compared byte-for-byte. Domain expert (CA) verifies test vectors against ITD portal. Blocker gate: cannot exit M1 unless all golden vectors match. |
| **Contingency** | Revert to hardcoded constants (preserved in git). Redo extraction with additional edge case analysis. |

### MR-2: Tenant Migration Causes Data Corruption

| Dimension | Assessment |
|-----------|-----------|
| **Parent Risk** | New — introduced by M8 |
| **Probability** | Low (20%) — If migration scripts are idempotent and tested |
| **Impact** | Critical — Data integrity failure across all users |
| **Affected Waves** | M8 |
| **Mitigation** | Database backup verified before migration. Migration tested on staging with production-scale data. Backfill script runs as idempotent batch. Rollback script tested. |
| **Contingency** | Rollback migration. Restore from backup. Root cause. Retry. |

### MR-3: Filing Season Scalability Failure

| Dimension | Assessment |
|-----------|-----------|
| **Parent Risk** | R05 (Scalability — High) |
| **Probability** | Medium (35%) until M11 |
| **Impact** | High — Users cannot file during peak |
| **Affected Waves** | All waves until M11 |
| **Mitigation** | Load testing before each filing season. In-memory session → Redis in M11. Rate limiting added early (M0). Auto-scaling configured. |
| **Contingency** | Scale vertically (larger instances). Add queue for PDF processing. |

### MR-4: DPDP Act Enforcement Before Compliance Complete

| Dimension | Assessment |
|-----------|-----------|
| **Parent Risk** | R02 (DPDP Non-Compliance — Critical) |
| **Probability** | Medium (50%) — DPDP rules expected within 12-18 months |
| **Impact** | Critical — Regulatory penalties; platform shutdown |
| **Affected Waves** | M9 (scheduled late in program) |
| **Mitigation** | Monitor DPDP rules timeline. If enforcement accelerates, elevate M9 before M7-M8. Consent stub implementation (minimal viable compliance) can be pulled forward. |
| **Contingency** | Emergency compliance sprint. Shift M9 ahead of M7-M8 if required. |

### MR-5: Key Person Loss During Modernization

| Dimension | Assessment |
|-----------|-----------|
| **Parent Risk** | R08 (Key Person Dependency — High) |
| **Probability** | Low (20%) — Founders currently active |
| **Impact** | High — Tax domain knowledge loss |
| **Affected Waves** | M3-M7 (tax-heavy waves) |
| **Mitigation** | M7 Knowledge Graph explicitly targets this risk. Domain knowledge captured in structured form. Rule documentation requirement in every tax wave. |
| **Contingency** | External CA consultation. Knowledge recovery from source code + existing docs. |

### MR-6: Wave Scope Creep

| Dimension | Assessment |
|-----------|-----------|
| **Parent Risk** | New — program management risk |
| **Probability** | High (60%) — Common in long programs |
| **Impact** | Medium — Timeline inflation; team burnout |
| **Affected Waves** | All |
| **Mitigation** | Strict exit criteria per wave. Architecture review board approves scope changes. Waves are capped at estimated duration + 25%. |
| **Contingency** | Descope non-critical capabilities to later waves. Preserve critical path. |

---

## Risk Heatmap (Modernization Phase)

```
                    IMPACT →
                    Low      Medium    High      Critical
P                   │         │         │         │
R  Very High        │         │         │         │
O                   │         │         │         │
B  High             │         │  MR-6   │         │
A                   │         │         │         │
B  Medium           │         │         │  MR-3   │  MR-1
I                   │         │         │  MR-4   │
L  Low              │         │         │  MR-5   │  MR-2
I                   │         │         │         │
T  Very Low         │         │         │         │
Y                   │         │         │         │
```

---

*End of Modernization Risk Plan v1.0*
