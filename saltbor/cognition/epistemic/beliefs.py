"""Epistemic beliefs and representations for SALTBOR Phase 1.3 (Section 6).

Explicitly distinguishes the 8 required knowledge states:
1. VERIFIED_KNOWLEDGE: Thoroughly tested and empirically validated.
2. PROVISIONAL_KNOWLEDGE: Supported by initial evidence but subject to further tests.
3. HYPOTHESIS: Formal explanatory conjecture undergoing active experimentation.
4. PERSONAL_BELIEF: Subjective opinion, conviction, or intuition.
5. RUMOR: Unverified socially transmitted narrative.
6. CONTRADICTORY_INFO: Inconsistent claims with unresolved counter-evidence.
7. FORGOTTEN_KNOWLEDGE: Atrophied knowledge with degraded details and low accessibility.
8. REFUTED_KNOWLEDGE: Formally disproven through empirical contradiction.

Preserves full provenance, evidence logs, confidence, context tags, and transmission history.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any, List, Optional


class BeliefType(str, Enum):
    """Epistemic classification of beliefs and knowledge states."""

    # Phase 1.3 Canonical Epistemic Categories
    VERIFIED_KNOWLEDGE = "verified_knowledge"
    PROVISIONAL_KNOWLEDGE = "provisional_knowledge"
    HYPOTHESIS = "hypothesis"
    PERSONAL_BELIEF = "personal_belief"
    RUMOR = "rumor"
    CONTRADICTORY_INFO = "contradictory_info"
    FORGOTTEN_KNOWLEDGE = "forgotten_knowledge"
    REFUTED_KNOWLEDGE = "refuted_knowledge"

    # Backward compatibility aliases with Phase 0.7 & 1.2
    OBSERVED_FACT = "observed_fact"
    TESTIMONY = "testimony"
    INFERENCE = "inference"
    OPINION = "opinion"
    ERRONEOUS_BELIEF = "erroneous_belief"
    VALIDATED_KNOWLEDGE = "validated_knowledge"


@dataclasses.dataclass
class EpistemicBelief:
    """A rich, structured personal belief or knowledge item held by an individual."""

    belief_id: str
    subject: str                        # Target entity, concept, or domain (e.g. 'milpa_yield', 'pumice_lime')
    predicate: str                      # Relationship or property ('causes', 'increases', 'requires', 'prevents')
    object_val: Any                     # State assertion, value, or effect
    belief_type: BeliefType = BeliefType.PERSONAL_BELIEF
    confidence: float = 0.50            # Subjective confidence in [0.0, 1.0]
    source_type: str = "direct_observation" # 'direct_observation', 'testimony', 'experiment', 'tradition'
    source_agent_id: Optional[str] = None
    provenance: str = "self_discovery"  # Origin description or lineage
    evidence_items: list[str] = dataclasses.field(default_factory=list)
    contradiction_items: list[str] = dataclasses.field(default_factory=list)
    transmission_lineage: list[str] = dataclasses.field(default_factory=list)
    hop_count: int = 0
    created_tick: int = 0
    updated_tick: int = 0
    context_tags: list[str] = dataclasses.field(default_factory=list)
    is_active: bool = True
    validation_status: str = "untested" # 'untested', 'provisional', 'supported', 'refuted', 'disputed'

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

            if self.belief_type == BeliefType.HYPOTHESIS:
                if len(self.evidence_items) >= 3 and len(self.contradiction_items) == 0:
                    self.validation_status = "supported"
                    self.belief_type = BeliefType.VERIFIED_KNOWLEDGE
                else:
                    self.validation_status = "provisional"
                    self.belief_type = BeliefType.PROVISIONAL_KNOWLEDGE
            elif self.belief_type == BeliefType.PROVISIONAL_KNOWLEDGE and len(self.evidence_items) >= 4:
                self.validation_status = "supported"
                self.belief_type = BeliefType.VERIFIED_KNOWLEDGE

        else:
            self.contradiction_items.append(evidence)
            # Decrease confidence
            delta = 0.25 * weight * self.confidence
            self.confidence = max(0.0, self.confidence - delta)

            if len(self.contradiction_items) >= 2:
                if len(self.evidence_items) > 0 and len(self.contradiction_items) > 0:
                    self.validation_status = "disputed"
                    self.belief_type = BeliefType.CONTRADICTORY_INFO
                if len(self.contradiction_items) >= 3 and len(self.contradiction_items) > len(self.evidence_items) * 1.5:
                    self.validation_status = "refuted"
                    self.belief_type = BeliefType.REFUTED_KNOWLEDGE

        return self.confidence

    def mark_forgotten(self, tick: int) -> None:
        """Mark this knowledge item as faded or degraded from prolonged disuse."""
        self.belief_type = BeliefType.FORGOTTEN_KNOWLEDGE
        self.confidence = max(0.05, self.confidence * 0.40)
        self.updated_tick = tick

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
            "provenance": self.provenance,
            "evidence_count": len(self.evidence_items),
            "contradiction_count": len(self.contradiction_items),
            "hop_count": self.hop_count,
            "lineage": self.transmission_lineage,
            "created_tick": self.created_tick,
            "updated_tick": self.updated_tick,
            "validation_status": self.validation_status,
            "context_tags": self.context_tags,
        }
