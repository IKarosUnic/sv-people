"""2D coordinate system for the 500 m × 500 m Saltbor world.

Provides basic spatial primitives — positions, bounding boxes, distance
calculations, and boundary checks — used by every module that deals with
locations or movement.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Spatial primitives
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Position:
    """A point in the 2-D Saltbor world, measured in metres."""

    x: float
    y: float

    # -- convenience --------------------------------------------------------

    def as_tuple(self) -> tuple[float, float]:
        """Return ``(x, y)`` for interop with :pydata:`Coordinate`."""
        return (self.x, self.y)

    def __iter__(self):  # noqa: D105 — allow tuple unpacking
        yield self.x
        yield self.y

    def __repr__(self) -> str:
        return f"Position(x={self.x:.1f}, y={self.y:.1f})"


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Axis-aligned rectangle defined by two opposite corners (metres)."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        if self.min_x > self.max_x or self.min_y > self.max_y:
            raise ValueError(
                f"Invalid BoundingBox: min corner ({self.min_x}, {self.min_y}) "
                f"must not exceed max corner ({self.max_x}, {self.max_y})."
            )

    @property
    def width(self) -> float:
        """Horizontal extent in metres."""
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        """Vertical extent in metres."""
        return self.max_y - self.min_y

    @property
    def center(self) -> Position:
        """Geometric centre of the box."""
        return Position(
            (self.min_x + self.max_x) / 2.0,
            (self.min_y + self.max_y) / 2.0,
        )

    def __repr__(self) -> str:
        return (
            f"BoundingBox(({self.min_x:.1f},{self.min_y:.1f})"
            f"–({self.max_x:.1f},{self.max_y:.1f}))"
        )


# ---------------------------------------------------------------------------
# Free functions
# ---------------------------------------------------------------------------

def distance(a: Position, b: Position) -> float:
    """Euclidean distance between two positions (metres)."""
    return math.hypot(a.x - b.x, a.y - b.y)


def is_within_bounds(pos: Position, world_width: float, world_height: float) -> bool:
    """Return *True* if *pos* lies inside ``[0, world_width] × [0, world_height]``."""
    return 0.0 <= pos.x <= world_width and 0.0 <= pos.y <= world_height


def is_inside_bbox(pos: Position, bbox: BoundingBox) -> bool:
    """Return *True* if *pos* lies inside the bounding box (inclusive)."""
    return (
        bbox.min_x <= pos.x <= bbox.max_x
        and bbox.min_y <= pos.y <= bbox.max_y
    )
