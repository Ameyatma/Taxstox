# Data Models — Complete Type Definitions

> Every structure we extracted, classified, and built today — formalized as Pydantic v2 models.
> These models are the single source of truth shared across parsers, engine, builder, and validator.

---

## 1. Form 16 Data Model

```python
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal
from typing import Optional
from enum import Enum

class Regime(str, Enum):
    OLD = "old"
    NEW = "new"

class Form16PartA(BaseModel):
    """Form 16 Part A — Employer & TDS Details"""
    certificate_no: str                          # SXLREKA
    employer_name: str                           # APPLIED MATERIALS INDIA PVT LTD
    employer_address: str
    employer_tan: str                            # BLRA04654G
    employer_pan: str                            # AAECA2635C
    employee_name: str                           # AMAN KUMAR MISHRA
    employee_pan: str                            # CFFPM4503N
    employee_address: str
    assessment_year: str                         # 2026-27
    period_from: date                            # 2025-04-01
    period_to: date                              # 2026-03-31
    cit_tds_jurisdiction: str

    quarterly_tds: list["QuarterlyTDS"]

    total_amount_paid: Decimal                   # 18,71,602
    total_tds_deducted: Decimal                  # 1,55,738
    total_tds_deposited: Decimal                 # 1,55,738

class QuarterlyTDS(BaseModel):
    quarter: str                                 # Q1, Q2, Q3, Q4
    receipt_number: str                          # QWBOIUDA
    amount_paid: Decimal                         # 3,93,000
    tds_deducted: Decimal                        # 25,682
    tds_deposited: Decimal                       # 25,682

class Form16PartB(BaseModel):
    """Form 16 Part B — Salary Detail & Tax Computation"""
    opting_out_115bac: bool                      # True = opted OUT of new regime (old regime)
                                                 # False = in new regime (115BAC)

    # Section 17 — Gross Salary
    salary_171: Decimal                          # 18,71,602
    perquisites_172: Decimal                     # 0
    profits_lieu_173: Decimal                    # 0
    total_gross_salary: Decimal                  # 18,71,602

    # Section 10 — Exempt Allowances
    exemptions_s10: "Section10Exemptions"

    # Section 16 — Deductions from Salary
    std_deduction_16ia: Decimal                  # 75,000 (new) / 50,000 (old)
    entertainment_16ii: Decimal                  # 0
    professional_tax_16iii: Decimal              # 0

    income_under_head_salaries: Decimal          # 17,96,602
    other_income_reported: Decimal               # 0
    gross_total_income: Decimal                  # 17,96,602

    chapter_vi_a: "ChapterVIADeductions"
    taxable_income: Decimal                      # 17,48,733
    tax_computation: "TaxComputation"

class Section10Exemptions(BaseModel):
    """Allowances exempt under section 10"""
    travel_concession_105: Decimal               # 10(5) LTA
    gratuity_1010: Decimal                       # 10(10)
    commuted_pension_1010A: Decimal
    leave_encashment_1010AA: Decimal
    hra_1013A: Decimal                           # 10(13A) House Rent Allowance
    special_allowances_1014: Decimal              # 10(14)
    other_exemptions_s10: list["OtherExemption"]

    @property
    def total(self) -> Decimal:
        return (self.travel_concession_105 + self.gratuity_1010 +
                self.commuted_pension_1010A + self.leave_encashment_1010AA +
                self.hra_1013A + self.special_allowances_1014 +
                sum(e.amount for e in self.other_exemptions_s10))

class OtherExemption(BaseModel):
    description: str
    gross_amount: Decimal
    qualifying_amount: Decimal
    deductible_amount: Decimal

class ChapterVIADeductions(BaseModel):
    """Deductions under Chapter VI-A"""
    sec80c: Decimal = Decimal("0")               # EPF, PPF, ELSS, LIC, etc. (max 1.5L)
    sec80ccc: Decimal = Decimal("0")             # Pension fund
    sec80ccd1: Decimal = Decimal("0")            # Employee NPS (within 80C limit)
    sec80ccd1b: Decimal = Decimal("0")           # Additional NPS (max 50K)
    sec80ccd2: Decimal = Decimal("0")            # Employer NPS (max 10% of Basic)
    sec80d: Decimal = Decimal("0")               # Health insurance
    sec80dd: Decimal = Decimal("0")              # Disabled dependent
    sec80ddb: Decimal = Decimal("0")             # Medical treatment
    sec80e: Decimal = Decimal("0")               # Education loan interest
    sec80ee: Decimal = Decimal("0")              # Home loan interest (first-time)
    sec80eea: Decimal = Decimal("0")             # Affordable housing
    sec80eeb: Decimal = Decimal("0")             # Electric vehicle
    sec80g: Decimal = Decimal("0")               # Donations
    sec80gg: Decimal = Decimal("0")              # Rent paid (no HRA)
    sec80gga: Decimal = Decimal("0")             # Scientific research donations
    sec80ggc: Decimal = Decimal("0")             # Political donations
    sec80tta: Decimal = Decimal("0")             # Savings interest (max 10K)
    sec80ttb: Decimal = Decimal("0")             # Senior citizen deposit interest
    sec80u: Decimal = Decimal("0")               # Disability
    sec80cch: Decimal = Decimal("0")             # Agnipath scheme

    @property
    def total(self) -> Decimal:
        return sum([
            self.sec80c, self.sec80ccc, self.sec80ccd1, self.sec80ccd1b,
            self.sec80ccd2, self.sec80d, self.sec80dd, self.sec80ddb,
            self.sec80e, self.sec80ee, self.sec80eea, self.sec80eeb,
            self.sec80g, self.sec80gg, self.sec80gga, self.sec80ggc,
            self.sec80tta, self.sec80ttb, self.sec80u, self.sec80cch,
        ])

class TaxComputation(BaseModel):
    taxable_income: Decimal                      # 17,48,733
    tax_on_income: Decimal                       # 1,49,747
    rebate_87a: Decimal                          # 0
    surcharge: Decimal                           # 0
    health_education_cess: Decimal               # 5,990
    tax_payable: Decimal                         # 1,55,737
    relief_89: Decimal                           # 0
    net_tax_payable: Decimal                     # 1,55,737

class SalaryComponent(BaseModel):
    """Individual salary component from Annexure"""
    name: str                                    # Basic, HRA, Special Allowance, etc.
    amount: Decimal
    nature: str                                  # Fully Taxable, Partly Exempt, Exempt

class Form16Annexure(BaseModel):
    """Salary breakup from Annexure to Form 16"""
    components: list[SalaryComponent]

    # Extracted components — auto-detected from Annexure text
    basic: Decimal
    hra: Decimal
    special_allowance: Decimal
    lta: Decimal
    lunch_coupons: Decimal                       # 24,000
    broadband_reimbursement: Decimal             # 12,000
    special_award: Decimal                       # 4,000
    nps_employer: Decimal                        # 47,869
    dbip_bonus: Decimal                          # 1,60,198
    # ... other components as present in Annexure

class Form12BA(BaseModel):
    """Perquisites valuation from Form 12BA"""
    income_under_head_salaries: Decimal
    perquisites: "PerquisitesDetail"

class PerquisitesDetail(BaseModel):
    """21 perquisite types from Form 12BA"""
    accommodation: Decimal = Decimal("0")
    car: Decimal = Decimal("0")
    sweeper_gardener_attendant: Decimal = Decimal("0")
    gas_electricity_water: Decimal = Decimal("0")
    rsu: Decimal = Decimal("0")                  # Restricted Stock Units
    espp: Decimal = Decimal("0")                 # Employee Stock Purchase Plan
    loan: Decimal = Decimal("0")
    free_meals: Decimal = Decimal("0")
    free_education: Decimal = Decimal("0")
    gifts_vouchers: Decimal = Decimal("0")
    credit_card: Decimal = Decimal("0")
    club_expenses: Decimal = Decimal("0")
    movable_assets: Decimal = Decimal("0")
    asset_transfer: Decimal = Decimal("0")
    other_benefit: Decimal = Decimal("0")
    stock_options_startup_80iac: Decimal = Decimal("0")
    stock_options_non_qualified: Decimal = Decimal("0")
    employer_contribution_fund: Decimal = Decimal("0")
    accretion_fund: Decimal = Decimal("0")
    other_benefits: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        return sum([
            self.accommodation, self.car, self.sweeper_gardener_attendant,
            self.gas_electricity_water, self.rsu, self.espp, self.loan,
            self.free_meals, self.free_education, self.gifts_vouchers,
            self.credit_card, self.club_expenses, self.movable_assets,
            self.asset_transfer, self.other_benefit, self.stock_options_startup_80iac,
            self.stock_options_non_qualified, self.employer_contribution_fund,
            self.accretion_fund, self.other_benefits,
        ])

class Form16Data(BaseModel):
    """Complete Form 16 data"""
    part_a: Form16PartA
    part_b: Form16PartB
    annexure: Form16Annexure
    form_12ba: Optional[Form12BA] = None

    # Derived properties
    @property
    def regime(self) -> Regime:
        return Regime.OLD if self.part_b.opting_out_115bac else Regime.NEW

    @property
    def effective_salary(self) -> Decimal:
        return self.part_b.income_under_head_salaries
```

