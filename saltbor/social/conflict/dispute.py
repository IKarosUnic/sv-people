"""Collective conflict, dispute escalation, negotiation, and mediation."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

import numpy as np

from saltbor.core.types import HumanID, Tick

if TYPE_CHECKING:
    from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


class DisputeCause(enum.Enum):
    """Identifiable causal genesis of an interpersonal or collective dispute."""

    RESOURCE_SCARCITY = "resource_scarcity"    # Food or material shortage competition
    DEBT_DEFAULT = "debt_default"              # Unpaid financial obligation
    WAGE_DISPUTE = "wage_dispute"              # Missed or reduced labor compensation
    BROKEN_AGREEMENT = "broken_agreement"      # Failure to perform contracted duty
    PROPERTY_ENCROACHMENT = "property_encroachment" # Spatial boundary friction
    LEADERSHIP_CHALLENGE = "leadership_challenge" # Rivalry for institutional authority


class DisputeStage(enum.Enum):
    """Escalation progression of a conflict."""

    GRIEVANCE = "grievance"        # Latent tension or verbal complaint
    NEGOTIATION = "negotiation"    # Direct discussion between parties
    ESCALATION = "escalation"      # Open hostility, faction building, or public protest
    MEDIATION = "mediation"        # Third-party intervention (elder/assembly)
    RESOLVED = "resolved"          # Mutually acceptable settlement reached
    FRACTURED = "fractured"        # Permanent breakdown or social estrangement


@dataclass
class Dispute:
    """A tracked conflict between individuals or collective factions."""

    dispute_id: str
    cause: DisputeCause
    description: str
    initiator_uid: HumanID
    respondent_uid: HumanID
    created_tick: Tick

    stage: DisputeStage = DisputeStage.GRIEVANCE
    initiator_allies: set[HumanID] = field(default_factory=set)
    respondent_allies: set[HumanID] = field(default_factory=set)
    mediator_uid: Optional[HumanID] = None

    intensity: float = 0.5           # 0.0 (mild disagreement) to 1.0 (severe crisis)
    resolution_summary: str = ""
    resolved_tick: Optional[Tick] = None

    def escalate(self, tick: Tick, additional_allies: Optional[list[HumanID]] = None) -> None:
        """Escalate to public factional dispute."""
        self.stage = DisputeStage.ESCALATION
        self.intensity = min(1.0, self.intensity + 0.25)
        if additional_allies:
            self.initiator_allies.update(additional_allies)
        logger.warning("Dispute %s ESCALATED to open confrontation (intensity: %.2f)", self.dispute_id, self.intensity)

    def attempt_negotiation(
        self,
        initiator: SyntheticHuman,
        respondent: SyntheticHuman,
        tick: Tick,
        concession_offered: bool = True,
    ) -> bool:
        """Attempt direct bilateral negotiation between parties."""
        self.stage = DisputeStage.NEGOTIATION
        # Agreeableness and patience promote compromise
        init_agree = initiator.personality.traits.get_trait_value("agreeableness") if initiator.personality else 0.5
        resp_agree = respondent.personality.traits.get_trait_value("agreeableness") if respondent.personality else 0.5

        compromise_score = (init_agree + resp_agree) / 2.0 + (0.2 if concession_offered else -0.1)
        if compromise_score >= 0.55:
            self.stage = DisputeStage.RESOLVED
            self.resolved_tick = tick
            self.resolution_summary = "Resolved peacefully through bilateral compromise and restitution."
            logger.info("Dispute %s RESOLVED via negotiation.", self.dispute_id)
            return True
        else:
            self.escalate(tick)
            return False

    def mediate_by_third_party(
        self,
        mediator: SyntheticHuman,
        tick: Tick,
        mediator_respect: float = 0.7,
    ) -> bool:
        """Third-party respected elder or assembly leader steps in to arbitrate."""
        self.stage = DisputeStage.MEDIATION
        self.mediator_uid = mediator.uid

        if mediator_respect >= 0.60:
            self.stage = DisputeStage.RESOLVED
            self.resolved_tick = tick
            self.resolution_summary = f"Arbitrated and settled under mediation by respected leader {mediator.name}."
            logger.info("Dispute %s RESOLVED via third-party mediation by %s.", self.dispute_id, mediator.name)
            return True
        else:
            self.stage = DisputeStage.FRACTURED
            self.resolution_summary = "Mediation failed; parties remain in active schism."
            logger.warning("Dispute %s FRACTURED: mediation was unsuccessful.", self.dispute_id)
            return False


class CollectiveConflictManager:
    """Detects, tracks, and manages community disputes and collective protests."""

    def __init__(self) -> None:
        self.disputes: dict[str, Dispute] = {}

    def initiate_dispute(
        self,
        dispute_id: str,
        cause: DisputeCause,
        description: str,
        initiator_uid: HumanID,
        respondent_uid: HumanID,
        current_tick: Tick,
        initial_intensity: float = 0.5,
    ) -> Dispute:
        disp = Dispute(
            dispute_id=dispute_id,
            cause=cause,
            description=description,
            initiator_uid=initiator_uid,
            respondent_uid=respondent_uid,
            created_tick=current_tick,
            intensity=initial_intensity,
        )
        self.disputes[dispute_id] = disp
        logger.info("New dispute logged: %s (%s)", description, cause.value)
        return disp

    def get_active_disputes(self) -> list[Dispute]:
        return [
            d for d in self.disputes.values()
            if d.stage not in (DisputeStage.RESOLVED, DisputeStage.FRACTURED)
        ]
