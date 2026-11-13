"""Comprehensive test suite for Multi-level LOD, Spatial Partitioning, and Large-Scale Simulation Architecture."""

import os
import tempfile
import time
import pytest
import numpy as np

from saltbor.cognition.memory.semantic import SemanticFact
from saltbor.persistence.database import DatabaseManager
from saltbor.persistence.multilevel_persistence import MultilevelPersistenceEngine
from saltbor.population.multilevel.aggregation import PopulationAggregator
from saltbor.population.multilevel.models import (
    CommunityAggregate,
    LODLevel,
    PersistentIndividualRecord,
    PopulationTier,
)
from saltbor.population.multilevel.population_manager import MultilevelPopulationManager
from saltbor.simulation.benchmarks.million_benchmark import MillionAgentBenchmark
from saltbor.simulation.multilevel.scalable_scheduler import ScalableMultilevelScheduler
from saltbor.world.spatial.multi_partition import (
    HierarchicalSpatialQuadtree,
    SpatialEntity,
    SpatialPartitionManager,
    UniformSpatialGrid,
)


def test_four_population_tiers_integrity():
    """Verify strict separation and non-equivalence among the 4 population tiers."""
    spatial = SpatialPartitionManager(cell_size=0.005)
    manager = MultilevelPopulationManager(spatial_manager=spatial)

    records = MillionAgentBenchmark.generate_synthetic_population(count=200, seed=123)
    manager.register_batch(records)

    # 1. Total persistent count must equal 200
    assert manager.persistent_count == 200

    # 2. Before hydration, active simulated is 0
    assert manager.active_simulated_count == 0
    assert manager.aggregated_count == 200
    assert manager.rendered_count == 0

    # 3. Promote 5 individuals to LOD 0
    for i in range(5):
        manager.promote_to_active(f"agent_{i:07d}", LODLevel.LOD_0_INDIVIDUAL)

    assert manager.active_simulated_count == 5
    assert manager.aggregated_count == 195

    summary = manager.get_tier_summary()
    assert summary["persistent_population"] == 200
    assert summary["actively_simulated"] == 5
    assert summary["aggregated_population"] == 195


def test_multilevel_lod_hydration_dehydration_roundtrip():
    """Verify that promoting an individual to LOD 0 and demoting it preserves all identity and state."""
    spatial = SpatialPartitionManager(cell_size=0.005)
    manager = MultilevelPopulationManager(spatial_manager=spatial)

    rec = PersistentIndividualRecord(
        uid="test_agent_001",
        serial=101,
        given_name="Guillermo",
        family_name="Ungos",
        gender="male",
        age_years=42.5,
        occupation="Líder Comunitario",
        current_location_id="casa_este_1",
        lat=13.6980,
        lon=-89.1920,
        wealth=185.50,
        health=0.92,
        energy=0.75,
        hunger=0.25,
        happiness=0.60,
        lod_tier=int(LODLevel.LOD_2_COHORT_GROUP),
        is_exceptional=True,
        exception_reason="Presidente Junta Vecinal",
    )
    manager.register_individual(rec)

    # 1. Promote to active LOD 0 (Hydration)
    human = manager.promote_to_active("test_agent_001", LODLevel.LOD_0_INDIVIDUAL)
    assert human is not None
    assert human.identity.serial == 101
    assert human.identity.given_name == "Guillermo"
    assert human.demographics.occupation == "Líder Comunitario"
    assert human.physical_state.money == 185.50
    assert rec.lod_tier == int(LODLevel.LOD_0_INDIVIDUAL)

    # 2. Modify dynamic state in active simulation
    human.physical_state.money += 50.0  # Earned money
    human.physical_state.hunger = 0.40  # Grew hungrier
    human.memory.semantic.store(SemanticFact(
        fact_id="test_fact",
        category="cultural",
        content="Comunidad construyó puente peatonal",
        confidence=0.95,
        source="news",
        learned_tick=1,
    ))

    # 3. Demote back to aggregated state (Dehydration)
    manager.demote_to_aggregated("test_agent_001", LODLevel.LOD_2_COHORT_GROUP)
    assert "test_agent_001" not in manager._active_humans
    assert rec.lod_tier == int(LODLevel.LOD_2_COHORT_GROUP)

    # Check that state updates were synchronized to persistent record
    assert rec.wealth == 235.50
    assert rec.hunger == 0.40
    assert rec.packed_cognitive_state is not None
    assert b"puente peatonal" in rec.packed_cognitive_state

    # 4. Re-promote and verify fact restored
    human_restored = manager.promote_to_active("test_agent_001", LODLevel.LOD_0_INDIVIDUAL)
    assert human_restored.physical_state.money == 235.50
    semantic_facts = [f.content for f in human_restored.memory.semantic.get_all()]
    assert any("puente peatonal" in f for f in semantic_facts)


