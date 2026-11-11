"""Tests running all Phase 1.2.2 Adversarial Robustness and Statistical Validation Experiments EXP_122_A through EXP_122_L."""

import pytest
from saltbor.simulation.experiments.phase122_experiments import (
    Experiment122_A_MultiSeedCounterfactualRobustness,
    Experiment122_B_ThresholdSensitivity,
    Experiment122_C_HiddenTechnologicalDiscovery,
    Experiment122_D_AdversarialCommunityDynamics,
    Experiment122_E_EcologicalRecoverySensitivity,
    Experiment122_F_MultidimensionalStatisticalValidation,
    Experiment122_G_KnowledgeExtinctionAndRediscovery,
    Experiment122_H_CollectiveLearningWithoutCentralAuthority,
    Experiment122_I_AblationAndMechanismDependency,
    Experiment122_J_LongitudinalCivilizationDivergence,
    Experiment122_K_PhysicalPersistenceAndPerformance,
    Experiment122_L_IntegratedAdversarialStressTest,
    PHASE122_EXPERIMENTS,
)


@pytest.mark.parametrize("exp_cls", PHASE122_EXPERIMENTS)
def test_exp_122_experiments_pass(exp_cls):
    """Execute each Phase 1.2.2 validation experiment and verify success, hypotheses and metrics."""
    exp = exp_cls()
    res = exp.run()
    assert res.success is True, f"{exp.config.experiment_id} failed: {res.summary}"
    assert res.experiment_id == exp.config.experiment_id
    assert len(res.hypotheses) > 0
    assert len(res.metrics) > 0
