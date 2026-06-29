"""End-to-end test with real Form 16 and AIS PDFs from actual FY 2025-26 filing.

Known correct numbers (verified against ITR portal submission):
- Salary (gross): ₹18,71,602
- Income under head salaries: ₹17,96,602
- TDS by employer: ₹1,55,738
- Regime: New (115BAC)
- 80CCD(2) Employer NPS: ₹47,869
- Equity MF LTCG: ₹58,273 (10 Quant ELSS redemptions)
- Non-equity STCG: ₹5,194 (4 ETF sales)
- Savings bank interest: ₹757
- Aggregate Total Income: ₹17,54,687
- Tax (incl. cess): ₹1,56,974
- Self-Assessment Tax: ₹1,240
- Balance Payable: ₹0
"""

import json
import sys
import os
from datetime import date
from decimal import Decimal
from pathlib import Path

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parsers.form16_parser import Form16Parser
from src.parsers.ais_parser import AISParser
from src.engine.classifier import ClassificationEngine
from src.engine.regime_optimizer import RegimeOptimizer
from src.models.tax import UserAnswers
from src.builders.itr_json_builder import ITRJSONBuilder
from src.builders.validator import ITRValidator

# ── Test Configuration ──────────────────────────────────────────────
PAN = "CFFPM4503N"
DOB = "25041995"
FORM16_PASSWORD = "CFFPM4503N"
FORM16_PATH = Path(r"C:\Users\ameya\OneDrive\Documents\F16_FY2025-26_192415.pdf")
AIS_PATH = Path(r"C:\Users\ameya\Downloads\XXXPM4503X_2025-26_AIS.pdf")

# Known correct values from our manual filing
EXPECTED = {
    "gross_salary": Decimal("1871602"),
    "income_salaries": Decimal("1796602"),
    "employer_tds": Decimal("155738"),
    "regime": "new",
    "nps_employer": Decimal("47869"),
    "ltcg_112a": Decimal("58273"),  # 10 Quant ELSS
    "stcg_other": Decimal("5194"),  # 4 ETF sales
    "savings_interest": Decimal("757"),
    "total_income": Decimal("1754687"),
    "tax_with_cess": Decimal("156974"),
    "self_assessment_tax": Decimal("1240"),
    "balance_payable": Decimal("0"),
}


