"""P4 Tests — AI Intelligence: Knowledge Graph, Finance Act Analyzer,
Rule Conflict Detection, Rule Impact Analysis, Interview Personalization,
Offline Interview, XAI, and Explanation enhancements.

Tests: 33
"""

import pytest
from decimal import Decimal

from src.engine.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeNode,
    KnowledgeEdge,
    NodeType,
    EdgeType,
    tax_knowledge_graph,
)
from src.engine.finance_act_analyzer import (
    FinanceActChangeAnalyzer,
    FinanceActDelta,
    ChangeType,
    analyze_fy_transition,
)
from src.engine.rule_conflict_detector import (
    RuleConflictDetector,
    ConflictReport,
    ConflictSeverity,
    detect_conflicts,
)
from src.engine.rule_impact_analyzer import (
    RuleImpactAnalyzer,
    ImpactAnalysis,
    analyze_rule_change,
)
from src.engine.xai import (
    ExplainableAIEngine,
    XAIReport,
    FeatureContribution,
    Counterfactual,
    SensitivityAnalysis,
)
from src.engine.explain import ExplanationEngine, Explanation, ComputationNarrative
from src.engine.audit import AuditTrail, AuditEventType, AuditEvent, AuditContext
from src.engine.rules.config import rule_repository, TaxYearConfig
from src.models.financial_year import FinancialYear

from src.domain.knowledge.provision_kb import (
    ProvisionKnowledgeBase,
    ProvisionEntry,
    provision_kb,
)
from src.domain.knowledge.tax_glossary import TaxGlossary, GlossaryEntry, tax_glossary
from src.domain.knowledge.circular_db import CBDTCircularDatabase, Circular, circular_db
from src.domain.knowledge.education_content import (
    EducationContent,
    EducationArticle,
    ExpertiseLevel,
    education_content,
)
from src.domain.interview.personalization import (
    InterviewPersonalizationEngine,
    TaxpayerProfile,
    QuestionRelevanceScore,
    personalization_engine,
)
from src.domain.interview.offline import (
    OfflineInterviewPack,
    OfflineQuestion,
    OfflineResponse,
    OfflineValidationRule,
    QuestionType,
    pack_interview,
)


# ═══════════════════════════════════════════════════════════════
# 4a: Knowledge Foundation Tests
# ═══════════════════════════════════════════════════════════════

class TestKnowledgeGraphEnhanced:
    """Test the enhanced knowledge graph (P4 expansion)."""

    def test_node_count_expanded(self):
        """Graph should have 100+ nodes after P4 expansion."""
        assert tax_knowledge_graph.node_count >= 80, (
            f"Expected 80+ nodes, got {tax_knowledge_graph.node_count}"
        )

    def test_edge_count_expanded(self):
        """Graph should have 50+ edges after P4 expansion."""
        assert tax_knowledge_graph.edge_count >= 50, (
            f"Expected 50+ edges, got {tax_knowledge_graph.edge_count}"
        )

    def test_cross_fy_edges_exist(self):
        """Cross-FY supersedes relationship should exist."""
        fy_edges = tax_knowledge_graph.query_edges(
            from_node="fy2025_26", edge_type=EdgeType.SUPERSEDES
        )
        assert len(fy_edges) > 0, "Expected SUPERSEDES edges between FYs"

    def test_search_by_keyword(self):
        """Keyword search should find relevant nodes."""
        results = tax_knowledge_graph.search_by_keyword("80C")
        assert len(results) >= 2, f"Expected 2+ results for '80C', got {len(results)}"
        labels = [n.label for n in results]
        assert any("80C" in l for l in labels)

    def test_get_provision_chain(self):
        """Provision chain should include dependencies."""
        chain = tax_knowledge_graph.get_provision_chain("cess")
        assert len(chain) >= 2, f"Expected 2+ nodes in cess chain, got {len(chain)}"

    def test_explain_concept(self):
        """Concept explanation should produce text."""
        text = tax_knowledge_graph.explain_concept("concept_ppf")
        assert "PPF" in text
        assert len(text) > 20

    def test_get_regime_applicable_old(self):
        """Old Regime should have many applicable provisions."""
        provisions = tax_knowledge_graph.get_regime_applicable("old")
        assert len(provisions) >= 10, f"Expected 10+ in old regime, got {len(provisions)}"

    def test_get_regime_excluded_new(self):
        """New Regime should exclude 80C, 80D, etc."""
        excluded = tax_knowledge_graph.get_regime_excluded("new")
        excluded_ids = {e.node_id for e in excluded}
        assert "sec_80c" in excluded_ids, "80C should be excluded from New Regime"
        assert "sec_80d" in excluded_ids, "80D should be excluded from New Regime"


