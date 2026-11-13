"""Scalable multi-rate event and priority scheduler for million-agent simulation.

Provides:
- Event-driven priority queue for scheduled historical and societal events.
- Multi-rate temporal decimation across the 5 LOD levels.
- Selective cognitive activation (only LOD 0 runs deliberate MAUT/brain subsystems).
- Continuity guarantee: aggregate and background updates prevent frozen individuals.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np

from saltbor.population.multilevel.models import LODLevel
from saltbor.population.multilevel.population_manager import MultilevelPopulationManager


@dataclass(order=True)
class ScheduledEvent:
    """Discrete event in priority queue scheduled for a future simulation tick."""

    scheduled_tick: int
    priority: int = 10  # Lower number = higher priority
    event_type: str = field(compare=False, default="general")
    target_uids: list[str] = field(compare=False, default_factory=list)
    payload: dict[str, Any] = field(compare=False, default_factory=dict)
    callback: Optional[Callable[[Any], None]] = field(compare=False, default=None)


class ScalableMultilevelScheduler:
    """Orchestrates multi-rate execution across millions of entities."""

    def __init__(
        self,
        manager: MultilevelPopulationManager,
        random_seed: int = 42,
    ) -> None:
        self.manager = manager
        self._rng = np.random.default_rng(random_seed)
        self._event_queue: list[ScheduledEvent] = []
        self._current_tick = 0

    def schedule_event(
        self,
        tick: int,
        event_type: str,
        target_uids: list[str],
        priority: int = 10,
        payload: Optional[dict[str, Any]] = None,
        callback: Optional[Callable[[Any], None]] = None,
    ) -> None:
        """Schedule a priority event for execution at or after tick."""
        event = ScheduledEvent(
            scheduled_tick=tick,
            priority=priority,
            event_type=event_type,
            target_uids=target_uids,
            payload=payload or {},
            callback=callback,
        )
        heapq.heappush(self._event_queue, event)

    def step(self, tick: int) -> dict[str, Any]:
        """Execute one simulation tick across priority events and decimated LOD tiers."""
        self._current_tick = tick
        events_processed = 0

        # 1. Process Due Scheduled Priority Events
        while self._event_queue and self._event_queue[0].scheduled_tick <= tick:
            event = heapq.heappop(self._event_queue)
            events_processed += 1

            # Important: Promote target entities to active simulation if affected by event
            for uid in event.target_uids:
                self.manager.promote_to_active(uid, target_lod=LODLevel.LOD_0_INDIVIDUAL)

            if event.callback:
                try:
                    event.callback(event.payload)
                except Exception:
                    pass

        # 2. Advance Population Manager State
        self.manager.step(tick)

        return {
            "tick": tick,
            "events_processed": events_processed,
            "events_pending": len(self._event_queue),
            "active_simulated": self.manager.active_simulated_count,
            "persistent_total": self.manager.persistent_count,
        }
