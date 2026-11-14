"""SimulationRunner — central orchestrator for the Saltbor simulation.

Coordinates the clock, environment, population, social dynamics, event bus,
persistence checkpoints, and metrics logging across simulation ticks.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from saltbor.core.clock import SimulationClock
from saltbor.core.config import SimulationConfig
from saltbor.core.identity import IdentityFactory
from saltbor.core.types import SimulationPhase, Tick
from saltbor.events.bus import EventBus
from saltbor.events.types import EventType, SimulationEvent
from saltbor.persistence.database import DatabaseManager
from saltbor.persistence.repositories import (
    BusinessRepository,
    CollectiveEnterpriseRepository,
    CommunityRepository,
    CulturalRepository,
    EventLogRepository,
    HumanRepository,
    InstitutionRepository,
    LoanRepository,
    MemoryRepository,
    MultiRelationshipRepository,
    RelationshipRepository,
    ReputationRepository,
    SimulationStateRepository,
    SocialEdgeRepository,
)
from saltbor.knowledge.layers.global_graph import GlobalKnowledgeGraph
from saltbor.knowledge.layers.collective_graph import CollectiveKnowledgeGraph
from saltbor.knowledge.layers.hypothesis_graph import HypothesisDiscoveryGraph
from saltbor.knowledge.layers.procedural_graph import ProceduralKnowledgeGraph
from saltbor.knowledge.persistence import KnowledgeRepository
from saltbor.persistence.schema import SchemaManager
from saltbor.population.factory import PopulationFactory
from saltbor.population.lod import CognitiveLOD, CognitiveLODManager
from saltbor.population.registry import PopulationRegistry
from saltbor.simulation.metrics import MetricsTracker
from saltbor.simulation.scheduler import SimulationScheduler
from saltbor.social.conflict.dispute import CollectiveConflictManager
from saltbor.social.dimensions.relationship import MultiDimensionalRelationship
from saltbor.social.engine import SocialEngine
from saltbor.social.language.contextual_dialogue import AdvancedOfflineDialogueEngine
from saltbor.social.network.analyzer import SocialNetworkAnalyzer
from saltbor.social.reputation.engine import ContextualReputationEngine
from saltbor.culture.festival import FestivalManager
from saltbor.culture.transmission import CulturalTransmissionEngine
from saltbor.economy.business.enterprise import BusinessRegistry
from saltbor.economy.commodity import InKindPaymentEngine
from saltbor.economy.credit.engine import CreditEngine
from saltbor.economy.mobility.inequality import EconomicMobilityEngine
from saltbor.institutions.governance import GovernanceEngine
from saltbor.institutions.legal import CommunityLegalCode, JudicialTribunal
from saltbor.institutions.model import SocialInstitution
from saltbor.cognition.social_learning.learning import SocialLearningEngine
from saltbor.world.activities.catalog import ActivityCatalog
from saltbor.world.regional import RegionalTradeEngine
from saltbor.world.environment.weather import EnvironmentEngine
from saltbor.world.geography.terrain import TerrainGrid
from saltbor.world.locations.registry import LocationRegistry
from saltbor.world.navigation.pathfinding import NavigationGraph

# Salvadoran Environmental & Cultural Context Engine (Section 19)
from saltbor.world.salvadoran.geography import SalvadoranGeographyEngine
from saltbor.world.salvadoran.climate import SalvadoranClimateEngine
from saltbor.culture.salvadoran.foodways import SalvadoranFoodwaysEngine
from saltbor.culture.salvadoran.festivities import SalvadoranFestivityEngine
from saltbor.culture.salvadoran.heritage import SalvadoranCulturalEngine
from saltbor.economy.salvadoran.informal_commerce import InformalCommerceEngine
from saltbor.economy.salvadoran.remittances import RemittanceEngine
from saltbor.economy.salvadoran.livelihoods import SalvadoranLivelihoodsEngine
from saltbor.social.language.salvadoran_spanish import SalvadoranSpanishEngine
from saltbor.knowledge.salvadoran.history import SalvadoranHistoricalMemoryEngine
from saltbor.social.salvadoran.community import ADESCOEngine

# Phase 0.9 Dynamic Social Networks, Emergent Communities & Collective Intelligence
from saltbor.social.network.graph_engine import SocialNetworkEngine
from saltbor.social.community.engine import CommunityFormationEngine
from saltbor.social.collective_intelligence.engine import CollectiveIntelligenceEngine
from saltbor.social.communication.engine import SocialCommunicationEngine
from saltbor.social.reputation.reputation_system import ReputationEngine
from saltbor.social.conflict.engine import ConflictCooperationEngine
from saltbor.social.organization.engine import OrganizationalIntelligenceEngine
from saltbor.social.culture.evolution import CulturalEvolutionEngine
from saltbor.social.economy.collective_economy import CollectiveEconomyEngine
from saltbor.social.institutions.emergent import EmergentInstitutionEngine
from saltbor.social.knowledge_integration import SocialKnowledgeBridge
from saltbor.social.lod import SocialLODManager

# Phase 1.3 Distributed Education & Scientific Inquiry
from saltbor.institutions.education import DistributedEducationEngine
from saltbor.cognition.epistemic.scientific_thinking import ScientificThinkingEngine

# Phase 1.4 Runtime Orchestration & Civilization Scenarios
import uuid
from saltbor.simulation.orchestrator import (
    EngineMetadata,
    ExecutionMode,
    OrchestratorContext,
    SimulationRuntimeOrchestrator,
)
from saltbor.simulation.scenarios.profiles import (
    ScenarioProfile,
    ScenarioProfileType,
    get_profile,
)
from saltbor.institutions.legal.code import LegalStatuteType

# Phase 1.5 Human Daily Life, Labor Market & Housing Engines
from saltbor.economy.commerce.commercial_engine import (
    CommercialEngine,
    CommercialEstablishment,
    CommercialProduct,
    EstablishmentType,
    VisitIntent,
)
from saltbor.economy.labor.market import (
    EmploymentContract,
    JobVacancy,
    LaborMarketEngine,
)
from saltbor.economy.housing.engine import (
    HousingEngine,
    HousingLease,
    HousingUnit,
)
from saltbor.economy.household.ledger import HouseholdLedger
from saltbor.social.everyday_life import (
    EverydaySocialEngine,
    SocialInvitation,
)
from saltbor.core.types import ContractType, EmploymentStatus, HousingTenureType
from saltbor.events.causal_graph import CausalEventGraph
from saltbor.health.engine import HealthEngine
from saltbor.accidents.engine import MisfortuneEngine
from saltbor.social.romance.engine import RomanceEngine
from saltbor.cognition.perception.engine import PerceptionEngine
from saltbor.psychology.engine import PsychologicalEngine
from saltbor.world.interaction.world_human_engine import WorldHumanInteractionEngine
from saltbor.lifecycle.family.caregiving import FamilyCaregivingEngine
from saltbor.simulation.extension_runtime import ExtensionRuntime
from saltbor.simulation.integrated_world import IntegratedWorldSimulationEngine

# Phase 1.9 Emergent Society, Institutional Evolution, Governance & CPR
from saltbor.social.organization.emergent_engine import (
    EmergentOrganizationEngine,
    EmergentOrganization,
    OrganizationType,
    MemberRole as OrgMemberRole,
    OrgLifecycleStatus,
)
from saltbor.social.institutions.institutional_evolution import (
    InstitutionalEvolutionEngine,
    EvolvingInstitution,
    InstitutionDomain,
    InstitutionalStatus,
)
from saltbor.social.governance.collective_decision import (
    CollectiveGovernanceEngine,
    CollectiveProposal,
    VotingProtocol as DeliberativeVotingProtocol,
    ProposalStatus,
)
from saltbor.social.norms.norm_evolution import (
    SocialNormEvolutionEngine,
    SocialNorm,
    NormDomain,
    NormFormalization,
    SanctionType,
)
from saltbor.social.resources.cpr_manager import (
    CollectiveResourceManager,
    CommonPoolResource,
    CPRType,
    CPRHealthStatus,
)
from saltbor.social.stratification.mobility_engine import (
    SocialStratificationEngine,
    StratificationProfile,
    InequalityMetrics,
)
from saltbor.social.conflict.intergroup_engine import (
    IntergroupConflictEngine,
    IntergroupDispute,
    IntergroupConflictType,
    ConflictTensionStage,
)

logger = logging.getLogger(__name__)


class SimulationRunner:
    """The master simulation runtime environment."""

    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        self.config = config or SimulationConfig()
        self.clock = SimulationClock(config=self.config)
        self.event_bus = EventBus()
        self.phase = SimulationPhase.INITIALIZING

        # Master RNG
        seed = self.config.random_seed
        if seed is not None:
            import random
            random.seed(seed)
        self.master_rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()

        # World
        self.locations = LocationRegistry.create_saltbor_map()
        self.nav_graph = NavigationGraph.build_saltbor_graph(self.locations)
        self.activities = ActivityCatalog()
        self.terrain = TerrainGrid()
        self.environment = EnvironmentEngine(ticks_per_year=getattr(self.config, "ticks_per_year", 35040.0), rng=self.master_rng)

        # Social & Population
        self.social = SocialEngine()
        self.population = PopulationRegistry()
        self.identity_factory = IdentityFactory(seed=self.config.random_seed)
        self.lod_manager = CognitiveLODManager()

        # Phase 0.5 Societal, Cultural, and Economic Systems
        self.culture = CulturalTransmissionEngine(rng=self.master_rng)
        self.festivals = FestivalManager(rng=self.master_rng)
        self.credit = CreditEngine(rng=self.master_rng)
        self.businesses = BusinessRegistry()
        self.institutions: dict[str, SocialInstitution] = {}
        self.governance = GovernanceEngine(rng=self.master_rng)
        self.mobility = EconomicMobilityEngine()
        self.social_learning = SocialLearningEngine(rng=self.master_rng)
        self.dialogue_engine = AdvancedOfflineDialogueEngine(rng=self.master_rng)
        self.multidimensional_relationships: dict[str, MultiDimensionalRelationship] = {}
        self.network_analyzer = SocialNetworkAnalyzer()
        self.reputation_engine = ContextualReputationEngine()
        self.conflict_manager = CollectiveConflictManager()

        # Phase 0.6 Macro-Regional, Meso-Legal & Commodity-Money Systems
        self.regional_trade = RegionalTradeEngine(rng=self.master_rng)
        self.legal_code = CommunityLegalCode()
        self.court = JudicialTribunal()
        self.inkind_payments = InKindPaymentEngine()

        # Phase 0.6 & 0.7 Knowledge, Epistemic, and Reasoning Architecture
        self.global_knowledge = GlobalKnowledgeGraph()
        self.collective_knowledge = CollectiveKnowledgeGraph()
        self.hypothesis_graph = HypothesisDiscoveryGraph()
        self.procedural_knowledge = ProceduralKnowledgeGraph()
        self.knowledge_repo: Optional[KnowledgeRepository] = None

        # Section 19: Salvadoran Environment & Cultural Context Engine
        self.salvadoran_geography = SalvadoranGeographyEngine()
        self.salvadoran_climate = SalvadoranClimateEngine(seed=seed)
        self.salvadoran_foodways = SalvadoranFoodwaysEngine()
        self.salvadoran_festivities = SalvadoranFestivityEngine()
        self.salvadoran_culture = SalvadoranCulturalEngine()
        self.salvadoran_informal_commerce = InformalCommerceEngine()
        self.salvadoran_remittances = RemittanceEngine()
        self.salvadoran_livelihoods = SalvadoranLivelihoodsEngine()
        self.salvadoran_spanish = SalvadoranSpanishEngine()
        self.salvadoran_history = SalvadoranHistoricalMemoryEngine()
        self.salvadoran_adesco = ADESCOEngine()

        # Phase 0.9 Social Networks, Communities, and Collective Systems
        self.social_network = SocialNetworkEngine()
        self.social.network_engine = self.social_network
        self.community_engine = CommunityFormationEngine()
        self.collective_intelligence = CollectiveIntelligenceEngine(collective_kg=self.collective_knowledge)
        self.communication_engine = SocialCommunicationEngine(social_network=self.social_network)
        self.reputation = ReputationEngine()
        self.conflict_cooperation = ConflictCooperationEngine()
        self.organizational_intelligence = OrganizationalIntelligenceEngine()
        self.cultural_evolution = CulturalEvolutionEngine()
        self.collective_economy = CollectiveEconomyEngine()
        self.emergent_institutions = EmergentInstitutionEngine()
        self.social_knowledge_bridge = SocialKnowledgeBridge(collective_kg=self.collective_knowledge)
        self.social_lod = SocialLODManager()

        # Phase 1.3 Distributed Education & Scientific Inquiry
        self.distributed_education = DistributedEducationEngine(rng=self.master_rng)
        self.scientific_thinking = ScientificThinkingEngine(rng=self.master_rng)

        # Phase 1.5 Commercial, Labor, Housing & Everyday Life Engines
        self.commerce_engine = CommercialEngine()
        self.labor_market = LaborMarketEngine()
        self.housing_engine = HousingEngine()
        self.everyday_social = EverydaySocialEngine()
        self.household_ledgers: dict[str, HouseholdLedger] = {}
        self.community_utility_treasury: dict[str, float] = {"balance": 150.0}

        # Phase 1.5 Extension: Causal, Health, Misfortune, Romance, Caregiving & World Interaction Engines
        self.causal_graph = CausalEventGraph()
        self.health_engine = HealthEngine(seed=seed)
        self.misfortune_engine = MisfortuneEngine(seed=seed)
        self.romance_engine = RomanceEngine(seed=seed)
        self.perception = PerceptionEngine(seed=seed)
        self.psychology = PsychologicalEngine(seed=seed)
        self._psych_event_cursor = 0
        self.world_interaction = WorldHumanInteractionEngine(seed=seed)
        self.world_human_engine = self.world_interaction
        self.family_caregiving = FamilyCaregivingEngine()

        # Phase 1.5 Extension runtime: ties health, romance, misfortune, family
        # lifecycle and territorial interaction into the live tick loop.
        self.extension = ExtensionRuntime(self)

        # Phase 1.8 Integrated World Simulation Engine: unifies street kinematics,
        # places capability hierarchy, diurnal daily life, and environmental causality.
        self.integrated_world = IntegratedWorldSimulationEngine(self)
        self.transportation = self.integrated_world.transportation
        self.daily_life = self.integrated_world.daily_life

        # Phase 1.9 Emergent Society, Institutional Evolution, Governance & CPR
        self.emergent_organizations = EmergentOrganizationEngine()
        self.institutional_evolution = InstitutionalEvolutionEngine()
        self.collective_governance = CollectiveGovernanceEngine()
        self.social_norms = SocialNormEvolutionEngine()
        self.cpr_manager = CollectiveResourceManager()
        self.social_stratification = SocialStratificationEngine()
        self.intergroup_conflicts = IntergroupConflictEngine()

        # Connect causal event graph to listen to all simulation events
        self.event_bus.subscribe(None, lambda evt: self.causal_graph.add_event(evt))

        # Persistence
        self.db = DatabaseManager(self.config.database_path)
        self.human_repo: Optional[HumanRepository] = None
        self.rel_repo: Optional[RelationshipRepository] = None
        self.event_repo: Optional[EventLogRepository] = None
        self.memory_repo: Optional[MemoryRepository] = None
        self.state_repo: Optional[SimulationStateRepository] = None
        self.cultural_repo: Optional[CulturalRepository] = None
        self.loan_repo: Optional[LoanRepository] = None
        self.business_repo: Optional[BusinessRepository] = None
        self.institution_repo: Optional[InstitutionRepository] = None
        self.multi_rel_repo: Optional[MultiRelationshipRepository] = None
        self.social_edge_repo: Optional[SocialEdgeRepository] = None
        self.community_repo: Optional[CommunityRepository] = None
        self.collective_enterprise_repo: Optional[CollectiveEnterpriseRepository] = None
        self.reputation_repo: Optional[ReputationRepository] = None

        # Execution & Metrics
        self.scheduler = SimulationScheduler(rng=self.master_rng)
        self.metrics = MetricsTracker()

        # Callbacks (for observation / visualization hooks)
        self._on_tick_callbacks: list[Callable[[Tick, SimulationRunner], None]] = []

        # Phase 1.4 Runtime Orchestrator
        self.orchestrator = SimulationRuntimeOrchestrator(self)
        self._register_orchestrator_engines()

    def _register_orchestrator_engines(self) -> None:
        """Register all civilization engines into the master orchestrator."""

        # -------------------------------------------------------------
        # 1. PERIODIC: Weekly Cuchubales (Rotating informal savings circles)
        # -------------------------------------------------------------
        def _weekly_cuchubales(ctx: OrchestratorContext, tick: Tick) -> None:
            for c in self.salvadoran_adesco.get_all_cuchubales():
                if c.turns_completed < len(c.member_uids):
                    res = self.salvadoran_adesco.execute_cuchubal_turn(c.circle_id)
                    if res.get("success"):
                        ben_uid = res.get("beneficiary")
                        if ben_uid:
                            h = self.population.get(uuid.UUID(ben_uid))
                            if h:
                                h.physical_state.money += res.get("pot_received_usd", 0.0)
                        self.event_bus.emit(
                            SimulationEvent(
                                event_type=EventType.CUCHUBAL_TURN_EXECUTED,
                                tick=tick,
                                source_human_id=uuid.UUID(ben_uid) if ben_uid else None,
                                data=res,
                                importance=0.60,
                            )
                        )

        self.orchestrator.register(
            EngineMetadata(
                name="WeeklyCuchubales",
                mode=ExecutionMode.PERIODIC,
                period_ticks=672,  # 7 days * 96 ticks/day
                priority=70,
                computational_cost="low",
                step_handler=_weekly_cuchubales,
            )
        )

        # -------------------------------------------------------------
        # 2. PERIODIC: Monthly Remittance Delivery Schedule (every 2880 ticks)
        # -------------------------------------------------------------
        def _monthly_remittance_cycle(ctx: OrchestratorContext, tick: Tick) -> None:
            for prof in self.salvadoran_remittances.get_all_profiles():
                for h in self.population.get_all():
                    if h.physical_state.home_location_id == prof.household_id:
                        h.has_remittance_pending = True

        self.orchestrator.register(
            EngineMetadata(
                name="MonthlyRemittanceSchedule",
                mode=ExecutionMode.PERIODIC,
                period_ticks=2880,  # 30 days * 96 ticks/day
                priority=80,
                computational_cost="low",
                step_handler=_monthly_remittance_cycle,
            )
        )

        # -------------------------------------------------------------
        # 3. EVENT_TRIGGERED: ADESCO Engine (Faenas, Assemblies, Proposals)
        # -------------------------------------------------------------
        def _on_adesco_event(ctx: OrchestratorContext, evt: SimulationEvent) -> None:
            act = evt.data.get("activity") if evt.data else None
            h_id = evt.source_human_id
            h = self.population.get(h_id) if h_id else None

            if act in ("community_meeting", "cooperate"):
                faenas = [f for f in self.salvadoran_adesco.get_all_faenas() if not f.is_completed]
                if faenas and h:
                    proj = faenas[0]
                    res = self.salvadoran_adesco.contribute_labor_to_faena(
                        project_id=proj.project_id,
                        volunteer_uid=str(h.uid),
                        hours_contributed=3.0,
                    )
                    if res.get("is_completed"):
                        if hasattr(self, "cpr_manager") and self.cpr_manager:
                            road = self.cpr_manager.get_resource("camino_el_calvario")
                            if road:
                                road.contribute_maintenance(str(h.uid), labor_hours=3.0, funds_usd=0.0, tick=evt.tick)
                        self.event_bus.emit(
                            SimulationEvent(
                                event_type=EventType.FAENA_COMPLETED,
                                tick=evt.tick,
                                source_human_id=h.uid,
                                location_id=evt.location_id,
                                data={"project_name": proj.name, "cohesion_boost": res.get("community_cohesion_generated", 0.5)},
                                importance=0.75,
                            )
                        )
            elif act == "community_proposal":
                p_id = f"faena_{uuid.uuid4().hex[:6]}"
                name = f"Faena Comunal — Reparación de Drenajes y Caminos ({p_id})"
                self.salvadoran_adesco.create_faena_project(
                    project_id=p_id,
                    name=name,
                    community_id="comunidad_centro_historico",
                    target_problem="reparacion_calle_y_quebrada",
                    required_hours=12.0,
                )
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.COMMUNITY_PROJECT_PROPOSED,
                        tick=evt.tick,
                        source_human_id=h.uid if h else None,
                        location_id=evt.location_id,
                        data={"project_id": p_id, "name": name},
                        importance=0.65,
                    )
                )

        self.orchestrator.register(
            EngineMetadata(
                name="ADESCOEngine",
                mode=ExecutionMode.EVENT_TRIGGERED,
                trigger_events=[EventType.ACTIVITY_STARTED, EventType.COMMUNITY_PROJECT_PROPOSED],
                priority=45,
                computational_cost="low",
                event_handler=_on_adesco_event,
            )
        )

        # -------------------------------------------------------------
        # 4. EVENT_TRIGGERED: Judicial Tribunal & Mediation
        # -------------------------------------------------------------
        def _on_judicial_event(ctx: OrchestratorContext, evt: SimulationEvent) -> None:
            act = evt.data.get("activity") if evt.data else None
            h_id = evt.source_human_id
            plaintiff = self.population.get(h_id) if h_id else None
            if not plaintiff:
                return

            if act == "litigate" or evt.event_type == EventType.DISPUTE_FILED:
                defendant = None
                if evt.target_human_id:
                    defendant = self.population.get(evt.target_human_id)
                if not defendant:
                    others = [p for p in self.population.get_all() if p.uid != plaintiff.uid]
                    if others:
                        defendant = others[self.master_rng.integers(0, len(others))]

                if defendant:
                    case_id = f"legal_{uuid.uuid4().hex[:6]}"
                    claim = evt.data.get("claim_description", "Disputa por daños a propiedad o deuda impaga")
                    damages = float(evt.data.get("claimed_damages", 35.0))
                    case = self.court.file_case(
                        case_id=case_id,
                        plaintiff=plaintiff,
                        defendant=defendant,
                        statute_type=LegalStatuteType.CONTRACT_ENFORCEMENT,
                        claim_description=claim,
                        claimed_damages=damages,
                        evidence_strength=0.75,
                        current_tick=evt.tick,
                    )
                    magistrate = next((p for p in self.population.get_all() if p.uid not in (plaintiff.uid, defendant.uid)), plaintiff)
                    verdict = self.court.adjudicate_and_enforce(
                        case_id=case_id,
                        magistrate=magistrate,
                        legal_code=self.legal_code,
                        plaintiff=plaintiff,
                        defendant=defendant,
                        municipal_institution=None,
                        reputation_engine=self.reputation_engine,
                        current_tick=evt.tick,
                    )
                    self.event_bus.emit(
                        SimulationEvent(
                            event_type=EventType.VERDICT_RENDERED,
                            tick=evt.tick,
                            source_human_id=plaintiff.uid,
                            target_human_id=defendant.uid,
                            location_id=evt.location_id,
                            data={"case_id": case_id, "verdict": verdict.value, "restitution": case.awarded_restitution},
                            importance=0.75,
                        )
                    )
                    if case.awarded_restitution > 0:
                        self.event_bus.emit(
                            SimulationEvent(
                                event_type=EventType.RESTITUTION_ENFORCED,
                                tick=evt.tick,
                                source_human_id=plaintiff.uid,
                                target_human_id=defendant.uid,
                                data={"case_id": case_id, "amount_usd": case.awarded_restitution},
                                importance=0.60,
                            )
                        )
            elif act == "seek_mediation":
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.CONFLICT_RESOLVED,
                        tick=evt.tick,
                        source_human_id=plaintiff.uid,
                        data={"resolution": "Acuerdo de mediación vecinal alcanzado con avenimiento de partes."},
                        importance=0.60,
                    )
                )

        self.orchestrator.register(
            EngineMetadata(
                name="JudicialTribunal",
                mode=ExecutionMode.EVENT_TRIGGERED,
                trigger_events=[EventType.ACTIVITY_STARTED, EventType.DISPUTE_FILED],
                priority=40,
                computational_cost="low",
                event_handler=_on_judicial_event,
            )
        )

        # -------------------------------------------------------------
        # 5. EVENT_TRIGGERED: Informal Commerce Engine
        # -------------------------------------------------------------
        def _on_commerce_event(ctx: OrchestratorContext, evt: SimulationEvent) -> None:
            act = evt.data.get("activity") if evt.data else None
            h_id = evt.source_human_id
            human = self.population.get(h_id) if h_id else None
            if not human:
                return

            store = self.salvadoran_informal_commerce.get_store("tienda_san_pedro")
            if not store:
                return

            if act == "commerce_buy":
                needed = ["frijol_rojo_lb", "arroz_lb", "pan_frances"]
                if human.physical_state.money >= 3.0:
                    res = self.salvadoran_informal_commerce.purchase_del_diario(
                        store_id="tienda_san_pedro",
                        customer_uid=str(human.uid),
                        customer_cash=human.physical_state.money,
                        needed_items=needed,
                    )
                    if res.get("success"):
                        human.physical_state.money = res.get("remaining_cash_usd", human.physical_state.money)
                        human.physical_state.hunger = max(0.0, human.physical_state.hunger - 0.25)
                        self.event_bus.emit(
                            SimulationEvent(
                                event_type=EventType.COMMERCE_TRANSACTION,
                                tick=evt.tick,
                                source_human_id=human.uid,
                                location_id=evt.location_id,
                                data=res,
                                importance=0.35,
                            )
                        )
                else:
                    fiado_res = self.salvadoran_informal_commerce.request_purchase_on_fiado(
                        store_id="tienda_san_pedro",
                        customer_uid=str(human.uid),
                        item_amount_usd=2.50,
                        customer_reputation=0.85,
                    )
                    if fiado_res.get("approved"):
                        human.has_pending_loan = True
                        human.physical_state.hunger = max(0.0, human.physical_state.hunger - 0.20)
                        self.event_bus.emit(
                            SimulationEvent(
                                event_type=EventType.FIADO_CREDIT_GRANTED,
                                tick=evt.tick,
                                source_human_id=human.uid,
                                location_id=evt.location_id,
                                data=fiado_res,
                                importance=0.45,
                            )
                        )
            elif act == "commerce_sell":
                human.physical_state.money += 4.50
                store.cash_box_usd += 4.50
                store.daily_sales_volume_usd += 4.50
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.COMMERCE_TRANSACTION,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        location_id=evt.location_id,
                        data={"type": "sale", "amount_usd": 4.50, "seller": str(human.uid)},
                        importance=0.35,
                    )
                )
            elif act == "repay_debt":
                settle_res = self.salvadoran_informal_commerce.settle_fiado_balance(
                    store_id="tienda_san_pedro",
                    customer_uid=str(human.uid),
                    payment_amount_usd=min(5.0, human.physical_state.money),
                )
                if settle_res.get("success"):
                    human.physical_state.money = max(0.0, human.physical_state.money - settle_res["amount_paid_usd"])
                    if settle_res.get("remaining_debt_usd", 0.0) <= 0.01:
                        human.has_pending_loan = False
                    self.event_bus.emit(
                        SimulationEvent(
                            event_type=EventType.FIADO_CREDIT_SETTLED,
                            tick=evt.tick,
                            source_human_id=human.uid,
                            location_id=evt.location_id,
                            data=settle_res,
                            importance=0.45,
                        )
                    )

        self.orchestrator.register(
            EngineMetadata(
                name="InformalCommerceEngine",
                mode=ExecutionMode.EVENT_TRIGGERED,
                trigger_events=[EventType.ACTIVITY_STARTED],
                priority=35,
                computational_cost="low",
                event_handler=_on_commerce_event,
            )
        )

        # -------------------------------------------------------------
        # 6. EVENT_TRIGGERED: Remittance Engine
        # -------------------------------------------------------------
        def _on_remittance_event(ctx: OrchestratorContext, evt: SimulationEvent) -> None:
            act = evt.data.get("activity") if evt.data else None
            h_id = evt.source_human_id
            human = self.population.get(h_id) if h_id else None
            if not human:
                return

            if act == "receive_remittance":
                hh_id = human.physical_state.home_location_id or "casa_norte_1"
                res = self.salvadoran_remittances.process_monthly_remittance(
                    household_id=hh_id,
                    current_household_cash=human.physical_state.money,
                )
                if res.get("received"):
                    amt = res.get("remittance_amount_usd", 250.0)
                    human.physical_state.money += amt
                    human.has_remittance_pending = False
                    self.event_bus.emit(
                        SimulationEvent(
                            event_type=EventType.REMITTANCE_RECEIVED,
                            tick=evt.tick,
                            source_human_id=human.uid,
                            location_id=evt.location_id,
                            data=res,
                            importance=0.70,
                        )
                    )

        self.orchestrator.register(
            EngineMetadata(
                name="RemittanceEngine",
                mode=ExecutionMode.EVENT_TRIGGERED,
                trigger_events=[EventType.ACTIVITY_STARTED],
                priority=30,
                computational_cost="low",
                event_handler=_on_remittance_event,
            )
        )

        # -------------------------------------------------------------
        # 7. EVENT_TRIGGERED: Distributed Education & Mentorship
        # -------------------------------------------------------------
        def _on_education_event(ctx: OrchestratorContext, evt: SimulationEvent) -> None:
            act = evt.data.get("activity") if evt.data else None
            h_id = evt.source_human_id
            human = self.population.get(h_id) if h_id else None
            if not human:
                return

            if act in ("teach_apprentice", "learn_trade"):
                apprs = self.distributed_education.get_all_apprenticeships()
                active_apprs = [a for a in apprs if a.is_active and not a.is_graduated]
                if active_apprs:
                    agr = active_apprs[0]
                    agr.ticks_completed += 4
                    agr.current_proficiency = min(1.0, agr.current_proficiency + 0.05)
                    if agr.current_proficiency >= agr.target_proficiency and not agr.is_graduated:
                        agr.is_graduated = True
                        agr.is_active = False
                        self.event_bus.emit(
                            SimulationEvent(
                                event_type=EventType.APPRENTICESHIP_GRADUATED,
                                tick=evt.tick,
                                source_human_id=human.uid,
                                location_id=evt.location_id,
                                data={"contract_id": agr.contract_id, "skill_domain": agr.skill_domain, "final_proficiency": agr.current_proficiency},
                                importance=0.75,
                            )
                        )

        self.orchestrator.register(
            EngineMetadata(
                name="DistributedEducationEngine",
                mode=ExecutionMode.EVENT_TRIGGERED,
                trigger_events=[EventType.ACTIVITY_STARTED],
                priority=50,
                computational_cost="low",
                event_handler=_on_education_event,
            )
        )

        # -------------------------------------------------------------
        # 8. EVENT_TRIGGERED: Scientific Thinking Engine
        # -------------------------------------------------------------
        def _on_scientific_event(ctx: OrchestratorContext, evt: SimulationEvent) -> None:
            act = evt.data.get("activity") if evt.data else None
            h_id = evt.source_human_id
            human = self.population.get(h_id) if h_id else None
            if not human:
                return

            if act == "conduct_experiment":
                session = self.scientific_thinking.start_investigation(
                    creator_uid=str(human.uid),
                    observation="Variación en rendimiento de maíz criollo usando abono bocashi orgánico",
                    anomaly_detected=True,
                    tick=evt.tick,
                )
                self.scientific_thinking.formulate_question(
                    session,
                    subject="abono_bocashi",
                    variable_of_interest="rendimiento_maiz",
                    tick=evt.tick,
                )
                self.scientific_thinking.generate_hypothesis(
                    session,
                    subject="abono_bocashi",
                    predicate="increases",
                    proposed_effect=1.8,
                    prior_confidence=0.45,
                    tick=evt.tick,
                )
                exp = self.scientific_thinking.design_experiment(
                    session=session,
                    manipulated_var="dosis_bocashi_kg",
                    treatment_val=2.0,
                    control_val=0.0,
                    trials=3,
                    tick=evt.tick,
                )
                self.scientific_thinking.run_experimental_trials(session, true_causal_effect=1.8, noise_std=0.2, tick=evt.tick)
                status, revised_belief = self.scientific_thinking.evaluate_and_revise(session, true_causal_effect=1.8, tick=evt.tick)

                is_supported = (status in ("supported", "confirmed"))
                ev_type = EventType.HYPOTHESIS_CONFIRMED if is_supported else EventType.HYPOTHESIS_REFUTED
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=ev_type,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        location_id=evt.location_id,
                        data={
                            "hypothesis": "abono_bocashi increases rendimiento_maiz",
                            "confidence": revised_belief.confidence,
                            "trials": 3,
                        },
                        importance=0.65,
                    )
                )

        self.orchestrator.register(
            EngineMetadata(
                name="ScientificThinkingEngine",
                mode=ExecutionMode.EVENT_TRIGGERED,
                trigger_events=[EventType.ACTIVITY_STARTED],
                priority=55,
                computational_cost="medium",
                event_handler=_on_scientific_event,
            )
        )

        # -------------------------------------------------------------
        # 9. EVENT_TRIGGERED: Advanced Contextual Dialogue Engine
        # -------------------------------------------------------------
        def _on_dialogue_event(ctx: OrchestratorContext, evt: SimulationEvent) -> None:
            act = evt.data.get("activity") if evt.data else None
            h_id = evt.source_human_id
            human = self.population.get(h_id) if h_id else None
            if not human or act not in ("socialize", "negotiate", "community_meeting"):
                return

            loc_id = human.physical_state.current_location_id
            co_located = [h for h in self.population.get_at_location(loc_id) if h.uid != human.uid]
            if co_located:
                partner = co_located[0]
                pair_key = f"{human.uid}_{partner.uid}"
                mrel = self.multidimensional_relationships.get(pair_key)
                if not mrel:
                    mrel = MultiDimensionalRelationship(
                        relationship_id=pair_key,
                        human_a_id=human.uid,
                        human_b_id=partner.uid,
                    )
                    self.multidimensional_relationships[pair_key] = mrel

                session = self.dialogue_engine.conduct_negotiation(
                    human_a=human,
                    human_b=partner,
                    topic="asuntos_comunitarios_y_cosecha",
                    relationship=mrel,
                    proposal_favor="colaboracion_mutua",
                    current_tick=evt.tick,
                )
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.DIALOGUE_OCCURRED,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        target_human_id=partner.uid,
                        location_id=loc_id,
                        data={
                            "speaker_a": human.name,
                            "speaker_b": partner.name,
                            "summary": session.summary,
                            "outcome": session.outcome.value,
                            "turns_count": len(session.turns),
                            "sample_turn": session.turns[0].text if session.turns else "",
                        },
                        importance=0.40,
                    )
                )

        self.orchestrator.register(
            EngineMetadata(
                name="AdvancedOfflineDialogueEngine",
                mode=ExecutionMode.EVENT_TRIGGERED,
                trigger_events=[EventType.ACTIVITY_STARTED],
                priority=60,
                computational_cost="low",
                cooldown_ticks=4,
                event_handler=_on_dialogue_event,
            )
        )

        # -------------------------------------------------------------
        # 9. EVENT_TRIGGERED: Phase 1.5 Everyday Life, Commercial, Labor & Housing
        # -------------------------------------------------------------
        def _on_phase15_everyday_event(ctx: OrchestratorContext, evt: SimulationEvent) -> None:
            act = evt.data.get("activity") if evt.data else None
            h_id = evt.source_human_id
            human = self.population.get(h_id) if h_id else None
            if not human:
                return

            loc_id = evt.location_id or human.physical_state.current_location_id or "plaza_central"

            # 1. Commercial Activities
            if act in ("window_shopping", "browse_store", "compare_prices", "purchase_goods", "dine_out"):
                intent_map = {
                    "window_shopping": VisitIntent.WINDOW_SHOP,
                    "browse_store": VisitIntent.BROWSE,
                    "compare_prices": VisitIntent.COMPARE_PRICES,
                    "purchase_goods": VisitIntent.PURCHASE,
                    "dine_out": VisitIntent.DINE,
                }
                intent = intent_map[act]
                est_id = "comedor_dona_maria" if act == "dine_out" else ("tienda_san_pedro" if loc_id == "tienda_san_pedro" else "mercado_central")
                co_located = [str(h.uid) for h in self.population.get_at_location(loc_id)]
                outcome = self.commerce_engine.execute_visit(
                    agent=human,
                    establishment_id=est_id,
                    intent=intent,
                    current_hour=self.clock.current_hour_int,
                    co_located_agents=co_located,
                )
                ev_type = (
                    EventType.WINDOW_SHOPPING_DONE if act == "window_shopping"
                    else EventType.STORE_BROWSED if act == "browse_store"
                    else EventType.PRICES_COMPARED if act == "compare_prices"
                    else EventType.DINED_OUT if act == "dine_out"
                    else EventType.GOODS_PURCHASED
                )
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=ev_type,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        location_id=loc_id,
                        data={
                            "establishment": est_id,
                            "intent": intent.value,
                            "purchased": outcome.purchased,
                            "spent_usd": outcome.total_spent_usd,
                            "reasoning": outcome.reasoning,
                        },
                        importance=0.35,
                    )
                )

            # 2. Dynamic Labor Market Activities
            elif act == "search_employment":
                vacs = self.labor_market.search_vacancies(human)
                if vacs:
                    best_vac = vacs[0]
                    self.labor_market.apply_for_job(human, best_vac.vacancy_id)
                    data = {"status": "applied", "vacancy_id": best_vac.vacancy_id, "title": best_vac.title}
                else:
                    day_res = self.labor_market.perform_informal_day_labor(human, current_tick=evt.tick)
                    data = {"status": "day_labor", "earned_usd": day_res["earned_usd"]}
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.JOB_SEARCHED,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        location_id=loc_id,
                        data=data,
                        importance=0.40,
                    )
                )

            # 3. Housing and Shelter Activities
            elif act == "seek_housing":
                rentals = self.housing_engine.get_available_rentals(max_daily_rent=3.50)
                if rentals:
                    target_unit = rentals[0]
                    lease_res = self.housing_engine.lease_unit(human, target_unit.unit_id, current_tick=evt.tick)
                    data = {"status": "leased" if lease_res.get("leased") else "failed", "unit_id": target_unit.unit_id}
                else:
                    data = {"status": "no_vacancy"}
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.HOUSING_SEARCHED,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        location_id=loc_id,
                        data=data,
                        importance=0.45,
                    )
                )

            elif act == "seek_shelter":
                human.housing_tenure = HousingTenureType.SHELTER
                human.physical_state.home_location_id = "casa_comunal"
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.SHELTER_ENTERED,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        location_id="casa_comunal",
                        data={"reason": "Seeking temporary shelter from precarity"},
                        importance=0.50,
                    )
                )

            # 4. Leisure Activities
            elif act == "visit_park":
                human.physical_state.energy = min(1.0, human.physical_state.energy + 0.05)
                if hasattr(human.emotions, "adjust_mood"):
                    human.emotions.adjust_mood(+0.10)
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.PARK_VISITED,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        location_id="parque_la_ceiba",
                        data={"activity": "strolling_and_resting"},
                        importance=0.25,
                    )
                )

            elif act in ("visit_friend", "visit_relative"):
                if hasattr(human.emotions, "adjust_mood"):
                    human.emotions.adjust_mood(+0.15)
                ev_t = EventType.FRIEND_VISITED if act == "visit_friend" else EventType.RELATIVE_VISITED
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=ev_t,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        location_id=loc_id,
                        data={"activity": act},
                        importance=0.30,
                    )
                )

            elif act == "play_sport":
                human.physical_state.energy = max(0.05, human.physical_state.energy - 0.15)
                if hasattr(human.emotions, "adjust_mood"):
                    human.emotions.adjust_mood(+0.20)
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.SPORT_PLAYED,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        location_id="parque_la_ceiba",
                        data={"sport": "futbol_comunitario"},
                        importance=0.30,
                    )
                )

            elif act == "participate_in_hobby":
                if hasattr(human.emotions, "adjust_mood"):
                    human.emotions.adjust_mood(+0.12)
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.HOBBY_PRACTICED,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        location_id=loc_id,
                        data={"hobby": "lectura_o_artesania"},
                        importance=0.25,
                    )
                )

            elif act == "seek_entertainment":
                if hasattr(human.emotions, "adjust_mood"):
                    human.emotions.adjust_mood(+0.18)
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.ENTERTAINMENT_ATTENDED,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        location_id=loc_id,
                        data={"type": "musica_y_juegos"},
                        importance=0.30,
                    )
                )

            elif act == "request_assistance":
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.ASSISTANCE_REQUESTED,
                        tick=evt.tick,
                        source_human_id=human.uid,
                        location_id=loc_id,
                        data={"reason": "hardship_and_subsistence"},
                        importance=0.45,
                    )
                )

        self.orchestrator.register(
            EngineMetadata(
                name="Phase15EverydayLifeEngine",
                mode=ExecutionMode.EVENT_TRIGGERED,
                trigger_events=[EventType.ACTIVITY_STARTED],
                priority=42,
                computational_cost="low",
                event_handler=_on_phase15_everyday_event,
            )
        )

    def _initialize_civilization_entities(self, load_existing: bool = False) -> None:
        """Seed or restore initial micro-enterprises, stores, remittances, and apprenticeships."""
        if load_existing and self.state_repo:
            commerce_data = self.state_repo.load_state("civilization_commerce")
            if commerce_data:
                logger.info("Restored civilization commerce state from database.")

        # 1. Corner Store (Tienda San Pedro)
        if not self.salvadoran_informal_commerce.get_store("tienda_san_pedro"):
            owner = self.population.get_all()[1] if self.population.count > 1 else self.population.get_all()[0]
            self.salvadoran_informal_commerce.register_corner_store(
                store_id="tienda_san_pedro",
                name="Tienda y Pulpería San Pedro",
                owner_uid=str(owner.uid),
                location_id="mercado_central",
                starting_cash=65.0,
            )

        # 2. ADESCO Faena & Cuchubal
        if not self.salvadoran_adesco.get_all_faenas():
            self.salvadoran_adesco.create_faena_project(
                project_id="faena_fundacional",
                name="Reparación Comunitaria de Cuesta El Calvario tras Lluvias",
                community_id="comunidad_centro_historico",
                target_problem="reparar_camino_vecinal",
                required_hours=20.0,
            )

        if not self.salvadoran_adesco.get_all_cuchubales():
            members = [str(h.uid) for h in self.population.get_all()[:6]]
            if members:
                self.salvadoran_adesco.create_cuchubal(
                    circle_id="cuchubal_vecinal_1",
                    name="Cuchubal de Confianza San Esteban",
                    organizer_uid=members[0],
                    member_uids=members,
                    contribution_usd=10.0,
                )

        # 3. Family Remittances (35% of households)
        if not self.salvadoran_remittances.get_all_profiles():
            for house_id in ("casa_norte_1", "casa_sur_1"):
                self.salvadoran_remittances.register_household_remittance(
                    household_id=house_id,
                    monthly_amount_usd=250.0,
                    sender_relation="hijo_en_eeuu",
                    reliability=0.90,
                )

        # 4. Mentorship Agreement
        if not self.distributed_education.get_all_apprenticeships() and self.population.count >= 3:
            humans = self.population.get_all()
            mentor = humans[0]
            apprentice = humans[2]
            mentor.is_mentor = True
            apprentice.is_apprentice = True
            self.distributed_education.establish_apprenticeship(
                mentor_uid=str(mentor.uid),
                apprentice_uid=str(apprentice.uid),
                domain="carpinteria",
                target_proficiency=0.70,
            )

        # 5. Phase 1.5 Commercial Establishments
        if not self.commerce_engine.get_all_establishments():
            # Verified Real Establishments
            self.commerce_engine.register_establishment(
                CommercialEstablishment(
                    establishment_id="mercado_central",
                    name="Mercado Central de San Salvador",
                    establishment_type=EstablishmentType.MERCADO_STALL,
                    location_id="mercado_central",
                    is_verified_real=True,
                    opening_hours=(6, 18),
                    operating_cost_per_day=5.0,
                    catalog={
                        "frijol_rojo": CommercialProduct("frijol_rojo", "Frijol Rojo Seda", "staple_food", 1.10, 80.0, "lb"),
                        "maiz_blanco": CommercialProduct("maiz_blanco", "Maíz Blanco", "staple_food", 0.35, 120.0, "lb"),
                        "queso_duro": CommercialProduct("queso_duro", "Queso Duro Viejo", "staple_food", 4.25, 25.0, "lb"),
                        "platanos": CommercialProduct("platanos", "Plátano Maduro", "staple_food", 0.30, 60.0, "unidad"),
                    },
                )
            )
            self.commerce_engine.register_establishment(
                CommercialEstablishment(
                    establishment_id="comedor_dona_maria",
                    name="Pupusería y Comedor Doña María",
                    establishment_type=EstablishmentType.COMEDOR_PUPUSERIA,
                    location_id="comedor_dona_maria",
                    is_verified_real=True,
                    opening_hours=(6, 21),
                    operating_cost_per_day=6.0,
                    catalog={
                        "pupusa_revuelta": CommercialProduct("pupusa_revuelta", "Pupusa Revuelta", "prepared_meal", 0.90, 100.0, "unidad"),
                        "pupusa_queso": CommercialProduct("pupusa_queso", "Pupusa de Queso con Loroco", "prepared_meal", 1.00, 80.0, "unidad"),
                        "plato_desayuno": CommercialProduct("plato_desayuno", "Desayuno Típico", "prepared_meal", 2.50, 40.0, "plato"),
                        "cafe_de_olla": CommercialProduct("cafe_de_olla", "Café de Olla", "prepared_meal", 0.50, 50.0, "taza"),
                    },
                )
            )
            # Explicitly Simulated Establishments
            self.commerce_engine.register_establishment(
                CommercialEstablishment(
                    establishment_id="tienda_san_pedro",
                    name="Tienda y Pulpería San Pedro",
                    establishment_type=EstablishmentType.PULPERIA,
                    location_id="mercado_central",
                    is_verified_real=False,
                    opening_hours=(6, 21),
                    operating_cost_per_day=3.5,
                    catalog={
                        "pan_frances": CommercialProduct("pan_frances", "Pan Francés (Bolsa)", "staple_food", 0.50, 60.0, "bolsa"),
                        "huevos": CommercialProduct("huevos", "Cartón de Huevos", "staple_food", 2.20, 25.0, "carton"),
                        "azucar": CommercialProduct("azucar", "Azúcar Morena", "staple_food", 0.55, 40.0, "lb"),
                        "aceite": CommercialProduct("aceite", "Aceite Vegetal", "staple_food", 1.75, 20.0, "botella"),
                    },
                )
            )

        # 6. Phase 1.5 Housing Units
        if not self.housing_engine.get_all_units():
            self.housing_engine.register_unit(
                HousingUnit(
                    unit_id="casa_norte_1",
                    name="Vivienda Don Carlos (San Esteban)",
                    location_id="casa_norte_1",
                    tenure_type=HousingTenureType.OWNER_OCCUPIED,
                    rent_per_day=0.0,
                    capacity=4,
                )
            )
            self.housing_engine.register_unit(
                HousingUnit(
                    unit_id="casa_sur_1",
                    name="Casa de Alquiler Familia Martínez",
                    location_id="casa_sur_1",
                    tenure_type=HousingTenureType.RENTAL,
                    rent_per_day=3.00,
                    capacity=4,
                )
            )
            self.housing_engine.register_unit(
                HousingUnit(
                    unit_id="meson_centro_1",
                    name="Pieza en Mesón El Centro 1",
                    location_id="casa_norte_1",
                    tenure_type=HousingTenureType.INFORMAL_HOUSING,
                    rent_per_day=1.50,
                    capacity=2,
                )
            )
            self.housing_engine.register_unit(
                HousingUnit(
                    unit_id="albergue_comunitario",
                    name="Albergue y Refugio Comunal",
                    location_id="casa_comunal",
                    tenure_type=HousingTenureType.SHELTER,
                    rent_per_day=0.0,
                    capacity=8,
                )
            )

        # 7. Phase 1.5 Household Ledgers
        if not self.household_ledgers and self.population.count > 0:
            humans = self.population.get_all()
            h1 = HouseholdLedger(
                household_id="hogar_carlos",
                dwelling_unit_id="casa_norte_1",
                dwelling_type="owner_occupied",
                shared_savings=120.0,
            )
            for m in humans[:3]:
                h1.add_member(m.uid)
            self.household_ledgers["hogar_carlos"] = h1

            if len(humans) > 3:
                h2 = HouseholdLedger(
                    household_id="hogar_rosa",
                    dwelling_unit_id="casa_sur_1",
                    dwelling_type="rental",
                    shared_savings=80.0,
                )
                for m in humans[3:6]:
                    h2.add_member(m.uid)
                self.household_ledgers["hogar_rosa"] = h2

        # 8. Phase 1.5 Labor Market Vacancies
        if not self.labor_market.get_open_vacancies() and self.population.count > 0:
            humans = self.population.get_all()
            employer_uid = str(humans[0].uid) if humans else "emp_01"
            self.labor_market.post_vacancy(
                business_id="taller_artesanal",
                employer_uid=employer_uid,
                title="Ayudante de Carpintería",
                required_skill="carpinteria",
                min_skill_level=0.30,
                offered_daily_wage=12.00,
                contract_type=ContractType.INFORMAL_WAGE,
                location_id="taller_artesanal",
            )
            self.labor_market.post_vacancy(
                business_id="comedor_dona_maria",
                employer_uid=employer_uid,
                title="Pupusera Auxiliar",
                required_skill="cocina",
                min_skill_level=0.25,
                offered_daily_wage=14.00,
                contract_type=ContractType.INFORMAL_WAGE,
                location_id="comedor_dona_maria",
            )

        # 9. Phase 1.9 Common-Pool Resources (CPR)
        if not self.cpr_manager.get_all_resources() and self.population.count > 0:
            humans = self.population.get_all()
            all_uids = {str(h.uid) for h in humans}
            self.cpr_manager.register_resource(
                resource_id="pozo_san_esteban",
                name="Pozo Comunal y Tanque San Esteban",
                resource_type=CPRType.WATER_WELL,
                community_id="comunidad_centro_historico",
                location_id="plaza_central",
                max_capacity=15000.0,
                initial_stock=12000.0,
                regeneration_rate=1200.0,
                unit="litros",
                daily_quota=50.0,
                authorized_users=all_uids,
                tick=0,
            )
            self.cpr_manager.register_resource(
                resource_id="camino_el_calvario",
                name="Cuesta y Camino Vecinal El Calvario",
                resource_type=CPRType.COMMUNAL_ROAD,
                community_id="comunidad_centro_historico",
                location_id="casa_norte_1",
                max_capacity=100.0,
                initial_stock=90.0,
                regeneration_rate=2.0,
                unit="transitabilidad_%",
                daily_quota=100.0,
                authorized_users=all_uids,
                tick=0,
            )
            self.cpr_manager.register_resource(
                resource_id="troja_comunal_centro",
                name="Troja y Silo Comunal de Granos Básicos",
                resource_type=CPRType.COMMUNITY_GRAIN_BANK,
                community_id="comunidad_centro_historico",
                location_id="mercado_central",
                max_capacity=200.0,
                initial_stock=150.0,
                regeneration_rate=0.0,
                unit="quintales",
                daily_quota=2.0,
                authorized_users=all_uids,
                tick=0,
            )

        # 10. Phase 1.9 Social Norms
        if not self.social_norms.get_all_norms():
            self.social_norms.register_norm(
                title="Turno y Cuota Hídrica en Pozo Comunal",
                description="Extracción máxima de 50 litros por familia por día para asegurar sostenibilidad del pozo.",
                domain=NormDomain.RESOURCE_SHARING,
                formalization=NormFormalization.COMMUNITY_AGREEMENT,
                default_sanction=SanctionType.REPUTATION_LOSS,
                fine_usd=2.50,
                legitimacy=0.88,
                enforcement_rigor=0.75,
                tick=0,
            )
            self.social_norms.register_norm(
                title="Solidaridad Obligatoria en Faenas Comunitarias",
                description="Participación activa en cuadrillas voluntarias de mantenimiento vial y limpieza convocadas por ADESCO.",
                domain=NormDomain.CIVIC_COOPERATION,
                formalization=NormFormalization.FORMAL_BYLAW,
                default_sanction=SanctionType.ECONOMIC_FINE,
                fine_usd=5.00,
                legitimacy=0.90,
                enforcement_rigor=0.80,
                tick=0,
            )
            self.social_norms.register_norm(
                title="Cumplimiento del Fiado Vecinal en Puestos de Mercado",
                description="Pago puntual de deudas de confianza por alimentos básicos en la fecha pactada.",
                domain=NormDomain.COMMERCIAL_PRACTICE,
                formalization=NormFormalization.IMPLICIT_CUSTOM,
                default_sanction=SanctionType.SOCIAL_OSTRACISM,
                fine_usd=0.0,
                legitimacy=0.85,
                enforcement_rigor=0.65,
                tick=0,
            )

        # 11. Phase 1.9 Evolving Institutions
        if not self.institutional_evolution.get_all_institutions():
            humans = self.population.get_all()
            director_uid = str(humans[0].uid) if humans else "admin_01"
            self.institutional_evolution.register_institution(
                name="ADESCO y Administración Comunal Centro Histórico",
                formal_acronym="ADESCO-CH",
                domain=InstitutionDomain.COMMUNITY_ADMINISTRATION,
                mission="Organización vecinal, gestión de faenas y defensa de infraestructura comunitaria.",
                headquarters_loc_id="casa_comunal",
                initial_treasury_usd=250.0,
                director_uid=director_uid,
                initial_rules=["Asamblea mensual obligatoria", "Aporte de faena comunal", "Veeduría de tesorería"],
                tick=0,
            )
            self.institutional_evolution.register_institution(
                name="Unidad Comunitaria de Salud Familiar El Calvario",
                formal_acronym="UCSF-CALVARIO",
                domain=InstitutionDomain.HEALTHCARE,
                mission="Atención médica ambulatoria, prevención de epidemias y saneamiento ambiental.",
                headquarters_loc_id="clinica_salud",
                initial_treasury_usd=400.0,
                director_uid=director_uid,
                initial_rules=["Atención prioritaria a menores", "Uso racional de medicamentos básicos"],
                tick=0,
            )

        # 12. Phase 1.9 Emergent Organizations
        if not self.emergent_organizations.get_all_organizations() and self.population.count >= 3:
            humans = self.population.get_all()
            founder_uids = [str(h.uid) for h in humans[:3]]
            self.emergent_organizations.create_organization(
                name="Asociación Gremial de Comerciantes del Mercado Central",
                org_type=OrganizationType.COMMERCIAL_ASSOCIATION,
                mission="Defensa colectiva de puestos, regulación de fiado y compras mayoristas de maíz.",
                founder_uids=founder_uids,
                initial_treasury_usd=120.0,
                headquarters_location_id="mercado_central",
                tick=0,
            )

    def initialize(self, load_existing: bool = False) -> None:
        """Set up database schema, initialize or load population, and wire events."""
        self.db.connect()
        SchemaManager.create_tables(self.db)

        self.human_repo = HumanRepository(self.db)
        self.rel_repo = RelationshipRepository(self.db)
        self.event_repo = EventLogRepository(self.db)
        self.memory_repo = MemoryRepository(self.db)
        self.state_repo = SimulationStateRepository(self.db)
        self.cultural_repo = CulturalRepository(self.db)
        self.loan_repo = LoanRepository(self.db)
        self.business_repo = BusinessRepository(self.db)
        self.institution_repo = InstitutionRepository(self.db)
        self.multi_rel_repo = MultiRelationshipRepository(self.db)
        self.knowledge_repo = KnowledgeRepository(self.db)
        self.social_edge_repo = SocialEdgeRepository(self.db)
        self.community_repo = CommunityRepository(self.db)
        self.collective_enterprise_repo = CollectiveEnterpriseRepository(self.db)
        self.reputation_repo = ReputationRepository(self.db)

        # Connect persistence handler to event bus
        self.event_bus.subscribe(None, lambda evt: self.event_repo.save(evt))  # type: ignore[misc]

        # Dispatch relevant events directly to affected individuals' memory & cognitive systems
        def _dispatch_to_individuals(evt: SimulationEvent) -> None:
            if evt.source_human_id:
                h = self.population.get(evt.source_human_id)
                if h:
                    h.receive_event(evt, self.event_bus)
            if evt.target_human_id and evt.target_human_id != evt.source_human_id:
                h = self.population.get(evt.target_human_id)
                if h:
                    h.receive_event(evt, self.event_bus)

        self.event_bus.subscribe(None, _dispatch_to_individuals)

        # Connect master runtime orchestrator to event bus
        self.event_bus.subscribe(None, self.orchestrator.handle_event)

        if load_existing and self.human_repo.count() > 0:
            logger.info("Restoring population from persistent SQLite database...")
            humans = self.human_repo.load_all()
            for h in humans:
                self.population.register(h)
            if humans:
                # Deterministic UIDs are derived from serial + seed.  Without
                # advancing the factory, new agents added after a checkpoint
                # load would reuse existing serials and overwrite people.
                self.identity_factory.advance_to(
                    max(int(h.identity.serial) for h in humans) + 1
                )

            saved_rels = self.rel_repo.load_all()
            for r in saved_rels:
                self.social.add_relationship(r)

            saved_tick = self.state_repo.load_tick()
            if saved_tick is not None:
                self.clock.set_tick(saved_tick)
        else:
            logger.info("Creating fresh initial population of %d synthetic humans...", self.config.initial_population_size)
            try:
                self.db.execute("DELETE FROM humans")
                self.db.execute("DELETE FROM relationships")
                self.db.execute("DELETE FROM simulation_state")
            except Exception as ex:
                logger.debug("Database cleanup ignored: %s", ex)

            humans = PopulationFactory.create_population(
                config=self.config,
                identity_factory=self.identity_factory,
                rng=self.master_rng,
                try_nemotron=False,
            )
            for h in humans:
                self.population.register(h)

            PopulationFactory.setup_initial_relationships(humans, self.social)

            # Checkpoint initial state
            self.human_repo.save_all(humans)
            self.rel_repo.save_all(self.social.get_all_relationships())
            self.state_repo.save_tick(0)

        # Seed or restore civilization institutions, stores, remittances, and educational contracts
        self._initialize_civilization_entities(load_existing=load_existing)

        # Restore extension domain state, or reconstruct initial unions/households.
        self.extension.initialize(load_existing=load_existing)

        # Phase 1.7: guarantee a psychological state for every living person.
        # The state is created from the individual's Big Five if this is a new
        # population, or restored from the extension checkpoint if resuming.
        for human in self.population.get_all():
            self.psychology.ensure(human)
        self._psych_event_cursor = len(getattr(self.event_bus, "event_log", []))

        # Emit simulation started event
        self.event_bus.emit(
            SimulationEvent(
                event_type=EventType.SIMULATION_STARTED,
                tick=self.clock.current_tick,
                data={"population_size": self.population.count},
                importance=0.8,
            )
        )
        self.phase = SimulationPhase.RUNNING

    def step(self) -> Tick:
        """Advance the simulation by exactly one discrete tick (15 simulated minutes)."""
        t0 = time.perf_counter()
        initial_event_count = len(self.event_bus.event_log)

        current_tick = self.clock.tick()

        # Step environmental climate & weather dynamics
        self.environment.step(current_tick)
        self.regional_trade.step(current_tick)

        # Master orchestrator steps scheduled and periodic civilization engines
        self.orchestrator.step(current_tick)

        # Day transition event and cultural maintenance
        if self.clock.tick_of_day == 0:
            # Phase 1.5 Dynamic Household living costs & utility overhead
            for h_ledger in self.household_ledgers.values():
                h_ledger.execute_daily_living_expenses(
                    current_tick=current_tick,
                    population_registry=self.population,
                    utility_treasury=self.community_utility_treasury,
                )

            # Phase 1.5 Housing daily rent collection, arrears & eviction dynamics
            self.housing_engine.collect_daily_rent(
                current_tick=current_tick,
                population_registry=self.population,
            )

            # Phase 1.5 Labor market daily payroll cycle (wages paid from enterprise liquidity)
            self.labor_market.execute_daily_payroll(
                business_registry=self.businesses,
                population_registry=self.population,
                current_tick=current_tick,
            )

            # Phase 1.5 Commercial establishments daily overhead and counter reset
            self.commerce_engine.execute_daily_accounting(current_tick)

            # Phase 1.5 Extension: Environmental impact of settlement
            self.world_interaction.record_human_environmental_impact(
                population_count=len(self.population.get_all()),
                current_tick=current_tick,
                event_bus=self.event_bus,
                causal_graph=self.causal_graph,
            )

            self.culture.decay_unpracticed_culture(current_tick)
            self.social_network.apply_decay_all(current_tick)
            self.cultural_evolution.decay_unpracticed_traditions(current_tick)
            alive_uids = {str(h.uid) for h in self.population.get_all()}
            self.cultural_evolution.check_cultural_extinction(alive_uids, current_tick)
            try:
                candidates = []
                for h in self.population.get_all():
                    interests = set()
                    if h.demographics.occupation:
                        interests.add(h.demographics.occupation)
                    for g in h.autonomy.get_active_goals():
                        interests.add(g.category)
                    candidates.append({
                        "uid": str(h.uid),
                        "interests": list(interests),
                        "location": h.physical_state.current_location_id,
                        "goals": {g.description for g in h.autonomy.get_active_goals()},
                        "friends": [str(fid) for fid in self.social.get_friends(h.uid)],
                    })
                self.community_engine.check_spontaneous_formation(candidates, tick=current_tick)
            except Exception:
                pass

            # Phase 1.9 Emergent Society, Institutions, Norms & CPR daily cycles
            self.social_norms.step(current_tick)
            self.cpr_manager.step(current_tick)
            self.institutional_evolution.step(current_tick)
            strat_metrics = self.social_stratification.step(self.population, self.social, current_tick)
            if strat_metrics:
                self.event_bus.emit(
                    SimulationEvent(
                        event_type=EventType.SOCIAL_STRATIFICATION_UPDATED,
                        tick=current_tick,
                        data={
                            "gini_income": strat_metrics.gini_income,
                            "gini_wealth": strat_metrics.gini_wealth,
                            "palma_ratio": strat_metrics.palma_ratio,
                            "upward_mobility": strat_metrics.upward_mobility_count,
                            "downward_mobility": strat_metrics.downward_mobility_count,
                        },
                        importance=0.45,
                    )
                )

            # Collect periodic membership dues for emergent organizations
            for org in self.emergent_organizations.get_all_organizations():
                org.collect_member_dues(self.population, current_tick)

            # Check spontaneous formation of organizations based on needs and resources
            try:
                org_candidates = []
                for h in self.population.get_all():
                    h_needs = []
                    if h.physical_state.money < 25.0:
                        h_needs.append("socorro")
                    occ = h.demographics.occupation.lower() if h.demographics.occupation else ""
                    if any(w in occ for w in ("comerciante", "vendedora", "pupusera")):
                        h_needs.append("comercio")
                    elif any(w in occ for w in ("agricultor", "jornalero", "peon")):
                        h_needs.append("agricultura")
                    org_candidates.append({
                        "uid": str(h.uid),
                        "needs": h_needs,
                        "location": h.physical_state.current_location_id,
                        "capital": max(5.0, h.physical_state.money * 0.15),
                    })
                spontaneous_org = self.emergent_organizations.attempt_spontaneous_formation(org_candidates, tick=current_tick)
                if spontaneous_org:
                    self.event_bus.emit(
                        SimulationEvent(
                            event_type=EventType.ORGANIZATION_FORMED,
                            tick=current_tick,
                            data={
                                "org_id": spontaneous_org.org_id,
                                "name": spontaneous_org.name,
                                "org_type": spontaneous_org.org_type.value,
                                "founder_count": len(spontaneous_org.leaders),
                            },
                            importance=0.65,
                        )
                    )
            except Exception:
                pass
            self.event_bus.emit(
                SimulationEvent(
                    event_type=EventType.DAY_STARTED,
                    tick=current_tick,
                    data={"day": self.clock.current_day + 1},
                    importance=0.4,
                )
            )

        # Build spatial location index for O(1) co-location discovery
        self.population.build_location_index()

        # Determine agent update sequence
        execution_order = self.scheduler.get_execution_order(self.population, current_tick)

        # Update each human
        for human in execution_order:
            curr_loc = human.physical_state.current_location_id
            # Discover others situated at the same location
            co_located = [
                h.uid for h in self.population.get_at_location(curr_loc)
                if h.uid != human.uid
            ] if curr_loc else []

            human.update(
                tick=current_tick,
                clock=self.clock,
                event_bus=self.event_bus,
                location_registry=self.locations,
                activity_catalog=self.activities,
                social_engine=self.social,
                nearby_humans=co_located,
                integrated_world=self.integrated_world,
            )

            # Phase 1.5 Extension: biological and emotional trajectories
            self.extension.step_individual(human, current_tick)

        # Phase 1.5 Extension: global daily orchestration (exposure, treatment,
        # accidents, disasters, romance, family lifecycle).
        self.extension.step(current_tick)

        # Phase 1.8 Integrated World: advances street journeys, verifies place occupancy,
        # handles road blockages, and synchronizes community historical memory.
        self.integrated_world.step(current_tick)

        # Phase 1.7: appraise the events that actually reached each person in
        # this tick, then advance the psychological state.  The cursor prevents
        # replaying history and keeps the cost proportional to new events.
        event_log = getattr(self.event_bus, "event_log", [])
        new_events = event_log[self._psych_event_cursor:]
        if new_events:
            self._psych_event_cursor = len(event_log)
            self.psychology.process_events(
                new_events,
                self.population,
                social=self.social,
            )
        self.psychology.step_population(
            self.population,
            current_tick,
            social=self.social,
            event_bus=self.event_bus,
            lod_manager=self.lod_manager,
            tick_minutes=self.config.tick_duration_minutes,
        )

        # Periodic checkpointing
        if current_tick % self.config.checkpoint_interval_ticks == 0:
            self.checkpoint()

        elapsed = time.perf_counter() - t0
        events_emitted = len(self.event_bus.event_log) - initial_event_count

        self.metrics.record_tick(
            tick=current_tick,
            duration_sec=elapsed,
            events_emitted=events_emitted,
            population=self.population,
        )

        # Notify any observer callbacks
        for cb in self._on_tick_callbacks:
            try:
                cb(current_tick, self)
            except Exception as ex:
                logger.warning("Tick callback failed: %s", ex)

        return current_tick

    def run(self, num_ticks: int = 96) -> None:
        """Run the simulation loop for a specified number of ticks."""
        for _ in range(num_ticks):
            self.step()

    def _prune_deceased_rows(self, living_ids: list[str]) -> None:
        """Remove database rows for humans no longer in the live registry."""
        living_set = {str(uid) for uid in living_ids}
        try:
            cursor = self.db.execute("SELECT uid FROM humans")
            stored_ids = [str(row["uid"]) for row in cursor.fetchall()]
        except Exception as ex:
            logger.debug("Unable to inspect persisted humans for pruning: %s", ex)
            return
        for stored_uid in stored_ids:
            if stored_uid not in living_set:
                self.human_repo.delete(stored_uid)

    def checkpoint(self) -> None:
        """Persist the current state snapshot to SQLite in one transaction.

        The individual repositories each open a transaction of their own.  At
        checkpoint frequency that meant dozens of separate commits (and WAL
        syncs) per simulated day; wrapping the whole snapshot collapses them
        into one, which the persistence layer supports because nested
        transactions yield the already-open connection.
        """
        with self.db.transaction():
            self._checkpoint_body()

    def _checkpoint_body(self) -> None:
        if self.human_repo and self.state_repo and self.rel_repo:
            living = self.population.get_all()
            living_ids = [str(h.uid) for h in living]
            self.human_repo.save_all(living)

            # Deceased humans are removed from the live registry, so they must
            # not survive in the database either.  Deleting stale rows here is
            # what prevents a dead character from being resurrected on reload.
            self._prune_deceased_rows(living_ids)

            living_set = set(living_ids)
            living_relationships = [
                rel for rel in self.social.get_all_relationships()
                if str(rel.human_a_id) in living_set and str(rel.human_b_id) in living_set
            ]
            self.rel_repo.save_all(living_relationships)
            self.state_repo.save_tick(self.clock.current_tick)

            # Phase 1.5 Extension: health, romance, accidents, family lifecycle,
            # territorial interaction, perception, psychological state and the
            # causal DAG.
            try:
                self.state_repo.save_state("phase15_extension", self.extension.to_dict())
            except Exception as ex:
                logger.warning("Error persisting Phase 1.5 extension state: %s", ex)

            # Phase 1.7: durable autobiographical timeline (incremental rows).
            try:
                self.psychology.persist_timeline(self.db)
            except Exception as ex:
                logger.warning("Error persisting psychological timeline: %s", ex)

            # Persist Phase 0.5 Societal Entities
            if self.cultural_repo:
                for elem in self.culture.get_all_elements():
                    self.cultural_repo.save(elem)
            if self.loan_repo:
                for loan in self.credit.loans.values():
                    self.loan_repo.save(loan)
            if self.business_repo:
                for biz in self.businesses.get_all():
                    self.business_repo.save(biz)
            if self.institution_repo:
                for inst in self.institutions.values():
                    self.institution_repo.save(inst)
            if self.multi_rel_repo:
                for mrel in self.multidimensional_relationships.values():
                    self.multi_rel_repo.save(mrel)
            if self.knowledge_repo:
                for h in self.population.get_all():
                    if hasattr(h, "knowledge_graph") and h.knowledge_graph is not None:
                        self.knowledge_repo.save_individual_knowledge(h.knowledge_graph)

            # Persist Phase 0.9 Social Networks, Communities & Enterprises
            if self.social_edge_repo:
                self.social_edge_repo.save_all(self.social_network.get_all_edges())
            if self.community_repo:
                for comm in self.community_engine.get_all_communities(active_only=False):
                    self.community_repo.save(comm)
            if self.collective_enterprise_repo:
                for ent in self.collective_economy.get_all_enterprises(active_only=False):
                    self.collective_enterprise_repo.save(ent)

            # Persist Phase 1.4 Civilization Integration Entities
            try:
                stores_data = []
                for st in self.salvadoran_informal_commerce.get_all_stores():
                    accounts_data = {
                        c_uid: {
                            "balance": acc.current_balance_usd,
                            "limit": acc.credit_limit_usd,
                            "trust": acc.trust_score,
                        }
                        for c_uid, acc in st.active_credit_accounts.items()
                    }
                    stores_data.append({
                        "id": st.store_id,
                        "name": st.name,
                        "cash": st.cash_box_usd,
                        "daily_sales": st.daily_sales_volume_usd,
                        "accounts": accounts_data,
                    })
                self.state_repo.save_state("civilization_commerce", stores_data)

                faenas_data = [
                    {
                        "id": f.project_id,
                        "name": f.name,
                        "hours": f.accumulated_labor_hours,
                        "completed": f.is_completed,
                    }
                    for f in self.salvadoran_adesco.get_all_faenas()
                ]
                self.state_repo.save_state("civilization_faenas", faenas_data)

                cases_data = [
                    {
                        "id": c.case_id,
                        "plaintiff": str(c.plaintiff_uid),
                        "defendant": str(c.defendant_uid),
                        "claim": c.claim_description,
                        "verdict": c.verdict.value if c.verdict else None,
                        "restitution": c.awarded_restitution,
                    }
                    for c in self.court.get_all_cases()
                ]
                self.state_repo.save_state("civilization_judicial", cases_data)

                # Persist Phase 1.9 Society, Institutions, CPR & Norms
                phase19_data = {
                    "organizations": [
                        {
                            "id": o.org_id,
                            "name": o.name,
                            "type": o.org_type.value,
                            "treasury": o.treasury_usd,
                            "status": o.status.value,
                            "members_count": len(o.members),
                        }
                        for o in self.emergent_organizations.get_all_organizations(active_only=False)
                    ],
                    "institutions": [
                        {
                            "id": i.institution_id,
                            "name": i.name,
                            "domain": i.domain.value,
                            "treasury": i.treasury_usd,
                            "legitimacy": i.legitimacy,
                            "status": i.status.value,
                        }
                        for i in self.institutional_evolution.get_all_institutions(active_only=False)
                    ],
                    "cpr": [
                        {
                            "id": r.resource_id,
                            "name": r.name,
                            "stock": r.current_stock,
                            "capacity": r.max_capacity,
                            "status": r.status.value,
                        }
                        for r in self.cpr_manager.get_all_resources()
                    ],
                    "norms": [
                        {
                            "id": n.norm_id,
                            "title": n.title,
                            "adherence": n.adherence_rate,
                            "active": n.is_active,
                        }
                        for n in self.social_norms.get_all_norms(active_only=False)
                    ],
                }
                self.state_repo.save_state("civilization_phase19_society", phase19_data)
            except Exception as ex:
                logger.warning("Error persisting Phase 1.4 civilization entities: %s", ex)

            self.event_bus.emit(
                SimulationEvent(
                    event_type=EventType.CHECKPOINT_SAVED,
                    tick=self.clock.current_tick,
                    data={"tick": self.clock.current_tick},
                    importance=0.3,
                )
            )

    def register_on_tick_callback(self, cb: Callable[[Tick, SimulationRunner], None]) -> None:
        """Register an observer hook called after every tick."""
        self._on_tick_callbacks.append(cb)

    def close(self) -> None:
        """Cleanly close database connections."""
        self.checkpoint()
        self.db.close()
        self.phase = SimulationPhase.STOPPED
