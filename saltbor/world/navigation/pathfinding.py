"""Navigation graph and pathfinding for the Saltbor settlement.

Implements a topological graph of roads, paths, and location waypoints,
providing shortest-path routing (Dijkstra) and travel time estimation.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Optional

from saltbor.core.types import Coordinate, LocationID, Tick
from saltbor.world.geography.grid import Position, distance
from saltbor.world.locations.registry import LocationRegistry


@dataclass(frozen=True, slots=True)
class Waypoint:
    """A point on the navigation network."""

    node_id: str
    position: Position
    is_location: bool = False
    location_id: Optional[LocationID] = None


@dataclass
class NavigationGraph:
    """Waypoints and walkable connections across Saltbor."""

    _nodes: dict[str, Waypoint] = field(default_factory=dict)
    _adj: dict[str, list[tuple[str, float]]] = field(default_factory=dict)

    # Standard adult walking speed: 1.4 m/s (~5.0 km/h)
    DEFAULT_WALKING_SPEED_MPS: float = 1.4

    def add_node(self, node: Waypoint) -> None:
        """Add a waypoint node to the network."""
        self._nodes[node.node_id] = node
        if node.node_id not in self._adj:
            self._adj[node.node_id] = []

    def add_edge(self, u_id: str, v_id: str, bi_directional: bool = True) -> None:
        """Connect two existing nodes with a walkable path."""
        if u_id not in self._nodes or v_id not in self._nodes:
            raise KeyError(f"Both nodes must exist: {u_id}, {v_id}")

        dist = distance(self._nodes[u_id].position, self._nodes[v_id].position)
        self._adj[u_id].append((v_id, dist))
        if bi_directional:
            self._adj[v_id].append((u_id, dist))

    def find_nearest_node(self, pos: Position | Coordinate) -> str:
        """Find the node_id closest to the given spatial coordinate."""
        p = Position(pos[0], pos[1]) if isinstance(pos, tuple) else pos
        return min(
            self._nodes.keys(),
            key=lambda nid: distance(p, self._nodes[nid].position),
        )

    def shortest_path(self, start_node_id: str, goal_node_id: str) -> list[str]:
        """Compute the shortest path of node IDs using Dijkstra's algorithm."""
        if start_node_id not in self._nodes or goal_node_id not in self._nodes:
            return []

        if start_node_id == goal_node_id:
            return [start_node_id]

        dist: dict[str, float] = {start_node_id: 0.0}
        parent: dict[str, Optional[str]] = {start_node_id: None}
        pq: list[tuple[float, str]] = [(0.0, start_node_id)]
        visited: set[str] = set()

        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)

            if u == goal_node_id:
                break

            for v, weight in self._adj.get(u, []):
                new_d = d + weight
                if new_d < dist.get(v, float("inf")):
                    dist[v] = new_d
                    parent[v] = u
                    heapq.heappush(pq, (new_d, v))

        if goal_node_id not in parent:
            # Fallback: direct connection if graph is disconnected
            return [start_node_id, goal_node_id]

        # Reconstruct path
        path: list[str] = []
        curr: Optional[str] = goal_node_id
        while curr is not None:
            path.append(curr)
            curr = parent[curr]
        path.reverse()
        return path

    def find_route(
        self,
        from_coord: Coordinate | Position,
        to_coord: Coordinate | Position,
    ) -> list[Position]:
        """Return a sequence of Positions connecting two arbitrary points."""
        start_pos = Position(from_coord[0], from_coord[1]) if isinstance(from_coord, tuple) else from_coord
        goal_pos = Position(to_coord[0], to_coord[1]) if isinstance(to_coord, tuple) else to_coord

        start_node = self.find_nearest_node(start_pos)
        goal_node = self.find_nearest_node(goal_pos)

        node_ids = self.shortest_path(start_node, goal_node)
        route = [start_pos]
        for nid in node_ids:
            node_p = self._nodes[nid].position
            if not route or distance(route[-1], node_p) > 1.0:
                route.append(node_p)
        if not route or distance(route[-1], goal_pos) > 1.0:
            route.append(goal_pos)

        return route

    def travel_distance(
        self,
        from_coord: Coordinate | Position,
        to_coord: Coordinate | Position,
    ) -> float:
        """Calculate total walking distance in metres along the route."""
        route = self.find_route(from_coord, to_coord)
        if len(route) < 2:
            return 0.0
        return sum(distance(route[i], route[i + 1]) for i in range(len(route) - 1))

    def travel_time_ticks(
        self,
        from_coord: Coordinate | Position,
        to_coord: Coordinate | Position,
        tick_duration_minutes: int = 15,
        speed_mps: Optional[float] = None,
    ) -> Tick:
        """Estimate travel time in ticks (minimum 1 tick if moving between locations)."""
        dist_m = self.travel_distance(from_coord, to_coord)
        if dist_m < 5.0:
            return 0  # Already there

        speed = speed_mps or self.DEFAULT_WALKING_SPEED_MPS
        seconds = dist_m / speed
        minutes = seconds / 60.0
        ticks = math.ceil(minutes / tick_duration_minutes)
        return max(1, ticks)

    @classmethod
    def build_saltbor_graph(cls, registry: LocationRegistry) -> NavigationGraph:
        """Construct the road and path network connecting all Saltbor locations."""
        graph = cls()

        # 1. Road Intersections (Waypoints forming main street grid)
        intersections = {
            "cross_center": (250.0, 250.0),
            "cross_north": (250.0, 350.0),
            "cross_south": (250.0, 150.0),
            "cross_east": (350.0, 250.0),
            "cross_west": (150.0, 250.0),
            "cross_ne": (350.0, 350.0),
            "cross_nw": (150.0, 350.0),
            "cross_se": (350.0, 150.0),
            "cross_sw": (150.0, 150.0),
            "cross_far_north": (250.0, 420.0),
            "cross_far_south": (250.0, 80.0),
            "cross_far_east": (430.0, 250.0),
            "cross_far_west": (70.0, 250.0),
        }

        for nid, (x, y) in intersections.items():
            graph.add_node(Waypoint(node_id=nid, position=Position(x, y)))

        # 2. Main Street Arteries
        grid_edges = [
            ("cross_center", "cross_north"),
            ("cross_center", "cross_south"),
            ("cross_center", "cross_east"),
            ("cross_center", "cross_west"),
            ("cross_north", "cross_ne"),
            ("cross_north", "cross_nw"),
            ("cross_south", "cross_se"),
            ("cross_south", "cross_sw"),
            ("cross_east", "cross_ne"),
            ("cross_east", "cross_se"),
            ("cross_west", "cross_nw"),
            ("cross_west", "cross_sw"),
            ("cross_north", "cross_far_north"),
            ("cross_south", "cross_far_south"),
            ("cross_east", "cross_far_east"),
            ("cross_west", "cross_far_west"),
        ]

        for u, v in grid_edges:
            graph.add_edge(u, v)

        # 3. Add all registered locations and connect to nearest intersection
        for loc in registry.get_all():
            loc_nid = f"loc_{loc.location_id}"
            loc_pos = Position(loc.position[0], loc.position[1])
            graph.add_node(
                Waypoint(
                    node_id=loc_nid,
                    position=loc_pos,
                    is_location=True,
                    location_id=loc.location_id,
                )
            )
            # Find nearest road intersection
            nearest_int = min(
                intersections.keys(),
                key=lambda i_id: distance(loc_pos, Position(*intersections[i_id])),
            )
            graph.add_edge(loc_nid, nearest_int)

        return graph
