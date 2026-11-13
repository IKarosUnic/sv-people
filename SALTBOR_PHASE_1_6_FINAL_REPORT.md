# SALTBOR — PHASE 1.6 FINAL REPORT
## Human Life, World Interaction, Geographic Intelligence and Open-Ended Society

**Date:** 2026-11-13
**Baseline:** Phase 1.5, `479 passed in 17.46s`
**Final state:** `526 passed` in `python -m pytest -q` (47 new tests)
**Machine:** Ryzen 7 8700G / Radeon 780M / 32 GB / Windows 11 / Python 3.14.5

---

## 0. Status vocabulary used in this document

These terms are **not** interchangeable and are used as defined here:

| Term | Meaning |
| --- | --- |
| **IMPLEMENTED** | Code exists in the repository and is importable. |
| **INTEGRATED** | Wired into `SimulationRunner` / `ExtensionRuntime` / API / UI and exercised in a running simulation. |
| **TESTED** | Covered by automated tests that were executed and passed. |
| **VALIDATED (conditions)** | An experiment produced evidence for the claim under the stated seeds, populations and horizons — no more. |
| **EXPERIMENTAL** | Works in the implemented path; behaviour or calibration is not established. |
| **NOT IMPLEMENTED** | Absent. No stub, no placeholder endpoint, no empty class. |

A passing test proves the mechanism runs; it does not prove the social or
biological claim is correct.

---

## 1. What was delivered in this phase

Five substantive additions, each chosen because the audit (see
`SALTBOR_PHASE_1_6_AUDIT.md`) showed a genuine gap:

1. **Dependency-free OpenStreetMap ingestion** → `saltbor/datasets/gis/shapefile_reader.py`,
   `pipeline.py`, rewritten `geofabrik_extractor.py`. 151,251 real features with
   per-feature provenance.
2. **Road routing over real geometry** → `saltbor/world/geographic/osm_router.py`
   (walk/drive, one-way, explicit failure reasons, no teleporting).
3. **Perception engine** → `saltbor/cognition/perception/{models,engine}.py`
   (acuity, detection, clarity-gated detail, interpretation, memory encoding,
   testimony).
4. **World/human integration** → perception round in `ExtensionRuntime`, 5 new
   event types, checkpoint persistence, perception in dossier and API.
5. **Experiment suite EXP_16_A…T** → `saltbor/simulation/experiments/phase16_experiments.py`,
   61 hypotheses, all executed, results reported honestly below.

Everything else in the specification that already existed was **extended or
exercised, not duplicated**: health, romance, family, caregiving, misfortune,
causal graph, economy, institutions, LOD, language and culture engines were left
in place.

---

## 2. Geographic foundation (summary; details in `SALTBOR_PHASE_1_6_OSM_GEOGRAPHY.md`)

- Source: Geofabrik `el-salvador-latest-free.shp.zip`, ODbL 1.0, EPSG:4326.
- Ingest: **151,251 features / 30.6 s** → `geography.sqlite` (184 MB) + manifest.
  - roads 121,344 · landuse 10,887 · pois 8,011 · waterways 4,433 · places 2,657 ·
    water 1,437 · buildings **989 (PARTIAL, pilot bbox)** · transport 897 ·
    adminareas 474 · natural 122.
- Buildings are honestly partial: `is_partial=true` + `coverage_bbox` recorded in
  the manifest and exposed by the API.
- Derived dataset and the 399 MB download are git-ignored and reproducible with
  `python -m saltbor.datasets.gis.pipeline --download …`.
- CNR viewer assessed and **NOT IMPLEMENTED** as a source: no documented public
  API contract and no explicit reuse license were establishable. No CNR
  geometry is redistributed.

---

## 3. Perception: the epistemic boundary — IMPLEMENTED, INTEGRATED, TESTED

`PerceptionEngine` runs every 2 ticks (`perception_interval_ticks = 2`) inside
`ExtensionRuntime`, over at most 6 co-located others per agent per round.

Mechanism (all parameters explicit in `models.py`):

```
detection_p = acuity(channel) × signal × exp(−distance/scale(channel, rain, night)) × attention × walls
clarity     = 0.25 + 0.55·p + 0.20·visual − rain_penalty + N(0, 0.08)
```

- `acuity` depends on age, fatigue, health, stress, time of day, rainfall,
  indoor/outdoor.
