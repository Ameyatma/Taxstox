"""AIS (Annual Information Statement) data models."""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class AISTDSEntry(BaseModel):
    information_code: str = ""
    information_source: str = ""
    quarter: str = ""
    date_of_payment: Optional[date] = None
    amount_paid: Decimal = Decimal("0")
    tds_deducted: Decimal = Decimal("0")
    tds_deposited: Decimal = Decimal("0")
    status: str = ""


class AISSavingsInterest(BaseModel):
    bank_name: str = ""
    bank_pan: str = ""
    account_number: str = ""
    account_type: str = "Saving"
    interest_amount: Decimal = Decimal("0")
    reported_on: Optional[date] = None


class AISTermDepositInterest(BaseModel):
    bank_name: str = ""
    bank_pan: str = ""
    account_number: str = ""
    interest_amount: Decimal = Decimal("0")
    reported_on: Optional[date] = None


class AISEquityMFSale(BaseModel):
    amc_name: str = ""
    isin: str = ""
    security_name: str = ""
    date_of_sale: Optional[date] = None
    quantity: Decimal = Decimal("0")
    sale_price_per_unit: Decimal = Decimal("0")
    sale_consideration: Decimal = Decimal("0")
    stt_paid: Decimal = Decimal("0")
    cost_of_acquisition: Decimal = Decimal("0")
    debit_type: str = ""
    credit_type: str = ""
    asset_type: str = "AMC"
    term: str = ""  # Long / Short
    unit_fmv: Decimal = Decimal("0")
    fair_market_value: Decimal = Decimal("0")
    indexed_cost: Decimal = Decimal("0")
    status: str = ""


class AISOtherUnitSale(BaseModel):
    depository: str = ""
    security_name: str = ""
    isin: str = ""
    date_of_sale: Optional[date] = None
    quantity: Decimal = Decimal("0")
    sale_price: Decimal = Decimal("0")
    sale_consideration: Decimal = Decimal("0")
    cost_of_acquisition: Decimal = Decimal("0")
    term: str = ""
    unit_fmv: Decimal = Decimal("0")
    fair_market_value: Decimal = Decimal("0")
    indexed_cost: Decimal = Decimal("0")
    status: str = ""


class AISSecuritiesPurchase(BaseModel):
    depository: str = ""
    client_id: str = ""
    holder_flag: str = ""
    market_purchase: Decimal = Decimal("0")
    market_sales: Decimal = Decimal("0")
    status: str = ""


class AISRefund(BaseModel):
    financial_year: str = ""
    mode: str = ""
    nature: str = ""
    amount: Decimal = Decimal("0")
    date_of_payment: Optional[date] = None


class AISAnnexureIISalary(BaseModel):
    information_source: str = ""
    employment_start: Optional[date] = None
    employment_end: Optional[date] = None
    gross_salary_171: Decimal = Decimal("0")
    perquisites_172: Decimal = Decimal("0")
    profits_lieu_173: Decimal = Decimal("0")
    total_gross_salary: Decimal = Decimal("0")


class AISData(BaseModel):
    # Part A: Personal Info
    pan: str = ""
    aadhaar_masked: str = ""
    name: str = ""
    dob: Optional[date] = None
    mobile: str = ""
    email: str = ""
    address: str = ""

    # Part B1: TDS
    salary_tds: list[AISTDSEntry] = Field(default_factory=list)
    other_tds: list[AISTDSEntry] = Field(default_factory=list)

    # Part B2: SFT
    savings_interest: list[AISSavingsInterest] = Field(default_factory=list)
    term_deposit_interest: list[AISTermDepositInterest] = Field(default_factory=list)
    equity_mf_sales: list[AISEquityMFSale] = Field(default_factory=list)
    other_unit_sales: list[AISOtherUnitSale] = Field(default_factory=list)
    securities_purchases: list[AISSecuritiesPurchase] = Field(default_factory=list)

    # Part B3: Tax Payments
    tax_payments: list[dict] = Field(default_factory=list)

    # Part B4: Refunds
    refunds: list[AISRefund] = Field(default_factory=list)

    # Part B7: Annexure II
    annexure_ii_salary: Optional[AISAnnexureIISalary] = None

    @property
    def total_non_salary_tds(self) -> Decimal:
        return sum((e.tds_deducted for e in self.other_tds), Decimal("0"))

    @property
    def total_savings_interest(self) -> Decimal:
        return sum((e.interest_amount for e in self.savings_interest), Decimal("0"))

    @property
    def total_tds_interest(self) -> Decimal:
        return sum((e.interest_amount for e in self.term_deposit_interest), Decimal("0"))

    @property
    def all_interest_income(self) -> Decimal:
        return self.total_savings_interest + self.total_tds_interest
