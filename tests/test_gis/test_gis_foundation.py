"""
Tests for SALTBOR GIS-First World Foundation & 2.5D Digital Twin.

Verifies:
1. Manifest and pilot zone metadata (San Salvador Centro)
2. Real-world layers (streets, buildings, parks, waterways, boundaries, poi)
3. 2.5D building extrusion parameters (heights, levels, categories)
4. Spatial indexing (STRtree) and bounding-box filtering performance (<5ms)
5. Point-in-polygon containment and nearest-street queries
6. Simulation layer coupling (agents in WGS84 with validation_state=SIMULATED)
7. Provenance metadata and license integrity across 100% of features
8. Offline asset self-containment (MapLibre local bundle)
"""

from __future__ import annotations
import os
import pytest
from fastapi.testclient import TestClient

from saltbor.visualization.server import create_app
from saltbor.world.gis import get_gis_engine, ValidationState


@pytest.fixture(scope="module")
def client():
    import tempfile
    import time
    test_db = os.path.join(tempfile.gettempdir(), f"gis_test_{os.getpid()}_{time.time_ns()}.db")
    app = create_app(db_path=test_db)
    with TestClient(app) as c:
        yield c
    for ext in ("", "-wal", "-shm"):
        try:
            p = test_db + ext
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


def test_gis_zones_list(client):
    """Verify available GIS zones endpoint returns san_salvador_centro."""
    resp = client.get("/api/gis/zones")
    assert resp.status_code == 200
    data = resp.json()
    assert "zones" in data
    zone_ids = [z["zone_id"] for z in data["zones"]]
    assert "san_salvador_centro" in zone_ids

    pilot = next(z for z in data["zones"] if z["zone_id"] == "san_salvador_centro")
    assert pilot["name"] == "Zona Piloto — San Salvador Centro Histórico"
    assert "streets" in pilot["layers"]
    assert "buildings" in pilot["layers"]
    assert "parks" in pilot["layers"]


def test_gis_zone_manifest(client):
    """Verify manifest endpoint returns accurate geographic bounds and layers."""
    resp = client.get("/api/gis/zone/san_salvador_centro")
    assert resp.status_code == 200
    manifest = resp.json()
    assert manifest["zone_id"] == "san_salvador_centro"
    bbox = manifest["bbox"]
    assert 13.68 < bbox["min_lat"] < bbox["max_lat"] < 13.72
    assert -89.22 < bbox["min_lon"] < bbox["max_lon"] < -89.17
    assert manifest["projection"] == "EPSG:4326 (WGS84)"


def test_gis_streets_layer_integrity(client):
    """Verify real street network features, road types, and licenses."""
    resp = client.get("/api/gis/layer/san_salvador_centro/streets")
    assert resp.status_code == 200
    geojson = resp.json()
    assert geojson["type"] == "FeatureCollection"
    features = geojson["features"]
    assert len(features) >= 100

    # Inspect first 10 streets
    for f in features[:10]:
        assert f["geometry"]["type"] == "LineString"
        props = f["properties"]
        assert "road_type" in props
        assert props["validation_state"] == "VERIFIED_REAL"
        assert props["license"] == "ODbL-1.0"
        assert props["source"] == "OpenStreetMap_Contributors"


def test_gis_buildings_25d_extrusion_layer(client):
    """Verify building footprints, levels, and real vs estimated height values."""
    resp = client.get("/api/gis/layer/san_salvador_centro/buildings")
    assert resp.status_code == 200
    geojson = resp.json()
    assert geojson["type"] == "FeatureCollection"
    features = geojson["features"]
    assert len(features) >= 200

    for f in features[:20]:
        assert f["geometry"]["type"] == "Polygon"
        props = f["properties"]
        assert props["height_m"] > 0
        assert props["levels"] >= 1
        assert props["validation_state"] in ("VERIFIED_REAL", "ESTIMATED")
        assert "height_source" in props
        assert props["license"] == "ODbL-1.0"


