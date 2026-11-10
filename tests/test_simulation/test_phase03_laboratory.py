"""Automated tests for Phase 0.3 Autonomous Simulation Laboratory & Behavioral Validation."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from saltbor.core.config import SimulationConfig
from saltbor.simulation.laboratory.lab import SimulationLaboratory
from saltbor.simulation.benchmarks.benchmark import PopulationBenchmark


@pytest.fixture
def lab_instance() -> SimulationLaboratory:
    temp_dir = Path(tempfile.mkdtemp())
    cfg = SimulationConfig(random_seed=42, database_path=temp_dir / "test_lab.db")
    return SimulationLaboratory(config=cfg)


def test_simulation_reproducibility(lab_instance: SimulationLaboratory) -> None:
    """Experiments executed with identical seeds must yield identical trajectories."""
    sim1 = lab_instance.start_simulation(seed=1234)
    for _ in range(20):
        sim1.step()
    h1 = sim1.population.get_by_serial(1)
    money_1 = h1.physical_state.money
    energy_1 = h1.physical_state.energy
    loc_1 = h1.physical_state.current_location_id
    sim1.close()

    # Re-run from identical seed
    sim2 = lab_instance.start_simulation(seed=1234)
    for _ in range(20):
        sim2.step()
    h2 = sim2.population.get_by_serial(1)
    money_2 = h2.physical_state.money
    energy_2 = h2.physical_state.energy
    loc_2 = h2.physical_state.current_location_id
    sim2.close()

    assert money_1 == pytest.approx(money_2, abs=1e-5)
    assert energy_1 == pytest.approx(energy_2, abs=1e-5)
    assert loc_1 == loc_2


def test_behavioral_experiment_a_autonomy(lab_instance: SimulationLaboratory) -> None:
    res = lab_instance.run_experiment("EXP_A", duration_ticks=48)
    assert res.success is True
    assert res.metrics["final_active_goals"] > 0 or res.metrics["goals_completed"] > 0


def test_behavioral_experiment_b_personality(lab_instance: SimulationLaboratory) -> None:
    res = lab_instance.run_experiment("EXP_B")
    assert res.success is True
    assert res.metrics["p1_neuroticism_drift"] > 0.005
    assert abs(res.metrics["p2_neuroticism_drift"]) < 0.001


def test_behavioral_experiment_c_memory(lab_instance: SimulationLaboratory) -> None:
    res = lab_instance.run_experiment("EXP_C")
    assert res.success is True
    assert res.metrics["location_valence"] < -0.3


def test_behavioral_experiment_d_social(lab_instance: SimulationLaboratory) -> None:
    res = lab_instance.run_experiment("EXP_D")
    assert res.success is True
    assert res.metrics["bonded_trust"] > res.metrics["initial_trust"]
    assert res.metrics["conflict_trust"] < res.metrics["bonded_trust"]


def test_behavioral_experiment_e_adaptation(lab_instance: SimulationLaboratory) -> None:
    res = lab_instance.run_experiment("EXP_E")
    assert res.success is True
    assert res.metrics["normal_choice"] == "eat"
    assert res.metrics["shock_choice"] == "cook"


def test_behavioral_experiment_f_conflicts(lab_instance: SimulationLaboratory) -> None:
    res = lab_instance.run_experiment("EXP_F")
    assert res.success is True
    assert res.metrics["workaholic_choice"] == "work"
    assert res.metrics["fatigued_choice"] in ("rest", "sleep")


def test_behavioral_experiment_g_long_term(lab_instance: SimulationLaboratory) -> None:
    res = lab_instance.run_experiment("EXP_G", duration_ticks=96)
    assert res.success is True
    assert res.metrics["total_new_memories"] > 0
    assert res.metrics["economic_delta_std"] > 0.0


def test_behavioral_experiment_h_emergence(lab_instance: SimulationLaboratory) -> None:
    res = lab_instance.run_experiment("EXP_H", duration_ticks=48)
    assert res.success is True
    assert res.metrics["distinct_locations_visited"] >= 3


def test_cognitive_causal_feedback_loop(lab_instance: SimulationLaboratory) -> None:
    results = lab_instance.validate_cognitive_architecture()
    assert results["all_systems_coupled"] is True
    assert results["limbic_response"] is True
    assert results["hippocampal_encoding"] is True
    assert results["spatial_aversion_formed"] is True


def test_individual_observability_and_explanation_trace(lab_instance: SimulationLaboratory) -> None:
    lab_instance.start_simulation(seed=42)
    lab_instance.advance_ticks(10)

    dossier = lab_instance.inspect_individual(1)
    assert "identity" in dossier
    assert "physical" in dossier
    assert "personality" in dossier
    assert "recent_memories" in dossier
    assert len(dossier["recent_memories"]) > 0

    trace_str = lab_instance.explain_last_decision(1)
    assert "Individual:" in trace_str
    assert "Relevant factors:" in trace_str
    assert "Reason for selection:" in trace_str
    assert "Alternatives considered:" in trace_str


def test_population_anti_artificial_audit(lab_instance: SimulationLaboratory) -> None:
    lab_instance.start_simulation(seed=42)
    lab_instance.advance_ticks(96)
    analysis = lab_instance.analyze_population()

    assert analysis["population_size"] == 20
    assert analysis["personality_diversity"]["is_diverse"] is True
    assert analysis["anti_artificial_audit"]["is_clean"] is True
    assert len(analysis["anti_artificial_audit"]["warnings"]) == 0


def test_population_benchmarks_execution() -> None:
    bench = PopulationBenchmark.run_benchmark(sizes=[20, 50], ticks_per_run=5)
    assert len(bench["benchmarks"]) == 2
    for b in bench["benchmarks"]:
        assert b["avg_tick_ms"] < 50.0  # sub-50ms tick time
        assert b["ticks_per_second"] > 10.0
