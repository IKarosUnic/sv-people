"""Cognitive Level of Detail (LOD) architecture for scalable population simulation."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional

from saltbor.core.types import ActivityType, HumanID


class CognitiveLOD(enum.Enum):
    """Execution detail tiers for individual cognitive processing."""

    LOD_0_FULL = 0       # Full cognition: deliberate MAUT, continuous steering, full episodic encoding
    LOD_1_ROUTINE = 1    # Reduced cognition: executing daily routines, simplified heuristic updates
    LOD_2_EVENT_DRIVEN = 2 # Event-driven: sleeping, home resting, updated on event/phase boundary
    LOD_3_DORMANT = 3    # Dormant state: deceased or archived, zero tick computation, preserved in history


@dataclass
class LODAssignment:
    """Tracks current LOD tier, focus status, and tick skip counters for an individual."""

    human_uid: HumanID
    tier: CognitiveLOD = CognitiveLOD.LOD_0_FULL
    is_focal_agent: bool = False
    ticks_in_tier: int = 0
    skip_tick_counter: int = 0


class CognitiveLODManager:
    """Dynamically modulates cognitive fidelity based on context, proximity, and activity."""

    def __init__(self, focal_uids: Optional[set[HumanID]] = None) -> None:
        self.focal_uids: set[HumanID] = set(focal_uids or set())
        self._assignments: dict[HumanID, LODAssignment] = {}

    def get_assignment(self, human_uid: HumanID) -> LODAssignment:
        if human_uid not in self._assignments:
            is_focal = human_uid in self.focal_uids
            self._assignments[human_uid] = LODAssignment(
                human_uid=human_uid,
                is_focal_agent=is_focal,
                tier=CognitiveLOD.LOD_0_FULL if is_focal else CognitiveLOD.LOD_1_ROUTINE,
            )
        return self._assignments[human_uid]

    def set_focal_agent(self, human_uid: HumanID, is_focal: bool = True) -> None:
        if is_focal:
            self.focal_uids.add(human_uid)
        else:
            self.focal_uids.discard(human_uid)
        assignment = self.get_assignment(human_uid)
        assignment.is_focal_agent = is_focal
        if is_focal:
            assignment.tier = CognitiveLOD.LOD_0_FULL

    def evaluate_lod(
        self,
        human_uid: HumanID,
        is_alive: bool,
        current_activity: Optional[ActivityType],
        activity_ticks_remaining: int,
        is_interacting: bool = False,
    ) -> CognitiveLOD:
        """Determine appropriate LOD tier for an individual in current tick."""
        assignment = self.get_assignment(human_uid)

        # 1. Deceased -> LOD 3 (Dormant)
        if not is_alive:
            assignment.tier = CognitiveLOD.LOD_3_DORMANT
            return CognitiveLOD.LOD_3_DORMANT

        # 2. Focal agent or currently interacting with someone -> LOD 0
        if assignment.is_focal_agent or is_interacting:
            assignment.tier = CognitiveLOD.LOD_0_FULL
            return CognitiveLOD.LOD_0_FULL

        # 3. Long duration sleep or home rest -> LOD 2 (Event-Driven)
        if current_activity in (ActivityType.SLEEP, ActivityType.REST) and activity_ticks_remaining > 4:
            assignment.tier = CognitiveLOD.LOD_2_EVENT_DRIVEN
            return CognitiveLOD.LOD_2_EVENT_DRIVEN

        # 4. Active routine work / study / travel -> LOD 1 (Routine)
        if activity_ticks_remaining > 0:
            assignment.tier = CognitiveLOD.LOD_1_ROUTINE
            return CognitiveLOD.LOD_1_ROUTINE

        # 5. Deliberating or choosing new actions -> LOD 0
        assignment.tier = CognitiveLOD.LOD_0_FULL
        return CognitiveLOD.LOD_0_FULL

    def should_execute_tick(self, human_uid: HumanID) -> bool:
        """Check whether the agent should compute this discrete tick given its LOD."""
        assignment = self.get_assignment(human_uid)
        tier = assignment.tier

        if tier == CognitiveLOD.LOD_3_DORMANT:
            return False

        if tier == CognitiveLOD.LOD_0_FULL:
            return True

        if tier == CognitiveLOD.LOD_1_ROUTINE:
            # Execute every tick but skip fine deliberations
            return True

        if tier == CognitiveLOD.LOD_2_EVENT_DRIVEN:
            # Macro-step: update every 4 ticks
            assignment.skip_tick_counter += 1
            if assignment.skip_tick_counter >= 4:
                assignment.skip_tick_counter = 0
                return True
            return False

        return True
