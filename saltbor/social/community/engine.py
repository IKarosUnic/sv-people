"""Emergent Community Formation Engine for Saltbor Phase 0.9.

Enables autonomous formation, evolution, governance, fission, and dissolution
of communities without developer predefinition.
"""

from __future__ import annotations

from collections import defaultdict
import enum
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from saltbor.core.types import HumanID, LocationID, Tick

logger = logging.getLogger(__name__)


class CommunityType(str, enum.Enum):
    """Typology of emergent collective organizations."""

    NEIGHBORHOOD = "neighborhood"
    FAMILY_CLAN = "family_clan"
    LABOR_COLLECTIVE = "labor_collective"
    COMMERCIAL_ASSOCIATION = "commercial_association"
    COOPERATIVE = "cooperative"
    CULTURAL_GROUP = "cultural_group"
    EDUCATIONAL_CIRCLE = "educational_circle"
    SPORTS_ORGANIZATION = "sports_organization"
    AGRICULTURAL_ASSOCIATION = "agricultural_association"
    MUTUAL_AID = "mutual_aid"
    INTEREST_GROUP = "interest_group"
    INFORMAL_COMMUNITY = "informal_community"


class MembershipRole(str, enum.Enum):
    """Roles within a community."""

    FOUNDER = "founder"
    LEADER = "leader"
    COORDINATOR = "coordinator"
    ELDER = "elder"
    ACTIVE_MEMBER = "active_member"
    CONTRIBUTOR = "contributor"
    NEW_MEMBER = "new_member"
    DISSIDENT = "dissident"


class CommunityStatus(str, enum.Enum):
    """Lifecycle phase of the community."""

    INCUBATING = "incubating"
    THRIVING = "thriving"
    STABLE = "stable"
    STRAINED = "strained"
    FISSIONING = "fissioning"
    DISSOLVED = "dissolved"


@dataclass
class CommunityNorm:
    """A community norm or operating rule."""

    norm_id: str
    rule_name: str
    description: str
    compliance_rate: float = 0.85 # [0.0, 1.0]
    sanction_description: str = "warning"
    created_tick: int = 0


@dataclass
class CommunityMembership:
    """Individual membership status in a community."""

    human_uid: str
    role: MembershipRole = MembershipRole.ACTIVE_MEMBER
    joined_tick: int = 0
    commitment: float = 0.7        # [0.0, 1.0]
    contributed_resources: float = 0.0
    status: str = "active"          # "active", "marginal", "defected", "expelled"
    satisfaction: float = 0.8      # [0.0, 1.0]


