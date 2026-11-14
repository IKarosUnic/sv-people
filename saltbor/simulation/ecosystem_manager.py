"""Unified Ecosystem Integration Manager connecting the Five Intelligence Pillars.

Glues:
1. Agent Intelligence (Skills & Graphify provenance)
2. Scientific Intelligence (ScientificKnowledgeService)
3. World Intelligence (WorldInformationService & RealGeographicEngine)
4. Media & Cultural Intelligence (WorldInformationEcosystem)
5. Engineering Intelligence (ObservabilityService & Telemetry)
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

from saltbor.core.types import HumanID, Tick
from saltbor.culture.media_ecosystem import MediaBroadcast, WorldInformationEcosystem
from saltbor.knowledge.scientific_service import ScientificKnowledgeService
from saltbor.simulation.observability_service import ObservabilityService, SpanKind
from saltbor.world.information_service import WorldInformationService

logger = logging.getLogger(__name__)


class EcosystemIntegrationManager:
    """Coordinates cross-pillar causality, data flows, and telemetry."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng(42)
        self.scientific_service = ScientificKnowledgeService()
        self.world_info_service = WorldInformationService()
        self.media_ecosystem = WorldInformationEcosystem(rng=self.rng)
        self.observability = ObservabilityService()

    def process_environmental_hazard_shock(
        self,
        event_id: str,
        hazard_name: str,
        affected_area: str,
        urgency: float,
        current_tick: Tick,
        affected_humans: list[HumanID],
    ) -> dict[str, Any]:
        """Trigger an environmental crisis and trace its multi-pillar causal consequences."""
        span_id = self.observability.start_span(
            name="ecosystem.environmental_hazard_pipeline",
            kind=SpanKind.EVENT_DISPATCH,
            tick=current_tick,
            attributes={"hazard": hazard_name, "area": affected_area, "urgency": urgency},
        )

        # 1. Media synthesis: generate public broadcast
        broadcast: MediaBroadcast = self.media_ecosystem.generate_weather_emergency_broadcast(
            event_id=event_id,
            hazard_name=hazard_name,
            affected_area=affected_area,
            urgency=urgency,
            current_tick=current_tick,
        )

        # 2. Human cognitive intake and behavioral shifts
        intake_results: list[dict[str, Any]] = []
        travel_canceled_count = 0
        fear_vigilance_count = 0

        for hid in affected_humans:
            res = self.media_ecosystem.evaluate_human_broadcast_exposure(hid, broadcast)
            intake_results.append(res)
            if res.get("behavioral_shift") == "cancel_travel_and_shelter":
                travel_canceled_count += 1
            if res.get("appraisal_emotion") == "fear_and_vigilance":
                fear_vigilance_count += 1

        self.observability.increment_counter("events.environmental_hazard.processed")
        self.observability.record_gauge("hazard.affected_population", len(affected_humans))
        self.observability.record_gauge("hazard.travel_canceled_ratio", travel_canceled_count / max(1, len(affected_humans)))

        self.observability.end_span(span_id)

        return {
            "broadcast": broadcast,
            "population_count": len(affected_humans),
            "travel_canceled_count": travel_canceled_count,
            "fear_vigilance_count": fear_vigilance_count,
            "intake_results": intake_results,
        }
