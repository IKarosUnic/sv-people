"""Data models and structures for the multi-level population and LOD architecture."""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


class PopulationTier(enum.Enum):
    """The four distinct non-equivalent population tiers."""

    PERSISTENT = "persistent"            # Registered in the civilization database/index
    ACTIVELY_SIMULATED = "actively_simulated" # Ticked with detailed individual cognition in RAM
    AGGREGATED = "aggregated"            # Processed through cohort or community differential equations
    RENDERED = "rendered"                # Currently visible in the camera frustum / GPU buffer


class LODLevel(enum.IntEnum):
    """The five simulation levels of detail."""

    LOD_0_INDIVIDUAL = 0  # Full individual deliberation, memory, and spatial steering
    LOD_1_SIMPLIFIED = 1  # Heuristic routine execution, interpolated movement
    LOD_2_COHORT_GROUP = 2 # Household / work squad mean-field dynamics with variance
    LOD_3_COMMUNITY = 3   # Community ODE/difference equations for economy & demography
    LOD_4_REGIONAL = 4    # Regional macro migration and environmental indicators


@dataclass(slots=True)
class PersistentIndividualRecord:
    """Compact, highly-efficient record for millions of persistent individuals."""

    uid: str
    serial: int
    given_name: str
    family_name: str
    gender: str
    age_years: float
    occupation: str
    current_location_id: str
    lat: float
    lon: float
    wealth: float = 100.0
    health: float = 0.95
    energy: float = 0.80
    hunger: float = 0.20
    happiness: float = 0.50
    community_id: str = "comunidad_centro"
    district_id: str = "distrito_san_salvador"
    household_id: str = "hogar_default"
    lod_tier: int = int(LODLevel.LOD_2_COHORT_GROUP)
    is_exceptional: bool = False
    exception_reason: str = ""
    kinship_uids: list[str] = field(default_factory=list)
    knowledge_keys: list[str] = field(default_factory=list)
    packed_cognitive_state: Optional[bytes] = None
    last_update_tick: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "serial": self.serial,
            "full_name": f"{self.given_name} {self.family_name}",
            "gender": self.gender,
            "age": round(self.age_years, 1),
            "occupation": self.occupation,
            "current_location_id": self.current_location_id,
            "lat": self.lat,
            "lon": self.lon,
            "wealth": round(self.wealth, 2),
            "health": round(self.health, 3),
            "energy": round(self.energy, 3),
            "hunger": round(self.hunger, 3),
            "happiness": round(self.happiness, 3),
            "community_id": self.community_id,
            "district_id": self.district_id,
            "lod_tier": self.lod_tier,
            "is_exceptional": self.is_exceptional,
            "exception_reason": self.exception_reason,
            "kinship_count": len(self.kinship_uids),
            "knowledge_count": len(self.knowledge_keys),
        }


@dataclass
class CohortGroup:
    """LOD 2: Group of individuals (e.g. household, artisanal workshop, agricultural crew)."""

    cohort_id: str
    community_id: str
    category: str  # "household", "workshop", "farmers", "traders"
    center_lat: float
    center_lon: float
    member_uids: list[str] = field(default_factory=list)
    avg_wealth: float = 100.0
    avg_health: float = 0.9
    avg_hunger: float = 0.2
    avg_energy: float = 0.8
    current_activity: str = "work"
    exceptional_members: list[str] = field(default_factory=list)


@dataclass
class CommunityAggregate:
    """LOD 3: Community-level statistical and economic aggregate state."""

    community_id: str
    district_id: str
    name: str
    center_lat: float
    center_lon: float
    total_population: int = 0
    age_cohorts: list[int] = field(default_factory=lambda: [0] * 18) # 18 5-year cohorts [0-4, 5-9... 85+]
    occupations: dict[str, int] = field(default_factory=dict)
    total_wealth: float = 0.0
    mean_wealth: float = 0.0
    gini_coefficient: float = 0.35
    food_reserves_kg: float = 10000.0
    water_reserves_liters: float = 50000.0
    daily_production_units: float = 500.0
    active_conflict_level: float = 0.0
    cultural_adoption_rate: float = 0.5
    exceptional_uids: list[str] = field(default_factory=list)


@dataclass
class RegionalAggregate:
    """LOD 4: Macro regional indicator for administrative districts and departments."""

    region_id: str
    name: str
    polygon_id: str
    population_density_sqkm: float = 0.0
    total_population: int = 0
    net_migration_rate: float = 0.0
    gdp_index: float = 1.0
    environmental_stress: float = 0.2
    active_communities_count: int = 0
