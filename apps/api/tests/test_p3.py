"""Unit tests for P3 — Entity Taxation."""

from decimal import Decimal


class TestEntityTaxEngine:
    def test_company_flat_25pct(self):
        from src.engine.entity_tax import EntityTaxEngine, EntityType
        engine = EntityTaxEngine()
        result = engine.compute(
            EntityType.COMPANY, Decimal("50000000"),
        )
        assert Decimal(result["tax"]) == Decimal("12500000")  # 25%

    def test_company_115baa_22pct(self):
        from src.engine.entity_tax import EntityTaxEngine, EntityType
        engine = EntityTaxEngine()
        result = engine.compute(
            EntityType.COMPANY_115BAA, Decimal("50000000"),
        )
        assert Decimal(result["tax"]) == Decimal("11000000")  # 22%

    def test_firm_30pct(self):
        from src.engine.entity_tax import EntityTaxEngine, EntityType
        engine = EntityTaxEngine()
        result = engine.compute(
            EntityType.FIRM, Decimal("1000000"),
        )
        assert Decimal(result["tax"]) == Decimal("300000")  # 30%

    def test_llp_same_as_firm(self):
        from src.engine.entity_tax import EntityTaxEngine, EntityType
        engine = EntityTaxEngine()
        result = engine.compute(
            EntityType.LLP, Decimal("1000000"),
        )
        assert Decimal(result["tax"]) == Decimal("300000")

    def test_company_surcharge_above_1cr(self):
        from src.engine.entity_tax import EntityTaxEngine, EntityType
        engine = EntityTaxEngine()
        result = engine.compute(
            EntityType.COMPANY, Decimal("20000000"),
        )
        surcharge = Decimal(result["surcharge"])
        assert surcharge > Decimal("0")

    def test_no_surcharge_below_threshold(self):
        from src.engine.entity_tax import EntityTaxEngine, EntityType
        engine = EntityTaxEngine()
        result = engine.compute(
            EntityType.FIRM, Decimal("5000000"),
        )
        assert Decimal(result["surcharge"]) == Decimal("0")

    def test_all_entity_types_computable(self):
        from src.engine.entity_tax import EntityTaxEngine, EntityType
        engine = EntityTaxEngine()
        for etype in EntityType:
            result = engine.compute(etype, Decimal("1000000"))
            assert "error" not in result, f"Failed for {etype}"
