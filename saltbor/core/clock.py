"""Simulation clock — discrete time management."""

from __future__ import annotations

from dataclasses import dataclass, field

from saltbor.core.config import SimulationConfig
from saltbor.core.types import Tick


@dataclass
class SimulationClock:
    """Manages discrete simulation time.

    One tick = ``config.tick_duration_minutes`` simulated minutes.
    The clock tracks the current tick, day, and time-of-day.
    """

    config: SimulationConfig = field(repr=False)
    _current_tick: Tick = field(default=0, init=False)

    # ---- Properties ----

    @property
    def current_tick(self) -> Tick:
        return self._current_tick

    @property
    def current_day(self) -> int:
        """Zero-based day number."""
        return self._current_tick // self.config.ticks_per_day

    @property
    def tick_of_day(self) -> int:
        """Tick index within the current day (0-based)."""
        return self._current_tick % self.config.ticks_per_day

    @property
    def current_hour(self) -> float:
        """Current hour of the simulated day (0.0–23.99…)."""
        minutes_since_midnight = (
            self.config.start_hour * 60
            + self.tick_of_day * self.config.tick_duration_minutes
        )
        return (minutes_since_midnight % (24 * 60)) / 60.0

    @property
    def current_hour_int(self) -> int:
        """Current hour as an integer (0–23)."""
        return int(self.current_hour) % 24

    @property
    def is_daytime(self) -> bool:
        """True if hour is between 6:00 and 22:00."""
        h = self.current_hour
        return 6.0 <= h < 22.0

    @property
    def is_night(self) -> bool:
        return not self.is_daytime

    # ---- Mutation ----

    def tick(self) -> Tick:
        """Advance the clock by one tick and return the new tick number."""
        self._current_tick += 1
        return self._current_tick

    def set_tick(self, tick: Tick) -> None:
        """Restore clock to a specific tick (e.g. when loading a save)."""
        self._current_tick = tick

    # ---- Display ----

    def time_string(self) -> str:
        """Human-readable time, e.g. ``'Day 3, 14:30'``."""
        h = self.current_hour
        hours = int(h)
        minutes = int((h - hours) * 60)
        return f"Day {self.current_day + 1}, {hours:02d}:{minutes:02d}"

    def __repr__(self) -> str:
        return f"SimulationClock(tick={self._current_tick}, {self.time_string()})"
