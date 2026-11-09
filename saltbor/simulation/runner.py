"""SimulationRunner — central orchestrator for the Saltbor simulation.

Coordinates the clock, environment, population, social dynamics, event bus,
persistence checkpoints, and metrics logging across simulation ticks.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from saltbor.core.clock import SimulationClock
from saltbor.core.config import SimulationConfig
from saltbor.core.identity import IdentityFactory
from saltbor.core.types import SimulationPhase, Tick
from saltbor.events.bus import EventBus
from saltbor.events.types import EventType, SimulationEvent
from saltbor.persistence.database import DatabaseManager
from saltbor.persistence.repositories import (
    EventLogRepository,
    HumanRepository,
    MemoryRepository,
    RelationshipRepository,
    SimulationStateRepository,
)
from saltbor.persistence.schema import SchemaManager
from saltbor.population.factory import PopulationFactory
from saltbor.population.registry import PopulationRegistry
from saltbor.simulation.metrics import MetricsTracker
from saltbor.simulation.scheduler import SimulationScheduler
from saltbor.social.engine import SocialEngine
from saltbor.world.activities.catalog import ActivityCatalog
from saltbor.world.locations.registry import LocationRegistry
from saltbor.world.navigation.pathfinding import NavigationGraph

logger = logging.getLogger(__name__)


class SimulationRunner:
    """The master simulation runtime environment."""

    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        self.config = config or SimulationConfig()
        self.clock = SimulationClock(config=self.config)
        self.event_bus = EventBus()
        self.phase = SimulationPhase.INITIALIZING

        # Master RNG
        seed = self.config.random_seed
        self.master_rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()

        # World
        self.locations = LocationRegistry.create_saltbor_map()
        self.nav_graph = NavigationGraph.build_saltbor_graph(self.locations)
        self.activities = ActivityCatalog()

        # Social & Population
        self.social = SocialEngine()
        self.population = PopulationRegistry()
        self.identity_factory = IdentityFactory()

        # Persistence
        self.db = DatabaseManager(self.config.database_path)
        self.human_repo: Optional[HumanRepository] = None
        self.rel_repo: Optional[RelationshipRepository] = None
        self.event_repo: Optional[EventLogRepository] = None
        self.memory_repo: Optional[MemoryRepository] = None
        self.state_repo: Optional[SimulationStateRepository] = None

        # Execution & Metrics
        self.scheduler = SimulationScheduler(rng=self.master_rng)
        self.metrics = MetricsTracker()

        # Callbacks (for observation / visualization hooks)
        self._on_tick_callbacks: list[Callable[[Tick, SimulationRunner], None]] = []

    def initialize(self, load_existing: bool = False) -> None:
        """Set up database schema, initialize or load population, and wire events."""
        self.db.connect()
        SchemaManager.create_tables(self.db)

        self.human_repo = HumanRepository(self.db)
        self.rel_repo = RelationshipRepository(self.db)
        self.event_repo = EventLogRepository(self.db)
        self.memory_repo = MemoryRepository(self.db)
        self.state_repo = SimulationStateRepository(self.db)

        # Connect persistence handler to event bus
        self.event_bus.subscribe(None, lambda evt: self.event_repo.save(evt))  # type: ignore[misc]

        if load_existing and self.human_repo.count() >= self.config.initial_population_size:
            logger.info("Restoring population from persistent SQLite database...")
            humans = self.human_repo.load_all()
            for h in humans:
                self.population.register(h)

            saved_rels = self.rel_repo.load_all()
            for r in saved_rels:
                self.social.add_relationship(r)

            saved_tick = self.state_repo.load_tick()
            if saved_tick is not None:
                self.clock.set_tick(saved_tick)
        else:
            logger.info("Creating fresh initial population of 20 synthetic humans...")
            humans = PopulationFactory.create_population(
                config=self.config,
                identity_factory=self.identity_factory,
                rng=self.master_rng,
                try_nemotron=False,
            )
            for h in humans:
                self.population.register(h)

            PopulationFactory.setup_initial_relationships(humans, self.social)

            # Checkpoint initial state
            self.human_repo.save_all(humans)
            self.rel_repo.save_all(self.social.get_all_relationships())
            self.state_repo.save_tick(0)

        # Emit simulation started event
        self.event_bus.emit(
            SimulationEvent(
                event_type=EventType.SIMULATION_STARTED,
                tick=self.clock.current_tick,
                data={"population_size": self.population.count},
                importance=0.8,
            )
        )
        self.phase = SimulationPhase.RUNNING

    def step(self) -> Tick:
        """Advance the simulation by exactly one discrete tick (15 simulated minutes)."""
        t0 = time.perf_counter()
        initial_event_count = len(self.event_bus.event_log)

        current_tick = self.clock.tick()

        # Day transition event
        if self.clock.tick_of_day == 0:
            self.event_bus.emit(
                SimulationEvent(
                    event_type=EventType.DAY_STARTED,
                    tick=current_tick,
                    data={"day": self.clock.current_day + 1},
                    importance=0.4,
                )
            )

        # Determine agent update sequence
        execution_order = self.scheduler.get_execution_order(self.population, current_tick)

        # Update each human
        for human in execution_order:
            curr_loc = human.physical_state.current_location_id
            # Discover others situated at the same location
            co_located = [
                h.uid for h in self.population.get_at_location(curr_loc)
                if h.uid != human.uid
            ] if curr_loc else []

            human.update(
                tick=current_tick,
                clock=self.clock,
                event_bus=self.event_bus,
                location_registry=self.locations,
                activity_catalog=self.activities,
                social_engine=self.social,
                nearby_humans=co_located,
            )

        # Periodic checkpointing
        if current_tick % self.config.checkpoint_interval_ticks == 0:
            self.checkpoint()

        elapsed = time.perf_counter() - t0
        events_emitted = len(self.event_bus.event_log) - initial_event_count

        self.metrics.record_tick(
            tick=current_tick,
            duration_sec=elapsed,
            events_emitted=events_emitted,
            population=self.population,
        )

        # Notify any observer callbacks
        for cb in self._on_tick_callbacks:
            try:
                cb(current_tick, self)
            except Exception as ex:
                logger.warning("Tick callback failed: %s", ex)

        return current_tick

    def run(self, num_ticks: int = 96) -> None:
        """Run the simulation loop for a specified number of ticks."""
        for _ in range(num_ticks):
            self.step()

    def checkpoint(self) -> None:
        """Persist current state snapshot to SQLite."""
        if self.human_repo and self.state_repo and self.rel_repo:
            self.human_repo.save_all(self.population.get_all())
            self.rel_repo.save_all(self.social.get_all_relationships())
            self.state_repo.save_tick(self.clock.current_tick)
            self.event_bus.emit(
                SimulationEvent(
                    event_type=EventType.CHECKPOINT_SAVED,
                    tick=self.clock.current_tick,
                    data={"tick": self.clock.current_tick},
                    importance=0.3,
                )
            )

    def register_on_tick_callback(self, cb: Callable[[Tick, SimulationRunner], None]) -> None:
        """Register an observer hook called after every tick."""
        self._on_tick_callbacks.append(cb)

    def close(self) -> None:
        """Cleanly close database connections."""
        self.checkpoint()
        self.db.close()
        self.phase = SimulationPhase.STOPPED
