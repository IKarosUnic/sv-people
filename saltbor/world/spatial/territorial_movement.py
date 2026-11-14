"""
Territorial Movement and Physical Mobility Engine for Saltbor (Phase 0.8).

Models realistic physical travel across the Salvadoran road network:
- No instantaneous teleportation between coordinates
- Time expenditure, travel ticks, and energy consumption
- Vehicle modalities: Walking, Public Bus, Pickup truck, and Private vehicle.
"""

from __future__ import annotations
import dataclasses
import math
from typing import Any, Optional

from saltbor.world.geographic.engine import RealGeographicEngine


@dataclasses.dataclass
class MovementJourney:
    """State of an in-progress or completed journey between districts."""
    human_uid: str
    origin_district_id: str
    destination_district_id: str
    transport_mode: str
    total_distance_km: float
    total_transit_hours: float
    total_ticks_required: int
    current_tick_progress: int = 0
    is_completed: bool = False
    energy_expended: float = 0.0
    fare_paid_usd: float = 0.0
    segments_path: list[str] = dataclasses.field(default_factory=list)


class TerritorialMovementEngine:
    """Coordinates realistic displacement of synthetic humans across El Salvador."""

    # Ticks per hour in simulation (e.g., 4 ticks = 1 hour, i.e., 15 min per tick)
    TICKS_PER_HOUR: int = 4

    # Transit fares in USD
    FARES_USD: dict[str, float] = {
        "walking": 0.0,
        "bus": 0.35,      # Standard urban/interurban bus fare
        "pickup": 0.50,   # Rural pickup / palangana fare
        "car": 2.50,      # Fuel estimate
    }

    def __init__(self, geo_engine: RealGeographicEngine) -> None:
        self.geo = geo_engine
        self._active_journeys: dict[str, MovementJourney] = {}

    def start_journey(
        self,
        human_uid: str,
        origin_district_id: str,
        destination_district_id: str,
        transport_mode: str = "walking",
        is_rainy_season: bool = False,
        is_temporal: bool = False,
        environment_engine: Optional[Any] = None,
    ) -> Optional[MovementJourney]:
        """Initiate physical displacement along road network, modulating by dynamic weather."""
        if environment_engine is not None and hasattr(environment_engine, "current_state"):
            env_state = environment_engine.current_state
            if env_state is not None:
                if getattr(env_state, "condition", None) and env_state.condition.value in ["torrential_downpour", "moderate_rain"]:
                    is_rainy_season = True
                if getattr(env_state, "condition", None) and env_state.condition.value == "torrential_downpour":
                    is_temporal = True

        route = self.geo.calculate_route(
            origin_district_id=origin_district_id,
            destination_district_id=destination_district_id,
            transport_mode=transport_mode,
            is_rainy_season=is_rainy_season,
            is_temporal=is_temporal,
        )

        if not route["is_accessible"]:
            return None

        hours = route["transit_hours"]
        ticks = max(1, int(math.ceil(hours * self.TICKS_PER_HOUR)))

        # Energy expenditure: walking expends more calories/energy
        energy_rate = 0.15 if transport_mode == "walking" else 0.03
        total_energy = min(1.0, hours * energy_rate)

        journey = MovementJourney(
            human_uid=str(human_uid),
            origin_district_id=origin_district_id,
            destination_district_id=destination_district_id,
            transport_mode=transport_mode,
            total_distance_km=route["total_distance_km"],
            total_transit_hours=hours,
            total_ticks_required=ticks,
            current_tick_progress=0,
            is_completed=(ticks == 0),
            energy_expended=round(total_energy, 3),
            fare_paid_usd=self.FARES_USD.get(transport_mode, 0.0),
            segments_path=route["segments"],
        )
        self._active_journeys[str(human_uid)] = journey
        return journey

    def step_tick(self, human_uid: str) -> bool:
        """Advance displacement by one simulation tick. Returns True if completed."""
        uid = str(human_uid)
        journey = self._active_journeys.get(uid)
        if not journey or journey.is_completed:
            return True

        journey.current_tick_progress += 1
        if journey.current_tick_progress >= journey.total_ticks_required:
            journey.is_completed = True
            return True
        return False

    def get_journey(self, human_uid: str) -> Optional[MovementJourney]:
        return self._active_journeys.get(str(human_uid))
