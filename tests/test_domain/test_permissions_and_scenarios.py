"""Unit tests for DomainPermissionEngine and HumanCenteredScenarioEngine."""

import pytest
from saltbor.domain.models import ApprovalStatus, PermissionType, WorldLayerType
from saltbor.domain.permissions import DomainPermissionEngine
from saltbor.domain.scenarios import HumanCenteredScenarioEngine


def test_permission_role_authorization_and_geographic_bounds():
    perms = DomainPermissionEngine()

    # Citizen blocked from editing municipal Layer B
    assert perms.authorize("citizen_juan", PermissionType.CREATE, WorldLayerType.LAYER_B_WORLD) is False

    # Municipal administrator authorized within San Salvador bounds
    assert perms.authorize(
        "alcaldia_san_salvador",
        PermissionType.CREATE,
        WorldLayerType.LAYER_B_WORLD,
        target_coords=(-89.22, 13.69),
    ) is True

    # Municipal administrator blocked outside bounds (e.g., in Santa Ana)
    assert perms.authorize(
        "alcaldia_san_salvador",
        PermissionType.CREATE,
        WorldLayerType.LAYER_B_WORLD,
        target_coords=(-89.55, 13.98),
    ) is False


def test_proposal_lifecycle_workflow():
    perms = DomainPermissionEngine()
    prop = perms.submit_proposal(
        user_id="citizen_juan",
        title="Mercado Comunitario en Barrio San Jacinto",
        target_layer=WorldLayerType.LAYER_B_WORLD,
        proposed_feature_data={"stalls": 15},
        rationale="Fomentar comercio local y evitar intermediarios.",
    )
    assert prop["status"] == ApprovalStatus.PROPOSED.value

    # Review by municipal administrator
    approved = perms.review_proposal(
        reviewer_id="alcaldia_san_salvador",
        proposal_id=prop["proposal_id"],
        decision="APPROVED",
        comment="Viable proyecto con presupuesto participativo.",
    )
    assert approved is True
    assert perms.proposals[prop["proposal_id"]]["status"] == ApprovalStatus.APPROVED.value


def test_scenario_execution_and_comparative_deltas():
    scen_engine = HumanCenteredScenarioEngine()

    def eval_base(seed, scen):
        return {"cost": 100}, {"welfare": 50}, {"gdp": 1000.0, "affected_population_count": 50}

    def eval_int(seed, scen):
        return {"cost": 120}, {"welfare": 75}, {"gdp": 1150.0, "affected_population_count": 50}

    scen_engine.create_scenario("S_BASE", "Base", "Desc", "economy", [])
    scen_engine.execute_scenario("S_BASE", eval_base)

    scen_engine.create_scenario("S_INT", "Int", "Desc", "economy", [{"type": "subsidy"}], baseline_scenario_id="S_BASE")
    scen_engine.execute_scenario("S_INT", eval_int)

    comp = scen_engine.compare_scenarios("S_BASE", "S_INT")
    assert comp["indicator_deltas"]["gdp"] == 150.0
    assert comp["indicator_percentage_changes"]["gdp"] == 15.0
