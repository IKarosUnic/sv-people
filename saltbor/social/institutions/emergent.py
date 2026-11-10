"""Emergent Institutions Engine for Saltbor Phase 0.9.

Models the institutionalization process: how spontaneous communities codify
rules, formalize procedures, designate authority, steward resources, and
undergo reform, crisis of legitimacy, or dissolution.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
import uuid
from typing import Any, Optional

from saltbor.core.types import HumanID, LocationID, Tick

logger = logging.getLogger(__name__)


class InstitutionCategory(str, enum.Enum):
    """Broad categories of emergent institutions."""

    NEIGHBORHOOD_COUNCIL = "neighborhood_council"
    AGRICULTURAL_BOARD = "agricultural_board"
    COMMERCIAL_SYNDICATE = "commercial_syndicate"
    MUTUAL_AID_SOCIETY = "mutual_aid_society"
    CULTURAL_CONFRATERNITY = "cultural_confraternity"
    COMMUNITY_TRIBUNAL = "community_tribunal"


@dataclasses.dataclass
class FormalProcedure:
    """An institutionalized operating procedure."""

    procedure_id: str
    name: str
    purpose: str
    trigger_condition: str
    required_signatories: int = 1
    action_steps: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class EmergentInstitution:
    """A formalized institution evolved from an emergent community."""

    institution_id: str
    name: str
    category: InstitutionCategory
    parent_community_id: Optional[str]
    charter_mission: str
    headquarters_location_id: Optional[str]
    created_tick: int = 0

    # Formal Rules & Procedures
    constitution_bylaws: list[str] = dataclasses.field(default_factory=list)
    formal_procedures: list[FormalProcedure] = dataclasses.field(default_factory=list)
    official_roles: dict[str, str] = dataclasses.field(default_factory=dict) # human_uid -> role_name

    # Resources & Assets
    endowment_funds: float = 200.0
    managed_assets: list[str] = dataclasses.field(default_factory=list)

    # Legitimacy & Institutional Health
    legitimacy_score: float = 0.85 # [0.0, 1.0]
    is_active: bool = True
    evolution_history: list[dict[str, Any]] = dataclasses.field(default_factory=list)

    def formalize_rule(self, rule_text: str, tick: int) -> None:
        """Enact a formal constitutional bylaw."""
        self.constitution_bylaws.append(rule_text)
        self.evolution_history.append({
            "tick": tick,
            "action": "rule_enacted",
            "rule": rule_text,
        })

    def appoint_officer(self, human_uid: str, role_title: str, tick: int) -> None:
        """Designate an official administrative office holder."""
        self.official_roles[human_uid] = role_title
        self.evolution_history.append({
            "tick": tick,
            "action": "officer_appointed",
            "uid": human_uid,
            "role": role_title,
        })

    def suffer_legitimacy_crisis(self, penalty: float, reason: str, tick: int) -> None:
        """Legitimacy degradation following corruption, incompetence, or abuse of power."""
        self.legitimacy_score = max(0.0, self.legitimacy_score - penalty)
        self.evolution_history.append({
            "tick": tick,
            "action": "legitimacy_crisis",
            "penalty": penalty,
            "reason": reason,
            "remaining_legitimacy": self.legitimacy_score,
        })
        if self.legitimacy_score <= 0.20:
            self.is_active = False


class EmergentInstitutionEngine:
    """Manages creation, codification, reform, and lifecycle of formal institutions."""

    def __init__(self) -> None:
        self._institutions: dict[str, EmergentInstitution] = {}

    def get_institution(self, inst_id: str) -> Optional[EmergentInstitution]:
        return self._institutions.get(inst_id)

    def get_all(self, active_only: bool = True) -> list[EmergentInstitution]:
        if not active_only:
            return list(self._institutions.values())
        return [inst for inst in self._institutions.values() if inst.is_active]

    def formalize_from_community(
        self,
        community_id: str,
        name: str,
        category: InstitutionCategory,
        charter: str,
        officers: dict[str, str], # uid -> role
        initial_rules: list[str],
        headquarters_location_id: Optional[str] = None,
        tick: int = 0,
    ) -> EmergentInstitution:
        """Codify an informal community into a persistent formal institution."""
        inst_id = f"inst_{category.value[:4]}_{uuid.uuid4().hex[:6]}"
        inst = EmergentInstitution(
            institution_id=inst_id,
            name=name,
            category=category,
            parent_community_id=community_id,
            charter_mission=charter,
            headquarters_location_id=headquarters_location_id,
            created_tick=tick,
            constitution_bylaws=list(initial_rules),
            official_roles=dict(officers),
        )
        self._institutions[inst_id] = inst
        logger.info("Codified emergent institution '%s' (%s)", name, inst_id)
        return inst
