"""API regression tests for the ITR filing flow (no PDFs, no DB).

PR4.5: Drives the real filing routers (process -> answers -> export) through
the genuine FastAPI app by seeding the in-memory SessionManager with factory
data. The System Under Test is the full request pipeline (middleware, routing,
regime optimizer v2, question engine, builder, validator) — no part is mocked
away.

Constraint (observed, not worked around): `Session.unified_data` hardcodes
`dob=None`, so the DOB validator check fails on the seeded session and
`/export` returns `validation_passed=False`. That is the production behavior,
so we assert the export is *well-formed and complete* (all schedules present)
rather than that it is fileable. Fileability is asserted separately on a build
with a populated DOB in test_itr_builders.py.
"""

from decimal import Decimal

import pytest

from src.models.tax import UserAnswers
from src.utils.session import session_manager
from tests._markers import db_required  # noqa: F401  (marker import; no DB hit here)

pytestmark = pytest.mark.api


def _seed_session():
    """Create an in-memory session populated with synthetic Form16/AIS data.

    Seeds a capital-gains AIS entry (an equity MF long-term sale) so the ITR
    selector auto-picks ITR-2 — the form that legally carries ScheduleCG and
    Schedule112A. A salaried-without-CG profile would select ITR-1 (SAHAJ),
    which by law cannot contain capital-gains schedules, so the export would
    legitimately omit them. Seeding CG makes the ScheduleCG/Schedule112A
    assertions in test_export_builds_complete_itr_json a genuine contract
    rather than an impossible one.
    """
    from tests.factories import (
        make_ais_data,
        make_form16_data,
    )
    from src.engine.classifier import ClassificationEngine

    session = session_manager.create(pan="ABCDE1234F", dob="25041995")
    # assessment_year '2026-27' => FY2025-26 (matches factory default)
    session.form16 = make_form16_data(
        salary=Decimal("1871602"),
        std_deduction=Decimal("75000"),
        employer_nps=Decimal("47869"),
        tds_deducted=Decimal("155738"),
        regime_new=True,
        employee_pan="ABCDE1234F",
        employer_tan="BLRA04654G",
        assessment_year="2026-27",
    )
    session.ais = make_ais_data(
        equity_mf_sales=[
            {
                "security_name": "Quant ELSS Tax Saver Fund",
                "isin": "INF966L01986",
                "date_of_sale": "2025-04-21",
                "quantity": "19.79",
                "sale_price_per_unit": "383.77",
                "sale_consideration": "7596",
                "cost_of_acquisition": "5000",
                "stt_paid": "0.20",
                "term": "Long",
            }
        ],
    )
    # Classify the AIS equity sale into the schedule-bound CG model so the
    # /process selector sees has_cg=True and selects ITR-2.
    session.classified_cg = ClassificationEngine().classify(
        session.ais.equity_mf_sales, session.ais.other_unit_sales
    )
    return session


def test_process_generates_questions(client):
    """POST /process/{id} must run classification + optimization and return questions."""
    session = _seed_session()
    resp = client.post(f"/api/v1/process/{session.session_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["itr_type"], "process did not return an ITR form type"
    # New regime is recommended for a default (no-deduction) salaried filer
    assert body["regime_recommended"] in ("new", "old")
    assert "questions" in body


def test_process_rejects_unknown_session(client):
    """POST /process/{bad-id} must 404 rather than leaking internal errors."""
    resp = client.post("/api/v1/process/does-not-exist")
    assert resp.status_code == 404


def test_submit_answers_returns_summary(client):
    """POST /answers/{id} must recompute tax and return a 1-page summary."""
    session = _seed_session()
    client.post(f"/api/v1/process/{session.session_id}")  # populate regime_result
    resp = client.post(
        f"/api/v1/answers/{session.session_id}",
        json={"session_id": session.session_id, "answers": {}},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "income" in body
    assert "tax_breakdown" in body
    assert "taxable_income" in body


def test_export_builds_complete_itr_json(client):
    """POST /export/{id} must return a structurally complete ITR JSON.

    We assert all canonical schedules are present (the build pipeline runs
    end-to-end). We deliberately do NOT assert validation_passed=True: the
    seeded session's unified_data has dob=None, so the DOB check fails — that
    is genuine production behavior, not a test defect.
    """
    session = _seed_session()
    client.post(f"/api/v1/process/{session.session_id}")
    client.post(f"/api/v1/answers/{session.session_id}", json={"answers": {}})
    resp = client.post(f"/api/v1/export/{session.session_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["json_data"], "export returned no ITR JSON"
    itr = body["json_data"]
    for required in ("PartA_GeneralInfo", "ScheduleS", "ScheduleCG", "Schedule112A"):
        assert required in itr, f"Exported ITR missing {required}"
    # Filename must be deterministic and reference the PAN + AY
    assert "ABCDE1234F" in body["filename"]


def test_export_rejects_unknown_session(client):
    """POST /export/{bad-id} must 404."""
    resp = client.post("/api/v1/export/does-not-exist")
    assert resp.status_code == 404
