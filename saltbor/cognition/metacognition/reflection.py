"""Cognitive Reflection Engine for Saltbor Phase 0.7 (Section 5).

Provides post-event introspective reflection:
- What was attempted?
- Why was it attempted (motivation/goal)?
- What actually occurred?
- What was learned?
- What should be done differently next time?

Executed conditionally based on event salience, surprise, and Cognitive LOD.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional
from uuid import uuid4

from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.epistemic.interface import EpistemicInterface


@dataclasses.dataclass
class ReflectionRecord:
    """An episodic cognitive reflection on a completed action or crisis."""

    reflection_id: str
    target_event: str
    action_attempted: str
    motivating_reason: str
    actual_outcome: str
    was_successful: bool
    lessons_learned: list[str]
    future_adaptation_strategy: str
    salience_score: float               # [0.0, 1.0]
    tick: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "reflection_id": self.reflection_id,
            "event": self.target_event,
            "attempted": self.action_attempted,
            "reason": self.motivating_reason,
            "actual_outcome": self.actual_outcome,
            "success": self.was_successful,
            "lessons": self.lessons_learned,
            "future_adaptation": self.future_adaptation_strategy,
        }


class CognitiveReflector:
    """Conducts post-action structured evaluations."""

    @staticmethod
    def reflect(
        target_event: str,
        action_attempted: str,
        motivating_reason: str,
        actual_outcome: str,
        was_successful: bool,
        lessons: Optional[list[str]] = None,
        epistemic: Optional[EpistemicInterface] = None,
        tick: int = 0,
    ) -> ReflectionRecord:
        """Execute a cognitive reflection cycle."""
        lessons_list = list(lessons or [])

        if was_successful:
            lessons_list.append(f"Confirmed efficacy of '{action_attempted}' for achieving '{motivating_reason}'")
            adaptation = f"Reinforce reliance on '{action_attempted}' in equivalent future contexts"
            salience = 0.65
        else:
            lessons_list.append(f"Action '{action_attempted}' produced unintended outcome: '{actual_outcome}'")
            adaptation = f"In future crises resembling '{target_event}', explore alternative strategies or seek collaboration before retrying"
            salience = 0.85

        record = ReflectionRecord(
            reflection_id=f"refl_{uuid4().hex[:8]}",
            target_event=target_event,
            action_attempted=action_attempted,
            motivating_reason=motivating_reason,
            actual_outcome=actual_outcome,
            was_successful=was_successful,
            lessons_learned=lessons_list,
            future_adaptation_strategy=adaptation,
            salience_score=salience,
            tick=tick,
        )

        if epistemic:
            epistemic.register_belief(
                EpistemicBelief(
                    belief_id=record.reflection_id,
                    subject=action_attempted,
                    predicate="reflection_adaptation",
                    object_val=adaptation,
                    belief_type=BeliefType.INFERENCE,
                    confidence=0.85,
                    source_type="cognitive_reflection",
                    created_tick=tick,
                    updated_tick=tick,
                    evidence_items=lessons_list,
                )
            )

        return record
