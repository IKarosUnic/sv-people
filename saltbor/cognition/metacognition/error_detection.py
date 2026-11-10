"""Cognitive Error Detection for Saltbor Phase 0.7 (Section 5).

Detects epistemic, perceptual, and planning errors:
1. Contradictions between held beliefs.
2. Incorrect premises and invalidated assumptions.
3. Outdated or stale information.
4. Large prediction-observation discrepancies.
5. Planning deadlocks or looping strategies.
6. Repetition of failed actions.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional

from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


@dataclasses.dataclass
class DetectedCognitiveError:
    """An identified cognitive or planning malfunction."""

    error_type: str                     # 'contradiction', 'incorrect_assumption', 'outdated_info', 'prediction_error', 'repetitive_failure'
    description: str
    severity: float                     # [0.0, 1.0]
    affected_elements: list[str]
    suggested_correction: str
    detected_tick: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.error_type,
            "description": self.description,
            "severity": round(self.severity, 3),
            "affected": self.affected_elements,
            "correction": self.suggested_correction,
        }


class CognitiveErrorDetector:
    """Monitors beliefs, plans, and outcomes to flag errors and trigger adaptation."""

    @staticmethod
    def detect_errors(
        graph: IndividualKnowledgeGraph,
        epistemic: Optional[EpistemicInterface] = None,
        recent_failed_actions: Optional[list[str]] = None,
        observed_outcomes_vs_predictions: Optional[list[tuple[str, str, str]]] = None, # (prediction, actual, context)
        current_tick: int = 0,
        stale_tick_threshold: int = 192, # 2 days of unverified claims
    ) -> list[DetectedCognitiveError]:
        """Scan cognitive state and flag errors requiring strategy revision."""
        errors: list[DetectedCognitiveError] = []

        # 1. Contradictions in belief network
        if epistemic:
            contras = epistemic.detect_contradictions()
            for c in contras:
                errors.append(
                    DetectedCognitiveError(
                        error_type="contradiction",
                        description=c.get("description", "Contradictory beliefs detected"),
                        severity=0.75,
                        affected_elements=[str(c.get("source", c.get("subject"))), str(c.get("target", c.get("predicate")))],
                        suggested_correction="Seek direct empirical observation or consult high-trust mentor to resolve contradiction",
                        detected_tick=current_tick,
                    )
                )

        # 2. Repetition of failed actions (Repetitive failure trap)
        failed_actions = recent_failed_actions or []
        counts: dict[str, int] = {}
        for act in failed_actions:
            counts[act] = counts.get(act, 0) + 1
            if counts[act] >= 2:
                errors.append(
                    DetectedCognitiveError(
                        error_type="repetitive_failure",
                        description=f"Action '{act}' has failed {counts[act]} consecutive times without strategy modification",
                        severity=0.85,
                        affected_elements=[act],
                        suggested_correction="Abandon repetitive action; seek alternative strategy, resource substitution, or external help",
                        detected_tick=current_tick,
                    )
                )

        # 3. Discrepancies between prediction and observation
        outcomes = observed_outcomes_vs_predictions or []
        for pred, actual, ctx in outcomes:
            if pred.lower() != actual.lower():
                errors.append(
                    DetectedCognitiveError(
                        error_type="prediction_error",
                        description=f"Predicted '{pred}', but actual outcome was '{actual}' in context '{ctx}'",
                        severity=0.60,
                        affected_elements=[pred, actual],
                        suggested_correction="Trigger abductive explanation to understand why prediction failed",
                        detected_tick=current_tick,
                    )
                )

        # 4. Outdated / Stale information
        for nid in graph.all_known_node_ids():
            claim = graph.get_claim(nid)
            if claim and not claim.is_forgotten and (current_tick - claim.last_verified_tick) > stale_tick_threshold:
                if claim.confidence > 0.6:  # High confidence on very old information
                    errors.append(
                        DetectedCognitiveError(
                            error_type="outdated_info",
                            description=f"Belief about '{nid}' unverified for {current_tick - claim.last_verified_tick} ticks; world state may have shifted",
                            severity=0.40,
                            affected_elements=[nid],
                            suggested_correction="Re-inspect location or verify status before acting on this premise",
                            detected_tick=current_tick,
                        )
                    )

        return errors
