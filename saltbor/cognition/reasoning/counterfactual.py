"""Counterfactual Reasoning Engine for Saltbor Phase 0.7 (Section 2.6).

Evaluates retrospective 'what if' alternative historical scenarios
("What would have happened if I had set a different price / accepted the proposal / asked for help?"),
while strictly segregating counterfactual simulations from factual episodic history.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional
from uuid import uuid4

from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.epistemic.interface import EpistemicInterface


@dataclasses.dataclass
class CounterfactualEvaluation:
    """An analytical evaluation comparing real factual history with a simulated alternative."""

    evaluation_id: str
    target_event_description: str
    actual_decision: str
    actual_outcome: str
    actual_utility: float
    counterfactual_alternative: str
    simulated_outcome: str
    simulated_utility: float
    utility_delta: float                # simulated - actual (>0 = regret / could have done better; <0 = relief / made right choice)
    emotional_impact: str               # 'regret', 'relief', 'indifference'
    learning_insight: str
    is_counterfactual_flag: bool = True # Strictly flagged to prevent factual episodic pollution
    created_tick: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "event": self.target_event_description,
            "actual_decision": self.actual_decision,
            "actual_outcome": self.actual_outcome,
            "counterfactual_alternative": self.counterfactual_alternative,
            "simulated_outcome": self.simulated_outcome,
            "actual_utility": round(self.actual_utility, 3),
            "simulated_utility": round(self.simulated_utility, 3),
            "utility_delta": round(self.utility_delta, 3),
            "emotional_impact": self.emotional_impact,
            "learning_insight": self.learning_insight,
            "is_counterfactual": True,
        }


class CounterfactualReasoningEngine:
    """Simulates counterfactual branches of past decision points."""

    def evaluate_counterfactual(
        self,
        event_description: str,
        actual_decision: str,
        actual_outcome: str,
        actual_utility: float,
        counterfactual_alternative: str,
        domain_model: Optional[dict[str, Any]] = None,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> CounterfactualEvaluation:
        """Simulate what would have happened under the counterfactual choice."""
        domain_model = domain_model or {}

        # 1. Determine simulated outcome using domain causal model
        simulated_outcome = "Alternative branch simulated without significant state divergence."
        simulated_utility = actual_utility

        if "price" in counterfactual_alternative.lower():
            price_change = domain_model.get("price_change_factor", 1.0)
            elasticity = domain_model.get("demand_elasticity", -1.2)
            # Demand change = elasticity * price_change
            if price_change > 1.0:
                simulated_outcome = f"Higher price (+{(price_change - 1.0)*100:.0f}%) would have reduced units sold but increased margin per unit"
                simulated_utility = actual_utility * (1.0 + (price_change - 1.0) * (1.0 + elasticity))
            else:
                simulated_outcome = f"Lower price ({(price_change - 1.0)*100:.0f}%) would have increased sales volume but compressed margins"
                simulated_utility = actual_utility * (1.0 + (price_change - 1.0) * (1.0 + elasticity))

        elif "help" in counterfactual_alternative.lower() or "collaborate" in counterfactual_alternative.lower():
            help_cost = domain_model.get("help_cost", 10.0)
            help_success_boost = domain_model.get("help_success_boost", 0.4)
            simulated_outcome = "Requesting assistance would have reduced personal burden and ensured task completion, at the cost of shared credit"
            simulated_utility = actual_utility + (help_success_boost * 30.0) - help_cost

        elif "accept_proposal" in counterfactual_alternative.lower():
            proposal_benefit = domain_model.get("proposal_benefit", 25.0)
            proposal_risk = domain_model.get("proposal_risk", 10.0)
            simulated_outcome = "Accepting proposal would have injected capital and labor, but introduced contractual obligations and shared governance"
            simulated_utility = actual_utility + proposal_benefit - proposal_risk

        else:
            simulated_outcome = f"Under '{counterfactual_alternative}', alternative consequences would have unfolded with moderate variance"
            simulated_utility = actual_utility + domain_model.get("hypothetical_utility_delta", 5.0)

        delta = simulated_utility - actual_utility
        if delta > 3.0:
            emotional_impact = "regret"
            lesson = f"In future similar situations, prefer '{counterfactual_alternative}' to capture higher utility (+{delta:.1f})"
        elif delta < -3.0:
            emotional_impact = "relief"
            lesson = f"Actual decision '{actual_decision}' was superior: avoiding '{counterfactual_alternative}' averted an estimated loss of {-delta:.1f}"
        else:
            emotional_impact = "indifference"
            lesson = "Alternative action would have produced roughly equivalent payoff; decision was robust"

        res = CounterfactualEvaluation(
            evaluation_id=f"counterfact_{uuid4().hex[:8]}",
            target_event_description=event_description,
            actual_decision=actual_decision,
            actual_outcome=actual_outcome,
            actual_utility=actual_utility,
            counterfactual_alternative=counterfactual_alternative,
            simulated_outcome=simulated_outcome,
            simulated_utility=simulated_utility,
            utility_delta=delta,
            emotional_impact=emotional_impact,
            learning_insight=lesson,
            is_counterfactual_flag=True,
            created_tick=tick,
        )

        if epistemic:
            # Store explicitly as a counterfactual reflection, NOT as factual ground truth
            belief = EpistemicBelief(
                belief_id=res.evaluation_id,
                subject=actual_decision,
                predicate="counterfactual_alternative",
                object_val=counterfactual_alternative,
                belief_type=BeliefType.HYPOTHESIS,
                confidence=0.75,
                source_type="counterfactual_reasoning",
                created_tick=tick,
                updated_tick=tick,
                evidence_items=[f"Simulation delta: {delta:+.2f}; Impact: {emotional_impact}; Lesson: {lesson}"],
                context_tags=["counterfactual", "hypothetical_branch"],
            )
            epistemic.register_belief(belief)

        return res
