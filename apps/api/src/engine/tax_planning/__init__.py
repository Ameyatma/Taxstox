"""Tax Planning Engine — Scenario simulation, loss harvesting, projections.

Engine layer. Uses RuleEvaluator for deterministic recomputation.
No framework imports.
"""

from src.engine.tax_planning.scenario_simulator import ScenarioSimulator
from src.engine.tax_planning.loss_harvesting_engine import LossHarvestingEngine
from src.engine.tax_planning.multi_year_projection import MultiYearProjectionEngine

__all__ = [
    "ScenarioSimulator",
    "LossHarvestingEngine",
    "MultiYearProjectionEngine",
]
