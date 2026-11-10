"""High-performance Knowledge Graph Engine for Saltbor Phase 0.6.

Maintains indexed forward and backward adjacency structures for sub-millisecond
neighborhood queries, cycle-safe multi-hop traversal, subgraph extraction,
and optional NetworkX topological bridging.
"""

from __future__ import annotations

import collections
import logging
from typing import Any, Callable, Iterator, Optional

from saltbor.knowledge.graph.node import KnowledgeNode, NodeType, ValidationStatus
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType

logger = logging.getLogger(__name__)


class KnowledgeGraphEngine:
    """Core in-memory graph representation with indexed adjacency."""

    def __init__(self, name: str = "KnowledgeGraph") -> None:
        self.name = name
        self._nodes: dict[str, KnowledgeNode] = {}
        # Adjacency indexes: node_id -> list of KnowledgeRelationship
        self._out_edges: dict[str, list[KnowledgeRelationship]] = collections.defaultdict(list)
        self._in_edges: dict[str, list[KnowledgeRelationship]] = collections.defaultdict(list)
        # Type index: NodeType/str -> set of node_ids
        self._type_index: dict[str, set[str]] = collections.defaultdict(set)
        # Relationship type index: RelationshipType/str -> set of rel_ids
        self._rel_type_index: dict[str, set[str]] = collections.defaultdict(set)
        self._relationships: dict[str, KnowledgeRelationship] = {}

    # -------------------------------------------------------------------------
    # Node Operations
    # -------------------------------------------------------------------------

    def add_node(self, node: KnowledgeNode) -> None:
        """Insert or replace a node, indexing its type."""
        self._nodes[node.node_id] = node
        t_key = str(node.node_type.value if isinstance(node.node_type, NodeType) else node.node_type)
        self._type_index[t_key].add(node.node_id)
        if node.node_id not in self._out_edges:
            self._out_edges[node.node_id] = []
        if node.node_id not in self._in_edges:
            self._in_edges[node.node_id] = []

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Fetch node by unique ID."""
        return self._nodes.get(node_id)

    def has_node(self, node_id: str) -> bool:
        """Check if node exists."""
        return node_id in self._nodes

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all incident edges."""
        if node_id not in self._nodes:
            return False

        node = self._nodes.pop(node_id)
        t_key = str(node.node_type.value if isinstance(node.node_type, NodeType) else node.node_type)
        self._type_index[t_key].discard(node_id)

        # Remove outgoing edges
        for rel in list(self._out_edges.get(node_id, [])):
            self.remove_relationship(rel.rel_id)

        # Remove incoming edges
        for rel in list(self._in_edges.get(node_id, [])):
            self.remove_relationship(rel.rel_id)

        self._out_edges.pop(node_id, None)
        self._in_edges.pop(node_id, None)
        return True

    def get_nodes_by_type(self, node_type: NodeType | str) -> list[KnowledgeNode]:
        """Fast lookup of all nodes matching a specific type."""
        t_key = str(node_type.value if isinstance(node_type, NodeType) else node_type)
        return [self._nodes[nid] for nid in self._type_index.get(t_key, set()) if nid in self._nodes]

    def all_nodes(self) -> list[KnowledgeNode]:
        """Return all nodes."""
        return list(self._nodes.values())

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    # -------------------------------------------------------------------------
    # Relationship Operations
    # -------------------------------------------------------------------------

    def add_relationship(self, rel: KnowledgeRelationship) -> None:
        """Add a directed typed relationship and update adjacency indexes."""
        self._relationships[rel.rel_id] = rel
        self._out_edges[rel.source_id].append(rel)
        self._in_edges[rel.target_id].append(rel)
        r_key = str(rel.rel_type.value if isinstance(rel.rel_type, RelationshipType) else rel.rel_type)
        self._rel_type_index[r_key].add(rel.rel_id)

    def get_relationship(self, rel_id: str) -> Optional[KnowledgeRelationship]:
        return self._relationships.get(rel_id)

    def remove_relationship(self, rel_id: str) -> bool:
        if rel_id not in self._relationships:
            return False
        rel = self._relationships.pop(rel_id)
        r_key = str(rel.rel_type.value if isinstance(rel.rel_type, RelationshipType) else rel.rel_type)
        self._rel_type_index[r_key].discard(rel_id)

        if rel.source_id in self._out_edges:
            self._out_edges[rel.source_id] = [r for r in self._out_edges[rel.source_id] if r.rel_id != rel_id]
        if rel.target_id in self._in_edges:
            self._in_edges[rel.target_id] = [r for r in self._in_edges[rel.target_id] if r.rel_id != rel_id]
        return True

    def all_relationships(self) -> list[KnowledgeRelationship]:
        return list(self._relationships.values())

    @property
    def relationship_count(self) -> int:
        return len(self._relationships)

    # -------------------------------------------------------------------------
    # Neighborhood & Query Operations
    # -------------------------------------------------------------------------

    def get_out_relationships(
        self,
        node_id: str,
        rel_type: Optional[RelationshipType | str] = None,
        min_confidence: float = 0.0,
    ) -> list[KnowledgeRelationship]:
        """Retrieve outgoing relationships from a node with optional filtering."""
        edges = self._out_edges.get(node_id, [])
        if rel_type is not None:
            r_val = str(rel_type.value if isinstance(rel_type, RelationshipType) else rel_type)
            edges = [e for e in edges if str(e.rel_type.value if isinstance(e.rel_type, RelationshipType) else e.rel_type) == r_val]
        if min_confidence > 0.0:
            edges = [e for e in edges if e.confidence >= min_confidence]
        return edges

    def get_in_relationships(
        self,
        node_id: str,
        rel_type: Optional[RelationshipType | str] = None,
        min_confidence: float = 0.0,
    ) -> list[KnowledgeRelationship]:
        """Retrieve incoming relationships to a node with optional filtering."""
        edges = self._in_edges.get(node_id, [])
        if rel_type is not None:
            r_val = str(rel_type.value if isinstance(rel_type, RelationshipType) else rel_type)
            edges = [e for e in edges if str(e.rel_type.value if isinstance(e.rel_type, RelationshipType) else e.rel_type) == r_val]
        if min_confidence > 0.0:
            edges = [e for e in edges if e.confidence >= min_confidence]
        return edges

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "out",  # "out", "in", "both"
        rel_type: Optional[RelationshipType | str] = None,
    ) -> list[KnowledgeNode]:
        """Get neighboring nodes along outgoing, incoming, or bidirectional edges."""
        target_ids: set[str] = set()
        if direction in ("out", "both"):
            for e in self.get_out_relationships(node_id, rel_type=rel_type):
                target_ids.add(e.target_id)
        if direction in ("in", "both"):
            for e in self.get_in_relationships(node_id, rel_type=rel_type):
                target_ids.add(e.source_id)

        return [self._nodes[tid] for tid in target_ids if tid in self._nodes]

    # -------------------------------------------------------------------------
    # Multi-Hop Traversal & Search
    # -------------------------------------------------------------------------

    def traverse_multi_hop(
        self,
        start_node_id: str,
        max_depth: int = 3,
        rel_types: Optional[list[RelationshipType | str]] = None,
        direction: str = "out",
        min_confidence: float = 0.0,
    ) -> list[tuple[str, int, list[str]]]:
        """BFS multi-hop traversal with cycle prevention.

        Returns list of tuples: (visited_node_id, depth, path_of_rel_ids)
        """
        if start_node_id not in self._nodes:
            return []

        rel_filter = None
        if rel_types:
            rel_filter = {str(r.value if isinstance(r, RelationshipType) else r) for r in rel_types}

        visited: set[str] = {start_node_id}
        queue: collections.deque[tuple[str, int, list[str]]] = collections.deque([(start_node_id, 0, [])])
        results: list[tuple[str, int, list[str]]] = []

        while queue:
            current_id, depth, path = queue.popleft()
            if depth > 0:
                results.append((current_id, depth, path))

            if depth >= max_depth:
                continue

            # Candidate edges
            candidate_edges: list[tuple[str, KnowledgeRelationship]] = []
            if direction in ("out", "both"):
                for e in self._out_edges.get(current_id, []):
                    candidate_edges.append((e.target_id, e))
            if direction in ("in", "both"):
                for e in self._in_edges.get(current_id, []):
                    candidate_edges.append((e.source_id, e))

            for neighbor_id, edge in candidate_edges:
                if edge.confidence < min_confidence:
                    continue
                e_type = str(edge.rel_type.value if isinstance(edge.rel_type, RelationshipType) else edge.rel_type)
                if rel_filter and e_type not in rel_filter:
                    continue
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1, path + [edge.rel_id]))

        return results

    def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        rel_types: Optional[list[RelationshipType | str]] = None,
        direction: str = "out",
    ) -> Optional[list[tuple[str, str, str]]]:
        """Find shortest path from source to target.

        Returns list of (curr_node, rel_type, next_node) or None.
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return None
        if source_id == target_id:
            return []

        rel_filter = None
        if rel_types:
            rel_filter = {str(r.value if isinstance(r, RelationshipType) else r) for r in rel_types}

        visited: set[str] = {source_id}
        queue: collections.deque[tuple[str, list[tuple[str, str, str]]]] = collections.deque([(source_id, [])])

        while queue:
            curr, path = queue.popleft()
            if curr == target_id:
                return path

            candidate_edges: list[tuple[str, KnowledgeRelationship]] = []
            if direction in ("out", "both"):
                for e in self._out_edges.get(curr, []):
                    candidate_edges.append((e.target_id, e))
            if direction in ("in", "both"):
                for e in self._in_edges.get(curr, []):
                    candidate_edges.append((e.source_id, e))

            for nxt, edge in candidate_edges:
                e_type = str(edge.rel_type.value if isinstance(edge.rel_type, RelationshipType) else edge.rel_type)
                if rel_filter and e_type not in rel_filter:
                    continue
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, path + [(curr, e_type, nxt)]))

        return None

    # -------------------------------------------------------------------------
    # Subgraph Extraction
    # -------------------------------------------------------------------------

    def extract_subgraph(
        self,
        center_node_id: str,
        radius: int = 1,
        rel_types: Optional[list[RelationshipType | str]] = None,
    ) -> KnowledgeGraphEngine:
        """Extract ego subgraph around center_node_id up to radius hops."""
        sub = KnowledgeGraphEngine(name=f"Subgraph_{center_node_id}_r{radius}")
        if center_node_id not in self._nodes:
            return sub

        sub.add_node(self._nodes[center_node_id])
        traversals = self.traverse_multi_hop(center_node_id, max_depth=radius, rel_types=rel_types, direction="both")
        for nid, _, _ in traversals:
            if nid in self._nodes:
                sub.add_node(self._nodes[nid])

        sub_node_ids = set(sub._nodes.keys())
        for nid in sub_node_ids:
            for rel in self._out_edges.get(nid, []):
                if rel.target_id in sub_node_ids:
                    sub.add_relationship(rel)

        return sub

    # -------------------------------------------------------------------------
    # NetworkX Bridge (Optional)
    # -------------------------------------------------------------------------

    def to_networkx(self) -> Any:
        """Convert this graph to a NetworkX DiGraph for advanced topological metrics."""
        try:
            import networkx as nx
        except ImportError:
            raise RuntimeError("NetworkX is not installed; install 'networkx' to use graph analytics bridge.")

        G = nx.DiGraph()
        for node in self._nodes.values():
            G.add_node(
                node.node_id,
                label=node.label,
                node_type=str(node.node_type.value if isinstance(node.node_type, NodeType) else node.node_type),
                validation_status=str(node.validation_status.value if isinstance(node.validation_status, ValidationStatus) else node.validation_status),
                **node.properties,
            )
        for rel in self._relationships.values():
            G.add_edge(
                rel.source_id,
                rel.target_id,
                rel_id=rel.rel_id,
                rel_type=str(rel.rel_type.value if isinstance(rel.rel_type, RelationshipType) else rel.rel_type),
                weight=rel.weight,
                confidence=rel.confidence,
                **rel.metadata,
            )
        return G
