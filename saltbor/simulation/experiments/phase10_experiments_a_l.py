"""Phase 1.0 Experiments Suite: Part 1 (EXP_10_A through EXP_10_L).

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
import time
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
from saltbor.simulation.runner import SimulationRunner

logger = logging.getLogger(__name__)


class Experiment10_A_MultigenerationalContinuity(BaseExperiment):
    """EXP_10_A: Continuidad multigeneracional a lo largo de 3+ generaciones."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_A",
            name="Continuidad Multigeneracional",
            description="Comprueba la trazabilidad y coexistencia de tres o más generaciones consecutivas.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = MultiGenerationalEngine()
        p1 = engine.register_founder("p_gen0_1", "Flores", birth_year=1970.0)
        p2 = engine.register_founder("p_gen0_2", "Flores", birth_year=1972.0)
        c1 = engine.birth_descendant("p_gen1_1", p1.human_id, p2.human_id, birth_year=1995.0, inherited_skills=["agricultura_cafetalera"])
        c2 = engine.birth_descendant("p_gen2_1", c1.human_id, None, birth_year=2020.0, inherited_skills=["agricultura_cafetalera", "comercio_local"])
        c3 = engine.birth_descendant("p_gen3_1", c2.human_id, None, birth_year=2045.0, inherited_skills=["gestion_agricola"])

        gen0 = engine.get_generation_cohort(0)
        gen3 = engine.get_generation_cohort(3)

        success = len(gen0) >= 2 and len(gen3) >= 1 and engine.records[c3.human_id].generation_index == 3
        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Continuidad generacional validada a través de cuatro cohortes sucesivas.",
            hypotheses=[
                {"hypothesis": "Las cohortes generacionales mantienen su genealogía e identidad", "verified": success}
            ],
            metrics={
                "total_generations": 4,
                "gen0_count": len(gen0),
                "gen3_count": len(gen3),
                "lineage_depth": max(l.generation_depth for l in engine.lineages.values()),
            },
            duration_seconds=elapsed,
        )


class Experiment10_B_DemographicTurnover(BaseExperiment):
    """EXP_10_B: Evolución demográfica durante varias generaciones."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_B",
            name="Evolución Demográfica Intergeneracional",
            description="Verifica el reemplazo biológico, natalidad y mortalidad acumulada.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = MultiGenerationalEngine()
        for i in range(10):
            engine.register_founder(f"init_{i}", f"Linaje_{i}", birth_year=1980.0)

        for i in range(15):
            engine.birth_descendant(f"child_{i}", f"init_{i % 10}", None, birth_year=2005.0)

        for i in range(8):
            engine.record_death(f"init_{i}", death_year=2025.0)

        living = [r for r in engine.records.values() if r.living]
        deceased = [r for r in engine.records.values() if not r.living]
        success = len(living) == 17 and len(deceased) == 8
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Reemplazo generacional y transición demográfica verificados.",
            hypotheses=[{"hypothesis": "La mortalidad y natalidad transforman la pirámide poblacional", "verified": success}],
            metrics={"living": len(living), "deceased": len(deceased), "cohort_ratio": len(living) / 25.0},
            duration_seconds=elapsed,
        )


class Experiment10_C_SettlementEvolution(BaseExperiment):
    """EXP_10_C: Formación y transformación gradual de asentamientos."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_C",
            name="Evolución de Asentamientos",
            description="Observa la transición de escala de caserío a comunidad/aldea.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = SettlementEvolutionEngine()
        settle = engine.found_settlement(
            name="Valle de las Flores",
            settlement_type=SettlementType.CASERIO,
            municipality="Ahuachapán Centro",
            department="Ahuachapán",
            coordinates=(13.921, -89.845),
        )
        for i in range(60):
            engine.add_inhabitant(settle.settlement_id, f"inhabitant_{i}")

        engine.develop_infrastructure(settle.settlement_id, investment=4.0)
        evolved_type = settle.settlement_type
        success = evolved_type in (SettlementType.ALDEA, SettlementType.BARRIO, SettlementType.COMUNIDAD_RURAL)
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Asentamiento evolucionó orgánicamente a {evolved_type.value}.",
            hypotheses=[{"hypothesis": "El crecimiento demográfico e infraestructural altera la categoría del asentamiento", "verified": success}],
            metrics={
                "settlement_type": evolved_type.value,
                "population": settle.population_count,
                "infrastructure_level": settle.resources.infrastructure_level,
            },
            duration_seconds=elapsed,
        )


