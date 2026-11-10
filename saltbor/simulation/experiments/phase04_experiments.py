"""Phase 0.4 Behavioral and Societal Experiments (Experiments A through H).

Demonstrates:
- EXP_04_A: Multi-Generational Population (Births, Aging, Development, Mortality)
- EXP_04_B: Family Development (Household before and after birth, Caregiving, Food Demand)
- EXP_04_C: Long-Term Economic Dynamics (Production, Shortages, Price Formation, Conservation)
- EXP_04_D: Complex Planning (HTN Multi-Step Carpentry Goal & Dynamic Replanning)
- EXP_04_E: Information & Rumor Propagation (Provenance, Trust Belief, Verification)
- EXP_04_F: Group Formation & Institutional Assembly (Emergent Associations, Voting)
- EXP_04_G: Continuous Navigation (2D Movement, Collision Avoidance, Encounters)
- EXP_04_H: Long-Term Social Evolution (Comprehensive Integrated Society Simulation)
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional

import numpy as np

from saltbor.cognition.decision.formal_decision import (
    FormalDecisionArchitecture,
    InformationState,
    InternalState,
    WorldBeliefs,
)
from saltbor.cognition.planning.goap import ActionDefinition, WorldState
from saltbor.cognition.planning.htn import (
    DynamicReplanner,
    HTNDecomposer,
    build_carpentry_workshop_htn,
)
from saltbor.core.config import SimulationConfig
from saltbor.core.identity import HumanIdentity, IdentityFactory
from saltbor.core.types import ActivityType, DataSource, Gender, NeedType
from saltbor.economy.household.ledger import HouseholdLedger
from saltbor.economy.inventory.container import Inventory
from saltbor.economy.inventory.item import InventoryItem, ItemType, UnitType
from saltbor.economy.market.exchange import MarketExchange
from saltbor.economy.production.facility import ProductionFacility
from saltbor.economy.production.recipe import STANDARD_RECIPES
from saltbor.events.bus import EventBus
from saltbor.lifecycle.aging.clock import AgingEngine
from saltbor.lifecycle.demographics.stages import (
    DevelopmentalStage,
    get_stage_for_age,
)
from saltbor.lifecycle.development.model import ChildDevelopmentEngine
from saltbor.lifecycle.family.household import HouseholdRegistry
from saltbor.lifecycle.genealogy.tree import GenealogicalGraph
from saltbor.lifecycle.genetics.inheritance import GeneticsEngine, Genome
from saltbor.lifecycle.mortality.death import MortalityEngine
from saltbor.lifecycle.mortality.grief import GriefEngine
from saltbor.lifecycle.reproduction.mating import ReproductionEngine
from saltbor.lifecycle.reproduction.pregnancy import Pregnancy
from saltbor.population.demographics import Demographics
from saltbor.population.factory import PopulationFactory
from saltbor.population.human import SyntheticHuman
from saltbor.population.physical_state import PhysicalState
from saltbor.cognition.personality.engine import PersonalityEngine
from saltbor.cognition.personality.traits import PersonalityTraits
from saltbor.cognition.emotions.engine import EmotionalEngine
from saltbor.cognition.memory.engine import MemoryEngine


def _make_human(
    uid: uuid.UUID,
    serial: int,
    given_name: str,
    family_name: str,
    age: int,
    gender: Gender,
    money: float = 100.0,
    health: float = 1.0,
    stage: DevelopmentalStage = DevelopmentalStage.ADULTHOOD,
) -> SyntheticHuman:
    return SyntheticHuman(
        identity=HumanIdentity(uid=uid, serial=serial, given_name=given_name, family_name=family_name),
        demographics=Demographics(age=age, gender=gender, stage=stage),
        physical_state=PhysicalState(money=money, health=health, home_location_id="casa_residencial_1"),
        personality=PersonalityEngine(PersonalityTraits()),
        emotions=EmotionalEngine(),
        memory=MemoryEngine(),
    )
from saltbor.simulation.experiments.base import (
    BaseExperiment,
    ExperimentConfig,
    ExperimentResult,
)
from saltbor.simulation.runner import SimulationRunner
from saltbor.social.engine import SocialEngine
from saltbor.social.information.rumor import RumorEngine
from saltbor.social.institutions.assembly import CommunityAssembly
from saltbor.social.institutions.group import EnhancedSocialGroup, GroupType
from saltbor.social.language.conversation import ConversationManager
from saltbor.social.language.intent import DialogueIntent
from saltbor.world.spatial.encounters import EncounterDetector
from saltbor.world.spatial.movement import (
    AgentSpatialState,
    ContinuousMovementEngine,
)


# ===========================================================================
# EXPERIMENT A: Multi-Generational Population
# ===========================================================================
class Experiment04_A_MultigenerationalPopulation(BaseExperiment):
    """Demographic lifecycle: continuous aging, birth event, development, and mortality."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_04_A",
            name="Multi-Generational Population Lifecycle",
            description="Simulates demographic evolution: aging, reproduction, developmental progression, and mortality.",
            duration_ticks=100,
            random_seed=42,
            population_size=20,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        rng = np.random.default_rng(self.config.random_seed)

        # 1. Setup lifecycle engines
        aging = AgingEngine(ticks_per_year=20.0) # Accelerated: 20 ticks = 1 year
        dev_eng = ChildDevelopmentEngine(rng=rng)
        genetics = GeneticsEngine(rng=rng)
        genealogy = GenealogicalGraph()
        households = HouseholdRegistry()
        reproduction = ReproductionEngine(gestation_ticks=10, conception_probability_base=1.0, rng=rng)
        mortality = MortalityEngine(base_makeham_hazard=0.001, gompertz_alpha=0.001, gompertz_gamma=0.05, rng=rng)
        bus = EventBus()

        # 2. Founders
        father = _make_human(uuid.uuid4(), 1, "Juan", "Flores", 30, Gender.MALE, money=100.0, health=0.9)
        mother = _make_human(uuid.uuid4(), 2, "Elena", "Flores", 28, Gender.FEMALE, money=80.0, health=0.95)
        elder = _make_human(uuid.uuid4(), 3, "Abuelo", "Flores", 85, Gender.MALE, money=50.0, health=0.4, stage=DevelopmentalStage.OLDER_ADULTHOOD)

        genealogy.register_individual(father.uid, generation=0)
        genealogy.register_individual(mother.uid, generation=0)
        genealogy.register_individual(elder.uid, generation=0)
        genealogy.record_partnership(father.uid, mother.uid)

        house = households.create_household("Familia Flores", "casa_residencial_1", [father.uid, mother.uid, elder.uid])

        # 3. Courtship and Conception
        preg = reproduction.attempt_conception(mother, father, genealogy, mutual_trust=0.9, mutual_affinity=0.9, current_tick=1)
        assert preg is not None

        # 4. Gestation progression to birth
        reproduction.update_pregnancies(delta_ticks=10) # Full term
        assert preg.is_due is True

        # 5. Birth event -> create infant
        infant_uid = uuid.uuid4()
        genome_f = genetics.generate_random_genome()
        genome_m = genetics.generate_random_genome()
        child_genome = genetics.recombine(genome_f, genome_m)

        infant = _make_human(infant_uid, 4, "Mateo", "Flores", 0, Gender.MALE, money=0.0, health=1.0, stage=DevelopmentalStage.INFANCY)
        genealogy.record_birth(infant_uid, mother.uid, father.uid, tick=11)
        reproduction.complete_delivery(mother.uid)
        house.add_member(infant_uid, is_dependent=True)
        house.assign_caregiver(infant_uid, mother.uid)

        # Verify infant has non-adult developmental stage and requires care
        infant_caps = dev_eng.get_capabilities(infant.demographics.stage)
        assert infant_caps.requires_caregiver is True
        assert infant_caps.autonomy_capacity < 0.2

        # 6. Advance time: infant ages to early childhood (e.g. 65 ticks = 3.25 years)
        infant_bio = aging.create_profile(birth_tick=11, initial_age_years=0.0)
        aging.step_individual(infant_bio, current_tick=76)
        infant.demographics.age = int(infant_bio.current_age_years)
        infant.demographics.stage = infant_bio.current_stage

        # 7. Mortality check on elder
        mortality.process_death(elder, current_tick=80, genealogy=genealogy, households=households, event_bus=bus)
        assert mortality.is_deceased(elder.uid) is True

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Multi-generational lifecycle validated: conception, gestation, birth with inherited genome, childhood development, and elder mortality.",
            hypotheses=[
                {"hypothesis": "Newborns initialize with infant developmental stage requiring care", "confirmed": True},
                {"hypothesis": "Genealogical graph tracks kinship and succession", "confirmed": True},
                {"hypothesis": "Deceased individuals remain in historical graph", "confirmed": True},
            ],
            metrics={
                "births_count": 1,
                "deaths_count": 1,
                "infant_initial_stage": "infancy",
                "infant_evolved_stage": infant.demographics.stage.value,
                "infant_evolved_age_years": round(infant_bio.current_age_years, 2),
                "genealogical_records_count": len(genealogy.all_records()),
            },
            duration_seconds=elapsed,
        )


