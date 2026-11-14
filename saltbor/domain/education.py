"""Education Activity Domain for SALTBOR.

Simulates the educational ecosystem and human learning trajectories:
- Elementary schools (*escuelas básicas*), high schools (*institutos nacionales*),
  technical centers (ITCA, INSAFORP), and universities.
- Dynamic student enrollment, daily attendance, progression, dropout, and adult re-entry.
- Mechanistic drivers of educational vulnerability:
  * Household poverty and pressure to enter informal labor.
  * Geographic distance and rural transit barriers.
  * Domestic caregiving burdens (especially for female youths).
  * Institutional capacity limits and lack of pedagogical supplies.
- Interventions: School bus transport, monthly student scholarships, school meal programs,
  and evening flexible technical training.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from saltbor.domain.models import DomainCategory, DomainDefinition, DomainStatus

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class EducationalFacility:
    facility_id: str
    name: str
    facility_type: str  # "escuela_basica", "instituto_nacional", "instituto_tecnico", "universidad"
    department: str
    is_rural: bool
    latitude: float
    longitude: float
    capacity: int = 250
    enrolled_students: List[str] = dataclasses.field(default_factory=list)
    teachers_count: int = 8
    has_meal_program: bool = False
    has_transport_service: bool = False
    monthly_tuition_usd: float = 0.0  # Public schools have 0.0 tuition


class EducationActivityDomain:
    """Specialized domain modeling educational access, progression, and interventions."""

    def __init__(self) -> None:
        self.facilities: Dict[str, EducationalFacility] = {}
        self.scholarships: Dict[str, float] = {}  # student_uid -> monthly stipend USD
        self.dropouts_recorded: List[Dict[str, Any]] = []
        self._seed_default_facilities()

    def get_definition(self) -> DomainDefinition:
        """Return formal DomainDefinition."""
        return DomainDefinition(
            domain_id="education",
            name="Education and Technical Training Domain",
            category=DomainCategory.EDUCATION,
            purpose="Simulate educational accessibility, student retention, dropout risk, and human capital accumulation across urban and rural El Salvador.",
            geographic_scope="El Salvador",
            resources=["educational_infrastructure", "teacher_hours", "pedagogical_supplies", "scholarship_funds"],
            infrastructure=["escuela_basica", "instituto_nacional", "instituto_tecnico", "universidad"],
            activities=[
                "education.attend_school",
                "education.studying",
                "education.abandon_studies",
                "education.return_to_education",
                "education.seek_training",
                "education.teaching",
            ],
            entities=["EducationalFacility", "StudentEnrollment", "ScholarshipFund"],
            indicators=["net_enrollment_rate", "annual_dropout_rate", "urban_rural_attendance_gap", "technical_skill_attainment"],
            possible_interventions=["rural_school_bus", "conditional_cash_transfer_scholarship", "school_feeding_program", "flexible_evening_shift"],
            data_sources=["MINED_estadisticas_educativas", "DIGESTYC_EHPM_alfabetismo", "UNESCO_UIS"],
            uncertainties=["interrupted_school_cycles_during_rains", "unrecorded_child_informal_labor"],
            version="1.0.0",
            status=DomainStatus.ACTIVE,
        )

    def register_facility(self, facility: EducationalFacility) -> None:
        self.facilities[facility.facility_id] = facility

    def enroll_student(self, student_uid: str, facility_id: str) -> bool:
        """Enroll student if capacity allows."""
        fac = self.facilities.get(facility_id)
        if not fac:
            return False
        if len(fac.enrolled_students) >= fac.capacity:
            logger.info("Facility %s is at full capacity.", fac.name)
            return False
        if student_uid not in fac.enrolled_students:
            fac.enrolled_students.append(student_uid)
        return True

    def simulate_student_daily_attendance(
        self,
        student_uid: str,
        facility_id: str,
        household_wealth: float,
        distance_meters: float,
        family_dependency_ratio: float = 0.5,
        is_raining_hard: bool = False,
        rng: Optional[np.random.Generator] = None,
    ) -> Dict[str, Any]:
        """Simulate whether an enrolled student attends class today or faces barriers/dropout."""
        fac = self.facilities.get(facility_id)
        if not fac:
            return {"attended": False, "reason": "facility_not_found"}

        rng_gen = rng or np.random.default_rng(42)

        # 1. Base attendance probability
        p_attend = 0.95

        # 2. Economic distress penalty
        stipend = self.scholarships.get(student_uid, 0.0)
        net_wealth = household_wealth + stipend
        if net_wealth < 20.0:
            p_attend -= 0.35  # Pressure to work or lack of lunch money

        # 3. Distance and rural transit friction
        if not fac.has_transport_service:
            if distance_meters > 3000.0:
                p_attend -= 0.30
            elif distance_meters > 1500.0:
                p_attend -= 0.15

        if is_raining_hard and fac.is_rural:
            p_attend -= 0.30  # River swells and impassable dirt roads

        # 4. Meal program bonus (incentivizes attendance in vulnerable households)
        if fac.has_meal_program and net_wealth < 35.0:
            p_attend += 0.20

        # 5. Caregiving burden
        if family_dependency_ratio > 0.6:
            p_attend -= 0.15

        p_attend = max(0.05, min(0.99, p_attend))
        attended = bool(rng_gen.random() < p_attend)

        # Check for permanent dropout risk if continuous severe economic distress
        dropout_triggered = False
        if not attended and net_wealth < 10.0 and distance_meters > 4000.0 and not stipend:
            if rng_gen.random() < 0.10:
                dropout_triggered = True
                if student_uid in fac.enrolled_students:
                    fac.enrolled_students.remove(student_uid)
                self.dropouts_recorded.append({
                    "student_uid": student_uid,
                    "facility_id": facility_id,
                    "reason": "Economic destitution and severe transit distance",
                })

        return {
            "student_uid": student_uid,
            "facility_id": facility_id,
            "attended": attended,
            "attendance_probability": round(p_attend, 3),
            "dropout_triggered": dropout_triggered,
            "has_scholarship": stipend > 0,
            "has_meal_program": fac.has_meal_program,
            "has_transport": fac.has_transport_service,
        }

    def evaluate_educational_intervention(
        self,
        facility_id: str,
        intervention_type: str,  # "school_bus", "scholarship", "meal_program"
        sample_students_count: int = 50,
    ) -> Dict[str, Any]:
        """Evaluate how a targeted educational policy changes attendance and retention."""
        fac = self.facilities.get(facility_id)
        if not fac:
            raise ValueError(f"Facility '{facility_id}' not found.")

        rng = np.random.default_rng(42)

        # Baseline run
        base_attendances = 0
        base_dropouts = 0
        for _ in range(sample_students_count):
            h_wealth = float(rng.uniform(5.0, 60.0))
            dist = float(rng.uniform(500.0, 5000.0))
            res = self.simulate_student_daily_attendance(
                student_uid="dummy_student",
                facility_id=facility_id,
                household_wealth=h_wealth,
                distance_meters=dist,
                rng=rng,
            )
            if res["attended"]:
                base_attendances += 1
            if res["dropout_triggered"]:
                base_dropouts += 1

        # Apply intervention
        original_bus = fac.has_transport_service
        original_meal = fac.has_meal_program

        if intervention_type == "school_bus":
            fac.has_transport_service = True
        elif intervention_type == "meal_program":
            fac.has_meal_program = True
        elif intervention_type == "scholarship":
            # Temporary stipend
            self.scholarships["dummy_student"] = 25.0

        int_attendances = 0
        int_dropouts = 0
        for _ in range(sample_students_count):
            h_wealth = float(rng.uniform(5.0, 60.0))
            dist = float(rng.uniform(500.0, 5000.0))
            res = self.simulate_student_daily_attendance(
                student_uid="dummy_student",
                facility_id=facility_id,
                household_wealth=h_wealth,
                distance_meters=dist,
                rng=rng,
            )
            if res["attended"]:
                int_attendances += 1
            if res["dropout_triggered"]:
                int_dropouts += 1

        # Revert intervention state
        fac.has_transport_service = original_bus
        fac.has_meal_program = original_meal
        self.scholarships.pop("dummy_student", None)

        base_rate = base_attendances / sample_students_count
        int_rate = int_attendances / sample_students_count

        return {
            "facility_id": facility_id,
            "facility_name": fac.name,
            "is_rural": fac.is_rural,
            "intervention_tested": intervention_type,
            "baseline_attendance_rate": round(base_rate, 3),
            "intervention_attendance_rate": round(int_rate, 3),
            "attendance_rate_gain_pct": round((int_rate - base_rate) * 100.0, 1),
            "baseline_dropouts_count": base_dropouts,
            "intervention_dropouts_count": int_dropouts,
            "effectiveness_assessment": (
                "Highly effective: reduces dropout and lifts attendance significantly"
                if int_rate - base_rate >= 0.15
                else "Moderate effect: attendance improved, complementary measures needed"
            ),
        }

    def _seed_default_facilities(self) -> None:
        """Seed urban and rural educational centers."""
        self.register_facility(
            EducationalFacility(
                facility_id="escuela_urbana_san_salvador",
                name="Centro Escolar España",
                facility_type="escuela_basica",
                department="San Salvador",
                is_rural=False,
                latitude=13.7010,
                longitude=-89.2200,
                capacity=400,
                teachers_count=16,
                has_meal_program=True,
                has_transport_service=False,
            )
        )
        self.register_facility(
            EducationalFacility(
                facility_id="escuela_rural_chalatenango",
                name="Centro Escolar Cantón El Rosario",
                facility_type="escuela_basica",
                department="Chalatenango",
                is_rural=True,
                latitude=14.0410,
                longitude=-88.9400,
                capacity=90,
                teachers_count=3,
                has_meal_program=False,
                has_transport_service=False,
            )
        )
