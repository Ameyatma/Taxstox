# Enterprise Capability Model — Part 2: Domains 6-20

> **Continuation of [ENTERPRISE_CAPABILITY_MODEL.md](ENTERPRISE_CAPABILITY_MODEL.md)**
> **Date:** 2026-07-05

---

## 6. Domain 5: Deduction & Exemption Management

### C5.1 — Chapter VI-A Deduction Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute all eligible Chapter VI-A deductions with statutory limit enforcement per financial year. |
| **Responsibilities** | Support all deduction sections: 80C (₹1.5L aggregate), 80CCC (pension), 80CCD(1) (NPS employee, within 80C), 80CCD(1B) (NPS additional ₹50K), 80CCD(2) (Employer NPS, 10%/14% of salary), 80D (health insurance ₹25K/₹50K), 80DD (disabled dependent ₹75K/₹1.25L), 80DDB (medical treatment ₹40K/₹1L), 80E (education loan interest), 80EE/80EEA (home loan interest additional), 80EEB (EV loan), 80G (donations 50%/100%), 80GG (rent without HRA ₹60K), 80GGA/GGC (scientific/political donations), 80TTA (savings interest ₹10K), 80TTB (senior citizen interest ₹50K), 80U (self-disability); enforce per-section limits; enforce 80C aggregate limit; handle component-level sub-limits (tuition fees max 2 children, home loan principal within 80C); regime-specific availability (most deductions only Old Regime) |
| **Inputs** | Form 16 Chapter VI-A data, User-provided investment amounts, Investment proof documents, FY, Regime, Senior citizen status |
| **Outputs** | ChapterVIADeductions (per section), TotalDeductions, LimitExceededWarnings, SupportingEvidenceRequired |
| **Dependencies** | C2.3 Filing Status, C3.9 Investment Proof Parser, C7.1 Regime Comparison, C12.3 Rule Repository (Chapter VI-A limits by FY) |
| **Business Value** | Major tax savings for Old Regime taxpayers; complex multi-section optimization |
| **Priority** | **Critical** |
| **Maturity Target** | All 20+ sections with auto-limit enforcement; deduction optimization suggestions; regime-aware availability |

### C5.2 — Section 10 Exemption Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute all Section 10 income exemptions available to the taxpayer. |
| **Responsibilities** | HRA exemption (10(13A)) — min of actual HRA, rent-10% basic, 40%/50% basic; LTA exemption (10(5)) — actual travel, 2 journeys in 4 years; gratuity exemption (10(10)) — 15/26 × completed years × last drawn salary, ₹20L cap; leave encashment (10(10AA)) — ₹25L cap (non-govt); commuted pension (10(10A)); child education allowance (10(14)) — ₹100/mo/child, max 2; hostel allowance — ₹300/mo/child, max 2; transport allowance (disabled); conveyance allowance; uniform allowance; research allowance; special allowances under 10(14); regime awareness (most exemptions only Old Regime) |
| **Inputs** | Form 16 Annexure (salary components), Rent paid, Metro/non-metro, Travel costs, Years of service, Last drawn salary, FY, Regime |
| **Outputs** | Section10Exemptions (per section), ExemptionEvidenceRequired |
| **Dependencies** | C3.3 Form 16 Parser, C12.3 Rule Repository (S10 limits by FY), C7.1 Regime Comparison |
| **Business Value** | Reduces taxable salary significantly; HRA alone can be ₹2L+ exemption |
| **Priority** | **High** |
| **Maturity Target** | Auto-computation from Form 16 Annexure + user location; employer-specific exemption policy awareness |

### C5.3 — Standard Deduction & Rebate Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Apply standard deduction, family pension deduction, and rebates per applicable provisions. |
| **Responsibilities** | Standard deduction (₹75K New / ₹50K Old for salaried; ₹75K/₹50K for family pension); family pension deduction (1/3rd or ₹15K); rebate u/s 87A (max ₹60K for New Regime income ≤₹12L; max ₹12.5K for Old Regime income ≤₹5L); rebate for senior citizens; marginal relief calculation |
| **Inputs** | Income type (salary/pension), Total income, Regime, FY, Age |
| **Outputs** | StandardDeduction, Rebate87A, MarginalRelief |
| **Dependencies** | C12.3 Rule Repository (87A thresholds by FY), C7.1 Regime Comparison |
| **Business Value** | Automatic application of basic deductions/rebates that every taxpayer is entitled to |
| **Priority** | **High** |
| **Maturity Target** | Auto-detection of eligibility; correct FY-specific thresholds |

