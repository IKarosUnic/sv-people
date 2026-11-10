"""Demographics package for lifecycle."""

from saltbor.lifecycle.demographics.stages import (
    DEFAULT_STAGE_CONFIGS,
    DevelopmentalStage,
    StageConfig,
    get_stage_for_age,
)

__all__ = [
    "DEFAULT_STAGE_CONFIGS",
    "DevelopmentalStage",
    "StageConfig",
    "get_stage_for_age",
]
