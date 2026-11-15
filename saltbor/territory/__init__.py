"""SALTBOR Territorial Ecosystem Subsystem (Phase 1.14).

Integrated territorial ecosystems, multi-scale governance, and public impact analysis:
- TerritorialEcosystemEngine: Master orchestrator.
- CrossDomainInteractionEngine: Explicit, traceable inter-domain causal mechanisms.
- MultiScaleTerritorialSimulationEngine: 6 nested geographic and organizational scales.
- RegionalEconomicNetworkEngine: Conserved multi-echelon supply chains & trade networks.
- PublicServiceCapacityEngine: Capacity, coverage areas, service queues, and gaps.
- CollaborativeGovernanceEngine: Multi-actor proposals, RBAC, approval workflows, and audit trails.
- HumanNeedsAssessmentEngine: 12-dimensional needs evaluation with epistemic taxonomy.
- TerritorialProjectEngine: Infrastructure project authoring, costing, and alternative design comparison.
- IntegratedImpactAnalysisEngine: Multi-domain impact reports (direct, indirect, feedback, distributional, unintended).
"""

from __future__ import annotations

from saltbor.territory.cross_domain import (
    CausalPropagationTrace,
    CrossDomainInteractionEngine,
)
from saltbor.territory.ecosystem import TerritorialEcosystemEngine
from saltbor.territory.governance import CollaborativeGovernanceEngine
from saltbor.territory.impact_analysis import IntegratedImpactAnalysisEngine
from saltbor.territory.models import (
    CollaborativeProposal,
    CrossDomainInteraction,
    CrossDomainMechanism,
    GovernanceAuditEntry,
    GovernanceRole,
    HumanNeedDimension,
    IntegratedImpactReport,
    NeedEvidenceTier,
    ProjectAlternativeConfig,
    ProjectApprovalStatus,
    ProjectType,
    PublicServiceFacility,
    RegionalTradeNode,
    ServiceCapacityStatus,
    ServiceCategory,
    SupplyChainLink,
    SupplyChainRole,
    TemporalBehavior,
    TerritorialElement,
    TerritorialElementType,
    TerritorialNeedScore,
    TerritorialProject,
    TerritorialScale,
)
from saltbor.territory.multi_scale import (
    MultiScaleCommunityRecord,
    MultiScaleHouseholdRecord,
    MultiScaleIndividualRecord,
    MultiScaleTerritorialSimulationEngine,
)
from saltbor.territory.needs_assessment import HumanNeedsAssessmentEngine
from saltbor.territory.projects import TerritorialProjectEngine
from saltbor.territory.public_services import PublicServiceCapacityEngine
from saltbor.territory.regional_economics import (
    RegionalEconomicNetworkEngine,
    TradeTransactionRecord,
)

__all__ = [
    "TerritorialEcosystemEngine",
    "CrossDomainInteractionEngine",
    "MultiScaleTerritorialSimulationEngine",
    "RegionalEconomicNetworkEngine",
    "PublicServiceCapacityEngine",
    "CollaborativeGovernanceEngine",
    "HumanNeedsAssessmentEngine",
    "TerritorialProjectEngine",
    "IntegratedImpactAnalysisEngine",
    "TerritorialScale",
    "TerritorialElementType",
    "TerritorialElement",
    "CrossDomainMechanism",
    "CrossDomainInteraction",
    "TemporalBehavior",
    "CausalPropagationTrace",
    "MultiScaleIndividualRecord",
    "MultiScaleHouseholdRecord",
    "MultiScaleCommunityRecord",
    "RegionalTradeNode",
    "SupplyChainLink",
    "SupplyChainRole",
    "TradeTransactionRecord",
    "ServiceCategory",
    "ServiceCapacityStatus",
    "PublicServiceFacility",
    "GovernanceRole",
    "ProjectApprovalStatus",
    "CollaborativeProposal",
    "GovernanceAuditEntry",
    "HumanNeedDimension",
    "NeedEvidenceTier",
    "TerritorialNeedScore",
    "ProjectType",
    "ProjectAlternativeConfig",
    "TerritorialProject",
    "IntegratedImpactReport",
]
