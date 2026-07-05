"""Form 26AS PDF parser — TRACES tax credit statement.

Extracts TDS, TCS, advance tax, and refund details for reconciliation
with Form 16 and AIS data.

Traceability: C3.7 (Form 26AS Parser — High gap, 0%→60%)
"""

from __future__ import annotations

import io
import logging
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pdfplumber

from src.parsers.confidence import (
    ConfidenceLevel,
    ScoredField,
    DocumentExtractionReport,
    high,
    medium,
    low,
    missing,
)

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────────────

class Form26ASTDSEntry:
    """A single TDS entry from Form 26AS."""
    def __init__(self) -> None:
        self.deductor_name: str = ""
        self.deductor_tan: str = ""
        self.section: str = ""            # 192, 194A, 194I, etc.
        self.amount_paid: Decimal = Decimal("0")
        self.tds_deducted: Decimal = Decimal("0")
        self.tds_deposited: Decimal = Decimal("0")
        self.quarter: str = ""
        self.date_of_payment: Optional[date] = None

    def to_dict(self) -> dict:
        return {
            "deductor_name": self.deductor_name,
            "deductor_tan": self.deductor_tan,
            "section": self.section,
            "amount_paid": str(self.amount_paid),
            "tds_deducted": str(self.tds_deducted),
            "tds_deposited": str(self.tds_deposited),
            "quarter": self.quarter,
        }


class Form26ASData:
    """Complete Form 26AS data."""
    def __init__(self) -> None:
        self.pan: str = ""
        self.assessment_year: str = ""
        self.tds_entries: list[Form26ASTDSEntry] = []
        self.total_tds: Decimal = Decimal("0")
        self.advance_tax: Decimal = Decimal("0")
        self.self_assessment_tax: Decimal = Decimal("0")
        self.refund_received: Decimal = Decimal("0")

    @property
    def total_tax_credit(self) -> Decimal:
        return self.total_tds + self.advance_tax + self.self_assessment_tax


# ── Parser ───────────────────────────────────────────────────────────

