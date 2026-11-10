"""Causal Reasoning Engine for Saltbor Phase 0.6.

Traces causal pathways, evaluates upstream drivers and downstream impacts,
distinguishes correlation from genuine causation, and supports fallible causal beliefs.
"""

from __future__ import annotations

import dataclasses
from typing import Optional

from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


@dataclasses.dataclass
class CausalStep:
    """An individual link in a causal chain."""

    cause_node_id: str
    effect_node_id: str
    rel_id: str
    confidence: float
    strength: float                     # [0.0, 1.0] estimated impact strength
    is_correlation_only: bool = False   # True if spurious or unproven correlation


@dataclasses.dataclass
class CausalChain:
    """A multi-hop causal sequence explaining a phenomenon."""

    origin_cause_id: str
    terminal_effect_id: str
    steps: list[CausalStep]
    aggregate_confidence: float
    aggregate_strength: float

    @property
    def hop_count(self) -> int:
        return len(self.steps)


class CausalReasoningEngine:
    """Evaluates causes and downstream effects using personal beliefs."""

    def trace_downstream_impacts(
        self,
        graph: IndividualKnowledgeGraph,
        root_cause_id: str,
        max_hops: int = 4,
        min_confidence: float = 0.25,
    ) -> list[CausalChain]:
        """Trace all downstream consequences emanating from root_cause_id."""
        if not graph.knows_concept(root_cause_id):
            return []

        causal_rel_types = {
            RelationshipType.CAUSES.value,
            RelationshipType.INFLUENCES.value,
            RelationshipType.PRODUCES.value,
            RelationshipType.ENABLES.value,
            RelationshipType.INHIBITS.value,
        }

        chains: list[CausalChain] = []

        # DFS traversal
        def _dfs(curr_id: str, current_steps: list[CausalStep], visited: set[str]) -> None:
            if len(current_steps) >= max_hops:
                return

            for rel in graph._out_edges.get(curr_id, []):
                r_type_str = str(rel.rel_type.value if isinstance(rel.rel_type, RelationshipType) else rel.rel_type)
                if r_type_str not in causal_rel_types:
                    continue

                claim = graph.get_claim(rel.rel_id)
                if not claim or claim.is_forgotten or claim.confidence < min_confidence:
                    continue

                target_id = rel.target_id
                if target_id in visited:
                    continue  # prevent cycle

                is_corr = rel.metadata.get("is_correlation_only", False)
                step = CausalStep(
                    cause_node_id=curr_id,
                    effect_node_id=target_id,
                    rel_id=rel.rel_id,
                    confidence=claim.confidence,
                    strength=rel.weight,
                    is_correlation_only=is_corr,
                )
                new_steps = current_steps + [step]

                # Calculate cumulative confidence and strength
                agg_conf = 1.0
                agg_str = 1.0
                for s in new_steps:
                    agg_conf *= s.confidence
                    agg_str *= s.strength

                chains.append(
                    CausalChain(
                        origin_cause_id=root_cause_id,
                        terminal_effect_id=target_id,
                        steps=new_steps,
                        aggregate_confidence=agg_conf,
                        aggregate_strength=agg_str,
                    )
                )

                visited.add(target_id)
                _dfs(target_id, new_steps, visited)
                visited.remove(target_id)

        _dfs(root_cause_id, [], {root_cause_id})
        # Sort by aggregate confidence descending
        chains.sort(key=lambda c: c.aggregate_confidence, reverse=True)
        return chains

    def formulate_causal_belief(
        self,
        graph: IndividualKnowledgeGraph,
        cause_id: str,
        effect_id: str,
        confidence: float = 0.6,
        is_spurious_correlation: bool = False,
        tick: int = 0,
    ) -> KnowledgeRelationship:
        """Allow an agent to formulate a personal causal belief (which may be fallible)."""
        rel_id = f"causal_{cause_id}_{effect_id}_{tick}"
        rel = KnowledgeRelationship(
            rel_id=rel_id,
            source_id=cause_id,
            target_id=effect_id,
            rel_type=RelationshipType.CAUSES,
            weight=0.8,
            confidence=confidence,
            provenance_source="subjective_causal_inference",
            created_tick=tick,
            metadata={"is_correlation_only": is_spurious_correlation},
        )
        graph.learn_relationship(
            rel=rel,
            confidence=confidence,
            source_pathway="problem_solving",
            tick=tick,
            is_misconception=is_spurious_correlation,
            evidence="Observed co-occurrence and inferred causal dependency",
        )
        return rel
