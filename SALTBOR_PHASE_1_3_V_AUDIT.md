# SALTBOR — PHASE 1.3-V REPOSITORY AUDIT & ARCHITECTURAL FOUNDATION
## INTERACTIVE VISUAL SIMULATION ENVIRONMENT, DIGITAL SOCIETY OBSERVABILITY & COGNITIVE EXPLORER

**Date:** November 10, 2026  
**Phase:** Phase 1.3-V  
**Status:** Audit Completed, Architecture Designed  
**Environment:** Python 3.14.5 (64-bit), SQLite WAL Mode, Pydantic v2, FastAPI/Uvicorn, Node v24.16.0  
**Hardware Reference:** AMD Ryzen 7 8700G (8C/16T), 32 GB DDR5-6000, AMD Radeon 780M, Windows 11  

---

## 1. REPOSITORY AUDIT & SYSTEM INVENTORY

### 1.1 Existing Frontend & Visualization Systems
- **Existing Visualization:**
  - `saltbor/visualization/cartography.py`: Static SVG generator and standalone HTML exporter for the territorial map of El Salvador (14 departments, 44 municipalities, 262 districts, roads CA-1/CA-2/CA-4, volcanoes, lakes, establishments).
  - `saltbor/visualization/console.py`: Rich/ASCII terminal overview rendering population, location distribution, and tick performance.
  - `saltbor/visualization/inspector.py`: Text-based multi-panel diagnostic profile for individuals (demographics, physical, personality drift, emotional profile, memory footprint, goals, relationships).
  - `saltbor/simulation/analysis/individual_observability.py`: Structured Python dictionary dossier and decision trace text generator.
  - `saltbor/simulation/analysis/phase05_observability.py`: Cultural lineage inspection, loan ledgers, business balance sheets, multi-dimensional relationship metrics.
  - `saltbor/knowledge/observability/inspector.py`: Individual, collective, and discovery profiles for knowledge graphs.
- **Finding:** No interactive real-time web application or simulation UI previously existed. The visualization layer consisted of offline text/terminal printers and static SVG/HTML exporters.
- **Decision:** Build an interactive, client-rendered Single-Page Application (SPA) backed by FastAPI and Server-Sent Events (SSE). The frontend uses hardware-accelerated HTML5 Canvas (2D Canvas with HiDPI and path batching) combined with an SVG overlay and a CSS design system for scientific instrumentation. This requires zero heavy external node bundling dependencies at runtime, operates 100% offline, and achieves sustained 60 FPS on the reference AMD Radeon 780M GPU.

---

### 1.2 Existing Backend Systems & Domain Models

