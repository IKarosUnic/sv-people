"""Unified World-Human Interaction & Bidirectional Territory Engine (Phase 1.5 Extension).

Bridges geographic environment, infrastructure, and human biological and social trajectories:
- Territory -> Human: Weather delays, heat exhaustion, waterborne pathogen transmission from polluted sources.
- Human -> Territory: Waste generation, water pollution accumulation, community cleanup faenas, ecological restoration.
- Explicit classification of all geographic entities to preserve provenance and prevent synthetic objects
  from being presented as verified real-world locations.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import uuid

import numpy as np

from saltbor.core.types import GeographicObjectType, LocationID, Tick
from saltbor.events.types import EventType, SimulationEvent
from saltbor.world.interaction.environmental_hazards import EnvironmentalHazardProfile
from saltbor.world.locations.capabilities import (
    PlaceCapability,
    PlaceCategory,
    PlaceProfile,
    PlaceService,
)

logger = logging.getLogger(__name__)


class WorldHumanInteractionEngine:
    """Orchestrates bidirectional causality between territory and synthetic population."""

    def __init__(self, seed: Optional[int] = 42) -> None:
        self.hazards = EnvironmentalHazardProfile()
        self._rng = np.random.default_rng(seed)
        self._object_registry: dict[str, GeographicObjectType] = {}
        self.places: dict[str, PlaceProfile] = {}
        self.faena_records: list[dict[str, Any]] = []
        self._seed_default_geographic_registry()
        self._seed_default_places()

    def _seed_default_geographic_registry(self) -> None:
        """Seed verified GIS locations and mark explicit provenance classifications."""
        # 1. Real-world geographic features
        for feat in ["rio_suchiacel", "lago_suchitlan", "cerro_guazapa", "parque_central_suchitoto"]:
            self._object_registry[feat] = GeographicObjectType.REAL_WORLD_GEOGRAPHIC

        # 2. Verified real establishments
        for est in ["mercado_central", "comedor_dona_maria", "unidad_salud", "alcaldia_municipal"]:
            self._object_registry[est] = GeographicObjectType.VERIFIED_REAL_ESTABLISHMENT

        # 3. Simulated establishments
        for sim in ["tienda_san_pedro", "taller_artesanal", "pupuseria_el_cipres", "clinica_san_pedro"]:
            self._object_registry[sim] = GeographicObjectType.SIMULATED_ESTABLISHMENT

        # 4. Synthetic residential buildings
        for bld in ["casa_don_pedro", "casa_familia_reyes", "meson_san_pedro", "albergue_municipal"]:
            self._object_registry[bld] = GeographicObjectType.SYNTHETIC_BUILDING

        # 5. Temporary environmental objects
        for tmp in ["derrumbe_km_12", "inundacion_rio_suchiacel", "charca_estancada"]:
            self._object_registry[tmp] = GeographicObjectType.TEMPORARY_ENVIRONMENTAL_OBJECT

    def classify_object(self, object_id: str) -> GeographicObjectType:
        """Classify a geographic object, never asserting a simulated entity is verified real."""
        return self._object_registry.get(object_id, GeographicObjectType.SYNTHETIC_BUILDING)

    def register_object(self, object_id: str, obj_type: GeographicObjectType) -> None:
        self._object_registry[object_id] = obj_type

    def _seed_default_places(self) -> None:
        """Initialize place profiles with 8-tier capabilities across urban/rural types."""
        # 1. Health clinics & hospitals (Tier 1-8)
        clinica = PlaceProfile(
            place_id="clinica_salud",
            name="Unidad Comunitaria de Salud Familiar San Salvador",
            category=PlaceCategory.CLINIC,
            capabilities=PlaceCapability.IDENTIFIABLE | PlaceCapability.NAVIGABLE | PlaceCapability.VISITABLE | PlaceCapability.SCHEDULED | PlaceCapability.SERVICE_PROVIDER | PlaceCapability.INVENTORY_STORAGE | PlaceCapability.ECONOMIC_CONSEQUENCES,
            wgs84_coords=(13.7018, -89.2010),
            capacity=12,
            opening_hour=7,
            closing_hour=18,
            cash_box_usd=120.0,
            inventory={"medicamentos": 30, "suero": 20, "analgesicos": 50},
            price_catalog={"medicamentos": 2.50, "consulta": 3.00},
            services={
                "consulta_general": PlaceService(
                    service_id="consulta_general",
                    name="Consulta Médica General",
                    cost_usd=3.00,
                    duration_ticks=2,
                    health_recovery=0.45,
                    stress_reduction=0.20,
                    required_staff_role="enfermero",
                    max_simultaneous_clients=4,
                ),
                "urgencia_menor": PlaceService(
                    service_id="urgencia_menor",
                    name="Atención de Urgencia Menor",
                    cost_usd=8.00,
                    duration_ticks=3,
                    health_recovery=0.70,
                    stress_reduction=0.35,
                    required_staff_role="medico",
                    max_simultaneous_clients=2,
                ),
            },
        )
        self.places[clinica.place_id] = clinica

        # 2. Central municipal market (Tier 1-8)
        mercado = PlaceProfile(
            place_id="mercado_central",
            name="Mercado Central de San Salvador (Edificio 4)",
            category=PlaceCategory.MARKET,
            capabilities=PlaceCapability.IDENTIFIABLE | PlaceCapability.NAVIGABLE | PlaceCapability.VISITABLE | PlaceCapability.SCHEDULED | PlaceCapability.INVENTORY_STORAGE | PlaceCapability.SOCIAL_INTERACTION | PlaceCapability.ECONOMIC_CONSEQUENCES,
            wgs84_coords=(13.6948, -89.1952),
            capacity=80,
            opening_hour=5,
            closing_hour=17,
            cash_box_usd=450.0,
            sub_places=["puesto_granos_1", "puesto_lacteos_2", "puesto_carniceria_3", "puesto_verduras_4"],
            inventory={"maiz_lb": 600, "frijol_lb": 500, "queso_lb": 250, "huevos": 800, "arroz_lb": 400},
            price_catalog={"maiz_lb": 0.45, "frijol_lb": 1.15, "queso_lb": 3.25, "huevos": 0.18, "arroz_lb": 0.60},
        )
        self.places[mercado.place_id] = mercado

        # 3. Traditional pupusería & eatery (Tier 1-8)
        pupuseria = PlaceProfile(
            place_id="comedor_dona_maria",
            name="Comedor y Pupusería Doña María",
            category=PlaceCategory.PUPUSERIA,
            capabilities=PlaceCapability.IDENTIFIABLE | PlaceCapability.NAVIGABLE | PlaceCapability.VISITABLE | PlaceCapability.SCHEDULED | PlaceCapability.SERVICE_PROVIDER | PlaceCapability.INVENTORY_STORAGE | PlaceCapability.SOCIAL_INTERACTION | PlaceCapability.ECONOMIC_CONSEQUENCES,
            wgs84_coords=(13.6980, -89.1925),
            capacity=25,
            opening_hour=6,
            closing_hour=21,
            cash_box_usd=85.0,
            inventory={"pupusas": 150, "cafe": 90, "chocolate": 40},
            price_catalog={"pupusa_revuelta": 0.75, "pupusa_queso": 0.85, "cafe_taza": 0.50},
            services={
                "orden_pupusas": PlaceService(
                    service_id="orden_pupusas",
                    name="Orden de 3 Pupusas Revueltas con Café",
                    cost_usd=2.75,
                    duration_ticks=2,
                    hunger_reduction=0.75,
                    energy_recovery=0.30,
                    stress_reduction=0.15,
                    max_simultaneous_clients=8,
                ),
            },
        )
        self.places[pupuseria.place_id] = pupuseria

        # 4. Residential housing units (Tier 1-4, 7, 8)
        for h_id, name, lat, lon in [
            ("casa_norte_1", "Vivienda Familiar Barrio San Miguelito #12", 13.7020, -89.1915),
            ("casa_norte_2", "Casa Colonial 1ª Calle Poniente #24", 13.7005, -89.1940),
            ("casa_sur_1", "Residencia Barrio La Vega #8", 13.6940, -89.1910),
            ("casa_sur_2", "Vivienda Familiar Barrio Santa Anita #45", 13.6935, -89.1960),
            ("casa_este_1", "Casa Barrio Concepción #33", 13.6970, -89.1870),
            ("casa_oeste_1", "Edificio Residencial Alameda Roosevelt #102", 13.6990, -89.2010),
            ("casa_residencial_1", "Casa Residencial Centro Histórico", 13.7000, -89.1930),
        ]:
            house = PlaceProfile(
                place_id=h_id,
                name=name,
                category=PlaceCategory.HOUSING,
                capabilities=PlaceCapability.IDENTIFIABLE | PlaceCapability.NAVIGABLE | PlaceCapability.VISITABLE | PlaceCapability.SCHEDULED | PlaceCapability.INVENTORY_STORAGE | PlaceCapability.SOCIAL_INTERACTION | PlaceCapability.ECONOMIC_CONSEQUENCES,
                wgs84_coords=(lat, lon),
                capacity=6,
                always_open=True,
                sub_places=[f"{h_id}_dormitorio", f"{h_id}_sala", f"{h_id}_cocina", f"{h_id}_patio"],
                inventory={"alimentos_despensa_kg": 15, "agua_potable_lts": 40},
            )
            self.places[h_id] = house

        # 5. Public civic spaces & parks (Tier 1-4, 7)
        plaza = PlaceProfile(
            place_id="plaza_central",
            name="Plaza Gerardo Barrios (Cívica Central)",
            category=PlaceCategory.PARK,
            capabilities=PlaceCapability.IDENTIFIABLE | PlaceCapability.NAVIGABLE | PlaceCapability.VISITABLE | PlaceCapability.SOCIAL_INTERACTION,
            wgs84_coords=(13.6978, -89.1915),
            capacity=150,
            always_open=True,
            is_outdoor=True,
        )
        self.places[plaza.place_id] = plaza

        # 6. Education & National Library (Tier 1-5, 7)
        binaes = PlaceProfile(
            place_id="binaes_estudio",
            name="Biblioteca Nacional de El Salvador BINAES",
            category=PlaceCategory.RECREATIONAL,
            capabilities=PlaceCapability.IDENTIFIABLE | PlaceCapability.NAVIGABLE | PlaceCapability.VISITABLE | PlaceCapability.SCHEDULED | PlaceCapability.SERVICE_PROVIDER | PlaceCapability.SOCIAL_INTERACTION,
            wgs84_coords=(13.6975, -89.1905),
            capacity=60,
            always_open=True,  # BINAES is open 24/7 in real El Salvador!
            services={
                "estudio_lectura": PlaceService(
                    service_id="estudio_lectura",
                    name="Sala de Lectura y Estudio Epistémico",
                    cost_usd=0.0,
                    duration_ticks=3,
                    stress_reduction=0.25,
                    energy_recovery=0.10,
                    max_simultaneous_clients=25,
                ),
            },
        )
        self.places[binaes.place_id] = binaes

        # 7. School / Vocational training
        escuela = PlaceProfile(
            place_id="escuela_comunal",
            name="Escuela República de Costa Rica / Calle Delgado",
            category=PlaceCategory.SCHOOL,
            capabilities=PlaceCapability.IDENTIFIABLE | PlaceCapability.NAVIGABLE | PlaceCapability.VISITABLE | PlaceCapability.SCHEDULED | PlaceCapability.SERVICE_PROVIDER | PlaceCapability.SOCIAL_INTERACTION,
            wgs84_coords=(13.6988, -89.1895),
            capacity=45,
            opening_hour=7,
            closing_hour=17,
        )
        self.places[escuela.place_id] = escuela

        # 8. Artisan workshop
        taller = PlaceProfile(
            place_id="taller_artesanal",
            name="Taller de Oficios y Herrería Barrio San Esteban",
            category=PlaceCategory.WORKSHOP,
            capabilities=PlaceCapability.IDENTIFIABLE | PlaceCapability.NAVIGABLE | PlaceCapability.VISITABLE | PlaceCapability.SCHEDULED | PlaceCapability.SERVICE_PROVIDER | PlaceCapability.INVENTORY_STORAGE | PlaceCapability.ECONOMIC_CONSEQUENCES,
            wgs84_coords=(13.6965, -89.1885),
            capacity=15,
            opening_hour=7,
            closing_hour=18,
            inventory={"herramientas": 12, "madera_piezas": 25, "hierro_piezas": 30},
            price_catalog={"reparacion_enseres": 4.50, "mueble_madera": 35.00},
        )
        self.places[taller.place_id] = taller

    def register_place(self, place: PlaceProfile) -> None:
        """Register or update a place profile."""
        self.places[place.place_id] = place

    def get_place(self, place_id: str) -> Optional[PlaceProfile]:
        """Retrieve place profile with alias resolution."""
        if place_id in self.places:
            return self.places[place_id]
        aliases = {
            "mercado_municipal": "mercado_central",
            "parque_central": "plaza_central",
            "alcaldia": "casa_comunal",
            "clinica": "clinica_salud",
            "unidad_salud": "clinica_salud",
            "pupuseria": "comedor_dona_maria",
        }
        mapped = aliases.get(place_id)
        return self.places.get(mapped) if mapped else None

    def can_enter_place(self, place_id: str, human_uid: str, current_hour: int) -> Tuple[bool, str]:
        """Check if a human can enter the specified place."""
        place = self.get_place(place_id)
        if place is None:
            # Default open for unprofiled locations
            return True, "Ubicación sin restricciones especiales"
        return place.can_enter(human_uid, current_hour)

    def enter_place(self, place_id: str, human_uid: str) -> bool:
        """Add human to place occupancy."""
        place = self.get_place(place_id)
        if place:
            return place.enter(human_uid)
        return True

    def leave_place(self, place_id: str, human_uid: str) -> bool:
        """Remove human from place occupancy."""
        place = self.get_place(place_id)
        if place:
            return place.leave(human_uid)
        return True

    # -------------------------------------------------------------------------
    # Territory -> Human Causal Pathways
    # -------------------------------------------------------------------------

    def evaluate_water_consumption_risk(
        self,
        human: Any,
        water_source: str,
        current_tick: Tick,
        health_engine: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
        coordinates: Optional[tuple[float, float]] = None,
    ) -> bool:
        """Evaluate gastrointestinal illness risk from consuming water from a given source."""
        cleanliness = self.hazards.water_sources.get(water_source, 0.60)
        if cleanliness >= 0.55:
            # Potable water, safe
            return False

        # Contaminated water: infection probability proportional to contamination
        contamination_level = 1.0 - cleanliness
        infection_chance = contamination_level * 0.40

        if self._rng.random() < infection_chance:
            logger.warning("Human %s drank contaminated water from %s (cleanliness=%.2f)", human.name, water_source, cleanliness)
            condition = None
            if health_engine:
                condition = health_engine.create_waterborne_illness(tick=current_tick, origin=water_source)
                getattr(human, "active_health_conditions", []).append(condition)

            if event_bus:
                cause_id = None
                if causal_graph is not None:
                    pollution_node = causal_graph.find_latest_node(
                        EventType.WATER_SOURCE_POLLUTED.value,
                        predicate=lambda n: n.location_id == water_source,
                    )
                    cause_id = pollution_node.event_id if pollution_node else None
                evt = SimulationEvent(
                    event_type=EventType.ILLNESS_CONTRACTED,
                    tick=current_tick,
                    source_human_id=human.uid,
                    location_id=water_source,
                    coordinates=coordinates,
                    data={
                        "source": water_source,
                        "cleanliness": cleanliness,
                        "condition": "Amebiasis / Diarrea",
                        "condition_id": condition.condition_id if condition else None,
                        "origin": f"water:{water_source}",
                        "coordinate_provenance": "synthetic_local_map" if coordinates else None,
                    },
                    importance=0.75,
                    cause_event_id=cause_id,
                )
                event_bus.emit(evt)
                if causal_graph:
                    causal_graph.add_event(
                        evt,
                        cause_event_id=cause_id,
                        description=f"{human.name} contrajo infección gastrointestinal por agua de {water_source}",
                    )

            return True

        return False

    def calculate_travel_burden(self, human: Any, distance_meters: float) -> tuple[float, float]:
        """Calculate travel duration and energy cost modulated by weather and terrain."""
        base_speed_mps = 1.25  # 4.5 km/h walking speed
        rain = self.hazards.rainfall_mm_per_hour
        temp = self.hazards.temperature_celsius

        # Rain slows travel by up to 40%
        speed_factor = max(0.60, 1.0 - (rain / 30.0))
        speed = base_speed_mps * speed_factor

        time_seconds = distance_meters / max(0.1, speed)
        ticks = max(1, int(time_seconds / 900.0))  # 15 mins per tick

        # Heat increases energy drain
        heat_multiplier = 1.5 if temp > 32.0 else 1.0
        energy_drain = round(0.015 * (distance_meters / 500.0) * heat_multiplier, 3)

        return ticks, energy_drain

    # -------------------------------------------------------------------------
    # Human -> Territory Causal Pathways
    # -------------------------------------------------------------------------

    def record_human_environmental_impact(
        self,
        population_count: int,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> None:
        """Settlement living and economic activities generate waste and degrade water if unmanaged."""
        # Daily solid waste generation: ~0.4 kg per person per day
        daily_waste = population_count * 0.40 / 24.0
        self.hazards.accumulated_waste_kg += daily_waste

        # River pollution increases if waste is high
        if self.hazards.accumulated_waste_kg > 200.0:
            self.hazards.water_pollution_index = min(1.0, self.hazards.water_pollution_index + 0.005)
            # Degrade rio_suchiacel cleanliness
            curr_clean = self.hazards.water_sources.get("rio_suchiacel", 0.70)
            self.hazards.water_sources["rio_suchiacel"] = max(0.20, curr_clean - 0.008)

            if self.hazards.water_sources["rio_suchiacel"] < 0.50 and current_tick % 24 == 0:
                logger.warning("Rio Suchiacel water source contaminated due to untreated waste")
                if event_bus:
                    evt = SimulationEvent(
                        event_type=EventType.WATER_SOURCE_POLLUTED,
                        tick=current_tick,
                        location_id="rio_suchiacel",
                        data={"cleanliness": self.hazards.water_sources["rio_suchiacel"]},
                        importance=0.8,
                    )
                    event_bus.emit(evt)
                    if causal_graph:
                        causal_graph.add_event(evt, description="Río Suchiacel contaminado por acumulación de desechos")

    def execute_community_cleanup_faena(
        self,
        volunteers_count: int,
        water_source: str,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> dict[str, Any]:
        """Community organizing faena clears waste and restores water quality."""
        waste_removed = min(self.hazards.accumulated_waste_kg, volunteers_count * 25.0)
        self.hazards.accumulated_waste_kg = max(0.0, self.hazards.accumulated_waste_kg - waste_removed)

        # Restore water source cleanliness
        prev_clean = self.hazards.water_sources.get(water_source, 0.50)
        boost = min(0.35, volunteers_count * 0.08)
        new_clean = min(0.95, prev_clean + boost)
        self.hazards.water_sources[water_source] = round(new_clean, 2)
        self.hazards.water_pollution_index = max(0.10, self.hazards.water_pollution_index - 0.15)

        record = {
            "water_source": water_source,
            "waste_removed_kg": waste_removed,
            "new_cleanliness": new_clean,
            "volunteers_count": volunteers_count,
            "tick": current_tick,
        }
        self.faena_records.append(record)

        logger.info("Faena comunitaria: %d volunteers cleaned %s (new cleanliness=%.2f)", volunteers_count, water_source, new_clean)
        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.WATER_SOURCE_CLEANED,
                tick=current_tick,
                location_id=water_source,
                data={
                    "source": water_source,
                    "waste_removed_kg": waste_removed,
                    "new_cleanliness": new_clean,
                    "volunteers_count": volunteers_count,
                },
                importance=0.75,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"Faena comunitaria restauró fuente de agua {water_source} a {new_clean*100:.0f}% potabilidad")

        return {
            "success": True,
            "waste_removed_kg": waste_removed,
            "new_cleanliness": new_clean,
            "is_potable": new_clean >= 0.55,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize territorial state, cleanup history, and places profiles."""
        return {
            "hazards": self.hazards.to_dict(),
            "object_registry": {k: v.value for k, v in self._object_registry.items()},
            "faena_records": list(self.faena_records),
            "places": {p_id: p.to_dict() for p_id, p in self.places.items()},
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        """Restore territorial state and cleanup history."""
        if "hazards" in data:
            self.hazards = EnvironmentalHazardProfile.from_dict(data["hazards"])
        for object_id, object_type in data.get("object_registry", {}).items():
            try:
                self._object_registry[str(object_id)] = GeographicObjectType(object_type)
            except ValueError:
                continue
        self.faena_records = list(data.get("faena_records", []))
        # Restore places dynamic attributes
        for p_id, p_dict in data.get("places", {}).items():
            place = self.get_place(p_id)
            if place:
                place.cash_box_usd = float(p_dict.get("cash_box_usd", place.cash_box_usd))
                place.material_condition = float(p_dict.get("material_condition", place.material_condition))
                if "inventory" in p_dict:
                    place.inventory = {k: int(v) for k, v in p_dict["inventory"].items()}
