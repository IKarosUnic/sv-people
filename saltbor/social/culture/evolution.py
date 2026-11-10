"""Cultural Evolution and Collective Learning Engine for Saltbor Phase 0.9.

Models cultural elements, dynamic adoption, intergenerational transmission,
imitation, innovation, mutation, conservation, and abandonment of traditions.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
import uuid
from typing import Any, Optional

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class CulturalCategory(str, enum.Enum):
    """Domains of shared cultural practices and traditions."""

    CULINARY_PRACTICE = "culinary_practice"       # E.g., pupusas revueltas vs. de ayote
    COMMERCIAL_CUSTOM = "commercial_custom"       # E.g., regateo, fiado de confianza
    COMMUNAL_TRADITION = "communal_tradition"     # E.g., faena colectiva, patronal festivals
    AGRICULTURAL_TECHNIQUE = "agricultural_technique" # E.g., milpa intercalada con frijol
    ARTISANAL_CRAFT = "artisanal_craft"           # E.g., alfareria de barro negro


@dataclasses.dataclass
class CulturalTradition:
    """A cultural practice or meme evolving across community generations."""

    tradition_id: str
    name: str
    category: CulturalCategory
    origin_community_id: str
    description: str
    adopters: set[str] = dataclasses.field(default_factory=set)
    utility_score: float = 0.7        # [0.0, 1.0] Perceived functional or social value
    sacredness: float = 0.5           # [0.0, 1.0] Resistance to change / emotional reverence
    variation_notes: list[str] = dataclasses.field(default_factory=list)
    created_tick: int = 0
    last_practiced_tick: int = 0
    is_active: bool = True

    def practice(self, practitioner_uid: str, tick: int) -> None:
        """Practice the tradition, sustaining its vitality."""
        self.adopters.add(practitioner_uid)
        self.last_practiced_tick = tick

    def mutate_tradition(self, innovator_uid: str, innovation_summary: str, tick: int) -> None:
        """Introduce an innovation or adaptive tweak to an existing tradition."""
        self.variation_notes.append(f"Tick {tick} by {innovator_uid}: {innovation_summary}")
        # Utility may shift upward with innovation
        self.utility_score = min(1.0, self.utility_score + 0.10)


class CulturalEvolutionEngine:
    """Coordinates collective cultural adoption, innovation, and generational drift."""

    def __init__(self) -> None:
        self._traditions: dict[str, CulturalTradition] = {}

    def register_tradition(
        self,
        name: str,
        category: CulturalCategory,
        origin_community_id: str,
        description: str,
        initial_adopters: Optional[list[str]] = None,
        utility_score: float = 0.75,
        sacredness: float = 0.5,
        tick: int = 0,
    ) -> CulturalTradition:
        """Introduce or formalize a cultural tradition."""
        trad_id = f"trad_{category.value[:4]}_{uuid.uuid4().hex[:6]}"
        trad = CulturalTradition(
            tradition_id=trad_id,
            name=name,
            category=category,
            origin_community_id=origin_community_id,
            description=description,
            utility_score=utility_score,
            sacredness=sacredness,
            created_tick=tick,
            last_practiced_tick=tick,
        )
        if initial_adopters:
            trad.adopters.update(initial_adopters)
        self._traditions[trad_id] = trad
        return trad

    def get_tradition(self, tradition_id: str) -> Optional[CulturalTradition]:
        return self._traditions.get(tradition_id)

    def get_all_traditions(self, active_only: bool = True) -> list[CulturalTradition]:
        if not active_only:
            return list(self._traditions.values())
        return [t for t in self._traditions.values() if t.is_active]

    def transmit_intergenerational(
        self,
        tradition_id: str,
        mentor_uid: str | HumanID,
        apprentice_uid: str | HumanID,
        teaching_quality: float = 0.8,
        tick: int = 0,
    ) -> bool:
        """Pass tradition from elder/mentor to younger apprentice."""
        trad = self.get_tradition(tradition_id)
        if not trad or str(mentor_uid) not in trad.adopters:
            return False

        if teaching_quality >= 0.40:
            trad.practice(str(apprentice_uid), tick)
            return True
        return False

    def diffuse_via_imitation(
        self,
        tradition_id: str,
        observer_uid: str | HumanID,
        observed_success: float,
        tick: int = 0,
    ) -> bool:
        """Adopt practice through observational imitation if proven beneficial."""
        trad = self.get_tradition(tradition_id)
        if not trad:
            return False

        # Adoption threshold depends on utility and demonstrated results
        if observed_success * trad.utility_score >= 0.45:
            trad.practice(str(observer_uid), tick)
            return True
        return False

    def decay_unpracticed_traditions(self, current_tick: int, dormancy_limit_ticks: int = 4000) -> list[str]:
        """Flag traditions that haven't been practiced as obsolete or dormant."""
        dormant_ids: list[str] = []
        for t in self._traditions.values():
            if t.is_active and (current_tick - t.last_practiced_tick) > dormancy_limit_ticks:
                t.is_active = False
                dormant_ids.append(t.tradition_id)
        return dormant_ids
