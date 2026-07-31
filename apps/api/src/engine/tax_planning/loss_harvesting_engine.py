"""Loss Harvesting Engine — Identifies tax-loss harvesting opportunities.

Analyzes a portfolio for unrealized losses that can offset capital gains.

Traceability: C19.2 (Tax-Loss Harvesting — 0%→30%, P6)
"""

from __future__ import annotations

from decimal import Decimal

from src.domain.tax_planning.loss_harvesting import (
    LossHarvestingOpportunity,
    HarvestingRecommendation,
    AssetType,
)


class LossHarvestingEngine:
    """Identifies and ranks tax-loss harvesting opportunities.

    Engine. Analyzes portfolio holdings for unrealized losses.
    Determines which gains each loss can offset and estimates tax saved.
    """

    def analyze_portfolio(
        self,
        holdings: list[dict],
        marginal_tax_rate: Decimal = Decimal("0.30"),
        existing_stcg: Decimal = Decimal("0"),
        existing_ltcg: Decimal = Decimal("0"),
        existing_vda_gains: Decimal = Decimal("0"),
    ) -> list[HarvestingRecommendation]:
        """Analyze portfolio for loss harvesting opportunities.

        Args:
            holdings: [{"name": "RELIANCE", "type": "listed_equity", "cost": "100000",
                       "current": "80000", "holding_days": 200, "stt_paid": True}, ...]
            marginal_tax_rate: Top slab rate for STCG non-equity
            existing_stcg: Existing short-term gains to offset
            existing_ltcg: Existing long-term gains to offset
            existing_vda_gains: Existing VDA gains to offset

        Returns:
            Ranked list of HarvestingRecommendation
        """
        recommendations: list[HarvestingRecommendation] = []

        for h in holdings:
            cost = Decimal(str(h.get("cost", "0")))
            current = Decimal(str(h.get("current", "0")))
            if current >= cost:
                continue  # No loss to harvest

            asset_type = AssetType(h.get("type", "listed_equity"))
            holding_days = h.get("holding_days", 0)

            # Determine if long-term
            lt_thresholds = {
                AssetType.LISTED_EQUITY: 365,
                AssetType.EQUITY_MF: 365,
                AssetType.DEBT_MF: 730,
                AssetType.GOLD_ETF: 730,
                AssetType.REAL_ESTATE: 730,
                AssetType.UNLISTED_SHARES: 730,
                AssetType.CRYPTO: 1,  # Always short-term for this purpose
            }
            is_lt = holding_days >= lt_thresholds.get(asset_type, 365)

            opportunity = LossHarvestingOpportunity(
                asset_name=h.get("name", "Unknown"),
                asset_type=asset_type,
                acquisition_cost=cost,
                current_value=current,
                unrealized_loss=current - cost,
                holding_period_days=holding_days,
                is_long_term=is_lt,
                stt_paid=h.get("stt_paid", False),
            )

            rec = HarvestingRecommendation.create(opportunity)
            rec.compute_tax_saved(marginal_tax_rate)

            # Determine what this loss can offset
            gain_type = opportunity.gain_type
            if gain_type == "stcg_equity" and existing_stcg > 0:
                rec.offsets_which_gains = f"Offsets ₹{min(opportunity.loss_amount, existing_stcg):,.0f} of STCG equity gains"
                rec.priority = 90
            elif gain_type == "ltcg_equity" and existing_ltcg > 0:
                rec.offsets_which_gains = f"Offsets ₹{min(opportunity.loss_amount, existing_ltcg):,.0f} of LTCG equity gains"
                rec.priority = 80
            elif gain_type == "vda" and existing_vda_gains > 0:
                rec.offsets_which_gains = f"Offsets ₹{min(opportunity.loss_amount, existing_vda_gains):,.0f} of VDA gains"
                rec.priority = 95
            else:
                rec.offsets_which_gains = "Carry forward — no current gains to offset"
                rec.priority = 40

            rec.action = f"Sell {h.get('name', 'holding')} — realize ₹{opportunity.loss_amount:,.0f} loss"
            rec.caveat = "Consult CA before executing. Wash sale rules may apply."

            recommendations.append(rec)

        # Sort by priority (highest first), then by tax saved (largest first)
        recommendations.sort(key=lambda r: (r.priority, float(r.estimated_tax_saved)), reverse=True)
        return recommendations

    @staticmethod
    def total_potential_savings(recommendations: list[HarvestingRecommendation]) -> Decimal:
        """Sum of estimated tax saved across all recommendations."""
        return sum(r.estimated_tax_saved for r in recommendations).quantize(Decimal("0.01"))
