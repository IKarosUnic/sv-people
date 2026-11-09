"""Personality engine — manages personality evolution over simulation time."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from saltbor.cognition.personality.traits import PersonalityTraits, TRAIT_NAMES
from saltbor.events.types import EventType, SimulationEvent

logger = logging.getLogger(__name__)

# Maximum absolute base-value shift per event (personality changes are SLOW).
_MAX_BASE_SHIFT: float = 0.002

# Maps event types to the traits they tend to influence and direction (+/-).
_EVENT_TRAIT_EFFECTS: dict[EventType, list[tuple[str, float]]] = {
    EventType.FRIENDSHIP_CREATED: [("extraversion", 0.3), ("agreeableness", 0.2)],
    EventType.FRIENDSHIP_ENDED: [("extraversion", -0.1), ("neuroticism", 0.2)],
    EventType.TRUST_BROKEN: [("agreeableness", -0.3), ("neuroticism", 0.3)],
    EventType.CONFLICT_OCCURRED: [("agreeableness", -0.2), ("neuroticism", 0.2)],
    EventType.COOPERATION_OCCURRED: [("agreeableness", 0.2), ("extraversion", 0.1)],
    EventType.GOAL_COMPLETED: [("persistence", 0.3), ("conscientiousness", 0.2)],
    EventType.GOAL_ABANDONED: [("persistence", -0.1), ("patience", -0.1)],
    EventType.JOB_STARTED: [("conscientiousness", 0.1), ("openness", 0.1)],
    EventType.JOB_LOST: [("neuroticism", 0.2), ("risk_tolerance", -0.1)],
    EventType.FINANCIAL_LOSS: [("risk_tolerance", -0.2), ("neuroticism", 0.2)],
    EventType.ACHIEVEMENT: [("persistence", 0.2), ("conscientiousness", 0.1), ("openness", 0.1)],
    EventType.SKILL_IMPROVED: [("conscientiousness", 0.1), ("persistence", 0.1)],
}


@dataclass
class PersonalityEngine:
    """Manages a human's personality traits over time.

    The engine applies very slow base-value shifts in response to significant
    life events, and drifts current values back toward their bases each tick.
    """

    traits: PersonalityTraits = field(default_factory=PersonalityTraits)

    # ------------------------------------------------------------------
    # Tick update
    # ------------------------------------------------------------------

    def update(self, tick: int, events: list[SimulationEvent] | None = None) -> None:
        """Process one simulation tick.

        * Drift all current trait values toward their bases.
        * Optionally process a batch of events for personality shifts.
        """
        self.traits.apply_drift(ticks=1)

        if events:
            for event in events:
                self._process_event(event)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_trait(self, name: str) -> float:
        """Return the effective (current) value of a trait by name."""
        return self.traits.effective_value(name)

    def get_base_trait(self, name: str) -> float:
        """Return the baseline value of a trait by name."""
        return self.traits.get_trait(name).base_value

    def get_behavioral_modifier(self, context: str = "") -> dict[str, float]:
        """Return a dict of modifiers that downstream decision engines can use.

        The modifiers are derived directly from current trait values and provide
        guidance like ``social_tendency``, ``caution``, ``creativity``, etc.
        """
        e = self.traits.effective_value
        modifiers: dict[str, float] = {
            "social_tendency": e("extraversion") * 0.6 + e("agreeableness") * 0.4,
            "caution": (1.0 - e("risk_tolerance")) * 0.5 + e("conscientiousness") * 0.3 + e("neuroticism") * 0.2,
            "creativity": e("openness") * 0.7 + (1.0 - e("conscientiousness")) * 0.3,
            "emotional_stability": 1.0 - e("neuroticism"),
            "determination": e("persistence") * 0.5 + e("conscientiousness") * 0.3 + e("patience") * 0.2,
            "impulsiveness": e("risk_tolerance") * 0.4 + (1.0 - e("patience")) * 0.4 + (1.0 - e("conscientiousness")) * 0.2,
        }
        return modifiers

    # ------------------------------------------------------------------
    # Experience application
    # ------------------------------------------------------------------

    def apply_experience(self, event: SimulationEvent, emotional_impact: float = 0.0) -> None:
        """Apply a significant life event to (very slowly) shift base values.

        ``emotional_impact`` is in [-1, 1]; positive = positive experience.
        The actual base shift is tiny — capped at ``_MAX_BASE_SHIFT``.
        """
        effects = _EVENT_TRAIT_EFFECTS.get(event.event_type, [])
        if not effects:
            return

        importance = event.importance
        for trait_name, direction in effects:
            # Scale: importance * direction * emotional_impact contribution
            raw_shift = direction * importance * _MAX_BASE_SHIFT
            # Emotional impact amplifies (same-sign) or dampens (opposite-sign)
            if emotional_impact != 0.0:
                raw_shift *= (1.0 + abs(emotional_impact) * 0.5)
            trait = self.traits.get_trait(trait_name)
            trait.shift_base(raw_shift)
            # Significant experiences also immediately impact current behavioral state
            trait.shift_current(raw_shift * 5.0)

        logger.debug(
            "Personality base shift from %s (importance=%.2f, emotion=%.2f)",
            event.event_type.value,
            importance,
            emotional_impact,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _process_event(self, event: SimulationEvent) -> None:
        """Shift *current* values in response to events (temporary effect)."""
        effects = _EVENT_TRAIT_EFFECTS.get(event.event_type, [])
        for trait_name, direction in effects:
            shift = direction * event.importance * 0.05  # moderate temporary shift
            self.traits.get_trait(trait_name).shift_current(shift)