def test_form16_parsing():
    """Test Form 16 PDF parsing against known values."""
    print("\n" + "=" * 60)
    print("TEST 1: Form 16 Parsing")
    print("=" * 60)

    parser = Form16Parser()
    form16 = parser.parse(FORM16_PATH, password=FORM16_PASSWORD)

    # Part A checks
    assert form16.part_a.employee_pan == PAN, f"PAN mismatch: {form16.part_a.employee_pan}"
    print(f"✅ PAN: {form16.part_a.employee_pan}")

    assert form16.part_a.employer_tan == "BLRA04654G", f"TAN mismatch: {form16.part_a.employer_tan}"
    print(f"✅ TAN: {form16.part_a.employer_tan}")

    assert "APPLIED MATERIALS" in form16.part_a.employer_name.upper(), f"Employer: {form16.part_a.employer_name}"
    print(f"✅ Employer: {form16.part_a.employer_name}")

    # TDS
    tds = form16.part_a.total_tds_deducted
    print(f"   TDS Deducted: ₹{tds:,.0f} (expected: ₹{EXPECTED['employer_tds']:,.0f})")
    if tds == EXPECTED["employer_tds"]:
        print("✅ TDS matches exactly")
    else:
        print(f"⚠️  TDS differs by ₹{abs(tds - EXPECTED['employer_tds']):,.0f}")

    # Part B checks
    gross = form16.part_b.salary_171
    print(f"   Gross Salary (17(1)): ₹{gross:,.0f} (expected: ₹{EXPECTED['gross_salary']:,.0f})")
    if gross == EXPECTED["gross_salary"]:
        print("✅ Gross Salary matches exactly")
    else:
        print(f"⚠️  Gross Salary differs by ₹{abs(gross - EXPECTED['gross_salary']):,.0f}")

    inc_sal = form16.part_b.income_under_head_salaries
    print(f"   Income under Head Salaries: ₹{inc_sal:,.0f} (expected: ₹{EXPECTED['income_salaries']:,.0f})")
    if inc_sal == EXPECTED["income_salaries"]:
        print("✅ Income Salaries matches exactly")
    else:
        print(f"⚠️  Income Salaries differs by ₹{abs(inc_sal - EXPECTED['income_salaries']):,.0f}")

    # Regime
    regime = form16.regime.value
    print(f"   Regime from Form 16: {regime} (expected: {EXPECTED['regime']})")
    assert regime == EXPECTED["regime"], f"Regime mismatch: {regime}"
    print("✅ Regime matches")

    # 80CCD(2)
    nps = form16.part_b.chapter_vi_a.sec80ccd2
    print(f"   80CCD(2) Employer NPS: ₹{nps:,.0f} (expected: ₹{EXPECTED['nps_employer']:,.0f})")
    if nps == EXPECTED["nps_employer"]:
        print("✅ 80CCD(2) matches exactly")
    else:
        print(f"⚠️  80CCD(2) differs by ₹{abs(nps - EXPECTED['nps_employer']):,.0f}")

    # Standard Deduction
    print(f"   Standard Deduction: ₹{form16.part_b.std_deduction_16ia:,.0f} (expected ₹75,000 for new regime)")
    if form16.part_b.std_deduction_16ia == Decimal("75000"):
        print("✅ Standard Deduction = ₹75,000 (new regime)")

    return form16


def test_ais_parsing():
    """Test AIS PDF parsing."""
    print("\n" + "=" * 60)
    print("TEST 2: AIS Parsing")
    print("=" * 60)

    parser = AISParser()
    ais = parser.parse(AIS_PATH, PAN, DOB)

    print(f"✅ PAN: {ais.pan}")
    print(f"✅ Name: {ais.name}")

    # Equity MF sales
    emf_count = len(ais.equity_mf_sales)
    print(f"   Equity MF Sales: {emf_count} entries (expected: 10)")
    if emf_count >= 1:
        total_emf_consideration = sum((s.sale_consideration for s in ais.equity_mf_sales), Decimal("0"))
        total_emf_cost = sum((s.cost_of_acquisition for s in ais.equity_mf_sales), Decimal("0"))
        total_emf_gain = total_emf_consideration - total_emf_cost
        print(f"   Equity MF Total Gain: ₹{total_emf_gain:,.0f} (expected: ₹{EXPECTED['ltcg_112a']:,.0f})")
        if abs(total_emf_gain - EXPECTED["ltcg_112a"]) <= 1:
            print("✅ Equity MF LTCG matches")
        else:
            print(f"⚠️  Equity MF LTCG differs by ₹{abs(total_emf_gain - EXPECTED['ltcg_112a']):,.0f}")

    # Other unit sales (ETF)
    otu_count = len(ais.other_unit_sales)
    print(f"   Other Unit Sales (ETF): {otu_count} entries (expected: 4)")
    if otu_count >= 1:
        total_otu_consideration = sum((s.sale_consideration for s in ais.other_unit_sales), Decimal("0"))
        total_otu_cost = sum((s.cost_of_acquisition for s in ais.other_unit_sales), Decimal("0"))
        total_otu_gain = total_otu_consideration - total_otu_cost
        print(f"   ETF Total Gain: ₹{total_otu_gain:,.0f} (expected: ₹{EXPECTED['stcg_other']:,.0f})")
        if abs(total_otu_gain - EXPECTED["stcg_other"]) <= 1:
            print("✅ ETF STCG matches")
        else:
            print(f"⚠️  ETF STCG differs by ₹{abs(total_otu_gain - EXPECTED['stcg_other']):,.0f}")

    # Interest
    total_int = ais.total_savings_interest
    print(f"   Savings Interest: ₹{total_int:,.0f} (expected: ₹{EXPECTED['savings_interest']:,.0f})")
    if total_int == EXPECTED["savings_interest"]:
        print("✅ Savings Interest matches exactly")
    else:
        print(f"⚠️  Interest differs by ₹{abs(total_int - EXPECTED['savings_interest']):,.0f}")

    return ais


