"""ITR-1 (SAHAJ) JSON Builder — For salaried individuals with simple income.

ITR-1 eligibility:
  - Salary/pension income
  - One house property
  - Interest income from savings / fixed deposits
  - Agricultural income ≤ ₹5,000
  - Total income ≤ ₹50,00,000
  - NO capital gains, NO business income, NO foreign income/assets
  - NO crypto/VDA income
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from src.models.form16 import Form16Data
from src.models.ais import AISData
from src.models.tax import UnifiedTaxData

logger = logging.getLogger(__name__)

AY = "2026-27"
FY = "2025-26"


class ITR1Builder:
    """Builds ITR-1 (SAHAJ) JSON from unified tax data."""

    def build(self, data: UnifiedTaxData) -> dict:
        result = {
            "PartA_GeneralInfo": self._build_general_info(data),
            "ScheduleS": self._build_schedule_s(data),
            "ScheduleHP": self._build_schedule_hp(data),
            "ScheduleOS": self._build_schedule_os(data),
            "ScheduleVI-A": self._build_schedule_via(data),
            "PartB-TI": self._build_partb_ti(data),
            "PartB-TTI": self._build_partb_tti(data),
            "ScheduleTaxPaid": self._build_tax_paid(data),
        }
        return result

    # ── Part A: General Info ──────────────────────────────────────────

    def _build_general_info(self, data: UnifiedTaxData) -> dict:
        form16 = data.form16
        info: dict[str, Any] = {
            "AssessmentYear": AY,
            "ITRType": "1",
            "PAN": data.pan or (form16.part_a.employee_pan if form16 else ""),
            "Name": form16.part_a.employee_name if form16 else "",
            "DOB": self._format_date(data.dob) if data.dob else "",
            "AadhaarNo": "",
            "Status": "IND",
            "EmployerCategory": "GOV" if (form16 and "GOV" in (form16.part_a.employer_name or "").upper()) else "PVT",
            "ReturnFileDate": date.today().strftime("%d/%m/%Y"),
            "MobileNo": "",
            "Email": "",
            "ResidentialStatus": "RES",
            "AuditInfo": {},
        }
        info["FilingSection"] = {
            "FilingStatus": "F",
            "FilingDate": date.today().strftime("%d/%m/%Y"),
            "ReturnType": "O",
            "ReturnFileMode": "JSON",
            "DueDate": "N",
            "Section": "1",
        }
        info["ScheduleBank"] = self._build_bank(form16)
        return info

    def _build_bank(self, form16: Form16Data | None) -> dict:
        return {
            "BankAccounts": [
                {
                    "AccountNo": "",
                    "IFSC": "",
                    "AccountType": "Savings",
                    "UseForRefund": "Y",
                    "IsVerified": "Y",
                }
            ]
        }

    # ── Schedule S: Salary ────────────────────────────────────────────

    def _build_schedule_s(self, data: UnifiedTaxData) -> dict:
        form16 = data.form16
        if not form16:
            return {"TotalGrossSalary": "0"}

        return {
            "TotalGrossSalary": str(form16.part_b.total_gross_salary),
            "Allowances": str(form16.part_b.allowances),
            "Perquisites": str(form16.part_b.perquisites),
            "ProfitsInLieuOfSalary": str(form16.part_b.profits_in_lieu_of_salary),
            "DeductionsUS16": str(form16.part_b.deduction_16),
            "IncomeChargeableUnderHeadSalary": str(form16.part_b.income_chargeable_salary),
        }

    # ── Schedule HP: House Property (max 1 for ITR-1) ──────────────────

    def _build_schedule_hp(self, data: UnifiedTaxData) -> dict:
        answers = data.user_answers
        has_loan = answers.home_loan_interest or Decimal("0") > 0 if answers else False
        interest = str(answers.home_loan_interest) if answers and answers.home_loan_interest else "0"

        return {
            "SelfOccupied": {
                "AnnualLettableValue": "0",
                "InterestPayable": interest,
                "IncomeFromHouseProperty": str(-int(Decimal(interest)) if Decimal(interest) > 0 else 0),
                "UnrealizedRent": "0",
            },
            "ArrearsOfRent": "0",
            "TotalIncomeFromHP": str(-int(Decimal(interest)) if Decimal(interest) > 0 else 0),
        }

    # ── Schedule OS: Other Sources (Interest) ──────────────────────────

    def _build_schedule_os(self, data: UnifiedTaxData) -> dict:
        ais = data.ais
        savings_interest = str(ais.total_savings_interest) if ais else "0"
        other_interest = str(ais.total_tds_interest) if ais else "0"
        total = str(Decimal(savings_interest) + Decimal(other_interest))

        return {
            "SavingBankInterest": savings_interest,
            "FixedDepositInterest": other_interest,
            "GrossInterestIncome": total,
            "DeductionUS57": "0",
            "NetInterestIncome": total,
            "TotalOtherSources": total,
        }

    # ── Schedule VI-A: Deductions ─────────────────────────────────────

    def _build_schedule_via(self, data: UnifiedTaxData) -> dict:
        form16 = data.form16
        answers = data.user_answers

        sec80c = str(form16.part_b.chapter_vi_a.sec80c) if form16 else "0"
        sec80ccd2 = str(form16.part_b.chapter_vi_a.sec80ccd2) if form16 else "0"
        sec80tta = self._calc_80tta(data)
        sec80d = self._calc_80d(answers)

        via = {
            "Section80C": {
                "PPF": "0",
                "ELSS": "0",
                "LIC": "0",
                "EPF": sec80c,
                "TuitionFeeChildren": "0",
                "HomeLoanPrincipal": "0",
                "Others": "0",
                "Total80C": sec80c,
            },
            "Section80CCD1B": {
                "NPSOwnContribution": "0",
                "Amount": "0",
            },
            "Section80D": sec80d,
            "Section80G": {"Amount": "0"},
            "Section80TTA": {"Amount": sec80tta},
            "TotalChapterVI_A": self._calc_total_via(sec80c, sec80ccd2, sec80tta,
                                                       Decimal(sec80d.get("Total80D", "0"))),
        }
        return via

    def _calc_80tta(self, data: UnifiedTaxData) -> str:
        """80TTA: Up to ₹10,000 deduction on savings interest."""
        if data.ais:
            si = data.ais.total_savings_interest
            return str(min(si, Decimal("10000")))
        return "0"

    def _calc_80d(self, answers) -> dict:
        if not answers:
            return {"HealthPremiumSelf": "0", "HealthPremiumParents": "0", "Total80D": "0"}

        self_amt = str(answers.health_premium_self or Decimal("0"))
        parent_amt = str(answers.health_premium_parents or Decimal("0"))
        total = str(Decimal(self_amt) + Decimal(parent_amt))
        return {
            "HealthPremiumSelf": self_amt,
            "HealthPremiumParents": parent_amt,
            "ParentsSeniorCitizen": "Y" if answers.parents_senior_citizen else "N",
            "Total80D": total,
        }

    def _calc_total_via(self, sec80c: str, sec80ccd2, sec80tta, sec80d) -> str:
        total = Decimal(sec80c) + Decimal(str(sec80ccd2)) + Decimal(sec80tta) + sec80d
        return str(total)

    # ── Part B-TI: Total Income ───────────────────────────────────────

    def _build_partb_ti(self, data: UnifiedTaxData) -> dict:
        breakdown = self._get_breakdown(data)

        salary = Decimal(breakdown.get("income_salary", "0"))
        hp_income = Decimal(breakdown.get("income_hp", "0"))
        os_income = Decimal(breakdown.get("income_interest", "0"))

        gross = salary + hp_income + os_income
        deductions = Decimal(breakdown.get("total_deductions", "0"))
        taxable = max(Decimal("0"), gross - deductions)

        return {
            "Salary": str(salary),
            "HouseProperty": str(hp_income),
            "OtherSources": str(os_income),
            "GrossTotalIncome": str(gross),
            "TotalDeductions": str(deductions),
            "TotalIncome": str(taxable),
        }

    # ── Part B-TTI: Tax Computation ───────────────────────────────────

    def _build_partb_tti(self, data: UnifiedTaxData) -> dict:
        breakdown = self._get_breakdown(data)
        regime = data.recommended_regime
        is_new = regime and regime.value == "new"

        total_income = Decimal(breakdown.get("total_income", "0"))

        # Compute slab-wise tax
        tax, cess, rebate = self._compute_tax(total_income, is_new)
        total_tax = max(Decimal("0"), tax - rebate) + cess

        return {
            "TaxOnSlabIncome": str(tax),
            "Rebate87A": str(rebate),
            "Surcharge": "0",
            "HealthEducationCess": str(cess),
            "TotalTaxLiability": str(total_tax),
            "TotalTaxBeforeRebate": str(tax),
        }

    def _compute_tax(self, total_income: Decimal, is_new: bool) -> tuple[Decimal, Decimal, Decimal]:
        """Compute slab-wise tax using RuleEvaluator (M1: no hardcoded slabs)."""
        from src.engine.rules.config import rule_repository
        from src.engine.rules.evaluator import RuleEvaluator
        from src.models.financial_year import FinancialYear

        config = rule_repository.get(FinancialYear.from_string("FY2025-26"))
        regime = config.new_regime if is_new else config.old_regime
        evaluator = RuleEvaluator()

        slab_tax = evaluator.compute_slab_tax(total_income, regime.slabs)
        rebate = evaluator.compute_rebate(slab_tax, total_income, regime)
        tax_after_rebate = max(Decimal("0"), slab_tax - rebate)
        cess = evaluator.compute_cess(tax_after_rebate, Decimal("0"), config.cess_rate)

        return slab_tax, cess, rebate

    # ── Schedule Tax Paid (TDS) ───────────────────────────────────────

    def _build_tax_paid(self, data: UnifiedTaxData) -> dict:
        form16 = data.form16
        ais = data.ais

        salary_tds = str(form16.part_a.total_tds_deducted) if form16 else "0"
        other_tds = str(ais.total_non_salary_tds) if ais else "0"
        total = str(Decimal(salary_tds) + Decimal(other_tds))

        return {
            "ScheduleTDS1": {"TotalTDS": salary_tds},
            "ScheduleTDS2": {"TotalTDSOther": other_tds},
            "TotalTDS": total,
            "TotalTaxPaid": total,
        }

    # ── Helpers ───────────────────────────────────────────────────────

    def _get_breakdown(self, data: UnifiedTaxData) -> dict:
        """Get regime breakdown from regime result."""
        regime = data.recommended_regime
        if not regime:
            return {}
        return regime.new_breakdown if regime.value == "new" else regime.old_breakdown

    def _format_date(self, d: date | str | None) -> str:
        if d is None:
            return ""
        if isinstance(d, date):
            return d.strftime("%d/%m/%Y")
        return str(d)