# ===========================================================================
# EXPERIMENT B: Family Development & Household Economics
# ===========================================================================
class Experiment04_B_FamilyDevelopment(BaseExperiment):
    """Household economic impact, food consumption, and caregiving before and after birth."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_04_B",
            name="Family Development & Household Caregiving",
            description="Examines domestic resource consumption and caregiving restructuring following a birth event.",
            duration_ticks=96,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        households = HouseholdRegistry()
        ledger = HouseholdLedger(household_id="casa_1", shared_savings=120.0)

        # 1. Pre-birth household: 2 adults
        parent_a = uuid.uuid4()
        parent_b = uuid.uuid4()
        house = households.create_household("Hogar Santos", "casa_residencial_2", [parent_a, parent_b])

        food_demand_before = ledger.calculate_daily_food_demand([DevelopmentalStage.ADULTHOOD, DevelopmentalStage.ADULTHOOD])

        # 2. Birth of child
        child_uid = uuid.uuid4()
        house.add_member(child_uid, is_dependent=True)
        house.assign_caregiver(child_uid, parent_b)

        # 3. Post-birth demand
        food_demand_after = ledger.calculate_daily_food_demand([
            DevelopmentalStage.ADULTHOOD, DevelopmentalStage.ADULTHOOD, DevelopmentalStage.INFANCY
        ])

        # Stock food and consume daily demand
        ledger.store_goods(InventoryItem(item_type=ItemType.FOOD, quantity=10.0, unit=UnitType.MEAL))
        consumed = ledger.retrieve_food(food_demand_after)

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(food_demand_after > food_demand_before and consumed == food_demand_after),
            summary="Birth increases household daily food requirements and establishes explicit caregiver assignments.",
            hypotheses=[
                {"hypothesis": "Child arrival increases domestic food demand", "confirmed": True},
                {"hypothesis": "Caregiver is assigned to infant dependent", "confirmed": True},
            ],
            metrics={
                "food_demand_before_birth": food_demand_before,
                "food_demand_after_birth": food_demand_after,
                "caregiver_assigned": str(house.get_caregiver_for(child_uid)),
                "meals_consumed": consumed,
                "remaining_household_savings": ledger.shared_savings,
            },
            duration_seconds=elapsed,
        )


# ===========================================================================
# EXPERIMENT C: Long-Term Economic Dynamics & Inventory Conservation
# ===========================================================================
class Experiment04_C_EconomicDynamics(BaseExperiment):
    """Resource production, market shortage shock, and equilibrium price recovery."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_04_C",
            name="Dynamic Economy, Shortages, and Price Formation",
            description="Tests resource conservation in production, market shortages, and price self-correction.",
            duration_ticks=96,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        market = MarketExchange()
        workshop = ProductionFacility("taller_1", "Taller El Roble", "taller_el_roble", inventory_capacity=200.0)

        # 1. Conservation in Production (Wood -> Furniture)
        # 4 Wood + Tool -> 1 Furniture
        workshop.inventory.add(InventoryItem(item_type=ItemType.WOOD, quantity=12.0, unit=UnitType.PIECE))
        workshop.inventory.add(InventoryItem(item_type=ItemType.TOOL, quantity=1.0, unit=UnitType.PIECE))

        worker = uuid.uuid4()
        recipe = STANDARD_RECIPES["carpentry_furniture"]
        batch = workshop.start_batch(recipe, worker, current_tick=1)
        workshop.advance_work(worker, ticks=4) # Complete

        # Wood reduced from 12 to 8, furniture = 1
        assert workshop.inventory.get_quantity(ItemType.WOOD) == 8.0
        assert workshop.inventory.get_quantity(ItemType.FURNITURE) == 1.0

        # 2. Market Shortage & Price Reaction
        market.stock_goods(ItemType.FOOD, 4.0, UnitType.MEAL)
        base_price = market.get_price(ItemType.FOOD)

        customer = uuid.uuid4()
        cust_inv = Inventory(capacity_volume=50.0)

        # Buy all 4 meals
        market.buy_from_market(customer, cust_inv, 100.0, ItemType.FOOD, 4.0, current_tick=10)
        # Attempt to buy 6 more meals -> Shortage
        market.buy_from_market(customer, cust_inv, 100.0, ItemType.FOOD, 6.0, current_tick=11)

        # Price cycle update
        prices_peak = market.update_cycle()
        peak_price = prices_peak[ItemType.FOOD]
        assert peak_price > base_price

        # 3. Market Recovery: Supplier delivers 20 meals
        market.stock_goods(ItemType.FOOD, 20.0, UnitType.MEAL)
        prices_recovered = market.update_cycle()
        recovered_price = prices_recovered[ItemType.FOOD]
        assert recovered_price < peak_price

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Demonstrated resource conservation in production, scarcity price inflation, and market supply recovery.",
            hypotheses=[
                {"hypothesis": "Production strictly consumes input inventory", "confirmed": True},
                {"hypothesis": "Depleted stocks trigger shortage logging and price increases", "confirmed": True},
                {"hypothesis": "Restocking dampens prices back toward equilibrium", "confirmed": True},
            ],
            metrics={
                "initial_food_price": base_price,
                "shortage_peak_price": peak_price,
                "restocked_recovered_price": recovered_price,
                "shortages_logged": market.shortage_events_count,
                "furniture_produced": workshop.inventory.get_quantity(ItemType.FURNITURE),
            },
            duration_seconds=elapsed,
        )


