"""Organizational Intelligence and Governance Engine for Saltbor Phase 0.9.

Models emergent leadership, legitimacy decay/renewal, deliberative assemblies,
governance structures, formal proposals, and collective decision making.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
import uuid
from typing import Any, Optional

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class GovernanceModel(str, enum.Enum):
    """Modes of community or institutional governance."""

    INFORMAL_CONSENSUS = "informal_consensus"
    DIRECT_ASSEMBLY = "direct_assembly"
    COUNCIL_OF_ELDERS = "council_of_elders"
    REPRESENTATIVE_DIRECTIVA = "representative_directiva"
    COOPERATIVE_BOARD = "cooperative_board"


class DecisionStatus(str, enum.Enum):
    """Status of an organizational proposal."""

    DRAFTED = "drafted"
    DEBATING = "debating"
    VOTING = "voting"
    ENACTED = "enacted"
    REJECTED = "rejected"


@dataclasses.dataclass
class OrganizationalProposal:
    """A formal policy or operational initiative proposed within an organization."""

    proposal_id: str
    organization_id: str
    proposer_uid: str
    title: str
    description: str
    cost_usd: float = 0.0
    status: DecisionStatus = DecisionStatus.DRAFTED
    votes_for: set[str] = dataclasses.field(default_factory=set)
    votes_against: set[str] = dataclasses.field(default_factory=set)
    created_tick: int = 0
    decided_tick: Optional[int] = None
    outcome_summary: str = ""


@dataclasses.dataclass
class LeadershipProfile:
    """An agent's emergent leadership profile and dynamic legitimacy within an organization."""

    human_uid: str
    organization_id: str
    role_title: str = "coordinator"
    legitimacy: float = 0.8         # [0.0, 1.0] Member confidence and approval
    experience_score: float = 0.5   # [0.0, 1.0]
    reputation_score: float = 0.6   # [0.0, 1.0]
    successful_initiatives: int = 0
    failed_initiatives: int = 0
    tenure_ticks: int = 0

    def adjust_legitimacy(self, delta: float) -> None:
        """Update legitimacy following successes, scandals, or project outcomes."""
        self.legitimacy = max(0.0, min(1.0, self.legitimacy + delta))
        if delta > 0:
            self.successful_initiatives += 1
        elif delta < -0.15:
            self.failed_initiatives += 1


class OrganizationalIntelligenceEngine:
    """Manages governance, assemblies, leadership legitimacy, and collective decision making."""

    def __init__(self) -> None:
        self._proposals: dict[str, OrganizationalProposal] = {}
        # (org_id, human_uid) -> LeadershipProfile
        self._leadership: dict[tuple[str, str], LeadershipProfile] = {}

    def register_leader(
        self,
        organization_id: str,
        human_uid: str | HumanID,
        role_title: str = "Presidente",
        initial_legitimacy: float = 0.85,
    ) -> LeadershipProfile:
        """Appoint or record an emergent leader."""
        uid = str(human_uid)
        profile = LeadershipProfile(
            human_uid=uid,
            organization_id=organization_id,
            role_title=role_title,
            legitimacy=initial_legitimacy,
        )
        self._leadership[(organization_id, uid)] = profile
        return profile

    def get_leadership_profile(
        self,
        organization_id: str,
        human_uid: str | HumanID,
    ) -> Optional[LeadershipProfile]:
        return self._leadership.get((organization_id, str(human_uid)))

    def evaluate_leadership_fitness(
        self,
        candidate_data: dict[str, Any], # {uid, experience, reputation, organization_skill, trust}
    ) -> float:
        """Calculate emergent leadership suitability based on social factors."""
        exp = candidate_data.get("experience", 0.5)
        rep = candidate_data.get("reputation", 0.5)
        skill = candidate_data.get("organization_skill", 0.5)
        trust = candidate_data.get("trust", 0.5)

        fitness = (exp * 0.25) + (rep * 0.35) + (skill * 0.20) + (trust * 0.20)
        return round(max(0.0, min(1.0, fitness)), 4)

    def submit_proposal(
        self,
        organization_id: str,
        proposer_uid: str | HumanID,
        title: str,
        description: str,
        cost_usd: float = 0.0,
        tick: int = 0,
    ) -> OrganizationalProposal:
        """Submit a proposal for organizational deliberation."""
        prop_id = f"prop_{uuid.uuid4().hex[:6]}"
        prop = OrganizationalProposal(
            proposal_id=prop_id,
            organization_id=organization_id,
            proposer_uid=str(proposer_uid),
            title=title,
            description=description,
            cost_usd=cost_usd,
            status=DecisionStatus.DEBATING,
            created_tick=tick,
        )
        self._proposals[prop_id] = prop
        return prop

    def cast_vote(
        self,
        proposal_id: str,
        voter_uid: str | HumanID,
        in_favor: bool,
    ) -> bool:
        """Cast vote on a pending proposal."""
        prop = self._proposals.get(proposal_id)
        if not prop:
            return False

        uid = str(voter_uid)
        if in_favor:
            prop.votes_for.add(uid)
            prop.votes_against.discard(uid)
        else:
            prop.votes_against.add(uid)
            prop.votes_for.discard(uid)
        return True

    def resolve_proposal(
        self,
        proposal_id: str,
        quorum_required: int = 3,
        approval_threshold: float = 0.5,
        tick: int = 0,
    ) -> bool:
        """Conclude assembly voting and determine enactment or rejection."""
        prop = self._proposals.get(proposal_id)
        if not prop:
            return False

        total_votes = len(prop.votes_for) + len(prop.votes_against)
        if total_votes < quorum_required:
            prop.status = DecisionStatus.REJECTED
            prop.decided_tick = tick
            prop.outcome_summary = f"Failed to meet quorum ({total_votes}/{quorum_required})"
            return False

        approval_ratio = len(prop.votes_for) / total_votes
        if approval_ratio > approval_threshold:
            prop.status = DecisionStatus.ENACTED
            prop.decided_tick = tick
            prop.outcome_summary = f"Enacted with {len(prop.votes_for)}/{total_votes} votes ({approval_ratio*100:.1f}%)"
            return True
        else:
            prop.status = DecisionStatus.REJECTED
            prop.decided_tick = tick
            prop.outcome_summary = f"Rejected with {len(prop.votes_against)}/{total_votes} votes against"
            return False