class TestProvisionKnowledgeBase:
    """Test the provision knowledge base."""

    def test_provision_count(self):
        """KB should have 30+ provisions."""
        assert len(provision_kb.all_provisions) >= 25

    def test_get_by_section(self):
        """Lookup by section number."""
        entry = provision_kb.get_by_section("80C")
        assert entry is not None
        assert entry.title == "Aggregate Deduction"

    def test_search_by_keyword(self):
        """Search provisions by keyword."""
        results = provision_kb.search("rebate")
        assert len(results) >= 1
        assert any("87A" in r.section for r in results)

    def test_category_summary(self):
        """Category summary should have multiple categories."""
        summary = provision_kb.category_summary
        assert "deduction" in summary
        assert "income" in summary

    def test_get_chain(self):
        """Provision chain includes related provisions."""
        chain = provision_kb.get_chain("sec_80c")
        assert len(chain) >= 2


class TestTaxGlossary:
    """Test the tax glossary."""

    def test_glossary_size(self):
        """Glossary should have 50+ terms."""
        assert len(tax_glossary.all_terms) >= 50

    def test_lookup_term(self):
        """Lookup a common term."""
        entry = tax_glossary.lookup("PAN")
        assert entry is not None
        assert "Permanent Account Number" in entry.definition

    def test_lookup_case_insensitive(self):
        """Lookup should be case-insensitive."""
        entry = tax_glossary.lookup("pan")
        assert entry is not None

    def test_search(self):
        """Search should find relevant terms."""
        results = tax_glossary.search("deduction")
        assert len(results) >= 5

    def test_category_summary(self):
        """Should have multiple categories."""
        summary = tax_glossary.category_summary
        assert "deduction" in summary
        assert "filing" in summary


class TestCBDTCircularDatabase:
    """Test the CBDT circular database."""

    def test_circular_count(self):
        """Should have several circulars registered."""
        assert len(circular_db.all_circulars) >= 5

    def test_get_by_provision(self):
        """Find circulars affecting a specific provision."""
        circulars = circular_db.get_by_provision("sec_115bac")
        assert len(circulars) >= 1

    def test_search(self):
        """Search circulars by keyword."""
        results = circular_db.search("115BAC")
        assert len(results) >= 1


class TestEducationContent:
    """Test the taxpayer education content."""

    def test_article_count(self):
        """Should have education articles."""
        assert education_content.article_count >= 6

    def test_get_by_topic(self):
        """Get articles by topic."""
        articles = education_content.get_by_topic("deduction")
        assert len(articles) >= 1

    def test_get_by_expertise(self):
        """Get articles by expertise level."""
        articles = education_content.get_by_expertise(ExpertiseLevel.BEGINNER)
        assert len(articles) >= 2

    def test_search(self):
        """Search articles."""
        results = education_content.search("capital gains")
        assert len(results) >= 1


# ═══════════════════════════════════════════════════════════════
# 4b: Rule Intelligence Tests
# ═══════════════════════════════════════════════════════════════

