# TaxStox — Detailed Architecture Reference

> **👉 For the buildable spec, see [MASTER_PLAN.md](MASTER_PLAN.md) — give that to any AI agent.**
> This file is the detailed reference with code snippets, data structures, and algorithms.
>
> **Authored by:** A 25-year CA + A 25-year Software Engineer, sitting side-by-side.
> **Principle:** The user uploads 2 PDFs, answers at most 5 yes/no questions, and gets a
> validated, regime-optimized, upload-ready ITR JSON. Every single piece of data that exists
> in Form 16 or AIS is machine-extracted. Zero manual data entry. Zero knowledge of ISIN
> codes, CG date ranges, or ITR schedules required.

---

## 1. Core Philosophy

```
                     ┌──────────────────┐
User provides  →     │  2 PDFs          │
                     │  + PAN + DOB     │
                     │  + 0-5 Yes/No    │
                     └──────┬───────────┘
                            │
                     ┌──────▼───────────┐
System does  →          │  Parse, Classify,│
                        │  Optimize, Build, │
                        │  Validate, Export │
                        └──────┬───────────┘
                               │
                     ┌─────────▼─────────┐
User receives  →       │  Download-ready    │
                       │  ITR JSON +        │
                       │  1-page Tax Summary│
                       └────────────────────┘
```

### 1.1 The Golden Rule

> **If data exists in Form 16 or AIS, the user never types it.**
> **If a deduction requires proof the user doesn't have, the system never suggests it.**
> **Every computation the CA did manually today — the engine does automatically.**

### 1.2 What We Learned From Manual Filing

| Lesson | System Response |
|---|---|
| Form 16 password is usually PAN (lowercase) | Auto-try. Ask only on failure. |
| AIS password is always PAN(lower)+DOB(ddmmyyyy) | Auto-compute from PAN+DOB. Never ask. |
| 80CCD(2) eligible amount locked at ₹0 in portal | Cross-validate in JSON. Auto-compute correct value. |
| CG date ranges must sum to BFLA exactly | Compute from AIS dates. Never allow manual entry. |
| ISIN INNOTREQUIRD vs INNOTAVAILAB | Use INNOTAVAILAB per ITD schema spec. |
| `SecondaryAdd` enum validation | Always set to "Y" if no secondary address given. |
| Bank refund flag — only one allowed | Auto-select first validated account. |
| Hash validation prevents direct JSON edits | Output JSON that passes the official utility's import. |
| 112A consolidated entries need Units > 0 | Compute from total sale / weighted avg price; never leave 0. |
| STCG and LTCG must be separated by date period | Auto-split from AIS sale dates into 5 ITR periods. |

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  React / Next.js  →  Web App  →  PWA  →  React Native (App)     │
│                                                                  │
│  Screens: Upload → Summary → Questions(0-5) → Review → Export   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST API
┌──────────────────────────────▼──────────────────────────────────┐
│                        BACKEND (FastAPI / Python)                │
│                                                                  │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ PDF      │  │ Classifi- │  │ Regime   │  │ JSON Builder  │  │
│  │ Parser   │→ │ cation    │→ │ Engine   │→ │ & Validator   │  │
│  │ Engine   │  │ Engine    │  │          │  │               │  │
│  └──────────┘  └───────────┘  └──────────┘  └───────────────┘  │
│                                                                  │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Form 16  │  │ AIS Code  │  │ Old vs   │  │ ITR-1 JSON    │  │
│  │ Decoder  │  │ → ITR     │  │ New      │  │ ITR-2 JSON    │  │
│  │          │  │ Schedule  │  │ Regime   │  │ ITR-3 JSON    │  │
│  │ Form 16  │  │ Mapper    │  │ Compute  │  │ ITR-4 JSON    │  │
│  │ Annexure │  │           │  │          │  │               │  │
│  └──────────┘  └───────────┘  └──────────┘  └───────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              VALIDATION ENGINE (20+ checks)               │   │
│  │  • Sums consistency   • Enum values   • Required fields  │   │
│  │  • CG date ranges     • TDS matching   • Bank accounts    │   │
│  │  • AIS cross-ref      • Limit checks   • Schema compliance│   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. PDF Parsing Engine

### 3.1 Form 16 Parser

```python
# PARSES: Form 16 Part A + Part B + Annexure + Form 12BA
# OUTPUT: Form16Data (structured dict)

class Form16Parser:
    INPUT:  PDF bytes + password (auto-tried: PAN_lower, PAN, last5PAN, etc.)
    OUTPUT: Form16Data {
        # Part A
        pan: str                    # CFFPM4503N
        employee_name: str          # AMAN KUMAR MISHRA
        employer_name: str          # APPLIED MATERIALS INDIA PVT LTD
        employer_tan: str           # BLRA04654G
        employer_address: str
        assessment_year: str        # 2026-27
        period_from: date           # 01-Apr-2025
        period_to: date             # 31-Mar-2026
        quarterly_tds: [            # 4 quarters
            {quarter: str, amount_paid: float, tds_deducted: float}
        ]
        total_amount_paid: float    # 18,71,602
        total_tds: float            # 1,55,738

        # Part B
        gross_salary_171: float     # 18,71,602
        perquisites_172: float      # 0
        profits_lieu_173: float     # 0
        exemptions_s10: {           # All allowances u/s 10
            hra: float              # 0 (new regime)
            lta: float              # 0 (new regime)
            other: float
        }
        std_deduction_16ia: float   # 75,000
        entertainment_16ii: float   # 0
        professional_tax_16iii: float  # 0
        income_under_head_salaries: float  # 17,96,602
        other_income_reported: float     # 0

        # Chapter VI-A
        deductions: {
            sec80c: float           # 0
            sec80ccc: float         # 0
            sec80ccd1: float        # 0
            sec80ccd1b: float       # 0
            sec80ccd2: float        # 47,869 (employer NPS)
            sec80d: float           # 0
            sec80e: float           # 0
            sec80g: float           # 0
            sec80tta: float         # 0
        }
        total_chapter_vi_a: float   # 47,869

        # Tax computation (from Part B)
        taxable_income: float       # 17,48,733
        tax_on_income: float        # 1,49,747
        surcharge: float            # 0
        cess: float                 # 5,990
        total_tax_payable: float    # 1,55,737
        relief_89: float            # 0

        # Regime
        opting_out_115bac: bool     # False (= new regime)

        # Annexure: Salary Breakup
        salary_components: {
            basic: float            # 9,32,472
            hra: float              # 3,72,990
            special_allowance: float # 2,40,424
            lta: float              # 77,649
            lunch_coupons: float    # 24,000
            broadband_reimb: float  # 12,000
            special_award: float    # 4,000
            nps_employer: float     # 47,869
            dbip_bonus: float       # 1,60,198
        }

        # Form 12BA: Perquisites
        perquisites_detail: {
            accommodation: 0,
            car: 0,
            rsu: 0,
            espp: 0,
            free_meals: 0,
            gifts: 0,
            # ... all 21 perquisite types
        }
    }
```

### 3.2 AIS Parser

```python
class AISParser:
    INPUT:  PDF bytes + password (computed: PAN_lower + DOB_ddmmyyyy)
    OUTPUT: AISData {
        pan: str                    # CFFPM4503N
        name: str                   # AMAN KUMAR MISHRA
        dob: date                   # 25/04/1995
        mobile: str                 # 7543037872
        email: str                  # contactamanmishra@gmail.com
        address: str                # Full address

        # Part B1: TDS
        salary_tds: {
            deductor_name: str      # APPLIED MATERIALS INDIA PVT LTD
            deductor_tan: str       # BLRA04654G
            monthly_entries: [{     # 12 entries
                date: date,
                amount_paid: float,
                tds_deducted: float,
                tds_deposited: float,
                status: str
            }]
            total_salary: float     # 18,71,602
            total_tds: float        # 1,55,738
        }
        other_tds: []               # Any non-salary TDS

        # Part B2: SFT (Specified Financial Transactions)
        sft: {
            savings_interest: [{    # SFT-016(SB)
                bank_name: str,     # STATE BANK OF INDIA
                account_number: str # 20132242544
                interest_amount: float # 407
                account_type: str   # Saving
            }]
            equity_mf_sales: [{     # SFT-18-EMF(M)
                amc_name: str       # Quant MF
                security_name: str  # Quant ELSS Tax Saver...
                isin: str           # INF966L01986
                date_of_sale: date  # 21-Apr-2025
                quantity: float     # 19.79
                sale_price: float   # 383.77
                sale_consideration: float # 7,596
                cost_of_acquisition: float # 5,000
                stt_paid: float     # 0.20
                term: str           # Long
                asset_type: str     # Equity MF
            }]
            other_unit_sales: [{    # SFT-17-OTU(M)
                depository: str     # CDSL
                security_name: str  # TATA Gold ETF
                isin: str           # INF277KA1976
                date_of_sale: date  # 27-Feb-2026
                quantity: float     # 5
                sale_price: float   # 15.38
                sale_consideration: float # 77
                cost: float         # 76.20
                term: str           # Short
            }]
            purchases: [{           # SFT-17(Pur)
                depository: str
                market_purchase: float
                market_sales: float
            }]
            # ... other SFT types
        }

        # Part B3: Tax Payments
        tax_payments: []

        # Part B4: Refunds
        refunds: [{
            financial_year: str     # 2024-25
            mode: str               # ECS
            amount: float           # 7,830
            date: date              # 07/07/2025
        }]

        # Part B7: Other Info
        annexure_ii_salary: {
            gross_salary: float     # 18,71,602
            perquisites: float      # 0
            profits_lieu: float     # 0
        }
    }
```

---

## 4. Classification Engine

### 4.1 AIS Code → ITR Schedule Mapper

