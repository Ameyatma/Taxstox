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


# ── Build the Knowledge Graph ────────────────────────────────────────

def build_tax_knowledge_graph() -> KnowledgeGraph:
    """Build the complete tax knowledge graph with all known provisions and relationships."""
    kg = KnowledgeGraph()

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

    # ── Nodes: Key Provisions ──
    provisions = [
        ("sec_10", "Section 10", "Exemptions"),
        ("sec_16", "Section 16", "Deductions from Salary"),
        ("sec_24b", "Section 24(b)", "Interest on Housing Loan"),
        ("sec_80c", "Section 80C", "Aggregate Deduction (₹1.5L)"),
        ("sec_80ccd1b", "Section 80CCD(1B)", "Additional NPS (₹50K)"),
        ("sec_80ccd2", "Section 80CCD(2)", "Employer NPS"),
        ("sec_80d", "Section 80D", "Health Insurance"),
        ("sec_80tta", "Section 80TTA", "Savings Interest (₹10K)"),
        ("sec_87a", "Section 87A", "Rebate"),
        ("sec_111a", "Section 111A", "Equity STCG (15%)"),
        ("sec_112a", "Section 112A", "Equity LTCG (12.5%)"),
        ("sec_115bac", "Section 115BAC", "New Regime Slabs"),
        ("sec_234a", "Section 234A", "Late Filing Interest"),
        ("sec_234b", "Section 234B", "Advance Tax Default Interest"),
        ("sec_234c", "Section 234C", "Advance Tax Deferment Interest"),
    ]
    for pid, label, desc in provisions:
        kg.add_node(KnowledgeNode(pid, NodeType.PROVISION, label, desc))

    # ── Nodes: AIS Codes ──
    ais_codes = [
        ("ais_tds192", "TDS-192", "TDS on Salary"),
        ("ais_sft016sb", "SFT-016(SB)", "Savings Interest"),
        ("ais_sft018emf", "SFT-018(EMF)", "Equity MF Sales"),
        ("ais_sft017otu", "SFT-017(OTU)", "Other Unit Sales"),
    ]
    for cid, code, desc in ais_codes:
        kg.add_node(KnowledgeNode(cid, NodeType.AIS_CODE, code, desc))

    # ── Edges: Regime availability ──
    kg.add_edge(KnowledgeEdge(EdgeType.APPLIES_TO, "regime_old", "sec_80c"))
    kg.add_edge(KnowledgeEdge(EdgeType.APPLIES_TO, "regime_old", "sec_80d"))
    kg.add_edge(KnowledgeEdge(EdgeType.EXCLUDES, "regime_new", "sec_80c"))
    kg.add_edge(KnowledgeEdge(EdgeType.APPLIES_TO, "regime_new", "sec_80ccd2"))
    kg.add_edge(KnowledgeEdge(EdgeType.APPLIES_TO, "regime_old", "sec_80ccd2"))

    # ── Edges: Section 115BAC overrides old slabs ──
    kg.add_edge(KnowledgeEdge(EdgeType.OVERRIDES, "sec_115bac", "regime_old",
        "New Regime slabs override Old Regime slabs for those opting in"))

    # ── Edges: AIS → ITR Schedule mappings ──
    kg.add_node(KnowledgeNode("schedule_tds1", NodeType.ITR_SCHEDULE, "Schedule TDS1", "Salary TDS"))
    kg.add_node(KnowledgeNode("schedule_tds2", NodeType.ITR_SCHEDULE, "Schedule TDS2", "Other TDS"))
    kg.add_node(KnowledgeNode("schedule_112a", NodeType.ITR_SCHEDULE, "Schedule 112A", "Equity LTCG"))
    kg.add_node(KnowledgeNode("schedule_cg", NodeType.ITR_SCHEDULE, "Schedule CG", "Capital Gains"))
    kg.add_node(KnowledgeNode("schedule_os", NodeType.ITR_SCHEDULE, "Schedule OS", "Other Sources"))
    kg.add_edge(KnowledgeEdge(EdgeType.MAPS_TO, "ais_tds192", "schedule_tds1"))
    kg.add_edge(KnowledgeEdge(EdgeType.MAPS_TO, "ais_sft016sb", "schedule_os"))
    kg.add_edge(KnowledgeEdge(EdgeType.MAPS_TO, "ais_sft018emf", "schedule_112a"))
    kg.add_edge(KnowledgeEdge(EdgeType.MAPS_TO, "ais_sft017otu", "schedule_cg"))

    # ── Edges: Provisions contain concepts ──
    kg.add_node(KnowledgeNode("concept_ppf", NodeType.CONCEPT, "PPF"))
    kg.add_node(KnowledgeNode("concept_elss", NodeType.CONCEPT, "ELSS"))
    kg.add_node(KnowledgeNode("concept_epf", NodeType.CONCEPT, "EPF"))
    kg.add_node(KnowledgeNode("concept_lic", NodeType.CONCEPT, "LIC Premium"))
    kg.add_edge(KnowledgeEdge(EdgeType.CONTAINS, "sec_80c", "concept_ppf"))
    kg.add_edge(KnowledgeEdge(EdgeType.CONTAINS, "sec_80c", "concept_elss"))
    kg.add_edge(KnowledgeEdge(EdgeType.CONTAINS, "sec_80c", "concept_epf"))
    kg.add_edge(KnowledgeEdge(EdgeType.CONTAINS, "sec_80c", "concept_lic"))

    # ── Dependency edges ──
    kg.add_edge(KnowledgeEdge(EdgeType.DEPENDS_ON, "sec_87a", "income_salary",
        "87A rebate depends on total income"))
    kg.add_edge(KnowledgeEdge(EdgeType.REQUIRES, "sec_80gg", "regime_old",
        "80GG requires Old Regime"))

    return kg


# Singleton instance — built once, queried everywhere
tax_knowledge_graph = build_tax_knowledge_graph()
