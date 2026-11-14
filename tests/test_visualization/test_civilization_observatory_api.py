"""Tests for the Phase 1.11 Civilization Observatory REST Endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from saltbor.visualization.controller import SimulationController
from saltbor.visualization.server import create_app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "test_civ_api.db"
    ctrl = SimulationController(seed=42, db_path=str(db_file))
    app = create_app(controller=ctrl, seed=42, db_path=str(db_file))
    with TestClient(app) as test_client:
        yield test_client
    ctrl.stop_worker()


def test_civilization_observatory_overview(client: TestClient) -> None:
    res = client.get("/api/civilization/observatory/overview")
    assert res.status_code == 200
    data = res.json()
    assert "civilization_id" in data
    assert "civilization_name" in data
    assert data["civilization_name"] == "Sociedad Cuscatleca"
    assert "population" in data
    assert data["population"] > 0
    assert "phase" in data
    assert "conditions" in data
    assert isinstance(data["conditions"], list)
    assert "cohesion_index" in data
    assert "ecological_stress" in data
    assert "ecological_health" in data
    assert "gini_wealth" in data
    assert "mean_age" in data
    assert "dependency_ratio" in data
    assert "accounting_conservation_verified" in data
    assert data["accounting_conservation_verified"] is True
    assert "identity_vector" in data


def test_civilization_timeline(client: TestClient) -> None:
    res = client.get("/api/civilization/timeline?limit=50")
    assert res.status_code == 200
    data = res.json()
    assert "total_snapshots" in data
    assert "timeline" in data
    assert isinstance(data["timeline"], list)
    assert len(data["timeline"]) >= 1
    sample = data["timeline"][0]
    assert "year" in sample
    assert "population" in sample
    assert "total_gdp_production" in sample
    assert "ecological_health" in sample
    assert "active_conditions" in sample
    assert "events" in data


def test_civilization_settlements(client: TestClient) -> None:
    res = client.get("/api/civilization/settlements")
    assert res.status_code == 200
    data = res.json()
    assert "count" in data
    assert "active_count" in data
    assert "settlements" in data
    assert len(data["settlements"]) >= 1
    s = data["settlements"][0]
    assert "settlement_id" in s
    assert "name" in s
    assert "settlement_type" in s
    assert "status" in s
    assert "carrying_capacity" in s
    assert "water_access" in s
    assert "soil_fertility" in s
    assert "commercial_intensity" in s
    assert "infrastructure" in s


def test_civilization_generations(client: TestClient) -> None:
    res = client.get("/api/civilization/generations")
    assert res.status_code == 200
    data = res.json()
    assert "total_living" in data
    assert data["total_living"] > 0
    assert "max_generation_depth" in data
    assert "mean_age" in data
    assert "dependency_ratio" in data
    assert "generation_cohorts" in data
    assert "family_lineages" in data


def test_civilization_technologies(client: TestClient) -> None:
    res = client.get("/api/civilization/technologies")
    assert res.status_code == 200
    data = res.json()
    assert "total_technologies" in data
    assert data["total_technologies"] >= 1
    assert "known_by_civilization" in data
    assert "technologies" in data
    t = data["technologies"][0]
    assert "tech_id" in t
    assert "name" in t
    assert "domain" in t
    assert "status" in t
    assert "productivity_bonus" in t


def test_civilization_compare(client: TestClient) -> None:
    res = client.get("/api/civilization/compare")
    assert res.status_code == 200
    data = res.json()
    assert "total_runs_recorded" in data
    assert "runs" in data
    assert isinstance(data["runs"], list)


def test_run_longitudinal_civilization(client: TestClient) -> None:
    payload = {
        "years": 15.0,
        "seed": 101,
        "civilization_name": "Sociedad Cuscatleca Alternativa",
    }
    res = client.post("/api/civilization/run_longitudinal", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "run_id" in data
    assert data["seed"] == 101
    assert data["duration_years"] == 15.0
    assert data["civilization_name"] == "Sociedad Cuscatleca Alternativa"
    assert "final_population" in data
    assert "survived" in data
    assert "vector_distance_from_start" in data
    assert "timeline_sample_count" in data
    assert data["timeline_sample_count"] == 16
