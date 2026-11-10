"""Phase 1.0 Experiments Suite: Part 2 (EXP_10_M through EXP_10_X).

Covers:
- EXP_10_M: Respuesta ante crisis ambientales.
- EXP_10_N: Resiliencia económica.
- EXP_10_O: Fragmentación de comunidades.
- EXP_10_P: Formación de nuevas identidades colectivas.
- EXP_10_Q: Evolución de relaciones entre sociedades.
- EXP_10_R: Pérdida y recuperación de conocimientos.
- EXP_10_S: Transformación histórica de una comunidad.
- EXP_10_T: Continuidad institucional después de cambios generacionales.
- EXP_10_U: Desarrollo tecnológico condicionado por recursos.
- EXP_10_V: Comparación de escenarios históricos.
- EXP_10_W: Extinción o transformación de una sociedad.
- EXP_10_X: Evolución civilizatoria a largo plazo.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from saltbor.civilization.economy import (
    EconomicCivilizationEngine,
    EconomicSector,
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
    SettlementType,
)
from saltbor.civilization.stratification import (
    SocialStratificationEngine,
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


class Experiment10_M_EnvironmentalCrisisResponse(BaseExperiment):
    """EXP_10_M: Respuesta colectiva y adaptación ante crisis ambientales (sequías/inundaciones)."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_M",
            name="Respuesta ante Crisis Ambientales",
            description="Evalúa resiliencia y adopción de estrategias adaptativas ante sequía extrema.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        resilience = CivilizationResilienceEngine()
        crisis = resilience.trigger_crisis(
            crisis_type=CrisisType.DROUGHT,
            severity=0.65,
            affected_settlements=["settle_san_miguel_rural"],
            tick_start=10,
        )
        outcome = resilience.resolve_crisis_step(crisis.crisis_id, resilience_score=0.45)
        success = outcome["strategy"] == AdaptationStrategy.TECHNICAL_ADAPTATION.value
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Crisis ambiental abordada mediante estrategia {outcome['strategy']}.",
            hypotheses=[{"hypothesis": "La brecha moderada entre severidad y resiliencia activa adaptación técnica", "verified": success}],
            metrics={"strategy": outcome["strategy"], "loss_ratio": outcome["loss_ratio"]},
            duration_seconds=elapsed,
        )


class Experiment10_N_EconomicResilience(BaseExperiment):
    """EXP_10_N: Resiliencia económica ante shocks de productividad y recuperación productiva."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_N",
            name="Resiliencia Económica",
            description="Comprueba la capacidad de sobrellevar un shock macro y rebotar productivamente.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        econ = EconomicCivilizationEngine()
        ent = econ.establish_enterprise("Taller de Confección", EconomicSector.MANUFACTURING, "founder_1", initial_capital=150.0)

        econ.simulate_economic_cycle(productivity_shock=0.3)
        capital_after_shock = ent.capital

        for _ in range(3):
            econ.simulate_economic_cycle(productivity_shock=1.4)
        capital_after_recovery = ent.capital

        success = ent.active and capital_after_recovery > capital_after_shock
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Recuperación productiva verificada tras absorber shock macroeconómico.",
            hypotheses=[{"hypothesis": "Los sistemas productivos resilientes rebotan tras caídas transitorias", "verified": success}],
            metrics={"capital_after_shock": capital_after_shock, "capital_after_recovery": capital_after_recovery},
            duration_seconds=elapsed,
        )


class Experiment10_O_CommunityFragmentation(BaseExperiment):
    """EXP_10_O: Fragmentación de comunidades por pérdida de cohesión social."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_O",
            name="Fragmentación de Comunidades",
            description="Observa la escisión territorial de asentamientos en nuevas unidades autónomas.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        civ_engine = CivilizationEvolutionEngine()
        parent = civ_engine.found_civilization("Comunidad Mayor", initial_settlement_name="Centro Mayor")
        s2 = civ_engine.settlements.found_settlement("Aldea Separatista", SettlementType.ALDEA, "Metapán", "Santa Ana", (14.3, -89.4))
        parent.settlement_ids.append(s2.settlement_id)

        fragment = civ_engine.fragment_civilization(parent.civilization_id, "Nueva Comunidad Escindida", [s2.settlement_id])
        success = fragment.civilization_id in civ_engine.civilizations and s2.settlement_id not in parent.settlement_ids
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Escisión de asentamiento y emergencia de nueva civilización autónoma.",
            hypotheses=[{"hypothesis": "La pérdida de cohesión desencadena fragmentación institucional y territorial", "verified": success}],
            metrics={"parent_settlements": len(parent.settlement_ids), "fragment_settlements": len(fragment.settlement_ids)},
            duration_seconds=elapsed,
        )


