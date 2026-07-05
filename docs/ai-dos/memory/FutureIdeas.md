# Future Ideas Memory

> **Purpose:** Backlog of ideas, enhancements, and features that are not yet scheduled but worth remembering.
> **Updated By:** Architect Agent — every session when new ideas emerge.
> **Last Updated:** 2026-07-05
> **Session ID:** INIT
> **Cross-Refs:** [CompletedFeatures.md](CompletedFeatures.md), [Architecture.md](Architecture.md), [Decisions.md](Decisions.md)

---

## 1. Idea Classification

| Tag | Meaning | When to Promote |
|-----|---------|-----------------|
| `HORIZON-1` | Likely within next 6 months | Next planning cycle |
| `HORIZON-2` | Likely within 6-18 months | When H1 items complete |
| `HORIZON-3` | 18+ months away, speculative | Revisit quarterly |
| `MOONSHOT` | Big, uncertain, potentially transformative | Annual strategy review |
| `TAX_LAW` | Triggered by expected tax law change | When Finance Act/Notification published |
| `USER_REQUEST` | Requested by users/stakeholders | When demand validated |

## 2. Idea Registry

### 2.1 Horizon 1 (Next 6 Months — After Core Platform)

| Idea ID | Title | Description | Value | Effort | Priority |
|---------|-------|-------------|-------|--------|----------|
| *None yet — core platform must be built first* | — | — | — | — | — |

### 2.2 Horizon 2 (6-18 Months)

| Idea ID | Title | Description | Value | Effort | Priority |
|---------|-------|-------------|-------|--------|----------|
| *None yet* | — | — | — | — | — |

### 2.3 Horizon 3 (18+ Months)

| Idea ID | Title | Description | Value | Effort | Priority |
|---------|-------|-------------|-------|--------|----------|
| *None yet* | — | — | — | — | — |

### 2.4 Moonshots

| Idea ID | Title | Description | Value | Feasibility |
|---------|-------|-------------|-------|-------------|
| *None yet* | — | — | — | — |

### 2.5 Tax Law Triggered (Expected Future Requirements)

| Idea ID | Trigger | Description | Expected FY | Preparation |
|---------|---------|-------------|-------------|-------------|
| TAX-IDEA-001 | DPDP Act Rules | Data principal rights: consent management, data portability, right to erasure | TBD | Architecture supports from day 1 |
| TAX-IDEA-002 | ITD e-filing 3.0 | New API integration for direct ITR submission | TBD | API abstraction layer designed for swap |
| TAX-IDEA-003 | DTC (Direct Tax Code) | If enacted, major overhaul of tax computation | Unknown | Monitor; modular architecture can adapt |

## 3. Idea Template

When logging a new idea:

```markdown
### IDEA-XXXX: [Title]

**Tag:** [HORIZON-1 | HORIZON-2 | HORIZON-3 | MOONSHOT | TAX_LAW | USER_REQUEST]
**Submitted:** YYYY-MM-DD
**Submitted By:** [Agent/Human]
**Value:** [HIGH | MEDIUM | LOW]
**Effort:** [LARGE | MEDIUM | SMALL]
**Priority:** [P1 | P2 | P3 | P4]

**Description:**
[What is the idea? 2-4 sentences.]

**Why This Matters:**
[What problem does it solve? For whom?]

**Dependencies:**
- [What needs to exist before this can be built?]

**Risks:**
- [What could go wrong? What's uncertain?]

**Next Step for Promotion:**
[What needs to happen before this idea becomes a planned feature?]
```

## 4. Idea Promotion Process

```
IDEA PROMOTION:

1. REVIEW: Quarterly review of all ideas
2. VALIDATE: User research, market analysis, legal check (for tax ideas)
3. ESTIMATE: Rough effort estimate (S/M/L)
4. PRIORITIZE: Against current roadmap and other ideas
5. DECIDE:
   ├── PROMOTE → Move to roadmap; create feature specification
   ├── KEEP → Retain in Future Ideas for next review
   └── CLOSE → Idea is no longer relevant; document why
6. FEEDBACK: Notify idea submitter of outcome
```

## 5. Ideas by Module (for Reference During Module Work)

| Module | Future Ideas |
|--------|-------------|
| `core-domain` | — |
| `tax-year-registry` | — |
| `rule-engine` | Rete algorithm for complex rule chains; rule conflict detection; rule visualization |
| `tax-rules-*` | Auto-generation of rules from structured Finance Act data; rule comparison across FYs |
| `itr-schema` | Schema auto-generation from CBDT JSON schemas; visual form builder |
| `computation-engine` | Parallel computation for Old vs New; incremental recomputation on answer change |
| `audit-trail` | Blockchain-based immutability proof; audit trail export for ITD scrutiny |
| `explain-engine` | Multi-language explanations; video explanations; CA-focused technical explanations |
| `validation-engine` | ML-based anomaly detection; cross-taxpayer pattern analysis |
| `regime-optimizer` | Multi-year optimization; family-unit optimization; break-even analysis |
| `user-api` | GraphQL for flexible queries; webhook notifications; bulk filing for CAs |
| `document-parser` | Direct ITD API pull (Form 26AS, AIS); ML-based handwriting recognition; multi-language OCR |

## 6. Parking Lot (Quick Capture)

Ideas that haven't been fully formed yet. Review weekly and either promote to the registry or discard.

| Quick Idea | Captured | By |
|------------|----------|-----|
| *None yet* | — | — |

---

## Session Log

| Date | Session ID | Changes Made | Agent |
|------|-----------|--------------|-------|
| 2026-07-05 | INIT | Future ideas memory initialized. 3 tax-law-triggered ideas pre-registered. | Architect |

---

*This file is the idea garden. Some seeds grow into features; some stay seeds. All are worth remembering.*
