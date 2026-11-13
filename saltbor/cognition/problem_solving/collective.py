"""Collective Problem Solving Engine for SALTBOR Phase 0.7 & Phase 1.3 (Section 9).

Coordinates multi-agent problem solving when individuals lack capabilities
they must pool from others:
- Specialist identification based on reputation or direct acquaintance.
- Collaboration requests and negotiations.
- Team formation and role/task distribution.
- Knowledge and perspective exchange.
- Proposal debate and disagreement resolution.
- Shared learning and mutual contribution recording.
- Realistic friction: conflicts of interest, distrust, misinformation, coordination failures,
  groupthink, and overreliance on flawed specialists.
- Cooperation can improve results, worsen them (coordination drag, shared errors), or have no effect.
"""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
import numpy as np

from saltbor.cognition.development.profile import CognitiveCapability, CognitiveProfile
from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.cognition.problem_solving.problem import Problem, ProblemOutcome
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph


@dataclasses.dataclass
class TeamMemberRole:
    """A member assigned to an ad-hoc problem solving collective."""

    agent_uid: str
    specialization: str                 # e.g., 'agriculture', 'logistics', 'commerce'
    assigned_subtask: str
    contributed_knowledge_ids: list[str] = dataclasses.field(default_factory=list)
    trust_level: float = 0.7
    has_conflicting_interest: bool = False
    coordination_readiness: float = 0.8


@dataclasses.dataclass
class CollectiveProposal:
    """A solution proposal submitted by a team member for group deliberation."""

    proposal_id: str
    author_uid: str
    strategy_summary: str
    resource_cost: float
    expected_success_probability: float
    is_objectively_sound: bool = True   # False if based on a flawed hypothesis or groupthink
    votes_in_favor: list[str] = dataclasses.field(default_factory=list)
    votes_against: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class CollectiveSolvingReport:
    """Outcome and record of a collective problem solving session."""

    session_id: str
    problem_description: str
    team_members: list[TeamMemberRole]
    proposals_debated: list[CollectiveProposal]
    selected_proposal: Optional[CollectiveProposal]
    disagreements_encountered: list[str]
    coordination_success: bool
    final_outcome: ProblemOutcome
    shared_learnings: list[str]
    contribution_ledger: dict[str, float] # agent_uid -> contribution weight
    coordination_cost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "problem": self.problem_description,
            "team_size": len(self.team_members),
            "proposals_count": len(self.proposals_debated),
            "disagreements": self.disagreements_encountered,
            "coordination_success": self.coordination_success,
            "outcome": self.final_outcome.value,
            "contributions": self.contribution_ledger,
            "shared_learnings": self.shared_learnings,
            "coordination_cost": round(self.coordination_cost, 3),
        }