- **A stranger is never identity-resolved.** Only a person already in the
  observer's `human_associations` can be named; `identity_threshold` is 0.30 for
  a known person and effectively unreachable (1.01) for a stranger.
- Interpretation attributes a claim to `self` or `external`, records the biases
  applied (`threat_bias`, `optimism_bias`, `prior_based_inference`,
  `testimony_trust`, …) and always offers alternative readings.
- Memory encoding is salience-gated; below threshold nothing is stored.
- Testimony (`receive_report`) is a distinct channel with confidence capped by
  credibility × trust, registered in `known_entities` as `source: testimony`.
- Randomness is derived from `blake2b(seed, identity.serial, target, tick)`, not
  from `uuid4`, so the same seed reproduces the same perceptions across process
  runs.

Verified in a live run: 20 humans × 12 ticks → 226 observations, 24
misunderstandings, 51 memories encoded.

**Deliberately not implemented:** vision, audio or language-model perception.
Structured detection keeps the cost at ~0.25 ms per agent-tick.

---

## 4. World–human feedback (existing engine, now measured)

`saltbor/world/interaction` already modelled environmental impact; Phase 1.6
exercised it quantitatively instead of rewriting it:

- Waste accumulates at `population × 0.40 kg / 24 h`.
- River pollution only begins above **200 kg of accumulated waste**.
- Community restoration reduces waste and improves the water source.
- 300 residents × 60 days crosses the threshold; 0 and 10 residents do not.

This is why EXP_16_M/N are supported *and* why their effect sizes are small at
pilot scale — the mechanism is threshold-based, and that limitation is recorded
(§9).

---

## 5. Persistence and migrations

| Change | Migration |
| --- | --- |
| New `geographic_features`, `dataset_provenance`, `layer_provenance` tables | Created by `pipeline._ensure_schema()`; rebuild via CLI |
| Composite spatial index `idx_features_layer_lat_lon` | `CREATE INDEX IF NOT EXISTS …` in `_ensure_schema()`; applied in place to existing DBs (0.43 s) + `ANALYZE` |
| Perception state in checkpoints | `PerceptionEngine.to_dict()/load_dict()`; added to the extension checkpoint document, backward compatible (`data.get("perception")` is optional) |
| Perception buffer unbounded growth | `PerceptionSnapshot.record()` keeps the last 40 observations/interpretations; totals remain exact |
| New event types | Additive `EventType` members + `EVENT_CATEGORIES`; old checkpoints replay unchanged |

No destructive migration was required. Old databases open and run; the
simulation simply reports `perception.available` with an empty state until the
next tick.

---

## 6. API and UI

New endpoints (all covered by tests in `tests/test_visualization/test_phase16_api.py`):

| Endpoint | Returns |
| --- | --- |
| `GET /api/perception/overview` | Aggregate detection/misunderstanding/memory counters |
| `GET /api/individuals/{uid}/perception` | Acuity with provenance, recent observations, known entities |
| `GET /api/geography/manifest` | Dataset + layer provenance, license, attribution, partial flags |
| `GET /api/geography/features` | Bounded bbox query, optional geometry |
| `GET /api/geography/route` | Real-network route with distance, duration, provenance |
| `GET /api/geography/ecological_profile` | Landuse/water/vegetation context |

`GET /api/individuals/{uid}` (dossier) now includes a `perception` block.

Frontend (`saltbor/visualization/web/app.js`): perception panel in the individual
inspector; OSM attribution badge driven by `/api/geography/manifest`;
`#gis-layer-summary` shows per-layer counts and flags partial layers.

**Not visually verified.** No browser was opened in this phase; the JS changes
are exercised only by the asset tests. This is a limitation, not a claim.

---

## 7. Experiment suite EXP_16_A … EXP_16_T

Reproducible with:

```bash
python -m saltbor.simulation.experiments.phase16_experiments   # or via the package
python -m pytest tests/test_experiments/test_phase16_experiments.py -q
```

All 20 experiments execute: **61 hypotheses — 58 supported, 2 inconclusive, 1 rejected.**
Machine-readable results: `docs/reports/phase16_experiments.json`.

