"""Automated test suite executing and verifying all 8 Phase 0.4 experiments."""

import pytest

from saltbor.simulation.laboratory.lab import SimulationLaboratory


@pytest.fixture
def lab():
    return SimulationLaboratory()


def test_experiment_04_a_multigenerational_population(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_04_A")
    assert result.success is True
    assert result.metrics["births_count"] >= 1
    assert result.metrics["deaths_count"] >= 1
    assert result.metrics["infant_initial_stage"] == "infancy"


def test_experiment_04_b_family_development(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_04_B")
    assert result.success is True
    assert result.metrics["food_demand_after_birth"] > result.metrics["food_demand_before_birth"]
    assert result.metrics["caregiver_assigned"] != "None"


def test_experiment_04_c_economic_dynamics(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_04_C")
    assert result.success is True
    assert result.metrics["shortage_peak_price"] > result.metrics["initial_food_price"]
    assert result.metrics["restocked_recovered_price"] < result.metrics["shortage_peak_price"]
    assert result.metrics["furniture_produced"] >= 1.0


def test_experiment_04_d_complex_planning(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_04_D")
    assert result.success is True
    assert result.metrics["initial_plan_length"] >= 5
    assert "Precondition failed" in result.metrics["replan_reason"]


def test_experiment_04_e_information_propagation(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_04_E")
    assert result.success is True
    assert result.metrics["b_reaction"] == "believe"
    assert result.metrics["d_reaction"] == "disbelieve"
    assert result.metrics["c_generation_hops"] == 2
    assert result.metrics["c_is_verified"] is True


def test_experiment_04_f_group_formation(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_04_F")
    assert result.success is True
    assert result.metrics["group_members_count"] == 5
    assert result.metrics["proposal_enacted"] is True
    assert result.metrics["votes_for"] >= 3


def test_experiment_04_g_continuous_navigation(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_04_G")
    assert result.success is True
    assert result.metrics["encounters_detected"] >= 1
    assert result.metrics["agent_a_final_x"] > 15.0


def test_experiment_04_h_long_term_social_evolution(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_04_H")
    assert result.success is True
    assert result.metrics["baby_stage"] == "infancy"
    assert result.metrics["furniture_produced"] >= 1.0
    assert result.metrics["conversation_turns"] >= 3
    assert len(result.metrics["inheritance_distributed"]) > 0
