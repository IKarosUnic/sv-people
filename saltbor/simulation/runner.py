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
        self.identity_factory = IdentityFactory()
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

        if load_existing and self.human_repo.count() >= self.config.initial_population_size:
            logger.info("Restoring population from persistent SQLite database...")
            humans = self.human_repo.load_all()
            for h in humans:
                self.population.register(h)

            saved_rels = self.rel_repo.load_all()
            for r in saved_rels:
                self.social.add_relationship(r)

            saved_tick = self.state_repo.load_tick()
            if saved_tick is not None:
                self.clock.set_tick(saved_tick)
        else:
            logger.info("Creating fresh initial population of 20 synthetic humans...")
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

        # Day transition event and cultural maintenance
        if self.clock.tick_of_day == 0:
            self.culture.decay_unpracticed_culture(current_tick)
            self.social_network.apply_decay_all(current_tick)
            self.cultural_evolution.decay_unpracticed_traditions(current_tick)
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

    def checkpoint(self) -> None:
        """Persist current state snapshot to SQLite."""
        if self.human_repo and self.state_repo and self.rel_repo:
            self.human_repo.save_all(self.population.get_all())
            self.rel_repo.save_all(self.social.get_all_relationships())
            self.state_repo.save_tick(self.clock.current_tick)

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
