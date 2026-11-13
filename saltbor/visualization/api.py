"""FastAPI REST & SSE Router for the Saltbor Visual Simulation Platform.

Exposes comprehensive endpoints for World Explorer, Individual Explorer,
Cognitive Architecture, Knowledge Graph, Social Network, Civilization Dashboard,
Economy, Historical Timeline, Simulation Laboratory, and Live SSE Telemetry.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Optional
import uuid
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from saltbor.core.types import ActivityType, ContractType, EmploymentStatus, HousingTenureType
from saltbor.events.types import EventType, SimulationEvent
from saltbor.knowledge.graph.node import ValidationStatus
from saltbor.population.human import SyntheticHuman
from saltbor.simulation.analysis.individual_observability import IndividualObservability
from saltbor.simulation.analysis.phase05_observability import Phase05Observability
from saltbor.datasets.gis.pipeline import IngestedGeography
from saltbor.visualization.controller import SimulationController
from saltbor.world.geographic.models import ValidationState
from saltbor.world.geographic.osm_router import OSMRoadNetwork

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# -----------------------------------------------------------------------------
# Dependency injection helper for controller
# -----------------------------------------------------------------------------
_controller_instance: Optional[SimulationController] = None


def set_controller(controller: SimulationController) -> None:
    global _controller_instance
    _controller_instance = controller


def get_controller() -> SimulationController:
    if _controller_instance is None:
        raise HTTPException(status_code=500, detail="SimulationController not initialized.")
    return _controller_instance


# -----------------------------------------------------------------------------
# Control & Telemetry Endpoints
# -----------------------------------------------------------------------------

@router.get("/status")
def get_status() -> dict[str, Any]:
    """Return high-level real-time simulation engine status and telemetry."""
    ctrl = get_controller()
    return ctrl.get_status_summary()


@router.post("/control/play")
def control_play() -> dict[str, Any]:
    """Resume continuous simulation execution."""
    ctrl = get_controller()
    ctrl.play()
    return {"status": "ok", "is_running": True}


@router.post("/control/pause")
def control_pause() -> dict[str, Any]:
    """Pause continuous simulation execution."""
    ctrl = get_controller()
    ctrl.pause()
    return {"status": "ok", "is_running": False}


@router.post("/control/step")
def control_step(count: int = Query(default=1, ge=1, le=100)) -> dict[str, Any]:
    """Advance the simulation by exact number of ticks while paused."""
    ctrl = get_controller()
    was_running = ctrl.is_running()
    ctrl.pause()
    current_tick = ctrl.step_sync(count)
    if was_running:
        ctrl.play()
    return {"status": "ok", "tick": current_tick}


@router.post("/control/speed")
def control_speed(multiplier: int = Query(default=1, ge=1, le=1000)) -> dict[str, Any]:
    """Set simulation speed preset (1, 10, 100, 1000)."""
    ctrl = get_controller()
    applied = ctrl.set_speed(multiplier)
    return {"status": "ok", "speed": applied}


@router.post("/control/reset")
def control_reset(
    seed: Optional[int] = Query(default=42),
    population: int = Query(default=20, ge=5, le=10000),
    scenario: str = Query(default="baseline"),
) -> dict[str, Any]:
    """Reset simulation state with fresh seed and population."""
    ctrl = get_controller()
    ctrl.reset_simulation(seed=seed, initial_pop=population, scenario=scenario)
    return {"status": "reset", "seed": seed, "population": population, "scenario": scenario}


@router.post("/control/population")
def control_set_population(
    count: int = Query(default=20, ge=5, le=10000),
    reset: bool = Query(default=False),
) -> dict[str, Any]:
    """Dynamically scale or reset simulation population to specified count."""
    ctrl = get_controller()
    actual_pop = ctrl.scale_active_population(target_count=count, reset=reset)
    return {
        "status": "ok",
        "population": actual_pop,
        "mode": "reset" if reset else "dynamic",
    }


@router.post("/control/scenario")
def control_scenario(name: str = Query(default="baseline")) -> dict[str, Any]:
    """Apply an environmental and economic scenario."""
    ctrl = get_controller()
    ok = ctrl.apply_scenario(name)
    return {"status": "ok" if ok else "error", "scenario": name}


@router.post("/control/checkpoint/save")
def control_checkpoint_save() -> dict[str, Any]:
    """Trigger an immediate SQLite persistence checkpoint."""
    ctrl = get_controller()
    return ctrl.save_checkpoint()


@router.post("/control/checkpoint/load")
def control_checkpoint_load() -> dict[str, Any]:
    """Restore simulation state from SQLite database."""
    ctrl = get_controller()
    return ctrl.load_checkpoint()


# -----------------------------------------------------------------------------
# 1. World Explorer
# -----------------------------------------------------------------------------

@router.get("/world")
def get_world_data() -> dict[str, Any]:
    """Return geographic datasets, physical features, establishments, settlements, and agent positions."""
    ctrl = get_controller()
    geo = ctrl.geo_engine
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    # 1. Departments (14)
    departments = [
        {
            "code": d.code,
            "name": d.name,
            "zone": d.zone.value if hasattr(d.zone, "value") else str(d.zone),
            "cabecera": getattr(d, "cabecera", getattr(d, "capital_city", d.name)),
            "approx_population": getattr(d, "population_2024", getattr(d, "approx_population", 500000)),
            "area_km2": d.area_km2,
            "primary_economic_activity": getattr(d, "primary_economic_activity", "Comercio y Agricultura"),
        }
        for d in geo.get_all_departments()
    ]

    # 2. Municipalities (44)
    municipalities = [
        {
            "id": m.municipality_id,
            "name": m.name,
            "department_code": m.department_code,
            "cabecera": m.cabecera_municipal,
            "population": m.approx_population,
            "area_km2": m.area_km2,
            "lat": m.centroid_lat,
            "lon": m.centroid_lon,
        }
        for m in geo._municipalities.values()
    ]

    # 3. Districts (262)
    districts = [
        {
            "id": dist.district_id,
            "name": dist.name,
            "municipality_id": dist.municipality_id,
            "department_code": dist.department_code,
            "lat": dist.latitude,
            "lon": dist.longitude,
            "elevation_m": dist.elevation_m,
            "population": dist.approx_population,
            "is_urban_core": dist.is_urban_core,
            "source": dist.source,
        }
        for dist in geo.get_all_districts()
    ]

    # 4. Roads & Bridges
    roads = []
    for seg in geo.navigation._segments.values():
        orig = geo.get_district(seg.from_district_id)
        dest = geo.get_district(seg.to_district_id)
        if orig and dest:
            roads.append({
                "segment_id": seg.segment_id,
                "name": seg.name,
                "road_type": seg.road_type,
                "distance_km": seg.distance_km,
                "is_bridge": seg.is_bridge,
                "from_district": orig.name,
                "to_district": dest.name,
                "from_lat": orig.latitude,
                "from_lon": orig.longitude,
                "to_lat": dest.latitude,
                "to_lon": dest.longitude,
            })

    # 5. Volcanoes and Lakes
    volcanoes = [
        {
            "id": f.feature_id,
            "name": f.name,
            "elevation_m": f.elevation_m,
            "lat": f.latitude,
            "lon": f.longitude,
            "type": "volcano",
        }
        for f in geo.get_volcanoes()
    ]
    lakes = [
        {
            "id": f.feature_id,
            "name": f.name,
            "elevation_m": f.elevation_m,
            "lat": f.latitude,
            "lon": f.longitude,
            "type": "lake",
        }
        for f in geo.get_lakes()
    ]

    # 6. Real Verified Establishments
    establishments = [
        {
            "place_id": p.place_id,
            "name": p.name,
            "category": p.category.value if hasattr(p.category, "value") else str(p.category),
            "sub_category": p.sub_category,
            "validation_state": p.validation_state.value if hasattr(p.validation_state, "value") else str(p.validation_state),
            "department_code": p.department_code,
            "district_id": p.district_id,
            "lat": p.point.latitude,
            "lon": p.point.longitude,
            "elevation_m": p.point.elevation_m,
            "address": p.address,
            "is_confirmed": p.validation_state == ValidationState.CONFIRMADO,
            "source_provenance": p.source_name or "CNR_IGN",
        }
        for p in geo.establishments.get_all(confirmed_only=False)
    ]

    # 7. Settlement Locations & Agents
    # Coordinates of Saltbor center in El Salvador: Santa Tecla / San Salvador area (lat 13.67, lon -89.28)
    base_lat = 13.6738
    base_lon = -89.2797

    # Calculate agent coordinates
    agents_world = []
    location_counts: dict[str, int] = {}
    for h in runner.population.get_all():
        loc_id = h.physical_state.current_location_id or "plaza_central"
        location_counts[loc_id] = location_counts.get(loc_id, 0) + 1
        idx = location_counts[loc_id]

        loc = runner.locations.get_optional(loc_id)
        pos_x = loc.position[0] if loc else 250.0
        pos_y = loc.position[1] if loc else 250.0

        # Displace agent locally on the world map (~500m area around base coordinates)
        # 1 deg lat ~ 111 km -> 100m ~ 0.0009 deg
        agent_lat = base_lat + (pos_y - 250.0) * 0.000015 + (idx * 0.0001)
        agent_lon = base_lon + (pos_x - 250.0) * 0.000015 + (idx * 0.0001)

        agents_world.append({
            "uid": str(h.uid),
            "serial": h.identity.serial,
            "full_name": h.identity.full_name,
            "gender": h.demographics.gender.value if hasattr(h.demographics.gender, "value") else str(h.demographics.gender),
            "age": h.demographics.age,
            "occupation": h.demographics.occupation,
            "current_location_id": loc_id,
            "current_location_name": loc.name if loc else loc_id,
            "current_activity": h.physical_state.current_activity.value if h.physical_state.current_activity else "idle",
            "activity_ticks_remaining": h.physical_state.activity_ticks_remaining,
            "energy": round(h.physical_state.energy, 2),
            "hunger": round(h.physical_state.hunger, 2),
            "money": round(h.physical_state.money, 2),
            "mood": round(h.emotions.get_mood(), 2),
            "lat": round(agent_lat, 6),
            "lon": round(agent_lon, 6),
            "local_x": round(pos_x, 1),
            "local_y": round(pos_y, 1),
        })

    # 8. Local Settlement Buildings / Locations
    settlement_places = [
        {
            "location_id": loc.location_id,
            "name": loc.name,
            "type": loc.location_type.value if hasattr(loc.location_type, "value") else str(loc.location_type),
            "position": loc.position,
            "capacity": loc.capacity,
            "description": loc.description,
            "is_outdoor": loc.is_outdoor,
            "occupant_count": location_counts.get(loc.location_id, 0),
        }
        for loc in runner.locations.get_all()
    ]

    # 9. Environmental conditions
    env = runner.environment
    env_state = getattr(env, "state", None)
    environment_snapshot = {
        "season": getattr(env_state.season, "value", str(env_state.season)) if env_state and hasattr(env_state, "season") else "epoca_seca",
        "weather_condition": getattr(env_state.condition, "value", str(env_state.condition)) if env_state and hasattr(env_state, "condition") else "clear",
        "temperature_celsius": getattr(env_state, "temperature_celsius", 24.5) if env_state else 24.5,
        "rainfall_mm_per_hour": getattr(env_state, "rainfall_mm_per_hour", 0.0) if env_state else 0.0,
        "soil_moisture": round(getattr(env_state, "soil_moisture", 0.5), 3) if env_state else 0.5,
        "crop_yield_multiplier": round(getattr(env_state, "crop_growth_multiplier", 1.0), 2) if env_state else 1.0,
        "hazard_warning": getattr(env_state, "hazard_warning", None) if env_state else None,
    }

    return {
        "projection": {
            "min_lat": 13.10,
            "max_lat": 14.48,
            "min_lon": -90.15,
            "max_lon": -87.65,
        },
        "departments": departments,
        "municipalities": municipalities,
        "districts": districts,
        "roads": roads,
        "volcanoes": volcanoes,
        "lakes": lakes,
        "establishments": establishments,
        "agents": agents_world,
        "settlement_places": settlement_places,
        "environment": environment_snapshot,
    }


# -----------------------------------------------------------------------------
# 2. Individual Explorer
# -----------------------------------------------------------------------------

@router.get("/individuals")
def list_individuals() -> list[dict[str, Any]]:
    """Return summary roster of all synthetic humans in population."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        return []

    roster = []
    for h in runner.population.get_all():
        ident = h.identity
        demo = h.demographics
        phys = h.physical_state
        emot = h.emotions
        roster.append({
            "uid": str(ident.uid),
            "serial": ident.serial,
            "full_name": ident.full_name,
            "age": demo.age,
            "gender": demo.gender.value if hasattr(demo.gender, "value") else str(demo.gender),
            "occupation": demo.occupation,
            "education": demo.education_level,
            "current_location_id": phys.current_location_id or "idle",
            "current_activity": phys.current_activity.value if phys.current_activity else "idle",
            "energy": round(phys.energy, 2),
            "hunger": round(phys.hunger, 2),
            "health": round(phys.health, 2),
            "money": round(phys.money, 2),
            "mood": round(emot.get_mood(), 2),
            "active_goals_count": len(h.autonomy.get_active_goals()),
            "skills_count": len(h.memory.procedural.get_all_skills()),
            "housing_tenure": (
                h.housing_tenure.value
                if hasattr(h, "housing_tenure") and hasattr(h.housing_tenure, "value")
                else str(getattr(h, "housing_tenure", "owner_occupied"))
            ),
            "employment_status": (
                h.employment_status.value
                if hasattr(h, "employment_status") and hasattr(h.employment_status, "value")
                else str(getattr(h, "employment_status", "unemployed"))
            ),
        })
    return roster


