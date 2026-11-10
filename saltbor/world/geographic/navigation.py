"""
Territorial Navigation and Pathfinding Engine for Saltbor (Phase 0.8).

Implements realistic multimodal routing along El Salvador's verified road network:
- Paved highways (CA-1, CA-2, CA-4, CA-12), secondary asphalt, cobblestones, and rural dirt roads
- Natural obstacle recognition: impassable volcanic craters, deep calderas, and river barriers
- River crossings strictly constrained to authentic bridges (Puente Cuscatlán, Puente de Oro, Puente Colima)
- Environmental friction: rainy season degradation, mud on dirt roads (-60% speed), landslides at Los Chorros, and temporal flooding
- Dynamic obstacle bypass and alternative route recalculation.
"""

from __future__ import annotations
import heapq
import math
from typing import Any, Optional

from saltbor.datasets.salvadoran.territory_data import (
    SALVADORAN_DISTRICTS_P8,
    SALVADORAN_PHYSICAL_FEATURES_P8,
    SALVADORAN_ROAD_NETWORK_P8,
    PhysicalFeatureData,
    RoadSegmentData,
)
from saltbor.world.geographic.spatial_index import haversine_distance_km


class TerritorialNavigationEngine:
    """Graph-based navigation engine constrained by Salvadoran terrain and real road network."""

    # Baseline speeds in km/h under optimal dry conditions
    BASE_SPEEDS_KMH: dict[str, dict[str, float]] = {
        "walking": {
            "paved_highway": 5.0,
            "secondary_asphalt": 4.8,
            "cobblestone": 4.2,
            "unpaved_dirt_road": 3.8,
        },
        "bus": {
            "paved_highway": 55.0,
            "secondary_asphalt": 38.0,
            "cobblestone": 20.0,
            "unpaved_dirt_road": 14.0,
        },
        "pickup": {
            "paved_highway": 60.0,
            "secondary_asphalt": 45.0,
            "cobblestone": 25.0,
            "unpaved_dirt_road": 20.0,
        },
        "car": {
            "paved_highway": 75.0,
            "secondary_asphalt": 50.0,
            "cobblestone": 22.0,
            "unpaved_dirt_road": 12.0,
        },
    }

    def __init__(self, load_defaults: bool = True) -> None:
        self._adj: dict[str, list[RoadSegmentData]] = {}
        self._segments: dict[str, RoadSegmentData] = {}
        self._obstacles: dict[str, PhysicalFeatureData] = {}
        self._dynamic_blocked_segments: set[str] = set()

        if load_defaults:
            for feat in SALVADORAN_PHYSICAL_FEATURES_P8.values():
                if feat.is_impassable_obstacle:
                    self._obstacles[feat.feature_id] = feat

            for seg in SALVADORAN_ROAD_NETWORK_P8:
                self.add_road_segment(seg)

    def add_road_segment(self, seg: RoadSegmentData, bi_directional: bool = True) -> None:
        """Register a road segment in the network graph."""
        self._segments[seg.segment_id] = seg
        if seg.from_district_id not in self._adj:
            self._adj[seg.from_district_id] = []
        self._adj[seg.from_district_id].append(seg)

        if bi_directional:
            rev_seg = RoadSegmentData(
                segment_id=f"{seg.segment_id}_rev",
                name=seg.name,
                from_district_id=seg.to_district_id,
                to_district_id=seg.from_district_id,
                road_type=seg.road_type,
                distance_km=seg.distance_km,
                base_speed_kmh=seg.base_speed_kmh,
                is_bridge=seg.is_bridge,
                bridge_name=seg.bridge_name,
                crosses_river_id=seg.crosses_river_id,
                flooding_vulnerability=seg.flooding_vulnerability,
                slope_gradient=seg.slope_gradient,
            )
            if seg.to_district_id not in self._adj:
                self._adj[seg.to_district_id] = []
            self._adj[seg.to_district_id].append(rev_seg)

    def block_segment(self, segment_id: str) -> None:
        """Mark a road segment as blocked (e.g. by landslide, derrumbe, or flood)."""
        self._dynamic_blocked_segments.add(segment_id)
        self._dynamic_blocked_segments.add(f"{segment_id}_rev")

    def unblock_segment(self, segment_id: str) -> None:
        """Clear block on a road segment."""
        self._dynamic_blocked_segments.discard(segment_id)
        self._dynamic_blocked_segments.discard(f"{segment_id}_rev")

    def clear_all_blocks(self) -> None:
        self._dynamic_blocked_segments.clear()

    def is_obstacle_in_path(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        tolerance_km: float = 3.0,
    ) -> list[str]:
        """Check if straight-line vector collides with an impassable physical obstacle."""
        collided: list[str] = []
        for obs_id, obs in self._obstacles.items():
            # Check proximity to obstacle centroid
            mid_lat = (lat1 + lat2) / 2.0
            mid_lon = (lon1 + lon2) / 2.0
            d_to_mid = haversine_distance_km(mid_lat, mid_lon, obs.latitude, obs.longitude)
            d_direct = haversine_distance_km(lat1, lon1, lat2, lon2)
            d1 = haversine_distance_km(lat1, lon1, obs.latitude, obs.longitude)
            d2 = haversine_distance_km(lat2, lon2, obs.latitude, obs.longitude)

            # Triangular inequality distance check to line segment
            if (d1 + d2) < (d_direct + tolerance_km):
                collided.append(obs.name)
        return collided

    def calculate_segment_friction(
        self,
        seg: RoadSegmentData,
        transport_mode: str = "walking",
        is_rainy_season: bool = False,
        is_temporal: bool = False,
    ) -> float:
        """Calculate effective traversal duration in hours for a single road segment."""
        # 1. Base speed lookup
        mode_speeds = self.BASE_SPEEDS_KMH.get(transport_mode, self.BASE_SPEEDS_KMH["walking"])
        speed = mode_speeds.get(seg.road_type, mode_speeds["paved_highway"])

        # 2. Road surface weather penalty
        if is_temporal:
            if seg.road_type == "unpaved_dirt_road":
                speed *= 0.35  # Severe mud, 65% reduction
            elif seg.road_type == "cobblestone":
                speed *= 0.60
            else:
                speed *= 0.75
        elif is_rainy_season:
            if seg.road_type == "unpaved_dirt_road":
                speed *= 0.55  # Regular rain, 45% reduction
            elif seg.road_type == "cobblestone":
                speed *= 0.80
            else:
                speed *= 0.90

        # 3. Slope gradient penalty (steep volcanic / mountain grades)
        if seg.slope_gradient > 0.05:
            slope_factor = 1.0 + (seg.slope_gradient * 3.0)
            speed /= slope_factor

        # Guard against zero speed
        effective_speed = max(0.5, speed)
        return seg.distance_km / effective_speed

    def find_route(
        self,
        origin_district_id: str,
        destination_district_id: str,
        transport_mode: str = "walking",
        is_rainy_season: bool = False,
        is_temporal: bool = False,
        extra_blocked_segments: Optional[set[str]] = None,
    ) -> dict[str, Any]:
        """Compute optimal route via Dijkstra minimizing travel duration."""
        if origin_district_id == destination_district_id:
            return {
                "origin": origin_district_id,
                "destination": destination_district_id,
                "is_accessible": True,
                "total_distance_km": 0.0,
                "transit_hours": 0.0,
                "path_district_ids": [origin_district_id],
                "segments": [],
                "bridges_crossed": [],
                "warnings": [],
            }

        blocked = set(self._dynamic_blocked_segments)
        if extra_blocked_segments:
            blocked.update(extra_blocked_segments)

        # During temporales, highly vulnerable segments (>0.70) auto-block
        if is_temporal:
            for seg in self._segments.values():
                if seg.flooding_vulnerability >= 0.70:
                    blocked.add(seg.segment_id)
                    blocked.add(f"{seg.segment_id}_rev")

        # Dijkstra priority queue: (cumulative_hours, current_node, path, segments_used)
        pq: list[tuple[float, str, list[str], list[RoadSegmentData]]] = [
            (0.0, origin_district_id, [origin_district_id], [])
        ]
        visited: dict[str, float] = {}

        while pq:
            hours, curr, path, segs = heapq.heappop(pq)

            if curr in visited and visited[curr] <= hours:
                continue
            visited[curr] = hours

            if curr == destination_district_id:
                total_dist = sum(s.distance_km for s in segs)
                bridges = [s.bridge_name for s in segs if s.is_bridge and s.bridge_name]
                return {
                    "origin": origin_district_id,
                    "destination": destination_district_id,
                    "is_accessible": True,
                    "total_distance_km": round(total_dist, 2),
                    "transit_hours": round(hours, 3),
                    "path_district_ids": path,
                    "segments": [s.name for s in segs],
                    "bridges_crossed": bridges,
                    "transport_mode": transport_mode,
                    "warnings": (
                        ["Afectado por temporal tropical; se evitaron rutas con riesgo de deslave o inundación."]
                        if is_temporal else []
                    ),
                }

            for seg in self._adj.get(curr, []):
                if seg.segment_id in blocked:
                    continue
                neighbor = seg.to_district_id
                seg_hours = self.calculate_segment_friction(
                    seg,
                    transport_mode=transport_mode,
                    is_rainy_season=is_rainy_season,
                    is_temporal=is_temporal,
                )
                new_hours = hours + seg_hours

                if neighbor not in visited or new_hours < visited.get(neighbor, float("inf")):
                    heapq.heappush(
                        pq,
                        (new_hours, neighbor, path + [neighbor], segs + [seg]),
                    )

        # Disconnected fallback (e.g. all roads blocked)
        return {
            "origin": origin_district_id,
            "destination": destination_district_id,
            "is_accessible": False,
            "reason": "No walkable or vehicular road connects the requested districts (roads blocked or unlinked).",
            "total_distance_km": 0.0,
            "transit_hours": float("inf"),
            "path_district_ids": [],
            "segments": [],
            "bridges_crossed": [],
            "warnings": ["Rutas bloqueadas o cortadas."],
        }
