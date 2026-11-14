# SALTBOR LICENSE & INTELLECTUAL PROPERTY COMPLIANCE
## Legal Framework, Data Attribution, and License Compatibility Matrix

**Version**: 1.0.0  
**Scope**: All SALTBOR Code, Embedded Datasets, External Dependencies, and Reference Materials  
**Status**: ACTIVE COMPLIANCE AUDIT  

---

### Executive Overview

SALTBOR is committed to strict intellectual property integrity and full compliance with open-source licensing. This document records the licensing status of all direct dependencies, external datasets (notably OpenStreetMap and Salvadoran public geospatial sources), and guidelines for incorporating future third-party software.

---

### 1. Master License Compatibility Matrix

All direct and optional dependencies used in SALTBOR operate under business-friendly, permissive, or weak-copyleft licenses:

| Component / Library | Stated License | License Category | Commercial Use Permitted? | Redistribution Obligations | SALTBOR Status |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **`python` (CPython)** | PSF License 2.0 | Permissive | Yes | Retain copyright notice. | Stdlib Base |
| **`sqlite3`** | Public Domain | Permissive / Free | Yes | None (Blessed, uncopyrighted). | Stdlib Core |
| **`numpy`** | BSD-3-Clause | Permissive | Yes | Retain BSD copyright notice. | Core Dependency |
| **`pydantic`** | MIT License | Permissive | Yes | Retain MIT copyright notice. | Core Dependency |
| **`pydantic-settings`**| MIT License | Permissive | Yes | Retain MIT copyright notice. | Core Dependency |
| **`shapely`** | BSD-3-Clause | Permissive | Yes | Retain BSD copyright notice. | Core Dependency |
| **`fastapi`** | MIT License | Permissive | Yes | Retain MIT copyright notice. | Viz Dependency |
| **`uvicorn`** | BSD-3-Clause | Permissive | Yes | Retain BSD copyright notice. | Viz Dependency |
| **`pytest`** | MIT License | Permissive | Yes | Retain MIT copyright notice. | Dev Dependency |
| **`numba`** | BSD-2-Clause | Permissive | Yes | Retain BSD copyright notice. | Dev Dependency |
| **`httpx`** | BSD-3-Clause | Permissive | Yes | Retain BSD copyright notice. | Dev Dependency |
| **`hypothesis`** | MPL 2.0 | Weak Copyleft | Yes | Changes to Hypothesis itself must remain MPL; file-level boundary. | Dev Approved |
| **`rich`** | MIT License | Permissive | Yes | Retain MIT copyright notice. | Viz Optional |

---

### 2. OpenStreetMap (OSM) Data & ODbL Compliance

SALTBOR utilizes real cartographic and spatial data representing the geography of El Salvador (San Esteban Catarina, Department of Cuscatlán, San Salvador Metropolitan Periphery, Los Chorros gorge).

- **Data Origin**: OpenStreetMap contributors (https://www.openstreetmap.org).
- **License**: **Open Database License (ODbL) 1.0** (https://opendatacommons.org/licenses/odbl/).
- **Attribution Obligation**:
  > *"Contains data from OpenStreetMap, © OpenStreetMap contributors, available under the Open Database License (ODbL)."*

#### SALTBOR Compliance Safeguards:
1. **Separation of Database vs Produced Work**:
   - The simulation queries spatial node coordinates, road types, and distances to calibrate in-memory graphs (`LocationRegistry`, `NavigationGraph`).
   - The simulation outcomes (agent decisions, synthetic histories, economic transactions) constitute a **Produced Work** under Section 4.3 of the ODbL and do not trigger a Share-Alike obligation on the simulation source code.
2. **Derivative Extracted GeoJSON**:
   - Any raw OSM extract distributed alongside the project retains the ODbL license and attribution notice in its metadata header.

---

### 3. Salvadoran Official Data & Public Sector Information

SALTBOR references public datasets from official institutions of the Republic of El Salvador:
- **CNR (Centro Nacional de Registros)**: Administrative municipal boundaries, departmental demarcations, and cadastral references.
- **MINEC / BCR (Banco Central de Reserva)**: Economic indicators, minimum wage scales, inflation series, and household income percentiles.
- **DIGESTYC / BCR (Censos y Encuestas de Hogares - EHPM)**: Demographic pyramids, occupational distributions, and family household sizes.

#### Compliance Policy:
- Official statistical aggregates and laws of the Republic of El Salvador are public domain information (*Información Pública de Oficio* under the *Ley de Acceso a la Información Pública - LAIP*).
- All synthetic agents are generated with **randomized, pseudonymous attributes** statistically calibrated to census distributions. No real personal data (PII) of living individuals is ever utilized or embedded.

---

### 4. Copyleft & Contamination Prevention Policy

To protect the architectural autonomy and distribution flexibility of SALTBOR:

1. **Strong Copyleft Isolation (GPLv3 / AGPLv3)**:
   - Strong copyleft libraries (such as GPL-licensed solvers or AGPL network tools) must **NOT** be imported as core Python dependencies.
   - If an algorithm from a GPL library is studied, it may only serve as conceptual reference (`REFERENCIA`), with all production simulation code authored from first principles.
2. **Weak Copyleft (LGPL / MPL)**:
   - Libraries licensed under LGPL or MPL (such as `hypothesis` under MPL 2.0) are permitted as isolated development/testing tools, provided their source files remain modular and unmixed with proprietary core engines.

---

### 5. Third-Party Code Inclusion Checklist

Before committing any external code, script, or snippet:
- [x] Does it have an explicit, recognizable open-source license?
- [x] Is the license permissive (MIT, BSD, Apache, CC0) or cleanly isolated?
- [x] Has the original author's copyright notice been preserved?
- [x] Does it avoid viral copyleft contamination?
- [x] Is it free of non-commercial-only clauses (CC-BY-NC) that restrict deployment?
- [x] Has the dependency been recorded in `EXTERNAL_REPOSITORY_CATALOG.md` and `DEPENDENCY_DECISIONS.md`?
