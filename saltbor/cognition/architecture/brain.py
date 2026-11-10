"""Functional Cognitive Architecture for Saltbor Phase 0.7 (Section 9).

Integrates the 6 specialized functional brain-inspired subsystems:
1. Executive / Frontal System (Planning, impulse control, goal prioritization, replanning)
2. Memory / Hippocampal System (Episodic retrieval, consolidation, contextual comparisons)
3. Emotional / Limbic System (Affective valence, motivation, fear/curiosity risk modulation)
4. Semantic / Temporal System (Concept associations, ontology, knowledge graphs, language)
5. Spatial / Parietal System (Spatial relations, distance costs, navigation feasibility)
6. Procedural / Cerebellar System (Automated habits, action sequences, execution adjustment)

All subsystems exchange information via strongly-typed interfaces and directly
influence concrete autonomous decisions in the simulation.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Optional

from saltbor.cognition.autonomy.engine import AutonomyEngine, Goal
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.planning.goap import ActionDefinition, WorldState
from saltbor.cognition.problem_solving.engine import ProblemSolvingEngine
from saltbor.cognition.reasoning.engine import AdvancedReasoningEngine
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class BrainDeliberationOutcome:
    """The synthesized decision outcome arising from the 6 functional cognitive systems."""

    action_name: str
    target_location_id: Optional[str]
    motivating_goal: Optional[str]
    executive_priority: float
    limbic_emotional_valence: float
    spatial_travel_cost: float
    procedural_habit_strength: float
    epistemic_certainty: float
    reasoning_summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action_name,
            "target_location": self.target_location_id,
            "goal": self.motivating_goal,
            "executive_priority": round(self.executive_priority, 3),
            "limbic_valence": round(self.limbic_emotional_valence, 3),
            "spatial_cost": round(self.spatial_travel_cost, 3),
            "habit_strength": round(self.procedural_habit_strength, 3),
            "epistemic_certainty": round(self.epistemic_certainty, 3),
            "summary": self.reasoning_summary,
        }


class CognitiveBrainArchitecture:
    """Master coordinator binding Frontal, Hippocampal, Limbic, Temporal, Parietal, and Cerebellar systems."""

    def __init__(
        self,
        human_uid: str,
        personality: PersonalityEngine,
        emotions: EmotionalEngine,
        memory: MemoryEngine,
        autonomy: AutonomyEngine,
        knowledge_graph: IndividualKnowledgeGraph,
        epistemic: EpistemicInterface,
        reasoning: AdvancedReasoningEngine,
        problem_solver: ProblemSolvingEngine,
    ) -> None:
        self.human_uid = str(human_uid)
        # 1. Executive / Frontal
        self.executive = autonomy
        self.problem_solver = problem_solver
        self.reasoning = reasoning

        # 2. Memory / Hippocampal
        self.hippocampal = memory

        # 3. Emotional / Limbic
        self.limbic = emotions
        self.personality = personality

        # 4. Semantic / Temporal
        self.temporal_knowledge = knowledge_graph
        self.epistemic = epistemic

        # 5. Spatial / Parietal (state and distance heuristics)
        self.known_spatial_positions: dict[str, tuple[float, float]] = {}

        # 6. Procedural / Cerebellar (habit library and routine tracking)
        self.habit_strengths: dict[str, float] = {} # action_name -> frequency/automaticity

    def register_location_coordinate(self, location_id: str, x: float, y: float) -> None:
        self.known_spatial_positions[location_id] = (x, y)

    def calculate_spatial_distance(self, loc_a: Optional[str], loc_b: Optional[str]) -> float:
        """Parietal subsystem: compute Euclidean physical distance between settlement locations."""
        if not loc_a or not loc_b or loc_a == loc_b:
            return 0.0
        pos_a = self.known_spatial_positions.get(loc_a, (0.0, 0.0))
        pos_b = self.known_spatial_positions.get(loc_b, (0.0, 0.0))
        dx = pos_a[0] - pos_b[0]
        dy = pos_a[1] - pos_b[1]
        return (dx * dx + dy * dy) ** 0.5

    def deliberate(
        self,
        current_location_id: Optional[str],
        available_candidate_actions: list[dict[str, Any]], # list of {action_name, target_loc, expected_effects}
        current_tick: int = 0,
    ) -> BrainDeliberationOutcome:
        """Synthesize all 6 cognitive systems into a bounded rational choice."""
        if not available_candidate_actions:
            return BrainDeliberationOutcome(
                action_name="rest",
                target_location_id=current_location_id,
                motivating_goal="quiescence",
                executive_priority=0.2,
                limbic_emotional_valence=0.0,
                spatial_travel_cost=0.0,
                procedural_habit_strength=0.1,
                epistemic_certainty=0.9,
                reasoning_summary="No candidate actions available; resting.",
            )

        # 1. Executive system: check primary active goals
        primary_goal = self.executive.current_primary_goal()
        prio_goal_desc = primary_goal.description if primary_goal else "maintenance"
        goal_prio = primary_goal.priority if primary_goal else 0.40

        # 2. Limbic system: affective mood and fear/curiosity bias
        mood = self.limbic.get_mood()
        fear = self.limbic.get_emotion("fear")
        curiosity = self.limbic.get_emotion("curiosity")
        risk_discount = max(0.2, 1.0 - (fear * 0.5))

        scored_actions: list[tuple[float, dict[str, Any], float, float, float, float]] = []

        for act in available_candidate_actions:
            act_name = act.get("action_name", "activity")
            target_loc = act.get("target_location", current_location_id)

            # Spatial parietal cost: distance penalty
            dist = self.calculate_spatial_distance(current_location_id, target_loc)
            spatial_penalty = min(0.40, dist / 500.0)

            # Procedural cerebellar automaticity: habits execute faster and cheaper
            habit = self.habit_strengths.get(act_name, 0.1)

            # Semantic temporal check: epistemic confidence in action domain
            domain = act.get("domain", act_name)
            claim = self.temporal_knowledge.get_claim(domain)
            epistemic_conf = claim.confidence if claim else 0.5

            # Goal alignment bonus (Executive)
            goal_bonus = 0.35 if primary_goal and any(w in act_name.lower() for w in prio_goal_desc.lower().split() if len(w) > 3) else 0.0

            # Composite brain utility formula
            utility = (
                (goal_prio * 0.35)
                + (goal_bonus)
                + (mood * 0.15)
                + (curiosity * 0.15 if "explore" in act_name or "study" in act_name else 0.0)
                + (habit * 0.15)
                + (epistemic_conf * 0.10)
                - (spatial_penalty * 0.20)
            ) * risk_discount

            scored_actions.append((utility, act, goal_prio, mood, dist, habit))

        scored_actions.sort(key=lambda item: item[0], reverse=True)
        best_utility, best_act, b_prio, b_mood, b_dist, b_habit = scored_actions[0]

        # Update procedural habit strength (Cerebellar learning)
        best_name = best_act.get("action_name", "activity")
        self.habit_strengths[best_name] = min(0.95, self.habit_strengths.get(best_name, 0.1) + 0.03)

        summary = (
            f"Frontal priority ({b_prio:.2f}) aligned with goal '{prio_goal_desc}', "
            f"modulated by Limbic mood ({b_mood:+.2f}), Parietal travel distance ({b_dist:.0f}m), "
            f"and Cerebellar habit strength ({b_habit:.2f})."
        )

        return BrainDeliberationOutcome(
            action_name=best_name,
            target_location_id=best_act.get("target_location", current_location_id),
            motivating_goal=prio_goal_desc,
            executive_priority=b_prio,
            limbic_emotional_valence=b_mood,
            spatial_travel_cost=b_dist,
            procedural_habit_strength=b_habit,
            epistemic_certainty=0.85,
            reasoning_summary=summary,
        )
