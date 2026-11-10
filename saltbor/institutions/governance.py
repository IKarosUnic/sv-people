"""Collective governance, institutional proposals, deliberative voting, and policy execution."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

import numpy as np

from saltbor.core.types import HumanID, Tick
from saltbor.institutions.model import (
    InstitutionalPolicy,
    MemberRole,
    SocialInstitution,
)
from saltbor.population.human import SyntheticHuman

logger = logging.getLogger(__name__)


class VotingProtocol(enum.Enum):
    """Democratic and collective decision-making rules."""

    SIMPLE_MAJORITY = "simple_majority"    # > 50% of present votes
    SUPERMAJORITY = "supermajority"        # >= 66% of votes
    CONSENSUS = "consensus"                # 100% agreement (no vetoes)
    COUNCIL_LEADERSHIP = "council_leadership" # Decided by leadership council (President + Treasurer)


@dataclass
class InstitutionalProposal:
    """A formal motion submitted for institutional deliberation and vote."""

    proposal_id: str
    institution_id: str
    title: str
    description: str
    proposer_uid: HumanID
    protocol: VotingProtocol = VotingProtocol.SIMPLE_MAJORITY
    created_tick: Tick = 0

    # Policy details to implement if enacted
    target_area: str = "economy"
    required_treasury_funds: float = 0.0
    policy_parameters: dict[str, Any] = field(default_factory=dict)

    # Balloting
    votes_for: set[HumanID] = field(default_factory=set)
    votes_against: set[HumanID] = field(default_factory=set)
    abstentions: set[HumanID] = field(default_factory=set)

    # Resolution
    is_closed: bool = False
    is_enacted: bool = False
    resolution_summary: str = ""
    resolution_tick: Optional[Tick] = None

    @property
    def total_votes(self) -> int:
        return len(self.votes_for) + len(self.votes_against)

    @property
    def approval_ratio(self) -> float:
        if self.total_votes == 0:
            return 0.0
        return len(self.votes_for) / float(self.total_votes)


class GovernanceEngine:
    """Orchestrates proposal tabling, debate, voting, and real world policy enforcement."""

    def __init__(self, rng: Optional[np.random.Generator] = None) -> None:
        self.rng = rng or np.random.default_rng()
        self.proposals: dict[str, InstitutionalProposal] = {}

    def submit_proposal(
        self,
        proposal_id: str,
        institution: SocialInstitution,
        title: str,
        description: str,
        proposer: SyntheticHuman,
        target_area: str = "economy",
        required_funds: float = 0.0,
        policy_params: Optional[dict[str, Any]] = None,
        protocol: VotingProtocol = VotingProtocol.SIMPLE_MAJORITY,
        current_tick: Tick = 0,
    ) -> InstitutionalProposal:
        """Table a formal proposal within an institution."""
        prop = InstitutionalProposal(
            proposal_id=proposal_id,
            institution_id=institution.institution_id,
            title=title,
            description=description,
            proposer_uid=proposer.uid,
            protocol=protocol,
            created_tick=current_tick,
            target_area=target_area,
            required_treasury_funds=required_funds,
            policy_parameters=policy_params or {},
        )
        # Proposer automatically votes for
        prop.votes_for.add(proposer.uid)
        self.proposals[proposal_id] = prop
        logger.info("Proposal '%s' tabled in institution %s by %s", title, institution.name, proposer.name)
        return prop

    def cast_vote(
        self,
        proposal_id: str,
        voter: SyntheticHuman,
        in_favor: bool,
    ) -> bool:
        """Register a member's vote."""
        prop = self.proposals.get(proposal_id)
        if not prop or prop.is_closed:
            return False

        prop.votes_for.discard(voter.uid)
        prop.votes_against.discard(voter.uid)
        if in_favor:
            prop.votes_for.add(voter.uid)
        else:
            prop.votes_against.add(voter.uid)
        return True

    def resolve_proposal(
        self,
        proposal_id: str,
        institution: SocialInstitution,
        current_tick: Tick,
        quorum_fraction: float = 0.40,
    ) -> tuple[bool, bool, str]:
        """Tally votes, enforce procedural thresholds, check treasury feasibility, and implement policy.

        Returns (resolved: bool, enacted: bool, summary: str).
        """
        prop = self.proposals.get(proposal_id)
        if not prop or prop.is_closed:
            return False, False, "Proposal inactive or already decided"

        total_members = max(1, institution.member_count)
        quorum_required = max(1, int(total_members * quorum_fraction))

        if prop.total_votes < quorum_required:
            prop.is_closed = True
            prop.is_enacted = False
            prop.resolution_tick = current_tick
            prop.resolution_summary = f"Defeated: Quorum not reached ({prop.total_votes} < {quorum_required})."
            logger.info("Proposal '%s' failed due to lack of quorum.", prop.title)
            return True, False, prop.resolution_summary

        # Determine threshold by protocol
        if prop.protocol == VotingProtocol.SIMPLE_MAJORITY:
            passes = prop.approval_ratio > 0.50
        elif prop.protocol == VotingProtocol.SUPERMAJORITY:
            passes = prop.approval_ratio >= 0.666
        elif prop.protocol == VotingProtocol.CONSENSUS:
            passes = len(prop.votes_against) == 0
        elif prop.protocol == VotingProtocol.COUNCIL_LEADERSHIP:
            # Check president vote
            presidents = [
                uid for uid, r in institution.members.items() if r == MemberRole.PRESIDENT
            ]
            passes = any(p in prop.votes_for for p in presidents) if presidents else (prop.approval_ratio > 0.50)
        else:
            passes = prop.approval_ratio > 0.50

        if not passes:
            prop.is_closed = True
            prop.is_enacted = False
            prop.resolution_tick = current_tick
            prop.resolution_summary = f"Rejected: failed {prop.protocol.value} threshold ({len(prop.votes_for)} for, {len(prop.votes_against)} against)."
            logger.info("Proposal '%s' REJECTED: %s", prop.title, prop.resolution_summary)
            return True, False, prop.resolution_summary

        # Check treasury resource feasibility
        if prop.required_treasury_funds > institution.treasury_money:
            prop.is_closed = True
            prop.is_enacted = False
            prop.resolution_tick = current_tick
            prop.resolution_summary = f"Passed vote but FAILED implementation: required treasury funds ${prop.required_treasury_funds:.2f} exceed treasury balance ${institution.treasury_money:.2f}."
            logger.warning("Proposal '%s' passed vote but lacked treasury backing.", prop.title)
            institution.legitimacy = max(0.2, institution.legitimacy - 0.10)
            return True, False, prop.resolution_summary

        # Deduct treasury funds and enact real world policy!
        institution.treasury_money -= prop.required_treasury_funds
        prop.is_closed = True
        prop.is_enacted = True
        prop.resolution_tick = current_tick
        prop.resolution_summary = (
            f"ENACTED under {prop.protocol.value}: {len(prop.votes_for)}/{prop.total_votes} in favor. "
            f"Committed ${prop.required_treasury_funds:.2f} from treasury."
        )

        policy = InstitutionalPolicy(
            policy_id=f"pol_{prop.proposal_id}",
            title=prop.title,
            target_area=prop.target_area,
            description=prop.description,
            enacted_tick=current_tick,
            parameters=prop.policy_parameters,
            is_active=True,
        )
        institution.enacted_policies.append(policy)
        institution.history_log.append(f"Tick {current_tick}: Policy ENACTED - {prop.title}")
        institution.legitimacy = min(1.0, institution.legitimacy + 0.05)
        logger.info("Proposal '%s' successfully ENACTED and implemented.", prop.title)

        return True, True, prop.resolution_summary
