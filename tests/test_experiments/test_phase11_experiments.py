"""Tests running all Phase 1.1 Experiments EXP_11_A through EXP_11_T."""

import pytest
from saltbor.simulation.experiments.phase11_experiments import (
    Experiment11_A_ArchitectureAudit,
    Experiment11_B_SeedReproducibility,
    Experiment11_C_IndividualGoalEmergence,
    Experiment11_D_SocialRelationshipEmergence,
    Experiment11_E_SpontaneousCommunityFormation,
    Experiment11_F_EconomicActivityEmergence,
    Experiment11_G_IntergenerationalCulturalTransmission,
    Experiment11_H_ScarcityAdaptation,
    Experiment11_I_LongitudinalDemographics,
    Experiment11_J_CollectiveProblemSolving,
    Experiment11_K_CognitiveArchitectureAblation,
    Experiment11_L_KnowledgeGraphAblation,
    Experiment11_M_ParameterSensitivity,
    Experiment11_N_LongHistoricalSimulation,
    Experiment11_O_SustainedPerformance,
    Experiment11_P_PersistenceAndRecovery,
    Experiment11_Q_SalvadoranGeographyValidation,
    Experiment11_R_ArchitecturalComparison,
    Experiment11_S_CausalTraceability,
    Experiment11_T_CivilizationIntegralTest,
)


@pytest.mark.parametrize(
    "exp_cls",
    [
        Experiment11_A_ArchitectureAudit,
        Experiment11_B_SeedReproducibility,
        Experiment11_C_IndividualGoalEmergence,
        Experiment11_D_SocialRelationshipEmergence,
        Experiment11_E_SpontaneousCommunityFormation,
        Experiment11_F_EconomicActivityEmergence,
        Experiment11_G_IntergenerationalCulturalTransmission,
        Experiment11_H_ScarcityAdaptation,
        Experiment11_I_LongitudinalDemographics,
        Experiment11_J_CollectiveProblemSolving,
        Experiment11_K_CognitiveArchitectureAblation,
        Experiment11_L_KnowledgeGraphAblation,
        Experiment11_M_ParameterSensitivity,
        Experiment11_N_LongHistoricalSimulation,
        Experiment11_O_SustainedPerformance,
        Experiment11_P_PersistenceAndRecovery,
        Experiment11_Q_SalvadoranGeographyValidation,
        Experiment11_R_ArchitecturalComparison,
        Experiment11_S_CausalTraceability,
        Experiment11_T_CivilizationIntegralTest,
    ],
)
def test_exp_11_experiments_pass(exp_cls):
    """Execute each Phase 1.1 reference experiment and verify success."""
    exp = exp_cls()
    res = exp.run()
    assert res.success is True, f"{exp.config.experiment_id} failed: {res.summary}"
    assert res.experiment_id == exp.config.experiment_id
    assert len(res.hypotheses) > 0
    assert len(res.metrics) > 0
