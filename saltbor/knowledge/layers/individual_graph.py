"""Individual Knowledge Graph (Layer 2).

Maintains a personal, bounded epistemic overlay referencing shared canonical
concepts or subjective local nodes, with confidence, provenance, misconceptions,
contradictions, and accessibility decay.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional

from saltbor.knowledge.graph.node import KnowledgeNode, NodeType, ValidationStatus
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.knowledge.layers.global_graph import GlobalKnowledgeGraph


@dataclasses.dataclass
class EpistemicClaim:
    """An individual's personal belief or acquaintance with a node or relationship."""

    target_id: str                      # node_id or rel_id
    is_relationship: bool = False
    confidence: float = 0.5             # Subjective certainty in [0.0, 1.0]
    source_pathway: str = "direct_experience"
    source_agent_id: Optional[str] = None
    acquired_tick: int = 0
    last_verified_tick: int = 0
    verification_count: int = 1
    contradiction_count: int = 0
    is_misconception: bool = False
    is_forgotten: bool = False          # Inaccessible or decayed from memory
    personal_notes: dict[str, Any] = dataclasses.field(default_factory=dict)
    contradictory_evidence: list[str] = dataclasses.field(default_factory=list)
    supporting_evidence: list[str] = dataclasses.field(default_factory=list)

    def reinforce(self, tick: int = 0, delta: float = 0.15, evidence: Optional[str] = None) -> None:
        """Reinforce confidence and mark as actively accessible."""
        self.confidence = min(1.0, self.confidence + delta)
        self.verification_count += 1
        self.last_verified_tick = tick
        self.is_forgotten = False
        if evidence:
            self.supporting_evidence.append(evidence)

    def weaken(self, tick: int = 0, delta: float = 0.20, evidence: Optional[str] = None) -> None:
        """Degrade confidence upon counter-evidence or contradictions."""
        self.confidence = max(0.0, self.confidence - delta)
        self.contradiction_count += 1
        self.last_verified_tick = tick
        if evidence:
            self.contradictory_evidence.append(evidence)


