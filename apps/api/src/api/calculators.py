"""Standalone tax calculators API — ClearTax-style tools."""

from decimal import Decimal

from fastapi import APIRouter, Query
from src.engine.regime_optimizer import RegimeOptimizer

router = APIRouter(prefix="/api/v1/calculator", tags=["Calculators"])


# ── Old Regime slab tax ─────────────────────────────────────────────

def slab_tax_old(income: Decimal) -> Decimal:
    tax = Decimal("0")
    r = income
    if r > Decimal("1000000"):
        tax += (r - Decimal("1000000")) * Decimal("0.30")
        r = Decimal("1000000")
    if r > Decimal("500000"):
        tax += (r - Decimal("500000")) * Decimal("0.20")
        r = Decimal("500000")
    if r > Decimal("250000"):
        tax += (r - Decimal("250000")) * Decimal("0.05")
    # Rebate 87A
    if income <= Decimal("500000"):
        tax = min(tax, Decimal("12500"))
        tax = max(Decimal("0"), tax - Decimal("12500"))
    return tax.quantize(Decimal("1"))


# ── New Regime slab tax ─────────────────────────────────────────────

def slab_tax_new(income: Decimal) -> Decimal:
    tax = Decimal("0")
    r = income
    if r > Decimal("2400000"):
        tax += (r - Decimal("2400000")) * Decimal("0.30")
        r = Decimal("2400000")
    if r > Decimal("2000000"):
        tax += (r - Decimal("2000000")) * Decimal("0.25")
        r = Decimal("2000000")
    if r > Decimal("1600000"):
        tax += (r - Decimal("1600000")) * Decimal("0.20")
        r = Decimal("1600000")
    if r > Decimal("1200000"):
        tax += (r - Decimal("1200000")) * Decimal("0.15")
        r = Decimal("1200000")
    if r > Decimal("800000"):
        tax += (r - Decimal("800000")) * Decimal("0.10")
        r = Decimal("800000")
    if r > Decimal("400000"):
        tax += (r - Decimal("400000")) * Decimal("0.05")
    # Rebate 87A (new regime)
    if income <= Decimal("700000"):
        rebate = min(tax, Decimal("60000"))
        tax = max(Decimal("0"), tax - rebate)
    return tax.quantize(Decimal("1"))


def add_cess(tax: Decimal) -> Decimal:
    return (tax * Decimal("4") / Decimal("100")).quantize(Decimal("1"))


# ── Regime Comparison ───────────────────────────────────────────────

@router.get("/regime-compare")
async def regime_compare(
    salary: float = Query(..., description="Annual gross salary"),
    deductions_80c: float = Query(0, description="80C investments"),
    deductions_80d: float = Query(0, description="80D health insurance"),
    hra_exemption: float = Query(0, description="HRA exemption amount"),
    home_loan_interest: float = Query(0, description="Home loan interest (24b)"),
    nps_employer: float = Query(0, description="Employer NPS (80CCD2)"),
    other_income: float = Query(0, description="Other income (interest, etc.)"),
):
    """Compare tax under Old vs New regime with user-provided inputs."""
    gross = Decimal(str(salary))
    ded_80c = Decimal(str(deductions_80c))
    ded_80d = Decimal(str(deductions_80d))
    hra = Decimal(str(hra_exemption))
    home_int = Decimal(str(home_loan_interest))
    nps_emp = Decimal(str(nps_employer))
    other = Decimal(str(other_income))

    # ── Old Regime ──
    std_old = Decimal("50000")
    prof_tax = Decimal("2500")

    income_salary_old = max(Decimal("0"), gross - hra - std_old - prof_tax)
    # Home loan loss
    home_loss = min(home_int, Decimal("200000"))
    # Deductions
    total_ded_old = min(ded_80c, Decimal("150000")) + ded_80d + nps_emp
    # Taxable
    taxable_old = max(Decimal("0"), income_salary_old + other - home_loss - total_ded_old)

    tax_old_slab = slab_tax_old(taxable_old)
    cess_old = add_cess(tax_old_slab)
    total_old = tax_old_slab + cess_old

    # ── New Regime ──
    std_new = Decimal("75000")
    income_salary_new = max(Decimal("0"), gross - std_new)
    taxable_new = max(Decimal("0"), income_salary_new + other - nps_emp)

    tax_new_slab = slab_tax_new(taxable_new)
    cess_new = add_cess(tax_new_slab)
    total_new = tax_new_slab + cess_new

    recommended = "new" if total_new <= total_old else "old"
    savings = abs(total_old - total_new)

    return {
        "old_regime": {
            "gross_salary": str(gross),
            "exemptions": str(hra + std_old),
            "deductions": str(total_ded_old),
            "taxable_income": str(taxable_old),
            "tax": str(tax_old_slab),
            "cess": str(cess_old),
            "total_tax": str(total_old),
        },
        "new_regime": {
            "gross_salary": str(gross),
            "exemptions": str(std_new),
            "deductions": str(nps_emp),
            "taxable_income": str(taxable_new),
            "tax": str(tax_new_slab),
            "cess": str(cess_new),
            "total_tax": str(total_new),
        },
        "recommended": recommended,
        "savings": str(savings),
    }


