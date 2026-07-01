# 16 — Tax Optimization Engine

> **Parent:** [00-README.md](00-README.md) | **Prev:** [15 Prompt Engineering](15-prompt-engineering.md) | **Next:** [17 Recommendation Engine](17-recommendation-engine.md)

---

## Core Principle

> **The AI NEVER calculates taxes. The AI discovers opportunities and delegates all computation to the deterministic Tax Rule Engine (TRE).**

The Tax Optimization Engine consists of two layers:
1. **AI Discovery Layer** — Finds every legal tax-saving opportunity
2. **Deterministic Tax Rule Engine** — Computes exact tax liability for every scenario

---

## 1. Tax Rule Engine (TRE) — Deterministic Backend

### 1.1 TRE Architecture

```
                    ┌──────────────────────────┐
                    │    TAX RULE ENGINE (TRE)   │
                    │                            │
 Input:             │  ┌──────────────────────┐ │
 - Income profile   │  │   Income Aggregator   │ │
 - Deductions       │  │   (Gross → Taxable)   │ │
 - Exemptions       │  └─────────┬────────────┘ │
 - TDS/TCS/Adv Tax  │            │               │
 - Regime choice    │  ┌─────────▼────────────┐ │
                    │  │   Slab Applicator     │ │
 Output:            │  │   (Income → Tax)      │ │
 - Taxable income   │  └─────────┬────────────┘ │
 - Gross tax        │            │               │
 - Rebate (87A)     │  ┌─────────▼────────────┐ │
 - Surcharge        │  │   Surcharge + Cess    │ │
 - Health & Edu Cess│  │   Applicator          │ │
 - Interest (234A/B/C)│ └─────────┬────────────┘ │
 - Late fee (234F)  │            │               │
 - Net tax payable  │  ┌─────────▼────────────┐ │
 - Refund due       │  │   TDS/TCS Adjuster    │ │
                    │  └─────────┬────────────┘ │
                    │            │               │
                    │  ┌─────────▼────────────┐ │
                    │  │   Interest Calculator │ │
                    │  │   (234A, 234B, 234C)  │ │
                    │  └──────────────────────┘ │
                    └──────────────────────────┘
```

### 1.2 TRE API Contract

