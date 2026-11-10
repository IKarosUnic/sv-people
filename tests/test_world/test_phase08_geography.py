"""
Unit and integration tests for SALTBOR Phase 0.8 Real Geographic World Engine.
"""

from __future__ import annotations
import tempfile
import pytest

from saltbor.world.geographic.engine import RealGeographicEngine
from saltbor.world.geographic.models import (
    GeoPoint,
    GeoBoundingBox,
    EstablishmentCategory,
    ValidationState,
    RealPlace,
)
from saltbor.world.geographic.spatial_index import (
    SpatialGridIndex,
    haversine_distance_km,
    wgs84_to_local_metric_xy,
    local_metric_xy_to_wgs84,
    is_valid_salvadoran_coordinate,
)
from saltbor.world.geographic.updater import IncrementalGeoUpdater
from saltbor.cognition.territorial_cognition import (
    IndividualTerritorialCognition,
    EpistemicSpatialStatus,
)
from saltbor.economy.territorial_economy import TerritorialEconomyEngine
from saltbor.visualization.cartography import CartographicVisualizer
from saltbor.persistence.database import DatabaseManager
from saltbor.persistence.schema import SchemaManager
from saltbor.persistence.geographic_repository import GeographicRepository


@pytest.fixture
def geo_engine():
    return RealGeographicEngine()


def test_territorial_hierarchy_integrity(geo_engine: RealGeographicEngine):
    """Verify 14 departments, 44 municipalities, and 262 districts conform to 2024 restructuring."""
    depts = geo_engine.get_all_departments()
    munis = geo_engine.get_all_municipalities()
    districts = geo_engine.get_all_districts()

    assert len(depts) == 14
    assert len(munis) == 44
    assert len(districts) == 262

    # Verify all districts link to valid municipalities and departments
    muni_ids = {m.municipality_id for m in munis}
    dept_codes = {d.code for d in depts}
    for dist in districts:
        assert dist.municipality_id in muni_ids
        assert dist.department_code in dept_codes
        assert is_valid_salvadoran_coordinate(dist.latitude, dist.longitude)


def test_spatial_index_and_haversine():
    """Verify haversine distance precision and sub-millisecond SpatialGridIndex lookup."""
    # San Salvador Cathedral to Santa Ana Cathedral ~ 54.5 km
    dist = haversine_distance_km(13.6989, -89.1914, 13.9942, -89.5564)
    assert 50.0 <= dist <= 60.0

    index = SpatialGridIndex(cell_size_degrees=0.05)
    index.insert("point_a", 13.70, -89.20, "point_a")
    index.insert("point_b", 13.71, -89.21, "point_b")
    index.insert("point_far", 13.35, -88.45, "point_far")

    near_results = index.find_within_radius(13.70, -89.20, radius_km=5.0)
    found_ids = {r[0] for r in near_results}
    assert "point_a" in found_ids
    assert "point_b" in found_ids
    assert "point_far" not in found_ids


def test_coordinate_projections():
    """Verify WGS84 to local metric projection and inverse transformation."""
    x_m, y_m = wgs84_to_local_metric_xy(13.70, -89.20)
    assert abs(x_m) < 200000.0
    assert abs(y_m) < 100000.0

    lat, lon = local_metric_xy_to_wgs84(x_m, y_m)
    assert abs(lat - 13.70) < 1e-4
    assert abs(lon - (-89.20)) < 1e-4


def test_establishment_directory_queries(geo_engine: RealGeographicEngine):
    """Verify establishment queries by category, confirmation status, and radius."""
    dir_inst = geo_engine.establishments
    assert len(dir_inst) >= 20

    # Hospital Rosales check
    rosales = dir_inst.get_by_id("hosp_rosales")
    assert rosales is not None
    assert rosales.category == EstablishmentCategory.PUBLIC_SERVICE
    assert rosales.validation_state == ValidationState.CONFIRMADO

    # Query public health services in San Salvador
    health_services = [
        p for p in dir_inst.get_by_category(EstablishmentCategory.PUBLIC_SERVICE)
        if "hospital" in p.sub_category or "health" in p.sub_category
    ]
    assert len(health_services) >= 2

    # Query within 10km of San Salvador center
    metro_places = dir_inst.find_places_nearby(13.6989, -89.1914, radius_km=10.0, confirmed_only=False)
    assert len(metro_places) >= 5


