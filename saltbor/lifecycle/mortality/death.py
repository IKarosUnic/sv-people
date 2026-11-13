"""Mortality engine: hazard models, death events, inheritance, and historical continuity."""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Optional

import numpy as np

from saltbor.core.types import HumanID, Tick
from saltbor.events.bus import EventBus
from saltbor.events.types import EventType, SimulationEvent
from saltbor.lifecycle.family.household import HouseholdRegistry
from saltbor.lifecycle.genealogy.tree import GenealogicalGraph

if TYPE_CHECKING:
    from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


class MortalityEngine:
    """Evaluates biological hazard and executes persistent death and succession mechanics."""

    def __init__(
        self,
        base_makeham_hazard: float = 0.0005,  # Baseline annual accident hazard rate A
        gompertz_alpha: float = 0.00005,      # Gompertz initial mortality parameter B
        gompertz_gamma: float = 0.08,         # Gompertz rate of mortality increase per year C
        rng: Optional[np.random.Generator] = None,
    ) -> None:
        self.makeham = base_makeham_hazard
        self.alpha = gompertz_alpha
        self.gamma = gompertz_gamma
        self.rng = rng or np.random.default_rng()
        self._deceased_registry: set[HumanID] = set()

    def is_deceased(self, uid: HumanID) -> bool:
        return uid in self._deceased_registry

    def mark_deceased(self, uid: HumanID) -> None:
        """Record a death that was executed by the integrated life-course coordinator."""
        self._deceased_registry.add(uid)

    def calculate_mortality_hazard(
        self,
        human: SyntheticHuman,
        ticks_per_year: float = 35040.0,
        ticks_elapsed: int = 1,
    ) -> float:
        """Calculate probabilistic mortality hazard over elapsed ticks.

        Combines Gompertz-Makeham senescence with acute physical distress
        (critical health, severe starvation, or complete exhaustion).
        """
        age = float(human.demographics.age)
        # Gompertz-Makeham annual hazard rate: h(x) = A + B * exp(C * x)
        exp_arg = min(700.0, self.gamma * max(0.0, age - 20.0))
        annual_hazard = self.makeham + self.alpha * math.exp(exp_arg)

        # Scale annual hazard to the tick duration
        dt_years = ticks_elapsed / ticks_per_year
        base_hazard = 1.0 - math.exp(-annual_hazard * dt_years)

        # Acute physical vulnerability multipliers
        health = human.physical_state.health
        hunger = human.physical_state.hunger
        energy = human.physical_state.energy

        distress_factor = 1.0
        if health < 0.20:
            distress_factor += (0.20 - health) * 15.0  # Critical illness
        if hunger > 0.90:
            distress_factor += (hunger - 0.90) * 20.0  # Acute starvation
        if energy < 0.05:
            distress_factor += (0.05 - energy) * 5.0   # Extreme exhaustion

        total_hazard = min(0.95, base_hazard * distress_factor)
        return float(total_hazard)

    def check_mortality(
        self,
        human: SyntheticHuman,
        ticks_per_year: float = 35040.0,
        ticks_elapsed: int = 1,
    ) -> bool:
        """Evaluate whether mortality occurs during this step."""
        if self.is_deceased(human.uid):
            return False

        hazard = self.calculate_mortality_hazard(human, ticks_per_year, ticks_elapsed)
        if self.rng.random() < hazard:
            return True
        return False

    def process_death(
        self,
        human: SyntheticHuman,
        current_tick: Tick,
        genealogy: GenealogicalGraph,
        households: HouseholdRegistry,
        event_bus: EventBus,
    ) -> dict[str, any]:
        """Execute complete mortality sequence:

        1. Mark as deceased in memory and registries (preserves records!).
        2. Record death in genealogical graph.
        3. Process asset inheritance to surviving household members/kin.
        4. Reassign orphan dependents if necessary.
        5. Emit DEATH event for community/grief processing.
        """
        self._deceased_registry.add(human.uid)
        human.physical_state.health = 0.0
        human.physical_state.energy = 0.0

        # Update genealogy
        genealogy.record_death(human.uid, current_tick)

        # Process household inheritance and succession
        household = households.get_for_human(human.uid)
        inherited_distribution: dict[HumanID, float] = {}
        if household:
            personal_funds = human.physical_state.money
            inherited_distribution = household.process_succession_and_inheritance(
                deceased_uid=human.uid,
                personal_funds=personal_funds,
                genealogy=genealogy,
            )
            human.physical_state.money = 0.0

        logger.info("Death recorded for %s (age %d) at tick %d", human.name, human.demographics.age, current_tick)

        # Emit death event
        death_evt = SimulationEvent(
            event_type=EventType.DEATH,
            tick=current_tick,
            source_human_id=human.uid,
            location_id=human.physical_state.current_location_id,
            data={
                "name": human.name,
                "age": human.demographics.age,
                "inheritance": {str(k): v for k, v in inherited_distribution.items()},
            },
            importance=0.95,
        )
        event_bus.emit(death_evt)

        return {
            "uid": human.uid,
            "name": human.name,
            "inheritance": inherited_distribution,
            "event": death_evt,
        }
