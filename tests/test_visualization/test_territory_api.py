"""Integration tests for Phase 1.14 Territorial Ecosystem & Observatory API endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from saltbor.visualization.api import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_api_territory_summary_and_hierarchy():
    r1 = client.get("/api/territory/summary")
    assert r1.status_code == 200
    summary = r1.json()
    assert summary["country"] == "El Salvador"
    assert summary["departments_count"] == 14
    assert summary["municipalities_count"] == 44
    assert summary["total_simulated_population"] > 0

    r2 = client.get("/api/territory/hierarchy")
    assert r2.status_code == 200
    hier = r2.json()
    assert len(hier["departments"]) == 14
    assert len(hier["municipalities"]) == 44


def test_api_cross_domain_endpoints():
    # Graph
    r1 = client.get("/api/territory/cross_domain/graph")
    assert r1.status_code == 200
    graph = r1.json()
    assert graph["total_interactions"] >= 6
    assert len(graph["domains"]) >= 6

    # Simulate interaction
    r2 = client.post(
        "/api/territory/cross_domain/simulate",
        json={
            "mechanism": "trans_accessibility",
            "params": {"road_friction_multiplier": 2.0, "is_road_disrupted": True},
        },
    )
    assert r2.status_code == 200
    data = r2.json()
    assert "outputs" in data
    assert "effective_reach_km" in data["outputs"]


def test_api_multi_scale_views():
    # Dept scale
    r1 = client.get("/api/territory/multi_scale/view/level_6_department_national")
    assert r1.status_code == 200
    assert r1.json()["total_population"] > 0

    # Household scale
    r2 = client.get("/api/territory/multi_scale/view/level_2_household")
    assert r2.status_code == 200
    assert r2.json()["total_households"] > 0

    # Single individual hierarchy
    r3 = client.get("/api/territory/individual/human_0001/hierarchy")
    assert r3.status_code == 200
    h = r3.json()
    assert "level_1_individual" in h
    assert "level_6_department_national" in h


def test_api_economic_network_and_trade():
    # Summary
    r1 = client.get("/api/territory/economic_network/summary")
    assert r1.status_code == 200
    econ = r1.json()
    assert len(econ["nodes"]) >= 4
    assert len(econ["links"]) >= 2

    # Conserved trade
    r2 = client.post(
        "/api/territory/economic_network/trade",
        json={
            "buyer_id": "wholesaler_tiendona_ss",
            "seller_id": "farm_usulutan_1",
            "commodity": "maiz_quintal",
            "quantity_units": 4,
            "link_id": "link_usulutan_tiendona",
        },
    )
    assert r2.status_code == 200
    assert r2.json()["success"] is True

    # Price transmission
    r3 = client.get("/api/territory/economic_network/price_transmission?farmgate_cost=20.0&commodity=maiz_quintal")
    assert r3.status_code == 200
    assert r3.json()["final_consumer_retail_price_usd"] > 20.0


def test_api_public_services_and_accessibility():
    # List facilities
    r1 = client.get("/api/territory/public_services/facilities")
    assert r1.status_code == 200
    assert len(r1.json()) >= 6

    # Accessibility query
    r2 = client.get("/api/territory/public_services/accessibility?lat=13.6989&lon=-89.1914&category=healthcare")
    assert r2.status_code == 200
    acc = r2.json()
    assert acc["has_accessible_facility"] is True
    assert acc["accessibility_index"] > 0.0

    # Submit demand
    r3 = client.post(
        "/api/territory/public_services/demand",
        json={"facility_id": "salud_chalatenango", "demanding_citizens_count": 25},
    )
    assert r3.status_code == 200
    assert r3.json()["served_citizens"] == 25


def test_api_governance_workflow():
    # Submit proposal
    r1 = client.post(
        "/api/territory/governance/propose",
        json={
            "actor_id": "citizen_ss_01",
            "title": "Clinica Comunitaria Rural",
            "description": "Construct small community health post",
            "project_type": "healthcare_facility",
            "target_department_code": "SS",
            "target_municipality_id": "SS01",
            "requested_budget_usd": 25000.0,
            "is_simulated_intervention": True,
        },
    )
    assert r1.status_code == 200
    pid = r1.json()["proposal_id"]

    # Review proposal with authorized municipal admin
    r2 = client.post(
        "/api/territory/governance/review",
        json={
            "reviewer_id": "admin_muni_ss_centro",
            "proposal_id": pid,
            "decision": "APPROVE",
            "notes": "Approved under local health initiative",
        },
    )
    assert r2.status_code == 200
    assert r2.json()["success"] is True

    # List proposals
    r3 = client.get("/api/territory/governance/proposals")
    assert r3.status_code == 200
    assert any(p["proposal_id"] == pid for p in r3.json())


def test_api_needs_assessment_and_projects():
    # Needs assessment
    r1 = client.get("/api/territory/needs/assessment?territory_id=chalatenango_dist")
    assert r1.status_code == 200
    data = r1.json()
    assert len(data["needs"]) >= 4
    assert len(data["pareto_priorities"]) >= 4

    # Project alternatives
    r2 = client.get("/api/territory/projects/alternatives")
    assert r2.status_code == 200
    alts = r2.json()
    assert alts["alternatives_compared_count"] >= 2


def test_api_phase114_experiments_listing_and_run():
    # List experiments
    r1 = client.get("/api/territory/experiments/phase114")
    assert r1.status_code == 200
    exps = r1.json()
    assert len(exps) == 20

    # Run EXP_114_N (Multi-Scale Population Consistency)
    r2 = client.post("/api/territory/experiments/phase114/run/EXP_114_N")
    assert r2.status_code == 200
    res = r2.json()
    assert res["success"] is True
    assert res["experiment_id"] == "EXP_114_N"


def test_api_connected_scenarios_demonstration():
    res = client.post("/api/territory/connected_scenarios/run")
    assert res.status_code == 200
    data = res.json()
    assert "Demostración de Escenarios Conectados" in data["title"]
    assert len(data["shared_individuals"]) == 5
    assert len(data["stages"]) == 5

    # Check stage 1 vs stage 2 vs stage 4 vs stage 5
    s1 = data["stages"][0]
    s2 = data["stages"][1]
    s4 = data["stages"][3]
    s5 = data["stages"][4]

    assert s1["commercial"]["road_friction_multiplier"] == 1.0
    assert s2["commercial"]["road_friction_multiplier"] >= 3.0
    assert s4["household"]["jose_cash_usd"] == 0.0
    assert s4["healthcare"]["clinic_wait_hours"] >= 3.0
    assert s5["education"]["mateo_attendance_pct"] >= 90.0
