"""
Territorial Cognition and Epistemic Spatial Knowledge for Saltbor (Phase 0.8).

Integrates real Salvadoran geography into individual synthetic human minds:
- Strict rejection of geographic omniscience: knowledge is acquired empirically or socially
- Epistemic spatial belief states:
  - UNKNOWN
  - HEARD_RUMOR (low confidence, unverified coordinates)
  - OBSERVED (sighted directly)
  - REMEMBERED (in memory, subject to decay)
  - VERIFIED_CONFIRMED (personally visited and confirmed in person)
  - DISPROVED (counter-evidence found upon visiting location)
- Social transmission of spatial recommendations, rumors, and directions
- Rumor debunking and epistemic belief revision upon personal exploration
- Integration with CognitiveBrainArchitecture's Spatial/Parietal and Frontal executive systems.
"""

from __future__ import annotations
import dataclasses
from enum import Enum
import logging
from typing import Any, Optional

from saltbor.world.geographic.establishments import EstablishmentDirectory
from saltbor.world.geographic.models import RealPlace
from saltbor.world.geographic.spatial_index import haversine_distance_m

logger = logging.getLogger(__name__)


class EpistemicSpatialStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    HEARD_RUMOR = "HEARD_RUMOR"
    OBSERVED = "OBSERVED"
    REMEMBERED = "REMEMBERED"
    VERIFIED_CONFIRMED = "VERIFIED_CONFIRMED"
    DISPROVED = "DISPROVED"


@dataclasses.dataclass
class TerritorialBelief:
    """An individual's subjective cognitive belief about a place or route."""
    place_id: str
    name: str
    perceived_lat: float
    perceived_lon: float
    perceived_category: str
    perceived_district_id: str
    status: EpistemicSpatialStatus
    confidence: float                   # [0.0, 1.0]
    source_human_uid: Optional[str] = None
    acquired_tick: int = 0
    last_visited_tick: Optional[int] = None
    visit_count: int = 0
    verification_notes: str = ""
    is_fictional_or_false: bool = False

    def is_verified(self) -> bool:
        return self.status == EpistemicSpatialStatus.VERIFIED_CONFIRMED and self.confidence >= 0.85


class IndividualTerritorialCognition:
    """Individual territorial cognitive mind belonging to a single synthetic human."""

    def __init__(self, human_uid: str, home_district_id: str = "dist_san_salvador") -> None:
        self.human_uid = str(human_uid)
        self.home_district_id = home_district_id
        # Map place_id -> TerritorialBelief
        self._beliefs: dict[str, TerritorialBelief] = {}
        # Known routes: (origin_dist, dest_dist) -> familiarity score [0.0, 1.0]
        self._route_familiarity: dict[tuple[str, str], float] = {}

    def get_belief(self, place_id: str) -> Optional[TerritorialBelief]:
        return self._beliefs.get(place_id)

    def knows_place(self, place_id: str, min_confidence: float = 0.40) -> bool:
        b = self._beliefs.get(place_id)
        if not b or b.status in (EpistemicSpatialStatus.UNKNOWN, EpistemicSpatialStatus.DISPROVED):
            return False
        return b.confidence >= min_confidence

    def record_personal_visit(
        self,
        place: RealPlace,
        actual_lat: float,
        actual_lon: float,
        tick: int = 0,
    ) -> tuple[bool, str]:
        """Agent visits coordinates and evaluates reality against subjective beliefs."""
        # Check if place actually exists at these coordinates (< 50 meters)
        distance_err_m = haversine_distance_m(
            actual_lat, actual_lon,
            place.point.latitude, place.point.longitude,
        )

        existing_belief = self._beliefs.get(place.place_id)

        # 1. Place actually exists and is open
        if distance_err_m <= 100.0 and place.is_confirmed:
            visits = (existing_belief.visit_count + 1) if existing_belief else 1
            self._beliefs[place.place_id] = TerritorialBelief(
                place_id=place.place_id,
                name=place.name,
                perceived_lat=place.point.latitude,
                perceived_lon=place.point.longitude,
                perceived_category=place.sub_category,
                perceived_district_id=place.district_id,
                status=EpistemicSpatialStatus.VERIFIED_CONFIRMED,
                confidence=0.98,
                source_human_uid=self.human_uid,
                acquired_tick=existing_belief.acquired_tick if existing_belief else tick,
                last_visited_tick=tick,
                visit_count=visits,
                verification_notes="Comprobado personalmente en el lugar.",
            )
            return True, f"Verificado con éxito: {place.name}"

        # 2. Place does NOT exist or is closed/moved -> Debunk rumor!
        self._beliefs[place.place_id] = TerritorialBelief(
            place_id=place.place_id,
            name=place.name,
            perceived_lat=actual_lat,
            perceived_lon=actual_lon,
            perceived_category=place.sub_category,
            perceived_district_id=place.district_id,
            status=EpistemicSpatialStatus.DISPROVED,
            confidence=0.05,
            source_human_uid=existing_belief.source_human_uid if existing_belief else None,
            acquired_tick=existing_belief.acquired_tick if existing_belief else tick,
            last_visited_tick=tick,
            visit_count=(existing_belief.visit_count + 1) if existing_belief else 1,
            verification_notes=f"Lugar no encontrado en coordenadas ({actual_lat:.4f}, {actual_lon:.4f}) o establecimiento cerrado.",
            is_fictional_or_false=True,
        )
        return False, f"Desmentido: El lugar {place.name} no se encuentra en las coordenadas visitadas."

    def receive_social_recommendation(
        self,
        recommender_uid: str,
        place_id: str,
        name: str,
        lat: float,
        lon: float,
        category: str,
        district_id: str,
        recommender_trust: float = 0.70,
        is_rumor_or_inaccurate: bool = False,
        tick: int = 0,
    ) -> TerritorialBelief:
        """Receive information or directions about a place from a peer."""
        existing = self._beliefs.get(place_id)
        if existing and existing.status == EpistemicSpatialStatus.VERIFIED_CONFIRMED:
            # Personal verification always trumps social rumors
            return existing

        initial_confidence = max(0.2, min(0.75, recommender_trust * 0.8))
        belief = TerritorialBelief(
            place_id=place_id,
            name=name,
            perceived_lat=lat,
            perceived_lon=lon,
            perceived_category=category,
            perceived_district_id=district_id,
            status=EpistemicSpatialStatus.HEARD_RUMOR,
            confidence=initial_confidence,
            source_human_uid=recommender_uid,
            acquired_tick=tick,
            verification_notes=f"Recomendado por {recommender_uid}.",
            is_fictional_or_false=is_rumor_or_inaccurate,
        )
        self._beliefs[place_id] = belief
        return belief

    def apply_memory_decay(self, current_tick: int, decay_threshold_ticks: int = 500) -> None:
        """Memory decay for places not visited recently."""
        for b in self._beliefs.values():
            if b.status == EpistemicSpatialStatus.VERIFIED_CONFIRMED:
                last = b.last_visited_tick or b.acquired_tick
                elapsed = current_tick - last
                if elapsed > decay_threshold_ticks:
                    b.status = EpistemicSpatialStatus.REMEMBERED
                    b.confidence = max(0.50, b.confidence - 0.15)
