"""
Salvadoran Community Dynamics, ADESCOs, and Rotating Savings Engine (Section 19.8).

Models authentic community organization structures in El Salvador:
- ADESCOs (Asociaciones de Desarrollo Comunal):
  * Junta Directiva (Presidente, Tesorero, Síndico, Vocales)
  * Faenas Comunales: collective volunteer workdays to clear washed-out roads,
    clean ravines (quebradas), or build community water projects
- Cuchubales / Tandas:
  * Rotating informal credit and savings circles among neighbors and market women
- Local reputation and community communication ('chambre' vs. prestige of being 'trabajador/a')
"""

from __future__ import annotations
import dataclasses
from typing import Any, Optional


@dataclasses.dataclass
class FaenaComunalProject:
    """A collective volunteer work project organized by the local ADESCO."""
    project_id: str
    name: str
    community_id: str
    target_problem: str                  # e.g., "reparar_cuesta_de_tierra_tras_temporal"
    required_labor_hours: float = 40.0   # e.g., 10 neighbors x 4 hours
    accumulated_labor_hours: float = 0.0
    required_tools: list[str] = dataclasses.field(default_factory=lambda: ["palas", "picos", "carretillas"])
    volunteers_registered: set[str] = dataclasses.field(default_factory=set)
    is_completed: bool = False
    cohesion_boost: float = 0.0


@dataclasses.dataclass
class CuchubalSavingsCircle:
    """A rotating savings and credit association ('cuchubal' or 'tanda')."""
    circle_id: str
    name: str
    organizer_uid: str
    member_uids: list[str]
    contribution_per_turn_usd: float = 10.0 # e.g., $10 weekly
    current_turn_index: int = 0
    turns_completed: int = 0
    payout_history: list[dict[str, Any]] = dataclasses.field(default_factory=list)

    @property
    def total_pot_per_turn(self) -> float:
        return round(len(self.member_uids) * self.contribution_per_turn_usd, 2)


class ADESCOEngine:
    """Manages community organization, communal volunteer projects, and local mutual aid."""

    def __init__(self) -> None:
        self._faenas: dict[str, FaenaComunalProject] = {}
        self._cuchubales: dict[str, CuchubalSavingsCircle] = {}

    # -------------------------------------------------------------------------
    # ADESCO Faenas Comunales (Collective Community Projects)
    # -------------------------------------------------------------------------

    def create_faena_project(
        self,
        project_id: str,
        name: str,
        community_id: str,
        target_problem: str,
        required_hours: float = 30.0,
    ) -> FaenaComunalProject:
        """ADESCO assembly launches a collective work project."""
        project = FaenaComunalProject(
            project_id=project_id,
            name=name,
            community_id=community_id,
            target_problem=target_problem,
            required_labor_hours=required_hours,
        )
        self._faenas[project_id] = project
        return project

    def contribute_labor_to_faena(
        self,
        project_id: str,
        volunteer_uid: str,
        hours_contributed: float = 4.0,
    ) -> dict[str, Any]:
        """A neighbor participates with shovel and pick in the communal workday."""
        proj = self._faenas.get(project_id)
        if not proj:
            return {"success": False, "reason": "Project not found"}

        proj.volunteers_registered.add(volunteer_uid)
        proj.accumulated_labor_hours += hours_contributed

        if proj.accumulated_labor_hours >= proj.required_labor_hours:
            proj.is_completed = True
            proj.cohesion_boost = min(0.95, 0.40 + (len(proj.volunteers_registered) * 0.05))

        return {
            "success": True,
            "project_name": proj.name,
            "volunteer": volunteer_uid,
            "hours_given": hours_contributed,
            "total_accumulated_hours": proj.accumulated_labor_hours,
            "is_completed": proj.is_completed,
            "community_cohesion_generated": proj.cohesion_boost,
        }

    # -------------------------------------------------------------------------
    # Cuchubales / Tandas (Rotating Savings Circles)
    # -------------------------------------------------------------------------

    def create_cuchubal(
        self,
        circle_id: str,
        name: str,
        organizer_uid: str,
        member_uids: list[str],
        contribution_usd: float = 10.0,
    ) -> CuchubalSavingsCircle:
        """Establish a rotating savings circle between neighbors or market vendors."""
        all_members = [organizer_uid] + [m for m in member_uids if m != organizer_uid]
        circle = CuchubalSavingsCircle(
            circle_id=circle_id,
            name=name,
            organizer_uid=organizer_uid,
            member_uids=all_members,
            contribution_per_turn_usd=contribution_usd,
        )
        self._cuchubales[circle_id] = circle
        return circle

    def execute_cuchubal_turn(self, circle_id: str) -> dict[str, Any]:
        """Execute one round of the savings circle: members pay in, one receives the lump sum pot."""
        circle = self._cuchubales.get(circle_id)
        if not circle:
            return {"success": False, "reason": "Cuchubal not found"}

        if circle.turns_completed >= len(circle.member_uids):
            return {"success": False, "reason": "Cuchubal has already completed full cycle"}

        beneficiary_uid = circle.member_uids[circle.current_turn_index]
        pot_amount = circle.total_pot_per_turn

        record = {
            "turn_number": circle.turns_completed + 1,
            "beneficiary_uid": beneficiary_uid,
            "amount_awarded_usd": pot_amount,
            "contributing_members_count": len(circle.member_uids),
        }
        circle.payout_history.append(record)

        circle.turns_completed += 1
        circle.current_turn_index = (circle.current_turn_index + 1) % len(circle.member_uids)

        return {
            "success": True,
            "cuchubal_name": circle.name,
            "beneficiary": beneficiary_uid,
            "pot_received_usd": pot_amount,
            "turn": record["turn_number"],
            "total_turns_in_cycle": len(circle.member_uids),
            "cycle_finished": circle.turns_completed >= len(circle.member_uids),
        }
