from src.engine.classifier import ClassificationEngine, classify_capital_gains
from src.engine.questions import QuestionEngine
from src.engine.regime_optimizer_v2 import RegimeOptimizerV2

# Backward-compatible alias for callers using RegimeOptimizer
RegimeOptimizer = RegimeOptimizerV2
optimize_regime = RegimeOptimizerV2().optimize

__all__ = [
    "ClassificationEngine",
    "QuestionEngine",
    "RegimeOptimizer",
    "RegimeOptimizerV2",
    "classify_capital_gains",
    "optimize_regime",
]
