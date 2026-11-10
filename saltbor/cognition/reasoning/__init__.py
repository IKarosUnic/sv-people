"""Advanced reasoning engine for Saltbor Phase 0.7."""

from saltbor.cognition.reasoning.abductive import AbductiveReasoningEngine, ExplanationHypothesis
from saltbor.cognition.reasoning.analogical import (
    AdvancedAnalogicalReasoningEngine,
    AnalogicalDomainSchema,
    AnalogicalTransferResult,
)
from saltbor.cognition.reasoning.causal import (
    AdvancedCausalReasoningEngine,
    CausalInferencePath,
    CausalLink,
    CausalRelationStatus,
)
from saltbor.cognition.reasoning.counterfactual import (
    CounterfactualEvaluation,
    CounterfactualReasoningEngine,
)
from saltbor.cognition.reasoning.deductive import (
    DeductionTrace,
    DeductiveReasoningEngine,
    LogicalRule,
    Premise,
)
from saltbor.cognition.reasoning.engine import AdvancedReasoningEngine, ReasoningBudget
from saltbor.cognition.reasoning.hypothetical import (
    HypotheticalReasoningEngine,
    HypotheticalScenario,
)
from saltbor.cognition.reasoning.inductive import (
    InductivePattern,
    InductiveReasoningEngine,
    ObservationRecord,
)

__all__ = [
    "AbductiveReasoningEngine",
    "AdvancedAnalogicalReasoningEngine",
    "AdvancedCausalReasoningEngine",
    "AdvancedReasoningEngine",
    "AnalogicalDomainSchema",
    "AnalogicalTransferResult",
    "CausalInferencePath",
    "CausalLink",
    "CausalRelationStatus",
    "CounterfactualEvaluation",
    "CounterfactualReasoningEngine",
    "DeductionTrace",
    "DeductiveReasoningEngine",
    "ExplanationHypothesis",
    "HypotheticalReasoningEngine",
    "HypotheticalScenario",
    "InductivePattern",
    "InductiveReasoningEngine",
    "LogicalRule",
    "ObservationRecord",
    "Premise",
    "ReasoningBudget",
]
