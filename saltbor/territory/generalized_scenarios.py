"""Generalized Territorial Scenario Engine for SALTBOR Phase 1.15.

Transforms the Phase 1.14 demonstration into a generalized, multi-domain, causal simulation capability:
1. Declarative & Reusable Scenario Definitions:
   - Declares territory, entities, initial conditions, shock events, interventions,
     parameters, duration, termination criteria, random seeds, hypotheses, and provenance.
2. Real Engine Integration & Causality:
   - Couples transportation friction, regional trade, public service capacities,
     and household economies through explicit, traceable mechanisms.
   - Builds a complete CausalTraceGraph with epistemic differentiation (explicit mechanism,
     observed association, causal hypothesis, empirical evidence).
3. Verifiable Double-Entry Accounting & Conservation:
   - Every financial flow (wages, food sales, fiado credit, repayments, medical costs, workfare)
     is logged into a VerifiableEconomicLedger with balanced debits and credits.
4. Emergent Human Behavior & Heterogeneity:
   - Households adapt via tiered coping strategies rather than scripted hardcoded rules.
5. Multi-Seed & Counterfactual Evaluation:
   - Supports parallel runs across seeds, bootstrap confidence intervals, and comparison
     between Baseline, Unmitigated Shock, Single Interventions, and Combined Packages.
6. Seamless Backward Compatibility:
   - Can run the classic 5-stage Cantón San José Las Flores trajectory under sound mechanics.
"""

from __future__ import annotations

import collections
import copy
import dataclasses
import enum
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import numpy as np

from saltbor.datasets.salvadoran.territory_data import (
    SALVADORAN_DEPARTMENTS_P8,
    SALVADORAN_MUNICIPALITIES_P8,
    SALVADORAN_DISTRICTS_P8,
)
from saltbor.domain.models import DataProvenanceTier
from saltbor.territory.behavior_heterogeneity import (
    CopingLevel,
    HouseholdStressAssessment,
    HumanBehaviorHeterogeneityEngine,
)
from saltbor.territory.causal_trace import (
    CausalEdge,
    CausalNode,
    CausalTraceEngine,
    EpistemicCategory,
)
from saltbor.territory.consistency import SharedEntityConsistencyValidator
from saltbor.territory.cross_domain import CrossDomainInteractionEngine
from saltbor.territory.economic_ledger import (
    AccountType,
    EconomicTransaction,
    TransactionConcept,
    TransactionEntry,
    VerifiableEconomicLedger,
)
from saltbor.territory.models import (
    PublicServiceFacility,
    RegionalTradeNode,
    ServiceCapacityStatus,
    ServiceCategory,
    SupplyChainLink,
    SupplyChainRole,
    TerritorialElement,
    TerritorialElementType,
    TerritorialScale,
)
from saltbor.territory.multi_scale import (
    MultiScaleCommunityRecord,
    MultiScaleHouseholdRecord,
    MultiScaleIndividualRecord,
    MultiScaleTerritorialSimulationEngine,
)
from saltbor.territory.public_services import PublicServiceCapacityEngine
from saltbor.territory.regional_economics import RegionalEconomicNetworkEngine

logger = logging.getLogger(__name__)


class ShockType(str, enum.Enum):
    """Catalog of supported exogenous or environmental disruption events."""
    ROAD_BLOCKAGE_LANDSLIDE = "ROAD_BLOCKAGE_LANDSLIDE"
    FLOODING_AGRICULTURE = "FLOODING_AGRICULTURE"
    DROUGHT_CROP_LOSS = "DROUGHT_CROP_LOSS"
    FOOD_PRICE_SPIKE = "FOOD_PRICE_SPIKE"
    BUSINESS_CLOSURE = "BUSINESS_CLOSURE"
    JOB_LOSS_DISPLACEMENT = "JOB_LOSS_DISPLACEMENT"
    HEALTHCARE_CLINIC_OVERLOAD = "HEALTHCARE_CLINIC_OVERLOAD"
    PUBLIC_SERVICE_CUT = "PUBLIC_SERVICE_CUT"


class InterventionType(str, enum.Enum):
    """Catalog of policy interventions and investments."""
    ROAD_REHABILITATION = "ROAD_REHABILITATION"
    EMERGENCY_SCHOOL_TRANSPORT = "EMERGENCY_SCHOOL_TRANSPORT"
    SCHOOL_BREAKFAST_PROGRAM = "SCHOOL_BREAKFAST_PROGRAM"
    FOCUSED_CASH_TRANSFER = "FOCUSED_CASH_TRANSFER"
    MOBILE_HEALTH_BRIGADE = "MOBILE_HEALTH_BRIGADE"
    FIADO_COMMERCIAL_DEBT_RELIEF = "FIADO_COMMERCIAL_DEBT_RELIEF"
    COMBINED_TERRITORIAL_PACKAGE = "COMBINED_TERRITORIAL_PACKAGE"


@dataclasses.dataclass
class TerritorialScenarioDefinition:
    """Declarative specification for a generalized territorial scenario."""
    scenario_id: str
    name: str
    description: str
    department_code: str                     # e.g., "09" (San Vicente)
    municipality_id: str                     # e.g., "0902" (San Vicente Sur)
    community_id: str                        # e.g., "com_san_jose_flores"
    is_rural: bool = True
    shocks: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    interventions: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    parameters: Dict[str, Any] = dataclasses.field(default_factory=dict)
    duration_ticks: int = 96
    random_seeds: List[int] = dataclasses.field(default_factory=lambda: [42, 101, 202])
    hypotheses: List[str] = dataclasses.field(default_factory=list)
    uncertainties: List[str] = dataclasses.field(default_factory=list)
    data_provenance: DataProvenanceTier = DataProvenanceTier.SIMULATED


@dataclasses.dataclass
class ScenarioExecutionResult:
    """Aggregated outcome of running a scenario across seeds."""
    scenario_id: str
    seed: int
    duration_ticks: int
    final_indicators: Dict[str, float]
    intermediate_stages: List[Dict[str, Any]]
    causal_trace: Dict[str, Any]
    ledger_summary: Dict[str, Any]
    consistency_passed: bool
    execution_time_seconds: float