```python
CLASSIFICATION_MAP = {
    # Salary
    "TDS-192": {
        "schedule": "ScheduleS",
        "handler": "build_salary_from_tds",
        "cross_ref": "Form16.salary"
    },

    # Savings Interest
    "SFT-016(SB)": {
        "schedule": "ScheduleOS",
        "handler": "build_savings_interest",
        "field": "IntrstFrmSavingBank",
        "deduction_available": {
            "old_regime": "80TTA",  # ₹10,000 limit
            "new_regime": None       # Not available
        }
    },

    # Term Deposit Interest
    "SFT-016(TD)": {
        "schedule": "ScheduleOS",
        "handler": "build_term_deposit_interest",
        "field": "IntrstFrmTermDeposit"
    },

    # Equity MF Sales (Long Term, STT Paid)
    "SFT-18-EMF(M)": {
        "Long": {
            "schedule": "Schedule112A",
            "handler": "build_112a_ltcg",
            "tax_rate": "12.5%",
            "exemption_limit": 125000   # ₹1.25L
        },
        "Short": {
            "schedule": "ScheduleCG_A2",
            "handler": "build_111a_stcg",
            "tax_rate": "15%",
            "section": "111A"
        }
    },

    # Other Unit Sales (Gold/Silver ETFs, Debt Funds)
    "SFT-17-OTU(M)": {
        "Long": {
            "schedule": "ScheduleCG_B8",
            "handler": "build_non_equity_ltcg",
            "tax_rate": "12.5% with indexation",
            "indexation": True
        },
        "Short": {
            "schedule": "ScheduleCG_A5",
            "handler": "build_non_equity_stcg",
            "tax_rate": "Slab rate",
            "section": "Applicable rates"
        }
    },

    # Immovable Property
    "SFT-001": {
        "schedule": "ScheduleHP",
        "handler": "build_house_property"
    },

    # Cash Deposits
    "SFT-004": {
        "schedule": "Informational",
        "handler": "flag_for_verification",
        "threshold": 10000000  # ₹1 Cr
    },

    # Credit Card Payments
    "SFT-013": {
        "schedule": "Informational",
        "handler": "flag_if_unexplained"
    },

    # Share Transactions (Depository) — already covered by SFT-17/18
    # Dividends
    "SFT-015": {
        "schedule": "ScheduleOS",
        "handler": "build_dividend_income",
        "field": "DividendGross",
        "taxable_at": "Slab rate"  # Post-2020, all dividends taxable
    },

    # Tax Payments
    "Part B3": {
        "schedule": "ScheduleIT",
        "handler": "build_tax_payments"
    },

    # Refunds
    "Part B4": {
        "schedule": "Informational",
        "handler": "verify_previous_refund_received"
    }
}
```

### 4.2 Capital Gain Classification Logic

```python
def classify_capital_gains(ais_data: AISData, form16: Form16Data) -> CGData:
    """
    Takes raw AIS SFT entries → produces correctly classified CG data
    with all ITR schedules populated.
    """
    cg = CGData()

    for sale in ais_data.sft.equity_mf_sales:
        entry = CGSaleEntry(
            date=sale.date_of_sale,
            isin=sale.isin,
            security_name=sale.security_name,
            quantity=sale.quantity,
            sale_price=sale.sale_price,
            consideration=sale.sale_consideration,
            cost=sale.cost_of_acquisition,
            stt_paid=sale.stt_paid > 0,
            term=sale.term,
        )

        if sale.term == "Long" and entry.stt_paid:
            # EQUITY: Held > 12 months + STT paid → Section 112A
            cg.schedule_112a.append(entry)         # Schedule 112A
            cg.b3_ltcg_12_5pct.append(entry)       # CG B3
            cg.si_2a.append(entry)                 # Schedule SI
        elif sale.term == "Short" and entry.stt_paid:
            # Listed equity STCG → Section 111A (15%)
            cg.a2_stcg_111a.append(entry)           # CG A2
        else:
            # Should not happen for EMF, but handle gracefully
            cg.unclassified.append(entry)

    for sale in ais_data.sft.other_unit_sales:
        entry = CGSaleEntry(...)

        if sale.term == "Short":
            # Non-equity STCG → Slab rate
            cg.a5_stcg_app_rate.append(entry)       # CG A5
        elif sale.term == "Long":
            # Non-equity LTCG → 12.5% with indexation
            cg.b8_ltcg_other.append(entry)          # CG B8

    # Auto-compute date ranges
    cg.date_ranges = compute_date_periods(cg)
    # Ensure sums match BFLA
    cg.validate_sums()

    return cg
```

### 4.3 CG Date Range Auto-Computer

```python
PERIOD_MAP = [
    # (start_day_month, end_day_month, period_key)
    ((4, 1),   (6, 15),  "Upto15Of6"),
    ((6, 16),  (9, 15),  "Upto15Of9"),
    ((9, 16),  (12, 15), "Up16Of9To15Of12"),
    ((12, 16), (3, 15),  "Up16Of12To15Of3"),
    ((3, 16),  (3, 31),  "Up16Of3To31Of3"),
]

def compute_date_periods(cg: CGData) -> CGDateRanges:
    """
    Group every CG transaction by its sale date into the 5 ITR periods.
    This eliminates the manual entry that caused our 11597-vs-11598 error.
    """
    ranges = CGDateRanges()

    for entry in cg.all_sales:
        period = get_period_for_date(entry.date)
        if entry.tax_rate == "12.5%":
            ranges.ltcg_12_5pct[period] += entry.gain
        elif entry.tax_rate == "Slab rate":
            ranges.stcg_app_rate[period] += entry.gain
        elif entry.tax_rate == "15%":
            ranges.stcg_20pct[period] += entry.gain

    # Cross-validate against CG totals
    assert ranges.ltcg_12_5pct.total == sum(e.gain for e in cg.b3_ltcg_12_5pct)
    assert ranges.stcg_app_rate.total == sum(e.gain for e in cg.a5_stcg_app_rate)

    return ranges
```

---

## 5. Minimal Yes/No Questions Per ITR Type

### 5.1 ITR-1 (Sahaj) — Salaried Individuals, Simple Income

**Eligibility:** Salary + One House Property + Other Sources (interest). Total income ≤ ₹50L.

| # | Question | When to Ask | Deduction |
|---|---|---|---|
| 1 | 🏠 Paying rent in a metro city (50% HRA) or non-metro (40%)? | If Form 16 shows HRA component | 10(13A) |
| 2 | 🏥 Health insurance premium paid for self/parents? | Always | 80D |
| 3 | 💰 Investments beyond what's in Form 16? (PPF, ELSS, LIC, FD) | If 80C in Form 16 < ₹1.5L | 80C |
| 4 | 🎓 Interest paid on education loan? | Always | 80E |
| 5 | 🏦 Home loan interest on self-occupied property? | If Schedule HP applicable | 24(b) |

**Auto-extracted from AIS + Form 16:**
- Salary income ✓
- TDS ✓
- Savings/Term deposit interest ✓
- Standard deduction ₹50K (old) / ₹75K (new) ✓

### 5.2 ITR-2 — No Business Income, Capital Gains

**Eligibility:** Your case. Salary + Capital Gains + Other Sources + House Property. No PGBP.

| # | Question | When to Ask | Deduction |
|---|---|---|---|
| 1 | 🏠 Paying rent? Metro/non-metro? Landlord PAN? | If Form 16 shows HRA | 10(13A) |
| 2 | 🏥 Health insurance premium? Self + Parents? Senior citizen? | Always | 80D |
| 3 | 💰 Additional 80C beyond EPF in Form 16? | If 80C < ₹1.5L | 80C |
| 4 | 🎓 Education loan interest? | Always | 80E |
| 5 | 🏦 Home loan? Self-occupied or let-out? | Always | 24(b) |
| -- | **Everything else is auto-detected from AIS** | -- | -- |

**Extra Auto-Detection for ITR-2:**
- All capital gains → Schedules 112A, CG A2/A5, CG B3/B8
- Dividend income → Schedule OS
- Foreign assets (if any AIS entry) → Schedule FA
- Crypto/VDAs (if any SFT entry) → Schedule VDA

### 5.3 ITR-3 — Business/Professional Income

| # | Question |
|---|---|
| 1 | Maintain books of accounts? (Yes → ITR-3; No → ITR-4 presumptive) |
| 2 | Presumptive taxation u/s 44AD/44ADA? |
| 3 | Audit required u/s 44AB? |
| 4 | GST registered? GST turnover? |

### 5.4 ITR-4 (Sugam) — Presumptive Income

| # | Question |
|---|---|
| 1 | Gross receipts/turnover? |
| 2 | Presumptive rate: 44AD (8%/6%) or 44ADA (50%)? |
| 3 | Any capital gains from business assets? |

---

## 6. Regime Optimization Engine

```python
class RegimeOptimizer:
    """
    Computes tax under OLD and NEW regimes.
    Returns the winner and exact savings.
    Never asks the user to choose — tells them which is better.
    """

    def compute(self, income: IncomeData, deductions: DeductionData) -> RegimeResult:
        old = self._compute_old_regime(income, deductions)
        new = self._compute_new_regime(income, deductions)

        return RegimeResult(
            old_tax=old.total_tax,
            new_tax=new.total_tax,
            recommended="OLD" if old.total_tax < new.total_tax else "NEW",
            savings=abs(old.total_tax - new.total_tax),
            old_breakdown=old,
            new_breakdown=new,
        )

    def _compute_old_regime(self, income, deductions):
        """Full old regime with all available deductions."""
        taxable = income.gross_salary

        # Section 10 exemptions
        hra_exempt = self._compute_hra(
            basic=income.salary_components.basic,
            hra_received=income.salary_components.hra,
            rent_paid=deductions.rent_paid,
            metro=deductions.metro_city
        )
        lta_exempt = self._compute_lta(
            lta_received=income.salary_components.lta,
            travel_cost=deductions.lta_travel_cost
        )
        taxable -= (hra_exempt + lta_exempt)

        # Section 16
        taxable -= 50000  # Standard deduction (old regime)

        # Add other income (capital gains, interest, dividends)
        taxable_other = (income.capital_gains.stcg_non_equity +
                        income.capital_gains.stcg_equity_111a +
                        income.other_sources.savings_interest +
                        income.other_sources.dividends)

        # Chapter VI-A deductions (applicable to salary + other income)
        deductions_total = min(
            deductions.sec80c, 150000           # 80C limit
        ) + min(
            deductions.sec80ccd1b, 50000        # 80CCD(1B) limit
        ) + deductions.sec80ccd2 + \
        min(
            deductions.sec80d,                  # 80D limit varies
            self._compute_80d_limit(deductions)
        ) + deductions.sec80e + \
        min(
            deductions.sec80tta, 10000          # 80TTA limit
        ) + deductions.home_loan_interest

        taxable -= deductions_total

        # Tax slabs (old regime)
        return self._slab_old(taxable)

    def _compute_new_regime(self, income, deductions):
        """New regime: minimal deductions, lower rates."""
        taxable = income.gross_salary

        # Section 16: Standard deduction = ₹75,000
        taxable -= 75000

        # Add other income
        taxable_other = (...)

        # Chapter VI-A: ONLY 80CCD(2) and 80CCH available
        taxable -= deductions.sec80ccd2   # Employer NPS

        # Tax slabs (new regime — lower rates)
        return self._slab_new(taxable)
```

### 6.1 Tax Slab Tables (FY 2025-26)

```python
OLD_REGIME_SLABS = [
    (0,          250000,  0.00),   # Nil
    (250000,     500000,  0.05),   # 5%
    (500000,    1000000,  0.20),   # 20%
    (1000000,   float('inf'), 0.30),  # 30%
]

NEW_REGIME_SLABS = [
    (0,          400000,  0.00),   # Nil
    (400000,     800000,  0.05),   # 5%
    (800000,    1200000,  0.10),   # 10%
    (1200000,   1600000,  0.15),   # 15%
    (1600000,   2000000,  0.20),   # 20%
    (2000000,   2400000,  0.25),   # 25%
    (2400000,  float('inf'), 0.30),  # 30%
]
```

---

## 7. JSON Builder & Validator

### 7.1 Builder Architecture

