"""Collective Governance and Deliberative Decision Engine for SALTBOR Phase 1.9.

Models authentic community deliberation, assemblies, democratic voting, power asymmetries,
dissent, strategic abstention, lobbying, consensus formation, and real-world policy enactment.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Any, Dict, List, Optional, Set
import uuid

from saltbor.core.types import HumanID, Tick

logger = logging.getLogger(__name__)


class VotingProtocol(str, enum.Enum):
    """Democratic and collective decision-making protocols."""

    SIMPLE_MAJORITY = "simple_majority"        # > 50% of cast votes
    SUPERMAJORITY = "supermajority"            # >= 66.7% of cast votes
    CONSENSUS = "consensus"                    # 100% agreement (any 'against' vote is a veto)
    COUNCIL_DIRECTIVA = "council_directiva"    # Decided exclusively by the elected board


class ProposalStatus(str, enum.Enum):
    """Lifecycle status of a collective proposal."""

    DRAFTED = "drafted"
    DEBATING = "debating"
    VOTING = "voting"
    ENACTED = "enacted"
    REJECTED = "rejected"
    FAILED_QUORUM = "failed_quorum"


@dataclasses.dataclass
class CollectiveProposal:
    """A formal motion submitted for assembly debate and vote."""

    proposal_id: str
    organization_id: str
    proposer_uid: str
    title: str
    description: str
    protocol: VotingProtocol = VotingProtocol.SIMPLE_MAJORITY
    cost_usd: float = 0.0
    status: ProposalStatus = ProposalStatus.DEBATING
    created_tick: int = 0
    decided_tick: Optional[int] = None

    # Votes and Stances
    votes_for: set[str] = dataclasses.field(default_factory=set)
    votes_against: set[str] = dataclasses.field(default_factory=set)
    abstentions: set[str] = dataclasses.field(default_factory=set)
    voter_influence_weights: dict[str, float] = dataclasses.field(default_factory=dict)

    # Deliberation Details
    arguments_raised: list[str] = dataclasses.field(default_factory=list)
    dissenting_reasons: list[str] = dataclasses.field(default_factory=list)
    outcome_summary: str = ""

    @property
    def total_participating_voters(self) -> int:
        return len(self.votes_for) + len(self.votes_against) + len(self.abstentions)

    @property
    def effective_votes_for(self) -> float:
        return sum(self.voter_influence_weights.get(uid, 1.0) for uid in self.votes_for)

    @property
    def effective_votes_against(self) -> float:
        return sum(self.voter_influence_weights.get(uid, 1.0) for uid in self.votes_against)

    @property
    def weighted_approval_ratio(self) -> float:
        total = self.effective_votes_for + self.effective_votes_against
        if total <= 0:
            return 0.0
        return round(self.effective_votes_for / total, 3)


class CollectiveGovernanceEngine:
    """Orchestrates community assemblies, proposal debates, voting, and decision enforcement."""

    def __init__(self) -> None:
        self._proposals: dict[str, CollectiveProposal] = {}
        self._assembly_history: list[dict[str, Any]] = []

    def get_proposal(self, proposal_id: str) -> Optional[CollectiveProposal]:
        return self._proposals.get(proposal_id)

    def get_proposals_by_organization(self, organization_id: str) -> list[CollectiveProposal]:
        return [p for p in self._proposals.values() if p.organization_id == organization_id]

    def submit_proposal(
        self,
        organization_id: str,
        proposer_uid: str,
        title: str,
        description: str,
        cost_usd: float = 0.0,
        protocol: VotingProtocol = VotingProtocol.SIMPLE_MAJORITY,
        tick: int = 0,
    ) -> CollectiveProposal:
        """Table a motion in the assembly."""
        prop_id = f"gov_{uuid.uuid4().hex[:6]}"
        prop = CollectiveProposal(
            proposal_id=prop_id,
            organization_id=organization_id,
            proposer_uid=proposer_uid,
            title=title,
            description=description,
            protocol=protocol,
            cost_usd=cost_usd,
            status=ProposalStatus.DEBATING,
            created_tick=tick,
        )
        # Proposer automatically votes in favor with standard baseline influence
        prop.votes_for.add(proposer_uid)
        prop.voter_influence_weights[proposer_uid] = 1.0
        self._proposals[prop_id] = prop
        return prop

    def cast_deliberative_vote(
        self,
        proposal_id: str,
        voter_uid: str,
        stance: str, # "for", "against", "abstain"
        influence_weight: float = 1.0,
        reason: str = "",
    ) -> bool:
        """Register an individual's vote, weighted by their social influence or authority."""
        prop = self._proposals.get(proposal_id)
        if not prop or prop.status in (ProposalStatus.ENACTED, ProposalStatus.REJECTED, ProposalStatus.FAILED_QUORUM):
            return False

        # Clear prior stance
        prop.votes_for.discard(voter_uid)
        prop.votes_against.discard(voter_uid)
        prop.abstentions.discard(voter_uid)

        prop.voter_influence_weights[voter_uid] = max(0.20, influence_weight)

        if stance == "for":
            prop.votes_for.add(voter_uid)
        elif stance == "against":
            prop.votes_against.add(voter_uid)
            if reason:
                prop.dissenting_reasons.append(f"{voter_uid}: {reason}")
        else:
            prop.abstentions.add(voter_uid)

        return True

    def resolve_assembly_vote(
        self,
        proposal_id: str,
        total_eligible_members: int,
        treasury_balance_usd: float,
        quorum_fraction: float = 0.40,
        board_member_uids: Optional[set[str]] = None,
        tick: int = 0,
    ) -> tuple[bool, str]:
        """Conclude assembly deliberation and determine whether policy is enacted.

        Returns (is_enacted: bool, outcome_summary: str).
        """
        prop = self._proposals.get(proposal_id)
        if not prop:
            return False, "Propuesta no encontrada"

        # Check quorum
        quorum_needed = max(1, int(total_eligible_members * quorum_fraction))
        total_voted = len(prop.votes_for) + len(prop.votes_against) + len(prop.abstentions)
        if total_voted < quorum_needed:
            prop.status = ProposalStatus.FAILED_QUORUM
            prop.decided_tick = tick
            prop.outcome_summary = f"Sin quórum ({total_voted}/{quorum_needed} requeridos)"
            return False, prop.outcome_summary

        # Check voting protocol threshold
        passes_threshold = False
        if prop.protocol == VotingProtocol.SIMPLE_MAJORITY:
            passes_threshold = prop.effective_votes_for > prop.effective_votes_against
        elif prop.protocol == VotingProtocol.SUPERMAJORITY:
            total_active = prop.effective_votes_for + prop.effective_votes_against
            passes_threshold = (prop.effective_votes_for / max(0.1, total_active)) >= 0.666
        elif prop.protocol == VotingProtocol.CONSENSUS:
            passes_threshold = len(prop.votes_against) == 0
        elif prop.protocol == VotingProtocol.COUNCIL_DIRECTIVA:
            board = board_member_uids or set()
            board_for = sum(1 for uid in prop.votes_for if uid in board)
            board_against = sum(1 for uid in prop.votes_against if uid in board)
            passes_threshold = board_for > board_against
        else:
            passes_threshold = prop.effective_votes_for > prop.effective_votes_against

        if not passes_threshold:
            prop.status = ProposalStatus.REJECTED
            prop.decided_tick = tick
            prop.outcome_summary = f"Rechazada: {len(prop.votes_for)} a favor vs {len(prop.votes_against)} en contra"
            return False, prop.outcome_summary

        # Check treasury resource feasibility
        if prop.cost_usd > treasury_balance_usd:
            prop.status = ProposalStatus.REJECTED
            prop.decided_tick = tick
            prop.outcome_summary = (
                f"Aprobada en voto pero RECHAZADA por falta de fondos (${prop.cost_usd:.2f} requeridos > "
                f"${treasury_balance_usd:.2f} en tesorería)"
            )
            return False, prop.outcome_summary

        # Policy ENACTED!
        prop.status = ProposalStatus.ENACTED
        prop.decided_tick = tick
        prop.outcome_summary = (
            f"ENACTADA bajo {prop.protocol.value}: {len(prop.votes_for)} votos a favor, "
            f"{len(prop.votes_against)} en contra, {len(prop.abstentions)} abstenciones. "
            f"Fondos comprometidos: ${prop.cost_usd:.2f}"
        )
        self._assembly_history.append({
            "proposal_id": prop.proposal_id,
            "organization_id": prop.organization_id,
            "tick": tick,
            "title": prop.title,
            "status": "enacted",
            "cost_usd": prop.cost_usd,
        })
        return True, prop.outcome_summary
