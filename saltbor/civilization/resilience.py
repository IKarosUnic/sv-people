"""Civilization Resilience and Crisis Engine for SALTBOR Phase 1.0.

Simulates civilization-level stress, systemic crisis, adaptive response, and transformation:
- Shocks: drought, flood, landslides, crop failures, commercial disruption, infrastructure loss, conflict, simulated epidemic, institutional collapse.
- Adaptive response mechanisms: resource pooling/redistribution, emergency migration, technical adaptation, institutional reform, conflict, settlement abandonment.
- Outcomes: resilient recovery, permanent transformation, irreversible fragmentation, or demographic collapse.
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


class AdaptationStrategy(str, Enum):
    RESOURCE_POOLING = "resource_pooling"
    EMERGENCY_MIGRATION = "emergency_migration"
    TECHNICAL_ADAPTATION = "technical_adaptation"
    REORGANIZATION = "reorganization"
    SETTLEMENT_ABANDONMENT = "settlement_abandonment"
    CONFLICT = "conflict"


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


class CivilizationResilienceEngine:
    """Evaluates systemic resilience and simulates community survival during macro shocks."""

    def __init__(self) -> None:
        self.crises: Dict[str, CrisisEvent] = {}

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
