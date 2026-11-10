"""Demographic profile for a synthetic human."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from saltbor.core.types import DataSource, Gender
from saltbor.lifecycle.demographics.stages import DevelopmentalStage, get_stage_for_age


class Demographics(BaseModel):
    """Demographic and developmental attributes of a synthetic individual.

    Supports continuous aging from birth (0 years) through late life (120+ years).
    """

    age: int = Field(default=25, ge=0, le=125, description="Age in years.")
    gender: Gender = Field(description="Gender identity.")
    occupation: str = Field(
        default="unemployed",
        description="Current occupation or job title.",
    )
    education_level: str = Field(
        default="secondary",
        description="Highest level of education attained.",
    )
    income_level: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Relative income level (0 = lowest, 1 = highest).",
    )
    native_language: str = Field(
        default="Spanish",
        description="Primary language spoken.",
    )
    data_source: DataSource = Field(
        default=DataSource.MOCK_GENERATED,
        description="Origin of this demographic record.",
    )
    birth_tick: int = Field(
        default=0,
        ge=0,
        description="Simulation tick at which this individual was born.",
    )
    stage: DevelopmentalStage = Field(
        default=DevelopmentalStage.ADULTHOOD,
        description="Current biological developmental stage.",
    )

    def model_post_init(self, __context: object) -> None:
        # Dynamically synchronize developmental stage if not explicitly set
        if self.stage == DevelopmentalStage.ADULTHOOD and self.age < 18:
            object.__setattr__(self, "stage", get_stage_for_age(float(self.age)))
        elif self.stage == DevelopmentalStage.ADULTHOOD and self.age >= 65:
            object.__setattr__(self, "stage", get_stage_for_age(float(self.age)))