```python
class ITRJSONBuilder:
    """
    Takes parsed + classified data → produces schema-compliant ITR JSON.
    Supports ITR-1, ITR-2, ITR-3, ITR-4.
    """

    def build(self, data: UnifiedTaxData, itr_type: str) -> dict:
        builder_map = {
            "ITR-1": ITR1Builder,
            "ITR-2": ITR2Builder,
            "ITR-3": ITR3Builder,
            "ITR-4": ITR4Builder,
        }
        builder = builder_map[itr_type](data)
        json_data = builder.build()

        # Validate before returning
        validator = ITRValidator(json_data, itr_type)
        errors = validator.validate()
        if errors:
            raise ValidationError(errors)

        return json_data
```

### 7.2 Critical Validations (The 20+ Checks We Discovered)

```python
class ITRValidator:
    CHECKS = [
        # Sum consistency checks
        "cg_date_ranges_sum_matches_bfla",
        "total_gross_salary_matches_components",
        "tds_total_matches_quarterly_sum",
        "total_income_matches_headwise_sum",
        "aggregate_income_matches_total_minus_special",
        "tax_computation_matches_taxable_income",
        "tax_paid_matches_tds_plus_self_assessment",

        # Enum & schema checks
        "secondary_add_is_valid_enum",
        "isin_is_valid_or_innotavailab",
        "nature_of_employment_is_valid",
        "residential_status_is_valid",
        "return_file_section_is_valid",
        "bank_account_type_is_valid",

        # Business rule checks
        "at_most_one_bank_for_refund",
        "pan_aadhaar_linked",
        "itr_form_matches_income_type",
        "regime_selection_is_valid",
        "112a_exemption_limit_applied",
        "std_deduction_applied_correctly",
        "sec80ccd2_within_10pct_limit",

        # Cross-reference checks
        "salary_in_ais_matches_form16",
        "tds_in_ais_matches_form16",
        "capital_gains_in_ais_fully_reported",
        "savings_interest_in_ais_fully_reported",
    ]

    def validate(self) -> List[ValidationError]:
        errors = []
        for check_name in self.CHECKS:
            check_fn = getattr(self, f"_check_{check_name}")
            result = check_fn()
            if not result.passed:
                errors.append(result.error)
        return errors
```

### 7.3 Date Range Sum Cross-Check (The Bug We Hit)

```python
def _check_cg_date_ranges_sum_matches_bfla(self):
    """Ensure CG Section F period-split sums equal BFLA totals."""
    cg = self.json["ITR"]["ITR2"]["ScheduleCGFor23"]
    bfla = self.json["ITR"]["ITR2"]["ScheduleBFLA"]

    # LTCG 12.5%
    ltcg_period_sum = sum(
        cg["AccruOrRecOfCG"]["LongTermUnder12_5Per"]["DateRange"].values()
    )
    ltcg_bfla = bfla["LTCG12_5Per"]["IncBFLA"]["IncOfCurYrUndHeadFromCYLA"]
    if ltcg_period_sum != ltcg_bfla:
        return Fail(f"LTCG date ranges sum ({ltcg_period_sum}) != BFLA ({ltcg_bfla})")

    # STCG Applicable Rate
    stcg_period_sum = sum(
        cg["AccruOrRecOfCG"]["ShortTermUnderAppRate"]["DateRange"].values()
    )
    stcg_bfla = bfla["STCGAppRate"]["IncBFLA"]["IncOfCurYrUndHeadFromCYLA"]
    if stcg_period_sum != stcg_bfla:
        return Fail(f"STCG date ranges sum ({stcg_period_sum}) != BFLA ({stcg_bfla})")

    return Pass()
```

---

## 8. Technology Stack

### 8.1 Backend

| Component | Technology | Rationale |
|---|---|---|
| API Framework | FastAPI (Python 3.12+) | Async, auto-docs, type-safe |
| PDF Parsing | pikepdf + pdfplumber | Decrypts + extracts text from password-protected PDFs |
| Data Validation | Pydantic v2 | Type-safe data models, built-in validators |
| Task Queue | Celery + Redis | Background PDF processing for large files |
| Database | PostgreSQL | Store anonymized user data, filing history |
| Cache | Redis | Cache parsed Form 16/AIS for session |
| File Storage | S3 / MinIO | Temporary PDF storage (auto-deleted after 24h) |
| Containerization | Docker + docker-compose | Reproducible dev/prod environments |

### 8.2 Frontend

| Component | Technology | Rationale |
|---|---|---|
| Framework | Next.js 14 (App Router) | SSR for SEO, API routes, React Server Components |
| UI Library | Tailwind CSS + shadcn/ui | Clean, accessible, customizable |
| State Management | Zustand | Lightweight, no boilerplate |
| PDF View | react-pdf | In-browser PDF preview before upload |
| PWA | next-pwa | Install as desktop/mobile app |
| E2E Tests | Playwright | Cross-browser testing |

### 8.3 Mobile App

| Component | Technology | Rationale |
|---|---|---|
| Framework | React Native + Expo | Shared logic with web, fast dev |
| Camera | expo-camera / react-native-document-picker | Scan Form 16 from phone |
| Native PDF | react-native-pdf | View documents on phone |

---

## 9. Project Structure

```
D:\IT_Returns\
├── ARCHITECTURE.md              # ← This file
├── DATA_MODEL.md                # Data structures & schemas
├── ITR_TYPES_QUESTIONS.md       # Per-ITR question trees
├── README.md                    # Project overview
│
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── src/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Environment config
│   │   │
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Base parser class
│   │   │   ├── form16.py        # Form 16 PDF parser
│   │   │   ├── ais.py           # AIS PDF parser
│   │   │   ├── form26as.py      # Form 26AS parser (future)
│   │   │   └── utils.py         # Shared PDF utilities
│   │   │
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── classifier.py    # AIS → ITR schedule mapper
│   │   │   ├── optimizer.py     # Old vs New regime
│   │   │   ├── daterange.py     # CG date period splitter
│   │   │   └── hra.py           # HRA exemption calculator
│   │   │
│   │   ├── builder/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Base JSON builder
│   │   │   ├── itr1.py          # ITR-1 JSON builder
│   │   │   ├── itr2.py          # ITR-2 JSON builder
│   │   │   ├── itr3.py          # ITR-3 JSON builder
│   │   │   ├── itr4.py          # ITR-4 JSON builder
│   │   │   └── templates/       # JSON templates per ITR type
│   │   │       ├── itr1_v1.json
│   │   │       ├── itr2_v1.json
│   │   │       └── ...
│   │   │
│   │   ├── validator/
│   │   │   ├── __init__.py
│   │   │   ├── checks.py        # 20+ cross-validation rules
│   │   │   ├── reconciler.py    # AIS vs Form 16 cross-check
│   │   │   └── schema.py        # ITR JSON schema validators
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── form16.py        # Form16Data pydantic model
│   │   │   ├── ais.py           # AISData pydantic model
│   │   │   ├── tax.py           # TaxData, IncomeData models
│   │   │   └── itr.py           # UnifiedTaxData model
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── upload.py        # File upload endpoints
│   │   │   ├── questions.py     # Smart question generation
│   │   │   ├── compute.py       # Tax computation endpoint
│   │   │   ├── export.py        # JSON download + portal instructions
│   │   │   └── auth.py          # OTP-based authentication
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # User model, OTP model
│   │   │   ├── otp.py           # Email/WhatsApp OTP sender
│   │   │   └── google_oauth.py   # Google Sign-In
│   │   │
│   │   ├── integrations/
│   │   │   ├── __init__.py
│   │   │   ├── pan_verify.py     # NSDL PAN Verification API
│   │   │   ├── aa_framework.py  # Account Aggregator (Phase 2)
│   │   │   ├── traces.py        # TRACES Form 26AS (Phase 2)
│   │   │   └── itd_efiling.py   # ITD e-Filing API (Phase 3)
│   │   │
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── pdf_crypto.py    # PDF password resolution
│   │       ├── pan_utils.py     # PAN validation, masking
│   │       └── itd_schema.py   # ITD schema version management
│   │
│   └── tests/
│       ├── fixtures/
│       │   ├── sample_form16.pdf
│       │   ├── sample_ais.pdf
│       │   └── expected_itr2.json
│       ├── test_parsers.py
│       ├── test_classifier.py
│       ├── test_optimizer.py
│       ├── test_builder.py
│       └── test_validator.py
│
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # Landing / upload screen
│   │   │   ├── questions/
│   │   │   │   └── page.tsx      # Smart questions (0-5)
│   │   │   ├── review/
│   │   │   │   └── page.tsx      # 1-page tax summary
│   │   │   └── export/
│   │   │       └── page.tsx      # Download JSON
│   │   │
│   │   ├── components/
│   │   │   ├── UploadZone.tsx     # Drag & drop PDF upload
│   │   │   ├── PanDobInput.tsx    # PAN + DOB fields
│   │   │   ├── YesNoQuestion.tsx  # Single yes/no card
│   │   │   ├── TaxSummary.tsx     # 1-page review card
│   │   │   ├── RegimeComparison.tsx # Old vs New bar chart
│   │   │   └── LoadingState.tsx   # Progress while parsing
│   │   │
│   │   ├── hooks/
│   │   │   ├── useUpload.ts
│   │   │   ├── useQuestions.ts
│   │   │   └── useTaxData.ts
│   │   │
│   │   └── lib/
│   │       ├── api.ts             # API client
│   │       └── types.ts           # TypeScript types
│   │
│   └── public/
│       └── manifest.json          # PWA manifest
│
├── mobile/                        # Future: React Native app
│   └── (placeholder)
│
└── docs/
    ├── API.md
    ├── ITR_SCHEMA_NOTES.md        # ITD schema quirks we discovered
    └── DEPLOYMENT.md
```

---

## 10. API Design

### 10.1 Endpoints

```
POST   /api/upload/form16        # Upload Form 16 PDF → returns Form16Data
POST   /api/upload/ais           # Upload AIS PDF → returns AISData
GET    /api/parse/{session_id}   # Get parsed data for session
GET    /api/questions/{itr_type} # Get smart questions for ITR type
POST   /api/questions/{session_id}  # Submit answers → returns CompleteTaxData
GET    /api/compute/{session_id} # Run regime optimizer → returns TaxSummary
GET    /api/export/{session_id}  # Download ITR JSON
GET    /api/preview/{session_id} # Preview filled ITR (schedules summary)
```

### 10.2 Core API Contract