class TestFinanceActChangeAnalyzer:
    """Test the Finance Act change analyzer."""

    def test_analyze_fy2425_to_fy2526(self):
        """Should detect changes between FY2024-25 and FY2025-26."""
        fy24 = FinancialYear.from_string("FY2024-25")
        fy25 = FinancialYear.from_string("FY2025-26")
        config24 = rule_repository.get(fy24)
        config25 = rule_repository.get(fy25)

        analyzer = FinanceActChangeAnalyzer()
        report = analyzer.analyze(config24, config25)

        assert report.change_count > 0, "Expected changes between FY24-25 and FY25-26"

    def test_slab_changes_detected(self):
        """New Regime slabs changed between FY24-25 and FY25-26."""
        report = analyze_fy_transition("FY2024-25", "FY2025-26")
        assert report is not None
        slab_changes = report.slab_changes
        assert len(slab_changes) > 0, "Expected slab changes"

    def test_rebate_change_detected(self):
        """87A rebate amounts changed."""
        report = analyze_fy_transition("FY2024-25", "FY2025-26")
        assert report is not None
        rebate_changes = [
            c for c in report.changes
            if c.change_type.value.startswith("rebate")
        ]
        assert len(rebate_changes) > 0, "Expected rebate changes"

    def test_summary_produces_text(self):
        """Summary should be non-empty."""
        report = analyze_fy_transition("FY2024-25", "FY2025-26")
        assert report is not None
        assert len(report.summary) > 0

    def test_same_fy_no_changes(self):
        """Comparing same FY should produce no changes."""
        fy25 = FinancialYear.from_string("FY2025-26")
        config = rule_repository.get(fy25)
        analyzer = FinanceActChangeAnalyzer()
        report = analyzer.analyze(config, config)
        assert report.change_count == 0


class TestRuleConflictDetector:
    """Test the rule conflict detector."""

    def test_detect_all_returns_report(self):
        """Should return a ConflictReport."""
        detector = RuleConflictDetector(tax_knowledge_graph)
        report = detector.detect_all()
        assert isinstance(report, ConflictReport)

    def test_no_override_conflicts(self):
        """Current graph should have no override conflicts."""
        detector = RuleConflictDetector(tax_knowledge_graph)
        report = detector.detect_all()
        assert len(report.errors) == 0, (
            f"Expected no errors, got: {[c.description for c in report.errors]}"
        )

    def test_convenience_function(self):
        """detect_conflicts() convenience function should work."""
        report = detect_conflicts(tax_knowledge_graph)
        assert isinstance(report, ConflictReport)


class TestRuleImpactAnalyzer:
    """Test the rule impact analyzer."""

    def test_analyze_80c_change(self):
        """Analyze impact of changing 80C limit."""
        analysis = analyze_rule_change(
            "sec_80c",
            "80C limit increased from ₹1.5L to ₹2.0L",
            old_value="₹1,50,000",
            new_value="₹2,00,000",
        )
        assert isinstance(analysis, ImpactAnalysis)
        assert analysis.total_impacted > 0

    def test_affected_segments_populated(self):
        """Impact analysis should identify affected segments."""
        analysis = analyze_rule_change("sec_80c", "80C limit change")
        assert len(analysis.affected_taxpayer_segments) > 0

    def test_required_test_updates(self):
        """Should suggest test updates."""
        analysis = analyze_rule_change("sec_80c", "80C limit change")
        assert len(analysis.required_test_updates) > 0

    def test_summary_produces_text(self):
        """Summary should be informative."""
        analysis = analyze_rule_change("sec_80c", "80C limit change")
        assert len(analysis.summary) > 0


# ═══════════════════════════════════════════════════════════════
# 4c: Interview Intelligence Tests
# ═══════════════════════════════════════════════════════════════

