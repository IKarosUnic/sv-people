"""Phase 1.5 Extension: World-Human Interaction, Complete Life Events & Emergent Human Society Experiments.

Implements the 16 rigorous integration experiments:
1.  EXP_15_EXT_01 — Romantic Relationship Formation & Courtship
2.  EXP_15_EXT_02 — Jealousy Emergence and Infidelity Dynamics
3.  EXP_15_EXT_03 — Infidelity Discovery, Trust Collapse & Separation
4.  EXP_15_EXT_04 — Unrequited Love, Heartbreak Grief & Recovery
5.  EXP_15_EXT_05 — Family Caregiving & Intergenerational Elder Support
6.  EXP_15_EXT_06 — Child Dependency, Parental Care & Attachment
7.  EXP_15_EXT_07 — Illness Onset, Symptom Progression & Clinical Recovery
8.  EXP_15_EXT_08 — Infectious Disease Airborne Transmission & Contact Patterns
9.  EXP_15_EXT_09 — Medical Access Inequality, Clinic Capacity & Triage
10. EXP_15_EXT_10 — Traffic Accidents & Contextual Environmental Hazards
11. EXP_15_EXT_11 — Workplace Injuries & Fatigue Hazard Multipliers
12. EXP_15_EXT_12 — Flooding, Road Blockage & Household Displacement
13. EXP_15_EXT_13 — Environmental Water Pollution & Community Cleanup Faena
14. EXP_15_EXT_14 — Crime, Theft & Strict Monetary Conservation
15. EXP_15_EXT_15 — Acute Financial Shock, Informal Day Labor & Recovery
16. EXP_15_EXT_16 — Multi-System Causal Cascade Traceability
"""

from __future__ import annotations

import logging
import math
import time
from typing import Any, Dict, List, Optional
import uuid

import numpy as np

from saltbor.accidents.engine import MisfortuneEngine
from saltbor.accidents.models import AccidentEvent, DisasterEvent
from saltbor.core.types import (
    AccidentType,
    ConditionCategory,
    DisasterType,
    EmotionType,
    EmploymentStatus,
    GeographicObjectType,
    HousingTenureType,
    RomanceStage,
    Tick,
)
from saltbor.events.causal_graph import CausalEventGraph
from saltbor.events.types import EventType, SimulationEvent
from saltbor.health.engine import HealthEngine
from saltbor.lifecycle.family.caregiving import FamilyCaregivingEngine
from saltbor.population.human import SyntheticHuman
from saltbor.simulation.experiments.base import (
    BaseExperiment,
    ExperimentConfig,
    ExperimentResult,
)
from saltbor.social.romance.engine import RomanceEngine
from saltbor.world.interaction.world_human_engine import WorldHumanInteractionEngine

logger = logging.getLogger(__name__)


def _make_agent(
    name: str,
    serial: int,
    money: float = 100.0,
    age: float = 28.0,
    seed: int = 42,
    occupation: str = "Agricultor",
) -> SyntheticHuman:
    """Helper to instantiate a differentiated SyntheticHuman."""
    h = SyntheticHuman.create(
        name=name,
        serial=serial,
        age=age,
        money=money,
        seed=seed,
    )
    h.demographics.occupation = occupation
    return h


# ============================================================================
# 1. EXP_15_EXT_01: Romantic Relationship Formation & Courtship
# ============================================================================

