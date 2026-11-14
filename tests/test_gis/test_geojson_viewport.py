"""Viewport GeoJSON used by the world map.

These tests exercise the real ingestion pipeline output and the API contract
that the frontend depends on: a standard FeatureCollection, per-feature
provenance, exact bbox filtering and attribution.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from saltbor.datasets.gis import pipeline
from saltbor.visualization.server import create_app
from tests.test_gis.shapefile_helper import write_shapefile

COORDS = (-89.2020, 13.6930, -89.1860, 13.7040)


@pytest.fixture(scope="module")
def geography_db(tmp_path_factory) -> Path:
    """Ingest a tiny bundle shaped like the Geofabrik layers."""
    downloads = tmp_path_factory.mktemp("shp")
    # Two roads inside the viewport, one far outside, one building inside.
    roads = [
        [(-89.1999, 13.7000), (-89.1990, 13.7000)],  # inside
        [(-89.1995, 13.7005), (-89.1995, 13.7010)],  # inside
        [(-88.5000, 13.2000), (-88.4990, 13.2000)],  # outside
    ]
    _write_lines(downloads / "gis_osm_roads_free_1", roads, ["Calle A", "Calle B", "Lejana"])
    _write_polygon(
        downloads / "gis_osm_buildings_a_free_1",
        [(-89.1996, 13.7001), (-89.1992, 13.7001), (-89.1992, 13.7004), (-89.1996, 13.7004)],
        "Casa Vista",
    )
    output = tmp_path_factory.mktemp("db") / "geography.sqlite"
    pipeline.ingest(
        downloads_dir=downloads,
        output_path=output,
        layers=["roads", "buildings"],
        acquired_at="2026-11-13",
    )
    return output


def _write_lines(base: Path, lines, names) -> None:
    write_shapefile(
        base,
        3,
        lines,
        [
            {
                "osm_id": str(5000 + i),
                "code": 5111,
                "fclass": "residential",
                "name": name,
                "ref": "",
                "oneway": "F",
                "maxspeed": 30,
                "layer": 0,
                "bridge": "F",
                "tunnel": "F",
            }
            for i, name in enumerate(names)
        ],
    )


def _write_polygon(base: Path, ring, name: str) -> None:
    write_shapefile(
        base,
        5,
        [ring],
        [{"osm_id": "6001", "code": 2011, "fclass": "residential", "name": name, "type": "residential"}],
    )


def test_geojson_returns_only_features_inside_viewport(geography_db: Path):
    geography = pipeline.IngestedGeography(geography_db)
    collection = geography.geojson(COORDS)

    assert collection["type"] == "FeatureCollection"
    assert collection["properties"]["license"] == "ODbL-1.0"
    assert collection["properties"]["source"] == "OpenStreetMap contributors"
    names = {f["properties"]["name"] for f in collection["features"]}
    assert names == {"Calle A", "Calle B", "Casa Vista"}
    assert "Lejana" not in names

    layers = {f["properties"]["layer"] for f in collection["features"]}
    assert layers == {"roads", "buildings"}
    for feature in collection["features"]:
        assert feature["geometry"]["type"] in ("LineString", "Polygon")
        assert feature["properties"]["validation_state"]
        assert feature["properties"]["license"] == "ODbL-1.0"
    geography.close()


def test_geojson_layer_filter_and_truncation(geography_db: Path):
    geography = pipeline.IngestedGeography(geography_db)
    roads = geography.geojson(COORDS, layers=("roads",))
    assert {f["properties"]["layer"] for f in roads["features"]} == {"roads"}

    limited = geography.geojson(COORDS, limit=1)
    assert len(limited["features"]) == 1
    assert limited["properties"]["truncated"] is True
    geography.close()


def test_geojson_without_database_is_empty_but_attributed(tmp_path: Path):
    geography = pipeline.IngestedGeography(tmp_path / "missing.sqlite")
    collection = geography.geojson(COORDS)
    assert collection["features"] == []
    assert collection["properties"]["available"] is False
    assert "OpenStreetMap" in collection["properties"]["attribution"]


def test_api_geojson_contract(geography_db: Path, monkeypatch):
    import saltbor.visualization.api as api_module

    monkeypatch.setattr(api_module, "_geography_instance", pipeline.IngestedGeography(geography_db))
    app = create_app(seed=3, db_path=str(geography_db.parent / "api.db"))
    with TestClient(app) as client:
        response = client.get(
            "/api/geography/geojson",
            params={
                "min_lon": COORDS[0],
                "min_lat": COORDS[1],
                "max_lon": COORDS[2],
                "max_lat": COORDS[3],
                "layers": "roads,buildings",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["type"] == "FeatureCollection"
        assert payload["properties"]["attribution"].startswith("© OpenStreetMap")
        assert len(payload["features"]) == 3
        assert json.dumps(payload["features"][0]["geometry"])  # serializable geometry

        bad = client.get(
            "/api/geography/geojson",
            params={
                "min_lon": COORDS[0],
                "min_lat": COORDS[1],
                "max_lon": COORDS[2],
                "max_lat": COORDS[3],
                "layers": "roads,secrets",
            },
        )
        assert bad.status_code == 400
        assert "secrets" in bad.json()["detail"]


@pytest.mark.skipif(
    not pipeline.DEFAULT_OUTPUT.exists(),
    reason="geography not ingested",
)
def test_real_viewport_has_osm_roads():
    geography = pipeline.IngestedGeography(pipeline.DEFAULT_OUTPUT)
    collection = geography.geojson(COORDS, layers=("roads",), limit=500)
    assert collection["features"], "the pilot viewport must contain real roads"
    assert all(f["properties"]["layer"] == "roads" for f in collection["features"])
    assert all(f["properties"]["source"] for f in collection["features"])
    assert all(f["properties"]["license"] == "ODbL-1.0" for f in collection["features"])
    geography.close()
