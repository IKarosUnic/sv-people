"""Personality engine — manages personality evolution over simulation time."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from saltbor.cognition.personality.traits import PersonalityTraits, TRAIT_NAMES
from saltbor.events.types import EventType, SimulationEvent

logger = logging.getLogger(__name__)

# Maximum absolute base-value shift per event (personality changes are SLOW).
_MAX_BASE_SHIFT: float = 0.002

# Maps event types to the traits they tend to influence and direction (+/-).
_EVENT_TRAIT_EFFECTS: dict[EventType, list[tuple[str, float]]] = {
    EventType.FRIENDSHIP_CREATED: [("extraversion", 0.3), ("agreeableness", 0.2)],
    EventType.FRIENDSHIP_ENDED: [("extraversion", -0.15), ("neuroticism", 0.2)],
    EventType.RELATIONSHIP_ENDED: [("extraversion", -0.2), ("neuroticism", 0.25), ("agreeableness", -0.1)],
    EventType.TRUST_BROKEN: [("agreeableness", -0.3), ("neuroticism", 0.3), ("risk_tolerance", -0.1)],
    EventType.CONFLICT_OCCURRED: [("agreeableness", -0.2), ("neuroticism", 0.2)],
    EventType.CONFLICT_RESOLVED: [("agreeableness", 0.2), ("patience", 0.2)],
    EventType.RECONCILIATION_ACHIEVED: [("agreeableness", 0.3), ("extraversion", 0.2), ("neuroticism", -0.15)],
    EventType.COOPERATION_OCCURRED: [("agreeableness", 0.2), ("extraversion", 0.1), ("persistence", 0.1)],
    EventType.SOCIAL_REJECTION: [("extraversion", -0.25), ("neuroticism", 0.3), ("agreeableness", -0.15)],
    EventType.GOAL_COMPLETED: [("persistence", 0.3), ("conscientiousness", 0.2)],
    EventType.GOAL_ABANDONED: [("persistence", -0.1), ("patience", -0.1)],
    EventType.FAILED_ATTEMPT: [("persistence", -0.1), ("patience", -0.1), ("neuroticism", 0.15)],
    EventType.JOB_STARTED: [("conscientiousness", 0.1), ("openness", 0.1)],
    EventType.JOB_PROMOTION: [("conscientiousness", 0.2), ("persistence", 0.2), ("risk_tolerance", 0.1)],
    EventType.JOB_LOST: [("neuroticism", 0.25), ("risk_tolerance", -0.15), ("persistence", -0.1)],
    EventType.FINANCIAL_LOSS: [("risk_tolerance", -0.2), ("neuroticism", 0.2)],
    EventType.ACHIEVEMENT: [("persistence", 0.2), ("conscientiousness", 0.1), ("openness", 0.1)],
    EventType.PERSONAL_ACHIEVEMENT: [("persistence", 0.25), ("conscientiousness", 0.15), ("openness", 0.1)],
    EventType.SKILL_IMPROVED: [("conscientiousness", 0.1), ("persistence", 0.1)],
    EventType.SKILL_ACQUIRED: [("conscientiousness", 0.15), ("persistence", 0.15), ("openness", 0.1)],
    EventType.SKILL_DECAYED: [("persistence", -0.05)],
    EventType.SELF_REFLECTION: [("patience", 0.2), ("conscientiousness", 0.15), ("neuroticism", -0.1)],
}


@dataclass
class PersonalityEngine:
    """Manages an individual's personality evolution over simulation time.

    Maintains the distinction between:
    - Innate temperament: biological starting values.
    - Base traits: long-term slowly shifting personality tendencies with historical audit log.
    - Current traits: temporary fluctuations that drift back to base values.
    - Values and behavioral patterns: learned heuristics, priorities, and coping styles.
    """

    traits: PersonalityTraits = field(default_factory=PersonalityTraits)
    evolution_history: list[dict[str, Any]] = field(default_factory=list)
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    stress_level: float = 0.0

    # ------------------------------------------------------------------
    # Tick update
    # ------------------------------------------------------------------

    def update(self, tick: int, events: list[SimulationEvent] | None = None) -> None:
        """Process one simulation tick.

        * Drift all current trait values toward their bases.
        * Gradually decay stress level toward 0.
        * Optionally process a batch of events for personality shifts.
        """
        self.traits.apply_drift(ticks=1)
        self.stress_level = max(0.0, self.stress_level - 0.005)

        if events:
            for event in events:
                self._process_event(event)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_trait(self, name: str) -> float:
        """Return the effective (current) value of a trait by name."""
        return self.traits.effective_value(name)

    def effective_value(self, name: str) -> float:
        """Return the effective (current) value of a trait by name."""
        return self.traits.effective_value(name)

    def get_base_trait(self, name: str) -> float:
        """Return the baseline value of a trait by name."""
        return self.traits.get_trait(name).base_value

    def get_temperament(self, name: str) -> float:
        """Return the initial biological temperament for a trait."""
        return getattr(self.traits.get_trait(name), "temperament_value", 0.5)

    @property
    def temperament_value(self) -> str:
        return getattr(self.traits, "temperament_name", "balanced")

    @temperament_value.setter
    def temperament_value(self, val: str) -> None:
        self.traits.temperament_name = val

    @property
    def personal_values(self) -> dict[str, float]:
        return getattr(self.traits, "personal_values", {})

    @personal_values.setter
    def personal_values(self, val: dict[str, float]) -> None:
        self.traits.personal_values = val

    @property
    def behavioral_patterns(self) -> dict[str, float]:
        return getattr(self.traits, "behavioral_patterns", {})

    @behavioral_patterns.setter
    def behavioral_patterns(self, val: dict[str, float]) -> None:
        self.traits.behavioral_patterns = val

    def get_evolution_log(self) -> list[dict[str, Any]]:
        """Return complete audit trail of personality base shifts."""
        return list(self.evolution_history)

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
            "ambition": e("persistence") * 0.5 + e("conscientiousness") * 0.3 + e("openness") * 0.2,
            "cooperativeness": e("agreeableness") * 0.7 + e("extraversion") * 0.3,
        }

        # Behavioral instability under acute chronic stress:
        # increases impulsiveness and erodes patience, creating human behavioral contradictions
        if self.stress_level > 0.5:
            modifiers["impulsiveness"] = min(1.0, modifiers["impulsiveness"] + self.stress_level * 0.25)
            modifiers["caution"] = max(0.1, modifiers["caution"] - self.stress_level * 0.15)

        return modifiers

    # ------------------------------------------------------------------
    # Experience application & Evolution
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

        # Track failure / success streaks
        if event.event_type in (EventType.FAILED_ATTEMPT, EventType.GOAL_ABANDONED, EventType.FINANCIAL_LOSS, EventType.JOB_LOST):
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.stress_level = min(1.0, self.stress_level + 0.20)
        elif event.event_type in (EventType.GOAL_COMPLETED, EventType.ACHIEVEMENT, EventType.PERSONAL_ACHIEVEMENT, EventType.JOB_PROMOTION):
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            self.stress_level = max(0.0, self.stress_level - 0.25)

        for trait_name, direction in effects:
            # Scale: importance * direction * emotional_impact contribution
            raw_shift = direction * importance * _MAX_BASE_SHIFT
            # Emotional impact amplifies (same-sign) or dampens (opposite-sign)
            if emotional_impact != 0.0:
                raw_shift *= (1.0 + abs(emotional_impact) * 0.5)

            # Cumulative regression / momentum from streaks:
            if self.consecutive_failures >= 3 and trait_name in ("patience", "persistence"):
                raw_shift -= 0.0005  # regression under persistent failure
            elif self.consecutive_successes >= 3 and trait_name in ("persistence", "risk_tolerance"):
                raw_shift += 0.0005  # confidence momentum

            trait = self.traits.get_trait(trait_name)
            old_base = trait.base_value
            trait.shift_base(raw_shift)
            new_base = trait.base_value

            # Significant experiences also immediately impact current behavioral state
            trait.shift_current(raw_shift * 5.0)

            # Record provenance in audit log
            self.evolution_history.append({
                "tick": event.tick,
                "event_type": event.event_type.value,
                "trait": trait_name,
                "old_base": round(old_base, 4),
                "new_base": round(new_base, 4),
                "delta": round(new_base - old_base, 5),
                "cause": f"{event.event_type.value} (importance={importance:.2f}, emotion={emotional_impact:.2f})",
            })

        logger.debug(
            "Personality base shift from %s (importance=%.2f, emotion=%.2f)",
            event.event_type.value,
            importance,
            emotional_impact,
        )

    def apply_social_influence(
        self,
        peer_traits: PersonalityTraits,
        interaction_quality: float,
        tick: int = 0,
    ) -> None:
        """Gently pull traits toward respected/trusted peer norms over shared time."""
        if interaction_quality <= 0.6:
            return
        influence_strength = 0.0003 * interaction_quality
        for name in TRAIT_NAMES:
            my_val = self.traits.get_trait(name).base_value
            peer_val = peer_traits.get_trait(name).base_value
            diff = peer_val - my_val
            shift = diff * influence_strength
            self.traits.get_trait(name).shift_base(shift)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _process_event(self, event: SimulationEvent) -> None:
        """Shift *current* values in response to events (temporary effect)."""
        effects = _EVENT_TRAIT_EFFECTS.get(event.event_type, [])
        for trait_name, direction in effects:
            shift = direction * event.importance * 0.05  # moderate temporary shift
            self.traits.get_trait(trait_name).shift_current(shift)
