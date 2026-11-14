"""Data models, enums, and structured contracts for the Universal Domain Platform.

Defines schemas for:
- Universal Domain Configuration
- Human Activity Catalog
- Contextual Behavior & Choices
- Editable World Layers (Layers A, B, C, D)
- Territorial & Organizational Permissions
- Data & Evidence Intelligence
- Scenarios & Interventions
- Decision Intelligence & Recommendations
- Compact Experiment Database
"""

from __future__ import annotations

import dataclasses
from enum import Enum
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4


# =============================================================================
# 1. Universal Domain Configuration Enums & Schemas
# =============================================================================

class DomainCategory(str, Enum):
    FOOD = "food_gastronomy"
    COMMERCE = "commerce_retail"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    TRANSPORTATION = "transportation"
    AGRICULTURE = "agriculture"
    HOUSING = "housing"
    PUBLIC_SERVICES = "public_services"
    TOURISM = "tourism"
    CULTURE = "culture_entertainment"
    MANUFACTURING = "manufacturing"
    LOGISTICS = "logistics"
    SOCIAL_ASSISTANCE = "social_assistance"
    ENVIRONMENTAL = "environmental_management"
    CUSTOM = "custom"


class DomainStatus(str, Enum):
    REGISTERED = "registered"
    VALIDATED = "validated"
    ACTIVE = "active"
    PAUSED = "paused"
    DEPRECATED = "deprecated"


@dataclasses.dataclass
class DomainDefinition:
    """Configurable domain specification."""

    domain_id: str
    name: str
    category: DomainCategory
    purpose: str
    geographic_scope: str = "El Salvador"
    bounding_box: Optional[Tuple[float, float, float, float]] = None  # (min_lon, min_lat, max_lon, max_lat)
    target_demographics: Dict[str, Any] = dataclasses.field(default_factory=dict)
    resources: List[str] = dataclasses.field(default_factory=list)
    infrastructure: List[str] = dataclasses.field(default_factory=list)
    activities: List[str] = dataclasses.field(default_factory=list)
    entities: List[str] = dataclasses.field(default_factory=list)
    operational_rules: Dict[str, Any] = dataclasses.field(default_factory=dict)
    available_services: List[str] = dataclasses.field(default_factory=list)
    economic_relationships: Dict[str, Any] = dataclasses.field(default_factory=dict)
    behavioral_mechanisms: List[str] = dataclasses.field(default_factory=list)
    indicators: List[str] = dataclasses.field(default_factory=list)
    possible_interventions: List[str] = dataclasses.field(default_factory=list)
    data_sources: List[str] = dataclasses.field(default_factory=list)
    uncertainties: List[str] = dataclasses.field(default_factory=list)
    version: str = "1.0.0"
    status: DomainStatus = DomainStatus.REGISTERED
    custom_parameters: Dict[str, Any] = dataclasses.field(default_factory=dict)


# =============================================================================
# 2. Human Activity Catalog Enums & Schemas
# =============================================================================

class ActivityCategory(str, Enum):
    FOOD = "food"
    COMMERCE = "commerce"
    EDUCATION = "education"
    HEALTH = "health"
    TRANSPORTATION = "transportation"
    AGRICULTURE = "agriculture"
    CIVIC = "civic"
    LEISURE = "leisure"


