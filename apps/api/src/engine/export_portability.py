"""Export & Portability Engine — ITR JSON download, PDF summary, data export.

Enables taxpayers to export their data in multiple formats.
Supports DPDP Act data portability requirements.

Traceability: C14.4 (Export & Portability — 30%→60%, P6)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from uuid import UUID


class ExportFormat(str, Enum):
    ITR_JSON = "itr_json"          # Schema-compliant ITD JSON
    PDF_SUMMARY = "pdf_summary"    # Tax computation summary
    CSV = "csv"                    # Raw data export
    DATA_PORTABILITY = "data_portability"  # DPDP Act — all user data


@dataclass
class ExportResult:
    """Result of an export operation."""

    format: ExportFormat
    filename: str
    content: str = ""              # For text-based formats
    content_type: str = "application/json"
    success: bool = True
    error_message: str = ""


class ExportEngine:
    """Handles data export and portability.

    Engine. Generates downloadable files in multiple formats.
    Supports DPDP Act data portability (user can take their data elsewhere).
    """

    @staticmethod
    def export_itr_json(itr_data: dict, filename: str = "") -> ExportResult:
        """Export the ITR JSON for ITD portal upload."""
        import json
        content = json.dumps(itr_data, indent=2)
        return ExportResult(
            format=ExportFormat.ITR_JSON,
            filename=filename or "itr_return.json",
            content=content,
            content_type="application/json",
        )

    @staticmethod
    def export_csv_summary(breakdown: dict, filename: str = "") -> ExportResult:
        """Export tax computation summary as CSV."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Field", "Value"])
        rows = [
            ("Financial Year", breakdown.get("financial_year", "")),
            ("Regime", breakdown.get("recommended_regime", "")),
            ("Gross Total Income", breakdown.get("gross_total_income", "0")),
            ("Total Deductions", breakdown.get("deductions", "0")),
            ("Total Income", breakdown.get("total_income", "0")),
            ("Tax Before Rebate", breakdown.get("tax_before_rebate", "0")),
            ("Rebate 87A", breakdown.get("rebate_87a", "0")),
            ("Surcharge", breakdown.get("surcharge", "0")),
            ("Health & Education Cess", breakdown.get("cess", "0")),
            ("Final Tax", breakdown.get("final_tax", "0")),
            ("TDS Credited", breakdown.get("tds_credited", "0")),
            ("Net Tax Payable", breakdown.get("net_tax_payable", "0")),
            ("Refund Due", breakdown.get("refund_due", "0")),
        ]
        for field, value in rows:
            writer.writerow([field, value])

        return ExportResult(
            format=ExportFormat.CSV,
            filename=filename or "tax_summary.csv",
            content=output.getvalue(),
            content_type="text/csv",
        )

    @staticmethod
    def export_data_portability(
        user_id: UUID, pan: str, name: str,
        filings: list[dict], profile: dict | None = None,
    ) -> ExportResult:
        """Export all user data for DPDP Act data portability.

        Generates a complete JSON export of all user data for
        transfer to another platform or personal archive.
        """
        import json
        from datetime import datetime, timezone

        data = {
            "export_type": "data_portability",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "user_id": str(user_id),
            "pan_masked": f"{pan[:3]}**{pan[5:]}",
            "name": name,
            "profile": profile or {},
            "filings": filings,
            "notes": (
                "This export contains all your TaxStox data per the DPDP Act 2023 "
                "right to data portability. You may provide this to any other "
                "tax platform or CA for continued service."
            ),
        }
        content = json.dumps(data, indent=2)
        return ExportResult(
            format=ExportFormat.DATA_PORTABILITY,
            filename=f"taxstox_data_export_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json",
            content=content,
            content_type="application/json",
        )

    @staticmethod
    def generate_pdf_summary_text(breakdown: dict) -> str:
        """Generate a human-readable PDF-ready text summary.

        Production: Render this text through a PDF generation library.
        Current: Returns formatted text ready for PDF conversion.
        """
        lines = [
            "=" * 60,
            "TAX COMPUTATION SUMMARY",
            "=" * 60,
            "",
            f"Financial Year: {breakdown.get('financial_year', 'N/A')}",
            f"Regime: {breakdown.get('recommended_regime', 'N/A').title()}",
            f"Savings vs Other Regime: ₹{breakdown.get('savings', '0')}",
            "",
            "-" * 60,
            "INCOME",
            "-" * 60,
            f"  Gross Total Income:    ₹{int(Decimal(str(breakdown.get('gross_total_income', '0')))):>12,}",
            f"  Total Deductions:      ₹{int(Decimal(str(breakdown.get('deductions', '0')))):>12,}",
            f"  Total Income:          ₹{int(Decimal(str(breakdown.get('total_income', '0')))):>12,}",
            "",
            "-" * 60,
            "TAX COMPUTATION",
            "-" * 60,
            f"  Tax Before Rebate:     ₹{int(Decimal(str(breakdown.get('tax_before_rebate', '0')))):>12,}",
            f"  Less: Rebate u/s 87A:  ₹{int(Decimal(str(breakdown.get('rebate_87a', '0')))):>12,}",
            f"  Add: Surcharge:        ₹{int(Decimal(str(breakdown.get('surcharge', '0')))):>12,}",
            f"  Add: HEC @ 4%:         ₹{int(Decimal(str(breakdown.get('cess', '0')))):>12,}",
            f"  FINAL TAX:             ₹{int(Decimal(str(breakdown.get('final_tax', '0')))):>12,}",
            "",
            "-" * 60,
            "TAX CREDITS",
            "-" * 60,
            f"  TDS Credited:          ₹{int(Decimal(str(breakdown.get('tds_credited', '0')))):>12,}",
            f"  Net Payable / Refund:   ₹{int(Decimal(str(breakdown.get('net_tax_payable', '0')))):>12,}",
            "",
            "=" * 60,
            "Generated by TaxStox — AI-Powered Tax Intelligence",
            "=" * 60,
        ]
        return "\n".join(lines)
