"""Cognitive engine — perception, attention filtering, and context interpretation.

Implements information processing, selective attention modulated by personality
and emotional state, and basic situational assessment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.core.types import HumanID, LocationID


@dataclass
class Perception:
    """A raw perceptual stimulus detected in the environment."""

    category: str        # 'social', 'spatial', 'physical', 'opportunity'
    content: str
    target_human_id: Optional[HumanID] = None
    location_id: Optional[LocationID] = None
    salience: float = 0.5  # Base physical/social salience
    data: dict[str, Any] = field(default_factory=dict)


class CognitiveEngine:
    """Perceptual, attentional, and context-integration subsystem."""

    def __init__(self) -> None:
        pass

    def perceive(
        self,
        current_location_id: Optional[LocationID],
        occupants: list[HumanID],
        is_daytime: bool,
        environmental_cues: Optional[list[str]] = None,
    ) -> list[Perception]:
        """Detect raw stimuli in current physical context."""
        perceptions: list[Perception] = []

        # Social stimuli
        for other_id in occupants:
            perceptions.append(
                Perception(
                    category="social",
                    content=f"Human {other_id} is present nearby",
                    target_human_id=other_id,
                    location_id=current_location_id,
                    salience=0.6,
                )
            )

        # Spatial stimuli
        if current_location_id:
            perceptions.append(
                Perception(
                    category="spatial",
                    content=f"Present at {current_location_id} during {'daytime' if is_daytime else 'night'}",
                    location_id=current_location_id,
                    salience=0.3,
                )
            )

        if environmental_cues:
            for cue in environmental_cues:
                perceptions.append(
                    Perception(
                        category="environment",
                        content=cue,
                        location_id=current_location_id,
                        salience=0.4,
                    )
                )

        return perceptions

    def attend(
        self,
        raw_perceptions: list[Perception],
        personality: PersonalityEngine,
        emotions: EmotionalEngine,
    ) -> list[Perception]:
        """Filter and rank perceptions via personality and emotional attention bias.

        - High extraversion prioritizes social cues.
        - High neuroticism or fear prioritizes threat/discomfort cues.
        - High openness prioritizes novel environmental stimuli.
        """
        if not raw_perceptions:
            return []

        extraversion = personality.get_trait("extraversion")
        neuroticism = personality.get_trait("neuroticism")
        openness = personality.get_trait("openness")

        fear = emotions.get_emotion("fear") if hasattr(emotions, "get_emotion") else 0.0
        curiosity = emotions.get_emotion("curiosity") if hasattr(emotions, "get_emotion") else 0.0

        def score(p: Perception) -> float:
            base = p.salience
            if p.category == "social":
                base += extraversion * 0.4
            elif p.category == "threat" or (p.category == "physical" and "hunger" in p.content):
                base += (neuroticism + fear) * 0.35
            elif p.category in ("environment", "opportunity"):
                base += (openness + curiosity) * 0.3
            return base

        ranked = sorted(raw_perceptions, key=score, reverse=True)
        # Attend to top 5 stimuli
        return ranked[:5]

    def reason(
        self,
        situation_description: str,
        options: list[str],
        memory: Optional[MemoryEngine] = None,
    ) -> str:
        """Basic heuristic evaluation generating an interpretable rationale."""
        if not options:
            return "No options to evaluate."
        return f"Evaluated {len(options)} options for situation '{situation_description}'"
