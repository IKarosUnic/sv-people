"""Global simulation configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class SimulationConfig(BaseSettings):
    """Central configuration for the Saltbor simulation.

    Values can be overridden via environment variables prefixed with ``SALTBOR_``
    (e.g. ``SALTBOR_RANDOM_SEED=42``).
    """

    model_config = {"env_prefix": "SALTBOR_"}

    # --- Simulation timing ---
    tick_duration_minutes: int = Field(
        default=15,
        description="Simulated minutes per tick (default 15 → 96 ticks/day).",
    )
    ticks_per_day: int = Field(default=96, description="Derived: 24*60 / tick_duration_minutes.")
    start_hour: int = Field(default=6, description="Hour of day when simulation day begins.")

    # --- World ---
    world_width: float = Field(default=500.0, description="World width in metres.")
    world_height: float = Field(default=500.0, description="World height in metres.")

    # --- Population ---
    initial_population_size: int = Field(default=20, description="Number of initial individuals.")
    min_age: int = Field(default=18, description="Minimum age for generated individuals.")
    max_age: int = Field(default=75, description="Maximum age for generated individuals.")

    # --- Persistence ---
    database_path: Path = Field(
        default=Path("saltbor.db"),
        description="Path to the SQLite database file.",
    )
    checkpoint_interval_ticks: int = Field(
        default=96,
        description="How often to checkpoint state (default: once per simulated day).",
    )

    # --- Memory ---
    max_working_memory_items: int = Field(default=7, description="Working memory capacity.")
    memory_decay_rate: float = Field(
        default=0.05,
        description="Base rate at which memory importance decays per simulated day.",
    )
    max_memory_bytes_per_human: int = Field(
        default=1_048_576,  # 1 MB
        description="Soft limit on logical memory per individual (bytes).",
    )

    # --- Randomness ---
    random_seed: Optional[int] = Field(
        default=None,
        description="Master random seed. None → non-deterministic.",
    )

    # --- LLM (optional) ---
    llm_enabled: bool = Field(default=False, description="Enable optional LLM integration.")
    llm_endpoint: Optional[str] = Field(default=None, description="LLM API endpoint URL.")

    # --- Visualization ---
    enable_console_viz: bool = Field(default=True, description="Enable console visualization.")

    def model_post_init(self, __context: object) -> None:
        # Ensure ticks_per_day is consistent with tick_duration_minutes.
        object.__setattr__(
            self, "ticks_per_day", (24 * 60) // self.tick_duration_minutes
        )
