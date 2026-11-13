# Saltbor — Synthetic Human & Society Simulation

**Saltbor** is a scalable, biologically inspired simulation of synthetic humans developing cognitive, emotional, and social lives within an interactive Salvadoran settlement.

Phase 0.4 introduces **Social Complexity, Biological Lifecycle, Dynamic Economy & Advanced Cognitive Architecture**:
- **Biological Lifecycle**: Continuous biological aging across 7 developmental stages (infancy to older adulthood), synthetic non-deterministic genetics, persistent genealogical pedigree graph, biological courtship, gestation and birth, household caregiving, succession/inheritance, and Gompertz-Makeham mortality with bereavement grief.
- **Dynamic Resource Economy**: Physical inventories with divisible units and spoilage, input-output recipe conservation (carpentry, farming, cooking), dynamic equilibrium pricing with oscillation dampening, market shortages, and household resource consumption scaling.
- **Advanced Cognitive Architecture**: Multi-Attribute Utility Theory (MAUT) formal decision model separating internal state, beliefs, information, preferences, actions, and consequences; Goal-Oriented Action Planning (GOAP) with A* state search; and Hierarchical Task Network (HTN) decomposition with dynamic obstacle replanning.
- **Social Complexity & Institutions**: 13 semantic dialogue intents, offline regional Salvadoran Spanish Natural Language Generation (NLG), multi-turn conversation sessions, rumor and information propagation with hop provenance and trust-weighted belief evaluation, enhanced social groups, and democratic community assemblies.
- **Continuous Spatial Movement**: 2D continuous waypoint navigation, repulsive vector collision avoidance steering, casual proximity encounters, and physical postures with carrying burden penalties.
- **Scalability & Cognitive LOD**: 4 execution tiers (LOD 0 Full Cognition, LOD 1 Routine, LOD 2 Event-Driven Macro-Steps, LOD 3 Dormant Historical Archive) and $O(1)$ 2D Spatial Grid Partitioning, enabling sustained throughput across scaled populations.

### Phase 1.6 — Geographic Intelligence, Perception & World Interaction (current)

- **OpenStreetMap foundation**: dependency-free ESRI Shapefile reader plus a normalized SQLite geography database, ingested from the Geofabrik El Salvador extract with per-feature provenance (source URL, acquisition date, ODbL 1.0 license, CRS, validation state). Executed build: **151,251 features in 30.6 s** — 121,344 roads, 10,887 landuse, 8,011 POIs, 4,433 waterways, 2,657 places; buildings (989) are explicitly **partial** (pilot bbox only).
- **Real road routing**: `OSMRoadNetwork` builds its topology from actual OSM geometry, supports walking and driving with class speeds and one-way tags, and returns explicit failure reasons instead of teleporting agents.
- **Perception engine**: agents only know what they perceived. Acuity depends on age, fatigue, health, stress, night and rain; clarity gates identity and detail, so a stranger is **never** identity-resolved; interpretations carry named biases and alternative readings; testimony is discounted by credibility × trust; memory encoding is salience-gated; randomness derives from the deterministic identity serial so seeds reproduce across processes.
- **Experiments EXP_16_A … EXP_16_T** (61 hypotheses) covering perception, interpretation, development, bias, physical cost, romance, infidelity, illness, environmental exposure, accidents, caregiving, institutional access, degradation and recovery, causal cascades, trajectories, generations, navigation, LOD performance and an integrated 96-tick run.
- **API/UI**: `/api/perception/*`, `/api/geography/{manifest,features,route,ecological_profile}`, a perception block in the individual dossier, and an OSM attribution badge in the frontend.

See `SALTBOR_PHASE_1_6_AUDIT.md`, `SALTBOR_PHASE_1_6_OSM_GEOGRAPHY.md` and `SALTBOR_PHASE_1_6_FINAL_REPORT.md`. Known limitations are listed there explicitly (checkpoint stalls, pilot-only buildings, no map rendering, CNR licensing unresolved).

Crucially, **Saltbor does not require a Large Language Model (LLM) or external API for any simulation mechanic**. The entire core simulation operates deterministically and algorithmically with sub-millisecond execution times (~1.06 ms per tick for 20 humans) and a lightweight footprint (~4.35 KB per human).