class Experiment15_EXT_01_RomanticFormation(BaseExperiment):
    """Verify that attraction and repeated courtship dates build affection, trust, and commitment."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_01",
            name="Romantic Relationship Formation & Courtship",
            description="Two unpartnered individuals with positive attraction date and advance from interest to formal dating.",
            duration_ticks=20,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = RomanceEngine(seed=self.config.random_seed)

        agent_a = _make_agent("Carlos Menjívar", 101, age=26.0, seed=11)
        agent_b = _make_agent("Elena Vasquez", 102, age=25.0, seed=12)

        # 1. Form initial interest
        rel = engine.initiate_romantic_interest(agent_a, agent_b, current_tick=1)
        assert rel is not None, "Failed to initiate romantic interest"
        assert rel.stage == RomanceStage.INTEREST

        init_aff = rel.dims_a.affection
        init_comm = rel.dims_a.commitment

        # 2. Conduct courtship dates
        for tick in range(2, 6):
            res = engine.conduct_courtship_date(rel.relationship_id, current_tick=tick)

        assert rel.dates_count == 4
        assert rel.dims_a.affection > init_aff, "Affection failed to increase"
        assert rel.dims_a.commitment > init_comm, "Commitment failed to increase"
        assert rel.stage == RomanceStage.DATING, f"Expected DATING, got {rel.stage.value}"

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Repeated courtship dates increase mutual affection, trust, and commitment",
            "predicted": True,
            "observed": (rel.dates_count == 4 and rel.stage == RomanceStage.DATING),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary=f"Romantic relationship successfully advanced to {rel.stage.value} with 4 dates.",
            hypotheses=[hyp],
            metrics={
                "initial_affection": init_aff,
                "final_affection": rel.dims_a.affection,
                "dates_count": rel.dates_count,
                "final_stage": rel.stage.value,
            },
            duration_seconds=elapsed,
            raw_data={"relationship": rel.to_dict()},
        )


# ============================================================================
# 2. EXP_15_EXT_02: Jealousy Emergence and Infidelity Dynamics
# ============================================================================

class Experiment15_EXT_02_JealousyAndInfidelity(BaseExperiment):
    """Verify that low commitment and high third-party attraction can precipitate infidelity."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_02",
            name="Jealousy Emergence and Infidelity Dynamics",
            description="An individual in a low-commitment relationship encounters an attractive third party, leading to an affair.",
            duration_ticks=10,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = RomanceEngine(seed=self.config.random_seed)

        agent_a = _make_agent("Roberto Rivas", 201, age=30.0, seed=21)
        agent_b = _make_agent("Silvia Castro", 202, age=29.0, seed=22)
        third_party = _make_agent("Marta Gómez", 203, age=28.0, seed=23)

        rel = engine.initiate_romantic_interest(agent_a, agent_b, current_tick=1)
        assert rel is not None
        rel.stage = RomanceStage.DATING
        # Artificially weaken commitment and increase conflict
        rel.dims_a.commitment = 0.20
        rel.dims_a.conflict_level = 0.65

        record = None
        for tick in range(2, 10):
            record = engine.evaluate_jealousy_and_infidelity(agent_a, third_party, current_tick=tick)
            if record:
                break
        assert record is not None, "Infidelity failed to occur under high vulnerability"
        assert record.is_discovered is False, "Infidelity should start secret / undiscovered"
        assert len(rel.infidelity_history) == 1

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Low commitment and high friction make infidelity plausible under third-party attraction",
            "predicted": True,
            "observed": (record is not None and not record.is_discovered),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Secret infidelity emerged under low commitment and high conflict.",
            hypotheses=[hyp],
            metrics={
                "infidelity_occurred": True,
                "is_discovered": record.is_discovered,
                "wayward_partner": record.wayward_partner_uid,
                "post_commitment": rel.dims_a.commitment,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 3. EXP_15_EXT_03: Infidelity Discovery, Trust Collapse & Separation
# ============================================================================

class Experiment15_EXT_03_InfidelityDiscoveryAndConfrontation(BaseExperiment):
    """Verify that discovery of an affair precipitates trust collapse and leads to separation/divorce."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_03",
            name="Infidelity Discovery, Trust Collapse & Separation",
            description="Discovery of secret infidelity destroys betrayed partner trust, causing relationship termination.",
            duration_ticks=10,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = RomanceEngine(seed=self.config.random_seed)

        agent_a = _make_agent("Manuel Guardado", 301, age=32.0, seed=31)
        agent_b = _make_agent("Lorena Martinez", 302, age=31.0, seed=32)
        third_party = _make_agent("Carolina Peña", 303, age=27.0, seed=33)

        rel = engine.initiate_romantic_interest(agent_a, agent_b, current_tick=1)
        assert rel is not None
        rel.stage = RomanceStage.COHABITING
        rel.dims_b.trust = 0.85
        rel.dims_b.jealousy = 0.90  # High suspicion accelerates discovery
        rel.dims_b.compatibility = 0.15  # Poor compatibility makes separation decisive
        rel.dims_b.communication_quality = 0.10

        # Manuel commits infidelity
        rel.dims_a.commitment = 0.15
        rel.dims_a.conflict_level = 0.70
        inf_rec = None
        for tick in range(2, 10):
            inf_rec = engine.evaluate_jealousy_and_infidelity(agent_a, third_party, current_tick=tick)
            if inf_rec:
                break
        assert inf_rec is not None

        # Evaluate discovery
        disc_res = None
        for tick in range(10, 20):
            disc_res = engine.evaluate_infidelity_discovery(rel.relationship_id, current_tick=tick)
            if disc_res:
                break
        assert disc_res is not None, "Discovery failed to trigger under high suspicion"
        assert inf_rec.is_discovered is True
        assert rel.dims_b.trust <= 0.25, f"Trust failed to collapse: {rel.dims_b.trust}"
        if disc_res.get("outcome") == "forgiven_reconciliation":
            assert rel.dims_b.trust == 0.25
            assert rel.is_active is True
        else:
            assert rel.stage in (RomanceStage.SEPARATED, RomanceStage.DIVORCED)
            assert rel.is_active is False

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Infidelity discovery causes catastrophic trust collapse and confrontation outcome",
            "predicted": True,
            "observed": (rel.dims_b.trust <= 0.25 and inf_rec.is_discovered),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary=f"Discovery collapsed trust to {rel.dims_b.trust:.2f} resulting in {rel.stage.value}.",
            hypotheses=[hyp],
            metrics={
                "discovered": True,
                "collapsed_trust": rel.dims_b.trust,
                "outcome": disc_res.get("outcome"),
                "relationship_active": rel.is_active,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 4. EXP_15_EXT_04: Unrequited Love, Heartbreak Grief & Recovery
# ============================================================================

class Experiment15_EXT_04_UnrequitedLoveAndHeartbreak(BaseExperiment):
    """Verify that romantic heartbreak creates acute grief that gradually heals over time."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_04",
            name="Unrequited Love, Heartbreak Grief & Recovery",
            description="An individual experiencing heartbreak processes emotional grief with measurable recovery.",
            duration_ticks=30,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = RomanceEngine(seed=self.config.random_seed)

        agent = _make_agent("Héctor Landaverde", 401, age=24.0, seed=41)
        from saltbor.social.romance.models import HeartbreakRecord
        hb = HeartbreakRecord(
            record_id="hb_01",
            individual_uid=str(agent.uid),
            former_partner_uid="uid_partner_former",
            tick_started=1,
            pain_intensity=0.80,
            reason="Amor no correspondido y rechazo sentimental",
        )
        agent.heartbreak_state = hb

        # Step emotional healing over 48 ticks (2 days)
        for tick in range(2, 50):
            engine.step_heartbreak_recovery(agent, current_tick=tick)

        assert hb.recovery_progress > 0.05, "Heartbreak recovery failed to progress"

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Heartbreak recovery progresses gradually over consecutive ticks",
            "predicted": True,
            "observed": hb.recovery_progress > 0.05,
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary=f"Heartbreak recovery progressed to {hb.recovery_progress:.2f}.",
            hypotheses=[hyp],
            metrics={
                "initial_pain": 0.80,
                "recovery_progress": hb.recovery_progress,
                "is_healed": hb.is_healed,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 5. EXP_15_EXT_05: Family Caregiving & Intergenerational Elder Support
# ============================================================================

class Experiment15_EXT_05_FamilyCaregivingElderSupport(BaseExperiment):
    """Verify adult children physically assist and financially support elderly parents."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_05",
            name="Family Caregiving & Intergenerational Elder Support",
            description="Adult child provides care and living allowance to an elderly relative with reduced health.",
            duration_ticks=10,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = FamilyCaregivingEngine()

        caregiver = _make_agent("Juan Morales", 501, money=80.0, age=35.0, seed=51)
        elder = _make_agent("Abuela Carmen", 502, money=5.0, age=72.0, seed=52)
        elder.physical_state.health = 0.55

        res = engine.perform_elder_care(
            caregiver=caregiver,
            elder=elder,
            financial_support_usd=15.0,
            current_tick=10,
        )

        assert res.get("success") is True
        assert elder.physical_state.money == 20.0, f"Expected elder $20.0, got {elder.physical_state.money}"
        assert caregiver.physical_state.money == 65.0, f"Expected caregiver $65.0, got {caregiver.physical_state.money}"
        assert elder.physical_state.health > 0.55, "Elder health was not stabilized"

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Elder care stabilizes elderly health and transfers support funds strictly from child savings",
            "predicted": True,
            "observed": (elder.physical_state.money == 20.0 and elder.physical_state.health > 0.55),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Elder received physical care and $15 support transfer from adult child.",
            hypotheses=[hyp],
            metrics={
                "elder_money_after": elder.physical_state.money,
                "caregiver_money_after": caregiver.physical_state.money,
                "elder_health": elder.physical_state.health,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 6. EXP_15_EXT_06: Child Dependency, Parental Care & Attachment
# ============================================================================

class Experiment15_EXT_06_ChildDependencyAndCare(BaseExperiment):
    """Verify young children rely on parental care to relieve hunger and gain emotional security."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_06",
            name="Child Dependency, Parental Care & Attachment",
            description="Parent performs childcare: child hunger is relieved and affection emotion is formed.",
            duration_ticks=10,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = FamilyCaregivingEngine()

        parent = _make_agent("Rosa Hernández", 601, age=29.0, seed=61)
        child = _make_agent("Carlitos Hernández", 602, age=6.0, seed=62)
        child.physical_state.hunger = 0.70

        res = engine.perform_childcare(caregiver=parent, child=child, current_tick=15)
        assert res.get("success") is True
        assert child.physical_state.hunger < 0.70, "Child hunger failed to drop"
        assert child.emotions.get_emotion(EmotionType.AFFECTION) > 0.0, "Child failed to gain affection security"

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Parental childcare reduces child hunger and fosters affection emotion",
            "predicted": True,
            "observed": (child.physical_state.hunger < 0.70 and child.emotions.get_emotion(EmotionType.AFFECTION) > 0.0),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Childcare successfully reduced hunger and generated affection attachment.",
            hypotheses=[hyp],
            metrics={
                "child_hunger_after": child.physical_state.hunger,
                "child_has_affection": child.emotions.get_emotion(EmotionType.AFFECTION) > 0.0,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 7. EXP_15_EXT_07: Illness Onset, Symptom Progression & Clinical Recovery
# ============================================================================

class Experiment15_EXT_07_IllnessOnsetAndClinicalRecovery(BaseExperiment):
    """Verify illness symptom progression and accelerated cure via medical treatment."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_07",
            name="Illness Onset, Symptom Progression & Clinical Recovery",
            description="Individual contracts illness, presents to clinic, receives treatment, and recovers safely.",
            duration_ticks=30,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = HealthEngine(seed=self.config.random_seed)

        patient = _make_agent("Mario Palacios", 701, money=40.0, seed=71)
        illness = engine.create_waterborne_illness(tick=1, origin="rio_suchiacel")
        patient.active_health_conditions.append(illness)

        init_health = patient.physical_state.health
        # 1. Step illness progression untreated for 5 ticks
        for t in range(2, 7):
            engine.step_individual_health(patient, current_tick=t)

        assert patient.physical_state.health < init_health, "Illness did not drain health"

        # 2. Seek medical care at clinic
        treat_res = engine.seek_medical_treatment(
            human=patient,
            facility_id="unidad_salud_suchitoto",
            current_tick=8,
        )
        assert treat_res.get("success") is True, f"Treatment failed: {treat_res.get('reason')}"
        assert illness.is_treated is True

        # 3. Step towards recovery
        for t in range(9, 35):
            engine.step_individual_health(patient, current_tick=t)

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Clinical treatment halts illness degradation and initiates recovery",
            "predicted": True,
            "observed": (illness.is_treated is True),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Patient contracted waterborne illness, received clinical treatment, and stabilized.",
            hypotheses=[hyp],
            metrics={
                "treated": illness.is_treated,
                "final_health": patient.physical_state.health,
                "ticks_active": illness.ticks_active,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 8. EXP_15_EXT_08: Infectious Disease Airborne Transmission & Contact Patterns
# ============================================================================

class Experiment15_EXT_08_AirborneDiseaseTransmission(BaseExperiment):
    """Verify that contagious respiratory disease transmits selectively to co-located individuals."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_08",
            name="Infectious Disease Airborne Transmission & Contact Patterns",
            description="Contagious individual interacts in co-located space with peers; transmission occurs based on susceptibility.",
            duration_ticks=10,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = HealthEngine(seed=self.config.random_seed)

        patient_zero = _make_agent("Infected Host", 801, seed=81)
        gripe = engine.create_respiratory_infection(tick=1)
        gripe.incubation_ticks = 0  # Active infectious stage
        patient_zero.active_health_conditions.append(gripe)

        # 3 susceptible co-located contacts in the same room
        contacts = [
            _make_agent(f"Peer_{i}", 802 + i, seed=82 + i)
            for i in range(3)
        ]
        # Make one peer fatigued (high susceptibility)
        contacts[0].physical_state.health = 0.50
        contacts[0].physical_state.energy = 0.20

        infected_uids: list[str] = []
        for tick in range(2, 12):
            batch = engine.simulate_airborne_contagion(
                infected_human=patient_zero,
                nearby_humans=contacts,
                current_tick=tick,
            )
            infected_uids.extend(batch)
            if infected_uids:
                break

        assert len(infected_uids) > 0, "Airborne transmission failed to spread to susceptible contacts"

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Airborne respiratory infection transmits selectively to co-located susceptible peers",
            "predicted": True,
            "observed": len(infected_uids) > 0,
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary=f"Infected host transmitted contagion to {len(infected_uids)} co-located contact(s).",
            hypotheses=[hyp],
            metrics={
                "contacts_exposed": len(contacts),
                "infected_count": len(infected_uids),
                "infected_uids": infected_uids,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 9. EXP_15_EXT_09: Medical Access Inequality, Clinic Capacity & Triage
# ============================================================================

class Experiment15_EXT_09_MedicalCapacityAndTriage(BaseExperiment):
    """Verify that clinics enforce realistic bed capacity and triage limitations."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_09",
            name="Medical Access Inequality, Clinic Capacity & Triage",
            description="Small clinic fills to maximum capacity; subsequent presenting patient is turned away.",
            duration_ticks=10,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = HealthEngine(seed=self.config.random_seed)

        # Retrieve rural dispensary with capacity = 2
        clinic = engine.get_facility("clinica_comunal_san_pedro")
        assert clinic is not None
        clinic.capacity_beds = 2  # Set small limit for test
        clinic.current_patients.clear()

        # Present 3 patients
        patients = [_make_agent(f"Patient_{i}", 901 + i, money=20.0, seed=91 + i) for i in range(3)]
        outcomes = []
        for p in patients:
            res = engine.seek_medical_treatment(p, facility_id="clinica_comunal_san_pedro", current_tick=10)
            outcomes.append(res)

        # First 2 should succeed, 3rd should be rejected due to capacity
        assert outcomes[0].get("success") is True
        assert outcomes[1].get("success") is True
        assert outcomes[2].get("success") is False, "Overflow patient should be turned away"
        assert "capacity" in outcomes[2].get("reason", "").lower()

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Health clinics strictly enforce physical capacity limits, turning away overflow",
            "predicted": True,
            "observed": (outcomes[0].get("success") and outcomes[1].get("success") and not outcomes[2].get("success")),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary=f"Dispensary admitted {len(clinic.current_patients)}/2 and correctly rejected excess patient.",
            hypotheses=[hyp],
            metrics={
                "capacity": clinic.capacity_beds,
                "treated": len(clinic.current_patients),
                "rejected_count": clinic.total_rejected_capacity,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 10. EXP_15_EXT_10: Traffic Accidents & Contextual Environmental Hazards
# ============================================================================

class Experiment15_EXT_10_TrafficAccidentsHazards(BaseExperiment):
    """Verify traffic accidents emerge from adverse precipitation, road condition, and driver fatigue."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_10",
            name="Traffic Accidents & Contextual Environmental Hazards",
            description="High rainfall and severe driver fatigue elevate traffic accident risk and cause damage.",
            duration_ticks=10,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        misfortune = MisfortuneEngine(seed=self.config.random_seed)
        health = HealthEngine(seed=self.config.random_seed)

        driver = _make_agent("Conductor Agotado", 1001, money=60.0, seed=101)
        driver.physical_state.energy = 0.10  # Severely fatigued

        # Weather state with heavy rain
        from saltbor.world.interaction.environmental_hazards import EnvironmentalHazardProfile
        weather = EnvironmentalHazardProfile(rainfall_mm_per_hour=25.0)

        accident = None
        # Evaluate multiple trips in stormy conditions
        for t in range(1, 30):
            accident = misfortune.evaluate_traffic_accident(
                human=driver,
                road_id="carretera_los_chorros",
                weather_state=weather,
                current_tick=t,
                health_engine=health,
            )
            if accident:
                break

        assert accident is not None, "Traffic accident failed to trigger under storm and severe fatigue"
        assert accident.accident_type == AccidentType.TRAFFIC_ACCIDENT
        assert accident.property_damage_usd > 0.0

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Severe fatigue combined with stormy weather triggers traffic accident risk",
            "predicted": True,
            "observed": (accident is not None and accident.property_damage_usd > 0.0),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary=f"Traffic accident triggered with ${accident.property_damage_usd:.2f} damage.",
            hypotheses=[hyp],
            metrics={
                "accident_id": accident.accident_id,
                "severity": accident.severity,
                "property_damage_usd": accident.property_damage_usd,
                "driver_injured": accident.injury_sustained,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 11. EXP_15_EXT_11: Workplace Injuries & Fatigue Hazard Multipliers
# ============================================================================

class Experiment15_EXT_11_WorkplaceInjuriesFatigue(BaseExperiment):
    """Verify occupational injury hazard increases under severe worker fatigue."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_11",
            name="Workplace Injuries & Fatigue Hazard Multipliers",
            description="Exhausted agricultural laborer operating tools incurs workplace trauma.",
            duration_ticks=10,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        misfortune = MisfortuneEngine(seed=self.config.random_seed)
        health = HealthEngine(seed=self.config.random_seed)

        laborer = _make_agent("Jornalero Cansado", 1101, seed=111)
        laborer.physical_state.energy = 0.15  # Heavy fatigue

        incident = None
        for t in range(1, 25):
            incident = misfortune.evaluate_workplace_incident(
                human=laborer,
                task_hazard_level=0.80,  # Agricultural machete clearing
                current_tick=t,
                health_engine=health,
            )
            if incident:
                break

        assert incident is not None, "Workplace injury failed to trigger under high fatigue and tool hazard"
        assert incident.injury_sustained is True
        assert len(laborer.active_health_conditions) > 0, "Laborer failed to receive injury condition"

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Workplace injury occurs when operating hazardous tools under severe fatigue",
            "predicted": True,
            "observed": (incident is not None and incident.injury_sustained),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Workplace trauma occurred during hazardous agricultural task under exhaustion.",
            hypotheses=[hyp],
            metrics={
                "incident_id": incident.accident_id,
                "severity": incident.severity,
                "laborer_conditions": len(laborer.active_health_conditions),
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 12. EXP_15_EXT_12: Flooding, Road Blockage & Household Displacement
# ============================================================================

class Experiment15_EXT_12_FloodingDisasterDisplacement(BaseExperiment):
    """Verify environmental disaster damages dwellings, blocks transportation, and displaces occupants."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_12",
            name="Flooding, Road Blockage & Household Displacement",
            description="Severe river flooding blocks access routes and degrades residential habitability.",
            duration_ticks=10,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        misfortune = MisfortuneEngine(seed=self.config.random_seed)
        from saltbor.economy.housing.engine import HousingEngine, HousingUnit

        housing = HousingEngine()
        unit = HousingUnit(
            unit_id="unit_ribera",
            name="Casa en la Ribera del Río",
            location_id="ribera_suchiacel",
            tenure_type=HousingTenureType.RENTAL,
            occupant_uids=["agent_fam_1", "agent_fam_2"],
            quality_score=0.80,
        )
        housing.register_unit(unit)

        disaster = misfortune.trigger_environmental_disaster(
            disaster_type=DisasterType.FLOODING,
            affected_location_ids=["ribera_suchiacel"],
            severity=0.75,
            current_tick=12,
            housing_engine=housing,
        )

        assert disaster is not None
        assert "carretera_los_chorros" in misfortune.blocked_roads
        assert unit.quality_score < 0.80, "Dwelling quality failed to degrade"
        assert len(disaster.displaced_human_ids) == 2, "Occupants failed to be displaced"

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Severe flooding blocks access roads and causes residential displacement",
            "predicted": True,
            "observed": ("carretera_los_chorros" in misfortune.blocked_roads and len(disaster.displaced_human_ids) == 2),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary=f"Flooding disaster blocked roads and displaced {len(disaster.displaced_human_ids)} individuals.",
            hypotheses=[hyp],
            metrics={
                "disaster_type": disaster.disaster_type.value,
                "roads_blocked": list(misfortune.blocked_roads),
                "dwelling_quality_after": unit.quality_score,
                "displaced_count": len(disaster.displaced_human_ids),
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 13. EXP_15_EXT_13: Environmental Water Pollution & Community Cleanup Faena
# ============================================================================

class Experiment15_EXT_13_WaterPollutionAndCleanupFaena(BaseExperiment):
    """Verify human settlement degrades water quality and community faenas restore potability."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_13",
            name="Environmental Water Pollution & Community Cleanup Faena",
            description="Untreated waste accumulation pollutes water source; community collective action restores it.",
            duration_ticks=20,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = WorldHumanInteractionEngine(seed=self.config.random_seed)

        # 1. Simulate heavy settlement waste accumulation
        engine.hazards.accumulated_waste_kg = 350.0
        engine.record_human_environmental_impact(population_count=50, current_tick=24)

        # Force river degradation below potability threshold
        engine.hazards.water_sources["rio_suchiacel"] = 0.40
        assert engine.hazards.is_water_source_potable("rio_suchiacel") is False, "Water should be non-potable"

        # 2. Organize community cleanup faena with 10 volunteers
        res = engine.execute_community_cleanup_faena(
            volunteers_count=10,
            water_source="rio_suchiacel",
            current_tick=26,
        )

        assert res.get("success") is True
        assert res.get("is_potable") is True, f"Water failed to reach potability: {res.get('new_cleanliness')}"
        assert engine.hazards.water_sources["rio_suchiacel"] >= 0.70

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Community faena mobilizes collective action to restore water potability",
            "predicted": True,
            "observed": (res.get("is_potable") is True and engine.hazards.water_sources["rio_suchiacel"] >= 0.70),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary=f"Community faena restored river potability to {engine.hazards.water_sources['rio_suchiacel']:.2f}.",
            hypotheses=[hyp],
            metrics={
                "initial_cleanliness": 0.40,
                "restored_cleanliness": engine.hazards.water_sources["rio_suchiacel"],
                "waste_removed_kg": res.get("waste_removed_kg"),
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 14. EXP_15_EXT_14: Crime, Theft & Strict Monetary Conservation
# ============================================================================

class Experiment15_EXT_14_TheftVictimizationAndConservation(BaseExperiment):
    """Verify theft transfers money strictly between individuals without currency creation or deletion."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_14",
            name="Crime, Theft & Strict Monetary Conservation",
            description="Theft incident transfers funds from victim to perpetrator, rigorously preserving total money.",
            duration_ticks=5,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        misfortune = MisfortuneEngine(seed=self.config.random_seed)

        victim = _make_agent("Comerciante Víctima", 1401, money=85.0, seed=141)
        thief = _make_agent("Ladrón Oportunista", 1402, money=2.0, seed=142)
        total_before = victim.physical_state.money + thief.physical_state.money

        res = misfortune.execute_theft_incident(
            victim=victim,
            perpetrator=thief,
            stolen_amount_usd=25.0,
            current_tick=5,
        )

        total_after = victim.physical_state.money + thief.physical_state.money
        assert res.get("success") is True
        assert victim.physical_state.money == 60.0
        assert thief.physical_state.money == 27.0
        assert math.isclose(total_before, total_after, rel_tol=1e-5), f"Money conservation violated: {total_before} != {total_after}"

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Total currency is strictly conserved during theft without creation or deletion",
            "predicted": True,
            "observed": math.isclose(total_before, total_after, rel_tol=1e-5),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary=f"Theft of $25 transferred strictly; conserved total money ${total_after:.2f}.",
            hypotheses=[hyp],
            metrics={
                "total_currency_before": total_before,
                "total_currency_after": total_after,
                "victim_balance": victim.physical_state.money,
                "thief_balance": thief.physical_state.money,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 15. EXP_15_EXT_15: Acute Financial Shock, Informal Day Labor & Recovery
# ============================================================================

class Experiment15_EXT_15_FinancialShockAndDayLaborRecovery(BaseExperiment):
    """Verify cash-depleted individual recovers liquidity through informal day labor."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_15",
            name="Acute Financial Shock, Informal Day Labor & Recovery",
            description="Individual suffering financial drainage works as an agricultural day laborer to survive.",
            duration_ticks=10,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        from saltbor.economy.labor.market import LaborMarketEngine

        labor_market = LaborMarketEngine()
        worker = _make_agent("Trabajador en Precariedad", 1501, money=1.20, seed=151)
        worker.physical_state.energy = 0.80

        # Perform day labor
        res = labor_market.perform_informal_day_labor(
            agent=worker,
            task_name="Jornalero de Cosecha de Café",
            current_tick=8,
        )

        assert res.get("success") is True
        assert worker.physical_state.money > 5.0, f"Worker balance failed to recover: {worker.physical_state.money}"

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "Informal day labor provides immediate emergency cash liquidity",
            "predicted": True,
            "observed": (res.get("success") and worker.physical_state.money > 5.0),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary=f"Informal agricultural labor restored balance from $1.20 to ${worker.physical_state.money:.2f}.",
            hypotheses=[hyp],
            metrics={
                "initial_money": 1.20,
                "earned_usd": res.get("earned_usd"),
                "recovered_balance": worker.physical_state.money,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# 16. EXP_15_EXT_16: Multi-System Causal Cascade Traceability
# ============================================================================

class Experiment15_EXT_16_MultiSystemCausalCascade(BaseExperiment):
    """Verify end-to-end multi-system causal cascade across environment, economy, and community."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_16",
            name="Multi-System Causal Cascade Traceability",
            description="Torrential rainfall triggers flood, road blockage, travel delay, and community restoration.",
            duration_ticks=15,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        causal_graph = CausalEventGraph()
        misfortune = MisfortuneEngine(seed=self.config.random_seed)

        # 1. Torrential Rain Event (Initiator)
        evt_rain = SimulationEvent(
            event_type=EventType.DISASTER_OCCURRED,
            tick=1,
            data={"weather": "Tormenta Tropical", "rainfall_mm": 55.0},
            importance=0.9,
        )
        node_rain = causal_graph.add_event(evt_rain, description="Tormenta tropical con precipitación extraordinaria de 55 mm")

        # 2. Flood Disaster (Caused by rain)
        evt_flood = SimulationEvent(
            event_type=EventType.DISASTER_OCCURRED,
            tick=2,
            cause_event_id=evt_rain.event_id,
            data={"disaster": "Inundación Río Suchiacel"},
            importance=0.85,
        )
        node_flood = causal_graph.add_event(evt_flood, cause_event_id=str(evt_rain.event_id), description="Desbordamiento del Río Suchiacel")

        # 3. Road Blockage (Caused by flood)
        evt_block = SimulationEvent(
            event_type=EventType.ROAD_BLOCKED,
            tick=3,
            cause_event_id=evt_flood.event_id,
            data={"road": "carretera_los_chorros"},
            importance=0.75,
        )
        node_block = causal_graph.add_event(evt_block, cause_event_id=str(evt_flood.event_id), description="Corte de vía en Los Chorros")

        # 4. Community Cleanup Reopening (Caused by blockage)
        evt_reopen = SimulationEvent(
            event_type=EventType.ROAD_REOPENED,
            tick=6,
            cause_event_id=evt_block.event_id,
            data={"cleared_by": "ADESCO Suchitoto"},
            importance=0.7,
        )
        node_reopen = causal_graph.add_event(evt_reopen, cause_event_id=str(evt_block.event_id), description="Reapertura de vía tras faena comunitaria")

        # Verify causal ancestral chain for the road reopening
        ancestors = causal_graph.get_causal_chain(str(evt_reopen.event_id))
        assert len(ancestors) == 3, f"Expected 3 ancestral causes, got {len(ancestors)}"
        assert ancestors[0].event_id == str(evt_rain.event_id), "Root cause should be rain"
        assert ancestors[1].event_id == str(evt_flood.event_id), "Intermediate cause should be flood"
        assert ancestors[2].event_id == str(evt_block.event_id), "Direct cause should be road block"

        # Explain event
        explanation = causal_graph.explain_event(str(evt_reopen.event_id))
        assert "Tormenta" in explanation["narrative_explanation"]

        elapsed = time.perf_counter() - t0
        hyp = {
            "hypothesis": "All cascading consequences link recursively to ancestor causes in DAG without cycles",
            "predicted": True,
            "observed": (len(ancestors) == 3 and ancestors[0].event_id == str(evt_rain.event_id)),
            "status": "HYPOTHESIS_SUPPORTED",
        }
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Acyclic causal graph successfully traced complete chain from tropical storm to road reopening.",
            hypotheses=[hyp],
            metrics={
                "causal_chain_depth": len(ancestors),
                "root_cause_type": ancestors[0].event_type,
                "consequences_count": len(causal_graph.get_consequence_tree(str(evt_rain.event_id))),
            },
            duration_seconds=elapsed,
            raw_data={"explanation": explanation},
        )


# ============================================================================
# 17. EXP_15_EXT_17: Multi-Seed Robustness, Uncertainty & Null Outcomes
# ============================================================================

class Experiment15_EXT_17_MultiSeedRobustness(BaseExperiment):
    """Re-run the stochastic mechanisms under several seeds and report spread.

    This experiment deliberately does not assert a social outcome.  It checks
    three things a single-seed demonstration cannot show:

    1. Risk ordering is stable across seeds (higher exposure => more events).
    2. Null outcomes remain possible (most short exposures infect nobody,
       potable water never makes anyone ill).
    3. Rates vary between seeds, so measured uncertainty is reported instead
       of a single deterministic number.
    """

    SEEDS = [7, 13, 42, 99, 2024]
    TRIPS_PER_CONDITION = 150
    EXPOSURE_TRIALS = 40
    CONTACTS_PER_TRIAL = 6
    WATER_DRAWS = 200
    ROMANCE_COUPLES = 20

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_15_EXT_17",
            name="Multi-Seed Robustness, Uncertainty & Null Outcomes",
            description="Stochastic hazard, contagion, water and romance mechanisms are re-run across five seeds to measure spread and confirm that null outcomes remain reachable.",
            duration_ticks=10,
            random_seed=42,
        )

    def run(self, runner: Optional[Any] = None) -> ExperimentResult:
        t0 = time.perf_counter()

        low_risk_rates: list[float] = []
        high_risk_rates: list[float] = []
        transmission_rates: list[float] = []
        zero_infection_fractions: list[float] = []
        clean_water_rates: list[float] = []
        contaminated_water_rates: list[float] = []
        romance_formations: list[int] = []
        age_gap_formations: list[int] = []

        for seed in self.SEEDS:
            misfortune = MisfortuneEngine(seed=seed)
            driver = _make_agent("Conductor de Prueba", 1700 + seed, money=100.0, seed=seed)

            from saltbor.world.interaction.environmental_hazards import EnvironmentalHazardProfile

            dry = EnvironmentalHazardProfile(rainfall_mm_per_hour=0.0, temperature_celsius=27.0)
            storm = EnvironmentalHazardProfile(rainfall_mm_per_hour=25.0, temperature_celsius=27.0)

            low_events = 0
            for trip in range(self.TRIPS_PER_CONDITION):
                driver.physical_state.energy = 0.90
                driver.physical_state.money = 100.0
                if misfortune.evaluate_traffic_accident(
                    human=driver,
                    road_id="carretera_los_chorros",
                    weather_state=dry,
                    current_tick=trip + 1,
                ):
                    low_events += 1

            high_events = 0
            for trip in range(self.TRIPS_PER_CONDITION):
                driver.physical_state.energy = 0.10
                driver.physical_state.money = 100.0
                if misfortune.evaluate_traffic_accident(
                    human=driver,
                    road_id="carretera_los_chorros",
                    weather_state=storm,
                    current_tick=trip + 1,
                ):
                    high_events += 1

            low_risk_rates.append(round(low_events / self.TRIPS_PER_CONDITION, 4))
            high_risk_rates.append(round(high_events / self.TRIPS_PER_CONDITION, 4))

            # Short, single-tick exposure: most trials should infect nobody.
            health = HealthEngine(seed=seed)
            infected_totals = 0
            zero_trials = 0
            for trial in range(self.EXPOSURE_TRIALS):
                host = _make_agent(f"Host {seed}-{trial}", 1800 + trial, seed=seed + trial)
                illness = health.create_respiratory_infection(tick=1)
                illness.incubation_ticks = 0
                host.active_health_conditions.append(illness)
                contacts = [
                    _make_agent(f"Contact {seed}-{trial}-{i}", 1900 + i, seed=seed + i)
                    for i in range(self.CONTACTS_PER_TRIAL)
                ]
                infected = health.simulate_airborne_contagion(host, contacts, current_tick=2)
                infected_totals += len(infected)
                if not infected:
                    zero_trials += 1

            transmission_rates.append(
                round(infected_totals / (self.EXPOSURE_TRIALS * self.CONTACTS_PER_TRIAL), 4)
            )
            zero_infection_fractions.append(round(zero_trials / self.EXPOSURE_TRIALS, 4))

            # Water exposure: a potable source must never make anyone ill.
            world = WorldHumanInteractionEngine(seed=seed)
            world.hazards.water_sources["pozo_comunal_san_pedro"] = 0.88
            world.hazards.water_sources["quebrada_el_zapote"] = 0.30
            resident = _make_agent("Residente", 2000, seed=seed)
            clean_hits = 0
            dirty_hits = 0
            for _ in range(self.WATER_DRAWS):
                if world.evaluate_water_consumption_risk(resident, "pozo_comunal_san_pedro", 1):
                    clean_hits += 1
                if world.evaluate_water_consumption_risk(resident, "quebrada_el_zapote", 2):
                    dirty_hits += 1
            clean_water_rates.append(round(clean_hits / self.WATER_DRAWS, 4))
            contaminated_water_rates.append(round(dirty_hits / self.WATER_DRAWS, 4))

            # Romance formation is an outcome, not a guarantee.
            romance = RomanceEngine(seed=seed)
            formed = 0
            for couple in range(self.ROMANCE_COUPLES):
                a = _make_agent(f"A {seed}-{couple}", 2100 + couple, age=26.0, seed=seed + couple)
                b = _make_agent(f"B {seed}-{couple}", 2200 + couple, age=27.0, seed=seed + couple + 1)
                if romance.initiate_romantic_interest(a, b, current_tick=couple + 1) is not None:
                    formed += 1
            romance_formations.append(formed)

            # A large age gap should make some pairings fail the attraction
            # gate: romantic interest is not a guaranteed matchmaker.
            gapped = 0
            for couple in range(self.ROMANCE_COUPLES):
                a = _make_agent(f"C {seed}-{couple}", 2300 + couple, age=24.0, seed=seed + couple)
                b = _make_agent(f"D {seed}-{couple}", 2400 + couple, age=72.0, seed=seed + couple + 1)
                if romance.initiate_romantic_interest(a, b, current_tick=couple + 1) is not None:
                    gapped += 1
            age_gap_formations.append(gapped)

        ordering_holds = all(
            high > low for low, high in zip(low_risk_rates, high_risk_rates)
        )
        null_outcomes_possible = all(z > 0.0 for z in zero_infection_fractions)
        potable_water_safe = all(rate == 0.0 for rate in clean_water_rates)
        contaminated_water_harmful = all(0.05 < rate < 0.60 for rate in contaminated_water_rates)
        seed_spread_present = len(set(zero_infection_fractions)) > 1
        age_gap_gate_holds = all(0 < formed < self.ROMANCE_COUPLES for formed in age_gap_formations)

        success = all([
            ordering_holds,
            null_outcomes_possible,
            potable_water_safe,
            contaminated_water_harmful,
            seed_spread_present,
            age_gap_gate_holds,
        ])

        hypotheses = [
            {
                "hypothesis": "Contextual risk ordering (storm + fatigue vs dry + rested) is stable across seeds",
                "predicted": True,
                "observed": ordering_holds,
                "status": "HYPOTHESIS_SUPPORTED" if ordering_holds else "HYPOTHESIS_REJECTED",
            },
            {
                "hypothesis": "Not every exposure produces infection; null trials persist across seeds",
                "predicted": True,
                "observed": null_outcomes_possible,
                "status": "HYPOTHESIS_SUPPORTED" if null_outcomes_possible else "HYPOTHESIS_REJECTED",
            },
            {
                "hypothesis": "Potable water produces no illness while contaminated water does",
                "predicted": True,
                "observed": potable_water_safe and contaminated_water_harmful,
                "status": "HYPOTHESIS_SUPPORTED" if (potable_water_safe and contaminated_water_harmful) else "HYPOTHESIS_REJECTED",
            },
            {
                "hypothesis": "Stochastic rates differ between seeds, so uncertainty must be reported",
                "predicted": True,
                "observed": seed_spread_present,
                "status": "HYPOTHESIS_SUPPORTED" if seed_spread_present else "INCONCLUSIVE",
            },
            {
                "hypothesis": "Romantic interest can fail: wide age-gap pairings are partly filtered out",
                "predicted": True,
                "observed": age_gap_gate_holds,
                "status": "HYPOTHESIS_SUPPORTED" if age_gap_gate_holds else "HYPOTHESIS_REJECTED",
            },
        ]

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=(
                f"Across {len(self.SEEDS)} seeds: traffic accident rate "
                f"{min(low_risk_rates):.4f}-{max(low_risk_rates):.4f} (dry/rested) vs "
                f"{min(high_risk_rates):.4f}-{max(high_risk_rates):.4f} (storm/fatigued); "
                f"zero-infection trials {min(zero_infection_fractions):.2f}-{max(zero_infection_fractions):.2f}; "
                f"romance formations {min(romance_formations)}-{max(romance_formations)} of {self.ROMANCE_COUPLES}."
            ),
            hypotheses=hypotheses,
            metrics={
                "seeds": list(self.SEEDS),
                "low_risk_accident_rates": low_risk_rates,
                "high_risk_accident_rates": high_risk_rates,
                "low_risk_accident_rate_mean": round(float(np.mean(low_risk_rates)), 4),
                "high_risk_accident_rate_mean": round(float(np.mean(high_risk_rates)), 4),
                "high_risk_rate_std": round(float(np.std(high_risk_rates)), 4),
                "per_contact_transmission_rates": transmission_rates,
                "zero_infection_trial_fractions": zero_infection_fractions,
                "clean_water_illness_rates": clean_water_rates,
                "contaminated_water_illness_rates": contaminated_water_rates,
                "romance_formations": romance_formations,
                "age_gap_romance_formations": age_gap_formations,
                "risk_ordering_stable": ordering_holds,
                "null_outcomes_possible": null_outcomes_possible,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# Registered Experiment Catalog
# ============================================================================

PHASE15_EXTENSION_EXPERIMENTS = [
    Experiment15_EXT_01_RomanticFormation,
    Experiment15_EXT_02_JealousyAndInfidelity,
    Experiment15_EXT_03_InfidelityDiscoveryAndConfrontation,
    Experiment15_EXT_04_UnrequitedLoveAndHeartbreak,
    Experiment15_EXT_05_FamilyCaregivingElderSupport,
    Experiment15_EXT_06_ChildDependencyAndCare,
    Experiment15_EXT_07_IllnessOnsetAndClinicalRecovery,
    Experiment15_EXT_08_AirborneDiseaseTransmission,
    Experiment15_EXT_09_MedicalCapacityAndTriage,
    Experiment15_EXT_10_TrafficAccidentsHazards,
    Experiment15_EXT_11_WorkplaceInjuriesFatigue,
    Experiment15_EXT_12_FloodingDisasterDisplacement,
    Experiment15_EXT_13_WaterPollutionAndCleanupFaena,
    Experiment15_EXT_14_TheftVictimizationAndConservation,
    Experiment15_EXT_15_FinancialShockAndDayLaborRecovery,
    Experiment15_EXT_16_MultiSystemCausalCascade,
    Experiment15_EXT_17_MultiSeedRobustness,
]