| ID | Subject | Seeds | Principal measurement | Outcome |
| --- | --- | --- | --- | --- |
| A | Perception without omniscience | 5 | known entities per observer, misses | SUPPORTED |
| B | Different interpretations of one event | 4 | claim, biases, valence divergence | SUPPORTED |
| C | Development across life stages | 5 | acuity, attention budget by age | SUPPORTED |
| D | Imperfect decisions / bias | 4 | prior-based inference, misunderstandings | SUPPORTED |
| E | Object/physical consequences | 4 | monotone travel cost, rain penalty | SUPPORTED |
| F | Romantic formation | 5 + control | formation rate, incompatible-pair control | SUPPORTED |
| G | Infidelity, trust, outcomes | 4 | trust drop, separations | H1/H2 SUPPORTED, **H3 INCONCLUSIVE** |
| H | Illness, treatment, recovery | 4 | residual severity, ticks to resolution (20.75 vs 23.0) | H1/H3 SUPPORTED, **H2 REJECTED** |
| I | Environmental exposure and health | 4 | incidence vs water quality | H1/H2 SUPPORTED, **H3 INCONCLUSIVE** |
| J | Accidents and geographic risk | 4 | rain 0.052 vs dry 0.005 over 1200 trips/arm | SUPPORTED |
| K | Family support and caregiving | 4 | child hunger/energy, caregiver cost | SUPPORTED |
| L | Institutional access and inequality | 3 | rich 18 vs poor 0 successful consultations of 60; 42 capacity rejections (fee $12) | SUPPORTED |
| M | Activity and degradation | 4 | waste kg by population, river pollution | SUPPORTED |
| N | Activity and recovery | 4 | waste removed, water index improved vs control | SUPPORTED |
| O | Causal cascades | 4 | chain depth 3 from rainfall to treatment | SUPPORTED |
| P | Individual trajectories | 3 | identical replay, internal divergence | SUPPORTED |
| Q | Multi-generational continuity | 3 | 3 generations preserved | SUPPORTED |
| R | Geographic navigation | 4 | path ≥ straight-line, walk slower than drive, unreachable reported | SUPPORTED |
| S | Large population LOD/performance | 2 | 3.83 percepts/agent/round at 100 and 400 agents; cadence halves cost | SUPPORTED |
| T | Integrated world–human run | 2 | 96 ticks, 1,125 observations, 1,255 events, reload with 20 individuals | SUPPORTED |

### 7.1 Honest negative and inconclusive results

- **EXP_16_H / H2 REJECTED — "treatment does not guarantee full recovery."**
  Under the tested conditions (waterborne illness, 120-tick horizon, 4 seeds) every
  treated patient recovered. Treatment shortened illness (20.75 vs 23.0 ticks) but
  no treated case remained unresolved, so the hypothesis is rejected rather than
  reframed. A longer horizon or a more severe pathogen would be needed to test
  non-recovery; that is future work, not a result.
- **EXP_16_G / H3 INCONCLUSIVE — "outcomes are not uniform."** All 4 couples
  separated after discovery. The sample is too small and the parameter set too
  uniform to claim heterogeneity in outcomes; we report inconclusive instead of
  tuning probabilities until it passes.
- **EXP_16_I / H3 INCONCLUSIVE — "clean water is not zero-risk."** The current
  risk function returns zero below a cleanliness threshold: a deterministic
  boundary, not a probabilistic model. This is a real modelling limitation (§9).

Two further defects were found and fixed **in the experiments, not the engines**:
EXP_16_L had used a facility with `fee_usd = 0.0` (making affordability inert) and
reused a full facility across arms; EXP_16_S compared arms on a shared population
whose memory had already grown, and counted cumulative instead of per-round
percepts. Both corrections are documented in code comments.

---

## 8. Tests

```
python -m pytest -q   →   526 passed in 37.87s
```

New coverage:

| File | Tests | What it proves |
| --- | --- | --- |
| `tests/test_cognition/test_perception.py` | 11 | No omniscience; acuity factors; clarity gating; strangers unidentified; known persons resolved; divergent interpretations; salience-gated memory; testimony channel; determinism; snapshot/engine round-trip |
| `tests/test_gis/test_osm_pipeline.py` | 11 | SHP/DBF parsing on a synthesized bundle; polygon closure; class normalization; provenance fields; partial-coverage flags; missing-source no-crash; grid routing; unreachable reasons; real extract readable |
| `tests/test_experiments/test_phase16_experiments.py` | 22 | Every experiment executes and reports; 20-ID coverage; whole-suite run |
| `tests/test_visualization/test_phase16_api.py` | 3 | Perception endpoint contract; dossier block; geography manifest/features/route with provenance |

The GIS tests build their own shapefile fixtures, so they do not depend on the
399 MB download; a separate test inspects the real extract when present.

---

## 9. Sustained performance (measured, not estimated)

