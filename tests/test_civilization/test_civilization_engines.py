"""Unit and integration tests for Phase 1.0 Civilization Evolution Engines."""

import pytest
from saltbor.civilization.economy import (
    EconomicCivilizationEngine,
    EconomicSector,
    Enterprise,
)
from saltbor.civilization.engine import (
    CivilizationEvolutionEngine,
    CivilizationPhase,
    CivilizationState,
)
from saltbor.civilization.graph import (
    HistoricalKnowledgeGraph,
    HistoricalNodeType,
    HistoricalRelType,
)
from saltbor.civilization.history import (
    HistoricalCategory,
    HistoricalMemoryEngine,
)
from saltbor.civilization.interaction import (
    MultiSocietyInteractionEngine,
    RelationType,
)
from saltbor.civilization.migration import (
    MigrationDynamicsEngine,
    MigrationReason,
    MigrationStatus,
)
from saltbor.civilization.multigenerational import (
    MultiGenerationalEngine,
)
from saltbor.civilization.resilience import (
    AdaptationStrategy,
    CivilizationResilienceEngine,
    CrisisType,
)
from saltbor.civilization.settlement import (
    SettlementEvolutionEngine,
    SettlementStatus,
    SettlementType,
)
from saltbor.civilization.stratification import (
    SocialStratificationEngine,
    SocialTier,
)
from saltbor.civilization.technology import (
    InnovationStatus,
    KnowledgeDomain,
    TechnologicalEvolutionEngine,
)


def test_civilization_evolution_foundation_and_growth():
    civ_engine = CivilizationEvolutionEngine()
    civ = civ_engine.found_civilization("Cuscatlán", territory="El Salvador", initial_year=2026.0)
    assert civ.name == "Cuscatlán"
    assert civ.phase == CivilizationPhase.EMERGING
    assert len(civ.settlement_ids) == 1

    # Populate settlement
    for i in range(50):
        civ_engine.settlements.add_inhabitant(civ.settlement_ids[0], f"inhabitant_{i}")

    civ_engine.evolve_step(civ.civilization_id, delta_years=2.0)
    assert civ.current_year == 2028.0
    assert civ.population_count == 50
    assert civ.phase == CivilizationPhase.GROWING


def test_historical_memory_ground_truth_and_narrative_drift():
    mem = HistoricalMemoryEngine()
    ev = mem.record_ground_truth(
        category=HistoricalCategory.INNOVATION,
        tick=100,
        year=2030.0,
        location="Santa Ana",
        actors=["Gremio Textil"],
        title="Invención del telar hidroneumático",
        description="Nuevo sistema de tejido impulsado por corriente de río.",
        significance=0.8,
    )
    assert ev.event_id in mem.ground_truth

    narrative = mem.form_cultural_narrative("soc_santa_ana", ev.event_id, framing="heroico")
    assert narrative.drift_factor == 0.05

    # 3 generations pass
    for _ in range(3):
        mem.transmit_narrative(narrative.narrative_id, fidelity_loss=0.15)
    assert narrative.transmission_count == 4
    assert narrative.drift_factor > 0.4


def test_settlement_scale_transitions():
    s_engine = SettlementEvolutionEngine()
    s = s_engine.found_settlement("Los Laureles", SettlementType.CASERIO, "Santa Tecla", "La Libertad", (13.67, -89.28))
    assert s.settlement_type == SettlementType.CASERIO

    # Add inhabitants to trigger transition
    for i in range(35):
        s_engine.add_inhabitant(s.settlement_id, f"p_{i}")
    assert s.settlement_type in (SettlementType.ALDEA, SettlementType.COMUNIDAD_RURAL)

    s.resources.infrastructure_level = 0.6
    for i in range(35, 120):
        s_engine.add_inhabitant(s.settlement_id, f"p_{i}")
    assert s.settlement_type in (SettlementType.BARRIO, SettlementType.NUCLEO_COMERCIAL)


def test_migration_and_remittances():
    mig = MigrationDynamicsEngine()
    record = mig.initiate_migration("migrant_a", "settle_rural", "settle_urban", MigrationReason.ECONOMIC_OPPORTUNITY, tick=50)
    assert record.status == MigrationStatus.IN_TRANSIT

    mig.complete_migration(record.migration_id, arrival_tick=60)
    assert record.status == MigrationStatus.SETTLED

    mig.send_remittance(record.migration_id, 250.0)
    assert mig.remittances_by_settlement["settle_rural"] == 250.0


def test_economic_intergenerational_inheritance():
    econ = EconomicCivilizationEngine()
    ent = econ.establish_enterprise("Agropecuaria El Progreso", EconomicSector.AGRICULTURE, "founder_a", initial_capital=200.0)
    ent.capital = 500.0

    econ.inherit_enterprise(ent.enterprise_id, "heir_b", transferred_capital_fraction=0.8)
    assert ent.owner_id == "heir_b"
    assert ent.generation_inherited == 1
    assert ent.capital == 400.0


def test_technology_material_constraints():
    tech = TechnologicalEvolutionEngine()
    t = tech.register_innovation_concept(
        "Purificador Solar",
        KnowledgeDomain.ENVIRONMENTAL,
        material_requirements=["filtro_ceramico", "espejo_concavo"],
    )
    # Fails if missing materials
    success_fail = tech.attempt_discovery(t.tech_id, "p1", "s1", ["espejo_concavo"], set())
    assert not success_fail
    assert t.status == InnovationStatus.HYPOTHESIS

    # Succeeds with all materials
    success_ok = tech.attempt_discovery(t.tech_id, "p1", "s1", ["filtro_ceramico", "espejo_concavo"], set())
    assert success_ok
    assert t.status == InnovationStatus.VALIDATED


def test_stratification_and_gini_calculation():
    strat = SocialStratificationEngine()
    strat.register_profile("p1", wealth=500.0, income=80.0, education=0.8)
    strat.register_profile("p2", wealth=450.0, income=75.0, education=0.7)
    strat.register_profile("p3", wealth=40.0, income=10.0, education=0.1)

    gini = strat.calculate_wealth_gini()
    assert 0.0 < gini < 1.0


def test_civilization_resilience_crisis_resolution():
    res = CivilizationResilienceEngine()
    crisis = res.trigger_crisis(CrisisType.FLOOD, severity=0.5, affected_settlements=["s_costa"], tick_start=10)
    outcome = res.resolve_crisis_step(crisis.crisis_id, resilience_score=0.6)
    assert outcome["resolved"] is True
    assert outcome["strategy"] == AdaptationStrategy.RESOURCE_POOLING.value


def test_historical_knowledge_graph_traversal():
    h_graph = HistoricalKnowledgeGraph()
    h_graph.add_historical_entity("settle_san_salvador", "San Salvador", HistoricalNodeType.SETTLEMENT, year=1525.0)
    h_graph.add_historical_entity("p_founder", "Gonzalo de Alvarado", HistoricalNodeType.PERSON, year=1525.0)
    h_graph.link_historical_relation("p_founder", "settle_san_salvador", HistoricalRelType.FOUNDED, year=1525.0)

    res = h_graph.query_settlement_emergence("settle_san_salvador")
    assert "p_founder" in res["founders"]
