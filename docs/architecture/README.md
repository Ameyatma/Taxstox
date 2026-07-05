# Enterprise Architecture — Canonical Artifacts

This directory is the **single canonical location** for all enterprise architecture documents. Every architecture artifact has exactly one authoritative copy, and it lives here.

## Target Architecture (FROZEN)

| Document | Description |
|----------|-------------|
| [ENTERPRISE_CAPABILITY_MODEL.md](ENTERPRISE_CAPABILITY_MODEL.md) | Target — Domains 1-5 (48 capabilities) |
| [ENTERPRISE_CAPABILITY_MODEL_PART2.md](ENTERPRISE_CAPABILITY_MODEL_PART2.md) | Target — Domains 6-9 (38 capabilities) |
| [ENTERPRISE_CAPABILITY_MODEL_PART3.md](ENTERPRISE_CAPABILITY_MODEL_PART3.md) | Target — Domains 10-16 (49 capabilities) |
| [ENTERPRISE_CAPABILITY_MODEL_PART4.md](ENTERPRISE_CAPABILITY_MODEL_PART4.md) | Target — Domains 17-20 + Bounded Contexts (13 capabilities) |

**⚠️ The Enterprise Capability Model is FROZEN. Do not modify.**

## Current State

| Document | Description |
|----------|-------------|
| [ARCHITECTURE_RECOVERY_REPORT.md](ARCHITECTURE_RECOVERY_REPORT.md) | Evidence-backed current state from 42-module audit |

## Gap Analysis & Diagnostics

| Document | Description |
|----------|-------------|
| [EnterpriseGapReport.md](EnterpriseGapReport.md) | 148-capability gap analysis |
| [ArchitectureHealthScore.md](ArchitectureHealthScore.md) | Overall architecture health: 31/100 |
| [DomainMaturityMatrix.md](DomainMaturityMatrix.md) | 15 bounded contexts, 14% coverage |
| [TechnicalDebtHeatmap.md](TechnicalDebtHeatmap.md) | **Canonical debt register** — 64 items |
| [EnterpriseRiskMatrix.md](EnterpriseRiskMatrix.md) | 15 enterprise risks |

## Repository Consolidation (Historical)

| Document | Description |
|----------|-------------|
| [RepositoryConsolidationReport.md](RepositoryConsolidationReport.md) | Discovery report |
| [RepositoryConsolidationPlan.md](RepositoryConsolidationPlan.md) | Execution plan |
| [CONSOLIDATION_COMPLETE.md](CONSOLIDATION_COMPLETE.md) | Final consolidation report |
| [GitAndDocAudit.md](GitAndDocAudit.md) | Git + documentation hygiene audit |
| [CanonicalDocumentLayout.md](CanonicalDocumentLayout.md) | Documentation topology design |

## Navigation

- **Chronological:** See [docs/recovery/](../recovery/README.md) and [docs/gap-analysis/](../gap-analysis/README.md)
- **Governance:** See [docs/governance/](../governance/README.md)
- **Agent bootstrap:** [CLAUDE.md](../../CLAUDE.md)
