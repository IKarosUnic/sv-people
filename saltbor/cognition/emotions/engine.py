"""Emotional engine — processes events into emotional responses and manages decay."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from saltbor.cognition.emotions.models import (
    EMOTION_DEFAULT_DECAY,
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
    EventType.FRIENDSHIP_CREATED: [
        (EmotionType.JOY, 0.5, 24),
        (EmotionType.AFFECTION, 0.4, 28),
        (EmotionType.EXCITEMENT, 0.3, 16),
    ],
    EventType.COOPERATION_OCCURRED: [
        (EmotionType.JOY, 0.3, 16),
        (EmotionType.SATISFACTION, 0.35, 20),
        (EmotionType.MOTIVATION, 0.2, 12),
    ],
    EventType.TRUST_INCREASED: [
        (EmotionType.AFFECTION, 0.35, 20),
        (EmotionType.SATISFACTION, 0.25, 16),
    ],
    EventType.CONVERSATION_HELD: [
        (EmotionType.JOY, 0.18, 10),
        (EmotionType.AFFECTION, 0.15, 12),
    ],
    EventType.RECONCILIATION_ACHIEVED: [
        (EmotionType.AFFECTION, 0.5, 32),
        (EmotionType.SATISFACTION, 0.45, 28),
        (EmotionType.JOY, 0.4, 20),
    ],
    EventType.CONFLICT_RESOLVED: [
        (EmotionType.SATISFACTION, 0.4, 24),
        (EmotionType.JOY, 0.3, 16),
    ],

    # Negative social
    EventType.FRIENDSHIP_ENDED: [
        (EmotionType.SADNESS, 0.5, 48),
        (EmotionType.LONELINESS, 0.45, 40),
        (EmotionType.ANGER, 0.2, 16),
    ],
    EventType.RELATIONSHIP_ENDED: [
        (EmotionType.SADNESS, 0.55, 48),
        (EmotionType.LONELINESS, 0.5, 44),
        (EmotionType.DISAPPOINTMENT, 0.4, 32),
    ],
    EventType.TRUST_BROKEN: [
        (EmotionType.ANGER, 0.5, 24),
        (EmotionType.DISAPPOINTMENT, 0.45, 32),
        (EmotionType.SADNESS, 0.35, 36),
    ],
    EventType.CONFLICT_OCCURRED: [
        (EmotionType.ANGER, 0.4, 16),
        (EmotionType.FRUSTRATION, 0.35, 16),
        (EmotionType.ANXIETY, 0.25, 20),
    ],
    EventType.SOCIAL_REJECTION: [
        (EmotionType.SHAME, 0.45, 28),
        (EmotionType.SADNESS, 0.4, 32),
        (EmotionType.LONELINESS, 0.5, 36),
        (EmotionType.DISAPPOINTMENT, 0.35, 24),
    ],

    # Economic
    EventType.JOB_STARTED: [
        (EmotionType.EXCITEMENT, 0.45, 20),
        (EmotionType.JOY, 0.4, 20),
        (EmotionType.MOTIVATION, 0.4, 24),
    ],
    EventType.JOB_PROMOTION: [
        (EmotionType.JOY, 0.6, 32),
        (EmotionType.SATISFACTION, 0.55, 36),
        (EmotionType.EXCITEMENT, 0.5, 24),
    ],
    EventType.JOB_LOST: [
        (EmotionType.FEAR, 0.5, 48),
        (EmotionType.ANXIETY, 0.55, 48),
        (EmotionType.SADNESS, 0.4, 36),
        (EmotionType.DISAPPOINTMENT, 0.4, 32),
    ],
    EventType.MONEY_EARNED: [
        (EmotionType.JOY, 0.3, 12),
        (EmotionType.SATISFACTION, 0.3, 16),
    ],
    EventType.FINANCIAL_LOSS: [
        (EmotionType.FEAR, 0.4, 28),
        (EmotionType.ANXIETY, 0.45, 32),
        (EmotionType.FRUSTRATION, 0.3, 16),
    ],

    # Achievement / personal goals
    EventType.GOAL_CREATED: [
        (EmotionType.EXCITEMENT, 0.35, 16),
        (EmotionType.CURIOSITY, 0.3, 16),
        (EmotionType.MOTIVATION, 0.4, 20),
    ],
    EventType.GOAL_COMPLETED: [
        (EmotionType.JOY, 0.6, 28),
        (EmotionType.SATISFACTION, 0.55, 32),
        (EmotionType.EXCITEMENT, 0.4, 20),
    ],
    EventType.GOAL_MODIFIED: [
        (EmotionType.CURIOSITY, 0.25, 16),
        (EmotionType.MOTIVATION, 0.3, 16),
    ],
    EventType.GOAL_PROCRASTINATED: [
        (EmotionType.GUILT, 0.35, 20),
        (EmotionType.ANXIETY, 0.25, 20),
    ],
    EventType.GOAL_ABANDONED: [
        (EmotionType.DISAPPOINTMENT, 0.4, 24),
        (EmotionType.SADNESS, 0.3, 20),
        (EmotionType.FRUSTRATION, 0.3, 16),
    ],
    EventType.FAILED_ATTEMPT: [
        (EmotionType.FRUSTRATION, 0.4, 16),
        (EmotionType.DISAPPOINTMENT, 0.35, 20),
        (EmotionType.SHAME, 0.2, 16),
    ],
    EventType.NEED_CRITICAL: [
        (EmotionType.FEAR, 0.4, 16),
        (EmotionType.ANXIETY, 0.45, 20),
        (EmotionType.FRUSTRATION, 0.35, 12),
    ],
    EventType.NEED_SATISFIED: [
        (EmotionType.SATISFACTION, 0.4, 16),
        (EmotionType.JOY, 0.3, 12),
    ],
    EventType.ACHIEVEMENT: [
        (EmotionType.JOY, 0.5, 24),
        (EmotionType.SATISFACTION, 0.5, 28),
        (EmotionType.EXCITEMENT, 0.4, 20),
    ],
    EventType.PERSONAL_ACHIEVEMENT: [
        (EmotionType.JOY, 0.55, 28),
        (EmotionType.SATISFACTION, 0.5, 32),
        (EmotionType.EXCITEMENT, 0.45, 24),
    ],

    # Cognitive & Learning
    EventType.SKILL_GAINED: [
        (EmotionType.JOY, 0.35, 16),
        (EmotionType.CURIOSITY, 0.35, 20),
        (EmotionType.SATISFACTION, 0.3, 16),
    ],
    EventType.SKILL_ACQUIRED: [
        (EmotionType.JOY, 0.4, 20),
        (EmotionType.SATISFACTION, 0.4, 24),
        (EmotionType.EXCITEMENT, 0.3, 16),
    ],
    EventType.SKILL_IMPROVED: [
        (EmotionType.SATISFACTION, 0.3, 16),
        (EmotionType.MOTIVATION, 0.25, 12),
    ],
    EventType.SKILL_DECAYED: [
        (EmotionType.DISAPPOINTMENT, 0.3, 16),
        (EmotionType.FRUSTRATION, 0.25, 12),
    ],
    EventType.INSIGHT_GAINED: [
        (EmotionType.CURIOSITY, 0.5, 24),
        (EmotionType.EXCITEMENT, 0.35, 16),
        (EmotionType.JOY, 0.3, 16),
    ],
    EventType.SELF_REFLECTION: [
        (EmotionType.CURIOSITY, 0.3, 16),
        (EmotionType.SATISFACTION, 0.2, 16),
    ],
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

            decay_rate = EMOTION_DEFAULT_DECAY.get(emotion_type, 0.02)
            state = EmotionState(
                emotion_type=emotion_type,
                intensity=intensity,
                duration_remaining=duration,
                decay_rate=decay_rate,
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

    def induce_emotion(
        self,
        emotion_type: EmotionType | str,
        intensity: float,
        duration_ticks: int = 16,
    ) -> EmotionState:
        """Directly induce an emotion (useful for experiments and direct simulation triggers)."""
        if isinstance(emotion_type, str):
            emotion_type = EmotionType(emotion_type)
        decay_rate = EMOTION_DEFAULT_DECAY.get(emotion_type, 0.02)
        state = EmotionState(
            emotion_type=emotion_type,
            intensity=max(0.0, min(1.0, intensity)),
            duration_remaining=duration_ticks,
            decay_rate=decay_rate,
        )
        self.profile.add_emotion(state)
        return state

    def add_emotional_charge(
        self,
        emotion_type: EmotionType | str,
        intensity: float,
        tick: int = 0,
    ) -> None:
        """Alias to induce emotional response with given intensity."""
        if intensity > 0:
            self.induce_emotion(emotion_type, intensity)

    def should_express(self, emotion_type: EmotionType | str) -> bool:
        """Check whether the given emotion is expressed outwardly."""
        return self.profile.should_express_externally(emotion_type)

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

    @property
    def regulation_capacity(self) -> float:
        """Return the individual's emotional regulation capacity."""
        return self.profile.regulation_capacity

    def get_decision_weights(self) -> dict[str, float]:
        """Return a dict of decision-relevant weights derived from emotions.

        These weights can be fed into the decision engine to influence choices.
        """
        mood = self.get_mood()

        weights: dict[str, float] = {
            "mood_valence": mood,
            "social_seeking": 0.0,
            "safety_seeking": 0.0,
            "achievement_drive": 0.0,
            "rest_preference": 0.0,
            "avoidance": 0.0,
            "novelty_seeking": 0.0,
        }

        # Loneliness / Sadness / Affection → seek social contact
        weights["social_seeking"] = (
            self.get_emotion(EmotionType.LONELINESS) * 0.5
            + self.get_emotion(EmotionType.SADNESS) * 0.3
            + self.get_emotion(EmotionType.AFFECTION) * 0.3
        )

        # Fear / Anxiety → seek safety and avoid risky ventures
        weights["safety_seeking"] = (
            self.get_emotion(EmotionType.FEAR) * 0.5
            + self.get_emotion(EmotionType.ANXIETY) * 0.5
        )

        # Motivation / Excitement / Curiosity / Satisfaction → drive to achieve
        weights["achievement_drive"] = (
            self.get_emotion(EmotionType.MOTIVATION) * 0.4
            + self.get_emotion(EmotionType.EXCITEMENT) * 0.3
            + self.get_emotion(EmotionType.CURIOSITY) * 0.2
            + self.get_emotion(EmotionType.SATISFACTION) * 0.2
        )

        # Frustration / Anger / Shame / Disappointment → avoidance
        weights["avoidance"] = (
            self.get_emotion(EmotionType.FRUSTRATION) * 0.35
            + self.get_emotion(EmotionType.ANGER) * 0.3
            + self.get_emotion(EmotionType.SHAME) * 0.25
            + self.get_emotion(EmotionType.DISAPPOINTMENT) * 0.2
        )

        # Curiosity / Excitement → seek novel environments and learning
        weights["novelty_seeking"] = (
            self.get_emotion(EmotionType.CURIOSITY) * 0.5
            + self.get_emotion(EmotionType.EXCITEMENT) * 0.4
        )

        # Negative mood & high anxiety → preference for rest / recovery
        if mood < -0.3:
            weights["rest_preference"] = abs(mood) * 0.3 + self.get_emotion(EmotionType.ANXIETY) * 0.2

        return weights
