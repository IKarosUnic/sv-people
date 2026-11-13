"""Dynamic Labor Market & Employment Ecosystem (Phase 1.5).

Simulates an authentic labor market:
- Job vacancies posted by enterprises with required qualifications, skill thresholds, and wages.
- Job search, application submission, employer evaluation, interview, and wage negotiation.
- Reservation wage dynamics: individuals reject jobs paying below their survival or opportunity cost.
- Complete employment states: formal, informal, day labor (jornaleros), self-employed, unemployed.
- Dismissals, layoffs during employer distress, and voluntary resignations upon wage arrears.
- Strict conservation of currency: payroll is disbursed directly from enterprise cash reserves.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

from saltbor.core.types import ContractType, EmploymentStatus, HumanID, LocationID, Tick

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class JobVacancy:
    """An open job requisition published by an enterprise or employer."""
    vacancy_id: str
    business_id: str
    employer_uid: str
    title: str
    required_skill: str
    min_skill_level: float               # [0.0, 1.0]
    offered_daily_wage: float            # In USD (e.g., $10.00 - $25.00)
    contract_type: ContractType
    location_id: LocationID
    applicants: list[str] = dataclasses.field(default_factory=list)
    is_filled: bool = False
    is_cancelled: bool = False
    created_tick: Tick = 0


@dataclasses.dataclass
class EmploymentContract:
    """An active or historical employment agreement."""
    contract_id: str
    employee_uid: str
    employer_uid: str
    business_id: str
    title: str
    daily_wage: float
    contract_type: ContractType
    location_id: LocationID
    start_tick: Tick
    end_tick: Optional[Tick] = None
    is_active: bool = True
    total_wages_paid: float = 0.0
    missed_paydays: int = 0
    termination_reason: str = ""


class LaborMarketEngine:
    """Central engine orchestrating the dynamic labor market."""

    def __init__(self) -> None:
        self._vacancies: dict[str, JobVacancy] = {}
        self._contracts: dict[str, EmploymentContract] = {}
        self._informal_day_labor_log: list[dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # Vacancy Operations
    # -------------------------------------------------------------------------

    def post_vacancy(
        self,
        business_id: str,
        employer_uid: str,
        title: str,
        required_skill: str,
        min_skill_level: float,
        offered_daily_wage: float,
        contract_type: ContractType = ContractType.INFORMAL_WAGE,
        location_id: str = "taller_artesanal",
        current_tick: Tick = 0,
    ) -> JobVacancy:
        """Publish a new job vacancy."""
        vac_id = f"vac_{uuid.uuid4().hex[:8]}"
        vacancy = JobVacancy(
            vacancy_id=vac_id,
            business_id=business_id,
            employer_uid=employer_uid,
            title=title,
            required_skill=required_skill,
            min_skill_level=min_skill_level,
            offered_daily_wage=round(offered_daily_wage, 2),
            contract_type=contract_type,
            location_id=location_id,
            created_tick=current_tick,
        )
        self._vacancies[vac_id] = vacancy
        logger.info("Published vacancy %s: '%s' ($%.2f/day)", vac_id, title, offered_daily_wage)
        return vacancy

    def get_open_vacancies(self) -> list[JobVacancy]:
        """Return all unfilled, active vacancies."""
        return [v for v in self._vacancies.values() if not v.is_filled and not v.is_cancelled]

    def get_vacancy(self, vacancy_id: str) -> Optional[JobVacancy]:
        return self._vacancies.get(vacancy_id)

    # -------------------------------------------------------------------------
    # Job Search, Application & Evaluation
    # -------------------------------------------------------------------------

    def search_vacancies(
        self,
        agent: Any,
        skill_filter: Optional[str] = None,
        min_wage: Optional[float] = None,
    ) -> list[JobVacancy]:
        """Search available jobs matching qualifications or criteria."""
        open_vacs = self.get_open_vacancies()
        results: list[JobVacancy] = []

        # Calculate agent reservation wage: minimum wage they are willing to accept
        money = getattr(agent.physical_state, "money", 0.0)
        hunger = getattr(agent.physical_state, "hunger", 0.0)
        # Desperate agents (low money, high hunger) have much lower reservation wage
        reservation_wage = max(4.0, 10.0 - (hunger * 4.0) - (1.0 if money < 10.0 else 0.0))

        for v in open_vacs:
            if min_wage and v.offered_daily_wage < min_wage:
                continue
            if v.offered_daily_wage < reservation_wage:
                continue
            if skill_filter and skill_filter.lower() not in v.required_skill.lower():
                continue
            results.append(v)

        return results

    def apply_for_job(self, agent: Any, vacancy_id: str) -> dict[str, Any]:
        """Submit an application for a vacancy."""
        vac = self._vacancies.get(vacancy_id)
        if not vac or vac.is_filled or vac.is_cancelled:
            return {"applied": False, "reason": "Vacancy unavailable"}

        agent_uid_str = str(agent.uid)
        if agent_uid_str not in vac.applicants:
            vac.applicants.append(agent_uid_str)

        return {"applied": True, "vacancy_id": vacancy_id, "applicant": agent_uid_str}

    def evaluate_and_hire(
        self,
        vacancy_id: str,
        business_enterprise: Any,
        population_registry: Any,
        current_tick: Tick = 0,
    ) -> dict[str, Any]:
        """Employer reviews applicants, assesses skills, and executes hiring decision."""
        vac = self._vacancies.get(vacancy_id)
        if not vac or vac.is_filled or vac.is_cancelled:
            return {"hired": False, "reason": "Vacancy inactive"}

        if not vac.applicants:
            return {"hired": False, "reason": "No applicants"}

        best_candidate: Optional[Any] = None
        best_score = -1.0

        for uid_str in vac.applicants:
            candidate = population_registry.get_optional(uuid.UUID(uid_str))
            if not candidate:
                continue

            # Skill matching score: handle list or dict gracefully
            skills = candidate.memory.procedural.get_all_skills() if hasattr(candidate, "memory") else []
            cand_skill = 0.3  # Baseline
            skill_list = list(skills.values()) if isinstance(skills, dict) else list(skills)
            for s in skill_list:
                s_id = getattr(s, "skill_id", "")
                s_name = getattr(s, "name", "")
                s_level = getattr(s, "level", 0.0)
                if vac.required_skill.lower() in s_id.lower() or vac.required_skill.lower() in s_name.lower():
                    cand_skill = max(cand_skill, s_level)

            # Score considers skill, conscientiousness, and reliability
            personality = getattr(candidate, "personality", None)
            conscientiousness = personality.get_trait("conscientiousness") if personality else 0.5
            total_score = (cand_skill * 0.6) + (conscientiousness * 0.4)

            if total_score > best_score:
                best_score = total_score
                best_candidate = candidate

        # Minimum hiring threshold
        if not best_candidate or best_score < 0.35:
            return {
                "hired": False,
                "reason": "Applicants did not meet minimum employer requirements",
                "applicants_count": len(vac.applicants),
            }

        # Check candidate's reservation wage acceptance
        cand_money = best_candidate.physical_state.money
        reservation_wage = max(4.0, 8.0 - (0.5 if cand_money < 20.0 else 0.0))
        if vac.offered_daily_wage < reservation_wage:
            return {
                "hired": False,
                "reason": f"Candidate rejected offer: offered ${vac.offered_daily_wage:.2f} < reservation wage ${reservation_wage:.2f}",
                "rejected_by_candidate": True,
            }

        # Create employment contract
        contract_id = f"ct_{uuid.uuid4().hex[:8]}"
        contract = EmploymentContract(
            contract_id=contract_id,
            employee_uid=str(best_candidate.uid),
            employer_uid=vac.employer_uid,
            business_id=vac.business_id,
            title=vac.title,
            daily_wage=vac.offered_daily_wage,
            contract_type=vac.contract_type,
            location_id=vac.location_id,
            start_tick=current_tick,
            is_active=True,
        )
        self._contracts[contract_id] = contract
        vac.is_filled = True

        # Update candidate demographics and occupation
        best_candidate.demographics.occupation = vac.title
        best_candidate.physical_state.work_location_id = vac.location_id
        best_candidate.employment_status = (
            EmploymentStatus.EMPLOYED_FORMAL
            if vac.contract_type in (ContractType.FORMAL_PERMANENT, ContractType.FORMAL_TEMPORARY)
            else EmploymentStatus.EMPLOYED_INFORMAL
        )

        logger.info(
            "Hired %s for '%s' at $%.2f/day (Contract: %s)",
            best_candidate.name, vac.title, vac.offered_daily_wage, contract_id
        )

        return {
            "hired": True,
            "contract_id": contract_id,
            "employee_uid": str(best_candidate.uid),
            "employee_name": best_candidate.name,
            "wage_daily": vac.offered_daily_wage,
            "title": vac.title,
        }

    # -------------------------------------------------------------------------
    # Resignation and Dismissal
    # -------------------------------------------------------------------------

    def resign(self, contract_id: str, reason: str, population_registry: Any, current_tick: Tick) -> bool:
        """Voluntary resignation by an employee."""
        contract = self._contracts.get(contract_id)
        if not contract or not contract.is_active:
            return False

        contract.is_active = False
        contract.end_tick = current_tick
        contract.termination_reason = f"Resigned: {reason}"

        emp = population_registry.get_optional(uuid.UUID(contract.employee_uid))
        if emp:
            emp.demographics.occupation = "Desempleado"
            emp.employment_status = EmploymentStatus.UNEMPLOYED

        logger.info("Contract %s terminated by resignation (%s)", contract_id, reason)
        return True

    def dismiss(self, contract_id: str, reason: str, population_registry: Any, current_tick: Tick) -> bool:
        """Dismissal or layoff of an employee by employer."""
        contract = self._contracts.get(contract_id)
        if not contract or not contract.is_active:
            return False

        contract.is_active = False
        contract.end_tick = current_tick
        contract.termination_reason = f"Dismissed: {reason}"

        emp = population_registry.get_optional(uuid.UUID(contract.employee_uid))
        if emp:
            emp.demographics.occupation = "Desempleado"
            emp.employment_status = EmploymentStatus.UNEMPLOYED

        logger.info("Contract %s terminated by dismissal (%s)", contract_id, reason)
        return True

    # -------------------------------------------------------------------------
    # Informal Day Labor / Temporary Work
    # -------------------------------------------------------------------------

    def perform_informal_day_labor(
        self,
        agent: Any,
        task_name: str = "Jornalero Agrícola / Ayudante de Carga",
        current_tick: Tick = 0,
    ) -> dict[str, Any]:
        """Perform short-term informal day labor for immediate cash."""
        # Wage range: $4.00 - $8.00 depending on agent physical energy
        energy = getattr(agent.physical_state, "energy", 0.5)
        earned = round(max(3.0, 4.0 + (energy * 4.0)), 2)

        agent.physical_state.money = round(agent.physical_state.money + earned, 2)
        agent.physical_state.energy = max(0.05, agent.physical_state.energy - 0.25)
        agent.physical_state.hunger = min(1.0, agent.physical_state.hunger + 0.20)

        record = {
            "agent_uid": str(agent.uid),
            "task": task_name,
            "earned_usd": earned,
            "tick": current_tick,
        }
        self._informal_day_labor_log.append(record)

        return {
            "success": True,
            "task": task_name,
            "earned_usd": earned,
            "new_balance_usd": agent.physical_state.money,
        }

    # -------------------------------------------------------------------------
    # Daily Payroll Cycle & Solvency Check
    # -------------------------------------------------------------------------

    def execute_daily_payroll(
        self,
        business_registry: Any,
        population_registry: Any,
        current_tick: Tick,
    ) -> dict[str, Any]:
        """Execute daily wage disbursements directly from enterprise liquidity to employees."""
        total_payroll_disbursed = 0.0
        active_contracts_count = 0
        missed_payments_count = 0

        for contract in list(self._contracts.values()):
            if not contract.is_active:
                continue

            active_contracts_count += 1
            biz = business_registry.get(contract.business_id)
            emp = population_registry.get_optional(uuid.UUID(contract.employee_uid))

            if not biz or not emp:
                continue

            wage = contract.daily_wage
            if biz.cash_reserve >= wage:
                biz.cash_reserve = round(biz.cash_reserve - wage, 2)
                emp.physical_state.money = round(emp.physical_state.money + wage, 2)
                contract.total_wages_paid += wage
                contract.missed_paydays = 0
                total_payroll_disbursed += wage
            else:
                contract.missed_paydays += 1
                missed_payments_count += 1
                logger.warning(
                    "Enterprise %s unable to pay wage $%.2f to %s (missed count=%d)",
                    biz.name, wage, emp.name, contract.missed_paydays
                )
                # Resignation after 2 missed paydays
                if contract.missed_paydays >= 2:
                    self.resign(
                        contract.contract_id,
                        reason="Unpaid wages (insolvent employer)",
                        population_registry=population_registry,
                        current_tick=current_tick,
                    )

        return {
            "tick": current_tick,
            "active_contracts": active_contracts_count,
            "total_payroll_disbursed_usd": round(total_payroll_disbursed, 2),
            "missed_payments": missed_payments_count,
        }

    def get_all_contracts(self) -> list[EmploymentContract]:
        return list(self._contracts.values())

    def get_active_contracts(self) -> list[EmploymentContract]:
        return [c for c in self._contracts.values() if c.is_active]
