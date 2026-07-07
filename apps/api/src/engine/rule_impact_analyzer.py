"""Rule Change Impact Analysis — Trace the downstream effects of rule changes.

Given a change to a tax rule (e.g., "80C limit increased to ₹2L"),
walks the knowledge graph dependency chain to identify:
- Which ITR schedules are affected
- Which computation steps must be recomputed
- Which taxpayer segments are impacted
- Required downstream code/test changes

Traceability: C12.7 (Rule Change Impact Analysis — 0%→50%, P4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from src.engine.knowledge_graph import (
    KnowledgeGraph,
    EdgeType,
    KnowledgeNode,
    tax_knowledge_graph,
)


@dataclass(frozen=True)
class ImpactedItem:
    """A single item impacted by a rule change."""

    node_id: str
    node_label: str
    impact_description: str
    distance: int = 0  # Number of hops from the changed rule


@dataclass
class ImpactAnalysis:
    """Complete impact analysis for a rule change."""

    changed_provision_id: str
    changed_description: str
    old_value: str = ""
    new_value: str = ""

    impacted_provisions: list[ImpactedItem] = field(default_factory=list)
    impacted_schedules: list[ImpactedItem] = field(default_factory=list)
    impacted_computation_steps: list[ImpactedItem] = field(default_factory=list)
    affected_taxpayer_segments: list[str] = field(default_factory=list)
    required_test_updates: list[str] = field(default_factory=list)
    required_code_changes: list[str] = field(default_factory=list)

    @property
    def total_impacted(self) -> int:
        return (
            len(self.impacted_provisions)
            + len(self.impacted_schedules)
            + len(self.impacted_computation_steps)
        )

    @property
    def summary(self) -> str:
        parts = [f"Impact Analysis: {self.changed_description}"]
        parts.append(f"  Provisions affected: {len(self.impacted_provisions)}")
        parts.append(f"  ITR schedules affected: {len(self.impacted_schedules)}")
        parts.append(f"  Computation steps affected: {len(self.impacted_computation_steps)}")
        parts.append(f"  Taxpayer segments: {', '.join(self.affected_taxpayer_segments) if self.affected_taxpayer_segments else 'all'}")
        return "\n".join(parts)


class RuleImpactAnalyzer:
    """Analyzes downstream impact of tax rule changes.

    Uses BFS on the knowledge graph to trace all nodes that
    depend on (or are affected by) a changed provision.
    """

    def __init__(self, graph: KnowledgeGraph | None = None) -> None:
        self.graph = graph or tax_knowledge_graph

    def analyze(
        self,
        provision_id: str,
        change_description: str,
        old_value: str = "",
        new_value: str = "",
    ) -> ImpactAnalysis:
        """Analyze the impact of changing a provision.

        Args:
            provision_id: The provision being changed (e.g., "sec_80c")
            change_description: Human-readable description of the change
            old_value: Previous value
            new_value: New value

        Returns:
            Complete ImpactAnalysis
        """
        analysis = ImpactAnalysis(
            changed_provision_id=provision_id,
            changed_description=change_description,
            old_value=old_value,
            new_value=new_value,
        )

        # BFS to find all reachable nodes via DEPENDS_ON and MAPS_TO edges
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(provision_id, 0)]

        while queue:
            current_id, distance = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            # Find all edges where this node is the source
            for edge in self.graph.edges:
                if edge.from_node == current_id:
                    # Follow DEPENDS_ON (what depends on this?) and MAPS_TO
                    if edge.edge_type in (EdgeType.DEPENDS_ON, EdgeType.MAPS_TO):
                        if edge.to_node not in visited:
                            queue.append((edge.to_node, distance + 1))

                            node = self.graph.nodes.get(edge.to_node)
                            label = node.label if node else edge.to_node
                            item = ImpactedItem(
                                node_id=edge.to_node,
                                node_label=label,
                                impact_description=f"Affected via {edge.edge_type.value}: {edge.description}" if edge.description else f"Affected via {edge.edge_type.value}",
                                distance=distance + 1,
                            )

                            # Classify by node type
                            if node and node.node_type.value == "itr_schedule":
                                analysis.impacted_schedules.append(item)
                            elif node and node.node_type.value == "provision":
                                analysis.impacted_provisions.append(item)
                            else:
                                analysis.impacted_computation_steps.append(item)

        # Determine affected taxpayer segments
        analysis.affected_taxpayer_segments = self._determine_segments(provision_id)

        # Determine required test updates
        analysis.required_test_updates = self._determine_test_updates(analysis)

        # Determine required code changes
        analysis.required_code_changes = self._determine_code_changes(analysis)

        return analysis

    def _determine_segments(self, provision_id: str) -> list[str]:
        """Determine which taxpayer segments are affected."""
        segments: list[str] = []

        # Check regime applicability
        for edge in self.graph.edges:
            if edge.to_node == provision_id:
                if edge.edge_type == EdgeType.APPLIES_TO:
                    if "old" in edge.from_node:
                        segments.append("Old Regime taxpayers")
                    elif "new" in edge.from_node:
                        segments.append("New Regime taxpayers")
                elif edge.edge_type == EdgeType.EXCLUDES:
                    if "new" in edge.from_node:
                        segments.append("New Regime taxpayers (excluded — verify)")
                    elif "old" in edge.from_node:
                        segments.append("Old Regime taxpayers (excluded — verify)")

        return segments if segments else ["All taxpayers"]

    def _determine_test_updates(self, analysis: ImpactAnalysis) -> list[str]:
        """Determine required test updates."""
        updates: list[str] = []

        provision_name = analysis.changed_provision_id.replace("sec_", "Section ").replace("_", " ")
        updates.append(f"Update golden vectors if {provision_name} changes tax liability")
        updates.append(f"Update {analysis.changed_provision_id} test cases in rule_tester.py")
        updates.append(f"Add regression test for {analysis.changed_description}")

        for item in analysis.impacted_provisions[:5]:
            updates.append(f"Verify tests for {item.node_label}")

        return updates

    def _determine_code_changes(self, analysis: ImpactAnalysis) -> list[str]:
        """Determine required code changes."""
        changes: list[str] = []

        provision_id = analysis.changed_provision_id

        # Check if it's in RuleRepository
        from src.engine.rules.config import rule_repository
        from src.models.financial_year import FinancialYear

        changes.append(f"Update TaxYearConfig for {provision_id} in rules/config.py")
        changes.append(f"Verify RuleEvaluator handles updated {provision_id} values")

        for item in analysis.impacted_schedules:
            if item.node_id in ("schedule_via", "schedule_tti"):
                changes.append(f"Update {item.node_label} builder in builders/")
            elif item.node_id in ("schedule_s", "schedule_cg"):
                changes.append(f"Review {item.node_label} computation in engine/")

        return changes


def analyze_rule_change(
    provision_id: str,
    change_description: str,
    old_value: str = "",
    new_value: str = "",
) -> ImpactAnalysis:
    """Convenience function: analyze the impact of a rule change."""
    analyzer = RuleImpactAnalyzer()
    return analyzer.analyze(provision_id, change_description, old_value, new_value)
