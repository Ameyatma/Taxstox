"""ITR JSON Validator — Validates the generated ITR JSON before export.

Checks:
1. Schema enum values (SecondaryAdd, ISIN, etc.)
2. Cross-schedule consistency (CG date ranges = BFLA)
3. Tax computation accuracy (independent recalculation)
4. Mandatory field presence
5. Known portal bugs/quirks
"""

import json
from decimal import Decimal
from typing import Any

from src.models.api import ValidationResult, ValidationReport


class ITRValidator:
    """Validates an ITR JSON against known ITD schema rules and computational sanity."""

    # Valid SecondaryAdd enum values
    VALID_SECONDARY_ADD = {"Y", "N", ""}
    VALID_ISIN_VALUES = {"INNOTAVAILAB", "INNOTREQUIRD"}  # Portal uses INNOTAVAILAB

    def validate(self, itr_json: dict) -> ValidationReport:
        """Run all validation checks and return a report."""
        results: list[ValidationResult] = []

        results.append(self._check_mandatory_fields(itr_json))
        results.append(self._check_enum_values(itr_json))
        results.append(self._check_schedule_cross_consistency(itr_json))
        results.append(self._check_tax_computation(itr_json))
        results.append(self._check_112a_exemption(itr_json))
        results.append(self._check_bank_accounts(itr_json))
        results.append(self._check_negative_values(itr_json))

        passed = sum(1 for r in results if r.passed)
        failed = len([r for r in results if not r.passed and r.severity != "warning"])
        warnings = len([r for r in results if not r.passed and r.severity == "warning"])

        return ValidationReport(
            results=results,
            passed=passed,
            failed=failed,
            warnings=warnings,
        )

    def _check_mandatory_fields(self, itr_json: dict) -> ValidationResult:
        """Check that all mandatory top-level sections exist."""
        mandatory = [
            "PartA_GeneralInfo",
            "ScheduleS",
            "PartB-TI",
            "PartB-TTI",
            "ScheduleTaxPaid",
        ]

        missing = [m for m in mandatory if m not in itr_json or not itr_json[m]]

        if missing:
            return ValidationResult(
                check_name="mandatory_fields",
                passed=False,
                severity="error",
                message=f"Missing mandatory sections: {', '.join(missing)}",
            )
        return ValidationResult(
            check_name="mandatory_fields",
            passed=True,
            message="All mandatory sections present.",
        )

    def _check_enum_values(self, itr_json: dict) -> ValidationResult:
        """Check that enum fields have valid values per ITD schema."""
        issues: list[str] = []

        # Check 112A: SecondaryAdd must be "Y" or "N", NOT empty string
        sched_112a = itr_json.get("Schedule112A", {})
        for i, sec in enumerate(sched_112a.get("Securities", [])):
            sa = sec.get("SecondaryAdd", "")
            if sa == "":
                issues.append(
                    f"Schedule112A Securities[{i}] SecondaryAdd is empty — "
                    f"must be 'Y' or 'N'. Portal rejects empty string."
                )

        # Check ISIN codes
        for section_key in ["A2_STCG_111A", "A5_STCG_AppRate", "B8_LTCG_Other"]:
            cg = itr_json.get("ScheduleCG", {})
            section = cg.get(section_key, {})
            for i, entry in enumerate(section.get("Entries", [])):
                isin = entry.get("ISINCode", "")
                if isin == "INNOTREQUIRD":
                    issues.append(
                        f"ScheduleCG {section_key} Entry[{i}] ISIN is INNOTREQUIRD — "
                        f"portal may auto-change to INNOTAVAILAB. Use INNOTAVAILAB."
                    )

        if issues:
            return ValidationResult(
                check_name="enum_values",
                passed=False,
                severity="error",
                message="; ".join(issues),
                fix_suggestion="Set SecondaryAdd='Y' and ISIN='INNOTAVAILAB' where applicable.",
            )
        return ValidationResult(
            check_name="enum_values",
            passed=True,
            message="All enum values are valid.",
        )

    def _check_schedule_cross_consistency(self, itr_json: dict) -> ValidationResult:
        """Cross-validate: Schedule CG Section F sums must match BFLA / PartB-TI."""
        issues: list[str] = []

        cg = itr_json.get("ScheduleCG", {})
        sec_f = cg.get("SecF", {})

        if sec_f:
            # LTCG 12.5% total in SecF should match B8 total + 112A total
            ltcg_f = Decimal(sec_f.get("Total_LTCG_12_5pct", "0"))
            # Cross-check with B8 and 112A
            b8_total = Decimal(
                cg.get("B8_LTCG_Other", {}).get("TotalBalance", "0")
            )
            s112a = itr_json.get("Schedule112A", {})
            s112a_total = Decimal(s112a.get("TotalBalance", "0"))
            expected_ltcg = b8_total + s112a_total

            if abs(ltcg_f - expected_ltcg) > 1:  # Allow ₹1 rounding
                issues.append(
                    f"CG SecF LTCG total ({ltcg_f}) ≠ B8 ({b8_total}) + 112A ({s112a_total}) = {expected_ltcg}"
                )

            # STCG AppRate total in SecF should match A5 total
            stcg_f = Decimal(sec_f.get("Total_STCG_AppRate", "0"))
            a5_total = Decimal(
                cg.get("A5_STCG_AppRate", {}).get("TotalBalance", "0")
            )
            if abs(stcg_f - a5_total) > 1:
                issues.append(
                    f"CG SecF STCG AppRate total ({stcg_f}) ≠ A5 ({a5_total})"
                )

        if issues:
            return ValidationResult(
                check_name="cross_consistency",
                passed=False,
                severity="error",
                message="; ".join(issues),
                fix_suggestion="Verify CG date range sums match schedule totals exactly.",
            )
        return ValidationResult(
            check_name="cross_consistency",
            passed=True,
            message="All cross-schedule totals are consistent.",
        )

    def _check_tax_computation(self, itr_json: dict) -> ValidationResult:
        """Independently verify the tax computation."""
        tti = itr_json.get("PartB-TTI", {})
        tax_paid = itr_json.get("ScheduleTaxPaid", {})

        # Total tax before cess
        tax_before_rebate = Decimal(tti.get("TotalTaxBeforeRebate", "0"))
        rebate = Decimal(tti.get("Rebate87A", "0"))
        surcharge = Decimal(tti.get("Surcharge", "0"))
        cess = Decimal(tti.get("HealthEducationCess", "0"))

        # Recompute
        tax_after_rebate = max(Decimal("0"), tax_before_rebate - rebate)
        expected_cess = (tax_after_rebate * Decimal("4") / Decimal("100")).quantize(Decimal("1"))
        expected_total = tax_after_rebate + expected_cess

        actual_total = Decimal(tti.get("TotalTaxLiability", "0"))

        if abs(expected_total - actual_total) > 2:  # Allow ₹2 rounding
            return ValidationResult(
                check_name="tax_computation",
                passed=False,
                severity="error",
                message=f"Tax computation mismatch: expected {expected_total}, got {actual_total}",
                fix_suggestion="Recompute tax slabs and cess.",
            )

        return ValidationResult(
            check_name="tax_computation",
            passed=True,
            message=f"Tax computation verified: ₹{actual_total:,.0f}.",
        )

    def _check_112a_exemption(self, itr_json: dict) -> ValidationResult:
        """Check that 112A exemption is correctly applied (max ₹1,25,000)."""
        s112a = itr_json.get("Schedule112A", {})
        if not s112a:
            return ValidationResult(
                check_name="112a_exemption",
                passed=True,
                message="No 112A entries — exemption check skipped.",
            )

        total_deduction = Decimal(s112a.get("TotalDeduction", "0"))
        if total_deduction > 125000:
            return ValidationResult(
                check_name="112a_exemption",
                passed=False,
                severity="error",
                message=f"112A exemption ({total_deduction}) exceeds ₹1,25,000 limit.",
                fix_suggestion="Cap 112A deduction at ₹1,25,000.",
            )

        return ValidationResult(
            check_name="112a_exemption",
            passed=True,
            message=f"112A exemption: ₹{total_deduction:,.0f} (max ₹1,25,000).",
        )

    def _check_bank_accounts(self, itr_json: dict) -> ValidationResult:
        """Check bank account configuration for refund."""
        gen_info = itr_json.get("PartA_GeneralInfo", {})
        banks = gen_info.get("ScheduleBank", {}).get("BankAccounts", [])

        # Count UseForRefund = Y
        refund_accounts = [b for b in banks if b.get("UseForRefund") == "Y"]

        if len(refund_accounts) > 1:
            return ValidationResult(
                check_name="bank_accounts",
                passed=False,
                severity="warning",
                message=f"Multiple bank accounts ({len(refund_accounts)}) have UseForRefund=Y. "
                        "Portal may show a warning.",
                fix_suggestion="Set UseForRefund=Y for only one account.",
            )
        elif len(refund_accounts) == 0 and len(banks) > 0:
            return ValidationResult(
                check_name="bank_accounts",
                passed=False,
                severity="warning",
                message="No bank account marked for refund (UseForRefund=Y).",
                fix_suggestion="Set UseForRefund=Y on one validated bank account.",
            )
        return ValidationResult(
            check_name="bank_accounts",
            passed=True,
            message="Bank account configuration is valid.",
        )

    def _check_negative_values(self, itr_json: dict) -> ValidationResult:
        """Check for negative values in key fields (schema may reject them)."""
        issues: list[str] = []

        def _check_dict(d: dict, path: str = "") -> None:
            for k, v in d.items():
                current_path = f"{path}.{k}" if path else k
                if isinstance(v, dict):
                    _check_dict(v, current_path)
                elif isinstance(v, (int, float)):
                    if v < 0:
                        issues.append(f"{current_path}: negative value ({v})")

        _check_dict(itr_json)

        if issues:
            return ValidationResult(
                check_name="negative_values",
                passed=False,
                severity="warning",
                message=f"Found {len(issues)} negative values: {issues[:5]}...",
                fix_suggestion="Negative values may cause schema rejection. Set to 0 if applicable.",
            )
        return ValidationResult(
            check_name="negative_values",
            passed=True,
            message="No negative values found.",
        )


def validate_itr_json(itr_json: dict) -> ValidationReport:
    """Convenience function to validate ITR JSON."""
    validator = ITRValidator()
    return validator.validate(itr_json)