```typescript
// POST /api/tax-engine/compute
interface TaxComputationRequest {
  assessmentYear: string;           // "2026-27"
  regime: 'old' | 'new';
  taxpayerType: TaxpayerType;       // individual, senior_citizen, super_senior
  residenceStatus: ResidenceStatus; // resident, non_resident, rnor

  // Income Heads
  salary: {
    grossSalary: number;
    allowances: Allowance[];
    perquisites: Perquisite[];
    standardDeduction: number;      // ₹50,000 or ₹75,000
    professionTax: number;
    entertainmentAllowance?: number;
  };

  houseProperty: HousePropertyEntry[];

  businessProfession: {
    presumptiveIncome?: number;     // 44AD / 44ADA
    regularIncome?: BusinessIncome;
  };

  capitalGains: {
    shortTerm: CapitalGainEntry[];  // 111A, non-111A
    longTerm: CapitalGainEntry[];   // 112, 112A
  };

  otherSources: {
    interestIncome: InterestEntry[];
    dividendIncome: number;
    otherIncome: OtherIncomeEntry[];
  };

  // Deductions (Chapter VI-A)
  deductions: {
    section80C: Section80CEntry[];      // max ₹1,50,000
    section80CCC: number;               // max ₹1,50,000 (under 80C cap)
    section80CCD_1: number;             // employee NPS
    section80CCD_1B: number;            // additional NPS ₹50,000
    section80CCD_2: number;             // employer NPS (14% of salary)
    section80D: Section80DEntry[];      // health insurance
    section80DD: number;                // disabled dependent
    section80DDB: number;               // medical treatment
    section80E: number;                 // education loan interest
    section80EE: number;                // first home loan interest
    section80EEA: number;               // affordable housing
    section80EEB: number;               // electric vehicle
    section80G: Section80GEntry[];      // donations
    section80GG: number;                // rent paid (no HRA)
    section80GGA: number;               // scientific research donations
    section80GGC: number;               // political contributions
    section80IA: number;
    section80IAB: number;
    section80IAC: number;
    section80IB: number;
    section80IBA: number;
    section80IC: number;
    section80ID: number;
    section80IE: number;
    section80JJA: number;
    section80JJAA: number;
    section80LA: number;
    section80P: number;
    section80PA: number;
    section80QQB: number;
    section80RRB: number;
    section80TTA: number;              // interest up to ₹10,000
    section80TTB: number;              // senior citizen interest up to ₹50,000
    section80U: number;                // disability
  };

  // Exemptions
  exemptions: {
    hra: HRAExemption;
    lta: LTAExemption;
    leaveEncashment: number;
    gratuity: number;
    vrs: number;
    houseRentAllowance: HRAComputation;
  };

  // Taxes Paid
  taxesPaid: {
    tds: TDSEntry[];
    tcs: TCSEntry[];
    advanceTax: AdvanceTaxEntry[];
    selfAssessmentTax: number;
    foreignTaxCredit?: ForeignTaxCredit[];
  };

  // Losses
  broughtForwardLosses: BroughtForwardLoss[];
  currentYearLosses: CurrentYearLoss[];
}

interface TaxComputationResponse {
  computationId: string;

  // Income Summary
  incomeHeads: {
    salary: { gross: number; taxable: number };
    houseProperty: { gross: number; taxable: number; loss: number };
    business: { gross: number; taxable: number };
    capitalGains: { stcg: number; ltcg: number; total: number };
    otherSources: { gross: number; taxable: number };
  };
  grossTotalIncome: number;

  // Deductions
  totalDeductions: number;
  deductionBreakdown: DeductionBreakdown[];

  // Taxable Income
  taxableIncome: number;

  // Tax Computation
  taxOnSlabs: SlabBreakdown[];
  taxBeforeRebate: number;
  rebate87A: number;
  taxAfterRebate: number;
  surcharge: number;
  healthEducationCess: number;
  totalTaxLiability: number;

  // Relief
  relief234: number;
  relief89: number;
  foreignTaxCredit: number;

  // Interest
  interest234A: number;
  interest234B: number;
  interest234C: number;
  totalInterest: number;

  // Late Fee
  lateFee234F: number;

  // Final
  grossTaxPayable: number;
  lessTaxesPaid: number;
  netTaxPayable: number;
  refundDue: number;

  // Metadata
  effectiveTaxRate: number;
  computationVersion: string;
  computedAt: string;
}
```

---

## 2. AI Discovery Layer — Deduction Discovery Algorithm

### 2.1 Discovery Strategy

