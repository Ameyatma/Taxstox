"""Recommendation Engine — AI-assisted tax decision intelligence.

Produces detailed, human-readable explanations for:
  - Why one regime is better than the other
  - What deductions made the difference
  - Confidence level in the recommendation
  - What missing data could change the recommendation
  - Actionable optimization suggestions

This replaces simple "Old Regime saves ₹X" with:
  "Old Regime is recommended because your HRA (₹2,06,753),
   home loan interest (₹2,00,000), and 80C (₹1,50,000) deductions
   reduce taxable income by ₹5,56,753. The New Regime's lower slab
   rates don't compensate for these deductions. Confidence: 94%."

Architecture aligns with the Tax Decision Intelligence System vision.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class RecommendationReason:
    """One reason contributing to the recommendation."""
    category: str           # "deduction", "exemption", "slab_rate", "missing_data"
    description: str         # Human-readable explanation
    impact_amount: Decimal   # How much this affects the tax difference
    confidence: float        # 0.0-1.0 how certain we are about this


@dataclass
class OptimizationSuggestion:
    """An actionable tax-saving suggestion."""
    action: str              # What to do: "Invest ₹50,000 in NPS"
    section: str             # Which tax section: "80CCD(1B)"
    potential_saving: Decimal  # How much tax could be saved
    deadline: str            # "Before March 31, 2026"
    priority: int            # 1-100, higher = more important
    explanation: str         # Why this helps


@dataclass
class RecommendationResult:
    """Complete tax regime recommendation with full reasoning."""
    recommended_regime: str          # "new" or "old"
    confidence: float = 0.85          # 0.0-1.0
    savings: Decimal = Decimal("0")   # How much the user saves with recommended regime

    # Detailed reasoning
    key_reasons: list[RecommendationReason] = field(default_factory=list)
    deduction_impact: dict = field(default_factory=dict)  # Per-deduction impact

    # What's holding back confidence
    missing_data: list[str] = field(default_factory=list)
    low_confidence_items: list[str] = field(default_factory=list)

    # Proactive suggestions
    optimizations: list[OptimizationSuggestion] = field(default_factory=list)

    # Summary paragraph
    summary: str = ""
    detailed_explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "recommended": self.recommended_regime,
            "confidence": self.confidence,
            "savings": str(self.savings),
            "key_reasons": [
                {"category": r.category, "description": r.description,
                 "impact": str(r.impact_amount), "confidence": r.confidence}
                for r in self.key_reasons
            ],
            "deduction_impact": {k: str(v) for k, v in self.deduction_impact.items()},
            "missing_data": self.missing_data,
            "low_confidence": self.low_confidence_items,
            "optimizations": [
                {"action": o.action, "section": o.section,
                 "potential_saving": str(o.potential_saving), "deadline": o.deadline,
                 "priority": o.priority, "explanation": o.explanation}
                for o in self.optimizations
            ],
            "summary": self.summary,
            "detailed_explanation": self.detailed_explanation,
        }


class RecommendationEngine:
    """Generates intelligent tax regime recommendations with reasoning.

    This is the AI layer on top of the deterministic tax computation.
    It answers NOT just "which regime is better" but "WHY, with what
    confidence, and what could change the recommendation."
    """

    def analyze(
        self,
        new_breakdown: dict,
        old_breakdown: dict,
        hra_received: Decimal = Decimal("0"),
        has_home_loan: bool = False,
        total_80c: Decimal = Decimal("0"),
        total_80d: Decimal = Decimal("0"),
        total_80ccd1b: Decimal = Decimal("0"),
        total_80tta: Decimal = Decimal("0"),
        has_capital_gains: bool = False,
    ) -> RecommendationResult:
        """Generate full recommendation with reasoning."""

        new_tax = Decimal(new_breakdown.get("net_tax", "0"))
        old_tax = Decimal(old_breakdown.get("net_tax", "0"))

        if new_tax <= old_tax:
            recommended = "new"
            savings = old_tax - new_tax
        else:
            recommended = "old"
            savings = new_tax - old_tax

        result = RecommendationResult(
            recommended_regime=recommended,
            savings=savings,
        )

        reasons: list[RecommendationReason] = []
        missing: list[str] = []
        low_conf: list[str] = []
        optimizations: list[OptimizationSuggestion] = []

        # ── Analyze WHY one regime wins ──

        # 1. Deduction impact
        new_ded = Decimal(new_breakdown.get("deductions_total", "0"))
        old_ded = Decimal(old_breakdown.get("deductions_total", "0"))
        ded_diff = old_ded - new_ded

        if ded_diff > 0:
            # Old regime has more deductions
            reasons.append(RecommendationReason(
                category="deduction",
                description=f"Old Regime allows ₹{int(ded_diff):,} more in deductions "
                            f"(total ₹{int(old_ded):,} vs ₹{int(new_ded):,})",
                impact_amount=ded_diff,
                confidence=0.95,
            ))

        # 2. HRA exemption impact (only in Old Regime if rent data provided)
        new_hra = Decimal(new_breakdown.get("hra_exemption", "0"))
        old_hra = Decimal(old_breakdown.get("hra_exemption", "0"))
        if old_hra > 0:
            reasons.append(RecommendationReason(
                category="exemption",
                description=f"HRA Exemption of ₹{int(old_hra):,} available under "
                            f"Old Regime significantly reduces taxable income",
                impact_amount=old_hra,
                confidence=0.90 if hra_received > 0 else 0.50,
            ))
        elif hra_received > 0:
            missing.append("Rent amount not provided. If you pay rent, "
                          "HRA exemption could reduce Old Regime tax further.")

        # 3. Slab rate comparison
        new_slab_tax = Decimal(new_breakdown.get("tax_slab", "0"))
        old_slab_tax = Decimal(old_breakdown.get("tax_slab", "0"))
        new_total = Decimal(new_breakdown.get("total_income", "0"))
        old_total = Decimal(old_breakdown.get("total_income", "0"))

        if new_total > 0 and old_total > 0:
            new_eff_rate = (new_slab_tax / new_total * Decimal("100")).quantize(Decimal("0.1"))
            old_eff_rate = (old_slab_tax / old_total * Decimal("100")).quantize(Decimal("0.1"))

            if new_eff_rate < old_eff_rate:
                reasons.append(RecommendationReason(
                    category="slab_rate",
                    description=f"New Regime effective tax rate ({new_eff_rate}%) is lower than "
                                f"Old Regime ({old_eff_rate}%) due to wider slabs",
                    impact_amount=savings,
                    confidence=0.99,
                ))
            else:
                reasons.append(RecommendationReason(
                    category="slab_rate",
                    description=f"Old Regime deductions reduce income enough that the effective "
                                f"rate ({old_eff_rate}%) beats New Regime's slabs ({new_eff_rate}%)",
                    impact_amount=savings,
                    confidence=0.95,
                ))

        # ── Confidence scoring ──
        confidence = 0.85  # Base confidence

        # Deduct for missing data
        if hra_received > 0 and Decimal(new_breakdown.get("hra_exemption", "0")) == 0:
            confidence -= 0.10
            low_conf.append("HRA exemption not computed — rent data needed")
        if has_home_loan and Decimal(old_breakdown.get("home_loan_loss", "0")) == 0:
            confidence -= 0.05
            low_conf.append("Home loan interest may not be fully captured")
        if has_capital_gains and Decimal(old_breakdown.get("income_cg", "0")) == 0:
            confidence -= 0.05
            low_conf.append("Capital gains may need broker statement upload")

        confidence = max(0.50, min(0.99, confidence))
        result.confidence = confidence

        # ── Deduction impact breakdown ──
        ded_detail = new_breakdown.get("deductions_detail", {})
        result.deduction_impact = {
            "80C (EPF, PPF, LIC, etc.)": Decimal(str(ded_detail.get("sec80c", "0"))),
            "80CCD(1B) NPS": Decimal(str(ded_detail.get("sec80ccd1b", "0"))),
            "80CCD(2) Employer NPS": Decimal(str(ded_detail.get("sec80ccd2", "0"))),
            "80D Health Insurance": Decimal(str(ded_detail.get("sec80d", "0"))),
            "80TTA Savings Interest": Decimal(str(ded_detail.get("sec80tta", "0"))),
        }

        # ── Optimization suggestions ──
        old_80c = Decimal(str(ded_detail.get("sec80c", "0")))
        old_80d = Decimal(str(ded_detail.get("sec80d", "0")))
        old_80ccd1b = Decimal(str(ded_detail.get("sec80ccd1b", "0")))

        # Suggest NPS if not maxing out
        if recommended == "old" and old_80ccd1b < Decimal("50000"):
            remaining = Decimal("50000") - old_80ccd1b
            saving = remaining * Decimal("0.30")  # Assume 30% slab
            optimizations.append(OptimizationSuggestion(
                action=f"Invest ₹{int(remaining):,} more in NPS (80CCD(1B))",
                section="80CCD(1B)",
                potential_saving=saving + (saving * Decimal("0.04")),  # + cess
                deadline="Before March 31, 2026",
                priority=95,
                explanation=f"Additional NPS deduction would save {int(saving * Decimal('1.04')):,} in tax "
                           f"under Old Regime. This is above your 80C limit.",
            ))

        # Suggest health insurance if not claimed
        if recommended == "old" and old_80d == 0:
            optimizations.append(OptimizationSuggestion(
                action="Buy health insurance policy for yourself/family",
                section="80D",
                potential_saving=Decimal("7800"),  # 25K * 30% + cess
                deadline="Before March 31, 2026",
                priority=75,
                explanation="Health insurance premium up to ₹25,000 is deductible under 80D. "
                           "This also provides actual health coverage.",
            ))

        # If New Regime is close — suggest maximizing deductions to flip
        if recommended == "new" and savings < Decimal("20000"):
            optimizations.append(OptimizationSuggestion(
                action="Max out 80C (₹1.5L), 80D, and 80CCD(1B) deductions",
                section="80C + 80D + 80CCD(1B)",
                potential_saving=savings + Decimal("5000"),
                deadline="Before March 31, 2026",
                priority=85,
                explanation=f"Old Regime is within ₹{int(savings):,}. Maximizing deductions "
                           f"could make Old Regime the better choice.",
            ))

        # Sort optimizations by priority
        optimizations.sort(key=lambda o: o.priority, reverse=True)
        result.optimizations = optimizations[:5]  # Top 5

        # ── Build summary ──
        if recommended == "new":
            result.summary = (
                f"New Tax Regime is recommended for you, saving ₹{int(savings):,}. "
                f"The wider tax slabs and higher standard deduction (₹75,000 vs ₹50,000) "
                f"compensate for the loss of deductions."
            )
            if ded_diff > 0:
                result.summary += (
                    f" Under Old Regime, you'd get ₹{int(ded_diff):,} more in deductions, "
                    f"but your effective tax rate would still be higher."
                )
        else:
            result.summary = (
                f"Old Tax Regime is recommended for you, saving ₹{int(savings):,}. "
                f"Your deductions (HRA, 80C, 80D, NPS etc.) reduce taxable income "
                f"significantly — more than the New Regime's lower slabs can compensate."
            )

        result.detailed_explanation = self._build_explanation(
            result, reasons, new_breakdown, old_breakdown
        )
        result.key_reasons = reasons
        result.missing_data = missing
        result.low_confidence_items = low_conf

        return result

    def _build_explanation(
        self,
        result: RecommendationResult,
        reasons: list[RecommendationReason],
        new_bd: dict,
        old_bd: dict,
    ) -> str:
        """Build a detailed human-readable explanation."""
        parts = []

        parts.append(f"### Regime Recommendation: {result.recommended_regime.upper()} REGIME")
        parts.append(f"Confidence: {result.confidence:.0%}")
        parts.append(f"Tax Savings: ₹{int(result.savings):,}")
        parts.append("")

        parts.append("### Key Factors")
        for i, r in enumerate(reasons, 1):
            parts.append(f"{i}. {r.description}")

        if result.missing_data:
            parts.append("")
            parts.append("### Data That Could Change This")
            for m in result.missing_data:
                parts.append(f"- {m}")

        if result.optimizations:
            parts.append("")
            parts.append("### Recommended Actions")
            for o in result.optimizations[:3]:
                parts.append(f"- {o.action}: Save ~₹{int(o.potential_saving):,}")

        parts.append("")
        parts.append("### Comparison")
        parts.append(f"New Regime Tax: ₹{int(Decimal(new_bd.get('net_tax', '0'))):,}")
        parts.append(f"Old Regime Tax: ₹{int(Decimal(old_bd.get('net_tax', '0'))):,}")

        return "\n".join(parts)
