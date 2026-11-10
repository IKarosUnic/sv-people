"""EXP_10 Civilization Evolution Suite: Part 1 (EXP_10_A through EXP_10_L).

Covers:
- EXP_10_A: Continuidad multigeneracional.
- EXP_10_B: Evolución demográfica durante varias generaciones.
- EXP_10_C: Formación y transformación de asentamientos.
- EXP_10_D: Migración entre territorios.
- EXP_10_E: Evolución de estructuras familiares.
- EXP_10_F: Transmisión intergeneracional de conocimientos.
- EXP_10_G: Evolución de tradiciones culturales.
- EXP_10_H: Aparición y difusión de innovaciones.
- EXP_10_I: Transformación económica.
- EXP_10_J: Movilidad social intergeneracional.
- EXP_10_K: Formación y transformación institucional.
- EXP_10_L: Evolución de desigualdades.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

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
from saltbor.civilization.migration import (
    MigrationDynamicsEngine,
    MigrationReason,
)
from saltbor.civilization.multigenerational import (
    MultiGenerationalEngine,
)
from saltbor.civilization.settlement import (
    SettlementEvolutionEngine,
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
from saltbor.simulation.experiments.base import (
    BaseExperiment,
    ExperimentConfig,
    ExperimentResult,
)

logger = logging.getLogger(__name__)


class Experiment10_A_MultigenerationalContinuity(BaseExperiment):
    """EXP_10_A: Continuidad multigeneracional a lo largo de 3+ generaciones."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        super().__init__(config or ExperimentConfig(name="EXP_10_A_MultigenerationalContinuity", max_ticks=300))

    def run(self) -> ExperimentResult:
        engine = MultiGenerationalEngine()
        # Gen 0
        p1 = engine.register_founder("p_gen0_1", "Flores", birth_year=1970.0)
        p2 = engine.register_founder("p_gen0_2", "Flores", birth_year=1972.0)
        # Gen 1
        c1 = engine.birth_descendant("p_gen1_1", p1.human_id, p2.human_id, birth_year=1995.0, inherited_skills=["agricultura_cafetalera"])
        # Gen 2
        c2 = engine.birth_descendant("p_gen2_1", c1.human_id, None, birth_year=2020.0, inherited_skills=["agricultura_cafetalera", "comercio_local"])
        # Gen 3
        c3 = engine.birth_descendant("p_gen3_1", c2.human_id, None, birth_year=2045.0, inherited_skills=["gestion_agricola"])

        gen0 = engine.get_generation_cohort(0)
        gen3 = engine.get_generation_cohort(3)

        success = len(gen0) >= 2 and len(gen3) >= 1 and engine.records[c3.human_id].generation_index == 3
        return ExperimentResult(
            success=success,
            ticks_executed=self.config.max_ticks,
            metrics={
                "total_generations": 4,
                "gen0_count": len(gen0),
                "gen3_count": len(gen3),
                "lineage_depth": max(l.generation_depth for l in engine.lineages.values()),
            },
        )


class Experiment10_B_DemographicTurnover(BaseExperiment):
    """EXP_10_B: Evolución demográfica durante varias generaciones."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        super().__init__(config or ExperimentConfig(name="EXP_10_B_DemographicTurnover", max_ticks=300))

    def run(self) -> ExperimentResult:
        engine = MultiGenerationalEngine()
        for i in range(10):
            engine.register_founder(f"init_{i}", f"Linaje_{i}", birth_year=1980.0)

        # Children born
        for i in range(15):
            engine.birth_descendant(f"child_{i}", f"init_{i % 10}", None, birth_year=2005.0)

        # Older generation passes away
        for i in range(8):
            engine.record_death(f"init_{i}", death_year=2025.0)

        living = [r for r in engine.records.values() if r.living]
        deceased = [r for r in engine.records.values() if not r.living]

        success = len(living) == 17 and len(deceased) == 8
        return ExperimentResult(
            success=success,
            ticks_executed=self.config.max_ticks,
            metrics={"living": len(living), "deceased": len(deceased), "cohort_ratio": len(living) / 25.0},
        )


class Experiment10_C_SettlementEvolution(BaseExperiment):
    """EXP_10_C: Formación y transformación gradual de asentamientos."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        super().__init__(config or ExperimentConfig(name="EXP_10_C_SettlementEvolution", max_ticks=300))

    def run(self) -> ExperimentResult:
        engine = SettlementEvolutionEngine()
        settle = engine.found_settlement(
            name="Valle de las Flores",
            settlement_type=SettlementType.CASERIO,
            municipality="Ahuachapán Centro",
            department="Ahuachapán",
            coordinates=(13.921, -89.845),
        )
        # Populate
        for i in range(60):
            engine.add_inhabitant(settle.settlement_id, f"inhabitant_{i}")

        # Develop infrastructure
        engine.develop_infrastructure(settle.settlement_id, investment=4.0)

        evolved_type = settle.settlement_type
        success = evolved_type in (SettlementType.ALDEA, SettlementType.BARRIO, SettlementType.COMUNIDAD_RURAL)
        return ExperimentResult(
            success=success,
            ticks_executed=self.config.max_ticks,
            metrics={
                "settlement_type": evolved_type.value,
                "population": settle.population_count,
                "infrastructure_level": settle.resources.infrastructure_level,
            },
        )


