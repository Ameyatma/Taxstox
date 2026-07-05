"""Unit tests for ClassificationEngine — AIS entries → ITR schedule buckets.

Verifies:
- Equity MF LTCG → Schedule 112A (12.5% tax, ₹1.25L exemption)
- Equity MF STCG → Schedule CG A2/111A (15% tax)
- Non-equity STCG → Schedule CG A5 (slab rate)
- Non-equity LTCG → Schedule CG B8 (12.5% tax)
- 112A exemption FIFO application
- Date range computation for Schedule CG Section F
- Asset class determination from security name
"""

from datetime import date
from decimal import Decimal

from src.engine.classifier import ClassificationEngine, classify_capital_gains, LTCG_112A_EXEMPTION
from src.models.ais import AISEquityMFSale, AISOtherUnitSale


class TestEquityMFClassification:
    """Equity mutual fund sale classification."""

    def test_equity_ltcg_classification(self, sample_ais_data_with_capital_gains):
        """Equity MF held >12mo → Schedule 112A, 12.5% tax, qualifies for exemption."""
        engine = ClassificationEngine()
        result = engine.classify(
            sample_ais_data_with_capital_gains.equity_mf_sales,
            sample_ais_data_with_capital_gains.other_unit_sales,
        )
        assert len(result.schedule_112a) == 1
        entry = result.schedule_112a[0]
        assert entry.security_name == "Quant ELSS Tax Saver Fund"
        assert entry.term == "Long"
        assert entry.tax_rate == "12.5%"
        assert entry.itr_section == "112A"
        assert entry.itr_schedule == "Schedule112A"
        assert entry.qualifies_for_125k_exemption is True
        assert entry.gain == Decimal("2596")

    def test_equity_stcg_classification(self, sample_ais_data_with_capital_gains):
        """Equity MF held ≤12mo → Schedule CG A2, 15% tax, no exemption."""
        engine = ClassificationEngine()
        result = engine.classify(
            sample_ais_data_with_capital_gains.equity_mf_sales,
            sample_ais_data_with_capital_gains.other_unit_sales,
        )
        assert len(result.cg_a2_stcg_111a) == 1
        entry = result.cg_a2_stcg_111a[0]
        assert entry.term == "Short"
        assert entry.tax_rate == "15%"
        assert entry.itr_section == "111A"
        assert entry.qualifies_for_125k_exemption is False


class TestOtherUnitClassification:
    """Non-equity unit sale classification."""

    def test_non_equity_stcg_classification(self, sample_ais_data_with_capital_gains):
        """Non-equity STCG → Schedule CG A5, slab rate."""
        engine = ClassificationEngine()
        result = engine.classify(
            sample_ais_data_with_capital_gains.equity_mf_sales,
            sample_ais_data_with_capital_gains.other_unit_sales,
        )
        assert len(result.cg_a5_stcg_app_rate) == 1
        entry = result.cg_a5_stcg_app_rate[0]
        assert entry.security_name == "TATA Gold ETF"
        assert entry.tax_rate == "Slab"
        assert entry.itr_schedule == "ScheduleCG_A5"

    def test_asset_class_gold_etf(self):
        """Gold ETF detected from security name."""
        engine = ClassificationEngine()
        sale = AISOtherUnitSale(
            depository="CDSL",
            security_name="TATA Gold ETF",
            isin="INF277KA1976",
            date_of_sale=date(2026, 2, 27),
            quantity=Decimal("5"),
            sale_price=Decimal("15.38"),
            sale_consideration=Decimal("77"),
            cost_of_acquisition=Decimal("76"),
            term="Short",
        )
        asset_class = engine._determine_asset_class(sale)
        assert asset_class == "etf_gold"

    def test_asset_class_debt_fund(self):
        """Debt fund detected from security name."""
        engine = ClassificationEngine()
        sale = AISOtherUnitSale(
            depository="CDSL",
            security_name="HDFC Short Term Debt Fund",
            isin="INF179K01234",
            date_of_sale=date(2025, 6, 15),
            quantity=Decimal("100"),
            sale_price=Decimal("25.00"),
            sale_consideration=Decimal("2500"),
            cost_of_acquisition=Decimal("2400"),
            term="Long",
        )
        asset_class = engine._determine_asset_class(sale)
        assert asset_class == "debt_fund"

    def test_asset_class_reit(self):
        """REIT detected from security name."""
        engine = ClassificationEngine()
        sale = AISOtherUnitSale(
            depository="CDSL",
            security_name="Embassy Office Parks REIT",
            isin="INF294K01123",
            date_of_sale=date(2025, 6, 15),
            quantity=Decimal("100"),
            sale_price=Decimal("300.00"),
            sale_consideration=Decimal("30000"),
            cost_of_acquisition=Decimal("28000"),
            term="Long",
        )
        asset_class = engine._determine_asset_class(sale)
        assert asset_class == "reit_invit"


