"""Lightweight terrain model: elevation, slopes, terrain surfaces, speed & energy penalties."""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from saltbor.core.types import Coordinate


class TerrainSurfaceType(enum.Enum):
    """Surface classification of a terrain cell."""

    PAVED_ROAD = "paved_road"            # High speed, lowest energy burn
    DIRT_PATH = "dirt_path"              # Standard community trail
    PLAINS = "plains"                    # Open grassland / arable farmland
    HILL = "hill"                        # Moderate incline, slower travel
    STEEP_SLOPE = "steep_slope"          # Heavy energy expenditure, significant speed reduction
    RIVER = "river"                      # Non-traversable without a crossing
    WATER_CROSSING = "water_crossing"    # Ford or bridge spanning the river
    DENSE_VEGETATION = "dense_vegetation"# Forest / thicket, slow passage
    ROCKY_GROUND = "rocky_ground"        # Low agricultural suitability, high stumble hazard
    SOIL = "soil"                        # Arable soil alias
    ROCK = "rock"                        # Rock alias
    BRIDGE = "bridge"                    # Bridge alias


@dataclass(frozen=True)
class TerrainCellProperties:
    """Biophysical consequences of traversing or cultivating a terrain cell."""

    surface_type: TerrainSurfaceType
    elevation_m: float
    slope_gradient: float                # 0.0 (flat) to 1.0 (very steep)
    traversable: bool = True
    speed_multiplier: float = 1.0        # 1.0 = normal walking speed (1.4 m/s)
    energy_burn_multiplier: float = 1.0  # Multiplier on metabolic energy loss
    agricultural_fertility: float = 1.0  # Multiplier on crop yield


