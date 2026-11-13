"""API contract tests for Phase 1.6 perception and OSM geography endpoints.

Every value asserted here originates from backend state produced by an actual
simulation step or from the ingested geography database — never from the UI.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from saltbor.datasets.gis.pipeline import DEFAULT_OUTPUT
from saltbor.visualization.server import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    db = Path(tempfile.mkdtemp()) / "api16.db"
    app = create_app(seed=5, db_path=str(db))
    with TestClient(app) as test_client:
        test_client.post("/api/control/step?count=6")
        yield test_client


def test_perception_endpoint_returns_subjective_state(client: TestClient):
    roster = client.get("/api/individuals").json()
    assert roster
    uid = roster[0]["uid"]

    response = client.get(f"/api/individuals/{uid}/perception")
    assert response.status_code == 200
    payload = response.json()

    assert payload["human_uid"] == uid
    assert "acuity" in payload
    assert 0.0 <= payload["acuity"]["visual"] <= 1.0
    assert "recent_observations" in payload
    for observation in payload["recent_observations"]:
        assert observation["perceiver_uid"] == uid
        assert observation["detected"] is True
        assert "clarity" in observation

    overview = client.get("/api/perception/overview").json()
    assert overview["available"] is True
    assert overview["observations_total"] >= payload["total_observations"]


def test_individual_dossier_includes_perception(client: TestClient):
    uid = client.get("/api/individuals").json()[0]["uid"]
    dossier = client.get(f"/api/individuals/{uid}").json()
    assert "perception" in dossier
    assert dossier["perception"]["human_uid"] == uid


@pytest.mark.skipif(not DEFAULT_OUTPUT.exists(), reason="geography not ingested")
def test_geography_endpoints_expose_provenance_and_routes(client: TestClient):
    manifest = client.get("/api/geography/manifest").json()
    assert manifest["available"] is True
    assert manifest["dataset"]["license"] == "ODbL-1.0"
    assert "OpenStreetMap" in manifest["attribution"]
    assert manifest["layers"]["roads"]["feature_count"] > 0

    features = client.get(
        "/api/geography/features",
        params={
            "min_lon": -89.202,
            "min_lat": 13.693,
            "max_lon": -89.186,
            "max_lat": 13.704,
            "layer": "roads",
            "limit": 10,
            "include_geometry": "true",
        },
    ).json()
    assert features["count"] > 0
    assert features["features"][0]["layer"] == "roads"
    assert features["features"][0]["geometry"]["type"] in ("LineString", "MultiLineString")

    route = client.get(
        "/api/geography/route",
        params={
            "from_lat": 13.6978,
            "from_lon": -89.1915,
            "to_lat": 13.6995,
            "to_lon": -89.1890,
            "mode": "walk",
        },
    ).json()
    assert route["found"] is True
    assert route["distance_m"] > 0
    assert route["duration_minutes"] > 0
    assert "OpenStreetMap" in route["attribution"]
