# Architecture Recovery — Navigation Index

The Architecture Recovery phase (2026-07-05) produced a comprehensive, evidence-backed documentation of the current platform state based on a 42-module source code audit of the TaxStox ITR platform.

## Canonical Document

**[ARCHITECTURE_RECOVERY_REPORT.md](../architecture/ARCHITECTURE_RECOVERY_REPORT.md)**

The report covers:
- Current architecture style (modular monolith)
- Complete module catalogue (42 Python files)
- Dependency analysis with import graph
- Domain model recovery (entities, value objects, aggregates)
- Business flow documentation (upload → parse → classify → optimize → build → validate)
- Data flow and tax computation flow
- Document processing flow
- Validation flow
- Existing strengths (12 identified) and weaknesses (15 identified)
- Technical debt register (15 items)
- Architectural debt register (8 items)
- Duplicated logic (6 instances)
- Missing abstractions (9 identified)
- Scalability, security, and testing gaps

## Related Documents

- [Enterprise Capability Model](../architecture/ENTERPRISE_CAPABILITY_MODEL.md) — Target state (FROZEN)
- [Enterprise Gap Report](../architecture/EnterpriseGapReport.md) — Gap analysis using recovery findings
- [Architecture Health Score](../architecture/ArchitectureHealthScore.md) — 31/100

## Phase Context

Architecture Recovery is Phase 1 of the enterprise architecture process:
1. **Architecture Recovery** ← You are here
2. Enterprise Capability Modelling (target definition)
3. Enterprise Gap Analysis
4. Modernization Roadmap
