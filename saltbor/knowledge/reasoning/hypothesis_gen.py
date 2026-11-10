"""Hypothesis Generation Engine for Saltbor Phase 0.6.

Detects anomalies, unmet needs, or unexplained phenomena, and abductively
generates explanatory hypotheses with testable predictions.
"""

from __future__ import annotations

import dataclasses
from typing import Optional
from uuid import uuid4

from saltbor.knowledge.layers.hypothesis_graph import Hypothesis, HypothesisDiscoveryGraph
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


@dataclasses.dataclass
class UnexplainedPhenomenon:
    """An observed event or anomaly requiring explanatory hypotheses."""

    phenomenon_id: str
    description: str
    observed_context: dict
    severity: float = 0.5


class HypothesisGenerationEngine:
    """Abductive reasoner that formulates explanations for anomalies."""

    def generate_hypotheses_for_phenomenon(
        self,
        graph: IndividualKnowledgeGraph,
        hypothesis_graph: HypothesisDiscoveryGraph,
        phenomenon: UnexplainedPhenomenon,
        tick: int = 0,
    ) -> list[Hypothesis]:
        """Formulate candidate explanatory hypotheses addressing an anomaly."""
        generated: list[Hypothesis] = []

        # Candidate 1: Environmental / External driver
        h1 = hypothesis_graph.propose_hypothesis(
            creator_uid=graph.human_uid,
            title=f"Environmental cause for {phenomenon.description}",
            target_phenomenon=phenomenon.phenomenon_id,
            statement=f"The anomaly '{phenomenon.description}' is driven by environmental fluctuations (e.g. soil moisture or temperature).",
            assumptions=["External conditions fluctuate non-linearly."],
            prior_confidence=0.50,
            tick=tick,
        )
        generated.append(h1)

        # Candidate 2: Material / Procedural defect
        h2 = hypothesis_graph.propose_hypothesis(
            creator_uid=graph.human_uid,
            title=f"Procedural defect explanation for {phenomenon.description}",
            target_phenomenon=phenomenon.phenomenon_id,
            statement=f"The anomaly '{phenomenon.description}' is caused by substandard tools or procedural contamination.",
            assumptions=["Tool wear and procedural variations affect output consistency."],
            prior_confidence=0.45,
            tick=tick,
        )
        generated.append(h2)

        return generated
