"""Conflict, Negotiation, and Cooperation Engine for Saltbor Phase 0.9.

Models interpersonal disputes, resource competition, organizational factionalism,
multi-stage negotiation, neutral mediation, compromise pacts, and persistent grudges.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
import uuid
from typing import Any, Optional

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class ConflictDomain(str, enum.Enum):
    """Origin of social conflict."""

    PERSONAL_AFFRONT = "personal_affront"
    COMMERCIAL_DISPUTE = "commercial_dispute"
    RESOURCE_COMPETITION = "resource_competition"
    COMMUNITY_DISAGREEMENT = "community_disagreement"
    LABOR_FRICTION = "labor_friction"
    ORGANIZATIONAL_POWER = "organizational_power"
    INTERGROUP_RIVALRY = "intergroup_rivalry"


class ConflictStage(str, enum.Enum):
    """Progression stages of a dispute."""

    LATENT = "latent"
    EMERGED = "emerged"
    ESCALATED = "escalated"
    NEGOTIATING = "negotiating"
    MEDIATING = "mediating"
    RESOLVED = "resolved"
    ENTRENCHED = "entrenched"


@dataclasses.dataclass
class NegotiationOffer:
    """An offer proposed during dispute negotiation."""

    offer_id: str
    proposer_uid: str
    recipient_uid: str
    concession_summary: str
    compensation_value: float = 0.0
    demanded_action: str = ""
    is_accepted: Optional[bool] = None


@dataclasses.dataclass
class SocialDispute:
    """A tracked dispute between individuals or collective factions."""

    dispute_id: str
    domain: ConflictDomain
    initiator_uid: str
    respondent_uid: str
    cause_description: str
    intensity: float = 0.5           # [0.0, 1.0]
    stage: ConflictStage = ConflictStage.EMERGED
    mediator_uid: Optional[str] = None
    created_tick: int = 0
    resolved_tick: Optional[int] = None
    offers: list[NegotiationOffer] = dataclasses.field(default_factory=list)
    resolution_summary: str = ""
    is_persistent: bool = False

    def escalate(self, boost: float = 0.2) -> None:
        """Escalate dispute severity."""
        self.intensity = min(1.0, self.intensity + boost)
        if self.intensity >= 0.75:
            self.stage = ConflictStage.ESCALATED

    def de_escalate(self, reduction: float = 0.25) -> None:
        """Cool down dispute friction."""
        self.intensity = max(0.0, self.intensity - reduction)
        if self.intensity <= 0.30 and self.stage == ConflictStage.ESCALATED:
            self.stage = ConflictStage.NEGOTIATING


class ConflictCooperationEngine:
    """Manages conflict emergence, negotiation, mediation, and pact formation."""

    def __init__(self) -> None:
        self._disputes: dict[str, SocialDispute] = {}

    def get_dispute(self, dispute_id: str) -> Optional[SocialDispute]:
        return self._disputes.get(dispute_id)

    def get_disputes_for_human(self, human_uid: str | HumanID) -> list[SocialDispute]:
        uid = str(human_uid)
        return [
            d for d in self._disputes.values()
            if d.initiator_uid == uid or d.respondent_uid == uid or d.mediator_uid == uid
        ]

    def initiate_dispute(
        self,
        initiator_uid: str | HumanID,
        respondent_uid: str | HumanID,
        domain: ConflictDomain,
        cause_description: str,
        initial_intensity: float = 0.5,
        tick: int = 0,
    ) -> SocialDispute:
        """Trigger an interpersonal or commercial conflict."""
        dispute_id = f"disp_{domain.value[:4]}_{uuid.uuid4().hex[:6]}"
        disp = SocialDispute(
            dispute_id=dispute_id,
            domain=domain,
            initiator_uid=str(initiator_uid),
            respondent_uid=str(respondent_uid),
            cause_description=cause_description,
            intensity=initial_intensity,
            stage=ConflictStage.EMERGED,
            created_tick=tick,
        )
        self._disputes[dispute_id] = disp
        logger.info("Dispute '%s' emerged between %s and %s: %s", dispute_id, initiator_uid, respondent_uid, cause_description)
        return disp

    def propose_offer(
        self,
        dispute_id: str,
        proposer_uid: str | HumanID,
        concession_summary: str,
        compensation_value: float = 0.0,
        demanded_action: str = "",
    ) -> Optional[NegotiationOffer]:
        """Submit a formal negotiation proposal."""
        disp = self.get_dispute(dispute_id)
        if not disp:
            return None

        p_uid = str(proposer_uid)
        recipient_uid = disp.respondent_uid if p_uid == disp.initiator_uid else disp.initiator_uid
        offer = NegotiationOffer(
            offer_id=f"off_{uuid.uuid4().hex[:6]}",
            proposer_uid=p_uid,
            recipient_uid=recipient_uid,
            concession_summary=concession_summary,
            compensation_value=compensation_value,
            demanded_action=demanded_action,
        )
        disp.offers.append(offer)
        disp.stage = ConflictStage.NEGOTIATING
        return offer

    def respond_to_offer(
        self,
        dispute_id: str,
        offer_id: str,
        accept: bool,
        tick: int = 0,
    ) -> bool:
        """Accept or reject a negotiation offer."""
        disp = self.get_dispute(dispute_id)
        if not disp:
            return False

        offer = next((o for o in disp.offers if o.offer_id == offer_id), None)
        if not offer:
            return False

        offer.is_accepted = accept
        if accept:
            disp.stage = ConflictStage.RESOLVED
            disp.resolved_tick = tick
            disp.resolution_summary = f"Resolved via offer: {offer.concession_summary} (${offer.compensation_value:.2f})"
            disp.intensity = 0.0
            return True
        else:
            disp.escalate(0.15)
            # If multiple failed attempts, may become entrenched
            rejected_count = sum(1 for o in disp.offers if o.is_accepted is False)
            if rejected_count >= 3:
                disp.stage = ConflictStage.ENTRENCHED
                disp.is_persistent = True
            return False

    def assign_mediator(
        self,
        dispute_id: str,
        mediator_uid: str | HumanID,
    ) -> bool:
        """Introduce an accepted elder or neutral mediator."""
        disp = self.get_dispute(dispute_id)
        if not disp:
            return False

        disp.mediator_uid = str(mediator_uid)
        disp.stage = ConflictStage.MEDIATING
        disp.de_escalate(0.20)
        return True

    def mediate_compromise(
        self,
        dispute_id: str,
        compromise_terms: str,
        tick: int = 0,
    ) -> bool:
        """Mediator orchestrates a compromise agreement."""
        disp = self.get_dispute(dispute_id)
        if not disp or not disp.mediator_uid:
            return False

        disp.stage = ConflictStage.RESOLVED
        disp.resolved_tick = tick
        disp.resolution_summary = f"Mediated compromise by {disp.mediator_uid}: {compromise_terms}"
        disp.intensity = 0.10
        return True
