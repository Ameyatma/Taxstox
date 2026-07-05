"""Taxpayer Data Provider — Abstract data source for tax computation.

Architecture:
  ┌─────────────────────────────────────────────────────┐
  │              TaxpayerDataProvider                    │
  │  (abstract interface — pluggable backend)           │
  ├─────────────────────────────────────────────────────┤
  │  PDF Backend (current)  │  ITD API Backend (future) │
  │  Form 16 + AIS PDFs     │  ERI-authenticated APIs   │
  │  pdfplumber + regex     │  REST calls to ITD         │
  └─────────────────────────┴───────────────────────────┘

When ERI license is obtained:
  1. Implement ITDDataProvider(DataProvider)
  2. Swap the backend in one line
  3. User flow stays identical — enter PAN → authenticate → auto-fill

For now, PDF parsing provides ALL the same data fields.
The data model is identical regardless of source.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class SalaryDetail:
    """Complete salary breakup — from Form 16 Annexure / ITD API."""
    basic_da: Decimal = Decimal("0")
    hra_received: Decimal = Decimal("0")
    lta_received: Decimal = Decimal("0")
    special_allowance: Decimal = Decimal("0")
    bonus: Decimal = Decimal("0")
    other_allowances: Decimal = Decimal("0")
    gross_salary: Decimal = Decimal("0")

    # Exempt allowances
    hra_exempt: Decimal = Decimal("0")
    lta_exempt: Decimal = Decimal("0")
    # Other exempt: child edu, hostel, transport, helper, uniform...
    other_exempt: Decimal = Decimal("0")
    total_exempt: Decimal = Decimal("0")

    # Perquisites (from 12BA)
    perquisites: Decimal = Decimal("0")

    def to_dict(self) -> dict:
        return {
            "basic_da": str(self.basic_da),
            "hra_received": str(self.hra_received),
            "hra_exempt": str(self.hra_exempt),
            "lta_received": str(self.lta_received),
            "lta_exempt": str(self.lta_exempt),
            "special_allowance": str(self.special_allowance),
            "bonus": str(self.bonus),
            "other_allowances": str(self.other_allowances),
            "perquisites": str(self.perquisites),
            "gross_salary": str(self.gross_salary),
            "total_exempt": str(self.total_exempt),
        }


@dataclass
class TDSDetail:
    """All TDS credits — from Form 16 + 26AS / ITD API."""
    # Salary TDS (TDS-192)
    salary_tds: Decimal = Decimal("0")
    employer_name: str = ""
    employer_tan: str = ""

    # Other TDS (from 26AS: interest, rent, professional, commission...)
    interest_tds: Decimal = Decimal("0")      # TDS-194A
    rent_tds: Decimal = Decimal("0")           # TDS-194I
    professional_tds: Decimal = Decimal("0")   # TDS-194J
    commission_tds: Decimal = Decimal("0")     # TDS-194H
    other_tds: Decimal = Decimal("0")          # All other TDS codes

    total_tds: Decimal = Decimal("0")

    def to_dict(self) -> dict:
        return {
            "salary_tds": str(self.salary_tds),
            "employer_name": self.employer_name,
            "interest_tds": str(self.interest_tds),
            "rent_tds": str(self.rent_tds),
            "other_tds": str(self.other_tds),
            "total_tds": str(self.total_tds),
        }


@dataclass
class InterestIncome:
    """Interest income from all sources — from AIS / ITD API."""
    savings_interest: Decimal = Decimal("0")     # SFT-016(SB)
    fd_interest: Decimal = Decimal("0")           # SFT-005
    rd_interest: Decimal = Decimal("0")           # SFT-006
    bond_interest: Decimal = Decimal("0")         # SFT-009
    other_interest: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        return (self.savings_interest + self.fd_interest +
                self.rd_interest + self.bond_interest + self.other_interest)

    def to_dict(self) -> dict:
        return {
            "savings_interest": str(self.savings_interest),
            "fd_interest": str(self.fd_interest),
            "total_interest": str(self.total),
        }


@dataclass
class CapitalGainsSummary:
    """Capital gains from all sources — from AIS / broker CSV / ITD API."""
    equity_sales_count: int = 0          # SFT-018(EMF)
    other_unit_sales_count: int = 0      # SFT-017(OTU)
    total_stcg: Decimal = Decimal("0")
    total_ltcg: Decimal = Decimal("0")
    total_cg: Decimal = Decimal("0")

    # Ready for ITR schedules
    schedule_112a_total: Decimal = Decimal("0")
    schedule_111a_total: Decimal = Decimal("0")
    schedule_a5_total: Decimal = Decimal("0")
    schedule_b8_total: Decimal = Decimal("0")

    def to_dict(self) -> dict:
        return {
            "equity_sales": self.equity_sales_count,
            "other_sales": self.other_unit_sales_count,
            "total_stcg": str(self.total_stcg),
            "total_ltcg": str(self.total_ltcg),
            "total_cg": str(self.total_cg),
        }


@dataclass
class DeductionsDetected:
    """Deductions detected from Form 16 + AIS / ITD API."""
    # 80C sub-components
    epf: Decimal = Decimal("0")             # Form 16 80C line
    ppf: Decimal = Decimal("0")
    elss: Decimal = Decimal("0")
    lic_premium: Decimal = Decimal("0")
    tuition_fees: Decimal = Decimal("0")
    home_loan_principal: Decimal = Decimal("0")

    # NPS
    nps_employer_80ccd2: Decimal = Decimal("0")   # Form 16 (f) line
    nps_own_80ccd1b: Decimal = Decimal("0")

    # Health insurance
    health_premium_self: Decimal = Decimal("0")
    health_premium_parents: Decimal = Decimal("0")

    # Other
    education_loan_interest_80e: Decimal = Decimal("0")
    donations_80g: Decimal = Decimal("0")

    total_detected: Decimal = Decimal("0")

    def to_dict(self) -> dict:
        return {
            "epf": str(self.epf),
            "nps_employer": str(self.nps_employer_80ccd2),
            "total_detected": str(self.total_detected),
        }


@dataclass
class TaxpayerData:
    """Complete taxpayer financial profile — from ANY data source.

    This is the universal data model. Whether data comes from:
    - PDF parsing (current)
    - ITD API (future with ERI license)
    - Manual user input (always available as fallback)

    The tax computation engine consumes this structure.
    """
    pan: str = ""
    name: str = ""
    dob: Optional[date] = None
    assessment_year: str = "2026-27"

    # Income
    salary: SalaryDetail = field(default_factory=SalaryDetail)
    interest: InterestIncome = field(default_factory=InterestIncome)
    capital_gains: CapitalGainsSummary = field(default_factory=CapitalGainsSummary)

    # TDS
    tds: TDSDetail = field(default_factory=TDSDetail)

    # Deductions
    deductions: DeductionsDetected = field(default_factory=DeductionsDetected)

    # User inputs (questions answered)
    pays_rent: bool = False
    rent_per_month: Decimal = Decimal("0")
    rent_city_metro: bool = False
    has_home_loan: bool = False
    home_loan_interest: Decimal = Decimal("0")

    # Data source tracking
    data_source: str = ""  # "pdf", "itd_api", "manual"
    extraction_confidence: float = 0.0  # 0.0-1.0

    def to_dict(self) -> dict:
        return {
            "pan": self.pan,
            "name": self.name,
            "assessment_year": self.assessment_year,
            "salary": self.salary.to_dict(),
            "interest": self.interest.to_dict(),
            "capital_gains": self.capital_gains.to_dict(),
            "tds": self.tds.to_dict(),
            "deductions": self.deductions.to_dict(),
            "data_source": self.data_source,
            "confidence": self.extraction_confidence,
        }


class TaxpayerDataProvider:
    """Abstract data provider — pluggable backends.

    Usage:
      # PDF backend (current)
      provider = PDFDataProvider(form16_pdf, ais_pdf, pan, dob)
      data = provider.fetch()

      # ITD API backend (future)
      provider = ITDDataProvider(auth_token, pan, assessment_year)
      data = provider.fetch()

      # Both return identical TaxpayerData structures.
    """

    def fetch(self) -> TaxpayerData:
        """Extract complete taxpayer financial profile."""
        raise NotImplementedError("Use a concrete provider implementation")


class PDFDataProvider(TaxpayerDataProvider):
    """Extract TaxpayerData from Form 16 + AIS PDFs.

    This implements the EXACT same data interface that the ITD API would provide.
    When ERI access is granted, swap to ITDDataProvider — no other code changes.
    """

    def __init__(self, form16_data, ais_data, pan: str, dob: str):
        self.form16 = form16_data
        self.ais = ais_data
        self.pan = pan
        self.dob_str = dob

    def fetch(self) -> TaxpayerData:
        """Extract complete data from uploaded PDFs."""
        data = TaxpayerData(
            pan=self.pan,
            data_source="pdf",
            extraction_confidence=0.0,
        )

        # ── Personal info ──
        if self.form16:
            data.name = self.form16.part_a.employee_name or ""
            data.assessment_year = self.form16.part_a.assessment_year or "2026-27"
        if self.ais and self.ais.name:
            data.name = data.name or self.ais.name

        # ── Salary detail ──
        if self.form16:
            annex = self.form16.annexure
            pb = self.form16.part_b

            data.salary.basic_da = annex.basic or Decimal("0")
            data.salary.hra_received = annex.hra or Decimal("0")
            data.salary.lta_received = annex.lta or Decimal("0")
            data.salary.special_allowance = annex.special_allowance or Decimal("0")
            data.salary.bonus = annex.dbip_bonus or Decimal("0")
            data.salary.gross_salary = pb.total_gross_salary or Decimal("0")

            # Section 10 exemptions from Form 16
            s10 = pb.exemptions_s10
            data.salary.lta_exempt = s10.travel_concession_105
            data.salary.hra_exempt = s10.hra_1013A
            data.salary.total_exempt = s10.total

            # Perquisites
            data.salary.perquisites = pb.perquisites_172 or Decimal("0")

            # Standard deduction (from Form 16 Part B)
            data.salary.other_allowances = max(
                Decimal("0"),
                data.salary.gross_salary
                - data.salary.basic_da
                - data.salary.hra_received
                - data.salary.lta_received
                - data.salary.special_allowance
                - data.salary.bonus
            )

            data.extraction_confidence += 0.40  # Salary = 40% of extraction

        # ── TDS ──
        if self.form16:
            pa = self.form16.part_a
            data.tds.salary_tds = pa.total_tds_deducted or Decimal("0")
            data.tds.employer_name = pa.employer_name or ""
            data.tds.employer_tan = pa.employer_tan or ""
            data.extraction_confidence += 0.15

        # ── Interest income from AIS ──
        if self.ais:
            data.interest.savings_interest = self.ais.total_savings_interest or Decimal("0")

            # Other TDS entries in AIS may indicate interest income
            for tds_entry in self.ais.other_tds:
                tds_amount = tds_entry.tds_deducted or Decimal("0")
                data.tds.other_tds += tds_amount

                # If TDS code suggests interest, add to interest income
                code = getattr(tds_entry, 'information_code', '') or ''
                if '194A' in code:
                    # TDS on interest at 10% → estimate gross interest
                    if tds_amount > 0:
                        data.interest.fd_interest += tds_amount * Decimal("10")  # 10% TDS → gross

            data.tds.total_tds = data.tds.salary_tds + data.tds.other_tds
            data.extraction_confidence += 0.15

        # ── Capital gains from AIS ──
        if self.ais:
            equity_sales = self.ais.equity_mf_sales or []
            other_sales = self.ais.other_unit_sales or []

            data.capital_gains.equity_sales_count = len(equity_sales)
            data.capital_gains.other_unit_sales_count = len(other_sales)

            # Sum up gains from classified data if available
            # Classification happens separately — this just counts

            if equity_sales or other_sales:
                data.extraction_confidence += 0.10

        # ── Deductions from Form 16 ──
        if self.form16:
            via = self.form16.part_b.chapter_vi_a
            data.deductions.epf = via.sec80c or Decimal("0")
            data.deductions.nps_employer_80ccd2 = via.sec80ccd2 or Decimal("0")
            data.deductions.total_detected = (
                data.deductions.epf
                + data.deductions.nps_employer_80ccd2
            )
            data.extraction_confidence += 0.15

        # ── Rent/HRA detection from salary breakup ──
        if data.salary.hra_received > 0:
            data.pays_rent = True  # Flag: if HRA received, likely paying rent
            # The user still needs to provide actual rent amount

        data.extraction_confidence = min(data.extraction_confidence, 0.95)

        return data