@dataclasses.dataclass(frozen=True)
class ActivityRequirementSpec:
    min_energy: float = 0.05
    max_hunger: float = 0.95
    min_money: float = 0.0
    required_facility_type: Optional[str] = None
    required_skills: Dict[str, float] = dataclasses.field(default_factory=dict)
    required_equipment: List[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class ActivityEffectSpec:
    energy_delta: float = 0.0
    hunger_delta: float = 0.0
    social_delta: float = 0.0
    money_delta: float = 0.0
    health_delta: float = 0.0
    skill_gains: Dict[str, float] = dataclasses.field(default_factory=dict)
    domain_metrics_impact: Dict[str, float] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class DomainActivity:
    """Catalog entry describing a human activity in a domain context."""

    activity_id: str
    name: str
    category: ActivityCategory
    domain_id: str
    description: str
    default_duration_ticks: int = 4  # 1 tick = 15 simulated minutes
    requirements: ActivityRequirementSpec = dataclasses.field(default_factory=ActivityRequirementSpec)
    effects_per_tick: ActivityEffectSpec = dataclasses.field(default_factory=ActivityEffectSpec)
    is_interruptible: bool = True
    context_tags: List[str] = dataclasses.field(default_factory=list)


# =============================================================================
# 3. Contextual Human Behavior Schemas
# =============================================================================

@dataclasses.dataclass
class ContextualDecisionOption:
    """An option considered by a human with its contextual valuation."""

    option_id: str
    activity_id: str
    target_entity_id: Optional[str] = None
    target_location_id: Optional[str] = None
    perceived_cost: float = 0.0
    perceived_benefit: float = 0.0
    distance_meters: float = 0.0
    familiarity_score: float = 0.5  # 0.0 (unfamiliar) to 1.0 (daily habit)
    social_recommendations: int = 0
    risk_estimate: float = 0.1
    utility_score: float = 0.0
    reasoning: str = ""
    is_non_purchase: bool = False


# =============================================================================
# 4. Editable World Layers Enums & Schemas
# =============================================================================

class WorldLayerType(str, Enum):
    LAYER_A_BASE = "layer_a_base"            # Immutable OSM/CNR cartography
    LAYER_B_WORLD = "layer_b_world"          # Custom user zones, municipal workspaces, custom facilities
    LAYER_C_ACTIVITY = "layer_c_activity"    # Living humans, households, operating businesses, schools, clinics
    LAYER_D_INTERVENTIONS = "layer_d_interventions" # Proposed businesses, services, policy changes


class FeatureGeometryType(str, Enum):
    POINT = "Point"
    LINESTRING = "LineString"
    POLYGON = "Polygon"
    MULTIPOLYGON = "MultiPolygon"


@dataclasses.dataclass
class EditableFeature:
    """Geographic entity placed on Layer B, C, or D without altering Layer A."""

    feature_id: str
    layer: WorldLayerType
    geometry_type: FeatureGeometryType
    coordinates: Any  # [lon, lat] or [[lon, lat], ...] or [[[lon, lat], ...]]
    name: str
    category: str
    properties: Dict[str, Any] = dataclasses.field(default_factory=dict)
    owner_id: str = "system"
    scenario_id: Optional[str] = None
    created_at: float = dataclasses.field(default_factory=time.time)
    updated_at: float = dataclasses.field(default_factory=time.time)
    source_attribution: str = "SALTBOR_USER"
    is_deleted: bool = False


# =============================================================================
# 5. Territorial and Organizational Permissions
# =============================================================================

class UserRole(str, Enum):
    CITIZEN = "citizen"
    BUSINESS_OWNER = "business_owner"
    BUSINESS_ADMINISTRATOR = "business_administrator"
    PROPERTY_ADMINISTRATOR = "property_administrator"
    RESEARCHER = "researcher"
    EDUCATIONAL_INSTITUTION = "educational_institution"
    HEALTHCARE_INSTITUTION = "healthcare_institution"
    MUNICIPAL_ADMINISTRATOR = "municipal_administrator"
    GOVERNMENT_INSTITUTION = "government_institution"
    PLATFORM_ADMINISTRATOR = "platform_administrator"


class PermissionType(str, Enum):
    READ = "read"
    CREATE = "create"
    EDIT = "edit"
    DELETE = "delete"
    ADMINISTER = "administer"


class ApprovalStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ACTIVE = "active"
    REJECTED = "rejected"


@dataclasses.dataclass
class UserSubject:
    user_id: str
    name: str
    roles: List[UserRole] = dataclasses.field(default_factory=lambda: [UserRole.CITIZEN])
    geographic_bounds: Optional[Tuple[float, float, float, float]] = None
    institution_id: Optional[str] = None


@dataclasses.dataclass
class AuditAction:
    audit_id: str
    user_id: str
    action_type: PermissionType
    target_resource_id: str
    target_layer: WorldLayerType
    timestamp: float = dataclasses.field(default_factory=time.time)
    details: Dict[str, Any] = dataclasses.field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


# =============================================================================
# 6. Data & Evidence Intelligence
# =============================================================================

class DataProvenanceTier(str, Enum):
    OBSERVED_REAL = "observed_real"                   # Verified empirical data (BCR, DIGESTYC, CNR, OSM)
    IMPORTED_REFERENCE = "imported_reference"         # External benchmarks (World Bank, FAO, WHO, UNESCO)
    USER_PROVIDED = "user_provided"                   # User uploaded / configured data
    SIMULATED = "simulated"                           # Emergent simulation output
    HYPOTHETICAL = "hypothetical"                     # Counterfactual or scenario assumptions
    MODEL_RECOMMENDATION = "model_recommendation"     # Prescriptive decision intelligence output


@dataclasses.dataclass
class DatasetMetadata:
    dataset_id: str
    name: str
    source: str
    license: str
    collection_date: str
    geographic_coverage: str
    temporal_coverage: str
    resolution: str
    methodology: str
    verification_status: str
    confidence_score: float  # 0.0 to 1.0
    limitations: List[str] = dataclasses.field(default_factory=list)
    tier: DataProvenanceTier = DataProvenanceTier.OBSERVED_REAL
    attributes: Dict[str, Any] = dataclasses.field(default_factory=dict)


# =============================================================================
# 7. Scenario and Intervention Engine
# =============================================================================

@dataclasses.dataclass
class ScenarioDefinition:
    scenario_id: str
    name: str
    description: str
    domain_id: str
    baseline_scenario_id: Optional[str] = None
    initial_conditions: Dict[str, Any] = dataclasses.field(default_factory=dict)
    interventions: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    geographic_scope: str = "El Salvador"
    population_filter: Dict[str, Any] = dataclasses.field(default_factory=dict)
    duration_ticks: int = 96
    random_seeds: List[int] = dataclasses.field(default_factory=lambda: [42, 101, 202])
    creator_id: str = "system"


@dataclasses.dataclass
class ScenarioOutcomeSummary:
    scenario_id: str
    domain_id: str
    direct_effects: Dict[str, Any]
    indirect_effects: Dict[str, Any]
    indicators: Dict[str, float]
    uncertainty_bounds: Dict[str, Tuple[float, float]]
    affected_population_count: int
    affected_organizations_count: int
    execution_time_seconds: float


# =============================================================================
# 8. Decision Intelligence & Recommendations
# =============================================================================

class ObjectivePriority(str, Enum):
    PROFITABILITY = "commercial_profitability"
    EMPLOYMENT = "local_employment"
    EDUCATION_ACCESS = "educational_accessibility"
    HEALTHCARE_ACCESS = "healthcare_accessibility"
    COMMUNITY_WELFARE = "community_development"
    SERVICE_COVERAGE = "public_service_coverage"
    RESOURCE_CONSERVATION = "resource_allocation"
    RESILIENCE = "environmental_resilience"


@dataclasses.dataclass
class RecommendationExplanation:
    recommendation_id: str
    user_objective: str
    priorities: List[ObjectivePriority]
    geographic_context: str
    information_sources: List[str]
    important_variables: List[str]
    alternatives_considered: List[Dict[str, Any]]
    expected_benefits: List[str]
    possible_disadvantages: List[str]
    economic_implications: Dict[str, Any]
    social_implications: Dict[str, Any]
    uncertainty_level: str  # "LOW", "MODERATE", "HIGH"
    evidence_quality: str   # "STRONG", "CORROBORATED", "PRELIMINARY", "HYPOTHETICAL"
    simulation_limitations: List[str]
    traceable_reasoning: str


# =============================================================================
# 9. Compact Experiment Database (Section 14)
# =============================================================================

@dataclasses.dataclass
class ExperimentDefinitionRecord:
    experiment_id: str
    research_question: str
    hypotheses: List[Dict[str, Any]]
    domain: str
    parameters: Dict[str, Any]
    initial_conditions: Dict[str, Any]
    population_selection: Dict[str, Any]
    geographic_scope: str
    random_seeds: List[int]


@dataclasses.dataclass
class ExperimentExecutionRecord:
    run_id: str
    execution_time_iso: str
    simulation_version: str
    configuration_version: str
    resource_consumption_sec: float
    execution_status: str  # "SUCCESS", "FAILED", "PARTIAL"


@dataclasses.dataclass
class ExperimentResultRecord:
    key_indicators: Dict[str, float]
    statistical_summaries: Dict[str, Dict[str, float]]
    comparisons: Dict[str, Any]
    confidence_intervals_95: Dict[str, Tuple[float, float]]
    significant_events: List[str]
    unexpected_outcomes: List[str]
    limitations: List[str]


@dataclasses.dataclass
class ExperimentEvidenceRecord:
    data_references: List[str]
    provenance: str
    relevant_logs: List[str]
    test_references: List[str]
    methodology: str


@dataclasses.dataclass
class ExperimentTraceabilityRecord:
    source_file_paths: List[str]
    relevant_classes: List[str]
    relevant_functions: List[str]
    git_commit: str
    graphify_references: List[str]
    test_identifiers: List[str]
    implementation_status: str  # "IMPLEMENTED", "TESTED", "INTEGRATED", "EXPERIMENTALLY_EVALUATED"


@dataclasses.dataclass
class CompactExperimentRecord:
    """Unified compact experiment representation with 5 distinct sections."""

    experiment_id: str
    name: str
    definition: ExperimentDefinitionRecord
    execution: ExperimentExecutionRecord
    results: ExperimentResultRecord
    evidence: ExperimentEvidenceRecord
    traceability: ExperimentTraceabilityRecord
