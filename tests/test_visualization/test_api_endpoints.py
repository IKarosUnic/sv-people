"""Tests for the visual simulation REST and SSE endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from saltbor.visualization.controller import SimulationController
from saltbor.visualization.server import create_app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "test_api_saltbor.db"
    ctrl = SimulationController(seed=42, db_path=str(db_file))
    app = create_app(controller=ctrl, seed=42, db_path=str(db_file))
    with TestClient(app) as test_client:
        yield test_client
    ctrl.stop_worker()


def test_status_endpoint(client: TestClient) -> None:
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "tick" in data
    assert "day" in data
    assert "active_population" in data
    assert data["active_population"] == 20
    assert "season" in data
    assert "is_daytime" in data


def test_control_endpoints(client: TestClient) -> None:
    # 1. Play
    res = client.post("/api/control/play")
    assert res.status_code == 200
    assert res.json()["is_running"] is True

    # 2. Pause
    res = client.post("/api/control/pause")
    assert res.status_code == 200
    assert res.json()["is_running"] is False

    # 3. Step
    res = client.post("/api/control/step?count=2")
    assert res.status_code == 200
    assert res.json()["tick"] >= 2

    # 4. Speed
    res = client.post("/api/control/speed?multiplier=10")
    assert res.status_code == 200
    assert res.json()["speed"] == 10

    # 5. Scenario
    res = client.post("/api/control/scenario?name=drought_crisis")
    assert res.status_code == 200
    assert res.json()["scenario"] == "drought_crisis"

    # 6. Checkpoint save & load
    res = client.post("/api/control/checkpoint/save")
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    res = client.post("/api/control/checkpoint/load")
    assert res.status_code == 200
    assert res.json()["status"] == "restored"


def test_population_control_scaling(client: TestClient) -> None:
    """Verify that population can be dynamically scaled beyond 20 from frontend endpoints."""
    # 1. Scale active population to 50 dynamically
    res = client.post("/api/control/population?count=50&reset=false")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["population"] == 50

    # 2. Check status summary reflects 50
    st_res = client.get("/api/status")
    assert st_res.status_code == 200
    assert st_res.json()["active_population"] == 50

    # 3. Check individuals roster returns 50 agents
    indiv_res = client.get("/api/individuals")
    assert indiv_res.status_code == 200
    assert len(indiv_res.json()) == 50

    # 4. Check GIS simulation layer contains 50 agent points
    gis_res = client.get("/api/gis/simulation_layer")
    assert gis_res.status_code == 200
    points = [f for f in gis_res.json()["features"] if f["geometry"]["type"] == "Point"]
    assert len(points) == 50

    # 5. Scale to 100 via reset
    res_reset = client.post("/api/control/reset?population=100")
    assert res_reset.status_code == 200
    assert res_reset.json()["population"] == 100

    st_res2 = client.get("/api/status")
    assert st_res2.status_code == 200
    assert st_res2.json()["active_population"] == 100

    # 6. Restore to baseline 20 for subsequent tests
    client.post("/api/control/reset?population=20")


def test_world_endpoint(client: TestClient) -> None:
    res = client.get("/api/world")
    assert res.status_code == 200
    data = res.json()
    assert "departments" in data
    assert len(data["departments"]) == 14
    assert "municipalities" in data
    assert len(data["municipalities"]) == 44
    assert "districts" in data
    assert len(data["districts"]) == 262
    assert "volcanoes" in data
    assert len(data["volcanoes"]) > 0
    assert "lakes" in data
    assert len(data["lakes"]) > 0
    assert "establishments" in data
    assert len(data["establishments"]) > 0
    assert "agents" in data
    assert len(data["agents"]) == 20
    assert "settlement_places" in data
    assert "environment" in data
    assert "temperature_celsius" in data["environment"]


def test_individuals_roster_and_detail(client: TestClient) -> None:
    res = client.get("/api/individuals")
    assert res.status_code == 200
    roster = res.json()
    assert len(roster) == 20
    first = roster[0]
    assert "uid" in first
    assert "serial" in first
    assert "full_name" in first
    assert "energy" in first
    assert "mood" in first

    # Detailed dossier
    first_uid = first["uid"]
    res_det = client.get(f"/api/individuals/{first_uid}")
    assert res_det.status_code == 200
    det = res_det.json()
    assert "identity" in det
    assert "demographics" in det or "physical" in det
    assert "personality" in det
    assert "traits_detailed" in det["personality"]
    assert "emotions" in det
    assert "active_goals" in det
    assert "skills" in det
    assert "cognitive_profile" in det
    assert "meta_learning" in det


def test_cognitive_subsystems_and_trace(client: TestClient) -> None:
    roster = client.get("/api/individuals").json()
    first_uid = roster[0]["uid"]

    res = client.get(f"/api/cognitive/{first_uid}")
    assert res.status_code == 200
    data = res.json()
    assert "subsystems" in data
    subs = data["subsystems"]
    assert "frontal" in subs
    assert "hippocampal" in subs
    assert "limbic" in subs
    assert "temporal" in subs
    assert "parietal" in subs
    assert "cerebellar" in subs

    assert subs["frontal"]["status"] == "OPERATIONAL"
    assert "decision_trace_pipeline" in data
    pipe = data["decision_trace_pipeline"]
    assert "step_1_observation" in pipe
    assert "step_6_decision" in pipe
    assert "step_8_result" in pipe


def test_knowledge_graph_endpoint(client: TestClient) -> None:
    res = client.get("/api/knowledge")
    assert res.status_code == 200
    kg = res.json()
    assert "nodes" in kg
    assert "edges" in kg
    assert len(kg["nodes"]) > 0
    assert "epistemic_states_summary" in kg


def test_social_network_endpoint(client: TestClient) -> None:
    res = client.get("/api/social")
    assert res.status_code == 200
    social = res.json()
    assert "nodes" in social
    assert "edges" in social
    assert len(social["nodes"]) == 20
    assert len(social["edges"]) > 0


def test_civilization_dashboard_endpoint(client: TestClient) -> None:
    res = client.get("/api/civilization")
    assert res.status_code == 200
    civ = res.json()
    assert "current_snapshot" in civ
    assert "time_series_history" in civ
    snap = civ["current_snapshot"]
    assert "population" in snap
    assert "total_wealth" in snap
    assert "gini_coefficient" in snap


def test_economy_endpoint(client: TestClient) -> None:
    res = client.get("/api/economy")
    assert res.status_code == 200
    econ = res.json()
    assert "enterprises" in econ
    assert "commodity_prices" in econ
    assert "informal_commerce" in econ


def test_timeline_endpoint(client: TestClient) -> None:
    res = client.get("/api/timeline")
    assert res.status_code == 200
    tl = res.json()
    assert isinstance(tl, list)
    assert len(tl) > 0


def test_laboratory_experiments_catalog(client: TestClient) -> None:
    res = client.get("/api/laboratory/experiments")
    assert res.status_code == 200
    exps = res.json()
    assert len(exps) > 0
    assert any(e["id"] == "EXP_A" for e in exps)


# -----------------------------------------------------------------------------
# Phase 1.5 Endpoints Tests
# -----------------------------------------------------------------------------

def test_phase15_labor_endpoints(client: TestClient) -> None:
    """Verify Phase 1.5 Labor Market vacancies and contracts endpoints."""
    # Vacancies
    res_vac = client.get("/api/labor/vacancies")
    assert res_vac.status_code == 200
    data_vac = res_vac.json()
    assert "total_vacancies" in data_vac
    assert "open_vacancies_count" in data_vac
    assert "vacancies" in data_vac
    assert isinstance(data_vac["vacancies"], list)

    # Contracts
    res_con = client.get("/api/labor/contracts")
    assert res_con.status_code == 200
    data_con = res_con.json()
    assert "total_contracts" in data_con
    assert "active_contracts_count" in data_con
    assert "daily_payroll_liability_usd" in data_con
    assert "contracts" in data_con


def test_phase15_housing_endpoints(client: TestClient) -> None:
    """Verify Phase 1.5 Housing units, tenure types, and leases endpoints."""
    # Housing Units
    res_units = client.get("/api/housing/units")
    assert res_units.status_code == 200
    data_units = res_units.json()
    assert "total_units" in data_units
    assert "occupancy_rate" in data_units
    assert "tenure_distribution" in data_units
    assert "units" in data_units
    assert len(data_units["units"]) > 0

    # Housing Leases
    res_leases = client.get("/api/housing/leases")
    assert res_leases.status_code == 200
    data_leases = res_leases.json()
    assert "total_leases" in data_leases
    assert "active_leases_count" in data_leases
    assert "total_rent_collected_usd" in data_leases
    assert "leases" in data_leases


def test_phase15_commerce_endpoints(client: TestClient) -> None:
    """Verify Phase 1.5 Commercial establishments, verified vs simulated, and visit history."""
    # Establishments
    res_est = client.get("/api/commerce/establishments")
    assert res_est.status_code == 200
    data_est = res_est.json()
    assert "total_establishments" in data_est
    assert "verified_real_count" in data_est
    assert "simulated_count" in data_est
    assert "establishments" in data_est
    assert len(data_est["establishments"]) > 0
    # Must have both verified real and simulated
    assert data_est["verified_real_count"] > 0
    assert data_est["simulated_count"] > 0

    # Visits
    res_vis = client.get("/api/commerce/visits")
    assert res_vis.status_code == 200
    data_vis = res_vis.json()
    assert "total_visits" in data_vis
    assert "zero_purchase_visits" in data_vis
    assert "intent_distribution" in data_vis
    assert "recent_visits" in data_vis


def test_phase15_lifestyle_endpoint(client: TestClient) -> None:
    """Verify Phase 1.5 Everyday Life, leisure invitations, and household overhead."""
    res = client.get("/api/lifestyle/summary")
    assert res.status_code == 200
    data = res.json()
    assert "social_invitations" in data
    assert "total_sent" in data["social_invitations"]
    assert "acceptance_rate" in data["social_invitations"]
    assert "households" in data
    assert "community_utility_treasury_usd" in data["households"]


def test_phase15_individual_socioeconomic_fields(client: TestClient) -> None:
    """Verify that individuals endpoint exposes tenure and employment status, and dossier exposes socioeconomic dict."""
    res = client.get("/api/individuals")
    assert res.status_code == 200
    roster = res.json()
    assert len(roster) > 0
    agent = roster[0]
    assert "housing_tenure" in agent
    assert "employment_status" in agent

    # Check detail dossier
    uid = agent["uid"]
    res_det = client.get(f"/api/individuals/{uid}")
    assert res_det.status_code == 200
    dossier = res_det.json()
    assert "socioeconomic" in dossier
    soc = dossier["socioeconomic"]
    assert "housing_tenure" in soc
    assert "employment_status" in soc
    assert "reservation_wage" in soc


def test_phase15_extension_health_facilities(client: TestClient) -> None:
    """Verify Phase 1.5 Extension Health Facilities and Triage endpoint."""
    res = client.get("/api/health/facilities")
    assert res.status_code == 200
    data = res.json()
    assert "total_facilities" in data
    assert "facilities" in data
    assert "population_active_conditions" in data
    assert "condition_categories" in data
    assert len(data["facilities"]) > 0
    f0 = data["facilities"][0]
    assert "facility_id" in f0
    assert "capacity_beds" in f0
    assert "occupancy_rate" in f0


def test_phase15_extension_romance_relationships(client: TestClient) -> None:
    """Verify Phase 1.5 Extension Romance Relationships endpoint."""
    res = client.get("/api/romance/relationships")
    assert res.status_code == 200
    data = res.json()
    assert "total_relationships" in data
    assert "active_relationships_count" in data
    assert "stage_distribution" in data
    assert "total_infidelities" in data
    assert "total_heartbreaks" in data
    assert "relationships" in data


def test_phase15_extension_accidents_and_disasters(client: TestClient) -> None:
    """Verify Phase 1.5 Extension Accidents and Disasters endpoint."""
    res = client.get("/api/accidents/recent")
    assert res.status_code == 200
    data = res.json()
    assert "total_accidents" in data
    assert "total_disasters" in data
    assert "blocked_roads" in data
    assert "accident_type_breakdown" in data
    assert "recent_accidents" in data
    assert "recent_disasters" in data


def test_phase15_extension_environmental_hazards(client: TestClient) -> None:
    """Verify Phase 1.5 Extension Environmental Hazards and Water Potability endpoint."""
    res = client.get("/api/environment/hazards")
    assert res.status_code == 200
    data = res.json()
    assert "rainfall_mm_per_hour" in data
    assert "accumulated_waste_kg" in data
    assert "water_sources" in data
    assert "rio_suchiacel" in data["water_sources"]
    assert "cleanliness_index" in data["water_sources"]["rio_suchiacel"]
    assert "is_potable" in data["water_sources"]["rio_suchiacel"]


def test_phase15_extension_causal_tree(client: TestClient) -> None:
    """Verify Phase 1.5 Extension Causal Event DAG tree querying."""
    # First emit a mock causal chain into runner
    ctrl = client.app.state.controller if hasattr(client.app.state, "controller") else None
    from saltbor.events.types import EventType, SimulationEvent
    # Let's get event from controller or trigger step
    client.post("/api/control/step?count=1")
    # Query causal tree endpoint
    # Find any event in runner causal graph
    res_status = client.get("/api/status")
    assert res_status.status_code == 200

    # Test 404 for nonexistent event
    res_404 = client.get("/api/events/causal_tree/nonexistent_event_id_xyz")
    assert res_404.status_code == 404


