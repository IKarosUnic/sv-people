"""Offline routing over the ingested OpenStreetMap road network (§3.3).

The synthetic settlement uses a hand-built waypoint graph for its 16 functional
locations.  That is appropriate at the *local* scale, but it cannot answer
questions about the real territory: how far is the health centre along actual
streets, which side of the river is reachable, how long does a market trip take
on foot in the rainy season.

This module builds a routing graph directly from the normalized OSM geometry
produced by :mod:`saltbor.datasets.gis.pipeline` and answers shortest-path
queries with a Dijkstra search whose cost is travel *time* for the requested
mode.  Everything is offline, deterministic and dependency-free.

Modelling assumptions (documented, not measured):

* Node identity is coordinate identity at 1e-5° (~1.1 m) precision.  OSM ways
  that share a node therefore connect; near-misses do not.  This is why a
  route may fail inside a bbox that was clipped.
* Walking speed varies by road class; driving speed uses ``maxspeed`` when the
  extract provides it, otherwise a class default.
* One-way tags are honoured for driving and ignored for walking.
* Congestion, closures, signals and crossings are *not* present in the
  extract; they are modelled by other systems (misfortune/road closure) and are
  not part of this static network.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from saltbor.datasets.gis.pipeline import OSM_ATTRIBUTION

EARTH_RADIUS_M = 6_371_008.8

# Metres per second by road class (walking and driving defaults).
_WALK_SPEED_MS: dict[str, float] = {
    "motorway": 0.0,
    "trunk": 1.15,
    "primary": 1.30,
    "secondary": 1.30,
    "tertiary": 1.30,
    "residential": 1.25,
    "pedestrian": 1.20,
    "service": 1.15,
    "track": 1.00,
    "path": 1.05,
    "footway": 1.20,
    "steps": 0.75,
    "cycleway": 1.35,
}

_DRIVE_SPEED_KMH: dict[str, float] = {
    "motorway": 90.0,
    "trunk": 80.0,
    "primary": 60.0,
    "secondary": 50.0,
    "tertiary": 40.0,
    "residential": 25.0,
    "pedestrian": 5.0,
    "service": 15.0,
    "track": 15.0,
    "path": 5.0,
    "footway": 5.0,
    "steps": 2.0,
    "cycleway": 15.0,
}


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


@dataclass(frozen=True)
class RoadEdge:
    """One directed traversable segment."""

    source: int
    target: int
    length_m: float
    road_class: str
    name: str
    oneway: bool
    maxspeed_kmh: Optional[float] = None


@dataclass
class RouteResult:
    """Outcome of a routing query."""

    found: bool
    mode: str
    distance_m: float = 0.0
    duration_minutes: float = 0.0
    path: list[tuple[float, float]] = field(default_factory=list)
    edges_traversed: int = 0
    start_snap_m: float = 0.0
    end_snap_m: float = 0.0
    is_approximate: bool = False
    reason: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "found": self.found,
            "mode": self.mode,
            "distance_m": round(self.distance_m, 1),
            "distance_km": round(self.distance_m / 1000.0, 3),
            "duration_minutes": round(self.duration_minutes, 1),
            "edges_traversed": self.edges_traversed,
            "path": [[round(lon, 6), round(lat, 6)] for lat, lon in self.path],
            "start_snap_m": round(self.start_snap_m, 1),
            "end_snap_m": round(self.end_snap_m, 1),
            "is_approximate": self.is_approximate,
            "reason": self.reason,
            "provenance": dict(self.provenance),
            "attribution": OSM_ATTRIBUTION,
        }


class OSMRoadNetwork:
    """A routable graph built from normalized OSM road geometry."""

    NODE_PRECISION = 5  # decimal places ≈ 1.1 m

    def __init__(self) -> None:
        self._node_ids: dict[tuple[float, float], int] = {}
        self._node_coords: list[tuple[float, float]] = []  # (lat, lon)
        self.adjacency: dict[int, list[RoadEdge]] = {}
        self.edge_count = 0
        self.source_feature_count = 0
        self.bbox: Optional[tuple[float, float, float, float]] = None

    # -- construction -----------------------------------------------------
    def _node(self, lon: float, lat: float) -> int:
        key = (round(lat, self.NODE_PRECISION), round(lon, self.NODE_PRECISION))
        idx = self._node_ids.get(key)
        if idx is None:
            idx = len(self._node_coords)
            self._node_ids[key] = idx
            self._node_coords.append(key)
            self.adjacency[idx] = []
        return idx

    def add_geometry(
        self,
        coordinates: Iterable[Iterable[float]],
        road_class: str = "residential",
        name: str = "",
        oneway: bool = False,
        maxspeed_kmh: Optional[float] = None,
    ) -> None:
        """Add one road polyline to the graph."""
        points = [(float(c[1]), float(c[0])) for c in coordinates if len(c) >= 2]
        if len(points) < 2:
            return
        self.source_feature_count += 1
        previous: Optional[int] = None
        for lat, lon in points:
            node = self._node(lon, lat)
            if previous is not None and previous != node:
                a, b = self._node_coords[previous], self._node_coords[node]
                length = haversine_m(a[0], a[1], b[0], b[1])
                self.adjacency[previous].append(
                    RoadEdge(previous, node, length, road_class, name, oneway, maxspeed_kmh)
                )
                if not oneway:
                    self.adjacency[node].append(
                        RoadEdge(node, previous, length, road_class, name, oneway, maxspeed_kmh)
                    )
                self.edge_count += 1
            previous = node

    @classmethod
    def from_geography(
        cls,
        geography: Any,
        bbox: tuple[float, float, float, float],
        max_features: int = 20000,
    ) -> "OSMRoadNetwork":
        """Build a graph from the ingested geography database inside ``bbox``."""
        network = cls()
        network.bbox = bbox
        if geography is None or not getattr(geography, "available", False):
            return network
        road_like = geography.features_in_bbox(
            bbox, layer="roads", limit=max_features, include_geometry=True
        )
        footpaths = geography.features_in_bbox(
            bbox, layer="waterways", limit=0, include_geometry=False
        )
        del footpaths  # waterways are not routable; kept out deliberately
        for feature in road_like:
            geometry = feature.get("geometry") or {}
            gtype = geometry.get("type")
            coords = geometry.get("coordinates") or []
            if gtype == "LineString":
                lines = [coords]
            elif gtype == "MultiLineString":
                lines = coords
            else:
                continue
            for line in lines:
                network.add_geometry(
                    line,
                    road_class=feature.get("feature_class", "residential"),
                    name=feature.get("name", ""),
                )
        return network

    # -- query ------------------------------------------------------------
    def __len__(self) -> int:
        return len(self._node_coords)

    def nearest_node(self, lat: float, lon: float) -> tuple[Optional[int], float]:
        """Return the nearest graph node and its distance in metres."""
        best: Optional[int] = None
        best_d = float("inf")
        for idx, (nlat, nlon) in enumerate(self._node_coords):
            # Cheap degree filter before the trigonometric distance.
            if abs(nlat - lat) > 0.05 or abs(nlon - lon) > 0.05:
                continue
            d = haversine_m(lat, lon, nlat, nlon)
            if d < best_d:
                best_d = d
                best = idx
        if best is None:
            return None, float("inf")
        return best, best_d

    @staticmethod
    def _speed_ms(edge: RoadEdge, mode: str) -> float:
        if mode == "drive":
            if edge.maxspeed_kmh:
                return max(2.0, edge.maxspeed_kmh / 3.6)
            return max(2.0, _DRIVE_SPEED_KMH.get(edge.road_class, 25.0) / 3.6)
        return _WALK_SPEED_MS.get(edge.road_class, 1.2)

    def route(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        mode: str = "walk",
        max_snap_m: float = 400.0,
    ) -> RouteResult:
        """Shortest-time path between two WGS84 points.

        ``start`` and ``end`` are ``(lat, lon)``.  When either end is further
        than ``max_snap_m`` from the network the result is reported as
        approximate rather than silently returned as a real route.
        """
        provenance = {
            "network": "osm_ingested_roads",
            "nodes": len(self._node_coords),
            "edges": self.edge_count,
            "mode": mode,
            "assumption": "coordinate-identity topology, class-based speeds",
        }
        if not self._node_coords:
            return RouteResult(False, mode, reason="network_empty", provenance=provenance)

        start_node, start_snap = self.nearest_node(*start)
        end_node, end_snap = self.nearest_node(*end)
        if start_node is None or end_node is None:
            return RouteResult(
                False, mode, reason="no_node_near_query",
                start_snap_m=start_snap, end_snap_m=end_snap, provenance=provenance,
            )
        if start_snap > max_snap_m or end_snap > max_snap_m:
            return RouteResult(
                False,
                mode,
                reason="snap_distance_exceeded",
                start_snap_m=start_snap,
                end_snap_m=end_snap,
                is_approximate=True,
                provenance=provenance,
            )

        distances: dict[int, float] = {start_node: 0.0}
        previous: dict[int, tuple[int, RoadEdge]] = {}
        heap: list[tuple[float, int]] = [(0.0, start_node)]
        visited: set[int] = set()

        while heap:
            cost, node = heapq.heappop(heap)
            if node in visited:
                continue
            visited.add(node)
            if node == end_node:
                break
            for edge in self.adjacency.get(node, []):
                if edge.oneway and mode == "walk":
                    pass  # pedestrians ignore one-way restrictions
                elif edge.oneway and edge.target == node:
                    continue
                speed = self._speed_ms(edge, mode)
                if speed <= 0.0:
                    continue  # not traversable in this mode
                new_cost = cost + edge.length_m / speed
                if new_cost < distances.get(edge.target, float("inf")):
                    distances[edge.target] = new_cost
                    previous[edge.target] = (node, edge)
                    heapq.heappush(heap, (new_cost, edge.target))

        if end_node not in distances:
            return RouteResult(
                False,
                mode,
                reason="no_connected_path",
                start_snap_m=start_snap,
                end_snap_m=end_snap,
                provenance=provenance,
            )

        # Reconstruct the path.
        node_path: list[int] = [end_node]
        total_distance = 0.0
        edges_used = 0
        cursor = end_node
        while cursor != start_node and cursor in previous:
            parent, edge = previous[cursor]
            total_distance += edge.length_m
            edges_used += 1
            node_path.append(parent)
            cursor = parent
        node_path.reverse()

        path = [self._node_coords[n] for n in node_path]
        duration_min = distances[end_node] / 60.0
        return RouteResult(
            True,
            mode,
            distance_m=total_distance,
            duration_minutes=duration_min,
            path=path,
            edges_traversed=edges_used,
            start_snap_m=start_snap,
            end_snap_m=end_snap,
            is_approximate=(start_snap > 50.0 or end_snap > 50.0),
            provenance=provenance,
        )
