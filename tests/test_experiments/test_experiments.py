"""Automated validation of all Phase 0.1 and Phase 0.2 behavioral experiments."""

from saltbor.experiments.experiments import (
    experiment_a_different_personalities,
    experiment_b_emotional_influence,
    experiment_behavioral_adaptation,
    experiment_c_memory_influence,
    experiment_d_personality_evolution,
    experiment_differential_reaction,
    experiment_divergent_relationships,
    experiment_e_self_improvement,
    experiment_f_relationship_arc,
    experiment_g_goal_abandonment,
    experiment_h_individual_divergence,
    experiment_selective_forgetting,
    experiment_skill_acquisition,
    experiment_autonomous_goal_generation,
)


def test_experiment_1_differential_reaction():
    res = experiment_differential_reaction()
    assert res["differential_demonstrated"] is True


def test_experiment_2_skill_acquisition():
    res = experiment_skill_acquisition()
    assert res["diminishing_returns_demonstrated"] is True


def test_experiment_3_autonomous_goal_formulation():
    res = experiment_autonomous_goal_generation()
    assert res["autonomy_demonstrated"] is True


def test_experiment_4_selective_memory_decay():
    res = experiment_selective_forgetting()
    assert res["selective_decay_demonstrated"] is True


def test_experiment_5_divergent_relationships():
    res = experiment_divergent_relationships()
    assert res["divergent_dynamics_demonstrated"] is True


def test_experiment_6_behavioral_adaptation():
    res = experiment_behavioral_adaptation()
    assert res["adaptation_demonstrated"] is True


def test_experiment_a_different_personalities():
    res = experiment_a_different_personalities()
    assert res["success"] is True
    assert res["different_decisions_produced"] is True


def test_experiment_b_emotional_influence():
    res = experiment_b_emotional_influence()
    assert res["success"] is True
    assert res["emotional_modulation_demonstrated"] is True


def test_experiment_c_memory_influence():
    res = experiment_c_memory_influence()
    assert res["success"] is True
    assert res["history_preserved_without_data_loss"] is True
    assert res["location_aversion_recorded"] is True


def test_experiment_d_personality_evolution():
    res = experiment_d_personality_evolution()
    assert res["success"] is True
    assert res["neuroticism_increased"] is True
    assert res["risk_tolerance_decreased"] is True


def test_experiment_e_self_improvement():
    res = experiment_e_self_improvement()
    assert res["success"] is True
    assert res["goal_completed"] is True


def test_experiment_f_relationship_arc():
    res = experiment_f_relationship_arc()
    assert res["success"] is True
    assert res["directional_asymmetry_demonstrated"] is True


def test_experiment_g_goal_abandonment():
    res = experiment_g_goal_abandonment()
    assert res["success"] is True
    assert res["abandoned_or_modified"] is True


def test_experiment_h_individual_divergence():
    res = experiment_h_individual_divergence()
    assert res["success"] is True
    assert res["divergence_demonstrated"] is True