---

## Technical Stack

- **Python**: 3.12+ (tested on Python 3.14.5)
- **Numerical Operations**: NumPy
- **Data Validation & Schemas**: Pydantic v2
- **Persistent Storage**: SQLite (WAL mode, transactions, full foreign key constraints)
- **Test Framework**: Pytest
- **External Data Adapter**: NVIDIA Nemotron Personas El Salvador (with automatic offline fallback generator)
- **Optional Extensions**: Abstract LLM Adapter interface (Ollama / Local APIs)

---

## Quick Start & Installation

### 1. Requirements

Ensure Python 3.12 or newer is installed:

```bash
python --version
```

### 2. Install Dependencies

From the repository root:

```bash
pip install -e .
```

For development and test dependencies:

```bash
pip install -e ".[dev]"
```

---

## Running the Simulation

The project includes an intuitive command-line interface via `saltbor.main`:

### Run Simulation Loop

Simulate 1 day (96 ticks at 15 minutes per tick) with live terminal reports every 6 simulated hours (24 ticks):

```bash
python -m saltbor.main run --ticks 96 --report-interval 24
```

Simulate 3 days continuously:

```bash
python -m saltbor.main run --ticks 288 --report-interval 48
```

#### CLI Options for `run`:
- `--ticks <int>`: Total discrete ticks to simulate (default: 96).
- `--report-interval <int>`: Ticks between console dashboard printouts (default: 24).
- `--seed <int>`: Master random seed for deterministic reproducibility (default: 42).
- `--db <path>`: SQLite database file path (default: `saltbor.db`).
- `--resume`: Resume from existing database state rather than re-creating population.
- `--verbose`: Display human occupancy rosters for every location.

---

### Inspect Individual Psychological State

Inspect the internal personality drift, biological temperament, emotional profile, working/episodic memory items, active goals lifecycle, and directional social attitudes of any individual (1..20):

```bash
python -m saltbor.main inspect --serial 1
```

```bash
python -m saltbor.main inspect --serial 4
```

---

### Inspect Settlement Locations

List all 16 functional buildings, coordinates, capacities, and schedules in Saltbor:

```bash
python -m saltbor.main locations
```

---

### Run Behavioral Validation Experiments

Execute the automated scientific experiments validating emergent cognitive and social behaviors:

```bash
python -m saltbor.main experiments
```

---

### Phase 0.3 Simulation Laboratory CLI

Phase 0.3 introduces the `lab` command for interactive experimental research, individual decision explainability traces, population diversity audits, and scalability benchmarking:

#### 1. Execute All 8 Laboratory Experiments and Export Reports
```bash
python -m saltbor.main lab experiments --export
```
Generates human-readable Markdown and structured JSON reports under `experiments/results/`.

#### 2. Individual Observability & Decision Trace
Inspect any individual's full internal state and view an interpretable decision explanation trace:
```bash
python -m saltbor.main lab trace --serial 1 --ticks 24
```

#### 3. Population Behavioral & Anti-Artificial Audit
Detect repetitive behavior, population homogeneity, emotional ineffectiveness, or spatial lock-in:
```bash
python -m saltbor.main lab population --ticks 96
```

#### 4. Hardware Scalability Benchmarks (20 to 1,000 Agents)
Benchmark CPU latency, tick throughput, and memory scaling:
```bash
python -m saltbor.main lab benchmark
```

---

## Behavioral Experiments Suite

Saltbor includes 14 automated experiments demonstrating measurable behavioral divergence:

### Phase 0.3 Autonomous Simulation Laboratory & Behavioral Stress Testing (NEW)

The new experimental laboratory (`saltbor.simulation.laboratory`) introduces formal behavioral hypothesis testing across 8 behavioral stress experiments:

