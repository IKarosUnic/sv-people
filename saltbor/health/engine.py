"""Health, Epidemiological Transmission and Clinical Infrastructure Engine (Phase 1.5 Extension).

Simulates:
- Explicit conditions: infectious, gastrointestinal, respiratory, chronic, occupational injuries, and distress.
- Contextual exposure: polluted water intake, crowded airborne contagion, vector seasonality, physical hazards.
- Susceptibility-based transmission without arbitrary labels.
- Healthcare infrastructure triage: operating hours, capacity limits, supplies, fees, and delays.
- Dynamic recovery or long-term complication trajectories.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import uuid

import numpy as np

from saltbor.core.types import ConditionCategory, LocationID, Tick
from saltbor.events.types import EventType, SimulationEvent
from saltbor.health.models import HealthCondition, MedicalFacility, TreatmentRecord

logger = logging.getLogger(__name__)


class HealthEngine:
    """Central engine managing population health, diseases, injuries, and clinics."""

    def __init__(self, seed: Optional[int] = 42) -> None:
        self._facilities: dict[str, MedicalFacility] = {}
        self.treatment_history: list[TreatmentRecord] = []
        self._rng = np.random.default_rng(seed)
        self._seed_default_facilities()

    def _seed_default_facilities(self) -> None:
        """Seed verified and community health facilities in Suchitoto context."""
        # 1. Public Primary Health Post (Free, limited beds)
        f1 = MedicalFacility(
            facility_id="unidad_salud_suchitoto",
            name="Unidad de Salud de Suchitoto (MINSAL)",
            facility_type="unidad_salud",
            location_id="unidad_salud",
            coordinates=(13.9365, -89.0270),
            capacity_beds=6,
            staff_available=3,
            medical_supplies_level=0.80,
            fee_usd=0.0,
            waiting_time_ticks=2,
            operating_hours=(7, 17),
        )
        # 2. Community Rural Clinic
        f2 = MedicalFacility(
            facility_id="clinica_comunal_san_pedro",
            name="Clínica Comunal y Dispensario San Pedro",
            facility_type="clinica_comunal",
            location_id="clinica_san_pedro",
            coordinates=(13.9310, -89.0315),
            capacity_beds=3,
            staff_available=1,
            medical_supplies_level=0.65,
            fee_usd=1.50,
            waiting_time_ticks=1,
            operating_hours=(8, 16),
        )
        self.register_facility(f1)
        self.register_facility(f2)

    def register_facility(self, facility: MedicalFacility) -> None:
        self._facilities[facility.facility_id] = facility

    def get_facility(self, facility_id: str) -> Optional[MedicalFacility]:
        return self._facilities.get(facility_id)

    def get_all_facilities(self) -> list[MedicalFacility]:
        return list(self._facilities.values())

    # -------------------------------------------------------------------------
    # Condition Factories
    # -------------------------------------------------------------------------

    def create_waterborne_illness(self, tick: Tick = 0, origin: str = "water_source") -> HealthCondition:
        """Create a gastrointestinal illness (e.g. Amoebiasis / Acute Diarrhea) from tainted water."""
        return HealthCondition(
            condition_id=f"cond_{uuid.uuid4().hex[:8]}",
            name="Infección Gastrointestinal / Amebiasis Aguda",
            category=ConditionCategory.GASTROINTESTINAL,
            severity=0.55,
            onset_tick=tick,
            duration_ticks=24,
            symptoms=["Cólicos abdominales", "Diarrea acuosa", "Fiebre moderada", "Deshidratación"],
            is_contagious=False,
            origin_exposure=origin,
            recovery_probability_per_day=0.30,
            complications_risk=0.15,
            treatment_required="Sales de rehidratación oral y antiparasitario",
            energy_drain_per_tick=0.03,
            health_drain_per_tick=0.015,
        )

    def create_respiratory_infection(self, tick: Tick = 0, origin: str = "airborne") -> HealthCondition:
        """Create an acute respiratory viral infection."""
        return HealthCondition(
            condition_id=f"cond_{uuid.uuid4().hex[:8]}",
            name="Infección Respiratoria Aguda / Gripe",
            category=ConditionCategory.RESPIRATORY,
            severity=0.40,
            onset_tick=tick,
            duration_ticks=30,
            symptoms=["Congestión nasal", "Tos seca", "Cefalea", "Malestar general"],
            is_contagious=True,
            transmission_rate=0.45,
            incubation_ticks=4,
            origin_exposure=origin,
            recovery_probability_per_day=0.40,
            complications_risk=0.05,
            treatment_required="Reposo domiciliario y acetaminofén",
            energy_drain_per_tick=0.02,
            health_drain_per_tick=0.008,
        )

    def create_workplace_trauma(self, tick: Tick = 0, task: str = "Jornalero") -> HealthCondition:
        """Create an occupational physical injury (machete cut, sprain, fracture)."""
        return HealthCondition(
            condition_id=f"cond_{uuid.uuid4().hex[:8]}",
            name="Herida Cortante Ocupacional / Traumatismo Físico",
            category=ConditionCategory.INJURY,
            severity=0.60,
            onset_tick=tick,
            duration_ticks=36,
            symptoms=["Dolor agudo localizado", "Hemorragia", "Movilidad reducida"],
            is_contagious=False,
            origin_exposure=f"labor:{task}",
            recovery_probability_per_day=0.25,
            complications_risk=0.20,
            treatment_required="Sutura, curación de herida y antibiótico profiláctico",
            energy_drain_per_tick=0.04,
            health_drain_per_tick=0.02,
        )

    def create_vector_borne_illness(self, tick: Tick = 0) -> HealthCondition:
        """Create Dengue infection transmitted by Aedes mosquitoes."""
        return HealthCondition(
            condition_id=f"cond_{uuid.uuid4().hex[:8]}",
            name="Dengue Clásico",
            category=ConditionCategory.INFECTIOUS,
            severity=0.65,
            onset_tick=tick,
            duration_ticks=40,
            symptoms=["Fiebre alta repentina", "Dolor retroocular", "Mialgias intensas", "Erupción cutánea"],
            is_contagious=False,
            origin_exposure="vector_mosquito",
            recovery_probability_per_day=0.20,
            complications_risk=0.15,
            treatment_required="Hidratación intravenosa, control de plaquetas y reposo estricto",
            energy_drain_per_tick=0.04,
            health_drain_per_tick=0.025,
        )

    def create_heat_exhaustion(self, tick: Tick = 0) -> HealthCondition:
        """Create acute heat exhaustion / dehydration from extreme temperature."""
        return HealthCondition(
            condition_id=f"cond_{uuid.uuid4().hex[:8]}",
            name="Golpe de Calor / Deshidratación Severa",
            category=ConditionCategory.CHRONIC,
            severity=0.45,
            onset_tick=tick,
            duration_ticks=12,
            symptoms=["Mareos", "Sudoración profusa", "Debilidad muscular", "Sed extrema"],
            is_contagious=False,
            origin_exposure="extreme_heat",
            recovery_probability_per_day=0.60,
            complications_risk=0.05,
            treatment_required="Sombra, ventilación y líquidos electrolíticos",
            energy_drain_per_tick=0.035,
            health_drain_per_tick=0.01,
        )

    def create_mental_distress(self, tick: Tick = 0, cause: str = "grief") -> HealthCondition:
        """Create acute emotional distress or grief state."""
        return HealthCondition(
            condition_id=f"cond_{uuid.uuid4().hex[:8]}",
            name="Distrés Emocional Agudo / Duelo Prolongado",
            category=ConditionCategory.MENTAL_DISTRESS,
            severity=0.50,
            onset_tick=tick,
            duration_ticks=50,
            symptoms=["Insomnio", "Apatía", "Labilidad afectiva", "Fatiga mental"],
            is_contagious=False,
            origin_exposure=cause,
            recovery_probability_per_day=0.20,
            complications_risk=0.05,
            treatment_required="Acompañamiento familiar, apoyo comunitario y descanso",
            energy_drain_per_tick=0.015,
            health_drain_per_tick=0.005,
        )

    # -------------------------------------------------------------------------
    # Transmission & Progression
    # -------------------------------------------------------------------------

    def step_individual_health(
        self,
        human: Any,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
        location_id: Optional[str] = None,
        coordinates: Optional[tuple[float, float]] = None,
    ) -> None:
        """Advance biological condition states, drain vitals, and evaluate natural resolution."""
        conditions: list[HealthCondition] = getattr(human, "active_health_conditions", [])
        if not conditions:
            # Baseline health regeneration if well-fed and rested
            if human.physical_state.hunger < 0.20 and human.physical_state.energy > 0.60:
                human.physical_state.health = min(1.0, human.physical_state.health + 0.005)
            return

        remaining_conditions: list[HealthCondition] = []
        for cond in conditions:
            cond.ticks_active += 1

            # Drain physical vitals
            human.physical_state.energy = max(0.05, human.physical_state.energy - cond.energy_drain_per_tick)
            human.physical_state.health = max(0.05, human.physical_state.health - cond.health_drain_per_tick)

            # Recovery calculation: treatment multiplies natural recovery rate
            recovery_chance = cond.recovery_probability_per_day / 24.0  # per tick scaling
            if cond.is_treated:
                recovery_chance *= 3.0

            # Rest activity boosts recovery
            if getattr(human.physical_state, "current_activity", None) == "rest_recover":
                recovery_chance *= 1.5

            if self._rng.random() < recovery_chance or cond.ticks_active >= cond.duration_ticks:
                logger.info("Human %s recovered from %s", human.name, cond.name)
                self.release_patient(str(human.uid))
                history = getattr(human, "health_history", None)
                if isinstance(history, list):
                    history.append({
                        "condition_id": cond.condition_id,
                        "condition_name": cond.name,
                        "category": cond.category.value if hasattr(cond.category, "value") else str(cond.category),
                        "onset_tick": cond.onset_tick,
                        "recovered_tick": current_tick,
                        "ticks_active": cond.ticks_active,
                        "was_treated": cond.is_treated,
                        "severity": cond.severity,
                    })
                if event_bus:
                    evt = SimulationEvent(
                        event_type=EventType.ILLNESS_RECOVERED,
                        tick=current_tick,
                        source_human_id=human.uid,
                        location_id=location_id or getattr(human.physical_state, "current_location_id", None),
                        coordinates=coordinates,
                        data={
                            "condition_id": cond.condition_id,
                            "condition_name": cond.name,
                            "was_treated": cond.is_treated,
                            "ticks_active": cond.ticks_active,
                            "coordinate_provenance": "synthetic_local_map" if coordinates else None,
                        },
                        importance=0.6,
                    )
                    event_bus.emit(evt)
                    if causal_graph:
                        causal_graph.add_event(evt, description=f"{human.name} se recuperó de {cond.name}")
                continue

            # Evaluate acute complications if untreated and critical
            if not cond.is_treated and cond.is_critical and cond.ticks_active % 12 == 0:
                if self._rng.random() < cond.complications_risk:
                    cond.severity = min(1.0, cond.severity + 0.15)
                    logger.warning("Human %s experienced complications with %s", human.name, cond.name)
                    if event_bus:
                        evt_comp = SimulationEvent(
                            event_type=EventType.HEALTH_COMPLICATION,
                            tick=current_tick,
                            source_human_id=human.uid,
                            location_id=location_id or getattr(human.physical_state, "current_location_id", None),
                            coordinates=coordinates,
                            data={
                                "condition": cond.name,
                                "new_severity": cond.severity,
                                "coordinate_provenance": "synthetic_local_map" if coordinates else None,
                            },
                            importance=0.75,
                        )
                        event_bus.emit(evt_comp)
                        if causal_graph:
                            causal_graph.add_event(evt_comp, description=f"Complicación de {cond.name} en {human.name}")

            remaining_conditions.append(cond)

        human.active_health_conditions = remaining_conditions

    def simulate_airborne_contagion(
        self,
        infected_human: Any,
        nearby_humans: list[Any],
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
        location_id: Optional[str] = None,
        coordinates: Optional[tuple[float, float]] = None,
    ) -> list[str]:
        """Simulate realistic airborne transmission of contagious respiratory illness."""
        infected_uids: list[str] = []
        contagious_conditions = [
            c for c in getattr(infected_human, "active_health_conditions", [])
            if c.is_contagious and not c.is_incubating
        ]
        if not contagious_conditions:
            return infected_uids

        for target in nearby_humans:
            if target.uid == infected_human.uid:
                continue

            # Check if target already has this condition
            target_conditions = getattr(target, "active_health_conditions", [])
            target_names = {c.name for c in target_conditions}

            for src_cond in contagious_conditions:
                if src_cond.name in target_names:
                    continue

                # Susceptibility formula: base transmission modulated by target energy and health
                susceptibility = (1.0 - getattr(target.physical_state, "health", 1.0) * 0.4)
                effective_prob = src_cond.transmission_rate * susceptibility * 0.35

                if self._rng.random() < effective_prob:
                    new_cond = self.create_respiratory_infection(tick=current_tick, origin=f"airborne_from:{infected_human.uid}")
                    target_conditions.append(new_cond)
                    target.active_health_conditions = target_conditions
                    infected_uids.append(str(target.uid))

                    logger.info("Transmission: %s infected %s with %s", infected_human.name, target.name, src_cond.name)
                    if event_bus:
                        evt = SimulationEvent(
                            event_type=EventType.DISEASE_TRANSMITTED,
                            tick=current_tick,
                            source_human_id=infected_human.uid,
                            target_human_id=target.uid,
                            location_id=location_id or getattr(infected_human.physical_state, "current_location_id", None),
                            coordinates=coordinates,
                            data={
                                "disease": src_cond.name,
                                "transmission_mode": "airborne_contact",
                                "coordinate_provenance": "synthetic_local_map" if coordinates else None,
                            },
                            importance=0.7,
                        )
                        event_bus.emit(evt)
                        if causal_graph:
                            causal_graph.add_event(evt, description=f"{infected_human.name} transmitió {src_cond.name} a {target.name}")
                    break

        return infected_uids

    # -------------------------------------------------------------------------
    # Healthcare Seeking, Triage & Treatment
    # -------------------------------------------------------------------------

    def seek_medical_treatment(
        self,
        human: Any,
        facility_id: str,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
        current_hour: Optional[int] = None,
    ) -> dict[str, Any]:
        """Triage an individual presenting for medical care at a healthcare facility.

        ``current_hour`` lets the live runner pass the simulation clock hour;
        experiments that only provide a tick retain the historical
        ``tick % 24`` interpretation.
        """
        facility = self._facilities.get(facility_id)
        if not facility:
            return {"success": False, "reason": "Facility not found"}

        # Operating hours check
        hour = current_tick % 24 if current_hour is None else int(current_hour) % 24
        if not facility.is_open_at_hour(hour):
            return {"success": False, "reason": f"Facility closed at hour {hour}:00"}

        # Capacity check
        if not facility.has_capacity:
            facility.total_rejected_capacity += 1
            if event_bus:
                evt_rej = SimulationEvent(
                    event_type=EventType.HEALTH_TREATMENT_SEEKED,
                    tick=current_tick,
                    source_human_id=human.uid,
                    location_id=facility.location_id,
                    coordinates=facility.coordinates,
                    data={
                        "facility_id": facility_id,
                        "outcome": "capacity_exhausted",
                        "coordinate_provenance": "verified_facility",
                    },
                    importance=0.5,
                )
                event_bus.emit(evt_rej)
                if causal_graph:
                    causal_graph.add_event(evt_rej, description=f"{human.name} no pudo ser atendido por cupo lleno en {facility.name}")
            return {"success": False, "reason": "No available beds or consultation capacity"}

        # Financial fee check
        fee = facility.fee_usd
        if human.physical_state.money < fee:
            return {"success": False, "reason": f"Insufficient funds for clinic fee (${human.physical_state.money:.2f} < ${fee:.2f})"}

        # Deduct fee with strict cash conservation
        human.physical_state.money = round(human.physical_state.money - fee, 2)
        facility.medical_supplies_level = max(0.10, facility.medical_supplies_level - 0.02)
        facility.total_patients_treated += 1
        patient_uid = str(human.uid)
        if patient_uid not in facility.current_patients:
            facility.current_patients.append(patient_uid)
            facility.admitted_at[patient_uid] = current_tick

        # Mark active conditions as treated
        treated_count = 0
        conditions: list[HealthCondition] = getattr(human, "active_health_conditions", [])
        for cond in conditions:
            if not cond.is_treated:
                cond.is_treated = True
                cond.treatment_tick = current_tick
                cond.severity = max(0.10, cond.severity * 0.60)
                treated_count += 1

        # Clinical record
        rec_id = f"tr_{uuid.uuid4().hex[:8]}"
        record = TreatmentRecord(
            record_id=rec_id,
            patient_uid=str(human.uid),
            facility_id=facility_id,
            condition_name=conditions[0].name if conditions else "Chequeo Preventivo",
            tick=current_tick,
            fee_charged_usd=fee,
            outcome="treated",
        )
        self.treatment_history.append(record)

        logger.info("Human %s treated at %s (fee $%.2f)", human.name, facility.name, fee)
        if event_bus:
            evt_treat = SimulationEvent(
                event_type=EventType.HEALTH_TREATMENT_RECEIVED,
                tick=current_tick,
                source_human_id=human.uid,
                location_id=facility.location_id,
                coordinates=facility.coordinates,
                data={
                    "facility_id": facility_id,
                    "facility_name": facility.name,
                    "fee_usd": fee,
                    "conditions_treated": treated_count,
                    "coordinate_provenance": "verified_facility",
                },
                importance=0.65,
            )
            event_bus.emit(evt_treat)
            if causal_graph:
                causal_graph.add_event(evt_treat, description=f"{human.name} recibió tratamiento médico en {facility.name}")

        return {
            "success": True,
            "facility_name": facility.name,
            "fee_usd": fee,
            "treated_conditions_count": treated_count,
        }

    def step_facilities(self, current_tick: Tick, max_stay_ticks: int = 16) -> list[dict[str, Any]]:
        """Release stabilized patients so bed capacity is finite and reusable.

        Without discharge, a clinic would fill once and remain permanently at
        capacity, making access inequality and capacity triage meaningless.
        """
        released: list[dict[str, Any]] = []
        for facility in self._facilities.values():
            for patient_uid, admitted_tick in list(facility.admitted_at.items()):
                if current_tick - admitted_tick >= max_stay_ticks:
                    facility.admitted_at.pop(patient_uid, None)
                    if patient_uid in facility.current_patients:
                        facility.current_patients.remove(patient_uid)
                    released.append({
                        "facility_id": facility.facility_id,
                        "patient_uid": patient_uid,
                        "admitted_tick": admitted_tick,
                        "released_tick": current_tick,
                    })
        return released

    def release_patient(self, human_uid: str) -> None:
        """Remove a recovered patient from any facility bed."""
        for facility in self._facilities.values():
            if human_uid in facility.current_patients:
                facility.current_patients.remove(human_uid)
            facility.admitted_at.pop(human_uid, None)

    def to_dict(self) -> dict[str, Any]:
        """Serialize facilities, occupancy and treatment history."""
        facilities = []
        for f in self._facilities.values():
            facilities.append({
                "facility_id": f.facility_id,
                "name": f.name,
                "facility_type": f.facility_type,
                "location_id": f.location_id,
                "coordinates": list(f.coordinates),
                "capacity_beds": f.capacity_beds,
                "current_patients": list(f.current_patients),
                "admitted_at": dict(f.admitted_at),
                "staff_available": f.staff_available,
                "medical_supplies_level": f.medical_supplies_level,
                "fee_usd": f.fee_usd,
                "waiting_time_ticks": f.waiting_time_ticks,
                "operating_hours": list(f.operating_hours),
                "total_patients_treated": f.total_patients_treated,
                "total_rejected_capacity": f.total_rejected_capacity,
            })
        history = [
            {
                "record_id": r.record_id,
                "patient_uid": r.patient_uid,
                "facility_id": r.facility_id,
                "condition_name": r.condition_name,
                "tick": r.tick,
                "fee_charged_usd": r.fee_charged_usd,
                "outcome": r.outcome,
            }
            for r in self.treatment_history
        ]
        return {"facilities": facilities, "treatment_history": history}

    def load_dict(self, data: dict[str, Any]) -> None:
        """Restore facilities and treatment records from a checkpoint."""
        self._facilities.clear()
        self.treatment_history.clear()
        for f in data.get("facilities", []):
            facility = MedicalFacility(
                facility_id=f["facility_id"],
                name=f["name"],
                facility_type=f.get("facility_type", "unidad_salud"),
                location_id=f.get("location_id", "unidad_salud"),
                coordinates=tuple(f.get("coordinates", (13.935, -89.028))),
                capacity_beds=int(f.get("capacity_beds", 10)),
                current_patients=list(f.get("current_patients", [])),
                admitted_at={str(k): int(v) for k, v in f.get("admitted_at", {}).items()},
                staff_available=int(f.get("staff_available", 3)),
                medical_supplies_level=float(f.get("medical_supplies_level", 0.85)),
                fee_usd=float(f.get("fee_usd", 0.0)),
                waiting_time_ticks=int(f.get("waiting_time_ticks", 2)),
                operating_hours=tuple(f.get("operating_hours", (7, 17))),
                total_patients_treated=int(f.get("total_patients_treated", 0)),
                total_rejected_capacity=int(f.get("total_rejected_capacity", 0)),
            )
            self.register_facility(facility)
        for r in data.get("treatment_history", []):
            self.treatment_history.append(TreatmentRecord(
                record_id=r["record_id"],
                patient_uid=r["patient_uid"],
                facility_id=r["facility_id"],
                condition_name=r.get("condition_name", ""),
                tick=int(r.get("tick", 0)),
                fee_charged_usd=float(r.get("fee_charged_usd", 0.0)),
                outcome=r.get("outcome", "treated"),
            ))
