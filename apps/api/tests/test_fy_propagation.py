"""PR3 Remediation — Financial-Year Propagation regression tests.

Verifies the FY-propagation blocker fix end-to-end:

  1. ``FinancialYear.from_assessment_year`` maps an assessment year to its
     financial year (AY '2026-27' ⇒ FY2025-26) — distinct from ``from_string``
     which would misread '2026-27' as FY2026-27.
  2. ``routes._resolve_financial_year`` derives the filing year from the
     Form 16 assessment year, with NO implicit FY2025-26 fallback
     (a missing/malformed assessment year is rejected, not silently defaulted).
  3. The ITR-1 builder's slab computation honours the propagated FY
     (``_compute_tax`` was hardcoded to FY2025-26 and ignored ``self._fy``).
  4. Optimizer → builders → validator receive the filing FY end-to-end.

Several of these tests FAIL under the pre-fix implementation and pass now.
"""

from decimal import Decimal

import pytest
from fastapi import HTTPException

from src.api.routes import _resolve_financial_year
from src.builders.itr1 import ITR1Builder
from src.builders.itr_json_builder import ITRJSONBuilder
from src.builders.validator import ITRValidator
from src.engine.regime_optimizer_v2 import RegimeOptimizerV2
from src.engine.rules.config import FY2024_25, FY2025_26
from src.models.financial_year import FinancialYear
from src.models.tax import ClassifiedCGData, UnifiedTaxData
from src.utils.session import Session
from tests.factories import make_form16_data, make_user_answers


# ── 1. Assessment year → financial year mapping ─────────────────────

class TestAssessmentYearToFY:
    """FinancialYear.from_assessment_year maps AY → FY correctly."""

    def test_ay_2026_27_maps_to_fy_2025_26(self):
        fy = FinancialYear.from_assessment_year("2026-27")
        assert fy.label == "FY2025-26"
        assert fy.assessment_year == "2026-27"
        assert (fy.start_year, fy.end_year) == (2025, 2026)

    def test_ay_2025_26_maps_to_fy_2024_25(self):
        fy = FinancialYear.from_assessment_year("2025-26")
        assert fy.label == "FY2024-25"
        assert fy.assessment_year == "2025-26"
        assert (fy.start_year, fy.end_year) == (2024, 2025)

    def test_four_digit_ay_form_accepted(self):
        assert FinancialYear.from_assessment_year("2026-2027").label == "FY2025-26"

    def test_assessment_year_differs_from_from_string(self):
        # from_string("2026-27") means FY2026-27; the AY '2026-27' means FY2025-26.
        assert FinancialYear.from_assessment_year("2026-27") != FinancialYear.from_string("2026-27")

    def test_malformed_ay_rejected(self):
        for bad in ("", "2026", "2026-2028", "not-a-year"):
            with pytest.raises(ValueError):
                FinancialYear.from_assessment_year(bad)


# ── 2. Filing-year resolution from Form 16 (no silent fallback) ─────

class TestResolveFilingYear:
    """routes._resolve_financial_year derives FY from Form 16 assessment year."""

    @staticmethod
    def _session(assessment_year: str) -> Session:
        session = Session(session_id="test", pan="ABCDE1234F", dob="01011990")
        session.form16 = make_form16_data(assessment_year=assessment_year)
        return session

    def test_fy_2024_25_from_form16(self):
        # FAILS pre-fix: no resolver existed; the audit context hardcoded FY2025-26.
        fy = _resolve_financial_year(self._session("2025-26"))
        assert fy.label == "FY2024-25"
        assert fy == FY2024_25

    def test_fy_2025_26_from_form16(self):
        fy = _resolve_financial_year(self._session("2026-27"))
        assert fy.label == "FY2025-26"
        assert fy == FY2025_26

    def test_missing_assessment_year_rejected_not_silent_default(self):
        with pytest.raises(HTTPException) as exc:
            _resolve_financial_year(self._session(""))
        assert exc.value.status_code == 400

    def test_malformed_assessment_year_rejected(self):
        with pytest.raises(HTTPException) as exc:
            _resolve_financial_year(self._session("garbage"))
        assert exc.value.status_code == 400

    def test_caches_resolved_year_on_session(self):
        session = self._session("2025-26")
        fy = _resolve_financial_year(session)
        assert session.financial_year is fy
        assert _resolve_financial_year(session) is fy


# ── 3. ITR-1 slab computation honours the propagated FY ─────────────

class TestITR1BuilderFYPropagation:
    """ITR-1 _compute_tax uses self._fy, not a hardcoded FY2025-26."""

    def test_compute_tax_uses_fy_2024_25_slabs(self):
        # New-regime slab tax on ₹15,00,000:
        #   FY2024-25: 3L@0 + 4L@5 + 3L@10 + 2L@15 + 3L@20 = ₹1,40,000
        #   FY2025-26: 4L@0 + 4L@5 + 4L@10 + 3L@15           = ₹1,05,000
        # Pre-fix _compute_tax hardcoded FY2025-26 → returned ₹1,05,000 here.
        builder = ITR1Builder(financial_year=FY2024_25)
        slab_tax, _, _ = builder._compute_tax(Decimal("1500000"), True)
        assert slab_tax == Decimal("140000")

    def test_compute_tax_default_still_fy_2025_26(self):
        builder = ITR1Builder()
        slab_tax, _, _ = builder._compute_tax(Decimal("1500000"), True)
        assert slab_tax == Decimal("105000")

    def test_compute_tax_differs_between_years(self):
        b24 = ITR1Builder(financial_year=FY2024_25)
        b25 = ITR1Builder(financial_year=FY2025_26)
        assert (
            b24._compute_tax(Decimal("1500000"), True)[0]
            != b25._compute_tax(Decimal("1500000"), True)[0]
        )


# ── 4. Optimizer → builders → validator receive the filing FY ───────

class TestEndToEndFYPropagation:
    """The resolved FY flows through optimizer, builders, and validator."""

    def test_optimizer_and_builders_consistent_with_resolved_fy(self):
        # Form 16 AY '2025-26' ⇒ FY2024-25.
        session = Session(session_id="test", pan="ABCDE1234F", dob="01011990")
        session.form16 = make_form16_data(
            assessment_year="2025-26", salary=Decimal("1500000"), regime_new=True,
        )
        fy = _resolve_financial_year(session)
        assert fy == FY2024_25

        result = RegimeOptimizerV2().optimize(
            form16=session.form16,
            classified_cg=ClassifiedCGData(),
            answers=make_user_answers(),
            financial_year=fy,
        )
        # Optimizer breakdown records the propagated FY.
        assert result.new_breakdown["financial_year"] == "FY2024-25"

        # ITR-2 builder emits the matching assessment year.
        unified = session.unified_data
        unified.regime_result = result
        unified.recommended_regime = result.recommended
        itr2 = ITRJSONBuilder(financial_year=fy).build(unified)
        assert itr2["PartA_GeneralInfo"]["AssessmentYear"] == "2025-26"

    def test_itr1_builder_assessment_year_from_propagated_fy(self):
        builder = ITR1Builder(financial_year=FY2024_25)
        out = builder.build(UnifiedTaxData())
        assert out["PartA_GeneralInfo"]["AssessmentYear"] == "2025-26"

    def test_validator_receives_propagated_fy(self):
        v24 = ITRValidator(financial_year=FY2024_25)
        v25 = ITRValidator(financial_year=FY2025_26)
        assert v24._config.financial_year.label == "FY2024-25"
        assert v25._config.financial_year.label == "FY2025-26"
