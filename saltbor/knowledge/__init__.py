"""Saltbor Knowledge Architecture — Phase 0.6.

Multi-Layer Knowledge Graphs, Autonomous Learning, Pedagogy & Transmission,
Inference & Reasoning, Experimentation & Empirical Discovery, Capability Composition,
and Multidimensional Intelligence Evaluation.
"""

from saltbor.knowledge.graph import (
    KnowledgeGraphEngine,
    KnowledgeNode,
    KnowledgeRelationship,
    NodeType,
    RelationshipType,
    ValidationStatus,
)
from saltbor.knowledge.layers import (
    AgentProceduralCompetency,
    CollectiveKnowledgeGraph,
    CollectiveKnowledgeItem,
    EpistemicClaim,
    EvidenceItem,
    GlobalKnowledgeGraph,
    Hypothesis,
    HypothesisDiscoveryGraph,
    IndividualKnowledgeGraph,
    ProceduralKnowledgeGraph,
    ProcedureDefinition,
    ProcedureStep,
)
from saltbor.knowledge.learning import (
    AutonomousLearningEngine,
    LearningPathway,
    LearningProfile,
    PATHWAY_CONFIDENCE_WEIGHTS,
)
from saltbor.knowledge.transmission import (
    KnowledgeTransmissionEngine,
    TransmissionRecord,
)
from saltbor.knowledge.reasoning import (
    AnalogicalMapping,
    AnalogicalReasoningEngine,
    CausalChain,
    CausalReasoningEngine,
    CompositionProposal,
    CompositionalReasoningEngine,
    HypothesisGenerationEngine,
    InferenceEngine,
    InferenceRule,
    ReasoningBudget,
    RuleBasedInferenceEngine,
    UnexplainedPhenomenon,
)
from saltbor.knowledge.experimentation import (
    ExperimentDesign,
    ExperimentOutcome,
    ExperimentationEngine,
)
from saltbor.knowledge.capabilities import (
    CapabilityCompositionSystem,
    EmergentProfession,
    FeasibleObjectCreation,
)
from saltbor.knowledge.integration import (
    KnowledgeDecisionBridge,
    KnowledgeMemoryBridge,
    KnowledgeSeekingOption,
)
from saltbor.knowledge.observability import (
    CollectiveKnowledgeProfile,
    DiscoveryProfile,
    IndividualKnowledgeProfile,
    KnowledgeObservability,
)
from saltbor.knowledge.evaluation import (
    MultidimensionalIntelligenceEvaluator,
    MultidimensionalIntelligenceReport,
)
from saltbor.knowledge.persistence import KnowledgeRepository

__all__ = [
    # Graph Core
    "KnowledgeNode",
    "NodeType",
    "ValidationStatus",
    "KnowledgeRelationship",
    "RelationshipType",
    "KnowledgeGraphEngine",
    # Layers
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
    # Learning
    "LearningPathway",
    "LearningProfile",
    "PATHWAY_CONFIDENCE_WEIGHTS",
    "AutonomousLearningEngine",
    # Transmission
    "KnowledgeTransmissionEngine",
    "TransmissionRecord",
    # Reasoning
    "InferenceRule",
    "RuleBasedInferenceEngine",
    "CausalChain",
    "CausalReasoningEngine",
    "CompositionProposal",
    "CompositionalReasoningEngine",
    "AnalogicalMapping",
    "AnalogicalReasoningEngine",
    "UnexplainedPhenomenon",
    "HypothesisGenerationEngine",
    "ReasoningBudget",
    "InferenceEngine",
    # Experimentation
    "ExperimentDesign",
    "ExperimentOutcome",
    "ExperimentationEngine",
    # Capabilities
    "EmergentProfession",
    "FeasibleObjectCreation",
    "CapabilityCompositionSystem",
    # Integration
    "KnowledgeMemoryBridge",
    "KnowledgeDecisionBridge",
    "KnowledgeSeekingOption",
    # Observability & Evaluation
    "IndividualKnowledgeProfile",
    "CollectiveKnowledgeProfile",
    "DiscoveryProfile",
    "KnowledgeObservability",
    "MultidimensionalIntelligenceReport",
    "MultidimensionalIntelligenceEvaluator",
    # Persistence
    "KnowledgeRepository",
]