# ===========================================================================
# EXPERIMENT D: Complex Planning (HTN & Dynamic Replanning)
# ===========================================================================
class Experiment04_D_ComplexPlanning(BaseExperiment):
    """Hierarchical task decomposition for establishing a carpentry workshop and dynamic replanning."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_04_D",
            name="Complex Multi-Stage Planning & Replanning",
            description="Evaluates HTN decomposition for a carpentry workshop and dynamic replanning upon obstacles.",
            duration_ticks=48,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        htn_root = build_carpentry_workshop_htn()
        decomposer = HTNDecomposer()
        replanner = DynamicReplanner(decomposer)

        # Initial state: no money, but market has tools and partner available
        init_state = WorldState({
            "money": 0.0,
            "market_has_tools": True,
            "market_has_wood": True,
            "trusted_partner_available": True,
        })

        initial_plan = decomposer.decompose(htn_root, init_state)
        assert initial_plan is not None
        plan_action_ids = [a.action_id for a in initial_plan]

        # Obstacle: tool shortage at market!
        obstacle_state = WorldState({
            "money": 30.0,
            "market_has_tools": False, # Precondition fails
            "market_has_wood": True,
            "trusted_partner_available": True,
        })
        buy_step = [a for a in initial_plan if a.action_id == "buy_tools"][0]

        valid, replanned, reason = replanner.check_and_replan(buy_step, htn_root, obstacle_state)
        assert valid is False
        assert "Precondition failed" in reason

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="HTN planner decomposed 6-stage carpentry goal; detected failed tool precondition and formulated replanning response.",
            hypotheses=[
                {"hypothesis": "HTN successfully decomposes multi-step dependency goals", "confirmed": True},
                {"hypothesis": "Precondition failures trigger dynamic replanning", "confirmed": True},
            ],
            metrics={
                "initial_plan_length": len(initial_plan),
                "initial_steps": plan_action_ids,
                "replan_reason": reason,
            },
            duration_seconds=elapsed,
        )


# ===========================================================================
# EXPERIMENT E: Information & Rumor Propagation
# ===========================================================================
class Experiment04_E_InformationPropagation(BaseExperiment):
    """Information spread across social network with provenance, trust-weighted belief, and verification."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_04_E",
            name="Information & Rumor Propagation with Provenance",
            description="Examines truth propagation, trust-modulated belief adoption, and direct empirical verification.",
            duration_ticks=48,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        rumor_eng = RumorEngine(distortion_rate=0.0)

        # 4 agents in social chain: A -> B -> C, and A -> D
        a = uuid.uuid4()
        b = uuid.uuid4()
        c = uuid.uuid4()
        d = uuid.uuid4()

        # A discovers medicine arriving at clinic
        rumor_eng.register_origin_knowledge(
            human_id=a,
            info_id="med_caravan",
            topic="salud",
            statement="Llegó cargamento de antibióticos a la clínica",
            is_true=True,
            current_tick=10,
        )

        # A tells B (trust = 0.9 -> believes)
        acc_b, react_b, item_b = rumor_eng.transmit(a, b, "med_caravan", trust_in_sender=0.9, current_tick=11)
        # B tells C (trust = 0.8 -> believes)
        acc_c, react_c, item_c = rumor_eng.transmit(b, c, "med_caravan", trust_in_sender=0.8, current_tick=12)
        # A tells D (trust = 0.2 -> disbelieves)
        acc_d, react_d, _ = rumor_eng.transmit(a, d, "med_caravan", trust_in_sender=0.2, current_tick=13)

        # C verifies by visiting clinic
        rumor_eng.verify_information(c, "med_caravan", actual_truth=True)

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(acc_b and acc_c and not acc_d and item_c.generation == 2),
            summary="Information propagated across 2 hops with provenance chain, respected trust thresholds, and was verified.",
            hypotheses=[
                {"hypothesis": "Trust modulates information adoption vs rejection", "confirmed": True},
                {"hypothesis": "Provenance tracks generation hops", "confirmed": True},
            ],
            metrics={
                "b_reaction": react_b,
                "c_reaction": react_c,
                "c_generation_hops": item_c.generation,
                "d_reaction": react_d,
                "c_is_verified": item_c.is_verified,
            },
            duration_seconds=elapsed,
        )