Script: `scripts/benchmark_phase16.py`; raw data:
`docs/reports/phase16_benchmark.json`. Each run: 20 warm-up ticks, then 100
measured ticks of a continuously running simulation with
`checkpoint_interval_ticks = 96`.

| Population | mean ms/tick | p50 | p95 | max | ticks/s | ms/agent/tick | RSS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 50 | 26.7 | 20.7 | 44.6 | 523.4 | 37.5 | 0.53 | 108 MB |
| 200 | 151.8 | 111.7 | 244.1 | 3,825.0 | 6.6 | 0.76 | 230 MB |

Geographic queries: `nearest_road` **0.23 ms/call** (500/500 hits),
`features_in_bbox` 500 features ≈ 127 ms (full-scan predicate; see §10).

Interpretation, stated plainly:

- Steady-state cost is roughly **0.53–0.76 ms per agent per tick** and scales
  near-linearly (0.53 → 0.76 between 50 and 200 agents; 0.99 in the earlier
  three-population run).
- The `max` column is a **checkpoint stall**, not simulation work: one checkpoint
  per 96 ticks serializes the whole extension state. Checkpoint work was reduced
  after this phase's first report (measured on the same 200-agent state, 5 runs):
  median **3.08 s → 2.49 s** and payload **20.75 MB → 11.71 MB** after batching
  memory upserts, compacting retained percepts and making the outer checkpoint
  transaction authoritative. It remains the largest obstacle to "thousands of
  agents": the residual cost is writing ~26,600 episodic rows per checkpoint.
  Incremental (dirty-only) persistence is still **NOT IMPLEMENTED**.
- Run-to-run variance on this laptop is significant (the same 50-agent
  configuration measured 28.0, 32.3 and 54.1 ms/tick across three runs). Treat
  these as order-of-magnitude figures with a stable per-agent slope, not as
  benchmarks with 1 % precision.
- Performance improvements delivered this phase: `nearest_road` 136 ms → 0.23 ms
  (composite index + progressive widening); perception buffers bounded at 40
  entries.

---

## 10. Known limitations (explicit)

1. **Checkpoint stalls.** Reduced from a 3.08 s to a 2.49 s median at 200 agents,
   but still ~2.5 s per simulated day and growing with population (10.7 s at 400
   agents in the earlier run). Incremental/dirty-only persistence is **NOT
   IMPLEMENTED**; the remaining cost is the row volume of episodic memory.
2. **No thousands-of-agents validation.** Largest sustained measurement here is
   400 agents; the LOD machinery exists (`population/lod.py`,
   `CognitiveLODManager`) but Phase 1.6 did not validate it at 10k+.
3. **Geography is country-wide for roads but pilot-only for buildings**, and
   routes ignore closures, congestion and surface conditions.
4. **`features_in_bbox` is a full scan** (~127 ms for 500 features) because it
   tests bbox intersection with `NOT (…)`; the API is fine at pilot scale and
   will not be at national scale.
5. **Map rendering is implemented but visually unverified.** The MapLibre map now
   loads real OSM roads (zoom ≥ 12) and buildings (zoom ≥ 15.5) from
   `/api/geography/geojson`, refreshing on `moveend` with a debounce, and shows
   the count in `#gis-osm-rendered`. No browser was opened: syntax, API contract
   and asset tests pass, but the rendered result has **not** been inspected.
   The curated legacy GIS layers still sit above the OSM layers.
6. **Objects and physical interaction** (spec §11) exist as
   `saltbor/world/interaction/` but are **not imported by `SimulationRunner`**;
   Phase 1.6 did not integrate an object model. EXP_16_E measures movement cost
   and physical consequences, not object manipulation.
7. **Institutions** have state (`institutions/governance.py`, `legal/`, `model.py`,
   imported by the runner) but no Phase 1.6 experiment covers decision-making,
   corruption, or resource allocation.
8. **Language** (`social/language/contextual_dialogue.py`, offline, wired into the
   runner) was not extended for Salvadoran register/vocabulary variation in this
   phase.
9. **Ecology** is represented through landuse/water tags and the waste/pollution
   indices; no flora/fauna population dynamics exist.
10. **Disease model** is coarse: transmission and recovery are parameterized, not
    calibrated against epidemiological data; clean water yields a hard zero-risk
    boundary (EXP_16_I H3).
