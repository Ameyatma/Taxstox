from src.engine.classifier import ClassificationEngine, classify_capital_gains
from src.engine.regime_optimizer_v2 import RegimeOptimizerV2
from src.engine.questions import QuestionEngine

# Backward-compatible alias for callers using RegimeOptimizer
RegimeOptimizer = RegimeOptimizerV2
optimize_regime = RegimeOptimizerV2().optimize

__all__ = [
    "ClassificationEngine", "classify_capital_gains",
    "RegimeOptimizer", "RegimeOptimizerV2", "optimize_regime",
    "QuestionEngine",
]
