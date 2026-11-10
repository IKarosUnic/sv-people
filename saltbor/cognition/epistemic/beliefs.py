"""Epistemic beliefs and representations for Phase 0.7.

Distinguishes between:
- OBSERVED_FACT: Directly witnessed by the individual.
- TESTIMONY: Communicated by another agent (subject to credibility discounting).
- INFERENCE: Derived through deduction, induction, abduction, or causal reasoning.
- HYPOTHESIS: Provisional explanatory claim undergoing testing.
- OPINION: Subjective preference, moral judgment, or social sentiment.
- RUMOR: Unverified multi-hop social claim.
- ERRONEOUS_BELIEF: Refuted belief or misconception held prior to correction.
- VALIDATED_KNOWLEDGE: Proven across multiple empirical trials or canonical proof.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any, Optional


class BeliefType(str, Enum):
    """Epistemic classification of beliefs."""

    OBSERVED_FACT = "observed_fact"
    TESTIMONY = "testimony"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    OPINION = "opinion"
    RUMOR = "rumor"
    ERRONEOUS_BELIEF = "erroneous_belief"
    VALIDATED_KNOWLEDGE = "validated_knowledge"


@dataclasses.dataclass
class EpistemicBelief:
    """A rich, structured personal belief held by an individual."""

    belief_id: str
    subject: str                        # Target entity, concept, or agent
    predicate: str                      # Relationship or property (e.g. 'requires', 'causes', 'is_open')
    object_val: Any                     # Value, target node, or state assertion
    belief_type: BeliefType = BeliefType.OBSERVED_FACT
    confidence: float = 0.5             # Subjective confidence in [0.0, 1.0]
    source_type: str = "direct_observation" # 'direct_observation', 'testimony', 'deduction', 'induction', 'experiment'
    source_agent_id: Optional[str] = None
    evidence_items: list[str] = dataclasses.field(default_factory=list)
    contradiction_items: list[str] = dataclasses.field(default_factory=list)
    created_tick: int = 0
    updated_tick: int = 0
    context_tags: list[str] = dataclasses.field(default_factory=list)
    is_active: bool = True
    validation_status: str = "untested" # 'untested', 'supported', 'refuted', 'disputed'

    def update_with_evidence(
        self,
        evidence: str,
        is_supporting: bool,
        evidence_weight: float = 1.0,
        tick: int = 0,
    ) -> float:
        """Update confidence and evidence log in a Bayesian-style manner."""
        self.updated_tick = tick
        weight = max(0.1, min(2.0, evidence_weight))

        if is_supporting:
            self.evidence_items.append(evidence)
            # Increase confidence with diminishing returns
            delta = 0.20 * weight * (1.0 - self.confidence)
            self.confidence = min(1.0, self.confidence + delta)
            if self.belief_type == BeliefType.HYPOTHESIS and len(self.evidence_items) >= 2:
                self.validation_status = "supported"
        else:
            self.contradiction_items.append(evidence)
            # Decrease confidence
            delta = 0.25 * weight * self.confidence
            self.confidence = max(0.0, self.confidence - delta)
            if len(self.contradiction_items) >= 2 and len(self.contradiction_items) > len(self.evidence_items):
                self.validation_status = "refuted"
                self.belief_type = BeliefType.ERRONEOUS_BELIEF

        return self.confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "belief_id": self.belief_id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object_val": self.object_val,
            "belief_type": self.belief_type.value,
            "confidence": round(self.confidence, 4),
            "source_type": self.source_type,
            "source_agent_id": self.source_agent_id,
            "evidence_count": len(self.evidence_items),
            "contradiction_count": len(self.contradiction_items),
            "created_tick": self.created_tick,
            "updated_tick": self.updated_tick,
            "validation_status": self.validation_status,
        }