| Domain Subsystem | Existing Implementation & Key Components | Available Data Structures | Status & Instrumentation Needed |
| :--- | :--- | :--- | :--- |
| **Simulation Core** | `SimulationRunner`, `SimulationClock`, `SimulationScheduler`, `SimulationConfig`, `MetricsTracker` | `current_tick`, `current_day`, `tick_of_day`, `is_daytime`, `current_hour_int`, `phase`, tick latency ms, event emission count | Fully available. Needs thread-safe asynchronous controller (`SimulationController`) for start/pause/step/speed/reset. |
| **Population & Demographics** | `PopulationRegistry`, `SyntheticHuman`, `Demographics`, `PhysicalState` | `uid`, `serial`, `full_name`, `age`, `gender`, `occupation`, `education_level`, `energy`, `hunger`, `health`, `money`, `current_location_id`, `current_activity`, `activity_ticks_remaining` | Fully available. Serialization to JSON required for active roster and individual dossiers. |
| **Personality & Emotions** | `PersonalityEngine`, `PersonalityTraits`, `EmotionalEngine` | Big Five + risk_tolerance, patience, persistence (`base_value`, `current_value`, drift), mood valence, regulation capacity, active emotional charges | Fully available. Exposed in `/api/individuals/{uid}`. |
| **Cognitive Brain Architecture** | `CognitiveBrainArchitecture`, `DecisionEngine`, `AutonomyEngine`, `MemoryEngine` | 6 Functional subsystems: Frontal, Hippocampal, Limbic, Temporal, Parietal, Cerebellar. Goal lifecycle, working memory, episodic memory, procedural skills, decision traces (`DecisionTrace`: chosen action, utility, reasoning, dominant factors, alternatives) | Fully available. Decision trace pipeline (`OBSERVATION → NEEDS → MEMORY RETRIEVAL → REASONING → PLANNING → DECISION → ACTION → RESULT`) maps directly to `SyntheticHuman.update()` and `BrainDeliberationOutcome`. |
| **Cognitive Development (Phase 1.3)** | `CognitiveProfile`, `MetaLearningEngine`, `CognitivePlasticityEngine`, `ScientificThinkingEngine` | 14 dynamic mental capabilities, 8.40 budget cap, fatigue, meta-learning strategies, power-law curves, 8 epistemic states, scientific inquiry cycle | Fully available. Exposed in Cognitive Architecture Explorer. |
| **Knowledge Architecture** | `GlobalKnowledgeGraph`, `CollectiveKnowledgeGraph`, `HypothesisDiscoveryGraph`, `IndividualKnowledgeGraph`, `ProceduralKnowledgeGraph` | Concepts, claims, confidence, verification count, source pathway, misconceptions, hypotheses, transmission records, endangered knowledge | Fully available. Exposed in `/api/knowledge` with node-link topology and provenance tracing. |
| **Social Networks & Communities** | `SocialNetworkEngine`, `SocialEngine`, `CommunityFormationEngine`, `MultiDimensionalRelationship` | Social edges, relationship types (family, friendship, trust, rivalry, trade, mentorship, cooperation, conflict), trust/affinity/familiarity, spontaneous communities, ADESCOs | Fully available. Exposed in `/api/social` with filtered local neighborhood extraction. |
| **Civilization Dynamics** | `CivilizationEngine`, `CulturalEvolutionEngine`, `BusinessRegistry`, `CreditEngine`, `CollectiveEconomyEngine`, `GovernanceEngine`, `JudicialTribunal`, `DistributedEducationEngine` | Cultural traditions, authenticity drift, business enterprises, loan contracts, informal commerce (fiado), educational workshops, dispute cases | Fully available. Exposed in `/api/civilization` and `/api/economy`. |
| **Real Territorial Geography** | `RealGeographicEngine`, `SalvadoranGeographyEngine`, `SalvadoranClimateEngine`, `EstablishmentDirectory`, `TerritorialNavigationEngine` | 14 departments, 44 municipalities, 262 districts (WGS84 lat/lon, elevations), national roads (CA-1, CA-2, CA-4), bridges, volcanoes, lakes, verified establishments directory (CONFIRMADO, PENDIENTE, etc.) | Fully available. Ground truth geographic data preserved; no fictitious coordinates presented as verified. |
| **Events & History** | `EventBus`, `EventLogRepository`, `SimulationEvent` | Full event log: tick, event type, source_human_id, target_human_id, location_id, importance, structured data payload | Fully available. Exposed in `/api/timeline` and streamed via `/api/events/stream`. |
| **Simulation Laboratory** | `SimulationLaboratory`, `BaseExperiment`, Phase A-H, Phase 04-13 Experiment suites | 70+ automated empirical experiments, hypotheses, validation thresholds, markdown/json report generators | Fully available. Exposed in `/api/laboratory`. |
| **Persistence** | `DatabaseManager`, SQLite repositories, WAL mode | State checkpoints, tick restoration, entity persistence | Fully available. Checkpoint creation and loading exposed via control API. |

---

## 2. DATA INSTRUMENTATION PLAN

### 2.1 What Data Is Available Directly
- Real-time simulation tick, day, hour, season, and climate variables.
- Complete individual attributes: physical health/energy/hunger/money, Big Five personality traits and drift, emotional mood and active charges, working and episodic memories, procedural skills.
- Cognitive decision traces: chosen action, expected utility, causal rationale, dominant factors, rejected alternatives.
- Real Salvadoran geography: WGS84 coordinates of 262 districts, 14 departments, 44 municipalities, verified establishments, roads, bridges, topography.
- Multi-dimensional social ties: relationship strengths, trust, affinity, familiarity.
- Historical event log in SQLite and in-memory event bus.

### 2.2 What Data Needs Instrumentation
1. **Simulation Control & Decoupling:**
   - Previous `SimulationRunner` ran synchronously in the calling thread.
   - We must provide a `SimulationController` that wraps `SimulationRunner` in a background worker thread with thread-safe controls (`play`, `pause`, `step`, `speed_multiplier`, `reset`, `checkpoint`).
   - Speeds: 1x (1 tick/sec), 10x (10 ticks/sec), 100x (100 ticks/sec), 1000x (unthrottled).
2. **Real-time Event Streaming:**
   - An asynchronous ring buffer subscribing to `EventBus` to push SSE events to connected clients at 10-20 Hz without blocking simulation ticks.
3. **Graph Neighborhood Traversal & Progressive LOD:**
   - Serializers that return filtered subgraphs (e.g. ego-networks of an individual or local knowledge neighborhoods) so that the browser is never overloaded with 10,000+ nodes simultaneously.
4. **Time-Series Aggregator:**
   - A ring buffer storing aggregate civilization metrics (population, average wealth, Gini coefficient, cultural retention, temperature) across historical ticks for instant chart rendering.