```
For each taxpayer profile, the AI systematically investigates:

┌─────────────────────────────────────────────────────────────┐
│                  DEDUCTION DISCOVERY FRAMEWORK               │
│                                                              │
│  PHASE 1: EXTRACTED DATA ANALYSIS                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ What we already know from documents:                    │ │
│  │  • Salary breakup → HRA potential                       │ │
│  │  • Form 16 deductions → 80C, 80D already claimed        │ │
│  │  • Bank interest → 80TTA potential                      │ │
│  │  • Home loan interest in Form 16 → 80EEA potential      │ │
│  │  • NPS contribution in salary → 80CCD(1B) gap          │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  PHASE 2: GAP ANALYSIS                                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ For every deduction section, check:                     │ │
│  │  • Is the taxpayer ELIGIBLE? (income type, status)      │ │
│  │  • Has it ALREADY been claimed? (from documents)        │ │
│  │  • Is there UNUSED capacity? (e.g., 80C < ₹1.5L)       │ │
│  │  • Does the taxpayer likely HAVE qualifying expenses?   │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  PHASE 3: EVIDENCE REQUIREMENT                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ For each discovered gap:                                │ │
│  │  • Required document(s) for claiming                    │ │
│  │  • Probability the taxpayer has this (heuristic)        │ │
│  │  • Question to ask if probability > threshold           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Deduction Discovery Rules (per Section)

```typescript
interface DeductionRule {
  section: string;
  name: string;
  maxAmount: number | ((profile: TaxpayerProfile) => number);
  eligibility: (profile: TaxpayerProfile) => boolean;
  alreadyClaimed: (profile: TaxpayerProfile, entities: ExtractedEntity[]) => number;
  gapDetection: (profile: TaxpayerProfile, claimed: number) => GapResult;
  requiredEvidence: string[];  // Document types needed
  questionTemplate: string;    // How to ask the user
  applicableRegimes: ('old' | 'new')[];
}
```

### 2.3 Complete Section-by-Section Discovery

The system investigates ALL of the following:

```
SECTION 80C (₹1,50,000 limit, aggregate)
├── Life Insurance Premium (LIC, private insurers)
├── PPF Contribution
├── EPF Contribution (employee share — already in Form 16)
├── NSC (National Savings Certificate)
├── ELSS Mutual Fund Investment
├── Home Loan Principal Repayment
├── Tuition Fees (children, max 2)
├── Sukanya Samriddhi Yojana
├── Senior Citizen Savings Scheme
├── 5-Year Fixed Deposit (Scheduled Bank / Post Office)
├── Infrastructure Bonds
└── Stamp Duty + Registration (property)

SECTION 80CCC (Annuity/Pension — under 80C cap)
└── Annuity plan premium (LIC or other insurer)

SECTION 80CCD(1) (NPS — employee, under 80C cap)
└── Employee NPS contribution (max 10% salary)

SECTION 80CCD(1B) (Additional NPS — separate from 80C)
└── Additional ₹50,000 for NPS

SECTION 80CCD(2) (Employer NPS — separate, no cap)
└── Employer contribution up to 14% of salary (Govt) / 10% (others)

SECTION 80D (Health Insurance)
├── Self/Spouse/Children: max ₹25,000 (₹50,000 for senior citizens)
├── Parents: additional ₹25,000 (₹50,000 for senior citizens)
├── Preventive health checkup: ₹5,000 (within above limits)
└── Combined maximum: ₹1,00,000 (if all senior citizens)

SECTION 80DD (Disabled Dependent)
├── Disability 40-79%: ₹75,000
└── Severe disability ≥80%: ₹1,25,000

SECTION 80DDB (Medical Treatment — Specified Diseases)
├── Self/Dependent < 60 years: ₹40,000
└── Senior Citizen: ₹1,00,000

SECTION 80E (Education Loan Interest)
└── Full interest amount, max 8 years

SECTION 80EE (First Home Loan — additional interest)
└── ₹50,000 (specific conditions)

SECTION 80EEA (Affordable Housing — additional interest)
└── ₹1,50,000 (specific conditions)

SECTION 80EEB (Electric Vehicle Loan Interest)
└── ₹1,50,000

SECTION 80G (Donations)
├── 100% deduction (no limit): PMNRF, PM Cares, etc.
├── 100% deduction (with limit): Certain trusts
├── 50% deduction (no limit): JN Memorial Fund, etc.
├── 50% deduction (with limit): Other approved institutions
└── Max qualifying limit: 10% of Adjusted GTI

SECTION 80GG (Rent Paid — no HRA)
└── Min of: ₹5,000/month, 25% of total income, rent - 10% of total income

SECTION 80TTA (Savings Interest — non-seniors)
└── Max ₹10,000 from savings account interest

SECTION 80TTB (Interest — senior citizens)
└── Max ₹50,000 from deposits (savings + FD + RD)

SECTION 80U (Disability — self)
├── Disability 40-79%: ₹75,000
└── Severe disability ≥80%: ₹1,25,000

EXEMPTIONS (not deductions — reduce taxable salary directly)
├── HRA (Section 10(13A)) — detailed computation
├── LTA (Section 10(5)) — max 2 journeys in 4 years
├── Leave Encashment (Section 10(10AA))
├── Gratuity (Section 10(10))
├── VRS Compensation (Section 10(10C))
├── Children Education Allowance (₹100/month/child, max 2)
├── Children Hostel Allowance (₹300/month/child, max 2)
├── Transport Allowance (disabled only)
└── Conveyance Allowance (exempt to extent spent)

