"""Unit tests for the PDF parser helpers (Form 16 / AIS).

PR4.5: Regression coverage for the parsing layer. These tests exercise the
deterministic, side-effect-free helpers — password derivation, date parsing,
and amount extraction — without requiring decrypted sample PDFs in the repo.
The full PDF-to-model path is covered by the (env-gated) E2E test.
"""

import pytest
from decimal import Decimal

from src.parsers.ais_parser import AISParser, _parse_date
from src.parsers.form16_parser import Form16Parser

pytestmark = pytest.mark.unit


def test_ais_password_derivation_is_deterministic():
    """AIS password = lowercase PAN + DDMMYYYY DOB."""
    pw = AISParser.compute_ais_password("CFFPM4503N", "25041995")
    assert pw == "cffpm4503n25041995"


def test_ais_password_derivation_strips_surrounding_whitespace():
    """Whitespace in PAN/DOB must not corrupt the derived password."""
    pw = AISParser.compute_ais_password("  CFFPM4503N  ", " 25041995 ")
    assert pw == "cffpm4503n25041995"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("15/03/2025", "2025-03-15"),
        ("15-03-2025", "2025-03-15"),
        ("2025-03-15", "2025-03-15"),
        ("", None),
        ("not-a-date", None),
    ],
)
def test_parse_date_accepts_common_formats_and_rejects_garbage(raw, expected):
    """Date parsing must accept ITD export formats and refuse invalid input."""
    result = _parse_date(raw)
    if expected is None:
        assert result is None
    else:
        assert result.strftime("%Y-%m-%d") == expected


def test_form16_amount_extraction_parses_indian_number_format():
    """_extract_amount must handle thousands separators and decimals."""
    text = "Gross Salary 18,71,602.00 and TDS 1,55,738"
    gross = Form16Parser._extract_amount(text, r"Gross Salary\s*")
    tds = Form16Parser._extract_amount(text, r"TDS\s*")
    assert gross == Decimal("1871602.00")
    assert tds == Decimal("155738")


def test_form16_amount_extraction_returns_none_when_absent():
    """Missing patterns must yield None, not zero or an exception."""
    assert Form16Parser._extract_amount("no numbers here", r"Bonus\s*") is None
