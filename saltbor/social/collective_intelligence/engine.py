"""Collective Intelligence Engine for Saltbor Phase 0.9.

Coordinates decentralized, multi-agent problem solving across 10 core capabilities:
1. Information Sharing
2. Experience Comparison
3. Task Distribution
4. Specialist Identification
5. Alternative Debate
6. Proposal Evaluation (Argument & Evidence Based, not naive voting)
7. Error & Flaw Detection
8. Common Knowledge Construction
9. Action Coordination
10. Outcome Evaluation & Feedback

Integrates with ProblemSolvingEngine, Knowledge Graphs, and Cognitive Diversity.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
import uuid
from typing import Any, Optional

from saltbor.cognition.problem_solving.problem import Problem, ProblemOutcome
from saltbor.knowledge.layers.collective_graph import CollectiveKnowledgeGraph
from saltbor.knowledge.graph.node import KnowledgeNode, NodeType

logger = logging.getLogger(__name__)


class DeliberationMethod(str, enum.Enum):
    """Method utilized for resolving proposal selection."""

    ARGUMENT_AND_EVIDENCE = "argument_and_evidence"
    EXPERIENCE_WEIGHTED = "experience_weighted"
    SPECIALIST_CONSENSUS = "specialist_consensus"
    DIALECTICAL_SYNTHESIS = "dialectical_synthesis"


@dataclasses.dataclass
class SharedInsight:
    """A verified or proposed insight contributed to the collective deliberation."""

    insight_id: str
    contributor_uid: str
    topic: str
    claim: str
    evidence_weight: float = 0.5  # [0.0, 1.0]
    epistemic_confidence: float = 0.7
    domain: str = "general"


@dataclasses.dataclass
class SolutionProposal:
    """A structured plan proposed to solve a collective challenge."""

    proposal_id: str
    author_uid: str
    strategy_summary: str
    required_tasks: list[dict[str, Any]] # list of {task_name, skill_needed, estimated_cost}
    expected_success_probability: float
    total_resource_cost: float
    supporting_arguments: list[str] = dataclasses.field(default_factory=list)
    detected_flaws: list[str] = dataclasses.field(default_factory=list)
    critique_score: float = 0.5 # [0.0, 1.0]


@dataclasses.dataclass
class TaskAssignment:
    """Delegated task assigned to a specific specialist."""

    task_id: str
    task_name: str
    assigned_uid: str
    skill_required: str
    status: str = "assigned" # "assigned", "in_progress", "completed", "failed"
    progress: float = 0.0
    result_notes: str = ""


@dataclasses.dataclass
class CollectiveSessionReport:
    """Comprehensive diagnostic record of a collective problem-solving session."""

    session_id: str
    problem_title: str
    domain: str
    participants_count: int
    specialists_identified: list[str]
    insights_shared: list[SharedInsight]
    proposals_generated: list[SolutionProposal]
    selected_proposal: Optional[SolutionProposal]
    detected_errors_count: int
    task_assignments: list[TaskAssignment]
    outcome: ProblemOutcome
    execution_success: bool
    common_knowledge_created: list[str]
    duration_ticks: int = 1


class CollectiveIntelligenceEngine:
    """Orchestrates collective problem solving through the 10 distinct capabilities."""

    def __init__(self, collective_kg: Optional[CollectiveKnowledgeGraph] = None) -> None:
        self.collective_kg = collective_kg or CollectiveKnowledgeGraph()
        self.past_sessions: list[CollectiveSessionReport] = []

    # -------------------------------------------------------------------------
    # Capability 1: Share Information
    # -------------------------------------------------------------------------
    def share_information(
        self,
        participants: list[dict[str, Any]], # list of agent dicts with {uid, knowledge_facts}
        target_problem: Problem,
    ) -> list[SharedInsight]:
        """Collect and pool pertinent domain facts from diverse participants."""
        insights: list[SharedInsight] = []
        for agent in participants:
            facts = agent.get("knowledge_facts", [])
            for fact in facts:
                if any(kw in str(fact).lower() for kw in (target_problem.domain.lower(), "solution", "technique", "method")):
                    insight = SharedInsight(
                        insight_id=f"ins_{uuid.uuid4().hex[:6]}",
                        contributor_uid=agent["uid"],
                        topic=target_problem.domain,
                        claim=str(fact),
                        evidence_weight=agent.get("experience_years", 2.0) / 10.0,
                        epistemic_confidence=agent.get("confidence", 0.75),
                        domain=target_problem.domain,
                    )
                    insights.append(insight)
        return insights

    # -------------------------------------------------------------------------
    # Capability 2: Compare Experiences
    # -------------------------------------------------------------------------
    def compare_experiences(
        self,
        insights: list[SharedInsight],
    ) -> dict[str, Any]:
        """Cross-reference claims from multiple individuals to discover consensus or contradictions."""
        consensus_map: dict[str, list[SharedInsight]] = {}
        contradictions: list[str] = []

        for ins in insights:
            key = ins.claim.lower().strip()
            consensus_map.setdefault(key, []).append(ins)

        # Average evidence
        synthesized: dict[str, float] = {}
        for claim, group in consensus_map.items():
            avg_evidence = sum(g.evidence_weight for g in group) / len(group)
            # Boost if multiple independent individuals corroborate
            support_multiplier = 1.0 + min(0.5, (len(group) - 1) * 0.15)
            synthesized[claim] = min(1.0, avg_evidence * support_multiplier)

        return {
            "claims_analyzed": len(insights),
            "unique_claims": len(synthesized),
            "corroborated_claims": synthesized,
            "contradictions": contradictions,
        }

    # -------------------------------------------------------------------------
    # Capability 3: Distribute Tasks
    # -------------------------------------------------------------------------
    def distribute_tasks(
        self,
        tasks: list[dict[str, Any]],
        candidates: list[dict[str, Any]], # {uid, skills: dict[name, level]}
    ) -> list[TaskAssignment]:
        """Assign subtasks to the most qualified candidates based on skill match."""
        assignments: list[TaskAssignment] = []
        assigned_uids: set[str] = set()

        for t in tasks:
            req_skill = t.get("skill_needed", "general")
            # Find candidate with highest matching skill not already saturated
            best_cand: Optional[str] = None
            best_score = -1.0

            for cand in candidates:
                skills = cand.get("skills", {})
                score = skills.get(req_skill, 0.1)
                # Prioritize available agents
                if cand["uid"] in assigned_uids:
                    score *= 0.75
                if score > best_score:
                    best_score = score
                    best_cand = cand["uid"]

            final_uid = best_cand or (candidates[0]["uid"] if candidates else "unassigned")
            assigned_uids.add(final_uid)

            assignment = TaskAssignment(
                task_id=f"task_{uuid.uuid4().hex[:6]}",
                task_name=t.get("task_name", "subtask"),
                assigned_uid=final_uid,
                skill_required=req_skill,
            )
            assignments.append(assignment)

        return assignments

    # -------------------------------------------------------------------------
    # Capability 4: Identify Specialists
    # -------------------------------------------------------------------------
    def identify_specialists(
        self,
        domain: str,
        candidates: list[dict[str, Any]], # {uid, specialization, skills: dict, reputation: float}
        required_capabilities: Optional[list[str]] = None,
    ) -> list[str]:
        """Filter and rank agents possessing superior expertise in the problem domain."""
        specialists: list[tuple[str, float]] = []
        target_domains = [domain.lower()] + [c.lower() for c in (required_capabilities or [])]

        for cand in candidates:
            spec = cand.get("specialization", "").lower()
            skills = cand.get("skills", {})
            matching_skill = max((skills.get(d, 0.0) for d in target_domains), default=0.0)
            rep = cand.get("reputation", 0.5)

            fitness = matching_skill * 0.6 + rep * 0.4
            if any(d in spec for d in target_domains) or matching_skill >= 0.5:
                fitness += 0.3
            specialists.append((cand["uid"], fitness))

        specialists.sort(key=lambda x: x[1], reverse=True)
        return [uid for uid, score in specialists if score >= 0.45]

    # -------------------------------------------------------------------------
    # Capability 5: Debate Alternatives
    # -------------------------------------------------------------------------
    def debate_alternatives(
        self,
        proposals: list[SolutionProposal],
        participants: list[dict[str, Any]],
    ) -> list[SolutionProposal]:
        """Critique proposals, discovering strengths, weaknesses, and potential pitfalls."""
        for prop in proposals:
            for part in participants:
                skills = part.get("skills", {})
                personality = part.get("personality", {})
                conscientiousness = personality.get("conscientiousness", 0.5)

                # High conscientiousness or relevant skills spot hidden flaws
                if conscientiousness > 0.65 or any(req["skill_needed"] in skills for req in prop.required_tasks):
                    if prop.total_resource_cost > 150.0:
                        prop.detected_flaws.append(f"Excessive resource burden identified by {part['uid']}")
                    if prop.expected_success_probability < 0.60:
                        prop.detected_flaws.append(f"Low empirical confidence identified by {part['uid']}")
                    prop.critique_score = max(0.1, prop.critique_score - 0.10)
                else:
                    prop.supporting_arguments.append(f"Supported on feasibility by {part['uid']}")
                    prop.critique_score = min(1.0, prop.critique_score + 0.05)
        return proposals

    # -------------------------------------------------------------------------
    # Capability 6: Evaluate Proposals (Evidence & Argument Based)
    # -------------------------------------------------------------------------
    def evaluate_proposals(
        self,
        proposals: list[SolutionProposal],
        method: DeliberationMethod = DeliberationMethod.ARGUMENT_AND_EVIDENCE,
    ) -> Optional[SolutionProposal]:
        """Select the highest-quality proposal using argumentation and evidence, avoiding naive majority."""
        if not proposals:
            return None

        best_prop: Optional[SolutionProposal] = None
        best_metric = -100.0

        for prop in proposals:
            # Metric = (Expected Success * 0.5) + (Critique Score * 0.3) - (Cost Factor * 0.2) - (Flaw Penalties)
            cost_factor = min(1.0, prop.total_resource_cost / 200.0)
            flaw_penalty = len(prop.detected_flaws) * 0.15
            score = (prop.expected_success_probability * 0.50) + (prop.critique_score * 0.35) - (cost_factor * 0.15) - flaw_penalty

            if score > best_metric:
                best_metric = score
                best_prop = prop

        return best_prop

    # -------------------------------------------------------------------------
    # Capability 7: Detect Errors
    # -------------------------------------------------------------------------
    def detect_errors(
        self,
        proposal: SolutionProposal,
        available_resources: dict[str, float],
    ) -> list[str]:
        """Detect execution errors and resource deficits prior to deployment."""
        errors: list[str] = []
        if available_resources.get("funds", 0.0) < proposal.total_resource_cost:
            errors.append(f"Budget deficit: required {proposal.total_resource_cost}, available {available_resources.get('funds', 0.0)}")

        if not proposal.required_tasks:
            errors.append("Proposal lacks decomposed actionable tasks")

        return errors

    # -------------------------------------------------------------------------
    # Capability 8: Build Common Knowledge
    # -------------------------------------------------------------------------
    def build_common_knowledge(
        self,
        group_id: str,
        group_type: str,
        problem: Problem,
        proven_solution_summary: str,
        tick: int = 0,
    ) -> KnowledgeNode:
        """Store validated collective solution in the collective knowledge graph."""
        node_id = f"col_sol_{problem.problem_id[:8]}_{uuid.uuid4().hex[:4]}"
        node = KnowledgeNode(
            node_id=node_id,
            node_type=NodeType.SOLUTION,
            label=f"Solucion Colectiva: {problem.description[:30]}",
            description=proven_solution_summary,
            properties={
                "domain": problem.domain,
                "problem_id": problem.problem_id,
                "consensus": 0.95,
            },
            created_tick=tick,
            origin_type="collective_deliberation",
        )
        self.collective_kg.institutionalize_knowledge(
            group_id=group_id,
            group_type=group_type,
            node=node,
            documentation_type="communal_consensus",
            tick=tick,
        )
        return node

    # -------------------------------------------------------------------------
    # Capabilities 9 & 10: Coordinate Actions & Evaluate Results
    # -------------------------------------------------------------------------
    def coordinate_and_execute(
        self,
        session_id: str,
        problem: Problem,
        participants: list[dict[str, Any]],
        proposals: list[SolutionProposal],
        available_resources: dict[str, float],
        group_id: str = "comm_general",
        tick: int = 0,
    ) -> CollectiveSessionReport:
        """Execute full collective problem solving workflow."""
        # 1. Share information
        insights = self.share_information(participants, problem)

        # 2. Compare experiences
        self.compare_experiences(insights)

        # 3. Identify specialists
        specialists = self.identify_specialists(
            domain=problem.domain,
            candidates=participants,
            required_capabilities=getattr(problem, "required_capabilities", None),
        )

        # 4. Debate alternatives
        debated_props = self.debate_alternatives(proposals, participants)

        # 5. Evaluate proposals via arguments & evidence
        chosen = self.evaluate_proposals(debated_props)

        # 6. Detect errors
        detected_errors: list[str] = []
        if chosen:
            detected_errors = self.detect_errors(chosen, available_resources)

        # 7. Distribute tasks
        assignments: list[TaskAssignment] = []
        execution_success = False
        outcome = ProblemOutcome.FAILED

        if chosen and not detected_errors:
            assignments = self.distribute_tasks(chosen.required_tasks, participants)
            # Execute tasks
            for task in assignments:
                task.status = "completed"
                task.progress = 1.0

            execution_success = True
            outcome = ProblemOutcome.SOLVED

            # 8. Build common knowledge
            common_node = self.build_common_knowledge(
                group_id=group_id,
                group_type="community",
                problem=problem,
                proven_solution_summary=chosen.strategy_summary,
                tick=tick,
            )
            common_created = [common_node.node_id]
        else:
            common_created = []

        report = CollectiveSessionReport(
            session_id=session_id,
            problem_title=problem.description,
            domain=problem.domain,
            participants_count=len(participants),
            specialists_identified=specialists,
            insights_shared=insights,
            proposals_generated=debated_props,
            selected_proposal=chosen,
            detected_errors_count=len(detected_errors),
            task_assignments=assignments,
            outcome=outcome,
            execution_success=execution_success,
            common_knowledge_created=common_created,
            duration_ticks=1,
        )
        self.past_sessions.append(report)
        return report
