# ITR-Type Questions Decision Trees

> **Principle:** For each ITR type, the system asks only questions whose answers CANNOT be
> derived from Form 16 or AIS. Every auto-detectable fact is auto-detected. Every question
> is yes/no or a single number. The user never sees a dropdown of 80C sub-sections or a CG
> date range cell.

---

## Universal Questions (All ITR Types)

These are asked once, before any ITR-type-specific questions:

| # | Question | Auto-Pre-Fill | Why Ask |
|---|---|---|---|
| 1 | **PAN** | — | Core identifier |
| 2 | **Date of Birth** | — | AIS password derivation + age-based rules (senior citizen slabs, 80D limits) |

---

## ITR-1 (Sahaj)

**Eligibility (auto-detected):**
- Salary income ✓ (from Form 16)
- Interest income ✓ (from AIS)
- One house property (if SFT-001 in AIS)
- NO capital gains (verified from AIS)
- Total income ≤ ₹50L

### Questions (Maximum 4)

```
Q1: Do you pay rent for your accommodation?
    → No  (skip to Q2)
    → Yes → How much per month? [₹_________]
          → City category?
              ○ Metro (Mumbai, Delhi, Kolkata, Chennai, Bangalore, Hyderabad)
              ○ Non-Metro
          → Is annual rent > ₹1,00,000?
              ○ Yes → Landlord PAN required [__________]
              ○ No

Q2: Do you have health insurance?
    → No  (skip to Q3)
    → Yes → Premium for self + spouse + children? [₹_________]
          → Premium for parents?
              ○ Not applicable
              ○ Parents < 60 years: [₹_________]
              ○ Parents ≥ 60 years (senior citizen): [₹_________]
          → Any preventive health checkup? [₹_________] (max ₹5,000)

Q3: Any investments beyond what appears in your Form 16?
    → No  (skip to Q4)
    → Yes → PPF contribution? [₹_________]
          → ELSS mutual funds? [₹_________]
          → LIC premium? [₹_________]
          → Tax-saver FD (5-year)? [₹_________]
          → NSC purchased? [₹_________]
          → Children's tuition fees? [₹_________]
          → Home loan principal repayment? [₹_________]
          → Sukanya Samriddhi? [₹_________]
    (System automatically caps total at ₹1,50,000 for 80C)

Q4: Do you have a home loan?
    → No  (skip)
    → Yes → Is the property self-occupied or let-out?
          → Interest paid this year? [₹_________]
          → (System auto-applies ₹2,00,000 limit for self-occupied)
```

### Auto-Detected (No Questions)

| Data | Source |
|---|---|
| Salary breakup | Form 16 Annexure |
| TDS on salary | Form 16 Part A |
| Savings bank interest | AIS SFT-016(SB) |
| Term deposit interest | AIS SFT-016(TD) |
| EPF contribution | Form 16 / AIS Annexure II |
| Standard deduction | Auto-applied (₹50K old, ₹75K new) |
| Professional tax | Form 16 Part B |
| Employer NPS (80CCD(2)) | Form 16 Part B |
| Any other TDS (FDs, etc.) | AIS Part B1 |
| Previous year refund | AIS Part B4 |

---

## ITR-2

**Eligibility (auto-detected):**
- Salary ✓
- Capital gains from shares, MFs, ETFs ✓ (AIS SFT-17, SFT-18)
- No business income
- May have foreign assets/income

### Questions (Maximum 5)

```
Q1: Do you pay rent for your accommodation?
    → No  (skip to Q2)
    → Yes → Monthly rent? [₹_________]
          → Metro or Non-Metro?
          → Landlord PAN (if annual rent > ₹1L)? [__________]

Q2: Do you have health insurance?
    → No  (skip to Q3)
    → Yes → Self + family premium? [₹_________]
          → Parents premium? [₹_________]
          → Are parents senior citizens? Yes / No

Q3: Any investments beyond EPF shown in Form 16?
    → No  (skip to Q4)
    → Yes → (Same sub-questions as ITR-1 Q3)
          → Own NPS contribution (beyond employer)? [₹_________]
             (System auto-applies ₹50,000 limit for 80CCD(1B))

Q4: Do you have a home loan?
    → No  (skip to Q5)
    → Yes → Self-occupied or let-out?
          → Interest paid? [₹_________]
          → Completion status?

Q5: Any income NOT reflected in your AIS?
    → No  (done)
    → Yes → Freelance / consulting income? [₹_________]
          → Rental income from property? [₹_________]
          → Foreign income? [₹_________]
          → Crypto / Virtual Digital Assets? [₹_________]
```

### Auto-Detected for ITR-2 (Beyond ITR-1)

