"""Test that the web application static assets are served properly."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from saltbor.visualization.controller import SimulationController
from saltbor.visualization.server import create_app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "test_web_assets.db"
    ctrl = SimulationController(seed=42, db_path=str(db_file))
    app = create_app(controller=ctrl, seed=42, db_path=str(db_file))
    with TestClient(app) as test_client:
        yield test_client
    ctrl.stop_worker()


def test_index_html_served(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert "SALTBOR" in html
    assert "FASE 1.3-V" in html
    assert "world-canvas" in html
    assert "view-individual" in html
    assert "view-cognitive" in html
    assert "view-knowledge" in html
    assert "view-social" in html
    assert "view-civilization" in html
    assert "view-economy" in html
    assert "view-timeline" in html
    assert "view-laboratory" in html
    assert "view-reports" in html


def test_style_css_served(client: TestClient) -> None:
    res = client.get("/style.css")
    assert res.status_code == 200
    assert "--accent-sky" in res.text
    assert "control-center" in res.text


def test_app_js_served(client: TestClient) -> None:
    res = client.get("/app.js")
    assert res.status_code == 200
    assert "renderWorldLoop" in res.text
    assert "fetchIndividualsRoster" in res.text
    assert "projectGeo" in res.text
