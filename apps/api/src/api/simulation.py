"""Tax Simulation API — What-if scenario engine.

Enables users to explore:
  - "What if I invest ₹X more in NPS?"
  - "What if my salary increases by 10%?"
  - "What if I sell property this year vs next year?"
  - "What if I prepay my home loan?"
  - "What if I switch from Old to New Regime?"
  - "What if I claim HRA vs LTA?"

Each simulation runs the full tax engine with modified parameters
and returns comparison: original vs simulated side-by-side.
"""

from decimal import Decimal
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.auth.jwt import get_current_user
from src.engine.regime_optimizer_v2 import RegimeOptimizerV2
from src.engine.recommendation_engine import RecommendationEngine
from src.models.tax import UserAnswers, ClassifiedCGData

router = APIRouter(prefix="/api/v1/tax", tags=["Tax Simulation"])


class SimulationRequest(BaseModel):
    """What-if scenario parameters. Only changed fields need to be provided."""

    # Income changes
    salary_increase_pct: float = 0.0          # +10 means +10% salary
    bonus_additional: int = 0                  # Extra bonus amount
    capital_gains_additional: int = 0          # Additional CG this year

    # Deduction changes (Old Regime)
    nps_additional: int = 0                    # Extra NPS 80CCD(1B)
    elss_investment: int = 0                   # ELSS under 80C
    health_insurance_additional: int = 0       # Extra 80D premium
    home_loan_prepay: int = 0                  # Reduction in loan → less interest

    # Rent changes
    rent_increase: int = 0                     # Monthly rent increase
    move_to_metro: bool = False

    # Regime switch
    force_regime: str = ""                     # "old" or "new" — forces regime
    defer_sale_to_next_year: bool = False      # Defer CG to next FY


class SimulationResult(BaseModel):
    """Side-by-side comparison of original vs simulated tax."""

    # Summary
    original_tax: int = 0
    simulated_tax: int = 0
    tax_difference: int = 0                     # Negative = you save tax
    recommended_regime: str = ""

    # Original breakdown (from current session)
    original_breakdown: dict = Field(default_factory=dict)

    # Simulated breakdown
    simulated_breakdown: dict = Field(default_factory=dict)

    # What changed
    changes_applied: list[str] = Field(default_factory=list)

    # Recommendation
    recommendation: str = ""
    actionable_items: list[dict] = Field(default_factory=list)


