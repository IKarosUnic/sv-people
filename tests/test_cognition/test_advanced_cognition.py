"""Unit tests for Formal Decision Architecture, GOAP, and HTN Planning (Phase 0.4)."""

import uuid
import pytest
import numpy as np

from saltbor.cognition.decision.formal_decision import (
    FormalDecisionArchitecture,
    InformationState,
    InternalState,
    WorldBeliefs,
)
from saltbor.cognition.planning.goap import (
    ActionDefinition,
    GOAPPlanner,
    WorldState,
)
from saltbor.cognition.planning.htn import (
    DynamicReplanner,
    HTNDecomposer,
    build_carpentry_workshop_htn,
)
from saltbor.core.types import ActivityType, NeedType


def test_formal_maut_decision_architecture():
    """Verify MAUT formal decision architecture separates state, beliefs, preferences, and consequences."""
    rng = np.random.default_rng(42)
    arch = FormalDecisionArchitecture(rng=rng)

    internal = InternalState(
        energy=0.2, # Highly exhausted
        hunger=0.8, # Very hungry
        health=0.9,
        money=15.0,
        needs={NeedType.HUNGER: 0.8, NeedType.REST: 0.8},
    )
    beliefs = WorldBeliefs(
        estimated_food_cost=5.0,
        location_aversions={},
        location_affinities={"casa_residencial_1": 0.3},
    )
    info = InformationState(
        current_location_id="plaza_mayor",
        available_activities=[ActivityType.SLEEP, ActivityType.EAT, ActivityType.WORK, ActivityType.RELAX],
        nearby_humans=[],
        is_daytime=False,
        current_hour=23,
        home_location_id="casa_residencial_1",
        work_location_id="taller_el_roble",
    )

    traits = {"conscientiousness": 0.7, "neuroticism": 0.4, "risk_tolerance": 0.3}
    emotions = {"anxiety": 0.2, "loneliness": 0.1}
    prefs = arch.derive_preference_weights(traits, emotions, mood=0.0)

    # Evaluate candidates
    candidates = [
        arch.evaluate_candidate(act, info.home_location_id if act == ActivityType.SLEEP else info.current_location_id,
                                internal, beliefs, info, prefs, set())
        for act in info.available_activities
    ]

    # Given exhaustion at 23:00 at night, SLEEP should have top utility
    chosen, trace = arch.select_action(candidates, exploration_temperature=0.05)
    assert chosen.action_type in (ActivityType.SLEEP, ActivityType.EAT)
    assert len(trace.alternatives_evaluated) == 4
    assert len(trace.dominant_factors) > 0


def test_goap_planner_action_sequence():
    """Verify GOAP planner discovers optimal sequence of actions to reach goal state."""
    # Actions
    act_gather_wood = ActionDefinition(
        action_id="gather_wood",
        name="Gather Wood",
        preconditions={"stamina": 1},
        effects={"wood": 2, "stamina": -1},
        cost=2.0,
    )
    act_buy_nails = ActionDefinition(
        action_id="buy_nails",
        name="Buy Nails",
        preconditions={"money": 5},
        effects={"nails": 10, "money": -5},
        cost=1.0,
    )
    act_craft_table = ActionDefinition(
        action_id="craft_table",
        name="Craft Table",
        preconditions={"wood": 2, "nails": 10},
        effects={"table": 1, "wood": -2, "nails": -10},
        cost=3.0,
    )

    planner = GOAPPlanner([act_gather_wood, act_buy_nails, act_craft_table])

    initial = WorldState({"stamina": 2, "money": 10, "wood": 0, "nails": 0, "table": 0})
    goal = {"table": 1}

    plan = planner.plan(initial, goal)
    assert plan is not None
    assert len(plan) == 3
    action_ids = [a.action_id for a in plan]
    assert "craft_table" == action_ids[-1]
    assert "gather_wood" in action_ids
    assert "buy_nails" in action_ids


def test_htn_decomposition_and_dynamic_replanning():
    """Verify HTN multi-stage carpentry workshop decomposition and replanning upon obstacle."""
    root_task = build_carpentry_workshop_htn()
    decomposer = HTNDecomposer()
    replanner = DynamicReplanner(decomposer)

    # Scenario: Agent starts with no money and market has tools
    state_no_money = WorldState({
        "money": 0.0,
        "market_has_tools": True,
        "market_has_wood": True,
        "trusted_partner_available": True,
    })

    plan = decomposer.decompose(root_task, state_no_money)
    assert plan is not None
    step_names = [a.action_id for a in plan]
    assert "assess_finances" in step_names
    assert "work_wages" in step_names # Must work for wages first to afford tools & premises
    assert "buy_tools" in step_names
    assert "start_operations" in step_names

    # Dynamic replanning: Suppose the agent is about to execute buy_tools, but market is out of tools!
    state_shortage = WorldState({
        "money": 30.0,
        "market_has_tools": False, # Precondition fails!
        "market_has_wood": True,
        "trusted_partner_available": True,
    })
    buy_step = [a for a in plan if a.action_id == "buy_tools"][0]

    valid, new_plan, reason = replanner.check_and_replan(buy_step, root_task, state_shortage)
    assert valid is False
    assert "Precondition failed" in reason
