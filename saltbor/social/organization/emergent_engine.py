"""Emergent Organization Engine for SALTBOR Phase 1.9.

Models the autonomous emergence, operation, factionalism, fission, merger,
transformation, and dissolution of collective human organizations in El Salvador.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class OrganizationType(str, enum.Enum):
    """Broad typologies of emergent Salvadoran organizations."""

    COMMERCIAL_ASSOCIATION = "commercial_association" # Vendedoras de mercado, gremio de comerciantes
    AGRICULTURAL_COOPERATIVE = "agricultural_coop"     # Cooperativa de granos básicos / hortalizas
    NEIGHBORHOOD_BOARD = "neighborhood_board"         # Comité vecinal / Junta comunal
    MUTUAL_AID_SOCIETY = "mutual_aid_society"         # Sociedad de socorro mutuo / entierro
    LABOR_UNION = "labor_union"                       # Sindicato de jornaleros / gremio de artesanos
    TRANSPORT_COLLECTIVE = "transport_collective"     # Colectivo de fletes / transporte local
    PRODUCER_GUILD = "producer_guild"                 # Gremio de panificadores / alfareros
    CULTURAL_COFRADIA = "cultural_cofradia"           # Cofradía patronal / grupo folclórico


class MemberRole(str, enum.Enum):
    """Roles within the internal organizational hierarchy."""

    FOUNDER = "founder"
    PRESIDENT = "president"
    TREASURER = "treasurer"
    SECRETARY = "secretary"
    COORDINATOR = "coordinator"
    ACTIVE_MEMBER = "active_member"
    APPRENTICE = "apprentice"
    DISSIDENT = "dissident"


class OrgLifecycleStatus(str, enum.Enum):
    """Status in organizational lifecycle."""

    INCUBATING = "incubating"
    THRIVING = "thriving"
    STABLE = "stable"
    STRAINED = "strained"
    FISSIONED = "fissioned"
    MERGED = "merged"
    DISSOLVED = "dissolved"


@dataclasses.dataclass
class OrganizationMembership:
    """An individual agent's affiliation and standing within an organization."""

    human_uid: str
    role: MemberRole = MemberRole.ACTIVE_MEMBER
    joined_tick: int = 0
    commitment: float = 0.80           # [0.0, 1.0] Willingness to contribute dues/labor
    satisfaction: float = 0.80         # [0.0, 1.0] Approval of leadership and direction
    faction_id: Optional[str] = None   # Subgroup identity if internal division arises
    status: str = "active"             # "active", "defected", "expelled"


