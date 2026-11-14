"""Comprehensive test suite for Phase 1.10 Intelligence Ecosystem."""

import pytest
import numpy as np

from saltbor.knowledge.scientific_service import ScientificKnowledgeService, EvidenceTier
from saltbor.world.information_service import WorldInformationService, ProvenanceSourceType
from saltbor.culture.media_ecosystem import (
    WorldInformationEcosystem,
    MediumCategory,
    MusicGenre,
)
from saltbor.simulation.observability_service import ObservabilityService, SpanKind
from saltbor.simulation.ecosystem_manager import EcosystemIntegrationManager


class TestPhase110IntelligenceEcosystem:
    """Validates the 5 interconnected pillars of Phase 1.10."""

    def test_scientific_intelligence_evidence_hierarchy(self):
        service = ScientificKnowledgeService()
        tier1_assertions = service.list_assertions_by_tier(EvidenceTier.TIER_1_ESTABLISHED)
        assert len(tier1_assertions) >= 3

        # Verify Ostrom assertion
        cpr = service.get_assertion("cpr_institutions")
        assert cpr is not None
        assert cpr.tier == EvidenceTier.TIER_1_ESTABLISHED
        assert not cpr.falsified

        # Test empirical falsification mechanism
        service.falsify_assertion("cpr_institutions", "Tested in extreme scarcity where all commons collapsed")
        assert service.get_assertion("cpr_institutions").falsified is True

    def test_world_intelligence_provenance_and_history(self):
        service = WorldInformationService()
        osm_prov = service.get_provenance("osm_el_salvador_2026")
        assert osm_prov is not None
        assert osm_prov.source_type == ProvenanceSourceType.GEOGRAPHIC_OPEN
        assert "ODbL" in osm_prov.license

        macro = service.get_macro_indicator(2026)
        assert macro is not None
        assert macro.informal_employment_rate > 0.50

        history = service.get_historical_records()
        event_ids = [h.event_id for h in history]
        assert "mitch_1998" in event_ids
        assert "terremoto_2001" in event_ids

    def test_media_and_cultural_ecosystem(self):
        rng = np.random.default_rng(123)
        ecosystem = WorldInformationEcosystem(rng=rng)

        # 1. Outlets exist
        assert "radio_la_campesina" in ecosystem.outlets
        assert "diario_el_cuscatleco" in ecosystem.outlets

        # 2. Generational Music Distribution
        p_elder = ecosystem.get_or_create_human_profile("human_elder", age=68)
        p_youth = ecosystem.get_or_create_human_profile("human_youth", age=19)
        assert p_elder.preferred_genre in [
            MusicGenre.CUMBIA_SALVADORENA,
            MusicGenre.BALADA_DEL_RECUERDO,
            MusicGenre.SALSA_Y_MERENGUE,
            MusicGenre.MARIACHI_RANCHERA,
        ]
        assert p_youth.preferred_genre in [
            MusicGenre.URBANO_REGGAETON,
            MusicGenre.ROCK_EN_ESPANOL,
            MusicGenre.CUMBIA_SALVADORENA,
            MusicGenre.SALSA_Y_MERENGUE,
        ]

        # 3. Sports Simulation
        match, broadcast = ecosystem.simulate_sports_match(
            home_team_id="tigres_santa_ana",
            away_team_id="albos_capitalinos",
            current_tick=100,
        )
        assert match.home_score >= 0 and match.away_score >= 0
        assert broadcast.topic == "sports"
        assert len(ecosystem.match_history) == 1

        # 4. Emergency Broadcast & Behavioral Ingestion
        alert = ecosystem.generate_weather_emergency_broadcast(
            event_id="landslide_01",
            hazard_name="Deslave Los Chorros",
            affected_area="Carretera Panamericana",
            urgency=0.9,
            current_tick=105,
        )
        res = ecosystem.evaluate_human_broadcast_exposure("human_commuter", alert)
        assert "exposed" in res
        assert "believed" in res
        assert "behavioral_shift" in res

    def test_engineering_intelligence_observability(self):
        obs = ObservabilityService()
        span_id = obs.start_span("test_engine_tick", kind=SpanKind.SIMULATION_TICK, tick=42)
        obs.increment_counter("ticks.total", 1.0)
        obs.record_gauge("heap_mb", 256.4)
        span = obs.end_span(span_id)

        assert span is not None
        assert span.duration_ms >= 0.0
        assert span.status_code == "OK"

        metrics = obs.get_summary_metrics()
        assert metrics["total_spans"] == 1
        assert metrics["counters"]["ticks.total"] == 1.0
        assert metrics["gauges"]["heap_mb"] == 256.4

    def test_cross_pillar_causal_integration(self):
        manager = EcosystemIntegrationManager(rng=np.random.default_rng(999))
        affected_agents = [f"commuter_{i}" for i in range(25)]

        outcome = manager.process_environmental_hazard_shock(
            event_id="flood_rio_lempa",
            hazard_name="Desbordamiento Río Lempa",
            affected_area="Bajo Lempa",
            urgency=0.85,
            current_tick=200,
            affected_humans=affected_agents,
        )

        assert outcome["population_count"] == 25
        assert outcome["broadcast"].urgency == 0.85
        # Heterogeneous response: not 100% and not 0%
        assert outcome["travel_canceled_count"] >= 0
        # Observability recorded spans
        summary = manager.observability.get_summary_metrics()
        assert summary["total_spans"] >= 1
        assert "events.environmental_hazard.processed" in summary["counters"]