```python
# POST /api/upload/form16
Request:
    file: PDF (multipart/form-data)
    password: str (optional — auto-tried if omitted)
Response:
    {
        "status": "parsed" | "password_required" | "invalid_pdf",
        "data": Form16Data | None,
        "required_password": bool
    }

# GET /api/questions/ITR-2
Response:
    {
        "itr_type": "ITR-2",
        "auto_detected": {
            "salary": 1796602,
            "capital_gains": {"ltcg_112a": 58273, "stcg_app_rate": 5194},
            "savings_interest": 757,
            "regime_recommended": "NEW",
            "regime_savings": 31809
        },
        "questions": [
            {
                "id": "rent",
                "text": "Do you pay rent for your accommodation?",
                "type": "yes_no",
                "if_yes": [
                    {"id": "rent_amount", "text": "Monthly rent amount?", "type": "number"},
                    {"id": "rent_city", "text": "City?", "type": "dropdown", "options": ["Metro (Mumbai, Delhi, Bangalore, etc.)", "Non-Metro"]},
                    {"id": "landlord_pan", "text": "Landlord PAN? (required if annual rent > ₹1L)", "type": "text", "optional": true}
                ],
                "impact": "Could save up to ₹77,582"
            },
            # ... max 4 more questions
        ]
    }

# GET /api/compute/{session_id}
Response:
    {
        "total_income": 1754687,
        "tax_liability": 156974,
        "tds_paid": 155738,
        "self_assessment_tax": 1240,
        "balance_payable": 0,
        "regime": "NEW",
        "filing_deadline": "2026-07-31",
        "schedule_summary": {
            "salary": 1796602,
            "capital_gains": 63467,
            "other_sources": 757,
            "deductions": 47869
        }
    }
```

---

## 11. Password Resolution — The "Never Ask" Approach

```python
# backend/src/utils/pdf_crypto.py

class PasswordResolver:
    """
    Resolves PDF passwords silently.
    Only prompts the user when all automatic attempts fail.

    KNOWLEDGE BASE (updated from real-world data):
    - AIS password: ALWAYS PAN(lowercase) + DOB(DDMMYYYY), e.g., cffpm4503n25041995
    - Form 16 password: COMMONLY PAN(lowercase), e.g., cffpm4503n
      - Sometimes: full PAN (case-sensitive)
      - Rarely: employer-assigned (ask user)
    - Form 26AS password: Same as AIS (PAN_lower + DOB)
    """

    FORM16_CANDIDATES = [
        "{pan_lower}",          # cffpm4503n
        "{pan}",                # CFFPM4503N
        "{pan_lower}@{dob_ddmm}",    # cffpm4503n@2504
        "{pan_lower}@123",      # cffpm4503n@123
        "{pan_lower}{dob_ddmm}",     # cffpm4503n2504
    ]

    def resolve_form16_password(self, pdf_path: str, pan: str, dob: date) -> str | None:
        """Try all candidates. Return password or None if all fail."""
        pan_lower = pan.lower()
        dob_ddmm = dob.strftime("%d%m")

        for template in self.FORM16_CANDIDATES:
            password = template.format(pan=pan, pan_lower=pan_lower,
                                       dob_ddmm=dob_ddmm)
            try:
                pdf = pikepdf.open(pdf_path, password=password)
                pdf.close()
                return password
            except pikepdf.PasswordError:
                continue

        return None  # All failed — prompt user

    def resolve_ais_password(self, pan: str, dob: date) -> str:
        """AIS password is STANDARD — PAN(lower) + DOB(DDMMYYYY)."""
        return f"{pan.lower()}{dob.strftime('%d%m%Y')}"
```

---

## 12. Deployment Strategy

### 12.1 Phase 1: Single-Server MVP

```
┌──────────────────────────────────────────┐
│  VPS (4GB RAM, 2 vCPU)                   │
│                                           │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐ │
│  │ Nginx   │→ │ FastAPI │  │ Redis    │ │
│  │ (TLS)   │  │ :8000   │  │ :6379    │ │
│  └─────────┘  └────┬────┘  └──────────┘ │
│                     │                     │
│  ┌──────────────────▼──────────────────┐ │
│  │         PostgreSQL :5432            │ │
│  └─────────────────────────────────────┘ │
│                                           │
│  ┌──────────────────────────────────────┐│
│  │  Next.js Static Export (CDN)         ││
│  └──────────────────────────────────────┘│
└──────────────────────────────────────────┘
```

### 12.2 Phase 2: Production

- Backend: Kubernetes or AWS ECS (auto-scaling during tax season Jul 1-31, peak traffic)
- Frontend: Vercel / Cloudflare Pages (CDN edge)
- Database: RDS PostgreSQL with read replicas
- File Processing: SQS + Lambda workers for PDF parsing at scale
- Monitoring: Sentry + Prometheus + Grafana
- Compliance: ISO 27001 controls, data encrypted at rest/transit, auto-delete PDFs after 24h

---

## 13. Data Privacy Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  CRITICAL: This system handles PAN, Aadhaar, salary,             │
│  capital gains, bank account numbers — the most sensitive        │
│  personal financial data possible under Indian law.              │
└─────────────────────────────────────────────────────────────────┘

PRINCIPLES:
1. PDFs are stored ONLY in memory during processing, never on disk
2. Extracted data is held in Redis with 24-hour TTL per session
3. JSON downloads are generated and streamed; never stored permanently
4. PAN is masked (CFFPM****N) in all logs and analytics
5. No data leaves the Indian server region
6. GDPR-equivalent consent before processing
7. Right to deletion: one-click wipe of all session data
8. Audit log of every access (for IT Act compliance)

IMPLEMENTATION:
- In-memory PDF processing via BytesIO
- Redis session store with automatic expiry
- No persistent storage of parsed tax data
- End-to-end TLS (TLS 1.3 minimum)
- Encryption at rest (AES-256) for any temporary disk cache
```

---

## 14. Authentication & User Management

### 14.1 Sign-Up / Sign-In Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    SIGN UP (First Time)                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Name as per PAN    [ AMAN KUMAR MISHRA            ]  │    │
│  │  PAN                [ CFFPM4503N                   ]  │    │
│  │  Date of Birth      [ 25/04/1995                   ]  │    │
│  │  Email              [ contactamanmishra@gmail.com  ]  │    │
│  │  Mobile (optional)  [ +91 7543037872              ]  │    │
│  │                                                      │    │
│  │  [ Send OTP ]                                        │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  SIGN IN (Returning User)                                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Email              [ contactamanmishra@gmail.com  ]  │    │
│  │  [ Send OTP ]  or  [ Sign in with Google ]           │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 14.2 Auth Architecture

```python
class User(BaseModel):
    """Minimal user profile — only what's needed for ITR filing"""
    id: UUID
    email: str
    email_verified: bool
    name_as_per_pan: str                    # AMAN KUMAR MISHRA
    pan: str                                # CFFPM4503N (encrypted at rest)
    pan_masked: str                         # CFFPM****N (for display)
    dob: date                               # 1995-04-25
    mobile: Optional[str]                   # +917543037872
    google_id: Optional[str]                # For social login

    # Session-only data (never persisted)
    # form16_data, ais_data — held in Redis, 24h TTL

    created_at: datetime
    last_filed_year: Optional[str]          # "2025-26"
    filing_count: int = 0
```

### 14.3 Why OTP, Not Password

```
1. Users forget passwords. They don't forget their email.
2. One less thing to remember = faster filing.
3. Email OTP is sufficient for a system that holds NO persistent financial data.
4. Google OAuth for even faster sign-in.
5. PAN + DOB are used ONLY for AIS/Form 16 password derivation and ITR JSON filling.
   They are NOT authentication credentials — they are tax profile data.
```

### 14.4 Security Boundaries

| Data | Storage | Encryption | Retention |
|---|---|---|---|
| Email, Name, PAN(masked) | PostgreSQL | AES-256 at rest | Until user deletes account |
| Full PAN, DOB | Encrypted column (pgcrypto) | AES-256, key in Vault | Until user deletes account |
| Form 16 PDF | Memory-only (BytesIO) | TLS in transit | Destroyed after parsing |
| AIS PDF | Memory-only (BytesIO) | TLS in transit | Destroyed after parsing |
| Parsed tax data | Redis (session scoped) | TLS in transit | 24-hour TTL |
| Generated ITR JSON | Streamed to client | TLS in transit | Never stored |
| OTP tokens | Redis | In-memory only | 5-minute TTL |

### 14.5 Registration Validation

```python
class RegistrationValidator:
    """
    Validates sign-up data against ITD records using PAN verification API.
    Ensures the name matches PAN exactly — critical for ITR filing.
    """

    async def validate_pan_details(self, pan: str, name: str, dob: date) -> bool:
        """
        Step 1: Call NSDL PAN Verification API
        Step 2: Cross-check name and DOB match PAN database
        Step 3: If mismatch, flag to user BEFORE they upload files
        """
        pan_info = await self.pan_verification_api.verify(pan)
        if pan_info.name.upper() != name.upper():
            raise ValidationError(
                f"Name '{name}' does not match PAN name '{pan_info.name}'."
                f" Please enter your name exactly as on your PAN card."
            )
        if pan_info.dob != dob:
            raise ValidationError(
                f"DOB does not match PAN records. Please use the DOB on your PAN card."
            )
        return True
```

---

## 15. API Integration — Fetching AIS / Form 16 / Form 26AS

> **The Ultimate Goal:** User enters PAN + DOB. Authenticates via OTP on Aadhaar-linked
> mobile. System fetches AIS, Form 26AS, and (optionally) Form 16 directly from ITD —
> zero PDF uploads required.

### 15.1 The Data Landscape

| Document | Contains | Source | API Access? |
|---|---|---|---|
| **AIS** | All financial transactions (TDS, SFT, interest, dividends, CG) | ITD Compliance Portal | ⚠️ Emerging |
| **Form 26AS** | Tax credits (TDS, TCS, Advance Tax, Self-Assessment) | TRACES Portal | ✅ Via intermediaries |
| **Form 16** | Salary breakup, exemptions, deductions, TDS by employer | Employer-issued | ❌ No central source |
| **26AS (Annual)** | Consolidated tax statement | TRACES | ✅ Via APIs |

### 15.2 Available APIs & Services

#### Tier 1: Official Government APIs (Free / Regulated)

| API | Provider | Status | What It Gives |
|---|---|---|---|
| **PAN Verification** | NSDL / UTITSL | ✅ Live | Name, DOB, PAN status, Aadhaar linking status |
| **e-Filing API Gateway** | ITD (incometax.gov.in) | ⚠️ Pilot phase | Registered intermediaries can file returns, fetch limited data |
| **TRACES API** | TIN-NSDL | ✅ For deductors | TDS statements, Form 16 generation (employer-side only) |
| **Aadhaar e-KYC** | UIDAI | ✅ Live | Identity verification, mobile number for OTP |

#### Tier 2: Account Aggregator Framework (RBI-Regulated, Consent-Based)

> **The AA framework is the LEGAL path to fetching financial data with user consent.**
> It is the future of tax data access in India.

| Aggregator | Type | What They Connect |
|---|---|---|
| **Sahamati** | AA Ecosystem Coordinator | List of all licensed AAs and FIUs |
| **Finvu** | Account Aggregator | Bank accounts, mutual funds, insurance, tax data (upcoming) |
| **OneMoney** | Account Aggregator | Multi-institution financial data |
| **CAMS Finserv** | Account Aggregator | Mutual fund data, capital gains statements |
| **NAPSB** (Protean/eGov) | Account Aggregator | NSDL-anchored, likely to integrate tax data first |

**How AA Works for Tax Data:**

```
User (PAN + Aadhaar OTP)
        │
        ▼
