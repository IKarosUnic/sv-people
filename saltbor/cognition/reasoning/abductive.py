"""Abductive Reasoning Engine for Saltbor Phase 0.7 (Section 2.3).

Generates multiple plausible explanations for surprising or anomalous observations,
ranks them by prior plausibility, explanatory coverage, and parsimony, and
formulates targeted discriminant tests to gather evidence and distinguish among them.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional
from uuid import uuid4

from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


@dataclasses.dataclass
class ExplanationHypothesis:
    """A candidate explanatory hypothesis generated via abduction."""

    hypothesis_id: str
    target_observation: str              # The surprising anomaly to explain
    candidate_cause: str                # Proposed upstream root cause
    explanation_statement: str          # Mechanistic story
    prior_plausibility: float           # Subjective initial likelihood in [0.0, 1.0]
    explanatory_coverage: float         # How completely it explains the symptoms
    parsimony_score: float              # Simplicity / Occam penalty (higher = fewer unproven assumptions)
    discriminant_test: str              # Specific inquiry or test to verify/falsify this explanation
    supporting_evidence: list[str] = dataclasses.field(default_factory=list)
    contradicting_evidence: list[str] = dataclasses.field(default_factory=list)
    created_tick: int = 0

    @property
    def composite_score(self) -> float:
        """Weighted balance of plausibility, coverage, and parsimony."""
        base = (self.prior_plausibility * 0.45) + (self.explanatory_coverage * 0.35) + (self.parsimony_score * 0.20)
        # Adjust for evidence
        n_sup = len(self.supporting_evidence)
        n_con = len(self.contradicting_evidence)
        delta = (n_sup * 0.15) - (n_con * 0.25)
        return max(0.01, min(0.99, base + delta))

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "target_observation": self.target_observation,
            "candidate_cause": self.candidate_cause,
            "explanation": self.explanation_statement,
            "prior_plausibility": round(self.prior_plausibility, 3),
            "composite_score": round(self.composite_score, 3),
            "discriminant_test": self.discriminant_test,
            "supporting_count": len(self.supporting_evidence),
            "contradicting_count": len(self.contradicting_evidence),
        }


class AbductiveReasoningEngine:
    """Inference to the best explanation for observed anomalies and disruptions."""

    def __init__(self) -> None:
        # Knowledge templates for domain abduction
        self._explanation_generators: dict[str, list[dict[str, Any]]] = self._setup_templates()

    def _setup_templates(self) -> dict[str, list[dict[str, Any]]]:
        """Domain causal templates that generate competing explanations."""
        return {
            "decrease_in_customers": [
                {
                    "cause": "price_increase",
                    "explanation": "Customers found recent prices excessive relative to alternative goods or income",
                    "plausibility": 0.70,
                    "coverage": 0.85,
                    "parsimony": 0.90,
                    "test": "Compare sales volume before and after price change; inspect customer complaints",
                },
                {
                    "cause": "new_competition",
                    "explanation": "A rival seller or workshop has opened nearby, capturing market share",
                    "plausibility": 0.60,
                    "coverage": 0.80,
                    "parsimony": 0.75,
                    "test": "Scout neighboring locations and commercial stalls for competing goods",
                },
                {
                    "cause": "quality_deterioration",
                    "explanation": "Recent batches of goods had flaws or lower durability, damaging reputation",
                    "plausibility": 0.55,
                    "coverage": 0.75,
                    "parsimony": 0.80,
                    "test": "Inspect finished goods inventory and test material integrity",
                },
                {
                    "cause": "seasonal_demand_shift",
                    "explanation": "General demographic demand for this product naturally drops during this season",
                    "plausibility": 0.65,
                    "coverage": 0.70,
                    "parsimony": 0.85,
                    "test": "Check historical sales records from the same season last year",
                },
                {
                    "cause": "schedule_or_hours_misalignment",
                    "explanation": "Workshop opening hours no longer align with working hours of local buyers",
                    "plausibility": 0.50,
                    "coverage": 0.60,
                    "parsimony": 0.80,
                    "test": "Observe foot traffic outside the store when closed vs open",
                },
            ],
            "crop_wilting": [
                {
                    "cause": "soil_drought",
                    "explanation": "Insufficient precipitation or irrigation has dried out root systems",
                    "plausibility": 0.75,
                    "coverage": 0.90,
                    "parsimony": 0.90,
                    "test": "Examine soil moisture depth and irrigation canal levels",
                },
                {
                    "cause": "pest_infestation",
                    "explanation": "Insect or fungal parasites are attacking leaves or stems",
                    "plausibility": 0.60,
                    "coverage": 0.80,
                    "parsimony": 0.75,
                    "test": "Inspect underside of leaves and stems for larvae or fungal spots",
                },
                {
                    "cause": "soil_nutrient_depletion",
                    "explanation": "Continuous cropping without fallow or manure has depleted vital minerals",
                    "plausibility": 0.50,
                    "coverage": 0.70,
                    "parsimony": 0.70,
                    "test": "Compare vigor of crops in adjacent fertilized or fallowed plots",
                },
            ],
            "unexpected_illness": [
                {
                    "cause": "contaminated_water",
                    "explanation": "Ingestion of unboiled water from a stagnant or downstream source",
                    "plausibility": 0.70,
                    "coverage": 0.85,
                    "parsimony": 0.85,
                    "test": "Check if others who drank from the same well or river developed symptoms",
                },
                {
                    "cause": "spoiled_food",
                    "explanation": "Consumption of improperly stored or decayed rations",
                    "plausibility": 0.65,
                    "coverage": 0.80,
                    "parsimony": 0.90,
                    "test": "Inspect remaining food stocks for mold, foul smell, or discoloration",
                },
                {
                    "cause": "exhaustion_and_exposure",
                    "explanation": "Overwork in cold weather weakened physical constitution",
                    "plausibility": 0.55,
                    "coverage": 0.65,
                    "parsimony": 0.80,
                    "test": "Review recent sleep, energy levels, and outdoor shelter conditions",
                },
            ],
        }

    def generate_explanations(
        self,
        anomaly_key: str,
        context: Optional[dict[str, Any]] = None,
        graph: Optional[IndividualKnowledgeGraph] = None,
        tick: int = 0,
        epistemic: Optional[EpistemicInterface] = None,
    ) -> list[ExplanationHypothesis]:
        """Generate competing explanatory hypotheses for an observed anomaly."""
        context = context or {}
        templates = self._explanation_generators.get(anomaly_key)

        explanations: list[ExplanationHypothesis] = []

        if templates:
            for t in templates:
                hyp_id = f"abduct_{uuid4().hex[:8]}"
                # Modulate plausibility by agent's knowledge if available
                plausibility = t["plausibility"]
                if graph and graph.knows_concept(t["cause"]):
                    plausibility = min(0.95, plausibility + 0.10)

                hyp = ExplanationHypothesis(
                    hypothesis_id=hyp_id,
                    target_observation=anomaly_key,
                    candidate_cause=t["cause"],
                    explanation_statement=t["explanation"],
                    prior_plausibility=plausibility,
                    explanatory_coverage=t["coverage"],
                    parsimony_score=t["parsimony"],
                    discriminant_test=t["test"],
                    created_tick=tick,
                )
                explanations.append(hyp)

                if epistemic:
                    belief = EpistemicBelief(
                        belief_id=hyp_id,
                        subject=anomaly_key,
                        predicate="abductively_explained_by",
                        object_val=t["cause"],
                        belief_type=BeliefType.HYPOTHESIS,
                        confidence=hyp.composite_score,
                        source_type="abductive_reasoning",
                        created_tick=tick,
                        updated_tick=tick,
                    )
                    epistemic.register_belief(belief)
        else:
            # Fallback open-ended abductive hypothesis generator
            hyp = ExplanationHypothesis(
                hypothesis_id=f"abduct_{uuid4().hex[:8]}",
                target_observation=anomaly_key,
                candidate_cause="unidentified_environmental_or_social_factor",
                explanation_statement=f"Observation '{anomaly_key}' likely stems from unobserved shifts in resources or behavior",
                prior_plausibility=0.40,
                explanatory_coverage=0.50,
                parsimony_score=0.60,
                discriminant_test=f"Inquire with peers and inspect physical location for anomalies regarding {anomaly_key}",
                created_tick=tick,
            )
            explanations.append(hyp)

        # Sort by composite score descending
        explanations.sort(key=lambda h: h.composite_score, reverse=True)
        return explanations

    def compare_and_rank(self, hypotheses: list[ExplanationHypothesis]) -> list[ExplanationHypothesis]:
        """Rank hypotheses according to accumulated evidence, plausibility, and parsimony."""
        return sorted(hypotheses, key=lambda h: h.composite_score, reverse=True)

    def differentiate_with_evidence(
        self,
        hypotheses: list[ExplanationHypothesis],
        tested_cause: str,
        evidence_found: str,
        supports_cause: bool,
        tick: int = 0,
    ) -> list[ExplanationHypothesis]:
        """Incorporate outcome of a discriminant test to update relative ranking."""
        for hyp in hypotheses:
            if hyp.candidate_cause == tested_cause:
                if supports_cause:
                    hyp.supporting_evidence.append(evidence_found)
                else:
                    hyp.contradicting_evidence.append(evidence_found)
        return self.compare_and_rank(hypotheses)