| ID | Experiment | Behavioral Phenomenon Validated | Outcome |
|---|---|---|---|
| **EXP_A** | **Individual Autonomy** | Independent goal formulation, prioritization, and lifecycle tracking under biological deficits. | **PASS** |
| **EXP_B** | **Personality Evolution** | Plastic trait drift (+0.011) under severe negative life events while maintaining baseline stability under routine events. | **PASS** |
| **EXP_C** | **Memory & Learning** | Significant traumatic experiences maintain accessibility and induce affective location aversion (-0.45), while routine records decay into dormant archive. | **PASS** |
| **EXP_D** | **Social Relationships** | Emergent trust development through repeated cooperation (+0.12) and sharp collapse under conflict/betrayal (-0.40). | **PASS** |
| **EXP_E** | **Environmental Adaptation** | Adaptive behavioral switching from commercial dining to domestic meal preparation under financial shock. | **PASS** |
| **EXP_F** | **Conflicting Needs** | High conscientiousness prioritizes vocational work while low conscientiousness yields to physical rest under identical exhaustion. | **PASS** |
| **EXP_G** | **Long-Term Development** | Sustained multi-day divergence in economic assets (STD > $20.00) and cumulative autobiographical memory logging without degradation. | **PASS** |
| **EXP_H** | **Emergence & Clustering** | Spontaneous formation of communal social hubs (e.g. `plaza_central`, `comedor_dona_maria`) and organic relationship networks. | **PASS** |

---

### Phase 0.2 Advanced Cognitive Experiments

| ID | Experiment | Behavioral Phenomenon Validated | Outcome |
|---|---|---|---|
| **A** | **Different Personalities** | Identical context (Plaza Mayor at 15:00) causes Scholar to **study** while Socializer chooses to **socialize**. | **PASS** |
| **B** | **Emotional Modulation** | Under identical needs, High Loneliness drives **socialization**, High Anxiety drives **rest/withdrawal**, and High Curiosity drives **study**. | **PASS** |
| **C** | **Memory & Location Aversion** | Traumatic event at Mercado Municipal creates negative emotional association, causing measurable avoidance while routine dining memories fade into dormant archive without data destruction. | **PASS** |
| **D** | **Personality Evolution** | Repeated financial loss and broken trust permanently shift baseline neuroticism upward and risk tolerance downward, with complete causal audit logs recorded in `evolution_history`. | **PASS** |
| **E** | **Autonomous Self-Improvement** | Individual autonomously identifies competency deficit, formulates multi-step learning plan, and deliberate practice increases carpentry proficiency from 0.10 to 0.44. | **PASS** |
| **F** | **Social Relational Arc** | Demonstrates cooperative bonding (trust 0.71), severe conflict collapse (trust 0.35), directional asymmetry (apologetic P1 vs skeptical P2), and mutual reconciliation (trust 0.62). | **PASS** |
| **G** | **Goal Abandonment** | Infeasible commercial objective encounters obstacles, undergoes hesitation/procrastination, and is rationally abandoned with recorded causal explanation. | **PASS** |
| **H** | **Individual Divergence** | Identical twins exposed to divergent environmental conditions (economic prosperity vs catastrophe) develop radically different personalities, emotional moods, and lifetime objectives. | **PASS** |

### Phase 0.1 Foundational Experiments

| # | Scientific Principle | Validation Outcome |
|---|---|---|
| **1** | **Differential Reaction** | High-neuroticism / low-agreeableness individual reacts with 2.0× higher anger than calm/cooperative individual when subjected to identical conflict. |
| **2** | **Skill Acquisition** | Asymptotic power-law learning curve demonstrates diminishing returns with continued practice. |
| **3** | **Autonomous Goals** | Fasting individual autonomously formulates an "Obtain and eat food" goal based on physiological hunger deficit. |
| **4** | **Selective Forgetting** | Trivial memories fade below salience threshold and are moved to dormant archive, while emotionally charged events remain active. |
| **5** | **Divergent Social Bonds** | Cooperative interactions build trust and affinity, while conflict produces rivalry. |
| **6** | **Behavioral Adaptation** | Experiencing repeated losses shifts risk tolerance downward and increases caution. |

---

## Running Automated Tests

Run the complete automated test suite (84 tests) with pytest:

```bash
uv run --extra dev pytest -v
```

or with standard pytest:

```bash
pytest -v
```

