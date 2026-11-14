# SALTBOR DEPENDENCY DECISIONS (ADRs)
## Architectural Decision Records for External Libraries & Runtime Dependencies

**Version**: 1.0.0  
**Status**: ACTIVE PRODUCTION SPECIFICATION  

---

### Executive Overview

Every third-party dependency introduced into SALTBOR expands the attack surface, increases memory footprint, complicates installation, and risks obsolescence. This document records the **Architectural Decision Records (ADRs)** governing the core dependencies of SALTBOR, detailing the formal justification for adopting, holding, or rejecting candidate libraries.

---

### Master Dependency Justification Matrix

| Package | Category | Status | Problem Solved | Memory / CPU Impact | Offline Verified | License | Risk Level |
| :--- | :---: | :---: | :--- | :--- | :---: | :---: | :---: |
| **`numpy`** | Runtime Core | **ACCEPTED** | Vectorized array operations, Gini calculations, statistical arrays. | Medium (~30 MB RAM) / Extremely fast (C/SIMD). | YES | BSD-3 | Low |
| **`pydantic`** | Runtime Core | **ACCEPTED** | Domain model validation, schema enforcement, JSON serialization. | Low (~15 MB RAM) / Ultra fast (Rust core in v2). | YES | MIT | Low |
| **`pydantic-settings`** | Runtime Core | **ACCEPTED** | Simulation environment configuration and validation. | Negligible (<2 MB RAM). | YES | MIT | Low |
| **`shapely`** | Runtime Core | **ACCEPTED** | Geometric 2D point-in-polygon and spatial containment. | Low (~15 MB RAM) / Very fast (C GEOS). | YES | BSD-3 | Low |
| **`fastapi`** | Runtime Viz | **ACCEPTED** | REST API endpoints for simulation inspection and web UI. | Low (~25 MB RAM) / Sub-millisecond latency. | YES | MIT | Low |
| **`uvicorn`** | Runtime Viz | **ACCEPTED** | Async ASGI server for the visualization dashboard. | Low (~10 MB RAM) / Low CPU footprint. | YES | BSD-3 | Low |
| **`sqlite3`** | Stdlib Core | **ACCEPTED** | Embedded ACID relational persistence with WAL mode. | Built-in (<4 KB base) / Zero network overhead. | YES | Public Domain | Zero |
| **`pytest`** | Dev / Testing | **ACCEPTED** | Standard test runner, parameterization, and assertion reporting. | Dev only / Fast execution (>600 tests in <90s). | YES | MIT | Low |
| **`numba`** | Dev / Opt | **ACCEPTED** | JIT compilation for computational bottlenecks in math loops. | Dev/Optional (~60 MB RAM) / Native CPU speed. | YES | BSD-2 | Low |
| **`httpx`** | Dev / Testing | **ACCEPTED** | In-process HTTP testing client for FastAPI without socket opening. | Dev only / Negligible RAM. | YES | BSD-3 | Low |
| **`hypothesis`** | Dev / Testing | **APPROVED** | Generative property-based testing for accounting & physical invariants. | Dev only / Configurable iterations. | YES | MPL 2.0 | Low |
| **`networkx`** | Analysis | **ON HOLD** | Advanced social network topology & centrality metrics. | Medium (~25 MB RAM) / Pure Python. | YES | BSD-3 | Low |
| **`mesa`** | Simulation | **REJECTED** | Monolithic ABM framework (superceded by native engine). | Monolithic bloat (~120 MB RAM) / Slower than native. | YES | Apache 2.0 | High (lock-in) |
| **`geopandas`** | GIS | **REJECTED** | Full GIS dataframe stack (requires GDAL, Fiona, PyPROJ). | Heavy bloat (>400 MB RAM, C++ compilation fragility). | YES | BSD-3 | High (fragile) |
| **`playwright`** | Dev / Testing | **ON HOLD** | Headless browser testing for visual UI validation. | Dev only / Requires ~150 MB browser binaries. | YES | Apache 2.0 | Medium |

---

### Detailed Architectural Decision Records

