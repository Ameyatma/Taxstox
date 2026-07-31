"""Tax Planning bounded context — Scenarios, loss harvesting, projections.

Domain layer. Zero framework imports. Pure Python.

Traceability: C19.1 (Scenario Simulator), C19.2 (Tax-Loss Harvesting),
             C19.3 (Multi-Year Projection)
"""

from src.domain.tax_planning.scenario import (
    TaxScenario,
    ScenarioComparison,
    ScenarioVariable,
)
from src.domain.tax_planning.loss_harvesting import (
    LossHarvestingOpportunity,
    HarvestingRecommendation,
    AssetType,
)
from src.domain.tax_planning.projection import (
    MultiYearProjection,
    ProjectionAssumption,
    YearProjection,
)

__all__ = [
    "TaxScenario",
    "ScenarioComparison",
    "ScenarioVariable",
    "LossHarvestingOpportunity",
    "HarvestingRecommendation",
    "AssetType",
    "MultiYearProjection",
    "ProjectionAssumption",
    "YearProjection",
]