┌──────────────────┐     Consent      ┌──────────────────┐
│  TaxStox (FIU)   │ ◄──────────────► │  Account          │
│  Our App         │                  │  Aggregator       │
└──────────────────┘                  └────────┬─────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────┐
                    │                          │                      │
               ┌────▼─────┐           ┌───────▼──────┐       ┌───────▼──────┐
               │ TRACES    │           │ Mutual Fund   │       │ Bank         │
               │ (Form 26AS)│          │ (CAMS/KFin)  │       │ (SBI/HDFC)   │
               └──────────┘           └──────────────┘       └──────────────┘
```

#### Tier 3: Commercial / Paid API Services

| Service | Pricing Model | Capabilities |
|---|---|---|
| **Quicko API** | B2B, per-return pricing | AIS parsing, ITR preparation, e-filing |
| **ClearTax GST/ITR APIs** | Enterprise licensing | Bulk ITR filing, data extraction from PDFs |
| **TaxBuddy** | Per-filing | Guided ITR with document upload |
| **Zerodha Console** | Free (for Zerodha users) | Capital gains P&L with ITR-ready schedules |
| **Groww ITR** | Freemium | MF capital gains auto-computed |
| **INDmoney** | Freemium | All-in-one financial data aggregator |

#### Tier 4: NSDL/TIN APIs (For Registered Entities)

```python
# TIN-NSDL APIs available to registered intermediaries
NSDL_APIS = {
    "PAN_VERIFICATION": {
        "endpoint": "https://tin.tin.nsdl.com/panverify",
        "requires": "Digital Signature Certificate (DSC) + registered intermediary",
        "returns": "Name, DOB, PAN status, Aadhaar link status",
    },
    "TDS_26AS": {
        "endpoint": "TRACES portal for deductors/collectors",
        "requires": "TAN registration + DSC",
        "returns": "Form 26AS (TDS details)",
        "limitation": "Deductor-side only, not taxpayer-side fetch",
    },
    "AIS_FETCH": {
        "status": "NOT YET AVAILABLE as taxpayer-facing API",
        "future": "ITD has announced plans for AIS API access via e-filing portal",
        "current_workaround": "User downloads AIS PDF from compliance portal; we parse it",
    },
}
```

### 15.3 The Hybrid Approach (Phase 1 → Phase 3 Evolution)

```
PHASE 1 (MVP): Upload-based
    User uploads: Form 16 PDF + AIS PDF
    System auto-decrypts (PAN-based password)
    ⏱️ 2 minutes total

PHASE 2: AIS Auto-Fetch
    User enters PAN → authenticates via Aadhaar OTP
    System fetches AIS + Form 26AS via AA framework
    User still uploads Form 16
    ⏱️ 1 minute total

PHASE 3: Fully Automated
    User enters PAN → authenticates via Aadhaar OTP
    System fetches: AIS + Form 26AS + Capital Gains Statement
    User optionally uploads Form 16 (if available)
    ⏱️ 30 seconds total
```

### 15.4 PAN Verification API (NSDL — Available Today)

```python
# backend/src/integrations/pan_verification.py

class NSDLPANVerification:
    """
    NSDL PAN Verification API.
    Available to registered entities with DSC.
    Used at sign-up to validate Name, DOB match PAN records.
    """

    BASE_URL = "https://tin.tin.nsdl.com/panverify"

    async def verify(self, pan: str) -> PANInfo:
        """
        Returns PAN card details from NSDL.
        Cross-checks name + DOB for registration validation.
        """
        response = await self._call_api(
            pan=pan,
            dsc=self.digital_signature_certificate,
        )
        return PANInfo(
            pan=pan,
            name=response["name"],           # As per PAN card
            dob=parse_date(response["dob"]),
            status=response["status"],        # Active / Inactive
            aadhaar_linked=response.get("aadhaar_linked", False),
            last_updated=response["last_updated"],
        )
```

### 15.5 The Immediate Practical Solution

For Phase 1, the PDF upload approach works perfectly well (as we proved today):

| What | How |
|---|---|
| AIS PDF | User downloads from compliance.insight.gov.in (1 click) |
| Form 16 PDF | User gets from employer / HR portal |
| Both take | ~2 minutes to obtain |

**The real UX win is:** Users DON'T need to read these PDFs, understand ISIN codes,
or know CG date ranges. They just upload and the system does the rest.

---

## 16. Post-Export: Crystal Clear ITR Portal Instructions

> **This screen appears immediately after the user downloads the JSON.**
> It is the single most important UX element in the entire app.
> Every step is click-by-click, button-label-by-button-label.

### 16.1 The Export Screen (What the User Sees)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ✅ Your ITR-2 JSON is ready!                                            │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  📄 ITR-2_CFFPM4503N_2025-26.json                         12 KB  │    │
│  │                                                                    │    │
│  │  Tax Summary:                                                      │    │
│  │  Taxable Income: ₹17,54,687   │   Tax: ₹1,56,974                 │    │
│  │  TDS: ₹1,55,738               │   To Pay: ₹1,240                 │    │
│  │                                                                    │    │
│  │  [ 📥 Download JSON ]    [ 📧 Email me the file ]                 │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  📋 WHAT TO DO NEXT — Follow These 8 Steps Exactly               │    │
│  │                                                                  │    │
│  │  STEP 1: Pay Your Tax (if balance payable > ₹0)                  │    │
│  │  ─────────────────────────────────────────                       │    │
│  │  You owe: ₹1,240                                                 │    │
│  │                                                                  │    │
│  │  👉 Go to: https://eportal.incometax.gov.in                      │    │
│  │  👉 Login → e-Pay Tax → New Payment                             │    │
│  │  👉 Select: AY 2026-27 │ Type: Self-Assessment Tax (300)         │    │
│  │  👉 Enter amount: 1240 → Pay via UPI/NetBanking/Card             │    │
│  │  👉 Save the Challan Receipt — you'll need BSR Code & Challan No │    │
│  │                                                                  │    │
│  │  ⚠ SKIP this step if Balance Payable shows ₹0                   │    │
│  │                                                                  │    │
│  │  STEP 2: Go to the ITR Filing Portal                             │    │
│  │  ─────────────────────────────────────                           │    │
│  │  👉 Open: https://eportal.incometax.gov.in                       │    │
│  │  👉 Click "Login" (top right)                                    │    │
│  │  👉 Enter PAN: CFFPM4503N → Password → Login                     │    │
│  │                                                                  │    │
│  │  STEP 3: Navigate to File ITR                                    │    │
│  │  ─────────────────────────────────────                           │    │
│  │  👉 After login, click: e-File → Income Tax Returns              │    │
│  │  👉 Click the blue button: "File Income Tax Return"              │    │
│  │                                                                  │    │
│  │  STEP 4: Select Filing Options                                   │    │
│  │  ─────────────────────────────────────                           │    │
│  │  👉 Assessment Year:        [ 2026-27 ]  ← MUST be this          │    │
│  │  👉 Mode of Filing:         [ Offline  ]  ← NOT Online           │    │
│  │  👉 Filing Type:            [ Original  ]                        │    │
│  │  👉 Audited u/s 44AB?:      [ No        ]                        │    │
│  │  👉 ITR Type:               [ ITR-2     ]                        │    │
│  │  👉 Click: "Continue"                                            │    │
│  │                                                                  │    │
│  │  STEP 5: Upload Your JSON File                                   │    │
│  │  ─────────────────────────────────────                           │    │
│  │  👉 Click "Choose File" or "Browse"                              │    │
│  │  👉 Select: ITR-2_CFFPM4503N_2025-26.json                       │    │
│  │  👉 Click "Upload"                                               │    │
│  │                                                                  │    │
│  │  Wait 5-10 seconds for validation. You should see:               │    │
│  │  ✅ "JSON uploaded successfully"                                 │    │
│  │                                                                  │    │
│  │  ⚠ If you see ANY red error, DO NOT PANIC.                      │    │
│  │     → Copy the exact error text                                  │    │
│  │     → Come back to TaxStox → "Help" → Paste error               │    │
│  │     → We'll fix the JSON and give you a new file                 │    │
│  │                                                                  │    │
│  │  STEP 6: Verify the Tax Computation                              │    │
│  │  ─────────────────────────────────────                           │    │
│  │  👉 The portal will show your income and tax breakdown           │    │
│  │  👉 Cross-check with our summary:                                │    │
│  │     Total Income:    ₹17,54,687   ← should match                 │    │
│  │     Gross Tax:       ₹1,56,974    ← should match                 │    │
│  │     Balance Payable: ₹0           ← should be ZERO after payment │    │
│  │                                                                  │    │
│  │  ⚠ If any number differs by more than ₹5, STOP.                 │    │
│  │     Contact support. DO NOT submit.                              │    │
│  │                                                                  │    │
│  │  STEP 7: Submit & E-Verify                                       │    │
│  │  ─────────────────────────────────────                           │    │
│  │  👉 Scroll to bottom                                             │    │
│  │  👉 Check: "I declare that the information is correct..."        │    │
│  │  👉 Click: "Proceed to Verification"                             │    │
│  │                                                                  │    │
│  │  👉 Choose verification method:                                  │    │
│  │     ○ E-Verify via Aadhaar OTP  ← EASIEST                       │    │
│  │     ○ E-Verify via Net Banking                                   │    │
│  │     ○ E-Verify via Demat Account                                 │    │
│  │     ○ Send signed ITR-V to CPC Bangalore  ← SLOWEST             │    │
│  │                                                                  │    │
│  │  👉 If Aadhaar OTP: Enter OTP sent to your Aadhaar-linked mobile │    │
│  │  👉 Click "Verify"                                               │    │
│  │                                                                  │    │
│  │  STEP 8: Download Acknowledgement                                │    │
│  │  ─────────────────────────────────────                           │    │
│  │  👉 After successful verification, you'll see:                   │    │
│  │     ✅ "ITR Submitted Successfully"                              │    │
│  │  👉 Click "Download Acknowledgement"                             │    │
│  │  👉 Save the PDF — it has your ITR-V / Acknowledgement Number    │    │
│  │  👉 Note the Acknowledgement Number: _______________             │    │
│  │                                                                  │    │
│  │  🎉 YOU'RE DONE!                                                 │    │
│  │                                                                  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  ⚠ TROUBLESHOOTING — Common Portal Errors                       │    │
│  │                                                                  │    │
│  │  Error: "Schema validation failed"                               │    │
│  │  → Your JSON has a format mismatch. Download again from us.      │    │
│  │                                                                  │    │
│  │  Error: "Invalid hash — modification detected"                   │    │
│  │  → The JSON was edited outside the utility. Use our original.    │    │
│  │                                                                  │    │
│  │  Error: "PAN-Aadhaar not linked"                                 │    │
│  │  → Go to incometax.gov.in → Link PAN-Aadhaar → Pay ₹1,000 fine  │    │
│  │  → Wait 24 hours after linking before filing                     │    │
│  │                                                                  │    │
│  │  Error: "Return already filed for this PAN"                      │    │
│  │  → Someone (employer/CA) already filed. Check with them.         │    │
│  │  → Or select "Revised Return" under section 139(5)               │    │
│  │                                                                  │    │
│  │  Need help? → support@taxflow.app | WhatsApp: +91-XXXXX         │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  [ 📥 Download JSON ]    [ 📋 Copy These Instructions ]    [ ✉️ Email ] │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 16.2 Context-Aware Instructions

The export screen adapts based on what the system computed:

```python
class ExportScreenGenerator:
    def generate(self, tax_data: UnifiedTaxData) -> ExportScreen:
        screen = ExportScreen()

        # STEP 1: Payment instructions — ONLY if money is owed
        if tax_data.final_balance_payable > 0:
            screen.steps.append(Step(
                title="Pay Your Tax",
                body=f"You owe ₹{tax_data.final_balance_payable}. "
                     f"Go to eportal.incometax.gov.in → e-Pay Tax → "
                     f"Self-Assessment Tax (300) → AY {tax_data.assessment_year} → "
                     f"Pay ₹{tax_data.final_balance_payable}",
                skippable=False,
                condition="balance_payable > 0"
            ))
        else:
            screen.steps.append(Step(
                title="No Payment Required",
                body="Your TDS + Advance Tax cover your entire liability. "
                     "Skip to Step 2.",
                skippable=True,
                condition="balance_payable == 0"
            ))

        # STEP 5: Upload path varies by ITR type
        screen.steps.append(Step(
            title="Upload Your JSON File",
            body=f"Select ITR-{tax_data.itr_type} in the dropdown. "
                 f"Upload: ITR{tax_data.itr_type}_{tax_data.pan}_{tax_data.fy}.json",
            condition="always"
        ))

        # Regime-specific cross-check
        screen.steps.append(Step(
            title="Verify the Tax Computation",
            critical_numbers=[
                ("Total Income", tax_data.final_total_income),
                ("Gross Tax", tax_data.final_tax_liability),
                ("Balance Payable", tax_data.final_balance_payable),
                ("Regime Applied", tax_data.recommended_regime),
            ],
            condition="always"
        ))

        return screen