@router.post("/simulate", response_model=SimulationResult)
async def simulate_tax_scenario(
    body: SimulationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Run a what-if tax simulation.

    Provide any combination of scenario parameters. The engine
    computes both the original and simulated tax, compares them,
    and recommends actions.

    Example request:
      {"nps_additional": 50000, "force_regime": "old"}
      → Shows how investing ₹50K in NPS under Old Regime affects tax.
    """
    # This endpoint requires an active session with Form 16 data
    # In production, fetch session data from DB/session manager
    # For now, return a helpful error
    raise HTTPException(
        status_code=501,
        detail="Simulation requires an active filing session. "
               "Start a filing first at POST /api/v1/upload, then call "
               "POST /api/v1/tax/simulate/{session_id}"
    )


@router.post("/simulate/{session_id}", response_model=SimulationResult)
async def simulate_with_session(
    session_id: str,
    body: SimulationRequest,
):
    """Run simulation using an active filing session's data."""
    from src.utils.session import session_manager

    session = session_manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    if not session.form16:
        raise HTTPException(status_code=400, detail="Upload Form 16 first.")

    optimizer = RegimeOptimizerV2()

    # ── ORIGINAL computation ──
    savings_interest = session.ais.total_savings_interest if session.ais else Decimal("0")
    other_interest = Decimal("0")
    if session.ais:
        other_interest = max(Decimal("0"),
            (session.ais.total_tds_interest or Decimal("0")) - savings_interest)

    original = optimizer.optimize(
        form16=session.form16,
        classified_cg=session.classified_cg or ClassifiedCGData(),
        answers=session.user_answers or UserAnswers(),
        savings_interest=savings_interest,
        other_interest=other_interest,
    )

    # ── SIMULATED computation ──
    # Apply scenario modifications to a copy of Form 16 data
    import copy
    sim_form16 = copy.deepcopy(session.form16)
    sim_answers = copy.deepcopy(session.user_answers or UserAnswers())
    changes = []

    # Salary change
    if body.salary_increase_pct != 0:
        factor = Decimal(str(1 + body.salary_increase_pct / 100))
        sim_form16.part_b.salary_171 *= factor
        sim_form16.part_b.total_gross_salary *= factor
        sim_form16.part_b.income_under_head_salaries *= factor
        changes.append(f"Salary {'+' if body.salary_increase_pct > 0 else ''}"
                       f"{body.salary_increase_pct:.0f}%")

    # Bonus
    if body.bonus_additional > 0:
        sim_form16.part_b.salary_171 += Decimal(str(body.bonus_additional))
        sim_form16.part_b.total_gross_salary += Decimal(str(body.bonus_additional))
        changes.append(f"Bonus +₹{body.bonus_additional:,}")

    # NPS
    if body.nps_additional > 0:
        if sim_answers.has_additional_80c:
            current = sim_answers.additional_80c_breakup.get("nps_own", Decimal("0"))
            sim_answers.additional_80c_breakup["nps_own"] = (
                Decimal(str(current)) + Decimal(str(body.nps_additional))
            )
        else:
            sim_answers.has_additional_80c = True
            sim_answers.additional_80c_breakup = {"nps_own": Decimal(str(body.nps_additional))}
        changes.append(f"NPS 80CCD(1B) +₹{body.nps_additional:,}")

    # ELSS
    if body.elss_investment > 0:
        if sim_answers.has_additional_80c:
            current = sim_answers.additional_80c_breakup.get("elss", Decimal("0"))
            sim_answers.additional_80c_breakup["elss"] = Decimal(str(current)) + Decimal(str(body.elss_investment))
        else:
            sim_answers.has_additional_80c = True
            sim_answers.additional_80c_breakup = {"elss": Decimal(str(body.elss_investment))}
        changes.append(f"ELSS 80C +₹{body.elss_investment:,}")

    # Health insurance
    if body.health_insurance_additional > 0:
        sim_answers.has_health_insurance = True
        sim_answers.health_premium_self = (
            (sim_answers.health_premium_self or Decimal("0"))
            + Decimal(str(body.health_insurance_additional))
        )
        changes.append(f"80D Health Insurance +₹{body.health_insurance_additional:,}")

    # Home loan prepay (reduces interest)
    if body.home_loan_prepay > 0:
        current_interest = sim_answers.home_loan_interest or Decimal("0")
        # Rough estimate: 10% of prepay = reduced interest
        interest_reduction = Decimal(str(body.home_loan_prepay)) * Decimal("0.10")
        sim_answers.home_loan_interest = max(Decimal("0"), current_interest - interest_reduction)
        changes.append(f"Home Loan Prepay ₹{body.home_loan_prepay:,} → Interest -₹{int(interest_reduction):,}")

    # Rent increase
    if body.rent_increase > 0:
        sim_answers.pays_rent = True
        sim_answers.rent_per_month = (
            (sim_answers.rent_per_month or Decimal("0"))
            + Decimal(str(body.rent_increase))
        )
        changes.append(f"Rent +₹{body.rent_increase:,}/mo")

    if body.move_to_metro:
        sim_answers.rent_city_metro = True
        changes.append("City → Metro (HRA now 50%)")

    # Defer CG
    sim_cg = session.classified_cg or ClassifiedCGData()
    if body.defer_sale_to_next_year:
        sim_cg = ClassifiedCGData()  # Zero out CG for simulation
        changes.append("Capital gains deferred to next FY")

    # Run simulation
    sim_rent = sim_answers.rent_per_month if sim_answers.pays_rent else Decimal("0")
    simulated = optimizer.optimize(
        form16=sim_form16,
        classified_cg=sim_cg,
        answers=sim_answers,
        savings_interest=savings_interest,
        other_interest=other_interest,
        rent_paid_monthly=sim_rent,
        metro_city=sim_answers.rent_city_metro,
    )

    # ── Comparison ──
    orig_tax = int(original.new_tax if original.recommended.value == "new" else original.old_tax)
    sim_tax = int(simulated.new_tax if simulated.recommended.value == "new" else simulated.old_tax)

    # Get recommendation
    rec_engine = RecommendationEngine()
    orig_bd = original.new_breakdown if original.recommended.value == "new" else original.old_breakdown
    sim_bd = simulated.new_breakdown if simulated.recommended.value == "new" else simulated.old_breakdown

    if len(changes) == 0:
        recommendation = "No changes applied. Add at least one scenario parameter."
    elif sim_tax < orig_tax:
        recommendation = (
            f"Great news! These changes would SAVE you ₹{orig_tax - sim_tax:,} in tax. "
            f"Consider implementing {'this change' if len(changes) == 1 else 'these changes'} "
            f"before the filing deadline."
        )
    elif sim_tax > orig_tax:
        recommendation = (
            f"These changes would INCREASE your tax by ₹{sim_tax - orig_tax:,}. "
            f"If possible, avoid or defer {'this change' if len(changes) == 1 else 'these changes'}."
        )
    else:
        recommendation = "These changes would not affect your tax liability."

    return SimulationResult(
        original_tax=orig_tax,
        simulated_tax=sim_tax,
        tax_difference=sim_tax - orig_tax,
        recommended_regime=simulated.recommended.value,
        original_breakdown=orig_bd,
        simulated_breakdown=sim_bd,
        changes_applied=changes,
        recommendation=recommendation,
        actionable_items=[
            {"action": c, "tax_impact": sim_tax - orig_tax}
            for c in changes
        ],
    )
