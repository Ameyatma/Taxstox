"""Rule Testing Framework — Verify tax rules across financial years.

Tests that rules produce correct, deterministic outputs and that
changes to one FY's rules do not affect other FYs.

Traceability: C12.5 (Rule Testing Framework — High gap, 0%→50%)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable

from src.engine.rules.config import rule_repository, TaxYearConfig
from src.engine.rules.evaluator import RuleEvaluator
from src.models.financial_year import FinancialYear


@dataclass(frozen=True)
class RuleTestCase:
    """A single rule test case with known inputs and expected output."""

    test_id: str
    description: str
    financial_year: FinancialYear
    rule_name: str                     # e.g., "slab_tax_new", "rebate_87a"
    input_data: dict[str, Any]
    expected_output: Any               # Expected result
    tolerance: Decimal = Decimal("0")  # Allowed difference (0 = exact match)


@dataclass
class RuleTestResult:
    """Result of running a single rule test case."""

    test_case: RuleTestCase
    passed: bool
    actual_output: Any = None
    error_message: str = ""


@dataclass
class RuleTestSuite:
    """Collection of rule test cases run against the RuleRepository + RuleEvaluator."""

    cases: list[RuleTestCase] = field(default_factory=list)
    results: list[RuleTestResult] = field(default_factory=list)

    def add_case(self, case: RuleTestCase) -> None:
        self.cases.append(case)

    def run_all(self) -> list[RuleTestResult]:
        """Run all test cases. Returns results."""
        evaluator = RuleEvaluator()
        self.results = []

        for case in self.cases:
            try:
                config = rule_repository.get(case.financial_year)
                actual = self._evaluate(case, config, evaluator)
                passed = self._compare(case.expected_output, actual, case.tolerance)
                self.results.append(RuleTestResult(
                    test_case=case, passed=passed, actual_output=actual,
                ))
            except Exception as e:
                self.results.append(RuleTestResult(
                    test_case=case, passed=False, error_message=str(e),
                ))

        return self.results

    def _evaluate(self, case: RuleTestCase, config: TaxYearConfig, evaluator: RuleEvaluator) -> Any:
        """Evaluate a rule test case against the given config."""
        rule = case.rule_name
        inp = case.input_data

        if rule == "slab_tax_new":
            return evaluator.compute_slab_tax(
                inp["income"], config.new_regime.slabs,
            )
        elif rule == "slab_tax_old":
            return evaluator.compute_slab_tax(
                inp["income"], config.old_regime.slabs,
            )
        elif rule == "rebate_87a_new":
            return evaluator.compute_rebate(
                inp["tax_before_rebate"], inp["total_income"], config.new_regime,
            )
        elif rule == "rebate_87a_old":
            return evaluator.compute_rebate(
                inp["tax_before_rebate"], inp["total_income"], config.old_regime,
            )
        elif rule == "surcharge":
            return evaluator.compute_surcharge(
                inp["total_income"], inp["tax_after_rebate"], config,
            )
        elif rule == "cess":
            return evaluator.compute_cess(
                inp["tax_after_rebate"], inp.get("surcharge", Decimal("0")), config.cess_rate,
            )
        elif rule == "deduction_limit":
            return config.get_deduction_limit(inp["section"], inp.get("regime"))
        else:
            raise ValueError(f"Unknown rule: {rule}")

    @staticmethod
    def _compare(expected: Any, actual: Any, tolerance: Decimal) -> bool:
        if isinstance(expected, Decimal) and isinstance(actual, Decimal):
            return abs(expected - actual) <= tolerance
        return expected == actual

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def all_passed(self) -> bool:
        return self.failed_count == 0 and len(self.results) > 0


# ── Standard Test Suite ──────────────────────────────────────────────

def build_standard_rule_test_suite() -> RuleTestSuite:
    """Build the standard rule test suite covering both FYs and both regimes."""
    suite = RuleTestSuite()
    FY25 = FinancialYear.from_string("FY2025-26")
    FY24 = FinancialYear.from_string("FY2024-25")

    # ── Slab Tax Tests ──
    # FY2025-26 New Regime: 0-4L:0%, 4-8L:5%, 8-12L:10%, 12-16L:15%, 16-20L:20%, 20-24L:25%, >24L:30%
    suite.add_case(RuleTestCase("SLAB-001", "New Regime ₹5L income", FY25,
        "slab_tax_new", {"income": Decimal("500000")}, Decimal("5000")))
    suite.add_case(RuleTestCase("SLAB-002", "New Regime ₹10L income", FY25,
        "slab_tax_new", {"income": Decimal("1000000")}, Decimal("40000")))
    suite.add_case(RuleTestCase("SLAB-003", "New Regime ₹3L (below exemption)", FY25,
        "slab_tax_new", {"income": Decimal("300000")}, Decimal("0")))

    # FY2024-25 New Regime: 0-3L:0%, 3-7L:5%, 7-10L:10%, 10-12L:15%, 12-15L:20%, >15L:30%
    suite.add_case(RuleTestCase("SLAB-004", "FY24-25 New Regime ₹5L", FY24,
        "slab_tax_new", {"income": Decimal("500000")}, Decimal("10000")))

    # FY2025-26 Old Regime: 0-2.5L:0%, 2.5-5L:5%, 5-10L:20%, >10L:30%
    suite.add_case(RuleTestCase("SLAB-005", "Old Regime ₹4L income", FY25,
        "slab_tax_old", {"income": Decimal("400000")}, Decimal("7500")))

    # ── Rebate Tests ──
    suite.add_case(RuleTestCase("REB-001", "87A New Regime below threshold", FY25,
        "rebate_87a_new", {"tax_before_rebate": Decimal("30000"), "total_income": Decimal("1000000")},
        Decimal("30000")))
    suite.add_case(RuleTestCase("REB-002", "87A New Regime above threshold", FY25,
        "rebate_87a_new", {"tax_before_rebate": Decimal("80000"), "total_income": Decimal("1500000")},
        Decimal("0")))

    # ── Surcharge Tests ──
    suite.add_case(RuleTestCase("SUR-001", "No surcharge below ₹50L", FY25,
        "surcharge", {"total_income": Decimal("4000000"), "tax_after_rebate": Decimal("500000")},
        Decimal("0")))
    suite.add_case(RuleTestCase("SUR-002", "10% surcharge above ₹50L", FY25,
        "surcharge", {"total_income": Decimal("6000000"), "tax_after_rebate": Decimal("500000")},
        Decimal("50000")))

    # ── Deduction Limit Tests ──
    suite.add_case(RuleTestCase("DED-001", "80C limit FY2025-26", FY25,
        "deduction_limit", {"section": "80C", "regime": "old"}, Decimal("150000")))
    suite.add_case(RuleTestCase("DED-002", "80C not available in New Regime", FY25,
        "deduction_limit", {"section": "80C", "regime": "new"}, Decimal("0")))

    return suite