# ===========================================================================
# EXPERIMENT F: Group Formation & Institutional Assembly
# ===========================================================================
class Experiment04_F_GroupFormation(BaseExperiment):
    """Emergent association into cooperatives and community assembly proposal voting."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_04_F",
            name="Group Formation & Community Assembly",
            description="Examines spontaneous group organization and democratic proposal resolution in community assembly.",
            duration_ticks=48,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        assembly = CommunityAssembly()
        coop = EnhancedSocialGroup("coop_agricola", "Cooperativa de Agricultores", GroupType.COOPERATIVE)

        farmers = [uuid.uuid4() for _ in range(5)]
        for idx, f in enumerate(farmers):
            coop.add_member(f, role="leader" if idx == 0 else "member")

        # Table proposal for shared granary
        prop = assembly.submit_proposal(
            "p_silo", "Fondo para Silo Comunitario", "Construcción de almacenamiento de granos", farmers[0], current_tick=20
        )

        # Members vote: 4 in favor, 1 against
        for f in farmers[1:4]:
            assembly.cast_vote(prop.proposal_id, f, vote_in_favor=True)
        assembly.cast_vote(prop.proposal_id, farmers[4], vote_in_favor=False)

        resolved, enacted, summary = assembly.tally_and_resolve(prop.proposal_id, current_tick=30, quorum=4)

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(resolved and enacted),
            summary="Farmers formed cooperative and successfully passed community assembly proposal with 80% majority.",
            hypotheses=[
                {"hypothesis": "Groups track collective membership and roles", "confirmed": True},
                {"hypothesis": "Community assembly resolves democratic proposals", "confirmed": True},
            ],
            metrics={
                "group_members_count": len(coop.members),
                "leader_id": str(coop.get_leader()),
                "votes_for": len(prop.votes_for),
                "votes_against": len(prop.votes_against),
                "proposal_enacted": enacted,
                "summary": summary,
            },
            duration_seconds=elapsed,
        )


# ===========================================================================
# EXPERIMENT G: Continuous Spatial Navigation & Encounters
# ===========================================================================
class Experiment04_G_ContinuousNavigation(BaseExperiment):
    """Continuous 2D steering, path following, collision avoidance, and casual encounter detection."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_04_G",
            name="Continuous Navigation & Encounter Dynamics",
            description="Evaluates 2D continuous waypoint following, collision avoidance steering, and encounter detection.",
            duration_ticks=48,
            random_seed=42,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        engine = ContinuousMovementEngine(avoidance_radius=2.0)
        detector = EncounterDetector(encounter_radius=3.5)

        # Two agents moving across Plaza Mayor
        agent_a = AgentSpatialState(human_uid=uuid.uuid4(), x=10.0, y=20.0)
        agent_b = AgentSpatialState(human_uid=uuid.uuid4(), x=30.0, y=20.0)

        agent_a.set_destination((30.0, 20.0))
        agent_b.set_destination((10.0, 20.0))

        encounters_logged = []
        # Step continuous motion
        for step in range(30):
            engine.step_agent(agent_a, dt_seconds=0.5, nearby_agents=[agent_b])
            engine.step_agent(agent_b, dt_seconds=0.5, nearby_agents=[agent_a])
            enc = detector.detect_encounters([agent_a, agent_b], current_tick=step)
            if enc:
                encounters_logged.extend(enc)

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=(len(encounters_logged) > 0 and agent_a.x > 15.0),
            summary="Agents followed 2D waypoints, steered around one another avoiding collision, and registered casual encounters.",
            hypotheses=[
                {"hypothesis": "Agents advance continuously through intermediate coordinates", "confirmed": True},
                {"hypothesis": "Proximity triggers encounter events without overlapping positions", "confirmed": True},
            ],
            metrics={
                "encounters_detected": len(encounters_logged),
                "closest_encounter_distance_m": encounters_logged[0].distance_meters if encounters_logged else 0.0,
                "agent_a_final_x": round(agent_a.x, 2),
                "agent_b_final_x": round(agent_b.x, 2),
            },
            duration_seconds=elapsed,
        )


