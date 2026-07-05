# Release Strategy

> **Date:** 2026-07-05
> **Principle:** Every wave ends with a deployable, tested release. Platform never broken.

---

## 1. Release Cadence

| Cadence | Trigger | Scope |
|---------|---------|-------|
| **Continuous** | Every PR merge to `main` | Bug fixes, minor improvements |
| **Wave Release** | Wave exit criteria met | Full wave capabilities |
| **Emergency** | P0 incident | Hotfix only |

## 2. Wave Release Process

```
WAVE DEVELOPMENT → WAVE EXIT GATES → STAGING DEPLOY → SMOKE TEST → PRODUCTION DEPLOY
                                                                        │
                                                          ┌─────────────┘
                                                          │
                                                    CANARY (5% traffic, 24h)
                                                          │
                                                    FULL ROLLOUT (100%)
                                                          │
                                                    MONITORING (72h intensive)
```

## 3. Feature Flags

All new capabilities deployed behind feature flags:

| Flag Type | Example | Rollout |
|-----------|---------|---------|
| **Boolean** | `ENABLE_ITR3_BUILDER` | Per-tenant |
| **Percentage** | `OCR_PIPELINE_ROLLOUT` | 5% → 25% → 100% |
| **User Segment** | `CA_FIRM_EARLY_ACCESS` | Specific tenants |

## 4. Environment Strategy

| Environment | Purpose | Deploy Trigger |
|-------------|---------|----------------|
| **Development** | Local development | Manual |
| **CI** | Automated tests | Every PR |
| **Staging** | Pre-production validation | Wave exit |
| **Production** | Live users | Post-staging smoke test |
| **DR** | Disaster recovery | Continuous replication |

## 5. Canary Deployment (M11+)

Applied to M11 (Production Hardening) and sustained thereafter:
- 5% traffic for 24 hours
- Monitor: error rate, p95 latency, tax computation correctness
- Auto-rollback if error rate exceeds baseline by 2x
- Graduated to 100% after 24h clean

## 6. Emergency Rollback

| Trigger | Response |
|---------|----------|
| Tax computation mismatch detected | **Immediate rollback.** Golden vector comparison in CI prevents most; runtime detection as safety net. |
| Error rate > 5% | Rollback + investigate |
| Security incident | Rollback + security incident response |

---

*End of Release Strategy v1.0*
