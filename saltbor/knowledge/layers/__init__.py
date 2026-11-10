"""Multi-layer knowledge representation systems."""

from saltbor.knowledge.layers.global_graph import GlobalKnowledgeGraph
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph, EpistemicClaim
from saltbor.knowledge.layers.collective_graph import CollectiveKnowledgeGraph, CollectiveKnowledgeItem
from saltbor.knowledge.layers.procedural_graph import (
    ProceduralKnowledgeGraph,
    ProcedureDefinition,
    ProcedureStep,
    AgentProceduralCompetency,
)
from saltbor.knowledge.layers.hypothesis_graph import (
    HypothesisDiscoveryGraph,
    Hypothesis,
    EvidenceItem,
)

__all__ = [
    "GlobalKnowledgeGraph",
    "IndividualKnowledgeGraph",
    "EpistemicClaim",
    "CollectiveKnowledgeGraph",
    "CollectiveKnowledgeItem",
    "ProceduralKnowledgeGraph",
    "ProcedureDefinition",
    "ProcedureStep",
    "AgentProceduralCompetency",
    "HypothesisDiscoveryGraph",
    "Hypothesis",
    "EvidenceItem",
]
