"""Accidents, Disasters & Misfortunes Models (Phase 1.5 Extension).

Defines contextual incident representations for traffic accidents, workplace trauma,
theft, infrastructural collapse, and environmental hazards like floods and landslides.
"""

from __future__ import annotations

import dataclasses
from typing import Any, List, Optional, Tuple

from saltbor.core.types import AccidentType, DisasterType, HumanID, LocationID, Tick


@dataclasses.dataclass
class AccidentEvent:
    """An acute localized incident involving individuals (traffic, work, fall, theft)."""
    accident_id: str
    accident_type: AccidentType
    location_id: LocationID
    coordinates: tuple[float, float] = (13.935, -89.028)
    tick: Tick = 0
    involved_human_ids: list[str] = dataclasses.field(default_factory=list)
    severity: float = 0.50               # [0.0, 1.0]
    property_damage_usd: float = 0.0
    injury_sustained: bool = False
    causal_factors: list[str] = dataclasses.field(default_factory=list)
    is_resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "accident_id": self.accident_id,
            "accident_type": self.accident_type.value,
            "location_id": self.location_id,
            "coordinates": self.coordinates,
            "tick": self.tick,
            "involved_human_ids": self.involved_human_ids,
            "severity": self.severity,
            "property_damage_usd": self.property_damage_usd,
            "injury_sustained": self.injury_sustained,
            "causal_factors": self.causal_factors,
            "is_resolved": self.is_resolved,
        }


@dataclasses.dataclass
class DisasterEvent:
    """A territorial environmental disaster affecting infrastructure, dwellings, and routes."""
    disaster_id: str
    disaster_type: DisasterType
    affected_location_ids: list[LocationID] = dataclasses.field(default_factory=list)
    affected_area_m2: float = 2500.0
    tick: Tick = 0
    severity: float = 0.65               # [0.0, 1.0]
    roads_blocked: list[str] = dataclasses.field(default_factory=list)
    housing_damaged_ids: list[str] = dataclasses.field(default_factory=list)
    displaced_human_ids: list[str] = dataclasses.field(default_factory=list)
    water_sources_contaminated: list[str] = dataclasses.field(default_factory=list)
    estimated_loss_usd: float = 0.0
    is_active: bool = True
    recovery_progress: float = 0.0       # [0.0, 1.0]

    def to_dict(self) -> dict[str, Any]:
        return {
            "disaster_id": self.disaster_id,
            "disaster_type": self.disaster_type.value,
            "affected_location_ids": self.affected_location_ids,
            "affected_area_m2": self.affected_area_m2,
            "tick": self.tick,
            "severity": self.severity,
            "roads_blocked": self.roads_blocked,
            "housing_damaged_ids": self.housing_damaged_ids,
            "displaced_human_ids": self.displaced_human_ids,
            "water_sources_contaminated": self.water_sources_contaminated,
            "estimated_loss_usd": self.estimated_loss_usd,
            "is_active": self.is_active,
            "recovery_progress": self.recovery_progress,
        }