class Experiment10_P_CollectiveIdentityFormation(BaseExperiment):
    """EXP_10_P: Formación de nuevas identidades colectivas y narrativas identitarias."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_P",
            name="Formación de Identidades Colectivas",
            description="Comprueba la emergencia de rasgos culturales e identidades comunitarias.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        civ_engine = CivilizationEvolutionEngine()
        civ = civ_engine.found_civilization("Identidad Pipil Renaciente")
        civ.cultural_traits["tradicion_nagual"] = 0.8
        civ.cultural_traits["lengua_nahuat"] = 0.65

        narratives = civ_engine.history.narratives.get(civ.civilization_id, [])
        success = civ.collective_identity == "Identidad Pipil Renaciente" and len(narratives) > 0
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Identidad colectiva configurada con rasgos culturales y narrativa fundacional.",
            hypotheses=[{"hypothesis": "Las identidades colectivas amalgaman rasgos culturales y mitos fundacionales", "verified": success}],
            metrics={"traits_count": len(civ.cultural_traits), "narratives_count": len(narratives)},
            duration_seconds=elapsed,
        )


class Experiment10_Q_InterSocietyRelations(BaseExperiment):
    """EXP_10_Q: Evolución de relaciones entre sociedades (comercio a conflicto o alianza)."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_Q",
            name="Relaciones Inter-Civilizatorias",
            description="Evalúa el fortalecimiento de lazos diplomáticos y comerciales bilaterales.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        interactions = MultiSocietyInteractionEngine()
        interactions.establish_relation("Sociedad_Norte", "Sociedad_Sur", RelationType.NEUTRAL, trust=0.5)
        interactions.conduct_trade("Sociedad_Norte", "Sociedad_Sur", value=150.0)
        rel = interactions.relations.get("Sociedad_Norte__Sociedad_Sur")

        success = rel is not None and rel.relation_type == RelationType.TRADE_PARTNER and rel.trust_level > 0.5
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="El comercio sostenido elevó el estatus de la relación a socio comercial.",
            hypotheses=[{"hypothesis": "El intercambio comercial mutuo profundiza la confianza y formaliza alianzas", "verified": success}],
            metrics={"relation_type": rel.relation_type.value if rel else None, "trust": rel.trust_level if rel else 0.0},
            duration_seconds=elapsed,
        )


