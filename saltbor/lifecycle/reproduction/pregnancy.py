"""Biological pregnancy, gestation progression, and delivery model."""

from __future__ import annotations

import dataclasses
from typing import Optional
from uuid import UUID

from saltbor.core.types import HumanID, Tick


@dataclasses.dataclass
class Pregnancy:
    """Represents an active pregnancy of an individual."""

    mother_uid: HumanID
    father_uid: Optional[HumanID]
    start_tick: Tick
    gestation_duration_ticks: int = 288  # e.g., 3 simulated days (or configurable)
    ticks_elapsed: int = 0
    is_delivered: bool = False
    complications_risk: float = 0.05
    postpartum_ticks_remaining: int = 0

    @property
    def progress(self) -> float:
        """Gestation completion ratio in [0.0, 1.0]."""
        if self.gestation_duration_ticks <= 0:
            return 1.0
        return min(1.0, self.ticks_elapsed / float(self.gestation_duration_ticks))

    @property
    def is_due(self) -> bool:
        return self.ticks_elapsed >= self.gestation_duration_ticks and not self.is_delivered

    def advance(self, delta_ticks: int = 1) -> bool:
        """Advance gestation by delta_ticks.

        Returns True if the pregnancy has reached full term (ready for delivery).
        """
        if self.is_delivered:
            if self.postpartum_ticks_remaining > 0:
                self.postpartum_ticks_remaining = max(0, self.postpartum_ticks_remaining - delta_ticks)
            return False

        self.ticks_elapsed += delta_ticks
        return self.is_due

    def deliver(self) -> None:
        """Mark pregnancy as delivered and initiate postpartum recovery."""
        self.is_delivered = True
        self.postpartum_ticks_remaining = 96  # 1 simulated day of postpartum rest

    def get_physical_impact(self) -> dict[str, float]:
        """Extra nutritional drain and energy fatigue caused by gestation."""
        if self.is_delivered:
            if self.postpartum_ticks_remaining > 0:
                return {"energy_penalty": 0.08, "hunger_boost": 0.05}
            return {}

        prog = self.progress
        # Impact rises progressively through the 3 trimesters
        return {
            "energy_penalty": round(0.04 + 0.12 * prog, 3),  # Increases fatigue
            "hunger_boost": round(0.05 + 0.15 * prog, 3),   # Increases nutritional requirements
        }

    def to_dict(self) -> dict:
        return {
            "mother_uid": str(self.mother_uid),
            "father_uid": str(self.father_uid) if self.father_uid else None,
            "start_tick": self.start_tick,
            "gestation_duration_ticks": self.gestation_duration_ticks,
            "ticks_elapsed": self.ticks_elapsed,
            "is_delivered": self.is_delivered,
            "complications_risk": self.complications_risk,
            "postpartum_ticks_remaining": self.postpartum_ticks_remaining,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Pregnancy:
        return cls(
            mother_uid=UUID(data["mother_uid"]),
            father_uid=UUID(data["father_uid"]) if data.get("father_uid") else None,
            start_tick=int(data["start_tick"]),
            gestation_duration_ticks=int(data.get("gestation_duration_ticks", 288)),
            ticks_elapsed=int(data.get("ticks_elapsed", 0)),
            is_delivered=bool(data.get("is_delivered", False)),
            complications_risk=float(data.get("complications_risk", 0.05)),
            postpartum_ticks_remaining=int(data.get("postpartum_ticks_remaining", 0)),
        )