### C5.4 — Deduction Optimization Advisor

| Attribute | Value |
|-----------|-------|
| **Purpose** | Proactively identify deductible investments the taxpayer has not yet claimed. |
| **Responsibilities** | Analyze current deduction utilization vs limits; identify unused deduction capacity (80C gap, 80D gap, 80CCD(1B) gap); analyze investments already made (from Form 16, AIS) vs maximum available; recommend specific actions ("Invest ₹30,000 more in PPF to max 80C"); estimate tax saving from each recommendation; prioritize by saving amount; respect regime constraints |
| **Inputs** | Current deduction utilization, Investment proof data, FY, Regime |
| **Outputs** | OptimizationSuggestions (ranked), PotentialTaxSavings, DeadlineWarnings |
| **Dependencies** | C5.1 Deduction Engine, C7.1 Regime Comparison, C19 Tax Planning |
| **Business Value** | Proactive tax saving; builds trust that platform is working for taxpayer |
| **Priority** | **Medium** |
| **Maturity Target** | Investment-linked suggestions (specific products); pre-deadline reminders; FY-end optimization rush handling |

### C5.5 — Donation (80G) Computation Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute 80G deduction with correct qualifying amount and percentage per donee institution. |
| **Responsibilities** | Maintain donee institution database with 80G approval status and percentage (50%/100%); compute qualifying limit (10% of adjusted GTI for limit-bound donations); distinguish with-qualifying-limit vs without-qualifying-limit donations; handle cash donation restriction (>₹2,000 not eligible); validate donee PAN and 80G certificate; support 80GGA (scientific research) and 80GGC (political party) |
| **Inputs** | Donation receipts, Donee PAN, Donation amount, Payment mode, Adjusted GTI |
| **Outputs** | Section80GDeduction, QualifyingAmount, DoneeVerificationStatus |
| **Dependencies** | C5.1 Deduction Engine, C12.3 Rule Repository, Donee institution database |
| **Business Value** | Encourages charitable giving; correctly computes complex eligibility rules |
| **Priority** | **Medium** |
| **Maturity Target** | Donee database with auto-verification; QR-code receipt scanning |

### C5.6 — Home Loan Deduction Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute all home loan related deductions across Sections 24(b), 80C (principal), 80EE, and 80EEA. |
| **Responsibilities** | Section 24(b) — interest on housing loan (₹2L self-occupied, unlimited let-out); pre-construction interest (5 equal installments from year of completion); Section 80C — principal repayment (within ₹1.5L limit); Section 80EE — first-time buyer additional ₹50K (conditions: loan ≤₹35L, property ≤₹50L, FY2016-17); Section 80EEA — affordable housing additional ₹1.5L (conditions: stamp duty ≤₹45L, loan sanctioned FY2019-22); co-borrower handling (each co-owner can claim proportionally); joint property handling |
| **Inputs** | Home loan statement, Property details, Loan sanction date, Possession date, Co-owner details, FY |
| **Outputs** | HomeLoanDeductions (24b + 80C principal + 80EE + 80EEA), PreConstructionInterestSchedule |
| **Dependencies** | C5.1 Deduction Engine, C4.2 House Property Engine, C12.3 Rule Repository |
| **Business Value** | One of the largest deduction categories; complex multi-section computation |
| **Priority** | **High** |
| **Maturity Target** | Direct lender API integration; auto-classification of principal vs interest; pre-construction auto-amortization |

