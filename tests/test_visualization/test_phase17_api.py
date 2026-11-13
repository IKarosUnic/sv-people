"""API contract tests for Phase 1.7 psychological observability."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from saltbor.visualization.server import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    db = Path(tempfile.mkdtemp()) / "api17.db"
    app = create_app(seed=9, db_path=str(db))
    with TestClient(app) as test_client:
        test_client.post("/api/control/step?count=4")
        yield test_client


def test_psychology_overview_comes_from_simulation_state(client: TestClient):
    payload = client.get("/api/psychology/overview").json()
    assert payload["individuals"] > 0
    assert payload["stats"]["appraisals"] > 0
    assert 0.0 <= payload["mean_stress"] <= 1.0
    assert "coping_attempts" in payload


def test_individual_psychology_and_timeline(client: TestClient):
    uid = client.get("/api/individuals").json()[0]["uid"]
    snapshot = client.get(f"/api/psychology/individual/{uid}").json()
    assert snapshot["human_uid"] == uid
    assert "state" in snapshot
    assert "chronic_stress" in snapshot["state"]
    assert "constitution" in snapshot
    assert "coping" in snapshot

    dossier = client.get(f"/api/individuals/{uid}").json()
    assert "psychology" in dossier
    assert dossier["psychology"]["human_uid"] == uid

    timeline = client.get(f"/api/psychology/timeline/{uid}").json()
    assert timeline["uid"] == uid
    assert "entries" in timeline
    assert "crises" in timeline


def test_social_support_view_is_backend_derived(client: TestClient):
    uid = client.get("/api/individuals").json()[0]["uid"]
    social = client.get(f"/api/psychology/social/{uid}").json()
    assert social["uid"] == uid
    assert "support" in social
    assert 0.0 <= social["support"]["perceived_support"] <= 1.0
