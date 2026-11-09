"""Built-in event handlers for cross-cutting concerns."""

from __future__ import annotations

import logging

from saltbor.events.types import SimulationEvent

logger = logging.getLogger(__name__)


def logging_handler(event: SimulationEvent) -> None:
    """Wildcard handler that logs every event at DEBUG level."""
    logger.debug("EVENT: %s", event)


def stdout_handler(event: SimulationEvent) -> None:
    """Wildcard handler that prints events to stdout (for development)."""
    print(f"  📢 {event}")
