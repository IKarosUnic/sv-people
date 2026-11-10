"""Automated tests executing all 24 Phase 0.9 Experiments (EXP_09_A through EXP_09_X)."""

import pytest
from saltbor.simulation.laboratory.lab import SimulationLaboratory


@pytest.fixture
def lab():
    return SimulationLaboratory()


def test_experiment_09_a_friendship_formation(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_A")
    assert res.success is True
    assert res.metrics["friendship_formed"] is True
    assert res.metrics["rivalry_formed"] is True
    assert res.metrics["ab_trust"] > 0.70


def test_experiment_09_b_community_formation(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_B")
    assert res.success is True
    assert res.metrics["communities_formed"] >= 1
    assert res.metrics["active_members"] >= 3


def test_experiment_09_c_social_network_evolution(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_C")
    assert res.success is True
    assert res.metrics["final_density"] > res.metrics["initial_density"]
    assert res.metrics["reciprocity_ratio"] >= 0.80


def test_experiment_09_d_rupture_and_reconciliation(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_D")
    assert res.success is True
    assert res.metrics["final_status"] == "reconciled"
    assert res.metrics["post_reconciliation_trust"] > res.metrics["post_rupture_trust"]


def test_experiment_09_e_collective_problem_solving(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_E")
    assert res.success is True
    assert res.metrics["execution_success"] is True
    assert len(res.metrics["specialists"]) >= 2
    assert res.metrics["selected_proposal"] == "prop_gaviones"


def test_experiment_09_f_knowledge_transmission(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_F")
    assert res.success is True
    assert res.metrics["was_accepted"] is True
    assert res.metrics["has_provenance"] is True


def test_experiment_09_g_rumor_propagation_and_distortion(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_G")
    assert res.success is True
    assert res.metrics["total_reached"] >= 2
    assert res.metrics["hops_reached"] >= 2
    assert res.metrics["final_distortion_factor"] > 0.2


def test_experiment_09_h_social_learning(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_H")
    assert res.success is True
    assert res.metrics["teaching_success"] is True
    assert res.metrics["imitation_success"] is True
    assert res.metrics["total_adopters"] >= 3


def test_experiment_09_i_leadership_emergence(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_I")
    assert res.success is True
    assert res.metrics["fit_elena"] > res.metrics["fit_pedro"]
    assert res.metrics["boosted_legitimacy"] > res.metrics["initial_legitimacy"]
    assert res.metrics["penalized_legitimacy"] < res.metrics["initial_legitimacy"]


def test_experiment_09_j_organization_formation(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_J")
    assert res.success is True
    assert res.metrics["proposal_status"] == "enacted"
    assert res.metrics["bylaws_count"] >= 2


def test_experiment_09_k_internal_conflicts(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_K")
    assert res.success is True
    assert res.metrics["strained_cohesion"] < res.metrics["initial_cohesion"]
    assert res.metrics["dispute_stage"] == "escalated"


def test_experiment_09_l_negotiation_and_cooperation(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_L")
    assert res.success is True
    assert res.metrics["final_stage"] == "resolved"
    assert res.metrics["mediator_uid"] == "sindico_comunal"


def test_experiment_09_m_reputation_and_trust(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_M")
    assert res.success is True
    assert res.metrics["professional_score"] > res.metrics["communal_score"]
    assert res.metrics["hearsay_score"] > 0.50


def test_experiment_09_n_economic_cooperation(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_N")
    assert res.success is True
    assert res.metrics["total_revenue"] == 150.0
    assert len(res.metrics["dividend_payouts"]) == 3


def test_experiment_09_o_cultural_development(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_O")
    assert res.success is True
    assert len(res.metrics["mutations"]) >= 1
    assert res.metrics["dormant_traditions_count"] >= 1


def test_experiment_09_p_institutional_transformation(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_P")
    assert res.success is True
    assert res.metrics["is_active"] is True
    assert res.metrics["bylaws_count"] == 3


def test_experiment_09_q_innovation_diffusion(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_Q")
    assert res.success is True
    assert res.metrics["final_adopters"] > res.metrics["initial_adopters"]
    assert res.metrics["final_adopters"] >= 4


def test_experiment_09_r_collective_intelligence_uncertainty(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_R")
    assert res.success is True
    assert res.metrics["execution_success"] is True
    assert "escalonada" in res.metrics["selected_strategy"].lower()


def test_experiment_09_s_community_fission_and_dissolution(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_S")
    assert res.success is True
    assert res.metrics["fission_success"] is True
    assert res.metrics["dissolution_success"] is True


def test_experiment_09_t_longitudinal_simulation(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_T")
    assert res.success is True
    assert res.metrics["final_day"] == 360
    assert len(res.metrics["snapshots"]) == 4


def test_experiment_09_u_geography_economy_society_integration(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_U")
    assert res.success is True
    assert res.metrics["trade_revenue"] == 120.0
    assert res.metrics["social_trust"] > 0.60


def test_experiment_09_v_persistence_and_recovery(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_V")
    assert res.success is True
    assert res.metrics["edges_reloaded"] == 1
    assert res.metrics["communities_reloaded"] == 1


def test_experiment_09_w_incomplete_information(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_W")
    assert res.success is True
    assert res.metrics["contract_size_prudent"] == 10.0
    assert res.metrics["updated_confidence"] > res.metrics["initial_confidence"]


def test_experiment_09_x_network_scalability(lab: SimulationLaboratory):
    res = lab.run_experiment("EXP_09_X")
    assert res.success is True
    assert res.metrics["all_scales_sub_second"] is True
