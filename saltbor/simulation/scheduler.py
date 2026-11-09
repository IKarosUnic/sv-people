"""Simulation scheduler — manages agent activation and execution order.

Provides deterministic tick sequencing and randomizes agent execution order
to eliminate first-mover bias. Supports future active/dormant partitioning for scaling.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from saltbor.core.types import Tick
from saltbor.population.human import SyntheticHuman
from saltbor.population.registry import PopulationRegistry


class SimulationScheduler:
    """Orchestrates agent updates for each discrete simulation tick."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self._rng = rng or np.random.default_rng()

    def get_execution_order(
        self,
        population: PopulationRegistry,
        tick: Tick,
    ) -> list[SyntheticHuman]:
        """Return agents in randomized execution order for the tick.

        Randomizing order prevents systematic biases where agent #1 always
        acts before agent #20 in shared locations.
        """
        humans = population.get_all()
        # In-place shuffle copy
        shuffled = list(humans)
        self._rng.shuffle(shuffled)
        return shuffled