class TerrainGrid:
    """A lightweight 2D spatial elevation and terrain surface matrix (500m x 500m)."""

    def __init__(
        self,
        width: float = 500.0,
        height: float = 500.0,
        cell_size: float = 25.0,
        width_meters: Optional[float] = None,
        height_meters: Optional[float] = None,
        cell_size_meters: Optional[float] = None,
    ) -> None:
        self.width = width_meters if width_meters is not None else width
        self.height = height_meters if height_meters is not None else height
        self.cell_size = cell_size_meters if cell_size_meters is not None else cell_size
        self.cols = max(1, int(math.ceil(self.width / self.cell_size)))
        self.rows = max(1, int(math.ceil(self.height / self.cell_size)))

        # 2D matrices for elevation and surface types
        self._elevation = np.zeros((self.rows, self.cols), dtype=np.float32)
        self._surface = np.full((self.rows, self.cols), TerrainSurfaceType.PLAINS, dtype=object)
        self._traversable_override: dict[tuple[int, int], bool] = {}

        self._initialize_saltbor_geography()

    def set_cell(
        self,
        col: int,
        row: int,
        elevation: float,
        surface: TerrainSurfaceType,
        is_walkable: bool = True,
    ) -> None:
        """Manually configure cell properties at (col, row)."""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self._elevation[row, col] = float(elevation)
            self._surface[row, col] = surface
            self._traversable_override[(row, col)] = is_walkable

    def _coord_to_indices(self, x: float, y: float) -> tuple[int, int]:
        c = max(0, min(self.cols - 1, int(math.floor(x / self.cell_size))))
        r = max(0, min(self.rows - 1, int(math.floor(y / self.cell_size))))
        return r, c

    def _initialize_saltbor_geography(self) -> None:
        """Procedurally generate Saltbor's hills, river, road network, and plains."""
        for r in range(self.rows):
            for c in range(self.cols):
                x = c * self.cell_size
                y = r * self.cell_size

                # Northern / North-Eastern hills (elevation up to 45m)
                if y > 350.0:
                    dist_to_hill_center = math.hypot(x - 300.0, y - 420.0)
                    elev = max(0.0, 45.0 - (dist_to_hill_center * 0.25))
                    self._elevation[r, c] = elev
                    if elev > 25.0:
                        self._surface[r, c] = TerrainSurfaceType.STEEP_SLOPE
                    elif elev > 10.0:
                        self._surface[r, c] = TerrainSurfaceType.HILL
                    else:
                        self._surface[r, c] = TerrainSurfaceType.PLAINS

                # River meandering along x = 120m to 140m
                river_center = 130.0 + 15.0 * math.sin(y / 60.0)
                if abs(x - river_center) < 20.0:
                    # Bridge / water crossings at y=200 (main road) and y=350 (sendero norte)
                    if 190.0 <= y <= 210.0 or 340.0 <= y <= 360.0:
                        self._surface[r, c] = TerrainSurfaceType.WATER_CROSSING
                        self._elevation[r, c] = 2.0
                    else:
                        self._surface[r, c] = TerrainSurfaceType.RIVER
                        self._elevation[r, c] = -1.5

                # Main commercial artery: paved road from x=100 to x=400 at y=200
                if 190.0 <= y <= 210.0 and self._surface[r, c] != TerrainSurfaceType.RIVER:
                    if self._surface[r, c] != TerrainSurfaceType.WATER_CROSSING:
                        self._surface[r, c] = TerrainSurfaceType.PAVED_ROAD

                # Dense vegetation in riparian zone
                if 30.0 < abs(x - river_center) < 60.0 and self._surface[r, c] == TerrainSurfaceType.PLAINS:
                    self._surface[r, c] = TerrainSurfaceType.DENSE_VEGETATION

    def get_cell_properties(self, x: float, y: float) -> TerrainCellProperties:
        """Lookup physical and traversal properties for coordinate (x, y)."""
        r, c = self._coord_to_indices(x, y)
        elev = float(self._elevation[r, c])
        surface = self._surface[r, c]

        # Calculate local slope gradient relative to adjacent cells
        dr = 1 if r < self.rows - 1 else -1
        dc = 1 if c < self.cols - 1 else -1
        dz_dr = abs(self._elevation[r + dr, c] - elev) / self.cell_size
        dz_dc = abs(self._elevation[r, c + dc] - elev) / self.cell_size
        slope = float(math.sqrt(dz_dr * dz_dr + dz_dc * dz_dc))

        traversable = True
        speed_mult = 1.0
        energy_mult = 1.0
        fertility = 1.0

        if surface == TerrainSurfaceType.RIVER:
            traversable = False
            speed_mult = 0.0
            fertility = 0.0
        elif surface in (TerrainSurfaceType.WATER_CROSSING, TerrainSurfaceType.BRIDGE):
            speed_mult = 0.85
            energy_mult = 1.15
        elif surface == TerrainSurfaceType.PAVED_ROAD:
            speed_mult = 1.25
            energy_mult = 0.85
            fertility = 0.0
        elif surface == TerrainSurfaceType.DIRT_PATH:
            speed_mult = 1.10
            energy_mult = 0.95
        elif surface == TerrainSurfaceType.HILL:
            speed_mult = max(0.5, 0.80 - (slope * 0.4))
            energy_mult = 1.0 + (slope * 1.5)
            fertility = 0.60
        elif surface == TerrainSurfaceType.STEEP_SLOPE:
            speed_mult = max(0.3, 0.50 - (slope * 0.5))
            energy_mult = 1.0 + (slope * 2.5)
            fertility = 0.20
        elif surface == TerrainSurfaceType.DENSE_VEGETATION:
            speed_mult = 0.70
            energy_mult = 1.40
            fertility = 0.80
        elif surface in (TerrainSurfaceType.ROCKY_GROUND, TerrainSurfaceType.ROCK):
            speed_mult = 0.65
            energy_mult = 1.30
            fertility = 0.15
        elif surface in (TerrainSurfaceType.PLAINS, TerrainSurfaceType.SOIL):
            speed_mult = 1.0
            energy_mult = 1.0
            fertility = 1.20  # Prime agricultural soil

        if (r, c) in self._traversable_override:
            traversable = self._traversable_override[(r, c)]

        return TerrainCellProperties(
            surface_type=surface,
            elevation_m=elev,
            slope_gradient=round(slope, 3),
            traversable=traversable,
            speed_multiplier=round(speed_mult, 3),
            energy_burn_multiplier=round(energy_mult, 3),
            agricultural_fertility=round(fertility, 3),
        )

    def is_traversable(self, x: float, y: float) -> bool:
        """Check whether the coordinate is passable."""
        return self.get_cell_properties(x, y).traversable

    def calculate_speed_multiplier(self, from_pos: tuple[float, float], to_pos: tuple[float, float]) -> float:
        """Compute the travel speed multiplier between two coordinates taking slope into account."""
        p1 = self.get_cell_properties(from_pos[0], from_pos[1])
        p2 = self.get_cell_properties(to_pos[0], to_pos[1])
        dist = max(1.0, math.hypot(to_pos[0] - from_pos[0], to_pos[1] - from_pos[1]))
        elev_diff = p2.elevation_m - p1.elevation_m
        slope_penalty = 0.5 * (elev_diff / dist) if elev_diff > 0 else 0.0
        base_speed = (p1.speed_multiplier + p2.speed_multiplier) / 2.0
        return max(0.2, base_speed - slope_penalty)

        return TerrainCellProperties(
            surface_type=surface,
            elevation_m=elev,
            slope_gradient=round(slope, 3),
            traversable=traversable,
            speed_multiplier=round(speed_mult, 3),
            energy_burn_multiplier=round(energy_mult, 3),
            agricultural_fertility=round(fertility, 3),
        )
