"""Scientific Intelligence and Evidence Hierarchy System.

Provides evidence classification (Tiers 1-5), scientific literature metadata retrieval,
and empirical falsification tracking for simulation models.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EvidenceTier(str, Enum):
    """Hierarchy of scientific evidence credibility for simulation modeling."""

    TIER_1_ESTABLISHED = "tier_1_established"  # Peer-reviewed meta-analysis, established empirical law
    TIER_2_LIMITED = "tier_2_limited"  # Peer-reviewed empirical study with domain-specific limitations
    TIER_3_THEORETICAL = "tier_3_theoretical"  # Formal theoretical model without exhaustive empirical validation
    TIER_4_ENGINEERING = "tier_4_engineering"  # Plausible heuristic or computational engineering assumption
    TIER_5_UNVERIFIED = "tier_5_unverified"  # Speculative or unverified simulation implementation


@dataclass
class ScientificSource:
    """Metadata representation of an external scientific study or dataset."""

    source_id: str
    title: str
    authors: list[str]
    year: int
    doi: Optional[str]
    abstract: str
    venue: str
    open_access_url: Optional[str] = None
    evidence_tier: EvidenceTier = EvidenceTier.TIER_2_LIMITED
    methodology: str = ""
    falsification_conditions: list[str] = field(default_factory=list)


@dataclass
class EvidenceAssertion:
    """A claim utilized in the simulation engine accompanied by its evidence provenance."""

    assertion_id: str
    domain: str  # e.g., "epidemiology", "economics", "climatology"
    statement: str
    tier: EvidenceTier
    primary_source_id: Optional[str]
    empirical_support: str
    falsified: bool = False
    falsification_notes: str = ""


class ScientificKnowledgeService:
    """Local-first registry for scientific evidence, literature metadata, and hypothesis validation."""

    def __init__(self) -> None:
        self._sources: dict[str, ScientificSource] = {}
        self._assertions: dict[str, EvidenceAssertion] = {}
        self._initialize_core_foundational_evidence()

    def _initialize_core_foundational_evidence(self) -> None:
        """Seed foundational scientific references supporting SALTBOR mechanisms."""
        # 1. Ostrom CPR
        self.register_source(
            ScientificSource(
                source_id="ostrom_1990",
                title="Governing the Commons: The Evolution of Institutions for Collective Action",
                authors=["Elinor Ostrom"],
                year=1990,
                doi="10.1017/CBO9780511807763",
                abstract="Seminal empirical investigation into enduring self-governed common-pool resources.",
                venue="Cambridge University Press",
                evidence_tier=EvidenceTier.TIER_1_ESTABLISHED,
                methodology="Comparative institutional analysis and empirical field case studies",
                falsification_conditions=[
                    "Common resources without top-down state or private control invariably collapse."
                ],
            )
        )
        self.register_assertion(
            EvidenceAssertion(
                assertion_id="cpr_institutions",
                domain="institutional_economics",
                statement="Communities can self-organize robust CPR institutions via graded sanctions.",
                tier=EvidenceTier.TIER_1_ESTABLISHED,
                primary_source_id="ostrom_1990",
                empirical_support="Verified across 100+ global irrigation and fishery commons.",
            )
        )

        # 2. Granovetter Thresholds
        self.register_source(
            ScientificSource(
                source_id="granovetter_1978",
                title="Threshold Models of Collective Behavior",
                authors=["Mark Granovetter"],
                year=1978,
                doi="10.1086/226707",
                abstract="Mathematical and sociological model of collective action dependent on individual thresholds.",
                venue="American Journal of Sociology",
                evidence_tier=EvidenceTier.TIER_1_ESTABLISHED,
                methodology="Formal sociological modeling and distribution analysis",
                falsification_conditions=[
                    "Collective participation is purely driven by direct average utility rather than distribution of thresholds."
                ],
            )
        )
        self.register_assertion(
            EvidenceAssertion(
                assertion_id="collective_action_thresholds",
                domain="sociology",
                statement="Individual collective mobilization depends on the proportion of peers already acting.",
                tier=EvidenceTier.TIER_1_ESTABLISHED,
                primary_source_id="granovetter_1978",
                empirical_support="Empirically confirmed in riot dynamics, consumer adoption, and strikes.",
            )
        )

        # 3. Two-Step Flow of Media Communication
        self.register_source(
            ScientificSource(
                source_id="katz_lazarsfeld_1955",
                title="Personal Influence: The Part Played by People in the Flow of Mass Communications",
                authors=["Elihu Katz", "Paul F. Lazarsfeld"],
                year=1955,
                doi="10.4324/9781315126234",
                abstract="Information from media flows to opinion leaders and from them to the broader public.",
                venue="Free Press",
                evidence_tier=EvidenceTier.TIER_1_ESTABLISHED,
                methodology="Longitudinal panel survey in Decatur, Illinois",
                falsification_conditions=[
                    "Mass media directly and uniformly transforms attitudes of all audience members equally."
                ],
            )
        )
        self.register_assertion(
            EvidenceAssertion(
                assertion_id="media_two_step_flow",
                domain="media_sociology",
                statement="Media effects are mediated by interpersonal discussion with trusted community members.",
                tier=EvidenceTier.TIER_1_ESTABLISHED,
                primary_source_id="katz_lazarsfeld_1955",
                empirical_support="Replicated across decades of voting and public health diffusion studies.",
            )
        )

    def register_source(self, source: ScientificSource) -> None:
        """Register or update a verified scientific publication."""
        self._sources[source.source_id] = source

    def register_assertion(self, assertion: EvidenceAssertion) -> None:
        """Register an engineering or theoretical assertion used in simulation models."""
        self._assertions[assertion.assertion_id] = assertion

    def get_source(self, source_id: str) -> Optional[ScientificSource]:
        return self._sources.get(source_id)

    def get_assertion(self, assertion_id: str) -> Optional[EvidenceAssertion]:
        return self._assertions.get(assertion_id)

    def list_assertions_by_tier(self, tier: EvidenceTier) -> list[EvidenceAssertion]:
        return [a for a in self._assertions.values() if a.tier == tier]

    def falsify_assertion(self, assertion_id: str, reason: str) -> bool:
        """Mark an assertion as falsified by empirical experiment."""
        assertion = self._assertions.get(assertion_id)
        if not assertion:
            return False
        assertion.falsified = True
        assertion.falsification_notes = reason
        logger.warning("Scientific assertion %s FALSIFIED: %s", assertion_id, reason)
        return True

    def export_evidence_matrix(self) -> list[dict[str, Any]]:
        """Export structured evidence audit for validation reports."""
        records = []
        for a in self._assertions.values():
            src = self._sources.get(a.primary_source_id or "")
            records.append({
                "assertion_id": a.assertion_id,
                "domain": a.domain,
                "statement": a.statement,
                "tier": a.tier.value,
                "falsified": a.falsified,
                "source_title": src.title if src else "Internal Engineering Assumption",
                "source_doi": src.doi if src else None,
            })
        return records
