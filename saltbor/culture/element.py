"""Cultural elements: traditions, customs, shared practices, foodways, and community norms.

Culture emerges from repeated individual and collective behavior, characterized by
unique origin, transmission history, geographic distribution, and dynamic adoption.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID, uuid4

from saltbor.core.types import HumanID, LocationID, Tick


class CulturalElementType(enum.Enum):
    """Categories of cultural elements emerging in Saltbor."""

    TRADITION = "tradition"                    # Multi-generational customary practice
    CUSTOM = "custom"                          # Habitual daily or weekly routine
    COMMUNITY_PRACTICE = "community_practice"  # Collective mutual aid or civic activity
    CELEBRATION = "celebration"                # Festival, seasonal feast, or anniversary
    SHARED_KNOWLEDGE = "shared_knowledge"      # Ecological, agricultural, or medicinal lore
    LOCAL_EXPRESSION = "local_expression"      # Regional idioms, proverbs, colloquial terms
    SKILL_CRAFT = "skill_craft"                # Distinctive artisanal technique or craft method
    FOOD_PRACTICE = "food_practice"            # Culinary recipes, preservation methods, communal eating
    SOCIAL_EXPECTATION = "social_expectation"  # Norms of reciprocity, respect, elder deference
    COLLECTIVE_MEMORY = "collective_memory"    # Shared memory of a flood, founding, or economic crisis
    INFORMAL_RULE = "informal_rule"            # Unwritten community understanding or boundary
    COMMUNITY_IDENTITY = "community_identity"  # Shared sense of belonging and civic pride


@dataclass
class TransmissionEvent:
    """Historical provenance of a single cultural transmission event."""

    from_human_id: Optional[HumanID]
    to_human_id: HumanID
    channel: str  # "family", "friendship", "mentorship", "observation", "festival", "dialogue"
    tick: Tick
    accepted: bool
    modified: bool = False
    notes: str = ""


@dataclass
class CulturalElement:
    """A distinct cultural element circulating and evolving within the artificial society."""

    element_id: str
    name: str
    element_type: CulturalElementType
    description: str
    origin_human_id: Optional[HumanID] = None
    origin_location_id: Optional[LocationID] = None
    origin_group_id: Optional[str] = None
    created_tick: Tick = 0

    # Practitioners and Adoption
    practitioners: set[HumanID] = field(default_factory=set)
    geographic_distribution: dict[LocationID, int] = field(default_factory=dict)
    associated_groups: set[str] = field(default_factory=set)

    # Transmission and Evolution Provenance
    transmission_history: list[TransmissionEvent] = field(default_factory=list)
    variant_of_id: Optional[str] = None  # Parent tradition if reinterpreted/modified
    mutations_count: int = 0
    authenticity: float = 1.0            # 0.0 to 1.0 (drift from original practice)
    confidence: float = 1.0              # Subjective certainty of practitioners

    # Persistence, Vitality, and Abandonment Conditions
    last_practiced_tick: Tick = 0
    consecutive_dormant_ticks: int = 0
    inactivity_threshold_ticks: int = 2880  # ~30 simulated days of disuse before abandonment
    minimum_adoption_threshold: int = 1
    is_abandoned: bool = False
    is_institutionalized: bool = False     # Adopted as an official institutional custom

    # Material & Social Consequence Parameters
    required_materials: dict[str, float] = field(default_factory=dict)  # e.g. {"grain": 2.0}
    required_labor_ticks: int = 1
    social_cohesion_bonus: float = 0.05
    energy_cost: float = 0.05

    @property
    def adoption_count(self) -> int:
        return len(self.practitioners)

    def is_active(self) -> bool:
        return not self.is_abandoned and self.adoption_count >= self.minimum_adoption_threshold

    def register_adoption(
        self,
        human_id: HumanID,
        location_id: Optional[LocationID],
        tick: Tick,
        from_human_id: Optional[HumanID] = None,
        channel: str = "observation",
        modified: bool = False,
    ) -> None:
        """Register a synthetic human adopting this cultural element."""
        self.practitioners.add(human_id)
        if location_id:
            self.geographic_distribution[location_id] = (
                self.geographic_distribution.get(location_id, 0) + 1
            )
        self.last_practiced_tick = tick
        self.consecutive_dormant_ticks = 0
        self.is_abandoned = False

        self.transmission_history.append(
            TransmissionEvent(
                from_human_id=from_human_id,
                to_human_id=human_id,
                channel=channel,
                tick=tick,
                accepted=True,
                modified=modified,
            )
        )

    def register_abandonment(self, human_id: HumanID, location_id: Optional[LocationID]) -> None:
        """Register an individual ceasing practice of this element."""
        self.practitioners.discard(human_id)
        if location_id and location_id in self.geographic_distribution:
            self.geographic_distribution[location_id] = max(
                0, self.geographic_distribution[location_id] - 1
            )
            if self.geographic_distribution[location_id] == 0:
                del self.geographic_distribution[location_id]

    def check_vitality(self, current_tick: Tick) -> bool:
        """Evaluate whether this element remains viable or falls into abandonment."""
        if not self.practitioners:
            self.consecutive_dormant_ticks = current_tick - self.last_practiced_tick
            if self.consecutive_dormant_ticks > self.inactivity_threshold_ticks:
                self.is_abandoned = True
                return False
        else:
            self.consecutive_dormant_ticks = 0
            self.is_abandoned = False
        return not self.is_abandoned

    def create_mutation(
        self,
        innovator_uid: HumanID,
        new_name: str,
        modification_desc: str,
        current_tick: Tick,
        material_shift: Optional[dict[str, float]] = None,
    ) -> CulturalElement:
        """Spawn an adapted or reinterpreted cultural variant from this parent element."""
        mutated_id = f"{self.element_id}_v{self.mutations_count + 1}"
        new_materials = dict(self.required_materials)
        if material_shift:
            new_materials.update(material_shift)

        mutated = CulturalElement(
            element_id=mutated_id,
            name=new_name,
            element_type=self.element_type,
            description=f"{self.description} (Adapted: {modification_desc})",
            origin_human_id=innovator_uid,
            origin_location_id=self.origin_location_id,
            origin_group_id=self.origin_group_id,
            created_tick=current_tick,
            variant_of_id=self.element_id,
            mutations_count=0,
            authenticity=max(0.2, round(self.authenticity * 0.85, 3)),
            confidence=round(self.confidence * 0.95, 3),
            last_practiced_tick=current_tick,
            required_materials=new_materials,
            required_labor_ticks=self.required_labor_ticks,
            social_cohesion_bonus=self.social_cohesion_bonus,
            energy_cost=self.energy_cost,
        )
        self.mutations_count += 1
        mutated.register_adoption(
            human_id=innovator_uid,
            location_id=self.origin_location_id,
            tick=current_tick,
            from_human_id=innovator_uid,
            channel="innovation",
            modified=True,
        )
        return mutated
