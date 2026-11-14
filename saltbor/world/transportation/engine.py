"""TransportationEngine — Real-World Street & Road Navigation (Phase 1.8).

Eliminates teleportation: synthetic humans travel step-by-step along
actual OpenStreetMap road networks. Handles distance kinematics, speed
modulations (weather, slope, fatigue), dynamic road hazards/blockages,
rerouting, and arrival verification.
"""

from __future__ import annotations

import logging
import math
import uuid
from typing import Any, Dict, List, Optional, Tuple

from saltbor.core.types import ActivityType, Tick
from saltbor.events.types import EventType, SimulationEvent
from saltbor.world.geographic.osm_router import OSMRoadNetwork, RouteResult, haversine_m
from saltbor.world.transportation.models import (
    ActiveJourney,
    JourneyStatus,
    RoadBlockage,
    TravelMode,
)

logger = logging.getLogger(__name__)

# Base speeds in metres per second (1 tick = 900 seconds)
_BASE_SPEEDS_MS: Dict[TravelMode, float] = {
    TravelMode.WALK: 1.25,     # ~4.5 km/h -> ~1,125 m / 15-min tick
    TravelMode.BICYCLE: 3.50,  # ~12.6 km/h -> ~3,150 m / tick
    TravelMode.BUS: 5.50,      # ~19.8 km/h -> ~4,950 m / tick (with stops)
    TravelMode.VEHICLE: 7.20,  # ~26.0 km/h -> ~6,480 m / tick (urban streets)
}


