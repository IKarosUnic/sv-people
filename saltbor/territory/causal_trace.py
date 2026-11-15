"""Causal Trace Engine for SALTBOR Generalized Territorial Scenarios.

Implements rigorous, multi-hop causal tracking for complex territorial systems:
- Traces every major systemic consequence back to its structural root causes.
- Strictly distinguishes epistemic categories:
    A. EXPLICIT_MECHANISM: Deterministic / rule-based causal mechanism implemented in simulation code.
    B. OBSERVED_ASSOCIATION: Statistical correlation / association observed in simulation run data.
    C. CAUSAL_HYPOTHESIS: Theoretical hypothesis pending empirical validation.
    D. EMPIRICAL_EVIDENCE: Relationship backed by external empirical literature / survey data (e.g. BCR, MINED, MINSAL).
- Generates DAGs (Directed Acyclic Graphs) with path search, root-cause analysis,
  downstream impact projection, and export to JSON and Mermaid diagram formats.
"""

from __future__ import annotations

import collections
import dataclasses
import enum
from typing import Any, Dict, List, Optional, Set, Tuple


class EpistemicCategory(str, enum.Enum):
    """Rigorous epistemic classification of systemic relationships."""
    EXPLICIT_MECHANISM = "EXPLICIT_MECHANISM"       # Implemented directly in engine equations / rules
    OBSERVED_ASSOCIATION = "OBSERVED_ASSOCIATION"   # Statistical co-occurrence in simulation run
    CAUSAL_HYPOTHESIS = "CAUSAL_HYPOTHESIS"         # Theoretical hypothesis pending validation
    EMPIRICAL_EVIDENCE = "EMPIRICAL_EVIDENCE"       # Calibrated against external data / literature


@dataclasses.dataclass
class CausalNode:
    """A discrete state observation or milestone event in the causal trajectory."""
    node_id: str
    entity_id: str
    entity_type: str         # "individual", "household", "business", "facility", "infrastructure", "territory"
    domain: str              # "transport", "commerce", "education", "healthcare", "household_finance", "governance"
    state_variable: str      # e.g., "road_friction", "cash_balance", "school_attendance", "health_status"
    value: Any
    unit: str
    tick: int
    label: str


@dataclasses.dataclass
class CausalEdge:
    """A directed causal or associational transition from an antecedent to a consequence."""
    edge_id: str
    source_node_id: str
    target_node_id: str
    mechanism_name: str
    magnitude_delta: float
    time_delay_ticks: int
    responsible_engine: str
    evidence_or_rule: str
    confidence: float        # 0.0 to 1.0
    epistemic_category: EpistemicCategory
    limitations: str = ""