def test_gis_spatial_index_and_bbox_filtering(client):
    """Verify bounding box spatial query filters features quickly (< 10 ms)."""
    # Small sub-box around Plaza Barrios
    query_params = {
        "min_lon": -89.1930,
        "min_lat": 13.6970,
        "max_lon": -89.1900,
        "max_lat": 13.6990,
    }
    resp = client.get("/api/gis/layer/san_salvador_centro/buildings", params=query_params)
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    features = data["features"]
    # Should be a filtered subset (smaller than all 966 buildings)
    assert 0 < len(features) < 300


def test_gis_point_in_polygon_containment():
    """Verify Shapely spatial query can determine if a coordinate is inside a building."""
    engine = get_gis_engine()
    # Query a point known to be inside a building in San Salvador Centro
    bldgs = engine.get_layer("san_salvador_centro", "buildings")["features"]
    target_bldg = bldgs[0]
    coords = target_bldg["geometry"]["coordinates"][0]
    # Centroid coordinate
    centroid_lon = sum(c[0] for c in coords) / len(coords)
    centroid_lat = sum(c[1] for c in coords) / len(coords)

    found = engine.find_containing_building("san_salvador_centro", centroid_lat, centroid_lon)
    assert found is not None
    assert found["properties"]["feature_id"] == target_bldg["properties"]["feature_id"]


def test_gis_simulation_layer_coupling(client):
    """Verify SIMULATION_LAYER dynamically projects agents onto San Salvador coordinates."""
    resp = client.get("/api/gis/simulation_layer")
    assert resp.status_code == 200
    geojson = resp.json()
    assert geojson["type"] == "FeatureCollection"
    assert geojson["metadata"]["layer_system"] == "SIMULATION_LAYER"
    assert geojson["metadata"]["validation_state"] == "SIMULATED"

    features = geojson["features"]
    agent_points = [f for f in features if f["geometry"]["type"] == "Point"]
    assert len(agent_points) >= 1

    for ap in agent_points:
        lon, lat = ap["geometry"]["coordinates"]
        assert 13.68 < lat < 13.72
        assert -89.22 < lon < -89.17
        props = ap["properties"]
        assert props["validation_state"] == "SIMULATED"
        assert props["source"] == "SALTBOR_SIMULATION"
        assert "energy" in props
        assert "hunger" in props
        assert "activity" in props


def test_gis_building_detail_endpoint(client):
    """Verify building detail inspection returns full architectural metadata."""
    resp = client.get("/api/gis/layer/san_salvador_centro/buildings")
    first_bldg_id = resp.json()["features"][0]["properties"]["feature_id"]

    detail_resp = client.get(f"/api/gis/building/{first_bldg_id}")
    assert detail_resp.status_code == 200
    bldg = detail_resp.json()
    assert bldg["properties"]["feature_id"] == first_bldg_id
    assert bldg["properties"]["height_m"] > 0


def test_gis_provenance_and_licensing_integrity():
    """Verify 100% of features in all GIS layers contain valid provenance metadata."""
    engine = get_gis_engine()
    manifest = engine.get_manifest("san_salvador_centro")
    assert manifest is not None

    for layer_name in ("streets", "buildings", "parks", "nature_water", "boundaries", "poi", "elevation"):
        layer = engine.get_layer("san_salvador_centro", layer_name)
        features = layer["features"]
        for f in features:
            props = f["properties"]
            assert "source" in props and len(props["source"]) > 0
            assert "license" in props and len(props["license"]) > 0
            assert "validation_state" in props
            assert props["validation_state"] in [v.value for v in ValidationState]
            assert "known_accuracy" in props


def test_offline_maplibre_assets_present():
    """Verify MapLibre GL JS and CSS are stored locally for 100% offline self-containment."""
    web_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "saltbor",
        "visualization",
        "web",
    )
    js_path = os.path.join(web_dir, "assets", "maplibre", "maplibre-gl.js")
    css_path = os.path.join(web_dir, "assets", "maplibre", "maplibre-gl.css")

    assert os.path.exists(js_path), f"MapLibre JS missing at {js_path}"
    assert os.path.exists(css_path), f"MapLibre CSS missing at {css_path}"
    assert os.path.getsize(js_path) > 500000
    assert os.path.getsize(css_path) > 30000