class Experiment10_D_TerritorialMigration(BaseExperiment):
    """EXP_10_D: Migración entre territorios y remesas."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        super().__init__(config or ExperimentConfig(name="EXP_10_D_TerritorialMigration", max_ticks=300))

    def run(self) -> ExperimentResult:
        mig_engine = MigrationDynamicsEngine()
        settle_engine = SettlementEvolutionEngine()

        rural = settle_engine.found_settlement("Caserío El Jocote", SettlementType.CASERIO, "Morazán Sur", "Morazán", (13.7, -88.1))
        urban = settle_engine.found_settlement("San Miguel Centro", SettlementType.CIUDAD, "San Miguel Centro", "San Miguel", (13.48, -88.18))

        # Evaluate migration propensity
        propensity = mig_engine.evaluate_migration_desire(
            human_id="mig_migrant_1",
            current_wealth=150.0,
            current_settlement_opportunity=0.2,
            family_in_destination_count=2,
            destination_opportunity=0.8,
            relocation_cost=40.0,
        )

        rec = mig_engine.initiate_migration("mig_migrant_1", rural.settlement_id, urban.settlement_id, MigrationReason.ECONOMIC_OPPORTUNITY, tick=10)
        mig_engine.complete_migration(rec.migration_id, arrival_tick=25)
        mig_engine.send_remittance(rec.migration_id, amount=120.0)

        success = propensity > 0.5 and mig_engine.remittances_by_settlement.get(rural.settlement_id, 0.0) == 120.0
        return ExperimentResult(
            success=success,
            ticks_executed=self.config.max_ticks,
            metrics={"propensity": propensity, "remittances_received": mig_engine.remittances_by_settlement.get(rural.settlement_id, 0.0)},
        )


class Experiment10_E_FamilyStructures(BaseExperiment):
    """EXP_10_E: Evolución y ramificación de estructuras familiares."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        super().__init__(config or ExperimentConfig(name="EXP_10_E_FamilyStructures", max_ticks=300))

    def run(self) -> ExperimentResult:
        engine = MultiGenerationalEngine()
        f1 = engine.register_founder("f_anc_1", "Navas")
        f2 = engine.register_founder("f_anc_2", "Navas")

        # Two branches
        b1 = engine.birth_descendant("f_b1_1", f1.human_id, f2.human_id, birth_year=2000.0)
        b2 = engine.birth_descendant("f_b2_1", f1.human_id, f2.human_id, birth_year=2002.0)

        # Offspring in each branch
        engine.birth_descendant("f_b1_child", b1.human_id, None, birth_year=2026.0)
        engine.birth_descendant("f_b2_child", b2.human_id, None, birth_year=2028.0)

        lineage = list(engine.lineages.values())[0]
        success = lineage.total_members_count >= 5 and lineage.generation_depth >= 3
        return ExperimentResult(
            success=success,
            ticks_executed=self.config.max_ticks,
            metrics={"members": lineage.total_members_count, "depth": lineage.generation_depth},
        )


