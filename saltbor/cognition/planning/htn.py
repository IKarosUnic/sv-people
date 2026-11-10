"""Hierarchical Task Network (HTN) planner with dynamic replanning upon failed preconditions."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from saltbor.cognition.planning.goap import ActionDefinition, WorldState

logger = logging.getLogger(__name__)


@dataclass
class HTNTask:
    """A task node in the hierarchical network (primitive or compound)."""

    task_id: str
    name: str
    is_compound: bool = False
    preconditions: dict[str, Any] = field(default_factory=dict)
    subtasks: list[HTNTask] = field(default_factory=list)
    action: Optional[ActionDefinition] = None
    fallback_tasks: list[HTNTask] = field(default_factory=list)


class HTNDecomposer:
    """Recursively decomposes compound high-level objectives into executable primitive actions."""

    def decompose(self, task: HTNTask, current_state: WorldState) -> Optional[list[ActionDefinition]]:
        """Decompose a high-level goal into a linear plan of primitive actions."""
        if not task.is_compound:
            if current_state.satisfies(task.preconditions) and task.action:
                return [task.action]
            return None

        # Compound task: decompose subtasks
        plan: list[ActionDefinition] = []
        simulated_state = WorldState(dict(current_state._state))

        for sub in task.subtasks:
            sub_plan = self.decompose(sub, simulated_state)
            if sub_plan is not None:
                plan.extend(sub_plan)
                for act in sub_plan:
                    simulated_state = simulated_state.apply_effects(act.effects)
            else:
                # Subtask failed preconditions: attempt fallback tasks
                recovered = False
                for fb in sub.fallback_tasks:
                    fb_plan = self.decompose(fb, simulated_state)
                    if fb_plan is not None:
                        plan.extend(fb_plan)
                        for act in fb_plan:
                            simulated_state = simulated_state.apply_effects(act.effects)
                        recovered = True
                        break
                if not recovered:
                    return None

        return plan


class DynamicReplanner:
    """Detects failed preconditions during execution and dynamically replans."""

    def __init__(self, decomposer: Optional[HTNDecomposer] = None) -> None:
        self.decomposer = decomposer or HTNDecomposer()

    def check_and_replan(
        self,
        current_step: ActionDefinition,
        high_level_task: HTNTask,
        current_state: WorldState,
    ) -> tuple[bool, Optional[list[ActionDefinition]], str]:
        """Check if current step preconditions hold. If violated, compute alternative plan.

        Returns (is_valid: bool, new_plan: Optional[list[ActionDefinition]], reason: str).
        """
        if current_state.satisfies(current_step.preconditions):
            return True, None, "Preconditions satisfied"

        # Precondition failed: identify missing variable
        missing = [
            f"{k} (need {v}, have {current_state.get(k)})"
            for k, v in current_step.preconditions.items()
            if not current_state.satisfies({k: v})
        ]
        reason = f"Precondition failed: {', '.join(missing)}"
        logger.info("Dynamic replanning triggered: %s", reason)

        # Replan from current state
        new_plan = self.decomposer.decompose(high_level_task, current_state)
        return False, new_plan, reason


def build_carpentry_workshop_htn() -> HTNTask:
    """Builds standard HTN compound task for establishing a carpentry workshop (Section 3 & Exp D)."""
    # Primitive actions
    act_assess = ActionDefinition(
        action_id="assess_finances",
        name="Assess Financial Situation",
        preconditions={},
        effects={"finances_assessed": True},
    )
    act_work_wages = ActionDefinition(
        action_id="work_wages",
        name="Work Day Shifts for Wages",
        preconditions={},
        effects={"money": 50.0},
    )
    act_borrow = ActionDefinition(
        action_id="borrow_funds",
        name="Borrow Funds from Trusted Partner",
        preconditions={"trusted_partner_available": True},
        effects={"money": 50.0, "has_debt": True},
    )
    act_buy_tools = ActionDefinition(
        action_id="buy_tools",
        name="Purchase Carpentry Tools at Market",
        preconditions={"money": 25.0, "market_has_tools": True},
        effects={"money": -25.0, "has_tools": True},
    )
    act_find_premises = ActionDefinition(
        action_id="find_premises",
        name="Locate and Rent Workshop Space",
        preconditions={"money": 15.0},
        effects={"money": -15.0, "has_premises": True},
    )
    act_buy_materials = ActionDefinition(
        action_id="buy_materials",
        name="Acquire Timber at Market",
        preconditions={"money": 10.0, "market_has_wood": True},
        effects={"money": -10.0, "has_wood": True},
    )
    act_start_operations = ActionDefinition(
        action_id="start_operations",
        name="Commence Carpentry Production",
        preconditions={"has_tools": True, "has_premises": True, "has_wood": True},
        effects={"workshop_established": True},
    )

    # Subtask: Obtain Capital (Work or Borrow fallback)
    sub_borrow = HTNTask(task_id="t_borrow", name="Borrow Money", action=act_borrow, preconditions=act_borrow.preconditions)
    sub_work = HTNTask(
        task_id="t_work",
        name="Work for Wages",
        action=act_work_wages,
        preconditions=act_work_wages.preconditions,
        fallback_tasks=[sub_borrow],
    )

    # Subtask: Obtain Tools
    sub_tools = HTNTask(task_id="t_tools", name="Acquire Tools", action=act_buy_tools, preconditions=act_buy_tools.preconditions)

    # Subtask: Secure Premises
    sub_premises = HTNTask(task_id="t_premises", name="Secure Premises", action=act_find_premises, preconditions=act_find_premises.preconditions)

    # Subtask: Acquire Wood
    sub_wood = HTNTask(task_id="t_wood", name="Acquire Timber", action=act_buy_materials, preconditions=act_buy_materials.preconditions)

    # Subtask: Launch
    sub_launch = HTNTask(task_id="t_launch", name="Start Operations", action=act_start_operations, preconditions=act_start_operations.preconditions)

    # Root compound task
    root = HTNTask(
        task_id="root_carpentry_workshop",
        name="Establish Carpentry Workshop",
        is_compound=True,
        subtasks=[
            HTNTask(task_id="t_assess", name="Assess", action=act_assess),
            sub_work,
            sub_tools,
            sub_premises,
            sub_wood,
            sub_launch,
        ],
    )
    return root