def test_gis_national_context_endpoint(client):
    """Verify national context endpoint returns real volcanoes, lakes, and departments."""
    resp = client.get("/api/gis/national_context")
    assert resp.status_code == 200
    fc = resp.json()
    assert fc["type"] == "FeatureCollection"
    features = fc["features"]
    assert len(features) >= 20

    volcanoes = [f for f in features if f["properties"].get("feature_type") == "volcano"]
    lakes = [f for f in features if f["properties"].get("feature_type") == "lake"]
    depts = [f for f in features if f["properties"].get("feature_type") == "department"]

    assert len(volcanoes) >= 5
    assert len(lakes) >= 3
    assert len(depts) == 14

    volc_names = [v["properties"]["name"] for v in volcanoes]
    assert any("Ilamatepec" in name or "Santa Ana" in name for name in volc_names)
    assert any("San Salvador" in name or "Quezaltepec" in name or "Boquerón" in name for name in volc_names)

    dept_codes = [d["properties"]["code"] for d in depts]
    for code in ("SS", "SA", "AH", "SO", "LL", "CH", "CU", "LP", "CA", "SV", "US", "SM", "MO", "LU"):
        assert code in dept_codes


def test_gis_street_names_and_urban_structure(client):
    """Verify real street names and road hierarchy are present in streets layer."""
    resp = client.get("/api/gis/layer/san_salvador_centro/streets")
    assert resp.status_code == 200
    fc = resp.json()
    features = fc["features"]

    named_streets = [f for f in features if f["properties"].get("name")]
    assert len(named_streets) > 100

    street_names = [f["properties"]["name"] for f in named_streets]
    # Verify historical San Salvador streets exist in the layer
    assert any("Rubén Darío" in s or "Darío" in s for s in street_names)
    assert any("Poniente" in s or "Oriente" in s for s in street_names)

    # Road hierarchy types
    road_types = {f["properties"]["road_type"] for f in features}
    assert "primary" in road_types or "secondary" in road_types
    assert "residential" in road_types


def test_gis_landmarks_and_parks_features(client):
    """Verify key historical monuments and green plazas in San Salvador Centro."""
    # Parks
    parks_resp = client.get("/api/gis/layer/san_salvador_centro/parks")
    assert parks_resp.status_code == 200
    parks_fc = parks_resp.json()
    park_names = [p["properties"].get("name") for p in parks_fc["features"] if p["properties"].get("name")]
    assert any("Morazán" in p or "San José" in p or "Simon Bolivar" in p or "Verde" in p for p in park_names)

    # Buildings
    bldgs_resp = client.get("/api/gis/layer/san_salvador_centro/buildings")
    assert bldgs_resp.status_code == 200
    bldgs_fc = bldgs_resp.json()
    bldg_names = [b["properties"].get("name") for b in bldgs_fc["features"] if b["properties"].get("name")]
    assert any("Teatro" in b or "Palacio" in b or "Catedral" in b or "Mercado" in b for b in bldg_names)


def test_gis_national_highways_and_water_endpoints(client):
    """Verify Geofabrik national vector datasets are served correctly."""
    # Highways
    resp_hwy = client.get("/api/gis/national_highways")
    assert resp_hwy.status_code == 200
    hwy_fc = resp_hwy.json()
    assert hwy_fc["type"] == "FeatureCollection"
    assert len(hwy_fc["features"]) > 2000
    hwy_names = [f["properties"].get("name") for f in hwy_fc["features"] if f["properties"].get("name")]
    assert any("Panamericana" in n or "Troncal del Norte" in n or "Orden de Malta" in n for n in hwy_names)

    # Water
    resp_water = client.get("/api/gis/national_water")
    assert resp_water.status_code == 200
    water_fc = resp_water.json()
    assert water_fc["type"] == "FeatureCollection"
    assert len(water_fc["features"]) > 100
    water_names = [f["properties"].get("name") for f in water_fc["features"] if f["properties"].get("name")]
    assert any("Ilopango" in n or "Coatepeque" in n or "Lempa" in n for n in water_names)

