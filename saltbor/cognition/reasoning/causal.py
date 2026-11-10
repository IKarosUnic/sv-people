"""Advanced Causal Reasoning Engine for Saltbor Phase 0.7 (Section 2.4).

Rigorous causal inference that strictly distinguishes:
1. Spurious correlation (mere temporal co-occurrence without direct mechanism).
2. Hypothetical causality (provisional causal hypothesis).
3. Evidence-backed causality (supported by interventions or empirical trials).
4. Confounding variables (common causes producing apparent correlations).
5. Direct vs. indirect multi-hop consequences.

Prevents assuming causality merely because two phenomena co-occur.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from saltbor.knowledge.graph.relationship import KnowledgeRelationship, RelationshipType
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


class CausalRelationStatus(str, Enum):
    """Epistemic status of an asserted causal dependency."""

    CORRELATION_ONLY = "correlation_only"
    HYPOTHETICAL_CAUSALITY = "hypothetical_causality"
    EVIDENCE_BACKED = "evidence_backed"
    CONFOUNDED = "confounded"


@dataclasses.dataclass
class CausalLink:
    """A single directed link between a cause and an effect."""

    cause_id: str
    effect_id: str
    status: CausalRelationStatus
    confidence: float                   # Epistemic certainty
    strength: float                     # Effect size [0.0, 1.0]
    mechanism_description: str
    confounding_variable: Optional[str] = None
    interventions_tested: int = 0
    is_direct: bool = True

    def validate_with_intervention(self, effect_observed: bool) -> None:
        """Update link upon performing a direct intervention on cause."""
        self.interventions_tested += 1
        if effect_observed:
            if self.status != CausalRelationStatus.CONFOUNDED:
                self.status = CausalRelationStatus.EVIDENCE_BACKED
                self.confidence = min(0.95, self.confidence + 0.20)
        else:
            self.status = CausalRelationStatus.CORRELATION_ONLY
            self.confidence = max(0.1, self.confidence - 0.30)


@dataclasses.dataclass
class CausalInferencePath:
    """A multi-hop causal chain distinguishing direct from indirect impacts."""

    root_cause_id: str
    target_effect_id: str
    links: list[CausalLink]
    aggregate_confidence: float
    aggregate_strength: float
    is_purely_causal: bool              # True only if all links are evidence-backed or hypothetical (no pure correlations)
    has_confounders: bool

    @property
    def hop_count(self) -> int:
        return len(self.links)

    @property
    def is_direct(self) -> bool:
        return len(self.links) == 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_cause": self.root_cause_id,
            "target_effect": self.target_effect_id,
            "hops": self.hop_count,
            "is_direct": self.is_direct,
            "is_purely_causal": self.is_purely_causal,
            "has_confounders": self.has_confounders,
            "aggregate_confidence": round(self.aggregate_confidence, 3),
            "aggregate_strength": round(self.aggregate_strength, 3),
            "path_links": [
                {
                    "cause": l.cause_id,
                    "effect": l.effect_id,
                    "status": l.status.value,
                    "conf": round(l.confidence, 3),
                    "confounder": l.confounding_variable,
                }
                for l in self.links
            ],
        }


class AdvancedCausalReasoningEngine:
    """Manages causal models, disentangles correlations from causation, and detects confounders."""

    def __init__(self) -> None:
        # Known causal structure: (cause, effect) -> CausalLink
        self._links: dict[tuple[str, str], CausalLink] = {}

    def register_link(self, link: CausalLink) -> None:
        self._links[(link.cause_id, link.effect_id)] = link

    def identify_confounder(
        self,
        var_x: str,
        var_y: str,
    ) -> Optional[str]:
        """Detect if an apparent association between X and Y is caused by a common parent Z.

        Checks if exists Z such that Z -> X and Z -> Y.
        """
        for (cause, effect), link in self._links.items():
            if effect == var_x and link.status in (CausalRelationStatus.EVIDENCE_BACKED, CausalRelationStatus.HYPOTHETICAL_CAUSALITY):
                parent_z = cause
                # Check if Z also causes Y
                if (parent_z, var_y) in self._links:
                    z_to_y = self._links[(parent_z, var_y)]
                    if z_to_y.status in (CausalRelationStatus.EVIDENCE_BACKED, CausalRelationStatus.HYPOTHETICAL_CAUSALITY):
                        return parent_z
        return None

    def evaluate_causality_vs_correlation(
        self,
        event_a: str,
        event_b: str,
        co_occurrence_count: int,
        independent_trials: int = 10,
    ) -> CausalLink:
        """Strictly evaluate whether A causes B or if it's mere correlation or confounded.

        Does NOT assume causality solely from co-occurrence.
        """
        # 1. Check for confounding variable
        confounder = self.identify_confounder(event_a, event_b)
        if confounder:
            link = CausalLink(
                cause_id=event_a,
                effect_id=event_b,
                status=CausalRelationStatus.CONFOUNDED,
                confidence=0.30,
                strength=0.20,
                mechanism_description=f"Spurious correlation: Both '{event_a}' and '{event_b}' are driven by common cause '{confounder}'",
                confounding_variable=confounder,
            )
            self.register_link(link)
            return link

        # 2. Check existing link
        key = (event_a, event_b)
        if key in self._links:
            return self._links[key]

        # 3. If only observed together without verified intervention or known mechanism:
        if co_occurrence_count > 0:
            link = CausalLink(
                cause_id=event_a,
                effect_id=event_b,
                status=CausalRelationStatus.CORRELATION_ONLY,
                confidence=0.40,
                strength=0.50,
                mechanism_description=f"Observed co-occurring {co_occurrence_count} times; mechanism unverified",
            )
        else:
            link = CausalLink(
                cause_id=event_a,
                effect_id=event_b,
                status=CausalRelationStatus.HYPOTHETICAL_CAUSALITY,
                confidence=0.25,
                strength=0.40,
                mechanism_description="Theoretical hypothesis pending empirical validation",
            )

        self.register_link(link)
        return link

    def trace_impacts(
        self,
        root_cause_id: str,
        max_hops: int = 4,
    ) -> list[CausalInferencePath]:
        """Trace forward downstream direct and indirect consequences from a root cause."""
        paths: list[CausalInferencePath] = []

        def _dfs(curr: str, current_links: list[CausalLink], visited: set[str]) -> None:
            if len(current_links) >= max_hops:
                return

            # Find all outgoing links from curr
            for (c, e), link in self._links.items():
                if c == curr and e not in visited:
                    new_links = current_links + [link]
                    agg_conf = 1.0
                    agg_str = 1.0
                    pure_causal = True
                    has_confounders = False

                    for l in new_links:
                        agg_conf *= l.confidence
                        agg_str *= l.strength
                        if l.status == CausalRelationStatus.CORRELATION_ONLY:
                            pure_causal = False
                        if l.status == CausalRelationStatus.CONFOUNDED:
                            has_confounders = True

                    paths.append(
                        CausalInferencePath(
                            root_cause_id=root_cause_id,
                            target_effect_id=e,
                            links=new_links,
                            aggregate_confidence=agg_conf,
                            aggregate_strength=agg_str,
                            is_purely_causal=pure_causal,
                            has_confounders=has_confounders,
                        )
                    )

                    visited.add(e)
                    _dfs(e, new_links, visited)
                    visited.remove(e)

        _dfs(root_cause_id, [], {root_cause_id})
        paths.sort(key=lambda p: (p.is_purely_causal, p.aggregate_confidence), reverse=True)
        return paths
