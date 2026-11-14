"""Institutional Evolution Engine for SALTBOR Phase 1.9.

Models how artificial societies develop, reform, maintain, struggle with,
and transform formal and informal institutions across 11 societal domains.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class InstitutionDomain(str, enum.Enum):
    """The 11 core societal domains of institutionalization."""

    COMMUNITY_ADMINISTRATION = "community_admin"       # ADESCOs, comités de desarrollo local
    EDUCATION = "education"                           # Escuelas comunitarias, centros de saberes
    HEALTHCARE = "healthcare"                         # Clínicas comunales, promotores de salud
    COMMERCE_REGULATION = "commerce_regulation"       # Administración de mercados, pesas y medidas
    SECURITY = "security"                             # Rondas vecinales, vigilancia comunitaria
    CONFLICT_RESOLUTION = "conflict_resolution"       # Juzgados comunales, tribunales de paz
    COMMON_RESOURCES_CPR = "cpr_governance"           # Juntas de agua, comités de cuenca
    INFRASTRUCTURE = "infrastructure"                 # Mantenimiento de caminos, puentes, alumbrado
    CULTURE_HERITAGE = "culture_heritage"             # Cofradías patronales, casas de la cultura
    SOCIAL_WELFARE = "social_welfare"                 # Albergues comunales, comedores solidarios
    LOCAL_GOVERNMENT = "local_government"             # Cabildos abiertos, alcaldías auxiliares


class InstitutionalStatus(str, enum.Enum):
    """Operational status of the institution."""

    ACTIVE_FUNCTIONING = "active_functioning"
    CAPACITY_STRAINED = "capacity_strained"           # Backlog of cases or budget deficit
    LEGITIMACY_CRISIS = "legitimacy_crisis"           # Scandals or popular distrust
    DORMANT_DEFUNCT = "dormant_defunct"               # Inactive, zero operations
    REFORMED = "reformed"                             # Restructured under new leadership/rules


@dataclasses.dataclass
class InstitutionalDecayMetric:
    """Quantitative performance indicator."""

    queue_length: int = 0
    services_rendered: int = 0
    operational_failures: int = 0
    efficiency_ratio: float = 0.85 # [0.0, 1.0]


@dataclasses.dataclass
class EvolvingInstitution:
    """A formal or semi-formal institution with verifiable properties and operational capacity."""

    institution_id: str
    name: str
    formal_acronym: str
    domain: InstitutionDomain
    mandate_mission: str
    headquarters_location_id: str

    # Territorial Jurisdiction
    department_code: str = "SS"
    municipality_id: str = "san_salvador_centro"
    district_id: str = "san_salvador"
    canton_name: Optional[str] = None
    created_tick: int = 0

    # Human Resources & Authority
    officers: dict[str, str] = dataclasses.field(default_factory=dict) # human_uid -> role ("Director", "Tesorero")
    staff_uids: set[str] = dataclasses.field(default_factory=set)

    # Financial & Material Assets
    treasury_usd: float = 500.0
    operating_budget_per_day: float = 10.0
    physical_assets: list[str] = dataclasses.field(default_factory=list)

    # Operational Rules and Capacity
    rules_and_bylaws: list[str] = dataclasses.field(default_factory=list)
    max_service_throughput_per_day: int = 15
    active_backlog_queue: list[dict[str, Any]] = dataclasses.field(default_factory=list)

    # Legitimacy and Social Standing
    legitimacy: float = 0.85           # [0.0, 1.0] Popular confidence
    reputation: float = 0.80           # [0.0, 1.0] General standing
    status: InstitutionalStatus = InstitutionalStatus.ACTIVE_FUNCTIONING

    # Inter-Institutional Relations
    institutional_alliances: set[str] = dataclasses.field(default_factory=set) # other institution_ids
    institutional_rivalries: set[str] = dataclasses.field(default_factory=set)

    # Decision History and Memory
    decision_history: list[dict[str, Any]] = dataclasses.field(default_factory=list)

    def request_service(self, petitioner_uid: str, service_type: str, tick: int) -> bool:
        """Citizen files a request or case with the institution."""
        if self.status in (InstitutionalStatus.DORMANT_DEFUNCT, InstitutionalStatus.LEGITIMACY_CRISIS):
            return False

        case = {
            "case_id": f"srv_{uuid.uuid4().hex[:6]}",
            "petitioner_uid": petitioner_uid,
            "service_type": service_type,
            "filed_tick": tick,
            "resolved": False,
        }
        self.active_backlog_queue.append(case)
        if len(self.active_backlog_queue) > self.max_service_throughput_per_day * 2:
            self.status = InstitutionalStatus.CAPACITY_STRAINED
        return True

    def process_daily_operations(self, tick: int) -> dict[str, Any]:
        """Execute daily operational queue, disburse budgets, and assess throughput."""
        # Deduct operating overhead
        actual_spent = min(self.treasury_usd, self.operating_budget_per_day)
        self.treasury_usd -= actual_spent

        if self.treasury_usd < self.operating_budget_per_day * 2:
            # Budget deficit reduces operational throughput
            effective_capacity = max(1, self.max_service_throughput_per_day // 2)
            self.legitimacy = max(0.15, self.legitimacy - 0.02)
        else:
            effective_capacity = self.max_service_throughput_per_day

        # Process cases up to capacity
        processed_count = 0
        while self.active_backlog_queue and processed_count < effective_capacity:
            case = self.active_backlog_queue.pop(0)
            case["resolved"] = True
            case["resolved_tick"] = tick
            processed_count += 1

        unresolved_backlog = len(self.active_backlog_queue)
        if unresolved_backlog == 0 and self.status == InstitutionalStatus.CAPACITY_STRAINED:
            self.status = InstitutionalStatus.ACTIVE_FUNCTIONING
        elif (unresolved_backlog > 0 or self.treasury_usd < self.operating_budget_per_day) and self.status == InstitutionalStatus.ACTIVE_FUNCTIONING:
            self.status = InstitutionalStatus.CAPACITY_STRAINED

        self.decision_history.append({
            "tick": tick,
            "event": "daily_operations",
            "processed": processed_count,
            "backlog": unresolved_backlog,
            "treasury_remaining": round(self.treasury_usd, 2),
            "legitimacy": round(self.legitimacy, 3),
        })

        return {
            "processed_count": processed_count,
            "backlog": unresolved_backlog,
            "treasury_usd": self.treasury_usd,
        }

    def suffer_crisis(self, penalty: float, reason: str, tick: int) -> None:
        """Record legitimacy collapse or administrative scandal."""
        self.legitimacy = max(0.05, self.legitimacy - penalty)
        self.reputation = max(0.05, self.reputation - penalty)
        if self.legitimacy <= 0.25:
            self.status = InstitutionalStatus.LEGITIMACY_CRISIS
        self.decision_history.append({
            "tick": tick,
            "event": "legitimacy_crisis",
            "penalty": penalty,
            "reason": reason,
            "remaining_legitimacy": self.legitimacy,
        })

    def enact_reform(self, new_rules: list[str], new_director_uid: str, tick: int) -> None:
        """Institutional restructuring to restore operational efficacy and legitimacy."""
        self.rules_and_bylaws.extend(new_rules)
        self.officers["director"] = new_director_uid
        self.status = InstitutionalStatus.REFORMED
        self.legitimacy = min(1.0, self.legitimacy + 0.30)
        self.reputation = min(1.0, self.reputation + 0.25)
        self.decision_history.append({
            "tick": tick,
            "event": "institutional_reform",
            "new_director": new_director_uid,
            "rules_enacted": len(new_rules),
            "restored_legitimacy": self.legitimacy,
        })


class InstitutionalEvolutionEngine:
    """Coordinates lifecycle, territorial grounding, service rendering, and reforms across institutions."""

    def __init__(self) -> None:
        self._institutions: dict[str, EvolvingInstitution] = {}

    def get_institution(self, inst_id: str) -> Optional[EvolvingInstitution]:
        return self._institutions.get(inst_id)

    def get_all_institutions(self, active_only: bool = True) -> list[EvolvingInstitution]:
        if not active_only:
            return list(self._institutions.values())
        return [i for i in self._institutions.values() if i.status != InstitutionalStatus.DORMANT_DEFUNCT]

    def get_institutions_by_domain(self, domain: InstitutionDomain) -> list[EvolvingInstitution]:
        return [i for i in self._institutions.values() if i.domain == domain]

    def register_institution(
        self,
        name: str,
        formal_acronym: str,
        domain: InstitutionDomain,
        mission: str,
        headquarters_loc_id: str,
        department_code: str = "SS",
        municipality_id: str = "san_salvador_centro",
        initial_treasury_usd: float = 300.0,
        director_uid: str = "admin_01",
        initial_rules: Optional[list[str]] = None,
        tick: int = 0,
    ) -> EvolvingInstitution:
        """Establish and ground a formal or semi-formal institution."""
        inst_id = f"inst_{domain.value[:4]}_{uuid.uuid4().hex[:6]}"
        inst = EvolvingInstitution(
            institution_id=inst_id,
            name=name,
            formal_acronym=formal_acronym,
            domain=domain,
            mandate_mission=mission,
            headquarters_location_id=headquarters_loc_id,
            department_code=department_code,
            municipality_id=municipality_id,
            treasury_usd=initial_treasury_usd,
            officers={"director": director_uid},
            rules_and_bylaws=list(initial_rules or []),
            created_tick=tick,
        )
        inst.decision_history.append({
            "tick": tick,
            "event": "charter_established",
            "director": director_uid,
        })
        self._institutions[inst_id] = inst
        return inst

    def step(self, current_tick: Tick) -> None:
        """Process daily operations and budget cycles across all institutions."""
        if current_tick % 96 == 0:
            for inst in self._institutions.values():
                if inst.status != InstitutionalStatus.DORMANT_DEFUNCT:
                    inst.process_daily_operations(current_tick)
