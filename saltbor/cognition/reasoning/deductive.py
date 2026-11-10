"""Deductive Reasoning Engine for Saltbor Phase 0.7 (Section 2.1).

Derives logically valid conclusions from known premises and formal inference rules.
Ensures full traceability from premises through inference steps to derived conclusions,
propagating epistemic uncertainty.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Callable, Optional
from uuid import uuid4

from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.knowledge.graph.node import KnowledgeNode, NodeType
from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


@dataclasses.dataclass
class Premise:
    """An antecedent proposition with an epistemic confidence."""

    statement: str
    concept_or_rel_id: str
    confidence: float = 1.0
    source: str = "known_knowledge"


@dataclasses.dataclass
class DeductionTrace:
    """Complete, transparent computational trace of a deductive derivation."""

    deduction_id: str
    rule_name: str
    premises: list[Premise]
    conclusion_statement: str
    conclusion_id: str
    confidence: float
    is_negation: bool = False
    alternative_suggestion: Optional[str] = None
    applied_tick: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "deduction_id": self.deduction_id,
            "rule_name": self.rule_name,
            "premises": [{"statement": p.statement, "conf": round(p.confidence, 3)} for p in self.premises],
            "conclusion": self.conclusion_statement,
            "confidence": round(self.confidence, 3),
            "alternative_suggestion": self.alternative_suggestion,
        }


@dataclasses.dataclass
class LogicalRule:
    """A formal deductive rule: IF premises THEN conclusion."""

    rule_id: str
    name: str
    description: str
    evaluator: Callable[[IndividualKnowledgeGraph, dict[str, Any]], Optional[DeductionTrace]]
    rule_validity: float = 1.0


class DeductiveReasoningEngine:
    """Executes deductive inference with full audit trails."""

    def __init__(self) -> None:
        self._rules: list[LogicalRule] = []
        self._setup_built_in_rules()

    def register_rule(self, rule: LogicalRule) -> None:
        self._rules.append(rule)

    def _setup_built_in_rules(self) -> None:
        """Register fundamental domain rules."""

        # Rule 1: Production Precondition Failure (Modus Tollens)
        # IF Product requires Material AND Material is NOT available THEN Product cannot be crafted
        def _rule_production_precondition(
            graph: IndividualKnowledgeGraph,
            context: dict[str, Any],
        ) -> Optional[DeductionTrace]:
            product_id = context.get("target_product")
            required_mat = context.get("required_material")
            inventory = context.get("inventory", {})

            if not product_id or not required_mat:
                return None

            # Premise 1: Agent knows product requires material
            # Check if agent knows product and material
            if not graph.knows_concept(product_id) or not graph.knows_concept(required_mat):
                return None

            claim_prod = graph.get_claim(product_id)
            claim_mat = graph.get_claim(required_mat)
            conf_prod = claim_prod.confidence if claim_prod else 0.5
            conf_mat = claim_mat.confidence if claim_mat else 0.5

            # Premise 2: Material is unavailable in inventory
            available_qty = inventory.get(required_mat, 0.0)
            required_qty = context.get("required_quantity", 1.0)

            if available_qty < required_qty:
                premises = [
                    Premise(
                        statement=f"{product_id} requires {required_qty} units of {required_mat}",
                        concept_or_rel_id=product_id,
                        confidence=conf_prod,
                    ),
                    Premise(
                        statement=f"Current inventory has {available_qty} units of {required_mat} (needs {required_qty})",
                        concept_or_rel_id=required_mat,
                        confidence=conf_mat,
                    ),
                ]
                conclusion_conf = min(conf_prod, conf_mat) * 0.95
                return DeductionTrace(
                    deduction_id=f"deduct_{uuid4().hex[:8]}",
                    rule_name="Modus Tollens: Production Precondition Unsatisfied",
                    premises=premises,
                    conclusion_statement=f"Cannot craft or produce {product_id} currently due to absence of {required_mat}",
                    conclusion_id=f"cannot_produce_{product_id}",
                    confidence=conclusion_conf,
                    is_negation=True,
                    alternative_suggestion=f"Acquire {required_mat} via market exchange, harvesting, or seek alternative recipe",
                    applied_tick=context.get("tick", 0),
                )
            return None

        self.register_rule(
            LogicalRule(
                rule_id="rule_prod_precondition",
                name="Production Precondition Unsatisfied",
                description="Concludes inability to produce when essential materials are missing",
                evaluator=_rule_production_precondition,
            )
        )

        # Rule 2: Transitive Requirement Deduction
        # IF A REQUIRES B AND B REQUIRES C THEN A INDIRECTLY REQUIRES C
        def _rule_transitive_requirement(
            graph: IndividualKnowledgeGraph,
            context: dict[str, Any],
        ) -> Optional[DeductionTrace]:
            target_id = context.get("target_concept")
            if not target_id or not graph.knows_concept(target_id):
                return None

            # Look for 2-hop requirements
            out_edges_1 = graph._out_edges.get(target_id, [])
            for r1 in out_edges_1:
                r1_type = str(r1.rel_type.value if hasattr(r1.rel_type, "value") else r1.rel_type)
                if r1_type in ("REQUIRES", "DEPENDS_ON"):
                    mid_id = r1.target_id
                    claim1 = graph.get_claim(r1.rel_id)
                    conf1 = claim1.confidence if claim1 else 0.5

                    out_edges_2 = graph._out_edges.get(mid_id, [])
                    for r2 in out_edges_2:
                        r2_type = str(r2.rel_type.value if hasattr(r2.rel_type, "value") else r2.rel_type)
                        if r2_type in ("REQUIRES", "DEPENDS_ON"):
                            end_id = r2.target_id
                            claim2 = graph.get_claim(r2.rel_id)
                            conf2 = claim2.confidence if claim2 else 0.5

                            premises = [
                                Premise(f"{target_id} requires {mid_id}", r1.rel_id, conf1),
                                Premise(f"{mid_id} requires {end_id}", r2.rel_id, conf2),
                            ]
                            return DeductionTrace(
                                deduction_id=f"deduct_{uuid4().hex[:8]}",
                                rule_name="Hypothetical Syllogism: Transitive Requirement",
                                premises=premises,
                                conclusion_statement=f"{target_id} transitively depends upon acquiring {end_id}",
                                conclusion_id=f"transitive_req_{target_id}_{end_id}",
                                confidence=min(conf1, conf2) * 0.90,
                                alternative_suggestion=f"Ensure upstream supply of {end_id} before pursuing {target_id}",
                                applied_tick=context.get("tick", 0),
                            )
            return None

        self.register_rule(
            LogicalRule(
                rule_id="rule_transitive_requirement",
                name="Transitive Requirement Syllogism",
                description="Derives upstream prerequisites through multi-hop dependency chains",
                evaluator=_rule_transitive_requirement,
            )
        )

    def deduce(
        self,
        graph: IndividualKnowledgeGraph,
        context: dict[str, Any],
        epistemic: Optional[EpistemicInterface] = None,
    ) -> list[DeductionTrace]:
        """Evaluate all deductive rules against knowledge and context.

        Returns list of structured deduction traces.
        """
        deductions: list[DeductionTrace] = []
        tick = context.get("tick", 0)

        for rule in self._rules:
            trace = rule.evaluator(graph, context)
            if trace is not None:
                deductions.append(trace)
                # Register derived belief in epistemic interface if provided
                if epistemic:
                    belief = EpistemicBelief(
                        belief_id=trace.conclusion_id,
                        subject=context.get("target_product", context.get("target_concept", "deduction")),
                        predicate="deduced_constraint",
                        object_val=trace.conclusion_statement,
                        belief_type=BeliefType.INFERENCE,
                        confidence=trace.confidence,
                        source_type="deductive_reasoning",
                        created_tick=tick,
                        updated_tick=tick,
                        evidence_items=[p.statement for p in trace.premises],
                    )
                    epistemic.register_belief(belief)

        return deductions
