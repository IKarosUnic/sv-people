"""General Problem Solving Engine for Saltbor Phase 0.7 (Section 3).

Executes the formal 14-step general problem solving cycle:
 1. Detect problem.
 2. Understand current state.
 3. Identify desired state.
 4. Recognize constraints.
 5. Consult relevant knowledge.
 6. Identify missing information.
 7. Generate alternatives.
 8. Evaluate consequences.
 9. Select strategy.
10. Execute actions.
11. Observe results.
12. Evaluate if problem solved.
13. Modify strategy when necessary.
14. Learn from results.

Supports full range of outcomes: solved, partially solved, failed,
seeking assistance, experimenting, temporary abandonment, or recognizing
insufficient capability.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Optional
from uuid import uuid4

from saltbor.cognition.epistemic.beliefs import BeliefType, EpistemicBelief
from saltbor.cognition.epistemic.interface import EpistemicInterface
from saltbor.cognition.problem_solving.problem import Problem, ProblemOutcome, StrategyType
from saltbor.cognition.reasoning.engine import AdvancedReasoningEngine
from saltbor.knowledge.layers.individual_graph import IndividualKnowledgeGraph

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ProblemSolvingTrace:
    """Complete, transparent computational trace of the 14-step problem solving cycle."""

    trace_id: str
    problem_id: str
    steps_executed: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    selected_strategy: StrategyType = StrategyType.DIRECT_ACTION
    outcome: ProblemOutcome = ProblemOutcome.FAILED
    satisfaction_ratio: float = 0.0
    modifications_count: int = 0
    lessons_learned: list[str] = dataclasses.field(default_factory=list)

    def record_step(self, step_number: int, name: str, details: dict[str, Any]) -> None:
        self.steps_executed.append({
            "step": step_number,
            "name": name,
            "details": details,
        })

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "problem_id": self.problem_id,
            "steps_count": len(self.steps_executed),
            "selected_strategy": self.selected_strategy.value,
            "outcome": self.outcome.value,
            "satisfaction_ratio": round(self.satisfaction_ratio, 3),
            "lessons": self.lessons_learned,
        }


class ProblemSolvingEngine:
    """General problem solver implementing the full 14-step cognitive workflow."""

    def __init__(self, reasoning: Optional[AdvancedReasoningEngine] = None) -> None:
        self.reasoning = reasoning or AdvancedReasoningEngine()

    def solve(
        self,
        problem: Problem,
        graph: IndividualKnowledgeGraph,
        epistemic: Optional[EpistemicInterface] = None,
        agent_skills: Optional[dict[str, float]] = None,
        agent_inventory: Optional[dict[str, float]] = None,
        known_specialists: Optional[dict[str, str]] = None,
        tick: int = 0,
    ) -> tuple[ProblemOutcome, ProblemSolvingTrace]:
        """Execute the 14-step general problem-solving procedure."""
        agent_skills = agent_skills or {}
        agent_inventory = agent_inventory or {}
        known_specialists = known_specialists or {}

        trace = ProblemSolvingTrace(
            trace_id=f"pst_{uuid4().hex[:8]}",
            problem_id=problem.problem_id,
        )
        problem.attempt_count += 1

        # Step 1: Detect problem
        discrepancies = [
            f"{k}: current={problem.current_state.get(k)} vs target={v}"
            for k, v in problem.desired_state.items()
            if problem.current_state.get(k) != v
        ]
        trace.record_step(1, "Detect problem", {"discrepancies": discrepancies, "urgency": problem.urgency})

        # Step 2: Understand current state
        trace.record_step(2, "Understand current state", {"state": dict(problem.current_state)})

        # Step 3: Identify desired state
        trace.record_step(3, "Identify desired state", {"goal": dict(problem.desired_state)})

        # Step 4: Recognize constraints
        trace.record_step(4, "Recognize constraints", {"constraints": dict(problem.constraints)})

        # Step 5: Consult relevant knowledge
        relevant_knowledge: list[str] = []
        if epistemic:
            nodes = epistemic.query_relevant_knowledge(problem.domain)
            relevant_knowledge = [n.label for n in nodes]
        trace.record_step(5, "Consult relevant knowledge", {"relevant_concepts": relevant_knowledge})

        # Step 6: Identify missing information / missing capabilities
        missing_info: list[str] = []
        missing_skills: list[str] = []
        for cap in problem.required_capabilities:
            if not graph.knows_concept(cap, min_confidence=0.3):
                missing_info.append(cap)
            if agent_skills.get(cap, 0.0) < 0.35:
                missing_skills.append(cap)

        missing_materials: dict[str, float] = {}
        for mat, req_qty in problem.required_materials.items():
            have_qty = agent_inventory.get(mat, 0.0)
            if have_qty < req_qty:
                missing_materials[mat] = req_qty - have_qty

        trace.record_step(6, "Identify missing information", {
            "missing_concepts": missing_info,
            "missing_skills": missing_skills,
            "missing_materials": missing_materials,
        })

        # Step 7: Generate alternatives
        candidate_strategies: list[tuple[StrategyType, float, str]] = []

        # Strategy A: Direct action (if all capabilities and materials in place)
        if not missing_info and not missing_skills and not missing_materials:
            candidate_strategies.append((StrategyType.DIRECT_ACTION, 0.90, "Execute direct action steps"))

        # Strategy B: Seek collaboration / help (if missing skills or capabilities but specialists exist)
        if missing_skills or missing_info:
            has_specialist = any(s in known_specialists for s in (missing_skills + missing_info))
            collab_score = 0.80 if has_specialist else 0.50
            candidate_strategies.append((
                StrategyType.SEEK_COLLABORATION,
                collab_score,
                f"Request assistance from specialist in {missing_skills or missing_info}",
            ))

        # Strategy C: Experimentation / Empirical Investigation (if missing knowledge but curious/willing)
        if missing_info:
            candidate_strategies.append((
                StrategyType.EXPERIMENTATION,
                0.65,
                f"Design controlled trials to discover {missing_info}",
            ))

        # Strategy D: Resource substitution (if missing specific material)
        if missing_materials:
            candidate_strategies.append((
                StrategyType.RESOURCE_SUBSTITUTION,
                0.60,
                f"Identify alternative materials substituting for {list(missing_materials.keys())}",
            ))

        # Strategy E: Temporary abandonment / deferral (if difficulty is extreme)
        if problem.difficulty > 0.80 and (len(missing_skills) >= 2 or len(missing_materials) >= 2):
            candidate_strategies.append((
                StrategyType.TEMPORARY_ABANDONMENT,
                0.70,
                "Acknowledge current resource deficit and defer until capacity increases",
            ))

        # Fallback if no strategy qualified
        if not candidate_strategies:
            candidate_strategies.append((
                StrategyType.TEMPORARY_ABANDONMENT,
                0.40,
                "No viable pathway under current resource constraints",
            ))

        trace.record_step(7, "Generate alternatives", {
            "options": [{"type": s.value, "score": sc, "desc": d} for s, sc, d in candidate_strategies]
        })

        # Step 8: Evaluate consequences
        # Apply MAUT / utility weighting
        scored_options = sorted(candidate_strategies, key=lambda opt: opt[1], reverse=True)
        trace.record_step(8, "Evaluate consequences", {
            "evaluated_utilities": {s.value: sc for s, sc, _ in scored_options}
        })

        # Step 9: Select strategy
        selected_strategy, highest_score, strategy_rationale = scored_options[0]
        trace.selected_strategy = selected_strategy
        trace.record_step(9, "Select strategy", {
            "selected": selected_strategy.value,
            "utility": highest_score,
            "rationale": strategy_rationale,
        })

        # Step 10: Execute actions
        simulated_state = dict(problem.current_state)
        action_success = False

        if selected_strategy == StrategyType.DIRECT_ACTION:
            # Apply desired state deltas
            for k, v in problem.desired_state.items():
                simulated_state[k] = v
            # Deduct materials
            for mat, qty in problem.required_materials.items():
                agent_inventory[mat] = max(0.0, agent_inventory.get(mat, 0.0) - qty)
            action_success = True

        elif selected_strategy == StrategyType.SEEK_COLLABORATION:
            # Collaboration provides missing skills
            specialist = known_specialists.get(missing_skills[0] if missing_skills else (missing_info[0] if missing_info else "general"))
            if specialist:
                for k, v in problem.desired_state.items():
                    simulated_state[k] = v
                action_success = True
            else:
                # Partial help
                for k in list(problem.desired_state.keys())[:1]:
                    simulated_state[k] = problem.desired_state[k]
                action_success = False

        elif selected_strategy == StrategyType.RESOURCE_SUBSTITUTION:
            # Substitute resource
            for k, v in problem.desired_state.items():
                simulated_state[k] = v
            action_success = True

        elif selected_strategy == StrategyType.EXPERIMENTATION:
            # Discovery step: learns concept
            for m in missing_info:
                graph.learn_concept(m, confidence=0.75, source_pathway="experimentation", tick=tick)
            action_success = False  # requires second pass to execute with newly learned concept

        elif selected_strategy == StrategyType.TEMPORARY_ABANDONMENT:
            action_success = False

        trace.record_step(10, "Execute actions", {
            "strategy": selected_strategy.value,
            "action_executed": action_success,
            "new_state": dict(simulated_state),
        })

        # Step 11: Observe results
        trace.record_step(11, "Observe results", {"resulting_state": dict(simulated_state)})

        # Step 12: Evaluate if problem solved
        is_solved, ratio = problem.evaluate_solution(simulated_state)
        trace.satisfaction_ratio = ratio
        trace.record_step(12, "Evaluate if problem solved", {
            "is_solved": is_solved,
            "satisfaction_ratio": ratio,
        })

        # Step 13: Modify strategy when necessary
        if not is_solved and selected_strategy != StrategyType.TEMPORARY_ABANDONMENT:
            trace.modifications_count += 1
            if selected_strategy == StrategyType.EXPERIMENTATION:
                # With concept newly learned, can now direct action on second attempt
                for k, v in problem.desired_state.items():
                    simulated_state[k] = v
                is_solved, ratio = problem.evaluate_solution(simulated_state)
                trace.satisfaction_ratio = ratio
                trace.record_step(13, "Modify strategy", {
                    "replanned": "Switched from experimentation to direct execution following discovery",
                    "post_modification_ratio": ratio,
                })
            else:
                trace.record_step(13, "Modify strategy", {
                    "replanned": "Action incomplete; scheduled follow-up trial",
                })
        else:
            trace.record_step(13, "Modify strategy", {"replanned": "None required"})

        # Final outcome determination
        if is_solved:
            outcome = ProblemOutcome.SOLVED
        elif ratio > 0.4:
            outcome = ProblemOutcome.PARTIALLY_SOLVED
        elif selected_strategy == StrategyType.SEEK_COLLABORATION:
            outcome = ProblemOutcome.ASSISTANCE_REQUESTED
        elif selected_strategy == StrategyType.EXPERIMENTATION:
            outcome = ProblemOutcome.EXPERIMENTING
        elif selected_strategy == StrategyType.TEMPORARY_ABANDONMENT:
            outcome = ProblemOutcome.TEMPORARILY_ABANDONED
        else:
            outcome = ProblemOutcome.FAILED

        trace.outcome = outcome

        # Step 14: Learn from results
        lessons: list[str] = []
        if is_solved:
            lessons.append(f"Strategy '{selected_strategy.value}' successfully solved '{problem.description}'")
            if epistemic:
                epistemic.register_belief(
                    EpistemicBelief(
                        belief_id=f"sol_{problem.problem_id}",
                        subject=problem.domain,
                        predicate="solved_by_strategy",
                        object_val=selected_strategy.value,
                        belief_type=BeliefType.VALIDATED_KNOWLEDGE,
                        confidence=0.90,
                        source_type="problem_solving",
                        created_tick=tick,
                        updated_tick=tick,
                    )
                )
        else:
            lessons.append(f"Strategy '{selected_strategy.value}' was insufficient (ratio={ratio:.2f})")
            if ratio < 0.2 and problem.attempt_count >= 2:
                lessons.append(f"Recognized current lack of capability for '{problem.domain}' difficulty {problem.difficulty}")
                trace.outcome = ProblemOutcome.INSUFFICIENT_CAPABILITY

        trace.lessons_learned = lessons
        trace.record_step(14, "Learn from results", {"lessons": lessons, "final_outcome": trace.outcome.value})

        return trace.outcome, trace
