"""AIS (Annual Information Statement) PDF parser.

AIS PDF password = PAN(lowercase) + DOB(DDMMYYYY)
Uses pdfplumber table extraction for reliable structured data parsing.
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
)

logger = logging.getLogger(__name__)


def _clean_cell(cell: Optional[str]) -> str:
    """Clean a table cell — strip whitespace, collapse newlines to spaces."""
    if not cell:
        return ""
    return " ".join(cell.split())


def _to_decimal(value_str: Optional[str]) -> Decimal:
    """Convert a string like '1,23,456.78' to Decimal."""
    if not value_str:
        return Decimal("0")
    cleaned = value_str.replace(",", "").replace(" ", "").strip()
    try:
        return Decimal(cleaned)
    except Exception:
        return Decimal("0")


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse a date string."""
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


class AISParser:
    """Parses an AIS PDF into structured AISData using table extraction."""

    @staticmethod
    def compute_ais_password(pan: str, dob: str) -> str:
        """Compute AIS password: PAN(lowercase) + DOB(DDMMYYYY)."""
        return f"{pan.lower().strip()}{dob.strip()}"

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
    def _extract_all_tables(pdf_bytes: bytes) -> list[list[list[Optional[str]]]]:
        """Extract all tables from all pages of the decrypted AIS PDF."""
        all_rows = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        all_rows.append([_clean_cell(c) for c in row])
        return all_rows

    def parse(self, pdf_path: Path, pan: str, dob: str) -> AISData:
        """Parse an AIS PDF using PAN+DOB for password derivation."""
        password = self.compute_ais_password(pan, dob)
        pdf_bytes = self.decrypt_pdf(pdf_path, password)
        all_rows = self._extract_all_tables(pdf_bytes)
        return self._parse_rows(all_rows, pan)

    def _parse_rows(self, all_rows: list[list[str]], pan: str) -> AISData:
        """Parse extracted table rows into structured AIS data."""
        ais = AISData(pan=pan)

        # Extract personal info from text-based rows
        full_text = " ".join([" ".join(r) for r in all_rows])
        self._extract_personal_info(full_text, ais)

        # Parse each row, classifying by information code
        salary_tds = []
        other_tds = []
        equity_mf_sales = []
        other_unit_sales = []
        savings_interest = []
        refunds = []
        securities_purchases = []
        annexure_salary = None
        in_equity_table = False
        in_otu_table = False

        for row in all_rows:
            joined = " ".join(row)

            # Detect table type from header/info code row
            info_code = self._find_info_code(row)

            if info_code == "TDS-192":
                salary_tds.extend(self._parse_tds_detail_rows(row, all_rows))
            elif info_code and info_code.startswith("TDS-") and info_code != "TDS-192":
                if "Ann.II-SAL" in info_code or "Annexure" in info_code:
                    annexure_salary = self._parse_annexure_salary(row, all_rows)
                else:
                    other_tds.extend(self._parse_tds_detail_rows(row, all_rows))

            elif "SFT-016(SB)" in joined:
                entry = self._parse_savings_interest_row(row, all_rows)
                if entry and entry.interest_amount > 0:
                    savings_interest.append(entry)

            elif "SFT-18-EMF(M)" in joined:
                in_equity_table = True
                in_otu_table = False

            elif "SFT-17-OTU(M)" in joined:
                in_otu_table = True
                in_equity_table = False

            elif "SFT-17(Pur)" in joined:
                in_equity_table = False
                in_otu_table = False
                entry = self._parse_securities_purchase_row(row, all_rows)
                if entry:
                    securities_purchases.append(entry)

            # Check for data rows (start with a number, not "SR.")
            elif row and row[0].strip().isdigit() and "SR." not in row[0]:
                sr_no = row[0].strip()

                has_date = bool(re.search(r"(\d{2}/\d{2}/\d{4})", joined))
                has_inf_isin = "INF" in joined
                has_equity_kw = "Equity" in joined or "Mutual" in joined or "MF(" in joined or "quant" in joined.lower()
                has_other_units_kw = "Other Units" in joined or "Exchange Traded" in joined or "GOLD" in joined.upper()

                # Detect equity MF table continuation even without SFT-18 header
                if has_equity_kw and has_date and has_inf_isin:
                    in_equity_table = True

                # Detect OTU table continuation even without SFT-17 header
                if has_other_units_kw and has_date:
                    in_otu_table = True

                # Equity MF sale data row
                if in_equity_table and len(row) >= 10 and has_date:
                    entry = self._parse_equity_mf_row(row)
                    if entry and entry.sale_consideration > 0 and entry.date_of_sale:
                        equity_mf_sales.append(entry)

                # Other unit sale data row
                if in_otu_table and len(row) >= 8 and has_date:
                    entry = self._parse_other_unit_row(row)
                    if entry and entry.sale_consideration > 0 and entry.date_of_sale:
                        other_unit_sales.append(entry)

                # Refund row
                if "ECS" in joined or "RTGS" in joined or "NEFT" in joined:
                    entry = self._parse_refund_row(row)
                    if entry:
                        refunds.append(entry)

            # Detect section boundaries — reset flags
            if "Part B" in joined and "SFT" not in joined and "TDS" not in joined:
                in_equity_table = False
                in_otu_table = False

        # Assign to AIS
        ais.salary_tds = salary_tds
        ais.other_tds = other_tds
        ais.equity_mf_sales = equity_mf_sales
        ais.other_unit_sales = other_unit_sales
        ais.savings_interest = savings_interest
        ais.refunds = refunds
        ais.securities_purchases = securities_purchases
        ais.annexure_ii_salary = annexure_salary

        return ais

    def _find_info_code(self, row: list[str]) -> Optional[str]:
        """Find an AIS information code in a table row."""
        joined = " ".join(row)
        # TDS codes
        tds_match = re.search(r"(TDS-\d+[A-Za-z]*(?:\.Ann\.II-SAL)?)", joined)
        if tds_match:
            return tds_match.group(1)
        # SFT codes
        sft_match = re.search(r"(SFT-\d+[A-Za-z]*(?:\([^)]+\))?(?:-[A-Z]+\([A-Z]\))?)", joined)
        if sft_match:
            return sft_match.group(1)
        return None

    def _parse_tds_detail_rows(self, summary_row: list[str], all_rows: list[list[str]]) -> list[AISTDSEntry]:
        """Parse quarterly TDS breakdown rows that follow a TDS summary row."""
        entries = []
        joined_summary = " ".join(summary_row)
        info_code = self._find_info_code(summary_row) or ""

        # Find the source name
        source = ""
        source_match = re.search(r"((?:APPLIED|TCS|WIPRO|INFOSYS)[\w\s.&]*(?:LTD|LIMITED|BANK|INDIA)?(?:\s*\([A-Z]{4}\d{5}[A-Z]\))?)", joined_summary)
        if source_match:
            source = source_match.group(1).strip()

        # Extract total from summary row
        for cell in summary_row:
            try:
                _to_decimal(cell)
            except Exception:
                pass

        # The detail rows have: SR_NO, QUARTER, DATE, AMOUNT_PAID, TDS_DEDUCTED, TDS_DEPOSITED
        # They follow the summary row; they have Q1-Q4 in them
        for row in all_rows:
            joined = " ".join(row)
            quarter_match = re.search(r"(Q[1-4]\([A-Za-z]+-[A-Za-z]+\))", joined)
            if not quarter_match:
                continue

            # Must have a date
            date_match = re.search(r"(\d{2}/\d{2}/\d{4})", joined)
            if not date_match:
                continue

            # Extract amounts — look for the numeric values in the row
            amounts = []
            for cell in row:
                c = cell.strip()
                if re.match(r"^[\d,]+$", c) or re.match(r"^[\d,]+\.[\d]{2}$", c):
                    amounts.append(_to_decimal(c))

            if len(amounts) >= 2:
                entries.append(AISTDSEntry(
                    information_code=info_code,
                    information_source=source,
                    quarter=quarter_match.group(1),
                    date_of_payment=_parse_date(date_match.group(1)),
                    amount_paid=amounts[0] if len(amounts) >= 1 else Decimal("0"),
                    tds_deducted=amounts[1] if len(amounts) >= 2 else Decimal("0"),
                    tds_deposited=amounts[2] if len(amounts) >= 3 else Decimal("0"),
                ))

        return entries

    def _parse_savings_interest_row(self, summary_row: list[str], all_rows: list[list[str]]) -> Optional[AISSavingsInterest]:
        """Parse an SFT-016(SB) savings interest entry."""
        joined = " ".join(summary_row)

        # Extract bank name and PAN from summary row
        source = ""
        source_match = re.search(r"((?:STATE BANK|HDFC BANK|ICICI BANK|[\w\s]+BANK)[\w\s.&()A-Z0-9]*)", joined, re.IGNORECASE)
        if source_match:
            source = source_match.group(1).strip()

        # Extract bank PAN from parentheses
        bank_pan = ""
        pan_match = re.search(r"\(([A-Z]{5}\d{4}[A-Z](?:\.[A-Z]{2}\d{3})?)\)", joined)
        if pan_match:
            bank_pan = pan_match.group(1)

        # Extract interest amount from summary row — last numeric value before end
        summary_interest = Decimal("0")
        for cell in reversed(summary_row):
            val = _to_decimal(cell)
            if val > 0:
                summary_interest = val
                break

        # Look for detail row with account number and "Saving"
        account_no = ""
        interest = summary_interest
        reported_on = None

        for row in all_rows:
            joined_detail = " ".join(row)
            if "SR. NO." in joined_detail or "INFORMATION CODE" in joined_detail:
                continue
            if "REPORTED ON" in joined_detail:
                continue

            # Detail row has: SR_NO, DATE, ACCOUNT_NO, ACCOUNT_TYPE, INTEREST, STATUS
            if "Saving" in joined_detail:
                # Column 1: date, Column 2: account number, Column 4: interest
                if len(row) >= 5:
                    reported_on = _parse_date(row[1]) if len(row) > 1 else None
                    account_no = row[2].strip() if len(row) > 2 else ""
                    interest = _to_decimal(row[4]) if len(row) > 4 else interest
                break

        if summary_interest > 0 or interest > 0:
            return AISSavingsInterest(
                bank_name=source.split("(")[0].strip() if "(" in source else source,
                bank_pan=bank_pan,
                account_number=account_no,
                account_type="Saving",
                interest_amount=interest if interest > 0 else summary_interest,
                reported_on=reported_on,
            )

        return None

    def _parse_equity_mf_row(self, row: list[str]) -> Optional[AISEquityMFSale]:
        """Parse an SFT-18-EMF(M) data row — column-adaptive since page layouts differ."""
        joined = " ".join(row)
        if not re.search(r"\d{2}/\d{2}/\d{4}", joined):
            return None

        # Find key values by scanning rather than hardcoding column indices
        # (Page 1 and Page 2 tables have different column layouts due to merged cells)

        date_of_sale = None
        amc_name = ""
        security_name = ""
        asset_type = ""
        quantity = Decimal("0")
        sale_price = Decimal("0")
        sale_consideration = Decimal("0")
        stt_paid = Decimal("0")
        cost_of_acquisition = Decimal("0")
        term = ""
        status = ""

        # Detect column layout by finding the date position:
        # Page 1 (22 cols): date[3], type[9], qty[10], price[11], cons[13], stt[14], cost[15]
        # Page 2 (17 cols): date[2], type[7], qty[8],  price[9],  cons[10], stt[11], cost[12]
        date_idx = -1
        for j in range(min(len(row), 5)):
            if re.match(r"\d{2}/\d{2}/\d{4}", row[j].strip()):
                date_idx = j
                break

        is_short = len(row) <= 18  # page 2 has 17 cols, no extra blank col before cons

        # Relative to date column:
        # Page 1: type=+6, qty=+7, price=+8, [blank], cons=+10, stt=+11, cost=+12
        # Page 2: type=+5, qty=+6, price=+7, cons=+8, stt=+9, cost=+10
        d = date_idx
        type_idx = d + (5 if is_short else 6) if d >= 0 else -1
        qty_idx = d + (6 if is_short else 7) if d >= 0 else -1
        price_idx = d + (7 if is_short else 8) if d >= 0 else -1
        cons_idx = d + (8 if is_short else 10) if d >= 0 else -1
        stt_idx = d + (9 if is_short else 11) if d >= 0 else -1
        cost_idx = d + (10 if is_short else 12) if d >= 0 else -1

        date_of_sale = _parse_date(row[date_idx]) if date_idx >= 0 else None
        amc_name = row[1] if len(row) > 1 else ""
        security_name = row[date_idx + 2] if date_idx >= 0 and len(row) > date_idx + 2 else ""
        asset_type = row[type_idx].strip() if type_idx >= 0 and len(row) > type_idx else ""
        quantity = _to_decimal(row[qty_idx]) if qty_idx >= 0 and len(row) > qty_idx else Decimal("0")
        sale_price = _to_decimal(row[price_idx]) if price_idx >= 0 and len(row) > price_idx else Decimal("0")
        sale_consideration = _to_decimal(row[cons_idx]) if cons_idx >= 0 and len(row) > cons_idx else Decimal("0")
        stt_paid = _to_decimal(row[stt_idx]) if stt_idx >= 0 and len(row) > stt_idx else Decimal("0")
        cost_of_acquisition = _to_decimal(row[cost_idx]) if cost_idx >= 0 and len(row) > cost_idx else Decimal("0")

        if "long" in asset_type.lower():
            term = "Long term"
        elif "short" in asset_type.lower():
            term = "Short term"

        # ISIN
        isin = ""
        isin_match = re.search(r"\(?(INF\d{3}[A-Z]?\d{6})\)?", security_name.replace(" ", ""))
        if isin_match:
            isin = isin_match.group(1)

        return AISEquityMFSale(
            amc_name=amc_name,
            isin=isin,
            security_name=security_name,
            date_of_sale=date_of_sale,
            quantity=quantity,
            sale_price_per_unit=sale_price,
            sale_consideration=sale_consideration,
            stt_paid=stt_paid,
            cost_of_acquisition=cost_of_acquisition,
            term=term,
        )

    def _parse_other_unit_row(self, row: list[str]) -> Optional[AISOtherUnitSale]:
        """Parse an SFT-17-OTU(M) data row — column-position based."""
        joined = " ".join(row)
        if not re.search(r"\d{2}/\d{2}/\d{4}", joined):
            return None

        # OTU layout: date[1], name[3], type[8], qty[10], price[11], cons[12], cost[13]
        date_of_sale = _parse_date(row[1]) if len(row) > 1 else None
        security_name = row[3] if len(row) > 3 else ""
        asset_type = row[8].strip() if len(row) > 8 else ""
        quantity = _to_decimal(row[10]) if len(row) > 10 else Decimal("0")
        sale_price = _to_decimal(row[11]) if len(row) > 11 else Decimal("0")
        sale_consideration = _to_decimal(row[12]) if len(row) > 12 else Decimal("0")
        cost_of_acquisition = _to_decimal(row[13]) if len(row) > 13 else Decimal("0")

        term = ""
        if "long" in asset_type.lower():
            term = "Long term"
        elif "short" in asset_type.lower():
            term = "Short term"

        isin = ""
        isin_match = re.search(r"\(?(INF\d{3}[A-Z]?\d{6})\)?", security_name.replace(" ", ""))
        if isin_match:
            isin = isin_match.group(1)

        return AISOtherUnitSale(
            depository="CDSL",
            security_name=security_name,
            isin=isin,
            date_of_sale=date_of_sale,
            quantity=quantity,
            sale_price=sale_price,
            sale_consideration=sale_consideration,
            cost_of_acquisition=cost_of_acquisition,
            term=term,
        )

    def _parse_securities_purchase_row(self, summary_row: list[str], all_rows: list[list[str]]) -> Optional[AISSecuritiesPurchase]:
        """Parse an SFT-17(Pur) securities purchase entry."""
        joined = " ".join(summary_row)
        source = ""
        source_match = re.search(r"([\w\s().&,]+?)\s*\d{4,}", joined)
        if source_match:
            source = source_match.group(1).strip().rstrip(",")

        market_purchase = Decimal("0")
        market_sales = Decimal("0")
        client_id = ""

        # The detail row follows
        for row in all_rows:
            joined_detail = " ".join(row)
            if "MARKET PURCHASE" in joined_detail and "MARKET SALES" in joined_detail:
                # Find the numeric values
                amounts = []
                for cell in row:
                    c = cell.strip()
                    if re.match(r"^[\d,]+$", c) or re.match(r"^[\d,]+\.[\d]{2}$", c):
                        amounts.append(_to_decimal(c))
                # Second-to-last is client ID, market purchase and sales are amounts
                if len(amounts) >= 2:
                    market_purchase = amounts[0] if len(amounts) >= 1 else Decimal("0")
                    market_sales = amounts[1] if len(amounts) >= 2 else Decimal("0")
                # Client ID
                for cell in row:
                    if cell.strip().isdigit() and len(cell.strip()) == 8:
                        client_id = cell.strip()
                break

        return AISSecuritiesPurchase(
            depository=source,
            client_id=client_id,
            market_purchase=market_purchase,
            market_sales=market_sales,
        )

    def _parse_annexure_salary(self, row: list[str], all_rows: list[list[str]]) -> Optional[AISAnnexureIISalary]:
        """Parse TDS-Ann.II-SAL salary annexure entry."""
        joined = " ".join(row)
        # Look for the detail row with salary breakup
        for detail_row in all_rows:
            joined_detail = " ".join(detail_row)
            if "GROSS SALARY" in joined_detail and "17(1)" in joined_detail:
                amounts = []
                for cell in detail_row:
                    c = cell.strip()
                    if re.match(r"^[\d,]+$", c) or re.match(r"^[\d,]+\.[\d]{2}$", c):
                        amounts.append(_to_decimal(c))
                if len(amounts) >= 1:
                    return AISAnnexureIISalary(
                        gross_salary_171=amounts[0] if len(amounts) >= 1 else Decimal("0"),
                        perquisites_172=amounts[1] if len(amounts) >= 2 else Decimal("0"),
                        profits_lieu_173=amounts[2] if len(amounts) >= 3 else Decimal("0"),
                        total_gross_salary=amounts[3] if len(amounts) >= 4 else (
                            amounts[0] if len(amounts) == 1 else Decimal("0")
                        ),
                    )
        return None

    def _parse_refund_row(self, row: list[str]) -> Optional[AISRefund]:
        """Parse a Part B4 refund row."""
        joined = " ".join(row)
        if not ("ECS" in joined or "RTGS" in joined or "NEFT" in joined):
            return None

        # Columns: SR, FY, MODE, NATURE, AMOUNT, DATE
        fy = ""
        fy_match = re.search(r"(\d{4}-\d{2})", joined)
        if fy_match:
            fy = fy_match.group(1)

        mode = ""
        if "ECS" in joined:
            mode = "ECS"
        elif "RTGS" in joined:
            mode = "RTGS"
        elif "NEFT" in joined:
            mode = "NEFT"

        amount = Decimal("0")
        date_of_payment = None
        # Find amount (numeric with commas) and date
        for cell in row:
            c = cell.strip()
            if re.match(r"^[\d,]+$", c):
                amount = _to_decimal(c)
            if re.match(r"\d{2}/\d{2}/\d{4}", c):
                date_of_payment = _parse_date(c)

        return AISRefund(
            financial_year=fy,
            mode=mode,
            amount=amount,
            date_of_payment=date_of_payment,
        )

    def _extract_personal_info(self, text: str, ais: AISData) -> None:
        """Extract personal information from Part A text."""
        # Name — format: "PAN XXXX XXXX NNNN FULL NAME"
        # Search using the actual PAN from the AIS data
        pan_to_find = ais.pan or ""
        pan_pos = text.find(pan_to_find) if pan_to_find else -1
        if pan_pos < 0:
            # Fallback: find any PAN-format string followed by masked Aadhaar
            pan_match = re.search(r"([A-Z]{5}[0-9]{4}[A-Z])\s+XXXX\s*XXXX", text)
            if pan_match:
                pan_pos = text.find(pan_match.group(1))
        if pan_pos >= 0:
            after_pan = text[pan_pos+10:]  # Skip PAN
            # Skip "XXXX XXXX NNNN" (masked Aadhaar)
            after_aadhaar = re.sub(r"XXXX\s*XXXX\s*\d{4}", "", after_pan).strip()
            name_match = re.search(r"([A-Z]{2,}(?:\s+[A-Z]{2,})+)", after_aadhaar)
            if name_match:
                ais.name = name_match.group(1).strip()

        # Aadhaar masked
        aadhaar_match = re.search(r"Aadhaar[^X]*?(XXXX\s*XXXX\s*\d{4})", text)
        if aadhaar_match:
            ais.aadhaar_masked = " ".join(aadhaar_match.group(1).split())

        # DOB
        dob_match = re.search(r"Date\s*of\s*Birth\s*(\d{2}/\d{2}/\d{4})", text)
        if dob_match:
            try:
                ais.dob = datetime.strptime(dob_match.group(1), "%d/%m/%Y").date()
            except ValueError:
                pass

        # Mobile — format: "Mobile Number 7543037872"
        mobile_match = re.search(r"Mobile\s*(?:Number)?\s*(\d{10})", text)
        if mobile_match:
            ais.mobile = mobile_match.group(1)

        # Email
        email_match = re.search(r"E-mail\s*(?:Address)?\s*([\w.+-]+@[\w-]+\.[\w.]+)", text)
        if email_match:
            ais.email = email_match.group(1)


def parse_ais(pdf_path: Path, pan: str, dob: str) -> AISData:
    """Convenience function: parse AIS PDF with PAN+DOB password."""
    parser = AISParser()
    return parser.parse(pdf_path, pan, dob)
