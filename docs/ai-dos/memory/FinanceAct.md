# Finance Act Memory

> **Purpose:** Track Finance Act versions, their effective dates, and implementation status.
> **Updated By:** Architect Agent — every session during tax rule work.
> **Last Updated:** 2026-07-05
> **Session ID:** INIT
> **Cross-Refs:** [BusinessRules.md](BusinessRules.md), [TaxRules.md](TaxRules.md), [Architecture.md](Architecture.md)

---

## 1. Finance Act Registry

### 1.1 Active Finance Acts

| Finance Act | Financial Year | Assessment Year | Effective From | Effective Until | Implementation Status |
|-------------|---------------|-----------------|----------------|-----------------|----------------------|
| Finance Act 2025 | FY2025-26 | AY2026-27 | 2025-04-01 | 2026-03-31 | **NOT STARTED** |
| Finance Act 2024 | FY2024-25 | AY2025-26 | 2024-04-01 | 2025-03-31 | **NOT STARTED** |
| Finance Act 2023 | FY2023-24 | AY2024-25 | 2023-04-01 | 2024-03-31 | **NOT STARTED** |
| Finance Act 2022 | FY2022-23 | AY2023-24 | 2022-04-01 | 2023-03-31 | **NOT STARTED** |
| Finance Act 2021 | FY2021-22 | AY2022-23 | 2021-04-01 | 2022-03-31 | **NOT STARTED** |
| Finance Act 2020 | FY2020-21 | AY2021-22 | 2020-04-01 | 2021-03-31 | **NOT STARTED** |

### 1.2 Future Finance Acts (Known Upcoming Changes)

| Finance Act | Expected | Key Expected Changes | Preparation Status |
|-------------|----------|---------------------|--------------------|
| Finance Act 2026 | Feb 2026 (Budget) | To be announced | **MONITORING** |
| Finance Act 2027 | Feb 2027 (Budget) | To be announced | **MONITORING** |

## 2. Finance Act Change Impact Matrix

When a new Finance Act is released, assess impact across these dimensions:

| Dimension | Impact Areas | Review Required By |
|-----------|-------------|--------------------|
| **Tax Slabs** | Income brackets, rates for old/new regime | Domain Expert |
| **Surcharge** | Thresholds, rates, caps | Domain Expert |
| **Cess** | Rate changes, new cesses | Domain Expert |
| **Deductions** | New sections, amended limits, sunset clauses | Domain Expert |
| **Exemptions** | New exemptions, withdrawn exemptions | Domain Expert |
| **Capital Gains** | Holding periods, indexation, new exemptions | Domain Expert |
| **TDS/TCS** | Rate changes, new provisions, threshold changes | Domain Expert |
| **ITR Forms** | New forms, schema changes, new schedules | Domain Expert |
| **Procedural** | Deadlines, compliance requirements, penalties | Domain Expert |
| **Definitions** | Changes to defined terms (e.g., "resident," "specified asset") | Domain Expert |

## 3. Finance Act Implementation Checklist

When implementing a new Finance Act:

```
FINANCE ACT IMPLEMENTATION CHECKLIST:

Pre-Implementation:
□ Finance Act gazette notification obtained
□ All sections affecting tax computation identified
□ CBDT notifications/circulars reviewed (if available)
□ ITR form schema changes identified (when CBDT releases)
□ Impact assessment completed (which modules change)
□ ADR written for any architecture-impacting changes

Implementation:
□ Tax slab configuration created for FY
□ New/changed deduction sections added to rule registry
□ Surcharge rates updated per new provisions
□ Cess rates verified/updated
□ Rebate thresholds updated
□ Capital gains rules updated if changed
□ TDS rates updated if changed
□ ITR schema updated per new form specifications
□ All changes tagged with: finance_act, section, effective_date
□ Existing rules superseded (not modified) with supersedes reference

Validation:
□ All new rules have corresponding test cases
□ Cross-year regression tests pass
□ Domain expert review completed
□ Sample computations verified against manual calculations
□ Edge cases tested (boundary thresholds, transitional provisions)

Deployment:
□ Release notes include compliance statement
□ Rollback plan documented
□ Monitoring alerts configured for new rule execution
□ Support documentation updated
```

## 4. Finance Act Versioning in Code

### 4.1 Metadata Standard

Every Finance Act rule in the codebase must carry:

```python
FINANCE_ACT_METADATA = {
    "finance_act": "Finance Act 2025",
    "financial_year": "FY2025-26",
    "assessment_year": "AY2026-27",
    "effective_from": "2025-04-01",
    "effective_until": "2026-03-31",
    "gazette_notification": "No. XX/2025 dated DD-MM-YYYY",
    "sections_affected": ["115BAC", "87A", "80C", ...],
    "supersedes": "Finance Act 2024 provisions",
    "superseded_by": None,
    "status": "ACTIVE"  # ACTIVE | SUPERSEDED | PROPOSED
}
```

### 4.2 Transition Rules

When a Finance Act introduces changes mid-year or with specific transition rules:

1. Rules must encode both old and new behavior with effective date gates
2. Computation must check the transaction date against the effective date
3. For FY-specific rules: use the financial year, not the current date
4. For transaction-specific rules (e.g., capital gains): use the transaction date
5. Transition provisions must be explicitly documented in the rule metadata

## 5. CBDT Notification Tracker

| Notification | Date | Subject | Affects FY | Implementation Status |
|-------------|------|---------|------------|----------------------|
| *None tracked yet* | — | — | — | — |

## 6. Known Future Changes (Tax Law Pipeline)

| Change | Source | Expected FY | Certainty | Preparation |
|--------|--------|-------------|-----------|-------------|
| DPDP Act rules | MeitY | TBD | HIGH — rules under drafting | Architecture must support data principal rights |
| New ITR portal APIs | ITD | TBD | MEDIUM — expected to replace e-filing 2.0 | API integration layer should be abstracted |
| DTC (Direct Tax Code) | Govt | Unknown | LOW — under consideration, no draft | Monitor; architecture is flexible enough |

---

## Session Log

| Date | Session ID | Changes Made | Agent |
|------|-----------|--------------|-------|
| 2026-07-05 | INIT | Finance Act memory initialized. 6 FYs registered (2020-26). | Architect |

---

*This file tracks Finance Act versions. When a new Budget is announced, this file drives the implementation.*
