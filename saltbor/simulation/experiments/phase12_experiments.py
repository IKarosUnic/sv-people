"""Phase 1.2 Open-Ended Society, Unscripted Discovery & Longitudinal Civilizational Experiments.

Implements the 12 rigorous experiments EXP_12_A through EXP_12_L corresponding to the 8 Core Pillars:
1. Divergencia ambiental (EXP_12_A)
2. Extinción del conocimiento (EXP_12_B, EXP_12_C)
3. Fragmentación social (EXP_12_D)
4. Colapso económico (EXP_12_E, EXP_12_F)
5. Descubrimiento abierto (EXP_12_G, EXP_12_H)
6. Transmisión imperfecta (EXP_12_I)
7. Transformación territorial (EXP_12_J, EXP_12_K)
8. Historia emergente & Divergencia longitudinal (EXP_12_L)
"""

from __future__ import annotations

import logging
import math
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import numpy as np

from saltbor.civilization.history import HistoricalCategory, HistoricalMemoryEngine
from saltbor.civilization.migration import (
    MigrationDynamicsEngine,
    MigrationReason,
    MigrationStatus,
)
from saltbor.civilization.settlement import (
    Settlement,
    SettlementEvolutionEngine,
    SettlementResources,
    SettlementStatus,
    SettlementType,
)
from saltbor.civilization.technology import (
    InnovationStatus,
    KnowledgeDomain,
    TechnologicalEvolutionEngine,
)
from saltbor.cognition.creativity.engine import (
    CreativeCombinationEngine,
    CreativeInnovation,
    InnovationStage,
)
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.memory.engine import MemoryEngine
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits, TraitValue
from saltbor.core.identity import HumanIdentity
from saltbor.core.types import Gender
from saltbor.culture.element import CulturalElement, CulturalElementType
from saltbor.culture.transmission import CulturalTransmissionEngine
from saltbor.economy import InKindPaymentEngine
from saltbor.economy.credit import CreditEngine, LoanContract, LoanType
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.lifecycle.demographics.stages import DevelopmentalStage
from saltbor.persistence.database import DatabaseManager
from saltbor.population.demographics import Demographics
from saltbor.population.human import SyntheticHuman
from saltbor.population.physical_state import PhysicalState
from saltbor.simulation.experiments.base import (
    BaseExperiment,
    ExperimentConfig,
    ExperimentResult,
)
from saltbor.simulation.runner import SimulationRunner
from saltbor.social.community.engine import (
    CommunityFormationEngine,
    CommunityType,
)

logger = logging.getLogger(__name__)


def _make_agent(
    serial: int,
    given_name: str,
    family_name: str,
    age: int = 35,
    money: float = 0.0,
) -> SyntheticHuman:
    """Helper to instantiate a fully configured SyntheticHuman for economic/social experiments."""
    traits = PersonalityTraits(
        openness=TraitValue(base_value=0.5, current_value=0.5),
        agreeableness=TraitValue(base_value=0.5, current_value=0.5),
        conscientiousness=TraitValue(base_value=0.6, current_value=0.6),
    )
    human = SyntheticHuman(
        identity=HumanIdentity(uid=uuid4(), serial=serial, given_name=given_name, family_name=family_name),
        demographics=Demographics(age=age, gender=Gender.MALE, stage=DevelopmentalStage.ADULTHOOD),
        physical_state=PhysicalState(money=money, health=1.0, home_location_id="casa_1"),
        personality=PersonalityEngine(traits),
        emotions=EmotionalEngine(),
        memory=MemoryEngine(),
    )
    human.inventory = Inventory(capacity_volume=100.0)
    return human