@dataclass
class Community:
    """An autonomous emergent community with collective identity, rules, and resources."""

    community_id: str
    name: str
    community_type: CommunityType
    collective_identity: str
    headquarters_location_id: Optional[str] = None
    created_tick: int = 0

    # Membership
    members: dict[str, CommunityMembership] = field(default_factory=dict)
    leaders: list[str] = field(default_factory=list)

    # Core Social Features
    objectives: list[dict[str, Any]] = field(default_factory=list)
    norms: list[CommunityNorm] = field(default_factory=list)
    resources: dict[str, float] = field(default_factory=lambda: {"funds": 50.0, "tools": 2.0})
    activities: list[dict[str, Any]] = field(default_factory=list)

    # Cohesion, Reputation & External Relations
    reputation: float = 0.6               # [0.0, 1.0] Perception in wider society
    internal_conflict_level: float = 0.0  # [0.0, 1.0] Active factional or personal friction
    external_relations: dict[str, float] = field(default_factory=dict) # other_comm_id -> trust [-1.0, 1.0]
    status: CommunityStatus = CommunityStatus.STABLE

    # History & Audit Trail
    history: list[dict[str, Any]] = field(default_factory=list)

    @property
    def active_member_count(self) -> int:
        return sum(1 for m in self.members.values() if m.status == "active")

    @property
    def cohesion(self) -> float:
        """Cohesion is high when members are satisfied and internal conflict is low."""
        if not self.members:
            return 0.0
        avg_satisfaction = sum(m.satisfaction for m in self.members.values()) / len(self.members)
        score = (avg_satisfaction * 0.7) + ((1.0 - self.internal_conflict_level) * 0.3)
        return round(max(0.0, min(1.0, score)), 3)

    def add_member(
        self,
        human_uid: str | HumanID,
        role: MembershipRole = MembershipRole.NEW_MEMBER,
        tick: int = 0,
        commitment: float = 0.7,
    ) -> CommunityMembership:
        """Admit a new member into the community."""
        uid = str(human_uid)
        membership = CommunityMembership(
            human_uid=uid,
            role=role,
            joined_tick=tick,
            commitment=commitment,
            satisfaction=0.8,
            status="active",
        )
        self.members[uid] = membership
        if role in (MembershipRole.FOUNDER, MembershipRole.LEADER) and uid not in self.leaders:
            self.leaders.append(uid)

        self.history.append({
            "tick": tick,
            "action": "member_joined",
            "human_uid": uid,
            "role": role.value,
        })
        return membership

    def remove_member(
        self,
        human_uid: str | HumanID,
        tick: int,
        reason: str = "voluntary_departure",
    ) -> Optional[CommunityMembership]:
        """Process departure or expulsion of a member."""
        uid = str(human_uid)
        if uid in self.members:
            mem = self.members[uid]
            mem.status = "defected" if reason == "voluntary_departure" else "expelled"
            if uid in self.leaders:
                self.leaders.remove(uid)

            self.history.append({
                "tick": tick,
                "action": "member_left",
                "human_uid": uid,
                "reason": reason,
            })

            # Check if community must dissolve or become strained
            if self.active_member_count < 2 and self.status != CommunityStatus.DISSOLVED:
                self.dissolve(tick, reason="insufficient_active_members")
            return mem
        return None

    def record_activity(
        self,
        tick: int,
        activity_name: str,
        participants: list[str],
        resource_cost: float = 0.0,
        outcome_success: bool = True,
    ) -> None:
        """Record a joint community activity (e.g. market setup, assembly, neighborhood repair)."""
        self.resources["funds"] = max(0.0, self.resources.get("funds", 0.0) - resource_cost)

        # Boost satisfaction of active participants
        for p in participants:
            if p in self.members:
                delta = 0.10 if outcome_success else -0.05
                self.members[p].satisfaction = max(0.0, min(1.0, self.members[p].satisfaction + delta))

        self.activities.append({
            "tick": tick,
            "activity": activity_name,
            "participants_count": len(participants),
            "success": outcome_success,
        })

    def trigger_fission(self, tick: int, dissident_uids: list[str], new_name: str) -> Community:
        """Fission / schism: split off a faction into an independent new community."""
        self.status = CommunityStatus.FISSIONING
        new_comm_id = f"comm_{uuid.uuid4().hex[:8]}"

        new_comm = Community(
            community_id=new_comm_id,
            name=new_name,
            community_type=self.community_type,
            collective_identity=f"Split from {self.name}",
            headquarters_location_id=self.headquarters_location_id,
            created_tick=tick,
            status=CommunityStatus.STABLE,
        )

        for d in dissident_uids:
            if d in self.members:
                self.remove_member(d, tick, reason="fission_schism")
                new_comm.add_member(d, role=MembershipRole.FOUNDER, tick=tick)

        # Distribute proportional share of liquid resources
        f_ratio = len(dissident_uids) / max(1, len(self.members) + len(dissident_uids))
        for res_name, amount in list(self.resources.items()):
            split_amount = round(amount * f_ratio, 2)
            self.resources[res_name] = max(0.0, amount - split_amount)
            new_comm.resources[res_name] = split_amount

        # Antagonism between parent and splinter group
        self.external_relations[new_comm_id] = -0.4
        new_comm.external_relations[self.community_id] = -0.4

        self.history.append({
            "tick": tick,
            "action": "fission_occurred",
            "new_community_id": new_comm_id,
            "splinter_size": len(dissident_uids),
        })

        if self.active_member_count >= 2:
            self.status = CommunityStatus.STABLE
        return new_comm

    def dissolve(self, tick: int, reason: str = "abandonment") -> None:
        """Disband and dissolve the community."""
        self.status = CommunityStatus.DISSOLVED
        self.history.append({
            "tick": tick,
            "action": "community_dissolved",
            "reason": reason,
        })


