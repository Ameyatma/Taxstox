# CLAUDE.md — TaxStox ITR Platform

> **Repository:** D:\IT_Returns
> **Release:** v0.10.0-alpha (Internal Alpha)
> **Purpose:** Enterprise AI-Powered Indian Tax Intelligence Platform
> **This file:** Bootstrap for all AI agents. Read before any action.

---

## Mandatory Reading Order

Every AI agent MUST read these documents in this exact order before taking any action:

1. **[docs/governance/00-Constitution.md](docs/governance/00-Constitution.md)** — Supreme governance. Non-negotiable.
2. **[docs/ai-dos/memory/README.md](docs/ai-dos/memory/README.md)** — Architect session protocol.
3. **[docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md](docs/architecture/ENTERPRISE_CAPABILITY_MODEL.md)** — FROZEN target architecture. 148 capabilities. 20 domains.
4. **[docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md](docs/architecture/ARCHITECTURE_RECOVERY_REPORT.md)** — Current architecture state. 42-module audit.
5. **[docs/architecture/ProductReadinessReview.md](docs/architecture/ProductReadinessReview.md)** — Authoritative assessment of production readiness.
6. **[docs/architecture/ProductionReadinessRemediationRoadmap.md](docs/architecture/ProductionReadinessRemediationRoadmap.md)** — ACTIVE execution plan. 6 waves (PR1-PR6).

---

## Authority Hierarchy

```
1. Constitution                    ← SUPREME
2. Chief Architect                 ← Architecture governance
3. Enterprise Capability Model     ← FROZEN target
4. Architecture Recovery Report    ← Current state
5. Enterprise Gap Report           ← Diagnostics
6. Enterprise Modernization Roadmap ← FROZEN (COMPLETE)
7. Product Engineering Roadmap     ← FROZEN (COMPLETE)
8. Product Readiness Review        ← AUTHORITATIVE ASSESSMENT
9. Production Readiness Remediation ← ACTIVE EXECUTION PLAN
10. Engineering Standards
11. Source Code
12. Project Memory
```

---

## Current State

| Attribute | Value |
|-----------|-------|
| Release | v0.10.0-alpha |
| Stage | Internal Alpha |
| Tests | 407 passing, 0 failures |
| Golden vectors | 9, unchanged |
| Architecture health | ~55/100 |
| Programs complete | Enterprise Modernization (M0-M11), Product Engineering (P1-P7) |
| Current PRRP wave | PR1 complete. PR2 next. |
| Production readiness | Ready for Internal Alpha |

---

## Quick Reference

```
Constitution violation?      → Stop. Escalate.
Architecture decision?        → PRRP defines the scope. No new ADRs for alpha.
Tax rule change?             → Domain expert review required.
New dependency?              → Must trace to PRRP finding.
Found a bug?                 → Register in KnownIssues.md
Made a decision?             → Log in Decisions.md
Feature complete?            → PRRP waves only. No new features.
Session ended?               → Update HANDOFF.md §1.
```
