"""Base ITR Builder — Common interface for all ITR form types.

Every ITR builder (ITR-1 through ITR-7) inherits from this base.
Provides shared: PAN masking, date formatting, bank account building,
regime mapping, filing section, and generation metadata.

Traceability: AD-002 (No base class for builders — resolved)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from src.models.financial_year import FinancialYear
from src.models.form16 import Form16Data, Regime


@dataclass
class GenerationMetadata:
    """Metadata about the ITR generation process."""

    generated_at: str = ""
    generator_version: str = "0.1.0"
    financial_year: str = ""
    assessment_year: str = ""
    itr_type: str = ""
    pan_masked: str = ""
    regime: str = ""
    schedules_populated: list[str] = field(default_factory=list)
    validation_passed: bool = False
    validation_summary: str = ""


class BaseITRBuilder:
    """Abstract base for all ITR form builders.

    Subclasses implement `build(data) -> dict` to produce
    schema-compliant ITR JSON for their specific form type.
    """

    def __init__(self, fy: Optional[FinancialYear] = None) -> None:
        self._fy = fy or FinancialYear.from_string("FY2025-26")
        self._ay = self._fy.assessment_year

    # ── Shared utilities for all builders ──

    @staticmethod
    def _mask_pan(pan: str) -> str:
        """Mask PAN for metadata: ABCDE1234F → ABC**1234F."""
        if not pan or len(pan) < 10:
            return "***"
        return f"{pan[:3]}**{pan[5:]}"

    @staticmethod
    def _format_date(d: Optional[date]) -> str:
        """Format date as DD/MM/YYYY."""
        return d.strftime("%d/%m/%Y") if d else ""

    @staticmethod
    def _regime_code(regime: Optional[Regime]) -> str:
        """Map regime to ITD code: NEW → 'N', OLD → 'O'."""
        if regime is None:
            return "N"
        return "N" if regime == Regime.NEW else "O"

    def _build_general_info(
        self,
        pan: str,
        name: str,
        dob_str: str,
        itr_type: str,
        regime: Optional[Regime] = None,
        aadhaar: str = "",
        mobile: str = "",
        email: str = "",
    ) -> dict[str, Any]:
        """Build Part A — General Information shared by all ITR types."""
        return {
            "AssessmentYear": self._ay,
            "ITRType": itr_type,
            "PAN": pan,
            "Name": name,
            "DOB": dob_str,
            "AadhaarNo": aadhaar,
            "Status": "IND",
            "EmployerCategory": "PVT",
            "ReturnFileDate": date.today().strftime("%d/%m/%Y"),
            "MobileNo": mobile,
            "Email": email,
            "ResidentialStatus": "RES",
            "Regime": self._regime_code(regime),
            "FilingSection": {
                "FilingStatus": "F",
                "ReturnType": "O",
                "NoticeNo": "",
            },
            "AuditInfo": {},
        }

    def _build_bank_accounts(self) -> dict[str, Any]:
        """Build bank account section with refund flag."""
        return {
            "BankAccounts": [
                {
                    "BankName": "",
                    "AccountNo": "",
                    "IFSCCode": "",
                    "AccountType": "Savings",
                    "UseForRefund": "Y",
                }
            ]
        }

    def _generate_metadata(
        self,
        itr_type: str,
        pan: str,
        schedules: list[str],
        validation_passed: bool,
        validation_summary: str = "",
    ) -> GenerationMetadata:
        """Create generation metadata."""
        from datetime import datetime, timezone
        return GenerationMetadata(
            generated_at=datetime.now(timezone.utc).isoformat(),
            financial_year=self._fy.label,
            assessment_year=self._ay,
            itr_type=itr_type,
            pan_masked=self._mask_pan(pan),
            schedules_populated=schedules,
            validation_passed=validation_passed,
            validation_summary=validation_summary,
        )

    # ── Subclass contract ──

    def build(self, data: Any) -> dict:
        """Build ITR JSON. MUST be overridden by subclasses."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement build(data)"
        )
