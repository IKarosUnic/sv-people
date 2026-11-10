"""Autonomous Learning Engine for Saltbor Phase 0.6.

Processes knowledge acquisition across all 12 pathways, accounts for individual
differences, developmental stages, and cognitive constraints.
"""

from __future__ import annotations

import logging
from typing import Optional

from saltbor.knowledge.layers.individual_graph import EpistemicClaim, IndividualKnowledgeGraph
from saltbor.knowledge.layers.procedural_graph import ProceduralKnowledgeGraph
from saltbor.knowledge.learning.pathways import (
    PATHWAY_CONFIDENCE_WEIGHTS,
    LearningPathway,
    LearningProfile,
)

logger = logging.getLogger(__name__)


class AutonomousLearningEngine:
    """Manages knowledge acquisition and belief updates for an agent."""

    def __init__(self, profile: Optional[LearningProfile] = None) -> None:
        self.profile = profile or LearningProfile()

    def acquire_concept(
        self,
        knowledge_graph: IndividualKnowledgeGraph,
        node_id: str,
        pathway: LearningPathway,
        source_agent_id: Optional[str] = None,
        tick: int = 0,
        evidence: Optional[str] = None,
        is_misconception: bool = False,
        fatigue_penalty: float = 0.0,
    ) -> EpistemicClaim:
        """Acquire or reinforce acquaintance with a concept."""
        base_confidence = PATHWAY_CONFIDENCE_WEIGHTS.get(pathway, 0.5)

        # Modulate by pathway-specific aptitude
        multiplier = self.profile.learning_speed
        if pathway in (LearningPathway.OBSERVATION, LearningPathway.SOCIAL_IMITATION):
            multiplier *= self.profile.observational_ability
        elif pathway in (LearningPathway.TEACHING, LearningPathway.APPRENTICESHIP, LearningPathway.DIALOGUE):
            multiplier *= self.profile.communication_ability
        elif pathway in (LearningPathway.EXPERIMENTATION, LearningPathway.PROBLEM_SOLVING):
            multiplier *= self.profile.analytical_reasoning
        elif pathway in (LearningPathway.DIRECT_EXPERIENCE, LearningPathway.TRIAL_AND_ERROR):
            multiplier *= self.profile.practical_aptitude

        # Fatigue / attention penalty
        effective_confidence = max(0.1, min(1.0, (base_confidence * multiplier) * (1.0 - fatigue_penalty * 0.5)))

        claim = knowledge_graph.learn_concept(
            node_id=node_id,
            confidence=effective_confidence,
            source_pathway=str(pathway.value),
            source_agent_id=source_agent_id,
            tick=tick,
            is_misconception=is_misconception,
            evidence=evidence,
        )
        return claim

    def identify_knowledge_gaps(
        self,
        knowledge_graph: IndividualKnowledgeGraph,
        procedure_id: str,
        procedural_graph: ProceduralKnowledgeGraph,
        agent_skills: dict[str, float],
    ) -> dict[str, list[str]]:
        """Identify missing prerequisite concepts and skills required for a procedure."""
        proc = procedural_graph.get_procedure(procedure_id)
        if not proc:
            return {"missing_concepts": [], "missing_skills": [f"Unknown procedure: {procedure_id}"]}

        missing_concepts = [
            cid for cid in proc.prerequisite_concepts
            if not knowledge_graph.knows_concept(cid, min_confidence=0.3)
        ]

        missing_skills = [
            f"{s_id} (needs {min_lvl:.2f}, has {agent_skills.get(s_id, 0.0):.2f})"
            for s_id, min_lvl in proc.required_skills.items()
            if agent_skills.get(s_id, 0.0) < min_lvl
        ]

        return {
            "missing_concepts": missing_concepts,
            "missing_skills": missing_skills,
        }

    def revise_belief(
        self,
        knowledge_graph: IndividualKnowledgeGraph,
        item_id: str,
        is_confirming: bool,
        evidence_summary: str,
        tick: int = 0,
    ) -> Optional[EpistemicClaim]:
        """Update an existing belief following newly received evidence."""
        claim = knowledge_graph.get_claim(item_id)
        if not claim:
            return None

        # Adaptability controls how readily an individual shifts confidence
        rate = 0.15 * self.profile.adaptability

        if is_confirming:
            claim.reinforce(tick=tick, delta=rate, evidence=evidence_summary)
        else:
            claim.weaken(tick=tick, delta=rate * 1.2, evidence=evidence_summary)

        return claim
