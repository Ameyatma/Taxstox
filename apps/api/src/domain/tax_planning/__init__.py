"""Tax Planning bounded context — Scenarios, loss harvesting, projections.

Domain layer. Zero framework imports. Pure Python.

Traceability: C19.1 (Scenario Simulator), C19.2 (Tax-Loss Harvesting),
             C19.3 (Multi-Year Projection)
"""

from src.domain.tax_planning.loss_harvesting import (
    AssetType,
    HarvestingRecommendation,
    LossHarvestingOpportunity,
)
from src.domain.tax_planning.projection import (
    MultiYearProjection,
    ProjectionAssumption,
    YearProjection,
)
from src.domain.tax_planning.scenario import (
    ScenarioComparison,
    ScenarioVariable,
    TaxScenario,
)

__all__ = [
    "AssetType",
    "HarvestingRecommendation",
    "LossHarvestingOpportunity",
    "MultiYearProjection",
    "ProjectionAssumption",
    "ScenarioComparison",
    "ScenarioVariable",
    "TaxScenario",
    "YearProjection",
]
