"""Social Communication and Information Transmission Engine for Saltbor Phase 0.9.

Models varied forms of communication (conversations, teaching, recommendations, warnings,
rumors, stories, negotiations, organizational meetings) across dynamic social networks,
including cognitive distortion, credibility weighting, and propagation dynamics.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
import random
import uuid
from typing import Any, Optional

from saltbor.core.types import HumanID, Tick
from saltbor.social.network.graph_engine import SocialNetworkEngine

logger = logging.getLogger(__name__)


class CommunicationType(str, enum.Enum):
    """Categorization of inter-agent communicative messages."""

    CONVERSATION = "conversation"
    TEACHING = "teaching"
    RECOMMENDATION = "recommendation"
    WARNING = "warning"
    RUMOR = "rumor"
    STORY = "story"
    DEBATE = "debate"
    NEGOTIATION = "negotiation"
    MEETING = "meeting"
    ORGANIZATIONAL = "organizational"


@dataclasses.dataclass
class SocialMessage:
    """A communicative message exchanged between agents."""

    message_id: str
    sender_id: str
    recipient_id: str
    communication_type: CommunicationType
    subject: str
    content: str
    intention: str                 # "inform", "persuade", "warn", "request", "deceive", "reconcile"
    context: dict[str, Any] = dataclasses.field(default_factory=dict)
    tick: int = 0

    # Provenance & Epistemics
    original_source_id: str = ""
    hop_count: int = 0
    confidence_claimed: float = 0.8
    evidence_level: float = 0.5
    distortion_factor: float = 0.0 # Accumulated semantic drift / distortion
    interpretation: Optional[str] = None
    was_believed: bool = True


@dataclasses.dataclass
class PropagationReport:
    """Diagnostic trace of an information diffusion cascade."""

    initial_message_id: str
    subject: str
    initiator_id: str
    total_reached: int
    hops_reached: int
    distortion_history: list[dict[str, Any]]
    believers_count: int
    skeptics_count: int


class SocialCommunicationEngine:
    """Manages communicative exchanges, rumor diffusion, and epistemic distortion."""

    def __init__(self, social_network: Optional[SocialNetworkEngine] = None) -> None:
        self.network = social_network or SocialNetworkEngine()
        self.message_history: list[SocialMessage] = []

    def create_message(
        self,
        sender_id: str | HumanID,
        recipient_id: str | HumanID,
        communication_type: CommunicationType,
        subject: str,
        content: str,
        intention: str = "inform",
        confidence_claimed: float = 0.8,
        evidence_level: float = 0.6,
        tick: int = 0,
        original_source_id: Optional[str] = None,
        hop_count: int = 0,
        distortion_factor: float = 0.0,
    ) -> SocialMessage:
        """Create a new communicative message."""
        s = str(sender_id)
        r = str(recipient_id)
        msg = SocialMessage(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            sender_id=s,
            recipient_id=r,
            communication_type=communication_type,
            subject=subject,
            content=content,
            intention=intention,
            tick=tick,
            original_source_id=original_source_id or s,
            hop_count=hop_count,
            confidence_claimed=confidence_claimed,
            evidence_level=evidence_level,
            distortion_factor=distortion_factor,
        )
        return msg

    def transmit_message(
        self,
        message: SocialMessage,
        recipient_skepticism: float = 0.3, # [0.0, 1.0] from personality conscientiousness / neuroticism
        recipient_experience: Optional[dict[str, Any]] = None,
    ) -> SocialMessage:
        """Deliver message to recipient, evaluating credibility, distortion, and belief."""
        # 1. Check direct edge trust from recipient to sender
        edge = self.network.get_edge(message.recipient_id, message.sender_id)
        rel_trust = edge.trust if edge else 0.45

        # Credibility = claimed confidence * trust * (1 - skepticism)
        credibility = message.confidence_claimed * rel_trust * (1.0 - 0.4 * recipient_skepticism)

        # 2. Check contradictory experience
        if recipient_experience and message.subject in recipient_experience:
            known_truth = recipient_experience[message.subject]
            if known_truth != message.content:
                credibility *= 0.3  # Slashes credibility if clashes with direct empirical experience

        message.was_believed = credibility >= 0.30

        # Recipient interprets message
        if message.was_believed:
            message.interpretation = f"Accepted as plausible: {message.content}"
        else:
            message.interpretation = f"Doubts claim from {message.sender_id} (credibility={credibility:.2f})"

        self.message_history.append(message)
        return message

    def distort_content(
        self,
        original_content: str,
        distortion_factor: float,
        distortion_type: str = "exaggeration",
    ) -> str:
        """Simulate realistic semantic mutation (rumor exaggeration / omission of caveats)."""
        if distortion_factor < 0.15:
            return original_content

        if "precio" in original_content.lower() or "costo" in original_content.lower():
            return original_content + " (dicen que se duplicara o habra escasez total)"
        elif "conflicto" in original_content.lower() or "pelea" in original_content.lower():
            return original_content + " (aseguran que hubo traicion grave)"
        elif "cosecha" in original_content.lower() or "granos" in original_content.lower():
            return original_content + " (se rumora perdida total por plaga)"
        elif "innovacion" in original_content.lower() or "metodo" in original_content.lower():
            return original_content + " (garantizan resultados milagrosos sin esfuerzo)"
        else:
            return original_content + f" [distorsionado nivel {distortion_factor:.1f}]"

    def propagate_cascade(
        self,
        initiator_id: str,
        communication_type: CommunicationType,
        subject: str,
        initial_content: str,
        max_hops: int = 4,
        distortion_rate_per_hop: float = 0.20,
        tick: int = 0,
    ) -> PropagationReport:
        """Simulate multi-hop information/rumor spreading through social graph."""
        visited: set[str] = {initiator_id}
        current_layer: list[tuple[str, str, float]] = [(initiator_id, initial_content, 0.0)]
        believers = 1
        skeptics = 0
        distortion_history: list[dict[str, Any]] = [
            {"hop": 0, "uid": initiator_id, "content": initial_content, "distortion": 0.0}
        ]
        hops_reached = 0

        for hop in range(1, max_hops + 1):
            next_layer: list[tuple[str, str, float]] = []
            if not current_layer:
                break

            for sender_uid, content_carried, cur_dist in current_layer:
                # Find neighbors with trust > 0.3
                neighbors = self.network.get_neighbors(sender_uid, min_trust=0.3, active_only=True)
                for nbr in neighbors:
                    if nbr not in visited:
                        visited.add(nbr)
                        # Distort message for next hop if it's a rumor or informal conversation
                        is_rumor = communication_type in (CommunicationType.RUMOR, CommunicationType.CONVERSATION)
                        next_dist = cur_dist + (distortion_rate_per_hop if is_rumor else 0.02)
                        distorted = self.distort_content(content_carried, next_dist) if is_rumor else content_carried

                        msg = self.create_message(
                            sender_id=sender_uid,
                            recipient_id=nbr,
                            communication_type=communication_type,
                            subject=subject,
                            content=distorted,
                            tick=tick + hop,
                            original_source_id=initiator_id,
                            hop_count=hop,
                            distortion_factor=next_dist,
                        )
                        res = self.transmit_message(msg)
                        if res.was_believed:
                            believers += 1
                            next_layer.append((nbr, distorted, next_dist))
                        else:
                            skeptics += 1

                        distortion_history.append({
                            "hop": hop,
                            "uid": nbr,
                            "content": distorted,
                            "distortion": round(next_dist, 3),
                            "believed": res.was_believed,
                        })

            if next_layer:
                hops_reached = hop
            current_layer = next_layer

        report = PropagationReport(
            initial_message_id=f"cascade_{uuid.uuid4().hex[:6]}",
            subject=subject,
            initiator_id=initiator_id,
            total_reached=len(visited) - 1,
            hops_reached=hops_reached,
            distortion_history=distortion_history,
            believers_count=believers,
            skeptics_count=skeptics,
        )
        return report
