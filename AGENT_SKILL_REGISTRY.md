# SALTBOR AGENT SKILL REGISTRY (AGENT_SKILL_REGISTRY.md)
**Status**: ACTIVE ECOSYSTEM REGISTRY (Phase 1.10)  
**Total Registered Skills**: 24 Specialized Domains  

---

## Skill Domain Index

| Domain ID | Category | Skill Path | Primary Capabilities & Target |
| :--- | :--- | :--- | :--- |
| `architecture` | Systems Engineering | [agent_skills/architecture/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/architecture/SKILL.md) | Decoupled engines, state flow, dependency inversion, clean boundaries |
| `simulation` | Core Engine | [agent_skills/simulation/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/simulation/SKILL.md) | Tick loops, state checkpoints, clock synchronization, reproducibility |
| `multi_agent_systems` | Agent Systems | [agent_skills/multi_agent_systems/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/multi_agent_systems/SKILL.md) | Spontaneous organization, leadership, social fission, cooperative norms |
| `artificial_life` | Emergence & ALife | [agent_skills/artificial_life/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/artificial_life/SKILL.md) | Metabolic loops, physiological drives, open-ended cultural survival |
| `cognitive_science` | Psychology & Mind | [agent_skills/cognitive_science/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/cognitive_science/SKILL.md) | Belief updating, confirmation bias, social epistemology, memory decay |
| `psychology` | Emotions & Traits | [agent_skills/psychology/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/psychology/SKILL.md) | OCC appraisal, emotional valence, Big Five personality integration |
| `sociology` | Social Dynamics | [agent_skills/sociology/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/sociology/SKILL.md) | Collective action, Granovetter thresholds, assembly deliberation |
| `social_science` | Institutions & CPR | [agent_skills/social_science/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/social_science/SKILL.md) | Ostrom CPR principles, graded sanctions, normative desuetudo |
| `economics` | Markets & Finance | [agent_skills/economics/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/economics/SKILL.md) | Absolute accounting conservation, informal *fiado*, solvency, Gini |
| `geospatial` | GIS & Topography | [agent_skills/geospatial/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/geospatial/SKILL.md) | OSM coordinates, road routing, slope penalties, bridges, obstacles |
| `environmental_science` | Climate & Hazards | [agent_skills/environmental_science/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/environmental_science/SKILL.md) | Seasonal rainfall (*verano/invierno*), landslides, crop yield impact |
| `media_systems` | Information & News | [agent_skills/media_systems/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/media_systems/SKILL.md) | Radio broadcasts, fictional press desks, bulletins, broadcast reach |
| `cultural_simulation` | Culture & Sports | [agent_skills/cultural_simulation/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/cultural_simulation/SKILL.md) | Music genres, generational taste evolution, football leagues, rivalries |
| `data_engineering` | Storage & Database | [agent_skills/data_engineering/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/data_engineering/SKILL.md) | SQLite WAL mode, schema migrations, duckdb/parquet analytics |
| `performance` | Profiling & Speed | [agent_skills/performance/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/performance/SKILL.md) | Benchmarking ms/tick, memory RSS, Numba and vectorized array loops |
| `testing` | Quality Assurance | [agent_skills/testing/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/testing/SKILL.md) | Pytest parameterization, deterministic seeds, property testing |
| `scientific_validation` | Epistemology & Science | [agent_skills/scientific_validation/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/scientific_validation/SKILL.md) | Falsifiable hypotheses, empirical tiers 1-5, multi-tier causality |
| `frontend` | Web UI Architecture | [agent_skills/frontend/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/frontend/SKILL.md) | Vanilla JS, SSE streams, responsive dashboard panels |
| `visualization` | Cartography & WebGL | [agent_skills/visualization/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/visualization/SKILL.md) | MapLibre vector maps, deck.gl point clouds, real-time agent flows |
| `security` | Auditing & Safety | [agent_skills/security/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/security/SKILL.md) | Offline sandboxes, zero untrusted scripts, dependency hygiene |
| `research` | Repository Discovery | [agent_skills/research/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/research/SKILL.md) | Codebase discovery, documentation indexing, architecture review |
| `python_engineering` | Python 3.14 Idioms | [agent_skills/python_engineering/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/python_engineering/SKILL.md) | Modern type hints, Pydantic v2 schemas, zero-copy buffers |
| `code_review` | Quality Gates | [agent_skills/code_review/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/code_review/SKILL.md) | Static audit, dead code pruning, regression containment |
| `documentation` | Technical Writing | [agent_skills/documentation/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/documentation/SKILL.md) | Markdown reporting, Mermaid graphs, KaTeX math documentation |

---

## Skill Selection Workflow

Before modifying or implementing any feature, the developer agent MUST:
1. Identify the primary and secondary domains in this table.
2. Read the corresponding `SKILL.md` file.
3. Apply the specified workflows, constraints, and validation criteria.
