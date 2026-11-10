"""Problem representation and outcome classification for Phase 0.7 (Section 3)."""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any, Optional


class ProblemOutcome(str, Enum):
    """Possible outcomes of a problem-solving episode."""

    SOLVED = "solved"
    PARTIALLY_SOLVED = "partially_solved"
    FAILED = "failed"
    ASSISTANCE_REQUESTED = "assistance_requested"
    INVESTIGATING = "investigating"
    EXPERIMENTING = "experimenting"
    TEMPORARILY_ABANDONED = "temporarily_abandoned"
    INSUFFICIENT_CAPABILITY = "insufficient_capability"


class StrategyType(str, Enum):
    """Categorical strategy options evaluated by problem solver."""

    DIRECT_ACTION = "direct_action"
    ACQUIRE_KNOWLEDGE = "acquire_knowledge"
    SEEK_COLLABORATION = "seek_collaboration"
    EXPERIMENTATION = "experimentation"
    RESOURCE_SUBSTITUTION = "resource_substitution"
    REPLANNING = "replanning"
    TEMPORARY_ABANDONMENT = "temporary_abandonment"


@dataclasses.dataclass
class Problem:
    """A formal problem definition with current state, goal state, and constraints."""

    problem_id: str
    description: str
    domain: str                         # e.g., 'crafting', 'agriculture', 'logistics', 'social'
    current_state: dict[str, Any]
    desired_state: dict[str, Any]
    constraints: dict[str, Any]         # e.g., {'max_cost': 50.0, 'max_ticks': 10, 'required_tools': ['hammer']}
    difficulty: float = 0.5             # [0.0, 1.0]
    required_capabilities: list[str] = dataclasses.field(default_factory=list)
    required_materials: dict[str, float] = dataclasses.field(default_factory=dict)
    urgency: float = 0.5                # [0.0, 1.0]
    attempt_count: int = 0
    created_tick: int = 0

    def evaluate_solution(self, resulting_state: dict[str, Any]) -> tuple[bool, float]:
        """Check how much of the desired state has been achieved.

        Returns (is_fully_solved: bool, satisfaction_ratio: float in [0.0, 1.0]).
        """
        if not self.desired_state:
            return True, 1.0

        satisfied = 0
        total = len(self.desired_state)

        for k, target_val in self.desired_state.items():
            curr = resulting_state.get(k)
            if isinstance(target_val, (int, float)) and isinstance(curr, (int, float)):
                if curr >= target_val:
                    satisfied += 1
            else:
                if curr == target_val:
                    satisfied += 1

        ratio = satisfied / total
        return ratio >= 0.99, ratio
