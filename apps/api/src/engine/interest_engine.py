"""Interest Computation Engine — Sections 234A, 234B, 234C, 234F.

Computes interest for late filing, advance tax default, and advance tax deferment.
All rates and rules per the Income Tax Act.

Traceability: C6.7 (Interest 234A/B/C — High gap, 0%→complete)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from src.models.financial_year import FinancialYear


@dataclass(frozen=True)
class InterestResult:
    """Interest and fee computation result."""

    interest_234a: Decimal = Decimal("0")
    interest_234b: Decimal = Decimal("0")
    interest_234c: Decimal = Decimal("0")
    late_filing_fee_234f: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        return (
            self.interest_234a + self.interest_234b
            + self.interest_234c + self.late_filing_fee_234f
        )

    @property
    def interest_explanation(self) -> str:
        parts = []
        if self.interest_234a > 0:
            parts.append(f"234A (late filing): ₹{self.interest_234a:,.0f}")
        if self.interest_234b > 0:
            parts.append(f"234B (advance tax default): ₹{self.interest_234b:,.0f}")
        if self.interest_234c > 0:
            parts.append(f"234C (advance tax deferment): ₹{self.interest_234c:,.0f}")
        if self.late_filing_fee_234f > 0:
            parts.append(f"234F (late fee): ₹{self.late_filing_fee_234f:,.0f}")
        if not parts:
            return "No interest or late fees applicable."
        return ". ".join(parts)


class InterestEngine:
    """Computes interest under Sections 234A, 234B, 234C and fee under 234F.

    Interest rate: 1% per month (simple interest).
    Part of a month = full month for interest calculation.
    """

    INTEREST_RATE_PER_MONTH = Decimal("0.01")  # 1% per month

    def compute(
        self,
        tax_liability: Decimal,
        tds_credited: Decimal,
        advance_tax_paid: Decimal,
        self_assessment_tax: Decimal,
        filing_date: date,
        fy: FinancialYear,
        total_income: Decimal | None = None,
        has_business_income: bool = False,
        is_senior_citizen: bool = False,
        advance_tax_payments: dict[str, Decimal] | None = None,
    ) -> InterestResult:
        """Compute all applicable interest and fees.

        Args:
            tax_liability: Total tax liability (after cess)
            tds_credited: Total TDS available as credit
            advance_tax_paid: Total advance tax paid
            self_assessment_tax: Self-assessment tax paid before filing
            filing_date: Date of filing
            fy: Financial year
            has_business_income: Whether taxpayer has business income
            is_senior_citizen: Senior citizen exemption from advance tax
            advance_tax_payments: Date-labeled payments for 234C computation
        """
        # Net assessed tax = tax liability - TDS
        assessed_tax = max(Decimal("0"), tax_liability - tds_credited)

        # Due date based on taxpayer type
        due_date = self._get_due_date(fy, has_business_income)

        # ── 234A: Late Filing Interest ──
        interest_234a = self._compute_234a(assessed_tax, filing_date, due_date)

        # ── 234B: Advance Tax Default ──
        interest_234b = self._compute_234b(
            assessed_tax, advance_tax_paid, self_assessment_tax,
            is_senior_citizen, has_business_income,
        )

        # ── 234C: Advance Tax Deferment ──
        interest_234c = self._compute_234c(
            assessed_tax, advance_tax_paid, advance_tax_payments or {},
        )

        # ── 234F: Late Filing Fee ──
        ti = total_income if total_income is not None else tax_liability
        late_fee = self._compute_234f(filing_date, due_date, ti)

        total = interest_234a + interest_234b + interest_234c + late_fee

        return InterestResult(
            interest_234a=interest_234a,
            interest_234b=interest_234b,
            interest_234c=interest_234c,
            late_filing_fee_234f=late_fee,
        )

    def _compute_234a(
        self, assessed_tax: Decimal, filing_date: date, due_date: date,
    ) -> Decimal:
        """234A: 1% per month on unpaid tax from due date to filing date."""
        if filing_date <= due_date:
            return Decimal("0")
        if assessed_tax <= 0:
            return Decimal("0")

        months = self._months_between(due_date, filing_date)
        return (assessed_tax * self.INTEREST_RATE_PER_MONTH * months).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP,
        )

    def _compute_234b(
        self,
        assessed_tax: Decimal,
        advance_tax_paid: Decimal,
        self_assessment_tax: Decimal,
        is_senior_citizen: bool,
        has_business_income: bool,
    ) -> Decimal:
        """234B: 1% per month if advance tax paid < 90% of assessed tax.

        Senior citizens with no business income are exempt from advance tax.
        """
        if assessed_tax <= Decimal("10000"):
            return Decimal("0")

        # Senior citizen exemption
        if is_senior_citizen and not has_business_income:
            return Decimal("0")

        total_paid = advance_tax_paid + self_assessment_tax
        threshold = assessed_tax * Decimal("0.90")

        if total_paid >= threshold:
            return Decimal("0")

        shortfall = assessed_tax - total_paid
        # Interest from April 1 of assessment year to filing date (approximated as 12 months)
        months = 12
        return (shortfall * self.INTEREST_RATE_PER_MONTH * months).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP,
        )

    def _compute_234c(
        self,
        assessed_tax: Decimal,
        advance_tax_paid: Decimal,
        payments: dict[str, Decimal],
    ) -> Decimal:
        """234C: 1% per month for each installment shortfall.

        Installment schedule:
          - Jun 15: 15% of assessed tax
          - Sep 15: 45% of assessed tax (cumulative)
          - Dec 15: 75% of assessed tax (cumulative)
          - Mar 15: 100% of assessed tax (cumulative)

        Each shortfall incurs 1% per month for 3 months.
        """
        if assessed_tax <= Decimal("10000"):
            return Decimal("0")

        total_interest = Decimal("0")
        installments = [
            ("Jun15", Decimal("0.15"), 3),
            ("Sep15", Decimal("0.45"), 3),
            ("Dec15", Decimal("0.75"), 3),
            ("Mar15", Decimal("1.00"), 1),
        ]

        for label, required_pct, months in installments:
            required = assessed_tax * required_pct
            paid = payments.get(label, Decimal("0"))
            if paid < required:
                shortfall = required - paid
                total_interest += (
                    shortfall * self.INTEREST_RATE_PER_MONTH * months
                )

        return total_interest.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    def _compute_234f(
        self, filing_date: date, due_date: date, total_income: Decimal,
    ) -> Decimal:
        """234F: Late filing fee.
        - Up to Dec 31: ₹5,000
        - After Dec 31: ₹10,000
        - Income ≤ ₹5L: ₹1,000 max
        """
        if filing_date <= due_date:
            return Decimal("0")

        year_end = date(due_date.year, 12, 31)

        if total_income <= Decimal("500000"):
            return Decimal("1000")
        elif filing_date <= year_end:
            return Decimal("5000")
        else:
            return Decimal("10000")

    @staticmethod
    def _get_due_date(fy: FinancialYear, has_business_income: bool) -> date:
        """ITR due date based on taxpayer type."""
        if has_business_income:
            # October 31 of assessment year (non-transfer pricing)
            return date(fy.end_year, 10, 31)
        # July 31 of assessment year
        return date(fy.end_year, 7, 31)

    @staticmethod
    def _months_between(start: date, end: date) -> int:
        """Count months between two dates (part month = full month)."""
        months = (end.year - start.year) * 12 + (end.month - start.month)
        if end.day > start.day:
            months += 1
        elif end.day < start.day and months == 0:
            months = 1
        return max(0, months)
