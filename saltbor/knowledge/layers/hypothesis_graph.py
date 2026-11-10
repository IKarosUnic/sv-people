"""Hypothesis and Discovery Graph (Layer 5).

Maintains uncertain propositions, scientific explanations, competing theories,
experimental evidence, and discovery life-cycles.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Optional
from uuid import uuid4

from saltbor.knowledge.graph.node import ValidationStatus


@dataclasses.dataclass
class EvidenceItem:
    """An empirical observation or test outcome supporting or contradicting a hypothesis."""

    evidence_id: str
    experiment_id: Optional[str]
    observer_uid: str
    observation_summary: str
    is_supporting: bool                 # True = supports, False = refutes
    weight: float = 1.0                 # Strength of the empirical signal
    timestamp_tick: int = 0
    context_data: dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class Hypothesis:
    """An explanatory proposition under epistemic evaluation."""

    hypothesis_id: str
    creator_uid: str
    title: str
    target_phenomenon: str              # What observation or problem this seeks to explain
    statement: str                      # The proposed causal or structural claim
    assumptions: list[str] = dataclasses.field(default_factory=list)
    status: ValidationStatus = ValidationStatus.PROPOSED
    prior_confidence: float = 0.5
    posterior_confidence: float = 0.5
    supporting_evidence: list[EvidenceItem] = dataclasses.field(default_factory=list)
    contradicting_evidence: list[EvidenceItem] = dataclasses.field(default_factory=list)
    created_tick: int = 0
    updated_tick: int = 0
    competing_hypothesis_ids: list[str] = dataclasses.field(default_factory=list)
    replications_count: int = 0

    def add_evidence(self, evidence: EvidenceItem, tick: int = 0) -> None:
        """Integrate empirical evidence and adjust posterior confidence using Bayesian-style heuristic."""
        if evidence.is_supporting:
            self.supporting_evidence.append(evidence)
            # Upward update with diminishing returns
            delta = 0.20 * evidence.weight * (1.0 - self.posterior_confidence)
            self.posterior_confidence = min(0.99, self.posterior_confidence + delta)
        else:
            self.contradicting_evidence.append(evidence)
            # Downward update
            delta = 0.25 * evidence.weight * self.posterior_confidence
            self.posterior_confidence = max(0.01, self.posterior_confidence - delta)

        self.updated_tick = tick
        self._update_status()

    def _update_status(self) -> None:
        """Update epistemic validation status based on accumulated evidence."""
        n_sup = len(self.supporting_evidence)
        n_con = len(self.contradicting_evidence)

        if n_con >= 2 and n_con > n_sup:
            self.status = ValidationStatus.REFUTED
        elif n_con > 0 and n_sup > 0 and abs(n_sup - n_con) <= 1:
            self.status = ValidationStatus.DISPUTED
        elif n_sup >= 3 and self.replications_count >= 1:
            self.status = ValidationStatus.REPLICATED
        elif n_sup >= 1 and n_con == 0:
            self.status = ValidationStatus.SUPPORTED
        elif n_sup == 0 and n_con == 0:
            if self.status not in (ValidationStatus.PROPOSED, ValidationStatus.UNTESTED):
                self.status = ValidationStatus.TESTING


class HypothesisDiscoveryGraph:
    """Repository of community hypotheses, competing theories, and discoveries."""

    def __init__(self) -> None:
        self._hypotheses: dict[str, Hypothesis] = {}
        self._phenomenon_index: dict[str, list[str]] = {}

    def propose_hypothesis(
        self,
        creator_uid: str,
        title: str,
        target_phenomenon: str,
        statement: str,
        assumptions: Optional[list[str]] = None,
        prior_confidence: float = 0.5,
        tick: int = 0,
    ) -> Hypothesis:
        """Propose a new explanatory hypothesis."""
        hid = f"hyp_{uuid4().hex[:8]}"
        hyp = Hypothesis(
            hypothesis_id=hid,
            creator_uid=str(creator_uid),
            title=title,
            target_phenomenon=target_phenomenon,
            statement=statement,
            assumptions=assumptions or [],
            status=ValidationStatus.PROPOSED,
            prior_confidence=prior_confidence,
            posterior_confidence=prior_confidence,
            created_tick=tick,
            updated_tick=tick,
        )
        self._hypotheses[hid] = hyp
        if target_phenomenon not in self._phenomenon_index:
            self._phenomenon_index[target_phenomenon] = []
        self._phenomenon_index[target_phenomenon].append(hid)

        # Mark other hypotheses for the same phenomenon as competing
        for other_id in self._phenomenon_index[target_phenomenon]:
            if other_id != hid:
                self._hypotheses[other_id].competing_hypothesis_ids.append(hid)
                hyp.competing_hypothesis_ids.append(other_id)

        return hyp

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Hypothesis]:
        return self._hypotheses.get(hypothesis_id)

    def get_competing_hypotheses(self, target_phenomenon: str) -> list[Hypothesis]:
        """Fetch all competing theories addressing a phenomenon."""
        hids = self._phenomenon_index.get(target_phenomenon, [])
        return [self._hypotheses[hid] for hid in hids if hid in self._hypotheses]
