"""Social institutions package."""

from saltbor.social.institutions.assembly import (
    CommunityAssembly,
    InstitutionalProposal,
)
from saltbor.social.institutions.emergent import (
    EmergentInstitution,
    EmergentInstitutionEngine,
    FormalProcedure,
    InstitutionCategory,
)
from saltbor.social.institutions.group import (
    EnhancedSocialGroup,
    GroupType,
)
from saltbor.social.institutions.institutional_evolution import (
    EvolvingInstitution,
    InstitutionDomain,
    InstitutionalEvolutionEngine,
    InstitutionalStatus,
)

__all__ = [
    "CommunityAssembly",
    "EnhancedSocialGroup",
    "GroupType",
    "InstitutionalProposal",
    "EmergentInstitution",
    "EmergentInstitutionEngine",
    "FormalProcedure",
    "InstitutionCategory",
    "EvolvingInstitution",
    "InstitutionDomain",
    "InstitutionalEvolutionEngine",
    "InstitutionalStatus",
]