```

### 16.3 The JSON Filename Convention

```python
def generate_filename(tax_data: UnifiedTaxData) -> str:
    """
    ITR{type}_{PAN}_{FY}.json
    Example: ITR2_CFFPM4503N_2025-26.json
    """
    fy_short = tax_data.assessment_year.replace("-", "")  # 2026-27 → 202627
    return f"ITR{tax_data.itr_type}_{tax_data.pan}_{tax_data.financial_year}.json"
```

### 16.4 Post-Filing Email (Sent 24 Hours After Export)

```
Subject: Did your ITR filing go through, Aman?

Body:
Hi Aman,

You downloaded your ITR-2 JSON yesterday. Just checking:

[ ✅ I've filed and verified ] → Great! Forward us your acknowledgement
                                  number and we'll track your refund.

[ ❌ I faced an error ]         → Reply with the error message.
                                  Our system auto-detects portal error patterns
                                  and regenerates the JSON.

[ ⏳ I haven't filed yet ]      → The ITR deadline is July 31, 2026.
                                  [ Download JSON again ]
                                  [ Book a CA callback ]

— TaxStox
```

---

## 17. Database Design — What We Store vs What We Don't

### 17.1 The Core Principle

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   STORE PERMANENTLY (PostgreSQL):                                   │
│   • User profile — so they don't re-enter PAN/DOB/Name every year   │
│   • Filing history metadata — "filed ITR-2 for FY 2025-26 on 28-Jun"│
│   • NOT the tax data itself                                         │
│                                                                     │
│   STORE TEMPORARILY (Redis, 24h TTL):                               │
│   • Parsed Form 16 contents                                         │
│   • Parsed AIS contents                                             │
│   • Session-scoped tax computation                                  │
│   • Generated ITR JSON (streamed to user, not saved)                │
│                                                                     │
│   NEVER STORE:                                                      │
│   • PDF files after parsing                                         │
│   • Bank account numbers beyond masked last-4 digits                │
│   • Unencrypted PAN or DOB                                          │
│   • Completed ITR JSON after download                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 17.2 Schema Design

```sql
-- ============================================
-- TABLE 1: Users — The ONLY persistent table
-- ============================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT NOT NULL UNIQUE,
    email_verified  BOOLEAN DEFAULT FALSE,
    google_id       TEXT UNIQUE,                  -- NULL if email-only signup
    name_as_per_pan TEXT NOT NULL,                -- "AMAN KUMAR MISHRA"
    pan_encrypted   BYTEA NOT NULL,               -- AES-256 encrypted full PAN
    pan_masked      TEXT NOT NULL,                -- "CFFPM****N" for display
    dob_encrypted   BYTEA NOT NULL,               -- AES-256 encrypted DOB
    mobile          TEXT,                         -- Optional, for WhatsApp OTP
    pan_verified    BOOLEAN DEFAULT FALSE,        -- Verified against NSDL?
    aadhaar_linked  BOOLEAN,                      -- From NSDL response
    preferences     JSONB DEFAULT '{}',           -- Theme, notifications, regime default
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ                   -- Soft delete for right-to-deletion
);

CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_google_id ON users(google_id) WHERE deleted_at IS NULL;

-- ============================================
-- TABLE 2: Filing History — Metadata only
-- ============================================
CREATE TABLE filing_history (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id),
    assessment_year     TEXT NOT NULL,            -- "2026-27"
    financial_year      TEXT NOT NULL,            -- "2025-26"
    itr_type            TEXT NOT NULL,            -- "ITR-2"
    regime              TEXT NOT NULL,            -- "NEW" or "OLD"

    -- Summary numbers (NOT the full tax data — just enough for dashboard)
    total_income        BIGINT,                   -- in paise (₹17,54,687 → 175468700)
    gross_tax           BIGINT,                   -- in paise
    tds_total           BIGINT,
    balance_payable     BIGINT,

    -- Filing status tracking
    json_generated_at   TIMESTAMPTZ NOT NULL,     -- When user downloaded JSON
    filed_at            TIMESTAMPTZ,              -- Set when user confirms they filed
    ack_number          TEXT,                     -- ITR-V acknowledgement number
    refund_amount       BIGINT,                   -- Detected from AIS Part B4 or user input
    refund_received_at  TIMESTAMPTZ,

    -- Source tracking
    form16_used         BOOLEAN DEFAULT FALSE,    -- Did user upload Form 16?
    ais_used            BOOLEAN DEFAULT FALSE,    -- Did user upload AIS?
    questions_answered  INT DEFAULT 0,            -- How many of the 0-5 questions

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_filing_history_user ON filing_history(user_id, assessment_year);

-- ============================================
-- TABLE 3: OTP Tokens (auto-expiring)
-- ============================================
CREATE TABLE otp_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT NOT NULL,
    otp_hash    TEXT NOT NULL,                    -- bcrypt(otp)
    purpose     TEXT NOT NULL,                    -- 'signup', 'signin', 'delete_account'
    attempts    INT DEFAULT 0,                    -- Max 3
    expires_at  TIMESTAMPTZ NOT NULL,             -- 5 minutes from creation
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_otp_email ON otp_tokens(email, purpose, expires_at);

-- Auto-cleanup: delete expired tokens
-- Run via pg_cron or application-level scheduler
SELECT cron.schedule('clean-otp', '*/5 * * * *',
    'DELETE FROM otp_tokens WHERE expires_at < NOW()'
);

-- ============================================
-- TABLE 4: Support Requests (optional)
-- ============================================
CREATE TABLE support_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    assessment_year TEXT,
    error_message   TEXT NOT NULL,                -- Portal error the user pasted
    resolution      TEXT,                         -- What fixed it
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 17.3 Redis Session Store (Temporary Tax Data)

```python
# Redis keys and their TTLs
REDIS_KEYS = {
    # Session-scoped tax data — 24 hours
    "session:{session_id}:form16_data": {
        "ttl": 86400,       # 24 hours
        "encrypted": True,  # AES-256 before storing in Redis
        "description": "Parsed Form 16 contents"
    },
    "session:{session_id}:ais_data": {
        "ttl": 86400,
        "encrypted": True,
        "description": "Parsed AIS contents"
    },
    "session:{session_id}:tax_computation": {
        "ttl": 86400,
        "encrypted": False,  # Tax math is not PII
        "description": "Computed tax liability, regime comparison"
    },
    "session:{session_id}:user_answers": {
        "ttl": 86400,
        "encrypted": False,
        "description": "0-5 yes/no question answers"
    },

    # Rate limiting — 15 minutes
    "ratelimit:{ip}:upload": {"ttl": 900},
    "ratelimit:{email}:otp": {"ttl": 900},

    # OTP — 5 minutes
    "otp:{email}:{purpose}": {"ttl": 300},
}
```

### 17.4 Encryption Architecture

```python
# backend/src/utils/crypto.py

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

class DataEncryption:
    """
    Two-layer encryption:
    1. Application-level key (Fernet) for PAN, DOB, mobile in PostgreSQL
    2. Session-level key (per-session Fernet) for Redis tax data

    Master keys live in HashiCorp Vault / AWS KMS — never in code or config.
    """

    def __init__(self, key_provider: KeyProvider):
        self.master_key = key_provider.get_master_key()
        self.fernet = Fernet(self.master_key)

    def encrypt_pan(self, pan: str) -> bytes:
        """Encrypt PAN before PostgreSQL storage."""
        return self.fernet.encrypt(pan.encode())

    def decrypt_pan(self, encrypted: bytes) -> str:
        """Decrypt PAN from PostgreSQL (only when deriving PDF passwords)."""
        return self.fernet.decrypt(encrypted).decode()

    def mask_pan(self, pan: str) -> str:
        """CFFPM4503N → CFFPM****N for display/logging."""
        return f"{pan[:5]}****{pan[-1]}"

    def generate_session_key(self) -> bytes:
        """Per-session key for Redis storage. Auto-destroyed with session."""
        return Fernet.generate_key()

class KeyProvider:
    """
    Production: HashiCorp Vault / AWS KMS / GCP Secret Manager
    Development: Environment variable (never committed)
    """
    def get_master_key(self) -> bytes:
        if ENV == "production":
            return self._fetch_from_vault()
        else:
            key = os.environ.get("ENCRYPTION_KEY")
            if not key:
                raise RuntimeError("ENCRYPTION_KEY not set")
            return base64.b64decode(key)
```

### 17.5 Why This Minimal Approach

| Concern | How We Handle It |
|---|---|
| **IT Act data breach liability** | No financial transaction data persisted. PII encrypted. |
| **User right to deletion** | Soft-delete from PostgreSQL. Redis auto-expires. Zero residual financial data. |
| **PAN as identifier** | Never stored as plaintext. Encrypted at rest. Masked in logs and UI. |
| **Hacker gets DB dump** | Gets email + masked PAN + encrypted blobs they can't decrypt without Vault key. Gets NO salary data, NO bank accounts, NO capital gains. |
| **Compliance audit** | Can prove: no financial data on disk, encryption at rest, 24h auto-purge, audit logs. |
| **Returning user** | Recognizes them by email → sends OTP → loads fresh data from new PDF uploads. |
| **Annual re-filing** | User comes back next year. Enters email → OTP → uploads new PDFs → new session. Previous year's filing history row shows "filed ITR-2 on 28-Jun-2026, refund ₹0". |

---

## 18. Critical Missing Scenarios — What We Didn't Think Of First

> Every one of these is based on real-world tax filing edge cases that WILL happen.
> If the system doesn't handle them, the user is stuck. No fallback. No manual fix.

---

### 18.1 Scenario: The ITR Portal Rejects the JSON

> **We hit this today.** Three validation errors across two JSON upload attempts.
> Each time, the user was stuck until we analyzed the JSON, found the error, and fixed it.

**The System Must:**

```python
class JSONRejectionHandler:
    """
    When the user pastes a portal error message, the system:
    1. Parses the error text using pattern matching
    2. Maps to known fixes
    3. Regenerates the JSON with the fix applied
    4. Presents a NEW download — user never re-enters data
    """

    KNOWN_ERROR_PATTERNS = {
        "is not a valid enum value": {
            "parser": r"The Path: \[(?P<json_path>[^\]]+)\].*is not a valid enum value",
            "action": "fix_enum_value",
            "regenerate": True,
            "user_message": "Fixed an invalid value in your JSON. Download again.",
        },
        "breakup of all the quarters is not equal": {
            "parser": r"In Schedule CG, Table F Sl\. No\. (?P<row>\d+) the breakup",
            "action": "fix_cg_date_ranges_sum",
            "regenerate": True,
            "user_message": "Fixed a 1-rupee rounding error in capital gains. Download again.",
        },
        "Invalid hash value identified": {
            "parser": r"Modification to ITR details outside Utility is not allowed",
            "action": "cannot_fix_directly",
            "regenerate": False,
            "user_message": "This JSON was edited outside the utility. Regenerate through the official ITR utility workflow. We'll guide you.",
        },
        "Secondary Add not found": {
            "parser": r"Secondary Add",
            "action": "set_secondary_add_enum",
            "regenerate": True,
            "user_message": "Fixed secondary address field. Download again.",
        },
        "Only .json files are allowed": {
            "parser": None,
            "action": "check_file_extension",
            "regenerate": False,
            "user_message": "Make sure you're uploading the .json file, not the PDF. The JSON filename starts with 'ITR'.",
        },
    }

    def handle(self, error_text: str, session_id: str) -> FixResult:
        for pattern_name, config in self.KNOWN_ERROR_PATTERNS.items():
            match = re.search(config["parser"], error_text) if config["parser"] else None
            if match or pattern_name in error_text:
                if config["regenerate"]:
                    fix_fn = getattr(self, config["action"])
                    fix_fn(session_id, match)
                    new_json = self.regenerate_json(session_id)
                    return FixResult(
                        fixed=True,
                        message=config["user_message"],
                        download_url=new_json.url,
                    )
                else:
                    return FixResult(
                        fixed=False,
                        message=config["user_message"],
                        manual_steps=self.get_manual_steps(config["action"]),
                    )

        # Unknown error — log for analysis, offer human support
        self.log_unknown_error(error_text, session_id)
        return FixResult(
            fixed=False,
            message="We haven't seen this error before. A CA will review your JSON within 2 hours.",
            support_ticket_id=self.create_support_ticket(error_text, session_id),
        )
```

---

### 18.2 Scenario: User Has No Form 16

**Why this happens:**
- Employer hasn't issued it yet (common before June)
- User left the job and employer is unresponsive
- User is a consultant / freelancer with only TDS entries in AIS
- User has ONLY capital gains and interest income (no salary at all)

**System Response:**

```python
class MissingDocumentHandler:
    """
    Adapts the flow based on which documents are available.
    The system works with ANY combination of AIS, Form 16, and Form 26AS.
    """

    def determine_filing_path(self, available_docs: AvailableDocuments) -> FilingPath:
        if available_docs.form16 and available_docs.ais:
            return FilingPath.FULL_AUTO    # Best case — everything auto-detected
        elif available_docs.ais and not available_docs.form16:
            return FilingPath.AIS_ONLY     # Salary from AIS TDS entries, no breakup
        elif available_docs.form16 and not available_docs.ais:
            return FilingPath.FORM16_ONLY  # Missing capital gains info — warn user
        else:
            return FilingPath.MANUAL_ENTRY # Neither — guided manual data entry fallback

class AISOnlySalaryExtractor:
    """
    When Form 16 is unavailable, extract salary info from AIS TDS-192 entries.
    Less detail (no HRA/LTA breakup), but enough for basic filing.
    """
    def extract_salary_from_ais(self, ais: AISData) -> PartialSalaryData:
        tds_192 = [e for e in ais.salary_tds if e.information_code == "TDS-192"]
        return PartialSalaryData(
            total_salary=sum(e.amount_paid for e in tds_192),
            total_tds=sum(e.tds_deducted for e in tds_192),
            employer_name=tds_192[0].information_source if tds_192 else "Unknown",
            employer_tan=None,  # Not available in AIS
            has_full_breakdown=False,  # Triggers: skip HRA/LTA questions
        )
```

---

### 18.3 Scenario: User Changed Jobs Mid-Year (Multiple Form 16s)

**Detection:**

```python
class MultiEmployerDetector:
    """
    Detects job changes from AIS TDS-192 entries with different deductor TANs,
    or from multiple Form 16 uploads.
    """
    def detect(self, form16_list: list[Form16Data], ais: AISData) -> MultiEmployerResult:
        unique_tans = set()
        employers = []

        # From Form 16s
        for f16 in form16_list:
            unique_tans.add(f16.part_a.employer_tan)
            employers.append(EmployerPeriod(
                name=f16.part_a.employer_name,
                tan=f16.part_a.employer_tan,
                from_date=f16.part_a.period_from,
                to_date=f16.part_a.period_to,
                salary=f16.part_b.salary_171,
                tds=f16.part_a.total_tds_deducted,
            ))

        # From AIS (if Form 16 not uploaded for one employer)
        tds_by_deductor = defaultdict(list)
        for entry in ais.salary_tds:
            tds_by_deductor[entry.information_source].append(entry)

        if len(employers) > 1:
            return MultiEmployerResult(
                is_multi=True,
                employers=employers,
                total_salary=sum(e.salary for e in employers),
                total_tds=sum(e.tds for e in employers),
                warning="Multiple employers detected. Each employer's TDS will be reported. "
                        "Standard deduction applies only once (₹75,000 total).",
            )
        return MultiEmployerResult(is_multi=False)
```

**ITR Impact:**
- Schedule S: Multiple employer entries (Employer 1, Employer 2...)
- Standard deduction: ₹75,000 total, NOT per employer
- Each employer's TAN and TDS reported separately in Schedule TDS1
- Professional tax: combined from both Form 16s if applicable

---

### 18.4 Scenario: Form 26AS / AIS / Form 16 TDS Mismatch

> **The #1 cause of ITR processing delays and CPC notices.**
> If TDS in Form 16 ≠ TDS in Form 26AS, the CPC will not grant the credit.

```python
class TDSReconciler:
    """
    Three-way reconciliation: Form 16 TDS ↔ AIS TDS ↔ Form 26AS TDS.

    If user hasn't uploaded Form 26AS, we flag: "Please download Form 26AS
    from TRACES to maximize your TDS credit."
    """

    def reconcile(self, form16: Optional[Form16Data],
                  ais: AISData,
                  form26as: Optional[Form26ASData]) -> ReconciliationReport:

        report = ReconciliationReport()

        # 1. Form 16 vs AIS
        if form16:
            f16_tds = form16.part_a.total_tds_deducted
            ais_tds = sum(e.tds_deducted for e in ais.salary_tds)
            if abs(f16_tds - ais_tds) > 1:  # Allow ₹1 rounding
                report.add_warning(
                    severity="HIGH",
                    message=f"Form 16 TDS (₹{f16_tds}) ≠ AIS TDS (₹{ais_tds}). "
                            f"AIS is the authoritative source for TDS credit. "
                            f"Your ITR will use the AIS value.",
                )

        # 2. AIS vs Form 26AS (if available)
        if form26as:
            for tds_entry in ais.salary_tds:
                match = form26as.find_matching_entry(
                    deductor_tan=tds_entry.source_id,
                    amount=tds_entry.tds_deducted,
                    date=tds_entry.date_of_payment,
                )
                if not match:
                    report.add_warning(
                        severity="MEDIUM",
                        message=f"TDS of ₹{tds_entry.tds_deducted} from "
                                f"{tds_entry.information_source} found in AIS "
                                f"but NOT in Form 26AS. This credit may be denied.",
                    )

        # 3. Non-salary TDS (FDs, NSCs, etc.) — these are FREE REFUNDS
        non_salary_tds = [e for e in ais.other_tds if e.information_code != "TDS-192"]
        if non_salary_tds:
            total = sum(e.tds_deducted for e in non_salary_tds)
            report.add_info(
                message=f"Found ₹{total} in non-salary TDS (bank FDs, etc.). "
                        f"This will increase your refund or reduce your tax payable.",
                impact=total,  # Positive impact
            )

        return report
```

**User-Facing Warning (Before JSON Generation):**

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠ TDS MISMATCH DETECTED                                     │
│                                                              │
│  Your Form 16 shows TDS:        ₹1,55,738                   │
│  Your AIS shows TDS:            ₹1,55,738  ✅ Match          │
│                                                              │
│  We recommend uploading your Form 26AS (from TRACES portal)  │
│  to three-way verify your TDS credit.                        │
│                                                              │
│  Without Form 26AS, we'll use AIS as the TDS credit source.  │
│                                                              │
│  [ I'll upload Form 26AS ]    [ Continue without it ]       │
└──────────────────────────────────────────────────────────────┘
```

---

### 18.5 Scenario: Advance Tax & Interest Liability (234A/B/C)

> **We almost missed this with Aman.** His TDS covered 99.2% of tax, so no interest
> was due. But for any user with significant non-salary income (capital gains >₹10,000,
> freelancing), advance tax may be due, and interest under 234A/B/C applies.

```python
class AdvanceTaxComputer:
    """
    Determines if advance tax was required and computes interest.
    This is CRITICAL for users with capital gains or business income.
    """

    def compute(self, tax_data: UnifiedTaxData) -> AdvanceTaxResult:
        total_tax = tax_data.final_tax_liability
        tds = tax_data.form16.part_a.total_tds_deducted

        # Rule: If (Total Tax - TDS) ≤ ₹10,000, no advance tax needed
        shortfall = total_tax - tds
        if shortfall <= 10000:
            return AdvanceTaxResult(
                advance_tax_required=False,
                interest_234b=0,
                interest_234c=0,
                message="Your TDS covers your tax liability. No advance tax was required.",
            )

        # Advance tax due dates and required percentages
        advance_tax_schedule = [
            ("15-Jun", 0.15),    # 15% of advance tax by June 15
            ("15-Sep", 0.45),    # 45% by Sep 15
            ("15-Dec", 0.75),    # 75% by Dec 15
            ("15-Mar", 1.00),    # 100% by Mar 15
        ]

        # Interest u/s 234B: If <90% of tax paid by March 31
        total_paid = tds + tax_data.self_assessment_tax  # SAT paid before filing
        if total_paid < total_tax * 0.90:
            interest_234b = (total_tax - total_paid) * 0.01 * months_of_default
        else:
            interest_234b = 0

        # Interest u/s 234C: Deferment of advance tax installments
        interest_234c = self._compute_234c(total_tax, tds, actual_payments_by_date)

        # Interest u/s 234A: Late filing (after July 31)
        if filing_date > due_date:
            interest_234a = shortfall * 0.01 * months_late

        return AdvanceTaxResult(
            advance_tax_required=True,
            shortfall=shortfall,
            interest_234a=interest_234a,
            interest_234b=interest_234b,
            interest_234c=interest_234c,
            total_interest=interest_234a + interest_234b + interest_234c,
            message=f"You should have paid ₹{shortfall} as advance tax. "
                    f"Interest of ₹{total_interest} will be added to your liability.",
        )
```

**User Warning:**

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠ ADVANCE TAX INTEREST APPLIES                              │
│                                                              │
│  Your capital gains of ₹5,194 created a tax shortfall.       │
│  Since you had no advance tax for these gains:               │
│                                                              │
│  Interest u/s 234B:  ₹0 (TDS covers >90% of total tax)      │
│  Interest u/s 234C:  ₹0 (shortfall ≤ ₹10,000)               │
│                                                              │
│  ✅ No interest is due. Good.                                 │
│                                                              │
│  ⚠ For next year: If your non-salary income exceeds          │
│     ₹10,000 in tax, pay advance tax by the quarterly          │
│     deadlines to avoid interest.                              │
└──────────────────────────────────────────────────────────────┘
```

---

### 18.6 Scenario: User Already Filed — Needs Revised Return

**Detection:**

```python
class PriorFilingDetector:
    """
    Checks if a return already exists for this PAN + Assessment Year.
    Uses AIS Part B4 refund data + user questioning.
    """

    def detect(self, pan: str, assessment_year: str) -> PriorFilingResult:
        # Query our own filing_history table
        existing = db.query(FilingHistory).filter(
            FilingHistory.user.pan_masked == mask_pan(pan),
            FilingHistory.assessment_year == assessment_year,
        ).first()

        if existing and existing.filed_at:
            return PriorFilingResult(
                already_filed=True,
                filed_on=existing.filed_at,
                original_ack_number=existing.ack_number,
                action="REVISED",
                message=f"You filed on {existing.filed_at}. "
                        f"If you need to correct anything, file a REVISED return "
                        f"u/s 139(5) using the original acknowledgement number.",
            )

        return PriorFilingResult(already_filed=False)
```

**In the Export Screen (Step 4 adapts):**

```
If already_filed:
    Filing Type: [ Revised u/s 139(5) ]  ← Auto-selected
    Original Acknowledgement No: [ ________________ ]  ← Required

If NOT already_filed:
    Filing Type: [ Original u/s 139(1) ]  ← Auto-selected
```

---

### 18.7 Scenario: User Has Capital Losses to Carry Forward

> **Critical for traders and active investors.** If you don't file your ITR by the
> due date (July 31), you LOSE the right to carry forward capital losses. Forever.

```python
class LossHarvestingAdvisor:
    """
    1. Detects capital losses from AIS
    2. Ensures they're correctly classified (STCL, LTCL)
    3. Warns if filing after due date (losses cannot be carried forward)
    4. Suggests tax-loss harvesting opportunities
    """

    def analyze(self, ais: AISData, filing_date: date) -> LossAnalysis:
        losses = self._extract_losses(ais)

        result = LossAnalysis(
            stcl_equity=Decimal("0"),       # Short-term capital loss (equity)
            stcl_non_equity=Decimal("0"),    # Short-term capital loss (non-equity)
            ltcl_equity=Decimal("0"),        # Long-term capital loss (equity)
            ltcl_non_equity=Decimal("0"),    # Long-term capital loss (non-equity)
        )

        for sale in ais.sft.all_sales:
            gain = sale.sale_consideration - sale.cost_of_acquisition
            if gain < 0:
                result.add_loss(abs(gain), sale.term, sale.asset_class)

        # Critical warning
        if result.has_losses and filing_date > DUE_DATE:
            result.add_critical_warning(
                "You have ₹{losses} in capital losses. Filing after July 31 means "
                "these losses CANNOT be carried forward to next year. You will "
                "permanently lose this tax benefit. File BEFORE July 31."
            )

        if result.has_losses and filing_date <= DUE_DATE:
            result.add_info(
                "You have ₹{losses} in capital losses. Filing by July 31 preserves "
                "your right to carry these forward for 8 years and set them off "
                "against future capital gains."
            )

        return result
```

---

### 18.8 Scenario: PAN-Aadhaar Not Linked

```python
def check_pan_aadhaar_link_status(pan: str) -> PANLinkStatus:
    """
    Calls NSDL API to check PAN-Aadhaar link status.
    If not linked: BLOCK filing until linked + 24h cooldown.
    """
    status = nsdl_api.check_link_status(pan)

    if not status.linked:
        return PANLinkStatus(
            linked=False,
            can_file=False,
            message="Your PAN and Aadhaar are not linked. "
                    "The IT department WILL NOT process your return. "
                    f"Link them now: incometax.gov.in → Link PAN-Aadhaar. "
                    f"Late fee: ₹1,000. Wait 24 hours after linking, then file.",
            block_filing=True,
        )

    return PANLinkStatus(linked=True, can_file=True)
```

---

### 18.9 Scenario: Previous Year Refund Still Pending

> **AIS Part B4 shows refunds.** If last year's refund is still pending, the system
> should flag it — the user may need to file a rectification or check their bank details.

```python
def check_pending_refunds(ais: AISData) -> list[RefundAlert]:
    alerts = []
    for refund in ais.refunds:
        if refund.financial_year != CURRENT_FY:
            days_since = (date.today() - refund.date_of_payment).days
            if days_since > 90:
                alerts.append(RefundAlert(
                    fy=refund.financial_year,
                    amount=refund.amount,
                    status="UNUSUALLY_DELAYED" if days_since > 180 else "PENDING",
                    action="Check refund status on incometax.gov.in → Refund Reissue",
                ))
    return alerts
```

---

### 18.10 Scenario: Zero-Document Filing

> **Neither Form 16 nor AIS available.**
> Possible reasons: newly employed, first-time filer, documents not yet generated.

```python
class ZeroDocumentFallback:
    """
    When the user has zero documents, the system becomes a guided manual-entry ITR tool.
    Still better than the ITD portal — the system knows all the rules, schedules, and math.
    """

    def guided_manual_flow(self, user: User) -> ManualFilingSession:
        questions = [
            "What was your total salary this year? (Check your payslips)",
            "Any TDS deducted? (Check your March payslip)",
            "Any bank FDs or savings accounts? (Approximate interest)",
            "Did you trade in stocks, mutual funds, or crypto?",
            "Any rent paid? Home loan? Health insurance?",
        ]
        # System builds ITR from answers — same engine, manual inputs
        # Less accurate, but better than not filing at all
        return ManualFilingSession(questions)
```

---

## 19. Development Roadmap (Updated)

| Phase | Timeline | Deliverables |
|---|---|---|
| **Phase 0: Auth + User Management** | Week 1 | Sign-up with PAN+DOB+Name+Email. Email OTP. NSDL PAN verification. Google OAuth. User sessions. |
| **Phase 1: Core Parsers** | Week 1-2 | Form 16 parser + AIS parser working on real PDFs. Password auto-resolution. Tested on our 3 files. |
| **Phase 2: Classification** | Week 3 | AIS code → ITR schedule mapper. CG classifier. Date range auto-computer. |
| **Phase 3: Regime Engine** | Week 4 | Old vs New regime computer. All deduction calculations. |
| **Phase 4: JSON Builder** | Week 5-6 | ITR-2 JSON builder. All 15+ schedules. Template-based for ITR-1/3/4. |
| **Phase 5: Validator** | Week 7 | 20+ cross-validation rules. Schema compliance checker. |
| **Phase 6: Export UX + Error Recovery** | Week 8 | Crystal-clear 8-step portal instructions. JSON rejection auto-detection & regeneration from known error patterns. Context-aware payment steps. Post-filing email follow-up. |
| **Phase 7: Missing Scenario Handlers** | Week 9 | Multi-Form 16 merger. AIS-only / Form 16-only paths. TDS reconciliation (AIS vs 26AS vs Form 16). Advance tax & 234A/B/C interest computer. Capital loss carry-forward. PAN-Aadhaar link check. Prior-year refund/pending demand check. Revised return detection. Zero-document guided manual fallback. |
| **Phase 8: Frontend** | Week 9-10 | React upload → questions → review → export flow. All screens. Error paste-and-fix UI. Document-less guided flow. |
| **Phase 8: Testing** | Week 10 | Test on 50+ anonymized Form 16 + AIS pairs. Compare output with manually filed returns. |
| **Phase 9: Launch** | Week 11 | Deploy. Soft launch with CA community. |
| **Phase 10: API Integrations** | Week 12-14 | NSDL PAN verification (Week 12). Account Aggregator for AIS/26AS fetch (Week 14+). |
| **Phase 11: Mobile App** | Week 14-16 | React Native app with document scanner. |

---

## 20. Immediate Next Actions

- [x] Create `ARCHITECTURE.md` — Full system design
- [x] Create `DATA_MODEL.md` — Complete pydantic model definitions
- [x] Create `ITR_TYPES_QUESTIONS.md` — Decision trees per ITR type
- [ ] Set up PostgreSQL schema (`users`, `filing_history`, `otp_tokens`) — Run the SQL in §17.2
- [ ] Set up Redis with TTL policies for session tax data
- [ ] Deploy HashiCorp Vault / configure AWS KMS for encryption keys
- [ ] Write `backend/src/auth/` — OTP-based signup/signin, Google OAuth
- [ ] Write `backend/src/integrations/pan_verify.py` — NSDL PAN verification at signup
- [ ] Write `backend/src/parsers/form16.py` — Start with the Form 16 we already parsed
- [ ] Write `backend/src/parsers/ais.py` — AIS parser from our JSON extraction code
- [ ] Write `backend/src/api/export.py` — JSON download + 8-step portal instruction generator
- [ ] Set up project skeleton with FastAPI + Next.js
- [ ] Create anonymized test fixtures from our real data
- [ ] Don't forget: `support_requests` table for portal error pattern detection
