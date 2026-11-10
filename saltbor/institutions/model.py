"""Institutions: cooperatives, mutual assistance networks, councils, and guilds."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from saltbor.core.types import HumanID, LocationID, Tick
from saltbor.economy.inventory.container import Inventory
from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


class InstitutionType(enum.Enum):
    """Broad categories of community institutions in Saltbor."""

    AGRICULTURAL_COOPERATIVE = "agricultural_cooperative" # Shared grain storage, seed purchasing, equipment
    MUTUAL_AID_NETWORK = "mutual_aid_network"             # Emergency relief funds, medical care, bereavement
    TRADE_GUILD = "trade_guild"                           # Artisanal apprenticeship, quality standards, wage setting
    COMMUNITY_COUNCIL = "community_council"               # Deliberative neighborhood governance and dispute resolution
    EDUCATIONAL_INSTITUTION = "educational_institution"   # Community school, vocational literacy, technical skills
    CIVIC_ASSOCIATION = "civic_association"               # Festival planning, park upkeep, road maintenance


class MemberRole(enum.Enum):
    """Functional role within an institutional hierarchy."""

    PRESIDENT = "president"
    TREASURER = "treasurer"
    SECRETARY = "secretary"
    COORDINATOR = "coordinator"
    MASTER_CRAFTSMAN = "master_craftsman"
    ACTIVE_MEMBER = "active_member"
    APPRENTICE = "apprentice"
    ELDER_ADVISOR = "elder_advisor"


@dataclass
class InstitutionalPolicy:
    """An enacted community policy with concrete effects on the artificial society."""

    policy_id: str
    title: str
    target_area: str  # "economy", "social_welfare", "public_works", "education"
    description: str
    enacted_tick: Tick
    parameters: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


@dataclass
class SocialInstitution:
    """A persistent collective organization with rules, roles, treasury, and world effects."""

    institution_id: str
    name: str
    institution_type: InstitutionType
    charter_description: str
    headquarters_location_id: LocationID
    created_tick: Tick = 0

    # Membership and Internal Hierarchy
    members: dict[HumanID, MemberRole] = field(default_factory=dict)
    responsibilities: dict[MemberRole, str] = field(default_factory=dict)

    # Collective Treasury and Assets
    treasury_money: float = 100.0
    treasury_inventory: Inventory = field(default_factory=lambda: Inventory(capacity_volume=300.0))
    periodic_dues: float = 2.0  # Dues collected from members every 96 ticks

    # Institutional Reputation, Legitimacy, and Rules
    reputation: float = 0.6          # 0.0 to 1.0 (community trust in institution)
    legitimacy: float = 0.8          # Member satisfaction with leadership
    bylaws: list[str] = field(default_factory=list)
    enacted_policies: list[InstitutionalPolicy] = field(default_factory=list)

    # History & Provenance
    history_log: list[str] = field(default_factory=list)

    @property
    def member_count(self) -> int:
        return len(self.members)

    def add_member(self, human_uid: HumanID, role: MemberRole = MemberRole.ACTIVE_MEMBER) -> None:
        self.members[human_uid] = role
        self.history_log.append(f"Member {human_uid} joined as {role.value}")
        logger.info("Institution %s: Member %s enrolled as %s", self.name, human_uid, role.value)

    def remove_member(self, human_uid: HumanID, reason: str = "voluntary departure") -> bool:
        if human_uid in self.members:
            role = self.members.pop(human_uid)
            self.history_log.append(f"Member {human_uid} ({role.value}) departed: {reason}")
            logger.info("Institution %s: Member %s departed (%s)", self.name, human_uid, reason)
            return True
        return False

    def collect_dues_from_members(self, population_registry: Any, current_tick: Tick) -> float:
        """Collect periodic operational contributions from members."""
        total_collected = 0.0
        for uid in list(self.members.keys()):
            human = population_registry.get_optional(uid)
            if human and human.physical_state.money >= self.periodic_dues:
                human.physical_state.money -= self.periodic_dues
                self.treasury_money += self.periodic_dues
                total_collected += self.periodic_dues
            elif human:
                # Inability to pay reduces legitimacy slightly
                self.legitimacy = max(0.2, self.legitimacy - 0.01)

        self.history_log.append(f"Tick {current_tick}: Collected dues totaling ${total_collected:.2f}")
        return total_collected

    def disburse_mutual_aid(
        self,
        beneficiary: SyntheticHuman,
        amount: float,
        reason: str,
        current_tick: Tick,
    ) -> bool:
        """Disburse assistance to a distressed member or family."""
        if self.treasury_money < amount:
            self.history_log.append(f"Tick {current_tick}: Failed to disburse aid to {beneficiary.name} (insufficient funds)")
            return False

        self.treasury_money -= amount
        beneficiary.physical_state.money += amount
        self.legitimacy = min(1.0, self.legitimacy + 0.05)
        self.reputation = min(1.0, self.reputation + 0.04)
        self.history_log.append(f"Tick {current_tick}: Disbursed aid ${amount:.2f} to {beneficiary.name} ({reason})")
        logger.info("Institution %s disbursed aid of $%.2f to %s", self.name, amount, beneficiary.name)
        return True