### C5.7 — NPS & Retirement Deduction Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute all NPS, EPF, and retirement-related deductions with inter-section coordination. |
| **Responsibilities** | 80CCD(1) — employee NPS contribution (within 80C ₹1.5L limit); 80CCD(1B) — additional NPS beyond 80C (₹50K, available in both regimes); 80CCD(2) — employer NPS contribution (10% of salary for non-govt, 14% for CG, available in BOTH regimes, no upper limit); 80CCC — annuity pension (within 80C limit); EPF (employee contribution under 80C); ensure correct inter-section coordination (no double counting); handle Atal Pension Yojana |
| **Inputs** | Form 16 Chapter VI-A, NPS statement, Salary (basic + DA), FY, Regime |
| **Outputs** | RetirementDeductions, Section80CCD1B_Deduction, Section80CCD2_Deduction |
| **Dependencies** | C3.3 Form 16 Parser, C5.1 Deduction Engine, C12.3 Rule Repository |
| **Business Value** | NPS is available in both regimes — critical optimization lever; complex inter-section limits |
| **Priority** | **High** |
| **Maturity Target** | NPS statement auto-parse; tier-1 vs tier-2 differentiation; employer contribution auto-detection |

---

## 7. Domain 6: Tax Computation Engine

### C6.1 — Slab Tax Computation Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute income tax on slab-rate income for any financial year and any applicable tax regime. |
| **Responsibilities** | Load tax slabs for given FY + regime; apply slab rates progressively to taxable income; handle different slab structures (Old Regime: 3 slabs, New Regime: 6 slabs, Senior citizens: higher basic exemption); compute tax before rebate; compute tax after rebate; support alternative slab structures for specific entities (cooperative societies, firms, companies); keep computation logic completely separate from slab data |
| **Inputs** | Total income (slab-rate portion), FY, Regime, Age category, Entity type |
| **Outputs** | TaxOnSlabIncome, PerSlabBreakdown, EffectiveTaxRate |
| **Dependencies** | C12.1 Finance Act Versioning, C12.3 Rule Repository (slab definitions) |
| **Business Value** | Core of tax computation; must be 100% correct and versioned by FY |
| **Priority** | **Critical** |
| **Maturity Target** | Generic slab engine that works for any FY without code change; verified against ITD portal output for every FY |

### C6.2 — Special Rate Income Tax Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute tax on income chargeable at special rates (capital gains, lottery, crypto, etc.). |
| **Responsibilities** | Section 111A: 15% on equity STCG; Section 112A: 12.5% on equity LTCG (above ₹1.25L); Section 112: 20% on other LTCG (with indexation) or 12.5% (without); Section 115BB: 30% on lottery/game winnings; Section 115BBH: 30% on crypto/VDAs; Section 115BBE: 60% on unexplained income; Section 115BBC: 30% on anonymous donations; Section 115BBD: 15% on foreign company dividends |
| **Inputs** | Special-rate income amounts by section, FY |
| **Outputs** | SpecialRateTax, PerSectionBreakdown |
| **Dependencies** | C4.4 Capital Gains Engine, C4.5 Other Sources Engine, C12.3 Rule Repository |
| **Business Value** | Different tax rates for different income types — must be correctly segregated from slab income |
| **Priority** | **Critical** |
| **Maturity Target** | All special rate sections; verified against ITD portal for each section |

### C6.3 — Surcharge Computation Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute surcharge on income tax with correct thresholds and marginal relief per financial year. |
| **Responsibilities** | Apply surcharge thresholds (₹50L: 10%, ₹1Cr: 15%, ₹2Cr: 25%, ₹5Cr: 37% for individuals — varies by entity type); compute marginal relief (surcharge cannot exceed income above threshold); different surcharge rates for different entity types (firms: 12%, domestic companies: 7%/12%, foreign companies: 2%/5%); cap on surcharge for specific income types (112A: max 15%); different caps for Old vs New Regime (New: surcharge capped at 25%) |
| **Inputs** | Total income, Tax amount, Entity type, Regime, FY |
| **Outputs** | SurchargeAmount, MarginalReliefComputation, EffectiveSurchargeRate |
| **Dependencies** | C6.1 Slab Tax Engine, C6.2 Special Rate Engine, C12.3 Rule Repository |
| **Business Value** | Significant additional liability for HNIs; marginal relief can reduce it substantially |
| **Priority** | **Critical** |
| **Maturity Target** | All entity types; verified marginal relief against ITD portal for edge cases at thresholds |

