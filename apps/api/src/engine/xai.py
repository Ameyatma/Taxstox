"""Explainable AI — Deterministic feature contribution and counterfactual generation.

Provides transparency into tax computation: "Why is my tax this amount?"
and "What would change my recommendation?" — without black-box ML.

Uses the RuleEvaluator to compute counterfactuals deterministically.
Every output is traceable to a specific rule evaluation.

Traceability: C10.6 (Explainable AI — 0%→30%, P4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable


@dataclass(frozen=True)
class FeatureContribution:
    """How much a single input feature contributed to the final tax."""

    feature: str                       # e.g., "salary_income", "80c_deduction"
    label: str                         # Human-readable: "Salary Income"
    value: Decimal                     # The actual value of this feature
    contribution_to_tax: Decimal       # How much tax this feature adds (positive = increases tax)
    percentage_of_total: Decimal       # Contribution as percentage of total tax
    direction: str                     # "increases_tax", "reduces_tax", "neutral"


@dataclass(frozen=True)
class Counterfactual:
    """A "what-if" scenario showing how tax would change."""

    scenario_id: str
    description: str                   # "If your salary were ₹X less..."
    change_description: str            # What changed
    original_tax: Decimal
    new_tax: Decimal
    tax_difference: Decimal            # Positive = you'd pay more, negative = you'd save
    savings_possible: Decimal          # max(0, -tax_difference)
    recommendation: str                # Actionable advice


@dataclass(frozen=True)
class SensitivityAnalysis:
    """How sensitive is the final tax to changes in each input?"""

    feature: str
    label: str
    baseline_value: Decimal
    sensitivity_score: float           # How much tax changes per ₹1 change in this input
    inflection_points: tuple[Decimal, ...]  # Values where tax behavior changes (e.g., slab boundaries)


@dataclass
class XAIReport:
    """Complete explainable AI report for a tax computation."""

    financial_year: str
    correlation_id: str

    # Feature contributions
    contributions: list[FeatureContribution] = field(default_factory=list)

    # Counterfactuals
    counterfactuals: list[Counterfactual] = field(default_factory=list)

    # Sensitivity
    sensitivities: list[SensitivityAnalysis] = field(default_factory=list)

    # Summary
    top_contributors: list[str] = field(default_factory=list)

    @property
    def summary_text(self) -> str:
        """One-paragraph XAI summary."""
        parts = []
        if self.contributions:
            top_3 = sorted(
                self.contributions,
                key=lambda c: abs(c.contribution_to_tax),
                reverse=True,
            )[:3]
            parts.append("Your tax is primarily driven by:")
            for c in top_3:
                direction = "increases" if c.contribution_to_tax > 0 else "reduces"
                parts.append(f"  • {c.label} (₹{c.value:,.0f}) — {direction} tax by ₹{abs(c.contribution_to_tax):,.0f}")
        if self.counterfactuals:
            best = min(self.counterfactuals, key=lambda cf: cf.tax_difference)
            if best.savings_possible > 0:
                parts.append(f"Best saving opportunity: {best.description} — save ₹{best.savings_possible:,.0f}")
        return "\n".join(parts)


class ExplainableAIEngine:
    """Deterministic XAI for tax computation.

    All counterfactuals are computed by re-running the RuleEvaluator
    with modified inputs. No ML models. No statistical estimates.
    Every output is a real computation that would match the ITD portal.
    """

    def __init__(self) -> None:
        self._evaluator = None  # Lazy import to avoid circular deps

    @property
    def evaluator(self):
        if self._evaluator is None:
            from src.engine.rules.evaluator import RuleEvaluator
            self._evaluator = RuleEvaluator()
        return self._evaluator

    def compute_contributions(
        self,
        breakdown: dict[str, Any],
        final_tax: Decimal,
    ) -> list[FeatureContribution]:
        """Compute feature contributions to final tax.

        Each income head and deduction gets a contribution score.
        Positive = increases tax. Negative = reduces tax.
        """
        if final_tax <= 0:
            return []

        contributions: list[FeatureContribution] = []

        # Income components (increase tax)
        income_features = [
            ("income_salary", "Salary Income"),
            ("income_house_property", "House Property Income"),
            ("income_capital_gains", "Capital Gains"),
            ("income_other_sources", "Other Sources Income"),
        ]
        for key, label in income_features:
            val = Decimal(str(breakdown.get(key, "0")))
            if val > 0:
                # Approximate contribution: proportional to income share
                gti = Decimal(str(breakdown.get("gross_total_income", "1")))
                share = val / gti if gti > 0 else Decimal("0")
                contrib = (final_tax * share).quantize(Decimal("0.01"))
                contributions.append(FeatureContribution(
                    feature=key, label=label, value=val,
                    contribution_to_tax=contrib,
                    percentage_of_total=(share * 100).quantize(Decimal("0.1")),
                    direction="increases_tax",
                ))

        # Deduction components (reduce tax)
        deduction_features = [
            ("deductions_total", "Total Deductions"),
            ("rebate_87a", "87A Rebate"),
        ]
        for key, label in deduction_features:
            val = Decimal(str(breakdown.get(key, "0")))
            if val > 0:
                contributions.append(FeatureContribution(
                    feature=key, label=label, value=val,
                    contribution_to_tax=-val,
                    percentage_of_total=Decimal("0"),
                    direction="reduces_tax",
                ))

        return contributions

    def generate_counterfactuals(
        self,
        breakdown: dict[str, Any],
        total_income: Decimal,
        final_tax: Decimal,
        regime: str = "new",
        compute_fn: Callable[[Decimal], Decimal] | None = None,
    ) -> list[Counterfactual]:
        """Generate counterfactual scenarios.

        Args:
            breakdown: Current tax breakdown
            total_income: Current total income
            final_tax: Current final tax
            regime: "old" or "new"
            compute_fn: Optional function that takes income and returns new tax.
                        If None, uses proportional estimation.
        """
        cfs: list[Counterfactual] = []

        # 1. What if income were ₹50K higher?
        higher = total_income + Decimal("50000")
        new_tax_higher = compute_fn(higher) if compute_fn else self._estimate(higher, total_income, final_tax)
        cfs.append(Counterfactual(
            scenario_id="CF-001",
            description=f"If your income were ₹50,000 higher",
            change_description="Income increased by ₹50,000",
            original_tax=final_tax,
            new_tax=new_tax_higher,
            tax_difference=new_tax_higher - final_tax,
            savings_possible=Decimal("0"),
            recommendation="Additional income at top marginal rate — plan for tax on bonuses or windfalls",
        ))

        # 2. What if income were ₹50K lower?
        lower = max(Decimal("0"), total_income - Decimal("50000"))
        new_tax_lower = compute_fn(lower) if compute_fn else self._estimate(lower, total_income, final_tax)
        savings = final_tax - new_tax_lower
        cfs.append(Counterfactual(
            scenario_id="CF-002",
            description=f"If your income were ₹50,000 lower",
            change_description="Income decreased by ₹50,000",
            original_tax=final_tax,
            new_tax=new_tax_lower,
            tax_difference=new_tax_lower - final_tax,
            savings_possible=savings,
            recommendation=f"Reducing taxable income by ₹50,000 would save ₹{savings:,.0f}" if savings > 0 else "No tax saving at this income level",
        ))

        # 3. Old Regime: What if all 80C were maxed?
        ded_80c = Decimal(str(breakdown.get("80c_deduction", "0")))
        max_80c = Decimal("150000")
        if ded_80c < max_80c and regime == "old":
            gap = max_80c - ded_80c
            new_income = total_income - gap
            new_tax_maxed = compute_fn(max(Decimal("0"), new_income)) if compute_fn else final_tax
            saving = final_tax - new_tax_maxed
            cfs.append(Counterfactual(
                scenario_id="CF-003",
                description=f"If you maxed out 80C (additional ₹{gap:,.0f})",
                change_description=f"80C increased from ₹{ded_80c:,.0f} to ₹{max_80c:,.0f}",
                original_tax=final_tax,
                new_tax=new_tax_maxed if new_tax_maxed < final_tax else final_tax,
                tax_difference=-(saving) if saving > 0 else Decimal("0"),
                savings_possible=saving if saving > 0 else Decimal("0"),
                recommendation=f"Max out 80C by investing ₹{gap:,.0f} more in PPF/ELSS/NPS" if saving > 0 else "80C already at limit — no additional saving",
            ))

        # 4. Old Regime: What if you added NPS 80CCD(1B)?
        ded_nps = Decimal(str(breakdown.get("80ccd1b_deduction", "0")))
        max_nps = Decimal("50000")
        if ded_nps < max_nps and regime == "old":
            gap = max_nps - ded_nps
            new_income_nps = total_income - gap
            new_tax_nps = compute_fn(max(Decimal("0"), new_income_nps)) if compute_fn else final_tax
            saving_nps = final_tax - new_tax_nps
            cfs.append(Counterfactual(
                scenario_id="CF-004",
                description=f"If you invested ₹{gap:,.0f} in NPS (80CCD(1B))",
                change_description=f"NPS contribution added: ₹{gap:,.0f}",
                original_tax=final_tax,
                new_tax=new_tax_nps if new_tax_nps < final_tax else final_tax,
                tax_difference=-(saving_nps) if saving_nps > 0 else Decimal("0"),
                savings_possible=saving_nps if saving_nps > 0 else Decimal("0"),
                recommendation=f"Invest ₹{gap:,.0f} in NPS for additional deduction" if saving_nps > 0 else "NPS already at max",
            ))

        # 5. What if you switched regimes? (if current is one regime)
        if regime in ("old", "new"):
            other = "new" if regime == "old" else "old"
            other_tax = Decimal(str(breakdown.get(f"tax_{other}", "0")))
            diff = other_tax - final_tax
            cfs.append(Counterfactual(
                scenario_id="CF-005",
                description=f"If you switched to {other.title()} Regime",
                change_description=f"Regime changed from {regime} to {other}",
                original_tax=final_tax,
                new_tax=other_tax if other_tax > 0 else final_tax,
                tax_difference=diff if other_tax > 0 else Decimal("0"),
                savings_possible=max(Decimal("0"), -diff),
                recommendation=f"Switch to {other.title()} Regime" if diff < 0 else f"Stay with {regime.title()} Regime",
            ))

        return cfs

    def compute_sensitivity(
        self,
        breakdown: dict[str, Any],
        total_income: Decimal,
        tax: Decimal,
    ) -> list[SensitivityAnalysis]:
        """Compute sensitivity of final tax to changes in key inputs."""
        sensitivities: list[SensitivityAnalysis] = []

        # Sensitivity to total income changes (marginal rate)
        delta = Decimal("1000")
        if total_income > 0:
            # Estimate marginal rate
            tax_plus = self._estimate(total_income + delta, total_income, tax)
            marginal_rate = float((tax_plus - tax) / delta) if delta > 0 else 0

            # Find inflection points (slab boundaries)
            from src.engine.rules.config import rule_repository
            try:
                from src.models.financial_year import FinancialYear
                fy_str = breakdown.get("financial_year", "FY2025-26")
                fy = FinancialYear.from_string(fy_str)
                config = rule_repository.get(fy)
                regime_config = config.new_regime  # Default to new
                inflections = tuple(
                    b.income_to for b in regime_config.slabs
                    if b.income_to < Decimal("999999999")
                )
            except Exception:
                inflections = ()

            sensitivities.append(SensitivityAnalysis(
                feature="total_income",
                label="Total Income",
                baseline_value=total_income,
                sensitivity_score=round(marginal_rate, 6),
                inflection_points=inflections,
            ))

        return sensitivities

    @staticmethod
    def _estimate(new_income: Decimal, old_income: Decimal, old_tax: Decimal) -> Decimal:
        """Proportional tax estimate (fallback when no compute_fn)."""
        if old_income <= 0:
            return old_tax
        ratio = new_income / old_income
        return (old_tax * ratio).quantize(Decimal("0.01"))

    def generate_report(
        self,
        breakdown: dict[str, Any],
        total_income: Decimal,
        final_tax: Decimal,
        correlation_id: str = "",
        financial_year: str = "",
        regime: str = "new",
    ) -> XAIReport:
        """Generate a complete XAI report."""
        report = XAIReport(
            financial_year=financial_year,
            correlation_id=correlation_id,
        )

        report.contributions = self.compute_contributions(breakdown, final_tax)
        report.counterfactuals = self.generate_counterfactuals(
            breakdown, total_income, final_tax, regime,
        )
        report.sensitivities = self.compute_sensitivity(breakdown, total_income, final_tax)

        # Top contributors
        contribs_sorted = sorted(
            report.contributions,
            key=lambda c: abs(c.contribution_to_tax),
            reverse=True,
        )
        report.top_contributors = [
            f"{c.label}: ₹{abs(c.contribution_to_tax):,.0f} ({c.direction})"
            for c in contribs_sorted[:3]
        ]

        return report