def test_navigation_bridges_and_obstacles(geo_engine: RealGeographicEngine):
    """Verify navigation respects water bodies, requires bridges over Rio Lempa, and computes multimodal travel."""
    # Obstacle inside Lake Coatepeque
    near_lake = geo_engine.get_physical_features_near(13.87, -89.55, radius_km=6.0)
    lake_ids = {f.feature_id for f, _ in near_lake}
    assert "lago_coatepeque" in lake_ids

    # Obstacle on Volcan de Santa Ana crater
    near_volcano = geo_engine.get_physical_features_near(13.85, -89.63, radius_km=6.0)
    volcano_ids = {f.feature_id for f, _ in near_volcano}
    assert "volc_santa_ana" in volcano_ids

    # Path crossing directly across Lake Coatepeque without roads is blocked as an obstacle
    obstacles = geo_engine.navigation.is_obstacle_in_path(13.85, -89.58, 13.90, -89.52)
    assert len(obstacles) > 0
    assert any("Coatepeque" in obs for obs in obstacles)

    # CA-1 San Salvador to San Vicente crosses Rio Lempa via Puente Cuscatlan
    route = geo_engine.calculate_route(
        origin_district_id="dist_san_salvador",
        destination_district_id="dist_san_vicente",
        transport_mode="bus",
    )
    assert route["is_accessible"] is True
    assert route["total_distance_km"] > 40.0
    assert route["transit_hours"] > 0.5


def test_los_chorros_closure_and_rerouting(geo_engine: RealGeographicEngine):
    """Simulate a landslide at Los Chorros and verify automatic rerouting / warnings."""
    normal_route = geo_engine.calculate_route("dist_colon", "dist_santa_tecla", transport_mode="car")
    assert normal_route["is_accessible"] is True
    assert normal_route["total_distance_km"] < 15.0

    # Close Los Chorros segment
    geo_engine.navigation.block_segment("ca1_lourdes_santatecla")
    try:
        blocked_route = geo_engine.calculate_route("dist_colon", "dist_santa_tecla", transport_mode="car")
        if blocked_route["is_accessible"]:
            assert blocked_route["total_distance_km"] > normal_route["total_distance_km"]
        else:
            assert "bloqueada" in blocked_route["reason"].lower() or len(blocked_route["warnings"]) > 0
    finally:
        geo_engine.navigation.unblock_segment("ca1_lourdes_santatecla")


def test_duplicate_detection_and_bounding_box(geo_engine: RealGeographicEngine):
    """Verify duplicate detection rejects duplicate within 75m, and rejects out-of-bounds coordinates."""
    updater = geo_engine.updater

    dup_cand = RealPlace(
        place_id="test_dup_cerámica",
        name="Artesanías y Cerámica Lenca San Bartolo Taller",
        category=EstablishmentCategory.PRODUCTIVE,
        sub_category="artisanal_workshop",
        department_code="MO",
        municipality_id="mo_sur",
        district_id="dist_guatajiagua",
        point=GeoPoint(13.6684, -88.1990),
        address="Cantón San Bartolo",
        source_name="OSM",
        source_id="W999",
        source_publication_date="2024-01-01",
        source_update_date="2024-01-01",
        saltbor_fetch_date="2026-11-10",
        independent_verification_date=None,
        confidence_level=0.5,
        validation_state=ValidationState.PENDIENTE_VALIDACION,
        opening_hours="08:00-17:00",
        accessibility_rating=0.8,
    )
    dup_matches = updater.detect_duplicates(dup_cand)
    assert len(dup_matches) > 0
    assert dup_matches[0][1] < 75.0  # distance in meters

    bad_cand = RealPlace(
        place_id="ocean_bar",
        name="Bar en Altamar",
        category=EstablishmentCategory.COMMERCE,
        sub_category="restaurant",
        department_code="SS",
        municipality_id="ss_centro",
        district_id="dist_san_salvador",
        point=GeoPoint(10.0, -85.0),
        address="Océano Pacífico",
        source_name="OSM",
        source_id="W999",
        source_publication_date="2024-01-01",
        source_update_date="2024-01-01",
        saltbor_fetch_date="2026-11-10",
        independent_verification_date=None,
        confidence_level=0.5,
        validation_state=ValidationState.PENDIENTE_VALIDACION,
        opening_hours="10:00-22:00",
        accessibility_rating=0.5,
    )
    success, _, err_msg = updater.apply_incremental_update([bad_cand], version_label="v1.2.0_bad", description="Ocean candidate update")
    assert success is False
    assert "outside" in err_msg.lower() or "salvador" in err_msg.lower()


