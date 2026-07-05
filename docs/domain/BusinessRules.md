# Business Rules Memory

> **Purpose:** Repository of all business rules governing the tax platform.
> **Updated By:** Architect Agent — every session when rules change.
> **Last Updated:** 2026-07-05
> **Session ID:** INIT
> **Cross-Refs:** [FinanceAct.md](FinanceAct.md), [TaxRules.md](TaxRules.md), [Decisions.md](Decisions.md)

---

## 1. Rule Categories

| Category | Description | Source | Volatility |
|----------|-------------|--------|------------|
| **Tax Slabs** | Income brackets and rates per regime per FY | Finance Act | Annual |
| **Deductions** | Chapter VI-A deductions (80C, 80D, etc.) | Income Tax Act + Finance Act | Rare |
| **Exemptions** | Income exemptions (10-series) | Income Tax Act | Rare |
| **Surcharge** | Additional tax on high income | Finance Act | Annual |
| **Cess** | Health and Education Cess | Finance Act | Rare |
| **Rebates** | 87A rebate for low income | Finance Act | Annual (threshold) |
| **Capital Gains** | Holding period, indexation, exemptions | Income Tax Act + Notifications | Periodic |
| **TDS** | Tax deducted at source rates | Income Tax Act + Notifications | Periodic |
| **Advance Tax** | Installment schedule and computation | Income Tax Act | Rare |
| **ITR Applicability** | Which ITR form applies to whom | CBDT Notifications | Annual |
| **AIS Reconciliation** | Rules for reconciling AIS with taxpayer data | CBDT Guidelines | Periodic |
| **Residential Status** | Determination of residential status | Income Tax Act §6 | Rare |
| **Set-off and Carry Forward** | Rules for setting off losses | Income Tax Act | Rare |
| **Old vs New Regime** | Conditions, restrictions, lock-in rules | Finance Act | Annual |

## 2. Critical Business Rules

### 2.1 Regime Selection Rules

```
OLD REGIME (pre-115BAC):
- All Chapter VI-A deductions available
- Standard deduction: Rs. 50,000 (salaried)
- Various exemptions apply
- Surcharge rates as per applicable slab
- Available to all taxpayers
- Once opted for NEW REGIME, can switch back (except for business income)

NEW REGIME (115BAC):
- Lower tax rates
- Most deductions NOT available (some exceptions added per Finance Act)
- Standard deduction: Rs. 75,000 (FY2025-26 onwards, salaried)
- Default regime from FY2023-24
- Business income: once opted, cannot revert (specific conditions)
- Surcharge capped at 25% (vs 37% in old regime for highest bracket)
```

### 2.2 Residential Status Determination

```
Resident and Ordinarily Resident (ROR):
- In India ≥ 182 days in the FY, OR
- In India ≥ 60 days in the FY AND ≥ 365 days in preceding 4 FYs
- (60 days replaced by 182 days for Indian citizens/PIO with India income > 15 lakh)

Resident but Not Ordinarily Resident (RNOR):
- Resident, but:
  - Non-resident in India in 9 out of 10 preceding FYs, OR
  - In India ≤ 729 days in preceding 7 FYs

Non-Resident (NR):
- Does not meet residence conditions
- Only India-sourced income taxable

Deemed Resident (new from FY2020-21):
- Indian citizen/PIO not liable to tax in any other country
- India income > 15 lakh
- Deemed resident but RNOR status
```

### 2.3 ITR Form Applicability

```
ITR-1 (SAHAJ):
- Resident individual
- Total income ≤ 50 lakh
- Income from: Salary, One house property, Other sources
- NOT for: Director, Listed shares, Capital gains, Business income, Foreign income/assets

ITR-2:
- Individual/HUF
- NOT having business/profession income
- CAN have: Capital gains, Foreign income/assets, Multiple house properties

ITR-3:
- Individual/HUF
- Having business/profession income
- CAN have: Everything ITR-2 covers plus business income

ITR-4 (SUGAM):
- Resident individual/HUF/Firm (not LLP)
- Total income ≤ 50 lakh
- Presumptive taxation scheme (44AD, 44ADA, 44AE)
- NOT for: Capital gains > taxable amount, Director, Listed shares

[ITR-5 through ITR-7: Entities — deferred to Phase 2]
```

## 3. Income Heads

