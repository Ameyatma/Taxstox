"""Rule Conflict Detector — Identifies contradictory or incompatible tax rules.

Traverses the knowledge graph to detect:
- OVERRIDES + APPLIES_TO conflicts (rule says both "applies" and "overrides")
- Circular DEPENDS_ON chains
- Regime exclusion contradictions
- Missing dependency edges

Traceability: C12.6 (Rule Conflict Detection — 0%→50%, P4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from src.engine.knowledge_graph import (
    KnowledgeGraph,
    EdgeType,
    tax_knowledge_graph,
)


class ConflictSeverity(str, Enum):
    ERROR = "error"        # Conflicting rules — could produce wrong tax
    WARNING = "warning"    # Suspicious pattern — likely unintended
    INFO = "info"          # Advisory — worth reviewing


@dataclass(frozen=True)
class RuleConflict:
    """A single detected rule conflict."""

    conflict_id: str
    severity: ConflictSeverity
    description: str
    nodes_involved: tuple[str, ...]  # node_ids
    recommendation: str = ""


@dataclass
class ConflictReport:
    """Complete rule conflict analysis report."""

    conflicts: list[RuleConflict] = field(default_factory=list)

    @property
    def errors(self) -> list[RuleConflict]:
        return [c for c in self.conflicts if c.severity == ConflictSeverity.ERROR]

    @property
    def warnings(self) -> list[RuleConflict]:
        return [c for c in self.conflicts if c.severity == ConflictSeverity.WARNING]

    @property
    def is_clean(self) -> bool:
        return len(self.errors) == 0


class RuleConflictDetector:
    """Detects conflicts in the tax knowledge graph.

    Domain service. Operates on the KnowledgeGraph to find:
    1. Override conflict: Both OVERRIDES and APPLIES_TO edges to same target
    2. Circular dependencies: DEPENDS_ON chains that loop back
    3. Regime contradictions: EXCLUDES + APPLIES_TO for same provision
    4. Orphaned provisions: DEPENDS_ON target doesn't exist in graph
    """

    def __init__(self, graph: KnowledgeGraph | None = None) -> None:
        self.graph = graph or tax_knowledge_graph

    def detect_all(self) -> ConflictReport:
        """Run all conflict detection checks."""
        report = ConflictReport()
        report.conflicts.extend(self._detect_override_conflicts())
        report.conflicts.extend(self._detect_circular_dependencies())
        report.conflicts.extend(self._detect_regime_contradictions())
        report.conflicts.extend(self._detect_orphaned_dependencies())
        return report

    def _detect_override_conflicts(self) -> list[RuleConflict]:
        """Detect nodes that are both overridden and applied-to by the same source."""
        conflicts: list[RuleConflict] = []

        # Build a map of (from, to) → edge types
        edge_map: dict[tuple[str, str], set[EdgeType]] = {}
        for edge in self.graph.edges:
            key = (edge.from_node, edge.to_node)
            if key not in edge_map:
                edge_map[key] = set()
            edge_map[key].add(edge.edge_type)

        # Check for conflicting edge types
        for (src, tgt), types in edge_map.items():
            if EdgeType.OVERRIDES in types and EdgeType.APPLIES_TO in types:
                src_node = self.graph.nodes.get(src)
                tgt_node = self.graph.nodes.get(tgt)
                conflicts.append(RuleConflict(
                    conflict_id=f"CONFLICT-OVERRIDE-{src}-{tgt}",
                    severity=ConflictSeverity.ERROR,
                    description=f"'{src_node.label if src_node else src}' both overrides and applies to '{tgt_node.label if tgt_node else tgt}'",
                    nodes_involved=(src, tgt),
                    recommendation="Resolve: choose either OVERRIDES or APPLIES_TO, not both",
                ))

        return conflicts

    def _detect_circular_dependencies(self) -> list[RuleConflict]:
        """Detect circular DEPENDS_ON chains using DFS."""
        conflicts: list[RuleConflict] = []

        # Build adjacency list for DEPENDS_ON edges
        adj: dict[str, list[str]] = {}
        for edge in self.graph.edges:
            if edge.edge_type == EdgeType.DEPENDS_ON:
                if edge.from_node not in adj:
                    adj[edge.from_node] = []
                adj[edge.from_node].append(edge.to_node)

        # DFS to detect cycles
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {node_id: WHITE for node_id in adj}

        def dfs(node: str, path: list[str]) -> list[str] | None:
            color[node] = GRAY
            path.append(node)
            for neighbor in adj.get(node, []):
                if color.get(neighbor, WHITE) == GRAY:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
                elif color.get(neighbor, WHITE) == WHITE:
                    result = dfs(neighbor, path)
                    if result:
                        return result
            path.pop()
            color[node] = BLACK
            return None

        visited = set()
        for node_id in adj:
            if node_id not in visited:
                cycle = dfs(node_id, [])
                if cycle:
                    node_labels = [
                        self.graph.nodes[n].label if n in self.graph.nodes else n
                        for n in cycle
                    ]
                    conflicts.append(RuleConflict(
                        conflict_id=f"CONFLICT-CYCLE-{'-'.join(cycle[:3])}",
                        severity=ConflictSeverity.ERROR,
                        description=f"Circular dependency detected: {' → '.join(node_labels)}",
                        nodes_involved=tuple(cycle),
                        recommendation="Break the cycle by removing or reversing one DEPENDS_ON edge",
                    ))
                    visited.update(cycle)
                    break  # Report one cycle at a time

        return conflicts

    def _detect_regime_contradictions(self) -> list[RuleConflict]:
        """Detect provisions both excluded and applied-to by the same regime."""
        conflicts: list[RuleConflict] = []

        regime_ids = {"regime_old", "regime_new"}
        for regime_id in regime_ids:
            applies_to = set()
            excludes = set()

            for edge in self.graph.edges:
                if edge.from_node == regime_id:
                    if edge.edge_type == EdgeType.APPLIES_TO:
                        applies_to.add(edge.to_node)
                    elif edge.edge_type == EdgeType.EXCLUDES:
                        excludes.add(edge.to_node)

            contradictions = applies_to & excludes
            for node_id in contradictions:
                node = self.graph.nodes.get(node_id)
                regime_node = self.graph.nodes.get(regime_id)
                conflicts.append(RuleConflict(
                    conflict_id=f"CONFLICT-REGIME-{regime_id}-{node_id}",
                    severity=ConflictSeverity.ERROR,
                    description=f"'{node.label if node else node_id}' is both APPLIES_TO and EXCLUDES under '{regime_node.label if regime_node else regime_id}'",
                    nodes_involved=(regime_id, node_id),
                    recommendation="Remove either APPLIES_TO or EXCLUDES edge",
                ))

        return conflicts

    def _detect_orphaned_dependencies(self) -> list[RuleConflict]:
        """Detect DEPENDS_ON edges pointing to non-existent nodes."""
        conflicts: list[RuleConflict] = []

        for edge in self.graph.edges:
            if edge.edge_type == EdgeType.DEPENDS_ON:
                if edge.to_node not in self.graph.nodes:
                    from_node = self.graph.nodes.get(edge.from_node)
                    conflicts.append(RuleConflict(
                        conflict_id=f"CONFLICT-ORPHAN-{edge.from_node}-{edge.to_node}",
                        severity=ConflictSeverity.WARNING,
                        description=f"'{from_node.label if from_node else edge.from_node}' depends on '{edge.to_node}' which does not exist in the knowledge graph",
                        nodes_involved=(edge.from_node, edge.to_node),
                        recommendation=f"Add node '{edge.to_node}' to the knowledge graph or remove this edge",
                    ))

        return conflicts


def detect_conflicts(graph: KnowledgeGraph | None = None) -> ConflictReport:
    """Convenience function: run all conflict detection."""
    detector = RuleConflictDetector(graph)
    return detector.detect_all()
