"""Emotional engine — processes events into emotional responses and manages decay."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from saltbor.cognition.emotions.models import (
    EMOTION_VALENCE,
    EmotionalProfile,
    EmotionState,
)
from saltbor.cognition.personality.traits import PersonalityTraits
from saltbor.core.types import EmotionType
from saltbor.events.types import EventType, SimulationEvent

logger = logging.getLogger(__name__)

# Maps event types to one or more emotional responses.
# Each entry is (EmotionType, base_intensity, base_duration_ticks).
_EVENT_EMOTION_MAP: dict[EventType, list[tuple[EmotionType, float, int]]] = {
    # Positive social
    EventType.FRIENDSHIP_CREATED: [(EmotionType.JOY, 0.5, 24), (EmotionType.AFFECTION, 0.3, 20)],
    EventType.COOPERATION_OCCURRED: [(EmotionType.JOY, 0.3, 12), (EmotionType.MOTIVATION, 0.2, 8)],
    EventType.TRUST_INCREASED: [(EmotionType.AFFECTION, 0.3, 16)],
    EventType.CONVERSATION_HELD: [(EmotionType.JOY, 0.15, 8)],
    # Negative social
    EventType.FRIENDSHIP_ENDED: [(EmotionType.SADNESS, 0.5, 48), (EmotionType.ANGER, 0.2, 12)],
    EventType.TRUST_BROKEN: [(EmotionType.ANGER, 0.5, 24), (EmotionType.SADNESS, 0.4, 36)],
    EventType.CONFLICT_OCCURRED: [(EmotionType.ANGER, 0.4, 16), (EmotionType.FRUSTRATION, 0.3, 12)],
    # Economic
    EventType.JOB_STARTED: [(EmotionType.JOY, 0.4, 16), (EmotionType.MOTIVATION, 0.4, 24)],
    EventType.JOB_LOST: [(EmotionType.FEAR, 0.5, 48), (EmotionType.SADNESS, 0.4, 36)],
    EventType.MONEY_EARNED: [(EmotionType.JOY, 0.3, 8)],
    EventType.FINANCIAL_LOSS: [(EmotionType.FEAR, 0.4, 24), (EmotionType.ANGER, 0.2, 12)],
    # Achievement / personal
    EventType.GOAL_COMPLETED: [(EmotionType.JOY, 0.6, 24), (EmotionType.MOTIVATION, 0.4, 16)],
    EventType.GOAL_ABANDONED: [(EmotionType.SADNESS, 0.3, 16), (EmotionType.FRUSTRATION, 0.3, 12)],
    EventType.NEED_CRITICAL: [(EmotionType.FEAR, 0.4, 12), (EmotionType.FRUSTRATION, 0.3, 8)],
    EventType.NEED_SATISFIED: [(EmotionType.JOY, 0.3, 8)],
    EventType.ACHIEVEMENT: [(EmotionType.JOY, 0.5, 20), (EmotionType.MOTIVATION, 0.3, 16)],
    # Cognitive
    EventType.SKILL_GAINED: [(EmotionType.JOY, 0.3, 12), (EmotionType.CURIOSITY, 0.3, 16)],
    EventType.SKILL_IMPROVED: [(EmotionType.MOTIVATION, 0.2, 8)],
    EventType.INSIGHT_GAINED: [(EmotionType.CURIOSITY, 0.5, 20), (EmotionType.JOY, 0.3, 12)],
}


@dataclass
class EmotionalEngine:
    """Generates emotional responses to events and manages emotional decay.

    Different personality types react differently:
    - High neuroticism amplifies negative emotional responses.
    - High extraversion amplifies positive social emotional responses.
    - High agreeableness softens anger / conflict responses.
    """

    profile: EmotionalProfile = field(default_factory=EmotionalProfile)

    # ------------------------------------------------------------------
    # Event processing
    # ------------------------------------------------------------------

    def process_event(
        self,
        event: SimulationEvent,
        personality: PersonalityTraits,
    ) -> list[EmotionState]:
        """Generate emotional response(s) for *event*, modulated by *personality*.

        Returns the list of :class:`EmotionState` objects that were added.
        """
        responses = _EVENT_EMOTION_MAP.get(event.event_type)
        if not responses:
            return []

        created: list[EmotionState] = []
        reactivity = self.profile.emotional_reactivity

        for emotion_type, base_intensity, base_duration in responses:
            # Modulate intensity based on personality
            intensity = base_intensity * (0.5 + reactivity)
            intensity *= event.importance  # scale by event importance

            valence = EMOTION_VALENCE.get(emotion_type, 0.0)
            if valence < 0:
                # Negative emotions amplified by neuroticism
                neuro = personality.effective_value("neuroticism")
                intensity *= (0.7 + neuro * 0.6)  # range [0.7, 1.3]
                # High agreeableness dampens anger specifically
                if emotion_type in (EmotionType.ANGER, EmotionType.FRUSTRATION):
                    agree = personality.effective_value("agreeableness")
                    intensity *= (1.2 - agree * 0.4)  # range [0.8, 1.2]
            else:
                # Positive emotions amplified by extraversion
                extra = personality.effective_value("extraversion")
                intensity *= (0.8 + extra * 0.4)  # range [0.8, 1.2]

            intensity = max(0.0, min(1.0, intensity))
            duration = max(1, int(base_duration * (0.5 + reactivity)))

            state = EmotionState(
                emotion_type=emotion_type,
                intensity=intensity,
                duration_remaining=duration,
                source_event_id=event.event_id,
            )
            self.profile.add_emotion(state)
            created.append(state)

        logger.debug(
            "Emotional response to %s: %s",
            event.event_type.value,
            [(s.emotion_type.value, f"{s.intensity:.2f}") for s in created],
        )
        return created

    # ------------------------------------------------------------------
    # Tick update
    # ------------------------------------------------------------------

    def update(self, tick: int) -> None:
        """Advance one tick: decay all active emotions."""
        self.profile.decay_all(ticks=1)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_emotion(self, emotion_type: EmotionType | str) -> float:
        """Return current intensity for a specific emotion (0.0 if absent)."""
        return self.profile.get_intensity(emotion_type)

    def get_mood(self) -> float:
        """Return overall mood as a float in [-1, 1]."""
        return self.profile.get_valence()

    def get_decision_weights(self) -> dict[str, float]:
        """Return a dict of decision-relevant weights derived from emotions.

        These weights can be fed into the decision engine to influence choices.
        """
        mood = self.get_mood()
        dominant = self.profile.get_dominant_emotion()

        weights: dict[str, float] = {
            "mood_valence": mood,
            "social_seeking": 0.0,
            "safety_seeking": 0.0,
            "achievement_drive": 0.0,
            "rest_preference": 0.0,
            "avoidance": 0.0,
        }

        # Sadness / loneliness → seek social contact
        weights["social_seeking"] = self.get_emotion(EmotionType.SADNESS) * 0.4 + \
            self.get_emotion(EmotionType.AFFECTION) * 0.3

        # Fear → seek safety
        weights["safety_seeking"] = self.get_emotion(EmotionType.FEAR) * 0.6

        # Motivation / curiosity → achievement drive
        weights["achievement_drive"] = self.get_emotion(EmotionType.MOTIVATION) * 0.5 + \
            self.get_emotion(EmotionType.CURIOSITY) * 0.3

        # Frustration / anger → avoidance of current situation
        weights["avoidance"] = self.get_emotion(EmotionType.FRUSTRATION) * 0.4 + \
            self.get_emotion(EmotionType.ANGER) * 0.3

        # Negative mood → preference for rest / self-care
        if mood < -0.3:
            weights["rest_preference"] = abs(mood) * 0.4

        return weights
