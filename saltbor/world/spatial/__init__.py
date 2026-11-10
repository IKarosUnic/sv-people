"""Spatial movement, physical interaction, and spatial partitioning package."""

from saltbor.world.spatial.actions import PhysicalActionState, PhysicalPosture
from saltbor.world.spatial.encounters import EncounterDetector, EncounterEvent
from saltbor.world.spatial.grid import SpatialGridPartition
from saltbor.world.spatial.movement import (
    AgentSpatialState,
    ContinuousMovementEngine,
)

__all__ = [
    "AgentSpatialState",
    "ContinuousMovementEngine",
    "EncounterDetector",
    "EncounterEvent",
    "PhysicalActionState",
    "PhysicalPosture",
    "SpatialGridPartition",
]
