"""Geofabrik OpenStreetMap extractor for SALTBOR's national context layers.

Reads the vendored Geofabrik El Salvador shapefile bundle (ODbL 1.0) and
extracts the national-scale cartographic layers used by the world map and the
territorial engine:

* national primary / trunk / motorway network (CA-1 Panamericana, CA-2 Litoral,
  CA-4 Troncal, Carretera de Oro, ...)
* named national water bodies (lakes, reservoirs, lagoons)
* cities and towns across the 14 departments

The shapefile access goes through :mod:`saltbor.datasets.gis.shapefile_reader`,
a dependency-free reader, because SALTBOR must ingest its geographic foundation
on an offline machine with no GDAL/Fiona/pyshp installation.

For the full normalized semantic ingestion (roads, buildings, landuse, water,
places, transport, POIs, boundaries with row-level provenance) use
:mod:`saltbor.datasets.gis.pipeline` instead; this module only produces the
compact national context layers.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from saltbor.datasets.gis.shapefile_reader import ShapefileReader

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR = BASE_DIR / "downloads" / "el_salvador_shp"
OUTPUT_DIR = BASE_DIR / "national"

SOURCE = "Geofabrik_OSM_El_Salvador"
SOURCE_URL = "https://download.geofabrik.de/central-america/el-salvador.html"
LICENSE = "ODbL-1.0"


def _write(fc: Dict[str, Any], name: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"{name}.geojson"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    logger.info("Wrote %d features to %s", len(fc["features"]), out_file)
    return out_file


def _feature_collection(name: str, features: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "name": f"saltbor_{name}",
        "metadata": {
            "source": SOURCE,
            "source_url": SOURCE_URL,
            "license": LICENSE,
            "attribution": "© OpenStreetMap contributors",
            "crs": "EPSG:4326 (WGS84)",
            "coverage": "El Salvador (National)",
            "features_count": len(features),
        },
        "features": features,
    }


def _empty(name: str) -> Dict[str, Any]:
    logger.warning("Shapefile layer unavailable for '%s'", name)
    return _feature_collection(name, [])


def extract_national_highways(
    min_classes: tuple[str, ...] = ("motorway", "trunk", "primary")
) -> Dict[str, Any]:
    """Extract the national highway network with real geometries."""
    shp_path = DOWNLOADS_DIR / "gis_osm_roads_free_1"
    if not shp_path.with_suffix(".shp").exists():
        return _empty("national_highways")

    reader = ShapefileReader(shp_path)
    features: List[Dict[str, Any]] = []
    for rec, shape in reader.iter_records(predicate=lambda a: a.get("fclass") in min_classes):
        name = rec.get("name") or rec.get("ref") or "Carretera Nacional"
        features.append(
            {
                "type": "Feature",
                "id": f"hwy_{rec['osm_id']}",
                "geometry": shape.__geo_interface__,
                "properties": {
                    "osm_id": rec["osm_id"],
                    "name": name,
                    "road_type": rec["fclass"],
                    "ref": rec.get("ref") or "",
                    "maxspeed": rec.get("maxspeed"),
                    "oneway": rec.get("oneway") in ("F", "B"),
                    "bridge": rec.get("bridge") == "T",
                    "validation_state": "VERIFIED_REAL",
                    "source": SOURCE,
                    "source_url": SOURCE_URL,
                    "license": LICENSE,
                    "known_accuracy": "metric",
                },
            }
        )
    fc = _feature_collection("national_highways", features)
    _write(fc, "highways")
    return fc


def extract_national_water() -> Dict[str, Any]:
    """Extract named lakes, reservoirs and water bodies."""
    shp_path = DOWNLOADS_DIR / "gis_osm_water_a_free_1"
    if not shp_path.with_suffix(".shp").exists():
        return _empty("national_water_bodies")

    reader = ShapefileReader(shp_path)
    features: List[Dict[str, Any]] = []
    for rec, shape in reader.iter_records(
        predicate=lambda a: bool((a.get("name") or "").strip())
    ):
        features.append(
            {
                "type": "Feature",
                "id": f"water_{rec['osm_id']}",
                "geometry": shape.__geo_interface__,
                "properties": {
                    "osm_id": rec["osm_id"],
                    "name": (rec.get("name") or "").strip(),
                    "water_type": rec.get("fclass"),
                    "validation_state": "VERIFIED_REAL",
                    "source": SOURCE,
                    "source_url": SOURCE_URL,
                    "license": LICENSE,
                    "known_accuracy": "metric",
                },
            }
        )
    fc = _feature_collection("national_water_bodies", features)
    _write(fc, "water")
    return fc


def extract_national_places() -> Dict[str, Any]:
    """Extract cities, towns and departmental cabeceras."""
    shp_path = DOWNLOADS_DIR / "gis_osm_places_free_1"
    if not shp_path.with_suffix(".shp").exists():
        return _empty("national_places")

    reader = ShapefileReader(shp_path)
    features: List[Dict[str, Any]] = []
    for rec, shape in reader.iter_records(
        predicate=lambda a: a.get("fclass") in ("city", "town") and bool(a.get("name"))
    ):
        features.append(
            {
                "type": "Feature",
                "id": f"place_{rec['osm_id']}",
                "geometry": shape.__geo_interface__,
                "properties": {
                    "osm_id": rec["osm_id"],
                    "name": (rec.get("name") or "").strip(),
                    "place_type": rec.get("fclass"),
                    "population": rec.get("population"),
                    "validation_state": "VERIFIED_REAL",
                    "source": SOURCE,
                    "source_url": SOURCE_URL,
                    "license": LICENSE,
                    "known_accuracy": "metric",
                },
            }
        )
    fc = _feature_collection("national_places", features)
    _write(fc, "places")
    return fc


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Extracting national GIS geometries from the Geofabrik shapefiles...")
    h = extract_national_highways()
    print(f"-> {len(h['features'])} national highways (CA-1, CA-2, CA-4, CA-8, Carretera de Oro)")
    w = extract_national_water()
    print(f"-> {len(w['features'])} national water bodies (lakes, lagoons, reservoirs)")
    p = extract_national_places()
    print(f"-> {len(p['features'])} cities and towns across 14 departments")
    print("Done.")
