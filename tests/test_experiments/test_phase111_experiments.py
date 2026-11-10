"""Tests running all Phase 1.1.1 Validation Extension Experiments EXP_111_A through EXP_111_J."""

import pytest
from saltbor.simulation.experiments.phase111_experiments import (
    Experiment111_A_DynamicCulturalDrift,
    Experiment111_B_Communities20to100Agents,
    Experiment111_C_LongitudinalAutonomousEconomy,
    Experiment111_D_CollectiveResourceConflicts,
    Experiment111_E_AutonomousTechnologicalDiscovery,
    Experiment111_F_KnowledgeTransmissionMentorship,
    Experiment111_G_InnovationAndEconomicSpecialization,
    Experiment111_H_MultiSeedReproducibility,
    Experiment111_I_CrossEnginePerformanceAudit,
    Experiment111_J_LongitudinalCommunityTransformation,
    PHASE111_EXPERIMENTS,
)


@pytest.mark.parametrize("exp_cls", PHASE111_EXPERIMENTS)
def test_exp_111_experiments_pass(exp_cls):
    """Execute each Phase 1.1.1 validation extension experiment and verify success."""
    exp = exp_cls()
    res = exp.run()
    assert res.success is True, f"{exp.config.experiment_id} failed: {res.summary}"
    assert res.experiment_id == exp.config.experiment_id
    assert len(res.hypotheses) > 0
    assert len(res.metrics) > 0