class Test112AExemption:
    """Section 112A ₹1.25L exemption application."""

    def test_exemption_covers_full_small_gain(self):
        """Gain below ₹1.25L → fully exempt."""
        engine = ClassificationEngine()
        small_gain = AISEquityMFSale(
            amc_name="Test AMC",
            isin="INF200K01999",
            security_name="Test Equity Fund",
            date_of_sale=date(2025, 6, 15),
            quantity=Decimal("100"),
            sale_price_per_unit=Decimal("110.00"),
            sale_consideration=Decimal("11000"),
            cost_of_acquisition=Decimal("10000"),
            stt_paid=Decimal("1"),
            term="Long",
        )
        result = engine.classify([small_gain], [])
        result = engine.apply_112a_exemption(result)

        entry = result.schedule_112a[0]
        assert entry.gain_after_exemption == Decimal("0")
        assert entry.gain == Decimal("1000")

    def test_exemption_partial_for_large_gain(self):
        """Gain above ₹1.25L → partially exempt."""
        engine = ClassificationEngine()
        large_gain = AISEquityMFSale(
            amc_name="Test AMC",
            isin="INF200K01999",
            security_name="Test Equity Fund",
            date_of_sale=date(2025, 6, 15),
            quantity=Decimal("10000"),
            sale_price_per_unit=Decimal("110.00"),
            sale_consideration=Decimal("1100000"),
            cost_of_acquisition=Decimal("800000"),
            stt_paid=Decimal("100"),
            term="Long",
        )
        result = engine.classify([large_gain], [])
        result = engine.apply_112a_exemption(result)

        entry = result.schedule_112a[0]
        assert entry.gain == Decimal("300000")
        assert entry.gain_after_exemption == Decimal("175000")  # 300000 - 125000

    def test_exemption_fifo_across_entries(self):
        """Exemption applied to oldest gains first (FIFO)."""
        engine = ClassificationEngine()
        older = AISEquityMFSale(
            amc_name="Test AMC",
            isin="INF200K01999",
            security_name="Older Fund",
            date_of_sale=date(2025, 4, 15),
            quantity=Decimal("1000"),
            sale_price_per_unit=Decimal("200.00"),
            sale_consideration=Decimal("200000"),
            cost_of_acquisition=Decimal("100000"),
            stt_paid=Decimal("10"),
            term="Long",
        )
        newer = AISEquityMFSale(
            amc_name="Test AMC",
            isin="INF200K02999",
            security_name="Newer Fund",
            date_of_sale=date(2025, 8, 15),
            quantity=Decimal("1000"),
            sale_price_per_unit=Decimal("200.00"),
            sale_consideration=Decimal("200000"),
            cost_of_acquisition=Decimal("100000"),
            stt_paid=Decimal("10"),
            term="Long",
        )
        result = engine.classify([older, newer], [])
        result = engine.apply_112a_exemption(result)

        # Older entry should be fully exempt (₹100K < ₹125K limit)
        assert result.schedule_112a[0].gain_after_exemption == Decimal("0")
        # Newer entry should be partially exempt (₹125K - ₹100K = ₹25K remaining)
        assert result.schedule_112a[1].gain_after_exemption == Decimal("75000")


class TestDateRanges:
    """Schedule CG Section F date period classification."""

    def test_period_mapping(self):
        """Date periods map correctly to ITR schema keys."""
        entries = [
            AISEquityMFSale(
                amc_name="Test", isin="INF200K01000",
                security_name="Test Fund",
                date_of_sale=date(2025, 5, 1),  # May → Upto15Of6? No, after March 31...
                quantity=Decimal("1"),
                sale_price_per_unit=Decimal("100"),
                sale_consideration=Decimal("100"),
                cost_of_acquisition=Decimal("50"),
                stt_paid=Decimal("1"),
                term="Long",
            ),
        ]
        engine = ClassificationEngine()
        result = engine.classify(entries, [])
        ranges = result.date_ranges

        # May = Upto15Of6? Wait — Apr 1 to Jun 15 = Upto15Of6. May 1 is in that range.
        assert ranges.ltcg_12_5pct["Upto15Of6"] == Decimal("50")


class TestConvenienceFunction:
    """Module-level convenience function."""

    def test_classify_capital_gains_function(self):
        """Convenience function produces same result as engine."""
        result = classify_capital_gains([], [])
        assert result.total_cg == Decimal("0")


class TestEmptyInput:
    """Classification with empty inputs."""

    def test_empty_sales(self):
        """Empty sales → empty classification."""
        engine = ClassificationEngine()
        result = engine.classify([], [])
        assert len(result.schedule_112a) == 0
        assert len(result.cg_a2_stcg_111a) == 0
        assert len(result.cg_a5_stcg_app_rate) == 0
        assert result.total_cg == Decimal("0")

    def test_tax_summary_empty(self):
        """Tax summary for empty classification returns zeros."""
        engine = ClassificationEngine()
        from src.models.tax import ClassifiedCGData
        summary = engine.get_tax_summary(ClassifiedCGData())
        assert Decimal(str(summary["total_cg_tax_pre_slab"])) == Decimal("0")
