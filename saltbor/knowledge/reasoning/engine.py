"""Unified Inference and Open-Ended Reasoning Engine for Saltbor Phase 0.6.

Integrates rule-based deduction, causal tracing, compositional synthesis,
analogical mapping, and hypothesis generation under bounded computational budgets.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Optional

from saltbor.knowledge.layers.hypothesis_graph import Hypothesis, HypothesisDiscoveryGraph
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph
from saltbor.knowledge.layers.procedural_graph import ProceduralKnowledgeGraph
from saltbor.knowledge.reasoning.analogical import AnalogicalMapping, AnalogicalReasoningEngine
from saltbor.knowledge.reasoning.causal import CausalChain, CausalReasoningEngine
from saltbor.knowledge.reasoning.compositional import CompositionProposal, CompositionalReasoningEngine
from saltbor.knowledge.reasoning.hypothesis_gen import HypothesisGenerationEngine, UnexplainedPhenomenon
from saltbor.knowledge.reasoning.rules import RuleBasedInferenceEngine

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ReasoningBudget:
    """Computational boundaries preventing unbounded search or combinatorial explosions."""

    max_inference_depth: int = 4
    search_budget_nodes: int = 150
    confidence_threshold: float = 0.25
    max_candidate_hypotheses: int = 5
    cycle_detection_limit: int = 50


class InferenceEngine:
    """Central orchestrator for cognitive inference and problem solving."""

    def __init__(self, budget: Optional[ReasoningBudget] = None) -> None:
        self.budget = budget or ReasoningBudget()
        self.rules = RuleBasedInferenceEngine()
        self.causal = CausalReasoningEngine()
        self.compositional = CompositionalReasoningEngine()
        self.analogical = AnalogicalReasoningEngine()
        self.hypothesis_gen = HypothesisGenerationEngine()

    def run_bounded_inference(
        self,
        graph: IndividualKnowledgeGraph,
        hypothesis_graph: Optional[HypothesisDiscoveryGraph] = None,
        tick: int = 0,
    ) -> dict[str, Any]:
        """Perform a cycle of bounded deductive and causal inference."""
        # 1. Rule-based forward deduction
        rule_inferences = self.rules.infer(
            graph=graph,
            max_inferences=self.budget.max_candidate_hypotheses,
            tick=tick,
        )

        # 2. Check for contradictions in belief set
        contradictions = self.detect_contradictions(graph)

        return {
            "rule_inferences": rule_inferences,
            "contradictions_detected": contradictions,
        }

    def detect_contradictions(self, graph: IndividualKnowledgeGraph) -> list[tuple[str, str, str]]:
        """Identify pairs of beliefs that contradict each other.

        Returns list of (concept_a, concept_b, reason).
        """
        contradictions: list[tuple[str, str, str]] = []
        for rel in graph._local_relationships.values():
            if str(rel.rel_type.value if hasattr(rel.rel_type, 'value') else rel.rel_type) == "CONTRADICTS":
                claim = graph.get_claim(rel.rel_id)
                if claim and not claim.is_forgotten and claim.confidence >= self.budget.confidence_threshold:
                    contradictions.append(
                        (rel.source_id, rel.target_id, f"Belief '{rel.source_id}' asserts contradiction with '{rel.target_id}'")
                    )
        return contradictions
