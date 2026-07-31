"""Tax-Loss Harvesting — Identifies unrealized losses for tax optimization.

Analyzes a taxpayer's portfolio to find opportunities where selling
losing positions can offset capital gains and reduce tax.

Traceability: C19.2 (Tax-Loss Harvesting — 0%→30%, P6)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class AssetType(str, Enum):
    LISTED_EQUITY = "listed_equity"
    EQUITY_MF = "equity_mf"
    DEBT_MF = "debt_mf"
    GOLD_ETF = "gold_etf"
    REAL_ESTATE = "real_estate"
    CRYPTO = "crypto"
    UNLISTED_SHARES = "unlisted_shares"


@dataclass(frozen=True)
class LossHarvestingOpportunity:
    """An unrealized loss that could be harvested. Value object."""

    asset_name: str
    asset_type: AssetType
    acquisition_cost: Decimal
    current_value: Decimal
    unrealized_loss: Decimal             # Current value - acquisition cost (negative)

    holding_period_days: int = 0
    is_long_term: bool = False
    stt_paid: bool = False

    @property
    def loss_amount(self) -> Decimal:
        return abs(self.unrealized_loss)

    @property
    def gain_type(self) -> str:
        """What type of gain this loss can offset."""
        if self.asset_type in (AssetType.LISTED_EQUITY, AssetType.EQUITY_MF):
            if self.is_long_term:
                return "ltcg_equity"
            return "stcg_equity"
        if self.asset_type == AssetType.CRYPTO:
            return "vda"  # Can only offset VDA gains
        if self.is_long_term:
            return "ltcg_other"
        return "stcg_other"


@dataclass
class HarvestingRecommendation:
    """A concrete tax-loss harvesting recommendation. Entity."""

    recommendation_id: UUID
    opportunity: LossHarvestingOpportunity
    sell_quantity: Decimal = Decimal("1")
    estimated_tax_saved: Decimal = Decimal("0")
    offsets_which_gains: str = ""        # Description of which gains are offset
    action: str = ""                     # "Sell 100 shares of X"
    priority: int = 50                   # 1-100
    caveat: str = ""                     # "Must hold for 30+ days to avoid wash sale"

    @staticmethod
    def create(opportunity: LossHarvestingOpportunity) -> HarvestingRecommendation:
        return HarvestingRecommendation(
            recommendation_id=uuid4(), opportunity=opportunity,
        )

    def compute_tax_saved(self, marginal_tax_rate: Decimal) -> Decimal:
        """Estimate tax saved by harvesting this loss."""
        if self.opportunity.gain_type in ("stcg_equity",):
            rate = Decimal("0.15")
        elif self.opportunity.gain_type in ("ltcg_equity", "ltcg_other"):
            rate = Decimal("0.125")
        elif self.opportunity.gain_type == "vda":
            rate = Decimal("0.30")
        else:
            rate = marginal_tax_rate  # STCG other → slab rate

        self.estimated_tax_saved = (self.opportunity.loss_amount * rate).quantize(Decimal("0.01"))
        return self.estimated_tax_saved