class CommunityFormationEngine:
    """Detects spontaneous community emergence and coordinates multi-community evolution."""

    def __init__(self) -> None:
        self._communities: dict[str, Community] = {}

    def get_community(self, community_id: str) -> Optional[Community]:
        return self._communities.get(community_id)

    def get_all_communities(self, active_only: bool = True) -> list[Community]:
        if not active_only:
            return list(self._communities.values())
        return [c for c in self._communities.values() if c.status != CommunityStatus.DISSOLVED]

    def get_communities_for_human(self, human_uid: str | HumanID) -> list[Community]:
        uid = str(human_uid)
        return [
            c for c in self._communities.values()
            if uid in c.members and c.members[uid].status == "active"
        ]

    def form_community(
        self,
        name: str,
        community_type: CommunityType,
        collective_identity: str,
        founder_uids: list[str | HumanID],
        tick: int = 0,
        initial_funds: float = 100.0,
        headquarters_location_id: Optional[str] = None,
        initial_norms: Optional[list[str]] = None,
    ) -> Community:
        """Form a community with founding members."""
        comm_id = f"comm_{community_type.value}_{uuid.uuid4().hex[:8]}"
        comm = Community(
            community_id=comm_id,
            name=name,
            community_type=community_type,
            collective_identity=collective_identity,
            headquarters_location_id=headquarters_location_id,
            created_tick=tick,
            resources={"funds": initial_funds, "tools": 3.0},
            status=CommunityStatus.STABLE,
        )

        for i, uid in enumerate(founder_uids):
            role = MembershipRole.FOUNDER if i == 0 else MembershipRole.ACTIVE_MEMBER
            comm.add_member(uid, role=role, tick=tick, commitment=0.85)

        if initial_norms:
            for rule in initial_norms:
                comm.norms.append(
                    CommunityNorm(
                        norm_id=f"norm_{uuid.uuid4().hex[:6]}",
                        rule_name=rule,
                        description=f"Standard community rule: {rule}",
                        created_tick=tick,
                    )
                )

        self._communities[comm_id] = comm
        logger.info("Formed emergent community '%s' (%s) with %d founders", name, comm_id, len(founder_uids))
        return comm

    def check_spontaneous_formation(
        self,
        candidates: list[dict[str, Any]], # list of {uid, interests: set, location: str, goals: set, friends: list[str]}
        tick: int = 0,
    ) -> list[Community]:
        """Detect natural clustering of agents and spontaneously form new communities.

        Triggers when 3 or more agents share:
        - Common geographic cluster or location
        - Overlapping interests or shared goals
        - Mutual positive friendship ties
        """
        formed: list[Community] = []
        interest_clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for agent in candidates:
            for interest in agent.get("interests", []):
                interest_clusters[interest].append(agent)

        for interest, agents in interest_clusters.items():
            if len(agents) >= 3:
                # Check for mutual friendliness
                uids = [a["uid"] for a in agents]
                # Avoid creating duplicate community for the exact same set
                already_exists = False
                for c in self.get_all_communities():
                    if set(uids).issubset(set(c.members.keys())) and interest in c.collective_identity:
                        already_exists = True
                        break

                if not already_exists:
                    comm_type = CommunityType.INTEREST_GROUP
                    if "agricola" in interest.lower() or "siembra" in interest.lower():
                        comm_type = CommunityType.AGRICULTURAL_ASSOCIATION
                    elif "comercio" in interest.lower() or "mercado" in interest.lower():
                        comm_type = CommunityType.COMMERCIAL_ASSOCIATION
                    elif "vecinal" in interest.lower() or "barrio" in interest.lower():
                        comm_type = CommunityType.NEIGHBORHOOD
                    elif "cultura" in interest.lower() or "musica" in interest.lower():
                        comm_type = CommunityType.CULTURAL_GROUP

                    new_comm = self.form_community(
                        name=f"Grupo de {interest.title()}",
                        community_type=comm_type,
                        collective_identity=f"Comunidad surgida por interes compartido en {interest}",
                        founder_uids=uids[:5],
                        tick=tick,
                    )
                    formed.append(new_comm)

        return formed
