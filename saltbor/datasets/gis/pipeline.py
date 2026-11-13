"""OpenStreetMap ingestion and normalization pipeline for SALTBOR.

This is the *actual* offline ingestion path.  It reads the Geofabrik El
Salvador shapefile bundle already vendored under
``saltbor/datasets/gis/downloads/``, normalizes every layer into a single
semantic model, and writes a provenance-carrying SQLite geography database
that the simulation can query at runtime without touching the network.

Design constraints (Phase 1.6 §3):

* **Offline first.**  No Overpass call is required to ingest or to run.
  Overpass remains available for controlled refresh via ``osm_connector``.
* **Provenance is not optional.**  Every feature row carries source, source
  URL, acquisition date, license, CRS, resolution, validation state and known
  limitations.  Derived datasets are ODbL 1.0 and must keep attribution.
* **No invented geometry.**  Only geometries present in the extract are
  written.  Where a semantic class is approximated (for example a building
  count in a district) the validation state says so.
* **Extensible beyond El Salvador.**  ``LAYER_SPECS`` is keyed by Geofabrik
  layer name, not by country, so any Geofabrik extract can be ingested.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Optional

from saltbor.datasets.gis.shapefile_reader import Shape, ShapefileReader

logger = logging.getLogger(__name__)

OSM_ATTRIBUTION = (
    "© OpenStreetMap contributors, ODbL 1.0 "
    "(https://www.openstreetmap.org/copyright)"
)
GEOFABRIK_URL = "https://download.geofabrik.de/central-america/el-salvador.html"
GEOFABRIK_SHAPEFILE_ZIP = (
    "https://download.geofabrik.de/central-america/el-salvador-latest-free.shp.zip"
)
ODBL_URL = "https://opendatacommons.org/licenses/odbl/1-0/"

DEFAULT_DOWNLOADS = Path(__file__).parent / "downloads" / "el_salvador_shp"
DEFAULT_OUTPUT = Path(__file__).parent / "ingested" / "geography.sqlite"


# ---------------------------------------------------------------------------
# Source acquisition
# ---------------------------------------------------------------------------

def download_source(
    downloads_dir: Optional[str | Path] = None,
    url: str = GEOFABRIK_SHAPEFILE_ZIP,
) -> Path:
    """Download and unpack the Geofabrik shapefile bundle (one-time, online).

    SALTBOR itself never needs the network: this is an explicit, user-invoked
    acquisition step.  The extract is ODbL 1.0 and the attribution must be kept
    whenever derived data is redistributed.
    """
    import io
    import zipfile

    import httpx

    downloads = Path(downloads_dir) if downloads_dir else DEFAULT_DOWNLOADS
    target = downloads / "el_salvador_shp"
    if target.exists() and any(target.glob("*.shp")):
        logger.info("Geofabrik extract already present at %s", target)
        return target

    downloads.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading %s (ODbL 1.0) ...", url)
    with httpx.stream("GET", url, timeout=120.0, follow_redirects=True) as response:
        response.raise_for_status()
        payload = b"".join(response.iter_bytes())
    logger.info("Downloaded %.1f MB", len(payload) / 1_048_576)

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        target.mkdir(parents=True, exist_ok=True)
        for member in archive.namelist():
            if member.endswith("/"):
                continue
            archive.extract(member, downloads)
    extracted = downloads / "el_salvador_shp"
    logger.info("Extracted to %s", extracted)
    return extracted


# ---------------------------------------------------------------------------
# Layer specifications
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LayerSpec:
    """Declarative definition of one Geofabrik shapefile layer."""

    layer: str
    stem: str
    geometry_kind: str  # point | line | polygon
    class_field: str
    class_map: dict[str, str] = field(default_factory=dict)
    default_class: str = "other"
    name_field: str = "name"
    limitations: str = ""

    def classify(self, attrs: dict[str, Any]) -> str:
        raw = attrs.get(self.class_field)
        if raw is None:
            return self.default_class
        key = str(raw).strip().lower()
        return self.class_map.get(key, self.default_class)


_ROAD_CLASSES = {
    "motorway": "motorway",
    "motorway_link": "motorway",
    "trunk": "trunk",
    "trunk_link": "trunk",
    "primary": "primary",
    "primary_link": "primary",
    "secondary": "secondary",
    "secondary_link": "secondary",
    "tertiary": "tertiary",
    "tertiary_link": "tertiary",
    "residential": "residential",
    "unclassified": "residential",
    "living_street": "residential",
    "pedestrian": "pedestrian",
    "service": "service",
    "track": "track",
    "path": "path",
    "footway": "footway",
    "steps": "steps",
    "cycleway": "cycleway",
    "bridleway": "path",
}

_BUILDING_CLASSES = {
    "residential": "residential",
    "house": "residential",
    "apartments": "residential",
    "detached": "residential",
    "garage": "residential",
    "garages": "residential",
    "hut": "residential",
    "shed": "residential",
    "commercial": "commercial",
    "retail": "commercial",
    "supermarket": "commercial",
    "kiosk": "commercial",
    "office": "commercial",
    "industrial": "industrial",
    "warehouse": "industrial",
    "manufacture": "industrial",
    "school": "institutional",
    "university": "institutional",
    "college": "institutional",
    "hospital": "institutional",
    "clinic": "institutional",
    "government": "institutional",
    "public": "institutional",
    "civic": "institutional",
    "church": "religious",
    "cathedral": "religious",
    "chapel": "religious",
    "mosque": "religious",
    "temple": "religious",
    "yes": "residential",
}

_LANDUSE_CLASSES = {
    "residential": "residential_area",
    "commercial": "commercial_area",
    "retail": "commercial_area",
    "industrial": "industrial_area",
    "farmland": "agricultural_area",
    "farm": "agricultural_area",
    "orchard": "agricultural_area",
    "vineyard": "agricultural_area",
    "plant_nursery": "agricultural_area",
    "forest": "forest",
    "meadow": "vegetation",
    "grass": "vegetation",
    "scrub": "vegetation",
    "park": "recreation_area",
    "recreation_ground": "recreation_area",
    "cemetery": "institutional_area",
    "quarry": "extraction_area",
    "landfill": "waste_area",
}

_NATURAL_CLASSES = {
    "water": "water_body",
    "wetland": "wetland",
    "wood": "forest",
    "scrub": "vegetation",
    "grassland": "vegetation",
    "beach": "coastline",
    "coastline": "coastline",
    "cliff": "terrain",
    "peak": "terrain",
    "volcano": "terrain",
    "ridge": "terrain",
    "valley": "terrain",
    "spring": "water_source",
    "hot_spring": "water_source",
}

_WATER_CLASSES = {
    "river": "river",
    "stream": "stream",
    "canal": "canal",
    "drain": "drain",
    "ditch": "drain",
    "water": "water_body",
    "reservoir": "reservoir",
    "lake": "lake",
    "pond": "pond",
    "dam": "dam",
    "weir": "dam",
    "waterfall": "waterfall",
}

_PLACES_CLASSES = {
    "national_capital": "national_capital",
    "city": "city",
    "town": "town",
    "village": "village",
    "hamlet": "hamlet",
    "suburb": "suburb",
    "neighbourhood": "neighbourhood",
    "quarter": "neighbourhood",
    "locality": "locality",
    "isolated_dwelling": "dwelling",
    "farm": "farm",
    "island": "island",
}

_TRANSPORT_CLASSES = {
    "bus_stop": "bus_stop",
    "bus_station": "bus_station",
    "railway_station": "railway_station",
    "halt": "railway_station",
    "station": "railway_station",
    "aerodrome": "airport",
    "airport": "airport",
    "ferry_terminal": "ferry_terminal",
    "taxi": "taxi_rank",
    "parking": "parking",
}

_AMENITY_CLASSES = {
    "school": "education",
    "kindergarten": "education",
    "college": "education",
    "university": "education",
    "library": "education",
    "hospital": "health",
    "clinic": "health",
    "doctors": "health",
    "dentist": "health",
    "pharmacy": "health",
    "police": "public_safety",
    "fire_station": "public_safety",
    "townhall": "government",
    "courthouse": "government",
    "post_office": "public_service",
    "bank": "finance",
    "atm": "finance",
    "marketplace": "market",
    "place_of_worship": "religious",
    "restaurant": "food_service",
    "fast_food": "food_service",
    "cafe": "food_service",
    "bar": "food_service",
    "fuel": "fuel",
    "bus_station": "transport",
}

LAYER_SPECS: tuple[LayerSpec, ...] = (
    LayerSpec(
        layer="roads",
        stem="gis_osm_roads_free_1",
        geometry_kind="line",
        class_field="fclass",
        class_map=_ROAD_CLASSES,
        limitations=(
            "Connectivity is geometric only. Saltbor infers junction sharing from "
            "identical coordinates; OSM turn restrictions are not present in the "
            "shapefile and are not modelled."
        ),
    ),
    LayerSpec(
        layer="buildings",
        stem="gis_osm_buildings_a_free_1",
        geometry_kind="polygon",
        class_field="type",
        class_map=_BUILDING_CLASSES,
        limitations=(
            "Building footprints are real OSM footprints. Storey count, occupancy "
            "and use are NOT implied by the polygon and are simulated separately."
        ),
    ),
    LayerSpec(
        layer="landuse",
        stem="gis_osm_landuse_a_free_1",
        geometry_kind="polygon",
        class_field="fclass",
        class_map=_LANDUSE_CLASSES,
        limitations="Land use polygons are coarse and not cadastral parcels.",
    ),
    LayerSpec(
        layer="natural",
        stem="gis_osm_natural_a_free_1",
        geometry_kind="polygon",
        class_field="fclass",
        class_map=_NATURAL_CLASSES,
        limitations="Polygon natural features only; linear coastlines live in the lines layer.",
    ),
    LayerSpec(
        layer="water",
        stem="gis_osm_water_a_free_1",
        geometry_kind="polygon",
        class_field="fclass",
        class_map=_WATER_CLASSES,
        limitations="Water bodies only; waterways are lines in the waterways layer.",
    ),
    LayerSpec(
        layer="waterways",
        stem="gis_osm_waterways_free_1",
        geometry_kind="line",
        class_field="fclass",
        class_map=_WATER_CLASSES,
        limitations="Flow direction and discharge volumes are not provided by OSM.",
    ),
    LayerSpec(
        layer="places",
        stem="gis_osm_places_free_1",
        geometry_kind="point",
        class_field="fclass",
        class_map=_PLACES_CLASSES,
        limitations="OSM place nodes approximate settlement centres, not administrative seats.",
    ),
    LayerSpec(
        layer="transport",
        stem="gis_osm_transport_free_1",
        geometry_kind="point",
        class_field="fclass",
        class_map=_TRANSPORT_CLASSES,
        limitations="Stop positions are snapshots; service frequency and schedules are absent.",
    ),
    LayerSpec(
        layer="pois",
        stem="gis_osm_pois_free_1",
        geometry_kind="point",
        class_field="fclass",
        class_map=_AMENITY_CLASSES,
        limitations=(
            "Points of interest record presence, not capacity, staffing, opening "
            "hours or operating status. Saltbor models those attributes explicitly."
        ),
    ),
    LayerSpec(
        layer="adminareas",
        stem="gis_osm_adminareas_a_free_1",
        geometry_kind="polygon",
        class_field="fclass",
        class_map={},
        default_class="admin_boundary",
        limitations=(
            "Administrative polygons reflect OSM boundary relations. The 2024 "
            "Salvadoran restructuring (D.L. 762) is authoritative in "
            "saltbor.datasets.salvadoran.territory_data, not in OSM."
        ),
    ),
)

LAYER_BY_NAME = {spec.layer: spec for spec in LAYER_SPECS}


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeatureRecord:
    """One normalized geographic feature with full provenance."""

    feature_id: str
    layer: str
    osm_id: str
    name: str
    feature_class: str
    source_class: str
    lat: float
    lon: float
    bbox: tuple[float, float, float, float]  # min_lon, min_lat, max_lon, max_lat
    geometry_type: str
    geometry_json: str
    validation_state: str
    source: str
    source_url: str
    license: str
    acquired_at: str
    crs: str
    resolution: str
    limitations: str

    def to_row(self) -> tuple[Any, ...]:
        return (
            self.feature_id,
            self.layer,
            self.osm_id,
            self.name,
            self.feature_class,
            self.source_class,
            self.lat,
            self.lon,
            self.bbox[0],
            self.bbox[1],
            self.bbox[2],
            self.bbox[3],
            self.geometry_type,
            self.geometry_json,
            self.validation_state,
            self.source,
            self.source_url,
            self.license,
            self.acquired_at,
            self.crs,
            self.resolution,
            self.limitations,
        )

    def to_dict(self, include_geometry: bool = False) -> dict[str, Any]:
        data = {
            "feature_id": self.feature_id,
            "layer": self.layer,
            "osm_id": self.osm_id,
            "name": self.name,
            "feature_class": self.feature_class,
            "source_class": self.source_class,
            "centroid": {"lat": round(self.lat, 7), "lon": round(self.lon, 7)},
            "bbox": [round(v, 7) for v in self.bbox],
            "geometry_type": self.geometry_type,
            "validation_state": self.validation_state,
            "source": self.source,
            "license": self.license,
        }
        if include_geometry:
            data["geometry"] = json.loads(self.geometry_json)
        return data


def _resolution_for(kind: str) -> str:
    return "1:10,000 (metric)" if kind == "polygon" else "metric"


def normalize_record(
    spec: LayerSpec,
    attrs: dict[str, Any],
    shape: Shape,
    reader: ShapefileReader,
    acquired_at: str,
    dataset_id: str,
    source_url: str,
) -> Optional[FeatureRecord]:
    """Convert one raw shapefile record into a normalized FeatureRecord."""
    geometry = shape.__geo_interface__
    if not geometry or geometry.get("type") == "GeometryCollection":
        return None

    osm_id = str(attrs.get("osm_id") or "").strip()
    if not osm_id:
        return None

    name = str(attrs.get(spec.name_field) or "").strip()
    source_class = str(attrs.get(spec.class_field) or "").strip().lower()
    feature_class = spec.classify(attrs)
    lon, lat = shape.centroid
    bbox = tuple(round(float(v), 7) for v in shape.bbox)

    # Validation is a statement about what the data actually supports.  A named
    # OSM feature is an observed real feature; an unnamed footprint is still
    # observed geometry, but its semantic class is inferred.
    if name:
        validation_state = "VERIFIED_REAL"
    else:
        validation_state = "IMPORTED_UNVERIFIED"

    return FeatureRecord(
        feature_id=f"{spec.layer}:{osm_id}",
        layer=spec.layer,
        osm_id=osm_id,
        name=name,
        feature_class=feature_class,
        source_class=source_class,
        lat=round(lat, 7),
        lon=round(lon, 7),
        bbox=bbox,
        geometry_type=geometry["type"],
        geometry_json=json.dumps(geometry, ensure_ascii=False, separators=(",", ":")),
        validation_state=validation_state,
        source=dataset_id,
        source_url=source_url,
        license="ODbL-1.0",
        acquired_at=acquired_at,
        crs=reader.crs,
        resolution=_resolution_for(spec.geometry_kind),
        limitations=spec.limitations,
    )


def iter_layer_features(
    spec: LayerSpec,
    downloads_dir: Path,
    acquired_at: str,
    limit: Optional[int] = None,
    bbox: Optional[tuple[float, float, float, float]] = None,
) -> Iterator[FeatureRecord]:
    stem = downloads_dir / spec.stem
    if not stem.with_suffix(".shp").exists():
        logger.warning("Layer %s unavailable (missing %s.shp)", spec.layer, spec.stem)
        return
    reader = ShapefileReader(stem)
    for attrs, shape in reader.iter_records(limit=limit, bbox=bbox):
        record = normalize_record(
            spec,
            attrs,
            shape,
            reader,
            acquired_at=acquired_at,
            dataset_id="Geofabrik_OSM_El_Salvador",
            source_url=GEOFABRIK_URL,
        )
        if record is not None:
            yield record


# ---------------------------------------------------------------------------
# SQLite materialization
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS dataset_provenance (
    dataset_id      TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    source          TEXT NOT NULL,
    source_url      TEXT NOT NULL,
    license         TEXT NOT NULL,
    attribution     TEXT NOT NULL,
    acquired_at     TEXT NOT NULL,
    crs             TEXT NOT NULL,
    layer_count     INTEGER NOT NULL DEFAULT 0,
    feature_count   INTEGER NOT NULL DEFAULT 0,
    known_limitations TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS layer_provenance (
        layer          TEXT PRIMARY KEY,
    geometry_kind   TEXT NOT NULL,
    feature_count   INTEGER NOT NULL,
    excluded_count  INTEGER NOT NULL DEFAULT 0,
    class_counts_json TEXT NOT NULL DEFAULT '{}',
    validation_json TEXT NOT NULL DEFAULT '{}',
    limitations     TEXT NOT NULL DEFAULT '',
    coverage_bbox   TEXT,
    is_partial      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS geographic_features (
    feature_id      TEXT PRIMARY KEY,
    layer           TEXT NOT NULL,
    osm_id          TEXT NOT NULL,
    name            TEXT NOT NULL DEFAULT '',
    feature_class   TEXT NOT NULL,
    source_class    TEXT NOT NULL DEFAULT '',
    lat             REAL NOT NULL,
    lon             REAL NOT NULL,
    min_lon         REAL NOT NULL,
    min_lat         REAL NOT NULL,
    max_lon         REAL NOT NULL,
    max_lat         REAL NOT NULL,
    geometry_type   TEXT NOT NULL,
    geometry_json   TEXT NOT NULL,
    validation_state TEXT NOT NULL,
    source          TEXT NOT NULL,
    source_url      TEXT NOT NULL,
    license         TEXT NOT NULL,
    acquired_at     TEXT NOT NULL,
    crs             TEXT NOT NULL,
    resolution      TEXT NOT NULL,
    limitations     TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_features_layer ON geographic_features(layer);
-- Composite index for the spatial lookups the router and the world engine
-- perform (layer + bounding box).  Without it SQLite reads every road of the
-- country for each nearest-road query.
CREATE INDEX IF NOT EXISTS idx_features_layer_lat_lon ON geographic_features(layer, lat, lon);
CREATE INDEX IF NOT EXISTS idx_features_class ON geographic_features(layer, feature_class);
CREATE INDEX IF NOT EXISTS idx_features_bbox ON geographic_features(min_lon, min_lat, max_lon, max_lat);
CREATE INDEX IF NOT EXISTS idx_features_name ON geographic_features(name);
"""

