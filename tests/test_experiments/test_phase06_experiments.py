"""Automated test suite executing and verifying all Phase 0.6 experiments.

Covers:
- Regional Legacy Experiments (EXP_06_REGIONAL_A through D)
- Mandatory Knowledge Architecture Experiments (EXP_06_A through EXP_06_L):
  * EXP_06_A: Individual Knowledge Acquisition Pathways
  * EXP_06_B: Knowledge Transmission & Pedagogy
  * EXP_06_C: Intergenerational Knowledge Survival
  * EXP_06_D: Independent Parallel Discovery
  * EXP_06_E: Compositional Capability Synthesis
  * EXP_06_F: Empirical Hypothesis Testing & Evidence
  * EXP_06_G: Contradictory Knowledge & Source Credibility
  * EXP_06_H: Collective Intelligence Synergy
  * EXP_06_I: Knowledge Specialization Divergence
  * EXP_06_J: Technological & Economic Innovation
  * EXP_06_K: Open-Ended Problem Solving & Decomposition
  * EXP_06_L: Knowledge Persistence & DB Save/Load Integrity
"""

import pytest
from saltbor.simulation.laboratory.lab import SimulationLaboratory


@pytest.fixture
def lab():
    return SimulationLaboratory()


# ===========================================================================
# Regional Legacy Experiments
# ===========================================================================

def test_experiment_06_regional_a_arbitrage(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_REGIONAL_A")
    assert result.success is True
    assert result.metrics["trade_volume_dollars"] > 0.0
    assert result.metrics["acquired_timber_units"] > 0.0


def test_experiment_06_regional_b_legal(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_REGIONAL_B")
    assert result.success is True
    assert result.metrics["verdict"] == "guilty_restitution_and_fine"
    assert result.metrics["restitution_paid"] == 45.0
    assert result.metrics["fine_paid_to_treasury"] == 15.0


def test_experiment_06_regional_c_payment_in_kind(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_REGIONAL_C")
    assert result.success is True
    assert result.metrics["value_credited"] > 6.0


def test_experiment_06_regional_d_shock_and_relief(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_REGIONAL_D")
    assert result.success is True
    assert result.metrics["saltbor_restocked_wood"] >= 30.0


# ===========================================================================
# Mandatory Phase 0.6 Knowledge Suite (EXP_06_A to EXP_06_L)
# ===========================================================================

def test_experiment_06_a_individual_knowledge_acquisition(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_A")
    assert result.success is True
    assert result.metrics["confidence_direct_experience"] > result.metrics["confidence_observation"]
    assert result.metrics["confidence_direct_experience"] >= result.metrics["confidence_teaching"]


def test_experiment_06_b_knowledge_transmission(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_B")
    assert result.success is True
    assert result.metrics["impostor_blocked"] is True
    assert result.metrics["master_transmission_successful"] is True
    assert result.metrics["student_confidence"] > 0.65


def test_experiment_06_c_intergenerational_knowledge(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_C")
    assert result.success is True
    assert result.metrics["survived_discoverer_death"] is True
    assert result.metrics["collective_preservation_active"] is True
    assert result.metrics["gen3_confidence"] > 0.3


def test_experiment_06_d_independent_discovery(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_D")
    assert result.success is True
    assert result.metrics["independent_hypotheses_count"] == 2
    assert result.metrics["no_telepathic_leakage"] is True


def test_experiment_06_e_compositional_reasoning(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_E")
    assert result.success is True
    assert result.metrics["composition_successful"] is True
    assert result.metrics["feasibility_score"] >= 0.50


def test_experiment_06_f_hypothesis_and_experimentation(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_F")
    assert result.success is True
    assert result.metrics["experiment_completed"] is True
    assert result.metrics["posterior_confidence"] > result.metrics["prior_confidence"]
    assert result.metrics["final_status"] == "supported"


def test_experiment_06_g_contradictory_knowledge(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_G")
    assert result.success is True
    assert result.metrics["properly_resisted_single_rumor"] is True
    assert result.metrics["confidence_after_inspection"] < result.metrics["confidence_after_rumor"]


def test_experiment_06_h_collective_intelligence(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_H")
    assert result.success is True
    assert result.metrics["farmer_alone_solved"] is False
    assert result.metrics["collective_cooperative_solved"] is True
    assert result.metrics["pooled_capabilities_count"] == 3


def test_experiment_06_i_knowledge_specialization(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_I")
    assert result.success is True
    assert result.metrics["forester_woodcraft_index"] == 1.0
    assert result.metrics["forester_agriculture_index"] == 0.0
    assert result.metrics["farmer_agriculture_index"] == 1.0
    assert result.metrics["specialization_divergence_delta"] == 1.0


def test_experiment_06_j_knowledge_and_economic_innovation(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_J")
    assert result.success is True
    assert result.metrics["construction_successful"] is True
    assert result.metrics["remaining_timber"] == 6.0


def test_experiment_06_k_open_ended_capability(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_K")
    assert result.success is True
    assert result.metrics["open_ended_synthesis_achieved"] is True
    assert result.metrics["causal_chain_length"] >= 1


def test_experiment_06_l_knowledge_persistence(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_06_L")
    assert result.success is True
    assert result.metrics["save_load_success"] is True
    assert result.metrics["node_label_matches"] is True
    assert result.metrics["individual_claim_restored"] is True
