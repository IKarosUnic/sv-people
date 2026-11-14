"""Civilization Resilience, Crisis and Environmental Interdependence Engine for SALTBOR Phase 1.11.

Simulates civilization-level stress, systemic crisis, adaptive response, and environmental feedback:
- Shocks: drought, flood, landslides, crop failures, commercial disruption, infrastructure loss,
  conflict, simulated epidemic, institutional collapse.
- Adaptive response mechanisms: resource pooling/redistribution, emergency migration, technical adaptation,
  institutional reform, conflict, settlement abandonment.
- Environmental Feedback Loop:
  Population growth -> resource demand -> environmental pressure -> agricultural decline -> migration -> settlement change.
  Or reverse:
  Community cooperation (ADESCO faenas) -> ecosystem restoration -> improved resources -> greater resilience.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from saltbor.core.types import Tick


class CrisisType(str, Enum):
    DROUGHT = "drought"
    FLOOD = "flood"
    LANDSLIDE = "landslide"
    FOOD_SCARCITY = "food_scarcity"
    ECONOMIC_COLLAPSE = "economic_collapse"
    TRADE_BLOCKADE = "trade_blockade"
    EPIDEMIC = "epidemic"
    INSTITUTIONAL_CRISIS = "institutional_crisis"
    ENVIRONMENTAL_DEGRADATION = "environmental_degradation"


class AdaptationStrategy(str, Enum):
    RESOURCE_POOLING = "resource_pooling"
    EMERGENCY_MIGRATION = "emergency_migration"
    TECHNICAL_ADAPTATION = "technical_adaptation"
    REORGANIZATION = "reorganization"
    SETTLEMENT_ABANDONMENT = "settlement_abandonment"
    CONFLICT = "conflict"
    COMMUNAL_RESTORATION = "communal_restoration"


@dataclass
class CrisisEvent:
    crisis_id: str
    crisis_type: CrisisType
    severity: float  # 0.0 to 1.0
    affected_settlement_ids: List[str]
    tick_start: Tick
    duration_ticks: int
    resolved: bool = False
    chosen_strategy: Optional[AdaptationStrategy] = None
    damage_assessment: Dict[str, float] = field(default_factory=dict)


@dataclass
class EnvironmentalState:
    settlement_id: str
    forest_cover: float = 0.65  # 0.0 to 1.0
    water_table_level: float = 0.80  # 0.0 (parched) to 1.0 (abundant)
    soil_fertility: float = 0.70  # 0.0 (eroded) to 1.0 (fertile)
    cumulative_erosion: float = 0.10
    annual_recharge_rate: float = 0.15
    extraction_pressure: float = 0.12


@dataclass
class EnvironmentalFeedbackResult:
    settlement_id: str
    new_water_table: float
    new_soil_fertility: float
    agricultural_yield_multiplier: float
    out_migration_pressure: float  # 0.0 to 1.0
    restoration_achieved: bool


class CivilizationResilienceEngine:
    """Evaluates systemic resilience, crisis resolution, and bidirectional environmental feedbacks."""

    def __init__(self) -> None:
        self.crises: Dict[str, CrisisEvent] = {}
        self.environmental_states: Dict[str, EnvironmentalState] = {}

    def ensure_environmental_state(self, settlement_id: str) -> EnvironmentalState:
        if settlement_id not in self.environmental_states:
            self.environmental_states[settlement_id] = EnvironmentalState(settlement_id=settlement_id)
        return self.environmental_states[settlement_id]

    def trigger_crisis(
        self,
        crisis_type: CrisisType,
        severity: float,
        affected_settlements: List[str],
        tick_start: Tick,
        duration_ticks: int = 50,
    ) -> CrisisEvent:
        c_id = f"crisis_{uuid4().hex[:8]}"
        crisis = CrisisEvent(
            crisis_id=c_id,
            crisis_type=crisis_type,
            severity=max(0.1, min(1.0, severity)),
            affected_settlement_ids=list(affected_settlements),
            tick_start=tick_start,
            duration_ticks=duration_ticks,
        )
        self.crises[c_id] = crisis
        return crisis

    def evaluate_settlement_resilience(
        self,
        infrastructure_level: float,
        resource_reserve: float,
        social_cohesion: float,
        institutional_capacity: float,
    ) -> float:
        """Composite resilience score (0.0 to 1.0)."""
        score = (
            infrastructure_level * 0.25 +
            min(1.0, resource_reserve / 100.0) * 0.30 +
            social_cohesion * 0.25 +
            institutional_capacity * 0.20
        )
        return max(0.0, min(1.0, score))

    def resolve_crisis_step(
        self,
        crisis_id: str,
        resilience_score: float,
    ) -> Dict[str, Any]:
        """Calculates adaptation outcome based on severity vs resilience."""
        if crisis_id not in self.crises:
            return {"resolved": False, "strategy": None, "loss": 0.0}
        crisis = self.crises[crisis_id]

        gap = crisis.severity - resilience_score
        if gap <= 0:
            # Successfully absorbed
            crisis.resolved = True
            crisis.chosen_strategy = AdaptationStrategy.RESOURCE_POOLING
            loss = crisis.severity * 0.1
        elif gap < 0.3:
            # Requires active adaptation
            crisis.chosen_strategy = AdaptationStrategy.TECHNICAL_ADAPTATION
            loss = gap * 0.4
        elif gap < 0.6:
            # Significant stress: emergency migration & reorganization
            crisis.chosen_strategy = AdaptationStrategy.EMERGENCY_MIGRATION
            loss = gap * 0.7
        else:
            # Severe catastrophe: displacement or abandonment
            crisis.chosen_strategy = AdaptationStrategy.SETTLEMENT_ABANDONMENT
            loss = 0.9

        crisis.damage_assessment = {"loss_ratio": round(loss, 3), "gap": round(gap, 3)}
        return {
            "resolved": crisis.resolved,
            "strategy": crisis.chosen_strategy.value if crisis.chosen_strategy else None,
            "loss_ratio": loss,
        }

    def evaluate_environmental_feedback(
        self,
        settlement_id: str,
        population_count: int,
        cooperation_index: float = 0.5,
        faena_conservation_hours: float = 0.0,
        current_water_level: Optional[float] = None,
        current_soil_fertility: Optional[float] = None,
    ) -> EnvironmentalFeedbackResult:
        """Simulates bidirectional feedback between population pressure and ecosystem viability.
        
        Feedback:
        - High population with low cooperation extracts water and degrades soil -> yields fall -> out-migration rises.
        - High cooperation and faenas reforest and terrace slopes -> soil fertility improves -> yields rise.
        """
        env = self.ensure_environmental_state(settlement_id)
        if current_water_level is not None:
            env.water_table_level = max(0.01, min(1.0, current_water_level))
        if current_soil_fertility is not None:
            env.soil_fertility = max(0.01, min(1.0, current_soil_fertility))

        # Extraction pressure scales with population
        env.extraction_pressure = min(1.0, (population_count / 150.0) * 0.25)

        # Restoration effect from communal faenas
        restoration = min(0.30, faena_conservation_hours * 0.015 + cooperation_index * 0.05)

        # Net water table adjustment
        net_water = env.annual_recharge_rate - env.extraction_pressure + (restoration * 0.5)
        env.water_table_level = max(0.05, min(1.0, env.water_table_level + net_water))

        # Soil degradation or recovery
        if env.extraction_pressure > 0.40 and cooperation_index < 0.40:
            env.soil_fertility = max(0.10, env.soil_fertility - 0.05)
            env.cumulative_erosion = min(1.0, env.cumulative_erosion + 0.06)
        elif restoration > 0.10:
            env.soil_fertility = min(1.0, env.soil_fertility + 0.04)
            env.forest_cover = min(1.0, env.forest_cover + 0.03)

        # Agricultural yield multiplier derived from soil and water
        yield_multiplier = (env.soil_fertility * 0.55 + env.water_table_level * 0.45) * 1.2

        # Distress migration pressure rises when yields collapse
        distress_migration = 0.0
        if yield_multiplier < 0.50:
            distress_migration = min(1.0, (0.50 - yield_multiplier) * 2.0)

        restoration_achieved = (restoration > 0.08)

        return EnvironmentalFeedbackResult(
            settlement_id=settlement_id,
            new_water_table=round(env.water_table_level, 3),
            new_soil_fertility=round(env.soil_fertility, 3),
            agricultural_yield_multiplier=round(yield_multiplier, 3),
            out_migration_pressure=round(distress_migration, 3),
            restoration_achieved=restoration_achieved,
        )
