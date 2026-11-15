"""Territorial Ecosystem Data Models & Schemas for SALTBOR Phase 1.14.

Defines schemas and data structures for:
- Nested territorial scales (Individual, Household, Business/Facility, Community, Municipality, Department/National).
- Territorial elements, operational attributes, and geographic relationships.
- Cross-domain interaction mechanisms, variables, and causal weights.
- Public service capacity, catchment areas, and queue metrics.
- Regional economic networks, multi-echelon supply chains, and price transmission.
- Collaborative governance roles, permissions, approval workflows, and audit logs.
- Multi-dimensional human needs assessment across 12 dimensions with epistemic tiers.
- Territorial project design, alternative configurations, and costing.
- Integrated multi-domain impact assessments (direct, indirect, feedback, distributional, unintended).
"""

from __future__ import annotations

import dataclasses
import enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from saltbor.domain.models import DataProvenanceTier


# =============================================================================
# Territorial Scales & Element Types
# =============================================================================

class TerritorialScale(str, enum.Enum):
    """The 6 nested geographic and organizational scales of SALTBOR."""
    LEVEL_1_INDIVIDUAL = "level_1_individual"
    LEVEL_2_HOUSEHOLD = "level_2_household"
    LEVEL_3_BUSINESS_INSTITUTION = "level_3_business_institution"
    LEVEL_4_COMMUNITY = "level_4_community"
    LEVEL_5_MUNICIPALITY = "level_5_municipality"
    LEVEL_6_DEPARTMENT_NATIONAL = "level_6_department_national"


class TerritorialElementType(str, enum.Enum):
    """Categorization of physical, human, organizational, and ecological elements."""
    POPULATION = "population"
    HOUSEHOLD = "household"
    BUSINESS = "business"
    EDUCATIONAL_FACILITY = "educational_facility"
    HEALTHCARE_FACILITY = "healthcare_facility"
    PUBLIC_SERVICE = "public_service"
    TRANSPORTATION = "transportation"
    AGRICULTURAL_PLOT = "agricultural_plot"
    NATURAL_RESOURCE = "natural_resource"
    COMMERCIAL_NETWORK = "commercial_network"
    INSTITUTION = "institution"
    COMMUNITY_ORGANIZATION = "community_organization"
    CULTURAL_ACTIVITY = "cultural_activity"
    ENVIRONMENTAL_ZONE = "environmental_zone"


@dataclasses.dataclass
class TerritorialElement:
    """Core entity within the interconnected territorial ecosystem."""
    element_id: str
    element_type: TerritorialElementType
    scale: TerritorialScale
    name: str
    latitude: float
    longitude: float
    department_code: str
    municipality_id: str
    district_id: Optional[str] = None
    canton_name: Optional[str] = None
    is_rural: bool = False
    is_formal: bool = True
    operational_attributes: Dict[str, Any] = dataclasses.field(default_factory=dict)
    connected_element_ids: List[str] = dataclasses.field(default_factory=list)
    parent_element_id: Optional[str] = None
    provenance_tier: DataProvenanceTier = DataProvenanceTier.OBSERVED_REAL
    source_reference: str = "CNR_IGN_2024"
    assumptions_label: Optional[str] = None


# =============================================================================
# Cross-Domain Mechanisms & Interactions
# =============================================================================