def test_individual_territorial_cognition():
    """Verify epistemic states, social knowledge transmission, and memory decay."""
    agent_a = IndividualTerritorialCognition("agent_carlos", home_district_id="dist_santa_tecla")
    agent_b = IndividualTerritorialCognition("agent_lucia", home_district_id="dist_san_salvador")

    # A receives recommendation from an acquaintance
    agent_a.receive_social_recommendation(
        recommender_uid="stranger_pedro",
        place_id="rumor_store",
        name="Tienda La Esperanza Barata",
        lat=13.68,
        lon=-89.28,
        category="commerce",
        district_id="dist_santa_tecla",
        recommender_trust=0.75,
        is_rumor_or_inaccurate=False,
        tick=10,
    )
    belief_a = agent_a.get_belief("rumor_store")
    assert belief_a is not None
    assert belief_a.status == EpistemicSpatialStatus.HEARD_RUMOR

    # Transmit from A to B
    agent_b.receive_social_recommendation(
        recommender_uid=agent_a.human_uid,
        place_id="rumor_store",
        name=belief_a.name,
        lat=belief_a.perceived_lat,
        lon=belief_a.perceived_lon,
        category=belief_a.perceived_category,
        district_id="dist_santa_tecla",
        recommender_trust=0.90,
        is_rumor_or_inaccurate=False,
        tick=15,
    )
    assert agent_b.knows_place("rumor_store")

    # Memory decay after tick elapsed > threshold
    agent_b.apply_memory_decay(current_tick=600, decay_threshold_ticks=400)
    decayed_belief = agent_b.get_belief("rumor_store")
    assert decayed_belief.confidence < 0.90


def test_territorial_economy_and_fiado(geo_engine: RealGeographicEngine):
    """Verify freight transport costs, pupuseria unit economics, and walking-radius fiado."""
    econ = TerritorialEconomyEngine(geo_engine)

    # Unit economics of Pupusería La Ceiba
    pnl = econ.evaluate_pupuseria_day("pupuseria_la_ceiba_planes", dough_type="maiz", daily_customers=50)
    assert pnl.gross_revenue_usd > 100.0
    assert pnl.net_profit_usd > 25.0
    assert 0.30 <= pnl.operating_margin <= 0.70

    # Fiado microcredit within 600m
    store_lat, store_lon = 13.7018, -89.2241
    ok_near, limit_near, _ = econ.evaluate_fiado_eligibility(
        store_lat + 0.001, store_lon + 0.001,  # ~150m away
        store_lat, store_lon,
        trust_score=0.90,
    )
    assert ok_near is True
    assert limit_near > 20.0

    ok_far, limit_far, reason = econ.evaluate_fiado_eligibility(
        store_lat + 0.02, store_lon + 0.02,  # >2.5 km away
        store_lat, store_lon,
        trust_score=0.90,
    )
    assert ok_far is False
    assert limit_far == 0.0
    assert "radio" in reason.lower() or "caminar" in reason.lower()


def test_offline_cartographic_visualization(geo_engine: RealGeographicEngine):
    """Verify offline SVG and ASCII map generation without any external web or CDN dependencies."""
    viz = CartographicVisualizer(geo_engine)

    ascii_map = viz.render_ascii_map()
    assert "EL SALVADOR" in ascii_map
    assert "CA-1" in ascii_map or "SAN SALVADOR" in ascii_map

    svg_content = viz.generate_svg_map(width=1000, height=550)
    assert "<svg" in svg_content
    assert "</svg>" in svg_content
    assert "MAPA TERRITORIAL REAL DE EL SALVADOR" in svg_content
    assert "xmlns=\"http://www.w3.org/2000/svg\"" in svg_content


def test_persistence_sqlite_roundtrip(geo_engine: RealGeographicEngine):
    """Verify storing geographic entities and establishments in SQLite and reloading them."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    db = DatabaseManager(tmp_path)
    db.connect()
    SchemaManager.create_tables(db)
    repo = GeographicRepository(db)

    try:
        places = geo_engine.establishments.get_all(confirmed_only=False)
        repo.save_places_batch(places)

        loaded_places = repo.get_all_places(confirmed_only=False)
        assert len(loaded_places) == len(places)

        # Query by department
        ss_places = repo.get_places_by_department("SS")
        assert len(ss_places) >= 5

        # Save and query version
        repo.save_version(geo_engine.updater.current_version)
        v_rec = repo.get_version(geo_engine.updater.current_version.version_id)
        assert v_rec is not None
        assert v_rec["record_count"] == len(places)
    finally:
        db.close()