@dataclasses.dataclass
class EmergentOrganization:
    """An autonomous organization created and sustained by synthetic humans."""

    org_id: str
    name: str
    org_type: OrganizationType
    mission_purpose: str
    founding_tick: int
    headquarters_location_id: Optional[str] = None
    territory_scope: str = "local"     # "canton", "barrio", "municipality", "regional"

    # Membership and Internal Roster
    members: dict[str, OrganizationMembership] = dataclasses.field(default_factory=dict)
    leaders: list[str] = dataclasses.field(default_factory=list)

    # Treasury, Inventory, and Capital Assets
    treasury_usd: float = 100.0
    shared_inventory: dict[str, float] = dataclasses.field(default_factory=dict)
    periodic_dues_usd: float = 1.50

    # Social Health, Legitimacy, and Cohesion
    legitimacy: float = 0.85           # [0.0, 1.0] Member trust in leadership
    internal_conflict_level: float = 0.0 # [0.0, 1.0] Factional strife
    status: OrgLifecycleStatus = OrgLifecycleStatus.STABLE

    # Provenance and History
    history_log: list[str] = dataclasses.field(default_factory=list)

    @property
    def active_member_count(self) -> int:
        return sum(1 for m in self.members.values() if m.status == "active")

    @property
    def cohesion(self) -> float:
        if not self.members:
            return 0.0
        active_mems = [m for m in self.members.values() if m.status == "active"]
        if not active_mems:
            return 0.0
        avg_sat = sum(m.satisfaction for m in active_mems) / len(active_mems)
        score = (avg_sat * 0.70) + ((1.0 - self.internal_conflict_level) * 0.30)
        return round(max(0.0, min(1.0, score)), 3)

    def add_member(
        self,
        human_uid: str,
        role: MemberRole = MemberRole.ACTIVE_MEMBER,
        tick: int = 0,
    ) -> OrganizationMembership:
        """Enroll member in the organization."""
        mem = OrganizationMembership(
            human_uid=str(human_uid),
            role=role,
            joined_tick=tick,
        )
        self.members[str(human_uid)] = mem
        if role in (MemberRole.FOUNDER, MemberRole.PRESIDENT) and str(human_uid) not in self.leaders:
            self.leaders.append(str(human_uid))
        self.history_log.append(f"Tick {tick}: {human_uid} joined as {role.value}")
        return mem

    def remove_member(
        self,
        human_uid: str,
        reason: str = "voluntary_departure",
        tick: int = 0,
    ) -> bool:
        """Process departure or expulsion of a member."""
        uid = str(human_uid)
        if uid in self.members:
            mem = self.members[uid]
            mem.status = "defected" if reason == "voluntary_departure" else "expelled"
            if uid in self.leaders:
                self.leaders.remove(uid)
            self.history_log.append(f"Tick {tick}: {uid} departed ({reason})")

            # Check if organization must dissolve
            if self.active_member_count < 2 and self.status != OrgLifecycleStatus.DISSOLVED:
                self.dissolve(reason="pérdida de masa crítica de integrantes", tick=tick)
            return True
        return False

    def collect_member_dues(self, population_registry: Any, tick: int) -> float:
        """Collect regular operating dues from active members."""
        total = 0.0
        for uid, mem in self.members.items():
            if mem.status != "active":
                continue
            human = population_registry.get_optional(uid)
            if human and human.physical_state.money >= self.periodic_dues_usd:
                human.physical_state.money -= self.periodic_dues_usd
                self.treasury_usd += self.periodic_dues_usd
                total += self.periodic_dues_usd
            elif human:
                # Inability or refusal to pay slightly strains membership
                mem.satisfaction = max(0.20, mem.satisfaction - 0.05)
                self.internal_conflict_level = min(1.0, self.internal_conflict_level + 0.02)

        self.history_log.append(f"Tick {tick}: Dues collected totaling ${total:.2f}")
        return total

    def shift_mission(self, new_purpose: str, tick: int) -> None:
        """Adapt organizational mission to evolving community needs."""
        old = self.mission_purpose
        self.mission_purpose = new_purpose
        self.history_log.append(f"Tick {tick}: Mission shifted from '{old}' to '{new_purpose}'")

    def escalate_internal_conflict(self, delta: float, reason: str, tick: int) -> None:
        """Increase factional tension."""
        self.internal_conflict_level = min(1.0, self.internal_conflict_level + delta)
        self.legitimacy = max(0.10, self.legitimacy - (delta * 0.5))
        self.history_log.append(f"Tick {tick}: Internal conflict increased (+{delta:.2f}) - {reason}")
        if self.internal_conflict_level >= 0.50 and self.status == OrgLifecycleStatus.STABLE:
            self.status = OrgLifecycleStatus.STRAINED

    def dissolve(self, reason: str, tick: int) -> None:
        """Formal liquidation and closure of the organization."""
        self.status = OrgLifecycleStatus.DISSOLVED
        self.history_log.append(f"Tick {tick}: Organization dissolved ({reason})")


