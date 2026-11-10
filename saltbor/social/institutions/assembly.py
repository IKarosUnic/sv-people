"""Community assemblies, collective proposals, voting, and local governance."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


@dataclass
class InstitutionalProposal:
    """A policy, community project, or regulatory proposal tabled for collective vote."""

    proposal_id: str
    title: str
    description: str
    proposer_uid: HumanID
    created_tick: Tick
    votes_for: set[HumanID] = field(default_factory=set)
    votes_against: set[HumanID] = field(default_factory=set)
    is_closed: bool = False
    is_enacted: bool = False
    resolution_tick: Optional[Tick] = None

    @property
    def total_votes(self) -> int:
        return len(self.votes_for) + len(self.votes_against)

    @property
    def approval_ratio(self) -> float:
        if self.total_votes == 0:
            return 0.0
        return len(self.votes_for) / float(self.total_votes)


class CommunityAssembly:
    """Deliberative local governance forum managing community proposals and voting."""

    def __init__(self, assembly_id: str = "asamblea_comunal", name: str = "Asamblea Comunal de Saltbor") -> None:
        self.assembly_id = assembly_id
        self.name = name
        self.proposals: dict[str, InstitutionalProposal] = {}
        self.enacted_policies: list[InstitutionalProposal] = []

    def submit_proposal(
        self,
        proposal_id: str,
        title: str,
        description: str,
        proposer_uid: HumanID,
        current_tick: Tick,
    ) -> InstitutionalProposal:
        """Table a new community proposal."""
        prop = InstitutionalProposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposer_uid=proposer_uid,
            created_tick=current_tick,
        )
        self.proposals[proposal_id] = prop
        # Proposer automatically votes in favor
        prop.votes_for.add(proposer_uid)
        logger.info("New proposal submitted to assembly: %s by %s", title, proposer_uid)
        return prop

    def cast_vote(
        self,
        proposal_id: str,
        voter_uid: HumanID,
        vote_in_favor: bool,
    ) -> bool:
        """Register an individual member's vote."""
        prop = self.proposals.get(proposal_id)
        if not prop or prop.is_closed:
            return False

        # Remove previous vote if any
        prop.votes_for.discard(voter_uid)
        prop.votes_against.discard(voter_uid)

        if vote_in_favor:
            prop.votes_for.add(voter_uid)
        else:
            prop.votes_against.add(voter_uid)

        return True

    def tally_and_resolve(
        self,
        proposal_id: str,
        current_tick: Tick,
        quorum: int = 3,
        threshold: float = 0.50,
    ) -> tuple[bool, bool, str]:
        """Tally votes for proposal and enact if quorum and majority threshold are met.

        Returns (resolved: bool, enacted: bool, summary: str).
        """
        prop = self.proposals.get(proposal_id)
        if not prop or prop.is_closed:
            return False, False, "Proposal not active"

        if prop.total_votes < quorum:
            return False, False, f"Quorum not reached ({prop.total_votes} < {quorum})"

        prop.is_closed = True
        prop.resolution_tick = current_tick

        if prop.approval_ratio > threshold:
            prop.is_enacted = True
            self.enacted_policies.append(prop)
            summary = f"Passed with {len(prop.votes_for)}/{prop.total_votes} votes ({prop.approval_ratio:.1%})"
            logger.info("Proposal '%s' ENACTED: %s", prop.title, summary)
            return True, True, summary
        else:
            prop.is_enacted = False
            summary = f"Rejected with {len(prop.votes_against)}/{prop.total_votes} votes"
            logger.info("Proposal '%s' REJECTED: %s", prop.title, summary)
            return True, False, summary