class CrossDomainMechanism(str, enum.Enum):
    """Traceable, explicit mechanisms linking sectoral domains."""
    # TRANSPORTATION -> COMMERCE
    TRANS_ACCESSIBILITY_REACH = "trans_accessibility_reach"
    TRANS_COST_PURCHASING = "trans_cost_purchasing"
    TRANS_DISRUPTION_DELIVERIES = "trans_disruption_deliveries"
    TRANS_NEW_CONNECTION_COMMERCE = "trans_new_connection_commerce"

    # EDUCATION -> ECONOMY
    EDU_ACCESSIBILITY_PARTICIPATION = "edu_accessibility_participation"
    EDU_SKILLS_LABOR_SUPPLY = "edu_skills_labor_supply"
    EDU_HOUSEHOLD_POVERTY_DROPOUT = "edu_household_poverty_dropout"
    EDU_LOCAL_EMPLOYMENT_INCENTIVE = "edu_local_employment_incentive"

    # HEALTHCARE -> HOUSEHOLD ECONOMY
    HLT_ACCESSIBILITY_UTILIZATION = "hlt_accessibility_utilization"
    HLT_TRAVEL_WAITING_COST = "hlt_travel_waiting_cost"
    HLT_CAPACITY_BOTTLENECK = "hlt_capacity_bottleneck"
    HLT_ILLNESS_LABOR_LIMITATION = "hlt_illness_labor_limitation"

    # AGRICULTURE -> FOOD COMMERCE
    AGR_HARVEST_SUPPLY_VOLUME = "agr_harvest_supply_volume"
    AGR_SEASONALITY_AVAILABILITY = "agr_seasonality_availability"
    AGR_TRANS_FRICTION_FOOD_PRICE = "agr_trans_friction_food_price"
    AGR_PRICE_SPIKE_CONSUMER_CHOICE = "agr_price_spike_consumer_choice"

    # ENVIRONMENT -> MULTIPLE DOMAINS
    ENV_DROUGHT_AGR_WATER_DISPLACEMENT = "env_drought_agr_water_displacement"
    ENV_FLOOD_TRANSPORT_HALT = "env_flood_transport_halt"
    ENV_DEGRADATION_LIVELIHOOD_SETTLEMENT = "env_degradation_livelihood_settlement"

    # INSTITUTIONS -> COMMUNITY
    INS_PUBLIC_PROGRAM_SERVICE = "ins_public_program_service"
    INS_CAPACITY_IMPLEMENTATION_GAP = "ins_capacity_implementation_gap"
    INS_TRUST_PARTICIPATION_COMPLIANCE = "ins_trust_participation_compliance"


class TemporalBehavior(str, enum.Enum):
    IMMEDIATE = "immediate"      # Intra-tick / same-day effect
    DAILY = "daily"              # 1-day step (96 ticks)
    SEASONAL = "seasonal"        # Seasonal cycle (invierno/verano)
    LAGGED = "lagged"            # Delayed multi-period effect


@dataclasses.dataclass
class CrossDomainInteraction:
    """An explicit, traceable causal linkage between domains."""
    interaction_id: str
    source_domain: str
    target_domain: str
    mechanism: CrossDomainMechanism
    description: str
    input_variables: List[str]
    output_variables: List[str]
    elasticity_or_rate: float
    geographic_scope: str  # e.g., "district", "municipality", "department", "national"
    temporal_behavior: TemporalBehavior
    delay_ticks: int = 0
    provenance_tier: DataProvenanceTier = DataProvenanceTier.SIMULATED
    assumptions_label: str = "Calibrated based on Salvadoran empirical context"
    causal_weight: float = 1.0
    uncertainty_std: float = 0.05
    active: bool = True


# =============================================================================
# Regional Economic Network & Supply Chains
# =============================================================================

class SupplyChainRole(str, enum.Enum):
    AGRICULTURAL_PRODUCER = "agricultural_producer"
    FOOD_PROCESSOR = "food_processor"
    WHOLESALER = "wholesaler"
    RETAILER = "retailer"
    RESTAURANT_COMEDOR = "restaurant_comedor"
    CONSUMER = "consumer"
    WORKER = "worker"
    TRANSPORTER = "transporter"
    FINANCIAL_INSTITUTION = "financial_institution"
    COOPERATIVE = "cooperative"


@dataclasses.dataclass
class RegionalTradeNode:
    """An economic actor participating in regional trade."""
    node_id: str
    name: str
    role: SupplyChainRole
    department_code: str
    municipality_id: str
    latitude: float
    longitude: float
    is_informal: bool = False
    cash_balance_usd: float = 500.0
    inventory_units: Dict[str, int] = dataclasses.field(default_factory=dict)
    unit_cost_usd: Dict[str, float] = dataclasses.field(default_factory=dict)
    selling_price_usd: Dict[str, float] = dataclasses.field(default_factory=dict)
    daily_overhead_usd: float = 10.0
    employees: List[str] = dataclasses.field(default_factory=list)
    daily_wage_usd: float = 12.0
    is_solvent: bool = True
    consecutive_loss_days: int = 0


@dataclasses.dataclass
class SupplyChainLink:
    """A directed physical and economic trade corridor connecting supply chain nodes."""
    link_id: str
    source_node_id: str
    target_node_id: str
    commodity: str
    distance_km: float
    is_paved: bool = True
    base_transport_cost_per_km: float = 0.05  # USD per km per unit
    current_friction_multiplier: float = 1.0  # Road damage, traffic, weather
    is_disrupted: bool = False
    max_throughput_units_per_day: int = 1000

    @property
    def effective_transport_cost(self) -> float:
        terrain_penalty = 1.0 if self.is_paved else 1.8
        disruption_penalty = 5.0 if self.is_disrupted else 1.0
        return self.distance_km * self.base_transport_cost_per_km * terrain_penalty * self.current_friction_multiplier * disruption_penalty


