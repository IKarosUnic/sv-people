"""Accidents, Disasters & Misfortunes Engine (Phase 1.5 Extension).

Simulates:
- Contextual traffic accidents: rain, road condition, fatigue, visibility.
- Workplace trauma: agricultural machete cuts, workshop falls, fatigue hazard multiplier.
- Environmental disasters: floods, landslides, road closures, and household displacement.
- Community emergency response, faenas, road reopening, and recovery.
- Theft & economic victimization with legal dispute escalation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set
import uuid

import numpy as np

from saltbor.accidents.models import AccidentEvent, DisasterEvent
from saltbor.core.types import AccidentType, DisasterType, HousingTenureType, LocationID, Tick
from saltbor.events.types import EventType, SimulationEvent

logger = logging.getLogger(__name__)


class MisfortuneEngine:
    """Manages accidents, physical mishaps, and environmental disasters."""

    def __init__(self, seed: Optional[int] = 42) -> None:
        self.accident_history: list[AccidentEvent] = []
        self.disaster_history: list[DisasterEvent] = []
        self.blocked_roads: set[str] = set()
        self._rng = np.random.default_rng(seed)

    # -------------------------------------------------------------------------
    # Contextual Traffic Accidents
    # -------------------------------------------------------------------------

    def evaluate_traffic_accident(
        self,
        human: Any,
        road_id: str,
        weather_state: Any,
        current_tick: Tick,
        health_engine: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
        coordinates: Optional[tuple[float, float]] = None,
        probability_scale: float = 1.0,
    ) -> Optional[AccidentEvent]:
        """Evaluate traffic accident risk based on precipitation, road slope, and fatigue."""
        rainfall = getattr(weather_state, "rainfall_mm_per_hour", 0.0)
        energy = getattr(human.physical_state, "energy", 0.5)

        # Baseline probability amplified by rain intensity and driver fatigue
        rain_hazard = min(0.15, (rainfall / 40.0) * 0.15) if rainfall > 0 else 0.0
        fatigue_hazard = max(0.0, (0.50 - energy) * 0.25) if energy < 0.50 else 0.0
        accident_prob = min(0.35, 0.01 + rain_hazard + fatigue_hazard) * max(0.0, probability_scale)

        if self._rng.random() >= accident_prob:
            return None

        severity = round(float(self._rng.uniform(0.30, 0.85)), 2)
        prop_loss = round(float(self._rng.uniform(10.0, 45.0)), 2)

        causal_factors = ["conducción_en_vía"]
        if rainfall > 5.0:
            causal_factors.append("pavimento_mojado_lluvia")
        if energy < 0.20:
            causal_factors.append("fatiga_del_conductor")

        acc_id = f"acc_{uuid.uuid4().hex[:8]}"
        accident = AccidentEvent(
            accident_id=acc_id,
            accident_type=AccidentType.TRAFFIC_ACCIDENT,
            location_id=road_id,
            coordinates=coordinates or (13.935, -89.028),
            tick=current_tick,
            involved_human_ids=[str(human.uid)],
            severity=severity,
            property_damage_usd=prop_loss,
            injury_sustained=severity > 0.40,
            causal_factors=causal_factors,
            is_resolved=False,
        )
        self.accident_history.append(accident)

        # Apply consequences to human
        human.physical_state.money = max(0.0, round(human.physical_state.money - (prop_loss * 0.3), 2))
        human.physical_state.energy = max(0.05, human.physical_state.energy - 0.20)

        # Inflict physical trauma if severe
        if accident.injury_sustained and health_engine:
            injury = health_engine.create_workplace_trauma(tick=current_tick, task="Tránsito / Carretera")
            injury.name = "Traumatismo por Accidente de Tránsito"
            injury.severity = severity
            getattr(human, "active_health_conditions", []).append(injury)

        logger.warning("Traffic accident %s on %s involving %s (sev=%.2f)", acc_id, road_id, human.name, severity)
        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.ACCIDENT_OCCURRED,
                tick=current_tick,
                source_human_id=human.uid,
                location_id=road_id,
                coordinates=accident.coordinates,
                data=accident.to_dict(),
                importance=0.75,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"Accidente vial de {human.name} en {road_id}")

        return accident

    # -------------------------------------------------------------------------
    # Workplace Hazards & Trauma
    # -------------------------------------------------------------------------

    def evaluate_workplace_incident(
        self,
        human: Any,
        task_hazard_level: float,
        current_tick: Tick,
        health_engine: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
        coordinates: Optional[tuple[float, float]] = None,
        probability_scale: float = 1.0,
    ) -> Optional[AccidentEvent]:
        """Evaluate acute workplace injury hazard (machete cut, carpentry laceration, fall)."""
        energy = getattr(human.physical_state, "energy", 0.5)

        # High fatigue increases occupational mishaps by 3x
        fatigue_multiplier = 3.0 if energy < 0.25 else 1.0
        injury_prob = task_hazard_level * 0.04 * fatigue_multiplier * max(0.0, probability_scale)

        if self._rng.random() >= injury_prob:
            return None

        severity = round(float(self._rng.uniform(0.35, 0.75)), 2)
        acc_id = f"work_{uuid.uuid4().hex[:8]}"
        accident = AccidentEvent(
            accident_id=acc_id,
            accident_type=AccidentType.WORKPLACE_INJURY,
            location_id=getattr(human.physical_state, "work_location_id", "taller_artesanal"),
            coordinates=coordinates or (13.935, -89.028),
            tick=current_tick,
            involved_human_ids=[str(human.uid)],
            severity=severity,
            injury_sustained=True,
            causal_factors=["riesgo_ocupacional", "fatiga" if energy < 0.25 else "descuido_momentaneo"],
        )
        self.accident_history.append(accident)

        if health_engine:
            injury = health_engine.create_workplace_trauma(tick=current_tick, task="Labores Físicas")
            injury.severity = severity
            getattr(human, "active_health_conditions", []).append(injury)

        logger.warning("Workplace injury %s suffered by %s", acc_id, human.name)
        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.INJURY_SUSTAINED,
                tick=current_tick,
                source_human_id=human.uid,
                location_id=accident.location_id,
                coordinates=accident.coordinates,
                data=accident.to_dict(),
                importance=0.7,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"Accidente laboral de {human.name}: {accident.causal_factors}")

        return accident

    def evaluate_domestic_incident(
        self,
        human: Any,
        housing_quality: float,
        current_tick: Tick,
        health_engine: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
        coordinates: Optional[tuple[float, float]] = None,
        probability_scale: float = 1.0,
    ) -> Optional[AccidentEvent]:
        """Evaluate falls and burns at home from age, fatigue and dwelling quality.

        The hazard is contextual: elderly residents, exhausted workers and
        dwellings with poor quality (lighting, stairs, cooking surfaces) face
        a higher risk.  It is not a random label attached to an arbitrary agent.
        """
        age = float(getattr(human.demographics, "age", 30))
        energy = float(getattr(human.physical_state, "energy", 0.5))
        age_factor = max(0.0, (age - 55.0) * 0.0012)
        fatigue_factor = max(0.0, (0.35 - energy) * 0.05)
        dwelling_factor = max(0.0, (0.75 - housing_quality) * 0.035)
        incident_prob = (0.0025 + age_factor + fatigue_factor + dwelling_factor) * max(0.0, probability_scale)

        if self._rng.random() >= incident_prob:
            return None

        severity = round(float(self._rng.uniform(0.20, 0.65)), 2)
        acc_id = f"dom_{uuid.uuid4().hex[:8]}"
        factors = ["vivienda"]
        if age >= 65:
            factors.append("adulto_mayor")
        if energy < 0.25:
            factors.append("fatiga")
        if housing_quality < 0.50:
            factors.append("vivienda_precaria")
        accident = AccidentEvent(
            accident_id=acc_id,
            accident_type=AccidentType.DOMESTIC_FALL,
            location_id=getattr(human.physical_state, "current_location_id", "casa_norte_1"),
            coordinates=coordinates or (13.935, -89.028),
            tick=current_tick,
            involved_human_ids=[str(human.uid)],
            severity=severity,
            injury_sustained=severity > 0.30,
            causal_factors=factors,
        )
        self.accident_history.append(accident)

        if accident.injury_sustained:
            human.physical_state.energy = max(0.05, human.physical_state.energy - 0.15)
            if health_engine:
                injury = health_engine.create_workplace_trauma(tick=current_tick, task="Hogar")
                injury.name = "Traumatismo Doméstico / Caída"
                injury.severity = severity
                getattr(human, "active_health_conditions", []).append(injury)

        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.ACCIDENT_OCCURRED,
                tick=current_tick,
                source_human_id=human.uid,
                location_id=accident.location_id,
                coordinates=accident.coordinates,
                data=accident.to_dict(),
                importance=0.62,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"Accidente doméstico de {human.name}: {factors}")
        return accident

    # -------------------------------------------------------------------------
    # Environmental Disasters (Floods & Landslides)
    # -------------------------------------------------------------------------

    def trigger_environmental_disaster(
        self,
        disaster_type: DisasterType,
        affected_location_ids: list[LocationID],
        severity: float,
        current_tick: Tick,
        roads_to_block: Optional[list[str]] = None,
        housing_engine: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
        coordinates: Optional[tuple[float, float]] = None,
    ) -> DisasterEvent:
        """Trigger an environmental disaster with physical damage and road blockages."""
        d_id = f"dis_{uuid.uuid4().hex[:8]}"
        roads = roads_to_block or ["carretera_los_chorros", "camino_puente_suchitoto"]
        for r in roads:
            self.blocked_roads.add(r)

        damaged_units: list[str] = []
        displaced_agents: list[str] = []

        # If housing engine available, damage dwellings and displace occupants
        if housing_engine:
            for u in housing_engine.get_all_units():
                if u.location_id in affected_location_ids or not affected_location_ids:
                    u.quality_score = max(0.20, round(u.quality_score - (severity * 0.40), 2))
                    damaged_units.append(u.unit_id)
                    # Displace occupants if severe
                    if severity > 0.60:
                        for occ in list(u.occupant_uids):
                            displaced_agents.append(occ)

        disaster = DisasterEvent(
            disaster_id=d_id,
            disaster_type=disaster_type,
            affected_location_ids=affected_location_ids,
            tick=current_tick,
            severity=severity,
            roads_blocked=roads,
            housing_damaged_ids=damaged_units,
            displaced_human_ids=displaced_agents,
            water_sources_contaminated=["rio_suchiacel", "pozo_comunal"],
            estimated_loss_usd=round(severity * 450.0, 2),
            is_active=True,
            recovery_progress=0.0,
        )
        self.disaster_history.append(disaster)

        logger.warning("Disaster %s (%s) struck %d locations. Roads blocked: %s", d_id, disaster_type.value, len(affected_location_ids), roads)
        if event_bus:
            evt_dis = SimulationEvent(
                event_type=EventType.DISASTER_OCCURRED,
                tick=current_tick,
                location_id=affected_location_ids[0] if affected_location_ids else "territorio",
                coordinates=coordinates,
                data=disaster.to_dict(),
                importance=0.9,
            )
            event_bus.emit(evt_dis)
            if causal_graph:
                causal_graph.add_event(evt_dis, description=f"Desastre de {disaster_type.value} azotó Suchitoto (severidad={severity:.2f})")

            for r in roads:
                evt_rb = SimulationEvent(
                    event_type=EventType.ROAD_BLOCKED,
                    tick=current_tick,
                    location_id=r,
                    data={"disaster_id": d_id, "road_id": r},
                    importance=0.7,
                )
                event_bus.emit(evt_rb)
                if causal_graph:
                    causal_graph.add_event(evt_rb, cause_event_id=str(evt_dis.event_id), description=f"Vía {r} bloqueada por escombros")

        return disaster

    def resolve_community_disaster_recovery(
        self,
        disaster_id: str,
        volunteers_count: int,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
    ) -> bool:
        """Community organizing faena clears road debris and restores damaged routes."""
        disaster = next((d for d in self.disaster_history if d.disaster_id == disaster_id), None)
        if not disaster or not disaster.is_active:
            return False

        # Progress proportional to community solidarity
        progress_boost = min(1.0, 0.40 + (volunteers_count * 0.15))
        disaster.recovery_progress = min(1.0, disaster.recovery_progress + progress_boost)

        if disaster.recovery_progress >= 0.99:
            disaster.is_active = False
            for r in list(disaster.roads_blocked):
                if r in self.blocked_roads:
                    self.blocked_roads.remove(r)
                if event_bus:
                    evt_open = SimulationEvent(
                        event_type=EventType.ROAD_REOPENED,
                        tick=current_tick,
                        location_id=r,
                        data={"road_id": r, "cleared_by_volunteers": volunteers_count},
                        importance=0.65,
                    )
                    event_bus.emit(evt_open)
                    if causal_graph:
                        causal_graph.add_event(evt_open, description=f"Vía {r} reabierta tras faena comunitaria de {volunteers_count} vecinos")

            logger.info("Disaster %s resolved through community recovery faena", disaster_id)

        return True

    # -------------------------------------------------------------------------
    # Theft, Robbery & Economic Victimization
    # -------------------------------------------------------------------------

    def execute_theft_incident(
        self,
        victim: Any,
        perpetrator: Any,
        stolen_amount_usd: float,
        current_tick: Tick,
        event_bus: Optional[Any] = None,
        causal_graph: Optional[Any] = None,
        coordinates: Optional[tuple[float, float]] = None,
    ) -> dict[str, Any]:
        """Model criminal theft / robbery with monetary transfer and psychological distress."""
        actual_stolen = min(victim.physical_state.money, stolen_amount_usd)
        victim.physical_state.money = round(victim.physical_state.money - actual_stolen, 2)
        perpetrator.physical_state.money = round(perpetrator.physical_state.money + actual_stolen, 2)

        acc_id = f"theft_{uuid.uuid4().hex[:8]}"
        accident = AccidentEvent(
            accident_id=acc_id,
            accident_type=AccidentType.THEFT_ROBBERY,
            location_id=getattr(victim.physical_state, "current_location_id", "plaza_central"),
            coordinates=coordinates or (13.935, -89.028),
            tick=current_tick,
            involved_human_ids=[str(victim.uid), str(perpetrator.uid)],
            severity=0.55,
            property_damage_usd=actual_stolen,
            causal_factors=["oportunidad", "vulnerabilidad"],
        )
        self.accident_history.append(accident)

        logger.warning("%s was robbed of $%.2f by %s", victim.name, actual_stolen, perpetrator.name)
        if event_bus:
            evt = SimulationEvent(
                event_type=EventType.PROPERTY_DAMAGED,
                tick=current_tick,
                source_human_id=perpetrator.uid,
                target_human_id=victim.uid,
                location_id=accident.location_id,
                coordinates=accident.coordinates,
                data={
                    "theft_id": acc_id,
                    "stolen_usd": actual_stolen,
                    "victim_balance": victim.physical_state.money,
                },
                importance=0.8,
            )
            event_bus.emit(evt)
            if causal_graph:
                causal_graph.add_event(evt, description=f"{victim.name} fue víctima de hurto de ${actual_stolen:.2f} por {perpetrator.name}")

        return {
            "success": True,
            "stolen_amount_usd": actual_stolen,
            "victim_remaining_usd": victim.physical_state.money,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize accident, disaster and road state for checkpointing."""
        return {
            "accidents": [a.to_dict() for a in self.accident_history],
            "disasters": [d.to_dict() for d in self.disaster_history],
            "blocked_roads": sorted(self.blocked_roads),
        }

    def load_dict(self, data: dict[str, Any]) -> None:
        """Restore accident and disaster history from a checkpoint."""
        self.accident_history.clear()
        self.disaster_history.clear()
        self.blocked_roads = set(data.get("blocked_roads", []))
        for a in data.get("accidents", []):
            self.accident_history.append(AccidentEvent(
                accident_id=a["accident_id"],
                accident_type=AccidentType(a.get("accident_type", "traffic_accident")),
                location_id=a.get("location_id", "plataforma"),
                coordinates=tuple(a.get("coordinates", (13.935, -89.028))),
                tick=int(a.get("tick", 0)),
                involved_human_ids=list(a.get("involved_human_ids", [])),
                severity=float(a.get("severity", 0.5)),
                property_damage_usd=float(a.get("property_damage_usd", 0.0)),
                injury_sustained=bool(a.get("injury_sustained", False)),
                causal_factors=list(a.get("causal_factors", [])),
                is_resolved=bool(a.get("is_resolved", False)),
            ))
        for d in data.get("disasters", []):
            self.disaster_history.append(DisasterEvent(
                disaster_id=d["disaster_id"],
                disaster_type=DisasterType(d.get("disaster_type", "flooding")),
                affected_location_ids=list(d.get("affected_location_ids", [])),
                affected_area_m2=float(d.get("affected_area_m2", 2500.0)),
                tick=int(d.get("tick", 0)),
                severity=float(d.get("severity", 0.65)),
                roads_blocked=list(d.get("roads_blocked", [])),
                housing_damaged_ids=list(d.get("housing_damaged_ids", [])),
                displaced_human_ids=list(d.get("displaced_human_ids", [])),
                water_sources_contaminated=list(d.get("water_sources_contaminated", [])),
                estimated_loss_usd=float(d.get("estimated_loss_usd", 0.0)),
                is_active=bool(d.get("is_active", True)),
                recovery_progress=float(d.get("recovery_progress", 0.0)),
            ))