class Experiment10_D_TerritorialMigration(BaseExperiment):
    """EXP_10_D: Migración entre territorios y remesas."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_D",
            name="Migración y Remesas Territoriales",
            description="Comprueba flujo migratorio rural-urbano y retornos en remesas.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        mig_engine = MigrationDynamicsEngine()
        settle_engine = SettlementEvolutionEngine()

        rural = settle_engine.found_settlement("Caserío El Jocote", SettlementType.CASERIO, "Morazán Sur", "Morazán", (13.7, -88.1))
        urban = settle_engine.found_settlement("San Miguel Centro", SettlementType.CIUDAD, "San Miguel Centro", "San Miguel", (13.48, -88.18))

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
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Migración completada con éxito y flujo de remesas hacia asentamiento de origen.",
            hypotheses=[{"hypothesis": "Los gradientes de oportunidad motivan la migración y generan remesas", "verified": success}],
            metrics={"propensity": propensity, "remittances_received": mig_engine.remittances_by_settlement.get(rural.settlement_id, 0.0)},
            duration_seconds=elapsed,
        )


class Experiment10_E_FamilyStructures(BaseExperiment):
    """EXP_10_E: Evolución y ramificación de estructuras familiares."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_E",
            name="Evolución de Estructuras Familiares",
            description="Comprueba la ramificación genealógica a lo largo de linajes extensos.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = MultiGenerationalEngine()
        f1 = engine.register_founder("f_anc_1", "Navas")
        f2 = engine.register_founder("f_anc_2", "Navas")

        b1 = engine.birth_descendant("f_b1_1", f1.human_id, f2.human_id, birth_year=2000.0)
        b2 = engine.birth_descendant("f_b2_1", f1.human_id, f2.human_id, birth_year=2002.0)

        engine.birth_descendant("f_b1_child", b1.human_id, None, birth_year=2026.0)
        engine.birth_descendant("f_b2_child", b2.human_id, None, birth_year=2028.0)

        lineage = list(engine.lineages.values())[0]
        success = lineage.total_members_count >= 5 and lineage.generation_depth >= 3
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Linaje familiar ramificado con profundidad de 3 generaciones y 5+ miembros.",
            hypotheses=[{"hypothesis": "Las familias se ramifican conservando el tronco genealógico", "verified": success}],
            metrics={"members": lineage.total_members_count, "depth": lineage.generation_depth},
            duration_seconds=elapsed,
        )


class Experiment10_F_KnowledgeTransmission(BaseExperiment):
    """EXP_10_F: Transmisión intergeneracional de conocimientos empíricos."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_F",
            name="Transmisión Intergeneracional de Conocimientos",
            description="Verifica la transmisión explícita de saberes empíricos entre maestro y aprendiz.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
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
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Transmisión de técnica artesanal registrada con procedencia temporal en el grafo.",
            hypotheses=[{"hypothesis": "Los conocimientos empíricos se transmiten con procedencia temporal explícita", "verified": success}],
            metrics={"transmitted_count": len(transmissions)},
            duration_seconds=elapsed,
        )


class Experiment10_G_CulturalTraditions(BaseExperiment):
    """EXP_10_G: Evolución y reinterpretación de tradiciones culturales."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_G",
            name="Evolución de Tradiciones Culturales",
            description="Examina la deriva semántica en narrativas orales a lo largo del tiempo.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
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
        for _ in range(4):
            memory.transmit_narrative(narrative.narrative_id, fidelity_loss=0.1)

        recollections = memory.query_collective_recollection("soc_izalco", current_year=2080.0)
        success = narrative.transmission_count == 5 and narrative.drift_factor > 0.3 and len(recollections) > 0
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Narrativa cultural retold con deriva semántica acumulada ({round(narrative.drift_factor, 2)}).",
            hypotheses=[{"hypothesis": "La transmisión intergeneracional induce deriva semántica acumulativa", "verified": success}],
            metrics={"drift": narrative.drift_factor, "transmission_count": narrative.transmission_count},
            duration_seconds=elapsed,
        )


