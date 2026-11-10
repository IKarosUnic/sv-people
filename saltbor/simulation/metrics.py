"""Performance, resource consumption, and simulation metrics tracker.

Monitors per-tick execution latency, logical and physical memory consumption
per individual, active event throughput, and scalability metrics.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from saltbor.core.types import Tick
from saltbor.population.registry import PopulationRegistry


@dataclass
class TickMetric:
    """Metrics recorded for a single simulation tick."""

    tick: Tick
    duration_ms: float
    events_emitted: int
    active_humans: int
    memory_footprint_bytes: int
    active_state_bytes: int = 0
    historical_records_bytes: int = 0


class MetricsTracker:
    """Collects and reports real-time performance and memory statistics."""

    def __init__(self) -> None:
        self._tick_history: list[TickMetric] = []
        self._start_time: float = time.perf_counter()
        self._max_history: int = 1000

    def record_tick(
        self,
        tick: Tick,
        duration_sec: float,
        events_emitted: int,
        population: PopulationRegistry,
    ) -> TickMetric:
        """Record measurements for a completed simulation tick.

        Separates active simulation state (working memory, physical state, active goals)
        from historical records (episodic archives, relationship histories, event logs).
        """
        all_humans = population.get_all()
        # Active cognitive state
        active_bytes = 0
        historical_bytes = 0
        total_mem_bytes = 0

        for h in all_humans:
            mem_stats = h.memory.get_memory_stats() if hasattr(h, "memory") else {"approx_bytes": 1000}
            total = mem_stats.get("approx_bytes", 1000)
            dormant = mem_stats.get("dormant_memories", 0) * 120
            episodic = mem_stats.get("episodic_memories", 0) * 150
            hist = dormant + episodic
            act = max(200, total - hist)

            active_bytes += act
            historical_bytes += hist
            total_mem_bytes += total

        metric = TickMetric(
            tick=tick,
            duration_ms=round(duration_sec * 1000.0, 3),
            events_emitted=events_emitted,
            active_humans=population.count,
            memory_footprint_bytes=total_mem_bytes,
            active_state_bytes=active_bytes,
            historical_records_bytes=historical_bytes,
        )

        self._tick_history.append(metric)
        if len(self._tick_history) > self._max_history:
            self._tick_history = self._tick_history[-self._max_history :]

        return metric

    def get_summary(self) -> dict[str, Any]:
        """Generate high-level performance and resource summary."""
        if not self._tick_history:
            return {"status": "no_ticks_recorded"}

        durations = [m.duration_ms for m in self._tick_history]
        total_ticks = len(self._tick_history)
        avg_tick_ms = sum(durations) / total_ticks
        max_tick_ms = max(durations)
        min_tick_ms = min(durations)

        latest = self._tick_history[-1]
        latest_mem = latest.memory_footprint_bytes
        active_mem = latest.active_state_bytes
        historical_mem = latest.historical_records_bytes
        active_humans = max(1, latest.active_humans)

        per_human_mem = latest_mem / active_humans
        per_human_active = active_mem / active_humans
        per_human_hist = historical_mem / active_humans

        elapsed = time.perf_counter() - self._start_time
        tps = total_ticks / elapsed if elapsed > 0 else 0.0

        return {
            "total_ticks_recorded": total_ticks,
            "average_tick_latency_ms": round(avg_tick_ms, 3),
            "min_tick_latency_ms": round(min_tick_ms, 3),
            "max_tick_latency_ms": round(max_tick_ms, 3),
            "ticks_per_second": round(tps, 2),
            "aggregate_memory_bytes": latest_mem,
            "active_state_memory_bytes": active_mem,
            "historical_records_bytes": historical_mem,
            "memory_per_human_bytes": round(per_human_mem, 1),
            "memory_per_human_kb": round(per_human_mem / 1024.0, 2),
            "active_memory_per_human_kb": round(per_human_active / 1024.0, 2),
            "historical_memory_per_human_kb": round(per_human_hist / 1024.0, 2),
            "target_1mb_compliance": per_human_mem < 1_048_576,
        }
