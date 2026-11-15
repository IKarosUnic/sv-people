"""Unit tests for CrossDomainInteractionEngine (Phase 1.14)."""

import pytest
from saltbor.territory.cross_domain import CrossDomainInteractionEngine
from saltbor.territory.models import CrossDomainMechanism


def test_cross_domain_initialization():
    engine = CrossDomainInteractionEngine(random_seed=42)
    assert len(engine.interactions) >= 6
    graph = engine.get_domain_coupling_graph()
    assert len(graph["domains"]) >= 6
    assert graph["total_interactions"] >= 6


def test_transportation_to_commerce_propagation():
    engine = CrossDomainInteractionEngine(random_seed=42)
    
    # Baseline condition: normal paved road
    res_base = engine.propagate_transport_to_commerce(
        road_friction_multiplier=1.0,
        travel_cost_per_km=0.05,
        commercial_reach_km=10.0,
        is_road_disrupted=False,
    )
    assert res_base["effective_reach_km"] >= 9.0
    assert res_base["delivery_cost_markup_usd"] == 0.0

    # Disrupted condition: road blocked by landslide
    res_disrupted = engine.propagate_transport_to_commerce(
        road_friction_multiplier=3.0,
        travel_cost_per_km=0.05,
        commercial_reach_km=10.0,
        is_road_disrupted=True,
    )
    assert res_disrupted["effective_reach_km"] < res_base["effective_reach_km"]
    assert res_disrupted["delivery_cost_markup_usd"] > 1.0
    assert res_disrupted["retail_price_inflation_factor"] > 1.05


def test_education_to_economy_propagation():
    engine = CrossDomainInteractionEngine(random_seed=42)
    
    # High poverty canton
    res_poor = engine.propagate_education_to_economy(
        school_attendance_rate=0.55,
        household_poverty_rate=0.60,
        available_local_jobs=80,
    )
    assert res_poor["dropout_rate"] > 0.15
    assert res_poor["immediate_youth_labor_supply_units"] > 5.0

    # Low poverty area with high attendance
    res_prosperous = engine.propagate_education_to_economy(
        school_attendance_rate=0.92,
        household_poverty_rate=0.15,
        available_local_jobs=20,
    )
    assert res_prosperous["dropout_rate"] < res_poor["dropout_rate"]
    assert res_prosperous["skilled_labor_growth_rate"] > 0.0


def test_healthcare_to_household_propagation():
    engine = CrossDomainInteractionEngine(random_seed=42)
    
    res = engine.propagate_healthcare_to_household_economy(
        facility_distance_km=12.0,
        queue_waiting_time_hours=4.5,
        daily_wage_usd=12.0,
        illness_incidence_rate=0.15,
    )
    assert res["out_of_pocket_transit_cost_usd"] > 4.0
    assert res["lost_wages_per_visit_usd"] > 6.0
    assert res["care_deferral_rate"] > 0.20
    assert res["total_household_economic_drag_usd"] > 10.0


def test_agriculture_to_food_commerce_propagation():
    engine = CrossDomainInteractionEngine(random_seed=42)
    
    # Drought harvest shortfall (50% of baseline yield)
    res_shortfall = engine.propagate_agriculture_to_food_commerce(
        crop_yield_quintales=50.0,
        baseline_yield_quintales=100.0,
        transport_distance_km=60.0,
        is_paved_corridor=True,
    )
    assert res_shortfall["farmgate_price_per_quintal_usd"] > 25.0
    assert res_shortfall["wholesale_price_per_quintal_usd"] > res_shortfall["farmgate_price_per_quintal_usd"]
    assert res_shortfall["consumer_purchasing_power_loss_pct"] > 40.0


def test_environment_and_institution_propagation():
    engine = CrossDomainInteractionEngine(random_seed=42)
    
    # Environmental shock
    env_res = engine.propagate_environment_to_multiple_domains(
        drought_severity_index=0.75,
        flood_severity_index=0.10,
    )
    assert env_res["crop_yield_loss_pct"] > 40.0
    assert env_res["climate_displacement_risk_pct"] > 5.0

    # Institutional governance to community
    ins_res = engine.propagate_institutions_to_community(
        municipal_budget_execution_rate=0.88,
        civic_trust_score=0.75,
        active_adesco_participating_citizens=180,
    )
    assert ins_res["effective_service_coverage_pct"] > 75.0
    assert ins_res["community_project_completion_rate"] > 0.70

    # Traces logged
    traces = engine.get_causal_traces(limit=10)
    assert len(traces) >= 2