### C6.4 — Health & Education Cess Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute Health and Education Cess at the applicable rate for the financial year. |
| **Responsibilities** | Apply HEC rate (currently 4% of [tax + surcharge]); handle rate changes across FYs (was 3% as Education Cess + Secondary & Higher Education Cess pre-FY2018-19; now 4% as Health & Education Cess); compute cess on (tax after rebate + surcharge); round to nearest rupee |
| **Inputs** | Tax after rebate, Surcharge, FY |
| **Outputs** | HECCess, TotalTaxLiability |
| **Dependencies** | C12.3 Rule Repository (cess rates by FY) |
| **Business Value** | Mandatory; small absolute amount but must be exactly correct |
| **Priority** | **High** |
| **Maturity Target** | FY-aware rate lookup; auto-handles historical rate changes |

### C6.5 — Tax Liability Aggregator

| Attribute | Value |
|-----------|-------|
| **Purpose** | Aggregate all tax components into the final tax liability with correct rounding per Section 288B. |
| **Responsibilities** | Combine slab tax + special rate taxes; subtract rebate (87A); add surcharge (with marginal relief); add HEC; round to nearest ₹10 (as per 288B) or nearest ₹1 (ITD portal practice); compute tax payable (after TDS/TCS/advance tax); compute refund due |
| **Inputs** | All tax components, TDS credits, Advance tax payments, Self-assessment tax, FY |
| **Outputs** | FinalTaxLiability, TaxPayable, RefundDue |
| **Dependencies** | C6.1-C6.4, C8.1 Tax Credit Reconciliation |
| **Business Value** | Final number that matters to the taxpayer |
| **Priority** | **Critical** |
| **Maturity Target** | Exact matching with ITD portal computation; verified for all rounding edge cases |

### C6.6 — Computation Pipeline Orchestrator

| Attribute | Value |
|-----------|-------|
| **Purpose** | Orchestrate the tax computation pipeline in the correct sequence with explicit stage dependencies. |
| **Responsibilities** | Enforce computation order (income → aggregation → deductions → tax → surcharge → cess → credits → final); manage data flow between stages; validate each stage output before passing to next; support partial recomputation (if one income head changes, only recompute downstream); track computation version and rule versions used; log intermediate results for audit trail |
| **Inputs** | ComputationRequest (data, FY, regime, options), StageOverrideConfig |
| **Outputs** | ComputationResult, StageResults, ComputationMetadata, RuleVersionsUsed |
| **Dependencies** | All C6 sub-capabilities, C11.1 Audit Trail |
| **Business Value** | Enforces consistent computation order; enables partial recomputation for performance |
| **Priority** | **High** |
| **Maturity Target** | Directed acyclic graph (DAG) computation model; parallel stage execution where independent |

### C6.7 — Interest Computation Engine (234A/B/C)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute interest payable under Sections 234A (late filing), 234B (advance tax default), and 234C (advance tax deferment). |
| **Responsibilities** | 234A: 1% per month on unpaid tax from due date (Jul 31/Oct 31/Nov 30); 234B: 1% per month if advance tax paid < 90% of assessed tax; 234C: 1% per month for each installment shortfall (15%/45%/75%/100% by Jun 15/Sep 15/Dec 15/Mar 15); compute months of default correctly (part month = full month); handle senior citizen exemption from advance tax (no business income) |
| **Inputs** | Tax liability, TDS/TCS, Advance tax payments by date, Filing date, Due date, Age category, Income types |
| **Outputs** | Interest234A, Interest234B, Interest234C, TotalInterest |
| **Dependencies** | C6.5 Tax Liability Aggregator, C8.1 Tax Credit Reconciliation, C12.3 Rule Repository |
| **Business Value** | Interest can be significant; correct computation avoids under/over-payment |
| **Priority** | **High** |
| **Maturity Target** | Verified against ITD portal for all interest scenarios; auto-detection of interest applicability |

