"""Transportation and Road Movement Models for SALTBOR (Phase 1.8).

Defines active journeys, travel modes, road blockages, and kinematics
along real-world OpenStreetMap road geometries in El Salvador.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TravelMode(str, Enum):
    """Modes of transportation available to synthetic humans."""
    WALK = "walk"
    BICYCLE = "bicycle"
    BUS = "bus"
    VEHICLE = "drive"


class JourneyStatus(str, Enum):
    """Status lifecycle of an active travel journey."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REROUTED = "rerouted"
    ARRIVED = "arrived"
    CANCELLED = "cancelled"


@dataclass
class RoadBlockage:
    """A physical obstruction on the road network (landslide, flood, accident)."""
    blockage_id: str
    cause: str  # e.g., 'inundacion_lluvia', 'derrumbe_cerro', 'accidente_transito'
    location_name: str
    lat: float
    lon: float
    radius_m: float = 80.0
    start_tick: int = 0
    duration_ticks: int = 16  # default 4 hours (16 * 15m)
    severity: float = 0.90   # 0.0 to 1.0 (impassability)
    cleared: bool = False

    def is_active_at(self, tick: int) -> bool:
        if self.cleared:
            return False
        return self.start_tick <= tick < (self.start_tick + self.duration_ticks)

    def blocks_point(self, lat: float, lon: float) -> bool:
        """Check if a coordinate point falls inside this blockage zone."""
        # Simple equirectangular distance approximation in meters
        dlat = (lat - self.lat) * 111_320.0
        dlon = (lon - self.lon) * (111_320.0 * math.cos(math.radians(self.lat)))
        dist = math.hypot(dlat, dlon)
        return dist <= self.radius_m

    @property
    def passable(self) -> bool:
        return self.severity < 0.85

    def to_dict(self) -> dict[str, Any]:
        return {
            "road_id": self.road_id,
            "cause": self.cause,
            "location_name": self.location_name,
            "lat": self.lat,
            "lon": self.lon,
            "radius_m": self.radius_m,
            "start_tick": self.start_tick,
            "duration_ticks": self.duration_ticks,
            "severity": self.severity,
            "passable": self.passable,
            "cleared": self.cleared,
        }


@dataclass
class ActiveJourney:
    """An individual synthetic human travelling tick-by-tick across the road network."""
    journey_id: str
    human_uid: str
    origin_location_id: str
    destination_location_id: str
    origin_coords: tuple[float, float]       # (lat, lon)
    destination_coords: tuple[float, float]  # (lat, lon)
    mode: TravelMode
    path_coords: list[tuple[float, float]]   # [(lat, lon), ...] from OSM router
    total_distance_m: float
    traversed_distance_m: float = 0.0
    current_coords: tuple[float, float] = (0.0, 0.0)
    current_segment_idx: int = 0
    departure_tick: int = 0
    estimated_arrival_tick: int = 0
    status: JourneyStatus = JourneyStatus.IN_PROGRESS
    purpose: str = "general_travel"
    delay_ticks: int = 0
    blocked_reason: Optional[str] = None
    reroute_count: int = 0
    edges_traversed: int = 0

    @property
    def progress_ratio(self) -> float:
        if self.total_distance_m <= 0.0:
            return 1.0
        return min(1.0, max(0.0, self.traversed_distance_m / self.total_distance_m))

    @property
    def remaining_distance_m(self) -> float:
        return max(0.0, self.total_distance_m - self.traversed_distance_m)

    def to_dict(self) -> dict[str, Any]:
        return {
            "journey_id": self.journey_id,
            "human_uid": self.human_uid,
            "origin_location_id": self.origin_location_id,
            "destination_location_id": self.destination_location_id,
            "origin_coords": [round(c, 6) for c in self.origin_coords],
            "destination_coords": [round(c, 6) for c in self.destination_coords],
            "current_coords": [round(c, 6) for c in self.current_coords],
            "mode": self.mode.value,
            "total_distance_m": round(self.total_distance_m, 1),
            "traversed_distance_m": round(self.traversed_distance_m, 1),
            "remaining_distance_m": round(self.remaining_distance_m, 1),
            "progress_ratio": round(self.progress_ratio, 3),
            "status": self.status.value,
            "purpose": self.purpose,
            "departure_tick": self.departure_tick,
            "estimated_arrival_tick": self.estimated_arrival_tick,
            "delay_ticks": self.delay_ticks,
            "blocked_reason": self.blocked_reason,
            "reroute_count": self.reroute_count,
            "path_points_count": len(self.path_coords),
        }

    @property
    def current_coordinate(self) -> Tuple[float, float]:
        return self.current_coords

    @property
    def polyline(self) -> List[Tuple[float, float]]:
        return self.path_coords

    @property
    def total_distance_km(self) -> float:
        return self.total_distance_m / 1000.0

    @property
    def start_tick(self) -> Tick:
        return self.departure_tick

    @property
    def effective_speed_kmh(self) -> float:
        base = 4.5 if self.mode == TravelMode.WALK else (15.0 if self.mode == TravelMode.BICYCLE else 22.0)
        if self.delay_ticks > 0:
            return max(1.0, base / (1.0 + self.delay_ticks * 0.1))
        return base

