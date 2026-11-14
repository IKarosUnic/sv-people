# SALTBOR AGENT OPERATING INSTRUCTIONS (AGENTS.md)
## Directives, Skill Routing, Engineering Protocols & Security Boundaries

**Target**: Autonomous Coding Agents, Assistant LLMs, and Software Engineers working on SALTBOR  
**Language / Environment**: Python 3.12–3.14 (Validated on Python 3.14.5, Windows 11)  
**Status**: ACTIVE SYSTEM DIRECTIVE  

---

### 1. Core Operating Directives

Every agent operating within this repository MUST strictly follow these universal rules:

1. **Accounting Conservation is Absolute**: Never create money, agricultural harvest, or physical assets out of thin air. In every economic transaction, the credit to one entity must exactly equal the debit to another.
2. **Pure Local & Offline Execution**: Do not introduce network calls, cloud APIs, telemetry, or mandatory remote dependencies into the simulation runtime.
3. **Never Rebuild Functional Engines**: Respect architectural continuity. Before implementing new capabilities, inspect `saltbor/` to build upon existing engines rather than creating redundant parallel systems.
4. **Follow the 10-Step Workflow**: Always follow the sequence: *Understand $\rightarrow$ Consult Skills $\rightarrow$ Research $\rightarrow$ Audit $\rightarrow$ Design $\rightarrow$ Implement $\rightarrow$ Test $\rightarrow$ Compare $\rightarrow$ Security/Perf Review $\rightarrow$ Document*.
5. **Deterministic Testing**: Ensure tests use fixed random seeds and SQLite in-memory or WAL modes for 100% reproducible execution.
6. **Strict License & Dependency Hygiene**: Consult [DEPENDENCY_DECISIONS.md](file:///c:/GIT%20HUB/sv%20people/DEPENDENCY_DECISIONS.md) and [LICENSE_COMPLIANCE.md](file:///c:/GIT%20HUB/sv%20people/LICENSE_COMPLIANCE.md) before suggesting or adding any external package.

---

### 2. Agent Skills Routing Table

When assigned a task, consult the specialized skill in `agent_skills/`:

| Task Domain | Relevant Skill File | Primary Focus |
| :--- | :--- | :--- |
| **System Architecture & Engine Design** | [agent_skills/architecture/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/architecture/SKILL.md) | Decoupled engines, clean state flow, SOLID principles. |
| **Simulation Core, Ticks & Clocks** | [agent_skills/simulation/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/simulation/SKILL.md) | `SimulationRunner`, tick loops, state checkpoints. |
| **Multi-Agent Coordination & Emergence** | [agent_skills/multi_agent_systems/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/multi_agent_systems/SKILL.md) | Spontaneous organizations, fission, mergers, leadership. |
| **Geospatial & Road Topography** | [agent_skills/geospatial/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/geospatial/SKILL.md) | OpenStreetMap, coordinates, slope penalties, obstacles. |
| **Social Norms, Governance & CPR** | [agent_skills/social_science/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/social_science/SKILL.md) | Ostrom CPR, deliberative assemblies, sanctions, desuetudo. |
| **Economic Systems & Inequality** | [agent_skills/economics/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/economics/SKILL.md) | Conservation, *fiado*, business solvency, Gini, Palma. |
| **Cognitive Appraisal & Psychology** | [agent_skills/psychology/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/psychology/SKILL.md) | OCC appraisal, emotional valence, Big Five traits. |
| **SQLite Persistence & Databases** | [agent_skills/data_engineering/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/data_engineering/SKILL.md) | WAL mode, ACID transactions, schema migrations. |
| **Performance, Profiling & Latency** | [agent_skills/performance/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/performance/SKILL.md) | Benchmarking ms/tick, memory RSS, Numba optimization. |
| **Automated Testing & Regressions** | [agent_skills/testing/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/testing/SKILL.md) | Pytest suites, parameterization, property-based tests. |
| **Scientific Validation & Causality** | [agent_skills/scientific_validation/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/scientific_validation/SKILL.md) | Falsifiable hypotheses, multi-tier causality tracing. |
| **Web Dashboards & REST API** | [agent_skills/frontend/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/frontend/SKILL.md) | Vanilla JS/HTML, FastAPI endpoints, subpanel design. |
| **Security & Dependency Auditing** | [agent_skills/security/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/security/SKILL.md) | Sandbox boundaries, zero untrusted scripts, audit rules. |
| **Technical Research & Discovery** | [agent_skills/research/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/research/SKILL.md) | Repository discovery, documentation analysis. |
| **Python 3.14 Idioms & Types** | [agent_skills/python_engineering/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/python_engineering/SKILL.md) | Modern typing, Pydantic v2 schemas, memory layout. |
| **Code Review & Quality Control** | [agent_skills/code_review/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/code_review/SKILL.md) | Dead code pruning, regression prevention, static audit. |
| **Documentation & Technical Writing** | [agent_skills/documentation/SKILL.md](file:///c:/GIT%20HUB/sv%20people/agent_skills/documentation/SKILL.md) | Markdown reporting, Mermaid diagrams, KaTeX formulas. |

---

### 3. Verification Protocol

Before declaring any engineering task complete:
1. Run the targeted test suite: `python -m pytest tests/<subsystem>/ -v`.
2. Run the behavioral experiments if modifying social/cognitive engines: `python -m pytest tests/test_experiments/ -v`.
3. Check execution latency and ensure no regression in `ms_per_tick`.
4. Ensure all newly referenced files are linked with clickable `[basename](file:///path/to/file)` format.
