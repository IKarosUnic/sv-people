"""Knowledge Observability and Diagnostic Inspector for Saltbor Phase 0.6.

Exposes comprehensive individual knowledge profiles, collective knowledge profiles,
discovery profiles, and transparent provenance explanations.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional

from saltbor.knowledge.graph.node import ValidationStatus
from saltbor.knowledge.layers.collective_graph import CollectiveKnowledgeGraph
from saltbor.knowledge.layers.hypothesis_graph import HypothesisDiscoveryGraph
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.knowledge.layers.procedural_graph import ProceduralKnowledgeGraph
from saltbor.knowledge.transmission.engine import KnowledgeTransmissionEngine


@dataclasses.dataclass
class IndividualKnowledgeProfile:
    """Detailed knowledge diagnostics for a single agent."""

    human_uid: str
    known_concepts_count: int
    known_relationships_count: int
    mean_confidence: float
    concepts_summary: list[dict[str, Any]]
    misconceptions: list[str]
    forgotten_items_count: int
    hypotheses_held: list[str]
    teaching_events_count: int
    learning_events_count: int


@dataclasses.dataclass
class CollectiveKnowledgeProfile:
    """Society-wide or institution-level knowledge diagnostics."""

    total_institutional_items: int
    group_repositories_summary: dict[str, int]
    endangered_knowledge_items: list[str]
    dominant_documentation_types: dict[str, int]


@dataclasses.dataclass
class DiscoveryProfile:
    """Global diagnostics of scientific and technological innovations."""

    total_hypotheses: int
    proposed_count: int
    supported_count: int
    replicated_count: int
    disputed_count: int
    refuted_count: int
    total_experiments_conducted: int
    experimental_success_rate: float


class KnowledgeObservability:
    """Diagnostic inspector for knowledge state at individual, institutional, and societal scales."""

    @staticmethod
    def inspect_individual(
        graph: IndividualKnowledgeGraph,
        transmission_engine: Optional[KnowledgeTransmissionEngine] = None,
    ) -> IndividualKnowledgeProfile:
        """Generate individual knowledge profile."""
        known_nodes = graph.all_known_nodes()
        concepts_summary = []
        confidences = []
        misconceptions = []

        for n in known_nodes:
            claim = graph.get_claim(n.node_id)
            if claim:
                confidences.append(claim.confidence)
                if claim.is_misconception:
                    misconceptions.append(n.node_id)
                concepts_summary.append({
                    "node_id": n.node_id,
                    "label": n.label,
                    "confidence": claim.confidence,
                    "source": claim.source_pathway,
                    "verified_times": claim.verification_count,
                })

        mean_conf = sum(confidences) / max(1, len(confidences))
        forgotten = sum(1 for c in graph._node_claims.values() if c.is_forgotten) + \
                    sum(1 for c in graph._rel_claims.values() if c.is_forgotten)

        teach_cnt = 0
        learn_cnt = 0
        if transmission_engine:
            teach_cnt = sum(1 for tx in transmission_engine.history if tx.immediate_transmitter_uid == graph.human_uid)
            learn_cnt = sum(1 for tx in transmission_engine.history if tx.recipient_uid == graph.human_uid)

        return IndividualKnowledgeProfile(
            human_uid=graph.human_uid,
            known_concepts_count=len(known_nodes),
            known_relationships_count=len([r for r, c in graph._rel_claims.items() if not c.is_forgotten]),
            mean_confidence=mean_conf,
            concepts_summary=concepts_summary,
            misconceptions=misconceptions,
            forgotten_items_count=forgotten,
            hypotheses_held=[nid for nid in graph.all_known_node_ids() if "hyp_" in nid],
            teaching_events_count=teach_cnt,
            learning_events_count=learn_cnt,
        )

    @staticmethod
    def inspect_collective(
        collective_graph: CollectiveKnowledgeGraph,
        active_population_uids: set[str],
    ) -> CollectiveKnowledgeProfile:
        """Generate collective knowledge profile."""
        endangered = collective_graph.check_endangered_knowledge(active_population_uids)
        group_summary = {
            gid: len(repo) for gid, repo in collective_graph._group_repositories.items()
        }
        total = sum(group_summary.values())

        doc_types: dict[str, int] = {}
        for repo in collective_graph._group_repositories.values():
            for item in repo.values():
                doc_types[item.documentation_type] = doc_types.get(item.documentation_type, 0) + 1

        return CollectiveKnowledgeProfile(
            total_institutional_items=total,
            group_repositories_summary=group_summary,
            endangered_knowledge_items=[it.item_id for it in endangered],
            dominant_documentation_types=doc_types,
        )

    @staticmethod
    def inspect_discoveries(
        hypothesis_graph: HypothesisDiscoveryGraph,
        experiments_log: Optional[list[Any]] = None,
    ) -> DiscoveryProfile:
        """Generate scientific and technological innovation profile."""
        hyps = list(hypothesis_graph._hypotheses.values())
        proposed = sum(1 for h in hyps if h.status in (ValidationStatus.PROPOSED, ValidationStatus.UNTESTED))
        supported = sum(1 for h in hyps if h.status == ValidationStatus.SUPPORTED)
        replicated = sum(1 for h in hyps if h.status == ValidationStatus.REPLICATED)
        disputed = sum(1 for h in hyps if h.status == ValidationStatus.DISPUTED)
        refuted = sum(1 for h in hyps if h.status == ValidationStatus.REFUTED)

        exp_count = len(experiments_log) if experiments_log else 0
        success_count = sum(1 for e in experiments_log if getattr(e, "supports_hypothesis", False)) if experiments_log else 0
        rate = success_count / max(1, exp_count)

        return DiscoveryProfile(
            total_hypotheses=len(hyps),
            proposed_count=proposed,
            supported_count=supported,
            replicated_count=replicated,
            disputed_count=disputed,
            refuted_count=refuted,
            total_experiments_conducted=exp_count,
            experimental_success_rate=rate,
        )
