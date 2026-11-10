"""Unit tests for Continuous Movement, Collision Avoidance, and Encounters (Phase 0.4)."""

import uuid
import math
import pytest

from saltbor.world.spatial.actions import PhysicalActionState, PhysicalPosture
from saltbor.world.spatial.encounters import EncounterDetector
from saltbor.world.spatial.movement import (
    AgentSpatialState,
    ContinuousMovementEngine,
)


def test_continuous_path_following_and_arrival():
    """Verify agent navigates through intermediate waypoints and signals arrival."""
    agent = AgentSpatialState(
        human_uid=uuid.uuid4(),
        x=0.0,
        y=0.0,
        base_speed_mps=2.0,
    )
    engine = ContinuousMovementEngine()

    # Destination via waypoint (5, 0) to (10, 0)
    agent.set_destination((10.0, 0.0), waypoints=[(5.0, 0.0), (10.0, 0.0)])
    assert agent.is_moving is True

    # Advance 2 seconds (covers 4 metres, nearing waypoint 1)
    arrived = engine.step_agent(agent, dt_seconds=2.0, nearby_agents=[])
    assert arrived is False
    assert agent.x > 3.0

    # Advance more to reach second waypoint and arrive
    for _ in range(10):
        if engine.step_agent(agent, dt_seconds=1.0, nearby_agents=[]):
            break

    assert agent.is_moving is False
    assert agent.x == pytest.approx(10.0, abs=0.5)


def test_collision_avoidance_steering():
    """Verify agents walking toward each other steer to avoid collision."""
    agent_a = AgentSpatialState(human_uid=uuid.uuid4(), x=0.0, y=0.0)
    agent_b = AgentSpatialState(human_uid=uuid.uuid4(), x=2.0, y=0.0)

    agent_a.set_destination((5.0, 0.0))
    agent_b.set_destination((-5.0, 0.0))

    engine = ContinuousMovementEngine(avoidance_radius=2.5)

    # Step simulation
    for _ in range(5):
        engine.step_agent(agent_a, dt_seconds=0.2, nearby_agents=[agent_b])
        engine.step_agent(agent_b, dt_seconds=0.2, nearby_agents=[agent_a])

    # Distance should remain >= personal space (no overlapping x, y = exact same)
    d = math.hypot(agent_a.x - agent_b.x, agent_a.y - agent_b.y)
    assert d > 0.4 # Kept separated


def test_encounter_detection_and_interaction_trigger():
    """Verify encounter detection within radius and cooldown filtering."""
    detector = EncounterDetector(encounter_radius=3.0)
    uid_a = uuid.uuid4()
    uid_b = uuid.uuid4()

    a1 = AgentSpatialState(human_uid=uid_a, x=10.0, y=10.0)
    b1 = AgentSpatialState(human_uid=uid_b, x=11.5, y=10.0) # 1.5m apart

    encounters = detector.detect_encounters([a1, b1], current_tick=10)
    assert len(encounters) == 1
    assert encounters[0].distance_meters == pytest.approx(1.5, 0.1)

    # Immediate second call should be suppressed by cooldown
    encounters_repeat = detector.detect_encounters([a1, b1], current_tick=11)
    assert len(encounters_repeat) == 0

    # Interaction trigger check
    should_chat = detector.should_initiate_interaction(familiarity=0.8, affinity=0.7, extraversion=0.6)
    assert should_chat is True


def test_physical_action_burden_penalty():
    """Verify carrying heavy loads imposes walking speed penalty."""
    state_light = PhysicalActionState(carried_weight_kg=2.0, max_carry_capacity_kg=20.0)
    state_heavy = PhysicalActionState(carried_weight_kg=18.0, max_carry_capacity_kg=20.0)

    assert state_light.speed_penalty_factor > 0.90
    assert state_heavy.speed_penalty_factor < 0.65
