"""Classification Engine — Maps AIS transactions to ITR schedules.

The engine takes raw AIS sale entries and classifies them into:
- Schedule 112A: Equity LTCG (held >12mo, STT paid, ₹1.25L exemption)
- Schedule CG A2: Equity STCG u/s 111A (held ≤12mo, STT paid, 15% tax)
- Schedule CG A5: Non-equity STCG (slab rate)
- Schedule CG B8: Non-equity LTCG (12.5% w/o indexation, 20% with)

Also computes CG date ranges for Schedule CG Section F.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from src.models.tax import CGSaleEntry, ClassifiedCGData, CGDateRanges
from src.models.ais import AISEquityMFSale, AISOtherUnitSale

# ₹1,25,000 exemption for LTCG under Section 112A
LTCG_112A_EXEMPTION = Decimal("125000")

# ISIN prefixes that indicate equity
EQUITY_ISIN_PREFIXES = ("INF", "INE")


class ClassificationEngine:
    """Classifies raw AIS capital gains into ITR schedule buckets."""

    def classify(
        self,
        equity_mf_sales: list[AISEquityMFSale],
        other_unit_sales: list[AISOtherUnitSale],
    ) -> ClassifiedCGData:
        """Classify all AIS sale entries into their ITR schedule buckets."""
        result = ClassifiedCGData()

        # Classify equity MF sales
        for sale in equity_mf_sales:
            entry = self._classify_equity_mf(sale)
            self._assign_to_schedule(result, entry)

        # Classify other unit sales (ETF, debt funds, etc.)
        for sale in other_unit_sales:
            entry = self._classify_other_unit(sale)
            self._assign_to_schedule(result, entry)

        # Compute date ranges for Schedule CG Section F
        result.date_ranges = self._compute_date_ranges(result)

        return result

    def _classify_equity_mf(self, sale: AISEquityMFSale) -> CGSaleEntry:
        """Classify a single equity mutual fund sale."""
        gain = sale.sale_consideration - sale.cost_of_acquisition
        is_long = sale.term.lower() == "long" if sale.term else False

        entry = CGSaleEntry(
            date=sale.date_of_sale or date.today(),
            isin=sale.isin,
            security_name=sale.security_name,
            quantity=sale.quantity,
            sale_price=sale.sale_price_per_unit,
            consideration=sale.sale_consideration,
            cost=sale.cost_of_acquisition,
            stt_paid=sale.stt_paid > 0,
            term=sale.term,
            asset_class="equity_mf",
            gain=gain,
        )

        if is_long:
            # Equity LTCG → Schedule 112A, taxed at 12.5%
            entry.tax_rate = "12.5%"
            entry.itr_section = "112A"
            entry.itr_schedule = "Schedule112A"
            entry.qualifies_for_125k_exemption = True
        else:
            # Equity STCG → Schedule CG A2, taxed at 15% u/s 111A
            entry.tax_rate = "15%"
            entry.itr_section = "111A"
            entry.itr_schedule = "ScheduleCG_A2"

        return entry

    def _classify_other_unit(self, sale: AISOtherUnitSale) -> CGSaleEntry:
        """Classify a non-equity unit sale (ETF, debt fund, gold ETF)."""
        gain = sale.sale_consideration - sale.cost_of_acquisition
        is_long = sale.term.lower() == "long" if sale.term else False

        entry = CGSaleEntry(
            date=sale.date_of_sale or date.today(),
            isin=sale.isin,
            security_name=sale.security_name,
            quantity=sale.quantity,
            sale_price=sale.sale_price,
            consideration=sale.sale_consideration,
            cost=sale.cost_of_acquisition,
            stt_paid=False,  # Non-equity typically no STT
            term=sale.term,
            asset_class=self._determine_asset_class(sale),
            gain=gain,
        )

        if is_long:
            # Non-equity LTCG → Schedule CG B8, taxed at 12.5% (or 20% with indexation)
            entry.tax_rate = "12.5%"
            entry.itr_section = "B8"
            entry.itr_schedule = "ScheduleCG_B8"
            entry.qualifies_for_125k_exemption = False
        else:
            # Non-equity STCG → Schedule CG A5, taxed at slab rate
            entry.tax_rate = "Slab"
            entry.itr_section = "A5"
            entry.itr_schedule = "ScheduleCG_A5"
            entry.qualifies_for_125k_exemption = False

        return entry

    def _determine_asset_class(self, sale: AISOtherUnitSale) -> str:
        """Determine asset class from ISIN or security name."""
        name = sale.security_name.upper() if sale.security_name else ""

        if "GOLD" in name or "SILVER" in name:
            if "GOLD" in name:
                return "etf_gold"
            return "etf_silver"
        if "ETF" in name:
            return "etf_other"
        if "DEBT" in name or "BOND" in name or "GILT" in name or "LIQUID" in name:
            return "debt_fund"
        if "REIT" in name or "INVIT" in name:
            return "reit_invit"
        return "other"

    def _assign_to_schedule(self, result: ClassifiedCGData, entry: CGSaleEntry) -> None:
        """Assign a classified entry to the correct schedule bucket."""
        schedule = entry.itr_schedule
        if schedule == "Schedule112A":
            result.schedule_112a.append(entry)
        elif schedule == "ScheduleCG_A2":
            result.cg_a2_stcg_111a.append(entry)
        elif schedule == "ScheduleCG_A5":
            result.cg_a5_stcg_app_rate.append(entry)
        elif schedule == "ScheduleCG_B8":
            result.cg_b8_ltcg_other.append(entry)

    def _compute_date_ranges(self, data: ClassifiedCGData) -> CGDateRanges:
        """Compute CG date ranges for Schedule CG Section F."""
        ranges = CGDateRanges()

        # 112A LTCG by period
        for entry in data.schedule_112a:
            period = entry.period
            ranges.ltcg_12_5pct[period] += entry.gain

        # STCG at slab rate by period
        for entry in data.cg_a5_stcg_app_rate:
            period = entry.period
            ranges.stcg_app_rate[period] += entry.gain

        # STCG at 15% (111A) by period
        for entry in data.cg_a2_stcg_111a:
            period = entry.period
            ranges.stcg_15pct[period] += entry.gain

        return ranges

    def apply_112a_exemption(self, data: ClassifiedCGData) -> ClassifiedCGData:
        """
        Apply the ₹1.25L LTCG exemption under Section 112A.

        Exemption is applied to the oldest gains first (FIFO within the year),
        or proportionally across all 112A entries.
        """
        remaining_exemption = LTCG_112A_EXEMPTION

        # Sort by date (oldest first) for FIFO application
        sorted_entries = sorted(data.schedule_112a, key=lambda e: e.date)

        for entry in sorted_entries:
            if remaining_exemption <= 0:
                entry.gain_after_exemption = entry.gain
                continue

            if entry.gain <= remaining_exemption:
                # Entire gain is exempt
                entry.gain_after_exemption = Decimal("0")
                remaining_exemption -= entry.gain
            else:
                # Partially exempt
                entry.gain_after_exemption = entry.gain - remaining_exemption
                remaining_exemption = Decimal("0")

        return data

    def get_tax_summary(self, data: ClassifiedCGData) -> dict:
        """Get a summary of capital gains tax liability."""
        # Apply exemption first
        data = self.apply_112a_exemption(data)

        # Compute tax on each category
        ltcg_112a_taxable = sum(
            (e.gain_after_exemption for e in data.schedule_112a), Decimal("0")
        )
        ltcg_112a_tax = ltcg_112a_taxable * Decimal("0.125")  # 12.5%

        stcg_15pct_total = sum(
            (e.gain for e in data.cg_a2_stcg_111a), Decimal("0")
        )
        stcg_15pct_tax = stcg_15pct_total * Decimal("0.15")  # 15%

        stcg_slab_total = sum(
            (e.gain for e in data.cg_a5_stcg_app_rate), Decimal("0")
        )
        # STCG slab-rate gains are taxed at the taxpayer's slab rate — computed by RegimeOptimizer

        ltcg_other_total = sum(
            (e.gain for e in data.cg_b8_ltcg_other), Decimal("0")
        )
        ltcg_other_tax = ltcg_other_total * Decimal("0.125")  # 12.5% without indexation

        return {
            "ltcg_112a_total_gain": sum((e.gain for e in data.schedule_112a), Decimal("0")),
            "ltcg_112a_exempt": LTCG_112A_EXEMPTION - max(Decimal("0"), LTCG_112A_EXEMPTION - sum((e.gain for e in data.schedule_112a), Decimal("0"))),
            "ltcg_112a_taxable": ltcg_112a_taxable,
            "ltcg_112a_tax": ltcg_112a_tax,
            "stcg_15pct_total": stcg_15pct_total,
            "stcg_15pct_tax": stcg_15pct_tax,
            "stcg_slab_total": stcg_slab_total,
            "ltcg_other_total": ltcg_other_total,
            "ltcg_other_tax": ltcg_other_tax,
            "total_cg_tax_pre_slab": ltcg_112a_tax + stcg_15pct_tax + ltcg_other_tax,
        }


def classify_capital_gains(
    equity_mf_sales: list[AISEquityMFSale],
    other_unit_sales: list[AISOtherUnitSale],
) -> ClassifiedCGData:
    """Convenience function for classification."""
    engine = ClassificationEngine()
    return engine.classify(equity_mf_sales, other_unit_sales)
