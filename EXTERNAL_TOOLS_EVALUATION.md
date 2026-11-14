# EXTERNAL TOOLS EVALUATION
**Date**: November 2026  
**System**: SALTBOR Phase 1.10 Architecture  
**Focus**: Rigorous Evaluation of Candidate Packages & Frameworks

---

## 1. Candidate Evaluation Matrix

In strict adherence to the mandate (*"Do not add a dependency merely because it is popular. For every candidate, record what problem it solves, whether SALTBOR already has equivalent functionality, license, maintenance, resource requirements, integration complexity, and whether to adopt, adapt, study or reject it"*):

| Tool / Repository | Problem It Solves | Existing SALTBOR Capability | License | Status & Maintenance | Resource Requirements | Complexity | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Mesa** | Agent-based modeling framework (scheduler, grid, space) | SALTBOR has a specialized, vectorized CPython/SQLite spatial engine (`SimulationRunner`, `SpatialPartitioning`) | Apache 2.0 | Active (v3.x) | Medium | High (requires architectural rewrite of ticks) | **Reject / Study** (Study scheduling patterns, but do not replace high-throughput custom runner) |
| **NetworkX** | Graph data structures, centralities, community clustering | Built-in social network graphs, `RumorEngine` graph, and Graphify AST | BSD-3-Clause | Active (v3.6.1 **Already Installed**) | Low | Low | **Adopt** (Already available in Python 3.14 venv for graph analytics) |
| **OSMnx** | OpenStreetMap download and graph extraction | Full custom offline pipeline (`ShapefileReader`, `pipeline.py`, `geography.sqlite`) | MIT | Active | High (pulls heavy GDAL/Shapely dependencies) | High | **Reject / Adapt** (Current offline shapefile reader handles El Salvador without heavy GDAL) |
| **SimPy** | Discrete-event process simulation | Tick-based discrete time (`Tick` loop in `SimulationRunner`) | MIT | Active | Low | Medium | **Study** (Keep discrete synchronous ticks for determinism; study event queues) |
| **Hypothesis** | Property-based testing | Parameterized pytest and stochastic seed fixtures | MPL-2.0 | Active | Low | Low | **Adopt (Optional)** / **Study** (Property testing useful for financial conservation) |
| **Playwright** | End-to-end browser and UI testing | Fast unit tests + FastAPI TestClient | Apache 2.0 | Active (**Installed**) | High | Medium | **Adopt (Test-only)** (For headless UI testing without affecting runtime) |
| **DuckDB** | In-process columnar SQL OLAP | SQLite 3.50.4 with WAL mode and in-memory analytics | MIT | Active | Low (single C++ binary, zero dependencies) | Low | **Adopt / Adapt** (Ideal for historical analytics; use SQLite as transactional core and DuckDB for columnar analysis) |
| **OpenTelemetry** | Distributed tracing, metrics, spans | `MetricsTracker` in `metrics.py` | Apache 2.0 | Active | Medium (many SDK plugins) | Medium | **Adapt (Clean In-House Spans)** (Implement standard OpenTelemetry span data structures locally without mandatory cloud collectors) |
| **MapLibre GL** | Vector map rendering and GPU cartography | Static Leaflet/GeoJSON tiles in `saltbor/visualization/web/` | BSD-3-Clause | Active | Low | Low | **Adopt (Frontend)** (Native vector tile rendering offline via web assets) |
| **deck.gl** | WebGL data layers for massive point clouds | Canvas/SVG custom renderer | MIT | Active | Low | Medium | **Adopt (Frontend)** (For rendering 100k+ agents smoothly in browser) |
| **OpenAlex** | Open scientific literature catalog & API | None | CC0 / MIT | Active | Low (REST API / offline JSON cache) | Low | **Adopt (Offline/Cached Adapter)** (Permits programmatic queries for evidence-backed research) |

---

## 2. Decision Log Summary

1. **Keep SQLite as Transactional Single Source of Truth**: SQLite 3.50.4 WAL mode guarantees 100% ACID compliance and accounting conservation.
2. **Implement Lightweight OpenTelemetry Spans In-House**: Provide zero-dependency structured traces that conform to OpenTelemetry semantics without adding bulky network telemetry packages.
3. **Pure Python/NumPy/Pandas Core**: Leverage Python 3.14.5 + NumPy 2.4.6 + Pandas 3.0.5 + NetworkX 3.6.1 already active in the virtual environment.
