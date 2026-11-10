"""Rule-based inference engine with explicit precondition validation."""

from __future__ import annotations

import dataclasses
from typing import Any, Callable, Optional
from uuid import uuid4

from saltbor.knowledge.graph.node import KnowledgeNode, NodeType
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


@dataclasses.dataclass
class InferenceRule:
    """A logical rule with required antecedent conditions and inferred consequent."""

    rule_id: str
    name: str
    antecedent_concept_ids: list[str]       # Required concepts the agent must know
    required_relationships: list[tuple[str, RelationshipType | str, str]] # (src, rel_type, tgt)
    consequent_node_generator: Optional[Callable[[IndividualKnowledgeGraph], KnowledgeNode]] = None
    consequent_rel_generator: Optional[Callable[[IndividualKnowledgeGraph], KnowledgeRelationship]] = None
    confidence_factor: float = 0.85
    explanation: str = ""


class RuleBasedInferenceEngine:
    """Executes forward-chaining deduction over an individual's known epistemic graph."""

    def __init__(self) -> None:
        self._rules: list[InferenceRule] = []

    def register_rule(self, rule: InferenceRule) -> None:
        self._rules.append(rule)

    def infer(
        self,
        graph: IndividualKnowledgeGraph,
        max_inferences: int = 10,
        tick: int = 0,
    ) -> list[tuple[str, str]]:
        """Evaluate registered rules against agent's knowledge.

        Returns list of (inferred_item_id, explanation).
        """
        inferred: list[tuple[str, str]] = []
        count = 0

        for rule in self._rules:
            if count >= max_inferences:
                break

            # Check concept preconditions
            all_concepts_known = True
            for cid in rule.antecedent_concept_ids:
                if not graph.knows_concept(cid, min_confidence=0.3):
                    all_concepts_known = False
                    break
            if not all_concepts_known:
                continue

            # Check relationship preconditions
            all_rels_known = True
            for src, r_type, tgt in rule.required_relationships:
                r_type_str = str(r_type.value if isinstance(r_type, RelationshipType) else r_type)
                # Check if graph has relationship between src and tgt
                matching = [
                    r for r in graph._out_edges.get(src, [])
                    if r.target_id == tgt and str(r.rel_type.value if isinstance(r.rel_type, RelationshipType) else r.rel_type) == r_type_str
                ]
                if not matching or not any(graph.get_claim(m.rel_id) and graph.get_claim(m.rel_id).confidence >= 0.3 for m in matching):
                    all_rels_known = False
                    break
            if not all_rels_known:
                continue

            # Antecedents satisfied: generate conclusions
            if rule.consequent_node_generator:
                node = rule.consequent_node_generator(graph)
                if not graph.has_node if hasattr(graph, 'has_node') else not graph.knows_concept(node.node_id):
                    graph.register_local_node(node, confidence=rule.confidence_factor, tick=tick)
                    inferred.append((node.node_id, f"Inferred concept by rule '{rule.name}': {rule.explanation}"))
                    count += 1

            if rule.consequent_rel_generator:
                rel = rule.consequent_rel_generator(graph)
                if rel.rel_id not in graph._rel_claims:
                    graph.learn_relationship(
                        rel=rel,
                        confidence=rule.confidence_factor,
                        source_pathway="rule_inference",
                        tick=tick,
                        evidence=f"Deduced via rule {rule.name}",
                    )
                    inferred.append((rel.rel_id, f"Inferred relationship by rule '{rule.name}'"))
                    count += 1

        return inferred
