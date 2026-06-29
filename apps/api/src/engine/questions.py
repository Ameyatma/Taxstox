"""Question Engine — Generates the minimal set of yes/no questions.

Principle: Only ask questions whose answers CANNOT be derived from Form 16 or AIS.
Everything auto-detectable is auto-detected. Questions are suppressed when irrelevant.
"""

from decimal import Decimal

from src.models.form16 import Form16Data, Regime
from src.models.ais import AISData
from src.models.tax import ClassifiedCGData
from src.models.api import Question, QuestionsResponse


class QuestionEngine:
    """Generates the minimal question set based on detected data."""

    def generate(
        self,
        itr_type: str,
        form16: Form16Data,
        ais: AISData,
        recommended_regime: Regime,
        regime_savings: Decimal,
    ) -> QuestionsResponse:
        """Generate the question set for the user."""
        questions: list[Question] = []
        income_summary = self._build_income_summary(form16, ais)

        # Q1: Rent / HRA
        rent_q = self._build_rent_question(form16, recommended_regime)
        if rent_q:
            questions.append(rent_q)

        # Q2: Health Insurance
        health_q = self._build_health_question(recommended_regime)
        if health_q:
            questions.append(health_q)

        # Q3: Additional 80C investments
        c80_q = self._build_80c_question(form16, recommended_regime)
        if c80_q:
            questions.append(c80_q)

        # Q4: Home Loan
        home_q = self._build_home_loan_question(ais, form16)
        if home_q:
            questions.append(home_q)

        # Q5: Other Income not in AIS
        other_q = self._build_other_income_question()
        if other_q:
            questions.append(other_q)

        return QuestionsResponse(
            itr_type=itr_type,
            regime_recommended=recommended_regime,
            regime_savings=regime_savings,
            income_summary=income_summary,
            questions=questions,
        )

    def _build_income_summary(self, form16: Form16Data, ais: AISData) -> dict:
        """Build a summary of detected income for the UI."""
        return {
            "salary": str(form16.part_b.total_gross_salary),
            "interest_savings": str(ais.total_savings_interest),
            "interest_fd": str(ais.total_tds_interest),
            "equity_mf_sales_count": len(ais.equity_mf_sales),
            "other_unit_sales_count": len(ais.other_unit_sales),
        }

    def _build_rent_question(
        self, form16: Form16Data, regime: Regime
    ) -> Question | None:
        """Q1: Rent payment — only relevant if HRA in Form 16 and Old Regime."""
        # HRA exemption only available under old regime
        if regime == Regime.NEW:
            return None

        # Check if HRA component exists
        if form16.annexure.hra == 0:
            return None

        return Question(
            id="rent",
            text="Do you pay rent for your accommodation?",
            type="yes_no",
            impact="HRA exemption reduces taxable salary under old regime.",
            sub_questions=[
                Question(
                    id="rent_amount",
                    text="How much rent do you pay per month?",
                    type="number",
                    depends_on="rent",
                    depends_on_answer="yes",
                ),
                Question(
                    id="rent_city",
                    text="Is your accommodation in a metro city?",
                    type="yes_no",
                    impact="Metro: 50% of basic, Non-metro: 40% of basic for HRA exemption.",
                    depends_on="rent",
                    depends_on_answer="yes",
                ),
                Question(
                    id="rent_landlord_pan",
                    text="Landlord's PAN? (Required if annual rent > ₹1,00,000)",
                    type="text",
                    depends_on="rent",
                    depends_on_answer="yes",
                ),
            ],
        )

    def _build_health_question(self, regime: Regime) -> Question | None:
        """Q2: Health Insurance — only under Old Regime (80D)."""
        if regime == Regime.NEW:
            return None

        return Question(
            id="health_insurance",
            text="Do you have health insurance?",
            type="yes_no",
            impact="80D deduction reduces taxable income under old regime.",
            sub_questions=[
                Question(
                    id="health_premium_self",
                    text="Annual premium for self + spouse + children?",
                    type="number",
                    impact="Max deduction: ₹25,000 (₹50,000 if senior citizen).",
                    depends_on="health_insurance",
                    depends_on_answer="yes",
                ),
                Question(
                    id="health_premium_parents",
                    text="Annual premium for parents?",
                    type="number",
                    depends_on="health_insurance",
                    depends_on_answer="yes",
                ),
                Question(
                    id="parents_senior_citizen",
                    text="Are your parents senior citizens (60+ years)?",
                    type="yes_no",
                    impact="Senior citizen parents: max deduction ₹50,000 instead of ₹25,000.",
                    depends_on="health_insurance",
                    depends_on_answer="yes",
                ),
            ],
        )

    def _build_80c_question(
        self, form16: Form16Data, regime: Regime
    ) -> Question | None:
        """Q3: Additional 80C investments — only under Old Regime."""
        if regime == Regime.NEW:
            return None

        # Show EPF already detected from Form 16
        epf_detected = form16.part_b.chapter_vi_a.sec80c

        return Question(
            id="additional_80c",
            text="Do you have any investments beyond EPF shown in your Form 16?",
            type="yes_no",
            impact=f"₹{epf_detected:,.0f} EPF already detected. 80C max: ₹1,50,000.",
            sub_questions=[
                Question(
                    id="80c_ppf",
                    text="PPF contribution?",
                    type="number",
                    depends_on="additional_80c",
                    depends_on_answer="yes",
                ),
                Question(
                    id="80c_elss",
                    text="ELSS mutual funds?",
                    type="number",
                    depends_on="additional_80c",
                    depends_on_answer="yes",
                ),
                Question(
                    id="80c_lic",
                    text="LIC premium?",
                    type="number",
                    depends_on="additional_80c",
                    depends_on_answer="yes",
                ),
                Question(
                    id="80c_tuition",
                    text="Children's tuition fees?",
                    type="number",
                    depends_on="additional_80c",
                    depends_on_answer="yes",
                ),
                Question(
                    id="80c_home_loan_principal",
                    text="Home loan principal repayment?",
                    type="number",
                    depends_on="additional_80c",
                    depends_on_answer="yes",
                ),
                Question(
                    id="80ccd1b_nps",
                    text="Own NPS contribution (beyond employer NPS)?",
                    type="number",
                    impact="Max additional ₹50,000 deduction under 80CCD(1B).",
                    depends_on="additional_80c",
                    depends_on_answer="yes",
                ),
            ],
        )

    def _build_home_loan_question(
        self, ais: AISData, form16: Form16Data
    ) -> Question | None:
        """Q4: Home Loan — check if evidence exists in AIS or Form 16."""
        # Auto-detect: any SFT for home loan, or 24(b) in Form 16
        # For now, ask if there are any hints (simplified)
        return Question(
            id="home_loan",
            text="Do you have a home loan?",
            type="yes_no",
            impact="Home loan interest deduction under Section 24(b) — up to ₹2,00,000 for self-occupied property.",
            sub_questions=[
                Question(
                    id="home_loan_interest",
                    text="Total interest paid on home loan this year?",
                    type="number",
                    depends_on="home_loan",
                    depends_on_answer="yes",
                ),
                Question(
                    id="home_loan_type",
                    text="Is the property self-occupied or let-out?",
                    type="dropdown",
                    impact="Self-occupied: max ₹2L deduction. Let-out: full interest deductible.",
                    depends_on="home_loan",
                    depends_on_answer="yes",
                ),
            ],
        )

    def _build_other_income_question(self) -> Question:
        """Q5: Income NOT in AIS — catch-all for unreported income."""
        return Question(
            id="other_income",
            text="Do you have any income NOT shown in your AIS?",
            type="yes_no",
            impact="Unreported income must be disclosed to avoid notices.",
            sub_questions=[
                Question(
                    id="other_income_freelance",
                    text="Freelance / consulting income?",
                    type="number",
                    depends_on="other_income",
                    depends_on_answer="yes",
                ),
                Question(
                    id="other_income_rental",
                    text="Rental income from property?",
                    type="number",
                    depends_on="other_income",
                    depends_on_answer="yes",
                ),
                Question(
                    id="other_income_crypto",
                    text="Crypto / Virtual Digital Assets income?",
                    type="number",
                    impact="VDA gains taxed at 30% under Section 115BBH.",
                    depends_on="other_income",
                    depends_on_answer="yes",
                ),
                Question(
                    id="other_income_foreign",
                    text="Foreign income?",
                    type="number",
                    impact="May require Schedule FA and Form 67 for foreign tax credit.",
                    depends_on="other_income",
                    depends_on_answer="yes",
                ),
            ],
        )
