# Enterprise Gap Analysis — Navigation Index

The Enterprise Gap Analysis phase (2026-07-05) produced five diagnostic artifacts comparing the current platform against the 148-capability Enterprise Capability Model.

## Canonical Diagnostic Documents

All documents live in the canonical architecture directory:

| Diagnostic | Document | Summary |
|-----------|----------|---------|
| **Gap Report** | [EnterpriseGapReport.md](../architecture/EnterpriseGapReport.md) | 148 capabilities assessed. 6 fully implemented, 28 partial, 84 not implemented, 30 UNKNOWN. 42 Critical gaps. |
| **Health Score** | [ArchitectureHealthScore.md](../architecture/ArchitectureHealthScore.md) | Overall **31/100**. 16 category scores with justifications. |
| **Maturity Matrix** | [DomainMaturityMatrix.md](../architecture/DomainMaturityMatrix.md) | 15 bounded contexts, **14%** overall coverage. BC3 highest at 37%. |
| **Debt Heatmap** | [TechnicalDebtHeatmap.md](../architecture/TechnicalDebtHeatmap.md) | **64 debt items** across 9 categories. Architecture debt dominates. |
| **Risk Matrix** | [EnterpriseRiskMatrix.md](../architecture/EnterpriseRiskMatrix.md) | **15 risks**. 4 Critical, 5 High. Top risk: FY2026 obsolescence. |

## Key Findings

- **Architecture Health:** 31/100 (Grade D)
- **Domain Coverage:** 14% of target capabilities implemented
- **Critical Gaps:** No rule-engine separation, single FY only, zero audit trail, zero tests, no multi-tenancy
- **Top Risks:** FY2026 obsolescence (95% probability), DPDP Act non-compliance, security breach from plaintext PII

## Related Documents

- [Enterprise Capability Model](../architecture/ENTERPRISE_CAPABILITY_MODEL.md) — FROZEN target measured against
- [Architecture Recovery Report](../architecture/ARCHITECTURE_RECOVERY_REPORT.md) — Current state used as baseline