class CausalTraceEngine:
    """Records, queries, and analyzes causal propagation networks across territorial domains."""

    def __init__(self) -> None:
        self.nodes: Dict[str, CausalNode] = {}
        self.edges: Dict[str, CausalEdge] = {}
        self._adjacency_out: Dict[str, List[str]] = collections.defaultdict(list)  # source -> [edge_ids]
        self._adjacency_in: Dict[str, List[str]] = collections.defaultdict(list)   # target -> [edge_ids]

    def clear(self) -> None:
        """Reset the trace graph."""
        self.nodes.clear()
        self.edges.clear()
        self._adjacency_out.clear()
        self._adjacency_in.clear()

    def record_node(
        self,
        node_id: str,
        entity_id: str,
        entity_type: str,
        domain: str,
        state_variable: str,
        value: Any,
        unit: str,
        tick: int,
        label: str,
    ) -> CausalNode:
        """Register a state observation milestone in the causal trace."""
        node = CausalNode(
            node_id=node_id,
            entity_id=entity_id,
            entity_type=entity_type,
            domain=domain,
            state_variable=state_variable,
            value=value,
            unit=unit,
            tick=tick,
            label=label,
        )
        self.nodes[node_id] = node
        return node

    def record_relation(
        self,
        edge_id: str,
        source_node_id: str,
        target_node_id: str,
        mechanism_name: str,
        magnitude_delta: float,
        time_delay_ticks: int,
        responsible_engine: str,
        evidence_or_rule: str,
        confidence: float,
        epistemic_category: EpistemicCategory,
        limitations: str = "",
    ) -> CausalEdge:
        """Record a directed relation between two state observations."""
        if source_node_id not in self.nodes:
            raise ValueError(f"Source causal node '{source_node_id}' does not exist.")
        if target_node_id not in self.nodes:
            raise ValueError(f"Target causal node '{target_node_id}' does not exist.")

        edge = CausalEdge(
            edge_id=edge_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            mechanism_name=mechanism_name,
            magnitude_delta=magnitude_delta,
            time_delay_ticks=time_delay_ticks,
            responsible_engine=responsible_engine,
            evidence_or_rule=evidence_or_rule,
            confidence=max(0.0, min(1.0, confidence)),
            epistemic_category=epistemic_category,
            limitations=limitations,
        )
        self.edges[edge_id] = edge
        self._adjacency_out[source_node_id].append(edge_id)
        self._adjacency_in[target_node_id].append(edge_id)
        return edge

    # =========================================================================
    # Query & Traversal Capabilities
    # =========================================================================

    def trace_root_causes(self, target_node_id: str) -> List[CausalNode]:
        """Backward traversal to identify all upstream root-cause nodes (nodes with no incoming edges)."""
        if target_node_id not in self.nodes:
            return []

        visited_nodes: Set[str] = set()
        roots: List[CausalNode] = []
        queue: collections.deque[str] = collections.deque([target_node_id])

        while queue:
            curr_id = queue.popleft()
            if curr_id in visited_nodes:
                continue
            visited_nodes.add(curr_id)

            in_edge_ids = self._adjacency_in.get(curr_id, [])
            if not in_edge_ids:
                if curr_id != target_node_id or len(self.nodes) == 1:
                    roots.append(self.nodes[curr_id])
            else:
                for eid in in_edge_ids:
                    src_id = self.edges[eid].source_node_id
                    if src_id not in visited_nodes:
                        queue.append(src_id)

        return roots

    def trace_downstream_impacts(self, source_node_id: str) -> List[CausalNode]:
        """Forward traversal to identify all cascading consequences stemming from a trigger node."""
        if source_node_id not in self.nodes:
            return []

        visited_nodes: Set[str] = set()
        consequences: List[CausalNode] = []
        queue: collections.deque[str] = collections.deque([source_node_id])

        while queue:
            curr_id = queue.popleft()
            if curr_id in visited_nodes:
                continue
            visited_nodes.add(curr_id)

            if curr_id != source_node_id:
                consequences.append(self.nodes[curr_id])

            out_edge_ids = self._adjacency_out.get(curr_id, [])
            for eid in out_edge_ids:
                tgt_id = self.edges[eid].target_node_id
                if tgt_id not in visited_nodes:
                    queue.append(tgt_id)

        return consequences

    def find_causal_paths(self, start_node_id: str, end_node_id: str) -> List[List[str]]:
        """Find all directed simple paths between two nodes."""
        if start_node_id not in self.nodes or end_node_id not in self.nodes:
            return []

        paths: List[List[str]] = []

        def dfs(current: str, target: str, current_path: List[str], visited: Set[str]) -> None:
            if current == target:
                paths.append(list(current_path))
                return

            visited.add(current)
            for eid in self._adjacency_out.get(current, []):
                nxt = self.edges[eid].target_node_id
                if nxt not in visited:
                    current_path.append(nxt)
                    dfs(nxt, target, current_path, visited)
                    current_path.pop()
            visited.remove(current)

        dfs(start_node_id, end_node_id, [start_node_id], set())
        return paths

    def count_by_epistemic_category(self) -> Dict[str, int]:
        """Tally edge count per epistemic category to audit scientific rigor."""
        counts = {cat.value: 0 for cat in EpistemicCategory}
        for edge in self.edges.values():
            counts[edge.epistemic_category.value] += 1
        return counts

    # =========================================================================
    # Export Formats
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Serialize full causal trace graph into a JSON-serializable dictionary."""
        return {
            "nodes": [
                {
                    "node_id": n.node_id,
                    "entity_id": n.entity_id,
                    "entity_type": n.entity_type,
                    "domain": n.domain,
                    "state_variable": n.state_variable,
                    "value": n.value,
                    "unit": n.unit,
                    "tick": n.tick,
                    "label": n.label,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "edge_id": e.edge_id,
                    "source_node_id": e.source_node_id,
                    "target_node_id": e.target_node_id,
                    "mechanism_name": e.mechanism_name,
                    "magnitude_delta": e.magnitude_delta,
                    "time_delay_ticks": e.time_delay_ticks,
                    "responsible_engine": e.responsible_engine,
                    "evidence_or_rule": e.evidence_or_rule,
                    "confidence": e.confidence,
                    "epistemic_category": e.epistemic_category.value,
                    "limitations": e.limitations,
                }
                for e in self.edges.values()
            ],
            "metrics": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "epistemic_breakdown": self.count_by_epistemic_category(),
            },
        }

    def to_mermaid(self) -> str:
        """Generate a Mermaid flowchart diagram of the causal cascade."""
        lines = ["flowchart TD"]
        for node in self.nodes.values():
            safe_label = f"\"{node.label}\\n[{node.domain}: {node.value} {node.unit}]\""
            lines.append(f"    {node.node_id}[{safe_label}]")

        for edge in self.edges.values():
            cat_short = edge.epistemic_category.value[:4]
            lines.append(
                f"    {edge.source_node_id} -->|{edge.mechanism_name} ({cat_short})| {edge.target_node_id}"
            )
        return "\n".join(lines)