11. **UI changes are unverified visually** (§6).
12. **CNR is not ingested** (§2).
13. Experiments use small samples (3–5 seeds, tens of agents); they are
    demonstrations of mechanism, not statistical claims.

---

## 11. Scientific assumptions and evidence register

| # | Assumption | Where it lives | Evidence status |
| --- | --- | --- | --- |
| 1 | Visual detection decays exponentially with distance, with a scale that shrinks at night and in rain | `perception/models.py` (`VISUAL_SCALE_*`, `RAIN_VISUAL_PENALTY`) | **Modelled, not calibrated.** Order-of-magnitude values chosen for plausibility; no psychophysics dataset was used |
| 2 | Familiarity lowers the clarity needed to recognise a person | `identity_threshold` 0.30 vs 1.01 | Modelled; consistent with face-recognition literature qualitatively, not fitted |
| 3 | Interpretation is biased by threat, optimism and priors | `interpret()` | Modelled; biases are named and recorded per observation |
| 4 | Salience gates memory encoding | `encode()` threshold | Modelled; consistent with the existing Phase 1.2 memory thresholds |
| 5 | Testimony is discounted by source credibility × trust | `receive_report()` | Modelled |
| 6 | Walking 5 km/h, driving by road class, one-way tags respected | `osm_router.py` | Class speeds are engineering assumptions; OSM tags are evidence |
| 7 | Industrial/residential waste 0.40 kg/person/day, river damage above 200 kg | `world/interaction` | Assumption; order-of-magnitude consistent with municipal waste figures, not locally measured |
| 8 | Treatment shortens illness but does not guarantee recovery | `health/engine.py` | Supported in direction (EXP_16_H H1); the "not guarantee" part was **not** observed at the tested horizon |
| 9 | Health access depends on fee, distance and capacity | `seek_medical_treatment()` | Validated with a $12 fee (rich 18/60 vs poor 0/60; 42 capacity rejections) |
| 10 | Accidents are more frequent in rain | `accidents/`, `misfortune` | Supported (0.052 vs 0.005 over 1,200 trips per arm) |
| 11 | Perception randomness must derive from stable identity, not `uuid4` | `PerceptionEngine._stable_id` | Validated by EXP_16_P (identical replay across process runs) |
| 12 | OSM `fclass` → SALTBOR class mapping is faithful | `pipeline.LAYER_SPECS` | Inspection only; no independent ground truth |
| 13 | Geofabrik extract is a valid, current OSM snapshot | manifest `acquired_at` | Download provenance recorded; freshness depends on the download date |

---

## 12. Deliverable ledger

| # | Required deliverable | Status |
| --- | --- | --- |
| 1 | Forensic architecture audit | **DELIVERED** — `SALTBOR_PHASE_1_6_AUDIT.md` |
| 2 | Updated architecture diagram | **DELIVERED** as an ASCII dependency map in the audit (§2) and this report (§13). No graphical diagram |
| 3 | Geographic ingestion and normalization pipeline | **IMPLEMENTED, INTEGRATED, TESTED, VALIDATED** (151,251 features) |
| 4 | OpenStreetMap integration documentation | **DELIVERED** — `SALTBOR_PHASE_1_6_OSM_GEOGRAPHY.md` |
| 5 | CNR reference assessment | **DELIVERED** (assessment); ingestion **NOT IMPLEMENTED** |
| 6 | World–human interaction systems | Perception **IMPLEMENTED/INTEGRATED/TESTED**; environment feedback **pre-existing, now measured**; object interaction **NOT INTEGRATED** |
| 7 | Updated backend and API | **IMPLEMENTED, TESTED** (6 new endpoints + dossier block) |
| 8 | Updated interactive frontend | **IMPLEMENTED** — panels, attribution, layer summary, and real OSM roads/buildings on the map; visual verification **not performed** |
| 9 | Persistence migrations | **IMPLEMENTED, TESTED** (additive schema + in-place index migration) |
| 10 | Experiment suite | **IMPLEMENTED, EXECUTED** (20 experiments, 61 hypotheses, results recorded) |
| 11 | Unit and integration test reports | **DELIVERED** — 526 passed, new-coverage table in §8 |
| 12 | Sustained performance benchmarks | **DELIVERED** — §9 + `docs/reports/phase16_benchmark.json` |
| 13 | Known limitations | **DELIVERED** — §10 |
| 14 | Assumptions and evidence register | **DELIVERED** — §11 |
| 15 | Updated architecture documentation | **DELIVERED** — §13, plus README section |
| 16 | Commit identifier and change summary | **DELIVERED** — §14 |

