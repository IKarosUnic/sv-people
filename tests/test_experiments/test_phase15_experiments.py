"""Tests running all Phase 1.5 Everyday Life, Labor Market & Housing Experiments EXP_15_A through EXP_15_O."""

import pytest
from saltbor.simulation.experiments.phase15_experiments import (
    Experiment15_A_ShoppingWithoutPurchasing,
    Experiment15_B_ConsumerPreferencesAndBudgetConstraints,
    Experiment15_C_CommercialBrowsingAndSocialEncounters,
    Experiment15_D_DynamicEmploymentSearch,
    Experiment15_E_JobCompetitionAndWageNegotiation,
    Experiment15_F_InformalLaborAndTemporaryWork,
    Experiment15_G_HouseholdCostDistribution,
    Experiment15_H_HousingAffordabilityAndTenancy,
    Experiment15_I_HomelessnessRiskAndProtectiveFactors,
    Experiment15_J_EconomicRecoveryAndPersistentPoverty,
    Experiment15_K_LeisureUnderDifferentIncomeConditions,
    Experiment15_L_FamilySupportNetworks,
    Experiment15_M_BusinessCreationAndFailure,
    Experiment15_N_IndividualPreferenceDivergence,
    Experiment15_O_IntegratedDailyLife,
    PHASE15_EXPERIMENTS,
)


@pytest.mark.parametrize("exp_cls", PHASE15_EXPERIMENTS)
def test_exp_15_experiments_pass(exp_cls):
    """Execute each Phase 1.5 experiment and verify validity, hypotheses and metrics."""
    exp = exp_cls()
    res = exp.run()
    assert res.success is True, f"{exp.config.experiment_id} failed: {res.summary}"
    assert res.experiment_id == exp.config.experiment_id
    assert len(res.hypotheses) > 0
    assert len(res.metrics) > 0
    for hyp in res.hypotheses:
        assert hyp["status"] in ("HYPOTHESIS_SUPPORTED", "HYPOTHESIS_REJECTED", "INCONCLUSIVE", "EXPERIMENT_ERROR")