class IndividualKnowledgeGraph:
    """Personal epistemic graph belonging to a single synthetic human."""

    def __init__(self, human_uid: str, global_graph: Optional[GlobalKnowledgeGraph] = None) -> None:
        self.human_uid = str(human_uid)
        self.global_graph = global_graph
        # Epistemic registry: node_id -> EpistemicClaim
        self._node_claims: dict[str, EpistemicClaim] = {}
        # Epistemic registry: rel_id -> EpistemicClaim
        self._rel_claims: dict[str, EpistemicClaim] = {}
        # Private / Subjective local nodes (e.g. personal hypotheses or discoveries)
        self._local_nodes: dict[str, KnowledgeNode] = {}
        # Private / Subjective local relationships
        self._local_relationships: dict[str, KnowledgeRelationship] = {}
        # Local adjacency for rapid personal traversal
        self._out_edges: dict[str, list[KnowledgeRelationship]] = {}
        self._in_edges: dict[str, list[KnowledgeRelationship]] = {}

    # -------------------------------------------------------------------------
    # Acquaintance & Belief Acquisition
    # -------------------------------------------------------------------------

    def learn_concept(
        self,
        node_id: str,
        confidence: float = 0.7,
        source_pathway: str = "observation",
        source_agent_id: Optional[str] = None,
        tick: int = 0,
        is_misconception: bool = False,
        evidence: Optional[str] = None,
    ) -> EpistemicClaim:
        """Acquaint the agent with a concept (canonical or local)."""
        if node_id in self._node_claims:
            claim = self._node_claims[node_id]
            claim.reinforce(tick=tick, delta=confidence * 0.2, evidence=evidence)
            if is_misconception:
                claim.is_misconception = True
            return claim

        claim = EpistemicClaim(
            target_id=node_id,
            is_relationship=False,
            confidence=max(0.0, min(1.0, confidence)),
            source_pathway=source_pathway,
            source_agent_id=source_agent_id,
            acquired_tick=tick,
            last_verified_tick=tick,
            is_misconception=is_misconception,
            is_forgotten=False,
        )
        if evidence:
            claim.supporting_evidence.append(evidence)
        self._node_claims[node_id] = claim
        return claim

    def register_local_node(self, node: KnowledgeNode, confidence: float = 0.8, tick: int = 0) -> None:
        """Register a privately generated concept or hypothesis."""
        self._local_nodes[node.node_id] = node
        self.learn_concept(
            node_id=node.node_id,
            confidence=confidence,
            source_pathway="hypothesis_generation",
            tick=tick,
        )

    def add_node(self, node: KnowledgeNode, confidence: float = 0.8, tick: int = 0) -> None:
        """Convenience alias for register_local_node."""
        self.register_local_node(node=node, confidence=confidence, tick=tick)

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Convenience alias for get_concept."""
        return self.get_concept(node_id)

    def learn_relationship(
        self,
        rel: KnowledgeRelationship,
        confidence: float = 0.7,
        source_pathway: str = "observation",
        source_agent_id: Optional[str] = None,
        tick: int = 0,
        is_misconception: bool = False,
        evidence: Optional[str] = None,
    ) -> EpistemicClaim:
        """Learn or assert a relationship between two known concepts."""
        # Ensure source and target are acquainted
        if rel.source_id not in self._node_claims:
            self.learn_concept(rel.source_id, confidence=confidence * 0.8, source_pathway=source_pathway, tick=tick)
        if rel.target_id not in self._node_claims:
            self.learn_concept(rel.target_id, confidence=confidence * 0.8, source_pathway=source_pathway, tick=tick)

        self._local_relationships[rel.rel_id] = rel
        if rel.source_id not in self._out_edges:
            self._out_edges[rel.source_id] = []
        if rel.target_id not in self._in_edges:
            self._in_edges[rel.target_id] = []

        # Avoid duplicates in adjacency
        if not any(r.rel_id == rel.rel_id for r in self._out_edges[rel.source_id]):
            self._out_edges[rel.source_id].append(rel)
        if not any(r.rel_id == rel.rel_id for r in self._in_edges[rel.target_id]):
            self._in_edges[rel.target_id].append(rel)

        claim = EpistemicClaim(
            target_id=rel.rel_id,
            is_relationship=True,
            confidence=max(0.0, min(1.0, confidence)),
            source_pathway=source_pathway,
            source_agent_id=source_agent_id,
            acquired_tick=tick,
            last_verified_tick=tick,
            is_misconception=is_misconception,
            is_forgotten=False,
        )
        if evidence:
            claim.supporting_evidence.append(evidence)
        self._rel_claims[rel.rel_id] = claim
        return claim

    # -------------------------------------------------------------------------
    # Retrieval and Epistemic Status
    # -------------------------------------------------------------------------

    def knows_concept(self, node_id: str, min_confidence: float = 0.15) -> bool:
        """Check if individual is acquainted with concept and hasn't forgotten it."""
        claim = self._node_claims.get(node_id)
        if not claim or claim.is_forgotten:
            return False
        return claim.confidence >= min_confidence

    def get_concept(self, node_id: str) -> Optional[KnowledgeNode]:
        """Resolve concept node from local nodes or global graph if acquainted."""
        if not self.knows_concept(node_id):
            return None
        if node_id in self._local_nodes:
            return self._local_nodes[node_id]
        if self.global_graph and self.global_graph.has_node(node_id):
            return self.global_graph.get_node(node_id)
        # Create lightweight placeholder if node was learned without explicit registration
        placeholder = KnowledgeNode(node_id=node_id, node_type=NodeType.CONCEPT, label=node_id)
        self._local_nodes[node_id] = placeholder
        return placeholder

    def get_claim(self, item_id: str) -> Optional[EpistemicClaim]:
        """Fetch epistemic claim for node or relationship."""
        return self._node_claims.get(item_id) or self._rel_claims.get(item_id)

    def all_known_node_ids(self) -> list[str]:
        """Return all active, non-forgotten node IDs."""
        return [nid for nid, c in self._node_claims.items() if not c.is_forgotten and c.confidence > 0.1]

    def all_known_nodes(self) -> list[KnowledgeNode]:
        """Return all accessible knowledge nodes."""
        nodes = []
        for nid in self.all_known_node_ids():
            n = self.get_concept(nid)
            if n:
                nodes.append(n)
        return nodes

    def get_neighbors(
        self,
        node_id: str,
        rel_type: Optional[RelationshipType | str] = None,
        min_confidence: float = 0.2,
    ) -> list[KnowledgeNode]:
        """Get neighboring nodes according to personal beliefs and accessible claims."""
        if not self.knows_concept(node_id):
            return []

        rel_filter = str(rel_type.value if isinstance(rel_type, RelationshipType) else rel_type) if rel_type else None
        neighbors = []
        for rel in self._out_edges.get(node_id, []):
            claim = self._rel_claims.get(rel.rel_id)
            if not claim or claim.is_forgotten or claim.confidence < min_confidence:
                continue
            r_type = str(rel.rel_type.value if isinstance(rel.rel_type, RelationshipType) else rel.rel_type)
            if rel_filter and r_type != rel_filter:
                continue
            target_node = self.get_concept(rel.target_id)
            if target_node:
                neighbors.append(target_node)
        return neighbors

    # -------------------------------------------------------------------------
    # Epistemic Decay & Forgetting
    # -------------------------------------------------------------------------

    def apply_decay(self, elapsed_ticks: int, retention_rate: float = 0.95) -> int:
        """Apply cognitive forgetting to unused, unreinforced beliefs.

        Returns number of forgotten items.
        """
        forgotten_count = 0
        decay_amount = (elapsed_ticks / 1000.0) * (1.0 - min(0.99, retention_rate)) * 0.1

        for claim in self._node_claims.values():
            if claim.is_forgotten:
                continue
            # Salience protection: frequently verified or high confidence items resist decay
            if claim.verification_count > 3 or claim.confidence > 0.85:
                continue
            claim.confidence = max(0.0, claim.confidence - decay_amount)
            if claim.confidence < 0.15:
                claim.is_forgotten = True
                forgotten_count += 1

        for claim in self._rel_claims.values():
            if claim.is_forgotten:
                continue
            if claim.verification_count > 3 or claim.confidence > 0.85:
                continue
            claim.confidence = max(0.0, claim.confidence - decay_amount)
            if claim.confidence < 0.15:
                claim.is_forgotten = True
                forgotten_count += 1

        return forgotten_count