class TransportationEngine:
    """Manages active journeys, road network routing, and dynamic street blockages."""

    def __init__(self, road_network: Optional[OSMRoadNetwork] = None) -> None:
        self.network = road_network or OSMRoadNetwork()
        self.active_journeys: Dict[str, ActiveJourney] = {}
        self.blockages: Dict[str, RoadBlockage] = {}
        self._completed_journeys_log: List[Dict[str, Any]] = []

    def register_blockage(
        self,
        cause: str,
        location_name: str,
        lat: float,
        lon: float,
        start_tick: int,
        duration_ticks: int = 16,
        radius_m: float = 80.0,
        severity: float = 0.90,
    ) -> RoadBlockage:
        """Register a new physical road blockage (flood, landslide, accident)."""
        b_id = f"blockage_{uuid.uuid4().hex[:6]}"
        blockage = RoadBlockage(
            blockage_id=b_id,
            cause=cause,
            location_name=location_name,
            lat=lat,
            lon=lon,
            radius_m=radius_m,
            start_tick=start_tick,
            duration_ticks=duration_ticks,
            severity=severity,
        )
        self.blockages[b_id] = blockage
        logger.info(
            "Registered road blockage %s (%s) at (%.4f, %.4f), radius=%.0fm, duration=%d ticks",
            b_id, cause, lat, lon, radius_m, duration_ticks,
        )
        return blockage

    def clear_blockage(self, blockage_id: str) -> bool:
        """Clear an existing road blockage."""
        if blockage_id in self.blockages:
            self.blockages[blockage_id].cleared = True
            logger.info("Cleared road blockage %s", blockage_id)
            return True
        return False

    def is_route_blocked(self, path: List[Tuple[float, float]], tick: int) -> Tuple[bool, Optional[RoadBlockage]]:
        """Check if any point along a coordinate path intersects an active blockage."""
        active_hazards = [b for b in self.blockages.values() if b.is_active_at(tick)]
        if not active_hazards:
            return False, None

        for lat, lon in path:
            for hazard in active_hazards:
                if hazard.blocks_point(lat, lon):
                    return True, hazard
        return False, None

    def initiate_journey(
        self,
        human_uid: str,
        origin_id: str,
        dest_id: str,
        start_tick: Tick = 0,
        mode: TravelMode = TravelMode.WALK,
        purpose: str = "commute",
        origin_coords: Tuple[float, float] = (13.6978, -89.1915),
        dest_coords: Tuple[float, float] = (13.6980, -89.1925),
    ) -> ActiveJourney:
        """Convenience method to start a journey with default coordinates."""
        return self.plan_journey(
            human_uid=human_uid,
            origin_loc_id=origin_id,
            destination_loc_id=dest_id,
            origin_coords=origin_coords,
            destination_coords=dest_coords,
            current_tick=start_tick,
            mode=mode,
            purpose=purpose,
        )

    def plan_journey(
        self,
        human_uid: str,
        origin_loc_id: str,
        destination_loc_id: str,
        origin_coords: Tuple[float, float],
        destination_coords: Tuple[float, float],
        current_tick: Tick,
        mode: TravelMode = TravelMode.WALK,
        purpose: str = "commute",
    ) -> ActiveJourney:
        """Calculate and initiate a physical journey between two locations."""
        # 1. Check if origin and destination are essentially the same
        dist_direct = haversine_m(origin_coords[0], origin_coords[1], destination_coords[0], destination_coords[1])
        if dist_direct < 15.0 or origin_loc_id == destination_loc_id:
            # Immediate zero-distance journey
            j_id = f"j_{uuid.uuid4().hex[:8]}"
            return ActiveJourney(
                journey_id=j_id,
                human_uid=human_uid,
                origin_location_id=origin_loc_id,
                destination_location_id=destination_loc_id,
                origin_coords=origin_coords,
                destination_coords=destination_coords,
                mode=mode,
                path_coords=[origin_coords, destination_coords],
                total_distance_m=dist_direct,
                traversed_distance_m=dist_direct,
                current_coords=destination_coords,
                departure_tick=current_tick,
                estimated_arrival_tick=current_tick,
                status=JourneyStatus.ARRIVED,
                purpose=purpose,
            )

        # 2. Compute route via OSMRoadNetwork
        routing_mode = "drive" if mode in (TravelMode.BUS, TravelMode.VEHICLE) else "walk"
        route_res = self.network.route(
            start=origin_coords,
            end=destination_coords,
            mode=routing_mode,
            max_snap_m=600.0,
        )

        path: List[Tuple[float, float]] = []
        total_dist = 0.0

        if route_res.found and len(route_res.path) >= 2:
            path = list(route_res.path)
            total_dist = route_res.distance_m
        else:
            # Fallback: Great-circle direct waypoint corridor (interpolated)
            steps = max(2, int(dist_direct / 100.0))
            path = [
                (
                    origin_coords[0] + (destination_coords[0] - origin_coords[0]) * (i / steps),
                    origin_coords[1] + (destination_coords[1] - origin_coords[1]) * (i / steps),
                )
                for i in range(steps + 1)
            ]
            total_dist = dist_direct

        # 3. Check for road blockages along the planned route
        blocked, hazard = self.is_route_blocked(path, current_tick)
        if blocked and hazard:
            logger.warning("Journey from %s to %s blocked by %s at start", origin_loc_id, destination_loc_id, hazard.cause)
            j_id = f"j_{uuid.uuid4().hex[:8]}"
            journey = ActiveJourney(
                journey_id=j_id,
                human_uid=human_uid,
                origin_location_id=origin_loc_id,
                destination_location_id=destination_loc_id,
                origin_coords=origin_coords,
                destination_coords=destination_coords,
                mode=mode,
                path_coords=path,
                total_distance_m=total_dist,
                traversed_distance_m=0.0,
                current_coords=origin_coords,
                departure_tick=current_tick,
                estimated_arrival_tick=current_tick + 10,
                status=JourneyStatus.BLOCKED,
                purpose=purpose,
                blocked_reason=f"Vía bloqueada por {hazard.cause} en {hazard.location_name}",
            )
            self.active_journeys[human_uid] = journey
            return journey

        # 4. Compute expected travel time
        base_speed = _BASE_SPEEDS_MS.get(mode, 1.25)
        dist_per_tick = base_speed * 900.0  # meters per 15-min tick
        estimated_ticks = max(1, int(math.ceil(total_dist / dist_per_tick)))

        j_id = f"j_{uuid.uuid4().hex[:8]}"
        journey = ActiveJourney(
            journey_id=j_id,
            human_uid=human_uid,
            origin_location_id=origin_loc_id,
            destination_location_id=destination_loc_id,
            origin_coords=origin_coords,
            destination_coords=destination_coords,
            mode=mode,
            path_coords=path,
            total_distance_m=total_dist,
            traversed_distance_m=0.0,
            current_coords=origin_coords,
            departure_tick=current_tick,
            estimated_arrival_tick=current_tick + estimated_ticks,
            status=JourneyStatus.IN_PROGRESS,
            purpose=purpose,
            edges_traversed=route_res.edges_traversed,
        )
        self.active_journeys[human_uid] = journey
        return journey

    def calculate_weather_speed_multiplier(self, weather_rain: float, mode: TravelMode = TravelMode.WALK) -> float:
        """Return speed attenuation multiplier based on rainfall intensity."""
        if weather_rain > 5.0:
            return 0.65 if mode == TravelMode.WALK else 0.75
        elif weather_rain > 0.5:
            return 0.85
        return 1.0

    def _apply_weather_penalty(self, nominal_speed: float, weather_rain: float, mode: TravelMode = TravelMode.WALK) -> float:
        """Apply rain attenuation to nominal speed."""
        return nominal_speed * self.calculate_weather_speed_multiplier(weather_rain, mode)

    def step(
        self,
        current_tick: Tick,
        population_registry: Any,
        weather_rain: float = 0.0,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> List[ActiveJourney]:
        """Advance all active journeys by one simulation tick."""
        arrived_journeys: List[ActiveJourney] = []
        finished_uids: List[str] = []

        # Cleanup expired blockages
        for b_id, b in list(self.blockages.items()):
            if not b.cleared and (current_tick >= b.start_tick + b.duration_ticks):
                b.cleared = True
                logger.info("Blockage %s cleared naturally at tick %d", b_id, current_tick)

        for human_uid, journey in list(self.active_journeys.items()):
            if journey.status in (JourneyStatus.ARRIVED, JourneyStatus.CANCELLED):
                finished_uids.append(human_uid)
                continue

            h_uuid = uuid.UUID(human_uid) if isinstance(human_uid, str) else human_uid
            human = population_registry.get_optional(h_uuid) if hasattr(population_registry, "get_optional") else None
            if human is None:
                # Agent no longer in registry
                finished_uids.append(human_uid)
                continue

            # Check if current road segment is blocked ahead
            blocked, hazard = self.is_route_blocked(journey.path_coords[journey.current_segment_idx:], current_tick)
            if blocked and hazard:
                journey.status = JourneyStatus.BLOCKED
                journey.delay_ticks += 1
                journey.blocked_reason = f"Obstáculo: {hazard.cause} en {hazard.location_name}"

                if event_bus:
                    event_bus.emit(
                        SimulationEvent(
                            event_type=EventType.ROAD_BLOCKED,
                            tick=current_tick,
                            source_human_id=human.uid,
                            location_id=journey.origin_location_id,
                            data={
                                "journey_id": journey.journey_id,
                                "hazard_cause": hazard.cause,
                                "hazard_location": hazard.location_name,
                                "human_name": human.name,
                            },
                            importance=0.60,
                        )
                    )

                # Attempt reroute if possible
                if journey.reroute_count < 2:
                    journey.reroute_count += 1
                    routing_mode = "drive" if journey.mode in (TravelMode.BUS, TravelMode.VEHICLE) else "walk"
                    alt_res = self.network.route(
                        start=journey.current_coords,
                        end=journey.destination_coords,
                        mode=routing_mode,
                    )
                    # Check if alt route avoids hazard
                    if alt_res.found and len(alt_res.path) >= 2:
                        alt_blocked, _ = self.is_route_blocked(alt_res.path, current_tick)
                        if not alt_blocked:
                            journey.path_coords = alt_res.path
                            journey.current_segment_idx = 0
                            journey.total_distance_m = journey.traversed_distance_m + alt_res.distance_m
                            journey.status = JourneyStatus.REROUTED
                            journey.blocked_reason = None
                            logger.info("Human %s rerouted around %s successfully", human.name, hazard.cause)
                            continue

                # If cannot reroute after 3 ticks of delay, cancel and turn back
                if journey.delay_ticks >= 3:
                    journey.status = JourneyStatus.CANCELLED
                    journey.blocked_reason = f"Viaje cancelado por bloqueo intransitable: {hazard.cause}"
                    # Return human to origin
                    human.physical_state.current_location_id = journey.origin_location_id
                    human.physical_state.current_activity = ActivityType.REST
                    human.physical_state.activity_ticks_remaining = 1
                    finished_uids.append(human_uid)
                    if event_bus:
                        event_bus.emit(
                            SimulationEvent(
                                event_type=EventType.JOURNEY_CANCELLED,
                                tick=current_tick,
                                source_human_id=human.uid,
                                location_id=journey.origin_location_id,
                                data={
                                    "journey_id": journey.journey_id,
                                    "reason": journey.blocked_reason,
                                },
                                importance=0.65,
                            )
                        )
                continue

            # Calculate actual kinematic speed for this tick
            base_speed = _BASE_SPEEDS_MS.get(journey.mode, 1.25)

            # Weather modulation: rain reduces travel speed
            weather_mult = 1.0
            if weather_rain > 5.0:
                # Heavy tropical downpour in El Salvador
                weather_mult = 0.65 if journey.mode == TravelMode.WALK else 0.75
            elif weather_rain > 0.5:
                # Moderate rain
                weather_mult = 0.85

            # Physical condition modulation: fatigue or illness slows agent
            condition_mult = 1.0
            if hasattr(human, "physical_state"):
                energy = getattr(human.physical_state, "energy", 1.0)
                if energy < 0.25:
                    condition_mult *= 0.70
                if getattr(human.physical_state, "health", 1.0) < 0.40:
                    condition_mult *= 0.65

            effective_speed_ms = base_speed * weather_mult * condition_mult
            distance_advance_m = effective_speed_ms * 900.0  # 15 minutes tick

            journey.traversed_distance_m += distance_advance_m

            # Interpolate position along polyline
            journey.current_coords = self._interpolate_coords(
                journey.path_coords, journey.progress_ratio
            )

            # Keep human's physical state in travel mode
            human.physical_state.current_activity = ActivityType.TRAVEL
            human.physical_state.activity_ticks_remaining = 1

            # Check for arrival
            if journey.traversed_distance_m >= journey.total_distance_m:
                journey.traversed_distance_m = journey.total_distance_m
                journey.current_coords = journey.destination_coords
                journey.status = JourneyStatus.ARRIVED

                # Update human's actual physical location
                human.physical_state.current_location_id = journey.destination_location_id
                human.physical_state.current_activity = None
                human.physical_state.activity_ticks_remaining = 0

                arrived_journeys.append(journey)
                finished_uids.append(human_uid)
                self._completed_journeys_log.append(journey.to_dict())

                if event_bus:
                    event_bus.emit(
                        SimulationEvent(
                            event_type=EventType.ARRIVED_AT_LOCATION,
                            tick=current_tick,
                            source_human_id=human.uid,
                            location_id=journey.destination_location_id,
                            data={
                                "from": journey.origin_location_id,
                                "to": journey.destination_location_id,
                                "distance_m": round(journey.total_distance_m, 1),
                                "mode": journey.mode.value,
                                "purpose": journey.purpose,
                            },
                            importance=0.25,
                        )
                    )

        # Remove finished journeys from active tracking
        for uid_str in finished_uids:
            self.active_journeys.pop(uid_str, None)

        return arrived_journeys

    def _interpolate_coords(
        self, path: List[Tuple[float, float]], ratio: float
    ) -> Tuple[float, float]:
        """Interpolate (lat, lon) coordinates along a piecewise polyline."""
        if not path:
            return (0.0, 0.0)
        if len(path) == 1 or ratio <= 0.0:
            return path[0]
        if ratio >= 1.0:
            return path[-1]

        # Calculate cumulative distances between vertices
        segment_lengths: List[float] = []
        total_len = 0.0
        for i in range(len(path) - 1):
            seg_len = haversine_m(path[i][0], path[i][1], path[i + 1][0], path[i + 1][1])
            segment_lengths.append(seg_len)
            total_len += seg_len

        if total_len <= 0.0:
            return path[0]

        target_dist = total_len * ratio
        accum = 0.0
        for i, seg_len in enumerate(segment_lengths):
            if accum + seg_len >= target_dist:
                seg_ratio = (target_dist - accum) / max(0.001, seg_len)
                lat = path[i][0] + (path[i + 1][0] - path[i][0]) * seg_ratio
                lon = path[i][1] + (path[i + 1][1] - path[i][1]) * seg_ratio
                return (round(lat, 6), round(lon, 6))
            accum += seg_len

        return path[-1]

    def get_active_journeys_summary(self) -> List[Dict[str, Any]]:
        """Return serialized summaries of all active journeys for UI telemetry."""
        return [j.to_dict() for j in self.active_journeys.values()]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for checkpointing."""
        return {
            "active_journeys": {uid: j.to_dict() for uid, j in self.active_journeys.items()},
            "blockages": {
                b_id: {
                    "blockage_id": b.blockage_id,
                    "cause": b.cause,
                    "location_name": b.location_name,
                    "lat": b.lat,
                    "lon": b.lon,
                    "radius_m": b.radius_m,
                    "start_tick": b.start_tick,
                    "duration_ticks": b.duration_ticks,
                    "cleared": b.cleared,
                }
                for b_id, b in self.blockages.items()
            },
            "completed_count": len(self._completed_journeys_log),
        }

    def load_dict(self, data: Dict[str, Any]) -> None:
        """Restore state from checkpoint dictionary."""
        if not data:
            return
        self.blockages.clear()
        for b_id, b_dict in data.get("blockages", {}).items():
            self.blockages[b_id] = RoadBlockage(
                blockage_id=b_dict["blockage_id"],
                cause=b_dict["cause"],
                location_name=b_dict["location_name"],
                lat=b_dict["lat"],
                lon=b_dict["lon"],
                radius_m=b_dict.get("radius_m", 80.0),
                start_tick=b_dict.get("start_tick", 0),
                duration_ticks=b_dict.get("duration_ticks", 16),
                cleared=b_dict.get("cleared", False),
            )
