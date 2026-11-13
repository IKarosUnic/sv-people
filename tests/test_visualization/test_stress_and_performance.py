"""Performance benchmarks and stress tests for the visualization backend."""

from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from saltbor.visualization.controller import SimulationController
from saltbor.visualization.server import create_app


@pytest.fixture(scope="module")
def perf_setup(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("perf_db") / "perf_saltbor.db"
    ctrl = SimulationController(seed=999, db_path=str(db_file))
    app = create_app(controller=ctrl, seed=999, db_path=str(db_file))
    with TestClient(app) as test_client:
        yield ctrl, test_client
    ctrl.stop_worker()


def test_simulation_stepping_throughput(perf_setup) -> None:
    ctrl, _ = perf_setup
    ticks_to_run = 50
    t0 = time.perf_counter()
    ctrl.step_sync(count=ticks_to_run)
    elapsed = time.perf_counter() - t0
    rate = ticks_to_run / elapsed

    assert elapsed > 0
    assert rate > 20.0, f"Expected >20 ticks/sec, got {rate:.1f}"


def test_world_endpoint_response_time(perf_setup) -> None:
    _, client = perf_setup
    latencies = []
    for _ in range(5):
        t0 = time.perf_counter()
        res = client.get("/api/world")
        assert res.status_code == 200
        latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_ms = sum(latencies) / len(latencies)
    assert avg_ms < 50.0, f"Average /api/world latency {avg_ms:.2f}ms exceeds target 50ms"


def test_cognitive_dossier_response_time(perf_setup) -> None:
    _, client = perf_setup
    roster = client.get("/api/individuals").json()
    uid = roster[0]["uid"]

    latencies = []
    for _ in range(5):
        t0 = time.perf_counter()
        res = client.get(f"/api/cognitive/{uid}")
        assert res.status_code == 200
        latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_ms = sum(latencies) / len(latencies)
    assert avg_ms < 25.0, f"Average /api/cognitive/{uid} latency {avg_ms:.2f}ms exceeds target 25ms"


def test_knowledge_graph_filtering_scalability(perf_setup) -> None:
    _, client = perf_setup
    res = client.get("/api/knowledge?max_nodes=300")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) <= 300


def test_multiple_event_subscribers_decoupling(perf_setup) -> None:
    ctrl, _ = perf_setup
    q1 = ctrl.subscribe_events()
    q2 = ctrl.subscribe_events()

    ctrl.step_sync(count=2)

    assert not q1.empty()
    assert not q2.empty()

    ctrl.unsubscribe_events(q1)
    ctrl.unsubscribe_events(q2)