| Head | Sections | Key Concepts |
|------|----------|--------------|
| **Salary** | §15-17 | Gross salary, perquisites, allowances, standard deduction, entertainment allowance, professional tax |
| **House Property** | §22-27 | Let out, self-occupied, deemed let out, GAV, municipal taxes, standard deduction (30%), interest deduction (2 lakh/ full), vacancy allowance |
| **Business/Profession** | §28-44DB | Presumptive (44AD/44ADA/44AE), regular books, depreciation, disallowances, audit requirements |
| **Capital Gains** | §45-55A | Short term (listed < 12mo, unlisted < 24mo, immovable < 24mo), long term, indexation, exemptions (54/54EC/54F), listed vs unlisted securities |
| **Other Sources** | §56-59 | Interest (savings, FD, bonds), dividends, gifts, winnings, family pension |

## 4. Deduction Rules (Chapter VI-A)

| Section | Category | Limit (FY2025-26) | Notes |
|---------|----------|-------------------|-------|
| 80C | Investments/Expenditure | 1,50,000 | PF, PPF, LIC, ELSS, NSC, tuition fees, home loan principal, stamp duty, SSY, SCSS, 5-year FD |
| 80CCC | Pension (annuity) | Part of 80C limit | Annuity from insurer to pension fund |
| 80CCD(1) | NPS (employee) | Part of 80C limit | Lower of: 10% salary / 20% GTI, or 1,50,000 |
| 80CCD(1B) | NPS (additional) | 50,000 | Over and above 80C limit |
| 80CCD(2) | NPS (employer) | 10% salary (14% for CG) | No upper limit; part of salary deductions |
| 80D | Medical Insurance | 25,000 / 50,000 (senior) | Self+family+parents; preventive checkup (5,000 included) |
| 80DD | Disabled Dependent | 75,000 / 1,25,000 | Normal / Severe disability |
| 80DDB | Medical Treatment | 40,000 / 1,00,000 | Specified diseases; age-based limit |
| 80E | Education Loan Interest | No limit | 8-year maximum from repayment start |
| 80EE | Home Loan Interest (first) | 50,000 | First-time buyer, loan ≤ 35L, property ≤ 50L |
| 80EEA | Home Loan Interest (affordable) | 1,50,000 | Stamp duty ≤ 45L, no other house |
| 80EEB | Electric Vehicle Loan | 1,50,000 | Loan sanctioned FY2020-23 |
| 80G | Donations | 50% / 100% of donation | With or without qualifying limit |
| 80GGA | Scientific Research Donation | 100% | Not for business income |
| 80GGC | Political Donation | 100% | Not cash |
| 80TTA | Savings Account Interest | 10,000 | Individual/HUF (not senior) |
| 80TTB | Interest (Senior Citizen) | 50,000 | Deposits with banks/post office |
| 80U | Self-Disability | 75,000 / 1,25,000 | Normal / Severe disability |

**Note:** Most deductions (except 80CCD(2), 80EEA, 80EEB, 80G, etc.) NOT available under NEW REGIME.

## 5. Old vs New Regime Optimization Rules

```
Comparison Algorithm:
1. Compute total income under OLD REGIME (with all eligible deductions)
2. Compute total income under NEW REGIME (with limited deductions)
3. Apply respective tax slabs
4. Apply surcharge, cess
5. Compare final liability
6. Recommend lower liability regime

Lock-in Rules:
- Business income taxpayers: once opt for NEW, cannot revert (except once in lifetime)
- Salaried: can switch every year
- Default: NEW REGIME (from FY2023-24)
- Employer TDS: based on regime declared by employee

Special Cases:
- New Regime may be better for: young earners, fewer deductions, lower incomes
- Old Regime may be better for: high deductions (80C, home loan, NPS, insurance), higher incomes
- Break-even analysis required per taxpayer — not one-size-fits-all
```

## 6. Compliance Calendar

| Due Date | Obligation | Applies To |
|----------|-----------|------------|
| 31st July | ITR filing (non-audit) | Individuals, non-audit cases |
| 31st October | ITR filing (audit, non-transfer pricing) | Audit cases |
| 30th November | ITR filing (transfer pricing) | International transaction cases |
| 31st December | Belated/Revised return | All (revised return deadline) |
| 15th June | Advance Tax (15% of liability) | All assessees |
| 15th September | Advance Tax (45% cumulative) | All assessees |
| 15th December | Advance Tax (75% cumulative) | All assessees |
| 15th March | Advance Tax (100% cumulative) | All assessees |

---

## Session Log

| Date | Session ID | Changes Made | Agent |
|------|-----------|--------------|-------|
| 2026-07-05 | INIT | Business rules memory initialized with core rules. | Architect |

---

*This file captures business rules that govern tax computation. When the law changes, this file changes.*