### C6.8 — Fee & Penalty Computation

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute late filing fees (Section 234F) and other applicable penalties. |
| **Responsibilities** | Section 234F: ₹5,000 (filed after due date but by Dec 31) / ₹10,000 (filed after Dec 31) / ₹1,000 (total income ≤₹5L); penalty for under-reporting (270A — 50% of tax on under-reported income); penalty for misreporting (270A — 200%); fee for PAN-Aadhaar late linking (₹1,000) |
| **Inputs** | Filing date, Due date, Total income, PAN-Aadhaar link status |
| **Outputs** | LateFee234F, PenaltyAssessment, TotalFeesAndPenalties |
| **Dependencies** | C2.5 Historical Filing Record, C12.3 Rule Repository |
| **Business Value** | Avoids surprises; taxpayers should know fees before filing |
| **Priority** | **Medium** |
| **Maturity Target** | All penalty sections; auto-computation from filing timeline |

---

## 8. Domain 7: Regime Optimization

### C7.1 — Old vs New Regime Comparison Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute and compare tax liability under both Old and New Regimes, recommending the optimal choice. |
| **Responsibilities** | Compute tax under Old Regime (all deductions, exemptions, higher slab rates); compute tax under New Regime (limited deductions, lower slab rates, higher standard deduction); compare final liability; recommend optimal regime; compute savings; show line-by-line comparison; identify which deductions make the difference; identify break-even point |
| **Inputs** | All income data, All deduction data, FY, Age category |
| **Outputs** | RegimeComparison, RecommendedRegime, Savings, LineByLineComparison, BreakEvenAnalysis |
| **Dependencies** | C6 Tax Computation Engine, C5 Deduction Engine, C4 Income Engines |
| **Business Value** | Core value proposition — regime choice can mean ₹50K+ difference for some taxpayers |
| **Priority** | **Critical** |
| **Maturity Target** | Exact ITD portal match for both regimes; side-by-side human-readable comparison |

### C7.2 — Regime Lock-in & Transition Advisor

| Attribute | Value |
|-----------|-------|
| **Purpose** | Handle regime lock-in rules and advise on transition between regimes across years. |
| **Responsibilities** | Track regime lock-in: business income taxpayers — once opted for New, can revert only once in lifetime; salaried — can switch every year; advise on long-term regime strategy (not just current year); simulate multi-year regime impact; warn on lock-in consequences before commitment |
| **Inputs** | Current year regime choice, Previous year regime history, Income type (business vs salary), Income projections |
| **Outputs** | RegimeLockInStatus, TransitionAdvice, MultiYearProjection |
| **Dependencies** | C2.5 Historical Filing Record, C4.3 Business Income Engine, C19 Tax Planning |
| **Business Value** | Prevents costly lock-in mistakes for business income taxpayers |
| **Priority** | **High** |
| **Maturity Target** | Multi-year regime optimization; lock-in warning with clear explanation of consequences |

### C7.3 — Regime Eligibility Checker

| Attribute | Value |
|-----------|-------|
| **Purpose** | Verify taxpayer is eligible for each regime and identify any restrictions. |
| **Responsibilities** | Check if taxpayer has business income (triggers lock-in rules); check if previous year New Regime with business income (cannot revert); check entity type restrictions (companies, firms have different rules); check if taxpayer has specific deductions only available in one regime |
| **Inputs** | Taxpayer profile, Income types, Previous year regime, Entity type |
| **Outputs** | RegimeEligibility (per regime), RestrictionWarnings |
| **Dependencies** | C2.3 Filing Status, C4.3 Business Income Engine, C2.5 Historical Filing Record |
| **Business Value** | Prevents invalid regime selection that ITD portal would reject |
| **Priority** | **High** |
| **Maturity Target** | All eligibility rules per Finance Act; auto-detection of lock-in from filing history |

### C7.4 — Marginal Tax Rate Analyzer

