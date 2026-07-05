# Enterprise Capability Model — Part 3: Domains 9-16

> **Continuation of Parts 1 & 2**
> **Date:** 2026-07-05

---

## 10. Domain 9: ITR Generation & Filing

### C9.1 — Multi-Form ITR JSON Builder

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate schema-compliant ITR JSON for all ITR form types (ITR-1 through ITR-7). |
| **Responsibilities** | Support ITR-1 (SAHAJ), ITR-2 (non-business with CG), ITR-3 (business full P&L), ITR-4 (SUGAM presumptive), ITR-5 (LLP/firm), ITR-6 (company), ITR-7 (trust/political party); populate all mandatory and applicable optional schedules; correct enum values per ITD schema; correct ISIN handling (INNOTAVAILAB vs INNOTREQUIRD); SecondaryAdd always "Y" or "N"; correct date format (DD/MM/YYYY); correct monetary format; correct segment handling for CG date ranges |
| **Inputs** | UnifiedTaxData, ITR type, Assessment year, ITD schema version |
| **Outputs** | Valid ITR JSON, SchemaVersion, HashValue |
| **Dependencies** | C4 Income Engines, C5 Deduction Engine, C6 Tax Computation, C3.6 AIS Code Classification |
| **Business Value** | Core output — the ITR JSON is what gets filed |
| **Priority** | **Critical** |
| **Maturity Target** | All 7 ITR types; auto-updating to latest ITD schema; template-driven generation |

### C9.2 — ITR-1 (SAHAJ) Builder

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate ITR-1 JSON for salaried individuals with simple income profiles. |
| **Eligibility** | Resident individual, total income ≤₹50L, salary + one house property + interest, no capital gains, no business income, no foreign assets, no crypto, no director, no unlisted shares |
| **Schedules** | Part A (General), Schedule S (Salary), Schedule HP (1 property), Schedule OS (Interest), Schedule VI-A, Part B-TI, Part B-TTI, Schedule Tax Paid, Schedule Bank |
| **Priority** | **Critical** |
| **Maturity Target** | Full ITD JSON Utility compatibility; validated against official schema |

### C9.3 — ITR-2 Builder

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate ITR-2 JSON for individuals/HUFs with capital gains and other non-business income. |
| **Schedules** | All ITR-1 schedules + Schedule 112A (Equity LTCG), Schedule CG (A2 111A STCG, A5 STCG slab, B8 LTCG other, Section F date ranges), Schedule OS (extended), Schedule AL (assets >₹50L), Schedule FA (foreign assets), Schedule FSI (foreign income), Schedule TR (tax relief), Schedule SI (special income), Schedule EI (exempt income), Schedule CYLA/BFLA (losses), Schedule VDA (crypto) |
| **Priority** | **Critical** |
| **Maturity Target** | All 15+ ITR-2 schedules; every AIS income type mapped to correct schedule |

### C9.4 — ITR-3 Builder

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate ITR-3 JSON for individuals/HUFs with business/profession income. |
| **Schedules** | All ITR-2 schedules + Schedule BP (P&L, balance sheet, depreciation, ratios), Schedule GST, Schedule 44AA audit, Schedule 44AB audit report |
| **Priority** | **High** |
| **Maturity Target** | Full P&L + balance sheet; auto-depreciation schedule; presumptive option sub-schedules |

### C9.5 — ITR-4 Builder

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate ITR-4 (SUGAM) JSON for presumptive taxation filers. |
| **Schedules** | Simplified business income (44AD/44ADA/44AE); turnover/gross receipts; presumptive income computation |
| **Priority** | **High** |
| **Maturity Target** | All presumptive sections; auto-detection of presumptive eligibility |

### C9.6 — ITR Filing Workflow

| Attribute | Value |
|-----------|-------|
| **Purpose** | Guide the taxpayer through the complete filing process from JSON download to e-verification. |
| **Responsibilities** | Generate portal-specific step-by-step filing instructions; pre-filing checklist; payment instructions (if balance payable); upload instructions with exact button names; verification instructions (Aadhaar OTP, net banking, Demat, ITR-V); post-filing tracking (acknowledgement, refund status); revised return workflow; grievance workflow for portal errors |
| **Inputs** | Generated ITR JSON, Tax liability, Filing type (Original/Revised/Belated) |
| **Outputs** | FilingInstructions (context-aware), PaymentChallan, AcknowledgementTracker |
| **Dependencies** | C9.1 Multi-Form Builder, C18 Notification System |
| **Business Value** | Reduces support burden; users succeed without CA help |
| **Priority** | **High** |
| **Maturity Target** | Screen-by-screen portal guidance with screenshots; error recovery steps for known portal errors |

### C9.7 — JSON Rejection Handler

| Attribute | Value |
|-----------|-------|
| **Purpose** | Handle ITD portal JSON rejections intelligently — diagnose, fix, regenerate without re-entering data. |
| **Responsibilities** | Parse ITD portal error messages; pattern-match against known error library; auto-fix common errors (enum values, rounding, cross-schedule consistency); regenerate fixed JSON; escalate unknown errors to support with full context; build error pattern library over time; user-friendly error explanations |
| **Inputs** | ITD portal error message/text, Original ITR JSON, Session data |
| **Outputs** | FixedITRJSON, ErrorDiagnosis, FixApplied, SupportTicket (if unknown error) |
| **Dependencies** | C8.3 ITR Schema Validator, C9.1 Multi-Form Builder |
| **Business Value** | Turns portal rejections from dead-ends into auto-resolved; major UX differentiator |
| **Priority** | **High** |
| **Maturity Target** | Auto-fix 95%+ of known error patterns; ML-based unknown error classification |

---

## 11. Domain 10: Audit & Explainability

### C10.1 — Computation Audit Trail

