"""Everyday Social Life, Leisure Invitations and Relational Dynamics (Phase 1.5).

Models authentic everyday social agency:
- Social invitations to dine out, visit the park, attend events, or play sports.
- Autonomous invitation evaluation: an invitation does NOT guarantee acceptance.
- Factors evaluated: interpersonal trust, relationship quality, physical exhaustion, financial constraints,
  personality traits (extraversion vs preference for solitude), and competing obligations.
- Mutual leisure activities: strengthen interpersonal affection, build shared memories, and alleviate stress.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Any, Dict, List, Optional
import uuid

from saltbor.core.types import ActivityType, HumanID, LocationID, Tick

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class SocialInvitation:
    """An invitation extended from one individual to another to share an activity."""
    invitation_id: str
    inviter_uid: str
    invitee_uid: str
    activity_type: ActivityType
    location_id: LocationID
    offered_treat: bool = False          # Inviter offers to cover costs (e.g. pay for dinner)
    status: str = "pending"              # "pending", "accepted", "rejected"
    rejection_reason: str = ""
    tick_sent: Tick = 0
    tick_resolved: Optional[Tick] = None


class EverydaySocialEngine:
    """Manages everyday leisure activities, invitations, and relational companionship."""

    def __init__(self) -> None:
        self.invitations_history: list[SocialInvitation] = []
        self.shared_leisure_sessions: list[dict[str, Any]] = []

    def send_invitation(
        self,
        inviter: Any,
        invitee: Any,
        activity_type: ActivityType,
        location_id: LocationID,
        offered_treat: bool = False,
        current_tick: Tick = 0,
    ) -> SocialInvitation:
        """Create and transmit a social invitation."""
        inv_id = f"inv_{uuid.uuid4().hex[:8]}"
        invitation = SocialInvitation(
            invitation_id=inv_id,
            inviter_uid=str(inviter.uid),
            invitee_uid=str(invitee.uid),
            activity_type=activity_type,
            location_id=location_id,
            offered_treat=offered_treat,
            tick_sent=current_tick,
        )
        self.invitations_history.append(invitation)
        logger.info(
            "%s invited %s to %s at %s (treat=%s)",
            inviter.name, invitee.name, activity_type.value, location_id, offered_treat
        )
        return invitation

    def evaluate_invitation(
        self,
        invitee: Any,
        invitation: SocialInvitation,
        social_engine: Any,
        current_tick: Tick = 0,
    ) -> tuple[bool, str]:
        """Invitee autonomously decides whether to accept or decline the invitation.
        
        An invitation does not guarantee participation:
        - Exhausted agents decline to rest.
        - Cash-strapped agents decline paid outings (unless treated).
        - Low trust or rival relationships decline.
        - High extraversion or affection increases acceptance probability.
        """
        # 1. Vital Need Check (Physical exhaustion)
        energy = getattr(invitee.physical_state, "energy", 0.5)
        if energy < 0.20:
            reason = "Demasiado exhausto/a; necesita descansar en casa."
            invitation.status = "rejected"
            invitation.rejection_reason = reason
            invitation.tick_resolved = current_tick
            return False, reason

        # 2. Financial Constraint Check (Dining / entertainment costs)
        money = getattr(invitee.physical_state, "money", 0.0)
        is_costly = invitation.activity_type in (
            ActivityType.DINE_OUT,
            ActivityType.SEEK_ENTERTAINMENT,
            ActivityType.PURCHASE_GOODS,
        )
        if is_costly and not invitation.offered_treat and money < 2.50:
            reason = "Presupuesto insuficiente para gastar en salidas hoy."
            invitation.status = "rejected"
            invitation.rejection_reason = reason
            invitation.tick_resolved = current_tick
            return False, reason

        # 3. Interpersonal Relationship & Trust Check
        inviter_uid_obj = uuid.UUID(invitation.inviter_uid)
        rel = social_engine.get_relationship(invitee.uid, inviter_uid_obj) if social_engine else None
        trust = rel.trust if rel else 0.50
        affinity = rel.affinity if rel else 0.50

        if trust < 0.25:
            reason = "Desconfianza o relación distante con la persona que invita."
            invitation.status = "rejected"
            invitation.rejection_reason = reason
            invitation.tick_resolved = current_tick
            return False, reason

        # 4. Personality & Preference Evaluation
        personality = getattr(invitee, "personality", None)
        extraversion = personality.get_trait("extraversion") if personality else 0.5
        agreeableness = personality.get_trait("agreeableness") if personality else 0.5

        # Social utility score
        utility = (trust * 0.35) + (affinity * 0.25) + (extraversion * 0.20) + (agreeableness * 0.20)
        if invitation.offered_treat:
            utility += 0.15

        if utility >= 0.40:
            invitation.status = "accepted"
            invitation.tick_resolved = current_tick
            reason = f"Aceptó con entusiasmo la invitación a {invitation.activity_type.value}."
            return True, reason
        else:
            reason = "Prefiere quedarse a atender asuntos personales o descansar a solas."
            invitation.status = "rejected"
            invitation.rejection_reason = reason
            invitation.tick_resolved = current_tick
            return False, reason

    def execute_shared_activity(
        self,
        inviter: Any,
        invitee: Any,
        invitation: SocialInvitation,
        social_engine: Any,
        current_tick: Tick = 0,
    ) -> dict[str, Any]:
        """Execute the joint leisure activity, updating relationships and satisfaction."""
        if invitation.status != "accepted":
            return {"executed": False, "reason": "Invitation was not accepted"}

        # Boost social need & emotional mood
        for agent in (inviter, invitee):
            agent.physical_state.energy = max(0.05, agent.physical_state.energy - 0.05)
            if hasattr(agent.emotions, "adjust_mood"):
                agent.emotions.adjust_mood(+0.15)

        # Strengthen relationship
        inviter_uid = uuid.UUID(invitation.inviter_uid)
        invitee_uid = uuid.UUID(invitation.invitee_uid)
        if social_engine:
            social_engine.record_interaction(
                source_id=inviter_uid,
                target_id=invitee_uid,
                tick=current_tick,
                positive=True,
                intensity=0.35,
                interaction_type=invitation.activity_type.value,
            )

        session_record = {
            "inviter_uid": invitation.inviter_uid,
            "invitee_uid": invitation.invitee_uid,
            "activity": invitation.activity_type.value,
            "location_id": invitation.location_id,
            "tick": current_tick,
        }
        self.shared_leisure_sessions.append(session_record)

        return {
            "executed": True,
            "activity": invitation.activity_type.value,
            "participants": [invitation.inviter_uid, invitation.invitee_uid],
        }
