"""Unit tests for EditableWorldEngine (Layers A, B, C, D)."""

import pytest
from saltbor.domain.editable_world import EditableWorldEngine
from saltbor.domain.models import FeatureGeometryType, WorldLayerType


def test_layer_a_immutability():
    world = EditableWorldEngine()
    with pytest.raises(PermissionError):
        world.create_feature(
            layer=WorldLayerType.LAYER_A_BASE,
            geometry_type=FeatureGeometryType.POINT,
            coordinates=[-89.22, 13.69],
            name="Attempted Base Mutation",
            category="test",
        )


def test_layer_b_c_d_feature_authoring_and_query():
    world = EditableWorldEngine()

    # Create Layer B municipal zone polygon
    zone = world.create_custom_zone_polygon(
        name="Distrito Culinario",
        polygon_coordinates=[[-89.23, 13.69], [-89.22, 13.69], [-89.22, 13.70], [-89.23, 13.69]],
        owner_id="alcaldia_ss",
    )
    assert zone.feature_id in [f.feature_id for f in world.query_layer(WorldLayerType.LAYER_B_WORLD)]

    # Create Layer C business point
    biz = world.create_custom_facility_point(
        name="Pupusería El Triunfo",
        latitude=13.698,
        longitude=-89.224,
        facility_category="food_establishment",
        owner_id="carmen",
        layer=WorldLayerType.LAYER_C_ACTIVITY,
    )
    assert biz.feature_id in [f.feature_id for f in world.query_layer(WorldLayerType.LAYER_C_ACTIVITY)]


def test_scenario_branching_and_isolation():
    world = EditableWorldEngine()
    feat = world.create_feature(
        layer=WorldLayerType.LAYER_D_INTERVENTIONS,
        geometry_type=FeatureGeometryType.POINT,
        coordinates=[-89.225, 13.695],
        name="Proposed Park",
        category="urban_intervention",
        scenario_id="scen_orig",
        owner_id="alcaldia_ss",
        properties={"budget": 10000},
    )

    clones = world.duplicate_scenario(
        source_scenario_id="scen_orig",
        new_scenario_id="scen_cloned",
        new_name="Alternative High-Budget Park",
        owner_id="alcaldia_ss",
    )
    assert len(clones) == 1
    clone_id = clones[0].feature_id

    # Update clone
    world.update_feature_properties(clone_id, {"budget": 25000}, user_id="alcaldia_ss")
    assert world.get_feature(feat.feature_id).properties["budget"] == 10000
    assert world.get_feature(clone_id).properties["budget"] == 25000
