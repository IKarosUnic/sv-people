"""Health, Disease & Medical Infrastructure Models (Phase 1.5 Extension).

Defines explicit biological health conditions, epidemiological transmission attributes,
clinical triage structures, and healthcare facility parameters.
"""

from __future__ import annotations

import dataclasses
from typing import Any, List, Optional, Tuple

from saltbor.core.types import ConditionCategory, HumanID, LocationID, Tick


@dataclasses.dataclass
class HealthCondition:
    """An active medical condition, disease, injury, or emotional distress state."""
    condition_id: str
    name: str
    category: ConditionCategory
    severity: float                      # [0.0, 1.0] where 1.0 is critical / incapacitated
    onset_tick: Tick = 0
    duration_ticks: int = 40             # Estimated natural course in ticks
    ticks_active: int = 0
    symptoms: list[str] = dataclasses.field(default_factory=list)

    # Transmission & Epidemiology
    is_contagious: bool = False
    transmission_rate: float = 0.0       # Secondary attack probability on close contact
    incubation_ticks: int = 0
    origin_exposure: str = "environment" # "water", "airborne_contact", "occupational", "vector"

    # Clinical Trajectory & Outcomes
    recovery_probability_per_day: float = 0.35
    complications_risk: float = 0.10
    treatment_required: str = "Reposo, hidratación y analgésicos"
    is_treated: bool = False
    treatment_tick: Optional[Tick] = None

    # Physiological Impact
    energy_drain_per_tick: float = 0.02
    health_drain_per_tick: float = 0.01

    @property
    def is_critical(self) -> bool:
        return self.severity >= 0.75

    @property
    def is_incubating(self) -> bool:
        return self.ticks_active < self.incubation_ticks

    def to_dict(self) -> dict[str, Any]:
        """Serialize a condition with its full clinical trajectory."""
        return {
            "condition_id": self.condition_id,
            "name": self.name,
            "category": self.category.value if hasattr(self.category, "value") else str(self.category),
            "severity": self.severity,
            "onset_tick": self.onset_tick,
            "duration_ticks": self.duration_ticks,
            "ticks_active": self.ticks_active,
            "symptoms": list(self.symptoms),
            "is_contagious": self.is_contagious,
            "transmission_rate": self.transmission_rate,
            "incubation_ticks": self.incubation_ticks,
            "origin_exposure": self.origin_exposure,
            "recovery_probability_per_day": self.recovery_probability_per_day,
            "complications_risk": self.complications_risk,
            "treatment_required": self.treatment_required,
            "is_treated": self.is_treated,
            "treatment_tick": self.treatment_tick,
            "energy_drain_per_tick": self.energy_drain_per_tick,
            "health_drain_per_tick": self.health_drain_per_tick,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HealthCondition":
        """Restore a condition captured by :meth:`to_dict`."""
        try:
            category = ConditionCategory(data.get("category", "infectious"))
        except ValueError:
            category = ConditionCategory.INFECTIOUS
        return cls(
            condition_id=str(data.get("condition_id", "cond_unknown")),
            name=str(data.get("name", "Condición")),
            category=category,
            severity=float(data.get("severity", 0.5)),
            onset_tick=int(data.get("onset_tick", 0)),
            duration_ticks=int(data.get("duration_ticks", 40)),
            ticks_active=int(data.get("ticks_active", 0)),
            symptoms=list(data.get("symptoms", [])),
            is_contagious=bool(data.get("is_contagious", False)),
            transmission_rate=float(data.get("transmission_rate", 0.0)),
            incubation_ticks=int(data.get("incubation_ticks", 0)),
            origin_exposure=str(data.get("origin_exposure", "environment")),
            recovery_probability_per_day=float(data.get("recovery_probability_per_day", 0.35)),
            complications_risk=float(data.get("complications_risk", 0.10)),
            treatment_required=str(data.get("treatment_required", "")),
            is_treated=bool(data.get("is_treated", False)),
            treatment_tick=int(data["treatment_tick"]) if data.get("treatment_tick") is not None else None,
            energy_drain_per_tick=float(data.get("energy_drain_per_tick", 0.02)),
            health_drain_per_tick=float(data.get("health_drain_per_tick", 0.01)),
        )


@dataclasses.dataclass
class MedicalFacility:
    """A physical healthcare institution (Unidad de Salud, Clínica Comunal, Hospital)."""
    facility_id: str
    name: str
    facility_type: str                   # "unidad_salud", "clinica_comunal", "hospital"
    location_id: LocationID
    coordinates: tuple[float, float] = (13.935, -89.028)
    capacity_beds: int = 10
    current_patients: list[str] = dataclasses.field(default_factory=list)
    admitted_at: dict[str, Tick] = dataclasses.field(default_factory=dict)
    staff_available: int = 3
    medical_supplies_level: float = 0.85 # [0.0, 1.0] supply depletion affects efficacy
    fee_usd: float = 0.0                 # Public services are free or subsidized
    waiting_time_ticks: int = 2
    operating_hours: tuple[int, int] = (7, 17)

    # Lifetime metrics
    total_patients_treated: int = 0
    total_rejected_capacity: int = 0

    @property
    def has_capacity(self) -> bool:
        return len(self.current_patients) < self.capacity_beds

    def is_open_at_hour(self, hour: int) -> bool:
        start, end = self.operating_hours
        if start <= end:
            return start <= hour < end
        return hour >= start or hour < end


@dataclasses.dataclass
class TreatmentRecord:
    """Historical clinical triage and treatment record."""
    record_id: str
    patient_uid: str
    facility_id: str
    condition_name: str
    tick: Tick
    fee_charged_usd: float
    outcome: str                         # "treated", "stabilized", "referred", "deferred"
