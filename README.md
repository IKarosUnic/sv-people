# Saltbor — Synthetic Human & Society Simulation

**Saltbor** is a scalable, modular simulation of synthetic humans living within a functional, evolving settlement.

Unlike conventional game NPCs driven by scripted decision trees or finite-state machines, each synthetic human in Saltbor possesses an evolving cognitive architecture: dynamic personality traits, multi-channel emotional dynamics, multi-tier memory systems (working, episodic, semantic, procedural), intrinsic goal generation, and interpersonal relationships.

Crucially, **Saltbor does not require a Large Language Model (LLM) for every individual or decision**. The entire core simulation operates deterministically and algorithmically with sub-millisecond execution times and compact memory footprints (~0.5 KB per human).

---

## Technical Stack

- **Python**: 3.12+ (tested on Python 3.14)
- **Numerical Operations**: NumPy
- **Data Validation & Schemas**: Pydantic v2
- **Persistent Storage**: SQLite (WAL mode, single centralized database)
- **Test Framework**: Pytest
- **External Data Adapter**: NVIDIA Nemotron Personas El Salvador (with automatic offline fallback adapter)
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

Simulate 1 day (96 ticks at 15 minutes per tick) with live terminal dashboard reports every 6 simulated hours (24 ticks):

```bash
python -m saltbor.main run --ticks 96 --report-interval 24
```

Simulate 3 days continuously:

```bash
python -m saltbor.main run --ticks 288 --report-interval 48
```

#### CLI Options for `run`:
- `--ticks <int>`: Total number of discrete ticks to simulate (default: 96).
- `--report-interval <int>`: Ticks between console dashboard printouts (default: 24).
- `--seed <int>`: Master random seed for deterministic reproducibility (default: 42).
- `--db <path>`: SQLite database file path (default: `saltbor.db`).
- `--resume`: Resume from existing database state rather than re-creating population.
- `--verbose`: Display human occupancy rosters for every location.

---

### Inspect Individual Psychological State

Inspect the internal personality drift, emotional profile, working/episodic memory items, active goals, and social relationships of any individual (1..20):

```bash
python -m saltbor.main inspect --serial 1
```

```bash
python -m saltbor.main inspect --serial 4
```

---

### Inspect Settlement Locations

List all 16 functional buildings, coordinates, and schedules in Saltbor:

```bash
python -m saltbor.main locations
```

---

### Run Behavioral Validation Experiments

Execute the 6 automated scientific experiments validating emergent behaviors:

```bash
python -m saltbor.main experiments
```

---

## Running Automated Tests

Run the complete automated test suite with pytest:

```bash
python -m pytest tests/ -v
```

All 20 tests validate:
1. Individual creation & immutable identity continuity
2. Working, episodic, semantic, and procedural memory creation
3. Memory decay, spacing effects, and selective forgetting
4. Multi-channel emotional reactions & personality modulation
5. Personality base shift and current value drift
6. Non-linear skill acquisition with diminishing returns
7. Autonomous goal generation from unmet physical/social needs
8. Multi-attribute utility decision-making
9. Social relationship evolution & trust dynamics
10. Dijkstra navigation & topological routing across Saltbor
11. Activity preconditions & biological degradation
12. Persistence & state recovery across application restarts
13. Deterministic reproducibility across random seeds
14. Resource consumption monitoring (< 1 MB quota compliance)

---

## Repository Structure

```
saltbor/
├── core/                    # Immutable identity, simulation clock, global config, types
├── population/              # SyntheticHuman aggregate root, demographics, factory, registry
├── cognition/               # Functional cognitive modules:
│   ├── personality/         # 8-dimensional traits with dual base/current drift
│   ├── emotions/            # 10 emotion channels, mood valence, dynamic decay
│   ├── memory/              # Working (7±2), episodic, semantic, procedural, consolidation
│   ├── cognitive/           # Sensory perception and personality-biased attention
│   ├── learning/            # Skill practice and experience distillation
│   ├── autonomy/            # Intrinsic goal generation and prioritization
│   └── decision/            # Multi-attribute utility action selection
├── social/                  # Relationships (trust, affinity, familiarity) and groups
├── world/                   # Settlement environment:
│   ├── geography/           # 2D coordinates, bounding boxes, distance calculations
│   ├── locations/           # Location models and Saltbor map (16 functional places)
│   ├── navigation/          # Dijkstra road graph and travel time estimators
│   └── activities/          # Activity catalog with durations, needs, and effects
├── events/                  # In-process pub/sub EventBus and event catalog
├── persistence/             # SQLite connection, WAL schema, serialization, repositories
├── simulation/              # SimulationRunner, agent scheduler, metrics tracker
├── visualization/           # Terminal console dashboard and individual inspector
├── datasets/                # Nemotron El Salvador adapter & mock data generator
├── llm/                     # Optional Ollama / external API interface
├── experiments/             # Automated behavioral validation experiments
└── main.py                  # Command-line entry point
```

---

## Behavioral Experiments Breakdown

| # | Scientific Principle | Validation Outcome |
|---|---|---|
| **1** | **Differential Reaction** | High-neuroticism / low-agreeableness individual reacts with **2.0× higher anger** than calm/cooperative individual when subjected to the identical conflict event. |
| **2** | **Skill Acquisition** | Asymptotic power-law learning curve demonstrates clear **diminishing returns** with continued practice. |
| **3** | **Autonomous Goals** | Fasting individual autonomously formulates an "Obtain and eat food" goal based on physiological hunger deficit without external prompting. |
| **4** | **Selective Forgetting** | After 40 simulated days, trivial daily memories drop below salience threshold and are pruned, while emotionally charged friendship events are protected and retained. |
| **5** | **Divergent Social Bonds** | Cooperative interactions build trust and affinity, while conflict produces rivalry with the same target. |
| **6** | **Behavioral Adaptation** | Experiencing repeated financial losses shifts risk tolerance downward and increases caution. |

---

## Performance & Resource Measurements

- **Tick Duration**: 0.75 – 0.85 ms per tick with 20 individuals.
- **Simulation Speed**: ~400 – 450 ticks per second (over 4.5 simulated days per wall-clock second).
- **Logical Memory Usage**: ~0.51 KB per human (Target < 1,024 KB: **PASS**).
- **Persistence Storage**: Single SQLite database with Write-Ahead-Logging (WAL) mode.

---

## Known Limitations & Roadmap

### Phase 0.1 Limitations
- Spatial movement between locations is discrete (travel activity over estimated ticks rather than micro-step continuous steering).
- Economic model tracks individual cash and activity costs/wages, but lacks macro-level dynamic market supply-demand price curves.
- Social communication uses structured event exchanges and relationship metrics rather than free-form natural language generation.

### Prioritized Roadmap for Phase 0.2+
1. **Dynamic Market Economy**: Inventory tracking at `Mercado Central`, fluctuating crop prices at `Cooperativa Agrícola`, and commercial dining margins.
2. **Conversation Synthesis**: Optional local LLM hook (via `saltbor.llm.adapter`) for generating localized Salvadoran Spanish dialogue snippets during socialization events in the plaza.
3. **Agent Sleep/Wake Partitioning**: Dormant agent scheduling to scale efficiently to 500 and 1,000 synthetic individuals without CPU overhead.
4. **Interactive Web Dashboard**: Optional lightweight browser viewer using HTML5 canvas or SVG to visualize movement across the settlement map.
