"""Tests running all Phase 1.2 Open-Ended Society Experiments EXP_12_A through EXP_12_L."""

import pytest
from saltbor.simulation.experiments.phase12_experiments import (
    Experiment12_A_EnvironmentalDivergence,
    Experiment12_B_CulturalKnowledgeExtinction,
    Experiment12_C_GenerationalKnowledgeSeverance,
    Experiment12_D_CommunityFissionAndNewSettlement,
    Experiment12_E_FoodCrisisAndDistressMigration,
    Experiment12_F_FinancialLiquidityFreezeAndInKindSettlement,
    Experiment12_G_OpenCombinatorialDiscovery,
    Experiment12_H_TechnologicalFailureAndResourceLoss,
    Experiment12_I_ImperfectTransmissionAndKnowledgeMutation,
    Experiment12_J_TerritorialDecayAndAbandonment,
    Experiment12_K_CivilizationalRecoveryPostCrisis,
    Experiment12_L_LongitudinalCivilizationalDivergence,
    PHASE12_EXPERIMENTS,
)


@pytest.mark.parametrize("exp_cls", PHASE12_EXPERIMENTS)
def test_exp_12_experiments_pass(exp_cls):
    """Execute each Phase 1.2 open-ended experiment and verify success and metrics."""
    exp = exp_cls()
    res = exp.run()
    assert res.success is True, f"{exp.config.experiment_id} failed: {res.summary}"
    assert res.experiment_id == exp.config.experiment_id
    assert len(res.hypotheses) > 0
    assert len(res.metrics) > 0