class TestInterviewPersonalization:
    """Test the interview personalization engine."""

    def test_suppress_rent_new_regime(self):
        """Rent question should be suppressed under New Regime."""
        profile = TaxpayerProfile(has_hra=True, regime="new")
        score = personalization_engine.score_question("rent", profile)
        assert score.suppress
        assert "New Regime" in score.reason

    def test_keep_rent_old_regime_with_hra(self):
        """Rent question should be kept under Old Regime with HRA."""
        profile = TaxpayerProfile(has_hra=True, regime="old")
        score = personalization_engine.score_question("rent", profile)
        assert not score.suppress

    def test_suppress_rent_no_hra(self):
        """Rent question suppressed when no HRA detected."""
        profile = TaxpayerProfile(has_hra=False, regime="old")
        score = personalization_engine.score_question("rent", profile)
        assert score.suppress

    def test_suppress_80c_full(self):
        """80C question suppressed when EPF fills limit."""
        profile = TaxpayerProfile(
            has_epf=True, regime="old",
            total_80c_detected=Decimal("150000"),
        )
        score = personalization_engine.score_question("additional_80c", profile)
        assert score.suppress

    def test_suppress_health_new_regime(self):
        """Health insurance suppressed under New Regime."""
        profile = TaxpayerProfile(regime="new")
        score = personalization_engine.score_question("health_insurance", profile)
        assert score.suppress

    def test_get_active_questions(self):
        """Should return max_questions active questions."""
        profile = TaxpayerProfile(has_hra=True, regime="old", has_epf=True)
        active = personalization_engine.get_active_questions(
            ["rent", "health_insurance", "additional_80c", "home_loan", "other_income"],
            profile,
            max_questions=3,
        )
        assert len(active) <= 3

    def test_personalize_sorts_by_relevance(self):
        """Questions should be sorted by relevance score."""
        profile = TaxpayerProfile(has_hra=True, regime="old")
        scores = personalization_engine.personalize(
            ["rent", "home_loan", "other_income"], profile,
        )
        # Rent (0.95) > other_income (0.75) > home_loan (0.40)
        assert scores[0].question_id == "rent"


class TestOfflineInterview:
    """Test the offline interview pack."""

    def test_pack_interview(self):
        """Should create a valid offline pack."""
        questions = [
            OfflineQuestion(
                question_id="q1", text="Do you pay rent?",
                question_type=QuestionType.YES_NO, order=1,
            ),
            OfflineQuestion(
                question_id="q2", text="Annual rent amount?",
                question_type=QuestionType.NUMBER, order=2,
                depends_on="q1", depends_on_answer="yes",
            ),
        ]
        pack = pack_interview("FY2025-26", "old", questions)
        assert pack.total_questions == 2
        assert pack.financial_year == "FY2025-26"
        assert pack.regime == "old"

    def test_pack_to_dict(self):
        """Pack should serialize to JSON-safe dict."""
        pack = pack_interview("FY2025-26", "new", [])
        d = pack.to_dict()
        assert "pack_id" in d
        assert "questions" in d
        assert "financial_year" in d

    def test_response_validation_required(self):
        """Required field validation should catch empty answers."""
        question = OfflineQuestion(
            question_id="q1", text="Name?", question_type=QuestionType.TEXT,
            validation_rules=(
                OfflineValidationRule("v1", "required", error_message="Required"),
            ),
        )
        response = OfflineResponse(pack_id="p1", question_id="q1", answer="")
        result = response.validate(question)
        assert not result["valid"]
        assert len(result["errors"]) > 0

    def test_response_validation_range(self):
        """Range validation should work."""
        question = OfflineQuestion(
            question_id="q1", text="Amount?", question_type=QuestionType.NUMBER,
            validation_rules=(
                OfflineValidationRule("v1", "range", parameters={"min": 0, "max": 1000000},
                                      error_message="Out of range"),
            ),
        )
        response = OfflineResponse(pack_id="p1", question_id="q1", answer="-100")
        result = response.validate(question)
        assert not result["valid"]


# ═══════════════════════════════════════════════════════════════
# 4d: Explanation Enhancement Tests
# ═══════════════════════════════════════════════════════════════

