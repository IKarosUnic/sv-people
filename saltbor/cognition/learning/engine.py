"""Learning engine — skill acquisition, strategy updates, and knowledge extraction.

Enables synthetic humans to improve skills through practice, adapt strategies
following success or failure, and distill experiences into general semantic beliefs.
"""

from __future__ import annotations

from typing import Optional

from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.memory.semantic import SemanticFact
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.core.types import SkillID
from saltbor.events.types import SimulationEvent


class LearningEngine:
    """Acquisition and behavioral adaptation engine."""

    def __init__(self) -> None:
        self.learning_rate: float = 1.0

    def practice_skill(
        self,
        skill_id: SkillID,
        memory: MemoryEngine,
        duration_ticks: int = 1,
        talent_factor: float = 1.0,
    ) -> float:
        """Practice a skill, earning experience points with diminishing returns."""
        xp_gain = 5.0 * duration_ticks * talent_factor * self.learning_rate
        return memory.procedural.improve_skill(skill_id, xp_gain)

    def extract_knowledge_from_event(
        self,
        event: SimulationEvent,
        memory: MemoryEngine,
    ) -> Optional[SemanticFact]:
        """Convert salient experiences into reusable semantic facts."""
        if event.importance < 0.4:
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
    ) -> dict[str, float]:
        """Adapt caution and persistence following an adverse or failed outcome."""
        persistence = personality.get_trait("persistence")
        neuroticism = personality.get_trait("neuroticism")

        # High persistence leads to trying new strategies; high neuroticism increases caution
        caution_increase = 0.05 * (1.0 + neuroticism - persistence)
        return {"caution_delta": max(0.01, caution_increase)}