| Data | Source | ITR Schedule |
|---|---|---|
| All equity MF sales (LTCG) | AIS SFT-18-EMF(M) | Schedule 112A → CG B3 |
| All equity MF sales (STCG) | AIS SFT-18-EMF(M) | Schedule CG A2 |
| All non-equity ETF sales | AIS SFT-17-OTU(M) | Schedule CG A5 / B8 |
| Gold/Silver ETF STCG | AIS SFT-17-OTU(M) | Schedule CG A5 |
| Debt fund redemptions | AIS SFT-17-OTU(M) | Schedule CG B8 |
| Dividend income | AIS SFT-015 | Schedule OS |
| Foreign remittances | AIS SFT-011 | Schedule FA (flag) |
| High-value purchases | AIS SFT-001, 004, 005 | Informational only |
| Securities purchase history | AIS SFT-17(Pur) | Basis for future CG |
| CG date range split | Auto-computed from sale dates | Schedule CG Section F |
| 112A consolidated entry | Auto-consolidated per ISIN | Schedule 112A |
| Schedule SI special rates | Auto-mapped | Schedule SI |
| 80CCD(2) employer NPS | Form 16 | Schedule VI-A |
| Form 67 (foreign tax credit) | Not auto — prompt if FSI exists | Schedule TR |

---

## ITR-3 (Business / Profession)

### Questions (Maximum 6)

```
Q1: Nature of business/profession?
    ○ Manufacturing / Trading
    ○ Services (consulting, freelancing, etc.)
    ○ Specified profession (doctor, lawyer, CA, architect, etc.)

Q2: Do you maintain regular books of accounts?
    → Yes → Audit required u/s 44AB?
    → No  → System suggests presumptive taxation u/s 44AD/44ADA

Q3: Gross receipts / turnover for the year?
    [₹_________]

Q4: Are you registered under GST?
    → Yes → GSTIN? [__________]
          → Annual turnover as per GST returns? [₹_________]

Q5: Any business assets sold during the year?
    → Yes → Details of each asset (system generates CG schedule)

Q6: Do you have any brought-forward business losses?
    → Yes → Upload last year's ITR JSON for auto-import
```

---

## ITR-4 (Sugam — Presumptive)

### Questions (Maximum 4)

```
Q1: Type of presumptive income?
    ○ Business (44AD) — 8% or 6% (digital receipts)
    ○ Profession (44ADA) — 50% of gross receipts
    ○ Transport (44AE)

Q2: Gross receipts / turnover?
    [₹_________]

Q3: Any capital gains during the year?
    → Yes → (System auto-extracts from AIS and adds to ITR-4)

Q4: Any income above presumptive rate?
    → No  (system auto-computes at presumptive rate)
    → Yes → Enter actual income [₹_________]
```

---

## Question Suppression Logic

The system actively suppresses questions when they're irrelevant:

```python
QUESTION_SUPPRESSION_RULES = {
    "rent": {
        "suppress_if": "form16.salary_components.hra == 0",
        "reason": "No HRA component in salary — rent deduction not applicable"
    },
    "health_insurance": {
        "suppress_if": "recommended_regime == 'NEW'",
        "reason": "80D not available under new regime"
    },
    "additional_80c": {
        "suppress_if": "recommended_regime == 'NEW'",
        "reason": "80C not available under new regime"
    },
    "home_loan": {
        "suppress_if": "no SFT for home loan in AIS AND no 24(b) in Form 16",
        "reason": "No evidence of home loan"
    },
    "education_loan": {
        "suppress_if": "recommended_regime == 'NEW'",
        "reason": "80E not available under new regime"
    },
    "lta_travel": {
        "suppress_if": "recommended_regime == 'NEW'",
        "reason": "LTA exemption not available under new regime"
    },
    "own_nps": {
        "suppress_if": "recommended_regime == 'NEW'",
        "reason": "80CCD(1B) not available under new regime"
    },
    "donations_80g": {
        "suppress_if": "recommended_regime == 'NEW' AND no SFT-020 in AIS",
        "reason": "80G not available under new regime"
    },
}
```

---

## The "Explain My Tax" One-Pager

After all questions (or skips), the system generates:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Your Tax Summary — FY 2025-26                          │
│                                                         │
│  📊 Income                              ₹              │
│  ├─ Salary                         17,96,602           │
│  ├─ Capital Gains (LTCG exempt)        5,194           │
│  └─ Bank Interest                        757           │
│     Gross Total                    18,02,553           │
│                                                         │
│  📉 Deductions                         ₹              │
│  └─ Employer NPS (80CCD(2))           47,869           │
│                                                         │
│  💰 Taxable Income                 17,54,687           │
│                                                         │
│  🧮 Tax Computation                    ₹              │
│  ├─ Tax (New Regime)               1,50,937           │
│  ├─ Cess @ 4%                         6,037           │
│  └─ Total Tax                      1,56,974           │
│                                                         │
│  💳 Payments                           ₹              │
│  ├─ TDS by Employer                1,55,738           │
│  ├─ Self-Assessment Tax               1,240           │
│  └─ Balance Payable                      0            │
│                                                         │
│  🏷️ Regime: NEW REGIME (saves ₹31,809 vs Old)          │
│                                                         │
│  [ Download ITR-2 JSON ]   [ See Full Computation ]    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

This is the ONLY screen the user needs to review before exporting.
