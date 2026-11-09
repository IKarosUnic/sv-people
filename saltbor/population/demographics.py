"""Demographic profile for a synthetic human."""

from __future__ import annotations

from pydantic import BaseModel, Field

from saltbor.core.types import DataSource, Gender


class Demographics(BaseModel):
    """Immutable demographic attributes of a synthetic individual.

    These represent relatively stable characteristics that change rarely
    or never during the simulation (e.g. native language, education level).
    Income level is a *relative* measure in ``[0, 1]``.
    """

    age: int = Field(ge=18, le=75, description="Age in years.")
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
