"""Tests running all Phase 1.2.1 Adversarial Validation Experiments EXP_121_A through EXP_121_I."""

import pytest
from saltbor.simulation.experiments.phase121_experiments import (
    Experiment121_A_CausalCounterfactualValidation,
    Experiment121_B_AblationInKindPayment,
    Experiment121_C_AblationKnowledgeTransmission,
    Experiment121_D_EmergentFissionFromGrievances,
    Experiment121_E_CascadingSocioecologicalAbandonment,
    Experiment121_F_CombinatorialSearchMaterialPhysics,
    Experiment121_G_IrreversibleCollapseVsContingentRecovery,
    Experiment121_H_MultidimensionalDivergence40Societies,
    Experiment121_I_ForensicSqlitePersistenceAndRecovery,
    PHASE121_EXPERIMENTS,
)


@pytest.mark.parametrize("exp_cls", PHASE121_EXPERIMENTS)
def test_exp_121_experiments_pass(exp_cls):
    """Execute each Phase 1.2.1 validation experiment and verify success and metrics."""
    exp = exp_cls()
    res = exp.run()
    assert res.success is True, f"{exp.config.experiment_id} failed: {res.summary}"
    assert res.experiment_id == exp.config.experiment_id
    assert len(res.hypotheses) > 0
    assert len(res.metrics) > 0