CAPITAL GAINS EXEMPTIONS
├── Section 54: LTCG on house property → reinvest in residential property
├── Section 54EC: LTCG → invest in specified bonds (NHAI, REC)
├── Section 54F: LTCG on any asset → invest in residential house
├── Section 54B: Capital gain on agricultural land → reinvest
└── Grandfathering: LTCG up to Jan 31, 2018 (equity)

SET-OFF & CARRY FORWARD OF LOSSES
├── House Property Loss → set off against any head (max ₹2L against salary)
├── STCL → set off against any capital gain
├── LTCL → set off only against LTCG
├── Business Loss → set off against any head except salary
├── Speculation Loss → set off only against speculation income
├── Carry Forward: 8 years for house property, business, speculation
└── Carry Forward: Indefinite for capital losses (8 years set-off window)
```

---

## 3. Regime Comparison Algorithm

### 3.1 Regime Differences

| Feature | Old Regime | New Regime (115BAC) |
|---------|------------|---------------------|
| Slab rates | 0%-30% (3 slabs) | 0%-30% (6 slabs, lower rates) |
| Basic exemption | ₹2.5L / ₹3L / ₹5L | ₹3L / ₹3L / ₹5L |
| Standard Deduction | ₹50,000 | ₹75,000 (from FY 2024-25) |
| 80C | ✓ Available | ✗ Not available |
| 80D | ✓ Available | ✗ Not available |
| HRA | ✓ Available | ✗ Not available |
| LTA | ✓ Available | ✗ Not available |
| 80CCD(1B) | ✓ Available | ✗ Not available |
| 80CCD(2) | ✓ Available (no limit) | ✓ Available (employer NPS) |
| Home Loan Interest | ✓ (Self-occupied, max ₹2L) | ✗ Not available |
| 80TTA/80TTB | ✓ Available | ✗ Not available |
| Family Pension | ✓ ₹15,000 deduction | ✗ Not available |
| All other deductions | ✓ Available | ✗ Not available |
| Default from FY 2023-24 | — | ✓ Yes (unless opted out) |

### 3.2 Comparison Algorithm

```typescript
async function compareRegimes(
  profile: TaxpayerProfile,
  entities: ExtractedEntity[],
  answers: UserAnswers
): Promise<RegimeComparison> {

  // 1. Build "maximum deduction" scenario for Old Regime
  const oldRegimeDeductions = await discoverAllDeductions(profile, entities, answers, 'old');
  const oldRegimeMax = maximizeDeductionSet(oldRegimeDeductions);

  // 2. Build New Regime scenario (very few deductions available)
  const newRegimeDeductions = await discoverAllDeductions(profile, entities, answers, 'new');

  // 3. For Old Regime: try every permutation of deductions within caps
  //    This is a bounded optimization problem (each section has a cap)
  const oldRegimeScenarios = await generateOldRegimeScenarios(
    profile, oldRegimeDeductions
  );

  // 4. Compute tax for every scenario (via TRE)
  const oldRegimeComputations = await Promise.all(
    oldRegimeScenarios.map(s => taxRuleEngine.compute({ ...profile, regime: 'old', deductions: s }))
  );

  // 5. Compute tax for New Regime (simpler — fewer deductions)
  const newRegimeComputation = await taxRuleEngine.compute({
    ...profile,
    regime: 'new',
    deductions: newRegimeDeductions,
  });

  // 6. Find best Old Regime scenario
  const bestOldRegime = oldRegimeComputations.reduce((best, curr) =>
    curr.refundDue > best.refundDue ? curr : best
  );

  // 7. Compare and recommend
  const comparison = {
    oldRegime: {
      taxableIncome: bestOldRegime.taxableIncome,
      totalTax: bestOldRegime.totalTaxLiability,
      deductions: bestOldRegime.totalDeductions,
      effectiveRate: bestOldRegime.effectiveTaxRate,
      refundDue: bestOldRegime.refundDue,
      netPayable: bestOldRegime.netTaxPayable,
    },
    newRegime: {
      taxableIncome: newRegimeComputation.taxableIncome,
      totalTax: newRegimeComputation.totalTaxLiability,
      deductions: newRegimeComputation.totalDeductions,
      effectiveRate: newRegimeComputation.effectiveTaxRate,
      refundDue: newRegimeComputation.refundDue,
      netPayable: newRegimeComputation.netTaxPayable,
    },
    recommendation: null as RegimeRecommendation | null,
  };

  // 8. Determine recommendation
  if (bestOldRegime.refundDue > newRegimeComputation.refundDue) {
    comparison.recommendation = {
      regime: 'old',
      savings: bestOldRegime.refundDue - newRegimeComputation.refundDue,
      reason: 'Old Regime is better due to higher eligible deductions',
      keyDeductions: bestOldRegime.deductionBreakdown.filter(d => d.amount > 0),
    };
  } else {
    comparison.recommendation = {
      regime: 'new',
      savings: newRegimeComputation.refundDue - bestOldRegime.refundDue,
      reason: 'New Regime is better due to lower slab rates and higher basic exemption',
    };
  }

  return comparison;
}
```

### 3.3 Scenario Generation (Old Regime)

```typescript
function generateOldRegimeScenarios(
  profile: TaxpayerProfile,
  deductions: DiscoveredDeductions
): DeductionSet[] {
  const scenarios: DeductionSet[] = [];

  // For each section with flexibility, generate variants:

  // 80C: Try with 0%, 50%, 75%, 100% of max (₹1.5L) for each component
  const section80COptions = generate80CScenarios(deductions.section80C);

  // 80D: Try without, with minimum, with maximum
  const section80DOptions = generate80DScenarios(deductions.section80D);

  // HRA: Try without, with actual, with maximum legal lease
  const hraOptions = generateHRAScenarios(deductions.hra);

  // Generate cross-product (bounded: max ~100 scenarios)
  for (const c of section80COptions.slice(0, 4)) {
    for (const d of section80DOptions.slice(0, 3)) {
      for (const h of hraOptions.slice(0, 3)) {
        scenarios.push({ ...c, ...d, ...h });
        if (scenarios.length > 100) break; // Hard cap
      }
    }
  }

  return scenarios;
}
```

---

## 4. HRA Optimization

### 4.1 HRA Computation (Section 10(13A))

```typescript
interface HRAInput {
  hraReceived: number;           // From Form 16
  rentPaid: number;              // Annual rent
  basicSalary: number;           // Basic + DA (forming part of retirement benefits)
  metroCity: boolean;            // Mumbai, Delhi, Chennai, Kolkata
}

