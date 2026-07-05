"""TaxYearConfig — Single source of truth for all FY-specific tax constants.

Replaces hardcoded constants scattered across regime_optimizer_v2.py,
deductions_computer.py, salary_computer.py, and classifier.py.

All values sourced from the Income Tax Act and Finance Acts.
New FYs are added as new TaxYearConfig instances — no code changes needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from functools import lru_cache
from typing import FrozenSet

from src.models.financial_year import FinancialYear


@dataclass(frozen=True)
class SlabBracket:
    """A single tax slab bracket."""
    income_to: Decimal       # Upper bound (None = unlimited)
    rate: Decimal            # e.g., 0.05 for 5%


@dataclass(frozen=True)
class RegimeConfig:
    """Tax configuration for one regime (Old or New)."""
    regime: str                                         # "old" or "new"
    std_deduction: Decimal                              # Standard deduction amount
    slabs: tuple[SlabBracket, ...]                      # Tax slab brackets (progressive)
    rebate_threshold: Decimal                           # Income threshold for 87A rebate
    rebate_max: Decimal                                 # Maximum rebate amount


@dataclass(frozen=True)
class DeductionLimit:
    """A single deduction limit (e.g., 80C = ₹1,50,000)."""
    section: str                                        # e.g., "80C", "80D", "80CCD(1B)"
    limit: Decimal                                      # Maximum deductible amount
    regime: str                                         # "old", "new", or "both"
    description: str                                    # Human-readable description


@dataclass(frozen=True)
class SurchargeThreshold:
    """A surcharge bracket."""
    income_threshold: Decimal                           # Income above which this applies
    rate: Decimal                                       # Surcharge rate (e.g., 0.10 for 10%)


@dataclass(frozen=True)
class TaxYearConfig:
    """Complete tax configuration for one financial year.

    Immutable. Hashable. Cacheable. Single source of truth.
    """

    financial_year: FinancialYear

    # Regime configurations
    old_regime: RegimeConfig
    new_regime: RegimeConfig

    # Deduction limits
    deduction_limits: FrozenSet[DeductionLimit] = field(default_factory=frozenset)

    # Surcharge
    surcharge_thresholds: tuple[SurchargeThreshold, ...] = field(default_factory=tuple)

    # Health & Education Cess rate
    cess_rate: Decimal = Decimal("0.04")               # 4%

    # Capital Gains
    ltcg_112a_exemption: Decimal = Decimal("125000")    # ₹1.25L exemption u/s 112A
    equity_stcg_rate: Decimal = Decimal("0.15")         # 15% u/s 111A
    equity_ltcg_rate: Decimal = Decimal("0.125")        # 12.5% u/s 112A
    non_equity_ltcg_rate: Decimal = Decimal("0.125")    # 12.5% (without indexation)

    # Professional tax cap
    max_professional_tax: Decimal = Decimal("2500")

    # HRA percentages
    hra_metro_pct: Decimal = Decimal("0.50")            # 50% for metro cities
    hra_non_metro_pct: Decimal = Decimal("0.40")        # 40% for non-metro

    def get_regime(self, regime: str) -> RegimeConfig:
        """Get configuration for a specific regime."""
        if regime in ("new", "NEW_REGIME", "new_regime"):
            return self.new_regime
        if regime in ("old", "OLD_REGIME", "old_regime"):
            return self.old_regime
        raise ValueError(f"Unknown regime: {regime}")

    def get_deduction_limit(self, section: str, regime: str | None = None) -> Decimal:
        """Get the deduction limit for a section, optionally filtered by regime."""
        for dl in self.deduction_limits:
            if dl.section.upper() == section.upper():
                if regime is None or dl.regime == "both" or dl.regime == regime:
                    return dl.limit
        return Decimal("0")

    def get_surcharge_rate(self, total_income: Decimal) -> Decimal:
        """Get applicable surcharge rate for a given total income."""
        rate = Decimal("0")
        for st in self.surcharge_thresholds:
            if total_income > st.income_threshold:
                rate = st.rate
        return rate


# ── FY2025-26 Configuration ──────────────────────────────────────────

FY2025_26 = FinancialYear.from_string("FY2025-26")

REGIME_OLD_FY2025_26 = RegimeConfig(
    regime="old",
    std_deduction=Decimal("50000"),
    slabs=(
        SlabBracket(income_to=Decimal("250000"), rate=Decimal("0.00")),
        SlabBracket(income_to=Decimal("500000"), rate=Decimal("0.05")),
        SlabBracket(income_to=Decimal("1000000"), rate=Decimal("0.20")),
        SlabBracket(income_to=Decimal("99999999999"), rate=Decimal("0.30")),
    ),
    rebate_threshold=Decimal("500000"),
    rebate_max=Decimal("12500"),
)

REGIME_NEW_FY2025_26 = RegimeConfig(
    regime="new",
    std_deduction=Decimal("75000"),
    slabs=(
        SlabBracket(income_to=Decimal("400000"), rate=Decimal("0.00")),
        SlabBracket(income_to=Decimal("800000"), rate=Decimal("0.05")),
        SlabBracket(income_to=Decimal("1200000"), rate=Decimal("0.10")),
        SlabBracket(income_to=Decimal("1600000"), rate=Decimal("0.15")),
        SlabBracket(income_to=Decimal("2000000"), rate=Decimal("0.20")),
        SlabBracket(income_to=Decimal("2400000"), rate=Decimal("0.25")),
        SlabBracket(income_to=Decimal("99999999999"), rate=Decimal("0.30")),
    ),
    rebate_threshold=Decimal("1200000"),
    rebate_max=Decimal("60000"),
)

DEDUCTION_LIMITS_FY2025_26: frozenset[DeductionLimit] = frozenset([
    DeductionLimit("80C", Decimal("150000"), "old", "Section 80C aggregate limit"),
    DeductionLimit("80CCC", Decimal("150000"), "old", "Pension fund (within 80C)"),
    DeductionLimit("80CCD(1)", Decimal("150000"), "old", "NPS employee (within 80C)"),
    DeductionLimit("80CCD(1B)", Decimal("50000"), "both", "Additional NPS (beyond 80C)"),
    DeductionLimit("80CCD(2)", Decimal("99999999999"), "both", "Employer NPS (no limit)"),
    DeductionLimit("80D_SELF", Decimal("25000"), "old", "Health insurance — self (non-senior)"),
    DeductionLimit("80D_SELF_SENIOR", Decimal("50000"), "old", "Health insurance — self (senior)"),
    DeductionLimit("80D_PARENTS", Decimal("25000"), "old", "Health insurance — parents (non-senior)"),
    DeductionLimit("80D_PARENTS_SENIOR", Decimal("50000"), "old", "Health insurance — parents (senior)"),
    DeductionLimit("80DD", Decimal("75000"), "old", "Disabled dependent (normal)"),
    DeductionLimit("80DD_SEVERE", Decimal("125000"), "old", "Disabled dependent (severe)"),
    DeductionLimit("80DDB", Decimal("40000"), "old", "Medical treatment (non-senior)"),
    DeductionLimit("80DDB_SENIOR", Decimal("100000"), "old", "Medical treatment (senior)"),
    DeductionLimit("80E", Decimal("99999999999"), "old", "Education loan interest (unlimited)"),
    DeductionLimit("80G", Decimal("99999999999"), "old", "Donations (varies by donee)"),
    DeductionLimit("80GG", Decimal("60000"), "old", "Rent without HRA"),
    DeductionLimit("80TTA", Decimal("10000"), "both", "Savings interest (non-senior)"),
    DeductionLimit("80TTB", Decimal("50000"), "both", "Interest (senior citizen)"),
    DeductionLimit("80U", Decimal("75000"), "old", "Self-disability (normal)"),
    DeductionLimit("80U_SEVERE", Decimal("125000"), "old", "Self-disability (severe)"),
    DeductionLimit("24B_SELF", Decimal("200000"), "old", "Home loan interest (self-occupied)"),
])

SURCHARGE_FY2025_26: tuple[SurchargeThreshold, ...] = (
    SurchargeThreshold(Decimal("5000000"), Decimal("0.10")),    # ₹50L+
    SurchargeThreshold(Decimal("10000000"), Decimal("0.15")),   # ₹1Cr+
    SurchargeThreshold(Decimal("20000000"), Decimal("0.25")),   # ₹2Cr+
    SurchargeThreshold(Decimal("50000000"), Decimal("0.37")),   # ₹5Cr+
)

TAX_YEAR_CONFIG_FY2025_26 = TaxYearConfig(
    financial_year=FY2025_26,
    old_regime=REGIME_OLD_FY2025_26,
    new_regime=REGIME_NEW_FY2025_26,
    deduction_limits=DEDUCTION_LIMITS_FY2025_26,
    surcharge_thresholds=SURCHARGE_FY2025_26,
)

# ── FY2024-25 Configuration ──────────────────────────────────────────

FY2024_25 = FinancialYear.from_string("FY2024-25")

REGIME_OLD_FY2024_25 = RegimeConfig(
    regime="old",
    std_deduction=Decimal("50000"),
    slabs=(
        SlabBracket(income_to=Decimal("250000"), rate=Decimal("0.00")),
        SlabBracket(income_to=Decimal("500000"), rate=Decimal("0.05")),
        SlabBracket(income_to=Decimal("1000000"), rate=Decimal("0.20")),
        SlabBracket(income_to=Decimal("99999999999"), rate=Decimal("0.30")),
    ),
    rebate_threshold=Decimal("500000"),
    rebate_max=Decimal("12500"),
)

REGIME_NEW_FY2024_25 = RegimeConfig(
    regime="new",
    std_deduction=Decimal("75000"),
    slabs=(
        SlabBracket(income_to=Decimal("300000"), rate=Decimal("0.00")),
        SlabBracket(income_to=Decimal("700000"), rate=Decimal("0.05")),
        SlabBracket(income_to=Decimal("1000000"), rate=Decimal("0.10")),
        SlabBracket(income_to=Decimal("1200000"), rate=Decimal("0.15")),
        SlabBracket(income_to=Decimal("1500000"), rate=Decimal("0.20")),
        SlabBracket(income_to=Decimal("99999999999"), rate=Decimal("0.30")),
    ),
    rebate_threshold=Decimal("700000"),
    rebate_max=Decimal("25000"),
)

TAX_YEAR_CONFIG_FY2024_25 = TaxYearConfig(
    financial_year=FY2024_25,
    old_regime=REGIME_OLD_FY2024_25,
    new_regime=REGIME_NEW_FY2024_25,
    deduction_limits=DEDUCTION_LIMITS_FY2025_26,  # Same deductions, same limits for FY24-25
    surcharge_thresholds=SURCHARGE_FY2025_26,       # Same surcharge structure
)


# ── Rule Repository ──────────────────────────────────────────────────

class RuleRepository:
    """Centralized, versioned repository for all tax year configurations.

    Usage:
        repo = RuleRepository()
        config = repo.get(FY2025_26)
        slabs = config.new_regime.slabs
        limit_80c = config.get_deduction_limit("80C", "old")
    """

    def __init__(self) -> None:
        self._configs: dict[FinancialYear, TaxYearConfig] = {
            FY2025_26: TAX_YEAR_CONFIG_FY2025_26,
            FY2024_25: TAX_YEAR_CONFIG_FY2024_25,
        }

    def get(self, fy: FinancialYear) -> TaxYearConfig:
        """Get tax configuration for a financial year."""
        if fy not in self._configs:
            raise KeyError(
                f"No tax configuration for {fy.label}. "
                f"Available: {[str(k) for k in self._configs.keys()]}"
            )
        return self._configs[fy]

    @property
    def supported_years(self) -> tuple[FinancialYear, ...]:
        """All supported financial years."""
        return tuple(sorted(self._configs.keys()))

    def register(self, config: TaxYearConfig) -> None:
        """Register a new tax year configuration."""
        self._configs[config.financial_year] = config


# Singleton instance
rule_repository = RuleRepository()
