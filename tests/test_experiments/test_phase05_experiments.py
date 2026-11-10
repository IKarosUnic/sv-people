"""Automated test suite executing and verifying all 10 Phase 0.5 experiments (EXP_05_A to EXP_05_J)."""

import pytest
from saltbor.simulation.laboratory.lab import SimulationLaboratory


@pytest.fixture
def lab():
    return SimulationLaboratory()


def test_experiment_05_a_cultural_evolution(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_05_A")
    assert result.success is True
    assert result.metrics["practitioners_count"] >= 2
    assert "custom_feria_olvidada" in result.metrics["abandoned_elements"]


def test_experiment_05_b_credit_and_debt(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_05_B")
    assert result.success is True
    assert result.metrics["loan1_paid_amount"] >= 60.0
    assert result.metrics["loan1_final_status"] == "paid_off"
    assert result.metrics["loan2_missed_payments"] >= 2
    assert result.metrics["loan2_status_after_restructure"] == "restructured"


def test_experiment_05_c_business_dynamics(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_05_C")
    assert result.success is True
    assert result.metrics["revenue_generated"] == 35.0
    assert result.metrics["worker_final_money"] == 22.0
    assert result.metrics["firm_status"] == "active"


def test_experiment_05_d_social_network_analysis(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_05_D")
    assert result.success is True
    assert result.metrics["total_nodes"] == 5
    assert result.metrics["total_edges"] == 5
    assert result.metrics["bridge_node_degree"] == 3


def test_experiment_05_e_institutional_development(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_05_E")
    assert result.success is True
    assert result.metrics["dues_collected"] == 15.0
    assert result.metrics["final_treasury_balance"] == 55.0
    assert result.metrics["policies_enacted_count"] >= 1


def test_experiment_05_f_social_learning(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_05_F")
    assert result.success is True
    assert result.metrics["level_after_observation"] > 0.05
    assert result.metrics["level_after_mentorship"] > result.metrics["level_after_observation"]
    assert result.metrics["mentorship_sessions"] >= 1


def test_experiment_05_g_geography_and_environment(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_05_G")
    assert result.success is True
    assert result.metrics["road_speed_multiplier"] > 1.0
    assert result.metrics["hill_energy_burn_multiplier"] > 1.0
    assert result.metrics["river_traversable"] is False
    assert result.metrics["crossing_traversable"] is True


def test_experiment_05_h_integrated_social_crisis(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_05_H")
    assert result.success is True
    assert result.metrics["drought_crop_multiplier"] <= 0.40
    assert result.metrics["consecutive_missed_payments"] >= 2
    assert result.metrics["aid_amount_disbursed"] == 25.0
    assert result.metrics["loan_restructured"] is True


def test_experiment_05_i_longitudinal_civilization(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_05_I")
    assert result.success is True
    assert result.metrics["simulated_years_elapsed"] == 5.0
    assert result.metrics["infant_evolved_stage"] == "childhood"
    assert result.metrics["tradition_practitioners"] >= 2
    assert result.metrics["settlement_gini"] >= 0.0


def test_experiment_05_j_emergent_behavior_validation(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_05_J")
    assert result.success is True
    assert "seed_42_trajectory" in result.metrics
    assert "seed_999_trajectory" in result.metrics
