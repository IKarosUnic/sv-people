"""Physical action postures and load carriage models."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional


class PhysicalPosture(enum.Enum):
    """Observable physical posture or motor activity."""

    STANDING = "standing"
    SITTING = "sitting"
    WALKING = "walking"
    WORKING = "working"
    RESTING = "resting"
    CARRYING_LOAD = "carrying_load"


@dataclass
class PhysicalActionState:
    """Current motor state, carrying burden, and physical constraints."""

    posture: PhysicalPosture = PhysicalPosture.STANDING
    carried_weight_kg: float = 0.0
    max_carry_capacity_kg: float = 25.0

    @property
    def speed_penalty_factor(self) -> float:
        """Walking speed penalty as carrying load approaches capacity."""
        if self.max_carry_capacity_kg <= 0 or self.carried_weight_kg <= 0:
            return 1.0
        burden_ratio = min(1.0, self.carried_weight_kg / self.max_carry_capacity_kg)
        return max(0.4, 1.0 - 0.5 * burden_ratio)