| Attribute | Value |
|-----------|-------|
| **Purpose** | Record every step of every tax computation in an immutable, queryable audit trail. |
| **Responsibilities** | Capture every intermediate computation: input values, rule applied (with legal provision reference), formula, output value, timestamp; generate unique computation ID; support replay — recompute and verify result matches; version every audit trail entry with rule version used; support comparison — what changed between two computations?; store in append-only event log |
| **Inputs** | Every computation step, Rule metadata, Input values, Computation context |
| **Outputs** | ImmutableAuditTrail, ComputationProof, ReplayVerification |
| **Dependencies** | C6 Computation Engine, C12 Rule Management, C17.6 Data Integrity |
| **Business Value** | Regulatory requirement; enables CA review; proves correctness if scrutinized; builds trust |
| **Priority** | **Critical** |
| **Maturity Target** | Blockchain-anchored hash for immutability proof; exportable audit trail for ITD scrutiny response |

### C10.2 — Plain-Language Explanation Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate human-readable explanations of every tax computation in plain English (and other Indian languages). |
| **Responsibilities** | Explain each component: "Your tax is ₹X because your income of ₹Y falls in the Z% tax bracket for income between ₹A and ₹B"; explain deductions: "₹50,000 standard deduction was applied, reducing your taxable salary from ₹X to ₹Y"; explain regime recommendation: "New Regime saves you ₹X because..."; multi-level explanations (summary for taxpayer, detail for CA, technical for auditor); template-based generation with data insertion; multi-language support (English, Hindi, Marathi, Tamil, etc.) |
| **Inputs** | Computation results, Audit trail data, Rule metadata, User's language preference |
| **Outputs** | HumanReadableExplanation (per component, multi-level, multi-language) |
| **Dependencies** | C10.1 Audit Trail, C11.2 Tax Provision Knowledge Base, C14 Reporting |
| **Business Value** | Demystifies tax for laypersons; builds trust; reduces CA dependency for basic understanding |
| **Priority** | **Critical** |
| **Maturity Target** | Natural language generation at 3 detail levels; 10+ Indian languages; CA-quality technical explanations |

### C10.3 — Legal Provision Tracer

| Attribute | Value |
|-----------|-------|
| **Purpose** | Trace every tax computation result directly to the specific legal provision that governs it. |
| **Responsibilities** | Link every computation to exact section/sub-section/clause of the Income Tax Act; link to Finance Act amendment that introduced/modified the provision; link to CBDT circular/notification if applicable; show provision evolution (how this rule changed across FYs); provide full text of relevant provision; highlight key phrases in provision text |
| **Inputs** | Computation step, Applicable section, FY |
| **Outputs** | LegalProvisionReference (section text, amendment history, CBDT circulars) |
| **Dependencies** | C11.2 Tax Provision Knowledge Base, C12.3 Rule Repository |
| **Business Value** | Gives CA and taxpayer confidence in correctness; essential for scrutiny defense |
| **Priority** | **High** |
| **Maturity Target** | Full Income Tax Act text linked to every rule; Finance Act amendment trail; CBDT circular cross-reference |

### C10.4 — Computation Verification & Self-Test

| Attribute | Value |
|-----------|-------|
| **Purpose** | Independently verify tax computation correctness through alternative calculation paths. |
| **Responsibilities** | Independent recomputation using alternative method (e.g., manual formula vs rule engine); cross-check totals (income heads sum = GTI, GTI - deductions = TI); cross-check with ITD calculator if available; golden-test-vector comparison for known inputs; flag any discrepancy >₹1 for investigation; regression test against previous year computation patterns |
| **Inputs** | Tax computation result, Alternative computation method, Golden test vectors |
| **Outputs** | VerificationReport, DiscrepanciesFound, ConfidenceScore |
| **Dependencies** | C6 Tax Computation Engine, C10.1 Audit Trail |
| **Business Value** | Catches computation bugs before they reach ITD; builds internal quality assurance |
| **Priority** | **High** |
| **Maturity Target** | Automated dual-path verification; statistical anomaly detection across all computations |

### C10.5 — Professional (CA) Review Mode

| Attribute | Value |
|-----------|-------|
| **Purpose** | Provide a CA-optimized view of the computation with drill-down to every detail. |
| **Responsibilities** | Schedule-by-schedule breakdown; per-section tax computation; deduction limit utilization with remaining capacity; regime comparison with sensitivity analysis; cross-year comparison; export to CA workpaper format; annotation capability (CA can add notes); client-ready summary export |
| **Inputs** | Complete computation data, CA preferences, Previous year data |
| **Outputs** | CAReviewDashboard, ScheduleBreakdowns, ClientSummary, WorkpaperExport |
| **Dependencies** | C10.1 Audit Trail, C10.2 Explanation Engine, C14 Reporting |
| **Business Value** | Enables CA to verify and sign off efficiently; platform adoption by professionals |
| **Priority** | **Medium** |
| **Maturity Target** | CA workpaper format (Excel/PDF); annotation workflow; bulk client review |

### C10.6 — Explainable AI for AI-Assisted Decisions

| Attribute | Value |
|-----------|-------|
| **Purpose** | Provide transparency into any AI-assisted recommendations or decisions. |
| **Responsibilities** | Explain AI recommendations (e.g., "We recommend X because of factors A, B, C with weights W1, W2, W3"); provide confidence scores; identify data gaps that reduce confidence; show alternative scenarios if key inputs change; never make definitive tax decisions — always present as recommendation with reasoning |
| **Inputs** | AI model output, Input features, Model metadata |
| **Outputs** | AIExplanation (factors, weights, confidence, alternatives) |
| **Dependencies** | C10.2 Explanation Engine, C7.6 Regime Comparison Visualization |
| **Business Value** | Regulatory requirement for AI in finance; builds trust in AI-assisted decisions |
| **Priority** | **Critical** |
| **Maturity Target** | SHAP/LIME-style feature attribution; counterfactual explanations; audit-grade model documentation |

---

