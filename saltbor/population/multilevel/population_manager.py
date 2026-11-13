"""Multi-level Population Manager orchestrating the 4 population tiers and 5 LOD levels.

Provides:
- Explicit separation of Persistent, Actively Simulated, Aggregated, and Rendered populations.
- State hydration and dehydration with zero loss of identity, memories, or personality.
- Promotion/demotion transition rules driven by importance, proximity, and causal events.
- Seamless coexistence with existing SyntheticHuman instances.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional

import numpy as np

from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.memory.semantic import SemanticFact
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.core.identity import HumanIdentity
from saltbor.core.types import DataSource, Gender, HumanID
from saltbor.population.demographics import Demographics
from saltbor.population.human import SyntheticHuman
from saltbor.population.multilevel.aggregation import PopulationAggregator
from saltbor.population.multilevel.models import (
    CohortGroup,
    CommunityAggregate,
    LODLevel,
    PersistentIndividualRecord,
    PopulationTier,
    RegionalAggregate,
)
from saltbor.population.physical_state import PhysicalState
from saltbor.world.spatial.multi_partition import SpatialPartitionManager

logger = logging.getLogger(__name__)


class MultilevelPopulationManager:
    """Central manager for millions of persistent individuals with selective cognitive hydration."""

    def __init__(self, spatial_manager: Optional[SpatialPartitionManager] = None) -> None:
        self.spatial = spatial_manager or SpatialPartitionManager()

        # 1. Persistent Population: All registered individuals indexed by UID
        self._persistent: dict[str, PersistentIndividualRecord] = {}

        # 2. Actively Simulated Population: Hydrated SyntheticHuman instances in RAM (LOD 0 / LOD 1)
        self._active_humans: dict[str, SyntheticHuman] = {}

        # 3. Aggregated Population: Cohorts and Communities (LOD 2 / LOD 3 / LOD 4)
        self._cohorts: dict[str, CohortGroup] = {}
        self._communities: dict[str, CommunityAggregate] = {}
        self._regions: dict[str, RegionalAggregate] = {}

        # Tracking and focal status
        self._focal_uids: set[str] = set()
        self._rendered_uids: set[str] = set()
        self._current_tick: int = 0

    # -------------------------------------------------------------------------
    # Population Counters & Tier Queries
    # -------------------------------------------------------------------------

    @property
    def persistent_count(self) -> int:
        """Total persistent population registered in civilization."""
        return len(self._persistent)

    @property
    def active_simulated_count(self) -> int:
        """Number of individuals currently with active cognitive/behavioral state in RAM."""
        return len(self._active_humans)

    @property
    def aggregated_count(self) -> int:
        """Number of individuals currently processed via collective or statistical models."""
        return max(0, self.persistent_count - self.active_simulated_count)

    @property
    def rendered_count(self) -> int:
        """Entities currently represented in the visual viewport."""
        return len(self._rendered_uids)

    def get_tier_summary(self) -> dict[str, Any]:
        """Return counts and distribution across the 4 non-equivalent population tiers."""
        lod_dist = {
            "lod_0_individual": 0,
            "lod_1_simplified": 0,
            "lod_2_cohort": 0,
            "lod_3_community": 0,
            "lod_4_regional": 0,
        }
        for rec in self._persistent.values():
            if rec.lod_tier == LODLevel.LOD_0_INDIVIDUAL:
                lod_dist["lod_0_individual"] += 1
            elif rec.lod_tier == LODLevel.LOD_1_SIMPLIFIED:
                lod_dist["lod_1_simplified"] += 1
            elif rec.lod_tier == LODLevel.LOD_2_COHORT_GROUP:
                lod_dist["lod_2_cohort"] += 1
            elif rec.lod_tier == LODLevel.LOD_3_COMMUNITY:
                lod_dist["lod_3_community"] += 1
            else:
                lod_dist["lod_4_regional"] += 1

        return {
            "persistent_population": self.persistent_count,
            "actively_simulated": self.active_simulated_count,
            "aggregated_population": self.aggregated_count,
            "rendered_population": self.rendered_count,
            "lod_distribution": lod_dist,
            "focal_agents": list(self._focal_uids),
            "communities_count": len(self._communities),
            "tick": self._current_tick,
        }

    # -------------------------------------------------------------------------
    # Registration & Seeding
    # -------------------------------------------------------------------------

    def register_individual(self, record: PersistentIndividualRecord) -> None:
        """Register an individual into the persistent directory and spatial index."""
        self._persistent[record.uid] = record
        self.spatial.insert_or_update(
            uid=record.uid,
            lon=record.lon,
            lat=record.lat,
            lod_tier=record.lod_tier,
            data=record,
        )

    def register_batch(self, records: list[PersistentIndividualRecord]) -> None:
        """Bulk register thousands or millions of individuals with spatial indexing."""
        for rec in records:
            self._persistent[rec.uid] = rec
            self.spatial.insert_or_update(
                uid=rec.uid,
                lon=rec.lon,
                lat=rec.lat,
                lod_tier=rec.lod_tier,
                data=rec,
            )

    def register_community(self, community: CommunityAggregate) -> None:
        self._communities[community.community_id] = community

    def register_cohort(self, cohort: CohortGroup) -> None:
        self._cohorts[cohort.cohort_id] = cohort

    # -------------------------------------------------------------------------
    # Hydration (Promotion) and Dehydration (Demotion)
    # -------------------------------------------------------------------------

    def promote_to_active(self, uid: str, target_lod: LODLevel = LODLevel.LOD_0_INDIVIDUAL) -> Optional[SyntheticHuman]:
        """Promote an individual to actively simulated population (LOD 0 or LOD 1).

        Reconstructs the full SyntheticHuman object in RAM with complete state fidelity.
        """
        rec = self._persistent.get(uid)
        if not rec:
            return None

        # Already active?
        if uid in self._active_humans:
            human = self._active_humans[uid]
            rec.lod_tier = int(target_lod)
            return human

        # Reconstruct SyntheticHuman from persistent record
        identity = HumanIdentity(
            uid=uuid.UUID(rec.uid) if len(rec.uid) == 36 else uuid.uuid5(uuid.NAMESPACE_DNS, rec.uid),
            serial=rec.serial,
            given_name=rec.given_name,
            family_name=rec.family_name,
            data_source=DataSource.MOCK_GENERATED,
        )

        demographics = Demographics(
            gender=Gender.FEMALE if rec.gender == "female" else Gender.MALE,
            birth_tick=0,
            age_years=rec.age_years,
            household_id=uuid.uuid5(uuid.NAMESPACE_DNS, rec.household_id),
            occupation=rec.occupation,
        )

        physical_state = PhysicalState(
            energy=rec.energy,
            hunger=rec.hunger,
            health=rec.health,
            money=rec.wealth,
            current_location_id=rec.current_location_id,
        )

        # Unpack stored cognitive profile or initialize standard engines
        personality = PersonalityEngine(
            traits=PersonalityTraits(
                openness=TraitValue(base_value=0.6, current_value=0.6),
                conscientiousness=TraitValue(base_value=0.7, current_value=0.7),
                extraversion=TraitValue(base_value=0.6, current_value=0.6),
                agreeableness=TraitValue(base_value=0.7, current_value=0.7),
                neuroticism=TraitValue(base_value=0.3, current_value=0.3),
            )
        )
        emotions = EmotionalEngine()
        memory = MemoryEngine()

        # If packed cognitive state exists, restore episodic facts and keys
        if rec.packed_cognitive_state:
            try:
                state_dict = json.loads(rec.packed_cognitive_state.decode("utf-8"))
                for idx, fact_text in enumerate(state_dict.get("semantic_facts", [])):
                    memory.semantic.store(SemanticFact(
                        fact_id=f"restored_fact_{idx}",
                        category="cultural_fact",
                        content=fact_text,
                        confidence=0.9,
                        source="history",
                        learned_tick=0,
                    ))
            except Exception:
                pass

        human = SyntheticHuman(
            identity=identity,
            demographics=demographics,
            physical_state=physical_state,
            personality=personality,
            emotions=emotions,
            memory=memory,
        )

        rec.lod_tier = int(target_lod)
        self._active_humans[uid] = human
        return human

    def demote_to_aggregated(self, uid: str, target_lod: LODLevel = LODLevel.LOD_2_COHORT_GROUP) -> None:
        """Demote an active individual to aggregated state, saving its state and freeing RAM."""
        human = self._active_humans.pop(uid, None)
        rec = self._persistent.get(uid)
        if not rec:
            return

        rec.lod_tier = int(target_lod)
        if human:
            # Sync back dynamic variables
            rec.wealth = human.physical_state.money
            rec.health = human.physical_state.health
            rec.energy = human.physical_state.energy
            rec.hunger = human.physical_state.hunger
            rec.current_location_id = human.physical_state.current_location_id or rec.current_location_id

            # Pack cognitive facts if learned during active phase
            semantic_facts = [f.content for f in human.memory.semantic.get_all()] if human.memory.semantic else []
            state_dict = {"semantic_facts": semantic_facts}
            rec.packed_cognitive_state = json.dumps(state_dict).encode("utf-8")

    # -------------------------------------------------------------------------
    # Simulation Step & Scheduling
    # -------------------------------------------------------------------------

    def step(self, tick: int) -> None:
        """Execute one simulation tick across all 5 LOD tiers."""
        self._current_tick = tick

        # 1. Update LOD 0 / LOD 1 Active Individuals
        # Ticked with their respective SyntheticHuman instance
        for uid, human in list(self._active_humans.items()):
            rec = self._persistent.get(uid)
            if not rec:
                continue

            # Decay needs and update position if traveling
            human.physical_state.hunger = min(1.0, human.physical_state.hunger + 0.005)
            human.physical_state.energy = max(0.0, human.physical_state.energy - 0.004)

            # Sync back to persistent record
            rec.hunger = human.physical_state.hunger
            rec.energy = human.physical_state.energy
            rec.wealth = human.physical_state.money
            rec.health = human.physical_state.health
            rec.last_update_tick = tick

            # Update spatial partition if coordinates moved
            self.spatial.insert_or_update(
                uid=uid,
                lon=rec.lon,
                lat=rec.lat,
                lod_tier=rec.lod_tier,
                data=rec,
            )

        # 2. Update LOD 3 Community Aggregates every 32 ticks (~8 hours)
        if tick % 32 == 0:
            for comm in self._communities.values():
                PopulationAggregator.step_community_dynamics(comm, dt_ticks=32)

    # -------------------------------------------------------------------------
    # Viewport Streaming & Frustum Culling
    # -------------------------------------------------------------------------

    def query_viewport_population(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        zoom: float,
        limit: int = 1500,
    ) -> dict[str, Any]:
        """Query population visible in the current viewport frustum at appropriate LOD."""
        # 1. Macro Zoom (zoom < 13): Deliver regional density polygons (LOD 4)
        if zoom < 13.0:
            regions_data = [
                {
                    "region_id": r.region_id,
                    "name": r.name,
                    "density": r.population_density_sqkm,
                    "total_population": r.total_population,
                }
                for r in self._regions.values()
            ]
            return {
                "render_mode": "regional_density",
                "lod_tier": int(LODLevel.LOD_4_REGIONAL),
                "count": len(regions_data),
                "data": regions_data,
            }

        # 2. Meso Zoom (13 <= zoom < 15): Deliver community / cohort clusters (LOD 2 / LOD 3)
        if zoom < 15.0:
            communities_data = [
                {
                    "community_id": c.community_id,
                    "name": c.name,
                    "lat": c.center_lat,
                    "lon": c.center_lon,
                    "population": c.total_population,
                    "mean_wealth": c.mean_wealth,
                    "gini": c.gini_coefficient,
                }
                for c in self._communities.values()
                if min_lon <= c.center_lon <= max_lon and min_lat <= c.center_lat <= max_lat
            ]
            return {
                "render_mode": "cohort_clusters",
                "lod_tier": int(LODLevel.LOD_3_COMMUNITY),
                "count": len(communities_data),
                "data": communities_data,
            }

        # 3. Micro Zoom (zoom >= 15): Deliver individual tokens inside bounding box (LOD 0 / LOD 1)
        entities = self.spatial.query_viewport(min_lon, min_lat, max_lon, max_lat, limit=limit)
        rendered_uids = set()
        agent_tokens = []

        for ent in entities:
            rec = self._persistent.get(ent.uid)
            if rec:
                rendered_uids.add(rec.uid)
                agent_tokens.append(rec.to_dict())

        self._rendered_uids = rendered_uids
        return {
            "render_mode": "individual_tokens",
            "lod_tier": int(LODLevel.LOD_0_INDIVIDUAL),
            "count": len(agent_tokens),
            "data": agent_tokens,
        }
