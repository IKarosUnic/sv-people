"""Integrated runtime orchestration for the Phase 1.5 extension domains.

The component engines (health, romance, misfortune, world interaction, family
caregiving) are deliberately independent.  This module is the single place
that connects them to the live tick loop so that their state transitions are
causal, observable and reproducible instead of being decorative data.

Every step here follows the same rule: an event is emitted *after* the
backend state transition that it describes.  UI panels therefore never render
an event that has not actually happened in the simulation.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional

import numpy as np

from saltbor.core.types import (
    ActivityType,
    ConditionCategory,
    DisasterType,
    HousingTenureType,
    RomanceStage,
    Tick,
)
from saltbor.events.types import EventType, SimulationEvent
from saltbor.lifecycle.life_events import LifeEventsCoordinator

logger = logging.getLogger(__name__)

# Local-map centre used for the Suchitoto-inspired synthetic settlement.
_CENTER_LAT = 13.9350
_CENTER_LON = -89.0280

# Deterministic location groups used by contextual disasters.
_FLOOD_PRONE_LOCATIONS = [
    "casa_sur_1",
    "mercado_central",
    "plaza_central",
    "casa_comunal",
    "quebrada_el_zapote",
]
_LANDSLIDE_PRONE_LOCATIONS = [
    "casa_norte_1",
    "cuesta_el_calvario",
    "cerro_guazapa",
    "camino_puente_suchitoto",
]

# Daily occupational hazard by broad occupation label.
_OCCUPATION_HAZARD = {
    "agricultor": 0.85,
    "jornalero": 0.85,
    "albañil": 0.90,
    "albanil": 0.90,
    "carpintero": 0.65,
    "mecánico": 0.60,
    "mecanico": 0.60,
    "cocinero": 0.35,
    "pupusera": 0.30,
    "comerciante": 0.18,
    "vendedor": 0.18,
    "maestro": 0.08,
    "enfermero": 0.10,
}


class ExtensionRuntime:
    """Owns the daily orchestration of health, romance, misfortune and family life."""

    def __init__(self, runner: Any) -> None:
        self.runner = runner
        config = getattr(runner, "config", None)
        seed = getattr(config, "random_seed", None)
        self._rng = np.random.default_rng(seed + 1515 if seed is not None else None)
        self.life_events = LifeEventsCoordinator(
            config=config,
            seed=(seed + 515) if seed is not None else None,
        )

        # Tunable rates.  Experiments may raise these to force a pathway, but
        # the defaults keep ordinary runs plausible.
        self.romance_formation_probability = 0.24
        self.courtship_probability = 0.30
        self.relationship_dynamics_probability = 0.90
        self.infidelity_opportunity_probability = 0.22
        self.discovery_probability = 0.55
        self.reconciliation_probability = 0.30
        self.traffic_accident_scale = 0.15
        self.work_accident_scale = 0.05
        self.domestic_accident_scale = 1.0
        self.theft_probability = 0.025
        self.disaster_base_probability = 0.020
        self.treatment_seek_probability = 0.80
        self.max_romance_pairs_per_day = 150
        self.max_unrequited_checks_per_day = 30

        # Phase 1.6 perception: every N ticks, each living individual refreshes
        # what they actually noticed.  Running it every tick would multiply the
        # cost of a subsystem that is dominated by attention capacity, not by
        # world detail, so two ticks is the documented default (30 simulated
        # minutes of perceptual refresh).
        self.perception_interval_ticks = 2
        self.max_co_located_perceived = 6

        self._initialized = False
        self._last_daily_tick = -1
        self._last_exposure_day = -1
        self._last_treatment_day = -1
        self._last_romance_day = -1
        self._last_theft_day = -1
        self._last_domestic_day = -1
        self._last_commute_day = -1
        self._last_work_day = -1
        self._disaster_cooldown_until = 0
        self._displaced_home_locations: dict[str, str] = {}
        self._displaced_tenure: dict[str, Any] = {}
        self._recovery_started: set[str] = set()
        self._unaffordable_reported: set[str] = set()
        self.stats = {
            "water_exposures": 0,
            "heat_exposures": 0,
            "vector_exposures": 0,
            "treatments": 0,
            "accidents": 0,
            "thefts": 0,
            "disasters": 0,
            "romances_started": 0,
            "dates": 0,
            "infidelities": 0,
            "discoveries": 0,
            "births": 0,
            "deaths": 0,
            "perception_rounds": 0,
            "perception_observations": 0,
            "hazards_perceived": 0,
            "misunderstandings": 0,
        }

    # ------------------------------------------------------------------
    # Coordinates and provenance
    # ------------------------------------------------------------------

    def coordinates_for(self, location_id: Optional[str]) -> tuple[float, float]:
        """Return deterministic WGS84 coordinates for a local-map location.

        These are explicitly synthetic local-map coordinates, not a claim that
        the simulated building exists at that real-world address.
        """
        if not location_id:
            return (_CENTER_LAT, _CENTER_LON)
        locations = getattr(self.runner, "locations", None)
        loc = locations.get_optional(location_id) if locations is not None else None
        if loc is None:
            return (_CENTER_LAT, _CENTER_LON)
        x, y = loc.position
        width = float(getattr(self.runner.config, "world_width", 500.0) or 500.0)
        height = float(getattr(self.runner.config, "world_height", 500.0) or 500.0)
        lat = _CENTER_LAT + ((y - height / 2.0) / 111_320.0)
        lon = _CENTER_LON + ((x - width / 2.0) / (111_320.0 * math.cos(math.radians(_CENTER_LAT))))
        return (round(lat, 6), round(lon, 6))

    def provenance_for(self, location_id: Optional[str]) -> str:
        engine = getattr(self.runner, "world_interaction", None)
        if engine is None or not location_id:
            return "synthetic_local_map"
        obj_type = engine.classify_object(location_id)
        return obj_type.value if hasattr(obj_type, "value") else str(obj_type)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self, load_existing: bool = False) -> None:
        """Restore extension state or reconstruct initial union/household state."""
        state_repo = getattr(self.runner, "state_repo", None)
        if load_existing and state_repo is not None:
            data = state_repo.load_state("phase15_extension")
            if data:
                self.load_dict(data)
                self._initialized = True
                logger.info("Phase 1.5 extension state restored from checkpoint.")
                return

        self.life_events.sync(
            population=self.runner.population,
            social_engine=self.runner.social,
            romance_engine=self.runner.romance_engine,
            current_tick=self.runner.clock.current_tick,
            identity_factory=self.runner.identity_factory,
        )
        self._initialized = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize all extension domain state into one checkpoint document."""
        return {
            "health": self.runner.health_engine.to_dict(),
            "misfortune": self.runner.misfortune_engine.to_dict(),
            "romance": self.runner.romance_engine.to_dict(),
            "world_interaction": self.runner.world_interaction.to_dict(),
            "perception": self.runner.perception.to_dict(),
            "psychology": self.runner.psychology.to_dict(),
            "life_events": self.life_events.to_dict(),
            "caregiving_history": list(self.runner.family_caregiving.caregiving_history),
            "causal_graph": self.runner.causal_graph.to_dict(),
            "last_daily_tick": self._last_daily_tick,
            "last_exposure_day": self._last_exposure_day,
            "last_treatment_day": self._last_treatment_day,
            "last_romance_day": self._last_romance_day,
            "last_theft_day": self._last_theft_day,
            "last_domestic_day": self._last_domestic_day,
            "disaster_cooldown_until": self._disaster_cooldown_until,
            "displaced_home_locations": dict(self._displaced_home_locations),
            "recovery_started": sorted(self._recovery_started),
            "stats": dict(self.stats),
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        """Restore every extension engine from a checkpoint document."""
        if data.get("health"):
            self.runner.health_engine.load_dict(data["health"])
        if data.get("misfortune"):
            self.runner.misfortune_engine.load_dict(data["misfortune"])
        if data.get("romance"):
            self.runner.romance_engine.load_dict(data["romance"])
        if data.get("world_interaction"):
            self.runner.world_interaction.load_dict(data["world_interaction"])
        if data.get("perception"):
            self.runner.perception.load_dict(data["perception"])
        if data.get("psychology"):
            self.runner.psychology.load_dict(data["psychology"])
            for human in self.runner.population.get_all():
                self.runner.psychology.ensure(human)
            self.runner._psych_event_cursor = len(
                getattr(self.runner.event_bus, "event_log", [])
            )
        if data.get("life_events"):
            self.life_events.load_dict(data["life_events"])
            self.life_events._identity_factory = self.runner.identity_factory
            self.life_events._population = self.runner.population
        if data.get("causal_graph"):
            self.runner.causal_graph.load_dict(data["causal_graph"])
        if "caregiving_history" in data:
            self.runner.family_caregiving.caregiving_history = list(data["caregiving_history"])

        self._last_daily_tick = int(data.get("last_daily_tick", -1))
        self._last_exposure_day = int(data.get("last_exposure_day", -1))
        self._last_treatment_day = int(data.get("last_treatment_day", -1))
        self._last_romance_day = int(data.get("last_romance_day", -1))
        self._last_theft_day = int(data.get("last_theft_day", -1))
        self._last_domestic_day = int(data.get("last_domestic_day", -1))
        self._disaster_cooldown_until = int(data.get("disaster_cooldown_until", 0))
        self._displaced_home_locations = {
            str(k): str(v) for k, v in data.get("displaced_home_locations", {}).items()
        }
        self._recovery_started = {str(x) for x in data.get("recovery_started", [])}
        self.stats.update({str(k): v for k, v in data.get("stats", {}).items()})
        self._sync_relationship_state()
        self.life_events._refresh_family_links(self.runner.population)

    # ------------------------------------------------------------------
    # Per-tick and daily orchestration
    # ------------------------------------------------------------------

    def step_individual(self, human: Any, current_tick: Tick) -> None:
        """Advance biological and emotional trajectories for one living human."""
        location_id = getattr(human.physical_state, "current_location_id", None)
        coords = self.coordinates_for(location_id)
        self.runner.health_engine.step_individual_health(
            human,
            current_tick,
            event_bus=self.runner.event_bus,
            causal_graph=self.runner.causal_graph,
            location_id=location_id,
            coordinates=coords,
        )
        self.runner.romance_engine.step_heartbreak_recovery(
            human,
            current_tick,
            event_bus=self.runner.event_bus,
            causal_graph=self.runner.causal_graph,
        )

    def step(self, current_tick: Tick) -> None:
        """Global extension step, called once per tick after human updates."""
        if not self._initialized:
            return

        self.sync_environment(current_tick)

        hour = self.runner.clock.current_hour_int

        # Perception: the epistemic boundary between world state and cognition.
        if current_tick % self.perception_interval_ticks == 0:
            self._perception_round(current_tick, hour)
        day = current_tick // self.runner.config.ticks_per_day

        if hour == 7 and self._last_commute_day != day:
            self._last_commute_day = day
            self._commute_round(current_tick)

        if hour == 8 and self._last_exposure_day != day:
            self._last_exposure_day = day
            self._exposure_round(current_tick)

        if hour == 10 and self._last_treatment_day != day:
            self._last_treatment_day = day
            self._treatment_round(current_tick)

        if hour == 11 and self._last_work_day != day:
            self._last_work_day = day
            self._work_round(current_tick)

        if hour == 18:
            self._airborne_round(current_tick)

        if hour == 19 and self._last_romance_day != day:
            self._last_romance_day = day
            self._romance_round(current_tick)

        if hour == 20 and self._last_theft_day != day:
            self._last_theft_day = day
            self._theft_round(current_tick)

        if hour == 21 and self._last_domestic_day != day:
            self._last_domestic_day = day
            self._domestic_round(current_tick)

        # Contextual disaster checks every hour; a running disaster suppresses
        # further triggering until recovery.
        if current_tick % 4 == 0:
            self.trigger_contextual_disaster(current_tick, force=False)

        # Daily integrated life-course transition at the day boundary.
        if current_tick % self.runner.config.ticks_per_day == 0 and self._last_daily_tick != current_tick:
            self._last_daily_tick = current_tick
            self._daily_life_round(current_tick)

    # ------------------------------------------------------------------
    # Perception
    # ------------------------------------------------------------------

    def _perception_round(self, current_tick: Tick, hour: int) -> None:
        """Refresh every individual's perceptual state and record salient percepts.

        Perception is a *per-individual* operation, never a population-wide
        omniscient scan: each person only perceives what their own location,
        acuity and attention support.
        """
        engine = self.runner.perception
        locations = self.runner.locations
        environment = getattr(self.runner.environment, "state", None)
        hazards = self.runner.world_interaction.hazards
        self.stats["perception_rounds"] += 1

        for human in list(self.runner.population.get_all()):
            loc_id = getattr(human.physical_state, "current_location_id", None)
            co_located: list[Any] = []
            if loc_id:
                co_located = [
                    other for other in self.runner.population.get_at_location(loc_id)
                    if other.uid != human.uid
                ]
            before = engine.get_snapshot(str(human.uid)).total_observations
            snapshot = engine.perceive(
                human,
                tick=current_tick,
                locations=locations,
                co_located_humans=co_located,
                environment_state=environment,
                hazards=hazards,
                social_engine=self.runner.social,
                max_others=self.max_co_located_perceived,
                hour=hour,
            )
            observed = snapshot.total_observations - before
            self.stats["perception_observations"] += max(0, observed)

            # Emit only percepts that are actually socially/historically
            # relevant; a full observation log would swamp the event bus.
            for observation, interpretation in self._todays_percepts(snapshot, current_tick):
                if observation.target_kind.value == "hazard" and observation.salience >= 0.45:
                    self.stats["hazards_perceived"] += 1
                    self._emit_perception_event(
                        human, observation, interpretation, current_tick,
                        EventType.HAZARD_PERCEIVED, importance=0.55,
                    )
                elif interpretation.is_misunderstanding and observation.clarity > 0.25:
                    self.stats["misunderstandings"] += 1
                    self._emit_perception_event(
                        human, observation, interpretation, current_tick,
                        EventType.MISUNDERSTANDING_OCCURRED, importance=0.40,
                    )
                elif (
                    observation.target_kind.value == "human"
                    and observation.attributes.get("identity_resolved")
                    and observation.clarity >= 0.72
                ):
                    self._emit_perception_event(
                        human, observation, interpretation, current_tick,
                        EventType.PERCEPTION_OBTAINED, importance=0.30,
                    )

    def _todays_percepts(self, snapshot: Any, current_tick: Tick) -> list[tuple[Any, Any]]:
        """Pair this tick's observations with their interpretations."""
        by_observation = {
            interp.observation_id: interp for interp in snapshot.interpretations
        }
        pairs = []
        for observation in snapshot.observations:
            if observation.tick != current_tick:
                continue
            interp = by_observation.get(observation.observation_id)
            if interp is not None:
                pairs.append((observation, interp))
        return pairs[-6:]

    def _emit_perception_event(
        self,
        human: Any,
        observation: Any,
        interpretation: Any,
        current_tick: Tick,
        event_type: EventType,
        importance: float,
    ) -> None:
        coordinates = self.coordinates_for(getattr(human.physical_state, "current_location_id", None))
        event = SimulationEvent(
            event_type=event_type,
            tick=current_tick,
            source_human_id=human.uid,
            location_id=getattr(human.physical_state, "current_location_id", None),
            coordinates=coordinates,
            data={
                "target_kind": observation.target_kind.value,
                "target_id": observation.target_id,
                "channel": observation.channel.value,
                "clarity": round(observation.clarity, 3),
                "claim": interpretation.claim,
                "confidence": interpretation.confidence,
                "biases": list(interpretation.biases_applied),
                "alternatives": list(interpretation.alternative_readings),
                "coordinate_provenance": "synthetic_local_map",
            },
            importance=importance,
        )
        self.runner.event_bus.emit(event)

    # ------------------------------------------------------------------
    # Environment
    # ------------------------------------------------------------------

    def sync_environment(self, current_tick: Tick) -> None:
        """Copy live weather into the territorial hazard profile."""
        env_state = getattr(self.runner.environment, "state", None)
        hazard = self.runner.world_interaction.hazards
        if env_state is None:
            return

        rainfall = float(getattr(env_state, "rainfall_mm_per_hour", 0.0) or 0.0)
        soil = float(getattr(env_state, "soil_moisture", 0.5) or 0.5)
        temperature = float(getattr(env_state, "temperature_celsius", 27.5) or 27.5)
        season = getattr(env_state, "season", None)
        season_name = getattr(season, "value", None) or str(season or hazard.season_name)

        hazard.rainfall_mm_per_hour = rainfall
        hazard.temperature_celsius = temperature
        hazard.season_name = season_name
        hazard.humidity_pct = round(min(98.0, 55.0 + rainfall * 0.8 + soil * 20.0), 1)
        hazard.flood_risk_level = round(
            max(0.02, min(1.0, 0.03 + rainfall / 70.0 + soil * 0.35)), 2
        )
        hazard.landslide_risk_level = round(
            max(0.02, min(1.0, 0.02 + rainfall / 90.0 + soil * 0.45)), 2
        )
        hazard.is_drought = "seca" in season_name.lower() and rainfall <= 0.0

    # ------------------------------------------------------------------
    # Health exposure, transmission and treatment
    # ------------------------------------------------------------------

    def _exposure_round(self, current_tick: Tick) -> None:
        hazard = self.runner.world_interaction.hazards
        for human in list(self.runner.population.get_all()):
            home = str(getattr(human.physical_state, "home_location_id", None) or "casa_norte_1")
            source = self.life_events.water_source_by_home.get(home) or self.life_events._water_source_for_home(home)
            coords = self.coordinates_for(home)
            if self.runner.world_interaction.evaluate_water_consumption_risk(
                human,
                source,
                current_tick,
                health_engine=self.runner.health_engine,
                event_bus=self.runner.event_bus,
                causal_graph=self.runner.causal_graph,
                coordinates=coords,
            ):
                self.stats["water_exposures"] += 1

            # Heat exhaustion is contextual: high temperature + outdoor exposure.
            if hazard.temperature_celsius >= 32.5:
                loc_id = getattr(human.physical_state, "current_location_id", None)
                loc = self.runner.locations.get_optional(loc_id) if loc_id else None
                is_outdoor = bool(getattr(loc, "is_outdoor", False)) if loc else False
                if is_outdoor or getattr(human.physical_state, "current_activity", None) == ActivityType.WORK:
                    heat_prob = min(0.055, (hazard.temperature_celsius - 32.0) * 0.012)
                    if self._rng.random() < heat_prob and not self._has_condition(human, "Golpe de Calor"):
                        condition = self.runner.health_engine.create_heat_exhaustion(tick=current_tick)
                        human.active_health_conditions.append(condition)
                        self._emit_condition_event(human, condition, current_tick, "exposure:heat", coords)
                        self.stats["heat_exposures"] += 1

            # Vector-borne risk rises in the rainy season with standing water.
            if "lluvios" in hazard.season_name.lower() or hazard.rainfall_mm_per_hour > 0.0:
                vector_prob = min(0.020, 0.004 + hazard.accumulated_waste_kg / 80_000.0)
                if self._rng.random() < vector_prob and not self._has_condition(human, "Dengue"):
                    condition = self.runner.health_engine.create_vector_borne_illness(tick=current_tick)
                    human.active_health_conditions.append(condition)
                    self._emit_condition_event(human, condition, current_tick, "exposure:vector", coords)
                    self.stats["vector_exposures"] += 1

    def _emit_condition_event(
        self,
        human: Any,
        condition: Any,
        current_tick: Tick,
        origin: str,
        coordinates: tuple[float, float],
    ) -> None:
        location_id = getattr(human.physical_state, "current_location_id", None)
        event = SimulationEvent(
            event_type=EventType.ILLNESS_CONTRACTED,
            tick=current_tick,
            source_human_id=human.uid,
            location_id=location_id,
            coordinates=coordinates,
            data={
                "condition_id": condition.condition_id,
                "condition": condition.name,
                "category": condition.category.value if hasattr(condition.category, "value") else str(condition.category),
                "severity": condition.severity,
                "origin": origin,
                "coordinate_provenance": "synthetic_local_map",
            },
            importance=0.72,
        )
        self.runner.event_bus.emit(event)
        self.runner.causal_graph.add_event(event, description=f"{human.name} desarrolló {condition.name} por {origin}")

    @staticmethod
    def _has_condition(human: Any, name_fragment: str) -> bool:
        return any(name_fragment.lower() in getattr(c, "name", "").lower() for c in getattr(human, "active_health_conditions", []))

    def _airborne_round(self, current_tick: Tick) -> None:
        groups: dict[str, list[Any]] = {}
        for human in self.runner.population.get_all():
            loc = getattr(human.physical_state, "current_location_id", None)
            if loc:
                groups.setdefault(loc, []).append(human)

        for loc_id, members in groups.items():
            if len(members) < 2:
                continue
            coords = self.coordinates_for(loc_id)
            for infected in members:
                contagious = [
                    c for c in getattr(infected, "active_health_conditions", [])
                    if getattr(c, "is_contagious", False) and not getattr(c, "is_incubating", False)
                ]
                if not contagious:
                    continue
                others = [m for m in members if m.uid != infected.uid]
                self.runner.health_engine.simulate_airborne_contagion(
                    infected,
                    others,
                    current_tick,
                    event_bus=self.runner.event_bus,
                    causal_graph=self.runner.causal_graph,
                    location_id=loc_id,
                    coordinates=coords,
                )

    def _treatment_round(self, current_tick: Tick) -> None:
        facilities = [
            f for f in self.runner.health_engine.get_all_facilities()
            if f.is_open_at_hour(self.runner.clock.current_hour_int)
        ]
        if not facilities:
            return

        for human in list(self.runner.population.get_all()):
            active = list(getattr(human, "active_health_conditions", []))
            untreated = [c for c in active if not getattr(c, "is_treated", False)]
            if not untreated:
                continue

            affordable = [f for f in facilities if human.physical_state.money >= f.fee_usd]
            if not affordable:
                marker = f"{human.uid}:{current_tick // self.runner.config.ticks_per_day}"
                if marker not in self._unaffordable_reported:
                    self._unaffordable_reported.add(marker)
                    self._emit_seek_event(
                        human,
                        current_tick,
                        facility=None,
                        outcome="unaffordable",
                        reason="Ingreso insuficiente para la cuota de atención",
                    )
                continue

            severity = max(float(getattr(c, "severity", 0.0)) for c in untreated)
            seek_chance = 1.0 if severity >= 0.65 else self.treatment_seek_probability
            if self._rng.random() >= seek_chance:
                continue

            facility = min(affordable, key=lambda f: self._distance_to(human, f))
            result = self.runner.health_engine.seek_medical_treatment(
                human,
                facility.facility_id,
                current_tick,
                event_bus=self.runner.event_bus,
                causal_graph=self.runner.causal_graph,
                current_hour=self.runner.clock.current_hour_int,
            )
            if result.get("success"):
                self.stats["treatments"] += 1
            elif "capacity" in str(result.get("reason", "")).lower():
                continue

    def _distance_to(self, human: Any, facility: Any) -> float:
        loc_id = getattr(human.physical_state, "current_location_id", None)
        hx, hy = self.coordinates_for(loc_id)
        fx, fy = facility.coordinates
        return (hx - fx) ** 2 + (hy - fy) ** 2

    def _emit_seek_event(
        self,
        human: Any,
        current_tick: Tick,
        facility: Optional[Any],
        outcome: str,
        reason: str,
    ) -> None:
        coordinates = facility.coordinates if facility else self.coordinates_for(
            getattr(human.physical_state, "current_location_id", None)
        )
        event = SimulationEvent(
            event_type=EventType.HEALTH_TREATMENT_SEEKED,
            tick=current_tick,
            source_human_id=human.uid,
            location_id=facility.location_id if facility else getattr(human.physical_state, "current_location_id", None),
            coordinates=coordinates,
            data={
                "facility_id": facility.facility_id if facility else None,
                "outcome": outcome,
                "reason": reason,
                "coordinate_provenance": "verified_facility" if facility else "synthetic_local_map",
            },
            importance=0.55,
        )
        self.runner.event_bus.emit(event)
        self.runner.causal_graph.add_event(event, description=f"{human.name}: {outcome} ({reason})")

    # ------------------------------------------------------------------
    # Accidents, theft and disasters
    # ------------------------------------------------------------------

    def _commute_round(self, current_tick: Tick) -> None:
        env_state = getattr(self.runner.environment, "state", None)
        if env_state is None:
            return
        for human in list(self.runner.population.get_all()):
            if getattr(human.physical_state, "current_activity", None) != ActivityType.TRAVEL:
                continue
            loc_id = getattr(human.physical_state, "current_location_id", None) or "carretera_los_chorros"
            accident = self.runner.misfortune_engine.evaluate_traffic_accident(
                human,
                road_id=loc_id,
                weather_state=env_state,
                current_tick=current_tick,
                health_engine=self.runner.health_engine,
                event_bus=self.runner.event_bus,
                causal_graph=self.runner.causal_graph,
                coordinates=self.coordinates_for(loc_id),
                probability_scale=self.traffic_accident_scale,
            )
            if accident is not None:
                self.stats["accidents"] += 1

    def _work_round(self, current_tick: Tick) -> None:
        for human in list(self.runner.population.get_all()):
            occupation = str(getattr(human.demographics, "occupation", "") or "").lower()
            hazard = _OCCUPATION_HAZARD.get(occupation)
            if hazard is None:
                if getattr(human.physical_state, "current_activity", None) != ActivityType.WORK:
                    continue
                hazard = 0.25
            loc_id = getattr(human.physical_state, "work_location_id", None) or getattr(
                human.physical_state, "current_location_id", None
            )
            accident = self.runner.misfortune_engine.evaluate_workplace_incident(
                human,
                task_hazard_level=hazard,
                current_tick=current_tick,
                health_engine=self.runner.health_engine,
                event_bus=self.runner.event_bus,
                causal_graph=self.runner.causal_graph,
                coordinates=self.coordinates_for(loc_id),
                probability_scale=self.work_accident_scale,
            )
            if accident is not None:
                self.stats["accidents"] += 1

    def _domestic_round(self, current_tick: Tick) -> None:
        for human in list(self.runner.population.get_all()):
            loc_id = getattr(human.physical_state, "current_location_id", None)
            home = getattr(human.physical_state, "home_location_id", None)
            if loc_id and home and loc_id != home:
                continue
            quality = self._housing_quality(home or "casa_norte_1")
            accident = self.runner.misfortune_engine.evaluate_domestic_incident(
                human,
                housing_quality=quality,
                current_tick=current_tick,
                health_engine=self.runner.health_engine,
                event_bus=self.runner.event_bus,
                causal_graph=self.runner.causal_graph,
                coordinates=self.coordinates_for(loc_id or home),
                probability_scale=self.domestic_accident_scale,
            )
            if accident is not None:
                self.stats["accidents"] += 1

    def _housing_quality(self, unit_id: Optional[str]) -> float:
        housing = getattr(self.runner, "housing_engine", None)
        if housing is None:
            return 0.65
        for unit in housing.get_all_units():
            if unit.unit_id == unit_id or unit.location_id == unit_id:
                return float(getattr(unit, "quality_score", 0.65))
        return 0.65

    def _theft_round(self, current_tick: Tick) -> None:
        candidates = [
            h for h in self.runner.population.get_all()
            if getattr(h.physical_state, "current_location_id", None) in ("mercado_central", "plaza_central")
        ]
        if len(candidates) < 2 or self._rng.random() >= self.theft_probability:
            return

        victims = [h for h in candidates if h.physical_state.money >= 15.0]
        perpetrators = [h for h in candidates if h.physical_state.money <= 12.0]
        if not victims or not perpetrators:
            return
        victim = victims[int(self._rng.integers(0, len(victims)))]
        perpetrator = perpetrators[int(self._rng.integers(0, len(perpetrators)))]
        if victim.uid == perpetrator.uid:
            return

        amount = round(min(victim.physical_state.money * 0.35, 18.0), 2)
        result = self.runner.misfortune_engine.execute_theft_incident(
            victim,
            perpetrator,
            stolen_amount_usd=amount,
            current_tick=current_tick,
            event_bus=self.runner.event_bus,
            causal_graph=self.runner.causal_graph,
            coordinates=self.coordinates_for(getattr(victim.physical_state, "current_location_id", None)),
        )
        if result.get("success"):
            self.stats["thefts"] += 1
            if self._rng.random() < 0.40:
                distress = self.runner.health_engine.create_mental_distress(
                    tick=current_tick, cause=f"theft:{perpetrator.uid}"
                )
                victim.active_health_conditions.append(distress)
                theft_node = self.runner.causal_graph.find_latest_node(
                    EventType.PROPERTY_DAMAGED.value, human_uid=str(victim.uid)
                )
                event = SimulationEvent(
                    event_type=EventType.ILLNESS_CONTRACTED,
                    tick=current_tick,
                    source_human_id=victim.uid,
                    location_id=getattr(victim.physical_state, "current_location_id", None),
                    coordinates=self.coordinates_for(getattr(victim.physical_state, "current_location_id", None)),
                    data={
                        "condition_id": distress.condition_id,
                        "condition": distress.name,
                        "origin": "theft_victimization",
                        "coordinate_provenance": "synthetic_local_map",
                    },
                    importance=0.6,
                    cause_event_id=theft_node.event_id if theft_node else None,
                )
                self.runner.event_bus.emit(event)
                self.runner.causal_graph.add_event(
                    event,
                    cause_event_id=theft_node.event_id if theft_node else None,
                    description=f"{victim.name} desarrolló distrés tras hurto",
                )

    def trigger_contextual_disaster(
        self,
        current_tick: Tick,
        force: bool = False,
    ) -> Optional[Any]:
        """Trigger a flood/landslide when current weather actually supports it."""
        active = [d for d in self.runner.misfortune_engine.disaster_history if d.is_active]
        if active or current_tick < self._disaster_cooldown_until:
            return None

        hazard = self.runner.world_interaction.hazards
        rainfall = float(hazard.rainfall_mm_per_hour)
        if not force and rainfall < 15.0:
            return None

        probability = self.disaster_base_probability * max(0.5, rainfall / 20.0) * (
            0.5 + max(hazard.flood_risk_level, hazard.landslide_risk_level)
        )
        if not force and self._rng.random() >= probability:
            return None

        is_landslide = hazard.landslide_risk_level > hazard.flood_risk_level and self._rng.random() < 0.45
        if is_landslide:
            disaster_type = DisasterType.LANDSLIDE
            affected = list(_LANDSLIDE_PRONE_LOCATIONS)
            location_id = "cerro_guazapa"
        else:
            disaster_type = DisasterType.FLOODING
            affected = list(_FLOOD_PRONE_LOCATIONS)
            location_id = "rio_suchiacel"

        severity = round(min(0.95, 0.45 + rainfall / 100.0 + self._rng.uniform(0.0, 0.15)), 2)
        previous_roads = set(self.runner.misfortune_engine.blocked_roads)
        disaster = self.runner.misfortune_engine.trigger_environmental_disaster(
            disaster_type=disaster_type,
            affected_location_ids=affected,
            severity=severity,
            current_tick=current_tick,
            housing_engine=self.runner.housing_engine,
            event_bus=self.runner.event_bus,
            causal_graph=self.runner.causal_graph,
            coordinates=self.coordinates_for(location_id),
        )
        self.stats["disasters"] += 1
        self._disaster_cooldown_until = current_tick + self.runner.config.ticks_per_day * 7
        self._include_zone_residents(disaster)
        self._apply_displacement(disaster)
        self._sync_water_sources_after_disaster(disaster)
        logger.info(
            "Contextual %s triggered at tick %d (severity %.2f, %d displaced)",
            disaster_type.value,
            current_tick,
            severity,
            len(disaster.displaced_human_ids),
        )
        return disaster

    def _include_zone_residents(self, disaster: Any) -> None:
        """Add households living in the affected zone to the displaced set.

        Disaster damage is not limited to tenants with a formal lease: a family
        living in its own home inside a flooded or landslide-prone zone is just
        as displaced.  Without this step only registered lease occupants could
        ever be moved, so integrated runs never produced displacement.
        """
        if float(getattr(disaster, "severity", 0.0)) < 0.60:
            return
        affected = {str(loc) for loc in disaster.affected_location_ids}
        displaced = {str(uid) for uid in disaster.displaced_human_ids}
        for human in self.runner.population.get_all():
            home = str(getattr(human.physical_state, "home_location_id", "") or "")
            uid = str(human.uid)
            if home in affected and uid not in displaced:
                disaster.displaced_human_ids.append(uid)
                displaced.add(uid)

    def _apply_displacement(self, disaster: Any) -> None:
        for uid in disaster.displaced_human_ids:
            human = self.runner.population.get_optional(_as_uuid(uid))
            if human is None:
                continue
            home = str(human.physical_state.home_location_id or "casa_norte_1")
            self._displaced_home_locations[str(uid)] = home
            self._displaced_tenure[str(uid)] = getattr(human, "housing_tenure", HousingTenureType.RENTAL)
            human.physical_state.current_location_id = "casa_comunal"
            human.housing_tenure = HousingTenureType.SHELTER

    def _sync_water_sources_after_disaster(self, disaster: Any) -> None:
        hazard = self.runner.world_interaction.hazards
        for source in disaster.water_sources_contaminated:
            current = hazard.water_sources.get(source, 0.60)
            hazard.water_sources[source] = round(max(0.15, current - disaster.severity * 0.25), 2)

    def _daily_life_round(self, current_tick: Tick) -> None:
        self.runner.health_engine.step_facilities(current_tick)

        # Settlement -> territory impact and community recovery.
        self.runner.world_interaction.record_human_environmental_impact(
            population_count=len(self.runner.population.get_all()),
            current_tick=current_tick,
            event_bus=self.runner.event_bus,
            causal_graph=self.runner.causal_graph,
        )
        self._recover_disasters(current_tick)

        summary = self.life_events.step_daily(
            current_tick,
            self.runner.population,
            self.runner.event_bus,
            causal_graph=self.runner.causal_graph,
            health_engine=self.runner.health_engine,
            caregiving_engine=self.runner.family_caregiving,
            romance_engine=self.runner.romance_engine,
            location_geo=self.coordinates_for,
        )
        self.stats["births"] += int(summary.get("births", 0))
        self.stats["deaths"] += int(summary.get("deaths", 0))
        self._sync_relationship_state()
        self.life_events._refresh_family_links(self.runner.population)

    def _recover_disasters(self, current_tick: Tick) -> None:
        for disaster in list(self.runner.misfortune_engine.disaster_history):
            if not disaster.is_active:
                continue
            if disaster.disaster_id not in self._recovery_started:
                self._recovery_started.add(disaster.disaster_id)
                event = SimulationEvent(
                    event_type=EventType.DISASTER_RECOVERY_STARTED,
                    tick=current_tick,
                    location_id=disaster.affected_location_ids[0] if disaster.affected_location_ids else None,
                    coordinates=self.coordinates_for(
                        disaster.affected_location_ids[0] if disaster.affected_location_ids else None
                    ),
                    data={
                        "disaster_id": disaster.disaster_id,
                        "blocked_roads": list(disaster.roads_blocked),
                        "coordinate_provenance": "synthetic_local_map",
                    },
                    importance=0.75,
                )
                self.runner.event_bus.emit(event)
                self.runner.causal_graph.add_event(event, description=f"Inicia faena de recuperación tras {disaster.disaster_type.value}")

            volunteers = max(1, int(len(self.runner.population.get_all()) * 0.10))
            self.runner.misfortune_engine.resolve_community_disaster_recovery(
                disaster.disaster_id,
                volunteers_count=volunteers,
                current_tick=current_tick,
                event_bus=self.runner.event_bus,
                causal_graph=self.runner.causal_graph,
            )
            if not disaster.is_active:
                self._restore_displaced_humans()

    def _restore_displaced_humans(self) -> None:
        for uid, home in list(self._displaced_home_locations.items()):
            human = self.runner.population.get_optional(_as_uuid(uid))
            if human is not None:
                human.physical_state.current_location_id = home
                human.physical_state.home_location_id = home
                human.housing_tenure = self._displaced_tenure.get(uid, HousingTenureType.RENTAL)
        self._displaced_home_locations.clear()
        self._displaced_tenure.clear()

    # ------------------------------------------------------------------
    # Romance and family
    # ------------------------------------------------------------------

    def _romance_round(self, current_tick: Tick) -> None:
        engine = self.runner.romance_engine
        adults = [
            h for h in self.runner.population.get_all()
            if h.demographics.age >= 18
        ]

        # 1. New attraction and courtship starts among genuinely available adults.
        available = [h for h in adults if engine.get_agent_relationship(str(h.uid)) is None]
        checked = 0
        for _ in range(min(self.max_romance_pairs_per_day, len(available) * 2)):
            if len(available) < 2 or checked >= self.max_romance_pairs_per_day:
                break
            i = int(self._rng.integers(0, len(available)))
            j = int(self._rng.integers(0, len(available)))
            if i == j:
                continue
            a, b = available[i], available[j]
            checked += 1
            if self._rng.random() >= self.romance_formation_probability:
                continue
            relationship = engine.initiate_romantic_interest(
                a, b, current_tick,
                event_bus=self.runner.event_bus,
                causal_graph=self.runner.causal_graph,
            )
            if relationship is not None:
                self.stats["romances_started"] += 1
                available = [h for h in available if h.uid not in (a.uid, b.uid)]

        # 2. Unrequited love is possible but rare, and only through explicit checks.
        for _ in range(min(self.max_unrequited_checks_per_day, len(available))):
            if len(available) < 2:
                break
            i = int(self._rng.integers(0, len(available)))
            j = int(self._rng.integers(0, len(available)))
            if i == j:
                continue
            if self._rng.random() < 0.10:
                engine.evaluate_unrequited_love(
                    available[i], available[j], current_tick,
                    event_bus=self.runner.event_bus,
                    causal_graph=self.runner.causal_graph,
                )

        # 3. Courtship dates and stage progression.
        for relationship in list(engine.get_all_relationships()):
            if not relationship.is_active:
                continue
            if relationship.stage in (
                RomanceStage.INTEREST,
                RomanceStage.DATING,
                RomanceStage.COHABITING,
            ) and self._rng.random() < self.courtship_probability:
                result = engine.conduct_courtship_date(
                    relationship.relationship_id,
                    current_tick,
                    event_bus=self.runner.event_bus,
                    causal_graph=self.runner.causal_graph,
                )
                if result.get("success"):
                    self.stats["dates"] += 1
                    if result.get("promoted"):
                        self._synchronize_union_residence(relationship)

            # Ordinary daily dynamics (conflict, drift, separation).
            if relationship.stage != RomanceStage.INTEREST and self._rng.random() < self.relationship_dynamics_probability:
                engine.step_relationship_dynamics(
                    relationship.relationship_id,
                    current_tick,
                    event_bus=self.runner.event_bus,
                    causal_graph=self.runner.causal_graph,
                )

        # 4. Contextual infidelity opportunity and discovery.
        active_relationships = [r for r in engine.get_all_relationships() if r.is_active]
        for relationship in active_relationships:
            if relationship.stage == RomanceStage.INTEREST:
                continue
            if self._rng.random() >= self.infidelity_opportunity_probability:
                continue
            wayward_uid = relationship.partner_a_id if self._rng.random() < 0.5 else relationship.partner_b_id
            wayward = self.runner.population.get_optional(_as_uuid(wayward_uid))
            if wayward is None:
                continue
            loc = getattr(wayward.physical_state, "current_location_id", None)
            candidates = [
                h for h in adults
                if str(h.uid) not in (relationship.partner_a_id, relationship.partner_b_id)
                and getattr(h.physical_state, "current_location_id", None) == loc
            ]
            if not candidates:
                candidates = [
                    h for h in adults
                    if str(h.uid) not in (relationship.partner_a_id, relationship.partner_b_id)
                ]
            if not candidates:
                continue
            third = candidates[int(self._rng.integers(0, len(candidates)))]
            record = engine.evaluate_jealousy_and_infidelity(
                wayward, third, current_tick,
                event_bus=self.runner.event_bus,
                causal_graph=self.runner.causal_graph,
            )
            if record is not None:
                self.stats["infidelities"] += 1

        for relationship in list(engine.get_all_relationships()):
            if any(not inf.is_discovered for inf in relationship.infidelity_history):
                if self._rng.random() < self.discovery_probability:
                    result = engine.evaluate_infidelity_discovery(
                        relationship.relationship_id,
                        current_tick,
                        event_bus=self.runner.event_bus,
                        causal_graph=self.runner.causal_graph,
                    )
                    if result is not None:
                        self.stats["discoveries"] += 1

        # 5. Reconciliation after ordinary or infidelity-driven separation.
        for relationship in list(engine.get_all_relationships()):
            if relationship.is_active or relationship.stage != RomanceStage.SEPARATED:
                continue
            if self._rng.random() < self.reconciliation_probability:
                engine.evaluate_reconciliation(
                    relationship.relationship_id,
                    current_tick,
                    event_bus=self.runner.event_bus,
                    causal_graph=self.runner.causal_graph,
                )

        self._sync_relationship_state()

    def _synchronize_union_residence(self, relationship: Any) -> None:
        """Make cohabitation a real household transfer, not just a label."""
        a = self.runner.population.get_optional(_as_uuid(relationship.partner_a_id))
        b = self.runner.population.get_optional(_as_uuid(relationship.partner_b_id))
        if a is None or b is None:
            return
        home_a = getattr(a.physical_state, "home_location_id", None)
        home_b = getattr(b.physical_state, "home_location_id", None)
        if not home_a or home_a == home_b:
            return

        household = self.life_events.households.get_for_human(a.uid)
        b.physical_state.home_location_id = home_a
        b.physical_state.current_location_id = home_a
        if household is not None:
            self.life_events.households.move_human(b.uid, household.household_id)

    def _sync_relationship_state(self) -> None:
        engine = self.runner.romance_engine
        for relationship in engine.get_all_relationships():
            a = self.runner.population.get_optional(_as_uuid(relationship.partner_a_id))
            b = self.runner.population.get_optional(_as_uuid(relationship.partner_b_id))
            if relationship.is_active:
                if a is not None:
                    a.romantic_partner_id = relationship.partner_b_id
                if b is not None:
                    b.romantic_partner_id = relationship.partner_a_id
                if relationship.stage in (RomanceStage.COHABITING, RomanceStage.MARRIED):
                    self._synchronize_union_residence(relationship)
            else:
                if a is not None and a.romantic_partner_id == relationship.partner_b_id:
                    a.romantic_partner_id = None
                if b is not None and b.romantic_partner_id == relationship.partner_a_id:
                    b.romantic_partner_id = None
                for human in (a, b):
                    if human is not None and getattr(human, "heartbreak_state", None) is None:
                        engine.attach_pending_heartbreak(human)


def _as_uuid(value: Any) -> Any:
    """Best-effort UUID coercion for IDs coming from JSON checkpoints."""
    import uuid

    if value is None or isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return value
