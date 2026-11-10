"""Continuous 2D spatial movement, velocity steering, and obstacle avoidance."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from saltbor.core.types import Coordinate, HumanID


@dataclass
class AgentSpatialState:
    """Continuous physical position, orientation, velocity, and navigation path."""

    human_uid: HumanID
    x: float
    y: float
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    vx: float = 0.0
    vy: float = 0.0
    heading_rad: float = 0.0
    base_speed_mps: float = 1.4      # Standard adult walking speed (~1.4 m/s)
    current_speed_mps: float = 1.4
    waypoints_queue: list[Coordinate] = field(default_factory=list)
    is_moving: bool = False
    radius_meters: float = 0.4        # Personal physical space

    @property
    def position(self) -> Coordinate:
        return (self.x, self.y)

    def set_destination(self, target: Coordinate, waypoints: Optional[list[Coordinate]] = None) -> None:
        self.waypoints_queue = list(waypoints or [target])
        self.target_x, self.target_y = self.waypoints_queue[0]
        self.is_moving = True


class ContinuousMovementEngine:
    """Simulates continuous 2D steering, path following, and collision avoidance."""

    def __init__(self, avoidance_radius: float = 1.5) -> None:
        self.avoidance_radius = avoidance_radius

    def step_agent(
        self,
        agent: AgentSpatialState,
        dt_seconds: float,
        nearby_agents: list[AgentSpatialState],
        speed_multiplier: float = 1.0,
    ) -> bool:
        """Advance agent position by dt_seconds.

        Returns True if the agent reached its final destination.
        """
        if not agent.is_moving or agent.target_x is None or agent.target_y is None:
            agent.vx = 0.0
            agent.vy = 0.0
            return False

        # Desired velocity towards current waypoint
        dx = agent.target_x - agent.x
        dy = agent.target_y - agent.y
        dist = math.hypot(dx, dy)

        speed = agent.base_speed_mps * max(0.2, speed_multiplier)
        agent.current_speed_mps = speed
        step_distance = speed * dt_seconds

        # Waypoint arrival / snap check
        if dist <= step_distance or dist < 0.2:
            agent.x = agent.target_x
            agent.y = agent.target_y
            if agent.waypoints_queue:
                agent.waypoints_queue.pop(0)

            if agent.waypoints_queue:
                agent.target_x, agent.target_y = agent.waypoints_queue[0]
                return False
            else:
                # Reached final destination
                agent.vx = 0.0
                agent.vy = 0.0
                agent.is_moving = False
                agent.target_x = None
                agent.target_y = None
                return True

        target_vx = (dx / dist) * speed
        target_vy = (dy / dist) * speed

        # Collision avoidance: repulsive vector from nearby agents within avoidance radius
        repulse_x = 0.0
        repulse_y = 0.0
        for other in nearby_agents:
            if other.human_uid == agent.human_uid:
                continue
            ox = agent.x - other.x
            oy = agent.y - other.y
            d_other = math.hypot(ox, oy)
            if 0.001 < d_other < self.avoidance_radius:
                # Stronger repulsion as agents get closer
                force = (self.avoidance_radius - d_other) / self.avoidance_radius
                repulse_x += (ox / d_other) * force * speed * 0.8
                repulse_y += (oy / d_other) * force * speed * 0.8

        # Blend target velocity with repulsive avoidance
        combined_vx = target_vx + repulse_x
        combined_vy = target_vy + repulse_y
        comb_speed = math.hypot(combined_vx, combined_vy)
        if comb_speed > speed:
            combined_vx = (combined_vx / comb_speed) * speed
            combined_vy = (combined_vy / comb_speed) * speed

        agent.vx = combined_vx
        agent.vy = combined_vy
        agent.x += combined_vx * dt_seconds
        agent.y += combined_vy * dt_seconds

        if math.hypot(agent.vx, agent.vy) > 0.01:
            agent.heading_rad = math.atan2(agent.vy, agent.vx)

        return False
