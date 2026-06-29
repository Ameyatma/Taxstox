"""Form 16 data models — Part A, Part B, Annexure, 12BA."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Regime(str, Enum):
    OLD = "old"
    NEW = "new"


class QuarterlyTDS(BaseModel):
    quarter: str  # Q1, Q2, Q3, Q4
    receipt_number: str = ""
    amount_paid: Decimal = Decimal("0")
    tds_deducted: Decimal = Decimal("0")
    tds_deposited: Decimal = Decimal("0")


class OtherExemption(BaseModel):
    description: str
    gross_amount: Decimal = Decimal("0")
    qualifying_amount: Decimal = Decimal("0")
    deductible_amount: Decimal = Decimal("0")


class Section10Exemptions(BaseModel):
    travel_concession_105: Decimal = Decimal("0")
    gratuity_1010: Decimal = Decimal("0")
    commuted_pension_1010A: Decimal = Decimal("0")
    leave_encashment_1010AA: Decimal = Decimal("0")
    hra_1013A: Decimal = Decimal("0")
    special_allowances_1014: Decimal = Decimal("0")
    other_exemptions_s10: list[OtherExemption] = Field(default_factory=list)

    @property
    def total(self) -> Decimal:
        return (
            self.travel_concession_105
            + self.gratuity_1010
            + self.commuted_pension_1010A
            + self.leave_encashment_1010AA
            + self.hra_1013A
            + self.special_allowances_1014
            + sum(e.deductible_amount for e in self.other_exemptions_s10)
        )


class Form16PartA(BaseModel):
    certificate_no: str = ""
    employer_name: str = ""
    employer_address: str = ""
    employer_tan: str = ""
    employer_pan: str = ""
    employee_name: str = ""
    employee_pan: str = ""
    employee_address: str = ""
    assessment_year: str = ""
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    cit_tds_jurisdiction: str = ""

    quarterly_tds: list[QuarterlyTDS] = Field(default_factory=list)

    total_amount_paid: Decimal = Decimal("0")
    total_tds_deducted: Decimal = Decimal("0")
    total_tds_deposited: Decimal = Decimal("0")


class ChapterVIADeductions(BaseModel):
    sec80c: Decimal = Decimal("0")
    sec80ccc: Decimal = Decimal("0")
    sec80ccd1: Decimal = Decimal("0")
    sec80ccd1b: Decimal = Decimal("0")
    sec80ccd2: Decimal = Decimal("0")
    sec80d: Decimal = Decimal("0")
    sec80dd: Decimal = Decimal("0")
    sec80ddb: Decimal = Decimal("0")
    sec80e: Decimal = Decimal("0")
    sec80ee: Decimal = Decimal("0")
    sec80eea: Decimal = Decimal("0")
    sec80eeb: Decimal = Decimal("0")
    sec80g: Decimal = Decimal("0")
    sec80gg: Decimal = Decimal("0")
    sec80gga: Decimal = Decimal("0")
    sec80ggc: Decimal = Decimal("0")
    sec80tta: Decimal = Decimal("0")
    sec80ttb: Decimal = Decimal("0")
    sec80u: Decimal = Decimal("0")
    sec80cch: Decimal = Decimal("0")

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
    taxable_income: Decimal = Decimal("0")
    tax_on_income: Decimal = Decimal("0")
    rebate_87a: Decimal = Decimal("0")
    surcharge: Decimal = Decimal("0")
    health_education_cess: Decimal = Decimal("0")
    tax_payable: Decimal = Decimal("0")
    relief_89: Decimal = Decimal("0")
    net_tax_payable: Decimal = Decimal("0")


class Form16PartB(BaseModel):
    opting_out_115bac: bool = False  # True = opted OUT of new → old regime

    # Section 17 — Gross Salary
    salary_171: Decimal = Decimal("0")
    perquisites_172: Decimal = Decimal("0")
    profits_lieu_173: Decimal = Decimal("0")
    total_gross_salary: Decimal = Decimal("0")

    # Section 10 — Exempt Allowances
    exemptions_s10: Section10Exemptions = Field(default_factory=Section10Exemptions)

    # Section 16 — Deductions from Salary
    std_deduction_16ia: Decimal = Decimal("0")
    entertainment_16ii: Decimal = Decimal("0")
    professional_tax_16iii: Decimal = Decimal("0")

    income_under_head_salaries: Decimal = Decimal("0")
    other_income_reported: Decimal = Decimal("0")
    gross_total_income: Decimal = Decimal("0")

    chapter_vi_a: ChapterVIADeductions = Field(default_factory=ChapterVIADeductions)
    taxable_income: Decimal = Decimal("0")
    tax_computation: TaxComputation = Field(default_factory=TaxComputation)


class SalaryComponent(BaseModel):
    name: str
    amount: Decimal = Decimal("0")
    nature: str = "Fully Taxable"  # Fully Taxable, Partly Exempt, Exempt


class Form16Annexure(BaseModel):
    components: list[SalaryComponent] = Field(default_factory=list)
    basic: Decimal = Decimal("0")
    hra: Decimal = Decimal("0")
    special_allowance: Decimal = Decimal("0")
    lta: Decimal = Decimal("0")
    lunch_coupons: Decimal = Decimal("0")
    broadband_reimbursement: Decimal = Decimal("0")
    special_award: Decimal = Decimal("0")
    nps_employer: Decimal = Decimal("0")
    dbip_bonus: Decimal = Decimal("0")


class PerquisitesDetail(BaseModel):
    accommodation: Decimal = Decimal("0")
    car: Decimal = Decimal("0")
    sweeper_gardener_attendant: Decimal = Decimal("0")
    gas_electricity_water: Decimal = Decimal("0")
    rsu: Decimal = Decimal("0")
    espp: Decimal = Decimal("0")
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


class Form12BA(BaseModel):
    income_under_head_salaries: Decimal = Decimal("0")
    perquisites: PerquisitesDetail = Field(default_factory=PerquisitesDetail)


class Form16Data(BaseModel):
    part_a: Form16PartA
    part_b: Form16PartB
    annexure: Form16Annexure
    form_12ba: Optional[Form12BA] = None

    @property
    def regime(self) -> Regime:
        return Regime.OLD if self.part_b.opting_out_115bac else Regime.NEW

    @property
    def effective_salary(self) -> Decimal:
        return self.part_b.income_under_head_salaries
