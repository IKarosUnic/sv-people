"""Tests running all Phase 1.3 Open-Ended Cognitive Evolution Experiments EXP_13_A through EXP_13_O."""

import pytest
from saltbor.simulation.experiments.phase13_experiments import (
    Experiment13_A_IndividualCognitiveDevelopment,
    Experiment13_B_LearningToLearn,
    Experiment13_C_CognitivePlasticity,
    Experiment13_D_IndividualCognitiveDivergence,
    Experiment13_E_KnowledgeDiscovery,
    Experiment13_F_ScientificReasoningAndFailedHypotheses,
    Experiment13_G_CulturalTransmission,
    Experiment13_H_CulturalFragmentation,
    Experiment13_I_IntergenerationalKnowledgeTransfer,
    Experiment13_J_DistributedEducation,
    Experiment13_K_CollectiveProblemSolving,
    Experiment13_L_CognitiveDevelopmentUnderScarcity,
    Experiment13_M_CognitiveAgingAndKnowledgeRetention,
    Experiment13_N_PersonalityAndBehavioralAdaptation,
    Experiment13_O_LongitudinalCognitiveAndCulturalEvolution,
    PHASE13_EXPERIMENTS,
)


@pytest.mark.parametrize("exp_cls", PHASE13_EXPERIMENTS)
def test_exp_13_experiments_pass(exp_cls):
    """Execute each Phase 1.3 experiment and verify validity, hypotheses and metrics."""
    exp = exp_cls()
    res = exp.run()
    assert res.success is True, f"{exp.config.experiment_id} failed: {res.summary}"
    assert res.experiment_id == exp.config.experiment_id
    assert len(res.hypotheses) > 0
    assert len(res.metrics) > 0
    for hyp in res.hypotheses:
        assert hyp["status"] in ("HYPOTHESIS_SUPPORTED", "HYPOTHESIS_REJECTED", "INCONCLUSIVE", "EXPERIMENT_ERROR")