## 12. Domain 11: Knowledge Management

### C11.1 — Tax Knowledge Graph

| Attribute | Value |
|-----------|-------|
| **Purpose** | Maintain a semantic knowledge graph connecting tax concepts, provisions, rules, forms, and their relationships. |
| **Responsibilities** | Model entities: Sections, Subsections, Clauses, Rules, Notifications, Circulars; model relationships: "Section 80C contains PPF, ELSS, LIC...", "Section 112A applies to equity LTCG with STT paid", "Section 115BAC overrides old regime slabs"; model conditions: "80D(self, non-senior, health_insurance_premium) → max ₹25,000"; model FY applicability; support graph queries: "What deductions are available for senior citizen under New Regime?"; support traversal for interview engine and explanation engine |
| **Inputs** | Income Tax Act, Finance Acts, CBDT circulars, Rules, Notifications, ITR form schemas |
| **Outputs** | KnowledgeGraph, GraphQueries, InferredRelationships |
| **Dependencies** | C12.2 Tax Provision Ingestion, C10.2 Explanation Engine, C13.2 Adaptive Question Engine |
| **Business Value** | Single source of truth for all tax knowledge; powers explainability, interview, and rule engine |
| **Priority** | **Critical** |
| **Maturity Target** | Complete IT Act semantic model; automated ingestion from new Finance Acts; graph-powered natural language Q&A |

### C11.2 — Tax Provision Knowledge Base

| Attribute | Value |
|-----------|-------|
| **Purpose** | Maintain a structured, versioned database of all tax provisions with full text, effective dates, and metadata. |
| **Responsibilities** | Store full text of every section of the Income Tax Act; store every Finance Act amendment with effective dates; store all CBDT circulars, notifications, and clarifications; store all IT Rules; maintain provision version history across FYs; link provisions to implementing code/rules; semantic search across provisions |
| **Inputs** | Income Tax Act, Finance Acts (annual), CBDT circulars, IT Rules, Case law (optional) |
| **Outputs** | TaxProvision (with version history), ProvisionSearch, ProvisionApplicability (by FY) |
| **Dependencies** | C12.1 Finance Act Versioning |
| **Business Value** | Foundation for all tax logic; ensures every computation is legally grounded |
| **Priority** | **Critical** |
| **Maturity Target** | Complete IT Act with all amendments; semantic search; automated CBDT circular ingestion |

### C11.3 — Finance Act Change Analyzer

| Attribute | Value |
|-----------|-------|
| **Purpose** | Analyze new Finance Acts/Bills to identify changes that impact the platform's tax logic. |
| **Responsibilities** | Compare new Finance Act with previous version; identify new sections, amended sections, repealed sections; identify changed rates, limits, thresholds; identify new deduction/exemption provisions; identify procedural changes (due dates, forms, filing requirements); generate impact assessment for engineering team; prioritize changes by taxpayer impact |
| **Inputs** | New Finance Act/Bill text, Previous Finance Act, Current rule implementations |
| **Outputs** | ChangeImpactReport, AffectedRules, AffectedModules, ImplementationPriority |
| **Dependencies** | C12.1 Finance Act Versioning, C12.3 Rule Repository |
| **Business Value** | Critical for annual update cycle; reduces time from Budget to implementation |
| **Priority** | **High** |
| **Maturity Target** | AI-assisted Finance Act diffing; auto-identification of impacted rules; implementation effort estimation |

### C11.4 — Tax Concept Glossary & Ontology

| Attribute | Value |
|-----------|-------|
| **Purpose** | Maintain a controlled vocabulary of tax terms with definitions, synonyms, and relationships. |
| **Responsibilities** | Define all tax terms (assessment year, financial year, total income, gross total income, deduction vs exemption vs rebate, residential status types, ITR form types, income heads, capital gain types); map synonyms ("taxable income" = "total income"); map Hindi and regional language equivalents; disambiguate overloaded terms ("assessment" = assessment year vs scrutiny assessment) |
| **Inputs** | Income Tax Act definitions, CBDT practice, CA domain expertise |
| **Outputs** | ControlledVocabulary, SynonymMap, MultiLanguageTerms |
| **Dependencies** | C11.1 Tax Knowledge Graph |
| **Business Value** | Ensures consistent terminology across UI, explanations, documentation; powers accurate search |
| **Priority** | **Medium** |
| **Maturity Target** | Complete bilingual (English-Hindi) ontology; 22 scheduled languages long-term |

### C11.5 — CBDT Circular & Judicial Precedent Database

| Attribute | Value |
|-----------|-------|
| **Purpose** | Track CBDT circulars, notifications, and key judicial precedents that clarify tax law interpretation. |
| **Responsibilities** | Ingest CBDT circulars (clarificatory); ingest notifications (rule amendments, threshold changes); track key Supreme Court and High Court judgments that affect interpretation; link circulars/precedents to the provisions they interpret; flag when a circular changes the interpretation of a provision already implemented |
| **Inputs** | CBDT website, e-Gazette, Supreme Court/High Court judgment databases |
| **Outputs** | CircularDatabase, PrecedentDatabase, InterpretationGuidance |
| **Dependencies** | C11.2 Tax Provision Knowledge Base, C12.1 Finance Act Versioning |
| **Business Value** | Tax law is as much about interpretation as statute; CBDT circulars are binding on ITD |
| **Priority** | **Medium** |
| **Maturity Target** | Auto-ingestion pipeline; semantic linking of circulars to provisions; impact flagging |

