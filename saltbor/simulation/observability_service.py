"""High-resolution, zero-cloud observability and telemetry service.

Implements lightweight OpenTelemetry-compatible tracing, spans, metrics tracking,
and asynchronous analytical logging for simulation engines and ticks.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from saltbor.core.types import Tick

logger = logging.getLogger(__name__)


class SpanKind(str, Enum):
    """Categorization of simulation spans."""

    INTERNAL = "internal"
    SIMULATION_TICK = "simulation_tick"
    ENGINE_STEP = "engine_step"
    EVENT_DISPATCH = "event_dispatch"
    DATA_INGESTION = "data_ingestion"


@dataclass
class TelemetrySpan:
    """An OpenTelemetry-compatible trace span."""

    name: str
    kind: SpanKind
    start_time_ns: int
    end_time_ns: int = 0
    duration_ms: float = 0.0
    tick: Optional[Tick] = None
    attributes: dict[str, Any] = field(default_factory=dict)
    status_code: str = "OK"  # OK or ERROR
    error_message: Optional[str] = None


class ObservabilityService:
    """Offline, in-memory structured tracing and telemetry manager."""

    def __init__(self, max_retained_spans: int = 10000) -> None:
        self.max_retained_spans = max_retained_spans
        self.completed_spans: list[TelemetrySpan] = []
        self._active_spans: dict[str, TelemetrySpan] = {}
        self._metric_counters: dict[str, float] = {}
        self._metric_gauges: dict[str, float] = {}

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        tick: Optional[Tick] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> str:
        """Start a new telemetry span and return its handle."""
        span_id = f"{name}_{time.perf_counter_ns()}"
        span = TelemetrySpan(
            name=name,
            kind=kind,
            start_time_ns=time.perf_counter_ns(),
            tick=tick,
            attributes=dict(attributes or {}),
        )
        self._active_spans[span_id] = span
        return span_id

    def end_span(
        self,
        span_id: str,
        status_code: str = "OK",
        error_message: Optional[str] = None,
        extra_attributes: Optional[dict[str, Any]] = None,
    ) -> Optional[TelemetrySpan]:
        """Complete a span, calculate its duration, and archive it."""
        span = self._active_spans.pop(span_id, None)
        if not span:
            return None

        span.end_time_ns = time.perf_counter_ns()
        span.duration_ms = (span.end_time_ns - span.start_time_ns) / 1_000_000.0
        span.status_code = status_code
        span.error_message = error_message
        if extra_attributes:
            span.attributes.update(extra_attributes)

        if len(self.completed_spans) >= self.max_retained_spans:
            self.completed_spans.pop(0)
        self.completed_spans.append(span)

        # Update engine timing gauge
        self.record_gauge(f"span.duration_ms.{span.name}", span.duration_ms)
        return span

    def increment_counter(self, name: str, amount: float = 1.0) -> None:
        self._metric_counters[name] = self._metric_counters.get(name, 0.0) + amount

    def record_gauge(self, name: str, value: float) -> None:
        self._metric_gauges[name] = value

    def get_summary_metrics(self) -> dict[str, Any]:
        """Return aggregated performance overview."""
        avg_durations: dict[str, float] = {}
        span_counts: dict[str, int] = {}
        for s in self.completed_spans:
            avg_durations[s.name] = avg_durations.get(s.name, 0.0) + s.duration_ms
            span_counts[s.name] = span_counts.get(s.name, 0) + 1

        for name, total in avg_durations.items():
            count = span_counts[name]
            avg_durations[name] = round(total / count, 3)

        return {
            "total_spans": len(self.completed_spans),
            "counters": dict(self._metric_counters),
            "gauges": dict(self._metric_gauges),
            "average_span_duration_ms": avg_durations,
        }