| Attribute | Value |
|-----------|-------|
| **Purpose** | Analyze the taxpayer's marginal tax rate to inform incremental income/deduction decisions. |
| **Responsibilities** | Compute effective marginal rate (tax on next ₹1 of income); identify bracket thresholds; show how close taxpayer is to next bracket; identify deduction sweet spots; analyze surcharge marginal rate (including marginal relief zone) |
| **Inputs** | Current tax computation, Income projections, Proposed deductions |
| **Outputs** | MarginalTaxRate, NextBracketThreshold, DeductionSweetSpots, SurchargeMarginalRate |
| **Dependencies** | C6.1 Slab Tax Engine, C6.3 Surcharge Engine, C7.1 Regime Comparison |
| **Business Value** | Enables informed incremental decisions; key for tax planning |
| **Priority** | **Medium** |
| **Maturity Target** | Interactive marginal rate visualization; "what-if" slider for income/deduction changes |

### C7.5 — Family Unit Regime Optimization

| Attribute | Value |
|-----------|-------|
| **Purpose** | Optimize regime selection across a family unit considering inter-member tax implications. |
| **Responsibilities** | Compute optimal regime for each family member; consider clubbing provisions; optimize deduction allocation across members; coordinate HUF regime with individual members; consider spouse with different income profiles |
| **Inputs** | Family member profiles, Income per member, Deduction options, Clubbing triggers |
| **Outputs** | PerMemberRegimeRecommendation, FamilyOptimizedStrategy, AggregateSavings |
| **Dependencies** | C2.6 Family Unit Management, C7.1 Regime Comparison, C4.6 Income Aggregation & Clubbing |
| **Business Value** | Holistic family optimization; typical CA service for HNI clients |
| **Priority** | **Medium** |
| **Maturity Target** | Joint optimization algorithm; cross-member deduction reallocation suggestions |

### C7.6 — Regime Comparison Visualization

| Attribute | Value |
|-----------|-------|
| **Purpose** | Present regime comparison results in visually intuitive formats for taxpayer understanding. |
| **Responsibilities** | Side-by-side income comparison chart; deduction availability matrix; effective tax rate visualization; waterfall chart (income → deductions → tax → cess = final liability); savings breakdown; interactive "what-if" controls |
| **Inputs** | RegimeComparison data, Tax breakdown |
| **Outputs** | Visualization data (chart-ready), Summary text, Interactive comparison UI |
| **Dependencies** | C7.1 Regime Comparison, C14 Reporting & Analytics |
| **Business Value** | Makes complex regime comparison understandable to non-experts |
| **Priority** | **Medium** |
| **Maturity Target** | Interactive visualization; downloadable comparison report; CA-friendly detailed view |

---

## 9. Domain 8: Compliance & Validation

### C8.1 — Tax Credit Reconciliation Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Three-way reconcile TDS/TCS/tax payments across Form 16, AIS, and Form 26AS to maximize legitimate tax credit. |
| **Responsibilities** | Match TDS entries by deductor TAN, amount, date; identify unmatched entries (in one source but not another); identify duplicate entries (same transaction reported twice); compute total claimable TDS using AIS as authoritative source; flag mismatches for taxpayer review; reconcile advance tax payments; reconcile self-assessment tax; generate reconciliation report with action items |
| **Inputs** | Form 16 Part A TDS, AIS TDS entries, Form 26AS (optional/future), Challan details |
| **Outputs** | ReconciliationReport, ClaimableTDS, MismatchesFlagged, UnmatchedDeductorList |
| **Dependencies** | C3.3 Form 16 Parser, C3.4 AIS Parser, C3.7 Form 26AS Parser |
| **Business Value** | #1 cause of CPC TDS credit denial; proactive reconciliation prevents notices |
| **Priority** | **Critical** |
| **Maturity Target** | Automatic resolution of common mismatches; TAN-deductor database for matching; real-time TRACES verification |

### C8.2 — Cross-Document Validation Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Validate consistency of taxpayer data across multiple documents (Form 16, AIS, Form 26AS, previous ITR). |
| **Responsibilities** | PAN consistency across all documents; name consistency (fuzzy match for minor spelling differences); DOB consistency; salary amount consistency (Form 16 Part B vs AIS TDS-192); TDS amount consistency; employer TAN consistency; interest income consistency (AIS SFT vs bank statements); capital gains consistency (AIS SFT vs broker statements) |
| **Inputs** | All parsed documents, Taxpayer profile |
| **Outputs** | CrossDocumentValidationReport, ConsistencyScore, InconsistencyAlerts |
| **Dependencies** | C3 Document Intelligence, C2.1 Taxpayer Profile |
| **Business Value** | Catches data errors before they become ITR errors; builds confidence in computed result |
| **Priority** | **High** |
| **Maturity Target** | ML-based inconsistency detection; auto-resolution of minor variations; confidence-weighted alerts |