### C11.6 — Taxpayer Education Content Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate and curate educational content to improve taxpayer financial literacy. |
| **Responsibilities** | Topic-based articles ("How HRA Exemption Works", "Understanding Capital Gains Tax"); FAQ generation from common user questions; video script generation; interactive learning modules; personalized content based on taxpayer profile and filing stage; multilingual content |
| **Inputs** | Tax knowledge base, Common user questions, Taxpayer profile |
| **Outputs** | EducationalArticles, FAQs, VideoScripts, InteractiveModules |
| **Dependencies** | C11.1 Tax Knowledge Graph, C11.2 Tax Provision Knowledge Base, C13 AI Interview Engine |
| **Business Value** | Empowers taxpayers; reduces support burden; builds platform authority |
| **Priority** | **Medium** |
| **Maturity Target** | AI-generated personalized tax guides; adaptive learning paths; content in 10+ languages |

---

## 13. Domain 12: Rule Management

### C12.1 — Finance Act Versioning

| Attribute | Value |
|-----------|-------|
| **Purpose** | Version all tax rules, rates, limits, and thresholds by Finance Act and financial year. |
| **Responsibilities** | Maintain Finance Act registry (FY2020-21 through current + future); store effective date ranges for every rule; support parallel operation of multiple FYs simultaneously; enable comparison of any rule across FYs; track rule lineage (which rule superseded which); deprecate rules with explicit end dates; archive superseded rules for historical computation |
| **Inputs** | Finance Act text, CBDT notifications, Rule effective dates |
| **Outputs** | FinanceActRegistry, RuleVersionHistory, CrossYearComparison |
| **Dependencies** | C11.2 Tax Provision Knowledge Base |
| **Business Value** | Architectural invariant — must support any FY without code change; foundation for compliance |
| **Priority** | **Critical** |
| **Maturity Target** | Complete FY2020-21 to FY2030-31 rule database; automated Finance Act ingestion pipeline |

### C12.2 — Rule Definition Language/Format

| Attribute | Value |
|-----------|-------|
| **Purpose** | Define a declarative format for tax rules that is human-readable, machine-executable, and version-controllable. |
| **Responsibilities** | Define rule schema: rule_id, section, FY, regime, conditions, formula, effective_from, effective_until, supersedes, metadata; support rule types: slab_rules (progressive rates), threshold_rules (if income > X then apply Y), limit_rules (max deduction = Z), formula_rules (HRA = min(A, B, C)), condition_rules (if senior_citizen then basic_exemption = ₹3L); support rule composition (rules that reference other rules); support rule conflict detection (two rules producing different results for same input) |
| **Inputs** | Tax law provisions, Domain expert interpretation |
| **Outputs** | RuleDefinition (in canonical format), RuleSchema, RuleValidation |
| **Dependencies** | C12.1 Finance Act Versioning, C11.2 Tax Provision Knowledge Base |
| **Business Value** | Separates tax rules from computation engine; enables non-programmer rule authors; version-controllable |
| **Priority** | **Critical** |
| **Maturity Target** | Declarative rule DSL; visual rule editor; automated rule testing against ITD portal reference computations |

### C12.3 — Rule Repository

| Attribute | Value |
|-----------|-------|
| **Purpose** | Central repository for all tax rules, queryable by FY, regime, section, income type, and taxpayer context. |
| **Responsibilities** | Store all rules organized by FY → Regime → Section → Rule; support FY-range queries: "all active rules for FY2025-26"; support context-sensitive rule retrieval: "what deductions apply to a senior citizen salaried individual under Old Regime?"; cache frequently accessed rules; provide rule change notifications to dependent systems; version all rule changes with audit trail |
| **Inputs** | Rule definitions, FY, Regime, Query context |
| **Outputs** | ApplicableRules (for context), RuleSet (for FY+Regime), RuleHistory |
| **Dependencies** | C12.1 Finance Act Versioning, C12.2 Rule Definition Language |
| **Business Value** | Single source of truth for all tax rules; every computation gets the right rules for the right FY |
| **Priority** | **Critical** |
| **Maturity Target** | Hot-reloadable rule updates; rule A/B testing; rule performance monitoring |

### C12.4 — Rule Evaluation Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Execute tax rules against taxpayer data and produce deterministic, auditable results. |
| **Responsibilities** | Load applicable rules for computation context (FY, regime, taxpayer profile); evaluate rules in correct dependency order; handle rule dependencies and prerequisites; handle conflicting rules (more specific wins); optimize repeated evaluations; cache intermediate results; log every rule evaluation for audit trail; support partial re-evaluation (if one input changes) |
| **Inputs** | Taxpayer data context, Rule set, Computation configuration |
| **Outputs** | RuleEvaluationResults, EvaluationTrace, AuditLog |
| **Dependencies** | C12.3 Rule Repository, C12.6 Rule Conflict Resolution |
| **Business Value** | Executes tax logic; must be 100% correct, 100% deterministic, 100% auditable |
| **Priority** | **Critical** |
| **Maturity Target** | Rete algorithm or similar for complex rule chains; sub-millisecond rule evaluation; parallel evaluation |

### C12.5 — Rule Testing Framework