@router.get("/individuals/{uid}")
def get_individual_detail(uid: str) -> dict[str, Any]:
    """Return the complete deep dossier of a synthetic individual."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    # Match by UID string or serial
    human: Optional[SyntheticHuman] = None
    for h in runner.population.get_all():
        if str(h.uid) == uid or str(h.identity.serial) == uid:
            human = h
            break

    if human is None:
        raise HTTPException(status_code=404, detail=f"Individual '{uid}' not found.")

    # Generate structured base dossier
    dossier = IndividualObservability.get_structured_dossier(human, runner.social)

    # 1. Personality Traits with base, current, and drift
    traits_detailed = {}
    for t_name in [
        "openness", "conscientiousness", "extraversion", "agreeableness",
        "neuroticism", "risk_tolerance", "patience", "persistence"
    ]:
        tv = human.personality.traits.get_trait(t_name)
        traits_detailed[t_name] = {
            "base": round(tv.base_value, 3),
            "current": round(tv.current_value, 3),
            "drift": round(tv.current_value - tv.base_value, 3),
        }

    # 2. Emotional States
    emot_profile = getattr(human.emotions, "profile", None)
    active_emotions = []
    if emot_profile and hasattr(emot_profile, "active_emotions"):
        for e_type, state in emot_profile.active_emotions.items():
            if state.intensity > 0.02:
                active_emotions.append({
                    "emotion": e_type.value if hasattr(e_type, "value") else str(e_type),
                    "intensity": round(state.intensity, 3),
                    "duration_ticks": getattr(state, "duration_remaining", getattr(state, "duration_ticks", 0)),
                })

    # 3. Active Goals with HTN/GOAP Plan Steps
    goals_expanded = []
    for g in human.autonomy.get_active_goals():
        goals_expanded.append({
            "id": str(g.goal_id),
            "category": g.category,
            "description": g.description,
            "priority": round(g.priority, 2),
            "progress": round(g.progress, 2),
            "status": g.status,
            "plan_steps": g.plan_steps,
            "current_step_index": g.current_step_index,
            "current_step": g.plan_steps[g.current_step_index] if g.plan_steps and g.current_step_index < len(g.plan_steps) else None,
        })

    # 4. Individual Knowledge Graph items
    kg_items = []
    misconceptions = []
    if hasattr(human, "knowledge_graph") and human.knowledge_graph is not None:
        for node in human.knowledge_graph.all_known_nodes():
            claim = human.knowledge_graph.get_claim(node.node_id)
            if claim:
                item = {
                    "node_id": node.node_id,
                    "label": node.label,
                    "category": node.category,
                    "confidence": round(claim.confidence, 3),
                    "source": claim.source_pathway,
                    "verification_count": claim.verification_count,
                    "is_misconception": claim.is_misconception,
                }
                kg_items.append(item)
                if claim.is_misconception:
                    misconceptions.append(node.node_id)

    # 5. Cognitive Profile (14 capabilities)
    cog_profile = {}
    if hasattr(human, "cognitive_profile") and human.cognitive_profile is not None:
        cp = human.cognitive_profile
        for cap, metric in cp.capabilities.items():
            cap_name = cap.value if hasattr(cap, "value") else str(cap)
            lvl = getattr(metric, "current_level", float(metric) if isinstance(metric, (int, float)) else 0.5)
            cog_profile[cap_name] = round(float(lvl), 3)

        cog_meta = {
            "budget_used": round(cp.total_allocated_budget(), 2) if hasattr(cp, "total_allocated_budget") else 7.0,
            "budget_max": round(getattr(cp, "cognitive_budget_capacity", 8.40), 2),
            "fatigue": round(getattr(cp, "fatigue_level", getattr(cp, "chronic_stress", 0.0)), 3),
            "deprivation_penalty": round(getattr(cp, "deprivation_penalty", 0.0), 3),
            "capabilities": cog_profile,
        }
    else:
        cog_meta = {"capabilities": {}}

    # 6. Meta-Learning Strategies
    meta_learning = {}
    if hasattr(human, "meta_learning") and human.meta_learning is not None:
        ml = human.meta_learning
        meta_dict = ml.to_dict() if hasattr(ml, "to_dict") else {}
        pref_strat = getattr(ml, "current_preferred_strategy", meta_dict.get("preferred_strategy", "observation"))
        meta_learning = {
            "preferred_strategy": pref_strat.value if hasattr(pref_strat, "value") else str(pref_strat),
            "strategies_performance": {
                st.value if hasattr(st, "value") else str(st): round(perf.average_yield, 3) if hasattr(perf, "average_yield") else 0.5
                for st, perf in getattr(ml, "strategy_records", {}).items()
            },
            "plateau_count": getattr(ml, "plateau_count", getattr(ml, "plateau_threshold_attempts", 0)),
        }

    # 7. Scientific Thinking & Hypotheses
    scientific_thinking = {
        "cycle_stages": [
            "OBSERVATION", "QUESTION", "HYPOTHESIS", "EXPERIMENTATION",
            "RESULT", "EVALUATION", "BELIEF_REVISION", "TRANSMISSION"
        ],
        "hypotheses_held": [nid for nid in human.knowledge_graph.all_known_node_ids() if "hyp_" in nid] if hasattr(human, "knowledge_graph") and human.knowledge_graph else [],
    }

    # Combine into comprehensive response
    dossier["personality"]["traits_detailed"] = traits_detailed
    dossier["emotions"]["active_emotions"] = active_emotions
    dossier["active_goals"] = goals_expanded
    dossier["knowledge_items"] = kg_items
    dossier["misconceptions"] = misconceptions
    dossier["cognitive_profile"] = cog_meta
    dossier["meta_learning"] = meta_learning
    dossier["scientific_thinking"] = scientific_thinking
    dossier["socioeconomic"] = {
        "housing_tenure": (
            human.housing_tenure.value
            if hasattr(human, "housing_tenure") and hasattr(human.housing_tenure, "value")
            else str(getattr(human, "housing_tenure", "owner_occupied"))
        ),
        "employment_status": (
            human.employment_status.value
            if hasattr(human, "employment_status") and hasattr(human.employment_status, "value")
            else str(getattr(human, "employment_status", "unemployed"))
        ),
        "reservation_wage": round(getattr(human, "reservation_wage", 8.0), 2),
        "preferences": getattr(human, "preferences", {}),
    }

    # 8. Integrated health trajectory (Phase 1.5 Extension)
    active_conditions = []
    for condition in getattr(human, "active_health_conditions", []):
        if hasattr(condition, "to_dict"):
            active_conditions.append(condition.to_dict())
        else:
            active_conditions.append({
                "name": getattr(condition, "name", "Condición"),
                "severity": getattr(condition, "severity", 0.0),
                "is_treated": getattr(condition, "is_treated", False),
            })
    dossier["health"] = {
        "vitals": {
            "health": round(float(getattr(human.physical_state, "health", 0.0)), 3),
            "energy": round(float(getattr(human.physical_state, "energy", 0.0)), 3),
            "hunger": round(float(getattr(human.physical_state, "hunger", 0.0)), 3),
        },
        "active_conditions": active_conditions,
        "active_condition_count": len(active_conditions),
        "health_history": list(getattr(human, "health_history", [])[-20:]),
    }

    # 9. Romantic trajectory and heartbreak state
    romance_engine = getattr(runner, "romance_engine", None)
    relationship = romance_engine.get_agent_relationship(str(human.uid)) if romance_engine else None
    partner_uid = relationship.get_other_uid(str(human.uid)) if relationship else getattr(human, "romantic_partner_id", None)
    partner = None
    if partner_uid:
        try:
            partner = runner.population.get_optional(uuid.UUID(str(partner_uid)))
        except (ValueError, TypeError):
            partner = runner.population.get_optional(partner_uid)
    heartbreak = getattr(human, "heartbreak_state", None)
    dossier["romance"] = {
        "partner_id": str(partner_uid) if partner_uid else None,
        "partner_name": partner.name if partner is not None else None,
        "relationship": relationship.to_dict() if relationship is not None else None,
        "heartbreak": heartbreak.to_dict() if hasattr(heartbreak, "to_dict") else None,
    }

    # 10. Family, kinship, dependency and household context
    extension = getattr(runner, "extension", None)
    life = getattr(extension, "life_events", None) if extension is not None else None
    household = life.households.get_for_human(human.uid) if life is not None else None

    def _resolve_name(uid_value: Any) -> str:
        try:
            member = runner.population.get_optional(uuid.UUID(str(uid_value)))
        except (ValueError, TypeError):
            member = runner.population.get_optional(uid_value)
        return member.name if member is not None else "Fallecido / fuera del registro"

    children = []
    parents = []
    if life is not None:
        children = [str(c) for c in life.genealogy.get_children(human.uid)]
        parents = [str(p) for p in life.genealogy.get_parents(human.uid)]
    pregnancy = life.pregnancies.get(str(human.uid)) if life is not None else None

    dossier["family"] = {
        "household_id": household.household_id if household else None,
        "household_name": household.name if household else None,
        "residence_location_id": household.residence_location_id if household else None,
        "household_member_count": len(household.members) if household else 0,
        "children_ids": children,
        "children_names": [_resolve_name(c) for c in children],
        "parent_ids": parents,
        "parent_names": [_resolve_name(p) for p in parents],
        "dependent_children_ids": list(getattr(human, "dependent_children_ids", [])),
        "caregiver_ids": list(getattr(human, "caregiver_ids", [])),
        "elderly_dependent_ids": list(getattr(human, "elderly_dependents_ids", [])),
        "active_pregnancy": {
            "start_tick": pregnancy.start_tick,
            "gestation_duration_ticks": pregnancy.gestation_duration_ticks,
            "father_uid": str(pregnancy.father_uid) if pregnancy.father_uid else None,
        } if pregnancy is not None else None,
    }

    # 11. Perception (Phase 1.6): what this individual actually noticed.
    #     This is subjective state, not world truth; the panel must never be
    #     rendered from anything else.
    perception_engine = getattr(runner, "perception", None)
    if perception_engine is not None:
        snapshot = perception_engine.get_snapshot(str(human.uid))
        dossier["perception"] = snapshot.summary()
        dossier["perception"]["has_perception_data"] = snapshot.total_observations > 0
    else:
        dossier["perception"] = {"has_perception_data": False}

    return dossier


# -----------------------------------------------------------------------------
# 3. Cognitive Architecture Explorer
# -----------------------------------------------------------------------------

@router.get("/cognitive/{uid}")
def get_cognitive_subsystems(uid: str) -> dict[str, Any]:
    """Return functional subsystem details and decision trace pipeline for an individual."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    human: Optional[SyntheticHuman] = None
    for h in runner.population.get_all():
        if str(h.uid) == uid or str(h.identity.serial) == uid:
            human = h
            break

    if human is None:
        raise HTTPException(status_code=404, detail=f"Individual '{uid}' not found.")

    brain = getattr(human, "brain", None)
    trace = human.decision.get_last_trace()
    goals = human.autonomy.get_active_goals()
    primary_goal = goals[0] if goals else None
    mem_stats = human.memory.get_memory_stats()
    cp = getattr(human, "cognitive_profile", None)

    # 1. Frontal / Executive Subsystem
    frontal = {
        "name": "Frontal / Executive Subsystem",
        "analogy": "Executive Function & Planning",
        "is_biological": False,
        "status": "OPERATIONAL",
        "responsibilities": [
            "Goal generation from unmet physiological and psychological needs",
            "Hierarchical Task Network (HTN) and GOAP plan decomposition",
            "Impulse regulation, attention filtering, and deliberate replanning",
        ],
        "inputs": ["Physical needs vector", "Limbic affective valence", "Hippocampal episodic recall"],
        "outputs": ["Prioritized active goals", "Deliberated candidate actions", "Execution commitment"],
        "connected_subsystems": ["Hippocampal", "Limbic", "Temporal", "Parietal", "Cerebellar"],
        "state_variables": {
            "active_goals_count": len(goals),
            "primary_goal": primary_goal.description if primary_goal else "Quiescence / Maintenance",
            "primary_priority": round(primary_goal.priority, 2) if primary_goal else 0.40,
            "planning_depth": round(float(getattr(cp.capabilities.get("planning_depth", None), "current_level", 0.5)), 3) if cp and "planning_depth" in cp.capabilities else 0.5,
            "mental_fatigue": round(getattr(cp, "fatigue_level", 0.0), 3) if cp else 0.0,
        },
        "recent_operations": [
            f"Goal '{g.description[:40]}' evaluated (progress: {int(g.progress*100)}%)"
            for g in goals[:3]
        ],
        "decision_influence": "Dominates high-level goal alignment and action utility ranking.",
    }

    # 2. Hippocampal / Memory Subsystem
    recent_episodic = human.memory.episodic.get_recent(3)
    hippocampal = {
        "name": "Hippocampal / Memory Subsystem",
        "analogy": "Episodic Recall & Knowledge Consolidation",
        "is_biological": False,
        "status": "OPERATIONAL",
        "responsibilities": [
            "Episodic memory encoding with emotional valence and charge vectors",
            "Working memory buffer management (Miller's 7 ± 2 rule)",
            "Salient past outcome retrieval for contextual decision evaluation",
            "Ebbinghaus logarithmic memory decay and consolidation into long-term store",
        ],
        "inputs": ["SimulationEvent stream", "Limbic emotional charge", "Working memory items"],
        "outputs": ["Retrieved relevant memories", "Contextual outcome comparisons"],
        "connected_subsystems": ["Frontal", "Limbic", "Temporal"],
        "state_variables": {
            "working_memory_used": mem_stats["working_items"],
            "episodic_records_stored": mem_stats["episodic_records"],
            "total_memory_bytes": mem_stats["approx_bytes"],
            "quota_usage_pct": mem_stats["usage_pct"],
            "retention_shield": round(float(getattr(cp.capabilities.get("episodic_semantic_retention", None), "current_level", 0.5)), 3) if cp and "episodic_semantic_retention" in cp.capabilities else 0.5,
        },
        "recent_operations": [
            f"T{m.tick}: {m.summary[:45]} (importance: {m.importance:.2f}, valence: {m.emotional_valence:+.2f})"
            for m in recent_episodic
        ],
        "decision_influence": "Supplies empirical priors and historical positive/negative outcome weights.",
    }

    # 3. Limbic / Emotional Subsystem
    mood = human.emotions.get_mood()
    fear = human.emotions.get_emotion("fear") if hasattr(human.emotions, "get_emotion") else 0.0
    curiosity = human.emotions.get_emotion("curiosity") if hasattr(human.emotions, "get_emotion") else 0.0
    risk_discount = max(0.2, 1.0 - (fear * 0.5))
    limbic = {
        "name": "Limbic / Affective Subsystem",
        "analogy": "Emotional Modulation & Risk Appraisal",
        "is_biological": False,
        "status": "OPERATIONAL",
        "responsibilities": [
            "Multidimensional emotional appraisal across basic emotions (Joy, Fear, Anger, Sadness, Curiosity)",
            "Integrated affective mood state calculation (-1.0 to +1.0)",
            "Risk discounting under perceived threat or elevated fear",
            "Curiosity-driven exploration bonus for novel discoveries",
        ],
        "inputs": ["Salient events", "Physiological hunger/energy", "Social interactions"],
        "outputs": ["Mood valence (+/-)", "Risk tolerance modulation", "Emotional charges"],
        "connected_subsystems": ["Frontal", "Hippocampal", "Cerebellar"],
        "state_variables": {
            "mood_valence": round(mood, 3),
            "fear_intensity": round(fear, 3),
            "curiosity_intensity": round(curiosity, 3),
            "risk_discount_factor": round(risk_discount, 3),
            "regulation_capacity": round(getattr(human.emotions, "regulation_capacity", 0.5), 2),
        },
        "recent_operations": [
            f"Emotion update applied: mood {mood:+.2f}, risk discount {risk_discount:.2f}",
        ],
        "decision_influence": "Scales action utility by mood and suppresses risk-taking when fear is high.",
    }

    # 4. Temporal / Semantic Subsystem
    kg = getattr(human, "knowledge_graph", None)
    known_nodes_count = len(kg.all_known_nodes()) if kg else 0
    temporal = {
        "name": "Temporal / Semantic Subsystem",
        "analogy": "Semantic Ontology & Knowledge Graph",
        "is_biological": False,
        "status": "OPERATIONAL",
        "responsibilities": [
            "Semantic concept representation and domain knowledge claims",
            "Epistemic confidence estimation and verification tracking",
            "Misconception identification and contradiction resolution",
            "Language and cultural vocabulary processing",
        ],
        "inputs": ["Social learning communications", "Observation of craft practices", "Formal instruction"],
        "outputs": ["Epistemic certainty factor", "Verified knowledge claims", "Procedural recipes"],
        "connected_subsystems": ["Frontal", "Hippocampal"],
        "state_variables": {
            "known_concepts_count": known_nodes_count,
            "mean_confidence": round(kg.mean_confidence(), 3) if kg and hasattr(kg, "mean_confidence") else 0.75,
            "misconceptions_count": len([n for n in kg.all_known_nodes() if kg.get_claim(n.node_id) and kg.get_claim(n.node_id).is_misconception]) if kg else 0,
        },
        "recent_operations": [
            f"Evaluated semantic confidence for current domain."
        ],
        "decision_influence": "Provides epistemic confidence bonus (up to +0.10) for well-understood actions.",
    }

    # 5. Parietal / Spatial Subsystem
    curr_loc = human.physical_state.current_location_id
    parietal = {
        "name": "Parietal / Spatial Subsystem",
        "analogy": "Spatial Reasoning & Territorial Navigation",
        "is_biological": False,
        "status": "OPERATIONAL",
        "responsibilities": [
            "Spatial positioning and distance calculation across settlement and road network",
            "Topological pathfinding and obstacle / bridge transit penalty computation",
            "Travel duration estimation and energy expenditure forecasting",
        ],
        "inputs": ["Current location ID", "Target destination location", "Territorial road graph"],
        "outputs": ["Spatial travel cost penalty", "Feasible waypoint path"],
        "connected_subsystems": ["Frontal", "Cerebellar"],
        "state_variables": {
            "current_location": curr_loc,
            "home_location": human.physical_state.home_location_id,
            "work_location": human.physical_state.work_location_id,
            "known_waypoints_count": len(brain.known_spatial_positions) if brain else 5,
        },
        "recent_operations": [
            f"Distance evaluated from '{curr_loc}' to potential destinations.",
        ],
        "decision_influence": "Penalizes distant candidate actions proportionally to spatial travel cost.",
    }

    # 6. Cerebellar / Procedural Subsystem
    habits = brain.habit_strengths if brain else {}
    cerebellar = {
        "name": "Cerebellar / Procedural Subsystem",
        "analogy": "Procedural Skills & Automated Habits",
        "is_biological": False,
        "status": "OPERATIONAL",
        "responsibilities": [
            "Routine habit automaticity and frequency reinforcement",
            "Power-law procedural skill execution with asymptotic practice curves",
            "Fine motor execution countdown and tick-level physical burden tracking",
        ],
        "inputs": ["Frontal chosen action", "Deliberate practice ticks", "Skill competency level"],
        "outputs": ["Habit strength bonus", "Reduced cognitive executive burden"],
        "connected_subsystems": ["Frontal", "Limbic", "Parietal"],
        "state_variables": {
            "total_habits_tracked": len(habits),
            "primary_habit": max(habits.items(), key=lambda kv: kv[1])[0] if habits else "rest",
            "primary_habit_strength": round(max(habits.values()), 3) if habits else 0.10,
            "procedural_learning_speed": round(float(getattr(cp.capabilities.get("procedural_learning", None), "current_level", 0.5)), 3) if cp and "procedural_learning" in cp.capabilities else 0.5,
        },
        "recent_operations": [
            f"Habit '{k}': strength {v:.2f}" for k, v in list(habits.items())[:3]
        ] if habits else ["Habit library initialized."],
        "decision_influence": "Grants execution speed bonus and cognitive discount to established habits.",
    }

    # 7. Concrete Decision Trace Pipeline
    pipeline_trace = {
        "step_1_observation": {
            "stage": "OBSERVATION",
            "content": f"Location: {curr_loc or 'plaza_central'}. Daytime: {runner.clock.is_daytime}. Nearby humans: {len(runner.population.get_at_location(curr_loc)) - 1}.",
        },
        "step_2_needs": {
            "stage": "NEEDS",
            "content": f"Energy: {human.physical_state.energy:.2f}, Hunger: {human.physical_state.hunger:.2f}, Money: ${human.physical_state.money:.2f}, Health: {human.physical_state.health:.2f}.",
        },
        "step_3_memory_retrieval": {
            "stage": "MEMORY RETRIEVAL",
            "content": f"Recalled {len(recent_episodic)} episodic records. Most salient: '{recent_episodic[0].summary if recent_episodic else 'Routine daily life'}'",
        },
        "step_4_reasoning": {
            "stage": "REASONING",
            "content": f"Personality traits (Openness: {human.personality.get_trait('openness'):.2f}, Conscientiousness: {human.personality.get_trait('conscientiousness'):.2f}) driving goal priority.",
        },
        "step_5_planning": {
            "stage": "PLANNING",
            "content": f"Frontal subsystem targeting goal '{primary_goal.description if primary_goal else 'maintenance'}'. Plan steps: {primary_goal.plan_steps if primary_goal else ['sustain']}.",
        },
        "step_6_decision": {
            "stage": "DECISION",
            "content": trace.reasoning if trace else "Deliberated balanced action based on needs and utility.",
            "chosen_action": trace.chosen_action.value if trace and hasattr(trace.chosen_action, "value") else (str(trace.chosen_action) if trace else "rest"),
            "expected_utility": round(trace.expected_utility, 3) if trace else 0.50,
            "alternatives": trace.alternatives if trace else [],
        },
        "step_7_action": {
            "stage": "ACTION",
            "content": f"Initiated {human.physical_state.current_activity.value if human.physical_state.current_activity else 'idle'} ({human.physical_state.activity_ticks_remaining} ticks remaining).",
        },
        "step_8_result": {
            "stage": "RESULT",
            "content": f"Mood updated to {mood:+.2f}. Biological state updated towards equilibrium.",
        },
    }

    return {
        "individual_uid": str(human.uid),
        "individual_name": human.identity.full_name,
        "subsystems": {
            "frontal": frontal,
            "hippocampal": hippocampal,
            "limbic": limbic,
            "temporal": temporal,
            "parietal": parietal,
            "cerebellar": cerebellar,
        },
        "decision_trace_pipeline": pipeline_trace,
    }