### Validation of Acceptance Criteria:
- **Phase 0.2 Acceptance**: 10 tests verifying differential reactions, skill acquisition, selective forgetting, and state persistence.
- **Phase 0.3 Laboratory Validation**: 13 tests in `tests/test_simulation/test_phase03_laboratory.py` verifying simulation reproducibility with fixed seeds, experiments A–H, cognitive causal feedback loops, individual observability traces, population diversity audits, and multi-scale population benchmarks.
- **Phase 0.4 Biological Lifecycle & Generational Tests**: 7 tests in `tests/test_lifecycle/test_lifecycle.py` verifying 7 developmental stages, synthetic non-deterministic genetics, bidirectional genealogy trees, household succession/inheritance, courtship/gestation/birth, continuous aging, and Gompertz-Makeham mortality with bereavement grief.
- **Phase 0.4 Dynamic Economy Tests**: 5 tests in `tests/test_economy/test_economy.py` verifying divisible inventories, production conservation, market shortages, dynamic price adaptation, and household food demand scaling.
- **Phase 0.4 Advanced Cognition Tests**: 3 tests in `tests/test_cognition/test_advanced_cognition.py` verifying formal MAUT decision decomposition, GOAP A* planning, and HTN carpentry decomposition with dynamic replanning.
- **Phase 0.4 Social Complexity Tests**: 3 tests in `tests/test_social/test_social_complexity.py` verifying offline regional Spanish dialogue NLG, rumor propagation with provenance and trust-gating, and community assembly democratic voting.
- **Phase 0.4 Continuous Spatial Movement Tests**: 4 tests in `tests/test_world/test_spatial_movement.py` verifying 2D path following, collision avoidance steering, encounter detection, and carrying burden speed penalties.
- **Phase 0.4 Scalability & LOD Tests**: 2 tests in `tests/test_simulation/test_lod_and_partitioning.py` verifying cognitive LOD 0–3 tier modulation and $O(1)$ spatial grid neighborhood lookups.
- **Phase 0.4 Behavioral Experiments Suite**: 8 tests in `tests/test_experiments/test_phase04_experiments.py` executing all 8 Phase 0.4 experiments (`EXP_04_A` through `EXP_04_H`).
- **Section 19 Authentic Salvadoran Integration Tests**: 10 experiments (`EXP_SV_01` through `EXP_SV_10`) in `tests/test_experiments/test_salvadoran_experiments.py` covering urban/rural differentiation, canícula/temporales, informal markets, and remesas.
- **Phase 0.8 Real Geographic World & El Salvador Integration**: 31 tests (20 experiments `EXP_08_A` through `EXP_08_T` in `tests/test_experiments/test_phase08_territorial_experiments.py` and 11 unit/integration tests in `tests/test_world/test_phase08_geography.py`) verifying the 2024 administrative restructuring (14 departments, 44 municipalities, 262 districts), CNR/Google Maps/OSM cartographic sources, real establishments with 7 validation states, spatial indexing with Dijkstra multimodal navigation, river bridges across Río Lempa, natural obstacle avoidance, pupusería unit economics, walking-radius fiado microcredit, individual epistemic spatial cognition, and 100% offline-first SQLite persistence.

Total tests: **526 passing automated tests** across all phases with 0 regressions (`python -m pytest -q`). Phase 1.6 added 47: perception (11), OSM pipeline and routing (11), experiment suite (22), API contracts (3).

---

## Performance & Resource Measurements

> Superseded for Phase 1.6 by `docs/reports/phase16_benchmark.json`: sustained runs measure **0.65–0.80 ms per agent per tick** (50 → 200 agents) with a checkpoint stall of 0.9–3.3 s once per simulated day. The figures below describe the earlier, smaller configurations.

- **Tick Duration**: ~0.68 ms per tick with 20 individuals.
- **Simulation Speed**: ~800 – 1,000 ticks per second (> 8 simulated days per wall-clock second).
- **Logical Memory Usage**: ~0.57 KB per human (Target < 1,024 KB: **PASS**).
- **Persistence Storage**: Single SQLite database in Write-Ahead-Logging (WAL) mode with zero lock contention.
