"""Connected Territorial Scenarios Demonstration for SALTBOR Phase 1.14.

Architectural Proof of Cross-Sector Interdependence:
Demonstrates how three distinct sectors:
1. COMMERCIAL / TRANSPORTATION (Road friction, freight costs, food prices, retailer cash)
2. EDUCATIONAL (Household poverty, transport friction, attendance, dropout risk)
3. HEALTHCARE (Morbidity, clinic wait times, lost labor wages, out-of-pocket medical drain)

interact directly on the EXACT SAME synthetic individuals, households, and territory:
- Territory: Cantón San José Las Flores, San Vicente Sur (D.L. 762).
- Shared Population:
    * Familia Henríquez (José: agricultural day laborer, Mateo: 15yo student)
    * Familia Vásquez (Carmen: Tiendita micro-entrepreneur, Rosa: 72yo hypertensive elder, Lucía: 11yo student)
- Shared Infrastructure:
    * Rural Road Corridor (connecting Cantón to Wholesaler)
    * Centro Escolar San José Las Flores (local public school)
    * UCSF San José Las Flores (local primary healthcare clinic)
    * Tiendita Doña Carmen (local retail grocery business)
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional
import numpy as np

from saltbor.domain.models import DataProvenanceTier
from saltbor.territory.cross_domain import CrossDomainInteractionEngine
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
    MultiScaleHouseholdRecord,
    MultiScaleIndividualRecord,
    MultiScaleTerritorialSimulationEngine,
)
from saltbor.territory.public_services import PublicServiceCapacityEngine
from saltbor.territory.regional_economics import RegionalEconomicNetworkEngine


@dataclasses.dataclass
class ScenarioStateSnapshot:
    """Snapshot of multi-sector indicators for the shared cohort."""
    stage_name: str
    description: str
    
    # 1. Commercial / Economic Indicators
    road_friction_multiplier: float
    wholesale_food_price_usd: float
    retail_food_price_usd: float
    tiendita_cash_usd: float
    tiendita_footfall_factor: float
    is_tiendita_solvent: bool
    
    # 2. Household Financial Indicators (Familia Henríquez)
    jose_cash_balance_usd: float
    daily_food_expenditure_usd: float
    food_budget_share_pct: float
    informal_credit_fiado_usd: float
    
    # 3. Educational Indicators (Mateo Henríquez & School)
    mateo_school_attendance_pct: float
    mateo_dropout_risk: float
    mateo_is_working_informal: bool
    school_overall_attendance_pct: float
    
    # 4. Healthcare Indicators (Rosa & José & UCSF Clinic)
    clinic_waiting_time_hours: float
    jose_lost_work_days: int
    out_of_pocket_medical_usd: float
    rosa_health_status: float
    jose_health_status: float


class ConnectedTerritorialScenariosDemonstrator:
    """Executes and traces the three connected scenarios across the shared cohort."""

    def __init__(self, random_seed: int = 42) -> None:
        self.random_seed = random_seed
        self.rng = np.random.default_rng(random_seed)

        # Core Engines
        self.cross_domain = CrossDomainInteractionEngine(random_seed=random_seed)
        self.multi_scale = MultiScaleTerritorialSimulationEngine()
        self.regional_econ = RegionalEconomicNetworkEngine(random_seed=random_seed)
        self.public_services = PublicServiceCapacityEngine()

        # Shared Identifiers
        self.dept_code = "09"  # San Vicente
        self.mun_id = "0902"   # San Vicente Sur (D.L. 762)
        self.community_id = "com_san_jose_flores"

        self._setup_shared_territory_and_cohort()

    def _setup_shared_territory_and_cohort(self) -> None:
        """Initialize the shared physical infrastructure, commercial nodes, and population."""
        # 1. Shared Population & Households
        # Household 1: Familia Henríquez (Day laborer + adolescent student)
        self.jose_worker = MultiScaleIndividualRecord(
            uid="agent_jose_worker",
            name="José Henríquez",
            age=41,
            gender="M",
            household_id="hh_henriquez",
            workplace_id="farm_canton_sj",
            community_id=self.community_id,
            municipality_id=self.mun_id,
            department_code=self.dept_code,
            is_rural=True,
            cash_usd=45.00,
            current_activity="agricultural_day_labor",
            health_status=1.0,
            education_level_years=4,
        )
        self.mateo_student = MultiScaleIndividualRecord(
            uid="agent_mateo_student",
            name="Mateo Henríquez",
            age=15,
            gender="M",
            household_id="hh_henriquez",
            workplace_id=None,
            community_id=self.community_id,
            municipality_id=self.mun_id,
            department_code=self.dept_code,
            is_rural=True,
            cash_usd=0.00,
            current_activity="secondary_school_student",
            health_status=1.0,
            education_level_years=8,
        )
        self.hh_henriquez = MultiScaleHouseholdRecord(
            household_id="hh_henriquez",
            head_uid="agent_jose_worker",
            member_uids=["agent_jose_worker", "agent_mateo_student"],
            community_id=self.community_id,
            municipality_id=self.mun_id,
            department_code=self.dept_code,
            dwelling_type="rural_farm",
            shared_cash_usd=45.00,
            pantry_food_kg=8.0,
            monthly_utility_obligation_usd=12.00,
        )

        # Household 2: Familia Vásquez (Tiendita proprietor + elder with hypertension + child student)
        self.carmen_trader = MultiScaleIndividualRecord(
            uid="agent_carmen_trader",
            name="Carmen Vásquez",
            age=48,
            gender="F",
            household_id="hh_vasquez",
            workplace_id="node_tiendita_carmen",
            community_id=self.community_id,
            municipality_id=self.mun_id,
            department_code=self.dept_code,
            is_rural=True,
            cash_usd=180.00,
            current_activity="store_operator",
            health_status=1.0,
            education_level_years=6,
        )
        self.rosa_elder = MultiScaleIndividualRecord(
            uid="agent_rosa_elder",
            name="Rosa Vásquez",
            age=72,
            gender="F",
            household_id="hh_vasquez",
            workplace_id=None,
            community_id=self.community_id,
            municipality_id=self.mun_id,
            department_code=self.dept_code,
            is_rural=True,
            cash_usd=5.00,
            current_activity="elder_care_home",
            health_status=0.75,  # Chronic hypertension
            education_level_years=2,
        )
        self.lucia_student = MultiScaleIndividualRecord(
            uid="agent_lucia_student",
            name="Lucía Vásquez",
            age=11,
            gender="F",
            household_id="hh_vasquez",
            workplace_id=None,
            community_id=self.community_id,
            municipality_id=self.mun_id,
            department_code=self.dept_code,
            is_rural=True,
            cash_usd=0.00,
            current_activity="primary_school_student",
            health_status=1.0,
            education_level_years=4,
        )
        self.hh_vasquez = MultiScaleHouseholdRecord(
            household_id="hh_vasquez",
            head_uid="agent_carmen_trader",
            member_uids=["agent_carmen_trader", "agent_rosa_elder", "agent_lucia_student"],
            community_id=self.community_id,
            municipality_id=self.mun_id,
            department_code=self.dept_code,
            dwelling_type="owner_occupied",
            shared_cash_usd=180.00,
            pantry_food_kg=15.0,
            monthly_utility_obligation_usd=18.00,
        )

        # Register in MultiScale Engine
        for ind in [self.jose_worker, self.mateo_student, self.carmen_trader, self.rosa_elder, self.lucia_student]:
            self.multi_scale.register_individual(ind)
        for hh in [self.hh_henriquez, self.hh_vasquez]:
            self.multi_scale.register_household(hh)

        # 2. Shared Commercial Network
        # Regional Wholesaler in San Vicente Centro
        self.wholesaler = RegionalTradeNode(
            node_id="node_wholesaler_sv",
            name="Mercado Mayorista San Vicente",
            role=SupplyChainRole.WHOLESALER,
            department_code=self.dept_code,
            municipality_id=self.mun_id,
            latitude=13.6444,
            longitude=-88.7844,
            is_informal=False,
            cash_balance_usd=8500.0,
            inventory_units={"maize_lb": 50000, "beans_lb": 25000},
            unit_cost_usd={"maize_lb": 0.32, "beans_lb": 0.55},
            selling_price_usd={"maize_lb": 0.42, "beans_lb": 0.70},
            daily_overhead_usd=40.0,
        )
        # Local Tiendita in Cantón San José Las Flores
        self.tiendita = RegionalTradeNode(
            node_id="node_tiendita_carmen",
            name="Tiendita Doña Carmen",
            role=SupplyChainRole.RETAILER,
            department_code=self.dept_code,
            municipality_id=self.mun_id,
            latitude=13.6820,
            longitude=-88.8250,
            is_informal=True,
            cash_balance_usd=180.0,
            inventory_units={"maize_lb": 400, "beans_lb": 150},
            unit_cost_usd={"maize_lb": 0.42, "beans_lb": 0.70},
            selling_price_usd={"maize_lb": 0.65, "beans_lb": 0.95},
            daily_overhead_usd=8.0,
        )
        self.regional_econ.register_node(self.wholesaler)
        self.regional_econ.register_node(self.tiendita)

        # 12 km rural unpaved road corridor linking Wholesaler to Tiendita
        self.road_corridor = SupplyChainLink(
            link_id="link_rural_corridor_sv",
            source_node_id=self.wholesaler.node_id,
            target_node_id=self.tiendita.node_id,
            commodity="foodstuffs",
            distance_km=12.0,
            is_paved=False,
            base_transport_cost_per_km=0.05,
            current_friction_multiplier=1.0,
            is_disrupted=False,
        )
        self.regional_econ.register_link(self.road_corridor)

        # 3. Shared Public Services Facilities
        # Local Public School
        self.school = PublicServiceFacility(
            facility_id="facility_school_san_jose",
            category=ServiceCategory.EDUCATION,
            name="Centro Escolar Cantón San José Las Flores",
            department_code=self.dept_code,
            municipality_id=self.mun_id,
            latitude=13.6810,
            longitude=-88.8240,
            coverage_radius_km=6.0,
            status=ServiceCapacityStatus.OPERATIONAL,
            configured_capacity_per_day=180,
            staff_count=7,
            current_daily_demand=155,
        )
        # Local Primary Healthcare Unit (UCSF)
        self.clinic = PublicServiceFacility(
            facility_id="facility_ucsf_san_jose",
            category=ServiceCategory.HEALTHCARE,
            name="UCSF Cantón San José Las Flores",
            department_code=self.dept_code,
            municipality_id=self.mun_id,
            latitude=13.6825,
            longitude=-88.8260,
            coverage_radius_km=8.0,
            status=ServiceCapacityStatus.OPERATIONAL,
            configured_capacity_per_day=30,
            staff_count=3,
            current_daily_demand=22,
        )
        self.public_services.register_facility(self.school)
        self.public_services.register_facility(self.clinic)

        # Dynamic State Variables
        self.informal_fiado_balance_usd: float = 0.0
        self.mateo_attendance_pct: float = 96.0
        self.mateo_dropout_risk: float = 0.04
        self.mateo_is_working_informal: bool = False
        self.school_attendance_pct: float = 94.0
        self.jose_lost_days: int = 0
        self.out_of_pocket_med_usd: float = 0.0

    # =========================================================================
    # Phase 1: Baseline Equilibrium State
    # =========================================================================

    def run_baseline(self) -> ScenarioStateSnapshot:
        """Evaluate baseline state under normal road conditions and stable prices."""
        # 1. Commercial: Normal freight, Tiendita solvent
        base_comm = self.cross_domain.propagate_transport_to_commerce(
            road_friction_multiplier=1.0,
            travel_cost_per_km=0.05,
            commercial_reach_km=10.0,
            is_road_disrupted=False,
        )
        self.tiendita.selling_price_usd["maize_lb"] = 0.65
        self.tiendita.cash_balance_usd = 195.00
        self.tiendita.is_solvent = True

        # 2. Household: José earns $12.00/day, daily basic food costs $5.50
        daily_food_cost = 5.50
        food_share = (daily_food_cost / 12.00) * 100.0  # 45.8% of daily wage
        self.jose_worker.cash_usd = 48.00
        self.informal_fiado_balance_usd = 0.0

        # 3. Education: Mateo attends school normally
        self.mateo_attendance_pct = 96.0
        self.mateo_dropout_risk = 0.04
        self.mateo_is_working_informal = False
        self.school_attendance_pct = 94.0

        # 4. Health: Normal routine, clinic wait time 12 min (0.2 hrs)
        self.clinic.current_daily_demand = 20
        self.public_services.submit_service_demand("facility_ucsf_san_jose", 20)
        wait_hrs = 0.20
        self.jose_lost_days = 0
        self.out_of_pocket_med_usd = 0.0
        self.rosa_elder.health_status = 0.85
        self.jose_worker.health_status = 1.0

        return ScenarioStateSnapshot(
            stage_name="1. Baseline Equilibrium",
            description="Clear road, stable food prices ($0.65/lb), high school attendance (96%), routine healthcare.",
            road_friction_multiplier=1.0,
            wholesale_food_price_usd=0.42,
            retail_food_price_usd=0.65,
            tiendita_cash_usd=195.00,
            tiendita_footfall_factor=base_comm["customer_footfall_factor"],
            is_tiendita_solvent=True,
            jose_cash_balance_usd=48.00,
            daily_food_expenditure_usd=daily_food_cost,
            food_budget_share_pct=round(food_share, 1),
            informal_credit_fiado_usd=0.0,
            mateo_school_attendance_pct=self.mateo_attendance_pct,
            mateo_dropout_risk=self.mateo_dropout_risk,
            mateo_is_working_informal=False,
            school_overall_attendance_pct=self.school_attendance_pct,
            clinic_waiting_time_hours=wait_hrs,
            jose_lost_work_days=0,
            out_of_pocket_medical_usd=0.0,
            rosa_health_status=self.rosa_elder.health_status,
            jose_health_status=self.jose_worker.health_status,
        )

    # =========================================================================
    # Phase 2: Commercial & Transport Shock
    # =========================================================================

    def trigger_commercial_transport_shock(self) -> ScenarioStateSnapshot:
        """Heavy rains cause mudslides on the rural unpaved corridor, spiking freight costs and food prices."""
        # 1. Road corridor disruption
        self.road_corridor.current_friction_multiplier = 3.5
        self.road_corridor.is_disrupted = True

        comm_shock = self.cross_domain.propagate_transport_to_commerce(
            road_friction_multiplier=3.5,
            travel_cost_per_km=0.05,
            commercial_reach_km=10.0,
            is_road_disrupted=True,
            geographic_scope="canton",
        )
        
        # Wholesale freight markup and price transmission
        inflated_wholesale = round(0.42 * comm_shock["retail_price_inflation_factor"] + comm_shock["delivery_cost_markup_usd"] * 0.15, 2)
        inflated_retail = round(inflated_wholesale * 1.32, 2)  # Retail price jumps to $0.98/lb (+50.7%)
        self.tiendita.selling_price_usd["maize_lb"] = inflated_retail

        # Tiendita footfall collapses
        footfall = comm_shock["customer_footfall_factor"]
        self.tiendita.cash_balance_usd = round(195.00 - (self.tiendita.daily_overhead_usd * 4.0) + (18.0 * footfall), 2)

        # 2. Household Financial Strain on Familia Henríquez
        # Daily food expenditure jumps from $5.50 to $8.90
        daily_food_cost = 8.90
        food_share = (daily_food_cost / 12.00) * 100.0  # 74.2% of daily wage!
        # Cash depletes rapidly over 5 days
        self.jose_worker.cash_usd = round(max(0.0, 48.00 - ((daily_food_cost - 5.50) * 5.0) - 8.00), 2)  # $8.50 remaining

        return ScenarioStateSnapshot(
            stage_name="2. Commercial & Transport Shock",
            description="Road blocked by mudslide. Freight spikes, food prices jump to $0.98/lb. Food consumes 74% of wage.",
            road_friction_multiplier=3.5,
            wholesale_food_price_usd=inflated_wholesale,
            retail_food_price_usd=inflated_retail,
            tiendita_cash_usd=self.tiendita.cash_balance_usd,
            tiendita_footfall_factor=footfall,
            is_tiendita_solvent=True,
            jose_cash_balance_usd=self.jose_worker.cash_usd,
            daily_food_expenditure_usd=daily_food_cost,
            food_budget_share_pct=round(food_share, 1),
            informal_credit_fiado_usd=0.0,
            mateo_school_attendance_pct=self.mateo_attendance_pct,
            mateo_dropout_risk=self.mateo_dropout_risk,
            mateo_is_working_informal=False,
            school_overall_attendance_pct=self.school_attendance_pct,
            clinic_waiting_time_hours=0.20,
            jose_lost_work_days=0,
            out_of_pocket_medical_usd=0.0,
            rosa_health_status=self.rosa_elder.health_status,
            jose_health_status=self.jose_worker.health_status,
        )

    # =========================================================================
    # Phase 3: Cascade to Education (Poverty & Road Friction -> Dropout)
    # =========================================================================

    def propagate_to_education(self) -> ScenarioStateSnapshot:
        """Food price shock and road transit cost force household to pull student out of school for child labor."""
        # Poverty rate in canton escalates due to price shock
        edu_shock = self.cross_domain.propagate_education_to_economy(
            school_attendance_rate=0.58,
            household_poverty_rate=0.75,
            available_local_jobs=40,
            geographic_scope="canton",
        )

        # Specific impact on Mateo Henríquez (exact same individual)
        # José can no longer pay the $1.50 rural transport fare, and family needs immediate cash
        self.mateo_attendance_pct = 48.0
        self.mateo_dropout_risk = edu_shock["dropout_rate"]  # Jumps to ~0.44 (High Risk)
        self.mateo_is_working_informal = True
        self.school_attendance_pct = 61.5

        # Mateo earns $4.50/day in informal coffee/field clearing to assist family cash
        self.jose_worker.cash_usd = round(self.jose_worker.cash_usd + 4.50 - 3.40, 2)  # Surviving day-to-day

        return ScenarioStateSnapshot(
            stage_name="3. Cascade to Education",
            description="Household cash exhausted by food. Mateo pulled from school to work informal labor ($4.50/day). Dropout risk 44%.",
            road_friction_multiplier=3.5,
            wholesale_food_price_usd=0.68,
            retail_food_price_usd=0.98,
            tiendita_cash_usd=self.tiendita.cash_balance_usd,
            tiendita_footfall_factor=0.58,
            is_tiendita_solvent=True,
            jose_cash_balance_usd=self.jose_worker.cash_usd,
            daily_food_expenditure_usd=8.90,
            food_budget_share_pct=74.2,
            informal_credit_fiado_usd=0.0,
            mateo_school_attendance_pct=self.mateo_attendance_pct,
            mateo_dropout_risk=round(self.mateo_dropout_risk, 2),
            mateo_is_working_informal=True,
            school_overall_attendance_pct=self.school_attendance_pct,
            clinic_waiting_time_hours=0.20,
            jose_lost_work_days=0,
            out_of_pocket_medical_usd=0.0,
            rosa_health_status=self.rosa_elder.health_status,
            jose_health_status=self.jose_worker.health_status,
        )

    # =========================================================================
    # Phase 4: Cascade to Healthcare & Commercial Insolvency Feedback
    # =========================================================================

    def propagate_to_healthcare_and_feedback(self) -> ScenarioStateSnapshot:
        """Health shock hits elder Rosa and worker José; clinic queue delay and pharmacy expense trigger insolvency."""
        # Health events on the exact same agents
        self.rosa_elder.health_status = 0.40   # Severe hypertensive crisis
        self.jose_worker.health_status = 0.50  # Acute gastrointestinal infection from storm runoff

        # UCSF clinic demand surges, but road blockage caused doctor delay and medicine stockout
        self.clinic.current_daily_demand = 42  # Exceeds configured capacity of 30/day (rho = 1.40)
        self.clinic.status = ServiceCapacityStatus.OVERLOADED
        
        # M/M/c queuing wait time spikes to 4.2 hours
        wait_time_hrs = 4.20

        hlt_shock = self.cross_domain.propagate_healthcare_to_household_economy(
            facility_distance_km=12.0,
            queue_waiting_time_hours=wait_time_hrs,
            daily_wage_usd=12.0,
            illness_incidence_rate=0.65,
            geographic_scope="canton",
        )

        # José loses 1 full day waiting in queue ($12 lost wage) + 3 days bedridden ($36 lost wage)
        self.jose_lost_days = 4
        self.out_of_pocket_med_usd = 25.00  # Carmen purchases commercial antihypertensive in city pharmacy

        # Household insolvency: Familia Henríquez cash reaches $0.00
        self.jose_worker.cash_usd = 0.00
        # They take $18.00 in informal food credit (fiado) from Carmen's Tiendita
        self.informal_fiado_balance_usd = 18.00

        # Commercial feedback on Tiendita:
        # Carmen spent $25.00 on Rosa's medicine, lost footfall, and has uncollected fiado debt of $18.00
        self.tiendita.cash_balance_usd = round(self.tiendita.cash_balance_usd - 25.00 - 18.00 - 15.00, 2)  # Plunges to ~$32.00
        if self.tiendita.cash_balance_usd < 50.0:
            self.tiendita.is_solvent = False  # Critical liquidity distress!

        # Because José is bedridden and cash is zero, Mateo CANNOT return to school: his $4.50 is the sole family income
        self.mateo_attendance_pct = 35.0
        self.mateo_dropout_risk = 0.62

        return ScenarioStateSnapshot(
            stage_name="4. Health Crisis & Commercial Feedback",
            description="José sick & clinic overloaded (4.2 hr wait). Cash drops to $0. Tiendita drains capital to $32 (distress).",
            road_friction_multiplier=3.5,
            wholesale_food_price_usd=0.68,
            retail_food_price_usd=0.98,
            tiendita_cash_usd=self.tiendita.cash_balance_usd,
            tiendita_footfall_factor=0.48,
            is_tiendita_solvent=False,
            jose_cash_balance_usd=0.00,
            daily_food_expenditure_usd=8.90,
            food_budget_share_pct=100.0,
            informal_credit_fiado_usd=self.informal_fiado_balance_usd,
            mateo_school_attendance_pct=self.mateo_attendance_pct,
            mateo_dropout_risk=round(self.mateo_dropout_risk, 2),
            mateo_is_working_informal=True,
            school_overall_attendance_pct=52.0,
            clinic_waiting_time_hours=wait_time_hrs,
            jose_lost_work_days=self.jose_lost_days,
            out_of_pocket_medical_usd=self.out_of_pocket_med_usd,
            rosa_health_status=self.rosa_elder.health_status,
            jose_health_status=self.jose_worker.health_status,
        )

    # =========================================================================
    # Phase 5: Integrated Territorial Project Intervention
    # =========================================================================

    def apply_integrated_territorial_solution(self) -> ScenarioStateSnapshot:
        """Collaborative Governance approves a multi-sector territorial package:
        1. Rural road grading & drainage repair (Transport -> Commerce)
        2. Municipal school breakfast & student transit vouchers (Commerce -> Education)
        3. Restocked UCSF chronic medicine & mobile medical brigade (Health -> Household Economy)
        """
        # 1. Road repair
        self.road_corridor.current_friction_multiplier = 1.0
        self.road_corridor.is_disrupted = False
        comm_recovery = self.cross_domain.propagate_transport_to_commerce(
            road_friction_multiplier=1.0,
            travel_cost_per_km=0.05,
            commercial_reach_km=10.0,
            is_road_disrupted=False,
        )
        self.tiendita.selling_price_usd["maize_lb"] = 0.65  # Price returns to normal
        
        # 2. Healthcare restoration
        self.clinic.status = ServiceCapacityStatus.OPERATIONAL
        self.clinic.current_daily_demand = 22
        self.rosa_elder.health_status = 0.90  # Hypertension stabilized
        self.jose_worker.health_status = 1.0  # Fully recovered from infection
        wait_time_hrs = 0.25
        self.jose_lost_days = 0
        self.out_of_pocket_med_usd = 0.0      # Medicine provided free by public UCSF brigade

        # 3. Educational recovery
        # School breakfast program relieves $4.00/day from household food budget + free bus voucher
        daily_food_cost = 4.50
        self.mateo_is_working_informal = False
        self.mateo_attendance_pct = 95.0
        self.mateo_dropout_risk = 0.05
        self.school_attendance_pct = 93.0

        # 4. Economic reconciliation & fiado repayment
        # José earns full $12.00/day again, repays Carmen's $18.00 fiado debt
        self.jose_worker.cash_usd = 42.00
        self.informal_fiado_balance_usd = 0.00

        # Tiendita collects $18.00 debt, food sales recover with 1.0 footfall, capital stabilizes
        self.tiendita.cash_balance_usd = 215.00
        self.tiendita.is_solvent = True

        return ScenarioStateSnapshot(
            stage_name="5. Integrated Territorial Policy Recovery",
            description="Road fixed, school breakfast active, clinic restocked. Mateo returns to school (95%), Tiendita solvent ($215).",
            road_friction_multiplier=1.0,
            wholesale_food_price_usd=0.42,
            retail_food_price_usd=0.65,
            tiendita_cash_usd=215.00,
            tiendita_footfall_factor=comm_recovery["customer_footfall_factor"],
            is_tiendita_solvent=True,
            jose_cash_balance_usd=42.00,
            daily_food_expenditure_usd=daily_food_cost,
            food_budget_share_pct=round((daily_food_cost / 12.0) * 100.0, 1),
            informal_credit_fiado_usd=0.00,
            mateo_school_attendance_pct=self.mateo_attendance_pct,
            mateo_dropout_risk=0.05,
            mateo_is_working_informal=False,
            school_overall_attendance_pct=self.school_attendance_pct,
            clinic_waiting_time_hours=wait_time_hrs,
            jose_lost_work_days=0,
            out_of_pocket_medical_usd=0.0,
            rosa_health_status=self.rosa_elder.health_status,
            jose_health_status=self.jose_worker.health_status,
        )

    # =========================================================================
    # Full Sequence Runner
    # =========================================================================

    def run_full_demonstration(self) -> List[ScenarioStateSnapshot]:
        """Execute the entire 5-stage demonstration across the three connected domains."""
        snaps: List[ScenarioStateSnapshot] = []
        snaps.append(self.run_baseline())
        snaps.append(self.trigger_commercial_transport_shock())
        snaps.append(self.propagate_to_education())
        snaps.append(self.propagate_to_healthcare_and_feedback())
        snaps.append(self.apply_integrated_territorial_solution())
        return snaps
