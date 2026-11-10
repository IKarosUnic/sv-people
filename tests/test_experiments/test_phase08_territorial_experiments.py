"""
Automated Pytest test suite executing and verifying all 20 Phase 0.8 territorial experiments (EXP_08_A through EXP_08_T).
"""

import pytest
from saltbor.simulation.laboratory.lab import SimulationLaboratory


@pytest.fixture
def lab():
    return SimulationLaboratory()


def test_exp_08_a_territorial_integrity(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_A")
    assert result.success is True
    assert result.metrics["departments_count"] == 14
    assert result.metrics["municipalities_count"] == 44
    assert result.metrics["districts_count"] == 262
    assert result.metrics["total_population_represented"] > 5_000_000


def test_exp_08_b_spatial_precision(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_B")
    assert result.success is True
    assert 50.0 <= result.metrics["dist_ss_santa_ana_km"] <= 55.0
    assert 110.0 <= result.metrics["dist_ss_san_miguel_km"] <= 115.0
    assert result.metrics["metric_projection_error_m"] < 50.0


def test_exp_08_c_real_establishments(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_C")
    assert result.success is True
    assert result.metrics["total_establishments"] == 41
    assert result.metrics["confirmed_establishments"] == 37
    assert result.metrics["categories_covered"] == 4


def test_exp_08_d_duplicate_detection(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_D")
    assert result.success is True
    assert result.metrics["duplicate_distance_m"] < 75.0
    assert result.metrics["name_similarity_score"] > 0.8
    assert result.metrics["matched_establishment_id"] is not None


def test_exp_08_e_incremental_update(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_E")
    assert result.success is True
    assert result.metrics["initial_count"] == 41
    assert result.metrics["final_count"] == 42
    assert result.metrics["added_count"] == 1
    assert result.metrics["new_version"] is not None


def test_exp_08_f_road_network_navigation(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_F")
    assert result.success is True
    assert result.metrics["route_distance_km"] > 100.0
    assert result.metrics["transit_hours_bus"] > 2.0
    assert "Puente Cuscatlán" in result.metrics["bridges_crossed"]


def test_exp_08_g_obstacle_avoidance(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_G")
    assert result.success is True
    assert "Lago de Coatepeque" in result.metrics["obstacles_collided"]
    assert result.metrics["bridge_accessible"] is True
    assert result.metrics["bridge_blocked_reroute_accessible"] is True


def test_exp_08_h_territorial_economy(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_H")
    assert result.success is True
    assert result.metrics["price_far_usd"] > result.metrics["price_near_usd"]
    assert result.metrics["pupuseria_net_profit_usd"] > 30.0
    assert 0.35 <= result.metrics["pupuseria_margin"] <= 0.65
    assert result.metrics["fiado_local_approved"] is True
    assert result.metrics["fiado_distant_rejected"] is True


def test_exp_08_i_geographic_cognition(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_I")
    assert result.success is True
    assert result.metrics["initial_knows_place"] is False
    assert result.metrics["decayed_status"] == "REMEMBERED"


def test_exp_08_j_social_transmission(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_J")
    assert result.success is True
    assert result.metrics["recommender_confidence"] > 0.9
    assert result.metrics["recipient_belief_status"] == "HEARD_RUMOR"


def test_exp_08_k_rumor_debunking(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_K")
    assert result.success is True
    assert result.metrics["initial_status"] == "HEARD_RUMOR"
    assert result.metrics["final_status"] == "DISPROVED"
    assert result.metrics["is_disproved"] is True


def test_exp_08_l_environmental_intelligence(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_L")
    assert result.success is True
    assert result.metrics["dirt_hours_rain"] > result.metrics["dirt_hours_dry"]
    assert result.metrics["dirt_hours_temporal"] > result.metrics["dirt_hours_rain"]
    assert result.metrics["ca1_dry_accessible"] is True
    assert result.metrics["temporal_warning_issued"] is True


def test_exp_08_m_offline_architecture(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_M")
    assert result.success is True
    assert result.metrics["offline_places_found"] >= 5
    assert result.metrics["offline_route_km"] > 0.0
    assert result.metrics["offline_reverse_geocode_dept"] == "Santa Ana"


def test_exp_08_n_persistence_cold_restart(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_N")
    assert result.success is True
    assert result.metrics["persisted_records_count"] == result.metrics["recovered_records_count"]
    assert result.metrics["version_checkpoint_recovered"] == "v1.0.0_baseline"


def test_exp_08_o_rollback_recovery(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_O")
    assert result.success is True
    assert result.metrics["defective_update_rejected"] is True
    assert result.metrics["revert_successful"] is True
    assert result.metrics["restored_count"] == 41


def test_exp_08_p_spatial_index_scalability(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_P")
    assert result.success is True
    assert result.metrics["benchmark_queries"] == 500
    assert result.metrics["total_hits_found"] > 0
    assert result.metrics["average_latency_ms"] < 1.0


def test_exp_08_q_global_integration(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_Q")
    assert result.success is True
    assert result.metrics["journey_ticks"] > 0
    assert result.metrics["distance_km"] > 0.0
    assert result.metrics["journey_completed"] is True
    assert result.metrics["place_verified"] == "VERIFIED_CONFIRMED"
    assert result.metrics["transaction_revenue_usd"] > 0.0


def test_exp_08_r_territorial_consistency(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_R")
    assert result.success is True
    assert result.metrics["districts_audited"] == 262
    assert result.metrics["establishments_audited"] == 41
    assert result.metrics["features_audited"] == 18
    assert result.metrics["anomalies_found"] == 0


def test_exp_08_s_source_provenance_audit(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_S")
    assert result.success is True
    assert result.metrics["cnr_admin_layers"] >= 4
    assert result.metrics["osm_licensed"] is True
    assert result.metrics["verified_institutional_sources"] >= 4


def test_exp_08_t_version_comparison_diff(lab: SimulationLaboratory):
    result = lab.run_experiment("EXP_08_T")
    assert result.success is True
    assert result.metrics["added_records"] == 1
    assert result.metrics["modified_records"] == 1
    assert result.metrics["removed_records"] == 1
