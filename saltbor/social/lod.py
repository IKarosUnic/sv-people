"""Social Level of Detail (LOD) and Scalability Manager for Saltbor Phase 0.9.

Ensures high performance (sub-second ticks for hundreds of agents) by tiering
social processing into Focal, Proximate, and Background detail tiers.
"""

from __future__ import annotations

import enum
import logging
from typing import Any, Iterable

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class SocialLODTier(int, enum.Enum):
    """Processing tier for social updates."""

    TIER_1_FOCAL = 1       # Full per-tick cognitive deliberation, active conversations, fine edge changes
    TIER_2_PROXIMATE = 2   # Event-driven updates, proximity batch checks (every 4 ticks)
    TIER_3_BACKGROUND = 3  # Lazy evaluation upon encounter, periodic statistical decay (every 96 ticks)


class SocialLODManager:
    """Classifies agents into LOD tiers and regulates update frequency."""

    def __init__(self) -> None:
        self._focal_uids: set[str] = set()
        self._agent_tiers: dict[str, SocialLODTier] = {}

    def set_focal_agents(self, uids: Iterable[str | HumanID]) -> None:
        """Mark specific agents as active focal targets (e.g. observer camera or key test agents)."""
        self._focal_uids = {str(u) for u in uids}

    def assign_tier(self, human_uid: str | HumanID, tier: SocialLODTier) -> None:
        self._agent_tiers[str(human_uid)] = tier

    def get_tier(self, human_uid: str | HumanID, is_nearby_focal: bool = False) -> SocialLODTier:
        uid = str(human_uid)
        if uid in self._focal_uids:
            return SocialLODTier.TIER_1_FOCAL
        if is_nearby_focal:
            return SocialLODTier.TIER_2_PROXIMATE
        return self._agent_tiers.get(uid, SocialLODTier.TIER_3_BACKGROUND)

    def should_process_social_tick(self, human_uid: str | HumanID, tick: int, is_nearby_focal: bool = False) -> bool:
        """Determine if social reasoning should execute for this agent on this tick."""
        tier = self.get_tier(human_uid, is_nearby_focal)
        if tier == SocialLODTier.TIER_1_FOCAL:
            return True
        elif tier == SocialLODTier.TIER_2_PROXIMATE:
            return (tick % 4) == 0
        else: # TIER_3_BACKGROUND
            return (tick % 96) == 0
