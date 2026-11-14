"""Unit tests for Food, Commerce, Education, Healthcare, Transportation, and Agriculture domains."""

import pytest
from saltbor.domain.agriculture import AgricultureActivityDomain
from saltbor.domain.commerce import BusinessActivityDomain
from saltbor.domain.education import EducationActivityDomain
from saltbor.domain.food import FoodActivityDomain
from saltbor.domain.healthcare import HealthcareActivityDomain
from saltbor.domain.transportation import TransportationActivityDomain


def test_food_domain_analytical_queries():
    food = FoodActivityDomain()
    # Query food sold in area
    nearby = food.query_food_sold_in_area(13.6985, -89.2245, radius_meters=1000.0)
    assert len(nearby) >= 2

    # Query unmet demand
    unmet = food.query_unmet_demand(13.6985, -89.2245)
    assert "unmet_demand_categories" in unmet

    # Simulate pupusería opening scenario
    pup_scen = food.simulate_new_pupuseria_scenario(13.6980, -89.2240)
    assert "commercially_viable" in pup_scen
    assert "estimated_net_profit_usd" in pup_scen

    # Price increase elasticity
    elast = food.simulate_price_increase_elasticity("pupuseria_dona_carmen", price_multiplier=1.25)
    assert "demand_elasticity" in elast
    assert "customer_loss_count" in elast


def test_business_commerce_accounting_conservation():
    comm = BusinessActivityDomain()
    ent = comm.enterprises["ferreteria_la_central"]
    initial_cash = ent.cash_liquidity
    initial_stock = ent.inventory["martillo"]

    # Process purchase
    res = comm.process_customer_purchase(
        enterprise_id="ferreteria_la_central",
        item_name="martillo",
        quantity=2,
        buyer_cash=50.0,
    )
    assert res["success"] is True
    assert ent.inventory["martillo"] == initial_stock - 2
    assert ent.cash_liquidity == initial_cash + res["total_paid_usd"]


def test_education_attendance_and_transport_intervention():
    edu = EducationActivityDomain()
    fac_id = "escuela_rural_chalatenango"
    res = edu.evaluate_educational_intervention(fac_id, intervention_type="school_bus", sample_students_count=40)
    assert res["attendance_rate_gain_pct"] > 0
    assert res["intervention_attendance_rate"] >= res["baseline_attendance_rate"]


def test_healthcare_queue_and_physician_expansion():
    health = HealthcareActivityDomain()
    fac_id = "unidad_salud_san_salvador"
    res = health.evaluate_capacity_expansion_intervention(fac_id, additional_physicians=2, simulated_patient_arrivals=50)
    assert res["wait_time_reduction_pct"] > 0
    assert res["intervention_attended"] >= res["baseline_attended"]


def test_transportation_detour_delay():
    trans = TransportationActivityDomain()
    norm = trans.simulate_commute_trip("u1", "Santa Tecla", "San Salvador", budget_usd=1.0)
    assert norm["status"] == "commuted_normal"

    route = trans.routes["ruta_42_san_salvador"]
    route.is_blocked = True
    blocked = trans.simulate_commute_trip("u1", "Santa Tecla", "San Salvador", budget_usd=1.0)
    route.is_blocked = False
    assert blocked["status"] == "detour_due_to_blockage"
    assert blocked["travel_time_minutes"] > norm["travel_time_minutes"]


def test_agriculture_drought_yield_impact():
    agri = AgricultureActivityDomain()
    norm = agri.simulate_crop_cycle("parcela_san_vicente_1", has_severe_canicula=False)
    drought = agri.simulate_crop_cycle("parcela_san_vicente_1", has_severe_canicula=True)
    assert drought["actual_harvest_quintales"] < norm["actual_harvest_quintales"]
    assert drought["loss_pct_due_to_drought"] >= 40.0
