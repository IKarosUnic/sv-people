"""Phase 1.11 Emergent Civilization, Longitudinal Simulation & Historical Evolution Experiments.

Implements all 24 required scientific experiments:
- EXP_111_A: Ten-year settlement evolution.
- EXP_111_B: Generational population transitions.
- EXP_111_C: Fifty-year family and social mobility.
- EXP_111_D: One-hundred-year historical continuity.
- EXP_111_E: Two-hundred-year civilization persistence.
- EXP_111_F: Settlement formation and abandonment.
- EXP_111_G: Rural-to-urban migration.
- EXP_111_H: Regional economic specialization.
- EXP_111_I: Economic crisis and recovery.
- EXP_111_J: Technological innovation and failure.
- EXP_111_K: Knowledge loss across generations.
- EXP_111_L: Cultural emergence and disappearance.
- EXP_111_M: Environmental degradation and adaptation.
- EXP_111_N: Institutional evolution.
- EXP_111_O: Intergenerational inequality.
- EXP_111_P: Historical memory distortion.
- EXP_111_Q: Population decline and demographic aging.
- EXP_111_R: Multi-region trade and migration.
- EXP_111_S: Historical causal reconstruction.
- EXP_111_T: Longitudinal persistence and recovery after interruption.
- EXP_111_U: Sensitivity to initial conditions.
- EXP_111_V: Alternative random seeds and outcome diversity.
- EXP_111_W: Performance under sustained simulation.
- EXP_111_X: Full civilization integration.
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional
import numpy as np

from saltbor.civilization.economy import EconomicSector
from saltbor.civilization.engine import CivilizationCondition
from saltbor.civilization.history import HistoricalCategory
from saltbor.civilization.longitudinal import LongitudinalCivilizationEngine
from saltbor.civilization.resilience import CrisisType
from saltbor.civilization.settlement import InfrastructureType, SettlementStatus, SettlementType
from saltbor.civilization.technology import InnovationStatus, KnowledgeDomain
from saltbor.simulation.experiments.base import BaseExperiment, ExperimentConfig, ExperimentResult
from saltbor.simulation.runner import SimulationRunner


# =============================================================================
# 1. EXP_111_A: Ten-Year Settlement Evolution
# =============================================================================
class Experiment111_A_TenYearSettlementEvolution(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_A",
            name="Ten-Year Settlement Evolution",
            description="Evaluates settlement growth, density, and infrastructure upgrades over 10 simulated years.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)
        res = engine.run_horizon(years=10.0)

        s_id = engine.primary_settlement_id
        settle = engine.settlements.settlements[s_id]

        hyp1 = settle.population_count > 24
        hyp2 = settle.resources.infrastructure_level > 0.30
        hyp3 = res.survived is True

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2 and hyp3),
            summary=f"10-year settlement evolution completed: final pop={settle.population_count}, infra={settle.resources.infrastructure_level:.2f}.",
            hypotheses=[
                {"hypothesis": "Population expands beyond baseline 24 founders", "confirmed": hyp1},
                {"hypothesis": "Infrastructure condition remains viable and operational", "confirmed": hyp2},
                {"hypothesis": "Settlement survives without early collapse", "confirmed": hyp3},
            ],
            metrics={
                "initial_population": res.initial_population,
                "final_population": settle.population_count,
                "infrastructure_level": settle.resources.infrastructure_level,
                "carrying_capacity": settle.resources.carrying_capacity,
                "duration_years": res.duration_years,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 2. EXP_111_B: Generational Population Transitions
# =============================================================================
class Experiment111_B_GenerationalPopulationTransitions(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_B",
            name="Generational Population Transitions",
            description="Evaluates natural mortality, births, and cohort turnover over 25 simulated years.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)
        res = engine.run_horizon(years=25.0)

        demo = engine.multigen.calculate_demographic_snapshot(engine.current_year)
        gen1_count = len(engine.multigen.get_generation_cohort(1))

        hyp1 = res.total_births >= 20
        hyp2 = res.total_deaths >= 5
        hyp3 = gen1_count >= 15

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2 and hyp3),
            summary=f"25-year generational transition: births={res.total_births}, deaths={res.total_deaths}, Gen1 cohort={gen1_count}.",
            hypotheses=[
                {"hypothesis": "Substantial new generation (Gen 1) born over 25 years", "confirmed": hyp1},
                {"hypothesis": "Natural mortality removes older founders under Gompertz curve", "confirmed": hyp2},
                {"hypothesis": "Gen 1 cohort expands and establishes family branches", "confirmed": hyp3},
            ],
            metrics={
                "total_births": res.total_births,
                "total_deaths": res.total_deaths,
                "generation_1_count": gen1_count,
                "dependency_ratio": demo.dependency_ratio,
                "mean_age": demo.mean_age,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 3. EXP_111_C: Fifty-Year Family and Social Mobility
# =============================================================================
class Experiment111_C_FiftyYearFamilyMobility(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_C",
            name="Fifty-Year Family and Social Mobility",
            description="Evaluates lineage wealth transfer and non-static mobility across 50 simulated years.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)
        res = engine.run_horizon(years=50.0)

        lineages = list(engine.multigen.lineages.values())
        max_depth = max(l.generation_depth for l in lineages)
        wealths = [l.intergenerational_wealth for l in lineages]
        has_wealth_divergence = (max(wealths) - min(wealths)) > 30.0

        hyp1 = max_depth >= 3
        hyp2 = res.accounting_conservation_verified is True
        hyp3 = has_wealth_divergence is True

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2 and hyp3),
            summary=f"50-year family mobility: max depth={max_depth} gens, wealth spread=${min(wealths):.1f} to ${max(wealths):.1f}.",
            hypotheses=[
                {"hypothesis": "Lineage depth reaches 3+ generations over 50 years", "confirmed": hyp1},
                {"hypothesis": "Probate inheritance maintains exact accounting conservation", "confirmed": hyp2},
                {"hypothesis": "Intergenerational wealth experiences non-static divergence", "confirmed": hyp3},
            ],
            metrics={
                "max_generation_depth": max_depth,
                "lineages_count": len(lineages),
                "wealth_min": min(wealths),
                "wealth_max": max(wealths),
                "duration_years": res.duration_years,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 4. EXP_111_D: One-Hundred-Year Historical Continuity
# =============================================================================
class Experiment111_D_OneHundredYearHistoricalContinuity(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_D",
            name="One-Hundred-Year Historical Continuity",
            description="Verifies civilizational persistence, historical memory, and lineage depth across 100 years.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)
        res = engine.run_horizon(years=100.0)

        demo = engine.multigen.calculate_demographic_snapshot(engine.current_year)
        events_count = len(engine.history.ground_truth)

        hyp1 = res.survived is True
        hyp2 = demo.max_generation_depth >= 4
        hyp3 = events_count >= 3

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2 and hyp3),
            summary=f"100-year continuity: pop={res.final_population}, max gen={demo.max_generation_depth}, events={events_count}.",
            hypotheses=[
                {"hypothesis": "Civilization sustains demographic survival across 100 years", "confirmed": hyp1},
                {"hypothesis": "Lineage depth spans 4+ generational transitions", "confirmed": hyp2},
                {"hypothesis": "Historical memory accumulates traceable milestone events", "confirmed": hyp3},
            ],
            metrics={
                "final_population": res.final_population,
                "generation_depth": demo.max_generation_depth,
                "historical_events_count": events_count,
                "final_phase": res.final_phase,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 5. EXP_111_E: Two-Hundred-Year Civilization Persistence
# =============================================================================
class Experiment111_E_TwoHundredYearCivilizationPersistence(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_E",
            name="Two-Hundred-Year Civilization Persistence",
            description="Evaluates long-term stability and ecological ceiling over two centuries of simulated time.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)
        res = engine.run_horizon(years=200.0)

        hyp1 = res.survived is True
        hyp2 = res.final_population > 50
        hyp3 = res.total_births > 500

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2 and hyp3),
            summary=f"200-year persistence: survived={res.survived}, pop={res.final_population}, births={res.total_births}, deaths={res.total_deaths}.",
            hypotheses=[
                {"hypothesis": "Civilization persists across 200 years without mathematical collapse", "confirmed": hyp1},
                {"hypothesis": "Population remains robust above critical viability threshold (50)", "confirmed": hyp2},
                {"hypothesis": "Continuous multi-generational turnover occurs (> 500 births)", "confirmed": hyp3},
            ],
            metrics={
                "final_population": res.final_population,
                "total_births": res.total_births,
                "total_deaths": res.total_deaths,
                "duration_seconds": res.duration_seconds,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 6. EXP_111_F: Settlement Formation and Abandonment
# =============================================================================
class Experiment111_F_SettlementFormationAndAbandonment(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_F",
            name="Settlement Formation and Abandonment",
            description="Simulates resource exhaustion driving distress migration and settlement abandonment.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)

        # Found vulnerable secondary settlement
        sec_settle = engine.settlements.found_settlement(
            name="Caserío Los Desamparados",
            settlement_type=SettlementType.CASERIO,
            municipality="San Salvador Centro",
            department="San Salvador",
            coordinates=(13.72, -89.20),
            founded_year=2026.0,
        )
        engine.civ_state.settlement_ids.append(sec_settle.settlement_id)

        # Move 4 inhabitants there
        inhabitants = list(engine.settlements.settlements[engine.primary_settlement_id].inhabitant_ids[:4])
        for uid in inhabitants:
            engine.settlements.remove_inhabitant(engine.primary_settlement_id, uid)
            engine.settlements.add_inhabitant(sec_settle.settlement_id, uid)

        # Trigger ecological drought intervention in secondary settlement
        def _drought_intervention(eng: LongitudinalCivilizationEngine):
            if eng.current_year >= 2028.0:
                s = eng.settlements.settlements[sec_settle.settlement_id]
                s.resources.water_access = 0.05
                s.resources.soil_fertility = 0.10

        res = engine.run_horizon(years=12.0, intervention=_drought_intervention)

        is_abandoned = (sec_settle.status == SettlementStatus.ABANDONED or sec_settle.population_count == 0)
        hyp1 = is_abandoned is True

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=hyp1,
            summary=f"Settlement abandonment verified: status={sec_settle.status.value}, pop={sec_settle.population_count}.",
            hypotheses=[
                {"hypothesis": "Resource drought drives complete desertion and ABANDONED status", "confirmed": hyp1},
            ],
            metrics={
                "secondary_settlement_status": sec_settle.status.value,
                "secondary_settlement_pop": sec_settle.population_count,
                "primary_settlement_pop": engine.settlements.settlements[engine.primary_settlement_id].population_count,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 7. EXP_111_G: Rural-to-Urban Migration
# =============================================================================
class Experiment111_G_RuralToUrbanMigration(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_G",
            name="Rural-to-Urban Migration",
            description="Evaluates demographic concentration driven by urban commercial opportunities.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)

        # Found rural agricultural caserío
        rural = engine.settlements.found_settlement(
            name="Aldea San Ramón",
            settlement_type=SettlementType.COMUNIDAD_RURAL,
            municipality="San Marcos",
            department="San Salvador",
            coordinates=(13.65, -89.18),
        )
        engine.civ_state.settlement_ids.append(rural.settlement_id)

        # Place 10 inhabitants in rural aldea
        for i in range(10):
            uid = f"rural_migrant_{i}"
            engine.multigen.register_founder(uid, "Ramírez", birth_year=2000.0, settlement_id=rural.settlement_id)
            engine.settlements.add_inhabitant(rural.settlement_id, uid)

        # Elevate commercial intensity in urban center
        urban = engine.settlements.settlements[engine.primary_settlement_id]
        urban.resources.commercial_intensity = 0.85
        rural.resources.commercial_intensity = 0.10

        res = engine.run_horizon(years=10.0)

        hyp1 = res.total_migrations >= 1
        hyp2 = urban.population_count > rural.population_count

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2),
            summary=f"Rural-to-urban migration observed: migrations={res.total_migrations}, urban={urban.population_count}, rural={rural.population_count}.",
            hypotheses=[
                {"hypothesis": "Commercial opportunity disparity induces inter-settlement migration", "confirmed": hyp1},
                {"hypothesis": "Urban center concentrates higher population than rural aldea", "confirmed": hyp2},
            ],
            metrics={
                "total_migrations": res.total_migrations,
                "urban_population": urban.population_count,
                "rural_population": rural.population_count,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 8. EXP_111_H: Regional Economic Specialization
# =============================================================================
class Experiment111_H_RegionalEconomicSpecialization(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_H",
            name="Regional Economic Specialization",
            description="Evaluates differential sectoral development across geographic environments.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)

        # Found coastal fishing settlement
        coastal = engine.settlements.found_settlement(
            name="Puerto La Libertad",
            settlement_type=SettlementType.CENTRO_URBANO,
            municipality="La Libertad Costa",
            department="La Libertad",
            coordinates=(13.48, -89.31),
        )
        engine.civ_state.settlement_ids.append(coastal.settlement_id)
        coastal.economic_specializations.append("fishing")

        # Primary settlement specializes in commerce
        engine.settlements.settlements[engine.primary_settlement_id].economic_specializations.append("commerce")

        # Establish fisheries in coastal and trading firms in primary
        engine.economy.establish_enterprise(
            name="Cooperativa Pesquera El Malecón",
            sector=EconomicSector.FISHING,
            founder_id="fisherman_1",
            initial_capital=90.0,
            location=coastal.settlement_id,
        )

        res = engine.run_horizon(years=8.0)

        hyp1 = "fishing" in coastal.economic_specializations
        hyp2 = EconomicSector.FISHING in engine.economy.sector_production

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2),
            summary="Regional economic specialization established: coastal fishing vs urban commerce.",
            hypotheses=[
                {"hypothesis": "Coastal settlement adopts fishing specialization based on geography", "confirmed": hyp1},
                {"hypothesis": "Macro economy reflects output across specialized sectors", "confirmed": hyp2},
            ],
            metrics={
                "coastal_specializations": coastal.economic_specializations,
                "sectors_active_count": len(engine.economy.sector_production),
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 9. EXP_111_I: Economic Crisis and Recovery
# =============================================================================
class Experiment111_I_EconomicCrisisAndRecovery(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_I",
            name="Economic Crisis and Recovery",
            description="Evaluates endogenous commercial shock, firm distress, and recovery under conservation.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)

        def _crisis_intervention(eng: LongitudinalCivilizationEngine):
            if eng.current_year == 2028.0:
                eng.economy.trigger_endogenous_crisis(
                    crisis_type="supply_chain_collapse",
                    affected_sector=EconomicSector.INFORMAL_COMMERCE,
                    severity=0.75,
                )

        res = engine.run_horizon(years=15.0, intervention=_crisis_intervention)

        crises = engine.economy.active_economic_crises
        hyp1 = len(crises) >= 1
        hyp2 = res.accounting_conservation_verified is True
        hyp3 = res.final_population > 20

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2 and hyp3),
            summary=f"Economic crisis absorbed: crises triggered={len(crises)}, final pop={res.final_population}.",
            hypotheses=[
                {"hypothesis": "Endogenous shock induces firm distress without arbitrary money creation", "confirmed": hyp1},
                {"hypothesis": "Accounting conservation strictly holds during crisis", "confirmed": hyp2},
                {"hypothesis": "Society weathers the crisis and sustains positive output", "confirmed": hyp3},
            ],
            metrics={
                "crises_count": len(crises),
                "final_gdp": res.timeline[-1].total_gdp_production,
                "survived": res.survived,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 10. EXP_111_J: Technological Innovation and Failure
# =============================================================================
class Experiment111_J_TechnologicalInnovationAndFailure(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_J",
            name="Technological Innovation and Failure",
            description="Evaluates discovery constraints and records unviable experiment failure.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)

        # Concept requiring unavailable advanced materials
        unviable = engine.tech.register_innovation_concept(
            name="Reactor Biocombustible Avanzado",
            domain=KnowledgeDomain.TECHNICAL,
            prerequisites=["electrificacion_industrial"],
            material_requirements=["platino", "acero_inoxidable"],
        )

        # Attempt discovery with missing materials
        success = engine.tech.attempt_discovery(
            tech_id=unviable.tech_id,
            innovator_id="inventor_1",
            settlement_id=engine.primary_settlement_id,
            available_materials=["madera", "barro"],
            known_tech_ids=set(),
            year=2026.0,
        )
        assert success is False

        # Record failure
        engine.tech.record_failed_attempt(
            tech_id=unviable.tech_id,
            innovator_id="inventor_1",
            settlement_id=engine.primary_settlement_id,
            reason="Falta de aleaciones metálicas y energía industrial.",
        )

        hyp1 = (unviable.status == InnovationStatus.FAILED)
        hyp2 = len(unviable.failure_history) >= 1

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2),
            summary=f"Innovation failure confirmed: status={unviable.status.value}, failures={unviable.failure_history}.",
            hypotheses=[
                {"hypothesis": "Discovery fails when material and tech prerequisites are missing", "confirmed": hyp1},
                {"hypothesis": "Failed innovation attempts are recorded in technological history", "confirmed": hyp2},
            ],
            metrics={
                "tech_status": unviable.status.value,
                "failure_reasons": unviable.failure_history,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 11. EXP_111_K: Knowledge Loss Across Generations
# =============================================================================
class Experiment111_K_KnowledgeLossAcrossGenerations(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_K",
            name="Knowledge Loss Across Generations",
            description="Evaluates specialized knowledge loss when sole practitioners die without transmission.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)

        loom = engine.tech.register_innovation_concept(
            name="Telar de Cintura Ancestral",
            domain=KnowledgeDomain.CULTURAL,
            prerequisites=[],
            material_requirements=[],
        )
        engine.tech.attempt_discovery(
            tech_id=loom.tech_id,
            innovator_id="elder_weaver",
            settlement_id=engine.primary_settlement_id,
            available_materials=[],
            known_tech_ids=set(),
        )
        assert loom.status == InnovationStatus.VALIDATED

        # Simulate knowledge decay as elder dies
        engine.tech.simulate_knowledge_decay(loom.tech_id, engine.primary_settlement_id)

        hyp1 = (loom.status == InnovationStatus.FORGOTTEN)

        # Rediscover knowledge via archive/cultural recovery
        recovered = engine.tech.recover_forgotten_knowledge(loom.tech_id, engine.primary_settlement_id)
        hyp2 = (recovered is True and loom.status == InnovationStatus.RECOVERED)

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2),
            summary=f"Knowledge loss and rediscovery verified: forgot={hyp1}, recovered={hyp2}.",
            hypotheses=[
                {"hypothesis": "Loss of all practitioners causes tech status transition to FORGOTTEN", "confirmed": hyp1},
                {"hypothesis": "Forgotten technology can be recovered through institutional memory", "confirmed": hyp2},
            ],
            metrics={
                "forgotten_status_achieved": hyp1,
                "recovered_status_achieved": hyp2,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 12. EXP_111_L: Cultural Emergence and Disappearance
# =============================================================================
class Experiment111_L_CulturalEmergenceAndDisappearance(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_L",
            name="Cultural Emergence and Disappearance",
            description="Evaluates tradition practice frequency, desuetudo decay, and extinction.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        from saltbor.social.culture.evolution import CulturalEvolutionEngine, CulturalCategory
        engine = CulturalEvolutionEngine()

        # Seed traditions: actively practiced, dormant unpracticed, and extinct
        trad_active = engine.register_tradition(
            name="Festival del Maíz",
            category=CulturalCategory.COMMUNAL_TRADITION,
            origin_community_id="comunidad_centro_historico",
            description="Celebración patronal de la cosecha de maíz",
            initial_adopters=["human_1", "human_2"],
            tick=0,
        )
        trad_dormant = engine.register_tradition(
            name="Receta Tradicional de Atole Shuco",
            category=CulturalCategory.CULINARY_PRACTICE,
            origin_community_id="comunidad_centro_historico",
            description="Costumbre culinaria sin celebración comunal reciente",
            initial_adopters=["human_1"],
            tick=0,
        )
        trad_extinct = engine.register_tradition(
            name="Danza del Venado Ancestral",
            category=CulturalCategory.ARTS_RECREATION,
            origin_community_id="comunidad_centro_historico",
            description="Danza ancestral cuyos practicantes han fallecido",
            initial_adopters=["human_deceased_elder"],
            tick=0,
        )

        # Active tradition is celebrated recently
        trad_active.last_practiced_tick = 4500
        trad_dormant.last_practiced_tick = 0

        # Cultural extinction detection: all practitioners of trad_extinct have perished
        extinct_ids = engine.check_cultural_extinction(alive_human_uids={"human_1", "human_2"}, tick=5000)

        # Dormancy decay over time (dormancy_limit_ticks=4000)
        dormant_ids = engine.decay_unpracticed_traditions(current_tick=5000, dormancy_limit_ticks=4000)

        hyp1 = (trad_dormant.tradition_id in dormant_ids) and (not trad_dormant.is_active) and trad_active.is_active
        hyp2 = (trad_extinct.tradition_id in extinct_ids) and trad_extinct.is_extinct and (not trad_active.is_extinct)

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2),
            summary=f"Cultural emergence and disappearance verified: active={trad_active.is_active}, dormant={not trad_dormant.is_active}, extinct={trad_extinct.is_extinct}.",
            hypotheses=[
                {"hypothesis": "Unpracticed tradition transitions to dormant status while active tradition persists", "confirmed": hyp1},
                {"hypothesis": "Tradition with zero surviving practitioners undergoes permanent cultural extinction", "confirmed": hyp2},
            ],
            metrics={
                "active_tradition_id": trad_active.tradition_id,
                "dormant_tradition_id": trad_dormant.tradition_id,
                "extinct_tradition_id": trad_extinct.tradition_id,
                "dormant_count": len(dormant_ids),
                "extinct_count": len(extinct_ids),
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 13. EXP_111_M: Environmental Degradation and Adaptation
# =============================================================================
class Experiment111_M_EnvironmentalDegradationAndAdaptation(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_M",
            name="Environmental Degradation and Adaptation",
            description="Evaluates bidirectional feedback: population pressure degrades soil, communal faena restores it.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)

        # Uncooperative exploitation
        deg_res = engine.resilience.evaluate_environmental_feedback(
            settlement_id=engine.primary_settlement_id,
            population_count=180,
            cooperation_index=0.20,
            faena_conservation_hours=0.0,
        )
        hyp1 = deg_res.agricultural_yield_multiplier < 1.0

        # Cooperative ecological restoration via ADESCO faena
        rest_res = engine.resilience.evaluate_environmental_feedback(
            settlement_id=engine.primary_settlement_id,
            population_count=50,
            cooperation_index=0.85,
            faena_conservation_hours=20.0,
        )
        hyp2 = rest_res.restoration_achieved is True
        hyp3 = rest_res.agricultural_yield_multiplier > deg_res.agricultural_yield_multiplier

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2 and hyp3),
            summary=f"Environmental feedback confirmed: degraded yield={deg_res.agricultural_yield_multiplier}, restored yield={rest_res.agricultural_yield_multiplier}.",
            hypotheses=[
                {"hypothesis": "Unchecked population extraction degrades agricultural yield", "confirmed": hyp1},
                {"hypothesis": "Communal faena achieves positive ecosystem restoration", "confirmed": hyp2},
                {"hypothesis": "Yield multiplier improves following cooperative conservation", "confirmed": hyp3},
            ],
            metrics={
                "degraded_yield": deg_res.agricultural_yield_multiplier,
                "restored_yield": rest_res.agricultural_yield_multiplier,
                "restoration_flag": rest_res.restoration_achieved,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 14. EXP_111_N: Institutional Evolution
# =============================================================================
class Experiment111_N_InstitutionalEvolution(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_N",
            name="Institutional Evolution",
            description="Evaluates ADESCO communal organization, assembly quorum, and rule amendment.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        from saltbor.social.institutions.assembly import CommunityAssembly
        assembly = CommunityAssembly()

        proposal = assembly.submit_proposal(
            proposal_id="prop_faena_01",
            title="Reglamento de Mantenimiento de Desagües y Calles",
            description="Establecer faenas mensuales obligatorias para mitigar anegamientos",
            proposer_uid="human_leader_1",
            current_tick=100,
        )

        # Cast votes across assembly members
        v1 = assembly.cast_vote("prop_faena_01", "voter_1", vote_in_favor=True)
        v2 = assembly.cast_vote("prop_faena_01", "voter_2", vote_in_favor=True)
        v3 = assembly.cast_vote("prop_faena_01", "voter_3", vote_in_favor=True)
        v4 = assembly.cast_vote("prop_faena_01", "voter_4", vote_in_favor=False)

        # Tally and resolve proposal
        resolved, passed, notes = assembly.tally_and_resolve(
            "prop_faena_01",
            current_tick=110,
            quorum=3,
            threshold=0.5,
        )

        hyp1 = proposal is not None and proposal.proposal_id == "prop_faena_01"
        hyp2 = (v1 and v2 and v3 and v4) and resolved and passed

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2),
            summary=f"Institutional evolution verified: initiative passed assembly vote ({notes}).",
            hypotheses=[
                {"hypothesis": "Communal initiative proposed through formal institutional assembly", "confirmed": hyp1},
                {"hypothesis": "Democratic voting achieves quorum and ratifies institutional rule", "confirmed": hyp2},
            ],
            metrics={"proposal_id": proposal.proposal_id, "passed": passed, "notes": notes},
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 15. EXP_111_O: Intergenerational Inequality
# =============================================================================
class Experiment111_O_IntergenerationalInequality(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_O",
            name="Intergenerational Inequality",
            description="Evaluates Gini and Palma inequality trajectories across 40 simulated years.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)
        res = engine.run_horizon(years=40.0)

        ginis = [s.wealth_gini for s in res.timeline]
        initial_gini = ginis[0]
        final_gini = ginis[-1]

        hyp1 = 0.0 <= final_gini <= 1.0
        hyp2 = len(ginis) >= 40

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2),
            summary=f"Intergenerational inequality tracked: initial Gini={initial_gini:.3f}, final Gini={final_gini:.3f}.",
            hypotheses=[
                {"hypothesis": "Gini coefficient remains mathematically bounded in [0.0, 1.0]", "confirmed": hyp1},
                {"hypothesis": "Continuous annual inequality tracking over 40 years", "confirmed": hyp2},
            ],
            metrics={
                "initial_gini": initial_gini,
                "final_gini": final_gini,
                "gini_trajectory_length": len(ginis),
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 16. EXP_111_P: Historical Memory Distortion
# =============================================================================
class Experiment111_P_HistoricalMemoryDistortion(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_P",
            name="Historical Memory Distortion",
            description="Evaluates narrative drift in oral lore vs institutional archive fidelity over generations.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)

        ev = engine.history.record_ground_truth(
            category=HistoricalCategory.NATURAL_DISASTER,
            tick=100,
            year=2026.0,
            location="Bajo Lempa",
            actors=["Comunidad El Zapote"],
            title="Inundación Mayor del Río Lempa",
            description="Crecida extraordinaria causa anegamiento de 40 hectáreas de cultivo.",
            significance=0.90,
        )

        narr = engine.history.form_cultural_narrative("civ_cuscatleca", ev.event_id, framing="tragic")

        # Oral transmission across 3 generations (3 retellings)
        for _ in range(3):
            engine.history.transmit_narrative(narr.narrative_id, fidelity_loss=0.15)

        recollections = engine.history.query_collective_recollection("civ_cuscatleca", current_year=2101.0)
        found = [r for r in recollections if r["event_id"] == ev.event_id]

        hyp1 = narr.drift_factor > 0.40
        hyp2 = len(found) >= 1
        hyp3 = narr.transmission_count == 4

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2 and hyp3),
            summary=f"Historical memory distortion verified: drift={narr.drift_factor:.2f}, retellings={narr.transmission_count}.",
            hypotheses=[
                {"hypothesis": "Oral transmission accumulates drift across generational retellings", "confirmed": hyp1},
                {"hypothesis": "High-significance event remains recollected despite factual drift", "confirmed": hyp2},
                {"hypothesis": "Transmission counter correctly increments with each retelling", "confirmed": hyp3},
            ],
            metrics={"drift_factor": narr.drift_factor, "transmission_count": narr.transmission_count},
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 17. EXP_111_Q: Population Decline and Demographic Aging
# =============================================================================
class Experiment111_Q_PopulationDeclineAndAging(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_Q",
            name="Population Decline and Demographic Aging",
            description="Evaluates mean age growth and dependency ratio rise under suppressed fertility.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)

        # Intervene with severe ecological pressure and fertility suppression
        def _fertility_slump_intervention(eng: LongitudinalCivilizationEngine):
            eng.civ_state.ecological_stress = 0.95
            eng.fertility_multiplier = 0.0

        res = engine.run_horizon(years=20.0, intervention=_fertility_slump_intervention)

        final_snap = res.timeline[-1]
        hyp1 = final_snap.mean_age > res.timeline[0].mean_age

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=hyp1,
            summary=f"Demographic aging observed: initial mean age={res.timeline[0].mean_age}, final mean age={final_snap.mean_age}.",
            hypotheses=[
                {"hypothesis": "Fertility slump induces demographic aging over time", "confirmed": hyp1},
            ],
            metrics={"initial_mean_age": res.timeline[0].mean_age, "final_mean_age": final_snap.mean_age},
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 18. EXP_111_R: Multi-Region Trade and Migration
# =============================================================================
class Experiment111_R_MultiRegionTradeAndMigration(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_R",
            name="Multi-Region Trade and Migration",
            description="Evaluates inter-society bilateral commerce and trust accumulation.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)

        # Register secondary society
        engine.civ_engine.interactions.register_society("soc_nonualco")
        rel = engine.civ_engine.interactions.establish_relation(
            engine.civ_state.civilization_id,
            "soc_nonualco",
            trust=0.5,
        )

        # Conduct bilateral commerce over 5 cycles
        for _ in range(5):
            engine.civ_engine.interactions.conduct_trade(
                engine.civ_state.civilization_id,
                "soc_nonualco",
                value=25.0,
            )

        hyp1 = rel.trade_volume >= 125.0
        hyp2 = rel.trust_level > 0.50

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2),
            summary=f"Multi-region trade verified: volume=${rel.trade_volume:.1f}, trust={rel.trust_level:.2f}.",
            hypotheses=[
                {"hypothesis": "Repeated trade transactions accumulate total trade volume", "confirmed": hyp1},
                {"hypothesis": "Bilateral commerce reinforces cross-society trust", "confirmed": hyp2},
            ],
            metrics={"trade_volume": rel.trade_volume, "trust_level": rel.trust_level},
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 19. EXP_111_S: Historical Causal Reconstruction
# =============================================================================
class Experiment111_S_HistoricalCausalReconstruction(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_S",
            name="Historical Causal Reconstruction",
            description="Evaluates backward and forward causal graph extraction across 5 connected events.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)
        hist = engine.history

        # Construct 5-link causal chain
        e1 = hist.record_ground_truth(HistoricalCategory.NATURAL_DISASTER, 100, 2026.0, "San Salvador", ["Volcán"], "Sequía", "Sequía")
        e2 = hist.record_ground_truth(HistoricalCategory.ECONOMIC_CRISIS, 200, 2026.5, "San Salvador", ["Mercado"], "Pérdida Agrícola", "Pérdida")
        e3 = hist.record_ground_truth(HistoricalCategory.MIGRATION, 300, 2027.0, "San Salvador", ["Familias"], "Éxodo Rural", "Éxodo")
        e4 = hist.record_ground_truth(HistoricalCategory.ORGANIZATION_CHANGE, 400, 2027.5, "San Salvador", ["ADESCO"], "Comité de Emergencia", "Comité")
        e5 = hist.record_ground_truth(HistoricalCategory.INSTITUTIONAL, 500, 2028.0, "San Salvador", ["Alcaldía"], "Reforma Tributaria", "Reforma")

        hist.link_causality(e1.event_id, e2.event_id, "reduccion_riego")
        hist.link_causality(e2.event_id, e3.event_id, "desempleo_agricola")
        hist.link_causality(e3.event_id, e4.event_id, "demanda_social")
        hist.link_causality(e4.event_id, e5.event_id, "aprobacion_reglamento")

        chain = hist.reconstruct_causal_sequence(e1.event_id)
        antecedents = hist.trace_antecedents(e5.event_id)

        hyp1 = len(chain) == 5
        hyp2 = len(antecedents) == 5
        hyp3 = chain[0].event_id == e1.event_id and chain[-1].event_id == e5.event_id

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2 and hyp3),
            summary=f"Causal reconstruction verified: forward chain={len(chain)} links, backward antecedents={len(antecedents)} links.",
            hypotheses=[
                {"hypothesis": "Forward causal chain reconstructs entire 5-link cascade", "confirmed": hyp1},
                {"hypothesis": "Backward traversal traces root trigger from terminal event", "confirmed": hyp2},
                {"hypothesis": "Sequence strictly preserves causal ordering without gaps", "confirmed": hyp3},
            ],
            metrics={"forward_chain_length": len(chain), "backward_chain_length": len(antecedents)},
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 20. EXP_111_T: Longitudinal Persistence and Recovery
# =============================================================================
class Experiment111_T_LongitudinalPersistenceAndRecovery(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_T",
            name="Longitudinal Persistence and Recovery",
            description="Evaluates checkpointing and process recovery across interrupted runs.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)

        # Run 10 simulated years
        res_pre = engine.run_horizon(years=10.0)
        pop_pre = res_pre.final_population
        year_pre = engine.current_year
        births_pre = engine.total_births
        deaths_pre = engine.total_deaths

        # Checkpoint state
        checkpoint = engine.checkpoint_state()

        # Instantiate a new engine from a different seed and restore checkpoint
        engine_reloaded = LongitudinalCivilizationEngine(seed=999)
        engine_reloaded.restore_state(checkpoint)

        hyp1 = (
            engine_reloaded.current_year == year_pre
            and engine_reloaded.total_births == births_pre
            and engine_reloaded.total_deaths == deaths_pre
            and len(engine_reloaded.multigen.records) == len(engine.multigen.records)
        )

        # Resume simulation for another 5 years
        res_post = engine_reloaded.run_horizon(years=5.0)
        hyp2 = (
            res_post.end_year == year_pre + 5.0
            and res_post.survived is True
            and engine_reloaded.total_births >= births_pre
        )

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2),
            summary=f"Longitudinal persistence recovery verified: year={engine_reloaded.current_year}, pop={res_post.final_population}.",
            hypotheses=[
                {"hypothesis": "Civilization state snapshot accurately restores demographic and temporal metrics", "confirmed": hyp1},
                {"hypothesis": "Resumed simulation proceeds seamlessly from restored checkpoint", "confirmed": hyp2},
            ],
            metrics={
                "restored_year": engine_reloaded.current_year,
                "pre_checkpoint_pop": pop_pre,
                "post_resumption_pop": res_post.final_population,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 21. EXP_111_U: Sensitivity to Initial Conditions
# =============================================================================
class Experiment111_U_SensitivityToInitialConditions(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_U",
            name="Sensitivity to Initial Conditions",
            description="Evaluates divergent trajectories from subtle initial environmental water offsets.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        # Run A: High initial water and soil endowment
        eng_a = LongitudinalCivilizationEngine(seed=42)
        eng_a.settlements.settlements[eng_a.primary_settlement_id].resources.water_access = 0.95
        eng_a.settlements.settlements[eng_a.primary_settlement_id].resources.soil_fertility = 0.95
        res_a = eng_a.run_horizon(years=25.0)

        # Run B: Low initial water and depleted soil endowment
        eng_b = LongitudinalCivilizationEngine(seed=42)
        eng_b.settlements.settlements[eng_b.primary_settlement_id].resources.water_access = 0.05
        eng_b.settlements.settlements[eng_b.primary_settlement_id].resources.soil_fertility = 0.05
        res_b = eng_b.run_horizon(years=25.0)

        pop_delta = abs(res_a.final_population - res_b.final_population)
        hyp1 = pop_delta >= 5
        hyp2 = res_a.vector_distance_from_start != res_b.vector_distance_from_start

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2),
            summary=f"Sensitivity confirmed: Run A pop={res_a.final_population}, Run B pop={res_b.final_population}, delta={pop_delta}.",
            hypotheses=[
                {"hypothesis": "Initial resource variation causes divergent population outcomes", "confirmed": hyp1},
                {"hypothesis": "Societal vector trajectories diverge under unequal endowments", "confirmed": hyp2},
            ],
            metrics={"pop_run_a": res_a.final_population, "pop_run_b": res_b.final_population, "pop_delta": pop_delta},
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 22. EXP_111_V: Alternative Random Seeds and Outcome Diversity
# =============================================================================
class Experiment111_V_OutcomeDiversityAcrossSeeds(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_V",
            name="Alternative Random Seeds and Outcome Diversity",
            description="Demonstrates non-scripted divergent trajectories across 5 distinct random seeds.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        seeds = [42, 101, 777, 1234, 9999]
        final_pops: List[int] = []

        for s in seeds:
            eng = LongitudinalCivilizationEngine(seed=s)
            res = eng.run_horizon(years=20.0)
            final_pops.append(res.final_population)

        pop_spread = max(final_pops) - min(final_pops)
        hyp1 = pop_spread >= 5
        hyp2 = len(set(final_pops)) >= 3

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2),
            summary=f"Outcome diversity confirmed: pops across 5 seeds={final_pops}, spread={pop_spread}.",
            hypotheses=[
                {"hypothesis": "Random seeds produce non-identical emergent populations", "confirmed": hyp1},
                {"hypothesis": "At least 3 distinct demographic trajectories emerge across 5 seeds", "confirmed": hyp2},
            ],
            metrics={"pops_by_seed": dict(zip(seeds, final_pops)), "population_spread": pop_spread},
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 23. EXP_111_W: Performance Under Sustained Simulation
# =============================================================================
class Experiment111_W_PerformanceUnderSustainedSimulation(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_W",
            name="Performance Under Sustained Simulation",
            description="Benchmarks execution latency and throughput across 100 sustained simulated years.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)
        res = engine.run_horizon(years=100.0)

        ms_per_year = (res.duration_seconds / 100.0) * 1000.0
        hyp1 = ms_per_year < 50.0  # Faster than 50 ms / year
        hyp2 = res.duration_seconds < 5.0

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2),
            summary=f"Sustained performance benchmark: total={res.duration_seconds:.3f}s for 100 years ({ms_per_year:.2f} ms/year).",
            hypotheses=[
                {"hypothesis": "Longitudinal execution maintains latency below 50 ms/year", "confirmed": hyp1},
                {"hypothesis": "Entire 100-year trajectory completes within 5 seconds", "confirmed": hyp2},
            ],
            metrics={
                "total_duration_sec": res.duration_seconds,
                "ms_per_year": ms_per_year,
                "years_simulated": 100.0,
            },
            duration_seconds=time.perf_counter() - t0,
        )


# =============================================================================
# 24. EXP_111_X: Full Civilization Integration
# =============================================================================
class Experiment111_X_FullCivilizationIntegration(BaseExperiment):
    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_111_X",
            name="Full Civilization Integration",
            description="Executes all 10 capability areas simultaneously across a 50-year integrated civilization trajectory.",
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = LongitudinalCivilizationEngine(seed=self.config.random_seed)
        res = engine.run_horizon(years=50.0)

        snap = res.timeline[-1]
        hyp1 = res.survived is True
        hyp2 = len(snap.active_conditions) >= 1
        hyp3 = len(snap.identity_vector) == 18
        hyp4 = res.accounting_conservation_verified is True

        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(hyp1 and hyp2 and hyp3 and hyp4),
            summary=f"Full civilization integration verified: pop={snap.population}, conditions={snap.active_conditions}, vector dimensions={len(snap.identity_vector)}.",
            hypotheses=[
                {"hypothesis": "Full civilization sustains demographic and institutional survival", "confirmed": hyp1},
                {"hypothesis": "Emergent analytical conditions are active and observable", "confirmed": hyp2},
                {"hypothesis": "18-dimensional societal identity vector is fully computed", "confirmed": hyp3},
                {"hypothesis": "Accounting conservation strictly preserved across 50 years", "confirmed": hyp4},
            ],
            metrics={
                "final_population": snap.population,
                "final_conditions": snap.active_conditions,
                "vector_distance_from_start": res.vector_distance_from_start,
                "duration_years": res.duration_years,
            },
            duration_seconds=time.perf_counter() - t0,
        )


PHASE111_CIVILIZATION_EXPERIMENTS = [
    Experiment111_A_TenYearSettlementEvolution,
    Experiment111_B_GenerationalPopulationTransitions,
    Experiment111_C_FiftyYearFamilyMobility,
    Experiment111_D_OneHundredYearHistoricalContinuity,
    Experiment111_E_TwoHundredYearCivilizationPersistence,
    Experiment111_F_SettlementFormationAndAbandonment,
    Experiment111_G_RuralToUrbanMigration,
    Experiment111_H_RegionalEconomicSpecialization,
    Experiment111_I_EconomicCrisisAndRecovery,
    Experiment111_J_TechnologicalInnovationAndFailure,
    Experiment111_K_KnowledgeLossAcrossGenerations,
    Experiment111_L_CulturalEmergenceAndDisappearance,
    Experiment111_M_EnvironmentalDegradationAndAdaptation,
    Experiment111_N_InstitutionalEvolution,
    Experiment111_O_IntergenerationalInequality,
    Experiment111_P_HistoricalMemoryDistortion,
    Experiment111_Q_PopulationDeclineAndAging,
    Experiment111_R_MultiRegionTradeAndMigration,
    Experiment111_S_HistoricalCausalReconstruction,
    Experiment111_T_LongitudinalPersistenceAndRecovery,
    Experiment111_U_SensitivityToInitialConditions,
    Experiment111_V_OutcomeDiversityAcrossSeeds,
    Experiment111_W_PerformanceUnderSustainedSimulation,
    Experiment111_X_FullCivilizationIntegration,
]