---

## 2. AIS Data Model

```python
class AISTDSEntry(BaseModel):
    """Single TDS entry from AIS Part B1"""
    information_code: str                       # TDS-192
    information_source: str                     # APPLIED MATERIALS INDIA PVT LTD
    quarter: str                                # Q4(Jan-Mar)
    date_of_payment: date                       # 2026-03-31
    amount_paid: Decimal                        # 1,53,600
    tds_deducted: Decimal                       # 12,257
    tds_deposited: Decimal                      # 12,257
    status: str                                 # Active

class AISSavingsInterest(BaseModel):
    """SFT-016(SB) — Savings Bank Interest"""
    bank_name: str                              # STATE BANK OF INDIA
    bank_pan: str                               # AAACS8577K
    account_number: str                         # 20132242544
    account_type: str                           # Saving
    interest_amount: Decimal                    # 407
    reported_on: date                           # 2026-05-28

class AISEquityMFSale(BaseModel):
    """SFT-18-EMF(M) — Equity Mutual Fund Sale"""
    amc_name: str                               # Quant MF
    isin: str                                   # INF966L01986
    security_name: str                          # Quant ELSS Tax Saver Fund...
    date_of_sale: date                          # 2025-12-29
    quantity: Decimal                           # 46.58
    sale_price_per_unit: Decimal                # 420.83
    sale_consideration: Decimal                 # 19,603
    stt_paid: Decimal                           # 0.20
    cost_of_acquisition: Decimal                # 12,500
    debit_type: str                             # redemption
    credit_type: str                            # purchase
    asset_type: str                             # AMC
    term: str                                   # Long
    unit_fmv: Decimal                           # 0
    fair_market_value: Decimal                  # 0
    indexed_cost: Decimal                       # 0
    status: str                                 # Active

class AISOtherUnitSale(BaseModel):
    """SFT-17-OTU(M) — Non-Equity Unit Sale (ETF, Debt Fund)"""
    depository: str                             # CDSL
    security_name: str                          # TATA ASSET MANAGEMENT LTD#TATA MF...
    isin: str                                   # INF277KA1976
    date_of_sale: date                          # 2026-02-27
    quantity: Decimal                           # 5
    sale_price: Decimal                         # 15.38
    sale_consideration: Decimal                 # 77
    cost_of_acquisition: Decimal                # 76.20
    term: str                                   # Short
    unit_fmv: Decimal                           # 0
    fair_market_value: Decimal                  # 0
    indexed_cost: Decimal                       # 0
    status: str                                 # Active

class AISSecuritiesPurchase(BaseModel):
    """SFT-17(Pur) — Securities Purchases (depository)"""
    depository: str
    client_id: str
    holder_flag: str
    market_purchase: Decimal                    # 2,22,959
    market_sales: Decimal                       # 85,145
    status: str

class AISRefund(BaseModel):
    """AIS Part B4 — Refund received"""
    financial_year: str                         # 2024-25
    mode: str                                   # ECS
    nature: str
    amount: Decimal                             # 7,830
    date_of_payment: date                       # 2025-07-07

class AISAnnexureIISalary(BaseModel):
    """AIS Part B7 — Annexure II Salary (cross-reference)"""
    information_source: str
    employment_start: date
    employment_end: date
    gross_salary_171: Decimal                   # 18,71,602
    perquisites_172: Decimal                    # 0
    profits_lieu_173: Decimal                   # 0
    total_gross_salary: Decimal                 # 18,71,602

class AISData(BaseModel):
    """Complete Annual Information Statement data"""
    # Part A: Personal Info
    pan: str
    aadhaar_masked: str
    name: str
    dob: date
    mobile: str
    email: str
    address: str

    # Part B1: TDS
    salary_tds: list[AISTDSEntry]
    other_tds: list[AISTDSEntry] = []

    # Part B2: SFT
    savings_interest: list[AISSavingsInterest] = []
    term_deposit_interest: list = []
    equity_mf_sales: list[AISEquityMFSale] = []
    other_unit_sales: list[AISOtherUnitSale] = []
    securities_purchases: list[AISSecuritiesPurchase] = []
    # ... other SFT types as needed

    # Part B3: Tax Payments
    tax_payments: list = []

    # Part B4: Refunds
    refunds: list[AISRefund] = []

    # Part B7: Other Information
    annexure_ii_salary: Optional[AISAnnexureIISalary] = None

    @property
    def total_non_salary_tds(self) -> Decimal:
        return sum(e.tds_deducted for e in self.other_tds)

    @property
    def total_savings_interest(self) -> Decimal:
        return sum(e.interest_amount for e in self.savings_interest)
```

