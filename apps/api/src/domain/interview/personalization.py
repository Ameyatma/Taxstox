"""Interview Personalization Engine — Scores and adapts questions to taxpayer profile.

Uses taxpayer age, income level, detected data, and regime to determine
which questions are relevant and suppress those that aren't.

Target: reduce average questions from 5 to ≤3.

Traceability: C13.6 (Interview Personalization — 10%→50%, P4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class TaxpayerProfile:
    """Minimal taxpayer profile for interview personalization.

    Derived from uploaded documents and AIS data.
    """
    age: int = 0
    has_hra: bool = False           # Detected HRA in Form 16
    has_epf: bool = False            # Detected EPF in Form 16
    has_home_loan_hint: bool = False # SFT or interest in AIS suggesting home loan
    has_capital_gains: bool = False  # CG transactions detected
    has_interest_income: bool = False # Interest entries in AIS
    has_dividend_income: bool = False
    has_foreign_assets: bool = False
    has_business_income: bool = False
    is_senior_citizen: bool = False
    is_super_senior_citizen: bool = False
    regime: str = "new"             # "old" or "new"
    estimated_income: Decimal = Decimal("0")
    total_80c_detected: Decimal = Decimal("0")  # From Form 16 EPF
    has_form16: bool = False
    has_ais: bool = False


@dataclass(frozen=True)
class QuestionRelevanceScore:
    """How relevant is a question to this specific taxpayer?"""

    question_id: str
    score: float = 0.0              # 0.0 (irrelevant) to 1.0 (essential)
    suppress: bool = False           # True = don't ask this question
    reason: str = ""                 # Why suppressed (or why kept)


class InterviewPersonalizationEngine:
    """Scores question relevance based on taxpayer profile.

    Domain service. No framework dependencies.
    Dedicated to one question: "Should we ask THIS question to THIS taxpayer?"
    """

    def score_question(
        self,
        question_id: str,
        profile: TaxpayerProfile,
    ) -> QuestionRelevanceScore:
        """Score relevance of a question for a given taxpayer profile."""
        scorers = {
            "rent": self._score_rent,
            "health_insurance": self._score_health,
            "additional_80c": self._score_80c,
            "home_loan": self._score_home_loan,
            "other_income": self._score_other_income,
        }
        scorer = scorers.get(question_id)
        if scorer:
            return scorer(profile)
        return QuestionRelevanceScore(
            question_id=question_id,
            score=0.5,
            suppress=False,
            reason="Unknown question type — asking conservatively",
        )

    def personalize(
        self,
        questions: list[str],
        profile: TaxpayerProfile,
    ) -> list[QuestionRelevanceScore]:
        """Score all candidate questions. Returns sorted by relevance (highest first)."""
        scores = [self.score_question(qid, profile) for qid in questions]
        # Sort by score descending, suppressed questions last
        scores.sort(key=lambda s: (s.suppress, -s.score))
        return scores

    def get_active_questions(
        self,
        questions: list[str],
        profile: TaxpayerProfile,
        max_questions: int = 5,
    ) -> list[str]:
        """Get the minimal set of questions to ask, respecting suppression and max."""
        scores = self.personalize(questions, profile)
        active = [s.question_id for s in scores if not s.suppress]
        return active[:max_questions]

    # ── Per-Question Scorers ──────────────────────────────────────────

    def _score_rent(self, profile: TaxpayerProfile) -> QuestionRelevanceScore:
        """Rent/HRA question relevance."""
        # Only relevant under Old Regime with HRA
        if profile.regime == "new":
            return QuestionRelevanceScore(
                question_id="rent", score=0.0, suppress=True,
                reason="HRA exemption not available under New Regime",
            )
        if not profile.has_hra:
            return QuestionRelevanceScore(
                question_id="rent", score=0.0, suppress=True,
                reason="No HRA component detected in Form 16",
            )
        return QuestionRelevanceScore(
            question_id="rent", score=0.95, suppress=False,
            reason="HRA detected — rent information needed for exemption computation",
        )

    def _score_health(self, profile: TaxpayerProfile) -> QuestionRelevanceScore:
        """Health insurance question relevance."""
        if profile.regime == "new":
            return QuestionRelevanceScore(
                question_id="health_insurance", score=0.0, suppress=True,
                reason="80D deduction not available under New Regime",
            )
        # More relevant for older taxpayers
        if profile.is_senior_citizen:
            return QuestionRelevanceScore(
                question_id="health_insurance", score=0.90, suppress=False,
                reason="Senior citizen — higher 80D limits available (₹50,000)",
            )
        return QuestionRelevanceScore(
            question_id="health_insurance", score=0.70, suppress=False,
            reason="80D deduction available under Old Regime",
        )

    def _score_80c(self, profile: TaxpayerProfile) -> QuestionRelevanceScore:
        """Additional 80C investments question relevance."""
        if profile.regime == "new":
            return QuestionRelevanceScore(
                question_id="additional_80c", score=0.0, suppress=True,
                reason="80C deduction not available under New Regime",
            )
        # If EPF already fills 80C (≥₹1.5L), suppress
        if profile.total_80c_detected >= Decimal("150000"):
            return QuestionRelevanceScore(
                question_id="additional_80c", score=0.1, suppress=True,
                reason=f"EPF of ₹{profile.total_80c_detected:,.0f} already covers full 80C limit of ₹1,50,000",
            )
        # If EPF is close to limit, low priority
        if profile.total_80c_detected >= Decimal("100000"):
            return QuestionRelevanceScore(
                question_id="additional_80c", score=0.30, suppress=False,
                reason=f"EPF covers ₹{profile.total_80c_detected:,.0f} — limited remaining 80C space",
            )
        return QuestionRelevanceScore(
            question_id="additional_80c", score=0.85, suppress=False,
            reason="80C space available — additional investments could reduce tax",
        )

    def _score_home_loan(self, profile: TaxpayerProfile) -> QuestionRelevanceScore:
        """Home loan question relevance."""
        if profile.regime == "new":
            # Home loan interest deduction not in new regime, but principal in 80C also not
            return QuestionRelevanceScore(
                question_id="home_loan", score=0.0, suppress=True,
                reason="Home loan interest deduction not available under New Regime",
            )
        if profile.has_home_loan_hint:
            return QuestionRelevanceScore(
                question_id="home_loan", score=0.90, suppress=False,
                reason="Home loan evidence detected in AIS — likely has deductible interest",
            )
        return QuestionRelevanceScore(
            question_id="home_loan", score=0.40, suppress=False,
            reason="No home loan evidence detected but may still have one",
        )

    def _score_other_income(self, profile: TaxpayerProfile) -> QuestionRelevanceScore:
        """Other income question relevance."""
        # Always ask (catch-all) but lower priority if we've detected a lot
        reasons = []
        if profile.has_capital_gains:
            reasons.append("Capital gains already detected")
        if profile.has_interest_income:
            reasons.append("Interest income detected from AIS")
        if profile.has_foreign_assets:
            reasons.append("Foreign assets detected")
        if profile.has_business_income:
            reasons.append("Business income detected")

        if reasons:
            return QuestionRelevanceScore(
                question_id="other_income", score=0.50, suppress=False,
                reason=". ".join(reasons) + ". Still worth asking about unreported income.",
            )
        return QuestionRelevanceScore(
            question_id="other_income", score=0.75, suppress=False,
            reason="No significant income sources detected — important to catch unreported income",
        )


# ── Singleton ─────────────────────────────────────────────────────────

personalization_engine = InterviewPersonalizationEngine()