def test_classification(ais):
    """Test capital gains classification."""
    print("\n" + "=" * 60)
    print("TEST 3: Capital Gains Classification")
    print("=" * 60)

    engine = ClassificationEngine()
    classified = engine.classify(ais.equity_mf_sales, ais.other_unit_sales)

    print(f"   Schedule 112A (Equity LTCG): {len(classified.schedule_112a)} entries")
    print(f"   Schedule CG A5 (Non-equity STCG): {len(classified.cg_a5_stcg_app_rate)} entries")
    print(f"   Schedule CG A2 (Equity STCG 15%): {len(classified.cg_a2_stcg_111a)} entries")
    print(f"   Schedule CG B8 (Non-equity LTCG): {len(classified.cg_b8_ltcg_other)} entries")

    total_112a_gain = sum((e.gain for e in classified.schedule_112a), Decimal("0"))
    total_a5_gain = sum((e.gain for e in classified.cg_a5_stcg_app_rate), Decimal("0"))

    print(f"   112A Total Gain: ₹{total_112a_gain:,.0f}")
    print(f"   A5 Total Gain: ₹{total_a5_gain:,.0f}")

    # Apply 112A exemption
    classified = engine.apply_112a_exemption(classified)
    taxable_112a = sum((e.gain_after_exemption for e in classified.schedule_112a), Decimal("0"))
    print(f"   112A Taxable (after ₹1.25L exemption): ₹{taxable_112a:,.0f}")

    tax_summary = engine.get_tax_summary(classified)
    print(f"   112A Tax: ₹{tax_summary['ltcg_112a_tax']:,.0f}")
    print("✅ Classification complete")

    return classified


def test_regime_optimizer(form16, classified):
    """Test regime optimization."""
    print("\n" + "=" * 60)
    print("TEST 4: Regime Optimization")
    print("=" * 60)

    optimizer = RegimeOptimizer()
    answers = UserAnswers()  # Default: no to everything

    result = optimizer.optimize(
        form16=form16,
        classified_cg=classified,
        answers=answers,
        savings_interest=Decimal("757"),
        other_interest=Decimal("0"),
    )

    print(f"   Old Regime Tax: ₹{result.old_tax:,.0f}")
    print(f"   New Regime Tax: ₹{result.new_tax:,.0f}")
    print(f"   Recommended: {result.recommended.value.upper()}")
    print(f"   Savings: ₹{result.savings:,.0f}")

    assert result.recommended.value == "new", f"Expected NEW regime, got {result.recommended.value}"
    print("✅ Recommends New Regime (correct)")

    expected_tax = EXPECTED["tax_with_cess"]
    actual_tax = result.new_tax
    print(f"   Tax (new regime): ₹{actual_tax:,.0f} (expected: ₹{expected_tax:,.0f})")
    if abs(actual_tax - expected_tax) <= 2:
        print("✅ Tax matches within ₹2")
    else:
        print(f"⚠️  Tax differs by ₹{abs(actual_tax - expected_tax):,.0f} — check slab calculation")

    return result


