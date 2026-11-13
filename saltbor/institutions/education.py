"""Distributed Education & Knowledge Institutions for SALTBOR Phase 1.3 (Section 8).

Implements decentralized, emergent educational structures without artificial population thresholds:
1. Pedagogical Roles:
   - APPRENTICE: Novice learning through supervised practice.
   - MENTOR: Experienced master guiding an apprentice 1-on-1.
   - TEACHER: Instructor facilitating group learning in a workshop or school.
   - SPECIALIST: Domain expert focused on high-proficiency practice.
   - RESEARCHER: Empirical investigator exploring unknown problems.
   - TRANSMITTER: Cultural elder preserving and propagating traditions.
   - AUTODIDACT: Independent learner discovering procedures through deliberate practice.

2. Emergent Educational Organizations:
   - APPRENTICESHIP: Bilateral contract pairing mentor and apprentice.
   - WORKSHOP (Taller): Practical guild-like vocational training.
   - SCHOOL (Espacio de Enseñanza): Communal instructional institution.
   - KNOWLEDGE_HUB (Centro de Saberes): Intergenerational lore and research repository.

3. Emergence and Decline:
   - Emergence requires: community skill deficit (demand), resource surplus, qualified masters, and social trust.
   - Decline and dissolution occur if funding vanishes, teachers leave, or prestige falls.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4
import numpy as np

from saltbor.cognition.development.profile import CognitiveCapability, CognitiveProfile
from saltbor.core.types import HumanID, LocationID, Tick


class EducationalRole(str, Enum):
    """Pedagogical roles within distributed education."""

    APPRENTICE = "apprentice"
    MENTOR = "mentor"
    TEACHER = "teacher"
    SPECIALIST = "specialist"
    RESEARCHER = "researcher"
    TRANSMITTER = "transmitter"
    AUTODIDACT = "autodidact"


class EducationalInstitutionType(str, Enum):
    """Spontaneous forms of educational spaces."""

    APPRENTICESHIP = "apprenticeship"          # 1-on-1 bilateral contract
    WORKSHOP = "workshop"                      # Vocational craft / technical atelier (Taller)
    SCHOOL = "school"                          # Collective community instruction
    KNOWLEDGE_HUB = "knowledge_hub"            # Intergenerational lore and study center


@dataclasses.dataclass
class ApprenticeshipAgreement:
    """A bilateral pedagogical contract between a mentor and apprentice."""

    contract_id: str
    mentor_uid: str
    apprentice_uid: str
    skill_domain: str
    target_proficiency: float = 0.60
    current_proficiency: float = 0.10
    start_tick: int = 0
    ticks_completed: int = 0
    is_active: bool = True
    is_graduated: bool = False
    compensation_per_tick: float = 0.20 # Economic stipend or tuition


@dataclasses.dataclass
class EducationalInstitution:
    """An emergent educational space (Taller, Escuela, Centro de Saberes)."""

    institution_id: str
    name: str
    institution_type: EducationalInstitutionType
    location_id: str
    founder_uid: str
    created_tick: int = 0
    primary_domain: str = "general" # e.g., 'agriculture', 'pottery', 'masonry', 'commerce'

    # Roster
    teachers: set[str] = dataclasses.field(default_factory=set)
    apprentices: set[str] = dataclasses.field(default_factory=set)
    graduates: list[str] = dataclasses.field(default_factory=list)

    # Health & Resources
    treasury_money: float = 50.0
    prestige: float = 0.60              # [0.0, 1.0] Community standing
    is_active: bool = True
    operational_history: list[str] = dataclasses.field(default_factory=list)
    dormant_ticks: int = 0

    def add_teacher(self, human_uid: str) -> None:
        self.teachers.add(str(human_uid))
        self.operational_history.append(f"Teacher {human_uid} joined")

    def enroll_apprentice(self, human_uid: str) -> None:
        self.apprentices.add(str(human_uid))
        self.operational_history.append(f"Apprentice {human_uid} enrolled")

    def graduate_apprentice(self, human_uid: str) -> None:
        if str(human_uid) in self.apprentices:
            self.apprentices.remove(str(human_uid))
            self.graduates.append(str(human_uid))
            self.prestige = min(1.0, self.prestige + 0.05)
            self.operational_history.append(f"Apprentice {human_uid} graduated!")

    def conduct_instruction_tick(
        self,
        domain_skill: str,
        learners_profiles: dict[str, CognitiveProfile],
        mentor_profiles: dict[str, CognitiveProfile],
        tick: int,
    ) -> dict[str, float]:
        """Execute a round of instruction, advancing student competencies."""
        if not self.is_active or not self.teachers or not self.apprentices:
            self.dormant_ticks += 1
            if self.dormant_ticks > 960: # 10 days dormant
                self.is_active = False
            return {}

        self.dormant_ticks = 0
        gains: dict[str, float] = {}

        # Effective teacher quality
        teacher_levels = [
            mentor_profiles[t].get_level(CognitiveCapability.COMMUNICATION_EFFICACY)
            for t in self.teachers if t in mentor_profiles
        ]
        avg_teacher_comm = float(np.mean(teacher_levels)) if teacher_levels else 0.50

        for a_uid in list(self.apprentices):
            profile = learners_profiles.get(a_uid)
            if not profile:
                continue

            soc_fid = profile.get_level(CognitiveCapability.SOCIAL_LEARNING_FIDELITY)
            proc_lrn = profile.get_level(CognitiveCapability.PROCEDURAL_LEARNING)

            # Synergistic instruction gain
            gain = 0.025 * avg_teacher_comm * (0.5 * soc_fid + 0.5 * proc_lrn)
            gains[a_uid] = gain

            # Train the learner's procedural learning capability
            profile.train_capability(CognitiveCapability.PROCEDURAL_LEARNING, effort_intensity=0.8, duration_ticks=1, current_tick=tick)

        return gains


class DistributedEducationEngine:
    """Manages spontaneous formation, operation, and dissolution of educational structures."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()
        self.institutions: dict[str, EducationalInstitution] = {}
        self.apprenticeships: dict[str, ApprenticeshipAgreement] = {}
        self.agent_roles: dict[str, EducationalRole] = {}

    def get_all_apprenticeships(self) -> list[ApprenticeshipAgreement]:
        """Return all active and completed mentorship agreements."""
        return list(self.apprenticeships.values())

    def get_all_institutions(self) -> list[EducationalInstitution]:
        """Return all educational workshops, schools, and hubs."""
        return list(self.institutions.values())

    def get_role(self, human_uid: str) -> EducationalRole:
        return self.agent_roles.get(str(human_uid), EducationalRole.AUTODIDACT)

    def set_role(self, human_uid: str, role: EducationalRole) -> None:
        self.agent_roles[str(human_uid)] = role

    def establish_apprenticeship(
        self,
        mentor_uid: str,
        apprentice_uid: str,
        domain: str,
        target_proficiency: float = 0.65,
        start_tick: int = 0,
    ) -> ApprenticeshipAgreement:
        """Create a formal 1-on-1 mentorship contract."""
        contract_id = f"appr_{uuid4().hex[:8]}"
        agr = ApprenticeshipAgreement(
            contract_id=contract_id,
            mentor_uid=str(mentor_uid),
            apprentice_uid=str(apprentice_uid),
            skill_domain=domain,
            target_proficiency=target_proficiency,
            start_tick=start_tick,
        )
        self.apprenticeships[contract_id] = agr
        self.set_role(mentor_uid, EducationalRole.MENTOR)
        self.set_role(apprentice_uid, EducationalRole.APPRENTICE)
        return agr

    def check_spontaneous_institution_emergence(
        self,
        location_id: str,
        community_need_domain: str,
        candidates: list[dict[str, Any]], # {uid, skill_level, prestige, money, age}
        collective_treasury: float,
        tick: int = 0,
    ) -> Optional[EducationalInstitution]:
        """Spontaneously spawn a Workshop or School if organic conditions are met:

        Conditions:
        1. A master craftsman / elder exists with skill >= 0.55 and prestige >= 0.50.
        2. At least 2 eligible learners (skill < 0.35, age between 12 and 35) are co-located.
        3. Community has sufficient resources (treasury >= 30.0 or master money >= 50.0).
        """
        # Find potential masters
        potential_masters = [
            c for c in candidates
            if c.get("skill_level", 0.0) >= 0.55 and c.get("prestige", 0.0) >= 0.50
        ]
        if not potential_masters:
            return None

        # Find potential students
        potential_learners = [
            c for c in candidates
            if c.get("skill_level", 0.0) < 0.35 and 12 <= c.get("age", 25) <= 40
        ]
        if len(potential_learners) < 2:
            return None

        # Check resource feasibility
        master = potential_masters[0]
        has_funds = (collective_treasury >= 30.0) or (master.get("money", 0.0) >= 50.0)
        if not has_funds:
            return None

        # Form Workshop or School
        inst_type = (
            EducationalInstitutionType.WORKSHOP
            if community_need_domain in ("pottery", "masonry", "blacksmithing", "textiles")
            else EducationalInstitutionType.SCHOOL
        )
        inst_id = f"edu_{uuid4().hex[:8]}"
        name = f"Taller Comunitario de {community_need_domain.title()} de {location_id}"
        if inst_type == EducationalInstitutionType.SCHOOL:
            name = f"Espacio de Aprendizaje de {location_id}"

        inst = EducationalInstitution(
            institution_id=inst_id,
            name=name,
            institution_type=inst_type,
            location_id=location_id,
            founder_uid=str(master["uid"]),
            created_tick=tick,
            primary_domain=community_need_domain,
            treasury_money=30.0,
            prestige=master.get("prestige", 0.60),
        )

        inst.add_teacher(master["uid"])
        self.set_role(master["uid"], EducationalRole.TEACHER)

        for lrn in potential_learners[:4]:
            inst.enroll_apprentice(lrn["uid"])
            self.set_role(lrn["uid"], EducationalRole.APPRENTICE)

        self.institutions[inst_id] = inst
        return inst

    def get_all_institutions(self, active_only: bool = True) -> list[EducationalInstitution]:
        if active_only:
            return [i for i in self.institutions.values() if i.is_active]
        return list(self.institutions.values())
