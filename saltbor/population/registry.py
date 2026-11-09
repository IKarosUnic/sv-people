"""Population registry — in-memory directory of synthetic humans."""

from __future__ import annotations

from typing import Iterator, Optional

from saltbor.core.types import HumanID, LocationID
from saltbor.population.human import SyntheticHuman


class PopulationRegistry:
    """Registry maintaining active synthetic humans with fast indexed lookups."""

    def __init__(self) -> None:
        self._by_id: dict[HumanID, SyntheticHuman] = {}
        self._by_serial: dict[int, SyntheticHuman] = {}

    def register(self, human: SyntheticHuman) -> None:
        """Register a human in the directory."""
        self._by_id[human.uid] = human
        self._by_serial[human.identity.serial] = human

    def get(self, human_id: HumanID) -> SyntheticHuman:
        """Retrieve by UUID."""
        if human_id not in self._by_id:
            raise KeyError(f"Human '{human_id}' not found.")
        return self._by_id[human_id]

    def get_optional(self, human_id: HumanID) -> Optional[SyntheticHuman]:
        return self._by_id.get(human_id)

    def get_by_serial(self, serial: int) -> Optional[SyntheticHuman]:
        """Retrieve by numeric serial."""
        return self._by_serial.get(serial)

    def get_all(self) -> list[SyntheticHuman]:
        """Return all registered humans."""
        return list(self._by_id.values())

    def get_at_location(self, location_id: LocationID) -> list[SyntheticHuman]:
        """Return all individuals currently situated at a specific location."""
        return [
            h for h in self._by_id.values()
            if h.physical_state.current_location_id == location_id
        ]

    @property
    def count(self) -> int:
        return len(self._by_id)

    def __len__(self) -> int:
        return len(self._by_id)

    def __iter__(self) -> Iterator[SyntheticHuman]:
        return iter(self._by_id.values())
