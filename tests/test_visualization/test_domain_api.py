"""Integration tests for Phase 1.13 Universal Domain & Workspace API endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from saltbor.visualization.api import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_api_list_universal_domains():
    resp = client.get("/api/domain/domains")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 6
    domain_ids = [d["domain_id"] for d in data]
    assert "food_gastronomy" in domain_ids
    assert "commerce_retail" in domain_ids


def test_api_register_and_activate_domain():
    # Register
    reg_resp = client.post(
        "/api/domain/register",
        json={
            "domain_id": "test_domain_api",
            "name": "API Test Domain",
            "category": "culture_entertainment",
            "purpose": "Test API domain registration",
            "geographic_scope": "San Salvador",
            "resources": ["tickets"],
            "activities": ["attend_concert"],
            "indicators": ["ticket_sales"],
        },
    )
    assert reg_resp.status_code == 200
    assert reg_resp.json()["status"] == "REGISTERED"

    # Activate
    act_resp = client.post("/api/domain/activate/test_domain_api")
    assert act_resp.status_code == 200
    assert act_resp.json()["status"] == "ACTIVE"


def test_api_list_activities():
    resp = client.get("/api/domain/activities?category=food")
    assert resp.status_code == 200
    acts = resp.json()
    assert len(acts) >= 5
    assert any(a["activity_id"] == "food.visit_restaurant" for a in acts)


def test_api_world_layers_and_feature_creation():
    # Get summary
    sum_resp = client.get("/api/domain/world/layers")
    assert sum_resp.status_code == 200
    assert "layer_a_base" in sum_resp.json()

    # Create Layer B feature
    feat_resp = client.post(
        "/api/domain/world/features",
        json={
            "layer": "layer_b_world",
            "geometry_type": "Point",
            "coordinates": [-89.224, 13.698],
            "name": "Mercado Modelo Central",
            "category": "market_facility",
            "owner_id": "alcaldia_ss",
        },
    )
    assert feat_resp.status_code == 200
    assert feat_resp.json()["status"] == "CREATED"

    # Verify Layer A mutation is strictly blocked (HTTP 403)
    block_resp = client.post(
        "/api/domain/world/features",
        json={
            "layer": "layer_a_base",
            "geometry_type": "Point",
            "coordinates": [-89.224, 13.698],
            "name": "Illegal Feature",
            "category": "test",
        },
    )
    assert block_resp.status_code == 403


def test_api_permissions_authorize():
    resp = client.post(
        "/api/domain/permissions/authorize",
        json={
            "user_id": "alcaldia_san_salvador",
            "action": "create",
            "target_layer": "layer_b_world",
            "target_coords": [-89.22, 13.69],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["authorized"] is True


def test_api_recommendations():
    resp = client.post(
        "/api/domain/recommendations",
        json={
            "user_objective": "Fomentar emprendimiento gastronómico local",
            "priorities": ["commercial_profitability", "community_development"],
            "geographic_context": "San Salvador Centro",
            "domain_id": "food_gastronomy",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "expected_benefits" in data
    assert "traceable_reasoning" in data


def test_api_food_feasibility_and_elasticity():
    feas_resp = client.post(
        "/api/domain/food/feasibility",
        json={"latitude": 13.698, "longitude": -89.224, "target_food_type": "pupuseria"},
    )
    assert feas_resp.status_code == 200
    assert "commercially_viable" in feas_resp.json()

    elast_resp = client.post(
        "/api/domain/food/price_elasticity",
        json={"establishment_id": "pupuseria_dona_carmen", "price_multiplier": 1.20},
    )
    assert elast_resp.status_code == 200
    assert "demand_elasticity" in elast_resp.json()


def test_api_compact_experiments_progressive_disclosure():
    # Run an experiment to ensure record exists
    run_resp = client.post("/api/domain/experiments/phase113/run/EXP_113_A")
    assert run_resp.status_code == 200
    assert run_resp.json()["success"] is True

    # Level 1: Summary
    s_resp = client.get("/api/domain/experiments/compact/EXP_113_A/level/summary")
    assert s_resp.status_code == 200
    assert s_resp.json()["level"] == "SUMMARY"

    # Level 2: Evidence
    e_resp = client.get("/api/domain/experiments/compact/EXP_113_A/level/evidence")
    assert e_resp.status_code == 200
    assert e_resp.json()["level"] == "EVIDENCE"

    # Level 3: Technical
    t_resp = client.get("/api/domain/experiments/compact/EXP_113_A/level/technical")
    assert t_resp.status_code == 200
    assert t_resp.json()["level"] == "TECHNICAL"

    # On-demand source code
    src_resp = client.get("/api/domain/experiments/compact/EXP_113_A/source")
    assert src_resp.status_code == 200
    assert len(src_resp.json()) >= 1