class Experiment10_F_KnowledgeTransmission(BaseExperiment):
    """EXP_10_F: Transmisión intergeneracional de conocimientos empíricos."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        super().__init__(config or ExperimentConfig(name="EXP_10_F_KnowledgeTransmission", max_ticks=300))

    def run(self) -> ExperimentResult:
        graph = HistoricalKnowledgeGraph()
        graph.add_historical_entity("p_artisan_parent", "Maestro Alfarero", HistoricalNodeType.PERSON, year=2000.0)
        graph.add_historical_entity("p_apprentice_child", "Aprendiz", HistoricalNodeType.PERSON, year=2024.0)

        graph.link_historical_relation(
            source_id="p_artisan_parent",
            target_id="p_apprentice_child",
            rel_type=HistoricalRelType.TRANSMITTED_TO,
            year=2025.0,
            metadata={"skill": "ceramica_negra_guatajiagua"},
        )

        transmissions = graph.query_intergenerational_transmission("p_artisan_parent")
        success = len(transmissions) > 0 and transmissions[0]["target_id"] == "p_apprentice_child"
        return ExperimentResult(
            success=success,
            ticks_executed=self.config.max_ticks,
            metrics={"transmitted_count": len(transmissions)},
        )


class Experiment10_G_CulturalTraditions(BaseExperiment):
    """EXP_10_G: Evolución y reinterpretación de tradiciones culturales."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        super().__init__(config or ExperimentConfig(name="EXP_10_G_CulturalTraditions", max_ticks=300))

    def run(self) -> ExperimentResult:
        memory = HistoricalMemoryEngine()
        ev = memory.record_ground_truth(
            category=HistoricalCategory.CULTURAL_SHIFT,
            tick=10,
            year=2000.0,
            location="Izalco",
            actors=["Cofradía local"],
            title="Fiesta Tradicional del Maíz",
            description="Ritual agrario comunitario de bendición de cosechas.",
            significance=0.85,
        )

        narrative = memory.form_cultural_narrative("soc_izalco", ev.event_id, framing="ancestral_communal")
        # Generational transmissions induce drift
        for _ in range(4):
            memory.transmit_narrative(narrative.narrative_id, fidelity_loss=0.1)

        recollections = memory.query_collective_recollection("soc_izalco", current_year=2080.0)
        success = narrative.transmission_count == 5 and narrative.drift_factor > 0.3 and len(recollections) > 0
        return ExperimentResult(
            success=success,
            ticks_executed=self.config.max_ticks,
            metrics={"drift": narrative.drift_factor, "transmission_count": narrative.transmission_count},
        )


class Experiment10_H_InnovationDiffusion(BaseExperiment):
    """EXP_10_H: Aparición, difusión y adopción de innovaciones técnicas."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        super().__init__(config or ExperimentConfig(name="EXP_10_H_InnovationDiffusion", max_ticks=300))

    def run(self) -> ExperimentResult:
        engine = TechnologicalEvolutionEngine()
        irrigation = engine.register_innovation_concept(
            name="Riego por Goteo Solar",
            domain=KnowledgeDomain.AGRICULTURAL,
            prerequisites=[],
            material_requirements=["tuberia_bambu", "valvula_arcilla"],
            productivity_bonus=0.25,
        )

        discovered = engine.attempt_discovery(
            tech_id=irrigation.tech_id,
            innovator_id="p_inventor_1",
            settlement_id="settle_san_vicente",
            available_materials=["tuberia_bambu", "valvula_arcilla"],
            known_tech_ids=set(),
            year=2028.0,
        )

        # Diffusion to other settlements
        engine.diffuse_to_settlement(irrigation.tech_id, "settle_usulutan")
        engine.diffuse_to_settlement(irrigation.tech_id, "settle_chalatenango")

        success = discovered and len(irrigation.known_by_settlements) == 3 and irrigation.status == InnovationStatus.DIFFUSED
        return ExperimentResult(
            success=success,
            ticks_executed=self.config.max_ticks,
            metrics={"known_settlements": len(irrigation.known_by_settlements), "status": irrigation.status.value},
        )


class Experiment10_I_EconomicTransformation(BaseExperiment):
    """EXP_10_I: Transformación estructural productiva y acumulación de capital."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        super().__init__(config or ExperimentConfig(name="EXP_10_I_EconomicTransformation", max_ticks=300))

    def run(self) -> ExperimentResult:
        econ = EconomicCivilizationEngine()
        ent = econ.establish_enterprise("Molino y Panadería Santa Tecla", EconomicSector.MANUFACTURING, "founder_1", initial_capital=100.0)

        # Simulate 10 production cycles
        for _ in range(10):
            econ.simulate_economic_cycle(productivity_shock=1.1)

        # Inherited by 2nd generation
        econ.inherit_enterprise(ent.enterprise_id, heir_id="heir_1", transferred_capital_fraction=0.9)

        success = ent.capital > 100.0 and ent.generation_inherited == 1 and ent.owner_id == "heir_1"
        return ExperimentResult(
            success=success,
            ticks_executed=self.config.max_ticks,
            metrics={"final_capital": ent.capital, "generation_inherited": ent.generation_inherited},
        )


