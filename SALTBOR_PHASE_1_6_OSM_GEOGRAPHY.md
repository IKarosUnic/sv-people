# SALTBOR — OPENSTREETMAP GEOGRAPHIC FOUNDATION (PHASE 1.6)

Status legend: **IMPLEMENTED** (code exists) · **INTEGRATED** (wired into the
runtime) · **TESTED** (automated tests) · **VALIDATED** (measured under stated
conditions) · **EXPERIMENTAL** · **NOT IMPLEMENTED**.

---

## 1. Source and licensing

| Field | Value |
| --- | --- |
| Primary source | Geofabrik regional extract, `el-salvador-latest-free.shp.zip` |
| Source URL | `https://download.geofabrik.de/central-america/el-salvador-latest-free.shp.zip` |
| Upstream | OpenStreetMap contributors, <https://www.openstreetmap.org/> |
| License of derived database | **ODbL 1.0** (Open Database License) |
| Attribution string | `© OpenStreetMap contributors — ODbL 1.0` (served by `/api/geography/manifest`, rendered in the UI badge) |
| CRS | EPSG:4326 (WGS84), `.prj` parsed and recorded |
| Acquisition date | recorded in `dataset_provenance.acquired_at` (this build: `2026-11-13`) |
| Resolution | per layer, as published by Geofabrik (OSM `fclass` taxonomy) |
| Validation state | per feature, `IMPORTED_VERIFIED` / `IMPORTED_UNVERIFIED` |

ODbL obligations honoured by construction: the derived database is
redistributable only with attribution and share-alike; the ingest manifest, the
API and the UI all carry the attribution and license fields. The 399 MB source
download and the 184 MB derived SQLite file are **excluded from version
control** (`.gitignore`: `saltbor/datasets/gis/downloads/`, `.../ingested/`) and
are reproducible with one command (below).

Nothing was scraped from Google Maps or any non-open source.

---

## 2. Ingestion pipeline — IMPLEMENTED, INTEGRATED, TESTED, VALIDATED

Files:

- `saltbor/datasets/gis/shapefile_reader.py` — dependency-free streaming
  SHP + DBF reader (Point, PolyLine, Polygon with Z/M), ring winding → GeoJSON
  holes, `__geo_interface__`, `.prj`/`.cpg` metadata, bbox and predicate
  filtering.
- `saltbor/datasets/gis/pipeline.py` — layer specs, `fclass` → SALTBOR class
  normalization, SQLite schema, provenance rows, `IngestedGeography` read API,
  CLI.
- `saltbor/datasets/gis/geofabrik_extractor.py` — rewritten on the new reader
  (previously dead code due to a missing `pyshp` dependency).

Why a custom reader: `pyshp`, `fiona`, `pyrosm` and `osmnx` are absent from the
environment and require network installation. SALTBOR is offline-first, so a
~300-line reader over the documented ESRI format was preferable to adding
native/binary dependencies. GeoPandas/Shapely/PROJ *are* installed and remain
usable for analysis, but are not required by the ingestion path.

### 2.1 Command

```bash
# first time only: download (≈399 MB) and build the normalized database
python -m saltbor.datasets.gis.pipeline --download \
    --buildings-bbox -89.2020 13.6930 -89.1860 13.7040 \
    --acquired-at 2026-11-13

# rebuild from an existing download
python -m saltbor.datasets.gis.pipeline \
    --buildings-bbox -89.2020 13.6930 -89.1860 13.7040 \
    --acquired-at 2026-11-13
```

Measured on the reference machine: **151,251 features in 30.6 s**, producing
`geography.sqlite` (184 MB) + `ingest_manifest.json`.

### 2.2 Result of the executed ingest

| Layer | Features | Classes (sample) | Completeness |
| --- | --- | --- | --- |
| roads | 121,344 | tertiary, secondary, primary, residential, pedestrian, trunk, service, track | full country |
| buildings | 989 | residential, commercial, institutional, industrial, religious, other | **PARTIAL** — pilot bbox only |
| landuse | 10,887 | residential_area, commercial_area, industrial_area, institutional_area, recreation_area | full country |
| natural | 122 | coastline, terrain | full country |
| water | 1,437 | water_body, reservoir, other | full country |
| waterways | 4,433 | river, stream, drain, canal | full country |
| places | 2,657 | city, town, village, hamlet, suburb, locality | full country |
| transport | 897 | bus_stop, bus_station, railway_station, airport, ferry_terminal | full country |
| pois | 8,011 | health, education, food_service, market, public_safety, other | full country |
| adminareas | 474 | admin_boundary | full country |

Buildings are ingested only inside the San Salvador Centro pilot bbox
`(-89.2020, 13.6930, -89.1860, 13.7040)` because the national building layer is
large and not needed for the pilot. This is recorded honestly, never hidden:

- `layers.buildings.is_partial = true`
- `layers.buildings.coverage_bbox = [-89.202, 13.693, -89.186, 13.704]`
- `layers.buildings.limitations` contains a `PARTIAL` note.

### 2.3 Provenance model

`geographic_features` columns: `feature_id`, `layer`, `feature_class`,
`osm_id`, `name`, `lat`, `lon`, `geometry_type`, `geometry_json`,
`min_lon/min_lat/max_lon/max_lat`, `source`, `source_url`, `acquired_at`,
`license`, `crs`, `resolution`, `validation_state`, `attributes_json`.

`dataset_provenance` and `layer_provenance` hold one row per dataset/layer with
the same fields plus counts, class distribution and limitations. Nothing in the
database lacks a source.

