"""General and collective problem solving architecture for Saltbor Phase 0.7."""

from saltbor.cognition.problem_solving.collective import (
    CollectiveProblemSolvingEngine,
    CollectiveProposal,
    CollectiveSolvingReport,
    TeamMemberRole,
)
from saltbor.cognition.problem_solving.engine import ProblemSolvingEngine, ProblemSolvingTrace
from saltbor.cognition.problem_solving.problem import Problem, ProblemOutcome, StrategyType

__all__ = [
    "CollectiveProblemSolvingEngine",
    "CollectiveProposal",
    "CollectiveSolvingReport",
    "Problem",
    "ProblemOutcome",
    "ProblemSolvingEngine",
    "ProblemSolvingTrace",
    "StrategyType",
    "TeamMemberRole",
]
