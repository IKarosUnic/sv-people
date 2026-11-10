"""Festivals and collective community events requiring physical resources, labor, and coordination."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from saltbor.core.types import HumanID, LocationID, Tick
from saltbor.culture.element import CulturalElement, CulturalElementType
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import ItemType
from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


class FestivalStatus(enum.Enum):
    """Execution status of a community festival or gathering."""

    PROPOSED = "proposed"              # Table-stage: collecting resources & volunteers
    PREPARING = "preparing"            # Active labor and material accumulation
    CELEBRATING = "celebrating"        # Live gathering taking place
    COMPLETED = "completed"            # Successfully held and concluded
    POSTPONED = "postponed"            # Delayed due to resource or participation shortfall
    FAILED = "failed"                  # Cancelled or aborted due to acute crisis / deficit


@dataclass
class Festival:
    """A community celebration requiring real material stockpiles, labor, and participant turnout."""

    festival_id: str
    name: str
    description: str
    host_location_id: LocationID
    organizer_uids: set[HumanID] = field(default_factory=set)
    scheduled_tick: Tick = 0
    duration_ticks: int = 8            # Typically 2 hours (8 ticks)
    status: FestivalStatus = FestivalStatus.PROPOSED

    # Physical Requirements
    required_food: float = 12.0        # Meals or food rations required
    required_wood: float = 4.0         # Wood for tables, decorations, firewood
    required_labor_ticks: int = 12     # Cumulative preparation labor needed
    accumulated_food: float = 0.0
    accumulated_wood: float = 0.0
    accumulated_labor: int = 0

    # Participants
    attendee_uids: set[HumanID] = field(default_factory=set)
    minimum_attendance: int = 4

    # Cultural & Social Outcomes
    result_summary: str = ""
    social_cohesion_generated: float = 0.0
    established_as_tradition_id: Optional[str] = None
    annual_recurrence_ticks: Optional[int] = None  # e.g. 35040 ticks for annual recurring tradition

    def is_materially_ready(self) -> bool:
        return (
            self.accumulated_food >= self.required_food
            and self.accumulated_wood >= self.required_wood
            and self.accumulated_labor >= self.required_labor_ticks
        )

    def contribute_resources(self, food_qty: float = 0.0, wood_qty: float = 0.0) -> None:
        self.accumulated_food += max(0.0, food_qty)
        self.accumulated_wood += max(0.0, wood_qty)

    def contribute_labor(self, worker_uid: HumanID, ticks: int = 1) -> None:
        self.organizer_uids.add(worker_uid)
        self.accumulated_labor += max(1, ticks)


class FestivalManager:
    """Oversees proposal, resource pooling, celebration, and tradition formation of festivals."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()
        self.festivals: dict[str, Festival] = {}

    def propose_festival(
        self,
        festival_id: str,
        name: str,
        description: str,
        host_location_id: LocationID,
        scheduled_tick: Tick,
        required_food: float = 10.0,
        required_wood: float = 4.0,
        required_labor: int = 8,
        proposer_uid: Optional[HumanID] = None,
    ) -> Festival:
        """Create a new festival proposal."""
        fest = Festival(
            festival_id=festival_id,
            name=name,
            description=description,
            host_location_id=host_location_id,
            scheduled_tick=scheduled_tick,
            required_food=required_food,
            required_wood=required_wood,
            required_labor_ticks=required_labor,
        )
        if proposer_uid:
            fest.organizer_uids.add(proposer_uid)
        self.festivals[festival_id] = fest
        logger.info("Festival proposed: '%s' scheduled for tick %d", name, scheduled_tick)
        return fest

    def prepare_step(
        self,
        festival_id: str,
        volunteer: SyntheticHuman,
        food_donation: float = 0.0,
        wood_donation: float = 0.0,
        labor_ticks: int = 1,
    ) -> bool:
        """A community member contributes materials and labor toward festival preparation."""
        fest = self.festivals.get(festival_id)
        if not fest or fest.status in (FestivalStatus.COMPLETED, FestivalStatus.FAILED):
            return False

        fest.status = FestivalStatus.PREPARING
        fest.contribute_resources(food_donation, wood_donation)
        fest.contribute_labor(volunteer.uid, labor_ticks)
        return True

    def execute_celebration(
        self,
        festival_id: str,
        current_tick: Tick,
        attendees: list[SyntheticHuman],
    ) -> tuple[bool, str, Optional[CulturalElement]]:
        """Attempt to hold the festival. Evaluates physical feasibility and turnout.

        If successful:
        - Material resources are consumed.
        - Attendees gain positive emotional valence and social cohesion.
        - May solidify into an emergent CulturalElement (tradition or custom).
        """
        fest = self.festivals.get(festival_id)
        if not fest:
            return False, "Festival not found", None

        # Check material prerequisites
        if not fest.is_materially_ready():
            # Check if postponement or outright failure
            if current_tick > fest.scheduled_tick + 96:
                fest.status = FestivalStatus.FAILED
                fest.result_summary = "Failed due to material deficit: food or wood requirements unfulfilled."
                logger.warning("Festival '%s' failed due to material shortage.", fest.name)
                return False, fest.result_summary, None
            else:
                fest.status = FestivalStatus.POSTPONED
                fest.scheduled_tick += 48  # Postpone by 12 hours
                fest.result_summary = f"Postponed to tick {fest.scheduled_tick} awaiting resources."
                return False, fest.result_summary, None

        # Check turnout
        fest.attendee_uids = {h.uid for h in attendees}
        if len(fest.attendee_uids) < fest.minimum_attendance:
            fest.status = FestivalStatus.POSTPONED
            fest.scheduled_tick += 48
            fest.result_summary = f"Postponed: insufficient community turnout ({len(fest.attendee_uids)} < {fest.minimum_attendance})."
            return False, fest.result_summary, None

        # Execute successful celebration!
        fest.status = FestivalStatus.COMPLETED
        cohesion = 0.15 + 0.02 * len(attendees)
        fest.social_cohesion_generated = round(cohesion, 3)

        # Distribute emotional joy and motivation to attendees
        for human in attendees:
            if human.emotions:
                human.emotions.add_emotional_charge("joy", 0.35, current_tick)
                human.emotions.add_emotional_charge("motivation", 0.25, current_tick)
                human.emotions.add_emotional_charge("loneliness", -0.40, current_tick)

        fest.result_summary = (
            f"Celebrated successfully at {fest.host_location_id} with {len(attendees)} participants. "
            f"Consumed {fest.required_food:.1f} food and {fest.required_wood:.1f} wood."
        )

        # Emergence of lasting cultural element
        tradition_elem = CulturalElement(
            element_id=f"trad_{fest.festival_id}",
            name=f"Tradición de {fest.name}",
            element_type=CulturalElementType.CELEBRATION,
            description=f"Annual/seasonal communal celebration established through collective effort: {fest.description}",
            origin_location_id=fest.host_location_id,
            created_tick=current_tick,
            practitioners=set(fest.attendee_uids),
            geographic_distribution={fest.host_location_id: len(attendees)},
            required_materials={"food": fest.required_food, "wood": fest.required_wood},
            required_labor_ticks=fest.required_labor_ticks,
            social_cohesion_bonus=cohesion,
        )
        fest.established_as_tradition_id = tradition_elem.element_id
        logger.info("Festival '%s' SUCCESSFUL! Established cultural tradition '%s'", fest.name, tradition_elem.name)
        return True, fest.result_summary, tradition_elem