---

## 3. Unified Tax Data Model

```python
class CGSaleEntry(BaseModel):
    """A single capital gain transaction, classified and ready for ITR"""
    # From AIS
    date: date
    isin: str
    security_name: str
    quantity: Decimal
    sale_price: Decimal
    consideration: Decimal
    cost: Decimal
    stt_paid: bool
    term: str                                   # Long / Short
    asset_class: str                            # equity_mf, etf_gold, etf_silver, debt_fund

    # Computed
    gain: Decimal                               # consideration - cost
    tax_rate: str                               # 12.5%, 15%, Slab rate
    itr_section: str                            # 112A, 111A, A5, B8
    itr_schedule: str                           # Schedule112A, ScheduleCG_A2, etc.

    # For 112A exemption
    qualifies_for_125k_exemption: bool
    gain_after_exemption: Decimal

    @property
    def period(self) -> str:
        """Map date to ITR date period"""
        m, d = self.date.month, self.date.day
        if (m == 4) or (m == 5) or (m == 6 and d <= 15):
            return "Upto15Of6"
        elif (m == 6 and d >= 16) or (m == 7) or (m == 8) or (m == 9 and d <= 15):
            return "Upto15Of9"
        elif (m == 9 and d >= 16) or (m == 10) or (m == 11) or (m == 12 and d <= 15):
            return "Up16Of9To15Of12"
        elif (m == 12 and d >= 16) or (m == 1) or (m == 2) or (m == 3 and d <= 15):
            return "Up16Of12To15Of3"
        else:
            return "Up16Of3To31Of3"

class CGDateRanges(BaseModel):
    """Capital gains split by ITR date periods — for Schedule CG Section F"""
    ltcg_12_5pct: dict[str, Decimal] = Field(default_factory=lambda: {
        "Upto15Of6": Decimal("0"),
        "Upto15Of9": Decimal("0"),
        "Up16Of9To15Of12": Decimal("0"),
        "Up16Of12To15Of3": Decimal("0"),
        "Up16Of3To31Of3": Decimal("0"),
    })
    stcg_app_rate: dict[str, Decimal] = Field(default_factory=lambda: {
        "Upto15Of6": Decimal("0"),
        "Upto15Of9": Decimal("0"),
        "Up16Of9To15Of12": Decimal("0"),
        "Up16Of12To15Of3": Decimal("0"),
        "Up16Of3To31Of3": Decimal("0"),
    })
    stcg_20pct: dict[str, Decimal] = Field(default_factory=dict)   # For 111A
    stcg_30pct: dict[str, Decimal] = Field(default_factory=dict)   # For 115BBH

    def validate_sums(self, bfla_ltcg: Decimal, bfla_stcg: Decimal) -> bool:
        ltcg_sum = sum(self.ltcg_12_5pct.values())
        stcg_sum = sum(self.stcg_app_rate.values())
        return ltcg_sum == bfla_ltcg and stcg_sum == bfla_stcg

class UserAnswers(BaseModel):
    """The 0-5 answers the user provides"""
    pays_rent: bool = False
    rent_per_month: Decimal = Decimal("0")
    rent_city_metro: bool = True
    landlord_pan: str = ""

    has_health_insurance: bool = False
    health_premium_self: Decimal = Decimal("0")
    health_premium_parents: Decimal = Decimal("0")
    parents_senior_citizen: bool = False

    has_additional_80c: bool = False
    additional_80c_breakup: dict = Field(default_factory=dict)

    has_home_loan: bool = False
    home_loan_interest: Decimal = Decimal("0")
    home_loan_self_occupied: bool = True

    has_other_income: bool = False
    other_income_details: list = Field(default_factory=list)

class UnifiedTaxData(BaseModel):
    """All parsed + user-provided data, ready for JSON building"""
    pan: str
    dob: date
    form16: Form16Data
    ais: AISData
    user_answers: UserAnswers

    # Auto-classified
    capital_gains: "ClassifiedCGData"
    regime_result: "RegimeResult"

    # Final computation
    final_total_income: Decimal
    final_tax_liability: Decimal
    final_balance_payable: Decimal
    recommended_regime: Regime

class ClassifiedCGData(BaseModel):
    """All capital gains classified into ITR schedule buckets"""
    schedule_112a: list[CGSaleEntry] = []       # Equity LTCG — Schedule 112A
    cg_a2_stcg_111a: list[CGSaleEntry] = []      # Equity STCG — CG A2 (15%)
    cg_a5_stcg_app_rate: list[CGSaleEntry] = []  # Non-equity STCG — CG A5 (slab)
    cg_b8_ltcg_other: list[CGSaleEntry] = []     # Non-equity LTCG — CG B8 (12.5%+indexation)
    date_ranges: CGDateRanges

    @property
    def total_stcg(self) -> Decimal:
        return (sum(e.gain for e in self.cg_a5_stcg_app_rate) +
                sum(e.gain for e in self.cg_a2_stcg_111a))

    @property
    def total_ltcg(self) -> Decimal:
        return (sum(e.gain for e in self.schedule_112a) +
                sum(e.gain for e in self.cg_b8_ltcg_other))

    @property
    def total_cg(self) -> Decimal:
        return self.total_stcg + self.total_ltcg

class RegimeResult(BaseModel):
    """Output of RegimeOptimizer"""
    old_tax: Decimal
    new_tax: Decimal
    recommended: Regime
    savings: Decimal
    old_breakdown: dict
    new_breakdown: dict
```

