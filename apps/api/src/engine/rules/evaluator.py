"""RuleEvaluator — Generic, deterministic tax rule evaluation engine.

Separates rule evaluation logic from rule data. Works with any TaxYearConfig
regardless of financial year. No FY-specific constants. No tax domain knowledge.

Traceability: C12.4 (Rule Evaluation Engine — Critical), ARC-001 (Rules hardcoded)
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from src.engine.rules.config import (
    TaxYearConfig,
    RegimeConfig,
    SlabBracket,
)


class RuleEvaluator:
    """Evaluates tax rules against taxpayer data.

    Pure computation. No state. No FY-specific constants. Deterministic.
    """

    @staticmethod
    def compute_slab_tax(income: Decimal, slabs: tuple[SlabBracket, ...]) -> Decimal:
        """Compute progressive slab tax for given income and slab structure."""
        tax = Decimal("0")
        remaining = income
        prev_limit = Decimal("0")

        for bracket in slabs:
            if remaining <= prev_limit:
                break
            taxable_in_slab = min(remaining, bracket.income_to) - prev_limit
            if taxable_in_slab > 0:
                tax += taxable_in_slab * bracket.rate
            prev_limit = bracket.income_to

        return tax.quantize(Decimal("0.01"))

    @staticmethod
    def compute_cess(tax_after_rebate: Decimal, surcharge: Decimal, rate: Decimal) -> Decimal:
        """Compute Health & Education Cess."""
        return ((tax_after_rebate + surcharge) * rate).quantize(Decimal("0.01"))

    @staticmethod
    def compute_rebate(
        tax_before_rebate: Decimal,
        total_income: Decimal,
        regime: RegimeConfig,
    ) -> Decimal:
        """Compute 87A rebate if eligible."""
        if total_income <= regime.rebate_threshold:
            return min(tax_before_rebate, regime.rebate_max)
        return Decimal("0")

    @staticmethod
    def compute_surcharge(
        total_income: Decimal,
        tax_after_rebate: Decimal,
        config: TaxYearConfig,
    ) -> Decimal:
        """Compute surcharge with marginal relief."""
        rate = config.get_surcharge_rate(total_income)
        if rate == 0:
            return Decimal("0")

        surcharge = tax_after_rebate * rate

        first_threshold = config.surcharge_thresholds[0].income_threshold
        excess_income = max(Decimal("0"), total_income - first_threshold)
        if surcharge > excess_income:
            surcharge = excess_income

        return surcharge.quantize(Decimal("0.01"))

    @staticmethod
    def round_final_tax(amount: Decimal) -> Decimal:
        """Round final tax to nearest rupee per Section 288B."""
        return amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