### C8.3 — ITR Schema Validation Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Validate generated ITR JSON against the ITD schema, known portal quirks, and best practices. |
| **Responsibilities** | JSON schema structural validation; mandatory field presence; data type conformance; enum value validation (SecondaryAdd, ISIN, ReturnFileMode, etc.); length/format validation (PAN, IFSC, Aadhaar); cross-schedule consistency (CG date ranges = BFLA, total income = sum of heads, TDS total = schedule sums); deduction limit enforcement (80C ≤1.5L, 80D limits, 112A ≤1.25L); business rule validation (refund bank count = 1, STCG with STT=No → A5 not A2); tax computation accuracy (independent recalculation); known portal bug workarounds (INNOTREQUIRD → INNOTAVAILAB, SecondaryAdd="" → "Y") |
| **Inputs** | Generated ITR JSON, ITR type, Assessment year |
| **Outputs** | ValidationReport (with pass/fail per rule), SchemaErrors, CrossScheduleErrors, TaxComputationErrors, FixSuggestions |
| **Dependencies** | C9 ITR Generation, C6 Tax Computation Engine, ITD schema specifications |
| **Business Value** | Prevents ITD portal rejection; each rejection avoided = one saved support interaction |
| **Priority** | **Critical** |
| **Maturity Target** | 100+ validation rules; auto-fix for known patterns; continuous update from portal error reports |

### C8.4 — AIS Income Completeness Checker

| Attribute | Value |
|-----------|-------|
| **Purpose** | Verify that all income reflected in AIS has been captured and reported in the ITR. |
| **Responsibilities** | Iterate all AIS entries (TDS + SFT); verify each has been mapped to an income head and ITR schedule; flag any AIS entry not accounted for; compare total income from AIS with total income in ITR; detect AIS entries that suggest unreported income sources; warn user about discrepancies |
| **Inputs** | AIS data, ITR data, Income computations |
| **Outputs** | CompletenessReport, MissingIncomeAlerts, AISvsITRComparison |
| **Dependencies** | C3.4 AIS Parser, C3.6 AIS Code Classification, C4 Income Engines |
| **Business Value** | ITD uses AIS for scrutiny selection; completeness is the best defense against notices |
| **Priority** | **Critical** |
| **Maturity Target** | 100% AIS entry reconciliation; auto-suggestion for missing entries |

### C8.5 — Regulatory Limit & Threshold Validator

| Attribute | Value |
|-----------|-------|
| **Purpose** | Validate all computations against statutory limits, thresholds, and conditions per the relevant Finance Act. |
| **Responsibilities** | Deduction limits (80C: ₹1.5L, 80D: ₹25K/50K, etc.); exemption limits (112A: ₹1.25L, HRA: formula-based); rebate thresholds (87A: ₹12L/₹5L income); surcharge thresholds (₹50L, ₹1Cr, ₹2Cr, ₹5Cr); TDS rate validation; advance tax threshold (₹10K tax above TDS); Section 44AB audit threshold; Section 44AD presumptive turnover limit; carry-forward loss conditions; verify limits against correct FY version |
| **Inputs** | All computations, FY |
| **Outputs** | LimitValidationReport, ThresholdCrossingAlerts |
| **Dependencies** | C12.3 Rule Repository (limits by FY), C4-C7 computation engines |
| **Business Value** | Ensures statutory compliance; prevents excess claims that ITD would disallow |
| **Priority** | **High** |
| **Maturity Target** | All statutory limits per FY; auto-updating from Finance Act changes |

### C8.6 — Anomaly & Risk Detection