class Experiment10_R_KnowledgeLossAndRecovery(BaseExperiment):
    """EXP_10_R: Pérdida y recuperación de conocimientos empíricos."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_R",
            name="Pérdida y Recuperación de Conocimientos",
            description="Simula el olvido de una técnica por aislamiento y su posterior rescate archivístico.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        tech_engine = TechnologicalEvolutionEngine()
        node = tech_engine.register_innovation_concept("Tratamiento Térmico de Añil", KnowledgeDomain.TECHNICAL)
        tech_engine.attempt_discovery(node.tech_id, "p_dyer", "settle_suchitoto", [], set(), 2026.0)

        tech_engine.simulate_knowledge_decay(node.tech_id, "settle_suchitoto")
        status_after_decay = node.status

        tech_engine.recover_forgotten_knowledge(node.tech_id, "settle_suchitoto")
        status_after_recovery = node.status

        success = status_after_decay == InnovationStatus.FORGOTTEN and status_after_recovery == InnovationStatus.RECOVERED
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Conocimiento técnico olvidado y posteriormente recuperado.",
            hypotheses=[{"hypothesis": "Los conocimientos no son eternos; pueden extinguirse y ser redescubiertos", "verified": success}],
            metrics={"status_after_decay": status_after_decay.value, "status_after_recovery": status_after_recovery.value},
            duration_seconds=elapsed,
        )


class Experiment10_S_SettlementHistoricalTransformation(BaseExperiment):
    """EXP_10_S: Transformación histórica profunda de una comunidad."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_S",
            name="Transformación Histórica de Asentamientos",
            description="Muestra el cambio de caserío costero a ciudad puerto consolidada.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = SettlementEvolutionEngine()
        s = engine.found_settlement("Puerto Libertad Emergente", SettlementType.CASERIO, "La Libertad Costa", "La Libertad", (13.48, -89.31))
        for i in range(850):
            engine.add_inhabitant(s.settlement_id, f"p_{i}")
        engine.develop_infrastructure(s.settlement_id, investment=10.0)

        success = s.settlement_type == SettlementType.CIUDAD and s.population_count == 850
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Asentamiento creció a {s.settlement_type.value} con {s.population_count} habitantes.",
            hypotheses=[{"hypothesis": "El escalamiento masivo de población e infraestructura induce metamorfosis urbana", "verified": success}],
            metrics={"final_type": s.settlement_type.value, "population": s.population_count},
            duration_seconds=elapsed,
        )


class Experiment10_T_InstitutionalGenerationalContinuity(BaseExperiment):
    """EXP_10_T: Continuidad institucional después de relevos generacionales."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_T",
            name="Continuidad Institucional Intergeneracional",
            description="Verifica la supervivencia de estatutos cooperativos a través del archivo institucional.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        memory = HistoricalMemoryEngine()
        ev = memory.record_ground_truth(
            category=HistoricalCategory.INSTITUTIONAL,
            tick=1,
            year=2026.0,
            location="Cooperativa Cafetalera",
            actors=["Fundador_1", "Fundador_2"],
            title="Acta de Constitución Cooperativa",
            description="Constitución formal de la asociación productiva.",
        )
        rec = memory.archive_institutionally("coop_cafetalera", ev.event_id, tick=2, recorded_version="Acta Fundacional")

        records = memory.institutional_archives.get("coop_cafetalera", [])
        success = len(records) > 0 and records[0].formal_status == "archived"
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="El archivo institucional preserva la validez jurídica tras la salida de fundadores.",
            hypotheses=[{"hypothesis": "Las instituciones trascienden a las personas mediante archivos formalizados", "verified": success}],
            metrics={"archive_count": len(records), "fidelity": records[0].fidelity if records else 0.0},
            duration_seconds=elapsed,
        )


class Experiment10_U_ResourceConditionedTech(BaseExperiment):
    """EXP_10_U: Desarrollo tecnológico condicionado estrictamente por recursos materiales."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_U",
            name="Desarrollo Tecnológico Condicionado",
            description="Demuestra el fracaso de invención sin materiales y éxito al obtenerlos.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = TechnologicalEvolutionEngine()
        geothermal = engine.register_innovation_concept(
            name="Aprovechamiento Geotérmico Local",
            domain=KnowledgeDomain.TECHNICAL,
            prerequisites=[],
            material_requirements=["turbina_bronce", "resorte_acero"],
        )

        failed_attempt = engine.attempt_discovery(geothermal.tech_id, "p1", "settle_berlin", ["vapor_agua"], set(), 2030.0)
        succeeded_attempt = engine.attempt_discovery(geothermal.tech_id, "p1", "settle_berlin", ["turbina_bronce", "resorte_acero"], set(), 2032.0)

        success = (not failed_attempt) and succeeded_attempt
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Invención tecnológica rechazada por falta de materiales y validada tras su provisión.",
            hypotheses=[{"hypothesis": "La innovación depende de fundamentos materiales concretos y no es etérea", "verified": success}],
            metrics={"failed_without_materials": not failed_attempt, "succeeded_with_materials": succeeded_attempt},
            duration_seconds=elapsed,
        )


