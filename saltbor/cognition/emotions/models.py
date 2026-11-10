"""Emotion data models for the Saltbor simulation."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, computed_field

from saltbor.core.types import EmotionType, EventID, Tick


# Valence mapping: how positive or negative each emotion is (-1 to +1).
EMOTION_VALENCE: dict[EmotionType, float] = {
    EmotionType.JOY: 1.0,
    EmotionType.EXCITEMENT: 0.85,
    EmotionType.SATISFACTION: 0.75,
    EmotionType.AFFECTION: 0.9,
    EmotionType.CURIOSITY: 0.4,
    EmotionType.MOTIVATION: 0.7,
    EmotionType.SADNESS: -0.8,
    EmotionType.FEAR: -0.6,
    EmotionType.ANGER: -0.7,
    EmotionType.FRUSTRATION: -0.6,
    EmotionType.ANXIETY: -0.65,
    EmotionType.DISAPPOINTMENT: -0.6,
    EmotionType.LONELINESS: -0.75,
    EmotionType.SHAME: -0.5,
    EmotionType.GUILT: -0.4,
}

# Default per-tick decay rates based on biological/psychological half-lives.
EMOTION_DEFAULT_DECAY: dict[EmotionType, float] = {
    EmotionType.JOY: 0.03,
    EmotionType.EXCITEMENT: 0.06,
    EmotionType.SATISFACTION: 0.02,
    EmotionType.AFFECTION: 0.02,
    EmotionType.CURIOSITY: 0.04,
    EmotionType.MOTIVATION: 0.03,
    EmotionType.ANGER: 0.07,
    EmotionType.FRUSTRATION: 0.05,
    EmotionType.FEAR: 0.04,
    EmotionType.ANXIETY: 0.02,
    EmotionType.DISAPPOINTMENT: 0.03,
    EmotionType.SADNESS: 0.015,
    EmotionType.LONELINESS: 0.015,
    EmotionType.SHAME: 0.035,
    EmotionType.GUILT: 0.025,
}


class EmotionState(BaseModel):
    """A single active emotion with intensity and time-based decay."""

    emotion_type: EmotionType
    intensity: float = Field(ge=0.0, le=1.0, description="Strength of the emotion.")
    duration_remaining: int = Field(ge=0, description="Ticks until the emotion naturally expires.")
    decay_rate: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Per-tick multiplicative decay applied to intensity.",
    )
    source_event_id: Optional[EventID] = None

    def decay(self, ticks: int = 1) -> None:
        """Reduce intensity and remaining duration."""
        for _ in range(ticks):
            self.intensity *= (1.0 - self.decay_rate)
            self.duration_remaining = max(0, self.duration_remaining - 1)
        # Snap to zero when negligible
        if self.intensity < 0.01:
            self.intensity = 0.0

    @property
    def is_expired(self) -> bool:
        """True when the emotion has fully decayed or timed out."""
        return self.intensity < 0.01 or self.duration_remaining <= 0

    @property
    def valence(self) -> float:
        """Signed emotional valence scaled by intensity."""
        return EMOTION_VALENCE.get(self.emotion_type, 0.0) * self.intensity


class EmotionalProfile(BaseModel):
    """Aggregate emotional state: all active emotions and derived mood."""

    active_emotions: dict[EmotionType, EmotionState] = Field(default_factory=dict)
    emotional_reactivity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Personality-derived modifier for how strongly emotions are felt.",
    )
    regulation_capacity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Capacity for emotional self-regulation and recovery to baseline.",
    )
    expressiveness: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Tendency to outwardly express internal emotions vs keep them internal.",
    )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def should_express_externally(self, emotion_type: EmotionType | str) -> bool:
        """Determine whether the internal emotion is expressed outwardly.

        Individual expression threshold: inhibited individuals require higher
        internal intensity before an emotion breaks out into observable behavior.
        """
        intensity = self.get_intensity(emotion_type)
        if intensity < 0.05:
            return False
        # Threshold: expressiveness 1.0 -> 0.20 threshold; expressiveness 0.0 -> 0.80 threshold
        threshold = max(0.20, 0.80 - self.expressiveness * 0.60)
        return intensity >= threshold

    def get_dominant_emotion(self) -> EmotionType | None:
        """Return the emotion type with the highest intensity, or None."""
        if not self.active_emotions:
            return None
        return max(self.active_emotions.values(), key=lambda e: e.intensity).emotion_type

    def get_valence(self) -> float:
        """Compute overall emotional valence in [-1, 1].

        Positive → happy/motivated, negative → sad/angry.
        """
        if not self.active_emotions:
            return 0.0
        total_weight = 0.0
        weighted_valence = 0.0
        for es in self.active_emotions.values():
            if es.intensity > 0.01:
                weighted_valence += es.valence
                total_weight += es.intensity
        if total_weight == 0.0:
            return 0.0
        raw = weighted_valence / total_weight
        return max(-1.0, min(1.0, raw))

    @computed_field  # type: ignore[misc]
    @property
    def overall_mood(self) -> float:
        """Alias for ``get_valence()`` exposed as a Pydantic computed field."""
        return self.get_valence()

    def get_intensity(self, emotion_type: EmotionType | str) -> float:
        """Return current intensity for a specific emotion (0.0 if absent)."""
        if isinstance(emotion_type, str):
            try:
                emotion_type = EmotionType(emotion_type)
            except ValueError:
                return 0.0
        state = self.active_emotions.get(emotion_type)
        return state.intensity if state else 0.0

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_emotion(self, state: EmotionState) -> None:
        """Add or intensify an emotion.

        If the emotion already exists, the intensities are combined (capped
        at 1.0) and the longer remaining duration is kept.
        """
        existing = self.active_emotions.get(state.emotion_type)
        if existing is not None:
            existing.intensity = min(1.0, existing.intensity + state.intensity * 0.5)
            existing.duration_remaining = max(existing.duration_remaining, state.duration_remaining)
            existing.source_event_id = state.source_event_id or existing.source_event_id
        else:
            self.active_emotions[state.emotion_type] = state.model_copy()

    def decay_all(self, ticks: int = 1) -> None:
        """Decay every active emotion and remove expired ones, modulated by regulation capacity."""
        expired: list[EmotionType] = []
        reg_factor = 1.0 + (self.regulation_capacity - 0.5) * 0.4  # [0.8, 1.2]
        for etype, estate in self.active_emotions.items():
            for _ in range(ticks):
                estate.intensity *= (1.0 - estate.decay_rate * reg_factor)
                estate.duration_remaining = max(0, estate.duration_remaining - 1)
            if estate.intensity < 0.01:
                estate.intensity = 0.0
            if estate.is_expired:
                expired.append(etype)
        for etype in expired:
            del self.active_emotions[etype]

    def clear(self) -> None:
        """Remove all active emotions."""
        self.active_emotions.clear()
