"""Metacognition Engine for Saltbor Phase 0.7 (Section 5).

Provides unified access to:
1. Self-audit of cognitive capacities and limitations (K/U/B/R/S).
2. Well-calibrated confidence estimation.
3. Cognitive error and contradiction detection.
4. Salient post-event reflection and future adaptation.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.cognition.metacognition.confidence import CalibratedConfidenceEstimator, ConfidenceAudit
from saltbor.cognition.metacognition.error_detection import CognitiveErrorDetector, DetectedCognitiveError
from saltbor.cognition.metacognition.reflection import CognitiveReflector, ReflectionRecord
from saltbor.cognition.metacognition.self_audit import MetacognitiveAuditor, MetacognitiveProfile
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph

logger = logging.getLogger(__name__)


class MetacognitionEngine:
    """Master introspective coordinator for evaluating self-capacities and correcting errors."""

    def __init__(self) -> None:
        self.auditor = MetacognitiveAuditor()
        self.confidence_estimator = CalibratedConfidenceEstimator()
        self.error_detector = CognitiveErrorDetector()
        self.reflector = CognitiveReflector()
        self.reflection_history: list[ReflectionRecord] = []

    def perform_self_audit(
        self,
        graph: IndividualKnowledgeGraph,
        epistemic: Optional[EpistemicInterface] = None,
        skills: Optional[dict[str, float]] = None,
        active_goal_requirements: Optional[list[str]] = None,
        neuroticism: float = 0.5,
        conscientiousness: float = 0.5,
        tick: int = 0,
    ) -> MetacognitiveProfile:
        """Perform a structured introspective audit of knowledge, skills, and self-efficacy."""
        return self.auditor.audit(
            graph=graph,
            epistemic=epistemic,
            skills=skills,
            active_goal_requirements=active_goal_requirements,
            neuroticism=neuroticism,
            conscientiousness=conscientiousness,
            tick=tick,
        )

    def estimate_confidence(
        self,
        pathway: str,
        verification_count: int = 1,
        supporting_evidence_count: int = 0,
        contradiction_count: int = 0,
        source_credibility: float = 1.0,
        domain_experience_level: float = 0.5,
        has_internal_contradiction: bool = False,
    ) -> ConfidenceAudit:
        """Compute soundly calibrated epistemic confidence."""
        return self.confidence_estimator.estimate(
            pathway=pathway,
            verification_count=verification_count,
            supporting_evidence_count=supporting_evidence_count,
            contradiction_count=contradiction_count,
            source_credibility=source_credibility,
            domain_experience_level=domain_experience_level,
            has_internal_contradiction=has_internal_contradiction,
        )

    def scan_for_errors(
        self,
        graph: IndividualKnowledgeGraph,
        epistemic: Optional[EpistemicInterface] = None,
        recent_failed_actions: Optional[list[str]] = None,
        observed_outcomes_vs_predictions: Optional[list[tuple[str, str, str]]] = None,
        current_tick: int = 0,
    ) -> list[DetectedCognitiveError]:
        """Detect contradictions, assumptions violations, or repeated failures."""
        return self.error_detector.detect_errors(
            graph=graph,
            epistemic=epistemic,
            recent_failed_actions=recent_failed_actions,
            observed_outcomes_vs_predictions=observed_outcomes_vs_predictions,
            current_tick=current_tick,
        )

    def reflect_on_outcome(
        self,
        target_event: str,
        action_attempted: str,
        motivating_reason: str,
        actual_outcome: str,
        was_successful: bool,
        lessons: Optional[list[str]] = None,
        epistemic: Optional[EpistemicInterface] = None,
        tick: int = 0,
    ) -> ReflectionRecord:
        """Execute a cognitive reflection upon an important event."""
        rec = self.reflector.reflect(
            target_event=target_event,
            action_attempted=action_attempted,
            motivating_reason=motivating_reason,
            actual_outcome=actual_outcome,
            was_successful=was_successful,
            lessons=lessons,
            epistemic=epistemic,
            tick=tick,
        )
        self.reflection_history.append(rec)
        return rec
