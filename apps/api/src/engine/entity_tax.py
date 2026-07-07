"""Entity Tax Engine — LLP, Partnership, Company, Trust, AOP/BOI.

Entities have different tax rates, slab structures, and surcharge rules
compared to individuals. Companies pay flat rates; firms pay flat 30%.

Traceability: C6.3 (Surcharge entity types — 60%→85%),
             C9.5-C9.7 (ITR-5/6/7 builders — 0%→50%, P3)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

from src.engine.rules.evaluator import RuleEvaluator
from src.models.financial_year import FinancialYear


class EntityType(str, Enum):
    COMPANY = "company"               # Domestic company
    COMPANY_115BAA = "company_115baa" # 22% concessional
    COMPANY_115BAB = "company_115bab" # 15% new manufacturing
    FIRM = "firm"                     # Partnership firm (including LLP)
    LLP = "llp"                       # Limited Liability Partnership
    TRUST = "trust"                   # Charitable/religious trust
    AOP = "aop"                       # Association of Persons
    BOI = "boi"                       # Body of Individuals
    COOPERATIVE = "cooperative"       # Cooperative society
    LOCAL_AUTHORITY = "local_authority"


@dataclass(frozen=True)
class EntityTaxConfig:
    """Tax configuration for an entity type.

    Companies: flat rate + surcharge based on total income.
    Firms/LLPs: flat 30% + surcharge at 12% if income > ₹1Cr.
    Trusts: slab rates (same as individual) or Maximum Marginal Rate.
    """
    entity_type: EntityType
    base_rate: Decimal                         # e.g., 0.25 for 25% (company)
    surcharge_rate: Decimal = Decimal("0")     # e.g., 0.07 for 7% (company > ₹1Cr)
    surcharge_threshold: Decimal = Decimal("0")
    cess_rate: Decimal = Decimal("0.04")       # 4% HEC
    uses_slab_rates: bool = False              # Trust/AOP/BOI use progressive slabs
    is_flat_rate: bool = True                  # Most entities use flat rates


# Entity tax configurations per FY2025-26
ENTITY_TAX_CONFIGS: dict[EntityType, EntityTaxConfig] = {
    EntityType.COMPANY: EntityTaxConfig(
        entity_type=EntityType.COMPANY,
        base_rate=Decimal("0.25"),
        surcharge_rate=Decimal("0.07"),
        surcharge_threshold=Decimal("10000000"),  # ₹1Cr
    ),
    EntityType.COMPANY_115BAA: EntityTaxConfig(
        entity_type=EntityType.COMPANY_115BAA,
        base_rate=Decimal("0.22"),              # 22% + 10% surcharge
        surcharge_rate=Decimal("0.10"),
        surcharge_threshold=Decimal("0"),        # Always applicable
    ),
    EntityType.COMPANY_115BAB: EntityTaxConfig(
        entity_type=EntityType.COMPANY_115BAB,
        base_rate=Decimal("0.15"),              # 15% + 10% surcharge
        surcharge_rate=Decimal("0.10"),
        surcharge_threshold=Decimal("0"),
    ),
    EntityType.FIRM: EntityTaxConfig(
        entity_type=EntityType.FIRM,
        base_rate=Decimal("0.30"),
        surcharge_rate=Decimal("0.12"),
        surcharge_threshold=Decimal("10000000"),
    ),
    EntityType.LLP: EntityTaxConfig(
        entity_type=EntityType.LLP,
        base_rate=Decimal("0.30"),
        surcharge_rate=Decimal("0.12"),
        surcharge_threshold=Decimal("10000000"),
    ),
    EntityType.TRUST: EntityTaxConfig(
        entity_type=EntityType.TRUST,
        base_rate=Decimal("0.30"),              # Maximum Marginal Rate
        uses_slab_rates=True,                    # Can use slab rates for certain income
        is_flat_rate=False,
    ),
    EntityType.AOP: EntityTaxConfig(
        entity_type=EntityType.AOP,
        base_rate=Decimal("0.30"),
        uses_slab_rates=True,                    # Slab rates if individual members known
        is_flat_rate=False,
    ),
    EntityType.COOPERATIVE: EntityTaxConfig(
        entity_type=EntityType.COOPERATIVE,
        base_rate=Decimal("0.22"),              # 22% (115BAD option) or slab
        uses_slab_rates=True,
        is_flat_rate=False,
    ),
    EntityType.LOCAL_AUTHORITY: EntityTaxConfig(
        entity_type=EntityType.LOCAL_AUTHORITY,
        base_rate=Decimal("0.30"),
        is_flat_rate=True,
    ),
    EntityType.BOI: EntityTaxConfig(
        entity_type=EntityType.BOI,
        base_rate=Decimal("0.30"),
        uses_slab_rates=True,
        is_flat_rate=False,
    ),
}


class EntityTaxEngine:
    """Computes tax for non-individual entities.

    Companies pay a flat percentage of total income.
    Firms and LLPs pay 30% flat.
    Trusts and AOPs can use slab rates or Maximum Marginal Rate.
    """

    def compute(
        self,
        entity_type: EntityType,
        total_income: Decimal,
        fy: Optional[FinancialYear] = None,
    ) -> dict:
        """Compute entity tax liability."""
        config = ENTITY_TAX_CONFIGS.get(entity_type)
        if not config:
            return {"error": f"Unknown entity type: {entity_type}"}

        if config.is_flat_rate:
            tax = total_income * config.base_rate
        else:
            # Use individual slabs as fallback for trusts/AOPs
            from src.engine.rules.config import rule_repository
            fy_obj = fy or FinancialYear.from_string("FY2025-26")
            tax_config = rule_repository.get(fy_obj)
            evaluator = RuleEvaluator()
            tax = evaluator.compute_slab_tax(total_income, tax_config.old_regime.slabs)

        # Surcharge
        surcharge = Decimal("0")
        if config.surcharge_rate > 0 and (
            config.surcharge_threshold == 0
            or total_income > config.surcharge_threshold
        ):
            surcharge = tax * config.surcharge_rate
            # Marginal relief for companies
            if entity_type == EntityType.COMPANY and total_income > Decimal("10000000"):
                excess = total_income - Decimal("10000000")
                if surcharge > excess:
                    surcharge = excess

        # Cess
        cess = (tax + surcharge) * config.cess_rate

        final_tax = tax + surcharge + cess

        return {
            "entity_type": entity_type.value,
            "total_income": str(total_income),
            "base_rate": str(config.base_rate),
            "tax": str(tax.quantize(Decimal("0.01"))),
            "surcharge": str(surcharge.quantize(Decimal("0.01"))),
            "surcharge_rate": str(config.surcharge_rate),
            "cess": str(cess.quantize(Decimal("0.01"))),
            "net_tax": str(final_tax.quantize(Decimal("1"))),
        }