---

## 4. Request / Response Models

```python
class UploadResponse(BaseModel):
    session_id: str
    status: str                                 # "parsed", "password_required", "error"
    data_summary: Optional[dict]                # Brief summary for UI
    password_required: bool
    password_hint: Optional[str]                # "Try your PAN (lowercase)"

class QuestionsResponse(BaseModel):
    itr_type: str                               # ITR-2
    regime_recommended: Regime
    regime_savings: Decimal
    income_summary: dict
    questions: list["Question"]

class Question(BaseModel):
    id: str
    text: str
    type: str                                   # yes_no, number, dropdown
    sub_questions: Optional[list["Question"]] = None
    impact: str                                 # Human-readable impact description
    suppressible: bool = True

class TaxSummaryResponse(BaseModel):
    """The one-page review card"""
    income: dict[str, Decimal]
    deductions: dict[str, Decimal]
    taxable_income: Decimal
    tax_breakdown: dict[str, Decimal]
    payments: dict[str, Decimal]
    balance_payable: Decimal
    regime: Regime
    regime_savings: Decimal
    filing_deadline: date

class ExportResponse(BaseModel):
    """Download-ready ITR JSON"""
    filename: str
    json_data: dict
    validation_passed: bool
    validation_warnings: list[str] = []
```

---

## 5. Validation Result Models

```python
class ValidationResult(BaseModel):
    check_name: str
    passed: bool
    severity: str                               # "error" (blocks filing) | "warning" | "info"
    message: str
    fix_suggestion: Optional[str] = None

class ValidationReport(BaseModel):
    results: list[ValidationResult]
    passed: int
    failed: int
    warnings: int

    @property
    def can_file(self) -> bool:
        return all(r.passed or r.severity != "error" for r in self.results)
```