def test_preservation_of_exceptional_individuals():
    """Verify that community leaders, VIPs, and extreme distress individuals are preserved in aggregates."""
    records = MillionAgentBenchmark.generate_synthetic_population(count=100, seed=42)

    # Mark specific individual as exceptional leader
    records[0].is_exceptional = True
    records[0].exception_reason = "Alcalde Comunal"

    # Mark another individual with extreme health distress
    records[1].health = 0.15

    agg = PopulationAggregator.aggregate_to_community(
        community_id="comm_01",
        name="Barrio San Jacinto",
        district_id="distrito_san_salvador",
        center_lat=13.695,
        center_lon=-89.190,
        records=records,
    )

    # Both exceptional agents must be explicitly preserved in exceptional_uids
    assert records[0].uid in agg.exceptional_uids
    assert records[1].uid in agg.exceptional_uids
    assert len(agg.exceptional_uids) >= 2


def test_mathematical_aggregation_moments():
    """Verify Gini index calculation and aggregate resource dynamics."""
    # Equality test (all have 100) -> Gini = 0.0
    gini_equal = PopulationAggregator.calculate_gini([100.0] * 50)
    assert round(gini_equal, 2) == 0.0

    # Extreme inequality test
    gini_unequal = PopulationAggregator.calculate_gini([1.0] * 99 + [10000.0])
    assert gini_unequal > 0.85

    # Test community dynamics consumption and production
    comm = CommunityAggregate(
        community_id="comm_test",
        district_id="dist_test",
        name="Test Community",
        center_lat=13.69,
        center_lon=-89.19,
        total_population=1000,
        age_cohorts=[50] * 18,
        food_reserves_kg=5000.0,
        water_reserves_liters=20000.0,
    )
    PopulationAggregator.step_community_dynamics(comm, dt_ticks=32, ambient_temp_c=28.0)
    # Resources must have been consumed
    assert comm.water_reserves_liters < 20000.0
    assert comm.daily_production_units > 0.0


def test_spatial_partitioning_quadtree_and_grid():
    """Verify UniformGrid and Quadtree radius and viewport queries."""
    grid = UniformSpatialGrid(cell_size=0.005)
    quadtree = HierarchicalSpatialQuadtree(capacity=16, max_depth=6)

    e1 = SpatialEntity(uid="e1", x=-89.1915, y=13.6978)
    e2 = SpatialEntity(uid="e2", x=-89.1918, y=13.6980) # ~40m away
    e3 = SpatialEntity(uid="e3", x=-89.3000, y=13.8000) # Far away

    for e in (e1, e2, e3):
        grid.insert(e)
        quadtree.insert(e)

    # Query radius ~100m (0.001 deg) around e1
    grid_nearby = grid.query_radius(-89.1915, 13.6978, radius=0.001)
    quad_nearby = quadtree.query_radius(-89.1915, 13.6978, radius=0.001)

    grid_uids = {ent.uid for ent in grid_nearby}
    quad_uids = {ent.uid for ent in quad_nearby}

    assert "e1" in grid_uids and "e2" in grid_uids
    assert "e3" not in grid_uids
    assert "e1" in quad_uids and "e2" in quad_uids
    assert "e3" not in quad_uids


