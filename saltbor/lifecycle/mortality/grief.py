"""Grief, bereavement, and community impact of death."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from saltbor.cognition.emotions.models import EmotionState
from saltbor.core.types import EmotionType, HumanID, Tick
from saltbor.lifecycle.genealogy.tree import GenealogicalGraph

if TYPE_CHECKING:
    from saltbor.population.human import SyntheticHuman
    from saltbor.social.engine import SocialEngine

logger = logging.getLogger(__name__)


class GriefEngine:
    """Calculates psychological bereavement and social mourning effects upon death."""

    def __init__(self) -> None:
        pass

    def apply_bereavement(
        self,
        survivor: SyntheticHuman,
        deceased_uid: HumanID,
        deceased_name: str,
        social: SocialEngine,
        genealogy: GenealogicalGraph,
        current_tick: Tick,
    ) -> float:
        """Apply emotional and behavioral grief to a survivor.

        Returns grief_intensity in [0.0, 1.0].
        """
        # 1. Kinship closeness factor
        kinship = genealogy.get_kinship_degree(survivor.uid, deceased_uid)
        kin_factor = 0.0
        if kinship == 0:
            return 0.0
        elif kinship == 1:    # Parent or child
            kin_factor = 0.85
        elif kinship == 2:  # Sibling or grandparent
            kin_factor = 0.65
        elif kinship is not None and kinship <= 4:
            kin_factor = 0.40

        # Check partner status
        rec = genealogy.get_record(survivor.uid)
        is_partner = (rec and rec.partner == deceased_uid)
        if is_partner:
            kin_factor = 0.95

        # 2. Relationship bond (trust + affinity)
        rel = social.get_relationship(survivor.uid, deceased_uid)
        bond = (rel.trust + rel.affinity) / 2.0

        # Combined grief intensity
        grief_intensity = min(1.0, max(kin_factor, bond * 0.8))

        if grief_intensity < 0.20:
            # Acquaintance / negligible impact
            return 0.0

        # 3. Emotional changes: spike in sadness, loneliness, and anxiety
        emotions = survivor.emotions
        if hasattr(emotions, "profile"):
            prof = emotions.profile
            # Sadness spike
            curr_sadness = prof.get_intensity(EmotionType.SADNESS)
            prof.active_emotions[EmotionType.SADNESS] = EmotionState(
                emotion_type=EmotionType.SADNESS,
                intensity=min(1.0, curr_sadness + 0.60 * grief_intensity),
                duration_remaining=int(192 * grief_intensity),  # Multi-day mourning
                decay_rate=0.005,  # Slow decay
            )
            # Loneliness spike
            curr_lone = prof.get_intensity(EmotionType.LONELINESS)
            prof.active_emotions[EmotionType.LONELINESS] = EmotionState(
                emotion_type=EmotionType.LONELINESS,
                intensity=min(1.0, curr_lone + 0.50 * grief_intensity),
                duration_remaining=int(144 * grief_intensity),
                decay_rate=0.008,
            )
            # Anxiety / vulnerability
            curr_anx = prof.get_intensity(EmotionType.ANXIETY)
            prof.active_emotions[EmotionType.ANXIETY] = EmotionState(
                emotion_type=EmotionType.ANXIETY,
                intensity=min(1.0, curr_anx + 0.35 * grief_intensity),
                duration_remaining=int(96 * grief_intensity),
                decay_rate=0.015,
            )

        # 4. Record salient semantic knowledge of the loss
        from saltbor.cognition.memory.semantic import SemanticFact
        survivor.memory.semantic.store(
            SemanticFact(
                fact_id=f"bereavement_{deceased_uid}",
                category="social_loss",
                content=f"Mourning the death of {deceased_name}.",
                confidence=1.0,
                source="community",
                learned_tick=current_tick,
            )
        )

        logger.info(
            "Survivor %s experienced grief (intensity: %.2f) for %s",
            survivor.name, grief_intensity, deceased_name
        )
        return grief_intensity