class Experiment10_H_InnovationDiffusion(BaseExperiment):
    """EXP_10_H: Aparición, difusión y adopción de innovaciones técnicas."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_H",
            name="Aparición y Difusión de Innovaciones",
            description="Demuestra el descubrimiento condicionado y su difusión geográfica entre asentamientos.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
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

        engine.diffuse_to_settlement(irrigation.tech_id, "settle_usulutan")
        engine.diffuse_to_settlement(irrigation.tech_id, "settle_chalatenango")

        success = discovered and len(irrigation.known_by_settlements) == 3 and irrigation.status == InnovationStatus.DIFFUSED
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Innovación agrícola descubierta y difundida a tres asentamientos.",
            hypotheses=[{"hypothesis": "Las innovaciones se descubren con requisitos materiales y se difunden espacialmente", "verified": success}],
            metrics={"known_settlements": len(irrigation.known_by_settlements), "status": irrigation.status.value},
            duration_seconds=elapsed,
        )


class Experiment10_I_EconomicTransformation(BaseExperiment):
    """EXP_10_I: Transformación estructural productiva y acumulación de capital."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_I",
            name="Transformación y Sucesión Productiva",
            description="Comprueba acumulación de capital y sucesión intergeneracional de negocios.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        econ = EconomicCivilizationEngine()
        ent = econ.establish_enterprise("Molino y Panadería Santa Tecla", EconomicSector.MANUFACTURING, "founder_1", initial_capital=100.0)

        for _ in range(10):
            econ.simulate_economic_cycle(productivity_shock=1.1)

        econ.inherit_enterprise(ent.enterprise_id, heir_id="heir_1", transferred_capital_fraction=0.9)
        success = ent.capital > 100.0 and ent.generation_inherited == 1 and ent.owner_id == "heir_1"
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Empresa manufacturera creció y fue heredada por segunda generación exitosamente.",
            hypotheses=[{"hypothesis": "Las empresas acumulan capital y pueden transferirse generacionalmente", "verified": success}],
            metrics={"final_capital": ent.capital, "generation_inherited": ent.generation_inherited},
            duration_seconds=elapsed,
        )


class Experiment10_J_SocialMobility(BaseExperiment):
    """EXP_10_J: Movilidad social intergeneracional y trayectorias ocupacionales."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_J",
            name="Movilidad Social Ascendente",
            description="Examina la transición de estratos sociales mediante acumulación de capacidades.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        strat = SocialStratificationEngine()
        prof = strat.register_profile("human_aspirant_1", wealth=40.0, income=10.0, education=0.1)
        initial_tier = prof.tier

        strat.adjust_mobility("human_aspirant_1", delta_wealth=350.0, delta_income=80.0, delta_education=0.6, delta_social_capital=0.4)
        final_tier = prof.tier

        success = prof.upward_events_count >= 1 and final_tier in (SocialTier.MIDDLE, SocialTier.MIDDLE_UPPER, SocialTier.PROSPEROUS)
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Movilidad social confirmada de {initial_tier.value} hacia {final_tier.value}.",
            hypotheses=[{"hypothesis": "El incremento en educación e ingresos impulsa la movilidad ascendente", "verified": success}],
            metrics={"initial_tier": initial_tier.value, "final_tier": final_tier.value, "upward_events": prof.upward_events_count},
            duration_seconds=elapsed,
        )


class Experiment10_K_InstitutionalTransformation(BaseExperiment):
    """EXP_10_K: Formación, registro y reforma institucional."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_K",
            name="Formación y Archivo Institucional",
            description="Valida la promulgación formal de estatutos y su archivo fidedigno.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
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
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Normativa comunal registrada y preservada en el archivo municipal.",
            hypotheses=[{"hypothesis": "Los acuerdos colectivos se cristalizan en registros institucionales", "verified": success}],
            metrics={"records_count": len(memory.institutional_archives.get("inst_alcaldia", []))},
            duration_seconds=elapsed,
        )


class Experiment10_L_InequalityEvolution(BaseExperiment):
    """EXP_10_L: Evolución de desigualdades y cálculo empírico del Gini."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_L",
            name="Evolución de Desigualdades (Gini)",
            description="Calcula el coeficiente de Gini a partir de perfiles económicos observados.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        strat = SocialStratificationEngine()
        strat.register_profile("p_rich_1", wealth=2000.0)
        strat.register_profile("p_rich_2", wealth=1500.0)
        for i in range(10):
            strat.register_profile(f"p_poor_{i}", wealth=30.0)

        gini = strat.calculate_wealth_gini()
        success = gini > 0.40
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Dispersión económica evaluada con Gini={round(gini, 3)}.",
            hypotheses=[{"hypothesis": "La concentración de capital en pocas unidades genera alto índice de Gini", "verified": success}],
            metrics={"gini_coefficient": gini},
            duration_seconds=elapsed,
        )
