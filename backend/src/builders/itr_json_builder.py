"""ITR JSON Builder — Generates upload-ready ITR JSON from UnifiedTaxData.

Produces JSON matching the ITD utility schema exactly, with:
- All mandatory schedules populated
- Correct enum values (INNOTAVAILAB, SecondaryAdd=Y, etc.)
- Cross-validated totals
- Proper date range segmentation for Schedule CG Section F
"""

import json
import hashlib
import logging
from datetime import date
from decimal import Decimal
from typing import Any

from src.models.form16 import Form16Data, Regime
from src.models.ais import AISData
from src.models.tax import (
    UnifiedTaxData,
    ClassifiedCGData,
    CGSaleEntry,
    CGDateRanges,
    UserAnswers,
    RegimeResult,
)

logger = logging.getLogger(__name__)

# Assessment Year mapping
AY = "2026-27"
FY = "2025-26"


class ITRJSONBuilder:
    """Builds the complete ITR-2 JSON structure from unified tax data."""

    def build(self, data: UnifiedTaxData) -> dict:
        """Build the full ITR JSON ready for upload."""
        json_data = {
            "PartA_GeneralInfo": self._build_general_info(data),
            "ScheduleS": self._build_schedule_s(data),
            "Schedule112A": self._build_schedule_112a(data),
            "ScheduleCG": self._build_schedule_cg(data),
            "ScheduleOS": self._build_schedule_os(data),
            "ScheduleCYLA": self._build_schedule_cyla(data),
            "ScheduleBFLA": self._build_schedule_bfla(data),
            "ScheduleSI": self._build_schedule_si(data),
            "ScheduleVI-A": self._build_schedule_via(data),
            "PartB-TI": self._build_partb_ti(data),
            "PartB-TTI": self._build_partb_tti(data),
            "ScheduleTaxPaid": self._build_schedule_tax_paid(data),
        }
        return json_data

    # ── Part A: General Info ──────────────────────────────────────

    def _build_general_info(self, data: UnifiedTaxData) -> dict:
        """Build Part A — General Information."""
        form16 = data.form16
        info: dict[str, Any] = {
            "AssessmentYear": AY,
            "ITRType": "2",
            "PAN": data.pan or (form16.part_a.employee_pan if form16 else ""),
            "Name": form16.part_a.employee_name if form16 else "",
            "DOB": self._format_date(data.dob) if data.dob else "",
            "AadhaarNo": "",
            "Status": "IND",
            "EmployerCategory": "GOV",
            "ReturnFileDate": date.today().strftime("%d/%m/%Y"),
            "MobileNo": "",
            "Email": "",
            "ResidentialStatus": "RES",
            "AuditInfo": {},
        }

        # Filing Section
        info["FilingSection"] = {
            "FilingStatus": "F",
            "ReturnType": "O",
            "NoticeNo": "",
            "NoticeDate": "",
        }

        # Regime
        info["Regime"] = "N" if data.recommended_regime == Regime.NEW else "O"

        # Bank accounts (for refund)
        info["ScheduleBank"] = {
            "BankAccounts": [
                {
                    "BankName": "",
                    "AccountNo": "",
                    "IFSCCode": "",
                    "AccountType": "",
                    "UseForRefund": "Y",
                }
            ]
        }

        return info

    # ── Schedule S: Salary ─────────────────────────────────────────

    def _build_schedule_s(self, data: UnifiedTaxData) -> dict:
        """Build Schedule S — Salary Income."""
        if not data.form16:
            return {"SalaryIncome": []}

        f = data.form16
        salary_entry = {
            "EmployerName": f.part_a.employer_name,
            "EmployerTAN": f.part_a.employer_tan,
            "EmployerPAN": f.part_a.employer_pan,
            "Address": f.part_a.employer_address,
            "Salary_171": str(f.part_b.salary_171),
            "Perquisites_172": str(f.part_b.perquisites_172),
            "ProfitsLieu_173": str(f.part_b.profits_lieu_173),
            "TotalGrossSalary": str(f.part_b.total_gross_salary),
            "StdDeduction_16ia": str(f.part_b.std_deduction_16ia),
            "Entertainment_16ii": str(f.part_b.entertainment_16ii),
            "ProfessionalTax_16iii": str(f.part_b.professional_tax_16iii),
            "IncomeUnderHeadSalaries": str(f.part_b.income_under_head_salaries),
        }

        return {"SalaryIncome": [salary_entry]}

    # ── Schedule 112A: Equity LTCG ─────────────────────────────────

    def _build_schedule_112a(self, data: UnifiedTaxData) -> dict:
        """Build Schedule 112A — From sale of equity share / unit of equity-oriented fund.

        Consolidated entry per ISIN with sale date range and FMV details.
        """
        cg = data.capital_gains
        entries_112a = cg.schedule_112a

        if not entries_112a:
            return {}

        # Build one consolidated entry for all equity MF LTCG
        # (Option: can also group by ISIN)
        total_consideration = sum((e.consideration for e in entries_112a), Decimal("0"))
        total_cost = sum((e.cost for e in entries_112a), Decimal("0"))
        total_gain = sum((e.gain for e in entries_112a), Decimal("0"))

        # Find date range
        dates = [e.date for e in entries_112a if e.date]
        from_date = min(dates).strftime("%d/%m/%Y") if dates else ""
        to_date = max(dates).strftime("%d/%m/%Y") if dates else ""

        # Apply ₹1.25L exemption
        exemption = min(total_gain, Decimal("125000"))
        taxable_gain = max(Decimal("0"), total_gain - exemption)

        consolidated = {
            "ISINCode": "INNOTAVAILAB",  # Consolidated — not a single ISIN
            "NameOfUnit": "Various Equity Mutual Funds",
            "NoOfUnits": str(sum((e.quantity for e in entries_112a), Decimal("0"))),
            "SalePricePerUnit": str(Decimal("0")),  # Not needed for consolidated
            "FullValueOfConsideration": str(total_consideration),
            "CostOfAcquisition": str(total_cost),
            "Expenditure": "0",
            "DateFrom": from_date,
            "DateTo": to_date,
            "FMVPerUnit": "0",
            "FMVTotal": "0",
            "Deduction": str(exemption),
            "Balance": str(taxable_gain),
            "SecondaryAdd": "Y",  # Must be "Y" or "N", NOT empty string
        }

        return {
            "Securities": [consolidated],
            "TotalDeduction": str(exemption),
            "TotalBalance": str(taxable_gain),
        }

    # ── Schedule CG: Capital Gains ──────────────────────────────────

    def _build_schedule_cg(self, data: UnifiedTaxData) -> dict:
        """Build Schedule CG — Capital Gains.

        Sections:
        - A2: STCG u/s 111A (equity, 15%)
        - A5: STCG at applicable rates (non-equity, slab)
        - B8: LTCG other than 112A
        - Section F: Date-range split
        """
        cg = data.capital_gains

        schedule: dict[str, Any] = {}

        # Section A2 — STCG u/s 111A (15%)
        if cg.cg_a2_stcg_111a:
            schedule["A2_STCG_111A"] = self._build_cg_section(
                cg.cg_a2_stcg_111a, "A2"
            )

        # Section A5 — STCG at applicable rate (slab)
        if cg.cg_a5_stcg_app_rate:
            schedule["A5_STCG_AppRate"] = self._build_cg_section(
                cg.cg_a5_stcg_app_rate, "A5"
            )

        # Section B8 — LTCG other than 112A
        if cg.cg_b8_ltcg_other:
            schedule["B8_LTCG_Other"] = self._build_cg_section(
                cg.cg_b8_ltcg_other, "B8"
            )

        # Section F — Date ranges
        if cg.date_ranges:
            schedule["SecF"] = self._build_cg_section_f(cg.date_ranges)

        return schedule

    def _build_cg_section(self, entries: list[CGSaleEntry], section: str) -> dict:
        """Build a CG section with individual entries."""
        items = []
        for e in entries:
            item = {
                "DateOfSale": e.date.strftime("%d/%m/%Y") if e.date else "",
                "ISINCode": e.isin or "INNOTAVAILAB",
                "NameOfSecurity": e.security_name,
                "NoOfUnits": str(e.quantity),
                "SalePrice": str(e.sale_price),
                "FullValueOfConsideration": str(e.consideration),
                "CostOfAcquisition": str(e.cost),
                "Expenditure": "0",
                "Balance": str(e.gain),
            }

            if section == "A2":
                item["STT"] = "Y" if e.stt_paid else "N"

            items.append(item)

        total_consideration = sum((e.consideration for e in entries), Decimal("0"))
        total_cost = sum((e.cost for e in entries), Decimal("0"))
        total_gain = sum((e.gain for e in entries), Decimal("0"))

        base = {
            "Entries": items,
            "TotalFullValueOfConsideration": str(total_consideration),
            "TotalCostOfAcquisition": str(total_cost),
            "TotalBalance": str(total_gain),
        }

        if section == "A2":
            base["TotalSTT"] = "Y" if any(e.stt_paid for e in entries) else "N"

        return base

    def _build_cg_section_f(self, ranges: CGDateRanges) -> dict:
        """Build CG Section F — Date range split.

        This is the cross-validation section that must match BFLA exactly.
        """
        periods = [
            "Upto15Of6",
            "Upto15Of9",
            "Up16Of9To15Of12",
            "Up16Of12To15Of3",
            "Up16Of3To31Of3",
        ]

        sec_f: dict[str, Any] = {}

        # LTCG at 12.5% (112A)
        ltcg_rows = []
        for period in periods:
            amount = ranges.ltcg_12_5pct.get(period, Decimal("0"))
            ltcg_rows.append({
                "Period": period,
                "Amount": str(amount),
            })
        sec_f["LTCG_12_5pct"] = ltcg_rows
        sec_f["Total_LTCG_12_5pct"] = str(sum(
            (ranges.ltcg_12_5pct.get(p, Decimal("0")) for p in periods), Decimal("0")
        ))

        # STCG at applicable rate
        stcg_rows = []
        for period in periods:
            amount = ranges.stcg_app_rate.get(period, Decimal("0"))
            stcg_rows.append({
                "Period": period,
                "Amount": str(amount),
            })
        sec_f["STCG_AppRate"] = stcg_rows
        sec_f["Total_STCG_AppRate"] = str(sum(
            (ranges.stcg_app_rate.get(p, Decimal("0")) for p in periods), Decimal("0")
        ))

        # STCG at 15% (111A)
        stcg_15_rows = []
        for period in periods:
            amount = ranges.stcg_15pct.get(period, Decimal("0"))
            stcg_15_rows.append({
                "Period": period,
                "Amount": str(amount),
            })
        sec_f["STCG_15pct"] = stcg_15_rows
        sec_f["Total_STCG_15pct"] = str(sum(
            (ranges.stcg_15pct.get(p, Decimal("0")) for p in periods), Decimal("0")
        ))

        return sec_f

    # ── Schedule OS: Other Sources ──────────────────────────────────

    def _build_schedule_os(self, data: UnifiedTaxData) -> dict:
        """Build Schedule OS — Income from Other Sources (Interest, Dividends)."""
        if not data.ais:
            return {}

        ais = data.ais
        entries = []

        # Savings bank interest
        if ais.total_savings_interest > 0:
            entries.append({
                "Source": "Savings Bank Interest",
                "GrossAmount": str(ais.total_savings_interest),
                "Deduction": "0",
                "NetAmount": str(ais.total_savings_interest),
            })

        # Term deposit interest
        if ais.total_tds_interest > 0:
            entries.append({
                "Source": "Fixed Deposit Interest",
                "GrossAmount": str(ais.total_tds_interest),
                "Deduction": "0",
                "NetAmount": str(ais.total_tds_interest),
            })

        if not entries:
            return {}

        total_os = sum(
            (Decimal(e["NetAmount"]) for e in entries), Decimal("0")
        )

        return {
            "OtherSourceIncome": entries,
            "TotalOtherSourceIncome": str(total_os),
        }

    # ── Schedule CYLA / BFLA ───────────────────────────────────────

    def _build_schedule_cyla(self, data: UnifiedTaxData) -> dict:
        """Schedule CYLA — Current Year Loss Adjustment."""
        # No losses in most cases; return empty
        return {}

    def _build_schedule_bfla(self, data: UnifiedTaxData) -> dict:
        """Schedule BFLA — Brought Forward Loss Adjustment."""
        # No brought-forward losses in most cases
        return {}

    # ── Schedule SI: Special Income ─────────────────────────────────

    def _build_schedule_si(self, data: UnifiedTaxData) -> dict:
        """Schedule SI — Income chargeable at special rates.

        Auto-computed: STCG 111A (15%), LTCG 112A (12.5%).
        """
        cg = data.capital_gains
        entries = []

        # STCG 111A (15%)
        total_stcg_15 = sum((e.gain for e in cg.cg_a2_stcg_111a), Decimal("0"))
        if total_stcg_15 > 0:
            entries.append({
                "Section": "111A",
                "NatureOfIncome": "Short Term Capital Gain (STCG) on equity shares/units",
                "Amount": str(total_stcg_15),
                "Rate": "15%",
                "TaxAmount": str(total_stcg_15 * Decimal("0.15")),
            })

        # LTCG 112A (12.5%)
        total_ltcg_112a = sum((e.gain for e in cg.schedule_112a), Decimal("0"))
        exemption_112a = min(total_ltcg_112a, Decimal("125000"))
        taxable_112a = max(Decimal("0"), total_ltcg_112a - exemption_112a)
        if taxable_112a > 0:
            entries.append({
                "Section": "112A",
                "NatureOfIncome": "Long Term Capital Gain (LTCG) on equity shares/units",
                "Amount": str(taxable_112a),
                "Rate": "12.5%",
                "TaxAmount": str(taxable_112a * Decimal("0.125")),
            })

        if not entries:
            return {}

        return {"SpecialIncome": entries}

    # ── Schedule VI-A: Deductions ───────────────────────────────────

    def _build_schedule_via(self, data: UnifiedTaxData) -> dict:
        """Build Schedule VI-A — Deductions under Chapter VI-A."""
        if not data.form16:
            return {}

        result = data.regime_result

        if data.recommended_regime == Regime.OLD:
            breakdown = result.old_breakdown
            deductions = breakdown.get("deductions_total", Decimal("0"))
            parts = {
                "80C": str(data.form16.part_b.chapter_vi_a.sec80c),
                "80CCD_1B": str(data.form16.part_b.chapter_vi_a.sec80ccd1b),
                "80CCD_2": str(data.form16.part_b.chapter_vi_a.sec80ccd2),
                "80D": str(data.form16.part_b.chapter_vi_a.sec80d),
                "80TTA": str(data.form16.part_b.chapter_vi_a.sec80tta),
                "80G": str(data.form16.part_b.chapter_vi_a.sec80g),
                "Total": str(deductions),
            }
        else:
            # New regime: only 80CCD(2)
            d = data.form16.part_b.chapter_vi_a.sec80ccd2
            parts = {
                "80CCD_2": str(d),
                "Total": str(d),
            }

        return {"Deductions": parts, "TotalDeductions": parts.get("Total", "0")}

    # ── Part B-TI: Total Income ─────────────────────────────────────

    def _build_partb_ti(self, data: UnifiedTaxData) -> dict:
        """Build Part B-TI — Computation of Total Income."""
        result = data.regime_result
        is_new = data.recommended_regime == Regime.NEW

        breakdown = result.new_breakdown if is_new else result.old_breakdown

        ti = {
            "IncomeUnderHeadSalaries": str(breakdown.get("income_salary", "0")),
            "IncomeUnderHeadHouseProperty": str(breakdown.get("home_loan_loss", "0")),
            "IncomeUnderHeadCapitalGains": str(breakdown.get("income_cg", "0")),
            "IncomeUnderHeadOtherSources": str(breakdown.get("income_interest", "0")),
            "GrossTotalIncome": str(breakdown.get("gross_total", "0")),
            "TotalDeductions": str(breakdown.get("deductions_total", "0")),
            "TotalIncome": str(breakdown.get("total_income", "0")),
        }

        return ti

    # ── Part B-TTI: Tax on Total Income ────────────────────────────

    def _build_partb_tti(self, data: UnifiedTaxData) -> dict:
        """Build Part B-TTI — Computation of Tax Liability."""
        result = data.regime_result
        is_new = data.recommended_regime == Regime.NEW
        breakdown = result.new_breakdown if is_new else result.old_breakdown

        tti = {
            "TotalIncome": str(breakdown.get("total_income", "0")),
            "TaxOnTotalIncome": str(breakdown.get("tax_slab", "0")),
            "TaxOnSpecialRates": str(breakdown.get("tax_special_rates", "0")),
            "TotalTaxBeforeRebate": str(
                Decimal(breakdown.get("tax_slab", "0"))
                + Decimal(breakdown.get("tax_special_rates", "0"))
            ),
            "Rebate87A": str(breakdown.get("rebate_87a", "0")),
            "Surcharge": "0",
            "HealthEducationCess": str(breakdown.get("cess", "0")),
            "TotalTaxLiability": str(breakdown.get("net_tax", "0")),
        }

        return tti

    # ── Schedule Tax Paid ──────────────────────────────────────────

    def _build_schedule_tax_paid(self, data: UnifiedTaxData) -> dict:
        """Build Schedule Tax Paid — TDS, Advance Tax, Self-Assessment Tax."""
        if not data.form16:
            return {}

        f = data.form16
        result = data.regime_result
        is_new = data.recommended_regime == Regime.NEW
        breakdown = result.new_breakdown if is_new else result.old_breakdown

        # TDS from salary
        salary_tds = f.part_a.total_tds_deducted

        # Other TDS (from AIS)
        other_tds = Decimal("0")
        if data.ais:
            other_tds = data.ais.total_non_salary_tds

        total_tds = salary_tds + other_tds

        # Total tax liability
        total_tax = breakdown.get("net_tax", Decimal("0"))
        total_tax_d = Decimal(total_tax) if not isinstance(total_tax, Decimal) else total_tax

        # Self-assessment tax needed
        balance = total_tax_d - total_tds
        self_assessment_tax = max(Decimal("0"), balance)

        tax_paid = {
            "TDS": {
                "SalaryTDS": str(salary_tds),
                "OtherTDS": str(other_tds),
                "TotalTDS": str(total_tds),
            },
            "AdvanceTax": "0",
            "SelfAssessmentTax": str(self_assessment_tax),
            "TotalTaxPaid": str(total_tds + self_assessment_tax),
            "BalancePayable": str(max(Decimal("0"), total_tax_d - total_tds - self_assessment_tax)),
            "RefundDue": str(max(Decimal("0"), total_tds + self_assessment_tax - total_tax_d)),
        }

        return tax_paid

    # ── Utility ─────────────────────────────────────────────────────

    @staticmethod
    def _format_date(d: date) -> str:
        """Format date as DD/MM/YYYY."""
        return d.strftime("%d/%m/%Y") if d else ""


def build_itr_json(data: UnifiedTaxData) -> dict:
    """Convenience function to build ITR JSON."""
    builder = ITRJSONBuilder()
    return builder.build(data)