### 2.3 What Must NOT Be Invented
- Do not fabricate synthetic brain scans, EEG waves, or biological neural signals: functional subsystems are strictly computational analogues (Frontal=Executive/GOAP, Hippocampal=Memory retrieval, Limbic=Utility/Mood weighting, Temporal=Semantic graph, Parietal=Spatial path cost, Cerebellar=Procedural habit).
- Do not invent artificial geographic places or claim unverified establishments are verified. Real WGS84 coordinates from CNR/OSM are used, and validation states (`CONFIRMADO`, `PENDIENTE_VALIDACION`) are strictly displayed.
- Do not fabricate economic indicators: Gini coefficient, loan balances, enterprise cash, and commodity prices are calculated from actual simulated entities.

---

## 3. APPLICATION ARCHITECTURE SPECIFICATION

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   SALTBOR PHASE 1.3-V                                   │
│                        INTERACTIVE VISUAL SIMULATION ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                 BROWSER CLIENT (SPA)                                    │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                     SIMULATION CONTROL CENTER (Universal Topbar)                  │  │
│  │   [Play/Pause] [Step] [1x/10x/100x/1000x] [Tick: 142] [Day 2 08:30] [Pop: 20]     │  │
│  │   [Scenario: Baseline] [Seed: 42] [Save/Load] [Theme: Dark/Light] [SSE: Connected]│  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │ 10 EXPLORER PANELS (Tabbed / Contextual Routing)                                  │  │
│  │ 1. World Explorer (HTML5 Canvas 2D, El Salvador WGS84, LOD, Settlements, Paths)   │  │
│  │ 2. Individual Explorer (Dossier, Traits Radar, Mood, Memory Stream, Goals HTN)    │  │
│  │ 3. Cognitive Architecture (6 Subsystems Diagram, Decision Pipeline Trace)        │  │
│  │ 4. Knowledge Graph (Force Graph, Claims, Epistemic States, Provenance, Search)   │  │
│  │ 5. Social Network (Ego Graph, Relationship Types, Trust, ADESCO Communities)      │  │
│  │ 6. Civilization Dashboard (Time-Series Charts: Demography, Economy, Culture, Gini)│  │
│  │ 7. Economy & Resources (Markets, Commodity Prices, Enterprises, Loans, Fiado)     │  │
│  │ 8. Historical Timeline (Chronological Filterable Events, Entity Deep-Links)       │  │
│  │ 9. Simulation Laboratory (Interactive Experiment Runner, Scenarios, Benchmarks)   │  │
│  │ 10. Scientific Reports (Live Markdown/JSON Reports, Hypotheses, Evidence)         │  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
│                                           ▲                                             │
│               HTTP REST (JSON)            │            Server-Sent Events (SSE)         │
│               State on Demand             │            Real-time Ticks & Events         │
│                                           ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                        FASTAPI BACKEND & CONTROLLER LAYER                         │  │
│  │   - SimulationController (Background Thread, Rate Limiter, Checkpoint Manager)     │  │
│  │   - REST Endpoints (/api/status, /api/world, /api/individuals, /api/cognitive...) │  │
│  │   - SSE Event Stream (/api/events/stream, buffered ring buffer, auto-reconnect)   │  │
│  │   - Static Web Application Server (/ serves index.html, app.js, style.css)       │  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
│                                           ▲                                             │
│                                           │ Direct In-Memory Engine Binding             │
│                                           ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐  │
│  │                        EXISTING SALTBOR SIMULATION BACKEND                        │  │
│  │   SimulationRunner | SyntheticHuman | CognitiveBrainArchitecture | KnowledgeGraphs │  │
│  │   SocialNetworkEngine | RealGeographicEngine | CivilizationEngine | SQLite DB WAL │  │
│  └───────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. HARDWARE OPTIMIZATION STRATEGY (AMD Ryzen 8700G & Radeon 780M)

1. **Rendering Performance:**
   - HTML5 Canvas with dirty-rect or requestAnimationFrame tick loop.
   - Batch line drawings and arc paths to minimize Canvas context switches.
   - Dynamic Level of Detail (LOD):
     - Low zoom: render department polygons, major highway lines, volcano symbols, and aggregate population heatmap.
     - High zoom: render individual district nodes, secondary roads, verified establishments, and individual synthetic agents.
2. **Network & Memory Bandwidth:**
   - No transmitting all 20+ synthetic humans' complete memory trees on every tick.
   - Lightweight tick telemetry (~2 KB/tick over SSE) carries tick, current population count, latency, and new events.
   - Full individual dossiers and subgraphs are requested on-demand via REST when selected.
3. **Simulation Decoupling:**
   - The simulation engine runs in an isolated background thread.
   - If the browser client drops frames or sleeps, the simulation engine is unaffected.
   - Frontend reconnection handles dropped SSE connections transparently with automatic exponential retry.
