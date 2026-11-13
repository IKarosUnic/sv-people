# SALTBOR — Third-Party Notices

SALTBOR is an original codebase. **No source code, assets, datasets, text, or binary files from the projects below were copied or vendored into this repository during Phase 1.7.** The projects are listed because their published ideas, mechanisms, or genres informed the design, or because they are runtime dependencies.

## Conceptual references (no code copied)

| Project | Author / repository | License | What informed SALTBOR |
|---|---|---|---|
| FAtiMA Toolkit | Universidade de Lisboa / `FAtiMA-Toolkit` | Apache-2.0 | OCC-style appraisal, emotional decay, coping concepts |
| Generative Agents | Joonspk / `joonspk-research/generative_agents` | Apache-2.0 | Associative memory retrieval, reflection, planning loop |
| StanfordHCI / genagents | Stanford HCI / `StanfordHCI/genagents` | MIT | Memory-stream and agent-architecture concepts |
| Mesa | Project Mesa | Apache-2.0 | Agent-based modelling conventions (not a dependency) |
| ReGoap | `ReGoap` | Apache-2.0 | Goal-oriented action planning concepts (not a dependency) |
| DFHack | DFHack contributors | Zlib | Simulation tooling and inspection concepts |
| Cataclysm: Dark Days Ahead | CleverRaven | Repository metadata: Apache-2.0; the project README states CC-BY-SA 3.0 for code/content | Survival needs, body-state and crafting concepts |
| RimWorld | Ludeon Studios | Proprietary | Social/psychological simulation genre; no assets, code, or text used |
| Dwarf Fortress | Bay 12 Games | Proprietary | Emergent simulation genre; no assets, code, or text used |
| RimWorld Psychology (community mod) | `rwpsychology/Psychology` | **No explicit license file found** | High-level topics only (personality, mental states, social dynamics). No code, text, or assets used. The previously cited `RimWorld-Community-Pack/Psychology` URL returns 404; `EdB/RimWorld-Psychology` also returns 404. |

Where a project has no explicit license, SALTBOR does not reuse its code or assets. Ideas and general mechanics are not copyrightable; the implementation here is independent.

## Data

| Dataset | License | Use |
|---|---|---|
| OpenStreetMap | ODbL 1.0 | Geographic base data in `saltbor/datasets/gis/`; attribution is shown in the UI and must be preserved in derived data |

## Runtime dependencies

Declared in `pyproject.toml` and installed from PyPI. Their licenses remain with their authors:

| Package | Typical license |
|---|---|
| numpy | BSD-3-Clause |
| pydantic / pydantic-settings | MIT |
| fastapi | MIT |
| uvicorn | BSD-3-Clause |
| shapely | BSD-3-Clause |
| pytest, pytest-cov, httpx | MIT / Apache-2.0 |
| numba (optional) | BSD-2-Clause |
| rich (optional) | MIT |

This table is informative, not a replacement for the license files shipped with each installed package. SALTBOR does not redistribute those packages in this repository.

## Attribution text for the UI/data

> Map data © OpenStreetMap contributors, available under the Open Database License (ODbL) 1.0.

## Contact / corrections

If a rights holder believes an attribution is missing or inaccurate, open an issue in the repository with the specific project and material so it can be reviewed and corrected.