| Attribute | Value |
|-----------|-------|
| **Purpose** | Comprehensive testing framework for tax rules against known test vectors and ITD reference computations. |
| **Responsibilities** | Define test cases per rule: happy path, boundary values (threshold-1, threshold, threshold+1), edge cases, exception paths; golden-test-vector comparison (known inputs → known output verified against ITD portal); regression test suite (all existing rules still produce same output); cross-year test isolation (FY2025-26 rule changes don't affect FY2024-25 results); automated rule validation before deployment |
| **Inputs** | Rule definitions, Test vectors, ITD reference computations |
| **Outputs** | TestResults, RegressionReport, GoldenVectorComparison |
| **Dependencies** | C12.4 Rule Evaluation Engine, C20 Testing Infrastructure |
| **Business Value** | Prevents tax computation errors; each rule change is verified before deployment |
| **Priority** | **High** |
| **Maturity Target** | 100% rule test coverage; automated golden-vector generation from ITD portal; CI/CD integration |

### C12.6 — Rule Conflict Detection & Resolution

| Attribute | Value |
|-----------|-------|
| **Purpose** | Detect when two or more rules could apply to the same situation and produce conflicting results. |
| **Responsibilities** | Static analysis: detect rules with overlapping conditions; runtime detection: flag when multiple rules fire and produce different results; resolution strategies: specificity (most specific rule wins), recency (newest rule wins within same FY), explicit priority (rule metadata defines priority); alert on unresolved conflicts; prevent deployment of conflicting rule sets |
| **Inputs** | Rule definitions, Rule evaluation results |
| **Outputs** | ConflictReport, ResolutionApplied, UnresolvedConflicts |
| **Dependencies** | C12.3 Rule Repository, C12.4 Rule Evaluation Engine |
| **Business Value** | Tax law is complex — multiple sections can apply; must resolve correctly |
| **Priority** | **High** |
| **Maturity Target** | Automated conflict detection in CI; resolution audit trail; conflict visualization |

### C12.7 — Rule Change Impact Analysis

| Attribute | Value |
|-----------|-------|
| **Purpose** | When a rule changes, identify all downstream impacts on computations, ITR schedules, and affected taxpayers. |
| **Responsibilities** | Trace rule dependencies: which other rules reference this rule's output? Which ITR schedules are affected? Which taxpayer segments are affected?; estimate tax impact distribution (how many taxpayers see tax change, by how much); identify affected test cases; generate impact report for domain expert review |
| **Inputs** | Changed rule, Rule dependency graph, Historical computation data (anonymized) |
| **Outputs** | ImpactAnalysisReport, AffectedRules, AffectedTaxpayerSegments, TestCaseUpdateList |
| **Dependencies** | C12.3 Rule Repository, C12.4 Rule Evaluation Engine, C11.1 Tax Knowledge Graph |
| **Business Value** | Before changing any rule, understand exactly what changes downstream |
| **Priority** | **Medium** |
| **Maturity Target** | Automated impact simulation; taxpayer impact distribution analysis; regression test auto-generation |

---

## 14. Domain 13: AI Interview Engine

### C13.1 — Interview Session Manager

| Attribute | Value |
|-----------|-------|
| **Purpose** | Manage the lifecycle of tax data collection interviews with state persistence, resume capability, and progress tracking. |
| **Responsibilities** | Create interview session per filing; track interview state (phase, current question, answers given); persist state for resume across sessions/devices; estimate remaining time/questions; provide progress indicator; support session expiry with data preservation; support multi-session for taxpayer with multiple filings |
| **Inputs** | Taxpayer profile, ITR type, Document data, Previous session state |
| **Outputs** | InterviewSession, InterviewState, ProgressEstimate |
| **Dependencies** | C2.1 Taxpayer Profile, C1.4 Session Management, C9.1 ITR Builder |
| **Business Value** | Users can pause/resume; never lose entered data; clear progress awareness |
| **Priority** | **High** |
| **Maturity Target** | Cross-device resume; offline-capable interview with sync |

### C13.2 — Adaptive Question Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate the minimal set of questions needed based on what has been auto-detected from documents, with intelligent branching. |
| **Responsibilities** | Analyze detected data — what do we already know? Generate questions only for what we don't know; suppress questions when irrelevant (no HRA questions if user has no HRA); branch based on answers (if "do you pay rent?" = No → skip rent amount questions); adapt question flow based on ITR type (ITR-1 gets 0-3 questions, ITR-3 gets 10-15 for business income); respect regime (no 80C questions for New Regime); auto-detect question relevance from document data |
| **Inputs** | Parsed document data (Form 16, AIS), ITR type, Regime, Taxpayer profile, Previous answers |
| **Outputs** | QuestionSequence, BranchingLogic, SuppressedQuestions (with reasons) |
| **Dependencies** | C3 Document Intelligence, C2.1 Taxpayer Profile, C7.1 Regime Comparison, C11.1 Tax Knowledge Graph |
| **Business Value** | Core UX — 0-5 questions for simple cases instead of 100-field portal form |
| **Priority** | **Critical** |
| **Maturity Target** | Zero-question filing for fully-detected cases; AI-powered question relevance prediction |

### C13.3 — Question Design Framework

| Attribute | Value |
|-----------|-------|
| **Purpose** | Design and manage the question library with metadata, validation, and multi-language support. |
| **Responsibilities** | Question types: yes_no, numeric, date, single_select, multi_select, file_upload, table_input, confirmation, information_display, computed_display; question metadata: id, text (multi-language), help_text, why_asked, impact_description, validation_rules, dependencies, applicable_conditions; question versioning; A/B testing support for question variants; question effectiveness tracking (completion rate, error rate, time spent) |
| **Inputs** | Question definitions, UX research, User feedback, Completion analytics |
| **Outputs** | QuestionLibrary, QuestionMetadata, MultiLanguageText |
| **Dependencies** | C13.2 Adaptive Question Engine, C11.4 Tax Concept Glossary |
| **Business Value** | Well-designed questions = better data = correct tax = satisfied users |
| **Priority** | **High** |
| **Maturity Target** | 200+ question library; A/B-optimized question variants; accessibility-optimized (WCAG AA) |

### C13.4 — Auto-Detection & Prefill Engine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Maximize data auto-detection from documents to minimize manual entry. |
| **Responsibilities** | Extract all auto-detectable fields from Form 16 (salary, exemptions, deductions, TDS, employer); extract from AIS (interest, capital gains, dividends, refunds, personal info); extract from previous year ITR (carry-forward data, recurring deductions, bank accounts); extract from broker statements (capital gains detail); compute derived values (regime from Form 16 115BAC checkbox, ITR type from income sources); assign confidence score to each auto-detected field; show detected values for confirmation, not re-entry |
| **Inputs** | All parsed documents, Previous year data, Taxpayer profile |
| **Outputs** | AutoDetectedData (with confidence scores), PrefillSuggestions |
| **Dependencies** | C3 Document Intelligence, C2.5 Historical Filing Record, C6 Computation Engine |
| **Business Value** | "If the data exists in documents, the user never types it" — core value prop |
| **Priority** | **Critical** |
| **Maturity Target** | >95% auto-detection rate for ITR-1/2; confidence-based review highlighting |

### C13.5 — Real-Time Validation & Feedback

| Attribute | Value |
|-----------|-------|
| **Purpose** | Validate user inputs in real-time with immediate, helpful feedback during the interview. |
| **Responsibilities** | Type validation (is this a valid number? date? PAN format?); range validation (80C > ₹1.5L? salary > 0?); logical validation (TDS > gross salary? interest rate > 50%?); cross-field validation (HRA claimed but no rent declared?); provide immediate fix suggestions; prevent impossible values from being entered; warn on unusual but possible values |
| **Inputs** | User input, Field metadata, Related field values, Statutory limits |
| **Outputs** | ValidationResult (per field), FixSuggestion, WarningMessage |
| **Dependencies** | C8.3 Schema Validator, C8.5 Regulatory Limit Validator |
| **Business Value** | Prevents errors at entry time rather than at submission time; better UX |
| **Priority** | **High** |
| **Maturity Target** | Instant validation (<100ms); contextual fix suggestions; ML-based anomaly detection in inputs |

### C13.6 — Interview Personalization

| Attribute | Value |
|-----------|-------|
| **Purpose** | Personalize the interview experience based on taxpayer segment, history, and behavior. |
| **Responsibilities** | Segment-based personalization (salaried vs business vs investor vs NRI vs senior citizen); experience-based (first-time filer gets more explanations, returning filer gets streamlined); language preference (question text, explanations, currency format); complexity preference (show me everything vs guide me); accessibility needs (screen reader optimized, keyboard navigation, high contrast) |
| **Inputs** | Taxpayer profile, Filing history, User preferences, Behavioral data |
| **Outputs** | PersonalizedInterviewConfig, SegmentSpecificQuestions, LanguageLocalization |
| **Dependencies** | C2 Taxpayer Management, C13.2 Adaptive Question Engine, C11.4 Tax Concept Glossary |
| **Business Value** | Different taxpayers need different experiences; one-size-fits-all interview fails |
| **Priority** | **Medium** |
| **Maturity Target** | ML-driven personalization from user behavior; accessibility WCAG AAA compliance |

### C13.7 — Document-Guided Interview

| Attribute | Value |
|-----------|-------|
| **Purpose** | Use uploaded documents to guide the interview — highlight what was found and what's missing. |
| **Responsibilities** | After document parsing, present: "We found: Salary ₹X from Form 16, Capital gains from Y transactions in AIS, Interest ₹Z from bank statements"; "We need your input on: HRA (rent details), 80C investments beyond EPF, Medical insurance premiums"; document-to-question traceability — "This question is asked because your Form 16 shows HRA of ₹X" |
| **Inputs** | Parsed documents, Auto-detected data, Missing data gaps |
| **Outputs** | DocumentSummary, DataGapsList, QuestionJustifications |
| **Dependencies** | C13.4 Auto-Detection Engine, C13.2 Adaptive Question Engine |
| **Business Value** | Transparency builds trust; users understand why each question is asked |
| **Priority** | **Medium** |
| **Maturity Target** | Interactive document highlighting tied to questions; "here's where we found this in your Form 16" |

### C13.8 — Offline Interview Capability

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable interview completion without continuous internet connectivity, with sync when reconnected. |
| **Responsibilities** | Offline-capable question engine (all logic local); local data storage (encrypted); conflict resolution on sync (server state vs local state); bandwidth-efficient sync (only changed data); background sync when connectivity restored; progress indicator for sync status |
| **Inputs** | Offline interview data, Last synced state, Network availability |
| **Outputs** | SyncedInterviewData, ConflictResolutionLog |
| **Dependencies** | C13.1 Session Manager, C17.4 Data Encryption |
| **Business Value** | Indian internet is unreliable; filing shouldn't require continuous connectivity |
| **Priority** | **Medium** |
| **Maturity Target** | Full offline PWA; encrypted local storage; delta sync protocol |

---

## 15. Domain 14: Reporting & Analytics

### C15.1 — Tax Summary & Dashboard

| Attribute | Value |
|-----------|-------|
| **Purpose** | Provide a comprehensive, actionable tax summary and dashboard for taxpayers and professionals. |
| **Responsibilities** | One-page tax summary (income breakup, deductions, tax, TDS, balance payable/refund); year-over-year comparison; effective tax rate trend; deduction utilization dashboard; tax credit dashboard; filing status tracker; upcoming deadlines; personalized insights ("Your effective tax rate decreased by 2.3% this year") |
| **Inputs** | Tax computation results, Historical filing data, Compliance calendar |
| **Outputs** | TaxSummary, TaxDashboard, PersonalizedInsights |
| **Dependencies** | C6 Tax Computation, C2.5 Historical Filing Record, C8.9 Compliance Calendar |
| **Business Value** | Gives taxpayer a clear picture of their tax situation at a glance |
| **Priority** | **High** |
| **Maturity Target** | Interactive dashboard with drill-down; customizable views for taxpayer vs CA |

### C15.2 — Comparative Analytics (Peer & Segment)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Provide anonymized peer and segment comparisons for context. |
| **Responsibilities** | Compare taxpayer's effective tax rate with similarly situated taxpayers (same income band, same city, same age group); compare deduction utilization with peers ("Your 80C utilization is 60% vs 85% average for your income group"); identify outlier patterns; strictly anonymized — no individual data exposed; opt-in only with explicit consent |
| **Inputs** | Anonymized aggregate data, Taxpayer computation, Consent flag |
| **Outputs** | PeerComparison, SegmentBenchmarks, OutlierFlags |
| **Dependencies** | C17.3 Data Privacy, C17.8 Compliance Framework |
| **Business Value** | Context for taxpayers; identifies optimization opportunities; drives engagement |
| **Priority** | **Low** |
| **Maturity Target** | Privacy-preserving federated analytics; segment-specific benchmarks |

### C15.3 — Regulatory & Compliance Reporting

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate reports required for regulatory compliance, audits, and enterprise governance. |
| **Responsibilities** | Compliance certificate generation; audit-ready computation reports; data processing activity logs; consent audit reports; security incident reports; filing volume reports; system uptime reports; SLA compliance reports |
| **Inputs** | System logs, Audit trails, Computation data, Security event logs |
| **Outputs** | ComplianceReports, AuditReports, SLADashboards |
| **Dependencies** | C10.1 Audit Trail, C17.8 Compliance Framework, C16 Administration |
| **Business Value** | Required for ISO 27001, SOC 2, DPDP Act compliance; enterprise customer requirement |
| **Priority** | **High** |
| **Maturity Target** | Auto-generated compliance reports; scheduled report distribution; auditor access portal |

### C15.4 — Export & Data Portability

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable taxpayers to export their data in standard formats for portability and record-keeping. |
| **Responsibilities** | Export ITR JSON; export computation PDF; export detailed Excel workpaper; export raw parsed data (JSON/CSV); export audit trail; export all uploaded documents in organized ZIP; support DPDP Act data portability requirements; schedule automatic annual export |
| **Inputs** | All taxpayer data, Export format request |
| **Outputs** | Exported files in requested format, Export manifest |
| **Dependencies** | C10.1 Audit Trail, C3 Document Intelligence, C17.3 Data Privacy |
| **Business Value** | Data portability is a legal right under DPDP Act; practical value for CA handoff |
| **Priority** | **High** |
| **Maturity Target** | One-click full data export; scheduled exports; direct CA portal sharing |

### C15.5 — Business Intelligence & Analytics (Platform Operator)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Provide platform operators with business intelligence on usage, performance, and trends. |
| **Responsibilities** | User acquisition and retention metrics; filing completion funnel; feature usage analytics; error and rejection analytics; performance monitoring dashboards; revenue analytics (if monetized); support ticket analytics; A/B test result analytics |
| **Inputs** | Application logs, User events, Business metrics |
| **Outputs** | BIDashboards, TrendReports, FunnelAnalytics |
| **Dependencies** | C16 Administration & Operations |
| **Business Value** | Data-driven product decisions; identifies UX friction; business health monitoring |
| **Priority** | **Medium** |
| **Maturity Target** | Real-time analytics pipeline; predictive user behavior modeling |

### C15.6 — Custom Report Builder

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable CAs and enterprise users to build custom reports for their specific needs. |
| **Responsibilities** | Drag-and-drop report builder; predefined report templates (ITR comparison, deduction summary, client portfolio); custom filtering and grouping; scheduled report generation; report sharing with clients; branded report export |
| **Inputs** | Report template/configuration, Data filters, Schedule |
| **Outputs** | CustomReport, ScheduledReportDelivery |
| **Dependencies** | C14.1 Tax Summary, C2.5 Historical Filing Record, C20 Enterprise Multi-Tenancy |
| **Business Value** | CA firms have specific reporting needs; custom reports = stickiness |
| **Priority** | **Medium** |
| **Maturity Target** | Template marketplace; white-label CA firm branding |

### C15.7 — Refund & Payment Tracker

| Attribute | Value |
|-----------|-------|
| **Purpose** | Track tax refunds and payments from filing through credit. |
| **Responsibilities** | Track refund status (filed → processed → refund issued → credited); estimate refund timeline based on historical patterns; detect refund delays (beyond normal processing time); track demand/outstanding tax payments; reconcile refund with AIS Part B4 data; alert on refund credited; alert on demand notice issued |
| **Inputs** | Filing data, ITD refund status, Bank statement (refund credit), AIS Part B4 |
| **Outputs** | RefundTracker, PaymentTracker, StatusAlerts |
| **Dependencies** | C2.5 Historical Filing Record, C15.4 ITD API Integration, C18 Notification System |
| **Business Value** | "Where is my refund?" is the #1 post-filing question |
| **Priority** | **Medium** |
| **Maturity Target** | Automated ITD refund status polling; bank integration for refund credit detection |

---

## 16. Domain 15: Integration & External APIs

### C16.1 — API Gateway & Management

| Attribute | Value |
|-----------|-------|
| **Purpose** | Expose platform capabilities as versioned, documented, rate-limited APIs for internal and external consumers. |
| **Responsibilities** | RESTful API with OpenAPI 3.0 specification; API versioning (URI path: /v1/, /v2/); authentication (API keys, OAuth 2.0); rate limiting (per consumer, per endpoint); request/response logging; API analytics (usage, latency, errors); API documentation portal; SDK generation (Python, JavaScript); webhook support |
| **Inputs** | API requests, Consumer credentials |
| **Outputs** | API responses, Rate limit headers, API logs |
| **Dependencies** | C1.2 Authentication, C1.3 Authorization, C17 Security |
| **Business Value** | Enables integrations with CA software, fintech apps, employer portals; platform extensibility |
| **Priority** | **Critical** |
| **Maturity Target** | GraphQL for flexible queries; gRPC for internal high-throughput; API marketplace |

### C16.2 — External Tax Authority APIs

| Attribute | Value |
|-----------|-------|
| **Purpose** | Integrate with Government of India tax authority APIs for data fetch, verification, and filing. |
| **Responsibilities** | NSDL PAN Verification API; ITD e-Filing API (when ERI license obtained); TRACES API (Form 26AS fetch); GSTN API (GST return data); UIDAI Aadhaar e-KYC API; Account Aggregator framework (RBI-regulated consent-based financial data); CBDT notification API; MCA API (company data for ITR-6) |
| **Inputs** | API requests with required authentication (DSC, API keys, consent tokens) |
| **Outputs** | Verified identity data, Tax credit data, Financial transaction data, Filing confirmation |
| **Dependencies** | C1.1 Registration (PAN verification), C1.8 Consent Management (AA framework), ERI license |
| **Business Value** | Direct API access eliminates document upload; fetches authoritative data from source |
| **Priority** | **High** |
| **Maturity Target** | Full AA framework integration; direct ITD API filing; zero-document auto-filing for simple cases |

### C16.3 — Financial Institution Integration

| Attribute | Value |
|-----------|-------|
| **Purpose** | Integrate with banks, brokers, mutual fund platforms, and insurance companies for automatic data fetch. |
| **Responsibilities** | Bank integration (savings/FD interest statements); broker integration (Zerodha, Groww, Upstox, Angel One, ICICI Direct, HDFC Securities, Kotak Securities, 5paisa, etc.); mutual fund platform integration (CAMS, KFintech, MF Central); insurance integration (LIC, HDFC Life, etc.); NPS integration (NSDL/CRA); home loan lender integration; employer/HRMS integration for Form 16 |
| **Inputs** | User credentials (with consent), API tokens, CAS statements |
| **Outputs** | Auto-fetched financial data, Standardized transaction records |
| **Dependencies** | C1.8 Consent Management, C17 Security, C3 Document Intelligence |
| **Business Value** | Ultimate vision: user enters PAN → everything auto-fetched → review → file |
| **Priority** | **High** |
| **Maturity Target** | 10+ broker integrations; CAMS/KFintech CAS auto-fetch; AA framework for bank data |

### C16.4 — Employer/Enterprise Integration

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable employers to push Form 16 data directly to the platform for their employees. |
| **Responsibilities** | Employer portal for bulk Form 16 upload; TRACES-format Form 16 acceptance; employer-specific deduction policies (car lease, meal card, NPS); employee invite flow (employer invites → employee files); employer dashboard (filing completion status across employees, anonymized) |
| **Inputs** | Form 16 data (TRACES format or API), Employee roster, Employer-specific policies |
| **Outputs** | EmployeePrePopulatedProfiles, EmployerFilingDashboard |
| **Dependencies** | C20 Enterprise Multi-Tenancy, C3.3 Form 16 Parser |
| **Business Value** | B2B channel; employers want their employees to file correctly |
| **Priority** | **Medium** |
| **Maturity Target** | HRMS integration (Workday, SAP, Oracle); auto-distribution to employees |

### C16.5 — CA/Professional Software Integration

| Attribute | Value |
|-----------|-------|
| **Purpose** | Integrate with professional tax software used by CAs for seamless data exchange. |
| **Responsibilities** | Import from: Tally, Busy, QuickBooks, Zoho Books (for business clients); import from: CompuTax, ClearTax, TaxBuddy (CA practice management); export to: ITD e-filing utility format; export to: Excel workpaper format; bulk operations for multiple clients |
| **Inputs** | Client accounting data, Previous year ITR data |
| **Outputs** | ImportedClientData, WorkpaperExports, ITRJSON |
| **Dependencies** | C16.1 API Gateway, C20 Enterprise Multi-Tenancy |
| **Business Value** | CAs won't switch if they can't import existing data; integration = adoption |
| **Priority** | **Medium** |
| **Maturity Target** | Tally/QuickBooks integration; CompuTax data migration; CA practice management API |

### C16.6 — Payment Gateway Integration

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable taxpayers to pay self-assessment tax, advance tax, and fees directly through the platform. |
| **Responsibilities** | Integrate with ITD e-Pay Tax gateway; integrate with UPI, net banking, card payment gateways; generate challan (ITNS 280/281/282/283/284/285/286/287); auto-fill challan from computed tax; track payment status; reconcile payment with ITD records |
| **Inputs** | Tax payable amount, Payment method, Taxpayer bank details |
| **Outputs** | ChallanReceipt, PaymentConfirmation, BankReconciliation |
| **Dependencies** | C6.5 Tax Liability Aggregator, C6.7 Interest Computation |
| **Business Value** | Complete the loop — compute tax AND pay it without leaving the platform |
| **Priority** | **Medium** |
| **Maturity Target** | Direct ITD e-Pay tax integration; auto-challan generation; payment status auto-polling |

### C16.7 — Webhook & Event Subscription System

| Attribute | Value |
|-----------|-------|
| **Purpose** | Enable external systems to subscribe to platform events via webhooks. |
| **Responsibilities** | Event types: filing.submitted, filing.accepted, refund.credited, deadline.approaching, document.expiring; subscription management; retry with exponential backoff; webhook signature verification; event schema versioning; dead letter queue for failed deliveries |
| **Inputs** | Webhook subscription, Platform events |
| **Outputs** | Webhook delivery, Delivery logs, Failure alerts |
| **Dependencies** | C16.1 API Gateway, C17 Security |
| **Business Value** | Enables real-time integrations; CA firms can trigger workflows on filing events |
| **Priority** | **Medium** |
| **Maturity Target** | Event streaming (SSE/WebSocket); event marketplace; dead letter replay |

### C16.8 — Sandbox & Developer Portal

| Attribute | Value |
|-----------|-------|
| **Purpose** | Provide a developer sandbox with test data, API documentation, and integration testing tools. |
| **Responsibilities** | Sandbox environment with synthetic taxpayer data; API documentation with interactive examples; SDK generation; integration test suite; API changelog; developer support forum |
| **Inputs** | Developer registration, API key |
| **Outputs** | SandboxAccess, APIDocumentation, SDKs, TestData |
| **Dependencies** | C16.1 API Gateway |
| **Business Value** | Enables third-party integrations; platform ecosystem growth |
| **Priority** | **Medium** |
| **Maturity Target** | Full developer portal; interactive API explorer; integration certification program |

---

*[Document continues with Domains 17-20 and Bounded Context Map in Part 4]*