class CollectiveProblemSolvingEngine:
    """Orchestrates distributed, multi-agent problem resolution."""

    def assemble_team(
        self,
        initiator_uid: str,
        problem: Problem,
        available_agents: list[dict[str, Any]], # list of {uid, specialization, skills, trust, conflicting_interest}
    ) -> list[TeamMemberRole]:
        """Identify specialists and form an ad-hoc collective."""
        needed_domains = list(problem.required_capabilities) or [problem.domain]
        team: list[TeamMemberRole] = [
            TeamMemberRole(
                agent_uid=initiator_uid,
                specialization="coordination",
                assigned_subtask="overall_management_and_assembly",
                trust_level=1.0,
            )
        ]

        assigned_domains: set[str] = set()

        for cand in available_agents:
            if cand["uid"] == initiator_uid:
                continue
            spec = cand.get("specialization", "general")
            # If candidate matches any required capability/domain
            if spec in needed_domains or any(cap in cand.get("skills", {}) for cap in needed_domains):
                role = TeamMemberRole(
                    agent_uid=cand["uid"],
                    specialization=spec,
                    assigned_subtask=f"resolve_{spec}_components",
                    trust_level=cand.get("trust", 0.7),
                    has_conflicting_interest=cand.get("conflicting_interest", False),
                    coordination_readiness=cand.get("coordination_readiness", 0.8),
                )
                team.append(role)
                assigned_domains.add(spec)

        return team

    def solve_collectively(
        self,
        problem: Problem,
        team: list[TeamMemberRole],
        tick: int = 0,
        member_profiles: Optional[dict[str, CognitiveProfile]] = None,
        inject_flawed_hypothesis_uid: Optional[str] = None,
    ) -> CollectiveSolvingReport:
        """Conduct debate, evaluate proposals, resolve disagreements, and execute collective action."""
        session_id = f"collab_{uuid4().hex[:8]}"
        disagreements: list[str] = []
        proposals: list[CollectiveProposal] = []
        contributions: dict[str, float] = {m.agent_uid: 0.0 for m in team}

        # 1. Proposal generation by specialists
        for member in team:
            if member.specialization != "coordination":
                is_flawed = (member.agent_uid == inject_flawed_hypothesis_uid)
                prop = CollectiveProposal(
                    proposal_id=f"prop_{uuid4().hex[:6]}",
                    author_uid=member.agent_uid,
                    strategy_summary=f"Apply {member.specialization} techniques to alleviate {problem.domain} shortage",
                    resource_cost=20.0 if not member.has_conflicting_interest else 60.0,
                    expected_success_probability=0.85 if not member.has_conflicting_interest else 0.40,
                    is_objectively_sound=not is_flawed,
                )
                proposals.append(prop)

        if not proposals:
            # Initiator proposal
            proposals.append(
                CollectiveProposal(
                    proposal_id=f"prop_{uuid4().hex[:6]}",
                    author_uid=team[0].agent_uid,
                    strategy_summary="Standard emergency allocation protocol",
                    resource_cost=30.0,
                    expected_success_probability=0.70,
                )
            )

        # 2. Debate & Voting
        for prop in proposals:
            for member in team:
                # Trust and conflict of interest influence vote
                if member.has_conflicting_interest and prop.author_uid != member.agent_uid:
                    prop.votes_against.append(member.agent_uid)
                    disagreements.append(f"Member {member.agent_uid} opposed proposal {prop.proposal_id} due to divergent self-interest")
                elif member.trust_level < 0.40:
                    prop.votes_against.append(member.agent_uid)
                    disagreements.append(f"Member {member.agent_uid} distrusts author {prop.author_uid}")
                else:
                    prop.votes_in_favor.append(member.agent_uid)

        # 3. Proposal Selection (majority vote)
        best_proposal = max(proposals, key=lambda p: len(p.votes_in_favor) - len(p.votes_against))

        # 4. Check for coordination friction & communication overhead
        net_votes = len(best_proposal.votes_in_favor) - len(best_proposal.votes_against)
        conflict_count = sum(1 for m in team if m.has_conflicting_interest)

        # Communication overhead calculation
        team_size = len(team)
        coordination_cost = 0.0
        if member_profiles and team_size > 2:
            comm_levels = [
                member_profiles[m.agent_uid].get_level(CognitiveCapability.COMMUNICATION_EFFICACY)
                for m in team if m.agent_uid in member_profiles
            ]
            avg_comm = float(np.mean(comm_levels)) if comm_levels else 0.50
            # Low communication in a larger group incurs friction
            coordination_cost = max(0.0, (team_size - 2) * 0.10 * (1.0 - avg_comm))

        # Failure condition 1: high conflict and net negative support
        if conflict_count > len(team) / 2 and net_votes <= 0:
            return CollectiveSolvingReport(
                session_id=session_id,
                problem_description=problem.description,
                team_members=team,
                proposals_debated=proposals,
                selected_proposal=None,
                disagreements_encountered=disagreements,
                coordination_success=False,
                final_outcome=ProblemOutcome.FAILED,
                shared_learnings=["Coordination collapsed due to conflicting self-interests and deep distrust."],
                contribution_ledger=contributions,
                coordination_cost=coordination_cost,
            )

        # Failure condition 2: Collective error / Groupthink (selected proposal is objectively flawed)
        if not best_proposal.is_objectively_sound:
            return CollectiveSolvingReport(
                session_id=session_id,
                problem_description=problem.description,
                team_members=team,
                proposals_debated=proposals,
                selected_proposal=best_proposal,
                disagreements_encountered=disagreements,
                coordination_success=True,
                final_outcome=ProblemOutcome.FAILED,
                shared_learnings=[
                    f"Team unreservedly adopted flawed strategy from {best_proposal.author_uid}",
                    "Collective failure resulted from groupthink and uncritical deference to specialist.",
                ],
                contribution_ledger=contributions,
                coordination_cost=coordination_cost,
            )

        # 5. Execution: Each member contributes their specialty
        for member in team:
            if not member.has_conflicting_interest:
                contributions[member.agent_uid] = 1.0 / max(1, len(team))
            else:
                contributions[member.agent_uid] = 0.2 / max(1, len(team))

        shared_learnings = [
            f"Successfully integrated {len(team)} disciplines ({', '.join(set(m.specialization for m in team))})",
            f"Consensus achieved on strategy: '{best_proposal.strategy_summary}'",
        ]

        # Coordination cost can degrade outcome from SOLVED to PARTIAL if too high
        final_outcome = ProblemOutcome.SOLVED if coordination_cost < 0.35 else ProblemOutcome.PARTIAL

        return CollectiveSolvingReport(
            session_id=session_id,
            problem_description=problem.description,
            team_members=team,
            proposals_debated=proposals,
            selected_proposal=best_proposal,
            disagreements_encountered=disagreements,
            coordination_success=True,
            final_outcome=final_outcome,
            shared_learnings=shared_learnings,
            contribution_ledger=contributions,
            coordination_cost=coordination_cost,
        )
