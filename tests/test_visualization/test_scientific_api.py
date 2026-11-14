"""Tests for Phase 1.12 Scientific & Causal Inference REST Endpoints."""

import pytest
from fastapi.testclient import TestClient

from saltbor.visualization.api import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_list_scientific_experiments():
    res = client.get("/api/scientific/experiments")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 20
    ids = [d["experiment_id"] for d in data]
    assert "EXP_112_A" in ids
    assert "EXP_112_T" in ids


def test_run_scientific_experiment():
    res = client.post("/api/scientific/run/EXP_112_A")
    assert res.status_code == 200
    data = res.json()
    assert data["experiment_id"] == "EXP_112_A"
    assert data["success"] is True
    assert "migration_rate" in data["metrics"]


def test_get_causal_dag():
    res = client.get("/api/scientific/causal/dag")
    assert res.status_code == 200
    data = res.json()
    assert data["variable_count"] >= 8
    assert data["edge_count"] >= 7


def test_estimate_ate():
    payload = {
        "treatment_var": "education_level",
        "outcome_var": "adult_income",
        "treatment_val": 12.0,
        "control_val": 6.0,
        "sample_size": 50,
    }
    res = client.post("/api/scientific/causal/estimate_ate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["treatment_var"] == "education_level"
    assert data["ate"] > 0.0
    assert "parental_wealth" in data["potential_confounders"]


def test_trace_event_causality():
    res = client.get("/api/scientific/causal/trace/sample_event")
    assert res.status_code == 200
    data = res.json()
    assert "steps" in data
    assert len(data["steps"]) > 0


def test_sensitivity_sweep():
    payload = {
        "parameter_name": "initial_wealth",
        "baseline_value": 75.0,
        "low": 20.0,
        "high": 180.0,
        "steps": 5,
    }
    res = client.post("/api/scientific/sensitivity/sweep", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["parameter_name"] == "initial_wealth"
    assert "elasticities" in data


def test_counterfactual_compare():
    payload = {
        "scenario_name": "Test Highway",
        "intervention_tick": 20,
        "intervention_description": "New road",
        "altered_parameters": {"multiplier": 1.5},
    }
    res = client.post("/api/scientific/counterfactual/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["divergence_point_tick"] >= 20
    assert "total_trajectory_divergence" in data


def test_get_geographic_departments():
    res = client.get("/api/scientific/geographic/departments")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 14
    dept_names = [d["department"] for d in data]
    assert "San Salvador" in dept_names
    assert "La Unión" in dept_names


def test_get_statistical_observatory():
    res = client.get("/api/scientific/statistical/observatory")
    assert res.status_code == 200
    data = res.json()
    assert "gini_wealth" in data
    assert "palma_ratio" in data
    assert "ci_95_wealth" in data


def test_get_validation_report():
    res = client.get("/api/scientific/validation/report")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "VALIDATED_FRAMEWORK"
    assert len(data["official_benchmarks"]) >= 5