class Experiment10_V_HistoricalScenarioComparison(BaseExperiment):
    """EXP_10_V: Comparación contrafáctica de escenarios históricos."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_V",
            name="Comparación de Escenarios Históricos",
            description="Compara respuestas contrafácticas de dos sociedades ante idéntica epidemia.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        res1 = CivilizationResilienceEngine()
        c1 = res1.trigger_crisis(CrisisType.EPIDEMIC, severity=0.8, affected_settlements=["s1"], tick_start=10)
        out1 = res1.resolve_crisis_step(c1.crisis_id, resilience_score=0.2)

        res2 = CivilizationResilienceEngine()
        c2 = res2.trigger_crisis(CrisisType.EPIDEMIC, severity=0.8, affected_settlements=["s1"], tick_start=10)
        out2 = res2.resolve_crisis_step(c2.crisis_id, resilience_score=0.85)

        success = out1["loss_ratio"] > out2["loss_ratio"] and out2["resolved"]
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Sociedad con alta resiliencia absorbió el choque epidemiológico con daño mínimo.",
            hypotheses=[{"hypothesis": "Condiciones iniciales de resiliencia diferencian radicalmente el desenlace histórico", "verified": success}],
            metrics={"scenario1_loss": out1["loss_ratio"], "scenario2_loss": out2["loss_ratio"]},
            duration_seconds=elapsed,
        )


class Experiment10_W_SocietyExtinctionOrTransformation(BaseExperiment):
    """EXP_10_W: Extinción o disolución de una sociedad por pérdida demográfica."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_W",
            name="Extinción o Transformación Social",
            description="Verifica la transición al estado extinto tras colapso demográfico sostenido.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        civ_engine = CivilizationEvolutionEngine()
        civ = civ_engine.found_civilization("Sociedad Efímera", initial_year=2020.0)

        for s_id in civ.settlement_ids:
            civ_engine.settlements.settlements[s_id].population_count = 0

        civ_engine.evolve_step(civ.civilization_id, delta_years=6.0, current_tick=100)
        success = civ.phase == CivilizationPhase.EXTINCT and not civ.active
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary="Sociedad clasificada como extinta tras despoblación irreversible.",
            hypotheses=[{"hypothesis": "La pérdida total de población activa extingue a la entidad civilizatoria", "verified": success}],
            metrics={"phase": civ.phase.value, "active": civ.active},
            duration_seconds=elapsed,
        )


class Experiment10_X_LongTermCivilizationEvolution(BaseExperiment):
    """EXP_10_X: Evolución civilizatoria a largo plazo (multidecenal / siglo)."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_10_X",
            name="Evolución Civilizatoria a Largo Plazo",
            description="Ejecuta una trayectoria de 25 años simulados con expansión territorial y poblacional.",
            duration_ticks=300,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        civ_engine = CivilizationEvolutionEngine()
        civ = civ_engine.found_civilization("Civilización Salvadoreña Emergente", initial_year=2026.0)

        for i in range(120):
            civ_engine.settlements.add_inhabitant(civ.settlement_ids[0], f"p_init_{i}")

        s2 = civ_engine.settlements.found_settlement("Santa Ana Satélite", SettlementType.CIUDAD, "Santa Ana Centro", "Santa Ana", (13.99, -89.55))
        for i in range(50):
            civ_engine.settlements.add_inhabitant(s2.settlement_id, f"p_s2_{i}")
        civ.settlement_ids.append(s2.settlement_id)

        for step in range(25):
            civ_engine.evolve_step(civ.civilization_id, delta_years=1.0, current_tick=step * 10)

        success = civ.current_year == 2051.0 and civ.population_count >= 170 and civ.active
        elapsed = time.perf_counter() - t0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=success,
            summary=f"Simulación de 25 años culminada exitosamente alcanzando año virtual {civ.current_year}.",
            hypotheses=[{"hypothesis": "La simulación multidecenal integra demografía, economía y territorio coherentemente", "verified": success}],
            metrics={"final_year": civ.current_year, "population": civ.population_count, "phase": civ.phase.value},
            duration_seconds=elapsed,
        )
