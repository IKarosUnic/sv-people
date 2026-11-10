"""Spatial 2D grid partitioning for O(1) local neighborhood and proximity queries."""

from __future__ import annotations

import math
from typing import Optional

from saltbor.core.types import Coordinate, HumanID


class SpatialGridPartition:
    """2D spatial hashing grid mapping continuous coordinates to discrete cells."""

    def __init__(self, cell_size: float = 25.0, width: float = 500.0, height: float = 500.0) -> None:
        self.cell_size = cell_size
        self.width = width
        self.height = height
        self.cols = max(1, int(math.ceil(width / cell_size)))
        self.rows = max(1, int(math.ceil(height / cell_size)))
        self._grid: dict[tuple[int, int], set[HumanID]] = {}
        self._agent_cells: dict[HumanID, tuple[int, int]] = {}

    def _coord_to_cell(self, x: float, y: float) -> tuple[int, int]:
        c = int(math.floor(x / self.cell_size))
        r = int(math.floor(y / self.cell_size))
        return (c, r)

    def insert(self, human_uid: HumanID, x: float, y: float) -> None:
        cell = self._coord_to_cell(x, y)
        if cell not in self._grid:
            self._grid[cell] = set()
        self._grid[cell].add(human_uid)
        self._agent_cells[human_uid] = cell

    def update_position(self, human_uid: HumanID, x: float, y: float) -> None:
        new_cell = self._coord_to_cell(x, y)
        old_cell = self._agent_cells.get(human_uid)

        if old_cell != new_cell:
            if old_cell and old_cell in self._grid:
                self._grid[old_cell].discard(human_uid)
            if new_cell not in self._grid:
                self._grid[new_cell] = set()
            self._grid[new_cell].add(human_uid)
            self._agent_cells[human_uid] = new_cell

    def remove(self, human_uid: HumanID) -> None:
        cell = self._agent_cells.pop(human_uid, None)
        if cell and cell in self._grid:
            self._grid[cell].discard(human_uid)

    def query_radius(
        self,
        center_x: float,
        center_y: float,
        radius: float,
        positions_map: dict[HumanID, Coordinate],
    ) -> list[HumanID]:
        """Return all agent UIDs strictly within radius meters of (center_x, center_y)."""
        min_c = int(math.floor((center_x - radius) / self.cell_size))
        max_c = int(math.floor((center_x + radius) / self.cell_size))
        min_r = int(math.floor((center_y - radius) / self.cell_size))
        max_r = int(math.floor((center_y + radius) / self.cell_size))

        nearby: list[HumanID] = []
        r2 = radius * radius

        for c in range(min_c, max_c + 1):
            for r in range(min_r, max_r + 1):
                cell_agents = self._grid.get((c, r))
                if not cell_agents:
                    continue
                for uid in cell_agents:
                    pos = positions_map.get(uid)
                    if pos:
                        dx = pos[0] - center_x
                        dy = pos[1] - center_y
                        if (dx * dx + dy * dy) <= r2:
                            nearby.append(uid)

        return nearby
