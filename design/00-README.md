# TaxStox — Design Reference

> **Product:** AI-Powered Indian Income Tax Assistant
> **Version:** 1.0
> **Date:** 2026-06-29
> **Status:** Design reference for visual implementation

---

## ⚠️ IMPORTANT

**The definitive build specification is now [docs/MASTER_PLAN.md](../docs/MASTER_PLAN.md).**

This `design/` directory contains visual references (design tokens, HTML prototypes) and
some architectural exploration. The documents numbered 02-27 below were PLANNED but
never created. Only 01, 04, and 09 exist — and 09 (multi-agent architecture) has been
**deprecated** in favor of the cost-aware modular monolith in MASTER_PLAN.md.

---

## What Exists (Visual Reference Only)

### Design System
- **[design-system/DESIGN.md](design-system/DESIGN.md)** — Design tokens (colors, typography, spacing, elevation, components)
  - Primary: ITD deep blue #003178 | Accent: Orange #F57C00 | Success: Green #166534
  - Typography: Hanken Grotesk (headings), Inter (body), JetBrains Mono (data)

### HTML Prototypes (Visual Reference)
These are UI mockups showing the intended user experience:
- `landing-page/code.html` — Hero + features
- `auth-signup/code.html` — Sign up with PAN validation
- `secure-upload-portal/code.html` — Drag-drop PDF upload
- `smart-questionnaire/code.html` — Wizard-style Q&A
- `tax-summary-review/code.html` — Regime comparison + deduction breakdown
- `post-export-instructions/code.html` — 8-step ITR portal guide
- `error-edge-cases/code.html` — 15 error states
- `user-dashboard/code.html` — Filing history + stats

### Existing Docs

| # | Document | Status |
|---|----------|--------|
| 01 | [Product & Functional Requirements](01-product-requirements.md) | ✅ Exists |
| 04 | [Information Architecture](04-information-architecture.md) | ✅ Exists (15+ pages planned, 3 actually built) |
| 09 | [Multi-Agent Architecture](09-multi-agent-architecture.md) | ⛔ DEPRECATED — see MASTER_PLAN.md |
| 02-03, 05-08, 10-27 | All other planned docs | ❌ Never created |

---

## Key Metrics (from PRD)

| Metric | Target |
|--------|--------|
| Time to complete filing | < 2 minutes |
| Questions per filing session | ≤ 5 |
| Refund accuracy vs. CA-prepared | ±₹500 |
| Document processing time | < 15s per PDF |
| PII retention | Purged 24h after generation |

---

## Glossary

| Term | Definition |
|------|------------|
| AIS | Annual Information Statement (Form 26AS successor) |
| AY | Assessment Year |
| FY | Financial Year (Apr 1 – Mar 31) |
| ITD | Income Tax Department of India |
| ITR | Income Tax Return |
| PAN | Permanent Account Number (10-char ID) |
| TAN | Tax Deduction Account Number (employer ID) |
| TDS | Tax Deducted at Source |

---

*For the complete build specification, see [docs/MASTER_PLAN.md](../docs/MASTER_PLAN.md).*
