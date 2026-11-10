"""Analogical Reasoning Engine for Saltbor Phase 0.6.

Identifies structural isomorphisms between familiar source domains and novel
target domains to generate plausible hypotheses rather than guaranteed truths.
"""

from __future__ import annotations

import dataclasses
from typing import Optional
from uuid import uuid4

from saltbor.knowledge.graph.node import KnowledgeNode, NodeType, ValidationStatus
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.knowledge.layers.hypothesis_graph import Hypothesis, HypothesisDiscoveryGraph
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


@dataclasses.dataclass
class AnalogicalMapping:
    """Structural alignment between source domain and target domain."""

    source_concept_id: str
    target_concept_id: str
    transferred_predicate: str           # e.g., 'preserves', 'hardens', 'strengthens'
    shared_properties: list[str]
    structural_similarity_score: float   # [0.0, 1.0]
    generated_hypothesis: Hypothesis


class AnalogicalReasoningEngine:
    """Transfers causal/functional schemas across domains."""

    def perform_analogical_transfer(
        self,
        graph: IndividualKnowledgeGraph,
        hypothesis_graph: HypothesisDiscoveryGraph,
        source_concept_id: str,
        target_concept_id: str,
        tick: int = 0,
    ) -> Optional[AnalogicalMapping]:
        """Map functional properties from source to target domain, forming an analogical hypothesis."""
        if not graph.knows_concept(source_concept_id) or not graph.knows_concept(target_concept_id):
            return None

        source_node = graph.get_concept(source_concept_id)
        target_node = graph.get_concept(target_concept_id)
        if not source_node or not target_node:
            return None

        # Compare shared properties
        src_props = set(source_node.properties.keys())
        tgt_props = set(target_node.properties.keys())
        shared = list(src_props.intersection(tgt_props))

        # Structural similarity metric
        sim_score = len(shared) / max(1, len(src_props.union(tgt_props)))
        if sim_score < 0.2:
            sim_score = 0.35  # baseline abstract resemblance

        # Find key outgoing relationships from source (e.g., source USED_FOR or CAUSES)
        source_rels = graph._out_edges.get(source_concept_id, [])
        if not source_rels:
            predicate = "preserves_or_enhances"
            effect_label = "improved_longevity"
        else:
            primary_rel = source_rels[0]
            predicate = str(primary_rel.rel_type.value if isinstance(primary_rel.rel_type, RelationshipType) else primary_rel.rel_type)
            effect_label = primary_rel.target_id

        # Formulate hypothesis (NOT a guaranteed truth!)
        hyp_title = f"Analogical application of {source_node.label} mechanism to {target_node.label}"
        statement = (
            f"Because {source_node.label} successfully {predicate} {effect_label}, "
            f"applying a similar technique to {target_node.label} will yield equivalent benefits."
        )

        hyp = hypothesis_graph.propose_hypothesis(
            creator_uid=graph.human_uid,
            title=hyp_title,
            target_phenomenon=f"Enhancement of {target_node.label}",
            statement=statement,
            assumptions=[f"{source_node.label} and {target_node.label} share underlying properties: {', '.join(shared) if shared else 'organic/physical'}."],
            prior_confidence=max(0.2, min(0.65, sim_score * 0.7)),
            tick=tick,
        )

        # Register analogical relationship in agent's graph
        sim_rel = KnowledgeRelationship(
            rel_id=f"sim_{source_concept_id}_{target_concept_id}_{tick}",
            source_id=source_concept_id,
            target_id=target_concept_id,
            rel_type=RelationshipType.SIMILAR_TO,
            weight=sim_score,
            confidence=0.7,
            provenance_source="analogical_reasoning",
            created_tick=tick,
            metadata={"shared_properties": shared},
        )
        graph.learn_relationship(
            rel=sim_rel,
            confidence=0.7,
            source_pathway="problem_solving",
            tick=tick,
            evidence=f"Identified shared traits: {shared}",
        )

        return AnalogicalMapping(
            source_concept_id=source_concept_id,
            target_concept_id=target_concept_id,
            transferred_predicate=predicate,
            shared_properties=shared,
            structural_similarity_score=sim_score,
            generated_hypothesis=hyp,
        )