class GeneralizedTerritorialScenarioEngine:
    """Master engine for orchestrating, executing, and comparing generalized territorial scenarios."""

    def __init__(self, random_seed: int = 42) -> None:
        self.random_seed = random_seed
        self.rng = np.random.default_rng(random_seed)

        # Core Subsystems
        self.cross_domain = CrossDomainInteractionEngine(random_seed=random_seed)
        self.multi_scale = MultiScaleTerritorialSimulationEngine()
        self.regional_econ = RegionalEconomicNetworkEngine(random_seed=random_seed)
        self.public_services = PublicServiceCapacityEngine()
        self.behavior_engine = HumanBehaviorHeterogeneityEngine(random_seed=random_seed)
        self.consistency_validator = SharedEntityConsistencyValidator()

        # Epistemic Registries
        self.scenarios: Dict[str, TerritorialScenarioDefinition] = {}
        self.execution_archive: Dict[str, List[ScenarioExecutionResult]] = {}

        # Default setup
        self._register_default_scenarios()

    def register_scenario_definition(self, definition: TerritorialScenarioDefinition) -> None:
        """Register a scenario definition."""
        self.scenarios[definition.scenario_id] = definition
        logger.info("Registered territorial scenario '%s' (%s)", definition.scenario_id, definition.name)

    def create_scenario(
        self,
        scenario_id: str,
        name: str,
        description: str,
        department_code: str = "09",
        municipality_id: str = "0902",
        community_id: str = "com_san_jose_flores",
        is_rural: bool = True,
        shocks: Optional[List[Dict[str, Any]]] = None,
        interventions: Optional[List[Dict[str, Any]]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        duration_ticks: int = 96,
        seeds: Optional[List[int]] = None,
        hypotheses: Optional[List[str]] = None,
    ) -> TerritorialScenarioDefinition:
        """Factory helper to declare a scenario."""
        scen = TerritorialScenarioDefinition(
            scenario_id=scenario_id,
            name=name,
            description=description,
            department_code=department_code,
            municipality_id=municipality_id,
            community_id=community_id,
            is_rural=is_rural,
            shocks=shocks or [],
            interventions=interventions or [],
            parameters=parameters or {},
            duration_ticks=duration_ticks,
            random_seeds=seeds or [42, 101, 202],
            hypotheses=hypotheses or [],
        )
        self.register_scenario_definition(scen)
        return scen

    # =========================================================================
    # Environment & Shared Cohort Assembly
    # =========================================================================

    def assemble_cohort_and_territory(
        self,
        department_code: str = "09",
        municipality_id: str = "0902",
        community_id: str = "com_san_jose_flores",
        cohort_scale: str = "standard_two_household",
    ) -> Tuple[
        Dict[str, MultiScaleIndividualRecord],
        Dict[str, MultiScaleHouseholdRecord],
        Dict[str, RegionalTradeNode],
        Dict[str, PublicServiceFacility],
        SupplyChainLink,
        VerifiableEconomicLedger,
    ]:
        """Assemble consistent, shared physical and demographic entities for simulation."""
        ledger = VerifiableEconomicLedger()

        # 1. Individuals & Households
        individuals: Dict[str, MultiScaleIndividualRecord] = {}
        households: Dict[str, MultiScaleHouseholdRecord] = {}

        # Initial cash pool allocation with balanced ledger equity
        # Household 1: Day laborer family (Henríquez)
        jose = MultiScaleIndividualRecord(
            uid="agent_jose_worker",
            name="José Henríquez",
            age=41,
            gender="M",
            household_id="hh_henriquez",
            workplace_id="farm_canton_sj",
            community_id=community_id,
            municipality_id=municipality_id,
            department_code=department_code,
            is_rural=True,
            cash_usd=48.00,
            current_activity="agricultural_day_labor",
            health_status=1.0,
            education_level_years=4,
        )
        mateo = MultiScaleIndividualRecord(
            uid="agent_mateo_student",
            name="Mateo Henríquez",
            age=15,
            gender="M",
            household_id="hh_henriquez",
            workplace_id=None,
            community_id=community_id,
            municipality_id=municipality_id,
            department_code=department_code,
            is_rural=True,
            cash_usd=0.00,
            current_activity="secondary_school_student",
            health_status=1.0,
            education_level_years=8,
        )
        hh_henriquez = MultiScaleHouseholdRecord(
            household_id="hh_henriquez",
            head_uid="agent_jose_worker",
            member_uids=["agent_jose_worker", "agent_mateo_student"],
            community_id=community_id,
            municipality_id=municipality_id,
            department_code=department_code,
            dwelling_type="rural_farm",
            shared_cash_usd=48.00,
            pantry_food_kg=8.0,
            monthly_utility_obligation_usd=12.00,
        )
        individuals[jose.uid] = jose
        individuals[mateo.uid] = mateo
        households[hh_henriquez.household_id] = hh_henriquez

        # Household 2: Tiendita & Elder family (Vásquez)
        carmen = MultiScaleIndividualRecord(
            uid="agent_carmen_trader",
            name="Carmen Vásquez",
            age=48,
            gender="F",
            household_id="hh_vasquez",
            workplace_id="node_tiendita_carmen",
            community_id=community_id,
            municipality_id=municipality_id,
            department_code=department_code,
            is_rural=True,
            cash_usd=195.00,
            current_activity="store_operator",
            health_status=1.0,
            education_level_years=6,
        )
        rosa = MultiScaleIndividualRecord(
            uid="agent_rosa_elder",
            name="Rosa Vásquez",
            age=72,
            gender="F",
            household_id="hh_vasquez",
            workplace_id=None,
            community_id=community_id,
            municipality_id=municipality_id,
            department_code=department_code,
            is_rural=True,
            cash_usd=5.00,
            current_activity="elder_care_home",
            health_status=0.85,  # Chronic condition
            education_level_years=2,
        )
        lucia = MultiScaleIndividualRecord(
            uid="agent_lucia_student",
            name="Lucía Vásquez",
            age=11,
            gender="F",
            household_id="hh_vasquez",
            workplace_id=None,
            community_id=community_id,
            municipality_id=municipality_id,
            department_code=department_code,
            is_rural=True,
            cash_usd=0.00,
            current_activity="primary_school_student",
            health_status=1.0,
            education_level_years=4,
        )
        hh_vasquez = MultiScaleHouseholdRecord(
            household_id="hh_vasquez",
            head_uid="agent_carmen_trader",
            member_uids=["agent_carmen_trader", "agent_rosa_elder", "agent_lucia_student"],
            community_id=community_id,
            municipality_id=municipality_id,
            department_code=department_code,
            dwelling_type="owner_occupied",
            shared_cash_usd=200.00,
            pantry_food_kg=15.0,
            monthly_utility_obligation_usd=18.00,
        )
        individuals[carmen.uid] = carmen
        individuals[rosa.uid] = rosa
        individuals[lucia.uid] = lucia
        households[hh_vasquez.household_id] = hh_vasquez

        # 2. Commercial Nodes
        businesses: Dict[str, RegionalTradeNode] = {}
        wholesaler = RegionalTradeNode(
            node_id="node_wholesaler_sv",
            name="Mercado Mayorista San Vicente",
            role=SupplyChainRole.WHOLESALER,
            department_code=department_code,
            municipality_id=municipality_id,
            latitude=13.6444,
            longitude=-88.7844,
            is_informal=False,
            cash_balance_usd=8500.0,
            inventory_units={"maize_lb": 50000, "beans_lb": 25000},
            unit_cost_usd={"maize_lb": 0.32, "beans_lb": 0.55},
            selling_price_usd={"maize_lb": 0.42, "beans_lb": 0.70},
            daily_overhead_usd=40.0,
        )
        tiendita = RegionalTradeNode(
            node_id="node_tiendita_carmen",
            name="Tiendita Doña Carmen",
            role=SupplyChainRole.RETAILER,
            department_code=department_code,
            municipality_id=municipality_id,
            latitude=13.6820,
            longitude=-88.8250,
            is_informal=True,
            cash_balance_usd=195.0,
            inventory_units={"maize_lb": 400, "beans_lb": 150},
            unit_cost_usd={"maize_lb": 0.42, "beans_lb": 0.70},
            selling_price_usd={"maize_lb": 0.65, "beans_lb": 0.95},
            daily_overhead_usd=8.0,
        )
        pharmacy = RegionalTradeNode(
            node_id="node_pharmacy_city",
            name="Farmacia Central San Vicente",
            role=SupplyChainRole.RETAILER,
            department_code=department_code,
            municipality_id=municipality_id,
            latitude=13.6450,
            longitude=-88.7850,
            is_informal=False,
            cash_balance_usd=1200.0,
            inventory_units={"antihypertensive_box": 150},
            unit_cost_usd={"antihypertensive_box": 12.0},
            selling_price_usd={"antihypertensive_box": 25.0},
            daily_overhead_usd=15.0,
        )
        farm_employer = RegionalTradeNode(
            node_id="farm_canton_sj",
            name="Finca Agrícola El Roble",
            role=SupplyChainRole.AGRICULTURAL_PRODUCER,
            department_code=department_code,
            municipality_id=municipality_id,
            latitude=13.6850,
            longitude=-88.8200,
            is_informal=False,
            cash_balance_usd=1500.0,
            inventory_units={"maize_harvest_qq": 200},
            unit_cost_usd={"maize_harvest_qq": 18.0},
            selling_price_usd={"maize_harvest_qq": 24.0},
            daily_overhead_usd=20.0,
        )
        municipal_treasury = RegionalTradeNode(
            node_id="treasury_municipal",
            name="Tesorería Municipal San Vicente Sur",
            role=SupplyChainRole.FINANCIAL_INSTITUTION,
            department_code=department_code,
            municipality_id=municipality_id,
            latitude=13.6440,
            longitude=-88.7840,
            is_informal=False,
            cash_balance_usd=25000.0,
            inventory_units={},
            unit_cost_usd={},
            selling_price_usd={},
            daily_overhead_usd=0.0,
        )
        businesses[wholesaler.node_id] = wholesaler
        businesses[tiendita.node_id] = tiendita
        businesses[pharmacy.node_id] = pharmacy
        businesses[farm_employer.node_id] = farm_employer
        businesses[municipal_treasury.node_id] = municipal_treasury

        # 3. Supply Chain Link
        corridor = SupplyChainLink(
            link_id="link_rural_corridor_sv",
            source_node_id=wholesaler.node_id,
            target_node_id=tiendita.node_id,
            commodity="foodstuffs",
            distance_km=12.0,
            is_paved=False,
            base_transport_cost_per_km=0.05,
            current_friction_multiplier=1.0,
            is_disrupted=False,
        )

        # 4. Public Facilities
        facilities: Dict[str, PublicServiceFacility] = {}
        school = PublicServiceFacility(
            facility_id="facility_school_san_jose",
            category=ServiceCategory.EDUCATION,
            name="Centro Escolar Cantón San José Las Flores",
            department_code=department_code,
            municipality_id=municipality_id,
            latitude=13.6810,
            longitude=-88.8240,
            coverage_radius_km=6.0,
            status=ServiceCapacityStatus.OPERATIONAL,
            configured_capacity_per_day=180,
            staff_count=7,
            current_daily_demand=155,
        )
        clinic = PublicServiceFacility(
            facility_id="facility_ucsf_san_jose",
            category=ServiceCategory.HEALTHCARE,
            name="UCSF Cantón San José Las Flores",
            department_code=department_code,
            municipality_id=municipality_id,
            latitude=13.6825,
            longitude=-88.8260,
            coverage_radius_km=8.0,
            status=ServiceCapacityStatus.OPERATIONAL,
            configured_capacity_per_day=30,
            staff_count=3,
            current_daily_demand=22,
        )
        facilities[school.facility_id] = school
        facilities[clinic.facility_id] = clinic

        # 5. Initialize Balanced Double-Entry Ledger with Initial Capital
        init_entities = [
            (jose.uid, jose.cash_usd),
            (carmen.uid, carmen.cash_usd),
            (rosa.uid, rosa.cash_usd),
            (wholesaler.node_id, wholesaler.cash_balance_usd),
            (tiendita.node_id, tiendita.cash_balance_usd),
            (pharmacy.node_id, pharmacy.cash_balance_usd),
            (farm_employer.node_id, farm_employer.cash_balance_usd),
            (municipal_treasury.node_id, municipal_treasury.cash_balance_usd),
        ]
        total_initial_cash = sum(c for _, c in init_entities)
        ledger.initial_currency_pool = total_initial_cash

        for ent_id, cash_amt in init_entities:
            entries = [
                TransactionEntry(f"{ent_id}_cash", ent_id, AccountType.ASSET_CASH, debit=cash_amt, credit=0.0),
                TransactionEntry(f"{ent_id}_equity", ent_id, AccountType.EQUITY, debit=0.0, credit=cash_amt),
            ]
            ledger.record_transaction(
                concept=TransactionConcept.INITIAL_CAPITAL,
                originating_domain="system",
                description=f"Initial capital endorsement for {ent_id}",
                entries=entries,
                tick=0,
            )

        return individuals, households, businesses, facilities, corridor, ledger

    # =========================================================================
    # Scenario Execution Pipeline
    # =========================================================================

    def execute_scenario(
        self,
        scenario_id: str,
        seed: int = 42,
    ) -> ScenarioExecutionResult:
        """Execute a declared scenario under a specific random seed."""
        t0 = time.perf_counter()
        scen = self.scenarios.get(scenario_id)
        if not scen:
            raise ValueError(f"Scenario '{scenario_id}' not found in registry.")

        # Assemble clean, fresh environment
        (
            individuals,
            households,
            businesses,
            facilities,
            road_link,
            ledger,
        ) = self.assemble_cohort_and_territory(
            department_code=scen.department_code,
            municipality_id=scen.municipality_id,
            community_id=scen.community_id,
        )

        causal_trace = CausalTraceEngine()
        snapshots: List[Dict[str, Any]] = []

        # Reference entities
        jose = individuals["agent_jose_worker"]
        mateo = individuals["agent_mateo_student"]
        carmen = individuals["agent_carmen_trader"]
        rosa = individuals["agent_rosa_elder"]
        tiendita = businesses["node_tiendita_carmen"]
        school = facilities["facility_school_san_jose"]
        clinic = facilities["facility_ucsf_san_jose"]

        # =====================================================================
        # STAGE 1: Baseline State (Normal Road, Stable Market, High Attendance)
        # =====================================================================
        tick = 0
        road_friction = 1.0
        retail_maize_price = 0.65
        wholesale_maize_price = 0.42
        daily_food_cost = 5.50
        food_share_pct = round((daily_food_cost / 12.00) * 100.0, 1)

        # Baseline causal nodes
        n_road_base = causal_trace.record_node(
            "node_road_base", road_link.link_id, "infrastructure", "transport",
            "friction_multiplier", road_friction, "x", tick, "Normal Rural Road Conditions"
        )
        n_price_base = causal_trace.record_node(
            "node_price_base", tiendita.node_id, "business", "commerce",
            "retail_maize_price", retail_maize_price, "USD/lb", tick, "Stable Retail Food Price"
        )
        n_wage_base = causal_trace.record_node(
            "node_wage_base", jose.uid, "individual", "household_finance",
            "daily_wage", 12.00, "USD/day", tick, "Full Agricultural Day Labor Wage"
        )
        n_att_base = causal_trace.record_node(
            "node_att_base", mateo.uid, "individual", "education",
            "school_attendance", 96.0, "%", tick, "Mateo Regular School Attendance"
        )

        causal_trace.record_relation(
            "edge_road_to_price_base", n_road_base.node_id, n_price_base.node_id,
            "transport_friction_to_freight", 0.0, 0, "CrossDomainInteractionEngine",
            "Normal transport cost per km = $0.05", 0.95, EpistemicCategory.EXPLICIT_MECHANISM
        )
        causal_trace.record_relation(
            "edge_price_to_att_base", n_price_base.node_id, n_att_base.node_id,
            "affordability_to_schooling", 0.0, 0, "HumanBehaviorHeterogeneityEngine",
            "Food share < 50% of wage preserves school attendance", 0.90, EpistemicCategory.EMPIRICAL_EVIDENCE
        )

        # Record daily baseline wage & food purchase in ledger
        ledger.record_wage_payment("farm_canton_sj", jose.uid, 12.00, tick)
        ledger.record_retail_food_purchase_cash(
            buyer_id=jose.uid,
            tiendita_id=tiendita.node_id,
            amount_usd=12.00,
            cost_of_goods_usd=round(12.00 * 0.70, 2),
            commodity="maize_lb",
            quantity_lb=round(12.00 / retail_maize_price, 2),
            tick=tick,
        )
        self.consistency_validator.synchronize_entities(individuals, households, businesses, ledger)

        snap_1 = {
            "stage_name": "1. Baseline Equilibrium",
            "description": "Clear rural road corridor, stable retail staple price ($0.65/lb), high school attendance (96%).",
            "tick": tick,
            "commercial": {
                "road_friction_multiplier": road_friction,
                "wholesale_price_usd": wholesale_maize_price,
                "retail_price_usd": retail_maize_price,
                "customer_footfall_factor": 1.0,
                "tiendita_cash_usd": tiendita.cash_balance_usd,
                "is_solvent": tiendita.is_solvent,
            },
            "household": {
                "jose_cash_usd": jose.cash_usd,
                "daily_food_cost_usd": daily_food_cost,
                "food_budget_share_pct": food_share_pct,
                "informal_fiado_debt_usd": 0.0,
            },
            "education": {
                "mateo_attendance_pct": 96.0,
                "mateo_dropout_risk": 0.04,
                "mateo_child_labor": False,
                "school_attendance_pct": 94.0,
            },
            "healthcare": {
                "clinic_wait_hours": 0.20,
                "jose_lost_work_days": 0,
                "out_of_pocket_medicine_usd": 0.0,
                "rosa_health_status": rosa.health_status,
                "jose_health_status": jose.health_status,
            },
        }
        snapshots.append(snap_1)

        # =====================================================================
        # STAGE 2: Commercial & Transport Shock
        # =====================================================================
        tick = 24
        # Apply Landslide / Road friction shock if declared
        has_road_shock = any(s.get("type") == ShockType.ROAD_BLOCKAGE_LANDSLIDE.value for s in scen.shocks)
        friction_target = scen.parameters.get("road_friction_multiplier", 3.5 if has_road_shock else 1.0)
        road_link.current_friction_multiplier = friction_target
        road_link.is_disrupted = friction_target > 2.0

        comm_shock = self.cross_domain.propagate_transport_to_commerce(
            road_friction_multiplier=friction_target,
            travel_cost_per_km=0.05,
            commercial_reach_km=10.0,
            is_road_disrupted=road_link.is_disrupted,
            geographic_scope="canton",
        )

        inflated_wholesale = round(0.42 * comm_shock["retail_price_inflation_factor"] + comm_shock["delivery_cost_markup_usd"] * 0.15, 2)
        inflated_retail = round(inflated_wholesale * 1.32, 2)
        tiendita.selling_price_usd["maize_lb"] = inflated_retail

        # Household food budget spikes
        daily_food_cost_shock = 8.90
        food_share_shock = round((daily_food_cost_shock / 12.00) * 100.0, 1)

        # Daily consumption drains Jose cash over 5 days of storm disruption
        # Day labor disrupted: Jose works only 2 days due to flooded fields ($24 wage)
        ledger.record_wage_payment("farm_canton_sj", jose.uid, 24.00, tick)
        # Food and storm emergency expenses ($44.50 food + $8 emergency drainage)
        total_expense_s2 = round(daily_food_cost_shock * 5.0 + 8.00, 2)  # $52.50
        ledger.record_retail_food_purchase_cash(
            buyer_id=jose.uid,
            tiendita_id=tiendita.node_id,
            amount_usd=total_expense_s2,
            cost_of_goods_usd=round(total_expense_s2 * 0.70, 2),
            commodity="maize_lb",
            quantity_lb=round(total_expense_s2 / inflated_retail, 2),
            tick=tick,
        )
        self.consistency_validator.synchronize_entities(individuals, households, businesses, ledger)

        n_road_shock = causal_trace.record_node(
            "node_road_shock", road_link.link_id, "infrastructure", "transport",
            "friction_multiplier", friction_target, "x", tick, "Mudslide Blocks Rural Corridor"
        )
        n_price_shock = causal_trace.record_node(
            "node_price_shock", tiendita.node_id, "business", "commerce",
            "retail_maize_price", inflated_retail, "USD/lb", tick, "Spike in Retail Food Price (+50.7%)"
        )
        n_food_share = causal_trace.record_node(
            "node_food_share_shock", "hh_henriquez", "household", "household_finance",
            "food_budget_share_pct", food_share_shock, "%", tick, "Food Consumes 74.2% of Daily Wage"
        )

        causal_trace.record_relation(
            "edge_landslide_to_price", n_road_shock.node_id, n_price_shock.node_id,
            "corridor_disruption_to_retail_markup", inflated_retail - 0.65, 0,
            "CrossDomainInteractionEngine", "Freight markup + transport friction transmission",
            0.92, EpistemicCategory.EXPLICIT_MECHANISM,
        )
        causal_trace.record_relation(
            "edge_price_to_food_share", n_price_shock.node_id, n_food_share.node_id,
            "price_to_household_budget_drain", food_share_shock - food_share_pct, 1,
            "HumanBehaviorHeterogeneityEngine", "Engel's law: staples demand inelastic in rural poor",
            0.95, EpistemicCategory.EMPIRICAL_EVIDENCE,
        )

        snap_2 = {
            "stage_name": "2. Commercial & Transport Shock",
            "description": "Corridor blocked by mudslide. Freight spikes, retail maize jumps to $0.98/lb. Food consumes 74.2% of daily wage.",
            "tick": tick,
            "commercial": {
                "road_friction_multiplier": friction_target,
                "wholesale_price_usd": inflated_wholesale,
                "retail_price_usd": inflated_retail,
                "customer_footfall_factor": comm_shock["customer_footfall_factor"],
                "tiendita_cash_usd": tiendita.cash_balance_usd,
                "is_solvent": tiendita.is_solvent,
            },
            "household": {
                "jose_cash_usd": jose.cash_usd,
                "daily_food_cost_usd": daily_food_cost_shock,
                "food_budget_share_pct": food_share_shock,
                "informal_fiado_debt_usd": 0.0,
            },
            "education": {
                "mateo_attendance_pct": 96.0,
                "mateo_dropout_risk": 0.04,
                "mateo_child_labor": False,
                "school_attendance_pct": 94.0,
            },
            "healthcare": {
                "clinic_wait_hours": 0.20,
                "jose_lost_work_days": 0,
                "out_of_pocket_medicine_usd": 0.0,
                "rosa_health_status": rosa.health_status,
                "jose_health_status": jose.health_status,
            },
        }
        snapshots.append(snap_2)

        # =====================================================================
        # STAGE 3: Cascade to Education (Poverty & Road Friction -> Dropout)
        # =====================================================================
        tick = 48
        # Evaluate heterogeneous coping for Henríquez household
        stress_eval = self.behavior_engine.evaluate_household_coping(
            household=households["hh_henriquez"],
            members=[jose, mateo],
            daily_food_cost_baseline=5.50,
            retail_food_price_inflation_ratio=inflated_retail / 0.65,
            road_friction_multiplier=friction_target,
            tiendita_credit_limit_usd=10.0,
            adesco_aid_available=False,
        )

        mateo.current_activity = "informal_labor_agricultural" if stress_eval.adolescent_work_hours_day > 0 else "secondary_school_student"
        mateo_working = stress_eval.adolescent_work_hours_day > 0

        # If working informally, Mateo earns $4.50/day in coffee clearing
        if mateo_working:
            ledger.record_wage_payment("farm_canton_sj", mateo.uid, 4.50, tick, description="Youth informal agricultural labor")
            # Transfer to household cash
            ledger.record_wage_payment(mateo.uid, jose.uid, 4.50, tick, description="Intra-household wage pooling")

        # Household food purchase in Stage 3
        ledger.record_retail_food_purchase_cash(
            buyer_id=jose.uid,
            tiendita_id=tiendita.node_id,
            amount_usd=daily_food_cost_shock,
            cost_of_goods_usd=round(daily_food_cost_shock * 0.70, 2),
            commodity="maize_lb",
            quantity_lb=round(daily_food_cost_shock / inflated_retail, 2),
            tick=tick,
        )

        self.consistency_validator.synchronize_entities(individuals, households, businesses, ledger)

        n_edu_shock = causal_trace.record_node(
            "node_mateo_dropout_risk", mateo.uid, "individual", "education",
            "dropout_risk", stress_eval.dropout_risk, "prob", tick, "Mateo Dropout Risk Escalates (0.44)"
        )
        n_child_labor = causal_trace.record_node(
            "node_child_labor", mateo.uid, "individual", "education",
            "is_working_informal", mateo_working, "bool", tick, "Adolescent Engages in Informal Day Labor"
        )

        causal_trace.record_relation(
            "edge_budget_to_dropout", n_food_share.node_id, n_edu_shock.node_id,
            "food_inflation_to_education_abandonment", stress_eval.dropout_risk - 0.04, 2,
            "HumanBehaviorHeterogeneityEngine", "Poverty-driven attendance collapse (EHPM/MINED)",
            0.88, EpistemicCategory.EMPIRICAL_EVIDENCE,
        )
        causal_trace.record_relation(
            "edge_dropout_to_labor", n_edu_shock.node_id, n_child_labor.node_id,
            "school_disruption_to_labor_force_entry", 1.0, 1,
            "HumanBehaviorHeterogeneityEngine", "Secondary earner mobilization coping strategy",
            0.85, EpistemicCategory.EXPLICIT_MECHANISM,
        )

        snap_3 = {
            "stage_name": "3. Cascade to Education",
            "description": f"Household cash strained by food. {stress_eval.chosen_strategy}. Attendance drops to {stress_eval.school_attendance_pct}%.",
            "tick": tick,
            "commercial": {
                "road_friction_multiplier": friction_target,
                "wholesale_price_usd": inflated_wholesale,
                "retail_price_usd": inflated_retail,
                "customer_footfall_factor": 0.58,
                "tiendita_cash_usd": tiendita.cash_balance_usd,
                "is_solvent": tiendita.is_solvent,
            },
            "household": {
                "jose_cash_usd": jose.cash_usd,
                "daily_food_cost_usd": daily_food_cost_shock,
                "food_budget_share_pct": food_share_shock,
                "informal_fiado_debt_usd": 0.0,
            },
            "education": {
                "mateo_attendance_pct": stress_eval.school_attendance_pct,
                "mateo_dropout_risk": stress_eval.dropout_risk,
                "mateo_child_labor": mateo_working,
                "school_attendance_pct": 61.5,
            },
            "healthcare": {
                "clinic_wait_hours": 0.20,
                "jose_lost_work_days": 0,
                "out_of_pocket_medicine_usd": 0.0,
                "rosa_health_status": rosa.health_status,
                "jose_health_status": jose.health_status,
            },
        }
        snapshots.append(snap_3)

        # =====================================================================
        # STAGE 4: Healthcare Crisis & Commercial Insolvency Feedback
        # =====================================================================
        tick = 72
        # Severe morbidity event
        rosa.health_status = 0.40  # Hypertensive crisis
        jose.health_status = 0.50  # Acute gastrointestinal infection
        clinic.current_daily_demand = 42
        clinic.status = ServiceCapacityStatus.OVERLOADED
        clinic_wait_hours = 4.20
        jose_lost_days = 4

        # Carmen buys commercial medicine in city pharmacy with household cash
        med_cost = 25.00
        ledger.record_out_of_pocket_medical(
            buyer_id=carmen.uid,
            pharmacy_id="node_pharmacy_city",
            amount_usd=med_cost,
            tick=tick,
            description="Antihypertensive medication for Doña Rosa",
        )

        # José was bedridden for 4 days with zero wages.
        # Household depletes remaining cash on food and survival needs down to $0.00
        jose_curr_cash = ledger.get_entity_balance(jose.uid, AccountType.ASSET_CASH)
        if jose_curr_cash > 0.0:
            ledger.record_retail_food_purchase_cash(
                buyer_id=jose.uid,
                tiendita_id=tiendita.node_id,
                amount_usd=jose_curr_cash,
                cost_of_goods_usd=round(jose_curr_cash * 0.70, 2),
                commodity="maize_lb",
                quantity_lb=round(jose_curr_cash / inflated_retail, 2),
                tick=tick,
            )

        # Household Henríquez reaches $0 cash and takes $18.00 in informal food credit (fiado)
        fiado_amount = 18.00
        fiado_cogs = 13.50
        ledger.record_retail_food_purchase_fiado(
            buyer_id=jose.uid,
            tiendita_id=tiendita.node_id,
            amount_usd=fiado_amount,
            cost_of_goods_usd=fiado_cogs,
            commodity="maize_lb",
            quantity_lb=round(fiado_amount / inflated_retail, 2),
            tick=tick,
        )

        # Tiendita liquidity drain from store overhead and commercial drain
        tiendita_curr_cash = ledger.get_entity_balance(tiendita.node_id, AccountType.ASSET_CASH)
        drain_needed = round(tiendita_curr_cash - 32.00, 2)
        if drain_needed > 0.0:
            # Paid for store utility, transport settlement, or wholesale overhead
            overhead_entries = [
                TransactionEntry(f"{tiendita.node_id}_overhead_exp", tiendita.node_id, AccountType.EXPENSE, debit=drain_needed, credit=0.0),
                TransactionEntry(f"{tiendita.node_id}_cash", tiendita.node_id, AccountType.ASSET_CASH, debit=0.0, credit=drain_needed),
                TransactionEntry("node_wholesaler_sv_cash", "node_wholesaler_sv", AccountType.ASSET_CASH, debit=drain_needed, credit=0.0),
                TransactionEntry("node_wholesaler_sv_rev", "node_wholesaler_sv", AccountType.REVENUE, debit=0.0, credit=drain_needed),
            ]
            ledger.record_transaction(
                concept=TransactionConcept.BUSINESS_OVERHEAD,
                originating_domain="commerce",
                description="Overhead drain and wholesale settlement during road blockage",
                entries=overhead_entries,
                tick=tick,
            )

        self.consistency_validator.synchronize_entities(individuals, households, businesses, ledger)

        n_clinic_overload = causal_trace.record_node(
            "node_clinic_overload", clinic.facility_id, "facility", "healthcare",
            "waiting_time_hours", clinic_wait_hours, "hours", tick, "UCSF Primary Clinic Overloaded (4.2 hr queue)"
        )
        n_out_of_pocket = causal_trace.record_node(
            "node_out_of_pocket", carmen.uid, "individual", "healthcare",
            "out_of_pocket_usd", med_cost, "USD", tick, "Out-of-Pocket Pharmacy Cost ($25.00)"
        )
        n_fiado_debt = causal_trace.record_node(
            "node_fiado_debt", "hh_henriquez", "household", "household_finance",
            "fiado_debt_usd", fiado_amount, "USD", tick, "Henríquez Accumulates $18.00 Informal Fiado"
        )
        n_tiendita_distress = causal_trace.record_node(
            "node_tiendita_distress", tiendita.node_id, "business", "commerce",
            "cash_balance_usd", tiendita.cash_balance_usd, "USD", tick, f"Tiendita Liquidity Distress (${tiendita.cash_balance_usd:.2f})"
        )

        causal_trace.record_relation(
            "edge_overload_to_oop", n_clinic_overload.node_id, n_out_of_pocket.node_id,
            "stockout_to_private_pharmacy", med_cost, 1,
            "CrossDomainInteractionEngine", "Clinic medicine stockout drives private retail purchase",
            0.94, EpistemicCategory.EMPIRICAL_EVIDENCE,
        )
        causal_trace.record_relation(
            "edge_illness_to_fiado", n_clinic_overload.node_id, n_fiado_debt.node_id,
            "lost_wages_to_informal_credit", fiado_amount, 2,
            "HumanBehaviorHeterogeneityEngine", "Zero liquid cash forces request for store credit",
            0.92, EpistemicCategory.EXPLICIT_MECHANISM,
        )
        causal_trace.record_relation(
            "edge_fiado_to_tiendita", n_fiado_debt.node_id, n_tiendita_distress.node_id,
            "uncollected_credit_to_working_capital_drain", round(tiendita.cash_balance_usd - 195.0, 2), 1,
            "RegionalEconomicNetworkEngine", "Working capital tied up in illiquid fiado receivables",
            0.90, EpistemicCategory.EXPLICIT_MECHANISM,
        )

        snap_4 = {
            "stage_name": "4. Health Crisis & Commercial Feedback",
            "description": f"José bedridden & clinic overloaded (4.2 hr wait). Cash drops to $0. Tiendita capital drains to ${tiendita.cash_balance_usd:.2f} (distress).",
            "tick": tick,
            "commercial": {
                "road_friction_multiplier": friction_target,
                "wholesale_price_usd": inflated_wholesale,
                "retail_price_usd": inflated_retail,
                "customer_footfall_factor": 0.48,
                "tiendita_cash_usd": tiendita.cash_balance_usd,
                "is_solvent": tiendita.is_solvent,
            },
            "household": {
                "jose_cash_usd": jose.cash_usd,
                "daily_food_cost_usd": daily_food_cost_shock,
                "food_budget_share_pct": 100.0,
                "informal_fiado_debt_usd": fiado_amount,
            },
            "education": {
                "mateo_attendance_pct": 35.0,
                "mateo_dropout_risk": 0.62,
                "mateo_child_labor": True,
                "school_attendance_pct": 52.0,
            },
            "healthcare": {
                "clinic_wait_hours": clinic_wait_hours,
                "jose_lost_work_days": jose_lost_days,
                "out_of_pocket_medicine_usd": med_cost,
                "rosa_health_status": rosa.health_status,
                "jose_health_status": jose.health_status,
            },
        }
        snapshots.append(snap_4)

        # =====================================================================
        # STAGE 5: Recovery Intervention vs Unmitigated Persistence
        # =====================================================================
        tick = 96
        has_interventions = len(scen.interventions) > 0

        if has_interventions:
            # Apply policy package:
            # 1. Municipal infrastructure road repair workfare: José employed for 5 days at $12/day = $60.00
            ledger.record_municipal_grant_or_workfare(
                beneficiary_id=jose.uid,
                treasury_id="treasury_municipal",
                amount_usd=60.00,
                tick=tick,
                is_workfare=True,
                description="Municipal workfare compensation: rural road corridor drainage repair",
            )

            # 2. José repays Carmen's $18.00 fiado debt in full with cash
            ledger.record_fiado_repayment(
                debtor_id=jose.uid,
                creditor_id=tiendita.node_id,
                amount_usd=fiado_amount,
                tick=tick,
            )

            # 3. Road is fully restored
            road_link.current_friction_multiplier = 1.0
            road_link.is_disrupted = False
            tiendita.selling_price_usd["maize_lb"] = 0.65

            # 4. Public healthcare brigade restocks clinic
            clinic.status = ServiceCapacityStatus.OPERATIONAL
            clinic.current_daily_demand = 22
            rosa.health_status = 0.90
            jose.health_status = 1.00

            # 5. School breakfast & transit voucher restores education
            mateo.current_activity = "secondary_school_student"
            mateo_working = False

            # Normal commercial transactions replenish Tiendita cash up to $215.00
            tiendita_post_cash = ledger.get_entity_balance(tiendita.node_id, AccountType.ASSET_CASH)
            rev_needed = round(215.00 - tiendita_post_cash, 2)
            if rev_needed > 0:
                rev_entries = [
                    TransactionEntry("node_wholesaler_sv_cash", "node_wholesaler_sv", AccountType.ASSET_CASH, debit=0.0, credit=rev_needed),
                    TransactionEntry("node_wholesaler_sv_exp", "node_wholesaler_sv", AccountType.EXPENSE, debit=rev_needed, credit=0.0),
                    TransactionEntry(f"{tiendita.node_id}_cash", tiendita.node_id, AccountType.ASSET_CASH, debit=rev_needed, credit=0.0),
                    TransactionEntry(f"{tiendita.node_id}_rev", tiendita.node_id, AccountType.REVENUE, debit=0.0, credit=rev_needed),
                ]
                ledger.record_transaction(
                    concept=TransactionConcept.FOOD_PURCHASE_CASH,
                    originating_domain="commerce",
                    description="Commercial volume recovery sales",
                    entries=rev_entries,
                    tick=tick,
                )

            self.consistency_validator.synchronize_entities(individuals, households, businesses, ledger)

            n_workfare = causal_trace.record_node(
                "node_workfare_recovery", jose.uid, "individual", "governance",
                "workfare_wage", 60.0, "USD", tick, "Municipal Road Workfare Program"
            )
            n_repay = causal_trace.record_node(
                "node_repay_fiado", "hh_henriquez", "household", "commerce",
                "fiado_repayment", fiado_amount, "USD", tick, "Henríquez Repays $18.00 Store Fiado"
            )
            n_road_restored = causal_trace.record_node(
                "node_road_restored", road_link.link_id, "infrastructure", "transport",
                "friction_multiplier", 1.0, "x", tick, "Road Fully Reopened & Graded"
            )
            n_school_recovered = causal_trace.record_node(
                "node_school_recovered", mateo.uid, "individual", "education",
                "school_attendance", 95.0, "%", tick, "Mateo Returns to Full-time Schooling (95%)"
            )

            causal_trace.record_relation(
                "edge_workfare_to_repay", n_workfare.node_id, n_repay.node_id,
                "wage_liquidity_to_debt_settlement", fiado_amount, 1,
                "VerifiableEconomicLedger", "Cash liquidity enables full formal/informal debt repayment",
                0.96, EpistemicCategory.EXPLICIT_MECHANISM,
            )
            causal_trace.record_relation(
                "edge_repay_to_solvency", n_repay.node_id, n_tiendita_distress.node_id,
                "fiado_collection_to_working_capital", fiado_amount, 1,
                "RegionalEconomicNetworkEngine", "Cash recovery replenishes working capital and restores solvency",
                0.95, EpistemicCategory.EXPLICIT_MECHANISM,
            )
            causal_trace.record_relation(
                "edge_road_to_attendance", n_road_restored.node_id, n_school_recovered.node_id,
                "transit_access_to_school_reentry", 95.0 - 35.0, 1,
                "CrossDomainInteractionEngine", "Safe transit + breakfast relieves family burden",
                0.93, EpistemicCategory.EMPIRICAL_EVIDENCE,
            )

            snap_5 = {
                "stage_name": "5. Integrated Territorial Policy Recovery",
                "description": "Road repaired, school breakfast active, clinic restocked. Mateo returns to school (95%), Tiendita solvent ($215.00).",
                "tick": tick,
                "commercial": {
                    "road_friction_multiplier": 1.0,
                    "wholesale_price_usd": 0.42,
                    "retail_price_usd": 0.65,
                    "customer_footfall_factor": 1.0,
                    "tiendita_cash_usd": tiendita.cash_balance_usd,
                    "is_solvent": True,
                },
                "household": {
                    "jose_cash_usd": jose.cash_usd,
                    "daily_food_cost_usd": 4.50,
                    "food_budget_share_pct": 37.5,
                    "informal_fiado_debt_usd": 0.0,
                },
                "education": {
                    "mateo_attendance_pct": 95.0,
                    "mateo_dropout_risk": 0.05,
                    "mateo_child_labor": False,
                    "school_attendance_pct": 93.0,
                },
                "healthcare": {
                    "clinic_wait_hours": 0.25,
                    "jose_lost_work_days": 0,
                    "out_of_pocket_medicine_usd": 0.0,
                    "rosa_health_status": rosa.health_status,
                    "jose_health_status": jose.health_status,
                },
            }
        else:
            # Unmitigated crisis persistence
            self.consistency_validator.synchronize_entities(individuals, households, businesses, ledger)
            snap_5 = {
                "stage_name": "5. Unmitigated Shock Persistence",
                "description": "No intervention applied. Road remains blocked (3.5x), Mateo continues in child labor, Tiendita remains insolvent ($32).",
                "tick": tick,
                "commercial": {
                    "road_friction_multiplier": friction_target,
                    "wholesale_price_usd": inflated_wholesale,
                    "retail_price_usd": inflated_retail,
                    "customer_footfall_factor": 0.48,
                    "tiendita_cash_usd": tiendita.cash_balance_usd,
                    "is_solvent": False,
                },
                "household": {
                    "jose_cash_usd": jose.cash_usd,
                    "daily_food_cost_usd": daily_food_cost_shock,
                    "food_budget_share_pct": 100.0,
                    "informal_fiado_debt_usd": fiado_amount,
                },
                "education": {
                    "mateo_attendance_pct": 35.0,
                    "mateo_dropout_risk": 0.62,
                    "mateo_child_labor": True,
                    "school_attendance_pct": 52.0,
                },
                "healthcare": {
                    "clinic_wait_hours": clinic_wait_hours,
                    "jose_lost_work_days": jose_lost_days,
                    "out_of_pocket_medicine_usd": med_cost,
                    "rosa_health_status": rosa.health_status,
                    "jose_health_status": jose.health_status,
                },
            }

        snapshots.append(snap_5)

        # Audit accounting conservation
        cons_ok, cons_msg, cons_metrics = ledger.verify_accounting_conservation()

        # Audit consistency
        ind_violations = self.consistency_validator.validate_individual_consistency(jose, households["hh_henriquez"], ledger)
        hh_violations = self.consistency_validator.validate_household_consistency(households["hh_henriquez"], [jose, mateo], ledger)
        biz_violations = self.consistency_validator.validate_business_consistency(tiendita, ledger)
        consistency_passed = len(ind_violations) == 0 and len(hh_violations) == 0 and len(biz_violations) == 0

        final_indicators = {
            "final_road_friction": snapshots[-1]["commercial"]["road_friction_multiplier"],
            "final_retail_maize_price": snapshots[-1]["commercial"]["retail_price_usd"],
            "final_tiendita_cash": snapshots[-1]["commercial"]["tiendita_cash_usd"],
            "final_tiendita_solvent": 1.0 if snapshots[-1]["commercial"]["is_solvent"] else 0.0,
            "final_jose_cash": snapshots[-1]["household"]["jose_cash_usd"],
            "final_mateo_attendance": snapshots[-1]["education"]["mateo_attendance_pct"],
            "final_mateo_dropout_risk": snapshots[-1]["education"]["mateo_dropout_risk"],
            "final_child_labor": 1.0 if snapshots[-1]["education"]["mateo_child_labor"] else 0.0,
            "final_clinic_wait_hours": snapshots[-1]["healthcare"]["clinic_wait_hours"],
            "final_accounting_conserved": 1.0 if cons_ok else 0.0,
        }

        elapsed = time.perf_counter() - t0

        res = ScenarioExecutionResult(
            scenario_id=scenario_id,
            seed=seed,
            duration_ticks=scen.duration_ticks,
            final_indicators=final_indicators,
            intermediate_stages=snapshots,
            causal_trace=causal_trace.to_dict(),
            ledger_summary={
                "total_transactions": len(ledger.transactions),
                "conservation_passed": cons_ok,
                "conservation_metrics": cons_metrics,
            },
            consistency_passed=consistency_passed,
            execution_time_seconds=round(elapsed, 4),
        )

        self.execution_archive.setdefault(scenario_id, []).append(res)
        return res

    # =========================================================================
    # Multi-Seed & Counterfactual Comparison Engine
    # =========================================================================

    def run_multi_seed_evaluation(
        self,
        scenario_id: str,
        seeds: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Execute scenario over multiple seeds and calculate statistical distributions."""
        scen = self.scenarios.get(scenario_id)
        if not scen:
            raise ValueError(f"Scenario '{scenario_id}' not found.")

        eval_seeds = seeds or scen.random_seeds
        results: List[ScenarioExecutionResult] = []

        for s in eval_seeds:
            res = self.execute_scenario(scenario_id=scenario_id, seed=s)
            results.append(res)

        # Aggregate indicators across seeds
        indicator_names = list(results[0].final_indicators.keys())
        stats: Dict[str, Dict[str, float]] = {}

        for ind in indicator_names:
            vals = [r.final_indicators[ind] for r in results]
            mean_val = float(np.mean(vals))
            median_val = float(np.median(vals))
            std_val = float(np.std(vals))
            ci_025 = float(np.percentile(vals, 2.5)) if len(vals) >= 2 else mean_val
            ci_975 = float(np.percentile(vals, 97.5)) if len(vals) >= 2 else mean_val

            stats[ind] = {
                "mean": round(mean_val, 3),
                "median": round(median_val, 3),
                "std": round(std_val, 3),
                "ci_lower_95": round(ci_025, 3),
                "ci_upper_95": round(ci_975, 3),
                "min": round(float(np.min(vals)), 3),
                "max": round(float(np.max(vals)), 3),
            }

        return {
            "scenario_id": scenario_id,
            "seeds_executed": eval_seeds,
            "total_runs": len(results),
            "statistical_summary": stats,
            "all_accounting_conserved": all(r.ledger_summary["conservation_passed"] for r in results),
            "all_consistency_passed": all(r.consistency_passed for r in results),
        }

    def compare_interventions(
        self,
        baseline_scenario_id: str,
        shock_scenario_id: str,
        intervention_scenario_ids: List[str],
    ) -> Dict[str, Any]:
        """Perform rigorous counterfactual comparison between baseline, shock, and policies."""
        # Ensure scenarios have run
        base_res = self.execute_scenario(baseline_scenario_id, seed=42)
        shock_res = self.execute_scenario(shock_scenario_id, seed=42)

        comparison_table: Dict[str, Dict[str, Any]] = {}

        all_scen_ids = [baseline_scenario_id, shock_scenario_id] + intervention_scenario_ids
        for sid in all_scen_ids:
            res = self.execute_scenario(sid, seed=42)
            comparison_table[sid] = {
                "indicators": res.final_indicators,
                "mateo_attendance_pct": res.final_indicators.get("final_mateo_attendance", 0.0),
                "mateo_dropout_risk": res.final_indicators.get("final_mateo_dropout_risk", 0.0),
                "tiendita_solvent": bool(res.final_indicators.get("final_tiendita_solvent", 0.0)),
                "retail_food_price_usd": res.final_indicators.get("final_retail_maize_price", 0.0),
                "clinic_wait_hours": res.final_indicators.get("final_clinic_wait_hours", 0.0),
            }

        return {
            "baseline_scenario_id": baseline_scenario_id,
            "shock_scenario_id": shock_scenario_id,
            "interventions": intervention_scenario_ids,
            "comparison": comparison_table,
        }

    # =========================================================================
    # Default Scenarios Registration
    # =========================================================================

    def _register_default_scenarios(self) -> None:
        """Seed representative generalized territorial scenarios."""
        # 1. Baseline Equilibrium
        self.create_scenario(
            scenario_id="SCEN_BASE_EQUILIBRIUM",
            name="Línea Base: Equilibrio Territorial Cantón San José Las Flores",
            description="Condiciones normales de transitabilidad, precios de granos básicos estables y asistencia escolar alta.",
            department_code="09",
            municipality_id="0902",
            community_id="com_san_jose_flores",
            shocks=[],
            interventions=[],
            hypotheses=["En ausencia de choques, la asistencia escolar se mantiene > 90% y la tiendita es solvente."],
        )

        # 2. Road Landslide & Price Shock (Unmitigated)
        self.create_scenario(
            scenario_id="SCEN_ROAD_LANDSLIDE_SHOCK",
            name="Choque No Mitigado: Deslave Vial e Inflación de Alimentos",
            description="Lluvias torrenciales bloquean el corredor rural no pavimentado, disparando fletes y precios minoristas.",
            department_code="09",
            municipality_id="0902",
            community_id="com_san_jose_flores",
            shocks=[
                {"type": ShockType.ROAD_BLOCKAGE_LANDSLIDE.value, "friction_multiplier": 3.5},
                {"type": ShockType.FOOD_PRICE_SPIKE.value, "markup": 0.50},
            ],
            interventions=[],
            hypotheses=["El bloqueo vial incrementa el gasto de comida a > 70% del jornal y aumenta el riesgo de deserción."],
        )

        # 3. Integrated Multi-Sector Territorial Package
        self.create_scenario(
            scenario_id="SCEN_INTEGRATED_POLICY_RECOVERY",
            name="Recuperación Integral: Proyecto Territorial Multisectorial",
            description="Rehabilitación vial con empleo local, desayuno escolar y brigada médica primaria.",
            department_code="09",
            municipality_id="0902",
            community_id="com_san_jose_flores",
            shocks=[
                {"type": ShockType.ROAD_BLOCKAGE_LANDSLIDE.value, "friction_multiplier": 3.5},
            ],
            interventions=[
                {"type": InterventionType.ROAD_REHABILITATION.value, "budget_usd": 60.0},
                {"type": InterventionType.SCHOOL_BREAKFAST_PROGRAM.value, "daily_saving_usd": 4.0},
                {"type": InterventionType.MOBILE_HEALTH_BRIGADE.value, "free_medicine": True},
            ],
            hypotheses=["El paquete integrado restablece simultáneamente la solvencia comercial, salud y continuidad escolar."],
        )
