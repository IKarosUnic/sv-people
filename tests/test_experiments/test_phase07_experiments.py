"""Automated test suite executing and verifying all 15 Phase 0.7 experiments (EXP_07_A through EXP_07_O).

Covers:
- EXP_07_A: Deductive Reasoning & Traceability
- EXP_07_B: Inductive Learning & Expectation Updating
- EXP_07_C: Abductive Reasoning & Competing Explanations
- EXP_07_D: Causal Reasoning & Confounder Detection
- EXP_07_E: Analogical Transfer Across Domains
- EXP_07_F: Counterfactual Reasoning & Segregation
- EXP_07_G: General 14-Step Unknown Problem Solving
- EXP_07_H: Metacognitive Self-Audit & Error Detection
- EXP_07_I: Creative Combination & Innovation Lifecycle
- EXP_07_J: Autonomous Open-Ended Goal Generation & Subgoals
- EXP_07_K: Collective Multi-Agent Problem Solving
- EXP_07_L: Independent Parallel Discovery Without Leakage
- EXP_07_M: Failure Adaptation & Strategy Revision
- EXP_07_N: Longitudinal Cognitive Development (7, 30, 90, 180 Days)
- EXP_07_O: Epistemic and Reasoning Persistence Integrity
"""

import pytest
from saltbor.simulation.laboratory.lab import SimulationLaboratory


@pytest.fixture
def lab():
    return SimulationLaboratory()


def test_experiment_07_a_deductive_reasoning(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_A")
    assert result.success is True
    assert result.metrics["traces_count"] > 0
    assert "cannot craft or produce bread" in result.metrics["conclusion"].lower()
    assert result.metrics["premises_count"] >= 2
    assert result.metrics["confidence"] > 0.70


def test_experiment_07_b_inductive_learning(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_B")
    assert result.success is True
    assert result.metrics["initial_frequency"] == 1.0
    assert 0.5 < result.metrics["initial_confidence"] < 1.0
    assert result.metrics["final_confidence"] < result.metrics["initial_confidence"]
    assert result.metrics["violation_count"] == 2


def test_experiment_07_c_abductive_reasoning(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_C")
    assert result.success is True
    assert result.metrics["hypotheses_count"] >= 4
    assert result.metrics["final_top_cause"] == "price_increase"
    assert result.metrics["final_top_score"] > 0.60


def test_experiment_07_d_causal_reasoning(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_D")
    assert result.success is True
    assert result.metrics["confounded_status"] == "confounded"
    assert result.metrics["identified_confounder"] == "summer_heat"
    assert result.metrics["correlation_status"] == "correlation_only"
    assert result.metrics["intervention_status"] == "evidence_backed"


def test_experiment_07_e_analogical_transfer(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_E")
    assert result.success is True
    assert result.metrics["structural_similarity"] >= 0.50
    assert result.metrics["mappings_count"] >= 3
    assert result.metrics["principles_transferred"] >= 3
    assert result.metrics["caveats_count"] >= 2


def test_experiment_07_f_counterfactual_reasoning(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_F")
    assert result.success is True
    assert result.metrics["utility_delta"] > 0.0
    assert result.metrics["emotional_impact"] == "regret"
    assert result.metrics["memory_polluted"] is False


def test_experiment_07_g_unknown_problem_solving(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_G")
    assert result.success is True
    assert result.metrics["steps_executed"] == 14
    assert result.metrics["outcome"] in ("solved", "assistance_requested")
    assert result.metrics["satisfaction_ratio"] > 0.50


def test_experiment_07_h_metacognition(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_H")
    assert result.success is True
    assert result.metrics["self_efficacy"] < 0.45
    assert len(result.metrics["needed_skills"]) == 2
    assert result.metrics["limitations_recognized"] >= 2
    assert result.metrics["errors_detected"] >= 1


def test_experiment_07_i_creative_combination(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_I")
    assert result.success is True
    assert result.metrics["impossible_sound"] is False
    assert len(result.metrics["stages_traversed"]) == 7
    assert result.metrics["final_stage"] == "validated_innovation"
    assert result.metrics["remaining_timber"] == 2.0
    assert result.metrics["remaining_iron"] == 1.0


def test_experiment_07_j_autonomous_goal_generation(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_J")
    assert result.success is True
    assert result.metrics["generated_goals_count"] >= 3
    assert len(result.metrics["drivers_represented"]) >= 3
    assert result.metrics["subgoals_count"] == 6


def test_experiment_07_k_collective_intelligence(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_K")
    assert result.success is True
    assert result.metrics["team_size"] == 4
    assert result.metrics["coordination_success"] is True
    assert result.metrics["outcome"] == "solved"
    assert len(result.metrics["contributions"]) == 4


def test_experiment_07_l_independent_discovery(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_L")
    assert result.success is True
    assert result.metrics["alpha_leaked_to_beta"] is False
    assert result.metrics["beta_leaked_to_alpha"] is False
    assert result.metrics["alpha_hypothesis"] != result.metrics["beta_hypothesis"]


def test_experiment_07_m_failure_adaptation(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_M")
    assert result.success is True
    assert result.metrics["initial_success"] is False
    assert result.metrics["adapted_success"] is True
    assert result.metrics["adapted_strategy"] != result.metrics["initial_strategy"]


def test_experiment_07_n_longitudinal_development(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_N")
    assert result.success is True
    assert result.metrics["milestones_evaluated"] == 4
    assert result.metrics["final_skill_level"] > result.metrics["initial_skill_level"]


def test_experiment_07_o_persistence(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_07_O")
    assert result.success is True
    assert result.metrics["roundtrip_fidelity"] == 1.0
    assert result.metrics["restored_concept"] == "water_filter"
    assert result.metrics["restored_confidence"] > 0.80