| Attribute | Value |
|-----------|-------|
| **Purpose** | Detect unusual patterns, potential errors, and risk indicators in the taxpayer's data. |
| **Responsibilities** | Sudden income changes (>50% YoY without explanation); unusually high deductions relative to income; missing common deductions (no 80C for salaried?); large cash deposits in AIS; frequent high-value transactions; crypto transactions (higher scrutiny); foreign transactions; income from multiple states; employer TDS mismatch patterns; detect potential PAN misuse or identity issues |
| **Inputs** | Current year data, Previous year data, AIS transaction patterns |
| **Outputs** | AnomalyReport, RiskIndicators, ErrorProbabilityScores, ProfessionalReviewFlags |
| **Dependencies** | C2.5 Historical Filing Record, C2.7 Taxpayer Risk Profiling, C4 Income Engines |
| **Business Value** | Proactive error detection; reduces scrutiny risk; when flagged for professional review, protects both taxpayer and platform |
| **Priority** | **High** |
| **Maturity Target** | ML-based anomaly detection trained on ITD scrutiny patterns; explainable risk scores |

### C8.7 — Audit Readiness Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Prepare the taxpayer for potential ITD scrutiny by verifying all supporting evidence is in order. |
| **Responsibilities** | Identify which deductions/claims require supporting documentation; check if evidence has been uploaded/linked; generate evidence checklist for taxpayer; verify PAN of counterparties (landlord, donee); verify TAN of deductors; check Form 26AS for TDS credit confirmation; identify high-scrutiny-risk items (large donations, high HRA claims, large capital losses) |
| **Inputs** | ITR data, Uploaded documents, AIS data, Scrutiny risk indicators |
| **Outputs** | AuditReadinessScore, MissingEvidenceList, HighScrutinyItemAlerts, EvidenceChecklist |
| **Dependencies** | C3.9 Investment Proof Parser, C8.6 Anomaly Detection, C11 Audit & Explainability |
| **Business Value** | If scrutinized, taxpayer has everything ready; reduces panic and professional fees |
| **Priority** | **Medium** |
| **Maturity Target** | Scrutiny scenario simulation; automated response preparation for common scrutiny queries |

### C8.8 — GST Reconciliation (for Business Income)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Reconcile GST turnover with income tax turnover for business income filers. |
| **Responsibilities** | Import GST returns (GSTR-1/GSTR-3B); extract reported turnover; compare with income tax turnover; flag discrepancies; adjust for timing differences (GST vs income tax recognition); compute reconciliation statement |
| **Inputs** | GST returns (JSON/PDF), Income tax turnover, FY |
| **Outputs** | GSTReconciliationReport, TurnoverDiscrepancyAlerts |
| **Dependencies** | C4.3 Business Income Engine, C3.1 Document Ingestion |
| **Business Value** | ITD increasingly cross-references GST and income tax data; reconciliation is a compliance necessity |
| **Priority** | **Medium** |
| **Maturity Target** | Direct GSTN API integration; auto-reconciliation; discrepancy explanation generation |

### C8.9 — Filing Deadline & Compliance Calendar

| Attribute | Value |
|-----------|-------|
| **Purpose** | Track all tax compliance deadlines and alert taxpayer of upcoming and missed deadlines. |
| **Responsibilities** | Maintain compliance calendar: ITR due dates (Jul 31/Oct 31/Nov 30), advance tax dates (Jun 15/Sep 15/Dec 15/Mar 15), belated return deadline (Dec 31), revised return deadline (Dec 31 or 3 months before assessment completion), PAN-Aadhaar linking deadline; personalized alerts based on taxpayer profile; compute consequences of missed deadlines (late fees, interest, loss of carry-forward) |
| **Inputs** | Taxpayer profile, Current date, Filing status |
| **Outputs** | ComplianceCalendar, UpcomingDeadlines, MissedDeadlineAlerts, ConsequenceWarnings |
| **Dependencies** | C2.5 Historical Filing Record, C18 Notification System |
| **Business Value** | Prevents missed deadlines; each missed deadline has financial consequences |
| **Priority** | **High** |
| **Maturity Target** | Personalized calendar; auto-advance tax reminders; multi-channel deadline alerts |

---

*[Document continues with Domains 9-20 in Part 3]*
