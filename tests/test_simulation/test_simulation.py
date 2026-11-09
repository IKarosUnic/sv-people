"""Tests for simulation loop execution, reproducibility, and resource budgets."""

import tempfile
from pathlib import Path

from saltbor.core.config import SimulationConfig
from saltbor.simulation.runner import SimulationRunner


def test_simulation_execution_and_metrics():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = Path(tf.name)

    try:
        cfg = SimulationConfig(
            random_seed=42,
            initial_population_size=20,
            database_path=db_path,
            checkpoint_interval_ticks=10,
        )
        runner = SimulationRunner(config=cfg)
        runner.initialize()

        # Run for 20 ticks
        runner.run(num_ticks=20)
        assert runner.clock.current_tick == 20

        # Check performance metrics
        summary = runner.metrics.get_summary()
        assert summary["total_ticks_recorded"] == 20
        assert summary["average_tick_latency_ms"] < 50.0  # Must be fast (<50ms per tick)
        assert summary["target_1mb_compliance"] is True   # Under 1MB logical memory
        assert summary["memory_per_human_kb"] < 1024.0

        runner.close()
    finally:
        try:
            db_path.unlink()
        except OSError:
            pass


def test_reproducibility_with_seed():
    """Identical random seeds produce identical simulation state trajectories."""
    def run_trajectory(seed: int) -> list[str]:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            db_path = Path(tf.name)
        try:
            cfg = SimulationConfig(
                random_seed=seed,
                initial_population_size=20,
                database_path=db_path,
            )
            runner = SimulationRunner(config=cfg)
            runner.initialize()
            runner.run(num_ticks=8)
            # Record detailed state across all humans
            trajectory = [
                f"{h.identity.serial}:{h.physical_state.current_location_id}:{h.physical_state.energy:.4f}:{h.physical_state.money:.2f}"
                for h in runner.population.get_all()
            ]
            runner.close()
            return trajectory
        finally:
            try:
                db_path.unlink()
            except OSError:
                pass

    traj1 = run_trajectory(seed=12345)
    traj2 = run_trajectory(seed=12345)
    traj3 = run_trajectory(seed=99999)

    assert traj1 == traj2, "Same seed must produce deterministic identical trajectory."
    # Different seed should diverge
    assert traj1 != traj3 or len(traj1) == 0
