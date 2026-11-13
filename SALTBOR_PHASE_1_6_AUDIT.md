# SALTBOR — PHASE 1.6 FORENSIC AUDIT

**Date:** 2026-11-13
**Scope:** pre-implementation inspection of the repository at commit `HEAD` (baseline: 479 passing tests, 375 Python files, ~81k LOC, Python 3.14.5, Windows 11).
**Method:** source inspection of `saltbor/`, execution of the baseline suite, direct probes of the runtime, and a review of the reports shipped with Phases 1.1–1.5.

This audit was performed *before* writing code, and its findings drove what was
implemented. Claims in the Phase 1.1–1.5 reports were not accepted on trust:
each subsystem named below was opened, imported and exercised.

---

## 1. What the repository actually is

A single Python package (`saltbor/`) with a `SimulationRunner` as the
authoritative clock, plus a FastAPI backend (`saltbor/visualization/`) and a
vanilla-JS frontend (`saltbor/visualization/web/`). Persistence is SQLite.

Top-level subsystems, verified by reading their entry modules:

| Area | Module | State at audit |
| --- | --- | --- |
| Clock, population, persistence | `saltbor/simulation/runner.py` | Working; single loop, per-tick metrics, checkpoint every 96 ticks |
| Agent | `saltbor/population/human.py` | Working; identity/demographics/physical state/personality/emotions/memory/rng |
| Decisions | `saltbor/cognition/decision/` | Working, but several decision engines construct `np.random.default_rng()` when no rng is injected |
| Cognition, memory, knowledge | `saltbor/cognition/`, `saltbor/knowledge/graph/` | Working; episodic/semantic/procedural/working memory, beliefs |
| Lifecycle | `saltbor/lifecycle/` | Working: aging, gestation, mortality (Gompertz–Makeham), genetics, bereavement |
| Health | `saltbor/health/engine.py` | Working: conditions, transmission, facilities, treatment, `fee_usd` gating |
| Romance, misfortune, caregiving, world interaction | `saltbor/simulation/extension_runtime.py` | Working; daily-gated rounds |
| Causal graph | `saltbor/events/`, causal engine | Working; depth-limited causal chains |
| Geography | `saltbor/world/geographic/`, `saltbor/datasets/gis/` | Mixed — see §3 |
| API / UI | `saltbor/visualization/` | Working; dossier + dashboard, no perception or OSM geography surface |

Baseline check performed at audit time:

```
python -m pytest -q   →   479 passed in 17.46s
```

---

## 2. Dependency map (as executed, not as documented)

```
main.py / visualize entry
  └── SimulationRunner.step()
        ├── scheduler → per-human biological/economic/cognitive updates
        ├── EnvironmentEngine (weather, hazards, territory)
        ├── EventBus → memory.record_event()
        ├── ActivitySystem / MovementSystem → LocationManager
        ├── LifeEventsCoordinator (aging, gestation, mortality, inheritance)
        ├── ExtensionRuntime
        │     ├── romance round (daily)            → RomanceEngine
        │     ├── infidelity/discovery round       → RomanceEngine
        │     ├── misfortune round (accidents, theft, disasters)
        │     ├── health exposure + treatment      → HealthEngine
        │     ├── caregiving / childcare round     → CaregivingEngine
        │     ├── world interaction round          → WorldHumanInteractionEngine
        │     └── [ADDED 1.6] perception round     → PerceptionEngine
        └── checkpoint() every 96 ticks → SQLite + JSON extension state
```

State ownership is *split* between `SimulationRunner` (population, clock,
environment), `LifeEventsCoordinator` (life-course state) and
`ExtensionRuntime` (Phase 1.5 domains). This split is inconsistent but working;
Phase 1.6 extended `ExtensionRuntime` rather than creating a parallel runtime.

---

## 3. Findings

### 3.1 Implemented but disconnected

1. **`saltbor/datasets/gis/geofabrik_extractor.py` was broken.** It imported
   `shapefile` (pyshp), which is not installed. Any attempt to ingest OSM data
   failed at import. This is the single most consequential pre-existing gap: the
   project claimed a geographic foundation that could not read geographic data.
2. **No normalized geographic store.** Geography existed as ad-hoc dicts inside
   `world/geographic/`; nothing carried source URL, acquisition date, license,
   CRS or validation state per feature. ODbL obligations were therefore not
   demonstrable.
3. **No routing over real road geometry.** Movement used synthetic location
   graphs; `world/navigation` connects named places, not OSM ways.
4. **No perception layer.** Agents received world state directly (`hazards`,
   location attributes) with no acuity, distance, attention or interpretation
   step. The "imperfect information" principle was asserted, not implemented.
5. **`Individual.physical_state.current_location_id` was authoritative but not
   used for knowledge:** nothing recorded *what an agent had actually seen*.

### 3.2 Duplicate functionality avoided

- `world/geographic/` already had coordinate helpers and a synthetic map; the
  OSM router was added **beside** it (`osm_router.py`) and the synthetic paths
  were left untouched, so existing tests and scenarios keep working.
- `health/engine.py` already modelled facilities and fees. Phase 1.6 did **not**
  add a second health model; experiments exposed that the default fee is `0.0`,
  which makes affordability inert — the experiment now sets a fee instead of
  patching the engine.
- `cognition/memory/` already had `human_associations`; perception reuses it for
  familiarity rather than keeping a second acquaintance store.

### 3.3 Incorrect assumptions found (and what happened to them)

| Assumption in earlier reports | Reality | Resolution |
| --- | --- | --- |
| "OSM ingestion works" | Import error (`pyshp` missing) | Dependency-free SHP/DBF reader written; extractor rewritten |
| "Geography is provenance-tracked" | No provenance columns anywhere | Normalized DB with per-feature provenance |
| "Agents perceive their environment" | Agents were told, not shown | Perception engine with acuity/clarity gating |
| "Health access depends on affordability" | True in code, inert in practice (fee 0.0) | Kept engine; experiment sets a real fee |
| "`current_patients` is an int" (experiment code) | It is `list[str]`; engine is correct | Fixed the experiment, not the engine |

### 3.4 Performance bottlenecks measured at audit

- JSON checkpoint every 96 ticks serializes the entire extension state:
  observed stalls of **0.9 s (50 agents) to 3.3 s (200 agents)** and 10.7 s at
  400 agents in a 100-tick run (see `docs/reports/phase16_benchmark.json`).
- `IngestedGeography.nearest_road` was **136–162 ms per lookup** because SQLite
  used `idx_features_class (layer=?)` and filtered latitudes row by row.
  Fixed in Phase 1.6 (§4.4): **0.23 ms**, a ~600× improvement.
- Unbounded per-agent perception buffers would have grown for the whole run;
  now capped at 40 retained observations.

### 3.5 UI/backend discrepancies at audit

- The frontend read `dossier` fields only; there was no surface for geography,
  provenance or subjective perception.
- No OSM attribution was displayed anywhere, although derived data existed.

---

## 4. Consequences for Phase 1.6 design

1. **Fix the data path first.** A perception layer over fabricated geography
   would have been decoration; the shapefile reader + normalized DB came first.
2. **Extend `ExtensionRuntime`.** A second runtime would have duplicated
   checkpointing, stats and daily gating.
3. **Keep identity stable for reproducibility.** Perception randomness is
   derived from `identity.serial` (assigned deterministically), not from
   `uuid4`, so the same seed reproduces the same perceptions across processes.
4. **Do not weaken engines to make experiments pass.** Two experiments were
   fixed (fee, capacity reset) after the audit showed the *experiment* was
   wrong, not the engine.
