# DEPENDENCY AND LICENSE AUDIT
**Date**: November 2026  
**System**: SALTBOR Phase 1.10 Architecture  
**Focus**: License Compatibility, Security Boundaries & Dependency Hygiene

---

## 1. Installed Runtime Dependency Audit

The active virtual environment (`Python 3.14.5`) was audited for license compatibility against commercial and open-source usage:

| Package | Version | License | Category | Compliance Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Python** | 3.14.5 | PSF | Core Runtime | Fully compliant. |
| **NumPy** | 2.4.6 | BSD-3-Clause | Numerical Array Computing | Permissive; fully compliant. |
| **SciPy** | 1.17.1 | BSD-3-Clause | Scientific & Statistical Library | Permissive; fully compliant. |
| **Pandas** | 3.0.5 | BSD-3-Clause | Tabular Data Processing | Permissive; fully compliant. |
| **NetworkX** | 3.6.1 | BSD-3-Clause | Graph Theory & Network Models | Permissive; fully compliant. |
| **FastAPI** | 0.138.0 | MIT | Web API & Visualization Server | Permissive; fully compliant. |
| **Uvicorn** | 0.49.0 | BSD-3-Clause | ASGI Server | Permissive; fully compliant. |
| **Pydantic** | 2.12.5 | MIT | Data Validation & Schemas | Permissive; fully compliant. |
| **Graphify** | 0.9.75 | MIT | Knowledge Graph AST Extractor | Permissive; fully compliant. |
| **Pytest** | 9.1.1 | MIT | Test Suite & Automation | Permissive; test only. |
| **Playwright** | 1.58.0 | Apache 2.0 | Browser Automation | Permissive; test only. |

---

## 2. Prohibited & Restricted Dependencies

1. **GPL / AGPL v3**: Prohibited in core simulation libraries to preserve distribution autonomy without viral licensing contamination.
2. **Mandatory Cloud SDKs (AWS, Azure, GCP, Datadog)**: Prohibited in runtime execution to maintain strict local-first, offline operation.
3. **Proprietary Telemetry / Tracking**: Zero third-party telemetry, analytics pingbacks, or mandatory external dependencies.

---

## 3. Data Provenance & Open Geospatial Licenses

- **OpenStreetMap (OSM)**: Open Database License (ODbL) 1.0. Derivative databases and exports stored in `saltbor/datasets/gis/` must credit OpenStreetMap contributors.
- **Geofabrik**: Raw dumps downloaded under ODbL.
- **Salvadoran Public Records (CNR, BCR, DIGESTYC)**: Public domain government statistical information, attributed with provenance timestamps and source agency IDs.
- **Scientific Literature (OpenAlex, PubMed, arXiv)**: Open access metadata under CC0/public domain; abstracts cached locally with full DOI attribution.
