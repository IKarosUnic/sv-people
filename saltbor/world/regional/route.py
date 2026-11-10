"""Regional trade routes: distances, transit durations, terrain friction, and hazards."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from saltbor.core.types import Tick


@dataclass
class RegionalTradeRoute:
    """A connecting trade corridor between two regional settlements."""

    route_id: str
    source_settlement_id: str
    target_settlement_id: str
    distance_km: float
    difficulty_multiplier: float = 1.0  # 1.0 flat road, 1.8 mountain pass, 1.4 river valley
    toll_fee: float = 0.0
    hazard_risk: float = 0.05           # Probability per journey of delay or cargo spoilage

    # Speed calculation: base walking speed with pack animals ~ 3.5 km/h = ~0.875 km per 15-min tick
    km_per_tick_base: float = 0.875

    @property
    def transit_ticks(self) -> int:
        """Estimated ticks to traverse this route in one direction."""
        effective_km_per_tick = self.km_per_tick_base / max(0.2, self.difficulty_multiplier)
        return max(4, int(math.ceil(self.distance_km / effective_km_per_tick)))