Specification sections that were **not** addressed by new work in this phase
(they were pre-existing and remain so): §11 objects, §14 institutional
behaviour beyond existing engines, §15 ecology, §19 LOD validation at scale,
§20 map rendering. They are named here rather than silently counted as complete.

---

## 13. Architecture after Phase 1.6

```
SimulationRunner (clock, population, environment, checkpoint)
 ├── PopulationFactory → SyntheticHuman (identity.serial, personality, memory, emotions)
 ├── Knowledge graphs (global / collective / procedural / hypothesis)
 ├── SocialEngine, MultiDimensionalRelationship, reputation, conflict, dialogue
 ├── Economy (business, credit, commodity, mobility), Culture (festival, transmission)
 ├── Institutions (governance, legal, model)
 ├── LifeEventsCoordinator (aging, gestation, mortality, inheritance, bereavement)
 ├── ExtensionRuntime
 │    ├── romance · infidelity · misfortune · health · caregiving · world interaction
 │    └── PerceptionEngine  ← NEW (every 2 ticks, ≤6 others/agent)
 │           ├── acuity (age, fatigue, health, stress, night, rain, indoor/outdoor)
 │           ├── detect → clarity → interpret → encode to memory
 │           └── receive_report (testimony / gossip)
 ├── IngestedGeography  ← NEW  (read-only SQLite, provenance per feature)
 │    └── OSMRoadNetwork  ← NEW (real topology, walk/drive, explicit failures)
 └── Visualization API (perception, geography, dossier) → web UI panels
```

---

## 14. Change summary

New files:

- `saltbor/datasets/gis/shapefile_reader.py`
- `saltbor/datasets/gis/pipeline.py`
- `saltbor/cognition/perception/{__init__,models,engine}.py`
- `saltbor/world/geographic/osm_router.py`
- `saltbor/simulation/experiments/phase16_experiments.py`
- `scripts/benchmark_phase16.py`
- `tests/test_cognition/test_perception.py`
- `tests/test_gis/test_osm_pipeline.py`
- `tests/test_experiments/test_phase16_experiments.py`
- `tests/test_visualization/test_phase16_api.py`
- `tests/test_gis/test_geojson_viewport.py` (viewport GeoJSON + API contract)
- `SALTBOR_PHASE_1_6_AUDIT.md`, `SALTBOR_PHASE_1_6_OSM_GEOGRAPHY.md`, this report
- `docs/reports/phase16_benchmark.json`, `docs/reports/phase16_experiments.json`

Modified:

- `saltbor/datasets/gis/geofabrik_extractor.py` (rewritten on the new reader — it previously failed to import)
- `saltbor/cognition/memory/engine.py` (string → UUID normalisation for associations)
- `saltbor/persistence/repositories.py` (batched memory upserts, shared SQL constants)
- `saltbor/persistence/database.py` (real nested-transaction depth tracking)
- `saltbor/datasets/gis/pipeline.py` (`geojson()`, streamed viewport query, spatial index)
- `saltbor/cognition/perception/models.py` (bounded buffer, compact checkpoint form)
- `saltbor/events/types.py` (5 perception event types + categories)
- `saltbor/simulation/runner.py` (perception engine)
- `saltbor/simulation/extension_runtime.py` (perception round, stats, checkpoint)
- `saltbor/simulation/experiments/__init__.py` (Phase 16 registration)
- `saltbor/visualization/api.py` (perception + geography endpoints, dossier)
- `saltbor/visualization/web/app.js` (perception panel, OSM attribution, layer summary)
- `.gitignore` (`saltbor/datasets/gis/ingested/`)

**Commit:** `99224c056591d8ed0e7ee8ce25ca84eb26e5f7c9`
(`feat(phase1.6): OSM geographic foundation, perception engine and EXP_16_A..T`).
This documentation update is recorded in the commit that follows it; the
implementation commit above is the one validated by `526 passed`.

---

## 15. Reproduction

```bash
# tests
python -m pytest -q

# geographic data (first time downloads ~399 MB)
python -m saltbor.datasets.gis.pipeline --download \
    --buildings-bbox -89.2020 13.6930 -89.1860 13.7040 --acquired-at 2026-11-13

# experiments
python -m pytest tests/test_experiments/test_phase16_experiments.py -q

# sustained benchmark
python scripts/benchmark_phase16.py --ticks 100 --populations 50,200
```
