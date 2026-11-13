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

logger = logging.getLogger(__name__)


class WorldHumanInteractionEngine:
    """Orchestrates bidirectional causality between territory and synthetic population."""

    def __init__(self, seed: Optional[int] = 42) -> None:
        self.hazards = EnvironmentalHazardProfile()
        self._rng = np.random.default_rng(seed)
        self._object_registry: dict[str, GeographicObjectType] = {}
        self.faena_records: list[dict[str, Any]] = []
        self._seed_default_geographic_registry()

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
        """Serialize territorial state and cleanup history."""
        return {
            "hazards": self.hazards.to_dict(),
            "object_registry": {k: v.value for k, v in self._object_registry.items()},
            "faena_records": list(self.faena_records),
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