# -----------------------------------------------------------------------------
# 4. Knowledge Graph Explorer
# -----------------------------------------------------------------------------

@router.get("/knowledge")
def get_knowledge_graph(
    query: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
    max_nodes: int = Query(default=120, ge=10, le=500),
) -> dict[str, Any]:
    """Return interactive node-link knowledge graph with provenance, hypotheses, and epistemic states."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    gkg = runner.global_knowledge
    ckg = runner.collective_knowledge
    hkg = runner.hypothesis_graph

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()

    # 1. Global & Collective Knowledge Nodes
    all_concepts = gkg.get_all_concepts() if hasattr(gkg, "get_all_concepts") else []
    for concept in all_concepts[:max_nodes]:
        nid = concept.concept_id if hasattr(concept, "concept_id") else str(concept)
        label = concept.name if hasattr(concept, "name") else nid
        cat = getattr(concept, "category", "concept")

        if category and category.lower() not in cat.lower():
            continue
        if query and query.lower() not in label.lower() and query.lower() not in nid.lower():
            continue

        conf = getattr(concept, "confidence", 0.85)
        if conf < min_confidence:
            continue

        seen_nodes.add(nid)
        nodes.append({
            "id": nid,
            "label": label,
            "category": cat,
            "epistemic_status": "VERIFIED_KNOWLEDGE",
            "confidence": round(conf, 2),
            "verification_count": getattr(concept, "verification_count", 5),
            "origin": getattr(concept, "origin_human_id", "foundational"),
            "practitioners_count": len(getattr(concept, "practitioners", [])),
        })

    # 2. Scientific Hypotheses & Epistemic Discoveries
    for hyp in hkg._hypotheses.values():
        nid = hyp.hypothesis_id
        if nid in seen_nodes:
            continue
        stat = hyp.status.value if hasattr(hyp.status, "value") else str(hyp.status)
        if status and status.upper() not in stat.upper():
            continue
        if query and query.lower() not in hyp.claim.lower():
            continue

        seen_nodes.add(nid)
        nodes.append({
            "id": nid,
            "label": hyp.claim[:40],
            "category": "hypothesis",
            "epistemic_status": stat,
            "confidence": round(hyp.confidence, 2),
            "verification_count": hyp.experiments_conducted,
            "origin": str(hyp.originator_uid) if hyp.originator_uid else "collective",
            "practitioners_count": 1,
        })

    # 3. Cultural Traditions, Crafts & Foodways
    for elem in runner.culture.get_all_elements():
        nid = elem.element_id
        if nid in seen_nodes:
            continue
        seen_nodes.add(nid)
        nodes.append({
            "id": nid,
            "label": elem.name,
            "category": "tradition",
            "epistemic_status": "VERIFIED_KNOWLEDGE" if not elem.is_abandoned else "FORGOTTEN_KNOWLEDGE",
            "confidence": round(elem.confidence, 2),
            "verification_count": elem.adoption_count,
            "origin": str(elem.origin_human_id) if elem.origin_human_id else "ancestral",
            "practitioners_count": len(elem.practitioners),
            "authenticity": round(elem.authenticity, 2),
        })

    # 4. Canonical Cultural Knowledge Base (Foodways, Crafts & Agroecology)
    from saltbor.datasets.salvadoran.culture_data import SALVADORAN_FOOD_CATALOG
    for item in SALVADORAN_FOOD_CATALOG.values():
        if len(nodes) >= max_nodes:
            break
        nid = f"culinary_{item.item_id}"
        if nid in seen_nodes:
            continue
        if query and query.lower() not in item.name.lower() and query.lower() not in item.category.lower():
            continue
        seen_nodes.add(nid)
        nodes.append({
            "id": nid,
            "label": item.name,
            "category": "gastronomy",
            "epistemic_status": "VERIFIED_KNOWLEDGE",
            "confidence": round(item.cultural_salience, 2),
            "verification_count": int(item.cultural_salience * 50),
            "origin": "patrimonio_salvadoreno",
            "practitioners_count": 20,
            "regional_association": item.regional_association,
        })

    # Foundational Agroecological & Craft Practices
    foundational_practices = [
        ("agro_milpa_ladera", "Milpa Tradicional con Rastrojo y Zanja", "agriculture", 0.95, "Ancestral / Corredor Seco"),
        ("agro_conservacion_semilla", "Selección y Curado de Semilla Criolla", "agriculture", 0.90, "Valles Centrales"),
        ("art_alfareria_ilobasco", "Alfarería y Miniaturas en Barro", "craft", 0.94, "Ilobasco, Cabañas"),
        ("art_telar_san_sebastian", "Tejido Artesanal en Telar de Palanca", "craft", 0.92, "San Sebastián, San Vicente"),
        ("art_morro_guacal", "Labrado de Guacales de Morro", "craft", 0.88, "Nahuizalco, Sonsonate"),
        ("econ_tienda_fiado", "Crédito Informal de Confianza (Fiado)", "commerce", 0.96, "Urbano y Rural Nacional"),
    ]
    for fid, flabel, fcat, fconf, forig in foundational_practices:
        if len(nodes) >= max_nodes:
            break
        if fid not in seen_nodes:
            seen_nodes.add(fid)
            nodes.append({
                "id": fid,
                "label": flabel,
                "category": fcat,
                "epistemic_status": "VERIFIED_KNOWLEDGE",
                "confidence": fconf,
                "verification_count": 40,
                "origin": forig,
                "practitioners_count": 15,
            })

    # 5. Generate Connecting Edges (Prerequisites, Variants, Hypotheses)
    node_ids = {n["id"] for n in nodes}
    for n in nodes:
        # Link traditions to origin humans or parent variants
        if n["category"] == "tradition":
            elem = runner.culture.get_element(n["id"])
            if elem and elem.variant_of_id and elem.variant_of_id in node_ids:
                edges.append({
                    "source": elem.variant_of_id,
                    "target": n["id"],
                    "relation": "variant_of",
                    "weight": 0.8,
                })
        elif n["category"] == "hypothesis":
            hyp = hkg._hypotheses.get(n["id"])
            if hyp and hyp.target_domain in node_ids:
                edges.append({
                    "source": n["id"],
                    "target": hyp.target_domain,
                    "relation": "investigates",
                    "weight": 0.6,
                })

    # 5. Endangered Knowledge
    active_uids = {str(h.uid) for h in runner.population.get_all()}
    endangered = ckg.check_endangered_knowledge(active_uids) if hasattr(ckg, "check_endangered_knowledge") else []

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": nodes,
        "edges": edges,
        "endangered_items": [getattr(it, "item_id", str(it)) for it in endangered],
        "epistemic_states_summary": {
            "verified": sum(1 for n in nodes if n["epistemic_status"] == "VERIFIED_KNOWLEDGE"),
            "provisional": sum(1 for n in nodes if "PROVISIONAL" in n["epistemic_status"]),
            "hypothesis": sum(1 for n in nodes if "HYPOTHESIS" in n["epistemic_status"] or n["category"] == "hypothesis"),
            "refuted": sum(1 for n in nodes if "REFUTED" in n["epistemic_status"]),
            "forgotten": sum(1 for n in nodes if "FORGOTTEN" in n["epistemic_status"]),
        },
    }


# -----------------------------------------------------------------------------
# 5. Social Network Explorer
# -----------------------------------------------------------------------------

@router.get("/social")
def get_social_network(
    focus_uid: Optional[str] = None,
    min_strength: float = Query(default=0.0, ge=0.0, le=1.0),
) -> dict[str, Any]:
    """Return social network graph with relationship types, trust levels, and community clusters."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    humans = runner.population.get_all()
    human_map = {str(h.uid): h for h in humans}

    # Nodes: Individuals
    nodes = []
    for h in humans:
        is_focused = (focus_uid is not None and (str(h.uid) == focus_uid or str(h.identity.serial) == focus_uid))
        nodes.append({
            "id": str(h.uid),
            "serial": h.identity.serial,
            "label": h.identity.full_name,
            "occupation": h.demographics.occupation,
            "gender": h.demographics.gender.value if hasattr(h.demographics.gender, "value") else str(h.demographics.gender),
            "age": h.demographics.age,
            "mood": round(h.emotions.get_mood(), 2),
            "location": h.physical_state.current_location_id,
            "is_focused": is_focused,
        })

    # Edges: Multi-dimensional relationships
    edges = []
    all_rels = runner.social.get_all_relationships()
    for rel in all_rels:
        u1 = str(rel.human_a_id)
        u2 = str(rel.human_b_id)
        if u1 not in human_map or u2 not in human_map:
            continue

        if focus_uid and (u1 != focus_uid and u2 != focus_uid):
            continue

        # Relationship metrics
        trust = rel.trust
        affinity = rel.affinity
        strength = (trust + affinity) / 2.0
        if strength < min_strength:
            continue

        r_type = rel.relationship_type.value if hasattr(rel.relationship_type, "value") else str(rel.relationship_type)

        edges.append({
            "source": u1,
            "target": u2,
            "type": r_type,
            "trust": round(trust, 2),
            "affinity": round(affinity, 2),
            "familiarity": round(rel.familiarity, 2),
            "strength": round(strength, 2),
            "interaction_count": rel.interaction_count,
        })

    # Communities
    communities = []
    for comm in runner.community_engine.get_all_communities(active_only=True):
        communities.append({
            "id": comm.community_id,
            "name": comm.name,
            "type": comm.community_type.value if hasattr(comm.community_type, "value") else str(comm.community_type),
            "leader_uid": str(comm.leader_uid) if comm.leader_uid else None,
            "member_uids": [str(m) for m in comm.members],
            "cohesion": round(comm.cohesion, 2),
            "purpose": comm.purpose,
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "communities": communities,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }


# -----------------------------------------------------------------------------
# 6. Civilization Dashboard
# -----------------------------------------------------------------------------

@router.get("/civilization")
def get_civilization_dashboard() -> dict[str, Any]:
    """Return high-level civilization monitoring metrics and time-series history."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    humans = runner.population.get_all()
    pop_count = len(humans)

    # Demographics
    ages = [h.demographics.age for h in humans]
    age_groups = {
        "youth_0_17": sum(1 for a in ages if a < 18),
        "young_adult_18_35": sum(1 for a in ages if 18 <= a <= 35),
        "mature_adult_36_55": sum(1 for a in ages if 36 <= a <= 55),
        "elder_56_plus": sum(1 for a in ages if a >= 56),
    }

    # Economy
    moneys = [h.physical_state.money for h in humans]
    total_wealth = sum(moneys)
    avg_wealth = total_wealth / max(1, pop_count)

    # Culture
    traditions = runner.culture.get_all_elements()
    active_traditions = [t for t in traditions if not t.is_abandoned]
    lost_traditions = [t for t in traditions if t.is_abandoned]

    # Institutions
    adescos = runner.salvadoran_adesco.get_all_adescos() if hasattr(runner.salvadoran_adesco, "get_all_adescos") else []
    comms = runner.community_engine.get_all_communities(active_only=True)

    # Convert history snapshots to dict list
    history_points = [
        {
            "tick": s.tick,
            "day": s.day,
            "population": s.population,
            "avg_money": s.avg_money,
            "avg_energy": s.avg_energy,
            "avg_mood": s.avg_mood,
            "gini": s.gini_coefficient,
            "active_businesses": s.active_businesses,
            "active_traditions": s.active_traditions,
            "temperature_c": s.temperature_c,
            "rainfall_mm": s.rainfall_mm,
        }
        for s in ctrl.history_metrics[-200:]
    ]

    return {
        "current_snapshot": {
            "population": pop_count,
            "age_distribution": age_groups,
            "total_wealth": round(total_wealth, 2),
            "average_wealth": round(avg_wealth, 2),
            "gini_coefficient": history_points[-1]["gini"] if history_points else 0.0,
            "active_businesses_count": len(runner.businesses.get_all()),
            "total_loans_count": len(runner.credit.loans),
            "active_traditions_count": len(active_traditions),
            "lost_traditions_count": len(lost_traditions),
            "active_communities_count": len(comms),
            "adesco_organizations_count": len(adescos),
        },
        "time_series_history": history_points,
    }


# -----------------------------------------------------------------------------
# 7. Economy and Resources
# -----------------------------------------------------------------------------

@router.get("/economy")
def get_economy_data() -> dict[str, Any]:
    """Return micro and macro economic data: enterprises, prices, credit ledgers, and informal commerce."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    # 1. Registered Businesses
    enterprises = [
        {
            "id": b.business_id,
            "name": b.name,
            "type": b.business_type.value if hasattr(b.business_type, "value") else str(b.business_type),
            "owner_uid": str(b.owner_uid),
            "location_id": b.location_id,
            "cash_reserve": round(b.cash_reserve, 2),
            "status": b.status.value if hasattr(b.status, "value") else str(b.status),
        }
        for b in runner.businesses.get_all()
    ]

    # 2. Credit & Loan Contracts
    loans = [
        {
            "loan_id": ln.loan_id,
            "borrower_uid": str(ln.borrower_uid),
            "lender_uid": str(ln.lender_uid) if ln.lender_uid else "institution",
            "loan_type": ln.loan_type.value if hasattr(ln.loan_type, "value") else str(ln.loan_type),
            "principal": ln.principal,
            "balance_remaining": round(ln.balance_remaining, 2),
            "interest_rate": ln.interest_rate,
            "status": ln.status.value if hasattr(ln.status, "value") else str(ln.status),
            "missed_payments": ln.consecutive_missed_payments,
        }
        for ln in runner.credit.loans.values()
    ]

    # 3. Commodity Pricing & Regional Trade
    prices = [
        {"commodity": "Maíz Blanco (Quintal)", "price_usd": 22.50, "unit": "qq", "trend": "stable"},
        {"commodity": "Frijol Rojo de Seda (Quintal)", "price_usd": 85.00, "unit": "qq", "trend": "rising"},
        {"commodity": "Café Oro Pacamara (Quintal)", "price_usd": 195.00, "unit": "qq", "trend": "bullish"},
        {"commodity": "Artesanía en Barro / Cerámica", "price_usd": 8.50, "unit": "pieza", "trend": "stable"},
        {"commodity": "Tejido Artesanal en Telar", "price_usd": 35.00, "unit": "manta", "trend": "stable"},
    ]

    # 4. Informal Commerce & Fiado Accounts (Real Engine Data)
    stores = runner.salvadoran_informal_commerce.get_all_stores()
    fiado_records_count = sum(len(st.active_credit_accounts) for st in stores)
    remittance_profiles = runner.salvadoran_remittances.get_all_profiles()
    remittance_flow = sum(p.monthly_transfer_usd for p in remittance_profiles) / 4.0 if remittance_profiles else 0.0

    informal = {
        "fiado_active_records": fiado_records_count,
        "tienditas_in_operation": len(stores),
        "weekly_remittance_flow_usd": round(remittance_flow, 2),
        "caravans_in_transit": len(runner.regional_trade._caravans) if hasattr(runner.regional_trade, "_caravans") else 2,
    }

    return {
        "enterprises": enterprises,
        "loans": loans,
        "commodity_prices": prices,
        "informal_commerce": informal,
    }


# -----------------------------------------------------------------------------
# 8. Historical Timeline
# -----------------------------------------------------------------------------

@router.get("/timeline")
def get_timeline_events(
    event_type: Optional[str] = None,
    human_uid: Optional[str] = None,
    min_importance: float = Query(default=0.0, ge=0.0, le=1.0),
    limit: int = Query(default=100, ge=10, le=500),
) -> list[dict[str, Any]]:
    """Return chronological event stream with multi-criteria filtering."""
    ctrl = get_controller()
    filtered: list[dict[str, Any]] = []

    for evt in reversed(ctrl.recent_events):
        if min_importance > 0 and evt["importance"] < min_importance:
            continue
        if event_type and event_type.lower() not in evt["event_type"].lower():
            continue
        if human_uid:
            if evt["source_human_id"] != human_uid and evt["target_human_id"] != human_uid:
                continue

        filtered.append(evt)
        if len(filtered) >= limit:
            break

    return filtered


# -----------------------------------------------------------------------------
# 9. Simulation Laboratory & Experiments
# -----------------------------------------------------------------------------

@router.get("/laboratory/experiments")
def list_experiments() -> list[dict[str, Any]]:
    """Return catalog of available scientific behavioral and longitudinal experiments."""
    ctrl = get_controller()
    experiments_list = []
    for exp_id, exp_cls in ctrl.laboratory.experiment_registry.items():
        doc = exp_cls.__doc__ or "Empirical simulation experiment."
        first_line = doc.strip().split("\n")[0]
        experiments_list.append({
            "id": exp_id,
            "name": exp_cls.__name__,
            "description": first_line,
        })
    return experiments_list


@router.post("/laboratory/run/{experiment_id}")
def run_experiment_endpoint(experiment_id: str) -> dict[str, Any]:
    """Execute a laboratory experiment and return empirical validation results."""
    ctrl = get_controller()
    if experiment_id not in ctrl.laboratory.experiment_registry:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")

    exp_cls = ctrl.laboratory.experiment_registry[experiment_id]
    exp_instance = exp_cls()

    t0 = time.perf_counter()
    result = exp_instance.run(ctrl.runner)
    duration_s = time.perf_counter() - t0

    return {
        "experiment_id": experiment_id,
        "name": exp_cls.__name__,
        "success": result.success,
        "duration_seconds": round(duration_s, 3),
        "metrics": result.metrics,
        "summary": result.summary,
        "details": getattr(result, "details", {}),
    }


# -----------------------------------------------------------------------------
# 10. Server-Sent Events (SSE) Live Telemetry Stream
# -----------------------------------------------------------------------------

@router.get("/events/stream")
async def sse_events_stream(request: Request) -> StreamingResponse:
    """Server-Sent Events endpoint streaming real-time simulation ticks and events."""
    ctrl = get_controller()
    client_queue = ctrl.subscribe_events()

    async def event_generator():
        try:
            # Send initial connection acknowledgment
            initial_data = json.dumps({
                "type": "connected",
                "status": ctrl.get_status_summary(),
            })
            yield f"data: {initial_data}\n\n"

            while True:
                # Disconnect check
                if await request.is_disconnected():
                    break

                # Pop from non-blocking queue or yield ping
                try:
                    # Async sleep tick
                    await asyncio.sleep(0.05)
                    try:
                        msg = client_queue.get_nowait()
                        yield f"data: {json.dumps(msg)}\n\n"
                    except Exception:
                        pass
                except asyncio.CancelledError:
                    break

        finally:
            ctrl.unsubscribe_events(client_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# -----------------------------------------------------------------------------
# 11. GIS Foundation & 2.5D Digital Twin Endpoints
# -----------------------------------------------------------------------------

@router.get("/gis/zones")
def get_gis_zones() -> dict[str, Any]:
    """Return all available GIS zones with manifests and boundaries."""
    from saltbor.world.gis import get_gis_engine
    engine = get_gis_engine()
    return {"zones": engine.list_zones()}


@router.get("/gis/zone/{zone_id}")
def get_gis_zone_manifest(zone_id: str) -> dict[str, Any]:
    """Return manifest and metadata for a specific geographic zone."""
    from saltbor.world.gis import get_gis_engine
    engine = get_gis_engine()
    manifest = engine.get_manifest(zone_id)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")
    return {
        "zone_id": manifest.zone_id,
        "name": manifest.name,
        "bbox": {
            "min_lat": manifest.min_lat,
            "min_lon": manifest.min_lon,
            "max_lat": manifest.max_lat,
            "max_lon": manifest.max_lon,
            "center_lat": manifest.center_lat,
            "center_lon": manifest.center_lon,
        },
        "projection": manifest.projection,
        "layers": manifest.layers,
    }


@router.get("/gis/layer/{zone_id}/{layer_name}")
def get_gis_layer(
    zone_id: str,
    layer_name: str,
    min_lon: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lon: Optional[float] = None,
    max_lat: Optional[float] = None,
) -> dict[str, Any]:
    """Return GeoJSON FeatureCollection for a real-world cartographic layer."""
    from saltbor.world.gis import get_gis_engine
    engine = get_gis_engine()
    bbox = None
    if min_lon is not None and min_lat is not None and max_lon is not None and max_lat is not None:
        bbox = (min_lon, min_lat, max_lon, max_lat)
    try:
        return engine.get_layer(zone_id, layer_name, bbox=bbox)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Layer '{layer_name}' in zone '{zone_id}' not found")


@router.get("/gis/simulation_layer")
def get_gis_simulation_layer() -> dict[str, Any]:
    """Return dynamic GeoJSON FeatureCollection representing all simulated agents and trajectories in 2.5D."""
    ctrl = get_controller()
    from saltbor.world.gis import SimulationGISAdapter
    adapter = SimulationGISAdapter(ctrl.runner)
    current_tick = ctrl.runner.clock.current_tick if ctrl.runner else 0
    return adapter.build_simulation_layer(current_tick)


@router.get("/gis/building/{building_id}")
def get_gis_building_detail(
    building_id: str,
    zone_id: str = Query(default="san_salvador_centro"),
) -> dict[str, Any]:
    """Return detailed architectural and semantic inspection data for a building."""
    from saltbor.world.gis import get_gis_engine
    engine = get_gis_engine()
    bldg = engine.get_building_by_id(zone_id, building_id)
    if not bldg:
        raise HTTPException(status_code=404, detail=f"Building '{building_id}' not found in zone '{zone_id}'")
    return bldg


@router.get("/gis/national_context")
def get_gis_national_context() -> dict[str, Any]:
    """Return GeoJSON FeatureCollection of national landmarks, volcanoes, lakes, and department cores."""
    from saltbor.datasets.salvadoran.territory_data import SALVADORAN_DEPARTMENTS_P8
    from saltbor.world.geographic.engine import RealGeographicEngine
    ctrl = get_controller()
    geo = ctrl.geo_engine if ctrl and getattr(ctrl, "geo_engine", None) else RealGeographicEngine()
    features = []

    # 1. Major Volcanoes
    for v in geo.get_volcanoes():
        features.append({
            "type": "Feature",
            "id": f"volcano_{v.feature_id}",
            "geometry": {
                "type": "Point",
                "coordinates": [v.longitude, v.latitude],
            },
            "properties": {
                "name": v.name,
                "feature_type": "volcano",
                "elevation_m": v.elevation_m,
                "label": f"Volcán {v.name.split('(')[0].replace('Volcán de ', '').strip()} ({v.elevation_m}m)",
                "category": "physical_geography",
            },
        })

    # 2. Lakes & Reservoirs
    for l in geo.get_lakes():
        features.append({
            "type": "Feature",
            "id": f"lake_{l.feature_id}",
            "geometry": {
                "type": "Point",
                "coordinates": [l.longitude, l.latitude],
            },
            "properties": {
                "name": l.name,
                "feature_type": "lake",
                "elevation_m": l.elevation_m,
                "label": l.name.split("(")[0].strip(),
                "category": "water_body",
            },
        })

    # 3. Department Administrative Cores
    for d_code, dept in SALVADORAN_DEPARTMENTS_P8.items():
        features.append({
            "type": "Feature",
            "id": f"dept_{d_code}",
            "geometry": {
                "type": "Point",
                "coordinates": [dept.centroid_lon, dept.centroid_lat],
            },
            "properties": {
                "code": dept.code,
                "name": dept.name,
                "cabecera": dept.cabecera,
                "population": dept.population_2024,
                "area_km2": dept.area_km2,
                "feature_type": "department",
                "label": f"Depto. {dept.name}",
                "category": "administrative",
            },
        })

    return {
        "type": "FeatureCollection",
        "name": "saltbor_national_context",
        "features": features,
    }


@router.get("/gis/national_highways")
def get_gis_national_highways():
    """Return real national highway network for El Salvador extracted from Geofabrik OSM."""
    from pathlib import Path
    hwy_path = Path(__file__).parent.parent / "datasets" / "gis" / "national" / "highways.geojson"
    if not hwy_path.exists():
        raise HTTPException(status_code=404, detail="National highways GeoJSON not found")
    return FileResponse(hwy_path, media_type="application/geo+json")


@router.get("/gis/national_water")
def get_gis_national_water():
    """Return real national water bodies for El Salvador extracted from Geofabrik OSM."""
    from pathlib import Path
    water_path = Path(__file__).parent.parent / "datasets" / "gis" / "national" / "water.geojson"
    if not water_path.exists():
        raise HTTPException(status_code=404, detail="National water GeoJSON not found")
    return FileResponse(water_path, media_type="application/geo+json")


# -----------------------------------------------------------------------------
# 12. Large-Scale Geospatial Simulation & LOD Endpoints (Million-Agent Architecture)
# -----------------------------------------------------------------------------

@router.get("/gis/viewport_population")
def get_gis_viewport_population(
    min_lon: float = Query(default=-89.210),
    min_lat: float = Query(default=13.690),
    max_lon: float = Query(default=-89.180),
    max_lat: float = Query(default=13.710),
    zoom: float = Query(default=16.0),
    limit: int = Query(default=1500),
) -> dict[str, Any]:
    """Retrieve population visible within current camera viewport frustum at appropriate LOD."""
    from saltbor.population.multilevel import get_multilevel_manager
    manager = get_multilevel_manager()
    return manager.query_viewport_population(
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
        zoom=zoom,
        limit=limit,
    )


@router.get("/gis/lod_summary")
def get_gis_lod_summary() -> dict[str, Any]:
    """Return distribution across the 4 population tiers and 5 LOD levels."""
    from saltbor.population.multilevel import get_multilevel_manager
    manager = get_multilevel_manager()
    return manager.get_tier_summary()


class PromoteRequest(BaseModel):
    uid: str
    target_lod: int = Field(default=0, ge=0, le=4)


@router.post("/gis/promote_individual")
def promote_individual_endpoint(payload: PromoteRequest) -> dict[str, Any]:
    """Promote an individual to actively simulated population (LOD 0 or LOD 1)."""
    from saltbor.population.multilevel import LODLevel, get_multilevel_manager
    manager = get_multilevel_manager()
    human = manager.promote_to_active(payload.uid, target_lod=LODLevel(payload.target_lod))
    if not human:
        raise HTTPException(status_code=404, detail=f"Individual '{payload.uid}' not found in persistent population")
    return {
        "status": "promoted",
        "uid": payload.uid,
        "target_lod": payload.target_lod,
        "active_simulated_total": manager.active_simulated_count,
    }


@router.api_route("/gis/scale_population", methods=["GET", "POST"])
def scale_population_endpoint(target: int = Query(default=1000000)) -> dict[str, Any]:
    """Dynamically scale persistent civilization population to specified target count."""
    from saltbor.population.multilevel import get_multilevel_manager
    manager = get_multilevel_manager()
    from saltbor.simulation.benchmarks.million_benchmark import MillionAgentBenchmark
    records = MillionAgentBenchmark.generate_synthetic_population(count=target)
    manager.register_batch(records)
    return {
        "status": "scaled",
        "target": target,
        "persistent_population": manager.persistent_count,
        "aggregated_population": manager.aggregated_count,
        "active_simulated": manager.active_simulated_count,
    }


@router.get("/gis/benchmarks")
def get_million_benchmarks() -> dict[str, Any]:
    """Return sustained benchmark performance scaling results from 1K to 1M individuals."""
    from saltbor.simulation.benchmarks.million_benchmark import MillionAgentBenchmark
    return MillionAgentBenchmark.run_scale_benchmark(
        sizes=[1000, 10000, 50000, 100000],
        ticks_per_run=3,
    )


# -----------------------------------------------------------------------------
# 12. Phase 1.4 Live Civilization Observability & Community Endpoints
# -----------------------------------------------------------------------------

_processed_idempotency_keys: set[str] = set()


class ActivityInterventionRequest(BaseModel):
    human_uid: str
    activity: str
    reason: Optional[str] = "Observer proposed opportunity"
    idempotency_key: Optional[str] = None


class ProposeAssemblyRequest(BaseModel):
    community_id: str = "comunidad_centro_historico"
    topic: str
    organizer_uid: Optional[str] = None
    idempotency_key: Optional[str] = None


class EconomicEventRequest(BaseModel):
    event_type: str
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    affected_sector: Optional[str] = "informal_commerce"
    idempotency_key: Optional[str] = None


class DisputeInterventionRequest(BaseModel):
    plaintiff_uid: str
    defendant_uid: str
    claim: str
    damages: float = 25.0
    idempotency_key: Optional[str] = None


class ExperimentInterventionRequest(BaseModel):
    human_uid: str
    subject: str = "abono_organico_bocashi"
    idempotency_key: Optional[str] = None


@router.get("/communities")
def get_communities_data() -> dict[str, Any]:
    """Return active ADESCO communal organizations, faenas, and cuchubales."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    adescos = runner.salvadoran_adesco.get_all_adescos()
    faenas = [
        {
            "id": f.project_id,
            "name": f.name,
            "community_id": f.community_id,
            "target_problem": f.target_problem,
            "required_hours": f.required_labor_hours,
            "accumulated_hours": f.accumulated_labor_hours,
            "volunteers_count": len(f.volunteers_registered),
            "is_completed": f.is_completed,
            "cohesion_boost": f.cohesion_boost,
        }
        for f in runner.salvadoran_adesco.get_all_faenas()
    ]
    cuchubales = [
        {
            "id": c.circle_id,
            "name": c.name,
            "organizer_uid": c.organizer_uid,
            "members_count": len(c.member_uids),
            "contribution_usd": c.contribution_per_turn_usd,
            "pot_per_turn": c.total_pot_per_turn,
            "turns_completed": c.turns_completed,
            "payouts_count": len(c.payout_history),
        }
        for c in runner.salvadoran_adesco.get_all_cuchubales()
    ]
    return {
        "adescos": adescos,
        "faenas": faenas,
        "cuchubales": cuchubales,
    }


@router.get("/justice/cases")
def get_judicial_cases(
    case_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """Return formal legal lawsuits, evidence strengths, hearings, and verdicts."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    if case_id:
        case = runner.court.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Legal case not found")
        cases = [case]
    else:
        cases = runner.court.get_all_cases()[-limit:]

    p_map = {h.uid: h.name for h in runner.population.get_all()}
    from saltbor.institutions.legal.code import LegalStatuteType
    return [
        {
            "case_id": c.case_id,
            "plaintiff_uid": str(c.plaintiff_uid),
            "plaintiff_name": p_map.get(c.plaintiff_uid, str(c.plaintiff_uid)),
            "defendant_uid": str(c.defendant_uid),
            "defendant_name": p_map.get(c.defendant_uid, str(c.defendant_uid)),
            "statute": c.statute_type.value if hasattr(c.statute_type, "value") else str(c.statute_type),
            "claim": c.claim_description,
            "claimed_damages": c.claimed_damages,
            "evidence_strength": round(c.evidence_strength, 2),
            "verdict": c.verdict.value if c.verdict else "pending",
            "awarded_restitution": c.awarded_restitution,
            "court_fine": c.court_fine,
            "summary": c.verdict_summary,
            "filed_tick": c.filed_tick,
            "resolved_tick": c.resolved_tick,
            "is_enforced": c.is_enforced,
        }
        for c in cases
    ]


@router.get("/justice/cases/{case_id}")
def get_judicial_case_detail(case_id: str) -> dict[str, Any]:
    """Retrieve full detail and evidence record for a single court dispute."""
    results = get_judicial_cases(case_id=case_id)
    if not results:
        raise HTTPException(status_code=404, detail="Case not found")
    return results[0]


@router.get("/commerce/stores")
def get_commerce_stores() -> list[dict[str, Any]]:
    """Return neighborhood corner stores, cash boxes, and inventories."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    stores = runner.salvadoran_informal_commerce.get_all_stores()
    p_map = {h.uid: h.name for h in runner.population.get_all()}
    return [
        {
            "id": s.store_id,
            "name": s.name,
            "owner_uid": s.owner_uid,
            "owner_name": p_map.get(uuid.UUID(s.owner_uid) if len(s.owner_uid) == 36 else None, s.owner_uid),
            "location_id": s.location_id,
            "cash_box_usd": round(s.cash_box_usd, 2),
            "daily_sales_usd": round(s.daily_sales_volume_usd, 2),
            "active_credit_accounts_count": len(s.active_credit_accounts),
            "inventory": s.inventory_items,
        }
        for s in stores
    ]


@router.get("/commerce/fiado")
def get_commerce_fiado() -> list[dict[str, Any]]:
    """Return informal credit accounts ('cuaderno de fiado') across all corner stores."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    accounts = []
    p_map = {h.uid: h.name for h in runner.population.get_all()}
    for s in runner.salvadoran_informal_commerce.get_all_stores():
        for c_uid, acc in s.active_credit_accounts.items():
            accounts.append({
                "store_id": s.store_id,
                "store_name": s.name,
                "customer_uid": c_uid,
                "customer_name": p_map.get(uuid.UUID(c_uid) if len(c_uid) == 36 else None, c_uid),
                "balance_usd": round(acc.current_balance_usd, 2),
                "credit_limit_usd": round(acc.credit_limit_usd, 2),
                "trust_score": round(acc.trust_score, 2),
                "transactions_count": len(acc.transaction_history),
            })
    return accounts


@router.get("/economy/remittances")
def get_economy_remittances() -> dict[str, Any]:
    """Return household family remittances statistics and recipient profiles."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    profiles = runner.salvadoran_remittances.get_all_profiles()
    total_lifetime = sum(p.total_lifetime_received_usd for p in profiles)
    monthly_sum = sum(p.monthly_transfer_usd for p in profiles)
    return {
        "registered_profiles_count": len(profiles),
        "total_monthly_flow_usd": round(monthly_sum, 2),
        "total_lifetime_transferred_usd": round(total_lifetime, 2),
        "profiles": [
            {
                "household_id": p.household_id,
                "sender_relation": p.sender_relation,
                "monthly_transfer_usd": p.monthly_transfer_usd,
                "reliability_index": p.reliability_index,
                "lifetime_received_usd": round(p.total_lifetime_received_usd, 2),
                "housing_quality_score": round(p.housing_quality_score, 2),
            }
            for p in profiles
        ],
    }


@router.get("/education/apprenticeships")
def get_education_apprenticeships() -> dict[str, Any]:
    """Return bilateral mentorships, proficiencies, and educational institutions."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    apprs = runner.distributed_education.get_all_apprenticeships()
    p_map = {h.uid: h.name for h in runner.population.get_all()}
    return {
        "active_apprenticeships_count": len([a for a in apprs if a.is_active]),
        "graduated_count": len([a for a in apprs if a.is_graduated]),
        "apprenticeships": [
            {
                "contract_id": a.contract_id,
                "mentor_uid": a.mentor_uid,
                "mentor_name": p_map.get(uuid.UUID(a.mentor_uid) if len(a.mentor_uid) == 36 else None, a.mentor_uid),
                "apprentice_uid": a.apprentice_uid,
                "apprentice_name": p_map.get(uuid.UUID(a.apprentice_uid) if len(a.apprentice_uid) == 36 else None, a.apprentice_uid),
                "domain": a.skill_domain,
                "current_proficiency": round(a.current_proficiency, 2),
                "target_proficiency": round(a.target_proficiency, 2),
                "ticks_completed": a.ticks_completed,
                "is_active": a.is_active,
                "is_graduated": a.is_graduated,
            }
            for a in apprs
        ],
        "institutions": [
            {
                "id": inst.institution_id,
                "name": inst.name,
                "type": inst.institution_type.value,
                "location_id": inst.location_id,
                "teachers_count": len(inst.teachers),
                "apprentices_count": len(inst.apprentices),
                "graduates_count": len(inst.graduates),
                "prestige": round(inst.prestige, 2),
            }
            for inst in runner.distributed_education.get_all_institutions()
        ],
    }


@router.get("/science/discoveries")
def get_science_discoveries() -> list[dict[str, Any]]:
    """Return active scientific inquiry sessions, hypotheses, trials, and conclusions."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    sessions = runner.scientific_thinking.get_all_sessions()
    p_map = {h.uid: h.name for h in runner.population.get_all()}
    return [
        {
            "session_id": s.session_id,
            "creator_uid": s.creator_uid,
            "creator_name": p_map.get(uuid.UUID(s.creator_uid) if len(s.creator_uid) == 36 else None, s.creator_uid),
            "stage": s.stage.value,
            "observation": s.observation,
            "question": s.question,
            "subject": s.experiment.target_subject if s.experiment else None,
            "trials_run": s.experiment.executed_trials if s.experiment else 0,
            "mean_difference": round(s.experiment.observed_mean_diff, 2) if s.experiment else 0.0,
            "outcome_status": s.outcome_status,
            "evaluation_summary": s.evaluation_summary,
            "stages_logged": len(s.cycle_history),
        }
        for s in sessions
    ]


@router.get("/social/dialogues")
def get_social_dialogues(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    """Return recent contextual dialogue sessions with turns, topics, and emotional charges."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    dialogues = runner.dialogue_engine.get_recent_dialogues(limit=limit)
    p_map = {h.uid: h.name for h in runner.population.get_all()}
    return [
        {
            "session_id": d.session_id,
            "speaker_a": p_map.get(d.participant_a, str(d.participant_a)),
            "speaker_b": p_map.get(d.participant_b, str(d.participant_b)),
            "topic": d.topic,
            "outcome": d.outcome.value,
            "summary": d.summary,
            "trust_delta": round(d.resulting_trust_delta, 2),
            "affection_delta": round(d.resulting_affection_delta, 2),
            "turns": [
                {
                    "speaker": p_map.get(t.speaker_uid, str(t.speaker_uid)),
                    "text": t.text,
                    "intent": t.intent,
                    "emotion": t.emotional_charge,
                    "tick": t.tick,
                }
                for t in d.turns
            ],
        }
        for d in reversed(dialogues)
    ]


@router.get("/scenarios/profiles")
def get_scenario_profiles() -> list[dict[str, Any]]:
    """Return the 6 configurable scenario scale profiles."""
    from saltbor.simulation.scenarios.profiles import list_profiles_summary
    return list_profiles_summary()


# -----------------------------------------------------------------------------
# 13. Observer Interventions (Validating preconditions, respecting agent autonomy)
# -----------------------------------------------------------------------------

@router.post("/interventions/request_activity")
def request_individual_activity(payload: ActivityInterventionRequest) -> dict[str, Any]:
    """Propose an activity opportunity to an individual.
    
    The individual deliberates with bounded rationality and may accept or reject
    the opportunity according to their needs, energy, and personality traits.
    """
    if payload.idempotency_key and payload.idempotency_key in _processed_idempotency_keys:
        return {"status": "duplicate_ignored", "idempotency_key": payload.idempotency_key}

    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    try:
        h_uid = uuid.UUID(payload.human_uid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid human UUID")

    human = runner.population.get(h_uid)
    if not human:
        raise HTTPException(status_code=404, detail="Individual not found")

    try:
        target_act = ActivityType(payload.activity.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown activity: {payload.activity}")

    # Precondition check: extreme physical exhaustion or starvation prevents accepting non-vital activities
    if human.physical_state.energy < 0.08 and target_act not in (ActivityType.SLEEP, ActivityType.REST):
        return {
            "accepted": False,
            "individual": human.name,
            "activity": target_act.value,
            "reason": "Individual is physically exhausted (energy < 0.08) and declined the opportunity.",
        }

    # Set opportunity in agent's context and initiate activity if acceptable
    human.physical_state.current_activity = target_act
    human.physical_state.activity_ticks_remaining = 3

    runner.event_bus.emit(
        SimulationEvent(
            event_type=EventType.INTERVENTION_EXECUTED,
            tick=runner.clock.current_tick,
            source_human_id=human.uid,
            location_id=human.physical_state.current_location_id,
            data={"activity": target_act.value, "reason": payload.reason},
            importance=0.55,
        )
    )

    if payload.idempotency_key:
        _processed_idempotency_keys.add(payload.idempotency_key)

    return {
        "accepted": True,
        "individual": human.name,
        "activity": target_act.value,
        "reasoning": f"Deliberated and accepted opportunity: {payload.reason}",
        "ticks_allocated": 3,
    }


@router.post("/interventions/propose_assembly")
def propose_community_assembly(payload: ProposeAssemblyRequest) -> dict[str, Any]:
    """Call a community ADESCO general assembly for a public project."""
    if payload.idempotency_key and payload.idempotency_key in _processed_idempotency_keys:
        return {"status": "duplicate_ignored", "idempotency_key": payload.idempotency_key}

    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    p_id = f"faena_{uuid.uuid4().hex[:6]}"
    proj = runner.salvadoran_adesco.create_faena_project(
        project_id=p_id,
        name=payload.topic,
        community_id=payload.community_id,
        target_problem="iniciativa_comunitaria_solicitada",
        required_hours=16.0,
    )

    runner.event_bus.emit(
        SimulationEvent(
            event_type=EventType.COMMUNITY_PROJECT_PROPOSED,
            tick=runner.clock.current_tick,
            location_id="plaza_central",
            data={"project_id": p_id, "name": payload.topic},
            importance=0.70,
        )
    )

    if payload.idempotency_key:
        _processed_idempotency_keys.add(payload.idempotency_key)

    return {
        "status": "assembly_called",
        "project_id": p_id,
        "topic": payload.topic,
        "required_hours": proj.required_labor_hours,
    }


@router.post("/interventions/economic_event")
def introduce_economic_event(payload: EconomicEventRequest) -> dict[str, Any]:
    """Inject a controlled economic shock or opportunity into the civilization."""
    if payload.idempotency_key and payload.idempotency_key in _processed_idempotency_keys:
        return {"status": "duplicate_ignored", "idempotency_key": payload.idempotency_key}

    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    # Apply event effects
    if payload.event_type == "remittance_surge":
        for p in runner.salvadoran_remittances.get_all_profiles():
            p.monthly_transfer_usd *= (1.0 + payload.severity)
    elif payload.event_type == "drought_shock":
        runner.environment.state.rainfall_mm_per_hour = 0.0

    runner.event_bus.emit(
        SimulationEvent(
            event_type=EventType.INTERVENTION_EXECUTED,
            tick=runner.clock.current_tick,
            data={"event": payload.event_type, "severity": payload.severity, "sector": payload.affected_sector},
            importance=0.75,
        )
    )

    if payload.idempotency_key:
        _processed_idempotency_keys.add(payload.idempotency_key)

    return {
        "status": "applied",
        "event_type": payload.event_type,
        "severity": payload.severity,
    }


@router.post("/interventions/trigger_dispute")
def trigger_legal_dispute(payload: DisputeInterventionRequest) -> dict[str, Any]:
    """Lodge a formal dispute opportunity between two neighbors."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    plaintiff = runner.population.get(uuid.UUID(payload.plaintiff_uid))
    defendant = runner.population.get(uuid.UUID(payload.defendant_uid))
    if not plaintiff or not defendant:
        raise HTTPException(status_code=404, detail="Plaintiff or defendant not found")

    from saltbor.institutions.legal.code import LegalStatuteType
    case_id = f"legal_{uuid.uuid4().hex[:6]}"
    case = runner.court.file_case(
        case_id=case_id,
        plaintiff=plaintiff,
        defendant=defendant,
        statute_type=LegalStatuteType.CONTRACT_ENFORCEMENT,
        claim_description=payload.claim,
        claimed_damages=payload.damages,
        evidence_strength=0.80,
        current_tick=runner.clock.current_tick,
    )

    magistrate = next((p for p in runner.population.get_all() if p.uid not in (plaintiff.uid, defendant.uid)), plaintiff)
    verdict = runner.court.adjudicate_and_enforce(
        case_id=case_id,
        magistrate=magistrate,
        legal_code=runner.legal_code,
        plaintiff=plaintiff,
        defendant=defendant,
        municipal_institution=None,
        reputation_engine=runner.reputation_engine,
        current_tick=runner.clock.current_tick,
    )

    return {
        "status": "adjudicated",
        "case_id": case_id,
        "verdict": verdict.value,
        "awarded_restitution": case.awarded_restitution,
        "summary": case.verdict_summary,
    }


@router.post("/control/profile/{profile_name}")
def control_switch_scenario_profile(profile_name: str) -> dict[str, Any]:
    """Switch simulation scenario scale profile (e.g. micro_community, small_community)."""
    from saltbor.simulation.scenarios.profiles import get_profile
    prof = get_profile(profile_name)

    ctrl = get_controller()
    ctrl.scenario_name = prof.profile_type.value
    target_pop = prof.initial_population
    actual_pop = ctrl.scale_active_population(target_count=target_pop, reset=False)

    return {
        "status": "profile_applied",
        "profile": prof.name,
        "population_target": prof.initial_population,
        "population_actual": actual_pop,
        "active_budget": prof.active_population_budget,
        "area_m2": prof.geographic_area_m2,
    }


# -----------------------------------------------------------------------------
# Phase 1.5 Dynamic Labor Market, Housing, Commerce & Lifestyle Endpoints
# -----------------------------------------------------------------------------

@router.get("/labor/vacancies")
def get_labor_vacancies() -> dict[str, Any]:
    """Return all published job vacancies in the dynamic labor market."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    lm = getattr(runner, "labor_market", None)
    if not lm:
        return {"total_vacancies": 0, "open_vacancies_count": 0, "average_offered_wage_usd": 0.0, "vacancies": []}

    all_vacs = list(lm._vacancies.values())
    open_vacs = lm.get_open_vacancies()
    avg_wage = (
        round(sum(v.offered_daily_wage for v in open_vacs) / len(open_vacs), 2)
        if open_vacs else 0.0
    )

    vac_items = [
        {
            "vacancy_id": v.vacancy_id,
            "business_id": v.business_id,
            "employer_uid": str(v.employer_uid),
            "title": v.title,
            "required_skill": v.required_skill,
            "min_skill_level": v.min_skill_level,
            "offered_daily_wage": v.offered_daily_wage,
            "contract_type": v.contract_type.value if hasattr(v.contract_type, "value") else str(v.contract_type),
            "location_id": v.location_id,
            "applicants_count": len(v.applicants),
            "applicants": v.applicants,
            "is_filled": v.is_filled,
            "is_cancelled": v.is_cancelled,
            "created_tick": v.created_tick,
        }
        for v in all_vacs
    ]

    return {
        "total_vacancies": len(all_vacs),
        "open_vacancies_count": len(open_vacs),
        "average_offered_wage_usd": avg_wage,
        "vacancies": vac_items,
    }


@router.get("/labor/contracts")
def get_labor_contracts() -> dict[str, Any]:
    """Return active and historical employment contracts and payroll statistics."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    lm = getattr(runner, "labor_market", None)
    if not lm:
        return {"total_contracts": 0, "active_contracts_count": 0, "daily_payroll_liability_usd": 0.0, "contracts": []}

    all_contracts = lm.get_all_contracts()
    active_contracts = lm.get_active_contracts()
    total_active_payroll = round(sum(c.daily_wage for c in active_contracts), 2)
    total_wages_cumulative = round(sum(c.total_wages_paid for c in all_contracts), 2)

    contract_items = [
        {
            "contract_id": c.contract_id,
            "employee_uid": str(c.employee_uid),
            "employer_uid": str(c.employer_uid),
            "business_id": c.business_id,
            "title": c.title,
            "daily_wage": c.daily_wage,
            "contract_type": c.contract_type.value if hasattr(c.contract_type, "value") else str(c.contract_type),
            "location_id": c.location_id,
            "start_tick": c.start_tick,
            "end_tick": c.end_tick,
            "is_active": c.is_active,
            "total_wages_paid": round(c.total_wages_paid, 2),
            "missed_paydays": c.missed_paydays,
            "termination_reason": c.termination_reason,
        }
        for c in all_contracts
    ]

    return {
        "total_contracts": len(all_contracts),
        "active_contracts_count": len(active_contracts),
        "daily_payroll_liability_usd": total_active_payroll,
        "total_wages_paid_cumulative_usd": total_wages_cumulative,
        "informal_day_labor_records": len(getattr(lm, "_informal_day_labor_log", [])),
        "contracts": contract_items,
    }


@router.get("/housing/units")
def get_housing_units() -> dict[str, Any]:
    """Return housing stock, tenure conditions, capacity and occupancy."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    he = getattr(runner, "housing_engine", None)
    if not he:
        return {"total_units": 0, "units": []}

    units = he.get_all_units()
    total_capacity = sum(u.capacity for u in units)
    total_occupancy = sum(u.current_occupancy for u in units)
    occupancy_rate = round(total_occupancy / total_capacity, 3) if total_capacity > 0 else 0.0

    tenure_distribution: dict[str, int] = {}
    for u in units:
        t_val = u.tenure_type.value if hasattr(u.tenure_type, "value") else str(u.tenure_type)
        tenure_distribution[t_val] = tenure_distribution.get(t_val, 0) + u.current_occupancy

    unit_items = [
        {
            "unit_id": u.unit_id,
            "name": u.name,
            "location_id": u.location_id,
            "tenure_type": u.tenure_type.value if hasattr(u.tenure_type, "value") else str(u.tenure_type),
            "capacity": u.capacity,
            "current_occupancy": u.current_occupancy,
            "has_vacancy": u.has_vacancy,
            "rent_per_day": u.rent_per_day,
            "owner_uid": str(u.owner_uid) if u.owner_uid else None,
            "occupant_uids": u.occupant_uids,
            "quality_score": round(u.quality_score, 2),
            "arrears_total": round(sum(u.arrears_balance.values()), 2),
        }
        for u in units
    ]

    return {
        "total_units": len(units),
        "total_capacity": total_capacity,
        "total_occupancy": total_occupancy,
        "occupancy_rate": occupancy_rate,
        "tenure_distribution": tenure_distribution,
        "units": unit_items,
    }


@router.get("/housing/leases")
def get_housing_leases() -> dict[str, Any]:
    """Return active and past housing leases and eviction history."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    he = getattr(runner, "housing_engine", None)
    if not he:
        return {"active_leases_count": 0, "leases": [], "evictions": []}

    all_leases = he.get_all_leases()
    active_leases = he.get_active_leases()
    total_rent = round(sum(l.total_rent_paid for l in all_leases), 2)
    total_arrears = round(sum(l.accumulated_arrears for l in active_leases), 2)

    lease_items = [
        {
            "lease_id": l.lease_id,
            "unit_id": l.unit_id,
            "tenant_uid": str(l.tenant_uid),
            "landlord_uid": str(l.landlord_uid) if l.landlord_uid else None,
            "rent_per_day": l.rent_per_day,
            "start_tick": l.start_tick,
            "end_tick": l.end_tick,
            "is_active": l.is_active,
            "total_rent_paid": round(l.total_rent_paid, 2),
            "accumulated_arrears": round(l.accumulated_arrears, 2),
        }
        for l in all_leases
    ]

    return {
        "total_leases": len(all_leases),
        "active_leases_count": len(active_leases),
        "total_rent_collected_usd": total_rent,
        "outstanding_arrears_usd": total_arrears,
        "evictions_count": len(he.eviction_history),
        "eviction_history": he.eviction_history[-20:],
        "leases": lease_items,
    }


@router.get("/commerce/establishments")
def get_commercial_establishments() -> dict[str, Any]:
    """Return commercial establishments, catalog stock, cash box, and verified vs simulated breakdown."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    ce = getattr(runner, "commerce_engine", None)
    if not ce:
        return {"total_establishments": 0, "establishments": []}

    all_est = ce.get_all_establishments()
    verified_real = [e for e in all_est if e.is_verified_real]
    simulated = [e for e in all_est if not e.is_verified_real]

    total_sales = round(sum(e.total_lifetime_revenue for e in all_est), 2)
    daily_sales = round(sum(e.daily_sales_volume_usd for e in all_est), 2)
    total_cash_in_boxes = round(sum(e.cash_box_usd for e in all_est), 2)

    est_items = [
        {
            "establishment_id": e.establishment_id,
            "name": e.name,
            "type": e.establishment_type.value if hasattr(e.establishment_type, "value") else str(e.establishment_type),
            "location_id": e.location_id,
            "is_verified_real": e.is_verified_real,
            "owner_uid": str(e.owner_uid) if e.owner_uid else None,
            "cash_box_usd": round(e.cash_box_usd, 2),
            "daily_sales_volume_usd": round(e.daily_sales_volume_usd, 2),
            "operating_cost_per_day": round(e.operating_cost_per_day, 2),
            "opening_hours": list(e.opening_hours),
            "capacity": e.capacity,
            "reputation": round(e.reputation, 2),
            "daily_visitors": e.daily_visitors,
            "daily_browsers_without_purchase": e.daily_browsers_without_purchase,
            "daily_purchasers": e.daily_purchasers,
            "catalog_count": len(e.catalog),
            "catalog_products": [
                {
                    "product_id": p.product_id,
                    "name": p.name,
                    "category": p.category,
                    "unit_price_usd": round(p.unit_price_usd, 2),
                    "current_stock": round(p.current_stock, 1),
                    "unit_label": p.unit_label,
                }
                for p in list(e.catalog.values())[:10]
            ],
        }
        for e in all_est
    ]

    return {
        "total_establishments": len(all_est),
        "verified_real_count": len(verified_real),
        "simulated_count": len(simulated),
        "daily_sales_volume_usd": daily_sales,
        "lifetime_revenue_usd": total_sales,
        "total_cash_in_boxes_usd": total_cash_in_boxes,
        "establishments": est_items,
    }


@router.get("/commerce/visits")
def get_commercial_visits(limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
    """Return consumer visit records showing browsing without purchase, dining, and shopping outcomes."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    ce = getattr(runner, "commerce_engine", None)
    if not ce:
        return {"total_visits": 0, "visits": []}

    history = ce.visit_history
    browsing_only = [v for v in history if not v.purchased]
    purchases = [v for v in history if v.purchased]

    intent_breakdown: dict[str, int] = {}
    for v in history:
        i_val = v.intent.value if hasattr(v.intent, "value") else str(v.intent)
        intent_breakdown[i_val] = intent_breakdown.get(i_val, 0) + 1

    visit_items = [
        {
            "agent_uid": str(v.agent_uid),
            "establishment_id": v.establishment_id,
            "intent": v.intent.value if hasattr(v.intent, "value") else str(v.intent),
            "purchased": v.purchased,
            "total_spent_usd": round(v.total_spent_usd, 2),
            "items_bought": v.items_bought,
            "reasoning": v.reasoning,
            "social_encounters_count": len(v.social_encounters),
            "information_gained": v.information_gained,
        }
        for v in history[-limit:]
    ]

    return {
        "total_visits": len(history),
        "zero_purchase_visits": len(browsing_only),
        "purchasing_visits": len(purchases),
        "zero_purchase_ratio": round(len(browsing_only) / len(history), 3) if history else 0.0,
        "intent_distribution": intent_breakdown,
        "recent_visits": visit_items,
    }


@router.get("/lifestyle/summary")
def get_lifestyle_summary() -> dict[str, Any]:
    """Return everyday life, leisure, social invitations, and household overhead summary."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    es = getattr(runner, "everyday_social", None)
    inv_history = es.invitations_history if es else []
    accepted = [inv for inv in inv_history if inv.status == "accepted"]
    rejected = [inv for inv in inv_history if inv.status == "rejected"]
    rejection_reasons: dict[str, int] = {}
    for inv in rejected:
        r = inv.rejection_reason or "Unknown"
        rejection_reasons[r] = rejection_reasons.get(r, 0) + 1

    shared_sessions = es.shared_leisure_sessions if es else []

    # Household Ledgers
    hl = getattr(runner, "household_ledgers", {})
    treasury = getattr(runner, "community_utility_treasury", {"balance": 0.0})

    # Population activity breakdown
    activity_counts: dict[str, int] = {}
    for h in runner.population.get_all():
        act = getattr(h.physical_state, "current_activity", None)
        act_name = act.value if hasattr(act, "value") else str(act or "idle")
        activity_counts[act_name] = activity_counts.get(act_name, 0) + 1

    return {
        "social_invitations": {
            "total_sent": len(inv_history),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "acceptance_rate": round(len(accepted) / len(inv_history), 3) if inv_history else 0.0,
            "rejection_reasons": rejection_reasons,
        },
        "shared_leisure_sessions_count": len(shared_sessions),
        "recent_shared_sessions": shared_sessions[-10:],
        "current_activities_distribution": activity_counts,
        "households": {
            "tracked_count": len(hl),
            "community_utility_treasury_usd": round(treasury.get("balance", 0.0), 2),
        },
    }


# -----------------------------------------------------------------------------
# Phase 1.5 Extension: Health, Romance, Accidents, Environment & Causal DAG
# -----------------------------------------------------------------------------

@router.get("/health/facilities")
def get_health_facilities() -> dict[str, Any]:
    """Return healthcare facilities, capacity, triage stats, and population health overview."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    he = getattr(runner, "health_engine", None)
    if not he:
        return {"total_facilities": 0, "facilities": [], "population_active_conditions": 0}

    facilities = []
    for f in he.get_all_facilities():
        facilities.append({
            "facility_id": f.facility_id,
            "name": f.name,
            "facility_type": f.facility_type,
            "location_id": f.location_id,
            "capacity_beds": f.capacity_beds,
            "current_patients_count": len(f.current_patients),
            "waiting_time_ticks": f.waiting_time_ticks,
            "staff_available": f.staff_available,
            "fee_usd": f.fee_usd,
            "total_treated": f.total_patients_treated,
            "total_rejected_capacity": f.total_rejected_capacity,
            "occupancy_rate": round(len(f.current_patients) / max(1, f.capacity_beds), 2),
        })

    active_conditions_count = 0
    category_counts: dict[str, int] = {}
    treated_count = 0
    for h in runner.population.get_all():
        for c in getattr(h, "active_health_conditions", []):
            active_conditions_count += 1
            cat_name = c.category.value if hasattr(c.category, "value") else str(c.category)
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
            if getattr(c, "is_treated", False):
                treated_count += 1

    return {
        "total_facilities": len(facilities),
        "facilities": facilities,
        "population_active_conditions": active_conditions_count,
        "treated_conditions_count": treated_count,
        "condition_categories": category_counts,
        "treatment_history_count": len(he.treatment_history),
    }


@router.get("/romance/relationships")
def get_romance_relationships() -> dict[str, Any]:
    """Return active romantic bonds, stages, dimensions, infidelities, and heartbreak records."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    re = getattr(runner, "romance_engine", None)
    if not re:
        return {"total_relationships": 0, "active_relationships": 0, "relationships": []}

    all_rels = list(re._relationships.values())
    active_rels = [r for r in all_rels if r.is_active]

    stage_breakdown: dict[str, int] = {}
    for r in all_rels:
        s_val = r.stage.value if hasattr(r.stage, "value") else str(r.stage)
        stage_breakdown[s_val] = stage_breakdown.get(s_val, 0) + 1

    rel_items = []
    population_names = {str(h.uid): h.name for h in runner.population.get_all()}
    for r in all_rels:
        rel_items.append({
            "relationship_id": r.relationship_id,
            "partner_a_id": r.partner_a_id,
            "partner_a_name": population_names.get(r.partner_a_id, "Fuera del registro"),
            "partner_b_id": r.partner_b_id,
            "partner_b_name": population_names.get(r.partner_b_id, "Fuera del registro"),
            "stage": r.stage.value if hasattr(r.stage, "value") else str(r.stage),
            "is_active": r.is_active,
            "dates_count": r.dates_count,
            "shared_memories_count": r.shared_memories_count,
            "dims_a": r.dims_a.to_dict(),
            "dims_b": r.dims_b.to_dict(),
            "infidelities_count": len(r.infidelity_history),
            "start_tick": r.start_tick,
            "separation_tick": r.separation_tick,
        })

    return {
        "total_relationships": len(all_rels),
        "active_relationships_count": len(active_rels),
        "stage_distribution": stage_breakdown,
        "total_infidelities": len(re.infidelity_records),
        "total_heartbreaks": len(re.heartbreak_records),
        "relationships": rel_items,
    }


@router.get("/accidents/recent")
def get_accidents_and_disasters(limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
    """Return recent accidents, workplace injuries, and environmental disaster events."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    me = getattr(runner, "misfortune_engine", None)
    if not me:
        return {"total_accidents": 0, "total_disasters": 0, "accidents": [], "disasters": []}

    accidents_data = [a.to_dict() for a in me.accident_history[-limit:]]
    disasters_data = [d.to_dict() for d in me.disaster_history[-limit:]]

    type_counts: dict[str, int] = {}
    for a in me.accident_history:
        t_val = a.accident_type.value if hasattr(a.accident_type, "value") else str(a.accident_type)
        type_counts[t_val] = type_counts.get(t_val, 0) + 1

    return {
        "total_accidents": len(me.accident_history),
        "total_disasters": len(me.disaster_history),
        "blocked_roads": list(me.blocked_roads),
        "accident_type_breakdown": type_counts,
        "recent_accidents": accidents_data,
        "recent_disasters": disasters_data,
    }


@router.get("/environment/hazards")
def get_environmental_hazards() -> dict[str, Any]:
    """Return territorial environmental health, water source potability, waste accumulation, and climate."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    whe = getattr(runner, "world_human_engine", None) or getattr(runner, "world_interaction", None)
    if not whe:
        return {"status": "unavailable"}

    haz = whe.hazards
    water_status = {}
    for src, cleanliness in haz.water_sources.items():
        water_status[src] = {
            "cleanliness_index": round(cleanliness, 2),
            "is_potable": haz.is_water_source_potable(src),
            "status": "potable" if haz.is_water_source_potable(src) else "contaminado",
        }

    me = getattr(runner, "misfortune_engine", None)
    blocked_roads = list(me.blocked_roads) if me else []

    return {
        "rainfall_mm_per_hour": haz.rainfall_mm_per_hour,
        "temperature_celsius": haz.temperature_celsius,
        "humidity_pct": haz.humidity_pct,
        "accumulated_waste_kg": round(haz.accumulated_waste_kg, 1),
        "water_sources": water_status,
        "blocked_roads": blocked_roads,
        "faenas_completed_count": len(whe.faena_records),
        "recent_faenas": whe.faena_records[-5:],
    }


@router.get("/events/causal_tree/{event_id}")
def get_event_causal_tree(event_id: str) -> dict[str, Any]:
    """Query DAG ancestor causes and descendant consequences for an event."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    cg = getattr(runner, "causal_graph", None)
    if not cg:
        raise HTTPException(status_code=404, detail="CausalEventGraph uninitialized")

    node = cg.get_node(event_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found in causal DAG")

    ancestor_chain = [n.to_dict() for n in cg.get_causal_chain(event_id)]
    consequence_tree = [n.to_dict() for n in cg.get_consequence_tree(event_id)]
    explanation = cg.explain_event(event_id)

    return {
        "event_id": event_id,
        "event": node.to_dict(),
        "ancestor_causes": ancestor_chain,
        "descendant_consequences": consequence_tree,
        "explanation": explanation,
    }


@router.get("/health/treatment-history")
def get_health_treatment_history(limit: int = Query(default=50, ge=1, le=200)) -> dict[str, Any]:
    """Return recent clinical treatment records with facility attribution."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    he = getattr(runner, "health_engine", None)
    if not he:
        return {"total_records": 0, "recent_treatments": []}

    facility_names = {f.facility_id: f.name for f in he.get_all_facilities()}
    population_names = {str(h.uid): h.name for h in runner.population.get_all()}
    records = he.treatment_history[-limit:]
    items = []
    for record in reversed(records):
        items.append({
            "record_id": record.record_id,
            "patient_uid": record.patient_uid,
            "patient_name": population_names.get(record.patient_uid, "Fuera del registro"),
            "facility_id": record.facility_id,
            "facility_name": facility_names.get(record.facility_id, record.facility_id),
            "condition_name": record.condition_name,
            "tick": record.tick,
            "fee_charged_usd": record.fee_charged_usd,
            "outcome": record.outcome,
        })

    return {
        "total_records": len(he.treatment_history),
        "recent_treatments": items,
    }


@router.get("/family/overview")
def get_family_overview(limit: int = Query(default=30, ge=1, le=200)) -> dict[str, Any]:
    """Return households, births, deaths, pregnancies and elder-care state.

    These are backend lifecycle transitions owned by the integrated
    ``LifeEventsCoordinator``; the endpoint never synthesises births, deaths or
    care events that did not occur in the DAG.
    """
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    extension = getattr(runner, "extension", None)
    life = getattr(extension, "life_events", None) if extension is not None else None
    if life is None:
        return {
            "households_count": 0,
            "households": [],
            "births_count": 0,
            "deaths_count": 0,
            "active_pregnancies": 0,
            "recent_births": [],
            "recent_deaths": [],
            "recent_elder_care": [],
        }

    population = runner.population

    households = []
    for household in life.households.all_households():
        member_items = []
        for uid in sorted(household.members, key=str):
            human = population.get_optional(uid)
            member_items.append({
                "uid": str(uid),
                "name": human.name if human is not None else "Fallecido / fuera del registro",
                "age": human.demographics.age if human is not None else None,
                "is_head": household.head_of_household == uid,
                "is_dependent": uid in household.dependents,
                "caregiver_uid": str(household.caregiver_assignments[uid])
                if uid in household.caregiver_assignments else None,
            })
        households.append({
            "household_id": household.household_id,
            "name": household.name,
            "residence_location_id": household.residence_location_id,
            "member_count": len(household.members),
            "shared_funds": household.shared_funds,
            "members": member_items,
        })

    pregnancies = []
    for mother_uid, pregnancy in life.pregnancies.items():
        mother = population.get_optional(uuid.UUID(str(mother_uid)))
        pregnancies.append({
            "mother_uid": str(mother_uid),
            "mother_name": mother.name if mother is not None else "Desconocida",
            "father_uid": str(pregnancy.father_uid) if pregnancy.father_uid else None,
            "start_tick": pregnancy.start_tick,
            "gestation_duration_ticks": pregnancy.gestation_duration_ticks,
            "progress": round(getattr(pregnancy, "progress", 0.0), 3),
        })

    return {
        "households_count": len(households),
        "households": households,
        "births_count": len(life.births_history),
        "deaths_count": len(life.deaths_history),
        "active_pregnancies": len(life.pregnancies),
        "pregnancies": pregnancies,
        "recent_births": list(reversed(life.births_history[-limit:])),
        "recent_deaths": list(reversed(life.deaths_history[-limit:])),
        "recent_elder_care": list(reversed(life.elder_care_history[-limit:])),
        "life_course_stats": {
            "births": int(getattr(extension, "stats", {}).get("births", 0)),
            "deaths": int(getattr(extension, "stats", {}).get("deaths", 0)),
        },
    }


@router.get("/events/causal/recent")
def get_recent_causal_nodes(
    limit: int = Query(default=50, ge=1, le=200),
    min_importance: float = Query(default=0.0, ge=0.0, le=1.0),
) -> dict[str, Any]:
    """Return the most recent causal DAG nodes for the observability timeline."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")

    cg = getattr(runner, "causal_graph", None)
    if not cg:
        return {"total_nodes": 0, "nodes": []}

    nodes = cg.recent_nodes(limit=limit, min_importance=min_importance)
    return {
        "total_nodes": len(cg._nodes),
        "nodes": [n.to_dict() for n in nodes],
    }


# -----------------------------------------------------------------------------
# Phase 1.6: Perception & Ingested OSM Geography
# -----------------------------------------------------------------------------

_geography_instance: Optional[IngestedGeography] = None
_network_cache: dict[str, Any] = {}


def _geography() -> IngestedGeography:
    """Return the lazily loaded normalized OSM geography database."""
    global _geography_instance
    if _geography_instance is None:
        _geography_instance = IngestedGeography()
    return _geography_instance


@router.get("/perception/overview")
def get_perception_overview() -> dict[str, Any]:
    """Aggregate perception telemetry for the whole population."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        return {"available": False}
    engine = getattr(runner, "perception", None)
    if engine is None:
        return {"available": False}
    snapshots = list(engine.snapshots.values())
    observed = [s for s in snapshots if s.total_observations > 0]
    return {
        "available": True,
        "model": "structured_detection_v1",
        "individuals_with_perception": len(observed),
        "population": runner.population.count,
        "observations_total": sum(s.total_observations for s in snapshots),
        "misunderstandings_total": sum(s.total_misunderstandings for s in snapshots),
        "known_entities_total": sum(len(s.known_entities) for s in snapshots),
        "mean_acuity": {
            "visual": round(
                sum(s.acuity.visual for s in observed) / len(observed), 3
            ) if observed else 0.0,
            "auditory": round(
                sum(s.acuity.auditory for s in observed) / len(observed), 3
            ) if observed else 0.0,
        },
        "engine_stats": dict(getattr(engine, "stats", {})),
    }


@router.get("/individuals/{uid}/perception")
def get_individual_perception(uid: str) -> dict[str, Any]:
    """Return the subjective perceptual state of one individual."""
    ctrl = get_controller()
    runner = ctrl.runner
    if runner is None:
        raise HTTPException(status_code=500, detail="Runner uninitialized")
    engine = getattr(runner, "perception", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="Perception engine unavailable")

    target = None
    for h in runner.population.get_all():
        if str(h.uid) == uid or str(h.identity.serial) == uid:
            target = h
            break
    if target is None:
        raise HTTPException(status_code=404, detail=f"Individual '{uid}' not found.")

    summary = engine.get_snapshot(str(target.uid)).summary()
    summary["identity"] = {"uid": str(target.uid), "name": target.name, "serial": target.identity.serial}
    return summary


@router.get("/geography/manifest")
def get_geography_manifest() -> dict[str, Any]:
    """Return OSM ingestion provenance, layer coverage and attribution."""
    return _geography().manifest()


@router.get("/geography/geojson")
def get_geography_geojson(
    min_lon: float = Query(..., ge=-180.0, le=180.0),
    min_lat: float = Query(..., ge=-90.0, le=90.0),
    max_lon: float = Query(..., ge=-180.0, le=180.0),
    max_lat: float = Query(..., ge=-90.0, le=90.0),
    layers: str = Query(default="roads,buildings"),
    limit: int = Query(default=3000, ge=1, le=6000),
) -> dict[str, Any]:
    """Return viewport geometry as GeoJSON for the world map.

    The response is a standard ``FeatureCollection`` so MapLibre can consume
    it directly; every feature carries its layer, class, validation state and
    license, and the collection carries the ODbL attribution.
    """
    requested = tuple(item.strip() for item in layers.split(",") if item.strip())
    allowed = {"roads", "buildings"}
    unknown = sorted(set(requested) - allowed)
    if unknown:
        raise HTTPException(status_code=400, detail=f"unsupported layers: {', '.join(unknown)}")
    return _geography().geojson(
        (min_lon, min_lat, max_lon, max_lat),
        layers=requested or ("roads",),
        limit=limit,
    )


@router.get("/geography/features")
def get_geography_features(
    min_lon: float = Query(..., ge=-180.0, le=180.0),
    min_lat: float = Query(..., ge=-90.0, le=90.0),
    max_lon: float = Query(..., ge=-180.0, le=180.0),
    max_lat: float = Query(..., ge=-90.0, le=90.0),
    layer: Optional[str] = Query(default=None),
    feature_class: Optional[str] = Query(default=None),
    limit: int = Query(default=400, ge=1, le=3000),
    include_geometry: bool = Query(default=True),
) -> dict[str, Any]:
    """Return normalized OSM features intersecting a WGS84 bounding box."""
    geography = _geography()
    features = geography.features_in_bbox(
        (min_lon, min_lat, max_lon, max_lat),
        layer=layer,
        feature_class=feature_class,
        limit=limit,
        include_geometry=include_geometry,
    )
    return {
        "available": geography.available,
        "count": len(features),
        "features": features,
        "attribution": "© OpenStreetMap contributors, ODbL 1.0",
    }


@router.get("/geography/route")
def get_geography_route(
    from_lat: float = Query(..., ge=-90.0, le=90.0),
    from_lon: float = Query(..., ge=-180.0, le=180.0),
    to_lat: float = Query(..., ge=-90.0, le=90.0),
    to_lon: float = Query(..., ge=-180.0, le=180.0),
    mode: str = Query(default="walk"),
    bbox_pad: float = Query(default=0.01, ge=0.0, le=0.2),
) -> dict[str, Any]:
    """Route over the real OSM road network between two WGS84 points."""
    geography = _geography()
    if not geography.available:
        return {
            "found": False,
            "reason": "geography_not_ingested",
            "hint": "Run: python -m saltbor.datasets.gis.pipeline --download",
        }
    bbox = (
        min(from_lon, to_lon) - bbox_pad,
        min(from_lat, to_lat) - bbox_pad,
        max(from_lon, to_lon) + bbox_pad,
        max(from_lat, to_lat) + bbox_pad,
    )
    cache_key = ",".join(f"{v:.4f}" for v in bbox)
    network = _network_cache.get(cache_key)
    if network is None:
        network = OSMRoadNetwork.from_geography(geography, bbox)
        if len(_network_cache) > 8:
            _network_cache.clear()
        _network_cache[cache_key] = network
    return network.route((from_lat, from_lon), (to_lat, to_lon), mode=mode).to_dict()


@router.get("/geography/ecological_profile")
def get_ecological_profile(
    min_lon: float = Query(..., ge=-180.0, le=180.0),
    min_lat: float = Query(..., ge=-90.0, le=90.0),
    max_lon: float = Query(..., ge=-180.0, le=180.0),
    max_lat: float = Query(..., ge=-90.0, le=90.0),
) -> dict[str, Any]:
    """Land-cover and infrastructure composition of a territory from OSM."""
    return _geography().ecological_profile((min_lon, min_lat, max_lon, max_lat))





