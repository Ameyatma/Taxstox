"""Unit tests for confidence scoring framework."""

from decimal import Decimal

from src.parsers.confidence import (
    ConfidenceLevel,
    ScoredField,
    DocumentExtractionReport,
    high,
    medium,
    low,
    missing,
)


class TestScoredField:
    def test_high_confidence(self):
        field = high("ABCDE1234F", "PAN regex")
        assert field.value == "ABCDE1234F"
        assert field.confidence == ConfidenceLevel.HIGH
        assert field.is_reliable is True
        assert field.needs_review is False
        assert field.is_missing is False

    def test_medium_confidence(self):
        field = medium(Decimal("50000"), "heuristic")
        assert field.is_reliable is True

    def test_low_confidence(self):
        field = low("maybe name", "fuzzy OCR")
        assert field.is_reliable is False
        assert field.needs_review is True

    def test_missing(self):
        field = missing()
        assert field.is_missing is True
        assert field.value is None

    def test_alternatives(self):
        field = ScoredField(
            value="CFFPM4503N",
            confidence=ConfidenceLevel.HIGH,
            source="regex",
            alternatives=["CFFPM4503M", "CFFPM45030"],
        )
        assert len(field.alternatives) == 2


class TestDocumentExtractionReport:
    def test_perfect_extraction(self):
        report = DocumentExtractionReport(
            document_type="form16",
            total_fields=10,
            fields_high=10,
        )
        assert report.extraction_rate == 1.0
        assert report.auto_fill_rate == 1.0
        assert report.is_reliable is True

    def test_partial_extraction(self):
        report = DocumentExtractionReport(
            document_type="form16",
            total_fields=10,
            fields_high=5,
            fields_medium=3,
            fields_low=1,
            fields_missing=1,
        )
        assert report.extraction_rate == 0.9
        assert report.auto_fill_rate == 0.8
        assert report.is_reliable is False

    def test_all_missing(self):
        report = DocumentExtractionReport(
            document_type="ais",
            total_fields=10,
            fields_missing=10,
        )
        assert report.extraction_rate == 0.0

    def test_to_dict(self):
        report = DocumentExtractionReport(
            document_type="form16",
            total_fields=10,
            fields_high=8,
            fields_medium=2,
        )
        d = report.to_dict()
        assert d["document_type"] == "form16"
        assert d["is_reliable"] is True
