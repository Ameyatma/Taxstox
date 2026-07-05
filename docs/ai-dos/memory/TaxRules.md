# Tax Rules Memory

> **Purpose:** Catalog of all implemented tax rules with their metadata, versioning, and dependencies.
> **Updated By:** Architect Agent — every session when tax rules are added or modified.
> **Last Updated:** 2026-07-05
> **Session ID:** INIT
> **Cross-Refs:** [BusinessRules.md](BusinessRules.md), [FinanceAct.md](FinanceAct.md), [Architecture.md](Architecture.md)

---

## 1. Tax Rule Catalog

### 1.1 Rule Organization

Tax rules are organized hierarchically:

```
FinanceAct (e.g., Finance Act 2025)
  └── ITR Type (e.g., ITR-1, ITR-2, ...)
       └── Income Head (e.g., Salary, Capital Gains, ...)
            └── Rule Category (e.g., Exemption, Deduction, Computation)
                 └── Specific Rule (e.g., Standard Deduction, 80C, STCG 15%)
```

### 1.2 Rule Statuses

| Status | Meaning |
|--------|---------|
| `ACTIVE` | Currently in force, being applied in computations |
| `SUPERSEDED` | Replaced by a newer version of the same rule |
| `PROPOSED` | Drafted, awaiting domain expert review |
| `DEPRECATED` | No longer applicable (provision removed from law) |
| `SUSPENDED` | Temporarily disabled (e.g., pending clarification from CBDT) |

### 1.3 Implemented Rules

| Rule ID | Rule Name | Section | FY | Regime | Status | Last Reviewed |
|---------|-----------|---------|-----|--------|--------|---------------|
| *No rules implemented yet — project initialization phase* | — | — | — | — | — | — |

### 1.4 Rule Implementation Queue (Priority Order)

| Priority | Rule Category | FYs | Regime | Dependencies |
|----------|--------------|-----|--------|--------------|
| P0 | Tax Slabs (Basic Rates) | FY2025-26 | Both | None |
| P0 | Surcharge Rates | FY2025-26 | Both | Tax Slabs |
| P0 | Health & Education Cess | FY2025-26 | Both | Tax Slabs |
| P0 | 87A Rebate | FY2025-26 | Both | Tax Slabs |
| P0 | Standard Deduction (Salary) | FY2025-26 | Both | Tax Slabs |
| P1 | 80C Deductions | FY2025-26 | Old | Tax Slabs |
| P1 | 80D Medical Insurance | FY2025-26 | Old | Tax Slabs |
| P1 | 80CCD NPS | FY2025-26 | Old | Tax Slabs |
| P1 | 80TTA/80TTB Interest | FY2025-26 | Old/New | Tax Slabs |
| P1 | Capital Gains (STCG 15%) | FY2025-26 | Both | Tax Slabs |
| P1 | Capital Gains (LTCG 10%/12.5%) | FY2025-26 | Both | Tax Slabs |
| P2 | All other deductions | FY2025-26 | Old | Tax Slabs |
| P2 | Capital Gains exemptions (54, 54EC, 54F) | FY2025-26 | Both | Capital Gains |
| P3 | Set-off and carry forward | FY2025-26 | Both | All income heads |
| P3 | Agricultural income integration | FY2025-26 | Both | Tax Slabs |
| P4 | Historical FYs (2024-25, 2023-24, ...) | FY2020-25 | Both | All P0-P3 for FY2025-26 |

## 2. Rule Metadata Standard

Every rule implementation must include:

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

class RuleStatus(Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    PROPOSED = "PROPOSED"
    DEPRECATED = "DEPRECATED"
    SUSPENDED = "SUSPENDED"

@dataclass(frozen=True)
class RuleMetadata:
    rule_id: str                        # Unique identifier, e.g., "TAX-SLAB-FY2025-26-OLD-01"
    rule_name: str                      # Human-readable name
    section: str                        # Legal provision, e.g., "Section 115BAC"
    subsection: Optional[str]           # e.g., "(1A)"
    financial_year: str                 # e.g., "FY2025-26"
    assessment_year: str                # e.g., "AY2026-27"
    regime: str                         # "OLD_REGIME", "NEW_REGIME", "BOTH"
    itr_types: list[str]                # ["ITR-1", "ITR-2", ...] or ["ALL"]
    income_head: str                    # "SALARY", "CAPITAL_GAINS", etc.
    effective_from: date
    effective_until: Optional[date]     # None if still active
    finance_act: str                    # e.g., "Finance Act 2025"
    notification_number: Optional[str]
    supersedes: Optional[str]           # rule_id of previous version
    superseded_by: Optional[str]        # rule_id of newer version
    status: RuleStatus
    conditions: list[str]               # Human-readable conditions for applicability
    exceptions: list[str]               # Known exceptions
    cross_references: list[str]         # Related rule_ids
    domain_reviewed_by: Optional[str]   # Domain expert name
    domain_reviewed_date: Optional[date]
    test_ids: list[str]                 # IDs of tests covering this rule
    last_updated: date
```

## 3. Rule Dependencies

### 3.1 Dependency Rules

1. **No Circular Dependencies:** Rule A must not depend on Rule B if Rule B depends on Rule A
2. **Explicit Ordering:** Computation order must be explicitly defined (e.g., gross income → deductions → tax → surcharge → cess)
3. **Optional Dependencies:** Some rules apply conditionally (e.g., 80C only if old regime)
4. **Conflict Resolution:** When two rules could apply, the more specific rule wins

### 3.2 Computation Pipeline (Standard Order)

```
Step 1:  Determine Residential Status
Step 2:  Compute Income under each Head
Step 2a:   Salary Income
Step 2b:   House Property Income
Step 2c:   Business/Profession Income
Step 2d:   Capital Gains
Step 2e:   Other Sources
Step 3:  Aggregate → Gross Total Income
Step 4:  Apply Chapter VI-A Deductions
Step 5:  Compute Total Income
Step 6:  Apply Tax Slabs → Tax on Total Income
Step 7:  Apply Rebate (87A)
Step 8:  Apply Surcharge (if applicable)
Step 9:  Apply Health & Education Cess
Step 10: Total Tax Liability
Step 11: Subtract TDS/TCS/Advance Tax
Step 12: Net Tax Payable / Refund
```

## 4. Rule Testing Standards

Each rule must have:

| Test Type | Minimum Count | Description |
|-----------|---------------|-------------|
| Happy Path | 2 | Rule applies normally at different values |
| Boundary Tests | 4 | Exactly at threshold, threshold-1, threshold+1, zero |
| Exception Tests | Per exception | Each condition/exception verified |
| Cross-Regime | 2 | Verify behavior difference Old vs New (if applicable) |
| Cross-Year | 2 | Verify rule only applies to its FY (if year-specific) |
| Rounding | 3 | Verify rounding behavior (0.49 down, 0.50 up as per §288B) |

## 5. Rule Change Impact Analysis

When a rule is modified:

```
IMPACT ANALYSIS CHECKLIST:
□ Which ITR types are affected?
□ Which financial years are affected?
□ Does this rule supersede an existing rule?
□ Are there downstream rules that depend on this rule's output?
□ Do any tests need to be updated?
□ Does the audit trail format change?
□ Does any explanation text need updating?
□ Does the regime optimizer logic need updating?
□ Are there any transitional provisions to implement?
```

---

## Session Log

| Date | Session ID | Changes Made | Agent |
|------|-----------|--------------|-------|
| 2026-07-05 | INIT | Tax rules memory initialized. Rule catalog and metadata standards defined. | Architect |

---

*This file is the inventory of all tax rules. Every rule implemented in code must be registered here first.*
