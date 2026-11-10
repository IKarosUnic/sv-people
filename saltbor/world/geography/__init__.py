"""Geography and terrain package for Saltbor."""

from saltbor.world.geography.grid import BoundingBox, Position, distance, is_within_bounds
from saltbor.world.geography.terrain import (
    TerrainCellProperties,
    TerrainGrid,
    TerrainSurfaceType,
)

__all__ = [
    "BoundingBox",
    "Position",
    "distance",
    "is_within_bounds",
    "TerrainCellProperties",
    "TerrainGrid",
    "TerrainSurfaceType",
]
