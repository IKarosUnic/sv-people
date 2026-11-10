"""Continuous biological aging model driven by simulation time."""

from __future__ import annotations

import dataclasses
from typing import Optional

from saltbor.core.types import Tick
from saltbor.lifecycle.demographics.stages import (
    DEFAULT_STAGE_CONFIGS,
    DevelopmentalStage,
    StageConfig,
    get_stage_for_age,
)


@dataclasses.dataclass
class BiologicalProfile:
    """Tracks continuous age, developmental stage, and physical capabilities."""

    birth_tick: Tick
    initial_age_years: float
    current_age_years: float
    current_stage: DevelopmentalStage
    vitality: float = 1.0           # Baseline physical resilience
    stamina_decay_rate: float = 0.02 # Rate at which stamina declines with intense exertion
    sensory_acuity: float = 1.0     # Perception multiplier

    def update_age(self, current_tick: Tick, ticks_per_year: float) -> tuple[float, bool]:
        """Update biological age based on elapsed simulation ticks.

        Returns (new_age_years, stage_changed: bool).
        """
        elapsed_ticks = max(0, current_tick - self.birth_tick)
        new_age = self.initial_age_years + (elapsed_ticks / float(ticks_per_year))
        self.current_age_years = round(new_age, 4)

        new_stage = get_stage_for_age(self.current_age_years)
        stage_changed = (new_stage != self.current_stage)
        self.current_stage = new_stage

        # Age-dependent physiological changes
        if self.current_age_years >= 60.0:
            # Gradual sensory and stamina slowdown in older adulthood
            decline_ratio = min(1.0, (self.current_age_years - 60.0) / 40.0)
            self.vitality = max(0.40, 1.0 - 0.40 * decline_ratio)
            self.sensory_acuity = max(0.60, 1.0 - 0.30 * decline_ratio)
        elif self.current_stage in (DevelopmentalStage.INFANCY, DevelopmentalStage.EARLY_CHILDHOOD):
            cfg = DEFAULT_STAGE_CONFIGS[self.current_stage]
            self.vitality = cfg.motor_coordination
            self.sensory_acuity = 0.70
        else:
            self.vitality = 1.0
            self.sensory_acuity = 1.0

        return self.current_age_years, stage_changed


class AgingEngine:
    """Manages biological time progression for all individuals."""

    def __init__(
        self,
        ticks_per_year: float = 35040.0,  # Default: 96 ticks/day * 365 days
        accelerated_ratio: float = 1.0,
    ) -> None:
        # Effective ticks per year: if accelerated, 1 year takes fewer ticks
        self.ticks_per_year = max(1.0, ticks_per_year / max(0.0001, accelerated_ratio))

    def create_profile(
        self,
        birth_tick: Tick,
        initial_age_years: float = 0.0,
        vitality: float = 1.0,
    ) -> BiologicalProfile:
        stage = get_stage_for_age(initial_age_years)
        return BiologicalProfile(
            birth_tick=birth_tick,
            initial_age_years=initial_age_years,
            current_age_years=initial_age_years,
            current_stage=stage,
            vitality=vitality,
        )

    def step_individual(self, profile: BiologicalProfile, current_tick: Tick) -> bool:
        """Advance biological age of an individual. Returns True if developmental stage changed."""
        _, changed = profile.update_age(current_tick, self.ticks_per_year)
        return changed