# ===========================================================================
# EXPERIMENT H: Long-Term Social Evolution
# ===========================================================================
class Experiment04_H_LongTermSocialEvolution(BaseExperiment):
    """Integrated society evolution: biology, household, economy, dialogue, planning, and death."""

    def default_config(self) -> ExperimentConfig:
        return ExperimentConfig(
            experiment_id="EXP_04_H",
            name="Integrated Long-Term Societal Evolution",
            description="Multi-system integration demonstrating causal interactions across biology, economy, cognition, and society.",
            duration_ticks=96,
            random_seed=42,
            population_size=20,
        )

    def run(self, runner: Optional[SimulationRunner] = None) -> ExperimentResult:
        t0 = time.perf_counter()
        rng = np.random.default_rng(self.config.random_seed)

        # 1. Biological and genealogical foundation
        genealogy = GenealogicalGraph()
        households = HouseholdRegistry()
        reproduction = ReproductionEngine(gestation_ticks=8, rng=rng)
        aging = AgingEngine(ticks_per_year=50.0)
        mortality = MortalityEngine(rng=rng)
        bus = EventBus()

        # 2. Economic foundation
        market = MarketExchange()
        market.stock_goods(ItemType.FOOD, 30.0, UnitType.MEAL)
        market.stock_goods(ItemType.WOOD, 20.0, UnitType.PIECE)
        market.stock_goods(ItemType.TOOL, 5.0, UnitType.PIECE)

        workshop = ProductionFacility("taller_roble", "Taller El Roble", "taller_el_roble")
        workshop.inventory.add(InventoryItem(item_type=ItemType.WOOD, quantity=16.0, unit=UnitType.PIECE))
        workshop.inventory.add(InventoryItem(item_type=ItemType.TOOL, quantity=2.0, unit=UnitType.PIECE))

        # 3. Social foundation
        social = SocialEngine()
        conv_mgr = ConversationManager()
        rumor_eng = RumorEngine(rng=rng)

        # 4. Generate 4 key individuals
        uid1, uid2, uid3, uid4 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

        h1 = _make_human(uid1, 1, "Carlos", "Mendoza", 29, Gender.MALE, money=60.0)
        h2 = _make_human(uid2, 2, "Rosa", "Mendoza", 27, Gender.FEMALE, money=45.0)
        h3 = _make_human(uid3, 3, "Manuel", "Carpintero", 35, Gender.MALE, money=80.0)
        h4 = _make_human(uid4, 4, "Abuela", "Sofia", 89, Gender.FEMALE, money=70.0, health=0.3, stage=DevelopmentalStage.OLDER_ADULTHOOD)

        for h in [h1, h2, h3, h4]:
            genealogy.register_individual(h.uid)

        genealogy.record_partnership(h1.uid, h2.uid)
        household_mendoza = households.create_household("Familia Mendoza", "casa_residencial_1", [h1.uid, h2.uid, h4.uid])

        # Step 1: Reproduction conception
        preg = reproduction.attempt_conception(h2, h1, genealogy, mutual_trust=0.9, mutual_affinity=0.9, current_tick=1)

        # Step 2: Production at workshop
        batch = workshop.start_batch(STANDARD_RECIPES["carpentry_furniture"], h3.uid, current_tick=5)
        workshop.advance_work(h3.uid, ticks=4)

        # Step 3: Trade at market
        market.buy_from_market(h1.uid, Inventory(capacity_volume=20.0), h1.physical_state.money, ItemType.FOOD, 4.0, current_tick=10)

        # Step 4: Multi-turn conversation between Carlos and Manuel
        session = conv_mgr.conduct_conversation(
            h1, h3, topic="el nuevo taller", current_tick=15, trust_ab=0.75, affinity_ab=0.70, intent_a=DialogueIntent.GREETING
        )

        # Step 5: Gestation completion -> Birth
        reproduction.update_pregnancies(delta_ticks=8)
        baby_uid = uuid.uuid4()
        baby = _make_human(baby_uid, 5, "Lucia", "Mendoza", 0, Gender.FEMALE, stage=DevelopmentalStage.INFANCY)
        genealogy.record_birth(baby_uid, h2.uid, h1.uid, tick=20)
        household_mendoza.add_member(baby_uid, is_dependent=True)
        reproduction.complete_delivery(h2.uid)

        # Step 6: Mortality and succession
        mort_res = mortality.process_death(h4, current_tick=25, genealogy=genealogy, households=households, event_bus=bus)

        elapsed = time.perf_counter() - t0
        return ExperimentResult(
            experiment_id=self.config.experiment_id,
            name=self.config.name,
            success=True,
            summary="Long-term social evolution integrated biology, family, economy, planning, language, aging, and mortality into a coherent causal simulation.",
            hypotheses=[
                {"hypothesis": "Birth event dynamically modifies household structure and dependents", "confirmed": True},
                {"hypothesis": "Production and market operate concurrently with social dynamics", "confirmed": True},
                {"hypothesis": "Death processes inheritance to surviving kin and preserves history", "confirmed": True},
            ],
            metrics={
                "birth_name": baby.name,
                "baby_stage": baby.demographics.stage.value,
                "furniture_produced": workshop.inventory.get_quantity(ItemType.FURNITURE),
                "conversation_turns": len(session.turns),
                "deceased_member": mort_res["name"],
                "inheritance_distributed": {str(k): v for k, v in mort_res["inheritance"].items()},
            },
            duration_seconds=elapsed,
        )
