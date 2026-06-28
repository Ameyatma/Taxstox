"""Unified tax data models — classification, CG entries, regime result."""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.models.form16 import Form16Data, Regime
from src.models.ais import AISData


class CGSaleEntry(BaseModel):
    """A single capital gain transaction, classified and ready for ITR."""
    date: date
    isin: str = ""
    security_name: str = ""
    quantity: Decimal = Decimal("0")
    sale_price: Decimal = Decimal("0")
    consideration: Decimal = Decimal("0")
    cost: Decimal = Decimal("0")
    stt_paid: bool = False
    term: str = ""  # Long / Short
    asset_class: str = ""  # equity_mf, etf_gold, etf_silver, debt_fund, other

    # Computed
    gain: Decimal = Decimal("0")
    tax_rate: str = ""  # "12.5%", "15%", "20%", "Slab"
    itr_section: str = ""  # 112A, 111A, A5, B8
    itr_schedule: str = ""  # Schedule112A, ScheduleCG_A2, etc.

    # For 112A exemption
    qualifies_for_125k_exemption: bool = False
    gain_after_exemption: Decimal = Decimal("0")

    @property
    def period(self) -> str:
        """Map sale date to ITR date period for Schedule CG Section F."""
        m, d = self.date.month, self.date.day
        if m == 4 or m == 5 or (m == 6 and d <= 15):
            return "Upto15Of6"
        elif (m == 6 and d >= 16) or m == 7 or m == 8 or (m == 9 and d <= 15):
            return "Upto15Of9"
        elif (m == 9 and d >= 16) or m == 10 or m == 11 or (m == 12 and d <= 15):
            return "Up16Of9To15Of12"
        elif (m == 12 and d >= 16) or m == 1 or m == 2 or (m == 3 and d <= 15):
            return "Up16Of12To15Of3"
        else:
            return "Up16Of3To31Of3"


class CGDateRanges(BaseModel):
    """Capital gains split by ITR date periods — for Schedule CG Section F."""
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
    stcg_15pct: dict[str, Decimal] = Field(default_factory=lambda: {
        "Upto15Of6": Decimal("0"),
        "Upto15Of9": Decimal("0"),
        "Up16Of9To15Of12": Decimal("0"),
        "Up16Of12To15Of3": Decimal("0"),
        "Up16Of3To31Of3": Decimal("0"),
    })

    def validate_sums(self, bfla_ltcg: Decimal, bfla_stcg: Decimal) -> bool:
        ltcg_sum = sum(self.ltcg_12_5pct.values())
        stcg_sum = sum(self.stcg_app_rate.values())
        return ltcg_sum == bfla_ltcg and stcg_sum == bfla_stcg


class UserAnswers(BaseModel):
    """The 0-5 answers the user provides."""
    pays_rent: bool = False
    rent_per_month: Decimal = Decimal("0")
    rent_city_metro: bool = True
    landlord_pan: str = ""

    has_health_insurance: bool = False
    health_premium_self: Decimal = Decimal("0")
    health_premium_parents: Decimal = Decimal("0")
    parents_senior_citizen: bool = False

    has_additional_80c: bool = False
    additional_80c_breakup: dict[str, Decimal] = Field(default_factory=dict)

    has_home_loan: bool = False
    home_loan_interest: Decimal = Decimal("0")
    home_loan_self_occupied: bool = True

    has_other_income: bool = False
    other_income_details: list[dict] = Field(default_factory=list)


class ClassifiedCGData(BaseModel):
    """All capital gains classified into ITR schedule buckets."""
    schedule_112a: list[CGSaleEntry] = Field(default_factory=list)
    cg_a2_stcg_111a: list[CGSaleEntry] = Field(default_factory=list)
    cg_a5_stcg_app_rate: list[CGSaleEntry] = Field(default_factory=list)
    cg_b8_ltcg_other: list[CGSaleEntry] = Field(default_factory=list)
    date_ranges: CGDateRanges = Field(default_factory=CGDateRanges)

    @property
    def total_stcg(self) -> Decimal:
        return sum(
            (e.gain for e in self.cg_a5_stcg_app_rate), Decimal("0")
        ) + sum((e.gain for e in self.cg_a2_stcg_111a), Decimal("0"))

    @property
    def total_ltcg(self) -> Decimal:
        return sum(
            (e.gain for e in self.schedule_112a), Decimal("0")
        ) + sum((e.gain for e in self.cg_b8_ltcg_other), Decimal("0"))

    @property
    def total_cg(self) -> Decimal:
        return self.total_stcg + self.total_ltcg


class RegimeResult(BaseModel):
    """Output of RegimeOptimizer."""
    old_tax: Decimal = Decimal("0")
    new_tax: Decimal = Decimal("0")
    recommended: Regime = Regime.NEW
    savings: Decimal = Decimal("0")
    old_breakdown: dict = Field(default_factory=dict)
    new_breakdown: dict = Field(default_factory=dict)


class UnifiedTaxData(BaseModel):
    """All parsed + user-provided data, ready for JSON building."""
    pan: str = ""
    dob: Optional[date] = None
    form16: Optional[Form16Data] = None
    ais: Optional[AISData] = None
    user_answers: UserAnswers = Field(default_factory=UserAnswers)

    # Auto-classified
    capital_gains: ClassifiedCGData = Field(default_factory=ClassifiedCGData)
    regime_result: RegimeResult = Field(default_factory=RegimeResult)

    # Final computation
    final_total_income: Decimal = Decimal("0")
    final_tax_liability: Decimal = Decimal("0")
    final_balance_payable: Decimal = Decimal("0")
    recommended_regime: Regime = Regime.NEW
