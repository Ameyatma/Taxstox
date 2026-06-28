"""Form 16 PDF parser — decrypt with pikepdf, extract with pdfplumber."""

import re
import io
import logging
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pdfplumber
import pikepdf

from src.models.form16 import (
    Form16Data,
    Form16PartA,
    Form16PartB,
    Form16Annexure,
    SalaryComponent,
    QuarterlyTDS,
    Section10Exemptions,
    ChapterVIADeductions,
    TaxComputation,
)

logger = logging.getLogger(__name__)


class Form16Parser:
    """Parses a Form 16 PDF into structured Form16Data."""

    # Known patterns for salary components
    COMPONENT_PATTERNS = {
        "basic": re.compile(r"Basic\s*(?:Salary|Pay|Wages)?", re.IGNORECASE),
        "hra": re.compile(r"House\s*Rent\s*Allowance|H\.?R\.?A\.?", re.IGNORECASE),
        "special_allowance": re.compile(r"Special\s*Allowance", re.IGNORECASE),
        "lta": re.compile(r"Leave\s*Travel|L\.?T\.?A\.?", re.IGNORECASE),
        "lunch_coupons": re.compile(r"Lunch\s*Coupon|Food\s*Coupon|Sodexo", re.IGNORECASE),
        "broadband_reimbursement": re.compile(r"Broadband|Internet\s*Reimb", re.IGNORECASE),
        "special_award": re.compile(r"Special\s*Award", re.IGNORECASE),
        "nps_employer": re.compile(r"NPS\s*Employer|Employer.*NPS|80CCD\(2\)", re.IGNORECASE),
        "dbip_bonus": re.compile(r"DBIP|Bonus|Incentive", re.IGNORECASE),
    }

    @staticmethod
    def decrypt_pdf(pdf_path: Path, password: str) -> bytes:
        """Decrypt a password-protected PDF and return decrypted bytes."""
        try:
            pdf = pikepdf.open(str(pdf_path), password=password)
            buf = io.BytesIO()
            pdf.save(buf)
            pdf.close()
            buf.seek(0)
            return buf.read()
        except pikepdf.PasswordError:
            raise ValueError(f"Incorrect password for {pdf_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to decrypt {pdf_path}: {e}")

    @staticmethod
    def extract_text(pdf_bytes: bytes) -> str:
        """Extract all text from a PDF (decrypted bytes or path)."""
        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)

    def parse(self, pdf_path: Path, password: Optional[str] = None) -> Form16Data:
        """Parse a Form 16 PDF, optionally decrypting with password."""
        try:
            # Try opening directly first
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            text = self.extract_text(pdf_bytes)
        except Exception:
            if not password:
                raise ValueError("PDF is encrypted. Provide a password.")
            pdf_bytes = self.decrypt_pdf(pdf_path, password)
            text = self.extract_text(pdf_bytes)

        return self._parse_text(text)

    def _parse_text(self, text: str) -> Form16Data:
        """Parse extracted Form 16 text into structured data."""
        part_a = self._extract_part_a(text)
        part_b = self._extract_part_b(text)
        annexure = self._extract_annexure(text)
        return Form16Data(part_a=part_a, part_b=part_b, annexure=annexure)

    def _extract_part_a(self, text: str) -> Form16PartA:
        """Extract Part A — Employer & Employee details, TDS."""
        data: dict = {}

        # PAN — match various formats:
        # "PAN of Employee:CFFPM4503N" / "Employee PAN / Aadhaar Number CFFPM4503N"
        pan_match = re.search(
            r"(?:Employee\s*)?PAN.*?([A-Z]{5}[0-9]{4}[A-Z])",
            text, re.IGNORECASE,
        )
        if pan_match:
            data["employee_pan"] = pan_match.group(1)

        # TAN — "TAN of Employer:BLRA04654G" / "TAN of the Deductor BLRA04654G"
        tan_match = re.search(
            r"TAN.*?([A-Z]{4}[0-9]{5}[A-Z])",
            text,
        )
        if tan_match:
            data["employer_tan"] = tan_match.group(1)

        # Employer PAN — "PAN of the Deductor AAECA2635C"
        emp_pan_match = re.search(
            r"(?:Deductor|Employer).*?PAN.*?([A-Z]{5}[0-9]{4}[A-Z])",
            text, re.IGNORECASE,
        )
        if emp_pan_match:
            data["employer_pan"] = emp_pan_match.group(1)

        # Alternatively, line 38 format: "AAECA2635C BLRA04654G CFFPM4503N"
        if not data.get("employer_pan") or not data.get("employer_tan"):
            # Three PAN-format strings on one line = Employer PAN + TAN + Employee PAN
            three_ids = re.findall(r"([A-Z]{5}[0-9]{4}[A-Z])", text)
            if len(three_ids) >= 2:
                # First is employer PAN, second is TAN (no, TAN is different format)
                # Actually TAN format is [A-Z]{4}[0-9]{5}[A-Z]
                pass

        # TAN can also be found directly
        if not data.get("employer_tan"):
            tan_direct = re.search(r"([A-Z]{4}[0-9]{5}[A-Z])", text)
            if tan_direct:
                data["employer_tan"] = tan_direct.group(1)

        # Employer name — first meaningful line of the Form 16
        lines = text.strip().split("\n")
        for line in lines[:3]:
            line = line.strip()
            if line and len(line) > 5 and "APPLIED" in line.upper():
                data["employer_name"] = line
                break

        # Employee name
        emp_name_match = re.search(
            r"Employee\s*Name\s*(.+?)(?:\n|PAN|Aadhaar)",
            text, re.IGNORECASE,
        )
        if emp_name_match:
            data["employee_name"] = emp_name_match.group(1).strip()

        # Certificate number
        cert_match = re.search(
            r"Certificate\s*(?:No|Number)\s*[:.]?\s*(\w+)",
            text, re.IGNORECASE,
        )
        if cert_match:
            data["certificate_no"] = cert_match.group(1)

        # Assessment Year
        ay_match = re.search(r"Assessment\s*Year\s*[:.]?\s*(\d{4}-\d{2,4})", text)
        if ay_match:
            data["assessment_year"] = ay_match.group(1)

        # TDS totals — format: "Total (Rs.) 1871602.00 155738.00 155738.00"
        total_line_match = re.search(
            r"Total\s*\(Rs\.\)\s*([\d,]+\.\d{2})\s*([\d,]+\.\d{2})\s*([\d,]+\.\d{2})",
            text,
        )
        if total_line_match:
            data["total_amount_paid"] = self._to_decimal(total_line_match.group(1))
            data["total_tds_deducted"] = self._to_decimal(total_line_match.group(2))
            data["total_tds_deposited"] = self._to_decimal(total_line_match.group(3))
        else:
            # Fallback: look for Verification line
            tds_verify = re.search(
                r"certify\s*that\s*a\s*sum\s*of\s*Rs\.\s*([\d,]+\.\d{2})",
                text, re.IGNORECASE,
            )
            if tds_verify:
                data["total_tds_deducted"] = self._to_decimal(tds_verify.group(1))
                data["total_tds_deposited"] = self._to_decimal(tds_verify.group(1))

        data["quarterly_tds"] = self._extract_quarterly_tds(text)
        return Form16PartA(**{k: v for k, v in data.items() if k in Form16PartA.model_fields})

    def _extract_quarterly_tds(self, text: str) -> list[QuarterlyTDS]:
        """Extract quarterly TDS breakdown.

        Format: Q1 QWBOIUDA 393000.00 25682.00 25682.00
        """
        quarters = []
        q_pattern = re.compile(
            r"(Q[1-4])\s+(\w+)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})",
        )
        for match in q_pattern.finditer(text):
            quarters.append(QuarterlyTDS(
                quarter=match.group(1),
                receipt_number=match.group(2) or "",
                amount_paid=self._to_decimal(match.group(3)),
                tds_deducted=self._to_decimal(match.group(4)),
                tds_deposited=self._to_decimal(match.group(5)),
            ))
        return quarters

    def _extract_part_b(self, text: str) -> Form16PartB:
        """Extract Part B — Salary detail & tax computation."""
        data: dict = {}

        # Opting out of 115BAC?  Format: "Whether opting out of taxation u/s 115BAC(1A)? No"
        opt_out_match = re.search(
            r"opting\s*out.*?115BAC.*?\?\s*(Yes|No)",
            text, re.IGNORECASE,
        )
        if opt_out_match:
            # "No" means NOT opting out → in new regime → opting_out_115bac = False
            data["opting_out_115bac"] = opt_out_match.group(1).strip().lower() == "yes"

        # Section 17(1) — Salary: "(a) Salary as per provisions contained in section 17(1) 1871602.00"
        data["salary_171"] = self._extract_amount(text, r"section\s*17\s*\(\s*1\s*\)\s*") or Decimal("0")

        # Section 17(2) — Perquisites
        data["perquisites_172"] = self._extract_amount(text, r"section\s*17\s*\(\s*2\s*\).*?[\d,]+\.\d{2}") or Decimal("0")
        # Try direct match: "(b) ... 0.00" near 17(2) text
        perq_match = re.search(
            r"under\s*section\s*17\s*\(\s*2\s*\).*?\n.*?([\d,]+\.\d{2})",
            text, re.DOTALL,
        )
        if perq_match:
            data["perquisites_172"] = self._to_decimal(perq_match.group(1))

        # Section 17(3) — Profits in lieu
        profits_match = re.search(
            r"under\s*section\s*17\s*\(\s*3\s*\).*?\n.*?([\d,]+\.\d{2})",
            text, re.DOTALL,
        )
        if profits_match:
            data["profits_lieu_173"] = self._to_decimal(profits_match.group(1))

        # Total gross salary: "(d) Total 1871602.00"
        total_match = re.search(r"\(d\)\s*Total\s*([\d,]+\.\d{2})", text)
        if total_match:
            data["total_gross_salary"] = self._to_decimal(total_match.group(1))

        # Standard Deduction: "Standard deduction under section 16(ia) 75000.00"
        std_ded = self._extract_amount(text, r"Standard\s*deduction.*?16\s*\(\s*ia\s*\)\s*")
        if std_ded is not None:
            data["std_deduction_16ia"] = std_ded

        # Professional Tax: "Tax on employment under section 16(iii)"
        pt = self._extract_amount(text, r"16\s*\(\s*iii\s*\)\s*")
        if pt is not None:
            data["professional_tax_16iii"] = pt

        # Income under head salaries: '6. Income chargeable under the head "Salaries" [(3+1(e)-5] 1796602.00'
        inc_sal_match = re.search(
            r'Income\s*chargeable.*?Salaries.*?([\d,]+\.\d{2})',
            text,
        )
        if inc_sal_match:
            data["income_under_head_salaries"] = self._to_decimal(inc_sal_match.group(1))

        # Gross Total Income: "9. Gross total income (6+8) 1796602.00"
        gti_match = re.search(r"Gross\s*total\s*income.*?([\d,]+\.\d{2})", text, re.IGNORECASE)
        if gti_match:
            data["gross_total_income"] = self._to_decimal(gti_match.group(1))

        # Taxable Income: "12. Total taxable income (9-11) 1748733.00"
        ti_match = re.search(r"Total\s*taxable\s*income.*?([\d,]+\.\d{2})", text)
        if ti_match:
            data["taxable_income"] = self._to_decimal(ti_match.group(1))

        # Chapter VI-A
        data["chapter_vi_a"] = self._extract_chapter_via(text)

        # Tax computation
        data["tax_computation"] = self._extract_tax_computation(text)

        return Form16PartB(**{k: v for k, v in data.items() if k in Form16PartB.model_fields})

    def _extract_section10_exemptions(self, text: str) -> Section10Exemptions:
        """Extract Section 10 exemptions."""
        return Section10Exemptions(
            hra_1013A=self._extract_amount(text, r"(?:HRA|House\s*Rent\s*Allowance).*?(?:10\(13A\)|exempt).*?[:.]?\s*") or Decimal("0"),
            travel_concession_105=self._extract_amount(text, r"(?:LTA|Leave\s*Travel|Travel\s*Concession).*?[:.]?\s*") or Decimal("0"),
        )

    def _extract_chapter_via(self, text: str) -> ChapterVIADeductions:
        """Extract Chapter VI-A deductions from Form 16.

        Format: "(f) 47869.00 47869.00" followed by "scheme under section 80CCD (2)"
        Aggregate: "11. 47869.00"
        """
        deductions = ChapterVIADeductions()

        # 80CCD(2): "(f) 47869.00 47869.00" followed by "80CCD (2)" on next line
        # The amounts come BEFORE the section label in the text layout
        nps_match = re.search(
            r"\(f\)\s*([\d,]+\.\d{2})\s*([\d,]+\.\d{2})\s*\n.*?80CCD\s*\(\s*2\s*\)",
            text, re.IGNORECASE,
        )
        if nps_match:
            deductions.sec80ccd2 = self._to_decimal(nps_match.group(2))

        # 80C: from "(a) 0.00 0.00" pattern near "80C"
        c80_match = re.search(
            r"section\s*80C.*?\n.*?([\d,]+\.\d{2})\s*([\d,]+\.\d{2})",
            text, re.DOTALL,
        )
        if c80_match:
            deductions.sec80c = self._to_decimal(c80_match.group(2))

        return deductions

    def _extract_tax_computation(self, text: str) -> TaxComputation:
        """Extract tax computation details.

        Format:
        13. Tax on total income 149747.00
        14. Rebate under section 87A 0.00
        16. Health and education cess 5990.00
        17. Tax payable 155737.00
        """
        return TaxComputation(
            tax_on_income=self._extract_amount(text, r"Tax\s*on\s*total\s*income\s*") or Decimal("0"),
            rebate_87a=self._extract_amount(text, r"Rebate\s*under\s*section\s*87A\s*") or Decimal("0"),
            health_education_cess=self._extract_amount(text, r"Health\s*and\s*education\s*cess\s*") or Decimal("0"),
            net_tax_payable=self._extract_amount(text, r"Net\s*tax\s*payable\s*") or Decimal("0"),
        )

    def _extract_annexure(self, text: str) -> Form16Annexure:
        """Extract Annexure — salary breakup.

        Format:
        Basic 9,32,472.00
        HRA 3,72,990.00
        Special Allowance 2,40,424.00
        ANNUAL LTA 77,649.00
        Annual Lunch Coupons 24,000.00
        ...
        Total
        18,71,602.00
        """
        annexure = Form16Annexure()

        # Find the Annexure section
        annex_match = re.search(
            r"ANNEXURE\s*TO\s*FORM.*?(?=FORM\s*NO\.12BA|Signature|$)",
            text, re.DOTALL | re.IGNORECASE,
        )
        annex_text = annex_match.group(0) if annex_match else text

        # Match lines like: "Component Name 1,23,456.00"
        # Components come between "Sec 17(1)" and "Total"
        comp_section = re.search(
            r"Sec\s*17\s*\(\s*1\s*\).*?(?=Total)",
            annex_text, re.DOTALL,
        )
        if comp_section:
            comp_text = comp_section.group(0)
        else:
            comp_text = annex_text

        # Extract component lines
        comp_pattern = re.compile(
            r"^\s*([A-Za-z][A-Za-z\s\-/&]+?)\s+([\d,]+\.\d{2})\s*$",
            re.MULTILINE,
        )

        for match in comp_pattern.finditer(comp_text):
            name = match.group(1).strip()
            amount_str = match.group(2)

            # Skip non-component lines
            if len(name) < 3 or len(name) > 60:
                continue

            # Skip section headers
            skip_words = ("salary as per", "section", "page", "certificate", "details of")
            if any(w in name.lower() for w in skip_words):
                continue

            amount = self._to_decimal(amount_str)
            comp = SalaryComponent(name=name, amount=amount)
            annexure.components.append(comp)

            # Classify into known components
            matched = False
            for attr, pattern in self.COMPONENT_PATTERNS.items():
                if pattern.search(name) and hasattr(annexure, attr):
                    current = getattr(annexure, attr)
                    setattr(annexure, attr, current + amount)
                    matched = True
                    break

            if not matched:
                # Try to auto-map
                name_upper = name.upper()
                if "BASIC" in name_upper:
                    annexure.basic += amount
                elif "HRA" in name_upper or "HOUSE RENT" in name_upper:
                    annexure.hra += amount
                elif "SPECIAL ALLOW" in name_upper:
                    annexure.special_allowance += amount
                elif "LTA" in name_upper or "TRAVEL" in name_upper:
                    annexure.lta += amount
                elif "LUNCH" in name_upper or "COUPON" in name_upper or "FOOD" in name_upper:
                    annexure.lunch_coupons += amount
                elif "BROADBAND" in name_upper or "INTERNET" in name_upper:
                    annexure.broadband_reimbursement += amount
                elif "SPECIAL AWARD" in name_upper:
                    annexure.special_award += amount
                elif "NPS" in name_upper:
                    annexure.nps_employer += amount
                elif "BONUS" in name_upper or "DBIP" in name_upper:
                    annexure.dbip_bonus += amount

        return annexure

    # --- Utility methods ---

    @staticmethod
    def _to_decimal(value_str: str) -> Decimal:
        """Convert a string like '1,23,456.78' to Decimal."""
        if not value_str:
            return Decimal("0")
        cleaned = value_str.replace(",", "").replace(" ", "").strip()
        try:
            return Decimal(cleaned)
        except Exception:
            return Decimal("0")

    @staticmethod
    def _extract_amount(text: str, pattern: str) -> Optional[Decimal]:
        """Extract a monetary amount after a pattern match."""
        match = re.search(pattern + r"([\d,]+(?:\.\d{2})?)", text)
        if match:
            return Form16Parser._to_decimal(match.group(1))
        return None


def parse_form16(pdf_path: Path, password: Optional[str] = None) -> Form16Data:
    """Convenience function to parse a Form 16 PDF."""
    parser = Form16Parser()
    return parser.parse(pdf_path, password)
