"""Goal-Oriented Action Planning (GOAP) engine with A* state-space search."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class ActionDefinition:
    """An atomic planning action with explicit preconditions and effects."""

    action_id: str
    name: str
    preconditions: dict[str, Any]    # Required world/agent state variables
    effects: dict[str, Any]          # State mutations applied upon completion
    cost: float = 1.0                # Planning cost heuristic
    duration_ticks: int = 1
    required_capabilities: list[str] = field(default_factory=list)
    resource_costs: dict[str, float] = field(default_factory=dict) # e.g. {"money": 20.0, "wood": 2.0}


class WorldState:
    """Represents a symbolic state of agent variables and resources for planning."""

    def __init__(self, state_dict: Optional[dict[str, Any]] = None) -> None:
        self._state: dict[str, Any] = dict(state_dict or {})

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def satisfies(self, conditions: dict[str, Any]) -> bool:
        """Check if this state satisfies all required preconditions."""
        for k, v in conditions.items():
            current_val = self._state.get(k)
            if isinstance(v, (int, float)) and isinstance(current_val, (int, float)):
                # If precondition specifies a numerical requirement, current must be >= required
                if current_val < v:
                    return False
            else:
                if current_val != v:
                    return False
        return True

    def apply_effects(self, effects: dict[str, Any]) -> WorldState:
        """Create a new state resulting from applying action effects."""
        new_state = dict(self._state)
        for k, v in effects.items():
            if isinstance(v, (int, float)) and k in new_state and isinstance(new_state[k], (int, float)):
                # Relative delta if key already exists as numeric
                new_state[k] = new_state[k] + v
            else:
                new_state[k] = v
        return WorldState(new_state)

    def to_tuple(self) -> tuple:
        """Hashable representation for visited state sets."""
        return tuple(sorted((k, str(v)) for k, v in self._state.items()))


class GOAPPlanner:
    """Finds optimal sequence of actions from initial state to goal state using A* search."""

    def __init__(self, available_actions: list[ActionDefinition]) -> None:
        self.actions = available_actions

    def plan(
        self,
        initial_state: WorldState,
        goal_conditions: dict[str, Any],
        max_iterations: int = 500,
    ) -> Optional[list[ActionDefinition]]:
        """A* search for a valid sequence of actions reaching goal_conditions."""
        # Priority queue entries: (f_score, g_score, state_tuple, path, current_state)
        start_h = self._heuristic(initial_state, goal_conditions)
        pq: list[tuple[float, float, int, list[ActionDefinition], WorldState]] = [
            (start_h, 0.0, 0, [], initial_state)
        ]
        visited: set[tuple] = set()
        tie_breaker = 0

        iterations = 0
        while pq and iterations < max_iterations:
            iterations += 1
            f, g, _, path, current_state = heapq.heappop(pq)

            if current_state.satisfies(goal_conditions):
                return path

            state_key = current_state.to_tuple()
            if state_key in visited:
                continue
            visited.add(state_key)

            for act in self.actions:
                if current_state.satisfies(act.preconditions):
                    next_state = current_state.apply_effects(act.effects)
                    next_key = next_state.to_tuple()
                    if next_key not in visited:
                        next_g = g + act.cost
                        next_h = self._heuristic(next_state, goal_conditions)
                        tie_breaker += 1
                        heapq.heappush(
                            pq,
                            (next_g + next_h, next_g, tie_breaker, path + [act], next_state),
                        )

        return None

    def plan_with_epistemic_bounds(
        self,
        initial_state: WorldState,
        goal_conditions: dict[str, Any],
        knowledge_graph: Optional[Any] = None,
        agent_skills: Optional[dict[str, float]] = None,
        allow_epistemic_learning: bool = True,
        max_depth: int = 8,
        max_iterations: int = 500,
    ) -> tuple[Optional[list[ActionDefinition]], list[str]]:
        """A* planning strictly constrained by agent's knowledge and skill proficiencies.

        If an action requires an unknown capability:
        - If allow_epistemic_learning is True, synthesizes precursor epistemic actions.
        - Otherwise, action is filtered out.
        Returns (plan, missing_or_learned_capabilities).
        """
        agent_skills = agent_skills or {}
        active_actions = list(self.actions)
        capabilities_learned: list[str] = []

        # Filter or augment actions based on epistemic capabilities
        if knowledge_graph is not None:
            augmented_actions: list[ActionDefinition] = []
            for act in active_actions:
                missing_caps = [
                    cap for cap in act.required_capabilities
                    if not (hasattr(knowledge_graph, "knows_concept") and knowledge_graph.knows_concept(cap, min_confidence=0.3))
                ]
                if not missing_caps:
                    augmented_actions.append(act)
                elif allow_epistemic_learning:
                    # Synthesize learning action
                    for cap in missing_caps:
                        learn_act = ActionDefinition(
                            action_id=f"learn_{cap}",
                            name=f"Study and acquire {cap}",
                            preconditions={},
                            effects={f"knows_{cap}": True},
                            cost=2.0,
                            duration_ticks=2,
                        )
                        if learn_act not in augmented_actions:
                            augmented_actions.append(learn_act)
                            capabilities_learned.append(cap)
                    # Add original action with updated precondition
                    new_preconds = dict(act.preconditions)
                    for cap in missing_caps:
                        new_preconds[f"knows_{cap}"] = True
                    augmented_actions.append(
                        ActionDefinition(
                            action_id=act.action_id,
                            name=act.name,
                            preconditions=new_preconds,
                            effects=act.effects,
                            cost=act.cost,
                            duration_ticks=act.duration_ticks,
                            required_capabilities=act.required_capabilities,
                            resource_costs=act.resource_costs,
                        )
                    )
            active_actions = augmented_actions

        planner = GOAPPlanner(available_actions=active_actions)
        plan = planner.plan(initial_state, goal_conditions, max_iterations=max_iterations)
        return plan, capabilities_learned

    def _heuristic(self, state: WorldState, goal: dict[str, Any]) -> float:
        """Estimate distance from current state to goal state."""
        h = 0.0
        for k, v in goal.items():
            curr = state.get(k)
            if curr is None:
                h += 1.0
            elif isinstance(v, (int, float)) and isinstance(curr, (int, float)):
                if curr < v:
                    h += float(v - curr)
            elif curr != v:
                h += 1.0
        return h
