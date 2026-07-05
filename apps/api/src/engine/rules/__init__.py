"""Rule Engine — versioned, FY-indexed tax rule repository.

M1 delivers:
- TaxYearConfig: Single source of truth for all FY-specific constants
- RuleRepository: Centralized rule storage with FY+regime indexing
- RuleEvaluator: Generic, deterministic rule evaluation engine
"""

from src.engine.rules.config import TaxYearConfig, RuleRepository
from src.engine.rules.evaluator import RuleEvaluator

__all__ = ["TaxYearConfig", "RuleRepository", "RuleEvaluator"]
