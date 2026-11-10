"""Spatial encounter detection and contextual interaction initiation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from saltbor.core.types import HumanID, Tick
from saltbor.world.spatial.movement import AgentSpatialState


@dataclass
class EncounterEvent:
    """An encounter between two individuals passing in close spatial proximity."""

    agent_a_uid: HumanID
    agent_b_uid: HumanID
    distance_meters: float
    tick: Tick
    interaction_triggered: bool = False


class EncounterDetector:
    """Detects proximity encounters and evaluates whether casual interactions occur."""

    def __init__(self, encounter_radius: float = 4.0) -> None:
        self.encounter_radius = encounter_radius
        self._recent_encounters: dict[tuple[HumanID, HumanID], Tick] = {}

    def _pair_key(self, a: HumanID, b: HumanID) -> tuple[HumanID, HumanID]:
        return (a, b) if a <= b else (b, a)

    def detect_encounters(
        self,
        agents: list[AgentSpatialState],
        current_tick: Tick,
        cooldown_ticks: int = 16,
    ) -> list[EncounterEvent]:
        """Detect agent pairs within encounter_radius, filtering out recent repeats."""
        encounters: list[EncounterEvent] = []
        n = len(agents)

        for i in range(n):
            a = agents[i]
            for j in range(i + 1, n):
                b = agents[j]
                dist = math.hypot(a.x - b.x, a.y - b.y)
                if dist <= self.encounter_radius:
                    key = self._pair_key(a.human_uid, b.human_uid)
                    last_tick = self._recent_encounters.get(key, -999)
                    if current_tick - last_tick >= cooldown_ticks:
                        self._recent_encounters[key] = current_tick
                        encounters.append(
                            EncounterEvent(
                                agent_a_uid=a.human_uid,
                                agent_b_uid=b.human_uid,
                                distance_meters=round(dist, 2),
                                tick=current_tick,
                            )
                        )

        return encounters

    def should_initiate_interaction(
        self,
        familiarity: float,
        affinity: float,
        extraversion: float,
        is_agent_hurrying: bool = False,
    ) -> bool:
        """Evaluate if an encounter produces a casual interaction (e.g. greeting or chat)."""
        if is_agent_hurrying:
            return False
        # Probabilistic threshold: higher familiarity & extraversion increase chance
        p = 0.20 + 0.35 * familiarity + 0.25 * affinity + 0.20 * extraversion
        return p >= 0.50