function computeHRAExemption(input: HRAInput): number {
  const annualRent = input.rentPaid * 12;

  // Three components — exempt is MINIMUM of:
  // (a) Actual HRA received
  // (b) Rent paid minus 10% of (Basic + DA)
  // (c) 50% of (Basic + DA) for metro, 40% for non-metro

  const a = input.hraReceived;
  const b = annualRent - (0.10 * input.basicSalary);
  const c = input.metroCity
    ? 0.50 * input.basicSalary
    : 0.40 * input.basicSalary;

  return Math.max(0, Math.min(a, b, c));
}
```

### 4.2 HRA Optimization Strategy

```typescript
function optimizeHRA(input: HRAInput): HRARecommendation {
  const currentExemption = computeHRAExemption(input);

  // Scenario: What if user increases rent?
  const scenarios = [];
  for (let multiplier = 1.0; multiplier <= 1.5; multiplier += 0.1) {
    const hypotheticalRent = Math.round(input.rentPaid * multiplier);
    const newExemption = computeHRAExemption({ ...input, rentPaid: hypotheticalRent });
    if (newExemption > currentExemption) {
      scenarios.push({
        rentPerMonth: hypotheticalRent,
        exemption: newExemption,
        additionalSaving: newExemption - currentExemption,
        taxSaving: (newExemption - currentExemption) * getApplicableSlabRate(input),
      });
    }
  }

  // Scenario: What if metro vs non-metro?
  const metroExemption = computeHRAExemption({ ...input, metroCity: true });
  const nonMetroExemption = computeHRAExemption({ ...input, metroCity: false });

  return {
    currentExemption,
    bestScenario: scenarios.sort((a, b) => b.taxSaving - a.taxSaving)[0],
    recommendation: currentExemption < input.hraReceived
      ? `You can still claim ₹${input.hraReceived - currentExemption} more HRA. Increase rent or check metro status.`
      : 'Your HRA is fully optimized.',
    requiredEvidence: ['rent_receipt', 'rent_agreement', 'landlord_pan'],
    warning: input.rentPaid > 83000
      ? 'Landlord PAN required for rent > ₹83,333/month'
      : undefined,
  };
}
```

---

## 5. Capital Gains Optimization

### 5.1 Grandfathering (Listed Equity LTCG up to 31-Jan-2018)

```typescript
function computeGrandfatheredLTCG(
  purchaseDate: Date,
  purchasePrice: number,
  saleDate: Date,
  salePrice: number,
  fmvJan31_2018: number
): { ltcg: number; grandfathered: boolean } {

  // Only applies to listed equity acquired before 01-Feb-2018
  if (purchaseDate >= new Date('2018-02-01')) {
    return { ltcg: salePrice - purchasePrice, grandfathered: false };
  }

  // Cost of acquisition = Higher of: (a) Actual cost, (b) Lower of: (i) FMV on 31-01-2018, (ii) Sale value
  const costForCG = Math.max(
    purchasePrice,
    Math.min(fmvJan31_2018, salePrice)
  );

  const ltcg = salePrice - costForCG;
  return { ltcg: Math.max(0, ltcg), grandfathered: true };
}
```

### 5.2 Capital Gains Exemption Optimization

```typescript
function optimizeCapitalGains(gains: CapitalGainEntry[]): CGRecommendation[] {
  const recommendations: CGRecommendation[] = [];

  for (const gain of gains) {
    if (gain.type === 'LTCG' && gain.assetType === 'residential_property') {
      // Section 54: Exemption if reinvested in residential property
      recommendations.push({
        section: '54',
        gainAmount: gain.gain,
        strategy: `Invest ₹${gain.gain} in residential property within 2 years (or construct within 3 years)`,
        deadline: gain.saleDate.addYears(2),
        taxSaving: gain.gain * 0.20, // LTCG tax rate
        requiredEvidence: ['purchase_deed', 'sale_deed', 'capital_gains_account'],
        lockIn: '3 years (cannot sell new property within 3 years)',
      });

      // Section 54EC: Alternative — invest in specified bonds
      recommendations.push({
        section: '54EC',
        gainAmount: gain.gain,
        strategy: `Invest up to ₹50L in NHAI/REC bonds within 6 months`,
        maxInvestment: 5000000,
        deadline: gain.saleDate.addMonths(6),
        taxSaving: Math.min(gain.gain, 5000000) * 0.20,
        requiredEvidence: ['bond_certificate'],
        lockIn: '5 years',
      });
    }

    if (gain.type === 'LTCG' && gain.assetType === 'listed_equity') {
      // Grandfathering + ₹1Lakh annual exemption
      recommendations.push({
        section: '112A',
        gainAmount: gain.gain,
        strategy: `₹1,00,000 of LTCG is tax-free u/s 112A. Remaining taxed at 10%.`,
        exemptAmount: Math.min(gain.gain, 100000),
        taxableAmount: Math.max(0, gain.gain - 100000),
        taxSaving: Math.min(gain.gain, 100000) * 0.10,
      });
    }
  }

  return recommendations;
}
```

---

## 6. Loss Harvesting Optimization

```typescript
function optimizeLossHarvesting(
  currentYearGains: CapitalGainEntry[],
  currentYearLosses: CapitalLossEntry[],
  broughtForwardLosses: BroughtForwardLoss[]
): LossOptimizationResult {

  // STCL can set off against both STCG and LTCG
  // LTCL can ONLY set off against LTCG
  // Remaining loss: Carry forward 8 years

  const totalSTCG = sum(currentYearGains.filter(g => g.type === 'STCG'), 'gain');
  const totalLTCG = sum(currentYearGains.filter(g => g.type === 'LTCG'), 'gain');
  const totalSTCL = sum(currentYearLosses.filter(l => l.type === 'STCL'), 'loss');
  const totalLTCL = sum(currentYearLosses.filter(l => l.type === 'LTCL'), 'loss');

  // Set-off order: STCL first against STCG, then against LTCG
  let remainingSTCL = totalSTCL;
  let remainingLTCL = totalLTCL;

  const stclAgainstSTCG = Math.min(remainingSTCL, totalSTCG);
  remainingSTCL -= stclAgainstSTCG;

  const stclAgainstLTCG = Math.min(remainingSTCL, totalLTCG - stclAgainstSTCG);
  remainingSTCL -= stclAgainstLTCG;

  const ltclAgainstLTCG = Math.min(remainingLTCL, totalLTCG - stclAgainstSTCG - stclAgainstLTCG);
  remainingLTCL -= ltclAgainstLTCG;

  return {
    currentYearSetOff: {
      stclAgainstSTCG,
      stclAgainstLTCG,
      ltclAgainstLTCG,
    },
    remainingLoss: remainingSTCL + remainingLTCL,
    carryForward: {
      stcl: remainingSTCL,
      ltcl: remainingLTCL,
      expiryYear: new Date().getFullYear() + 8,
    },
    recommendation: remainingSTCL > 0
      ? 'Consider selling profitable stocks to offset remaining STCL before year-end'
      : undefined,
  };
}
```

---

## 7. Optimization Report Structure

Every optimization produces a structured report:

```typescript
interface OptimizationReport {
  reportId: string;
  sessionId: string;
  generatedAt: string;

