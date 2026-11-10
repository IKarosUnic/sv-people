"""Tests running all Phase 1.0 Experiments EXP_10_A through EXP_10_X."""

import pytest
from saltbor.simulation.experiments.phase10_experiments_a_l import (
    Experiment10_A_MultigenerationalContinuity,
    Experiment10_B_DemographicTurnover,
    Experiment10_C_SettlementEvolution,
    Experiment10_D_TerritorialMigration,
    Experiment10_E_FamilyStructures,
    Experiment10_F_KnowledgeTransmission,
    Experiment10_G_CulturalTraditions,
    Experiment10_H_InnovationDiffusion,
    Experiment10_I_EconomicTransformation,
    Experiment10_J_SocialMobility,
    Experiment10_K_InstitutionalTransformation,
    Experiment10_L_InequalityEvolution,
)
from saltbor.simulation.experiments.phase10_experiments_m_x import (
    Experiment10_M_EnvironmentalCrisisResponse,
    Experiment10_N_EconomicResilience,
    Experiment10_O_CommunityFragmentation,
    Experiment10_P_CollectiveIdentityFormation,
    Experiment10_Q_InterSocietyRelations,
    Experiment10_R_KnowledgeLossAndRecovery,
    Experiment10_S_SettlementHistoricalTransformation,
    Experiment10_T_InstitutionalGenerationalContinuity,
    Experiment10_U_ResourceConditionedTech,
    Experiment10_V_HistoricalScenarioComparison,
    Experiment10_W_SocietyExtinctionOrTransformation,
    Experiment10_X_LongTermCivilizationEvolution,
)


@pytest.mark.parametrize(
    "exp_cls",
    [
        Experiment10_A_MultigenerationalContinuity,
        Experiment10_B_DemographicTurnover,
        Experiment10_C_SettlementEvolution,
        Experiment10_D_TerritorialMigration,
        Experiment10_E_FamilyStructures,
        Experiment10_F_KnowledgeTransmission,
        Experiment10_G_CulturalTraditions,
        Experiment10_H_InnovationDiffusion,
        Experiment10_I_EconomicTransformation,
        Experiment10_J_SocialMobility,
        Experiment10_K_InstitutionalTransformation,
        Experiment10_L_InequalityEvolution,
        Experiment10_M_EnvironmentalCrisisResponse,
        Experiment10_N_EconomicResilience,
        Experiment10_O_CommunityFragmentation,
        Experiment10_P_CollectiveIdentityFormation,
        Experiment10_Q_InterSocietyRelations,
        Experiment10_R_KnowledgeLossAndRecovery,
        Experiment10_S_SettlementHistoricalTransformation,
        Experiment10_T_InstitutionalGenerationalContinuity,
        Experiment10_U_ResourceConditionedTech,
        Experiment10_V_HistoricalScenarioComparison,
        Experiment10_W_SocietyExtinctionOrTransformation,
        Experiment10_X_LongTermCivilizationEvolution,
    ],
)
def test_exp_10_experiments_pass(exp_cls):
    exp = exp_cls()
    result = exp.run()
    assert result.success, f"Experiment {exp.config.name} failed with metrics: {result.metrics}"