# ── HRA Calculator ───────────────────────────────────────────────────

@router.get("/hra")
async def hra_calculator(
    basic_salary: float = Query(..., description="Monthly basic salary + DA"),
    hra_received: float = Query(..., description="Monthly HRA received"),
    rent_paid: float = Query(..., description="Monthly rent paid"),
    metro_city: bool = Query(True, description="Is it a metro city?"),
):
    """Calculate HRA exemption under Section 10(13A)."""
    basic = Decimal(str(basic_salary))
    hra = Decimal(str(hra_received))
    rent = Decimal(str(rent_paid))

    annual_basic = basic * Decimal("12")
    annual_hra = hra * Decimal("12")
    annual_rent = rent * Decimal("12")

    # HRA exemption = Minimum of:
    # 1. Actual HRA received
    # 2. Rent paid - 10% of basic
    # 3. 50% of basic (metro) or 40% of basic (non-metro)
    option1 = annual_hra
    option2 = annual_rent - (annual_basic * Decimal("0.10"))
    option3 = annual_basic * (Decimal("0.50") if metro_city else Decimal("0.40"))

    exemption = max(Decimal("0"), min(option1, max(Decimal("0"), option2), option3))

    return {
        "annual_basic": str(annual_basic),
        "annual_hra_received": str(annual_hra),
        "annual_rent_paid": str(annual_rent),
        "metro_city": metro_city,
        "calculation": {
            "actual_hra_received": str(option1),
            "rent_minus_10pct_basic": str(max(Decimal("0"), option2)),
            "pct_of_basic": f"{'50' if metro_city else '40'}% of basic = {option3}",
        },
        "hra_exemption": str(exemption),
        "taxable_hra": str(max(Decimal("0"), annual_hra - exemption)),
    }


# ── Capital Gains Tax Calculator ─────────────────────────────────────

@router.get("/capital-gains")
async def capital_gains_calculator(
    gain_type: str = Query(..., description="ltcg_equity, stcg_equity, ltcg_other, stcg_other"),
    gain_amount: float = Query(..., description="Total capital gain"),
):
    """Calculate tax on capital gains."""
    gain = Decimal(str(gain_amount))

    rates = {
        "ltcg_equity": {"rate": Decimal("0.125"), "exemption": Decimal("125000"), "label": "LTCG on Equity (112A) @ 12.5%"},
        "stcg_equity": {"rate": Decimal("0.15"), "exemption": Decimal("0"), "label": "STCG on Equity (111A) @ 15%"},
        "ltcg_other": {"rate": Decimal("0.125"), "exemption": Decimal("0"), "label": "LTCG on Other Assets @ 12.5%"},
        "stcg_other": {"rate": Decimal("0"), "exemption": Decimal("0"), "label": "STCG on Other Assets @ Slab Rate"},
    }

    info = rates.get(gain_type, rates["ltcg_equity"])

    if gain_type == "stcg_other":
        taxable = gain
        tax = Decimal("0")  # Added to slab income
        note = "STCG on other assets is taxed at your applicable slab rate."
    else:
        exemption = min(gain, info["exemption"])
        taxable = max(Decimal("0"), gain - exemption)
        tax = taxable * info["rate"]
        note = None

    return {
        "gain_type": info["label"],
        "total_gain": str(gain),
        "exemption": str(info["exemption"]) if info["exemption"] > 0 else "0",
        "taxable_gain": str(taxable) if gain_type != "stcg_other" else str(gain),
        "tax_rate": str(info["rate"]) if info["rate"] > 0 else "Slab Rate",
        "tax_amount": str(tax),
        "note": note,
    }


# ── Quick Tax Estimator ──────────────────────────────────────────────

@router.get("/quick-estimate")
async def quick_estimate(
    annual_income: float = Query(..., description="Total annual income"),
    regime: str = Query("new", description="old or new"),
):
    """Quick tax estimate — simple slab calculation."""
    income = Decimal(str(annual_income))

    if regime == "old":
        # Apply standard deduction ₹50,000
        taxable = max(Decimal("0"), income - Decimal("50000"))
        tax = slab_tax_old(taxable)
    else:
        # Apply standard deduction ₹75,000
        taxable = max(Decimal("0"), income - Decimal("75000"))
        tax = slab_tax_new(taxable)

    cess = add_cess(tax)
    total = tax + cess

    return {
        "annual_income": str(income),
        "regime": "Old Regime" if regime == "old" else "New Regime",
        "taxable_income": str(taxable),
        "tax": str(tax),
        "cess": str(cess),
        "total_tax": str(total),
        "monthly_equivalent": str((total / Decimal("12")).quantize(Decimal("1"))),
    }
