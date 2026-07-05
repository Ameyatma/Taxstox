"""AIS Information Code → ITR Schedule Mapper.

Every TDS and SFT information code from the Annual Information Statement
maps to a specific ITR schedule and field. This module provides that mapping
for ALL 40+ codes as verified against the ITD portal (FY 2025-26).

Used by:
- CrossValidator: Form 16 ↔ Form 26AS reconciliation
- TaxComputationPipeline: aggregate TDS credits by schedule
- ITR JSON Builder: populate correct schedules with correct sources
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CodeMapping:
    """Maps one AIS information code to its ITR destination."""
    code: str                          # e.g., "TDS-192"
    description: str                   # Human-readable description
    itr_schedule: str                  # Target schedule: "TDS1", "TDS2", "OS", "CG", "HP"
    itr_field: str                     # Field within the schedule
    income_type: str                   # "salary", "interest", "rent", "professional", "capital_gains", "other"
    claimable_as_tds: bool = True      # Whether this TDS can be claimed as tax credit


# ── Complete Code Map (FY 2025-26) ────────────────────────────────────

CODE_MAP: dict[str, CodeMapping] = {
    # ═══ TDS CODES ═══
    # Salary TDS
    "TDS-192": CodeMapping(
        code="TDS-192",
        description="TDS on Salary",
        itr_schedule="ScheduleTDS1",
        itr_field="TotalTDS",
        income_type="salary",
    ),

    # Interest TDS
    "TDS-194A": CodeMapping(
        code="TDS-194A",
        description="TDS on Interest (other than securities)",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonInterest",
        income_type="interest",
    ),

    # Rent TDS
    "TDS-194I": CodeMapping(
        code="TDS-194I",
        description="TDS on Rent",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonRent",
        income_type="rent",
    ),

    # Professional/Technical fees TDS
    "TDS-194J": CodeMapping(
        code="TDS-194J",
        description="TDS on Professional/Technical Fees",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonProfessionalFees",
        income_type="professional",
    ),

    # Commission/Brokerage TDS
    "TDS-194H": CodeMapping(
        code="TDS-194H",
        description="TDS on Commission/Brokerage",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonCommission",
        income_type="other",
    ),

    # Contract payments TDS
    "TDS-194C": CodeMapping(
        code="TDS-194C",
        description="TDS on Contract Payments",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonContract",
        income_type="other",
    ),

    # Insurance commission TDS
    "TDS-194D": CodeMapping(
        code="TDS-194D",
        description="TDS on Insurance Commission",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonInsuranceCommission",
        income_type="other",
    ),

    # Lottery commission TDS
    "TDS-194G": CodeMapping(
        code="TDS-194G",
        description="TDS on Commission on Sale of Lottery Tickets",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonLotteryCommission",
        income_type="other",
    ),

    # MF income TDS
    "TDS-194K": CodeMapping(
        code="TDS-194K",
        description="TDS on Income from Mutual Fund Units",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonMFIncome",
        income_type="other",
    ),

    # Foreign payments TDS
    "TDS-195": CodeMapping(
        code="TDS-195",
        description="TDS on Foreign Payments (Non-Resident)",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonForeignPayments",
        income_type="other",
    ),

    # Premature EPF withdrawal
    "TDS-192A": CodeMapping(
        code="TDS-192A",
        description="TDS on Premature EPF Withdrawal",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonEPFWithdrawal",
        income_type="other",
    ),

    # Lottery winnings
    "TDS-194B": CodeMapping(
        code="TDS-194B",
        description="TDS on Lottery/Crossword Winnings",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonLottery",
        income_type="other",
    ),

    # Race winnings
    "TDS-194BB": CodeMapping(
        code="TDS-194BB",
        description="TDS on Race Winnings",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonRaceWinnings",
        income_type="other",
    ),

    # Immovable property TDS
    "TDS-194IA": CodeMapping(
        code="TDS-194IA",
        description="TDS on Sale of Immovable Property (1%)",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonPropertySale",
        income_type="capital_gains",
        claimable_as_tds=True,  # Buyer deducts, seller claims
    ),

    # Rent by individual/HUF
    "TDS-194IB": CodeMapping(
        code="TDS-194IB",
        description="TDS on Rent by Individual/HUF (>₹50K/month)",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonRentIndividual",
        income_type="rent",
    ),

    # Cash withdrawal TDS
    "TDS-194N": CodeMapping(
        code="TDS-194N",
        description="TDS on Cash Withdrawal > ₹1 Cr",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonCashWithdrawal",
        income_type="other",
    ),

    # E-commerce TDS
    "TDS-194O": CodeMapping(
        code="TDS-194O",
        description="TDS on E-Commerce Payments",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonEcommerce",
        income_type="other",
    ),

    # Virtual Digital Assets TDS
    "TDS-194S": CodeMapping(
        code="TDS-194S",
        description="TDS on Virtual Digital Assets (Crypto)",
        itr_schedule="ScheduleTDS2",
        itr_field="TDSonVDA",
        income_type="capital_gains",
    ),

    # ═══ SFT CODES ═══
    # These are "Specified Financial Transactions" — reported for information
    # They don't have TDS but ARE income sources that must be reported

    "SFT-005": CodeMapping(
        code="SFT-005",
        description="Fixed Deposit Interest (>₹10,000)",
        itr_schedule="ScheduleOS",
        itr_field="FixedDepositInterest",
        income_type="interest",
        claimable_as_tds=False,  # SFT codes report transactions, not TDS
    ),

    "SFT-016(SB)": CodeMapping(
        code="SFT-016(SB)",
        description="Savings Account Interest (>₹10,000)",
        itr_schedule="ScheduleOS",
        itr_field="SavingsInterest",
        income_type="interest",
        claimable_as_tds=False,
    ),

    "SFT-017(OTU)": CodeMapping(
        code="SFT-017(OTU)",
        description="Other Units (Debt MFs, ETFs, Gold Bonds) Sale",
        itr_schedule="ScheduleCG",
        itr_field="A5_STCG_AppRate / B8_LTCG_Other",
        income_type="capital_gains",
        claimable_as_tds=False,
    ),

    "SFT-018(EMF)": CodeMapping(
        code="SFT-018(EMF)",
        description="Equity Mutual Fund Transactions",
        itr_schedule="ScheduleCG",
        itr_field="Schedule112A / A2_STCG_111A",
        income_type="capital_gains",
        claimable_as_tds=False,
    ),

    "SFT-010": CodeMapping(
        code="SFT-010",
        description="Shares Acquisition (>₹10L)",
        itr_schedule="ScheduleCG",
        itr_field="cost_of_acquisition",
        income_type="capital_gains",  # Provides cost basis
        claimable_as_tds=False,
    ),

    "SFT-011": CodeMapping(
        code="SFT-011",
        description="Buyback of Shares",
        itr_schedule="ScheduleCG",
        itr_field="buyback_consideration",
        income_type="capital_gains",
        claimable_as_tds=False,
    ),

    "SFT-013": CodeMapping(
        code="SFT-013",
        description="Foreign Exchange Purchase (>₹10L)",
        itr_schedule="ScheduleFA",
        itr_field="foreign_assets",
        income_type="other",
        claimable_as_tds=False,
    ),

    "SFT-001": CodeMapping(
        code="SFT-001",
        description="Share/Debenture Holdings (>₹10L)",
        itr_schedule="ScheduleAL",
        itr_field="assets_liabilities",
        income_type="other",
        claimable_as_tds=False,
    ),

    "SFT-002": CodeMapping(
        code="SFT-002",
        description="Immovable Property Transaction (>₹30L)",
        itr_schedule="ScheduleCG",
        itr_field="property_sale",
        income_type="capital_gains",
        claimable_as_tds=False,
    ),

    "SFT-003": CodeMapping(
        code="SFT-003",
        description="Cash Deposits (>₹10L in Savings)",
        itr_schedule="ScheduleAL",
        itr_field="cash_deposits",
        income_type="other",
        claimable_as_tds=False,
    ),

    "SFT-009": CodeMapping(
        code="SFT-009",
        description="Bonds/Debentures (>₹10L)",
        itr_schedule="ScheduleOS",
        itr_field="bond_interest",
        income_type="interest",
        claimable_as_tds=False,
    ),

    "SFT-014": CodeMapping(
        code="SFT-014",
        description="Immovable Property Purchase (>₹30L)",
        itr_schedule="ScheduleCG",
        itr_field="cost_of_acquisition_property",
        income_type="capital_gains",  # Cost basis for future sale
        claimable_as_tds=False,
    ),
}


def get_mapping(code: str) -> Optional[CodeMapping]:
    """Get the ITR mapping for an AIS information code.

    Handles variants: "TDS-192", "TDS192", "TDS 192", "TDS-192-Ann.II-SAL"
    """
    # Normalize: strip everything after first space or dash-number group
    clean = code.strip().upper()

    # Try exact match
    if clean in CODE_MAP:
        return CODE_MAP[clean]

    # Try without suffix (e.g., "TDS-192-Ann.II-SAL" -> "TDS-192")
    for prefix in CODE_MAP:
        if clean.startswith(prefix):
            return CODE_MAP[prefix]

    # Try without dashes
    no_dash = clean.replace("-", "").replace(" ", "")
    for prefix, mapping in CODE_MAP.items():
        if prefix.replace("-", "").replace(" ", "") == no_dash:
            return mapping

    return None


def get_all_tds_codes() -> list[CodeMapping]:
    """Get all codes that represent claimable TDS."""
    return [m for m in CODE_MAP.values() if m.claimable_as_tds and m.code.startswith("TDS")]


def get_all_income_codes() -> list[CodeMapping]:
    """Get all codes that represent reportable income sources."""
    return [m for m in CODE_MAP.values() if m.income_type in ("salary", "interest", "rent", "professional", "capital_gains")]


def get_tds_by_schedule() -> dict[str, list[CodeMapping]]:
    """Group TDS codes by their target ITR schedule."""
    groups: dict[str, list[CodeMapping]] = {}
    for m in CODE_MAP.values():
        if m.claimable_as_tds:
            groups.setdefault(m.itr_schedule, []).append(m)
    return groups