class Form26ASParser:
    """Parses Form 26AS PDF into structured data with confidence scoring."""

    TAN_PATTERN = re.compile(r"[A-Z]{4}[0-9]{5}[A-Z]")
    AMOUNT_PATTERN = re.compile(r"[\d,]+\.\d{2}")
    DATE_PATTERN = re.compile(r"\d{2}/\d{2}/\d{4}")

    def parse(self, pdf_path: Path, password: Optional[str] = None) -> tuple[Form26ASData, DocumentExtractionReport]:
        """Parse Form 26AS PDF. Returns data + extraction report."""
        data = Form26ASData()
        report = DocumentExtractionReport(document_type="form26as", total_fields=8)

        try:
            text = self._extract_text(pdf_path, password)
        except Exception as e:
            logger.error(f"Form 26AS extraction failed: {e}")
            return data, report

        # Extract PAN
        pan_match = re.search(r"PAN\s*[:.]?\s*([A-Z]{5}[0-9]{4}[A-Z])", text)
        if pan_match:
            data.pan = pan_match.group(1)
            report.fields_high += 1

        # Assessment Year
        ay_match = re.search(r"Assessment\s*Year\s*[:.]?\s*(\d{4}-\d{2,4})", text)
        if ay_match:
            data.assessment_year = ay_match.group(1)
            report.fields_high += 1

        # Extract TDS entries by deductor
        data.tds_entries = self._extract_tds_entries(text)
        if data.tds_entries:
            report.fields_high += 1

        # Total TDS
        data.total_tds = sum(e.tds_deducted for e in data.tds_entries)
        if data.total_tds > 0:
            report.fields_high += 1

        # Advance tax
        data.advance_tax = self._extract_advance_tax(text)
        if data.advance_tax > 0:
            report.fields_medium += 1

        # Self-assessment tax
        data.self_assessment_tax = self._extract_self_assessment_tax(text)
        if data.self_assessment_tax > 0:
            report.fields_medium += 1

        # Refund
        data.refund_received = self._extract_refund(text)
        if data.refund_received > 0:
            report.fields_medium += 1

        logger.info(
            "Form 26AS parsed",
            extra={
                "pan": data.pan[:3] + "**" if data.pan else "N/A",
                "tds_entries": len(data.tds_entries),
                "total_tds": str(data.total_tds),
            },
        )

        return data, report

    def _extract_text(self, pdf_path: Path, password: Optional[str] = None) -> str:
        """Extract text from PDF, optionally decrypting."""
        try:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            return self._read_pdf(pdf_bytes)
        except Exception:
            if password:
                import pikepdf
                pdf = pikepdf.open(str(pdf_path), password=password)
                buf = io.BytesIO()
                pdf.save(buf)
                pdf.close()
                buf.seek(0)
                return self._read_pdf(buf.read())
            raise

    @staticmethod
    def _read_pdf(pdf_bytes: bytes) -> str:
        parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    parts.append(page_text)
        return "\n".join(parts)

    def _extract_tds_entries(self, text: str) -> list[Form26ASTDSEntry]:
        """Extract TDS entries by deductor from Form 26AS text."""
        entries: list[Form26ASTDSEntry] = []

        # Find deductor TANs
        tans = self.TAN_PATTERN.findall(text)
        seen_tans: set[str] = set()

        for tan in tans:
            if tan in seen_tans:
                continue
            seen_tans.add(tan)

            # Try to find associated name and TDS amounts near the TAN
            entry = Form26ASTDSEntry()
            entry.deductor_tan = tan

            # Search for amounts near TAN
            tan_pos = text.find(tan)
            if tan_pos < 0:
                continue

            context = text[tan_pos:tan_pos + 500]

            # Deductor name — text after TAN
            name_match = re.search(
                r"(?:Name of the Deductor|Name)\s*[:.]?\s*(.+?)(?:\n|$)",
                context, re.IGNORECASE,
            )
            if name_match:
                entry.deductor_name = name_match.group(1).strip()[:100]

            # Section
            section_match = re.search(r"Section\s*[:.]?\s*(\d+[A-Z]*)", context, re.IGNORECASE)
            if section_match:
                entry.section = section_match.group(1)

            # TDS amount
            amounts = self.AMOUNT_PATTERN.findall(context)
            if len(amounts) >= 2:
                entry.amount_paid = self._to_decimal(amounts[0])
                entry.tds_deducted = self._to_decimal(amounts[1])
                if len(amounts) >= 3:
                    entry.tds_deposited = self._to_decimal(amounts[2])
                else:
                    entry.tds_deposited = entry.tds_deducted

            if entry.tds_deducted > 0:
                entries.append(entry)

        return entries

    def _extract_advance_tax(self, text: str) -> Decimal:
        """Extract advance tax payments."""
        match = re.search(
            r"Advance\s*Tax\s*[:.]?\s*([\d,]+\.\d{2})",
            text, re.IGNORECASE,
        )
        if match:
            return self._to_decimal(match.group(1))
        return Decimal("0")

    def _extract_self_assessment_tax(self, text: str) -> Decimal:
        """Extract self-assessment tax payments."""
        match = re.search(
            r"Self[\s-]*Assessment\s*Tax\s*[:.]?\s*([\d,]+\.\d{2})",
            text, re.IGNORECASE,
        )
        if match:
            return self._to_decimal(match.group(1))
        return Decimal("0")

    def _extract_refund(self, text: str) -> Decimal:
        """Extract refund received."""
        match = re.search(
            r"Refund\s*[:.]?\s*([\d,]+\.\d{2})",
            text, re.IGNORECASE,
        )
        if match:
            return self._to_decimal(match.group(1))
        return Decimal("0")

    @staticmethod
    def _to_decimal(value_str: str) -> Decimal:
        try:
            return Decimal(value_str.replace(",", "").strip())
        except Exception:
            return Decimal("0")


def parse_form26as(pdf_path: Path, password: Optional[str] = None) -> tuple[Form26ASData, DocumentExtractionReport]:
    """Convenience function to parse Form 26AS PDF."""
    parser = Form26ASParser()
    return parser.parse(pdf_path, password)
