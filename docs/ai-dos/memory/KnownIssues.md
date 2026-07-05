# Known Issues Memory

> **Purpose:** Central registry of all known bugs, issues, limitations, and their resolution status.
> **Updated By:** Architect Agent — every session.
> **Last Updated:** 2026-07-05
> **Session ID:** INIT
> **Cross-Refs:** [TechnicalDebt.md](TechnicalDebt.md), [CompletedFeatures.md](CompletedFeatures.md)

---

## 1. Issue Registry

### 1.1 Severity Definitions

| Severity | Definition | Response Time | Resolution Time |
|----------|-----------|---------------|-----------------|
| **P0 — Critical** | System down, data loss, security breach, incorrect tax computation affecting all users | Immediate (any hour) | 4 hours |
| **P1 — High** | Major feature broken, incorrect tax in specific scenario, significant performance degradation | 2 hours (business hours) | 24 hours |
| **P2 — Medium** | Feature partially broken, minor incorrect behavior, workaround exists | 24 hours | 1 sprint |
| **P3 — Low** | Cosmetic issue, minor annoyance, edge case affecting < 1% of users | 1 week | 2 sprints |
| **P4 — Trivial** | Typo, formatting, non-functional improvement | Next sprint | When capacity allows |

### 1.2 Issue Statuses

| Status | Meaning |
|--------|---------|
| `OPEN` | Identified, not yet being worked on |
| `INVESTIGATING` | Root cause being determined |
| `IN_PROGRESS` | Fix being implemented |
| `IN_REVIEW` | Fix implemented, under review |
| `RESOLVED` | Fix merged and deployed |
| `VERIFIED` | Fix confirmed by reporter or automated test |
| `CLOSED` | No further action needed |
| `WONT_FIX` | Decided not to fix (with rationale) |
| `CANNOT_REPRODUCE` | Unable to reproduce the issue |
| `DUPLICATE` | Duplicate of another issue |

### 1.3 Open Issues

| Issue ID | Severity | Module | Title | Reported | Status | Owner |
|----------|----------|--------|-------|----------|--------|-------|
| ISS-001 | P0 | All | FY2026 obsolescence — entire platform hardcoded for FY2025-26 | 2026-07-05 | OPEN | Chief Architect |
| ISS-002 | P0 | All | Zero automated tests — no safety net for any change | 2026-07-05 | OPEN | Tech Lead |
| ISS-003 | P0 | Security | PAN stored as plaintext in database; dev JWT secret hardcoded in source | 2026-07-05 | OPEN | Security Lead |
| ISS-004 | P0 | Auth | No RBAC/authorization — any authenticated user has full access | 2026-07-05 | OPEN | Chief Architect |
| ISS-005 | P0 | Compliance | DPDP Act 2023 compliance entirely absent — no consent management | 2026-07-05 | OPEN | Chief Architect |
| ISS-006 | P1 | Architecture | Dual optimizer implementations (v1+v2) causing maintenance duplication | 2026-07-05 | OPEN | Tech Lead |
| ISS-007 | P1 | Architecture | Circular dependency via lazy import in regime_optimizer_v2.py:334 | 2026-07-05 | OPEN | Tech Lead |
| ISS-008 | P1 | Infrastructure | In-memory sessions prevent horizontal scaling; lost on server restart | 2026-07-05 | OPEN | DevOps Lead |
| ISS-009 | P1 | Operations | No structured logging, metrics, monitoring, or alerting | 2026-07-05 | OPEN | DevOps Lead |
| ISS-010 | P1 | Security | PDF passwords logged in plaintext — PAN-based passwords exposed | 2026-07-05 | OPEN | Security Lead |

### 1.4 Recently Resolved Issues

| Issue ID | Severity | Module | Title | Resolved | Resolution |
|----------|----------|--------|-------|----------|------------|
| *No resolved issues yet* | — | — | — | — | — |

## 2. Issue Template

When logging a new issue:

```markdown
### Issue: [Brief Title]
- **Issue ID:** ISS-XXXX
- **Severity:** P0/P1/P2/P3/P4
- **Module:** [Affected Module]
- **Reported:** YYYY-MM-DD
- **Reported By:** [Agent/Human]
- **Status:** OPEN

**Description:**
[What is the problem? What is the expected behavior? What is the actual behavior?]

**Reproduction Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3 — what goes wrong?]

**Impact:**
- Users affected: [Estimate]
- Financial impact: [If any — incorrect tax computation?]
- Data impact: [If any — data loss/corruption?]

**Workaround:**
[Is there a temporary workaround while the fix is being developed?]

**Root Cause (to be filled during investigation):**
[What caused this issue?]

**Fix (to be filled during implementation):**
[What was changed to fix this issue?]

**Prevention (to be filled after resolution):**
[What process/tool/test change would have prevented this issue?]
```

## 3. Tax Computation Issues (Special Handling)

Issues affecting tax computation correctness follow an escalated process:

```
TAX COMPUTATION ISSUE REPORTED:
│
├── IMMEDIATE: Confirm if the issue affects currently filed returns
│   └── If YES → P0; escalate to Domain Expert immediately
│
├── WITHIN 2 HOURS: Domain Expert confirms correct tax treatment
│   └── If system is wrong → Fix immediately; notify affected users
│   └── If system is correct → Document with legal provision reference
│
├── WITHIN 24 HOURS: Root cause analysis
│   └── Was this a rule implementation error?
│   └── Was this a rule interpretation error?
│   └── Was this an engine/algorithm error?
│   └── Was this an input data error?
│
├── WITHIN 1 SPRINT: Prevention
│   └── Add test case for the specific scenario
│   └── Add validation to catch similar scenarios
│   └── Review related rules for similar errors
│   └── Update domain expert review checklist
│
└── POST-RESOLUTION:
    └── Update KnownIssues.md with root cause and prevention
    └── Update BusinessRules.md if rule interpretation changed
    └── Add to regression test suite
```

## 4. Issue Metrics (Tracked Per Sprint)

| Metric | Current | Target | Trend |
|--------|---------|--------|-------|
| Open P0 | 0 | 0 | — |
| Open P1 | 0 | ≤ 2 | — |
| Open P2 | 0 | ≤ 10 | — |
| Open P3 | 0 | ≤ 20 | — |
| Total Open | 0 | ≤ 30 | — |
| Mean Time to Resolve (P0) | N/A | < 4 hours | — |
| Mean Time to Resolve (P1) | N/A | < 24 hours | — |
| Mean Time to Resolve (P2) | N/A | < 1 sprint | — |
| Issue Reopen Rate | 0% | < 5% | — |

## 5. Known Limitations (By Design)

Some limitations are by design and are not bugs. They are tracked here so they are not re-reported:

| Limitation ID | Description | Reason | Revisit When |
|---------------|-------------|--------|--------------|
| *No known limitations yet* | — | — | — |

---

## Session Log

| Date | Session ID | Changes Made | Agent |
|------|-----------|--------------|-------|
| 2026-07-05 | INIT | Known issues memory initialized. | Architect |

---

*This file is the bug tracker. Every issue, every resolution, every lesson learned lives here.*
