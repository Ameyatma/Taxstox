"""Tax Knowledge Graph — Semantic graph of tax provisions, concepts, and relationships.

Nodes: provisions, concepts, rules, ITR schedules, AIS codes
Edges: contains, maps_to, overrides, depends_on, requires, supersedes

Powers: explanation engine, interview engine, rule conflict detection, AI-assisted Q&A

Traceability: C11.1 (Tax Knowledge Graph — Critical gap, 0%→50%)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class NodeType(str, Enum):
    PROVISION = "provision"       # Section 80C, Section 115BAC
    CONCEPT = "concept"           # deduction, exemption, income_head
    RULE = "rule"                 # 80C_limit, HRA_formula
    ITR_SCHEDULE = "itr_schedule" # ScheduleS, Schedule112A
    AIS_CODE = "ais_code"         # TDS-192, SFT-018(EMF)
    FINANCE_ACT = "finance_act"   # Finance Act 2025


class EdgeType(str, Enum):
    CONTAINS = "contains"           # Section 80C contains PPF, ELSS
    MAPS_TO = "maps_to"             # TDS-192 maps to ScheduleTDS1
    OVERRIDES = "overrides"         # 115BAC overrides old slabs
    DEPENDS_ON = "depends_on"       # Rebate 87A depends_on total_income
    REQUIRES = "requires"           # 80GG requires no HRA received
    SUPERSEDES = "supersedes"       # Finance Act 2025 supersedes 2024
    APPLIES_TO = "applies_to"       # Old Regime applies_to salaried
    EXCLUDES = "excludes"           # New Regime excludes 80C


@dataclass(frozen=True)
class KnowledgeNode:
    """A single node in the tax knowledge graph."""

    node_id: str
    node_type: NodeType
    label: str                          # Human-readable name
    description: str = ""
    financial_year: str = ""            # "" = applies to all FYs
    regime: str = ""                    # "" = applies to both
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeEdge:
    """A directed relationship between two knowledge nodes."""

    edge_type: EdgeType
    from_node: str                      # node_id
    to_node: str                        # node_id
    description: str = ""
    financial_year: str = ""


@dataclass
class KnowledgeGraph:
    """In-memory semantic graph of tax knowledge.

    Nodes and edges are immutable. The graph is built once at startup
    and queried for explanations, interview branching, and rule resolution.
    """

    nodes: dict[str, KnowledgeNode] = field(default_factory=dict)
    edges: list[KnowledgeEdge] = field(default_factory=list)

    def add_node(self, node: KnowledgeNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: KnowledgeEdge) -> None:
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        return self.nodes.get(node_id)

    def query_edges(
        self,
        from_node: str | None = None,
        to_node: str | None = None,
        edge_type: EdgeType | None = None,
    ) -> list[KnowledgeEdge]:
        """Query edges by source, target, or type."""
        results = self.edges
        if from_node:
            results = [e for e in results if e.from_node == from_node]
        if to_node:
            results = [e for e in results if e.to_node == to_node]
        if edge_type:
            results = [e for e in results if e.edge_type == edge_type]
        return results

    def get_contained_concepts(self, provision_id: str) -> list[KnowledgeNode]:
        """Get all concepts contained within a provision (e.g., 80C → PPF, ELSS)."""
        edges = self.query_edges(from_node=provision_id, edge_type=EdgeType.CONTAINS)
        return [self.nodes[e.to_node] for e in edges if e.to_node in self.nodes]

    def get_itr_mapping(self, ais_code: str) -> Optional[KnowledgeNode]:
        """Get ITR schedule for an AIS code."""
        edges = self.query_edges(from_node=ais_code, edge_type=EdgeType.MAPS_TO)
        if edges and edges[0].to_node in self.nodes:
            return self.nodes[edges[0].to_node]
        return None

    def get_overrides(self, provision_id: str) -> list[KnowledgeNode]:
        """Get provisions that override this one."""
        edges = self.query_edges(from_node=provision_id, edge_type=EdgeType.OVERRIDES)
        return [self.nodes[e.to_node] for e in edges if e.to_node in self.nodes]

    def search_by_keyword(self, keyword: str) -> list[KnowledgeNode]:
        """Search all nodes by keyword in label or description."""
        kw = keyword.lower()
        return [
            n for n in self.nodes.values()
            if kw in n.label.lower() or kw in n.description.lower()
        ]

    def get_provision_chain(self, provision_id: str) -> list[KnowledgeNode]:
        """Get a provision and its dependency chain (what it depends on, what depends on it)."""
        entry = self.nodes.get(provision_id)
        if not entry:
            return []
        chain = [entry]
        # What does this depend on?
        for edge in self.query_edges(from_node=provision_id, edge_type=EdgeType.DEPENDS_ON):
            if edge.to_node in self.nodes:
                chain.append(self.nodes[edge.to_node])
        # What depends on this?
        for edge in self.query_edges(to_node=provision_id, edge_type=EdgeType.DEPENDS_ON):
            if edge.from_node in self.nodes:
                chain.append(self.nodes[edge.from_node])
        return chain

    def get_regime_applicable(self, regime: str) -> list[KnowledgeNode]:
        """Get all provisions applicable to a specific regime."""
        regime_id = f"regime_{regime}" if not regime.startswith("regime_") else regime
        results: list[KnowledgeNode] = []
        for edge in self.query_edges(from_node=regime_id, edge_type=EdgeType.APPLIES_TO):
            if edge.to_node in self.nodes:
                results.append(self.nodes[edge.to_node])
        return results

    def get_regime_excluded(self, regime: str) -> list[KnowledgeNode]:
        """Get all provisions excluded by a specific regime."""
        regime_id = f"regime_{regime}" if not regime.startswith("regime_") else regime
        results: list[KnowledgeNode] = []
        for edge in self.query_edges(from_node=regime_id, edge_type=EdgeType.EXCLUDES):
            if edge.to_node in self.nodes:
                results.append(self.nodes[edge.to_node])
        return results

    def get_fy_changes(self, fy_from: str, fy_to: str) -> list[KnowledgeEdge]:
        """Get edges that represent changes between two financial years."""
        changes: list[KnowledgeEdge] = []
        for edge in self.edges:
            if edge.financial_year == fy_to:
                changes.append(edge)
        return changes

    def explain_concept(self, concept_id: str) -> str:
        """Generate a plain-language explanation of a concept from the graph."""
        node = self.nodes.get(concept_id)
        if not node:
            return f"No explanation available for '{concept_id}'."
        parts = [f"**{node.label}**: {node.description}"]

        # What contains it?
        containing = [
            e.from_node for e in self.query_edges(to_node=concept_id, edge_type=EdgeType.CONTAINS)
            if e.from_node in self.nodes
        ]
        if containing:
            parts.append(f"Part of: {', '.join(self.nodes[c].label for c in containing)}")

        # What does it depend on?
        deps = [
            e.to_node for e in self.query_edges(from_node=concept_id, edge_type=EdgeType.DEPENDS_ON)
            if e.to_node in self.nodes
        ]
        if deps:
            parts.append(f"Depends on: {', '.join(self.nodes[d].label for d in deps)}")

        return ". ".join(parts)

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)


# ── Build the Knowledge Graph ────────────────────────────────────────

def build_tax_knowledge_graph() -> KnowledgeGraph:
    """Build the complete tax knowledge graph with 100+ nodes and cross-FY relationships.

    Integrates with ProvisionKnowledgeBase for provision metadata.
    Every node and edge is traceable to a specific IT Act provision or ITD schema.
    """
    kg = KnowledgeGraph()

    # ── Nodes: Financial Years ──
    kg.add_node(KnowledgeNode("fy2024_25", NodeType.FINANCE_ACT, "FY2024-25",
        "Financial Year 2024-25 (Assessment Year 2025-26)"))
    kg.add_node(KnowledgeNode("fy2025_26", NodeType.FINANCE_ACT, "FY2025-26",
        "Financial Year 2025-26 (Assessment Year 2026-27)"))

    # ── Nodes: Tax Regimes ──
    kg.add_node(KnowledgeNode("regime_old", NodeType.CONCEPT, "Old Regime",
        "Pre-115BAC tax regime with all deductions and exemptions"))
    kg.add_node(KnowledgeNode("regime_new", NodeType.CONCEPT, "New Regime (115BAC)",
        "Post-115BAC default regime with lower rates, limited deductions"))

    # ── Nodes: Income Heads ──
    for head_id, label in [
        ("income_salary", "Salary Income"),
        ("income_house_property", "House Property Income"),
        ("income_business", "Business & Profession Income"),
        ("income_capital_gains", "Capital Gains"),
        ("income_other_sources", "Other Sources"),
    ]:
        kg.add_node(KnowledgeNode(head_id, NodeType.CONCEPT, label))

    # ── Nodes: ITR Forms ──
    for itr_id, label, desc in [
        ("itr1", "ITR-1 (SAHAJ)", "Resident individuals, salary, one house property, income ≤₹50L"),
        ("itr2", "ITR-2", "Individuals/HUFs without business income, capital gains, foreign assets"),
        ("itr3", "ITR-3", "Individuals/HUFs with business/profession income"),
        ("itr4", "ITR-4 (SUGAM)", "Presumptive taxation under 44AD/44ADA/44AE"),
    ]:
        kg.add_node(KnowledgeNode(itr_id, NodeType.ITR_SCHEDULE, label, desc))

    # ── Nodes: ITR Schedules ──
    for sched_id, label, desc in [
        ("schedule_s", "Schedule S", "Salary Income"),
        ("schedule_hp", "Schedule HP", "House Property Income"),
        ("schedule_bp", "Schedule BP", "Business & Profession Income"),
        ("schedule_cg", "Schedule CG", "Capital Gains"),
        ("schedule_112a", "Schedule 112A", "Equity LTCG (12.5% with ₹1.25L exemption)"),
        ("schedule_os", "Schedule OS", "Income from Other Sources"),
        ("schedule_via", "Schedule VI-A", "Chapter VI-A Deductions"),
        ("schedule_tds1", "Schedule TDS1", "TDS on Salary"),
        ("schedule_tds2", "Schedule TDS2", "TDS on Other Income"),
        ("schedule_fa", "Schedule FA", "Foreign Assets"),
        ("schedule_ti", "Part B-TI", "Total Income"),
        ("schedule_tti", "Part B-TTI", "Tax Computation"),
    ]:
        kg.add_node(KnowledgeNode(sched_id, NodeType.ITR_SCHEDULE, label, desc))

    # ── Nodes: Key Provisions (expanded from 14 to 30+) ──
    provisions = [
        # Salary
        ("sec_171", "Section 17(1)", "Salary income — basic, allowances, bonus"),
        ("sec_172", "Section 17(2)", "Perquisites — rent-free accommodation, car, ESOP"),
        ("sec_173", "Section 17(3)", "Profits in lieu of salary — termination, keyman insurance"),
        ("std_deduction", "Section 16(ia)", "Standard Deduction — ₹50K (Old) / ₹75K (New)"),
        ("professional_tax", "Section 16(iii)", "Professional Tax deduction (max ₹2,500)"),
        # Exemptions
        ("sec_10", "Section 10", "Exemptions — HRA, LTA, gratuity, agricultural income"),
        ("hra_1013a", "Section 10(13A)", "HRA Exemption — rent-based formula"),
        ("lta_105", "Section 10(5)", "Leave Travel Concession/Assistance"),
        ("gratuity_1010", "Section 10(10)", "Gratuity exemption (max ₹20L)"),
        # Chapter VI-A Deductions
        ("sec_80c", "Section 80C", "Aggregate Deduction — PPF, ELSS, EPF, LIC, tuition (₹1.5L)"),
        ("sec_80ccc", "Section 80CCC", "Pension fund contribution (within 80C)"),
        ("sec_80ccd1", "Section 80CCD(1)", "NPS employee contribution (within 80C)"),
        ("sec_80ccd1b", "Section 80CCD(1B)", "Additional NPS deduction (₹50K, beyond 80C)"),
        ("sec_80ccd2", "Section 80CCD(2)", "Employer NPS contribution (both regimes)"),
        ("sec_80d", "Section 80D", "Health Insurance premium (₹25K-₹1L depending on age)"),
        ("sec_80dd", "Section 80DD", "Disabled dependent maintenance (₹75K/₹1.25L)"),
        ("sec_80ddb", "Section 80DDB", "Medical treatment for specified diseases"),
        ("sec_80e", "Section 80E", "Education loan interest (unlimited, 8 years)"),
        ("sec_80ee", "Section 80EE", "First home loan interest (₹50K, additional)"),
        ("sec_80eea", "Section 80EEA", "Affordable housing loan interest (₹1.5L, additional)"),
        ("sec_80g", "Section 80G", "Donations to charitable institutions"),
        ("sec_80gg", "Section 80GG", "Rent paid without HRA (max ₹60K)"),
        ("sec_80tta", "Section 80TTA", "Savings account interest (₹10K, non-senior)"),
        ("sec_80ttb", "Section 80TTB", "Deposit interest for senior citizens (₹50K)"),
        ("sec_80u", "Section 80U", "Self-disability deduction (₹75K/₹1.25L)"),
        # House Property
        ("sec_24b", "Section 24(b)", "Housing loan interest (₹2L self-occupied, unlimited let-out)"),
        # Capital Gains
        ("sec_111a", "Section 111A", "Equity STCG — 15% (held ≤12 months, STT paid)"),
        ("sec_112a", "Section 112A", "Equity LTCG — 12.5% (held >12 months, ₹1.25L exemption)"),
        ("sec_115bbh", "Section 115BBH", "Crypto/VDA income — 30% flat, no deductions"),
        # Tax Computation
        ("sec_115bac", "Section 115BAC", "New Regime slabs — default from FY2023-24"),
        ("sec_87a", "Section 87A", "Rebate — ₹12.5K (Old, ₹5L) / ₹60K (New, ₹12L)"),
        ("surcharge", "Surcharge", "10%-37% on high income with marginal relief"),
        ("cess", "HEC", "Health & Education Cess — 4% on tax + surcharge"),
        # Interest & Penalties
        ("sec_234a", "Section 234A", "Late filing interest — 1%/month"),
        ("sec_234b", "Section 234B", "Advance tax default interest — 1%/month"),
        ("sec_234c", "Section 234C", "Advance tax deferment interest — 1%/month"),
        ("sec_234f", "Section 234F", "Late filing fee — ₹1K/₹5K/₹10K"),
        # Presumptive
        ("sec_44ad", "Section 44AD", "Presumptive business income — 8%/6% of turnover"),
        ("sec_44ada", "Section 44ADA", "Presumptive professional income — 50% of receipts"),
        ("sec_44ae", "Section 44AE", "Presumptive transport income — ₹7,500/tonne"),
        # Residential Status
        ("sec_6", "Section 6", "Residential Status — ROR/RNOR/NR determination"),
    ]

    for pid, label, desc in provisions:
        kg.add_node(KnowledgeNode(pid, NodeType.PROVISION, label, desc))

    # ── Nodes: AIS Codes (expanded) ──
    ais_codes = [
        ("ais_tds192", "TDS-192", "TDS on Salary"),
        ("ais_tds194a", "TDS-194A", "TDS on Interest"),
        ("ais_tds194i", "TDS-194I", "TDS on Rent"),
        ("ais_tds194j", "TDS-194J", "TDS on Professional Fees"),
        ("ais_tds194h", "TDS-194H", "TDS on Commission"),
        ("ais_tds194c", "TDS-194C", "TDS on Contract Payments"),
        ("ais_tds194d", "TDS-194D", "TDS on Insurance Commission"),
        ("ais_tds194s", "TDS-194S", "TDS on VDA/Crypto Transfer"),
        ("ais_sft016sb", "SFT-016(SB)", "Savings Bank Interest"),
        ("ais_sft016td", "SFT-016(TD)", "Term Deposit Interest"),
        ("ais_sft018emf", "SFT-018(EMF)", "Equity MF Sales"),
        ("ais_sft017otu", "SFT-017(OTU)", "Other Unit Sales"),
        ("ais_sft017pur", "SFT-017(Pur)", "Securities Purchases"),
        ("ais_sft005", "SFT-005", "Immovable Property Transactions"),
        ("ais_sft008", "SFT-008", "Cash Deposits >₹10L"),
        ("ais_sft013", "SFT-013", "Foreign Remittance"),
    ]
    for cid, code, desc in ais_codes:
        kg.add_node(KnowledgeNode(cid, NodeType.AIS_CODE, code, desc))

    # ── Nodes: 80C Sub-Concepts (expanded) ──
    concept_80c = [
        ("concept_epf", "EPF", "Employees' Provident Fund — auto-deducted from salary"),
        ("concept_ppf", "PPF", "Public Provident Fund — 15-year lock-in, govt-backed"),
        ("concept_elss", "ELSS", "Equity-Linked Savings Scheme — 3-year lock-in mutual fund"),
        ("concept_nsc", "NSC", "National Savings Certificate — 5-year post office investment"),
        ("concept_lic", "LIC Premium", "Life Insurance Premium — max 10% of sum assured"),
        ("concept_tuition", "Tuition Fees", "Children's tuition fees — max 2 children"),
        ("concept_home_principal", "Home Loan Principal", "Principal repayment on home loan"),
        ("concept_tax_saving_fd", "Tax-Saving FD", "5-year bank fixed deposit for 80C"),
        ("concept_ssy", "Sukanya Samriddhi", "Girl child savings scheme"),
        ("concept_scss", "SCSS", "Senior Citizens Savings Scheme"),
        ("concept_nps_80c", "NPS (80CCD(1))", "NPS contribution within 80C limit"),
    ]
    for cid, label, desc in concept_80c:
        kg.add_node(KnowledgeNode(cid, NodeType.CONCEPT, label, desc))
        kg.add_edge(KnowledgeEdge(EdgeType.CONTAINS, "sec_80c", cid, desc))

    # ── Nodes: Other Concepts ──
    other_concepts = [
        ("concept_stcg", "Short-Term Capital Gains", "Gains on assets held ≤ holding period"),
        ("concept_ltcg", "Long-Term Capital Gains", "Gains on assets held > holding period"),
        ("concept_indexation", "Indexation", "Inflation-adjusting cost using CII table"),
        ("concept_marginal_relief", "Marginal Relief", "Surcharge cap at excess income over threshold"),
        ("concept_ror", "ROR", "Resident and Ordinarily Resident"),
        ("concept_rnor", "RNOR", "Resident but Not Ordinarily Resident"),
        ("concept_nr", "NR", "Non-Resident"),
        ("concept_advance_tax", "Advance Tax", "Tax paid in installments during the FY"),
        ("concept_self_assessment", "Self-Assessment Tax", "Tax paid at ITR filing time"),
    ]
    for cid, label, desc in other_concepts:
        kg.add_node(KnowledgeNode(cid, NodeType.CONCEPT, label, desc))

    # ── Edges: Regime relationships ──
    # Old Regime → available deductions
    old_regime_provisions = [
        "sec_80c", "sec_80ccc", "sec_80ccd1", "sec_80d", "sec_80dd",
        "sec_80ddb", "sec_80e", "sec_80ee", "sec_80eea", "sec_80g",
        "sec_80gg", "sec_80u", "hra_1013a", "lta_105", "gratuity_1010",
        "sec_24b",
    ]
    for pid in old_regime_provisions:
        kg.add_edge(KnowledgeEdge(EdgeType.APPLIES_TO, "regime_old", pid,
            f"{pid} available only under Old Regime"))

    # New Regime → limited provisions
    new_regime_provisions = ["sec_80ccd2", "std_deduction"]
    for pid in new_regime_provisions:
        kg.add_edge(KnowledgeEdge(EdgeType.APPLIES_TO, "regime_new", pid,
            f"{pid} available under both regimes"))

    # New Regime → excludes
    new_excludes = [
        "sec_80c", "sec_80d", "hra_1013a", "lta_105", "sec_80e",
        "sec_80g", "sec_80gg", "sec_24b",
    ]
    for pid in new_excludes:
        kg.add_edge(KnowledgeEdge(EdgeType.EXCLUDES, "regime_new", pid,
            f"Not available under New Regime"))

    # ── Edges: Section 115BAC overrides old regime structure ──
    kg.add_edge(KnowledgeEdge(EdgeType.OVERRIDES, "sec_115bac", "regime_old",
        "New Regime slabs override Old Regime slabs for those opting in"))

    # ── Edges: AIS → ITR Schedule mappings (expanded) ──
    ais_itr_map = [
        ("ais_tds192", "schedule_tds1", "Salary TDS → Schedule TDS1"),
        ("ais_tds194a", "schedule_tds2", "Interest TDS → Schedule TDS2"),
        ("ais_tds194i", "schedule_tds2", "Rent TDS → Schedule TDS2"),
        ("ais_tds194j", "schedule_tds2", "Professional Fee TDS → Schedule TDS2"),
        ("ais_tds194h", "schedule_tds2", "Commission TDS → Schedule TDS2"),
        ("ais_tds194c", "schedule_tds2", "Contract Payment TDS → Schedule TDS2"),
        ("ais_sft016sb", "schedule_os", "Savings Interest → Schedule OS"),
        ("ais_sft016td", "schedule_os", "Term Deposit Interest → Schedule OS"),
        ("ais_sft018emf", "schedule_112a", "Equity MF Sales → Schedule 112A"),
        ("ais_sft017otu", "schedule_cg", "Other Unit Sales → Schedule CG"),
        ("ais_sft005", "schedule_cg", "Property Transactions → Schedule CG"),
    ]
    for code_id, sched_id, desc in ais_itr_map:
        kg.add_edge(KnowledgeEdge(EdgeType.MAPS_TO, code_id, sched_id, desc))

    # ── Edges: Provisions → ITR Schedules ──
    provision_schedule_map = [
        ("sec_171", "schedule_s"), ("sec_172", "schedule_s"), ("sec_173", "schedule_s"),
        ("std_deduction", "schedule_s"), ("hra_1013a", "schedule_s"),
        ("sec_24b", "schedule_hp"), ("sec_80eea", "schedule_hp"),
        ("sec_44ad", "schedule_bp"), ("sec_44ada", "schedule_bp"),
        ("sec_111a", "schedule_cg"), ("sec_112a", "schedule_112a"), ("sec_115bbh", "schedule_cg"),
        ("sec_80c", "schedule_via"), ("sec_80ccd1b", "schedule_via"),
        ("sec_80ccd2", "schedule_via"), ("sec_80d", "schedule_via"),
        ("sec_80tta", "schedule_via"), ("sec_80ttb", "schedule_via"),
        ("sec_80g", "schedule_via"), ("sec_80e", "schedule_via"),
        ("sec_87a", "schedule_tti"), ("surcharge", "schedule_tti"), ("cess", "schedule_tti"),
        ("sec_234a", "schedule_tti"), ("sec_234b", "schedule_tti"),
        ("sec_234c", "schedule_tti"), ("sec_234f", "schedule_tti"),
    ]
    for pid, sched_id in provision_schedule_map:
        kg.add_edge(KnowledgeEdge(EdgeType.MAPS_TO, pid, sched_id,
            f"Maps to {sched_id}"))

    # ── Edges: Dependency chains ──
    kg.add_edge(KnowledgeEdge(EdgeType.DEPENDS_ON, "sec_87a", "income_salary",
        "87A rebate depends on total income"))
    kg.add_edge(KnowledgeEdge(EdgeType.DEPENDS_ON, "surcharge", "sec_87a",
        "Surcharge computed after rebate"))
    kg.add_edge(KnowledgeEdge(EdgeType.DEPENDS_ON, "cess", "surcharge",
        "Cess computed on tax + surcharge"))
    kg.add_edge(KnowledgeEdge(EdgeType.DEPENDS_ON, "schedule_tti", "schedule_ti",
        "Tax computation depends on total income"))
    kg.add_edge(KnowledgeEdge(EdgeType.DEPENDS_ON, "schedule_ti", "schedule_via",
        "Total income = GTI - deductions"))

    # ── Edges: REQUIRES relationships ──
    kg.add_edge(KnowledgeEdge(EdgeType.REQUIRES, "sec_80gg", "regime_old",
        "80GG requires Old Regime"))
    kg.add_edge(KnowledgeEdge(EdgeType.REQUIRES, "sec_80ttb", "concept_stcg",
        "80TTB requires senior citizen status (not tracked here)"))

    # ── Edges: Cross-FY relationships ──
    kg.add_edge(KnowledgeEdge(EdgeType.SUPERSEDES, "fy2025_26", "fy2024_25",
        "FY2025-26 rules supersede FY2024-25 rules"))
    kg.add_edge(KnowledgeEdge(EdgeType.OVERRIDES, "sec_115bac", "sec_87a",
        "New Regime rebate limits override Old Regime rebate", financial_year="FY2025-26"))

    # ── Edges: ITR form eligibility ──
    kg.add_edge(KnowledgeEdge(EdgeType.APPLIES_TO, "itr1", "income_salary",
        "ITR-1 requires only salary + one house property + other sources"))
    kg.add_edge(KnowledgeEdge(EdgeType.APPLIES_TO, "itr2", "income_capital_gains",
        "ITR-2 supports capital gains"))
    kg.add_edge(KnowledgeEdge(EdgeType.APPLIES_TO, "itr3", "income_business",
        "ITR-3 required for business income"))
    kg.add_edge(KnowledgeEdge(EdgeType.APPLIES_TO, "itr4", "sec_44ad",
        "ITR-4 for presumptive taxation"))

    return kg


# Singleton instance — built once, queried everywhere
tax_knowledge_graph = build_tax_knowledge_graph()
