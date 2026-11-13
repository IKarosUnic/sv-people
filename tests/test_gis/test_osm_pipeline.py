"""Tests for the offline OpenStreetMap ingestion pipeline and router.

The pipeline is exercised end-to-end on a tiny ESRI shapefile bundle written by
this test, so the test does not depend on the 399 MB vendored extract.  A
separate test inspects the real extract when it is present.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

from saltbor.datasets.gis import pipeline
from saltbor.datasets.gis.geofabrik_extractor import DOWNLOADS_DIR
from saltbor.datasets.gis.shapefile_reader import ShapefileError, ShapefileReader
from saltbor.world.geographic.osm_router import OSMRoadNetwork, haversine_m


# ---------------------------------------------------------------------------
# Minimal ESRI Shapefile writer (test fixture only)
# ---------------------------------------------------------------------------

def _write_shapefile(base: Path, shape_type: int, geometries: list[list[tuple[float, float]]], records: list[dict]) -> None:
    """Write a minimal ``.shp``/``.dbf`` pair for the reader to consume."""
    records_payload = b""
    record_number = 1
    for coords in geometries:
        if shape_type == 1:  # Point
            (x, y), = coords
            content = struct.pack("<i2d", shape_type, x, y)
        elif shape_type == 3:  # PolyLine
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            content = struct.pack("<i4d2i", shape_type, min(xs), min(ys), max(xs), max(ys), 1, len(coords))
            content += struct.pack("<i", 0)
            for x, y in coords:
                content += struct.pack("<2d", x, y)
        elif shape_type == 5:  # Polygon
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            ring = list(coords)
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            content = struct.pack("<i4d2i", shape_type, min(xs), min(ys), max(xs), max(ys), 1, len(ring))
            content += struct.pack("<i", 0)
            for x, y in ring:
                content += struct.pack("<2d", x, y)
        else:  # pragma: no cover - guard
            raise ValueError(shape_type)
        records_payload += struct.pack(">2i", record_number, len(content) // 2) + content
        record_number += 1

    xs = [c[0] for g in geometries for c in g]
    ys = [c[1] for g in geometries for c in g]
    bbox = (min(xs), min(ys), max(xs), max(ys)) if xs else (0.0, 0.0, 0.0, 0.0)
    header = struct.pack(">i", 9994) + b"\x00" * 20 + struct.pack(">i", (100 + len(records_payload)) // 2)
    header += struct.pack("<ii", 1000, shape_type) + struct.pack("<4d", *bbox) + struct.pack("<4d", 0.0, 0.0, 0.0, 0.0)
    base.with_suffix(".shp").write_bytes(header + records_payload)
    base.with_suffix(".prj").write_text(
        'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]',
        encoding="utf-8",
    )
    base.with_suffix(".cpg").write_text("UTF-8", encoding="utf-8")

    # DBF
    fields = list(records[0].keys())
    field_specs = []
    for name in fields:
        sample = records[0][name]
        if isinstance(sample, (int, float)):
            field_specs.append((name, "N", 12, 3 if isinstance(sample, float) else 0))
        else:
            field_specs.append((name, "C", 40, 0))

    header_len = 32 + 32 * len(field_specs) + 1
    record_len = 1 + sum(spec[2] for spec in field_specs)
    dbf = bytearray()
    dbf += struct.pack("<4B", 0x03, 126, 1, 1)
    dbf += struct.pack("<i", len(records)) + struct.pack("<hh", header_len, record_len)
    dbf += b"\x00" * 20
    for name, ftype, length, decimals in field_specs:
        dbf += name.encode("ascii")[:11].ljust(11, b"\x00")
        dbf += ftype.encode("ascii") + b"\x00" * 4 + bytes([length, decimals]) + b"\x00" * 14
    dbf += b"\x0d"
    for record in records:
        dbf += b" "
        for name, ftype, length, decimals in field_specs:
            value = record[name]
            if ftype == "N":
                text = f"{value:.{decimals}f}" if decimals else str(int(value))
            else:
                text = str(value)
            dbf += text.encode("utf-8")[:length].ljust(length)
    dbf += b"\x1a"
    base.with_suffix(".dbf").write_bytes(bytes(dbf))


@pytest.fixture()
def mini_bundle(tmp_path: Path) -> Path:
    """A three-layer bundle with the same stems the pipeline expects."""
    downloads = tmp_path / "el_salvador_shp"
    downloads.mkdir()

    _write_shapefile(
        downloads / "gis_osm_roads_free_1",
        3,
        [
            [(-89.2000, 13.7000), (-89.1990, 13.7000)],
            [(-89.1990, 13.7000), (-89.1990, 13.7010)],
            [(-89.2000, 13.7010), (-89.1990, 13.7010)],
        ],
        [
            {"osm_id": "1001", "code": 5111, "fclass": "residential", "name": "Calle Uno", "ref": "", "oneway": "F", "maxspeed": 30, "layer": 0, "bridge": "F", "tunnel": "F"},
            {"osm_id": "1002", "code": 5113, "fclass": "primary", "name": "Avenida Dos", "ref": "CA-1", "oneway": "B", "maxspeed": 60, "layer": 0, "bridge": "F", "tunnel": "F"},
            {"osm_id": "1003", "code": 5121, "fclass": "footway", "name": "", "ref": "", "oneway": "F", "maxspeed": 0, "layer": 0, "bridge": "F", "tunnel": "F"},
        ],
    )
    _write_shapefile(
        downloads / "gis_osm_buildings_a_free_1",
        5,
        [[(-89.1995, 13.7002), (-89.1992, 13.7002), (-89.1992, 13.7005), (-89.1995, 13.7005), (-89.1995, 13.7002)]],
        [{"osm_id": "2001", "code": 2011, "fclass": "residential", "name": "Casa Muestra", "type": "residential"}],
    )
    _write_shapefile(
        downloads / "gis_osm_places_free_1",
        1,
        [[(-89.1995, 13.7005)]],
        [{"osm_id": "3001", "code": 1001, "fclass": "city", "population": 1200, "name": "Villa Ejemplo"}],
    )
    return downloads


# ---------------------------------------------------------------------------
# Shapefile reader
# ---------------------------------------------------------------------------

def test_shapefile_reader_parses_geometry_and_attributes(mini_bundle: Path):
    reader = ShapefileReader(mini_bundle / "gis_osm_roads_free_1")
    assert reader.record_count == 3
    assert "fclass" in reader.field_names
    assert reader.crs == "EPSG:4326"

    records = list(reader.iter_records())
    assert len(records) == 3
    attrs, shape = records[0]
    assert attrs["name"] == "Calle Uno"
    assert attrs["maxspeed"] == 30
    geometry = shape.__geo_interface__
    assert geometry["type"] == "LineString"
    assert len(geometry["coordinates"]) == 2


def test_shapefile_reader_rejects_non_shapefile(tmp_path: Path):
    bogus = tmp_path / "bogus.shp"
    bogus.write_bytes(b"not a shapefile at all")
    with pytest.raises(ShapefileError):
        ShapefileReader(bogus)


def test_polygons_close_and_report_polygon_geometry(mini_bundle: Path):
    reader = ShapefileReader(mini_bundle / "gis_osm_buildings_a_free_1")
    attrs, shape = next(iter(reader.iter_records()))
    geometry = shape.__geo_interface__
    assert geometry["type"] in ("Polygon", "MultiPolygon")
    ring = geometry["coordinates"][0] if geometry["type"] == "Polygon" else geometry["coordinates"][0][0]
    assert ring[0] == ring[-1]
    assert attrs["name"] == "Casa Muestra"


# ---------------------------------------------------------------------------
# Ingestion pipeline
# ---------------------------------------------------------------------------

def test_pipeline_normalizes_classes_and_records_provenance(mini_bundle: Path, tmp_path: Path):
    output = tmp_path / "ingested" / "geography.sqlite"
    report = pipeline.ingest(
        downloads_dir=mini_bundle,
        output_path=output,
        layers=["roads", "buildings", "places"],
        acquired_at="2026-11-13",
    )

    assert report.feature_count == 5
    assert report.layers["roads"]["feature_count"] == 3
    assert report.layers["roads"]["class_counts"]["residential"] == 1
    assert report.layers["roads"]["class_counts"]["primary"] == 1
    assert report.layers["roads"]["class_counts"]["footway"] == 1
    assert report.layers["buildings"]["class_counts"]["residential"] == 1
    assert report.layers["places"]["class_counts"]["city"] == 1

    geography = pipeline.IngestedGeography(output)
    manifest = geography.manifest()
    assert manifest["available"] is True
    assert "OpenStreetMap" in manifest["attribution"]
    dataset = manifest["dataset"]
    assert dataset["license"] == "ODbL-1.0"
    assert dataset["crs"] == "EPSG:4326 (WGS84)"
    assert dataset["source_url"].startswith("https://download.geofabrik.de")

    roads = geography.features_in_bbox((-89.201, 13.699, -89.198, 13.702), layer="roads")
    assert len(roads) == 3
    assert all(r["license"] == "ODbL-1.0" for r in roads)
    assert any(r["name"] == "Calle Uno" for r in roads)

    # Unnamed OSM geometry is imported but explicitly unverified.
    unnamed = [r for r in roads if not r["name"]]
    assert unnamed and unnamed[0]["validation_state"] == "IMPORTED_UNVERIFIED"
    assert geography.nearest_road(13.7000, -89.1999) is not None
    geography.close()


def test_pipeline_marks_partial_coverage(mini_bundle: Path, tmp_path: Path):
    output = tmp_path / "ingested" / "geography.sqlite"
    report = pipeline.ingest(
        downloads_dir=mini_bundle,
        output_path=output,
        layers=["roads"],
        bbox=(-89.2000, 13.6999, -89.1995, 13.7001),
        acquired_at="2026-11-13",
    )
    assert report.layers["roads"]["is_partial"] is True
    assert report.layers["roads"]["coverage_bbox"] is not None
    assert "PARTIAL" in report.layers["roads"]["limitations"]

    geography = pipeline.IngestedGeography(output)
    manifest = geography.manifest()
    assert manifest["layers"]["roads"]["is_partial"] is True
    geography.close()


def test_pipeline_without_source_does_not_crash(tmp_path: Path):
    report = pipeline.ingest(
        downloads_dir=tmp_path / "missing",
        output_path=tmp_path / "ingested" / "geography.sqlite",
        layers=["roads", "places"],
        acquired_at="2026-11-13",
    )
    assert report.feature_count == 0
    assert report.layers["roads"]["feature_count"] == 0
    manifest = pipeline.IngestedGeography(report.output_path).manifest()
    assert manifest["available"] is True


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _grid_network() -> OSMRoadNetwork:
    network = OSMRoadNetwork()
    base_lat, base_lon, step = 13.6970, -89.1930, 0.001
    for i in range(4):
        network.add_geometry(
            [(base_lon + j * step, base_lat + i * step) for j in range(4)],
            road_class="residential",
        )
    for j in range(4):
        network.add_geometry(
            [(base_lon + j * step, base_lat + i * step) for i in range(4)],
            road_class="residential",
        )
    network.add_geometry(
        [(base_lon + 0.05, base_lat + 0.05), (base_lon + 0.051, base_lat + 0.05)],
        road_class="path",
    )
    return network


def test_router_follows_network_and_does_not_teleport():
    network = _grid_network()
    start = (13.6970, -89.1930)
    end = (13.6990, -89.1910)
    route = network.route(start, end, mode="walk")

    assert route.found
    straight = haversine_m(start[0], start[1], end[0], end[1])
    assert route.distance_m >= straight * 0.99
    assert route.edges_traversed >= 2
    assert len(route.path) >= 3
    assert route.duration_minutes > 0


def test_router_walk_is_slower_than_drive():
    network = _grid_network()
    walk = network.route((13.6970, -89.1930), (13.6990, -89.1910), mode="walk")
    drive = network.route((13.6970, -89.1930), (13.6990, -89.1910), mode="drive")
    assert walk.found and drive.found
    assert walk.duration_minutes > drive.duration_minutes


def test_router_reports_unreachable_destination():
    network = _grid_network()
    isolated = (13.7470, -89.1430)
    route = network.route((13.6970, -89.1930), isolated, mode="walk", max_snap_m=400.0)
    assert route.found is False
    assert route.reason in ("no_connected_path", "snap_distance_exceeded")
    assert route.is_approximate is True or route.reason == "no_connected_path"


def test_router_empty_network_reports_reason():
    route = OSMRoadNetwork().route((13.69, -89.19), (13.70, -89.18))
    assert route.found is False
    assert route.reason == "network_empty"


# ---------------------------------------------------------------------------
# Real vendored extract (optional)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not (DOWNLOADS_DIR / "gis_osm_roads_free_1.shp").exists(),
    reason="Geofabrik extract not present (run the pipeline with --download)",
)
def test_real_extract_is_readable():
    reader = ShapefileReader(DOWNLOADS_DIR / "gis_osm_roads_free_1")
    assert reader.record_count > 100_000
    attrs, shape = next(iter(reader.iter_records(limit=1)))
    assert "fclass" in attrs
    assert shape.__geo_interface__["type"] in ("LineString", "MultiLineString")
    assert reader.crs == "EPSG:4326"