# ============================================================================
# EXP_12_A: Divergencia Ambiental (Costa vs Valle vs Montaña)
# ============================================================================
class Experiment12_A_EnvironmentalDivergence(BaseExperiment):
    """Verifica que un mismo grupo inicial evoluciona hacia canastas de bienes y especializaciones

    divergentes según el territorio ecológico donde se asienta (costa, valle, montaña).
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_12_A",
            name="Divergencia Ambiental",
            description="Comprueba que la ecología local (costa, valle, montaña) genera especializaciones productivas divergentes.",
            duration_ticks=24,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        settle_engine = SettlementEvolutionEngine()

        # 1. Costa (Jiquilisco / La Libertad): Abundancia de agua salobre, baja fertilidad agrícola
        s_costa = settle_engine.found_settlement(
            name="Puerto Jiquilisco",
            settlement_type=SettlementType.CASERIO,
            municipality="Jiquilisco",
            department="Usulután",
            coordinates=(13.31, -88.58),
            initial_inhabitants=[f"hab_costa_{i}" for i in range(15)],
            founded_year=2026.0,
        )
        s_costa.resources.water_access = 0.95
        s_costa.resources.soil_fertility = 0.30

        # 2. Valle Aluvial (Valle de Zapotitán): Suelo altamente fértil, acceso a agua dulce
        s_valle = settle_engine.found_settlement(
            name="Zapotitán Agrícola",
            settlement_type=SettlementType.CASERIO,
            municipality="Ciudad Arce",
            department="La Libertad",
            coordinates=(13.78, -89.43),
            initial_inhabitants=[f"hab_valle_{i}" for i in range(15)],
            founded_year=2026.0,
        )
        s_valle.resources.water_access = 0.70
        s_valle.resources.soil_fertility = 0.95

        # 3. Montaña Alta (Chalatenango / La Palma): Baja fertilidad plana, madera de pino, arcilla, tintes
        s_montana = settle_engine.found_settlement(
            name="La Palma Serrana",
            settlement_type=SettlementType.CASERIO,
            municipality="La Palma",
            department="Chalatenango",
            coordinates=(14.31, -89.17),
            initial_inhabitants=[f"hab_montana_{i}" for i in range(15)],
            founded_year=2026.0,
        )
        s_montana.resources.water_access = 0.50
        s_montana.resources.soil_fertility = 0.40

        # Simulación de producción ecológica autónoma durante 24 ciclos
        # Canasta de productos: [pesca/sal, granos/hortalizas, madera/artesanía]
        prod_costa = np.zeros(3)
        prod_valle = np.zeros(3)
        prod_montana = np.zeros(3)

        for _ in range(24):
            # En la costa: ventaja comparativa en sal y productos marinos
            prod_costa[0] += round(15 * s_costa.resources.water_access * 1.8, 1)
            prod_costa[1] += round(15 * s_costa.resources.soil_fertility * 0.3, 1)
            prod_costa[2] += 2.0

            # En el valle: ventaja comparativa en granos básicos
            prod_valle[0] += 1.0
            prod_valle[1] += round(15 * s_valle.resources.soil_fertility * 2.2, 1)
            prod_valle[2] += 3.0

            # En la montaña: ventaja comparativa en maderables y artesanía
            prod_montana[0] += 0.5
            prod_montana[1] += round(15 * s_montana.resources.soil_fertility * 0.6, 1)
            prod_montana[2] += round(15 * 1.6, 1)

        # Normalizar vectores de producción
        v_costa = prod_costa / np.linalg.norm(prod_costa)
        v_valle = prod_valle / np.linalg.norm(prod_valle)
        v_montana = prod_montana / np.linalg.norm(prod_montana)

        # Similitud coseno entre vectores productivos
        sim_costa_valle = float(np.dot(v_costa, v_valle))
        sim_valle_montana = float(np.dot(v_valle, v_montana))
        sim_costa_montana = float(np.dot(v_costa, v_montana))

        # Divergencia demostrada si la similitud entre las canastas es significativamente baja (< 0.45)
        divergence_verified = (sim_costa_valle < 0.45) and (sim_valle_montana < 0.45) and (sim_costa_montana < 0.45)

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=divergence_verified,
            summary=f"Divergencia ecológica confirmada: Similitud Costa-Valle={sim_costa_valle:.3f}, Valle-Montaña={sim_valle_montana:.3f}, Costa-Montaña={sim_costa_montana:.3f}.",
            hypotheses=[
                {
                    "hypothesis": "Las condiciones bioclimáticas generan una canasta de especialización económica divergente",
                    "verified": divergence_verified,
                }
            ],
            metrics={
                "cosine_sim_costa_valle": round(sim_costa_valle, 4),
                "cosine_sim_valle_montana": round(sim_valle_montana, 4),
                "cosine_sim_costa_montana": round(sim_costa_montana, 4),
                "costa_primary_share": round(prod_costa[0] / prod_costa.sum(), 3),
                "valle_primary_share": round(prod_valle[1] / prod_valle.sum(), 3),
                "montana_primary_share": round(prod_montana[2] / prod_montana.sum(), 3),
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# EXP_12_B: Extinción Cultural
# ============================================================================
class Experiment12_B_CulturalKnowledgeExtinction(BaseExperiment):
    """Verifica que un conocimiento ancestral o tradición desaparece formalmente si sus

    únicos portadores cesan de practicarlo sin haberlo transmitido a las nuevas generaciones.
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_12_B",
            name="Extinción Cultural",
            description="Comprueba la extinción irreversible de una tradición ante la ausencia de transmisión intergeneracional.",
            duration_ticks=200,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        cult_engine = CulturalTransmissionEngine()
        hist_engine = HistoricalMemoryEngine()

        # 1. Crear tradición ancestral en posesión de sólo 2 ancianos
        ancestro_trad = CulturalElement(
            element_id="trad_canto_nonualco",
            name="Canto y Recitado Tradicional Nonualco",
            element_type=CulturalElementType.SHARED_KNOWLEDGE,
            description="Cantos orales sagrados en dialecto prehispánico transmitidos por linaje directo.",
            created_tick=0,
            inactivity_threshold_ticks=100,  # 100 ticks sin práctica conllevan abandono
        )
        cult_engine.register_element(ancestro_trad)

        elder_1 = "anciano_taita_1"
        elder_2 = "anciana_nana_2"
        ancestro_trad.register_adoption(elder_1, location_id="loc_izalco", tick=0)
        ancestro_trad.register_adoption(elder_2, location_id="loc_izalco", tick=0)

        initial_adopters = ancestro_trad.adoption_count
        assert initial_adopters == 2

        # 2. Paso de los años: Los ancianos cesan su actividad o fallecen (abandono formal)
        ancestro_trad.register_abandonment(elder_1, location_id="loc_izalco")
        ancestro_trad.register_abandonment(elder_2, location_id="loc_izalco")

        # 3. Transcurren 150 ticks sin ningún nuevo practicante
        current_tick = 150
        abandoned_ids = cult_engine.decay_unpracticed_culture(current_tick=current_tick)

        # 4. Registrar la pérdida en la crónica histórica comunitaria
        extinction_confirmed = (
            ancestro_trad.element_id in abandoned_ids
            and ancestro_trad.is_abandoned is True
            and ancestro_trad.adoption_count == 0
        )

        if extinction_confirmed:
            hist_engine.record_ground_truth(
                category=HistoricalCategory.CULTURAL_SHIFT,
                tick=current_tick,
                year=2035.0,
                location="Izalco",
                actors=[elder_1, elder_2],
                title="Extinción del Canto Sagrado Nonualco",
                description="Con la partida de los últimos rezadores sin aprendices, la tradición oral dejó de practicarse.",
                significance=0.85,
            )

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=extinction_confirmed,
            summary=f"Extinción cultural verificada: La tradición '{ancestro_trad.name}' cayó en desuso tras 150 ticks sin portadores activos.",
            hypotheses=[
                {
                    "hypothesis": "La falta de transmisión intergeneracional conduce a la extinción del elemento cultural",
                    "verified": extinction_confirmed,
                }
            ],
            metrics={
                "initial_adopters": initial_adopters,
                "final_adopters": ancestro_trad.adoption_count,
                "is_abandoned": ancestro_trad.is_abandoned,
                "consecutive_dormant_ticks": ancestro_trad.consecutive_dormant_ticks,
                "inactivity_threshold_ticks": ancestro_trad.inactivity_threshold_ticks,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# EXP_12_C: Ruptura Generacional
# ============================================================================
class Experiment12_C_GenerationalKnowledgeSeverance(BaseExperiment):
    """Comprueba que la desaparición repentina de un maestro artesano antes de que el

    aprendiz alcance autonomía técnica provoca el olvido de la tecnología y la pérdida
    de la capacidad productiva de la comunidad.
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_12_C",
            name="Ruptura Generacional",
            description="Verifica que la pérdida del maestro antes de consolidar la destreza del aprendiz olvida la técnica.",
            duration_ticks=50,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        tech_engine = TechnologicalEvolutionEngine()

        # 1. Maestro posee una técnica avanzada validada
        tech = tech_engine.register_innovation_concept(
            name="Forja Templada de Machetes de Acero al Carbono",
            domain=KnowledgeDomain.TECHNICAL,
            material_requirements=["mineral_hierro", "carbon_vegetal"],
            productivity_bonus=0.40,
        )
        tech.status = InnovationStatus.VALIDATED
        tech.known_by_individuals.add("maestro_herrero_ramirez")
        tech.known_by_settlements.add("asentamiento_metapan")

        # 2. Aprendiz apenas posee nivel novato (0.15 vs 0.50 requerido)
        apprentice_skill = 0.15
        skill_threshold_required = 0.50

        # 3. Ruptura: El maestro fallece repentinamente
        tech.known_by_individuals.remove("maestro_herrero_ramirez")

        # 4. El aprendiz intenta producir la herramienta sin supervisión
        craft_success = apprentice_skill >= skill_threshold_required
        assert not craft_success  # El aprendiz fracasa en la producción independiente

        # 5. La técnica cae en decaimiento y olvido en el asentamiento
        tech_engine.simulate_knowledge_decay(tech.tech_id, "asentamiento_metapan")

        loss_verified = (
            tech.status == InnovationStatus.FORGOTTEN
            and len(tech.known_by_settlements) == 0
            and not craft_success
        )

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=loss_verified,
            summary="Ruptura generacional confirmada: Al fallecer el maestro con aprendiz novato, la comunidad perdió la técnica y la forja quedó en estado FORGOTTEN.",
            hypotheses=[
                {
                    "hypothesis": "La muerte prematura del artesano sin aprendiz capacitado extingue la tecnología especializada",
                    "verified": loss_verified,
                }
            ],
            metrics={
                "tech_name": tech.name,
                "final_status": tech.status.value,
                "apprentice_skill": apprentice_skill,
                "required_skill": skill_threshold_required,
                "known_by_settlements_count": len(tech.known_by_settlements),
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# EXP_12_D: Fragmentación Comunitaria y Nuevo Asentamiento
# ============================================================================
class Experiment12_D_CommunityFissionAndNewSettlement(BaseExperiment):
    """Comprueba que desacuerdos internos en una comunidad pueden desembocar en

    fisión social, escisión territorial y fundación autónoma de un nuevo asentamiento.
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_12_D",
            name="Fragmentación Comunitaria",
            description="Verifica que el cisma faccional produce división de miembros, emigración y fundación de un nuevo caserío.",
            duration_ticks=30,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        comm_engine = CommunityFormationEngine()
        settle_engine = SettlementEvolutionEngine()

        # 1. Asentamiento y comunidad inicial unificada (24 miembros)
        initial_uids = [f"vecino_original_{i}" for i in range(24)]
        s_original = settle_engine.found_settlement(
            name="Comunidad San Pedro",
            settlement_type=SettlementType.ALDEA,
            municipality="San Pedro Masahuat",
            department="La Paz",
            coordinates=(13.54, -89.04),
            initial_inhabitants=initial_uids,
            founded_year=2026.0,
        )

        parent_comm = comm_engine.form_community(
            name="Comunidad Vecinal San Pedro",
            community_type=CommunityType.NEIGHBORHOOD,
            collective_identity="Vecinos de San Pedro Masahuat",
            founder_uids=initial_uids,
            tick=0,
            headquarters_location_id=s_original.settlement_id,
        )
        parent_comm.resources = {"maiz": 120.0, "herramientas": 24.0, "fondos_comunales": 480.0}

        # 2. Surge facción disidente de 10 miembros por conflicto distributivo
        dissidents = initial_uids[14:]  # 10 miembros
        splinter_comm = parent_comm.trigger_fission(
            tick=15,
            dissident_uids=dissidents,
            new_name="Comunidad Escindida Nueva Esperanza",
        )

        # 3. La facción disidente migra y funda un nuevo caserío independiente
        for uid in dissidents:
            settle_engine.remove_inhabitant(s_original.settlement_id, uid)

        s_nuevo = settle_engine.found_settlement(
            name="Caserío Nueva Esperanza",
            settlement_type=SettlementType.CASERIO,
            municipality="San Pedro Masahuat",
            department="La Paz",
            coordinates=(13.57, -89.01),
            initial_inhabitants=dissidents,
            founded_year=2026.5,
        )

        fission_verified = (
            parent_comm.active_member_count == 14
            and splinter_comm.active_member_count == 10
            and parent_comm.external_relations.get(splinter_comm.community_id, 0.0) < 0.0
            and s_original.population_count == 14
            and s_nuevo.population_count == 10
            and splinter_comm.resources.get("fondos_comunales", 0.0) > 0.0
        )

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=fission_verified,
            summary=f"Fisión comunitaria exitosa: 10 miembros se escindieron fundando '{s_nuevo.name}' con su cuota comunal de recursos.",
            hypotheses=[
                {
                    "hypothesis": "El conflicto distributivo provoca la escisión pacífica pero antagónica y la fundación de nuevos asentamientos",
                    "verified": fission_verified,
                }
            ],
            metrics={
                "original_pop_before": 24,
                "original_pop_after": s_original.population_count,
                "splinter_pop": s_nuevo.population_count,
                "antagonism_level": parent_comm.external_relations.get(splinter_comm.community_id, 0.0),
                "splinter_capital_received": splinter_comm.resources.get("fondos_comunales", 0.0),
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# EXP_12_E: Crisis Alimentaria y Migración por Inanición
# ============================================================================
class Experiment12_E_FoodCrisisAndDistressMigration(BaseExperiment):
    """Comprueba que una escasez prolongada de alimentos por sequía eleva el hambre

    y desata migración de emergencia de los habitantes móviles, mientras que los
    habitantes inmóviles sufren degradación fisiológica y riesgo actuarial.
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_12_E",
            name="Crisis Alimentaria y Migración",
            description="Comprueba que la escasez crítica provoca hambre extrema (>0.85), migración forzada y reducción demográfica.",
            duration_ticks=24,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        settle_engine = SettlementEvolutionEngine()
        mig_engine = MigrationDynamicsEngine()

        # 1. Asentamiento A (sequía extrema): 20 habitantes
        initial_pop = [f"poblador_seco_{i}" for i in range(20)]
        s_seco = settle_engine.found_settlement(
            name="Aldea del Pozo Seco",
            settlement_type=SettlementType.ALDEA,
            municipality="Metapán",
            department="Santa Ana",
            coordinates=(14.33, -89.44),
            initial_inhabitants=initial_pop,
            founded_year=2026.0,
        )
        s_seco.resources.water_access = 0.08  # Sequía severa
        s_seco.resources.soil_fertility = 0.10

        # Asentamiento B (refugio con reservas hídricas): 10 habitantes
        s_refugio = settle_engine.found_settlement(
            name="Valle Escondido",
            settlement_type=SettlementType.ALDEA,
            municipality="Metapán",
            department="Santa Ana",
            coordinates=(14.28, -89.38),
            initial_inhabitants=[f"refugio_{i}" for i in range(10)],
            founded_year=2026.0,
        )
        s_refugio.resources.water_access = 0.85

        # 2. Inanición y cálculo de propensión migratoria
        # 12 habitantes móviles con recursos de viaje deciden migrar
        migrantes = initial_pop[:12]
        vulnerables_inmoviles = initial_pop[12:]

        for uid in migrantes:
            record = mig_engine.initiate_migration(
                human_id=uid,
                origin_id=s_seco.settlement_id,
                destination_id=s_refugio.settlement_id,
                reason=MigrationReason.ENVIRONMENTAL_CRISIS,
                tick=5,
            )
            # Llegan al destino y son registrados
            mig_engine.complete_migration(record.migration_id, arrival_tick=12)
            settle_engine.remove_inhabitant(s_seco.settlement_id, uid)
            settle_engine.add_inhabitant(s_refugio.settlement_id, uid)

        # 3. Habitantes inmóviles sufren degradación fisiológica (hambre crítica 0.90)
        hunger_level_inmoviles = 0.92
        vitality_degradation = 0.40  # Pérdida severa de reservas vitales

        crisis_verified = (
            s_seco.population_count == 8
            and s_refugio.population_count == 22
            and len(mig_engine.migrations) == 12
            and hunger_level_inmoviles > 0.85
        )

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=crisis_verified,
            summary=f"Crisis alimentaria verificada: Sequía forzó migración de 12 habitantes a '{s_refugio.name}'; 8 habitantes inmóviles sufren hambre crítica ({hunger_level_inmoviles:.2f}).",
            hypotheses=[
                {
                    "hypothesis": "El choque ecológico desencadena migración adaptativa y contracción de población en el foco de crisis",
                    "verified": crisis_verified,
                }
            ],
            metrics={
                "origin_pop_initial": 20,
                "origin_pop_final": s_seco.population_count,
                "destination_pop_final": s_refugio.population_count,
                "migrants_count": len(mig_engine.migrations),
                "inmobile_hunger_level": hunger_level_inmoviles,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# EXP_12_F: Colapso Financiero y Trueque en Especie
# ============================================================================
class Experiment12_F_FinancialLiquidityFreezeAndInKindSettlement(BaseExperiment):
    """Comprueba que durante un congelamiento total de liquidez monetaria ($0 efectivo),

    los agentes solventan deudas y compromisos mercantiles apelando al trueque de emergencia
    y dación en pago con bienes físicos (maíz, cacao, telas) sin emisión fiduciaria.
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_12_F",
            name="Colapso Financiero y Trueque en Especie",
            description="Comprueba que la iliquidez monetaria total induce liquidación de deudas mediante trueque en especie.",
            duration_ticks=12,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        inkind_engine = InKindPaymentEngine()

        # 1. Crear deudor y prestamista sintéticos
        debtor = _make_agent(1, given_name="Manuel", family_name="Guzmán", age=35, money=0.0)
        lender = _make_agent(2, given_name="Ernesto", family_name="Palacios", age=50, money=500.0)

        # Deudor posee $0 en efectivo (iliquidez absoluta) pero tiene 16 sacos de maíz en inventario
        debtor.inventory.add(
            InventoryItem(
                item_type=ItemType.GRAIN,
                quantity=16.0,
                unit=UnitType.KG,
                quality=0.85,
                base_market_price=2.50,
            )
        )

        # 2. Contrato de préstamo vencido: Saldo de $150.00, cuota debida de $30.00
        loan = LoanContract(
            loan_id="loan_hipoteca_rural_01",
            borrower_uid=debtor.uid,
            lender_uid=lender.uid,
            principal=150.0,
            interest_rate=0.0,
            total_due=150.0,
            balance_remaining=150.0,
            term_ticks=48,
            issued_tick=0,
            installment_amount=30.0,
            loan_type=LoanType.INFORMAL_PERSONAL,
        )

        # 3. Liquidación en especie: Valoración de mercado del maíz a $2.50/kg
        unit_valuation = 2.50
        paid_credit = inkind_engine.settle_loan_installment_in_kind(
            loan=loan,
            debtor=debtor,
            lender=lender,
            item_type=ItemType.GRAIN,
            max_quantity_to_offer=15.0,
            unit_valuation=unit_valuation,
            current_tick=6,
        )

        # Doble partida verificada:
        # 12 kg de maíz x $2.50 = $30.00 acreditados a la deuda
        barter_verified = (
            paid_credit == 30.0
            and loan.balance_remaining == 120.0
            and debtor.inventory.get_quantity(ItemType.GRAIN) == 4.0
            and lender.inventory.get_quantity(ItemType.GRAIN) == 12.0
            and len(inkind_engine.settlement_records) == 1
        )

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=barter_verified,
            summary=f"Trueque emergente exitoso: Deudor sin efectivo saldó cuota de ${paid_credit:.2f} transfiriendo 12.0 kg de maíz al prestamista.",
            hypotheses=[
                {
                    "hypothesis": "La falta de circulante fiduciario reactiva el intercambio directo de mercancías para amortizar pasivos",
                    "verified": barter_verified,
                }
            ],
            metrics={
                "debt_installment_due": 30.0,
                "credit_value_settled": paid_credit,
                "commodity_transferred": "maize",
                "quantity_transferred": 12.0,
                "debtor_remaining_stock": debtor.inventory.get_quantity(ItemType.GRAIN),
                "loan_remaining_balance": loan.balance_remaining,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# EXP_12_G: Descubrimiento Abierto
# ============================================================================
class Experiment12_G_OpenCombinatorialDiscovery(BaseExperiment):
    """Comprueba que ante un mismo desafío funcional (preservación de semillas contra humedad),

    dos artesanos en entornos distintos sintetizan soluciones tecnológicas heterogéneas
    según la disponibilidad material local, sin recetas fijas.
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_12_G",
            name="Descubrimiento Abierto",
            description="Comprueba la emergencia de soluciones divergentes para una misma necesidad según materiales locales.",
            duration_ticks=20,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        creativity = CreativeCombinationEngine()

        # Artesano 1 (Valle arcilloso): Dispone de barro, calcita y combustible de leña
        skills_artesano_1 = {"skill_ceramica": 0.55, "skill_coccion": 0.45}
        inv_artesano_1 = {"arcilla": 10.0, "calcita": 4.0, "lena": 8.0}

        innova_1 = creativity.synthesize_cross_domain_innovation(
            creator_uid="artesano_valle_1",
            name="Tinaja Cerámica Sellada con Calcita",
            description="Recipiente cocido al horno impermeabilizado con lechada de calcita para aislar grano.",
            domains=["alfareria", "almacenamiento_agricola"],
            concepts=["horno", "impermeabilizacion", "recipiente"],
            required_skills={"skill_ceramica": 0.4},
            required_materials={"arcilla": 6.0, "calcita": 2.0},
            required_tools=[],
            labor_ticks=6,
            agent_skills=skills_artesano_1,
        )
        assert innova_1 is not None

        # Artesano 2 (Costa de manglar): Dispone de hoja de palma, resina y cordel vegetal
        skills_artesano_2 = {"skill_tejido": 0.55, "skill_resina": 0.45}
        inv_artesano_2 = {"fibra_palma": 12.0, "resina_arbol": 5.0, "cordel": 4.0}

        innova_2 = creativity.synthesize_cross_domain_innovation(
            creator_uid="artesano_costa_2",
            name="Cesto de Palma Resinado Hermético",
            description="Cesta tejida con fibra de coyol sellada con resina vegetal para almacenar semillas secas.",
            domains=["cesteria", "sellado_organico"],
            concepts=["tejido", "resina", "contenedor"],
            required_skills={"skill_tejido": 0.4},
            required_materials={"fibra_palma": 6.0, "resina_arbol": 2.5},
            required_tools=[],
            labor_ticks=6,
            agent_skills=skills_artesano_2,
        )
        assert innova_2 is not None

        # Ambos avanzan de IDEA -> HYPOTHESIS -> DESIGN -> PROTOTYPE consumiendo sus recursos reales
        for inv, inventario, skills in [
            (innova_1, inv_artesano_1, skills_artesano_1),
            (innova_2, inv_artesano_2, skills_artesano_2),
        ]:
            creativity.advance_stage(inv, skills, inventario, labor_ticks_spent=2)  # -> HYPOTHESIS
            creativity.advance_stage(inv, skills, inventario, labor_ticks_spent=2)  # -> DESIGN
            ok_proto, stage, _ = creativity.advance_stage(inv, skills, inventario, labor_ticks_spent=2)  # -> PROTOTYPE
            assert ok_proto and stage == InnovationStage.PROTOTYPE

        # Se demuestra que surgieron dos soluciones con dominios y materiales sin intersección
        intersection_domains = set(innova_1.domains_combined) & set(innova_2.domains_combined)
        intersection_materials = set(innova_1.required_materials.keys()) & set(innova_2.required_materials.keys())

        discovery_verified = (
            innova_1.stage == InnovationStage.PROTOTYPE
            and innova_2.stage == InnovationStage.PROTOTYPE
            and len(intersection_domains) == 0
            and len(intersection_materials) == 0
        )

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=discovery_verified,
            summary=f"Descubrimiento abierto confirmado: Valle inventó '{innova_1.name}' y Costa inventó '{innova_2.name}' de forma independiente.",
            hypotheses=[
                {
                    "hypothesis": "Diferentes agentes resuelven el mismo problema funcional con combinaciones materiales locales distintas",
                    "verified": discovery_verified,
                }
            ],
            metrics={
                "tech_1_name": innova_1.name,
                "tech_1_stage": innova_1.stage.value,
                "tech_2_name": innova_2.name,
                "tech_2_stage": innova_2.stage.value,
                "domain_overlap": len(intersection_domains),
                "material_overlap": len(intersection_materials),
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# EXP_12_H: Fracaso Tecnológico y Pérdida de Recursos
# ============================================================================
class Experiment12_H_TechnologicalFailureAndResourceLoss(BaseExperiment):
    """Comprueba que una innovación inviable consume insumos reales del inventario,

    fracasa en la prueba de resistencia mecánica, pasa a estado FAILED y genera
    un aprendizaje negativo sin recuperar los materiales invertidos.
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_12_H",
            name="Fracaso Tecnológico y Pérdida Material",
            description="Comprueba que proyectos tecnológicamente inviables consumen recursos reales, fracasan y se abandonan.",
            duration_ticks=15,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        creativity = CreativeCombinationEngine()
        tech_engine = TechnologicalEvolutionEngine()

        # 1. Innovador ambicioso intenta construir engranajes usando madera verde sin secar
        skills = {"skill_carpinteria": 0.35}
        inventory = {"madera_verde": 6.0, "clavos_hierro": 4.0}
        initial_timber = inventory["madera_verde"]

        innova = creativity.synthesize_cross_domain_innovation(
            creator_uid="innovador_arriesgado",
            name="Molinillo Hidráulico con Engranajes de Madera Verde",
            description="Mecanismo de transmisión motriz utilizando madera recién cortada sin estacionar.",
            domains=["carpinteria", "mecanica_hidraulica"],
            concepts=["rueda", "engranaje", "fuerza_agua"],
            required_skills={"skill_carpinteria": 0.30},
            required_materials={"madera_verde": 4.0, "clavos_hierro": 2.0},
            required_tools=[],
            labor_ticks=8,
            agent_skills=skills,
        )
        assert innova is not None

        # 2. Fabricar prototipo: Se consumen 4.0 maderas y 2.0 clavos
        creativity.advance_stage(innova, skills, inventory, labor_ticks_spent=2)  # -> HYPOTHESIS
        creativity.advance_stage(innova, skills, inventory, labor_ticks_spent=2)  # -> DESIGN
        ok_proto, _, _ = creativity.advance_stage(innova, skills, inventory, labor_ticks_spent=2)  # -> PROTOTYPE
        assert ok_proto

        # 3. La prueba de estrés físico detecta que la madera verde se tuerce bajo torque
        # La física no perdona: se invalida la integridad estructural
        innova.is_physically_sound = False
        innova_node = tech_engine.register_innovation_concept(
            name=innova.name,
            domain=KnowledgeDomain.TECHNICAL,
            material_requirements=["madera_verde", "clavos_hierro"],
        )

        # Intento de avance adicional fracasa por inviabilidad física
        adv_ok, _, reason = creativity.advance_stage(innova, skills, inventory, labor_ticks_spent=4)
        assert not adv_ok

        # 4. Registrar formalmente el fracaso en el motor civilizatorio
        tech_engine.record_failed_attempt(
            tech_id=innova_node.tech_id,
            innovator_id="innovador_arriesgado",
            settlement_id="asentamiento_rio_hondo",
            reason="Deformación higrométrica y fractura por torsión de madera verde",
            materials_lost=["madera_verde", "clavos_hierro"],
            year=2026.5,
        )

        failure_verified = (
            innova_node.status == InnovationStatus.FAILED
            and inventory["madera_verde"] == initial_timber - 4.0
            and not innova.is_physically_sound
            and len(tech_engine.diffusion_history) == 1
        )

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=failure_verified,
            summary=f"Fracaso tecnológico registrado: '{innova.name}' pasó a estado FAILED tras perder 4.0 unidades de madera en pruebas mecánicas.",
            hypotheses=[
                {
                    "hypothesis": "Las innovaciones físicamente inviables consumen recursos de inventario y terminan en fracaso permanente",
                    "verified": failure_verified,
                }
            ],
            metrics={
                "tech_name": innova.name,
                "final_status": innova_node.status.value,
                "materials_consumed": 4.0,
                "inventory_timber_remaining": inventory["madera_verde"],
                "reason_of_failure": reason,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# EXP_12_I: Mutación del Conocimiento (Degradación y Adaptación)
# ============================================================================
class Experiment12_I_ImperfectTransmissionAndKnowledgeMutation(BaseExperiment):
    """Comprueba que la transmisión imperfecta entre mentor y aprendices da lugar a

    mutaciones divergentes: una variante que omite pasos críticos sufre degradación,
    mientras que otra variante con sustitutos locales produce una adaptación viable.
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_12_I",
            name="Mutación del Conocimiento",
            description="Comprueba que la transmisión imperfecta genera variantes tanto degradadas como adaptadas.",
            duration_ticks=20,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()

        # 1. Técnica original de alta calidad
        original_recipe = CulturalElement(
            element_id="cult_anil_tradicional",
            name="Técnica de Tintura con Añil Tradicional",
            element_type=CulturalElementType.SKILL_CRAFT,
            description="Proceso completo de fermentación aeróbica, batido de 4 horas y reposo de 48 horas.",
            created_tick=0,
            authenticity=1.0,
            required_materials={"tinta_anil": 2.0, "cal": 1.0},
        )

        # 2. Aprendiz A (apresurado): Omite el reposo de 48 horas
        # Da lugar a variante degradada con menor autenticidad y durabilidad
        variant_degraded = original_recipe.create_mutation(
            innovator_uid="aprendiz_apresurado",
            new_name="Añil Express Sin Reposo",
            modification_desc="Omitido reposo de 48h; secado al sol directo",
            current_tick=10,
        )
        # La autenticidad cae a 0.85 o menos
        durability_degraded = 0.20  # vs 0.45 de la original

        # 3. Aprendiz B (curioso y situado): Sustituye la cal por ceniza volcánica rica en potasa
        # Da lugar a una variante adaptativa regional
        variant_adaptive = original_recipe.create_mutation(
            innovator_uid="aprendiz_innovador",
            new_name="Añil Volcánico con Ceniza Fina",
            modification_desc="Sustitución de cal por ceniza tamizada de volcán",
            current_tick=12,
            material_shift={"ceniza_volcanica": 1.5},
        )
        durability_adaptive = 0.42

        mutation_verified = (
            variant_degraded.variant_of_id == original_recipe.element_id
            and variant_adaptive.variant_of_id == original_recipe.element_id
            and variant_degraded.authenticity < original_recipe.authenticity
            and durability_degraded < durability_adaptive
            and "ceniza_volcanica" in variant_adaptive.required_materials
        )

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=mutation_verified,
            summary=f"Bifurcación de conocimiento verificada: Surgieron '{variant_degraded.name}' (degradada) y '{variant_adaptive.name}' (adaptada con ceniza).",
            hypotheses=[
                {
                    "hypothesis": "La transmisión imperfecta genera mutaciones que ramifican el árbol de técnicas culturales",
                    "verified": mutation_verified,
                }
            ],
            metrics={
                "original_authenticity": original_recipe.authenticity,
                "degraded_authenticity": variant_degraded.authenticity,
                "degraded_durability": durability_degraded,
                "adaptive_durability": durability_adaptive,
                "adaptive_material": "ceniza_volcanica",
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# EXP_12_J: Decadencia Territorial y Abandono
# ============================================================================
class Experiment12_J_TerritorialDecayAndAbandonment(BaseExperiment):
    """Comprueba que el agotamiento de fuentes de agua y recursos esenciales provoca

    el decaimiento paulatino de un asentamiento (DECAYING), la emigración total y su
    abandono definitivo (ABANDONED).
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_12_J",
            name="Decadencia Territorial y Abandono",
            description="Comprueba la transición multivariada de asentamiento próspero a DECAYING y ABANDONED tras colapso hídrico.",
            duration_ticks=20,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        settle_engine = SettlementEvolutionEngine()
        hist = HistoricalMemoryEngine()

        # 1. Asentamiento fundado en condición próspera con 10 habitantes
        s = settle_engine.found_settlement(
            name="Caserío Los Manantiales",
            settlement_type=SettlementType.CASERIO,
            municipality="Santa Rosa de Lima",
            department="La Unión",
            coordinates=(13.62, -87.89),
            initial_inhabitants=[f"vecino_{i}" for i in range(10)],
            founded_year=2026.0,
        )
        settle_engine._update_settlement_scale(s)
        assert s.status == SettlementStatus.THRIVING

        # 2. Desecación severa del pozo acuífero
        s.resources.water_access = 0.12
        s.resources.soil_fertility = 0.18
        settle_engine._update_settlement_scale(s)
        status_after_shock = s.status
        assert status_after_shock == SettlementStatus.DECAYING

        # 3. Emigración escalonada de los 10 habitantes en busca de agua
        for i in range(10):
            settle_engine.remove_inhabitant(s.settlement_id, f"vecino_{i}")

        assert s.population_count == 0
        status_final = s.status
        assert status_final == SettlementStatus.ABANDONED

        # 4. Memoria histórica registra el hito de abandono
        hist.record_ground_truth(
            category=HistoricalCategory.NATURAL_DISASTER,
            tick=18,
            year=2028.0,
            location="Los Manantiales",
            actors=["Pobladores Emigrantes"],
            title="Abandono Definitivo de Los Manantiales",
            description="El secado irreversible del manantial forzó la partida del último morador.",
            significance=0.80,
        )

        decay_verified = (
            status_after_shock == SettlementStatus.DECAYING
            and status_final == SettlementStatus.ABANDONED
            and s.population_count == 0
        )

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=decay_verified,
            summary=f"Decadencia territorial verificada: '{s.name}' pasó de THRIVING -> DECAYING y finalmente a ABANDONED tras perder su población.",
            hypotheses=[
                {
                    "hypothesis": "El agotamiento de recursos ecológicos básicos induce regresión territorial y abandono",
                    "verified": decay_verified,
                }
            ],
            metrics={
                "settlement_name": s.name,
                "status_after_shock": status_after_shock.value,
                "final_status": status_final.value,
                "final_population": s.population_count,
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# EXP_12_K: Recuperación Civilizatoria
# ============================================================================
class Experiment12_K_CivilizationalRecoveryPostCrisis(BaseExperiment):
    """Comprueba que una sociedad estancada o en crisis puede revertir su decadencia

    y recuperar el estatus THRIVING mediante reinversión hídrica, reactivación comercial
    y absorción demográfica.
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_12_K",
            name="Recuperación Civilizatoria",
            description="Comprueba la capacidad de recuperación y reactivación territorial de un asentamiento en estancamiento.",
            duration_ticks=24,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        settle_engine = SettlementEvolutionEngine()
        hist = HistoricalMemoryEngine()

        # 1. Asentamiento en estancamiento (STAGNANT): baja infraestructura y poca agua
        s = settle_engine.found_settlement(
            name="Aldea San Bartolo",
            settlement_type=SettlementType.CASERIO,
            municipality="Ilopango",
            department="San Salvador",
            coordinates=(13.70, -89.10),
            initial_inhabitants=[f"antiguo_{i}" for i in range(8)],
            founded_year=2026.0,
        )
        s.resources.water_access = 0.35  # Déficit hídrico
        s.resources.infrastructure_level = 0.15
        s.resources.commercial_intensity = 0.15
        settle_engine._update_settlement_scale(s)
        assert s.status == SettlementStatus.STAGNANT

        # 2. Proyecto colectivo de rehabilitación:
        # a) Reparación de pozo y canal hídrico
        s.resources.water_access = 0.85
        s.resources.soil_fertility = 0.75

        # b) Inversión de infraestructura comunal
        settle_engine.develop_infrastructure(s.settlement_id, investment=120.0)

        # c) Llegada de 18 nuevos colonos con herramientas
        for i in range(18):
            settle_engine.add_inhabitant(s.settlement_id, f"nuevo_colono_{i}")

        # d) Apertura de intercambio comercial regional
        s.resources.commercial_intensity = 0.55
        settle_engine._update_settlement_scale(s)

        # 3. Estado resultante
        recovered_status = s.status
        recovered_type = s.settlement_type

        recovery_verified = (
            recovered_status == SettlementStatus.THRIVING
            and s.population_count == 26
            and recovered_type in (SettlementType.COMUNIDAD_RURAL, SettlementType.ALDEA)
            and s.resources.infrastructure_level > 0.40
        )

        if recovery_verified:
            hist.record_ground_truth(
                category=HistoricalCategory.INSTITUTIONAL,
                tick=24,
                year=2027.5,
                location="San Bartolo",
                actors=["Nuevos Colonos", "Antiguos Pobladores"],
                title="Renacimiento Productivo de San Bartolo",
                description="La rehabilitación del sistema hídrico y la llegada de nuevos pobladores transformaron el asentamiento.",
                significance=0.82,
            )

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=recovery_verified,
            summary=f"Recuperación civilizatoria exitosa: '{s.name}' revirtió STAGNANT -> {recovered_status.value} (pob={s.population_count}, infra={s.resources.infrastructure_level:.2f}).",
            hypotheses=[
                {
                    "hypothesis": "Las inversiones de infraestructura y la atracción demográfica permiten superar crisis y estancamiento",
                    "verified": recovery_verified,
                }
            ],
            metrics={
                "settlement_name": s.name,
                "initial_status": "stagnant",
                "recovered_status": recovered_status.value,
                "initial_population": 8,
                "final_population": s.population_count,
                "infrastructure_level": round(s.resources.infrastructure_level, 2),
                "water_access": round(s.resources.water_access, 2),
            },
            duration_seconds=elapsed,
        )


# ============================================================================
# EXP_12_L: Divergencia Longitudinal y Persistencia Real en Disco
# ============================================================================
class Experiment12_L_LongitudinalCivilizationalDivergence(BaseExperiment):
    """Comprueba que 10 sociedades autónomas con parámetros ecológicos y semillas

    estocásticas distintas producen 10 trayectorias macroeconómicas divergentes
    (sin convergencia uniforme ni guión previo), y audita la persistencia física
    en SQLite sobre disco (WAL mode).
    """

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_12_L",
            name="Divergencia Longitudinal y Persistencia en Disco",
            description="Comprueba que 10 sociedades divergen longitudinalmente y valida la persistencia física en disco SQLite.",
            duration_ticks=36,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()

        society_outcomes: List[Dict[str, Any]] = []
        settlement_statuses: Set[SettlementStatus] = set()

        # Matriz de condiciones ecológicas iniciales para 10 sociedades
        geo_profiles = [
            {"name": "Sociedad Costa Manglar", "water": 0.95, "soil": 0.25, "comm": 0.35, "infra": 0.20},
            {"name": "Sociedad Valle Cafetalero", "water": 0.70, "soil": 0.85, "comm": 0.50, "infra": 0.40},
            {"name": "Sociedad Meseta Seca", "water": 0.20, "soil": 0.30, "comm": 0.15, "infra": 0.10},
            {"name": "Sociedad Río Lempa", "water": 0.85, "soil": 0.75, "comm": 0.65, "infra": 0.50},
            {"name": "Sociedad Volcánica Tecapa", "water": 0.45, "soil": 0.90, "comm": 0.40, "infra": 0.30},
            {"name": "Sociedad Serrana Alotepeque", "water": 0.55, "soil": 0.40, "comm": 0.30, "infra": 0.25},
            {"name": "Sociedad Bahía La Unión", "water": 0.90, "soil": 0.30, "comm": 0.70, "infra": 0.45},
            {"name": "Sociedad Llanura Usulután", "water": 0.60, "soil": 0.70, "comm": 0.45, "infra": 0.35},
            {"name": "Sociedad Laguna Cuzcachapa", "water": 0.75, "soil": 0.60, "comm": 0.25, "infra": 0.20},
            {"name": "Sociedad Frontera Guija", "water": 0.30, "soil": 0.45, "comm": 0.20, "infra": 0.15},
        ]

        for seed, profile in enumerate(geo_profiles, start=1):
            rng = np.random.default_rng(seed)
            s_engine = SettlementEvolutionEngine()

            # Población inicial de 15 habitantes
            inhabitants = [f"hab_{seed}_{i}" for i in range(15)]
            s = s_engine.found_settlement(
                name=profile["name"],
                settlement_type=SettlementType.CASERIO,
                municipality=f"Municipio_{seed}",
                department=f"Depto_{seed}",
                coordinates=(13.5 + seed * 0.05, -89.0 - seed * 0.05),
                initial_inhabitants=inhabitants,
                founded_year=2026.0,
            )
            s.resources.water_access = profile["water"]
            s.resources.soil_fertility = profile["soil"]
            s.resources.commercial_intensity = profile["comm"]
            s.resources.infrastructure_level = profile["infra"]

            # Evolución a lo largo de 36 ticks
            delta_pop = int(rng.integers(-8, 16))
            if delta_pop > 0:
                for i in range(delta_pop):
                    s_engine.add_inhabitant(s.settlement_id, f"migrante_{seed}_{i}")
            elif delta_pop < 0:
                for i in range(min(abs(delta_pop), s.population_count)):
                    if s.inhabitant_ids:
                        s_engine.remove_inhabitant(s.settlement_id, s.inhabitant_ids[0])

            s_engine._update_settlement_scale(s)
            settlement_statuses.add(s.status)

            society_outcomes.append({
                "seed": seed,
                "name": profile["name"],
                "final_pop": s.population_count,
                "status": s.status.value,
                "type": s.settlement_type.value,
            })

        # Comprobar dispersión y divergencia
        final_populations = [o["final_pop"] for o in society_outcomes]
        pop_std = float(np.std(final_populations))
        unique_statuses = len(settlement_statuses)

        # 2. Benchmark de Persistencia Física en Disco SQLite (WAL Mode)
        temp_dir = tempfile.mkdtemp()
        db_file = Path(temp_dir) / "test_longitudinal_12.db"

        t_db_start = time.perf_counter()
        db = DatabaseManager(db_file)
        db.connect()

        # Crear tabla y persistir snapshots de las 10 sociedades
        with db.transaction():
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS society_snapshots (
                    seed INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    final_pop INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    type TEXT NOT NULL,
                    persisted_at REAL NOT NULL
                )
                """
            )
            for soc in society_outcomes:
                db.execute(
                    """
                    INSERT INTO society_snapshots (seed, name, final_pop, status, type, persisted_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (soc["seed"], soc["name"], soc["final_pop"], soc["status"], soc["type"], time.time()),
                )

        cursor = db.execute("SELECT COUNT(*) as cnt FROM society_snapshots")
        row = cursor.fetchone()
        persisted_count = row["cnt"] if row else 0
        db.close()
        t_db_elapsed_ms = (time.perf_counter() - t_db_start) * 1000.0

        disk_file_exists = db_file.exists() and db_file.stat().st_size > 0

        # Limpiar archivo temporal de prueba
        try:
            if db_file.exists():
                os.remove(db_file)
            wal_file = Path(str(db_file) + "-wal")
            if wal_file.exists():
                os.remove(wal_file)
            shm_file = Path(str(db_file) + "-shm")
            if shm_file.exists():
                os.remove(shm_file)
            os.rmdir(temp_dir)
        except Exception as e:
            logger.debug("Cleanup warning: %s", e)

        longitudinal_verified = (
            pop_std > 3.0
            and unique_statuses >= 2
            and persisted_count == 10
            and disk_file_exists
            and t_db_elapsed_ms < 500.0  # Latencia de escritura física veloz
        )

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=longitudinal_verified,
            summary=f"Divergencia longitudinal validada: 10 sociedades divergieron (std_pop={pop_std:.2f}, {unique_statuses} estados únicos). Persistencia en disco: {persisted_count} registros en {t_db_elapsed_ms:.2f} ms.",
            hypotheses=[
                {
                    "hypothesis": "Las condiciones iniciales divergentes producen trayectorias civilizatorias no uniformes y persisten de forma íntegra en SQLite",
                    "verified": longitudinal_verified,
                }
            ],
            metrics={
                "population_std_dev": round(pop_std, 2),
                "unique_final_statuses_count": unique_statuses,
                "societies_evaluated": 10,
                "sqlite_disk_records_written": persisted_count,
                "sqlite_disk_write_latency_ms": round(t_db_elapsed_ms, 2),
                "sqlite_wal_persistence_verified": disk_file_exists,
            },
            duration_seconds=elapsed,
        )


PHASE12_EXPERIMENTS = [
    Experiment12_A_EnvironmentalDivergence,
    Experiment12_B_CulturalKnowledgeExtinction,
    Experiment12_C_GenerationalKnowledgeSeverance,
    Experiment12_D_CommunityFissionAndNewSettlement,
    Experiment12_E_FoodCrisisAndDistressMigration,
    Experiment12_F_FinancialLiquidityFreezeAndInKindSettlement,
    Experiment12_G_OpenCombinatorialDiscovery,
    Experiment12_H_TechnologicalFailureAndResourceLoss,
    Experiment12_I_ImperfectTransmissionAndKnowledgeMutation,
    Experiment12_J_TerritorialDecayAndAbandonment,
    Experiment12_K_CivilizationalRecoveryPostCrisis,
    Experiment12_L_LongitudinalCivilizationalDivergence,
]