  // Regime Recommendation
  regimeRecommendation: {
    recommended: 'old' | 'new';
    savings: number;
    comparisonTable: RegimeComparisonRow[];
    explanation: string;
    confidence: number;
  };

  // Discovered Opportunities
  opportunities: OptimizationOpportunity[];

  // Applied vs. Available
  deductionsApplied: DeductionApplied[];
  deductionsAvailable: DeductionAvailable[];

  // Risk Assessment
  riskItems: RiskItem[];
  overallRiskScore: 'low' | 'medium' | 'high';

  // Scenario Analysis
  scenarios: ScenarioAnalysis[];

  // Required Actions
  requiredActions: RequiredAction[];

  // Supporting Provisions
  legalReferences: LegalReference[];
}

interface OptimizationOpportunity {
  opportunityId: string;
  category: 'deduction' | 'exemption' | 'credit' | 'loss_setoff' | 'regime_switch';
  section: string;
  title: string;
  description: string;
  potentialSaving: number;
  confidence: number;
  requiredEvidence: string[];
  risks: string[];
  recommendation: string;
  userAction: 'invest' | 'claim' | 'declare' | 'verify' | 'consult';
}
```

---

## 8. Safety Constraints

The AI must NEVER:

1. **Calculate tax** — Always call TRE for any computation
2. **Exceed statutory limits** — Hard caps enforced by TRE (₹1.5L for 80C, etc.)
3. **Claim without evidence** — Every deduction gated by document evidence
4. **Assume eligibility** — Check all conditions before recommending
5. **Recommend illegal avoidance** — System rejects fabricated deductions
6. **Double-claim** — Detect and prevent claiming same expense under multiple sections
7. **Miss reporting requirements** — AIS-reported income always included
8. **Override user rejection** — If user declines a deduction, do NOT re-recommend

---

*Next: [17 Recommendation Engine](17-recommendation-engine.md)*