#### ADR-001: Strict Lean Core Policy & Custom Engine Architecture
- **Context**: Simulation frameworks often import hundreds of transitive packages, resulting in gigabyte virtual environments and dependency rot.
- **Decision**: SALTBOR maintains an ultra-lean runtime core. Heavy external frameworks are rejected in favor of focused, native engines tailored to the specific cognitive, sociological, and geographical needs of El Salvador.
- **Consequences**:
  - Positive: Fast cold-start times ($<0.15$ s), minimal memory footprint (under 150 MB for 100 agents), and guaranteed Python 3.14 compatibility.
  - Trade-off: Domain engines (e.g., ADESCO cuchubales, Ostrom CPR, SES stratification) must be authored and maintained internally.

#### ADR-002: Rejection of Mesa in Favor of Native `SimulationRunner`
- **Context**: Mesa is the standard Python ABM framework.
- **Decision**: Retain Mesa strictly as an architectural **`REFERENCIA`**, not a core dependency.
- **Rationale**:
  - Mesa enforces its own event scheduler and simple grid models that do not natively accommodate:
    1. Multi-tier cognitive LOD (Level of Detail).
    2. Embedded SQLite v4 WAL state checkpointing.
    3. Multidimensional psychological appraisals (OCC + Big Five).
    4. Topographic slope navigation on real OpenStreetMap road graphs.
  - SALTBOR's native `SimulationRunner` delivers **125.87 ticks/second** at $N=20$, far outpacing standard Mesa loops while conserving accounting integrity.

#### ADR-003: Adoption of Hypothesis for Property-Based Testing
- **Context**: Edge cases in conservation laws (e.g., rounding errors in financial dues, floating-point drift in Gini calculation, negative energy loops) are difficult to anticipate via hand-written unit tests.
- **Decision**: Approve `hypothesis` as an optional development dependency (`[project.optional-dependencies] dev`).
- **Rationale**:
  - Generates hundreds of pseudorandom edge-case inputs to verify invariants (e.g. $\sum \text{Treasury}_{\text{after}} == \sum \text{Treasury}_{\text{before}}$).
  - Shrinks any failing counterexample to the minimal reproducible case.
  - Zero runtime impact in production simulation runs.

#### ADR-004: In-Memory Spatial Geometry with Shapely vs Full GeoPandas/GDAL
- **Context**: Modeling cantón boundaries, urban parcel perimeters, and flooded zones requires polygon containment testing.
- **Decision**: Adopt `shapely` directly; reject `geopandas` and `gdal`.
- **Rationale**:
  - `shapely` provides fast, reliable GEOS geometric operations (point-in-polygon, intersections, buffering) in a self-contained precompiled binary wheel.
  - `geopandas` pulls in `fiona`, `pyproj`, and `gdal`, creating notorious installation headaches on Windows and consuming hundreds of megabytes of RAM.
  - SALTBOR stores coordinates in standard WGS84 (latitude/longitude) and converts distances via native Haversine and local UTM projections with pure NumPy.

#### ADR-005: Built-in SQLite + WAL vs External SQL Engines
- **Context**: The simulation generates tens of thousands of event logs, relationship shifts, and state checkpoints.
- **Decision**: Standardize exclusively on Python's built-in `sqlite3` configured with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`).
- **Rationale**:
  - Requires zero installation or external service daemons (PostgreSQL/MySQL).
  - WAL mode allows concurrent readers (e.g., FastAPI visualization server) to query live simulation metrics without blocking the simulation execution thread.
  - Checkpoint files remain 100% portable single-file databases.

#### ADR-006: Lightweight Vanilla Web Interface vs NPM / Node Frameworks
- **Context**: The simulation includes an interactive web dashboard for real-time visualization of maps, agents, and institutions.
- **Decision**: Implement the frontend using standard **Vanilla HTML5, modern CSS3, and ES6 JavaScript** served directly by FastAPI. Reject Node.js, Webpack, Vite, React, Tailwind, and NPM.
- **Rationale**:
  - Eliminates the `node_modules` directory entirely (often 300+ MB with thousands of vulnerable micro-packages).
  - The entire UI is under 150 KB, loads instantaneously in any modern browser, and requires zero compilation or build step.
  - Operates completely offline without external CDN dependencies.
