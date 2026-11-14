"""IntegratedWorldSimulationEngine — Master World & Human Unification (Phase 1.8).

Binds all simulation subsystems into a single, cohesive causal ecosystem:
- SyntheticHuman, PhysicalState, PsychologicalState, Emotions, Personality, Memory, Decision, Goals
- SocialNetworkEngine, CommunityFormation, Relationships, Family, Romance, ADESCO
- Economy: CommercialEngine, LaborMarketEngine, HousingEngine, HouseholdLedger
- HealthEngine, MisfortuneEngine, EnvironmentalHazards
- TransportationEngine, OSMRoadNetwork, RoadBlockages
- WorldInteractionEngine, PlaceHierarchy, Services, Inventories
- DailyLifeSimulationEngine, DiurnalPhases
- SalvadoranHistoricalMemoryEngine, CausalEventGraph, EventBus
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from saltbor.core.types import (
    ActivityType,
    EmploymentStatus,
    GeographicObjectType,
    HousingTenureType,
    Tick,
)
from saltbor.events.types import EventType, SimulationEvent
from saltbor.lifecycle.daily_life.engine import DailyLifeSimulationEngine, get_diurnal_phase
from saltbor.world.locations.capabilities import PlaceCapability, PlaceCategory
from saltbor.world.transportation.engine import TransportationEngine
from saltbor.world.transportation.models import ActiveJourney, JourneyStatus, TravelMode
from saltbor.social.resources.cpr_manager import CPRHealthStatus

logger = logging.getLogger(__name__)


class IntegratedWorldSimulationEngine:
    """Master engine coordinating world-human interactions and causal propagation."""

    def __init__(self, runner: Any) -> None:
        self.runner = runner

        # Transportation Engine (OSM street network & kinematic travel)
        osm_network = getattr(getattr(runner, "geographic_updater", None), "network", None)
        self.transportation = TransportationEngine(road_network=osm_network)

        # Daily Life Simulation Engine (diurnal phases, schedules, autonomy)
        self.daily_life = DailyLifeSimulationEngine(seed=getattr(runner.config, "random_seed", 42))

        # World Interaction & Place Capabilities
        self.world_interaction = getattr(runner, "world_interaction", None)

        # Causal event graph & historical memory
        self.causal_graph = getattr(runner, "causal_graph", None)
        self.historical_memory = getattr(runner, "salvadoran_history", None)

        self._active_blockage_cooldown = 0
        self._last_historical_consolidation_tick = -1

    def step(self, current_tick: Tick) -> None:
        """Execute one integrated simulation step across all subsystems."""
        clock = self.runner.clock
        hour = clock.current_hour_int
        weather = getattr(self.runner, "environment", None)
        rain_mm = getattr(weather, "precipitation_mm", 0.0) if weather else 0.0

        # ---------------------------------------------------------------------
        # 1. Environmental Causal Propagation to Infrastructure (Roads & Places)
        # ---------------------------------------------------------------------
        self._evaluate_environmental_impacts(current_tick, rain_mm)

        # ---------------------------------------------------------------------
        # 2. Advance Active Street Journeys (Kinematic Progress, Blockages, Arrivals)
        # ---------------------------------------------------------------------
        arrived_journeys = self.transportation.step(
            current_tick=current_tick,
            population_registry=self.runner.population,
            weather_rain=rain_mm,
            event_bus=self.runner.event_bus,
            causal_graph=self.causal_graph,
        )

        for journey in arrived_journeys:
            # Human has arrived at destination: enter place
            if self.world_interaction:
                self.world_interaction.leave_place(journey.origin_location_id, journey.human_uid)
                self.world_interaction.enter_place(journey.destination_location_id, journey.human_uid)

        # ---------------------------------------------------------------------
        # 3. Synchronize Historical Memory with Major Community Crises
        # ---------------------------------------------------------------------
        if current_tick - self._last_historical_consolidation_tick >= 96:
            self._consolidate_historical_events(current_tick)
            self._last_historical_consolidation_tick = current_tick

    def _evaluate_environmental_impacts(self, current_tick: Tick, rain_mm: float) -> None:
        """Propagate weather extremes to road blockages and physical wear."""
        if rain_mm > 15.0 and current_tick > self._active_blockage_cooldown:
            # Tropical storm triggering a flood in quebradas or landslide
            self._active_blockage_cooldown = current_tick + 48  # 12-hour cooldown

            # Blockage at low-lying river road or mountain pass
            loc_name = "Quebrada El Zapote / Calle Rubén Darío"
            lat, lon = (13.6980, -89.1950)
            b = self.transportation.register_blockage(
                cause="Inundación por tormenta tropical",
                location_name=loc_name,
                lat=lat,
                lon=lon,
                start_tick=current_tick,
                duration_ticks=20,  # 5 hours
                radius_m=120.0,
            )

            # Emit infrastructure event
            if self.runner.event_bus:
                evt = SimulationEvent(
                    event_type=EventType.ROAD_BLOCKED,
                    tick=current_tick,
                    location_id="quebrada_el_zapote",
                    data={
                        "cause": b.cause,
                        "location": loc_name,
                        "rain_mm": rain_mm,
                        "duration_ticks": b.duration_ticks,
                    },
                    importance=0.75,
                )
                self.runner.event_bus.emit(evt)
                if self.causal_graph:
                    self.causal_graph.add_event(evt, description=f"Tormenta de {rain_mm:.1f}mm anegó {loc_name}")

            # Degrade CPR communal road physical condition
            if hasattr(self.runner, "cpr_manager") and self.runner.cpr_manager:
                road_cpr = self.runner.cpr_manager.get_resource("camino_el_calvario")
                if road_cpr:
                    road_cpr.current_stock = max(10.0, road_cpr.current_stock - 25.0)
                    if road_cpr.stock_ratio < 0.30:
                        road_cpr.status = CPRHealthStatus.STRESSED

    def _consolidate_historical_events(self, current_tick: Tick) -> None:
        """Transfer major community disasters, faenas, and institutional milestones to historical memory."""
        if self.historical_memory is None:
            return

        events = getattr(self.runner.event_bus, "event_log", [])
        recent = [e for e in events[-100:] if e.importance >= 0.70]
        for e in recent:
            summary = e.data.get("description") or e.data.get("cause") or f"Acontecimiento notable: {e.event_type.value}"
            try:
                self.historical_memory.record_historical_event(
                    tick=e.tick,
                    event_type=e.event_type.value,
                    summary=summary,
                    importance=e.importance,
                )
            except Exception:
                pass

    def initiate_agent_movement(
        self,
        human: Any,
        destination_loc_id: str,
        current_tick: Tick,
        mode: TravelMode = TravelMode.WALK,
        purpose: str = "general_travel",
    ) -> Tuple[bool, str]:
        """Initiate non-teleporting journey on the real street network."""
        pstate = getattr(human, "physical_state", None)
        if not pstate:
            return False, "Estado físico no disponible"

        origin_loc_id = pstate.current_location_id or "plaza_central"
        if origin_loc_id == destination_loc_id:
            return True, "Ya se encuentra en el destino"

        # Check if human is already in transit
        uid_str = str(human.uid)
        if uid_str in self.transportation.active_journeys:
            curr_j = self.transportation.active_journeys[uid_str]
            if curr_j.status == JourneyStatus.IN_PROGRESS:
                return False, f"El agente ya se encuentra viajando hacia {curr_j.destination_location_id}"

        # Resolve coordinates
        coords_engine = getattr(self.runner, "extension", None)
        orig_coords = (
            coords_engine.coordinates_for(origin_loc_id)
            if coords_engine
            else (13.6978, -89.1915)
        )
        dest_coords = (
            coords_engine.coordinates_for(destination_loc_id)
            if coords_engine
            else (13.6980, -89.1925)
        )

        # Plan journey
        journey = self.transportation.plan_journey(
            human_uid=uid_str,
            origin_loc_id=origin_loc_id,
            destination_loc_id=destination_loc_id,
            origin_coords=orig_coords,
            destination_coords=dest_coords,
            current_tick=current_tick,
            mode=mode,
            purpose=purpose,
        )

        if journey.status == JourneyStatus.BLOCKED:
            # Path is obstructed by flood or landslide
            return False, journey.blocked_reason or "Ruta bloqueada por obstáculo intransitable"

        # Set human in transit
        pstate.current_activity = ActivityType.TRAVEL
        pstate.activity_ticks_remaining = max(1, journey.estimated_arrival_tick - current_tick)

        if self.runner.event_bus:
            self.runner.event_bus.emit(
                SimulationEvent(
                    event_type=EventType.JOURNEY_STARTED,
                    tick=current_tick,
                    source_human_id=human.uid,
                    location_id=origin_loc_id,
                    data={
                        "from": origin_loc_id,
                        "to": destination_loc_id,
                        "mode": mode.value,
                        "distance_m": round(journey.total_distance_m, 1),
                        "purpose": purpose,
                    },
                    importance=0.20,
                )
            )

        return True, "Viaje iniciado en la red vial"

    def execute_place_interaction(
        self,
        human: Any,
        place_id: str,
        interaction_type: str,
        current_tick: Tick,
        current_hour: int,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a structured physical interaction with a place."""
        if not self.world_interaction:
            return {"success": False, "reason": "WorldInteractionEngine no disponible"}

        place = self.world_interaction.get_place(place_id)
        if not place:
            return {"success": False, "reason": f"Lugar '{place_id}' no registrado en capacidades"}

        uid_str = str(human.uid)
        details = details or {}

        # 1. ENTER PLACE
        if interaction_type == "enter":
            can_enter, reason = place.can_enter(uid_str, current_hour)
            if not can_enter:
                if self.runner.event_bus and "saturado" in reason.lower():
                    self.runner.event_bus.emit(
                        SimulationEvent(
                            event_type=EventType.PLACE_SATURATED,
                            tick=current_tick,
                            source_human_id=human.uid,
                            location_id=place_id,
                            data={"place_name": place.name, "capacity": place.capacity},
                            importance=0.40,
                        )
                    )
                return {"success": False, "reason": reason}

            place.enter(uid_str)
            if self.runner.event_bus:
                self.runner.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.PLACE_ENTERED,
                        tick=current_tick,
                        source_human_id=human.uid,
                        location_id=place_id,
                        data={"place_name": place.name},
                        importance=0.15,
                    )
                )
            return {"success": True, "place": place.to_dict()}

        # 2. LEAVE PLACE
        elif interaction_type == "leave":
            place.leave(uid_str)
            if self.runner.event_bus:
                self.runner.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.PLACE_EXITED,
                        tick=current_tick,
                        source_human_id=human.uid,
                        location_id=place_id,
                        data={"place_name": place.name},
                        importance=0.10,
                    )
                )
            return {"success": True}

        # 3. REQUEST SPECIALIZED SERVICE (e.g. Clinic consultation, pupusería meal)
        elif interaction_type == "service":
            service_id = details.get("service_id", "consulta_general")
            client_money = getattr(human.physical_state, "money", 0.0)

            res = place.request_service(service_id, uid_str, client_money)
            if res.get("success"):
                cost = res.get("cost_usd", 0.0)
                human.physical_state.money = max(0.0, human.physical_state.money - cost)

                # Apply benefits
                if "health_recovery" in res:
                    human.physical_state.health = min(1.0, human.physical_state.health + res["health_recovery"])
                if "hunger_reduction" in res:
                    human.physical_state.hunger = max(0.0, human.physical_state.hunger - res["hunger_reduction"])
                if "energy_recovery" in res:
                    human.physical_state.energy = min(1.0, human.physical_state.energy + res["energy_recovery"])

                if self.runner.event_bus:
                    self.runner.event_bus.emit(
                        SimulationEvent(
                            event_type=EventType.SERVICE_COMPLETED,
                            tick=current_tick,
                            source_human_id=human.uid,
                            location_id=place_id,
                            data={
                                "service_id": service_id,
                                "cost_usd": cost,
                                "place_name": place.name,
                            },
                            importance=0.55,
                        )
                    )
            else:
                if self.runner.event_bus:
                    self.runner.event_bus.emit(
                        SimulationEvent(
                            event_type=EventType.SERVICE_DENIED,
                            tick=current_tick,
                            source_human_id=human.uid,
                            location_id=place_id,
                            data={"service_id": service_id, "reason": res.get("reason")},
                            importance=0.45,
                        )
                    )
            return res

        # 4. PURCHASE RETAIL PRODUCT (Market, store, pharmacy)
        elif interaction_type == "purchase":
            product_id = details.get("product_id", "maiz_lb")
            qty = details.get("quantity", 5)
            buyer_money = getattr(human.physical_state, "money", 0.0)

            res = place.purchase_product(product_id, qty, buyer_money)
            if res.get("success"):
                total_cost = res.get("total_cost", 0.0)
                human.physical_state.money = max(0.0, human.physical_state.money - total_cost)

                # Add to human's pantry or reduce hunger
                human.physical_state.hunger = max(0.0, human.physical_state.hunger - 0.20)

                if self.runner.event_bus:
                    self.runner.event_bus.emit(
                        SimulationEvent(
                            event_type=EventType.TRADE_COMPLETED,
                            tick=current_tick,
                            source_human_id=human.uid,
                            location_id=place_id,
                            data={
                                "product_id": product_id,
                                "quantity": res.get("quantity_bought"),
                                "total_cost": total_cost,
                                "place_name": place.name,
                            },
                            importance=0.35,
                        )
                    )
            else:
                if "agotado" in res.get("reason", "").lower() and self.runner.event_bus:
                    self.runner.event_bus.emit(
                        SimulationEvent(
                            event_type=EventType.SUPPLY_SHORTAGE_EXPERIENCED,
                            tick=current_tick,
                            source_human_id=human.uid,
                            location_id=place_id,
                            data={"product_id": product_id, "reason": res.get("reason")},
                            importance=0.50,
                        )
                    )
            return res

        return {"success": False, "reason": f"Tipo de interacción desconocido: '{interaction_type}'"}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize unified simulation state for checkpointing."""
        return {
            "transportation": self.transportation.to_dict(),
            "daily_life": self.daily_life.to_dict(),
            "active_blockage_cooldown": self._active_blockage_cooldown,
            "last_historical_tick": self._last_historical_consolidation_tick,
        }

    def load_dict(self, data: Dict[str, Any]) -> None:
        """Restore unified simulation state from checkpoint dictionary."""
        if not data:
            return
        if "transportation" in data:
            self.transportation.load_dict(data["transportation"])
        if "daily_life" in data:
            self.daily_life.load_dict(data["daily_life"])
        self._active_blockage_cooldown = data.get("active_blockage_cooldown", 0)
        self._last_historical_consolidation_tick = data.get("last_historical_tick", -1)
