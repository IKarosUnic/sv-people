"""Multi-Contextual Reputation and Social Influence Engine for Saltbor Phase 0.9.

Reputation is situated, multidimensional, and non-omniscient. Tracks personal,
professional, and communal dimensions derived from direct experience and peer testimonials.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Any, Optional

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class ReputationDomain(str, enum.Enum):
    """Contextual spheres of reputation."""

    PERSONAL = "personal"         # Warmth, reliability, kindness among friends
    PROFESSIONAL = "professional" # Craft competence, quality, punctuality, commercial honesty
    COMMUNAL = "communal"         # Contribution to collective projects, solidarity, norm compliance


@dataclasses.dataclass
class ContextualReputationRecord:
    """Reputation evaluation of an individual within a specific sphere or community."""

    subject_uid: str
    observer_uid: Optional[str] = None # None means community consensus view
    domain: ReputationDomain = ReputationDomain.COMMUNAL
    community_id: Optional[str] = None

    score: float = 0.5           # [0.0, 1.0]
    confidence: float = 0.5      # [0.0, 1.0] based on direct interactions vs hearsay
    fulfilled_agreements: int = 0
    violated_agreements: int = 0
    cooperation_count: int = 0
    conflict_count: int = 0
    testimonials_count: int = 0
    last_updated_tick: int = 0

    def record_experience(
        self,
        event_type: str,
        success: bool,
        magnitude: float = 0.5,
        tick: int = 0,
    ) -> None:
        """Update reputation based on an empirical interaction."""
        self.last_updated_tick = tick
        delta = magnitude * 0.15

        if event_type == "agreement":
            if success:
                self.fulfilled_agreements += 1
                self.score = min(1.0, self.score + delta)
            else:
                self.violated_agreements += 1
                self.score = max(0.0, self.score - delta * 2.2) # Asymmetric penalty for breach of trust
        elif event_type == "cooperation":
            if success:
                self.cooperation_count += 1
                self.score = min(1.0, self.score + delta * 1.1)
            else:
                self.conflict_count += 1
                self.score = max(0.0, self.score - delta * 1.3)
        elif event_type == "conflict":
            self.conflict_count += 1
            self.score = max(0.0, self.score - delta * 1.8)

        # Experience increases evaluator confidence
        self.confidence = min(1.0, self.confidence + 0.10)

    def incorporate_testimonial(
        self,
        reported_score: float,
        source_trust: float,
        tick: int = 0,
    ) -> None:
        """Update reputation through word-of-mouth hearsay weighted by source trust."""
        self.testimonials_count += 1
        self.last_updated_tick = tick

        weight = max(0.05, min(0.40, source_trust * 0.35))
        # Nudge existing score toward reported assessment
        self.score = round((1.0 - weight) * self.score + weight * reported_score, 4)
        self.confidence = min(1.0, self.confidence + weight * 0.5)


class ReputationEngine:
    """Manages situated, multi-domain, non-omniscient reputations across society."""

    def __init__(self) -> None:
        # Key: (subject_uid, observer_uid, domain, community_id) -> ContextualReputationRecord
        self._records: dict[tuple[str, Optional[str], str, Optional[str]], ContextualReputationRecord] = {}

    def get_or_create(
        self,
        subject_uid: str | HumanID,
        observer_uid: Optional[str | HumanID] = None,
        domain: ReputationDomain = ReputationDomain.COMMUNAL,
        community_id: Optional[str] = None,
        initial_score: float = 0.5,
    ) -> ContextualReputationRecord:
        """Fetch or initialize a situated reputation profile."""
        s = str(subject_uid)
        o = str(observer_uid) if observer_uid else None
        key = (s, o, domain.value, community_id)

        if key not in self._records:
            self._records[key] = ContextualReputationRecord(
                subject_uid=s,
                observer_uid=o,
                domain=domain,
                community_id=community_id,
                score=initial_score,
                confidence=0.3 if o is not None else 0.5,
            )
        return self._records[key]

    def record_pact_outcome(
        self,
        subject_uid: str | HumanID,
        observer_uid: str | HumanID,
        fulfilled: bool,
        domain: ReputationDomain = ReputationDomain.PROFESSIONAL,
        community_id: Optional[str] = None,
        tick: int = 0,
    ) -> ContextualReputationRecord:
        """Record agreement fulfillment or breach."""
        rec = self.get_or_create(subject_uid, observer_uid, domain, community_id)
        rec.record_experience("agreement", success=fulfilled, magnitude=0.7, tick=tick)

        # Also update community-wide aggregate view
        comm_rec = self.get_or_create(subject_uid, None, domain, community_id)
        comm_rec.record_experience("agreement", success=fulfilled, magnitude=0.3, tick=tick)
        return rec

    def record_cooperation_effort(
        self,
        subject_uid: str | HumanID,
        observer_uid: str | HumanID,
        cooperated: bool,
        domain: ReputationDomain = ReputationDomain.COMMUNAL,
        community_id: Optional[str] = None,
        tick: int = 0,
    ) -> ContextualReputationRecord:
        """Record participation in communal or cooperative endeavors."""
        rec = self.get_or_create(subject_uid, observer_uid, domain, community_id)
        rec.record_experience("cooperation", success=cooperated, magnitude=0.5, tick=tick)

        comm_rec = self.get_or_create(subject_uid, None, domain, community_id)
        comm_rec.record_experience("cooperation", success=cooperated, magnitude=0.25, tick=tick)
        return rec

    def transmit_testimonial(
        self,
        subject_uid: str | HumanID,
        teller_uid: str | HumanID,
        listener_uid: str | HumanID,
        domain: ReputationDomain = ReputationDomain.PROFESSIONAL,
        trust_in_teller: float = 0.7,
        community_id: Optional[str] = None,
        tick: int = 0,
    ) -> ContextualReputationRecord:
        """Teller shares their evaluation of subject with listener."""
        teller_rec = self.get_or_create(subject_uid, teller_uid, domain, community_id)
        listener_rec = self.get_or_create(subject_uid, listener_uid, domain, community_id)

        listener_rec.incorporate_testimonial(
            reported_score=teller_rec.score,
            source_trust=trust_in_teller,
            tick=tick,
        )
        return listener_rec

    def get_social_influence(
        self,
        subject_uid: str | HumanID,
        domain: ReputationDomain = ReputationDomain.COMMUNAL,
        community_id: Optional[str] = None,
    ) -> float:
        """Compute emergent social influence in a given context."""
        comm_rec = self.get_or_create(subject_uid, None, domain, community_id)
        # Influence = reputation * confidence * agreement reliability
        base = comm_rec.score * comm_rec.confidence
        if comm_rec.violated_agreements > 0:
            breach_ratio = comm_rec.violated_agreements / max(1, comm_rec.fulfilled_agreements + comm_rec.violated_agreements)
            base *= max(0.2, 1.0 - breach_ratio)
        return round(base, 4)
