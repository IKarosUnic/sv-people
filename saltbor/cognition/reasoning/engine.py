"""Unified Advanced Reasoning Engine for Saltbor Phase 0.7.

Coordinates the 7 specialized reasoning modes:
1. Deductive reasoning (Modus Ponens/Tollens, syllogisms, traceable premise-conclusion chains)
2. Inductive reasoning (Pattern extraction, frequency tracking, uncertainty bounds)
3. Abductive reasoning (Inference to best explanation, competing hypotheses, discriminant tests)
4. Causal reasoning (Correlation vs. causality, confounder identification, multi-hop impacts)
5. Analogical reasoning (Cross-domain structural transfer with contextual boundary awareness)
6. Counterfactual reasoning (Retrospective what-if simulation segregated from factual history)
7. Hypothetical reasoning (Prospective scenario projection with post-facto verification)
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Optional

from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.cognition.reasoning.abductive import AbductiveReasoningEngine
from saltbor.cognition.reasoning.analogical import AdvancedAnalogicalReasoningEngine
from saltbor.cognition.reasoning.causal import AdvancedCausalReasoningEngine
from saltbor.cognition.reasoning.counterfactual import CounterfactualReasoningEngine
from saltbor.cognition.reasoning.deductive import DeductiveReasoningEngine
from saltbor.cognition.reasoning.hypothetical import HypotheticalReasoningEngine
from saltbor.cognition.reasoning.inductive import InductiveReasoningEngine
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ReasoningBudget:
    """Computational boundaries preventing combinatorial explosions."""

    max_deduction_rules: int = 20
    max_causal_hops: int = 4
    search_budget_nodes: int = 150
    confidence_threshold: float = 0.20
    max_candidate_hypotheses: int = 6


class AdvancedReasoningEngine:
    """Master reasoning orchestrator uniting all 7 cognitive reasoning modalities."""

    def __init__(self, budget: Optional[ReasoningBudget] = None) -> None:
        self.budget = budget or ReasoningBudget()
        self.deductive = DeductiveReasoningEngine()
        self.inductive = InductiveReasoningEngine()
        self.abductive = AbductiveReasoningEngine()
        self.causal = AdvancedCausalReasoningEngine()
        self.analogical = AdvancedAnalogicalReasoningEngine()
        self.counterfactual = CounterfactualReasoningEngine()
        self.hypothetical = HypotheticalReasoningEngine()

    def run_deduction(
        self,
        graph: IndividualKnowledgeGraph,
        context: dict[str, Any],
        epistemic: Optional[EpistemicInterface] = None,
    ) -> list[Any]:
        return self.deductive.deduce(graph=graph, context=context, epistemic=epistemic)

    def record_induction(
        self,
        condition: str,
        outcome: str,
        value: float = 1.0,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> Any:
        return self.inductive.record_observation(
            condition=condition,
            outcome=outcome,
            value=value,
            tick=tick,
            epistemic=epistemic,
        )

    def explain_abductively(
        self,
        anomaly_key: str,
        context: Optional[dict[str, Any]] = None,
        graph: Optional[IndividualKnowledgeGraph] = None,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> list[Any]:
        return self.abductive.generate_explanations(
            anomaly_key=anomaly_key,
            context=context,
            graph=graph,
            tick=tick,
            epistemic=epistemic,
        )

    def trace_causal_chain(
        self,
        root_cause_id: str,
        max_hops: Optional[int] = None,
    ) -> list[Any]:
        hops = max_hops or self.budget.max_causal_hops
        return self.causal.trace_impacts(root_cause_id=root_cause_id, max_hops=hops)

    def transfer_analogically(
        self,
        source_domain_id: str,
        target_domain_id: str,
        graph: Optional[IndividualKnowledgeGraph] = None,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> Optional[Any]:
        return self.analogical.transfer_knowledge(
            source_domain_id=source_domain_id,
            target_domain_id=target_domain_id,
            graph=graph,
            tick=tick,
            epistemic=epistemic,
        )

    def simulate_counterfactual(
        self,
        event_description: str,
        actual_decision: str,
        actual_outcome: str,
        actual_utility: float,
        counterfactual_alternative: str,
        domain_model: Optional[dict[str, Any]] = None,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> Any:
        return self.counterfactual.evaluate_counterfactual(
            event_description=event_description,
            actual_decision=actual_decision,
            actual_outcome=actual_outcome,
            actual_utility=actual_utility,
            counterfactual_alternative=counterfactual_alternative,
            domain_model=domain_model,
            tick=tick,
            epistemic=epistemic,
        )

    def formulate_hypothesis(
        self,
        condition_action: str,
        predicted_consequence: str,
        assumptions: Optional[list[str]] = None,
        confidence: float = 0.50,
        expected_utility_delta: float = 0.0,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> Any:
        return self.hypothetical.formulate_scenario(
            condition_action=condition_action,
            predicted_consequence=predicted_consequence,
            assumptions=assumptions,
            confidence=confidence,
            expected_utility_delta=expected_utility_delta,
            tick=tick,
            epistemic=epistemic,
        )