def test_multilevel_persistence_sqlite_wal():
    """Verify high-throughput batch insertion and indexed retrieval in SQLite WAL mode."""
    temp_db = os.path.join(tempfile.gettempdir(), f"saltbor_test_persist_{time.time_ns()}.db")
    db = DatabaseManager(temp_db)
    try:
        db.connect()
        engine = MultilevelPersistenceEngine(db)

        records = MillionAgentBenchmark.generate_synthetic_population(count=2000, seed=99)
        engine.save_batch(records, chunk_size=1000)

        assert engine.count_total() == 2000

        # Load individual
        rec = engine.load_record("agent_0000010")
        assert rec is not None
        assert rec.serial == 11

        # Query by district index
        district_records = engine.load_by_district("distrito_san_salvador", limit=500)
        assert len(district_records) > 0
        assert district_records[0].district_id == "distrito_san_salvador"
    finally:
        db.close()
        for ext in ("", "-wal", "-shm"):
            p = temp_db + ext
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


def test_scalable_scheduler_priority_and_decimation():
    """Verify priority queue processing and promotion of targeted individuals."""
    spatial = SpatialPartitionManager(cell_size=0.005)
    manager = MultilevelPopulationManager(spatial_manager=spatial)
    records = MillionAgentBenchmark.generate_synthetic_population(count=100, seed=55)
    manager.register_batch(records)

    scheduler = ScalableMultilevelScheduler(manager=manager, random_seed=42)

    callback_ran = []

    # Schedule event at tick 5 targeting agent_0000075
    scheduler.schedule_event(
        tick=5,
        event_type="community_assembly",
        target_uids=["agent_0000075"],
        priority=1,
        callback=lambda payload: callback_ran.append(payload),
        payload={"topic": "Agua potable"},
    )

    # Step ticks 1 to 4 -> event should not fire yet
    for t in range(1, 5):
        scheduler.step(t)
    assert len(callback_ran) == 0
    assert "agent_0000075" not in manager._active_humans

    # Step tick 5 -> event must fire and agent_0000075 must be promoted to active
    scheduler.step(5)
    assert len(callback_ran) == 1
    assert "agent_0000075" in manager._active_humans


def test_viewport_streaming_lod_modes():
    """Verify viewport streaming delivers appropriate LOD modes according to zoom level."""
    spatial = SpatialPartitionManager(cell_size=0.005)
    manager = MultilevelPopulationManager(spatial_manager=spatial)
    records = MillionAgentBenchmark.generate_synthetic_population(count=500, seed=77)
    manager.register_batch(records)

    comm = CommunityAggregate(
        community_id="comm_01",
        district_id="distrito_san_salvador",
        name="Centro",
        center_lat=13.6978,
        center_lon=-89.1915,
        total_population=500,
    )
    manager.register_community(comm)

    # 1. Macro Zoom (zoom = 11) -> regional density
    macro_res = manager.query_viewport_population(-89.21, 13.69, -89.18, 13.71, zoom=11.0)
    assert macro_res["render_mode"] == "regional_density"

    # 2. Meso Zoom (zoom = 14) -> cohort clusters
    meso_res = manager.query_viewport_population(-89.21, 13.69, -89.18, 13.71, zoom=14.0)
    assert meso_res["render_mode"] == "cohort_clusters"
    assert meso_res["count"] >= 1

    # 3. Micro Zoom (zoom = 16) -> individual tokens
    micro_res = manager.query_viewport_population(-89.21, 13.69, -89.18, 13.71, zoom=16.0)
    assert micro_res["render_mode"] == "individual_tokens"
    assert micro_res["count"] > 0
    assert "uid" in micro_res["data"][0]
