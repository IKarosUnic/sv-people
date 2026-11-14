"""Pytest suite verifying all 20 Phase 1.12 Scientific & Causal Experiments."""

import pytest

from saltbor.simulation.experiments.phase112_scientific_experiments import (
    PHASE112_EXPERIMENTS,
    Experiment112_A_InternalMigration,
    Experiment112_B_RemittanceReduction,
    Experiment112_C_AgriculturalProductivity,
    Experiment112_D_WaterScarcityCPR,
    Experiment112_E_InformalEmployment,
    Experiment112_F_EducationIntergenerational,
    Experiment112_G_InstitutionalTrust,
    Experiment112_H_RegionalInequality,
    Experiment112_I_CulturalTransmission,
    Experiment112_J_ClimateDisplacement,
    Experiment112_K_SocialNetworkResilience,
    Experiment112_L_HouseholdCoping,
    Experiment112_M_CommunityDiversification,
    Experiment112_N_AlternativeInstitutions,
    Experiment112_O_SensitivityInitialConditions,
    Experiment112_P_MultiSeedReproducibility,
    Experiment112_Q_CausalConfounding,
    Experiment112_R_CounterfactualDevelopment,
    Experiment112_S_LongitudinalComparison,
    Experiment112_T_ScalabilityBenchmark,
)
from saltbor.simulation.laboratory.lab import SimulationLaboratory


@pytest.mark.parametrize("exp_id,exp_cls", list(PHASE112_EXPERIMENTS.items()))
def test_phase112_experiment_execution(exp_id: str, exp_cls):
    """Verify each Phase 1.12 experiment executes independently and confirms hypotheses."""
    experiment = exp_cls()
    result = experiment.run()

    assert result.experiment_id == exp_id
    assert result.success is True, f"Experiment {exp_id} failed: {result.summary}"
    assert len(result.hypotheses) > 0
    assert all(h["confirmed"] for h in result.hypotheses), f"Hypothesis refuted in {exp_id}: {result.hypotheses}"
    assert len(result.metrics) > 0


def test_simulation_laboratory_integration():
    """Verify all 20 Phase 1.12 experiments are registered in SimulationLaboratory."""
    lab = SimulationLaboratory()
    for exp_id in PHASE112_EXPERIMENTS.keys():
        assert exp_id in lab.experiment_registry, f"{exp_id} missing from SimulationLaboratory registry"
        res = lab.run_experiment(exp_id)
        assert res.success is True, f"Laboratory run of {exp_id} failed: {res.summary}"