def test_json_builder(form16, ais, classified, regime_result):
    """Test ITR JSON generation."""
    print("\n" + "=" * 60)
    print("TEST 5: ITR JSON Builder")
    print("=" * 60)

    from src.models.tax import UnifiedTaxData

    unified = UnifiedTaxData(
        pan=PAN,
        dob=date(1995, 4, 25),
        form16=form16,
        ais=ais,
        user_answers=UserAnswers(),
        capital_gains=classified,
        regime_result=regime_result,
        recommended_regime=regime_result.recommended,
    )

    builder = ITRJSONBuilder()
    itr_json = builder.build(unified)

    # Check key fields
    assert "PartA_GeneralInfo" in itr_json, "Missing PartA_GeneralInfo"
    print("✅ PartA_GeneralInfo present")

    assert "ScheduleS" in itr_json, "Missing ScheduleS"
    print("✅ ScheduleS present")

    sched_s = itr_json["ScheduleS"]
    assert sched_s.get("SalaryIncome"), "No salary income entries"
    print("✅ Salary income entry exists")

    # 112A
    sched_112a = itr_json.get("Schedule112A", {})
    if sched_112a:
        secondary_add = sched_112a.get("Securities", [{}])[0].get("SecondaryAdd", "")
        if secondary_add == "":
            print("⚠️  SecondaryAdd is empty — portal will reject!")
        else:
            print(f"✅ SecondaryAdd = '{secondary_add}'")

    # Schedule CG
    sched_cg = itr_json.get("ScheduleCG", {})
    if sched_cg:
        print(f"✅ ScheduleCG present with sections: {list(sched_cg.keys())}")

    # Tax Paid
    tax_paid = itr_json.get("ScheduleTaxPaid", {})
    if tax_paid:
        tds = Decimal(tax_paid.get("TDS", {}).get("SalaryTDS", "0"))
        print(f"   Salary TDS: ₹{tds:,.0f} (expected: ₹{EXPECTED['employer_tds']:,.0f})")

        balance = Decimal(tax_paid.get("BalancePayable", "0"))
        print(f"   Balance Payable: ₹{balance:,.0f} (expected: ₹{EXPECTED['balance_payable']:,.0f})")

    # Save JSON for inspection
    output_path = Path(__file__).parent / "test_output.json"
    with open(output_path, "w") as f:
        json.dump(itr_json, f, indent=2, default=str)
    print(f"✅ Full JSON saved to: {output_path}")

    return itr_json


def test_validator(itr_json):
    """Test JSON validation."""
    print("\n" + "=" * 60)
    print("TEST 6: JSON Validation")
    print("=" * 60)

    validator = ITRValidator()
    report = validator.validate(itr_json)

    print(f"   Passed: {report.passed}, Failed: {report.failed}, Warnings: {report.warnings}")

    for r in report.results:
        icon = "✅" if r.passed else ("⚠️" if r.severity == "warning" else "❌")
        print(f"   {icon} {r.check_name}: {r.message}")

    if report.can_file:
        print("✅ JSON passes validation — ready to upload!")
    else:
        print("❌ JSON has blocking errors — needs fixes before upload")

    return report


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("TaxStox — End-to-End Test with Real Data")
    print("FY 2025-26 | PAN: CFFPM4503N")
    print("=" * 60)

    try:
        form16 = test_form16_parsing()
    except Exception as e:
        print(f"❌ Form 16 parsing FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    try:
        if AIS_PATH.exists():
            ais = test_ais_parsing()
        else:
            print(f"\n⚠️  AIS PDF not found at {AIS_PATH} — skipping AIS test")
            ais = None
    except Exception as e:
        print(f"❌ AIS parsing FAILED: {e}")
        import traceback
        traceback.print_exc()
        ais = None  # Continue with partial data

    try:
        if ais:
            classified = test_classification(ais)
        else:
            print("\n⚠️  Skipping classification (no AIS data)")
            from src.models.tax import ClassifiedCGData
            classified = ClassifiedCGData()
    except Exception as e:
        print(f"❌ Classification FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    try:
        regime_result = test_regime_optimizer(form16, classified)
    except Exception as e:
        print(f"❌ Regime optimization FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    try:
        itr_json = test_json_builder(form16, ais, classified, regime_result)
    except Exception as e:
        print(f"❌ JSON builder FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    try:
        test_validator(itr_json)
    except Exception as e:
        print(f"❌ Validation FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
