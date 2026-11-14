"""SALTBOR Universal Domain Simulation & Decision Intelligence Platform.

Phase 1.13 Module:
Provides configurable, multi-domain human activity simulation infrastructure
sharing a unified synthetic human core, geographic environment, conserved economy,
and social network foundation.
"""

from saltbor.domain.agriculture import AgricultureActivityDomain, FarmPlot
from saltbor.domain.behavior import ContextualBehaviorEngine
from saltbor.domain.catalog import HumanActivityCatalog
from saltbor.domain.commerce import BusinessActivityDomain, EnterpriseProfile
from saltbor.domain.data_registry import DomainDataRegistry
from saltbor.domain.decision_intelligence import DecisionIntelligenceEngine
from saltbor.domain.editable_world import EditableWorldEngine
from saltbor.domain.education import EducationActivityDomain, EducationalFacility
from saltbor.domain.engine import UniversalDomainEngine
from saltbor.domain.experiment_database import CompactExperimentDatabase
from saltbor.domain.food import FoodActivityDomain, FoodEstablishment
from saltbor.domain.healthcare import HealthcareActivityDomain, HealthcareFacility
from saltbor.domain.models import (
    ActivityCategory,
    ApprovalStatus,
    CompactExperimentRecord,
    ContextualDecisionOption,
    DataProvenanceTier,
    DatasetMetadata,
    DomainActivity,
    DomainCategory,
    DomainDefinition,
    DomainStatus,
    EditableFeature,
    FeatureGeometryType,
    ObjectivePriority,
    PermissionType,
    RecommendationExplanation,
    ScenarioDefinition,
    ScenarioOutcomeSummary,
    UserRole,
    UserSubject,
    WorldLayerType,
)
from saltbor.domain.permissions import DomainPermissionEngine
from saltbor.domain.scenarios import HumanCenteredScenarioEngine
from saltbor.domain.transportation import TransitRoute, TransportationActivityDomain

__all__ = [
    "ActivityCategory",
    "AgricultureActivityDomain",
    "ApprovalStatus",
    "BusinessActivityDomain",
    "CompactExperimentDatabase",
    "CompactExperimentRecord",
    "ContextualBehaviorEngine",
    "ContextualDecisionOption",
    "DataProvenanceTier",
    "DatasetMetadata",
    "DecisionIntelligenceEngine",
    "DomainActivity",
    "DomainCategory",
    "DomainDefinition",
    "DomainPermissionEngine",
    "DomainStatus",
    "EditableFeature",
    "EditableWorldEngine",
    "EducationActivityDomain",
    "EducationalFacility",
    "EnterpriseProfile",
    "FarmPlot",
    "FeatureGeometryType",
    "FoodActivityDomain",
    "FoodEstablishment",
    "HealthcareActivityDomain",
    "HealthcareFacility",
    "HumanActivityCatalog",
    "HumanCenteredScenarioEngine",
    "ObjectivePriority",
    "PermissionType",
    "RecommendationExplanation",
    "ScenarioDefinition",
    "ScenarioOutcomeSummary",
    "TransitRoute",
    "TransportationActivityDomain",
    "UniversalDomainEngine",
    "UserRole",
    "UserSubject",
    "WorldLayerType",
]
