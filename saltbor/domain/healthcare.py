"""Healthcare and Social Services Domain for SALTBOR.

Simulates the operational health service infrastructure of El Salvador:
- Community health clinics (*Unidades de Salud*), national hospitals, and private clinics.
- Service capacity, physician/nursing rosters, medical supplies, and appointment queues.
- Realistic health-seeking behaviors:
  * Prompt clinical visits for severe discomfort.
  * *Delaying care* due to bus fare, long queues, or lost day-labor wages.
  * Utilization of preventive vaccination and maternal checkups.
- Facility overload, triage bottlenecks, and wait times.
- Explicit boundary: Models operational capacity and accessibility, NOT clinical medical diagnoses.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from saltbor.domain.models import DomainCategory, DomainDefinition, DomainStatus

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class HealthcareFacility:
    facility_id: str
    name: str
    facility_type: str  # "unidad_de_salud", "hospital_nacional", "clinica_comunitaria"
    department: str
    is_rural: bool
    latitude: float
    longitude: float
    daily_consultation_capacity: int = 50
    physicians_on_duty: int = 3
    nurses_on_duty: int = 4
    medical_supplies_stock: float = 100.0  # Percentage available
    consultation_fee_usd: float = 0.0  # Public health system is nominally free
    current_waiting_queue: int = 0
    total_patients_attended_today: int = 0
    total_patients_turned_away: int = 0


class HealthcareActivityDomain:
    """Operational simulation of healthcare accessibility, queues, and resource allocation."""

    def __init__(self) -> None:
        self.facilities: Dict[str, HealthcareFacility] = {}
        self.care_delays_recorded: List[Dict[str, Any]] = []
        self._seed_default_facilities()

    def get_definition(self) -> DomainDefinition:
        """Return formal DomainDefinition."""
        return DomainDefinition(
            domain_id="healthcare",
            name="Healthcare and Social Services Domain",
            category=DomainCategory.HEALTHCARE,
            purpose="Simulate operational healthcare access, patient queues, facility capacity, and behavioral care delays across El Salvador.",
            geographic_scope="El Salvador",
            resources=["clinical_personnel_hours", "essential_medicines", "consultation_rooms", "triage_capacity"],
            infrastructure=["unidad_de_salud", "hospital_nacional", "clinica_comunitaria", "puesto_de_salud"],
            activities=[
                "health.seek_medical_attention",
                "health.delay_treatment",
                "health.attend_preventive",
                "health.provide_care",
            ],
            entities=["HealthcareFacility", "ClinicalAppointmentQueue", "MedicalSupplyInventory"],
            indicators=["average_waiting_time_minutes", "care_delay_rate", "facility_overload_ratio", "preventive_coverage_rate"],
            possible_interventions=["mobile_health_brigade", "extended_evening_hours", "essential_medicine_restocking", "community_health_promoter"],
            data_sources=["MINSAL_infraestructura_salud", "DIGESTYC_EHPM_salud", "OPS_OMS_indicadores"],
            uncertainties=["epidemiological_seasonality_dengue_flu", "stockouts_of_specialized_drugs"],
            version="1.0.0",
            status=DomainStatus.ACTIVE,
        )

    def register_facility(self, facility: HealthcareFacility) -> None:
        self.facilities[facility.facility_id] = facility

    def simulate_patient_care_seeking(
        self,
        patient_uid: str,
        facility_id: str,
        symptom_severity: float,  # 0.1 (mild cold) to 0.9 (acute injury/fever)
        patient_cash: float,
        transit_cost_usd: float,
        distance_meters: float,
        rng: Optional[np.random.Generator] = None,
    ) -> Dict[str, Any]:
        """Simulate whether an individual seeks care immediately, postpones, or is turned away."""
        fac = self.facilities.get(facility_id)
        if not fac:
            return {"outcome": "facility_not_found"}

        rng_gen = rng or np.random.default_rng(42)

        # 1. Behavioral decision: Seek vs. Delay
        # Delaying care happens when transit cost or lost wages exceed perceived urgency
        total_trip_cost = transit_cost_usd + fac.consultation_fee_usd
        delay_care = False

        if symptom_severity < 0.60:
            if patient_cash < total_trip_cost or total_trip_cost > patient_cash * 0.40:
                delay_care = True
            elif distance_meters > 5000.0 and patient_cash < 15.0:
                delay_care = True

        if delay_care:
            self.care_delays_recorded.append({
                "patient_uid": patient_uid,
                "facility_id": facility_id,
                "severity": symptom_severity,
                "reason": "Financial transit barrier or opportunity cost of wages",
            })
            return {
                "outcome": "treatment_delayed",
                "patient_uid": patient_uid,
                "facility_id": facility_id,
                "reason": "Transit cost or queue delay discouraged care seeking",
                "waited_minutes": 0,
            }

        # 2. Arrives at facility: check queue and capacity
        if fac.current_waiting_queue >= fac.daily_consultation_capacity:
            fac.total_patients_turned_away += 1
            return {
                "outcome": "turned_away_capacity_exceeded",
                "patient_uid": patient_uid,
                "facility_id": facility_id,
                "queue_length": fac.current_waiting_queue,
            }

        # 3. Patient enqueued and attended
        fac.current_waiting_queue += 1
        fac.total_patients_attended_today += 1

        # Wait time depends on queue and physician count (approx 15 mins per patient per doctor)
        wait_minutes = int((fac.current_waiting_queue / max(1, fac.physicians_on_duty)) * 15)

        # Medicine stock availability
        has_prescribed_drugs = bool(rng_gen.random() < (fac.medical_supplies_stock / 100.0))

        return {
            "outcome": "attended_successfully",
            "patient_uid": patient_uid,
            "facility_id": facility_id,
            "wait_time_minutes": wait_minutes,
            "prescribed_drugs_dispensed": has_prescribed_drugs,
            "facility_utilization_pct": round((fac.total_patients_attended_today / fac.daily_consultation_capacity) * 100.0, 1),
        }

    def evaluate_capacity_expansion_intervention(
        self,
        facility_id: str,
        additional_physicians: int = 2,
        restock_supplies: bool = True,
        simulated_patient_arrivals: int = 60,
    ) -> Dict[str, Any]:
        """Evaluate how hiring additional doctors or restocking supplies reduces wait times and turn-aways."""
        fac = self.facilities.get(facility_id)
        if not fac:
            raise ValueError(f"Facility '{facility_id}' not found.")

        rng = np.random.default_rng(42)

        # Run baseline
        base_attended = 0
        base_turned_away = 0
        base_wait_times = []

        fac.current_waiting_queue = 0
        for i in range(simulated_patient_arrivals):
            res = self.simulate_patient_care_seeking(
                patient_uid=f"base_patient_{i}",
                facility_id=facility_id,
                symptom_severity=float(rng.uniform(0.3, 0.9)),
                patient_cash=float(rng.uniform(2.0, 25.0)),
                transit_cost_usd=0.50,
                distance_meters=1500.0,
                rng=rng,
            )
            if res["outcome"] == "attended_successfully":
                base_attended += 1
                base_wait_times.append(res["wait_time_minutes"])
            elif res["outcome"] == "turned_away_capacity_exceeded":
                base_turned_away += 1

        # Run intervention
        orig_doctors = fac.physicians_on_duty
        orig_capacity = fac.daily_consultation_capacity
        orig_stock = fac.medical_supplies_stock

        fac.physicians_on_duty += additional_physicians
        fac.daily_consultation_capacity += (additional_physicians * 20)
        if restock_supplies:
            fac.medical_supplies_stock = 98.0
        fac.current_waiting_queue = 0

        int_attended = 0
        int_turned_away = 0
        int_wait_times = []

        for i in range(simulated_patient_arrivals):
            res = self.simulate_patient_care_seeking(
                patient_uid=f"int_patient_{i}",
                facility_id=facility_id,
                symptom_severity=float(rng.uniform(0.3, 0.9)),
                patient_cash=float(rng.uniform(2.0, 25.0)),
                transit_cost_usd=0.50,
                distance_meters=1500.0,
                rng=rng,
            )
            if res["outcome"] == "attended_successfully":
                int_attended += 1
                int_wait_times.append(res["wait_time_minutes"])
            elif res["outcome"] == "turned_away_capacity_exceeded":
                int_turned_away += 1

        # Revert
        fac.physicians_on_duty = orig_doctors
        fac.daily_consultation_capacity = orig_capacity
        fac.medical_supplies_stock = orig_stock
        fac.current_waiting_queue = 0

        mean_base_wait = float(np.mean(base_wait_times)) if base_wait_times else 0.0
        mean_int_wait = float(np.mean(int_wait_times)) if int_wait_times else 0.0

        return {
            "facility_id": facility_id,
            "facility_name": fac.name,
            "additional_physicians": additional_physicians,
            "baseline_attended": base_attended,
            "intervention_attended": int_attended,
            "baseline_turned_away": base_turned_away,
            "intervention_turned_away": int_turned_away,
            "mean_wait_time_baseline_mins": round(mean_base_wait, 1),
            "mean_wait_time_intervention_mins": round(mean_int_wait, 1),
            "wait_time_reduction_pct": round(((mean_base_wait - mean_int_wait) / max(1.0, mean_base_wait)) * 100.0, 1),
            "operational_impact": "Overload eliminated and wait times significantly lowered." if int_turned_away == 0 else "Partial relief; demand remains high.",
        }

    def _seed_default_facilities(self) -> None:
        """Seed urban and rural health centers."""
        self.register_facility(
            HealthcareFacility(
                facility_id="unidad_salud_san_salvador",
                name="Unidad de Salud San Jacinto",
                facility_type="unidad_de_salud",
                department="San Salvador",
                is_rural=False,
                latitude=13.6890,
                longitude=-89.2150,
                daily_consultation_capacity=60,
                physicians_on_duty=3,
                nurses_on_duty=4,
                medical_supplies_stock=75.0,
            )
        )
        self.register_facility(
            HealthcareFacility(
                facility_id="unidad_salud_rural_morazan",
                name="Unidad Comunitaria de Salud Perquín",
                facility_type="unidad_de_salud",
                department="Morazán",
                is_rural=True,
                latitude=13.9570,
                longitude=-88.1610,
                daily_consultation_capacity=25,
                physicians_on_duty=1,
                nurses_on_duty=2,
                medical_supplies_stock=55.0,
            )
        )
