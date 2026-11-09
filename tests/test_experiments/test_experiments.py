"""Automated validation of all 6 behavioral experiments."""

from saltbor.experiments.experiments import (
    experiment_behavioral_adaptation,
    experiment_differential_reaction,
    experiment_divergent_relationships,
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