# =============================================================================
# Public Service Capacity & Infrastructure
# =============================================================================

class ServiceCategory(str, enum.Enum):
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    PUBLIC_TRANSIT = "public_transit"
    WATER_ACCESS = "water_access"
    SANITATION = "sanitation"
    WASTE_COLLECTION = "waste_collection"
    COMMUNITY_SPACE = "community_space"
    PUBLIC_MARKET = "public_market"
    CULTURAL_FACILITY = "cultural_facility"
    EMERGENCY_SERVICE = "emergency_service"


class ServiceCapacityStatus(str, enum.Enum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    CLOSED = "closed"
    UNCONFIGURED = "unconfigured"


@dataclasses.dataclass
class PublicServiceFacility:
    """Infrastructure facility with operational and throughput constraints."""
    facility_id: str
    category: ServiceCategory
    name: str
    department_code: str
    municipality_id: str
    latitude: float
    longitude: float
    coverage_radius_km: float = 5.0
    status: ServiceCapacityStatus = ServiceCapacityStatus.OPERATIONAL
    configured_capacity_per_day: Optional[int] = None  # None = Unknown / Unconfigured
    staff_count: Optional[int] = None                  # None = Unknown / Unconfigured
    available_equipment_score: float = 1.0             # 0.0 to 1.0
    current_daily_demand: int = 0
    current_waiting_queue: int = 0
    served_today: int = 0
    unmet_demand_today: int = 0
    geographic_accessibility_index: float = 1.0        # Friction-based accessibility
    service_limitations: List[str] = dataclasses.field(default_factory=list)
    provenance_tier: DataProvenanceTier = DataProvenanceTier.OBSERVED_REAL


# =============================================================================
# Collaborative Governance & Institutional Permissions
# =============================================================================

class GovernanceRole(str, enum.Enum):
    CITIZEN = "citizen"
    BUSINESS_OWNER = "business_owner"
    COMMUNITY_LEADER_ADESCO = "community_leader_adesco"
    RESEARCHER = "researcher"
    EDUCATIONAL_REPRESENTATIVE = "educational_representative"
    HEALTHCARE_REPRESENTATIVE = "healthcare_representative"
    MUNICIPAL_ADMINISTRATOR = "municipal_administrator"
    GOVERNMENT_MINISTRY_OFFICIAL = "government_ministry_official"
    NONPROFIT_COORDINATOR = "nonprofit_coordinator"


class ProjectApprovalStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    IN_EXECUTION = "in_execution"
    COMPLETED = "completed"
    REJECTED = "rejected"


@dataclasses.dataclass
class GovernanceAuditEntry:
    entry_id: str
    timestamp_tick: int
    actor_id: str
    actor_role: GovernanceRole
    action: str
    target_id: str
    details: Dict[str, Any]
    authorized: bool


@dataclasses.dataclass
class CollaborativeProposal:
    """A versioned territorial project proposal submitted through the governance engine."""
    proposal_id: str
    title: str
    description: str
    proposer_id: str
    proposer_role: GovernanceRole
    target_municipality_id: str
    target_department_code: str
    project_type: str
    requested_budget_usd: float
    status: ProjectApprovalStatus = ProjectApprovalStatus.DRAFT
    version: int = 1
    versions_history: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    approval_signatures: Dict[str, str] = dataclasses.field(default_factory=dict) # role -> actor_id
    rejection_reasons: List[str] = dataclasses.field(default_factory=list)
    conflicts_identified: List[str] = dataclasses.field(default_factory=list)
    is_simulated_intervention: bool = True  # Distinguish simulated vs real-world intent


# =============================================================================
# Human Needs Assessment (12 Dimensions)
# =============================================================================

class HumanNeedDimension(str, enum.Enum):
    FOOD_AVAILABILITY = "food_availability"
    EMPLOYMENT_OPPORTUNITY = "employment_opportunity"
    EDUCATIONAL_ACCESSIBILITY = "educational_accessibility"
    HEALTHCARE_ACCESSIBILITY = "healthcare_accessibility"
    HOUSING_SECURITY = "housing_security"
    TRANSPORTATION_MOBILITY = "transportation_mobility"
    WATER_ACCESS = "water_access"
    SANITATION = "sanitation"
    SOCIAL_SUPPORT = "social_support"
    RECREATION = "recreation"
    CULTURAL_PARTICIPATION = "cultural_participation"
    ECONOMIC_OPPORTUNITY = "economic_opportunity"


class NeedEvidenceTier(str, enum.Enum):
    CONFIRMED_SERVICE_SHORTAGE = "confirmed_service_shortage"          # Real empirical shortfall
    POTENTIAL_ACCESSIBILITY_GAP = "potential_accessibility_gap"        # Distance/spatial travel gap
    SIMULATED_UNMET_DEMAND = "simulated_unmet_demand"                  # Agent cognitive/economic frustration
    USER_REPORTED_NEED = "user_reported_need"                          # Submitted community proposal
    UNVERIFIED_HYPOTHESIS = "unverified_hypothesis"                    # Exploratory scenario assumption


@dataclasses.dataclass
class TerritorialNeedScore:
    """Need assessment record for a specific community or territory."""
    need_id: str
    territory_id: str
    scale: TerritorialScale
    dimension: HumanNeedDimension
    unmet_severity: float  # 0.0 (fully satisfied) to 1.0 (extreme deprivation)
    evidence_tier: NeedEvidenceTier
    affected_population_estimate: int
    confidence_interval_95: Tuple[float, float]
    primary_causal_factors: List[str]
    explicit_assumptions: str


# =============================================================================
# Territorial Project Design & Alternative Configurations
# =============================================================================

class ProjectType(str, enum.Enum):
    PUBLIC_MARKET = "public_market"
    COMMUNITY_COMMERCIAL_CENTER = "community_commercial_center"
    RURAL_SCHOOL = "rural_school"
    HEALTHCARE_FACILITY = "healthcare_facility"
    TRANSPORTATION_CONNECTION = "transportation_connection"
    AGRICULTURAL_DISTRIBUTION_CENTER = "agricultural_distribution_center"
    CULTURAL_FACILITY = "cultural_facility"
    PUBLIC_RECREATIONAL_SPACE = "public_recreational_space"
    VOCATIONAL_TRAINING_CENTER = "vocational_training_center"
    WATER_INFRASTRUCTURE = "water_infrastructure"


@dataclasses.dataclass
class ProjectAlternativeConfig:
    """An alternative design configuration for a proposed territorial intervention."""
    config_id: str
    name: str
    description: str  # e.g., "1 large central facility", "3 distributed micro-facilities", "mobile brigade"
    capital_cost_usd: float
    annual_operating_cost_usd: float
    daily_service_capacity: int
    catchment_radius_km: float
    expected_service_coverage_pct: float
    estimated_implementation_months: int
    trade_off_summary: str


@dataclasses.dataclass
class TerritorialProject:
    """A proposed public intervention project in a territory."""
    project_id: str
    title: str
    project_type: ProjectType
    objective: str
    department_code: str
    municipality_id: str
    latitude: float
    longitude: float
    target_population: int
    selected_config: ProjectAlternativeConfig
    alternative_configs: List[ProjectAlternativeConfig] = dataclasses.field(default_factory=list)
    relevant_domains: List[str] = dataclasses.field(default_factory=list)
    potential_externalities: List[str] = dataclasses.field(default_factory=list)
    success_indicators: List[str] = dataclasses.field(default_factory=list)
    uncertainties: List[str] = dataclasses.field(default_factory=list)
    status: ProjectApprovalStatus = ProjectApprovalStatus.DRAFT


# =============================================================================
# Integrated Multi-Domain Impact Analysis
# =============================================================================

@dataclasses.dataclass
class DomainImpactDelta:
    domain_id: str
    indicator_name: str
    baseline_value: float
    intervention_value: float
    absolute_delta: float
    relative_change_pct: float
    is_positive: bool


@dataclasses.dataclass
class IntegratedImpactReport:
    """Traceable multi-domain impact assessment for an intervention."""
    report_id: str
    project_id: str
    intervention_name: str
    direct_effects: List[DomainImpactDelta]
    indirect_effects: List[DomainImpactDelta]
    feedback_loops: List[str]
    delayed_effects: List[str]
    distributional_gini_delta: float
    distributional_lowest_quintile_gain_pct: float
    unintended_consequences: List[str]
    potential_negative_effects: List[str]
    simulated_vs_empirical_breakdown: Dict[str, str]
    overall_recommendation: str