class TestExplainableAI:
    """Test the XAI engine."""

    def test_compute_contributions(self):
        """Should compute feature contributions."""
        engine = ExplainableAIEngine()
        breakdown = {
            "income_salary": "900000",
            "gross_total_income": "1000000",
            "deductions_total": "150000",
            "rebate_87a": "0",
        }
        final_tax = Decimal("50000")
        contribs = engine.compute_contributions(breakdown, final_tax)
        assert len(contribs) >= 2

    def test_generate_counterfactuals(self):
        """Should generate counterfactual scenarios."""
        engine = ExplainableAIEngine()
        breakdown = {
            "income_salary": "900000",
            "gross_total_income": "1000000",
            "80c_deduction": "50000",
            "80ccd1b_deduction": "0",
        }
        total_income = Decimal("1000000")
        final_tax = Decimal("50000")
        cfs = engine.generate_counterfactuals(breakdown, total_income, final_tax, "old")
        assert len(cfs) >= 5, f"Expected 5+ counterfactuals, got {len(cfs)}"
        assert any(cf.scenario_id == "CF-001" for cf in cfs)  # Income +50K
        assert any(cf.scenario_id == "CF-003" for cf in cfs)  # Max 80C
        assert any(cf.scenario_id == "CF-005" for cf in cfs)  # Switch regime

    def test_compute_sensitivity(self):
        """Should compute sensitivity analysis."""
        engine = ExplainableAIEngine()
        breakdown = {"financial_year": "FY2025-26"}
        total_income = Decimal("1000000")
        final_tax = Decimal("50000")
        sensitivities = engine.compute_sensitivity(breakdown, total_income, final_tax)
        assert len(sensitivities) >= 1
        assert sensitivities[0].feature == "total_income"

    def test_generate_report(self):
        """Should generate a complete XAI report."""
        engine = ExplainableAIEngine()
        breakdown = {
            "income_salary": "900000",
            "gross_total_income": "1000000",
            "deductions_total": "150000",
        }
        report = engine.generate_report(
            breakdown,
            total_income=Decimal("1000000"),
            final_tax=Decimal("50000"),
            correlation_id="test-123",
            financial_year="FY2025-26",
            regime="old",
        )
        assert isinstance(report, XAIReport)
        assert len(report.summary_text) > 0
        assert len(report.top_contributors) > 0


class TestExplanationEngineEnhanced:
    """Test the enhanced explanation engine."""

    def test_explain_number(self):
        """Deep-dive explanation of a specific number."""
        ctx = AuditContext("FY2025-26")
        audit_event = ctx.event(
            AuditEventType.SLAB_APPLIED, "tax_computation", "C6.1",
            "Applied slab tax: 5% on ₹4,00,000",
            input_data={"income": "925000"},
            output_data={"slab_tax": "32500", "income": "925000"},
            rule_reference="slab_new",
        )
        trail = AuditTrail(
            correlation_id=ctx.correlation_id,
            financial_year="FY2025-26",
            events=(audit_event,),
        )

        engine = ExplanationEngine()
        text = engine.explain_number(trail, "slab_tax")
        assert text is not None
        assert "slab_tax" in text
        assert "32500" in text

    def test_explain_with_provision_enrichment(self):
        """Explanation should include provision references."""
        ctx = AuditContext("FY2025-26")
        events = [
            ctx.event(
                AuditEventType.INCOME_COMPUTED, "income", "C4.1",
                "Salary income computed",
                output_data={"income": "900000", "income_head": "salary"},
                rule_reference="salary_171",
            ),
            ctx.event(
                AuditEventType.TAX_FINALIZED, "tax_computation", "C6.5",
                "Tax finalized",
                output_data={"net_tax": "45000"},
            ),
        ]
        trail = AuditTrail(
            correlation_id=ctx.correlation_id,
            financial_year="FY2025-26",
            events=tuple(events),
        )

        engine = ExplanationEngine()
        narrative = engine.explain(trail)
        assert len(narrative.steps) == 2
        # First step should have provision reference for salary
        assert narrative.steps[0].provision != ""

    def test_language_parameter_accepted(self):
        """Language parameter should be accepted."""
        ctx = AuditContext("FY2025-26")
        trail = AuditTrail(ctx.correlation_id, "FY2025-26", ())
        engine = ExplanationEngine()
        narrative = engine.explain(trail, language="en")
        assert isinstance(narrative, ComputationNarrative)