class Experiment10_J_SocialMobility(BaseExperiment):
    """EXP_10_J: Movilidad social intergeneracional y trayectorias ocupacionales."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        super().__init__(config or ExperimentConfig(name="EXP_10_J_SocialMobility", max_ticks=300))

    def run(self) -> ExperimentResult:
        strat = SocialStratificationEngine()
        prof = strat.register_profile("human_aspirant_1", wealth=40.0, income=10.0, education=0.1)
        initial_tier = prof.tier

        # Upward mobility through education, technical skill, and commerce
        strat.adjust_mobility("human_aspirant_1", delta_wealth=350.0, delta_income=80.0, delta_education=0.6, delta_social_capital=0.4)
        final_tier = prof.tier

        success = prof.upward_events_count >= 1 and final_tier in (SocialTier.MIDDLE, SocialTier.MIDDLE_UPPER, SocialTier.PROSPEROUS)
        return ExperimentResult(
            success=success,
            ticks_executed=self.config.max_ticks,
            metrics={"initial_tier": initial_tier.value, "final_tier": final_tier.value, "upward_events": prof.upward_events_count},
        )


class Experiment10_K_InstitutionalTransformation(BaseExperiment):
    """EXP_10_K: Formación, registro y reforma institucional."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        super().__init__(config or ExperimentConfig(name="EXP_10_K_InstitutionalTransformation", max_ticks=300))

    def run(self) -> ExperimentResult:
        memory = HistoricalMemoryEngine()
        ev = memory.record_ground_truth(
            category=HistoricalCategory.INSTITUTIONAL,
            tick=50,
            year=2030.0,
            location="Alcaldía Municipal",
            actors=["Consejo Comunitario"],
            title="Promulgación de Ordenanza Hídrica Comunal",
            description="Creación de normativa para protección de cuencas compartidas.",
            significance=0.8,
        )

        rec = memory.archive_institutionally(
            institution_id="inst_alcaldia",
            event_id=ev.event_id,
            tick=52,
            recorded_version="Estatuto Oficial de Cuencas",
            completeness=0.92,
            fidelity=0.98,
        )

        success = rec.record_id in [r.record_id for r in memory.institutional_archives.get("inst_alcaldia", [])]
        return ExperimentResult(
            success=success,
            ticks_executed=self.config.max_ticks,
            metrics={"records_count": len(memory.institutional_archives.get("inst_alcaldia", []))},
        )


class Experiment10_L_InequalityEvolution(BaseExperiment):
    """EXP_10_L: Evolución de desigualdades y cálculo empírico del Gini."""

    def __init__(self, config: Optional[ExperimentConfig] = None) -> None:
        super().__init__(config or ExperimentConfig(name="EXP_10_L_InequalityEvolution", max_ticks=300))

    def run(self) -> ExperimentResult:
        strat = SocialStratificationEngine()
        # Create an unequal population
        strat.register_profile("p_rich_1", wealth=2000.0)
        strat.register_profile("p_rich_2", wealth=1500.0)
        for i in range(10):
            strat.register_profile(f"p_poor_{i}", wealth=30.0)

        gini = strat.calculate_wealth_gini()
        success = gini > 0.40  # Significant measured inequality
        return ExperimentResult(
            success=success,
            ticks_executed=self.config.max_ticks,
            metrics={"gini_coefficient": gini},
        )