Classification of feature confidence (per the specification's distinction):

| Category | How it appears in SALTBOR |
| --- | --- |
| Verified geographic data | OSM feature with `name` and a specific `fclass` → `IMPORTED_VERIFIED` |
| Approximate geographic data | OSM geometry without name / generic class → `IMPORTED_UNVERIFIED`; routes carry `is_approximate` and `snap_distance_m` |
| Synthetic infrastructure | existing `world/geographic/` synthetic map, unchanged, never presented as OSM |
| Simulated establishments | Phase 1.5 businesses/facilities (not OSM) |
| Unverified records | `IMPORTED_UNVERIFIED` |

---

## 3. Routing over real geometry — IMPLEMENTED, INTEGRATED, TESTED, VALIDATED

`saltbor/world/geographic/osm_router.py`:

- Builds a graph from ingested road geometry using coordinate identity at
  `1e-5°` (≈1.1 m); every vertex becomes a node, so intersections connect
  through real geometry rather than through invented shortcuts.
- Class-based speeds (walk and drive), one-way handling (`oneway` tag).
- Dijkstra over the graph, `RouteResult` with `found`, `distance_m`,
  `duration_minutes`, `path`, `edges_traversed`, `snap_distance_m`,
  `is_approximate`, `reason`, and provenance/attribution fields.
- Unreachable or too-distant targets return `found=False` with an explicit
  reason (`network_empty`, `snap_distance_exceeded`, `no_connected_path`) —
  agents never teleport.

Measured on the real extract (pilot area): a 483 m walk takes 6.5 min while the
765 m drive takes 1.8 min — different routes, different speeds, both plausible.

---

## 4. Runtime access and performance

`IngestedGeography` (read-only SQLite connection):

- `manifest()` — dataset + per-layer provenance, attribution, counts.
- `features_in_bbox(bbox, layer, class, limit, include_geometry)`.
- `nearest_road(lat, lon)` — progressive bbox widening.
- `nearest_features(lat, lon, layer, limit)`.
- `ecological_profile(lat, lon)` — landuse/water/vegetation context.

### 4.1 Index migration (performance fix, measured)

The query plan used `idx_features_class (layer=?)` and then filtered 121k rows.
Added a composite index:

```sql
CREATE INDEX IF NOT EXISTS idx_features_layer_lat_lon
    ON geographic_features(layer, lat, lon);
```

This is created by `_ensure_schema` on new ingests; existing databases are
migrated in place with the same statement (0.43 s, idempotent, followed by
`ANALYZE`). Verified query plan after migration:

```
SEARCH geographic_features USING INDEX idx_features_layer_lat_lon (layer=? AND lat>? AND lat<?)
```

| Measurement | Before | After |
| --- | --- | --- |
| `nearest_road`, 500 calls | 136.1 ms/call (162 ms with naive widening) | **0.23–0.29 ms/call** |

---

## 5. CNR (Centro Nacional de Registros) reference assessment

Target: <https://mapa.elsalvadormaps.sv/cnr/map/4>

| Aspect | Finding |
| --- | --- |
| Nature | ArcGIS-based institutional viewer publishing Salvadoran territorial layers (administrative boundaries, cadastral, hydrography, orthophotos) |
| Public machine interface | The viewer exposes an ArcGIS REST endpoint used by the web map, but **no documented, stable public API contract, no bulk download endpoint and no explicit open license** were found in the viewer itself |
| Licensing | CNR data are institutional/public-sector data; reuse terms are not stated on the map viewer. Redistribution of derived layers is therefore **not established** |
| Resolution / accuracy | Higher cadastral accuracy than OSM where published, but coverage and update cadence per layer are not documented publicly |
| Action taken | **NOT IMPLEMENTED** as a data source. No CNR geometry was downloaded, cached or redistributed |
| What would be required | Written authorization or an explicit open license for each layer, a stable endpoint or bulk export, and attribution requirements; then ingestion would reuse `pipeline.LAYER_SPECS` with a new `source` value and `license` per layer |

The viewer remains useful as a **visual cross-check** for OSM administrative
boundaries (department/municipality names and extents), which is how it is
referenced here. This assessment is deliberately conservative: the specification
forbids assuming that every CNR layer is downloadable or licensed for reuse.

**Optional integration point (EXPERIMENTAL, not enabled):** if a CNR ArcGIS
REST feature layer is later authorized, it can be read with
`?f=geojson&where=1=1&outFields=*` and normalized with the existing
`FeatureRecord` contract, because the schema is source-agnostic.

---

## 6. API surface (INTEGRATED, TESTED)

| Endpoint | Purpose |
| --- | --- |
| `GET /api/geography/manifest` | Dataset + layer provenance, counts, license, attribution, partial flags |
| `GET /api/geography/features?min_lon&min_lat&max_lon&max_lat&layer&limit&include_geometry` | Bounded feature query |
| `GET /api/geography/route?from_lat&from_lon&to_lat&to_lon&mode=walk|drive` | Real-network route with distance/duration/provenance |
| `GET /api/geography/ecological_profile?lat&lon` | Environmental context of a point |

All responses include `source`, `license` and `attribution`.

---

## 7. Known limitations of the geographic foundation

1. Buildings are national-**incomplete**: only the pilot bbox is ingested.
2. No MBTiles/vector-tile packaging: the UI receives GeoJSON from the API, which
   is adequate at pilot scale but not for country-wide rendering.
3. Road **closures, congestion and travel cost** are not modelled; routing is
   static per ingest.
4. Footpaths/cycleways are treated with class speeds, not with surface or
   accessibility attributes.
5. Address points and cadastral parcels are absent (not present in the Geofabrik
   free extract).
6. Elevation, soil and landcover are represented only through OSM tags; no DEM
   is used, so slope-dependent travel time is not modelled.
7. The CNR reference is not ingested (licensing unresolved, see §5).
8. `nearest_road` returns the nearest **centroid**, not the nearest point on the
   line; the router snaps to vertices.
