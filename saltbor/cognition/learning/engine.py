"""Learning engine — skill acquisition, strategy updates, and knowledge extraction.

Enables synthetic humans to improve skills through practice, direct instruction,
observation of skilled peers, adapt following mistakes, and distill experiences
into general semantic beliefs and transferrable competencies.
"""

from __future__ import annotations

import logging
from typing import Optional

from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.memory.semantic import SemanticFact
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.core.types import SkillID, Tick
from saltbor.events.types import SimulationEvent

logger = logging.getLogger(__name__)


class LearningEngine:
    """Acquisition and behavioral adaptation engine."""

    def __init__(self, learning_rate: float = 1.0) -> None:
        self.learning_rate: float = learning_rate

    def practice_skill(
        self,
        skill_id: SkillID,
        memory: MemoryEngine,
        duration_ticks: int = 1,
        talent_factor: float = 1.0,
        current_tick: Tick = 0,
    ) -> float:
        """Practice a skill directly, earning experience points with diminishing returns."""
        xp_gain = 5.0 * duration_ticks * talent_factor * self.learning_rate
        return memory.procedural.improve_skill(
            skill_id=skill_id,
            xp_gain=xp_gain,
            talent_factor=talent_factor,
            current_tick=current_tick,
            enable_transfer=True,
        )

    def learn_through_instruction(
        self,
        skill_id: SkillID,
        instructor_level: float,
        memory: MemoryEngine,
        duration_ticks: int = 1,
        talent_factor: float = 1.0,
        current_tick: Tick = 0,
    ) -> float:
        """Acquire skill competence through pedagogical instruction by a teacher or master.

        Instruction multiplies learning speed proportional to the instructor's proficiency.
        """
        pedagogical_multiplier = 1.0 + max(0.2, instructor_level) * 0.8  # up to 1.8x
        xp_gain = 5.0 * duration_ticks * talent_factor * self.learning_rate * pedagogical_multiplier
        return memory.procedural.improve_skill(
            skill_id=skill_id,
            xp_gain=xp_gain,
            talent_factor=talent_factor,
            current_tick=current_tick,
            enable_transfer=True,
        )

    def learn_by_observing(
        self,
        skill_id: SkillID,
        observed_expert_level: float,
        memory: MemoryEngine,
        current_tick: Tick = 0,
    ) -> float:
        """Acquire foundational insight by observing a skilled individual at the same location.

        Provides ~40% of active practice XP through social modeling.
        """
        modeling_multiplier = max(0.1, observed_expert_level) * 0.4
        xp_gain = 5.0 * modeling_multiplier * self.learning_rate
        return memory.procedural.improve_skill(
            skill_id=skill_id,
            xp_gain=xp_gain,
            talent_factor=1.0,
            current_tick=current_tick,
            enable_transfer=True,
        )

    def extract_knowledge_from_event(
        self,
        event: SimulationEvent,
        memory: MemoryEngine,
    ) -> Optional[SemanticFact]:
        """Convert salient experiences into reusable semantic facts."""
        if event.importance < 0.35:
            return None

        fact_id = f"fact_{event.event_type.value}_{event.tick}"
        content = f"Event {event.event_type.value} occurred at tick {event.tick}"
        if event.location_id:
            content += f" at {event.location_id}"

        fact = SemanticFact(
            fact_id=fact_id,
            category="experience",
            content=content,
            confidence=0.85,
            source="personal_experience",
            learned_tick=event.tick,
        )
        memory.semantic.store(fact)
        return fact

    def learn_from_failure(
        self,
        failure_event: SimulationEvent,
        personality: PersonalityEngine,
        memory: Optional[MemoryEngine] = None,
    ) -> dict[str, float]:
        """Adapt caution, persistence, and knowledge following an adverse or failed outcome."""
        persistence = personality.get_trait("persistence")
        neuroticism = personality.get_trait("neuroticism")

        # High persistence leads to trying new strategies; high neuroticism increases caution
        caution_increase = 0.05 * (1.0 + neuroticism - persistence)

        # Distill semantic lesson if memory engine provided
        if memory:
            fact_id = f"lesson_failure_{failure_event.event_type.value}"
            lesson = f"Caution advised: setback encountered during {failure_event.event_type.value}"
            memory.semantic.update_with_evidence(
                fact_id=fact_id,
                is_confirming=True,
                delta=0.25,
                new_content=lesson,
                current_tick=failure_event.tick,
            )

        return {"caution_delta": max(0.01, caution_increase)}
