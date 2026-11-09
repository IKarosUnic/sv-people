"""Location data model for the Saltbor world.

Each :class:`Location` represents a discrete place where humans can go —
a house, shop, park, etc.  Locations carry scheduling information, capacity
limits, available activities, and an optional bounding box for spatial
queries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel, Field

from saltbor.core.types import (
    ActivityType,
    Coordinate,
    HumanID,
    LocationID,
    LocationType,
)
from saltbor.world.geography.grid import BoundingBox


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------

@dataclass
class LocationSchedule:
    """Opening-hour windows for each day of the week.

    ``hours`` maps day-of-week (0 = Monday … 6 = Sunday) to an
    ``(open_hour, close_hour)`` pair expressed in 24-h format.
    A ``None`` value for a day means the location is closed all day.
    If a day key is absent the location defaults to its ``default_hours``.

    A location with ``always_open = True`` ignores the schedule entirely.
    """

    always_open: bool = False
    default_hours: tuple[int, int] = (0, 24)
    hours: dict[int, Optional[tuple[int, int]]] = field(default_factory=dict)

    def is_open_at(self, hour: int, day_of_week: int = 0) -> bool:
        """Return *True* if the location is open at the given *hour*.

        Parameters
        ----------
        hour:
            Hour of the day (0–23).
        day_of_week:
            Day of the week (0 = Monday).  Defaults to 0 because the
            simulation currently models generic days rather than a real
            calendar.
        """
        if self.always_open:
            return True
        window = self.hours.get(day_of_week, self.default_hours)
        if window is None:
            return False
        open_h, close_h = window
        return open_h <= hour < close_h


# ---------------------------------------------------------------------------
# Location model
# ---------------------------------------------------------------------------

class Location(BaseModel):
    """A discrete place in the Saltbor world.

    Pydantic model so it can be (de)serialized to/from JSON and validated
    at creation time.
    """

    model_config = {"arbitrary_types_allowed": True}

    location_id: LocationID
    name: str
    location_type: LocationType
    position: Coordinate  # (x, y) in metres
    bounding_box: Optional[BoundingBox] = None
    schedule: LocationSchedule = Field(default_factory=LocationSchedule)
    available_activities: list[ActivityType] = Field(default_factory=list)
    capacity: int = 10
    current_occupants: list[HumanID] = Field(
        default_factory=list,
        exclude=True,  # never serialised to DB/JSON
    )
    resources: dict[str, Any] = Field(default_factory=dict)
    access_restrictions: list[str] = Field(default_factory=list)
    description: str = ""
    is_outdoor: bool = False

    # -- Convenience methods ------------------------------------------------

    def is_open(self, hour: int, day_of_week: int = 0) -> bool:
        """Check whether the location is open at *hour* on *day_of_week*."""
        return self.schedule.is_open_at(hour, day_of_week)

    def has_capacity(self) -> bool:
        """Return *True* if there is room for at least one more occupant."""
        return len(self.current_occupants) < self.capacity

    def add_occupant(self, human_id: HumanID) -> bool:
        """Add *human_id* to the occupants list if there is room.

        Returns *True* on success, *False* if the location is full or the
        human is already present.
        """
        if human_id in self.current_occupants:
            return False
        if not self.has_capacity():
            return False
        self.current_occupants.append(human_id)
        return True

    def remove_occupant(self, human_id: HumanID) -> bool:
        """Remove *human_id* from the occupants list.

        Returns *True* if the human was present and removed, *False*
        otherwise.
        """
        try:
            self.current_occupants.remove(human_id)
            return True
        except ValueError:
            return False

    @property
    def occupant_count(self) -> int:
        """Number of humans currently in this location."""
        return len(self.current_occupants)

    def __repr__(self) -> str:
        return (
            f"Location(id={self.location_id!r}, name={self.name!r}, "
            f"type={self.location_type.value}, occupants={self.occupant_count}/{self.capacity})"
        )
