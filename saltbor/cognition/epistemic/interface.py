"""Epistemic Interface for Saltbor Individuals (Section 1).

Provides an individual agent with an un-omniscient, bounded lens to query
their personal knowledge graph, retrieve episodic memory traces, detect
contradictions, evaluate source credibility, update beliefs upon evidence,
and assess epistemic needs (knowing when to learn or request assistance).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.memory.episodic import EpisodicRecord
from saltbor.knowledge.graph.node import KnowledgeNode, NodeType
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.knowledge.layers.individual_graph import EpistemicClaim, IndividualKnowledgeGraph

logger = logging.getLogger(__name__)


class EpistemicInterface:
    """Bounded, subjective epistemic query and belief management interface."""

    def __init__(
        self,
        human_uid: str,
        knowledge_graph: IndividualKnowledgeGraph,
        memory: Optional[MemoryEngine] = None,
    ) -> None:
        self.human_uid = str(human_uid)
        self.knowledge_graph = knowledge_graph
        self.memory = memory
        # Dedicated personal beliefs table: belief_id -> EpistemicBelief
        self._beliefs: dict[str, EpistemicBelief] = {}
        # Known agents' credibility history: agent_uid -> score in [0.0, 1.0]
        self._source_credibility: dict[str, float] = {}

    # -------------------------------------------------------------------------
    # 1. Knowledge Queries
    # -------------------------------------------------------------------------

    def query_relevant_knowledge(
        self,
        concept_or_tag: str,
        min_confidence: float = 0.25,
    ) -> list[KnowledgeNode]:
        """Consult personal knowledge for concepts matching a query or related to it."""
        results: list[KnowledgeNode] = []
        # Check direct knowledge
        if self.knowledge_graph.knows_concept(concept_or_tag, min_confidence=min_confidence):
            node = self.knowledge_graph.get_concept(concept_or_tag)
            if node:
                results.append(node)

        # Check neighborhood relationships
        neighbors = self.knowledge_graph.get_neighbors(concept_or_tag, min_confidence=min_confidence)
        for n in neighbors:
            if n not in results:
                results.append(n)

        # Check all known nodes for property/tag matches
        for nid in self.knowledge_graph.all_known_node_ids():
            claim = self.knowledge_graph.get_claim(nid)
            if not claim or claim.is_forgotten or claim.confidence < min_confidence:
                continue
            node = self.knowledge_graph.get_concept(nid)
            if not node:
                continue
            if concept_or_tag.lower() in node.label.lower() or concept_or_tag.lower() in node.description.lower():
                if node not in results:
                    results.append(node)

        return results

    def get_concept_properties(self, concept_id: str) -> dict[str, Any]:
        """Fetch properties of a known concept."""
        if not self.knowledge_graph.knows_concept(concept_id):
            return {}
        node = self.knowledge_graph.get_concept(concept_id)
        return dict(node.properties) if node else {}

    # -------------------------------------------------------------------------
    # 2. Episodic Experience Retrieval
    # -------------------------------------------------------------------------

    def retrieve_past_experiences(
        self,
        query_text: str,
        limit: int = 5,
        min_salience: float = 0.2,
    ) -> list[EpisodicRecord]:
        """Retrieve relevant past episodic memories matching query keywords."""
        if not self.memory:
            return []

        all_memories = self.memory.episodic.get_recent(count=50)
        query_terms = [t.lower() for t in query_text.split() if len(t) > 2]
        scored: list[tuple[float, EpisodicRecord]] = []

        for rec in all_memories:
            if rec.importance < min_salience:
                continue
            summary_lower = rec.summary.lower()
            overlap = sum(1 for term in query_terms if term in summary_lower)
            if overlap > 0 or not query_terms:
                score = (overlap * 0.5) + (rec.importance * 0.3) + (abs(rec.emotional_valence) * 0.2)
                scored.append((score, rec))

        scored.sort(key=lambda s: s[0], reverse=True)
        return [rec for _, rec in scored[:limit]]

    # -------------------------------------------------------------------------
    # 3. Missing Information Detection
    # -------------------------------------------------------------------------

    def identify_missing_information(
        self,
        required_elements: list[str],
        min_confidence: float = 0.30,
    ) -> list[str]:
        """Identify which required concepts, materials, or facts are currently unknown."""
        missing: list[str] = []
        for elem in required_elements:
            if not self.knowledge_graph.knows_concept(elem, min_confidence=min_confidence):
                # Also check local beliefs
                has_belief = any(
                    b.subject == elem and b.is_active and b.confidence >= min_confidence
                    for b in self._beliefs.values()
                )
                if not has_belief:
                    missing.append(elem)
        return missing

    # -------------------------------------------------------------------------
    # 4. Cross-Domain Concept Combination
    # -------------------------------------------------------------------------

    def combine_concepts(
        self,
        concept_a_id: str,
        concept_b_id: str,
        tick: int = 0,
    ) -> Optional[dict[str, Any]]:
        """Combine two known concepts to explore potential syntheses or similarities."""
        if not self.knowledge_graph.knows_concept(concept_a_id) or not self.knowledge_graph.knows_concept(concept_b_id):
            return None

        node_a = self.knowledge_graph.get_concept(concept_a_id)
        node_b = self.knowledge_graph.get_concept(concept_b_id)
        if not node_a or not node_b:
            return None

        shared_props = set(node_a.properties.keys()).intersection(set(node_b.properties.keys()))
        synthesis_name = f"Synthesis of {node_a.label} and {node_b.label}"

        return {
            "concept_a": node_a.node_id,
            "concept_b": node_b.node_id,
            "shared_properties": list(shared_props),
            "synthesis_name": synthesis_name,
            "domain_a": node_a.properties.get("domain", "general"),
            "domain_b": node_b.properties.get("domain", "general"),
            "compatibility_score": max(0.2, len(shared_props) / max(1, len(node_a.properties) + len(node_b.properties))),
        }

    # -------------------------------------------------------------------------
    # 5. Contradiction Detection
    # -------------------------------------------------------------------------

    def detect_contradictions(self) -> list[dict[str, Any]]:
        """Detect logical or factual contradictions among personal beliefs."""
        contradictions: list[dict[str, Any]] = []

        # Check explicit contradictory relationships in graph
        for rel in self.knowledge_graph._local_relationships.values():
            r_type = str(rel.rel_type.value if hasattr(rel.rel_type, "value") else rel.rel_type)
            if r_type == "CONTRADICTS":
                claim = self.knowledge_graph.get_claim(rel.rel_id)
                if claim and not claim.is_forgotten and claim.confidence >= 0.2:
                    contradictions.append({
                        "type": "relational_contradiction",
                        "source": rel.source_id,
                        "target": rel.target_id,
                        "confidence": claim.confidence,
                        "description": f"Belief in '{rel.source_id}' directly contradicts '{rel.target_id}'",
                    })

        # Check beliefs with mutual opposition
        active_beliefs = [b for b in self._beliefs.values() if b.is_active]
        for i, b1 in enumerate(active_beliefs):
            for b2 in active_beliefs[i + 1 :]:
                if b1.subject == b2.subject and b1.predicate == b2.predicate:
                    if b1.object_val != b2.object_val:
                        contradictions.append({
                            "type": "value_contradiction",
                            "subject": b1.subject,
                            "predicate": b1.predicate,
                            "belief_1": {"val": b1.object_val, "conf": b1.confidence, "source": b1.source_type},
                            "belief_2": {"val": b2.object_val, "conf": b2.confidence, "source": b2.source_type},
                            "description": f"Conflicting beliefs about {b1.subject}.{b1.predicate}: {b1.object_val} vs {b2.object_val}",
                        })

        return contradictions

    # -------------------------------------------------------------------------
    # 6. Source Reliability Evaluation
    # -------------------------------------------------------------------------

    def evaluate_source_reliability(
        self,
        source_agent_id: str,
        social_trust: float = 0.5,
    ) -> float:
        """Evaluate the reliability of a testimony source.

        Balances prior historical credibility and social relationship trust.
        """
        prior_cred = self._source_credibility.get(source_agent_id, 0.5)
        # Blended credibility
        reliability = (prior_cred * 0.6) + (social_trust * 0.4)
        return max(0.05, min(0.95, reliability))

    def record_source_outcome(
        self,
        source_agent_id: str,
        was_truthful: bool,
    ) -> None:
        """Update credibility of a source based on verified accuracy."""
        current = self._source_credibility.get(source_agent_id, 0.5)
        if was_truthful:
            self._source_credibility[source_agent_id] = min(0.95, current + 0.10)
        else:
            self._source_credibility[source_agent_id] = max(0.05, current - 0.25)

    # -------------------------------------------------------------------------
    # 7. Belief Management & Evidentiary Updating
    # -------------------------------------------------------------------------

    def register_belief(self, belief: EpistemicBelief) -> EpistemicBelief:
        """Register a new subjective belief."""
        self._beliefs[belief.belief_id] = belief
        return belief

    def get_belief(self, belief_id: str) -> Optional[EpistemicBelief]:
        return self._beliefs.get(belief_id)

    def find_beliefs_about(self, subject: str) -> list[EpistemicBelief]:
        return [b for b in self._beliefs.values() if b.subject == subject and b.is_active]

    def update_belief_with_evidence(
        self,
        belief_id_or_concept: str,
        evidence: str,
        is_supporting: bool,
        evidence_weight: float = 1.0,
        tick: int = 0,
    ) -> float:
        """Revise belief confidence after receiving empirical evidence."""
        # Check in local beliefs
        if belief_id_or_concept in self._beliefs:
            return self._beliefs[belief_id_or_concept].update_with_evidence(
                evidence=evidence,
                is_supporting=is_supporting,
                evidence_weight=evidence_weight,
                tick=tick,
            )

        # Check in knowledge graph claims
        claim = self.knowledge_graph.get_claim(belief_id_or_concept)
        if claim:
            if is_supporting:
                claim.reinforce(tick=tick, delta=0.15 * evidence_weight, evidence=evidence)
            else:
                claim.weaken(tick=tick, delta=0.20 * evidence_weight, evidence=evidence)
            return claim.confidence

        return 0.5

    # -------------------------------------------------------------------------
    # 8. Epistemic Need Assessment (Knowing when to learn or ask for help)
    # -------------------------------------------------------------------------

    def assess_epistemic_need(
        self,
        task_requirements: list[str],
        confidence_threshold: float = 0.40,
    ) -> tuple[bool, list[str]]:
        """Determine whether the agent has sufficient knowledge or needs to learn/ask for help.

        Returns (is_sufficient: bool, missing_or_uncertain_elements: list[str]).
        """
        uncertain_or_missing: list[str] = []

        for req in task_requirements:
            claim = self.knowledge_graph.get_claim(req)
            if not claim or claim.is_forgotten:
                uncertain_or_missing.append(req)
            elif claim.confidence < confidence_threshold:
                uncertain_or_missing.append(f"{req} (low confidence: {claim.confidence:.2f})")

        is_sufficient = len(uncertain_or_missing) == 0
        return is_sufficient, uncertain_or_missing
