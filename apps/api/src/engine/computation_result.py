"""ComputationResult — Immutable, explainable, FY-aware tax computation output.

Traceability: C6.5 (Tax Liability Aggregator), C6.6 (Pipeline Orchestrator),
             C10.2 (Explanation Engine foundation)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from src.models.financial_year import FinancialYear


@dataclass(frozen=True)
class SlabStep:
    """A single slab bracket computation step."""
    income_from: Decimal
    income_to: Optional[Decimal]   # None = unlimited
    rate: Decimal
    taxable_in_slab: Decimal
    tax_in_slab: Decimal

    @property
    def explanation(self) -> str:
        limit = f"₹{self.income_to:,.0f}" if self.income_to else "above"
        return (
            f"Income from ₹{self.income_from:,.0f} to {limit}: "
            f"₹{self.taxable_in_slab:,.0f} × {self.rate * 100:.0f}% = "
            f"₹{self.tax_in_slab:,.0f}"
        )


@dataclass(frozen=True)
class TaxBreakdown:
    """Complete tax computation breakdown for one regime."""

    regime: str  # "old" or "new"
    financial_year: str

    # Income
    income_salary: Decimal = Decimal("0")
    income_house_property: Decimal = Decimal("0")
    income_capital_gains: Decimal = Decimal("0")
    income_other_sources: Decimal = Decimal("0")
    gross_total_income: Decimal = Decimal("0")

    # Deductions
    deductions_total: Decimal = Decimal("0")
    total_income: Decimal = Decimal("0")

    # Tax Components
    slab_income: Decimal = Decimal("0")
    slab_steps: tuple[SlabStep, ...] = ()
    slab_tax: Decimal = Decimal("0")
    special_rate_tax: Decimal = Decimal("0")
    tax_before_rebate: Decimal = Decimal("0")
    rebate_87a: Decimal = Decimal("0")
    surcharge: Decimal = Decimal("0")
    surcharge_rate: Decimal = Decimal("0")
    cess: Decimal = Decimal("0")
    cess_rate: Decimal = Decimal("0")
    final_tax: Decimal = Decimal("0")

    # Credits
    tds_credited: Decimal = Decimal("0")
    advance_tax: Decimal = Decimal("0")
    self_assessment_tax: Decimal = Decimal("0")

    # Final
    net_tax_payable: Decimal = Decimal("0")
    refund_due: Decimal = Decimal("0")

    @property
    def effective_tax_rate(self) -> Decimal:
        if self.total_income <= 0:
            return Decimal("0")
        return (self.final_tax / self.total_income * Decimal("100")).quantize(
            Decimal("0.01")
        )


@dataclass(frozen=True)
class RegimeComparison:
    """Side-by-side regime comparison result."""

    old: TaxBreakdown
    new: TaxBreakdown
    recommended: str          # "old" or "new"
    savings: Decimal          # How much the recommended regime saves
    financial_year: str

    @property
    def summary(self) -> str:
        regime = "Old Regime" if self.recommended == "old" else "New Regime"
        return (
            f"{regime} recommended — saves ₹{self.savings:,.0f}. "
            f"Old: ₹{self.old.final_tax:,.0f}, New: ₹{self.new.final_tax:,.0f}."
        )


@dataclass(frozen=True)
class ComputationResult:
    """Complete, immutable, explainable tax computation result.

    The single source of truth for any tax computation output.
    Contains everything needed for audit, explanation, and ITR generation.
    """

    financial_year: FinancialYear
    regime_comparison: RegimeComparison
    computed_at: str = ""  # ISO timestamp

    # Interest (234A/B/C)
    interest_234a: Decimal = Decimal("0")
    interest_234b: Decimal = Decimal("0")
    interest_234c: Decimal = Decimal("0")
    total_interest: Decimal = Decimal("0")

    # Late fees
    late_filing_fee_234f: Decimal = Decimal("0")

    # Grand total
    total_amount_payable: Decimal = Decimal("0")

    @property
    def recommended_breakdown(self) -> TaxBreakdown:
        if self.regime_comparison.recommended == "new":
            return self.regime_comparison.new
        return self.regime_comparison.old

    @property
    def final_liability(self) -> Decimal:
        return self.total_amount_payable

    def to_summary_dict(self) -> dict:
        """Compact summary for API responses."""
        bd = self.recommended_breakdown
        return {
            "financial_year": self.financial_year.label,
            "recommended_regime": self.regime_comparison.recommended,
            "savings": str(self.regime_comparison.savings),
            "gross_total_income": str(bd.gross_total_income),
            "deductions": str(bd.deductions_total),
            "total_income": str(bd.total_income),
            "tax_before_rebate": str(bd.tax_before_rebate),
            "rebate_87a": str(bd.rebate_87a),
            "surcharge": str(bd.surcharge),
            "cess": str(bd.cess),
            "final_tax": str(bd.final_tax),
            "tds_credited": str(bd.tds_credited),
            "net_tax_payable": str(bd.net_tax_payable),
            "refund_due": str(bd.refund_due),
            "interest_234abc": str(self.total_interest),
            "total_payable": str(self.total_amount_payable),
        }