_INSERT = """
INSERT OR REPLACE INTO geographic_features VALUES (
    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
)
"""


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create the geography schema, rebuilding an incompatible derived table.

    The geography database is a *derived* artifact: it can always be rebuilt
    from the source extract, so an incompatible older layout is dropped rather
    than migrated.  No source data and no user simulation state lives here.
    """
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='layer_provenance'"
    ).fetchone()
    if row and "coverage_bbox" not in (row[0] or ""):
        logger.info("Rebuilding geography schema (incompatible derived artifact)")
        for table in ("geographic_features", "layer_provenance", "dataset_provenance"):
            conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.executescript(_SCHEMA)


@dataclass
class IngestReport:
    """Outcome of one ingestion run."""

    dataset_id: str
    output_path: str
    layers: dict[str, dict[str, Any]]
    feature_count: int
    duration_seconds: float
    acquired_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "output_path": self.output_path,
            "feature_count": self.feature_count,
            "duration_seconds": round(self.duration_seconds, 2),
            "acquired_at": self.acquired_at,
            "attribution": OSM_ATTRIBUTION,
            "layers": self.layers,
        }


def ingest(
    downloads_dir: Optional[str | Path] = None,
    output_path: Optional[str | Path] = None,
    layers: Optional[Iterable[str]] = None,
    limit_per_layer: Optional[int] = None,
    bbox: Optional[tuple[float, float, float, float]] = None,
    layer_bboxes: Optional[dict[str, tuple[float, float, float, float]]] = None,
    acquired_at: Optional[str] = None,
    progress: Optional[Callable[[str, int], None]] = None,
) -> IngestReport:
    """Ingest Geofabrik layers into the normalized geography database.

    ``limit_per_layer`` and ``bbox`` exist for tests.  ``layer_bboxes`` allows a
    layer to be ingested over a narrower pilot extent (typically buildings,
    which are far too voluminous to materialize nationally).  Any partial
    coverage is recorded in the manifest as ``is_partial`` together with the
    exact bbox, so a pilot can never be mistaken for national coverage.
    """
    layer_bboxes = layer_bboxes or {}
    import time

    started = time.perf_counter()
    downloads = Path(downloads_dir) if downloads_dir else DEFAULT_DOWNLOADS
    output = Path(output_path) if output_path else DEFAULT_OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    stamp = acquired_at or _dt.date.today().isoformat()

    selected = set(layers) if layers else {spec.layer for spec in LAYER_SPECS}
    specs = [spec for spec in LAYER_SPECS if spec.layer in selected]

    conn = sqlite3.connect(output)
    try:
        _ensure_schema(conn)
        conn.execute("DELETE FROM geographic_features WHERE layer IN (%s)" % ",".join("?" * len(specs)),
                     [s.layer for s in specs])
        conn.execute("DELETE FROM layer_provenance WHERE layer IN (%s)" % ",".join("?" * len(specs)),
                     [s.layer for s in specs])

        layer_summaries: dict[str, dict[str, Any]] = {}
        total = 0
        for spec in specs:
            class_counts: dict[str, int] = {}
            validation_counts: dict[str, int] = {}
            rows: list[tuple[Any, ...]] = []
            written = 0
            effective_bbox = layer_bboxes.get(spec.layer, bbox)
            is_partial = effective_bbox is not None or limit_per_layer is not None
            for record in iter_layer_features(
                spec,
                downloads,
                acquired_at=stamp,
                limit=limit_per_layer,
                bbox=effective_bbox,
            ):
                rows.append(record.to_row())
                class_counts[record.feature_class] = class_counts.get(record.feature_class, 0) + 1
                validation_counts[record.validation_state] = (
                    validation_counts.get(record.validation_state, 0) + 1
                )
                written += 1
                if progress is not None and written % 50000 == 0:
                    progress(spec.layer, written)
                if len(rows) >= 5000:
                    conn.executemany(_INSERT, rows)
                    rows.clear()
            if rows:
                conn.executemany(_INSERT, rows)
                rows.clear()

            limitations = spec.limitations
            if is_partial:
                limitations += (
                    " THIS INGEST IS PARTIAL: only features inside the recorded "
                    "coverage bbox / limit were materialized."
                )
            conn.execute(
                "INSERT OR REPLACE INTO layer_provenance VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    spec.layer,
                    spec.geometry_kind,
                    written,
                    0,
                    json.dumps(class_counts, sort_keys=True),
                    json.dumps(validation_counts, sort_keys=True),
                    limitations,
                    json.dumps(list(effective_bbox)) if effective_bbox else None,
                    1 if is_partial else 0,
                ),
            )
            layer_summaries[spec.layer] = {
                "geometry_kind": spec.geometry_kind,
                "feature_count": written,
                "class_counts": class_counts,
                "validation_counts": validation_counts,
                "limitations": limitations,
                "coverage_bbox": list(effective_bbox) if effective_bbox else None,
                "is_partial": is_partial,
            }
            total += written
            logger.info("Ingested %s: %d features", spec.layer, written)

        conn.execute(
            "INSERT OR REPLACE INTO dataset_provenance VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                "Geofabrik_OSM_El_Salvador",
                "El Salvador OpenStreetMap extract (Geofabrik shapefile bundle)",
                "OpenStreetMap contributors via Geofabrik",
                GEOFABRIK_URL,
                "ODbL-1.0",
                OSM_ATTRIBUTION,
                stamp,
                "EPSG:4326 (WGS84)",
                len(layer_summaries),
                total,
                "OSM is crowd-sourced: completeness varies by area and feature type. "
                "Absence of a feature is not evidence of its absence on the ground.",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    report = IngestReport(
        dataset_id="Geofabrik_OSM_El_Salvador",
        output_path=str(output),
        layers=layer_summaries,
        feature_count=total,
        duration_seconds=time.perf_counter() - started,
        acquired_at=stamp,
    )
    manifest_path = output.parent / "ingest_manifest.json"
    manifest_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


# ---------------------------------------------------------------------------
# Runtime access
# ---------------------------------------------------------------------------

class IngestedGeography:
    """Read-only runtime access to the normalized OSM geography database."""

    def __init__(self, path: Optional[str | Path] = None) -> None:
        self.path = Path(path) if path else DEFAULT_OUTPUT
        self.available = self.path.exists()
        self._conn: Optional[sqlite3.Connection] = None
        if not self.available:
            logger.warning(
                "Ingested geography database %s not found; run "
                "`python -m saltbor.datasets.gis.pipeline` to build it.",
                self.path,
            )

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            if not self.available:
                raise FileNotFoundError(self.path)
            self._conn = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # -- provenance -------------------------------------------------------
    def manifest(self) -> dict[str, Any]:
        if not self.available:
            return {"available": False, "attribution": OSM_ATTRIBUTION, "layers": {}}
        dataset = dict(self.conn.execute("SELECT * FROM dataset_provenance LIMIT 1").fetchone() or {})
        layers = {}
        for row in self.conn.execute("SELECT * FROM layer_provenance ORDER BY layer").fetchall():
            layers[row["layer"]] = {
                "geometry_kind": row["geometry_kind"],
                "feature_count": row["feature_count"],
                "class_counts": json.loads(row["class_counts_json"] or "{}"),
                "validation_counts": json.loads(row["validation_json"] or "{}"),
                "limitations": row["limitations"],
                "coverage_bbox": json.loads(row["coverage_bbox"]) if row["coverage_bbox"] else None,
                "is_partial": bool(row["is_partial"]),
            }
        return {
            "available": True,
            "attribution": OSM_ATTRIBUTION,
            "dataset": dataset,
            "layers": layers,
        }

    def counts(self) -> dict[str, int]:
        if not self.available:
            return {}
        rows = self.conn.execute(
            "SELECT layer, COUNT(*) AS n FROM geographic_features GROUP BY layer"
        ).fetchall()
        return {row["layer"]: row["n"] for row in rows}

    # -- spatial queries --------------------------------------------------
    def features_in_bbox(
        self,
        bbox: tuple[float, float, float, float],
        layer: Optional[str] = None,
        feature_class: Optional[str] = None,
        limit: int = 500,
        include_geometry: bool = False,
    ) -> list[dict[str, Any]]:
        """Return features intersecting ``(min_lon, min_lat, max_lon, max_lat)``."""
        if not self.available:
            return []
        min_lon, min_lat, max_lon, max_lat = bbox
        sql = (
            "SELECT * FROM geographic_features WHERE NOT (max_lon < ? OR min_lon > ? "
            "OR max_lat < ? OR min_lat > ?)"
        )
        params: list[Any] = [min_lon, max_lon, min_lat, max_lat]
        if layer:
            sql += " AND layer = ?"
            params.append(layer)
        if feature_class:
            sql += " AND feature_class = ?"
            params.append(feature_class)
        sql += " LIMIT ?"
        params.append(limit)
        out = []
        for row in self.conn.execute(sql, params).fetchall():
            item = {
                "feature_id": row["feature_id"],
                "layer": row["layer"],
                "name": row["name"],
                "feature_class": row["feature_class"],
                "centroid": {"lat": row["lat"], "lon": row["lon"]},
                "bbox": [row["min_lon"], row["min_lat"], row["max_lon"], row["max_lat"]],
                "geometry_type": row["geometry_type"],
                "validation_state": row["validation_state"],
                "source": row["source"],
                "license": row["license"],
            }
            if include_geometry:
                item["geometry"] = json.loads(row["geometry_json"])
            out.append(item)
        return out

    def geojson(
        self,
        bbox: tuple[float, float, float, float],
        layers: tuple[str, ...] = ("roads", "buildings"),
        limit: int = 3000,
        margin_deg: float = 0.003,
    ) -> dict[str, Any]:
        """Return viewport geometry as a GeoJSON FeatureCollection.

        Uses the composite ``(layer, lat, lon)`` index on the stored centroid
        with a small margin, then filters exactly against each feature's
        bounding box.  Scanning every road of the country to answer a map pan
        would cost ~130 ms per request and would not scale beyond the pilot.
        """
        collection: dict[str, Any] = {
            "type": "FeatureCollection",
            "features": [],
            "properties": {
                "source": "OpenStreetMap contributors",
                "license": "ODbL-1.0",
                "attribution": "© OpenStreetMap contributors — ODbL 1.0",
                "layers": list(layers),
                "truncated": False,
            },
        }
        if not self.available:
            collection["properties"]["available"] = False
            return collection

        min_lon, min_lat, max_lon, max_lat = bbox
        placeholders = ",".join("?" for _ in layers)
        cursor = self.conn.execute(
            "SELECT layer, feature_id, name, feature_class, min_lon, min_lat, "
            "max_lon, max_lat, geometry_json, validation_state, source, license "
            "FROM geographic_features WHERE layer IN ("
            + placeholders
            + ") AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
            (
                *layers,
                min_lat - margin_deg,
                max_lat + margin_deg,
                min_lon - margin_deg,
                max_lon + margin_deg,
            ),
        )

        features = []
        # The indexed pre-filter is approximate: features whose centroid falls
        # inside the widened window may still lie outside the viewport.  SQL
        # LIMIT must therefore not be applied before the exact test, or a dense
        # edge of the viewport can consume the whole window and return nothing.
        # Iterate lazily and stop at the requested number of real hits.
        max_candidates = max(limit * 4, 4000)
        for candidates, row in enumerate(cursor):
            if candidates >= max_candidates:
                collection["properties"]["truncated"] = True
                break
            # Exact intersection test against the feature bounding box.
            if (
                row["max_lon"] < min_lon
                or row["min_lon"] > max_lon
                or row["max_lat"] < min_lat
                or row["min_lat"] > max_lat
            ):
                continue
            geometry = None
            if row["geometry_json"]:
                try:
                    geometry = json.loads(row["geometry_json"])
                except (TypeError, ValueError):
                    geometry = None
            if not geometry:
                continue
            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "layer": row["layer"],
                        "feature_id": row["feature_id"],
                        "name": row["name"],
                        "class": row["feature_class"],
                        "validation_state": row["validation_state"],
                        "source": row["source"],
                        "license": row["license"],
                    },
                }
            )
            if len(features) >= limit:
                collection["properties"]["truncated"] = True
                break

        collection["features"] = features
        collection["properties"]["count"] = len(features)
        return collection

    def nearest_road(self, lat: float, lon: float, radius_deg: float = 0.02) -> Optional[dict[str, Any]]:
        """Return the nearest road feature to a WGS84 point, if any.

        The search widens its bounding box progressively.  In the dense San
        Salvador extract a single 0.02° box contains thousands of road
        segments, so always scanning it costs ~130 ms per lookup; starting at
        0.0015° finds the nearest street in a few dozen rows for nearly every
        urban point and only broadens where the territory is sparse.
        """
        if not self.available:
            return None
        best: Optional[tuple[float, dict[str, Any]]] = None
        for current_radius in (0.0015, 0.004, 0.01, radius_deg):
            rows = self.conn.execute(
                "SELECT feature_id, name, feature_class, lat, lon "
                "FROM geographic_features WHERE layer='roads' "
                "AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
                (
                    lat - current_radius,
                    lat + current_radius,
                    lon - current_radius,
                    lon + current_radius,
                ),
            ).fetchall()
            for row in rows:
                d = (row["lat"] - lat) ** 2 + (row["lon"] - lon) ** 2
                if best is None or d < best[0]:
                    best = (
                        d,
                        {
                            "feature_id": row["feature_id"],
                            "name": row["name"],
                            "feature_class": row["feature_class"],
                            "centroid": {"lat": row["lat"], "lon": row["lon"]},
                            "distance_deg": round(d ** 0.5, 6),
                        },
                    )
            # A hit well inside the box cannot be beaten by a wider search.
            if best is not None and best[0] ** 0.5 <= current_radius:
                break
            if current_radius >= radius_deg:
                break
        return best[1] if best else None

    def nearest_features(
        self,
        lat: float,
        lon: float,
        layer: str,
        limit: int = 5,
        radius_deg: float = 0.05,
    ) -> list[dict[str, Any]]:
        if not self.available:
            return []
        rows = self.conn.execute(
            "SELECT feature_id, name, feature_class, lat, lon FROM geographic_features "
            "WHERE layer=? AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?",
            (layer, lat - radius_deg, lat + radius_deg, lon - radius_deg, lon + radius_deg),
        ).fetchall()
        ranked = sorted(rows, key=lambda r: (r["lat"] - lat) ** 2 + (r["lon"] - lon) ** 2)
        return [
            {
                "feature_id": r["feature_id"],
                "name": r["name"],
                "feature_class": r["feature_class"],
                "centroid": {"lat": r["lat"], "lon": r["lon"]},
            }
            for r in ranked[:limit]
        ]

    def ecological_profile(self, bbox: tuple[float, float, float, float]) -> dict[str, Any]:
        """Aggregate land cover inside a bbox for the world/interaction engines."""
        if not self.available:
            return {"available": False}
        profile: dict[str, Any] = {"available": True, "bbox": list(bbox), "by_layer": {}}
        for layer in ("landuse", "natural", "water", "waterways", "buildings", "roads"):
            rows = self.conn.execute(
                "SELECT feature_class, COUNT(*) AS n FROM geographic_features "
                "WHERE layer=? AND NOT (max_lon < ? OR min_lon > ? OR max_lat < ? OR min_lat > ?) "
                "GROUP BY feature_class ORDER BY n DESC",
                (layer, bbox[0], bbox[2], bbox[1], bbox[3]),
            ).fetchall()
            profile["by_layer"][layer] = {row["feature_class"]: row["n"] for row in rows}
        return profile


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    """``python -m saltbor.datasets.gis.pipeline`` entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="saltbor-gis-ingest",
        description="Ingest the Geofabrik OpenStreetMap extract into the normalized geography database.",
    )
    parser.add_argument("--downloads", default=str(DEFAULT_DOWNLOADS), help="Directory holding the Geofabrik shapefiles")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Destination SQLite geography database")
    parser.add_argument("--layers", nargs="*", default=None, help=f"Subset of layers: {', '.join(LAYER_BY_NAME)}")
    parser.add_argument("--limit-per-layer", type=int, default=None, help="Bounded pilot ingestion")
    parser.add_argument("--bbox", nargs=4, type=float, default=None, metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"))
    parser.add_argument(
        "--buildings-bbox",
        nargs=4,
        type=float,
        default=None,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help="Pilot extent for the voluminous buildings layer",
    )
    parser.add_argument("--acquired-at", default=None, help="Acquisition date recorded in provenance (default: today)")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download and unpack the Geofabrik shapefile bundle before ingesting (requires network)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    def _progress(layer: str, count: int) -> None:
        print(f"  ... {layer}: {count} features")

    if args.download:
        download_source(args.downloads)

    layer_bboxes = {
        "buildings": tuple(args.buildings_bbox)
    } if args.buildings_bbox else None
    report = ingest(
        downloads_dir=args.downloads,
        output_path=args.output,
        layers=args.layers,
        limit_per_layer=args.limit_per_layer,
        bbox=tuple(args.bbox) if args.bbox else None,
        layer_bboxes=layer_bboxes,
        acquired_at=args.acquired_at,
        progress=_progress,
    )

    print("\nOpenStreetMap ingestion complete")
    print(f"  dataset     : {report.dataset_id}")
    print(f"  features    : {report.feature_count}")
    print(f"  duration    : {report.duration_seconds:.1f}s")
    print(f"  database    : {report.output_path}")
    for layer, info in report.layers.items():
        partial = " [PARTIAL]" if info.get("is_partial") else ""
        print(f"    {layer:<12} {info['feature_count']:>8}  ({len(info['class_counts'])} classes){partial}")
    print(f"\n{OSM_ATTRIBUTION}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
