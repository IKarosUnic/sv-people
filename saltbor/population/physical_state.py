"""Mutable physical state of a synthetic human."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from saltbor.core.types import ActivityType, LocationID, NeedType


class PhysicalState(BaseModel):
    """Tracks the physical condition and location of an individual.

    All float fields are in ``[0.0, 1.0]`` unless otherwise noted.
    ``money`` is denominated in an abstract local currency unit.
    """

    energy: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Current energy level (1 = fully rested, 0 = exhausted).",
    )
    hunger: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Current hunger level (0 = sated, 1 = starving).",
    )
    health: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Overall health (1 = perfect, 0 = critical).",
    )

    current_location_id: Optional[LocationID] = Field(
        default=None, description="Where the person currently is."
    )
    current_activity: Optional[ActivityType] = Field(
        default=None, description="What the person is currently doing."
    )
    activity_ticks_remaining: int = Field(
        default=0, ge=0, description="Ticks left on current activity."
    )

    money: float = Field(
        default=100.0, ge=0.0, description="Available money (abstract units)."
    )
    home_location_id: Optional[LocationID] = Field(
        default=None, description="Assigned home location."
    )
    work_location_id: Optional[LocationID] = Field(
        default=None, description="Assigned work location."
    )

    # ------------------------------------------------------------------
    # Derived needs
    # ------------------------------------------------------------------

    def get_needs(self) -> dict[NeedType, float]:
        """Compute urgency scores for each basic need.

        Returns a dict mapping each :class:`NeedType` to a float in
        ``[0, 1]`` where **higher means more urgent**.
        """
        # Hunger urgency is the hunger value itself
        hunger_urgency = self.hunger

        # Rest urgency is inverse of energy
        rest_urgency = 1.0 - self.energy

        # Social need stays moderate — no physical sensor for it
        social_urgency = 0.3

        # Safety driven by low health
        safety_urgency = max(0.0, 1.0 - self.health)

        # Achievement — mildly present when idle
        achievement_urgency = 0.2 if self.current_activity is None else 0.1

        # Autonomy — baseline need
        autonomy_urgency = 0.15

        # Comfort — rises with hunger and low energy combined
        comfort_urgency = min(1.0, (hunger_urgency + rest_urgency) / 2.0)

        # Stimulation — rises when idle and well-rested
        stimulation_urgency = (
            0.4 if self.current_activity is None and self.energy > 0.5 else 0.15
        )

        return {
            NeedType.HUNGER: round(hunger_urgency, 4),
            NeedType.REST: round(rest_urgency, 4),
            NeedType.SOCIAL: round(social_urgency, 4),
            NeedType.SAFETY: round(safety_urgency, 4),
            NeedType.ACHIEVEMENT: round(achievement_urgency, 4),
            NeedType.AUTONOMY: round(autonomy_urgency, 4),
            NeedType.COMFORT: round(comfort_urgency, 4),
            NeedType.STIMULATION: round(stimulation_urgency, 4),
        }

    # ------------------------------------------------------------------
    # Per-tick updates
    # ------------------------------------------------------------------

    def update(self, tick_duration_minutes: int) -> None:
        """Apply natural per-tick changes to hunger and energy.

        Parameters
        ----------
        tick_duration_minutes:
            Length of one tick in simulated minutes (e.g. 15).
        """
        hours = tick_duration_minutes / 60.0

        # Hunger increases ~0.06 per hour while awake
        hunger_rate = 0.06 * hours
        self.hunger = min(1.0, self.hunger + hunger_rate)

        # Energy decreases while doing anything except sleeping/resting
        if self.current_activity in (ActivityType.SLEEP, ActivityType.REST):
            # Recover energy while sleeping/resting
            recovery_rate = 0.12 * hours  # ~full recovery in 8 h
            self.energy = min(1.0, self.energy + recovery_rate)
            # Sleeping also slows hunger gain
            self.hunger = max(0.0, self.hunger - hunger_rate * 0.5)
        else:
            # Base drain; work/exercise drains faster
            base_drain = 0.04 * hours
            if self.current_activity in (ActivityType.WORK, ActivityType.EXERCISE):
                base_drain *= 1.5
            self.energy = max(0.0, self.energy - base_drain)

        # Eating sates hunger
        if self.current_activity == ActivityType.EAT:
            self.hunger = max(0.0, self.hunger - 0.35 * hours)

        # Tick down activity timer
        if self.activity_ticks_remaining > 0:
            self.activity_ticks_remaining -= 1
            if self.activity_ticks_remaining == 0:
                self.current_activity = None
