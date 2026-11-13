"""SimulationRuntimeOrchestrator — central orchestration layer for SALTBOR.

Coordinates all civilization engines through declarative contracts, distinguishing:
- PER_TICK systems (immediate physics, environment, location indexing, biological updates)
- EVENT_TRIGGERED systems (judicial hearings, commerce transactions, remittances, dialogue)
- PERIODIC systems (daily cultural decay, weekly cuchubales, monthly assembly/loans)
- LONGITUDINAL systems (Gini inequality, demographic shifts, long-term technological diffusion)
- ON_DEMAND systems (scientific laboratory experiments, observer interventions)

Provides dependency-aware ordering, priority execution, batched processing,
cooldown enforcement, failure isolation, and event deduplication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import logging
import time
from typing import Any, Callable, Optional, TYPE_CHECKING
import uuid

import numpy as np

from saltbor.core.types import Tick
from saltbor.events.types import EventType, SimulationEvent

if TYPE_CHECKING:
    from saltbor.simulation.runner import SimulationRunner

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    """Execution frequency and trigger modality for civilization engines."""

    PER_TICK = "per_tick"
    EVENT_TRIGGERED = "event_triggered"
    PERIODIC = "periodic"
    LONGITUDINAL = "longitudinal"
    ON_DEMAND = "on_demand"


@dataclass
class EngineMetadata:
    """Declarative specification and operational profile of a civilization engine."""

    name: str
    mode: ExecutionMode
    priority: int = 50                     # Lower number executes first (1..100)
    trigger_events: list[EventType] = field(default_factory=list)
    period_ticks: int = 96                 # For PERIODIC (96=1 day, 672=1 week, 2880=1 month)
    longitudinal_interval: int = 960       # For LONGITUDINAL (e.g. 10 days)
    cooldown_ticks: int = 0                # Minimum ticks between executions
    computational_cost: str = "low"        # "low", "medium", "high"
    dependencies: list[str] = field(default_factory=list)
    failure_isolated: bool = True
    
    # Handlers
    step_handler: Optional[Callable[[OrchestratorContext, Tick], None]] = None
    event_handler: Optional[Callable[[OrchestratorContext, SimulationEvent], None]] = None

    # Telemetry
    last_executed_tick: int = -1
    execution_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0


@dataclass
class OrchestratorContext:
    """Execution context injected into engine handlers."""

    runner: SimulationRunner
    tick: Tick
    master_rng: np.random.Generator

    @property
    def population(self) -> Any:
        return self.runner.population

    @property
    def event_bus(self) -> Any:
        return self.runner.event_bus

    @property
    def clock(self) -> Any:
        return self.runner.clock


class SimulationRuntimeOrchestrator:
    """Master orchestrator scheduling and dispatching across all civilization engines."""

    def __init__(self, runner: SimulationRunner) -> None:
        self.runner = runner
        self._engines: dict[str, EngineMetadata] = {}
        self._event_subscribers: dict[EventType, list[EngineMetadata]] = {}
        self._recent_events_dedup: dict[str, int] = {}  # event_sig -> tick
        self._sorted_per_tick_cache: Optional[list[EngineMetadata]] = None
        self._is_active: bool = True

    # -------------------------------------------------------------------------
    # Engine Registration
    # -------------------------------------------------------------------------

    def register(self, engine: EngineMetadata) -> None:
        """Register a civilization engine and wire its event triggers."""
        self._engines[engine.name] = engine
        self._sorted_per_tick_cache = None

        if engine.mode == ExecutionMode.EVENT_TRIGGERED or engine.trigger_events:
            for ev_type in engine.trigger_events:
                if ev_type not in self._event_subscribers:
                    self._event_subscribers[ev_type] = []
                self._event_subscribers[ev_type].append(engine)

        logger.debug(
            "Registered orchestrator engine '%s' [Mode: %s, Priority: %d]",
            engine.name, engine.mode.value, engine.priority
        )

    def get_engine(self, name: str) -> Optional[EngineMetadata]:
        return self._engines.get(name)

    def get_all_engines(self) -> list[EngineMetadata]:
        return list(self._engines.values())

    # -------------------------------------------------------------------------
    # Dependency-aware Topological Ordering
    # -------------------------------------------------------------------------

    def _get_sorted_per_tick_engines(self) -> list[EngineMetadata]:
        """Compute execution order respecting dependencies and priority."""
        if self._sorted_per_tick_cache is not None:
            return self._sorted_per_tick_cache

        per_tick = [e for e in self._engines.values() if e.mode == ExecutionMode.PER_TICK]
        
        # Simple topological sort with priority tie-breaker
        sorted_list: list[EngineMetadata] = []
        visited: set[str] = set()

        def visit(eng: EngineMetadata) -> None:
            if eng.name in visited:
                return
            visited.add(eng.name)
            for dep_name in eng.dependencies:
                dep_eng = self._engines.get(dep_name)
                if dep_eng and dep_eng.mode == ExecutionMode.PER_TICK:
                    visit(dep_eng)
            sorted_list.append(eng)

        for eng in sorted(per_tick, key=lambda e: e.priority):
            visit(eng)

        self._sorted_per_tick_cache = sorted_list
        return sorted_list

    # -------------------------------------------------------------------------
    # Tick Progression
    # -------------------------------------------------------------------------

    def step(self, tick: Tick) -> None:
        """Execute scheduled and periodic engines for the given tick."""
        if not self._is_active:
            return

        ctx = OrchestratorContext(runner=self.runner, tick=tick, master_rng=self.runner.master_rng)

        # 1. Deduplication cache cleanup (keep current tick only)
        if len(self._recent_events_dedup) > 500:
            self._recent_events_dedup = {k: t for k, t in self._recent_events_dedup.items() if t >= tick - 1}

        # 2. Per-tick engines (topologically sorted by priority)
        for eng in self._get_sorted_per_tick_engines():
            self._execute_step_handler(eng, ctx, tick)

        # 3. Periodic engines
        for eng in self._engines.values():
            if eng.mode == ExecutionMode.PERIODIC:
                if tick % eng.period_ticks == 0:
                    if eng.cooldown_ticks > 0 and (tick - eng.last_executed_tick) < eng.cooldown_ticks:
                        continue
                    self._execute_step_handler(eng, ctx, tick)

        # 4. Longitudinal systems
        for eng in self._engines.values():
            if eng.mode == ExecutionMode.LONGITUDINAL:
                if tick > 0 and tick % eng.longitudinal_interval == 0:
                    self._execute_step_handler(eng, ctx, tick)

    def _execute_step_handler(self, eng: EngineMetadata, ctx: OrchestratorContext, tick: Tick) -> None:
        """Execute an engine's step handler with performance measurement and failure isolation."""
        if eng.step_handler is None:
            return

        t0 = time.perf_counter()
        try:
            eng.step_handler(ctx, tick)
            eng.last_executed_tick = tick
            eng.execution_count += 1
        except Exception as ex:
            eng.error_count += 1
            logger.error("Engine '%s' failed in tick %d: %s", eng.name, tick, ex, exc_info=True)
            if not eng.failure_isolated:
                raise ex
        finally:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            eng.total_latency_ms += elapsed_ms

    # -------------------------------------------------------------------------
    # Event-Driven Dispatch
    # -------------------------------------------------------------------------

    def handle_event(self, event: SimulationEvent) -> None:
        """Dispatch a simulation event to subscribed event-triggered engines."""
        if not self._is_active:
            return

        # Event deduplication check
        ev_sig = f"{event.event_type.value}:{event.source_human_id}:{event.target_human_id}:{event.location_id}:{event.tick}"
        if ev_sig in self._recent_events_dedup:
            return
        self._recent_events_dedup[ev_sig] = event.tick

        subscribers = self._event_subscribers.get(event.event_type, [])
        if not subscribers:
            return

        ctx = OrchestratorContext(runner=self.runner, tick=event.tick, master_rng=self.runner.master_rng)

        # Sort subscribers by priority
        for eng in sorted(subscribers, key=lambda e: e.priority):
            if eng.cooldown_ticks > 0 and (event.tick - eng.last_executed_tick) < eng.cooldown_ticks:
                continue

            if eng.event_handler is not None:
                t0 = time.perf_counter()
                try:
                    eng.event_handler(ctx, event)
                    eng.last_executed_tick = event.tick
                    eng.execution_count += 1
                except Exception as ex:
                    eng.error_count += 1
                    logger.error("Engine '%s' failed on event %s: %s", eng.name, event.event_type.value, ex, exc_info=True)
                    if not eng.failure_isolated:
                        raise ex
                finally:
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0
                    eng.total_latency_ms += elapsed_ms

    # -------------------------------------------------------------------------
    # Telemetry and Observability
    # -------------------------------------------------------------------------

    def get_status_summary(self) -> dict[str, Any]:
        """Summary of active engines, execution metrics, and latency."""
        return {
            "registered_engines_count": len(self._engines),
            "modes": {
                mode.value: sum(1 for e in self._engines.values() if e.mode == mode)
                for mode in ExecutionMode
            },
            "engines": [
                {
                    "name": e.name,
                    "mode": e.mode.value,
                    "priority": e.priority,
                    "cost": e.computational_cost,
                    "executions": e.execution_count,
                    "errors": e.error_count,
                    "avg_latency_ms": round(e.total_latency_ms / max(1, e.execution_count), 3),
                    "last_tick": e.last_executed_tick,
                }
                for e in sorted(self._engines.values(), key=lambda e: e.priority)
            ],
        }
