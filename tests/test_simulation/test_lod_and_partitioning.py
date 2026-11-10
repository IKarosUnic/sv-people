"""Unit tests for Cognitive LOD and Spatial Grid Partitioning (Phase 0.4)."""

import uuid
import pytest

from saltbor.core.types import ActivityType
from saltbor.population.lod import CognitiveLOD, CognitiveLODManager
from saltbor.world.spatial.grid import SpatialGridPartition


def test_cognitive_lod_tier_transitions():
    """Verify dynamic assignment of LOD tiers based on agent state and activity."""
    manager = CognitiveLODManager()
    uid = uuid.uuid4()

    # Living agent with no active activity -> LOD 0 (deliberation)
    tier = manager.evaluate_lod(uid, is_alive=True, current_activity=None, activity_ticks_remaining=0)
    assert tier == CognitiveLOD.LOD_0_FULL
    assert manager.should_execute_tick(uid) is True

    # Long sleep activity -> LOD 2 (event driven macro-step)
    tier_sleep = manager.evaluate_lod(
        uid, is_alive=True, current_activity=ActivityType.SLEEP, activity_ticks_remaining=8
    )
    assert tier_sleep == CognitiveLOD.LOD_2_EVENT_DRIVEN

    # Routine work activity -> LOD 1 (routine execution)
    tier_work = manager.evaluate_lod(
        uid, is_alive=True, current_activity=ActivityType.WORK, activity_ticks_remaining=3
    )
    assert tier_work == CognitiveLOD.LOD_1_ROUTINE

    # Deceased individual -> LOD 3 (dormant historical state)
    tier_dead = manager.evaluate_lod(uid, is_alive=False, current_activity=None, activity_ticks_remaining=0)
    assert tier_dead == CognitiveLOD.LOD_3_DORMANT
    assert manager.should_execute_tick(uid) is False # Zero compute


def test_spatial_grid_partition_radius_query():
    """Verify spatial 2D grid correctly partitions coordinates and retrieves radius neighbors."""
    grid = SpatialGridPartition(cell_size=20.0, width=500.0, height=500.0)

    u1 = uuid.uuid4()
    u2 = uuid.uuid4()
    u3 = uuid.uuid4()

    positions = {
        u1: (100.0, 100.0),
        u2: (105.0, 100.0), # 5 metres away from u1
        u3: (200.0, 200.0), # far away (~141 metres)
    }

    grid.insert(u1, 100.0, 100.0)
    grid.insert(u2, 105.0, 100.0)
    grid.insert(u3, 200.0, 200.0)

    # Query with radius 10m around u1 (100, 100)
    nearby_10m = grid.query_radius(100.0, 100.0, 10.0, positions)
    assert u1 in nearby_10m
    assert u2 in nearby_10m
    assert u3 not in nearby_10m

    # Move u2 far away and verify update
    positions[u2] = (300.0, 300.0)
    grid.update_position(u2, 300.0, 300.0)

    nearby_after_move = grid.query_radius(100.0, 100.0, 10.0, positions)
    assert u1 in nearby_after_move
    assert u2 not in nearby_after_move