class EmergentOrganizationEngine:
    """Manages creation, evolution, fission, mergers, and lifecycle of organizations."""

    def __init__(self) -> None:
        self._organizations: dict[str, EmergentOrganization] = {}

    def get_organization(self, org_id: str) -> Optional[EmergentOrganization]:
        return self._organizations.get(org_id)

    def get_all_organizations(self, active_only: bool = True) -> list[EmergentOrganization]:
        if not active_only:
            return list(self._organizations.values())
        return [o for o in self._organizations.values() if o.status not in (OrgLifecycleStatus.DISSOLVED, OrgLifecycleStatus.MERGED)]

    def create_organization(
        self,
        name: str,
        org_type: OrganizationType,
        mission: str,
        founder_uids: list[str],
        initial_treasury_usd: float = 60.0,
        headquarters_location_id: Optional[str] = None,
        tick: int = 0,
    ) -> EmergentOrganization:
        """Charter a new emergent organization."""
        org_id = f"org_{org_type.value[:4]}_{uuid.uuid4().hex[:6]}"
        org = EmergentOrganization(
            org_id=org_id,
            name=name,
            org_type=org_type,
            mission_purpose=mission,
            founding_tick=tick,
            headquarters_location_id=headquarters_location_id,
            treasury_usd=initial_treasury_usd,
        )
        for idx, f_uid in enumerate(founder_uids):
            role = MemberRole.PRESIDENT if idx == 0 else (MemberRole.TREASURER if idx == 1 else MemberRole.FOUNDER)
            org.add_member(f_uid, role=role, tick=tick)

        self._organizations[org_id] = org
        return org

    def attempt_spontaneous_formation(
        self,
        candidates: list[dict[str, Any]], # {uid, needs, location, trust_network, capital}
        tick: int = 0,
    ) -> Optional[EmergentOrganization]:
        """Check if conditions exist for autonomous formation of a new organization.

        Requires: shared need/interest, geographical co-location, mutual trust >= 0.50.
        """
        if len(candidates) < 3:
            return None

        # Group by shared need
        need_groups: dict[str, list[dict[str, Any]]] = {}
        for c in candidates:
            for need in c.get("needs", []):
                need_groups.setdefault(need, []).append(c)

        for need, group in need_groups.items():
            if len(group) >= 3:
                # Check location coherence
                locs = {c.get("location") for c in group if c.get("location")}
                if len(locs) <= 2: # localized
                    founder_uids = [c["uid"] for c in group[:5]]
                    type_map = {
                        "comercio": (OrganizationType.COMMERCIAL_ASSOCIATION, "Defensa de puestos y compras mayoristas"),
                        "agricultura": (OrganizationType.AGRICULTURAL_COOPERATIVE, "Acopio colectivo de maíz y frijol"),
                        "agua": (OrganizationType.NEIGHBORHOOD_BOARD, "Comité de agua y administración del pozo"),
                        "socorro": (OrganizationType.MUTUAL_AID_SOCIETY, "Fondo de emergencia familiar y salud"),
                        "transporte": (OrganizationType.TRANSPORT_COLLECTIVE, "Coordinación de fletes y viajes"),
                    }
                    org_type, mission = type_map.get(need, (OrganizationType.NEIGHBORHOOD_BOARD, f"Atención colectiva a necesidad: {need}"))
                    name = f"Asociación de {need.capitalize()} Local"
                    org = self.create_organization(
                        name=name,
                        org_type=org_type,
                        mission=mission,
                        founder_uids=founder_uids,
                        initial_treasury_usd=sum(c.get("capital", 10.0) for c in group[:5]) * 0.20,
                        headquarters_location_id=next(iter(locs)) if locs else "plaza_central",
                        tick=tick,
                    )
                    return org
        return None

    def execute_fission(
        self,
        org_id: str,
        dissident_uids: list[str],
        new_org_name: str,
        new_mission: str,
        asset_split_ratio: float = 0.40,
        tick: int = 0,
    ) -> Tuple[Optional[EmergentOrganization], Optional[EmergentOrganization]]:
        """Split an organization experiencing acute internal conflict into two distinct bodies."""
        parent = self._organizations.get(org_id)
        if not parent or len(dissident_uids) < 1 or parent.active_member_count <= len(dissident_uids):
            return None, None

        # Create spin-off organization
        split_funds = round(parent.treasury_usd * asset_split_ratio, 2)
        parent.treasury_usd = max(0.0, parent.treasury_usd - split_funds)

        child_org = self.create_organization(
            name=new_org_name,
            org_type=parent.org_type,
            mission=new_mission,
            founder_uids=dissident_uids,
            initial_treasury_usd=split_funds,
            headquarters_location_id=parent.headquarters_location_id,
            tick=tick,
        )

        # Remove dissidents from parent
        for d_uid in dissident_uids:
            parent.remove_member(d_uid, reason="escisión_por_fisión", tick=tick)

        parent.history_log.append(f"Tick {tick}: Escisión completada; formada '{new_org_name}'")
        parent.internal_conflict_level = max(0.10, parent.internal_conflict_level - 0.40)
        parent.status = OrgLifecycleStatus.STABLE

        return parent, child_org

    def execute_merger(
        self,
        org_a_id: str,
        org_b_id: str,
        merged_name: str,
        tick: int = 0,
    ) -> Optional[EmergentOrganization]:
        """Merge two compatible organizations into a unified entity."""
        org_a = self._organizations.get(org_a_id)
        org_b = self._organizations.get(org_b_id)
        if not org_a or not org_b or org_a.status == OrgLifecycleStatus.DISSOLVED or org_b.status == OrgLifecycleStatus.DISSOLVED:
            return None

        # Combine members and treasuries
        combined_treasury = round(org_a.treasury_usd + org_b.treasury_usd, 2)
        merged_founders = org_a.leaders + org_b.leaders
        new_mission = f"Fusión consolidada de {org_a.name} y {org_b.name}"

        merged_org = self.create_organization(
            name=merged_name,
            org_type=org_a.org_type,
            mission=new_mission,
            founder_uids=merged_founders[:4],
            initial_treasury_usd=combined_treasury,
            headquarters_location_id=org_a.headquarters_location_id or org_b.headquarters_location_id,
            tick=tick,
        )

        for uid, mem in org_a.members.items():
            if mem.status == "active":
                merged_org.add_member(uid, role=mem.role, tick=tick)
        for uid, mem in org_b.members.items():
            if mem.status == "active" and uid not in merged_org.members:
                merged_org.add_member(uid, role=mem.role, tick=tick)

        org_a.status = OrgLifecycleStatus.MERGED
        org_b.status = OrgLifecycleStatus.MERGED
        org_a.history_log.append(f"Tick {tick}: Fusionada en '{merged_name}'")
        org_b.history_log.append(f"Tick {tick}: Fusionada en '{merged_name}'")

        return merged_org
