"""AIS (Annual Information Statement) PDF parser.

AIS PDF password = PAN(lowercase) + DOB(DDMMYYYY)
Example: PAN=CFFPM4503N, DOB=25-04-1995 → password=cffpm4503n25041995
"""

import io
import re
import logging
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pdfplumber
import pikepdf

from src.models.ais import (
    AISData,
    AISTDSEntry,
    AISSavingsInterest,
    AISEquityMFSale,
    AISOtherUnitSale,
    AISSecuritiesPurchase,
    AISRefund,
    AISAnnexureIISalary,
    AISTermDepositInterest,
)

logger = logging.getLogger(__name__)


class AISParser:
    """Parses an AIS PDF into structured AISData."""

    # AIS section markers (text patterns that indicate sections)
    SECTION_MARKERS = {
        "part_a": re.compile(r"Part\s*A\s*[–\-]\s*Personal\s*Information|Personal\s*Details", re.IGNORECASE),
        "tds": re.compile(r"Part\s*B1\s*[–\-]\s*TDS|Tax\s*Deducted\s*at\s*Source|Information\s*Code\s*TDS", re.IGNORECASE),
        "sft": re.compile(r"Part\s*B2\s*[–\-]\s*SFT|Statement\s*of\s*Financial\s*Transaction", re.IGNORECASE),
        "refund": re.compile(r"Part\s*B4\s*[–\-]\s*Refund|Refund\s*Received", re.IGNORECASE),
        "annexure_ii": re.compile(r"Part\s*B7|Annexure\s*II|Other\s*Information", re.IGNORECASE),
    }

    # AIS information codes
    CODE_MAP = {
        "TDS-192": "salary_tds",
        "TDS-193": "interest_tds",
        "TDS-194A": "interest_tds",
        "TDS-194": "dividend_tds",
        "TDS-195": "other_tds",
        "SFT-016(SB)": "savings_interest",
        "SFT-016(TD)": "term_deposit",
        "SFT-18-EMF(M)": "equity_mf_sale",
        "SFT-17-OTU(M)": "other_unit_sale",
        "SFT-17(Pur)": "securities_purchase",
    }

    @staticmethod
    def compute_ais_password(pan: str, dob: str) -> str:
        """
        Compute AIS password from PAN and DOB.

        Format: PAN(lowercase) + DOB(DDMMYYYY)
        Example: PAN='CFFPM4503N', DOB='25041995' → 'cffpm4503n25041995'
        """
        pan_lower = pan.lower().strip()
        dob_clean = dob.strip()
        return f"{pan_lower}{dob_clean}"

    @staticmethod
    def decrypt_pdf(pdf_path: Path, password: str) -> bytes:
        """Decrypt a password-protected AIS PDF."""
        try:
            pdf = pikepdf.open(str(pdf_path), password=password)
            buf = io.BytesIO()
            pdf.save(buf)
            pdf.close()
            buf.seek(0)
            return buf.read()
        except pikepdf.PasswordError:
            raise ValueError(f"Incorrect password for AIS PDF: {pdf_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to decrypt AIS PDF {pdf_path}: {e}")

    @staticmethod
    def extract_text(pdf_bytes: bytes) -> str:
        """Extract all text from decrypted AIS PDF."""
        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)

    def parse(self, pdf_path: Path, pan: str, dob: str) -> AISData:
        """Parse an AIS PDF using PAN+DOB for password derivation."""
        password = self.compute_ais_password(pan, dob)
        pdf_bytes = self.decrypt_pdf(pdf_path, password)
        text = self.extract_text(pdf_bytes)
        return self._parse_text(text, pan)

    def _parse_text(self, text: str, pan: str) -> AISData:
        """Parse extracted AIS text into structured data."""
        ais = AISData(pan=pan)

        # Extract personal info
        self._extract_personal_info(text, ais)

        # Extract TDS entries (Part B1)
        ais.salary_tds, ais.other_tds = self._extract_tds_entries(text)

        # Extract SFT entries (Part B2)
        self._extract_sft_entries(text, ais)

        # Extract refunds (Part B4)
        ais.refunds = self._extract_refunds(text)

        # Extract Annexure II salary (Part B7)
        ais.annexure_ii_salary = self._extract_annexure_ii(text)

        return ais

    def _extract_personal_info(self, text: str, ais: AISData) -> None:
        """Extract personal information from Part A."""
        # Name
        name_match = re.search(r"Name\s*[:.]?\s*(.+?)(?:\n|PAN|Aadhaar)", text)
        if name_match:
            ais.name = name_match.group(1).strip()

        # Aadhaar
        aadhaar_match = re.search(r"Aadhaar\s*(?:Number|No)[.:]?\s*XXXX\s*XXXX\s*(\d{4})", text)
        if aadhaar_match:
            ais.aadhaar_masked = f"XXXX XXXX {aadhaar_match.group(1)}"

        # DOB
        dob_match = re.search(r"Date\s*of\s*Birth[.:]?\s*(\d{2}[/-]\d{2}[/-]\d{4})", text)
        if dob_match:
            dob_str = dob_match.group(1)
            try:
                ais.dob = datetime.strptime(dob_str.replace("-", "/"), "%d/%m/%Y").date()
            except ValueError:
                pass

        # Mobile
        mobile_match = re.search(r"Mobile\s*(?:No|Number)[.:]?\s*(\d{10})", text)
        if mobile_match:
            ais.mobile = mobile_match.group(1)

        # Email
        email_match = re.search(r"Email\s*(?:ID|Address)?[.:]?\s*([\w.+-]+@[\w-]+\.[\w.]+)", text, re.IGNORECASE)
        if email_match:
            ais.email = email_match.group(1)

        # Address
        addr_match = re.search(r"Address\s*[:.]?\s*(.+?)(?:\n\n|\n(?:PAN|Mobile))", text, re.DOTALL)
        if addr_match:
            ais.address = " ".join(addr_match.group(1).split())

    def _extract_tds_entries(self, text: str) -> tuple[list[AISTDSEntry], list[AISTDSEntry]]:
        """Extract TDS entries from Part B1."""
        salary_entries = []
        other_entries = []

        # Find TDS section
        tds_section_match = re.search(
            r"Part\s*B1.*?(?=Part\s*B2|Part\s*B3|Part\s*B4|$)",
            text, re.DOTALL | re.IGNORECASE,
        )
        tds_text = tds_section_match.group(0) if tds_section_match else text

        # Parse individual TDS entries
        # TDS entries typically have: Code, Source, Quarter, Amount Paid, TDS
        entry_pattern = re.compile(
            r"(TDS-\d+[A-Za-z]*)\s+"
            r"([A-Z][A-Za-z\s.&]+?)\s+"
            r"(Q[1-4]\(\w+-\w+\))\s+"
            r"(\d{2}/\d{2}/\d{4})\s+"
            r"([\d,]+)\s+"
            r"([\d,]+)\s+"
            r"([\d,]+)",
            re.IGNORECASE,
        )

        for match in entry_pattern.finditer(tds_text):
            entry = AISTDSEntry(
                information_code=match.group(1),
                information_source=match.group(2).strip(),
                quarter=match.group(3),
                date_of_payment=self._parse_date(match.group(4)),
                amount_paid=self._to_decimal(match.group(5)),
                tds_deducted=self._to_decimal(match.group(6)),
                tds_deposited=self._to_decimal(match.group(7)),
            )
            if entry.information_code == "TDS-192":
                salary_entries.append(entry)
            else:
                other_entries.append(entry)

        return salary_entries, other_entries

    def _extract_sft_entries(self, text: str, ais: AISData) -> None:
        """Extract SFT (Statement of Financial Transactions) entries."""
        # SFT-016(SB) — Savings Bank Interest
        ais.savings_interest = self._extract_savings_interest(text)

        # SFT-016(TD) — Term Deposit Interest
        ais.term_deposit_interest = self._extract_term_deposit_interest(text)

        # SFT-18-EMF(M) — Equity Mutual Fund Sales
        ais.equity_mf_sales = self._extract_equity_mf_sales(text)

        # SFT-17-OTU(M) — Other Unit Sales (ETF, Debt Funds)
        ais.other_unit_sales = self._extract_other_unit_sales(text)

        # SFT-17(Pur) — Securities Purchases
        ais.securities_purchases = self._extract_securities_purchases(text)

    def _extract_savings_interest(self, text: str) -> list[AISSavingsInterest]:
        """Extract SFT-016(SB) savings bank interest entries."""
        entries = []
        # Pattern for savings interest: Bank name, PAN, Account#, Type, Interest, Date
        sb_pattern = re.compile(
            r"(?:SFT-016\(SB\)|Savings.*?Interest).*?"
            r"([A-Z][A-Za-z\s]+(?:BANK|Bank))\s+"
            r"([A-Z]{5}\d{4}[A-Z])\s+"
            r"(\d+)\s+"
            r"(Saving|Savings)\s+"
            r"([\d,]+)\s+"
            r"(\d{2}/\d{2}/\d{4})",
            re.IGNORECASE,
        )
        for match in sb_pattern.finditer(text):
            entries.append(AISSavingsInterest(
                bank_name=match.group(1).strip(),
                bank_pan=match.group(2),
                account_number=match.group(3),
                account_type=match.group(4),
                interest_amount=self._to_decimal(match.group(5)),
                reported_on=self._parse_date(match.group(6)),
            ))
        return entries

    def _extract_term_deposit_interest(self, text: str) -> list[AISTermDepositInterest]:
        """Extract SFT-016(TD) term deposit interest entries."""
        entries = []
        td_pattern = re.compile(
            r"(?:SFT-016\(TD\)|Term\s*Deposit).*?"
            r"([A-Z][A-Za-z\s]+(?:BANK|Bank))\s+"
            r"([A-Z]{5}\d{4}[A-Z])\s+"
            r"(\d+)\s+"
            r"([\d,]+)\s+"
            r"(\d{2}/\d{2}/\d{4})",
            re.IGNORECASE,
        )
        for match in td_pattern.finditer(text):
            entries.append(AISTermDepositInterest(
                bank_name=match.group(1).strip(),
                bank_pan=match.group(2),
                account_number=match.group(3),
                interest_amount=self._to_decimal(match.group(4)),
                reported_on=self._parse_date(match.group(5)),
            ))
        return entries

    def _extract_equity_mf_sales(self, text: str) -> list[AISEquityMFSale]:
        """Extract SFT-18-EMF(M) equity mutual fund sale entries."""
        entries = []
        # Pattern for equity MF sales from AIS
        emf_pattern = re.compile(
            r"(?:SFT-18|EMF\(M\)).*?"
            r"([A-Z][A-Za-z\s]+(?:MF|Mutual\s*Fund|Asset|AMC)).*?"
            r"(INF\d{3}[A-Z]?\d{6})",  # ISIN
            re.IGNORECASE | re.DOTALL,
        )

        # More general table-based approach
        # AIS typically uses pipe-separated or fixed-width tables
        table_rows = self._extract_table_rows(text, "SFT-18")
        for row in table_rows:
            cells = [c.strip() for c in row.split("|") if c.strip()]
            if len(cells) >= 10:
                try:
                    entries.append(AISEquityMFSale(
                        amc_name=cells[0] if len(cells) > 0 else "",
                        isin=cells[1] if len(cells) > 1 else "",
                        security_name=cells[2] if len(cells) > 2 else "",
                        date_of_sale=self._parse_date(cells[3]) if len(cells) > 3 else None,
                        quantity=self._to_decimal(cells[4]) if len(cells) > 4 else Decimal("0"),
                        sale_price_per_unit=self._to_decimal(cells[5]) if len(cells) > 5 else Decimal("0"),
                        sale_consideration=self._to_decimal(cells[6]) if len(cells) > 6 else Decimal("0"),
                        stt_paid=self._to_decimal(cells[7]) if len(cells) > 7 else Decimal("0"),
                        cost_of_acquisition=self._to_decimal(cells[8]) if len(cells) > 8 else Decimal("0"),
                        term=cells[9] if len(cells) > 9 else "",
                    ))
                except (ValueError, IndexError):
                    continue

        return entries

    def _extract_other_unit_sales(self, text: str) -> list[AISOtherUnitSale]:
        """Extract SFT-17-OTU(M) non-equity unit sales (ETF, debt funds)."""
        entries = []
        table_rows = self._extract_table_rows(text, "SFT-17")
        for row in table_rows:
            cells = [c.strip() for c in row.split("|") if c.strip()]
            if len(cells) >= 10:
                try:
                    entries.append(AISOtherUnitSale(
                        depository=cells[0] if len(cells) > 0 else "",
                        security_name=cells[1] if len(cells) > 1 else "",
                        isin=cells[2] if len(cells) > 2 else "",
                        date_of_sale=self._parse_date(cells[3]) if len(cells) > 3 else None,
                        quantity=self._to_decimal(cells[4]) if len(cells) > 4 else Decimal("0"),
                        sale_price=self._to_decimal(cells[5]) if len(cells) > 5 else Decimal("0"),
                        sale_consideration=self._to_decimal(cells[6]) if len(cells) > 6 else Decimal("0"),
                        cost_of_acquisition=self._to_decimal(cells[7]) if len(cells) > 7 else Decimal("0"),
                        term=cells[8] if len(cells) > 8 else "",
                    ))
                except (ValueError, IndexError):
                    continue
        return entries

    def _extract_securities_purchases(self, text: str) -> list[AISSecuritiesPurchase]:
        """Extract SFT-17(Pur) securities purchase summary."""
        entries = []
        table_rows = self._extract_table_rows(text, "SFT-17.*?Pur")
        for row in table_rows:
            cells = [c.strip() for c in row.split("|") if c.strip()]
            if len(cells) >= 5:
                try:
                    entries.append(AISSecuritiesPurchase(
                        depository=cells[0] if len(cells) > 0 else "",
                        client_id=cells[1] if len(cells) > 1 else "",
                        market_purchase=self._to_decimal(cells[3]) if len(cells) > 3 else Decimal("0"),
                        market_sales=self._to_decimal(cells[4]) if len(cells) > 4 else Decimal("0"),
                    ))
                except (ValueError, IndexError):
                    continue
        return entries

    def _extract_refunds(self, text: str) -> list[AISRefund]:
        """Extract Part B4 — Refund received."""
        entries = []
        refund_pattern = re.compile(
            r"(\d{4}-\d{2})\s+"
            r"(ECS|RTGS|NEFT|Cheque)\s+"
            r"([\d,]+)\s+"
            r"(\d{2}/\d{2}/\d{4})",
            re.IGNORECASE,
        )
        for match in refund_pattern.finditer(text):
            entries.append(AISRefund(
                financial_year=match.group(1),
                mode=match.group(2),
                amount=self._to_decimal(match.group(3)),
                date_of_payment=self._parse_date(match.group(4)),
            ))
        return entries

    def _extract_annexure_ii(self, text: str) -> Optional[AISAnnexureIISalary]:
        """Extract Part B7 Annexure II — Salary cross-reference."""
        sal_171 = self._extract_amount(text, r"Gross\s*Salary.*?17\(1\).*?[:.]?\s*")
        sal_172 = self._extract_amount(text, r"Perquisites.*?17\(2\).*?[:.]?\s*")
        sal_173 = self._extract_amount(text, r"Profits.*?17\(3\).*?[:.]?\s*")
        total = self._extract_amount(text, r"Total\s*Gross\s*Salary.*?[:.]?\s*")

        if any([sal_171, sal_172, sal_173, total]):
            return AISAnnexureIISalary(
                gross_salary_171=sal_171 or Decimal("0"),
                perquisites_172=sal_172 or Decimal("0"),
                profits_lieu_173=sal_173 or Decimal("0"),
                total_gross_salary=total or Decimal("0"),
            )
        return None

    @staticmethod
    def _extract_table_rows(text: str, section_marker: str) -> list[str]:
        """Extract rows from a table-like section of AIS text."""
        section_match = re.search(
            rf"{section_marker}.*?(?=\n\s*\n|Part\s*B\d|Section|\Z)",
            text, re.DOTALL | re.IGNORECASE,
        )
        if not section_match:
            return []
        section_text = section_match.group(0)
        return [line.strip() for line in section_text.split("\n") if line.strip() and "|" in line]

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
    def _parse_date(date_str: str) -> Optional[date]:
        """Parse a date string in DD/MM/YYYY format."""
        if not date_str:
            return None
        date_str = date_str.strip()
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _extract_amount(text: str, pattern: str) -> Optional[Decimal]:
        """Extract a monetary amount after a pattern match."""
        match = re.search(pattern + r"([\d,]+(?:\.\d{2})?)", text)
        if match:
            return AISParser._to_decimal(match.group(1))
        return None


def parse_ais(pdf_path: Path, pan: str, dob: str) -> AISData:
    """Convenience function: parse AIS PDF with PAN+DOB password."""
    parser = AISParser()
    return parser.parse(pdf_path, pan, dob)
