# SALTBOR — PHASE 1.5 EXTENSION
## World–Human Interaction, Complete Life Events & Emergent Human Society
### Validation, Assumptions & Limitations Report

**Date:** November 2026
**Scope:** Bidirectional territory ↔ human coupling, biological life and health, accidents and disasters, romance and family, psychological experience, social conflict and solidarity, socioeconomic trajectories, geographic grounding of events, causal event graph, observability, and multi-seed statistical validation.

---

## 1. What is actually implemented

| Domain | Module | Live in tick loop |
| :--- | :--- | :--- |
| Unified world–human interaction, territory provenance | `saltbor/world/interaction/world_human_engine.py`, `environmental_hazards.py` | `ExtensionRuntime.sync_environment`, `_exposure_round`, `_daily_life_round` |
| Health conditions, contagion, facilities | `saltbor/health/engine.py`, `health/models.py` | `ExtensionRuntime.step_individual`, `_airborne_round`, `_treatment_round` |
| Accidents, disasters, theft | `saltbor/accidents/engine.py`, `accidents/models.py` | `_commute_round`, `_work_round`, `_domestic_round`, `_theft_round`, `trigger_contextual_disaster` |
| Romance, jealousy, infidelity, heartbreak | `saltbor/social/romance/engine.py`, `models.py` | `_romance_round`, `step_heartbreak_recovery` |
| Family, caregiving, births/deaths, households | `saltbor/lifecycle/life_events.py`, `lifecycle/family/caregiving.py` | `_daily_life_round` |
| Causal DAG with ancestor/consequence inspection | `saltbor/events/causal_graph.py` | every extension engine emits into it |
| Orchestration & checkpointing | `saltbor/simulation/extension_runtime.py`, `runner.py` | `ExtensionRuntime.step`, `to_dict`/`load_dict` |
| Observability | `saltbor/visualization/api.py`, `web/` | `/api/health/facilities`, `/api/romance/relationships`, `/api/family/overview`, `/api/accidents/recent`, `/api/environment/hazards`, `/api/events/causal/recent`, `/api/timeline` |

The runner creates the engines (`health_engine`, `misfortune_engine`, `romance_engine`, `world_interaction`, `family_caregiving`) and calls `extension.step_individual()` per human plus `extension.step()` per tick. No extension event is generated outside a state transition: every emitted `SimulationEvent` is written after the corresponding mutation in the same call.

### Geographic provenance policy

`WorldHumanInteractionEngine.classify_object()` returns exactly one of:

1. `REAL_WORLD_GEOGRAPHIC` — rivers, lake, hill, central park.
2. `VERIFIED_REAL_ESTABLISHMENT` — market, comedor, health unit, municipality.
3. `SIMULATED_ESTABLISHMENT` — tienda, workshop, pupusería, clinic.
4. `SYNTHETIC_BUILDING` — houses, mesón, shelter (the default).
5. `TEMPORARY_ENVIRONMENTAL_OBJECT` — flood pool, landslide, standing water.

Event payloads carry `coordinate_provenance` (`verified_facility` / `synthetic_local_map`) so a UI marker never implies a verified real address for a simulated object. Unregistered IDs default to `SYNTHETIC_BUILDING`, never to “real”.

---

## 2. Mechanism parameters: calibrated vs scenario

Every number below is an explicit simulation parameter, not a measurement of Suchitoto. The right-hand column states which ones are anchored to published/observable ranges and which are invented scenario values requiring calibration.

| Parameter | Value | Status |
| :--- | :--- | :--- |
| Baseline traffic-incident risk per modelled trip | 0.01 | Scenario assumption |
| Rain contribution to road risk | `min(0.15, rainfall / 40 × 0.15)` | Ordinal shape from wet-pavement literature; magnitude invented |
| Fatigue contribution (below 50 % energy) | `(0.50 − energy) × 0.25` | Scenario assumption |
| Per-trip risk cap | 0.35 | Scenario guardrail |
| Runtime commute risk scale | 0.15 | Calibrated so ordinary days are not dominated by accidents |
| Workplace injury risk | `hazard × 0.04 × (3 if energy < 0.25)` | Ordinal fatigue effect supported; magnitude invented |
| Occupational hazard weights | 0.08 (teacher) – 0.90 (construction) | Ordinal from ILO-style sector hazard ordering |
| Domestic incident risk | `0.0025 + (age−55)×0.0012 + (0.35−energy)×0.05 + (0.75−quality)×0.035` | Age/dwelling gradient supported; magnitudes invented |
| Waterborne illness per drink | `(1 − cleanliness) × 0.40` | Dose–response shape plausible; magnitude invented |
| Airborne per-contact per-tick | `transmission_rate × (1 − health×0.4) × 0.35` | Simplified Wells–Riley-like structure, **not** a calibrated epidemiological model |
| Respiratory transmission_rate / incubation | 0.45 / 4 ticks | Scenario values |
| Facility fees | $0.00 public unit, $1.50 community clinic | Plausible for MINSAL / private dispensary; unverified locally |
| Initial attraction | `age_score×0.40 + agreeableness_mean×0.30 + U(0.10, 0.35)` | Invented heuristic; gate at 0.40 |
| Infidelity opportunity / discovery / reconciliation (runtime) | 0.22 / 0.55 / 0.30 per eligible day | **Scenario probabilities, not empirical rates** |

No parameter is presented as a population prevalence. The engines are generative mechanisms, and their rates are tunable; the experiments test mechanism behaviour, not real-world incidence.

### Evidence base and its limits

* Disease: exposure-pathway logic (water, airborne contact, vectors, heat) follows standard outbreak reasoning, but transmission probabilities are not fitted and there is no waning immunity, age-structured contact matrix, or vaccination.
* Relationships: attraction/trust/commitment dimensions are drawn from relationship-science constructs (Sternberg-style components, Gottman-style conflict/communication), but the update equations are authored, not estimated.
* Disasters: flood/landslide triggering is driven by rainfall, soil moisture and terrain class; damage curves are linear heuristics.
* Economics: Phase 1.5 double-entry discipline is enforced; see `SALTBOR_PHASE_1_5_AUDIT.md`.

---

## 3. Reproducible experiments

`python experiments/run_phase15_extension_experiments.py` executes the catalogue in `saltbor/simulation/experiments/phase15_extension_experiments.py` and writes `experiments/results/phase15/phase15_extension_results.json`. The same catalogue runs under pytest via `tests/test_experiments/test_phase15_extension_experiments.py` (parametrized over every experiment class).

| ID | Experiment | What is checked |
| :--- | :--- | :--- |
| EXT_01 | Romantic formation & courtship | Dates raise affection and commitment; stage reaches `DATING` |
| EXT_02 | Jealousy & infidelity dynamics | Jealousy and betrayal require the modelled preconditions |
| EXT_03 | Discovery, trust collapse, separation | Discovery erodes trust; separation and later reconciliation both modelled |
| EXT_04 | Unrequited love & heartbreak | Rejection produces grief, then measurable recovery |
| EXT_05 | Family caregiving | Elder support transfers time/money between real household members |
| EXT_06 | Child dependency | Children depend on adults; care is age-appropriate |
| EXT_07 | Illness onset → recovery | Symptoms/severity progress; treated and untreated paths differ |
| EXT_08 | Airborne transmission | Co-located susceptible contacts can be infected; not all are |
| EXT_09 | Medical capacity & triage | Clinic bed limit rejects the overflow patient with a reason |
| EXT_10 | Traffic accidents | Storm + fatigue raises risk; damage and injury follow |
| EXT_11 | Workplace injuries | Fatigue multiplies occupational hazard |
| EXT_12 | Flooding & displacement | Housing damaged, roads blocked, occupants displaced |
| EXT_13 | Water pollution & cleanup faena | Pollution degrades a source; collective cleanup restores it |
| EXT_14 | Theft & money conservation | Transfer conserves total currency exactly |
| EXT_15 | Financial shock → day labour | Informal work restores liquidity |
| EXT_16 | Multi-system causal cascade | Storm → flood → road closure → reopening chain in the DAG |
| EXT_17 | **Multi-seed robustness, uncertainty & null outcomes** | See below |

`EXP_15_EXT_17` runs five seeds (7, 13, 42, 99, 2024) and does **not** assert a social outcome. Measured:

* Traffic-incident rate, dry/rested, 150 trips × 5 seeds: **0.0000 – 0.0200** (mean 0.0120).
* Traffic-incident rate, storm/fatigued, same volume: **0.1467 – 0.2467** (mean 0.2147, σ 0.0366). Risk ordering held for every seed.
* Per-contact airborne transmission, single-tick exposure: **0.0542 – 0.0958**.
* Share of 40-exposure trials with **zero** infections: **0.525 – 0.675** — most exposures infect nobody.
* Illness rate from potable water: **0.000 in all seeds**; from a contaminated source **0.215 – 0.375**.
* Romantic interest among demographically close couples: 20/20 in every seed (the age-compatibility gate is lenient for peers). Among 24 vs 72-year-old pairings: **11–13 of 20** formed — romantic interest genuinely fails for some pairings.
* Rate spread across seeds is non-zero, so uncertainty is reported rather than a single point value.

---

## 3b. End-to-end verification in the live tick loop

The experiments drive the engines directly. The integrated loop was therefore
also exercised through `SimulationRunner`, and this is where one real gap was
found and fixed: flood damage could only displace tenants holding a formal
lease, so households that owned or informally occupied a dwelling in the
affected zone were never moved and displacement was inert in every integrated
run. `ExtensionRuntime._include_zone_residents()` now adds every resident whose
`home_location_id` lies in the affected zone to the displaced set before
`_apply_displacement()` runs.

Observed in `SimulationRunner` (20 agents, seed 42, SQLite checkpointing on):

| Scenario | Observed |
| :--- | :--- |
| 700 ticks, default (dry season, potable sources) | 10 romantic relationships, 17 dates, 0 illness, 0 accidents, 7 495 causal nodes |
| 400 ticks, forced torrential downpour | 7 waterborne exposures, 1 vector exposure, 6 treatments, 1 flood (severity 0.95) that displaced 3 residents into the communal shelter and restored them after the faena, river cleanliness 0.70 → 0.46, 1 traffic accident, 1 infidelity |
| Checkpoint → reload | 10 relationships, health conditions and 3 160 causal nodes restored identically |

The dry-season run being clinically quiet is a property of the model, not a
disabled subsystem: rainfall is zero in the dry season, initial water sources
are above the potability threshold, and the daytime temperature peak (34 °C)
only crosses the heat-risk threshold for a few midday ticks.

---

## 4. Acceptance criteria

| # | Criterion | Verification |
| :-: | :--- | :--- |
| 1 | Individuals interact with actual geographic/environmental features | `evaluate_water_consumption_risk`, `calculate_travel_burden`, facility coordinates, `classify_object` provenance |
| 2 | Geography influences movement, access and opportunities | travel burden by rain/heat; facility distance/fee in `_treatment_round`; road closures in `_commute_round` |
| 3 | Environment responds to human activity | `record_human_environmental_impact` (waste → river degradation), `execute_community_cleanup_faena` |
| 4 | Health events have biological and social consequences | condition drains, treatment, recovery events, `HEALTH_TREATMENT_SEEKED` outcomes |
| 5 | Romance evolves through decisions and histories | multi-dimensional `RomanticDimensions`, courtship, conflict, discovery |
| 6 | Infidelity/separation/reconciliation possible, not forced | seeded opportunity + discovery + reconciliation probabilities; no forced path |
| 7 | Accidents/disasters have contextual causes | rainfall, fatigue, dwelling quality, age, hazard class |
| 8 | Divergent life trajectories | socioeconomic engines (Phase 1.5) + shocks + caregiving |
| 9 | Consequences propagate through relationships | household moves on cohabitation, caregiving transfers, bereavement, theft distress |
| 10 | Events geographically and historically traceable | coordinates + `location_id` + tick + causal parent on every extension event; checkpointed |
| 11 | UI shows real backend events | extension/casualty panels read the same APIs that expose engine state |
| 12 | Offline, large-scale compatible | no network calls; SQLite checkpoint round-trip; per-location contagion grouping; per-human health is O(conditions) |

---

## 5. Known limitations

1. **Not a clinical or epidemiological predictor.** Transmission probabilities are not fitted to outbreak data; there is no population structure beyond co-location, no immunity waning, no vaccination, no age-stratified severity. Do not read case counts as forecasts.
2. **Not a validated psychological model.** Romance, jealousy and infidelity are mechanisms with explicit preconditions, not psychometric findings. No claim is made that the parameter values reflect real base rates.
3. **Synthetic geography.** Local building positions are mapped from world coordinates to WGS84 deterministically; they are *not* cadastral records. Only entities in the provenance registry may be described as real.
4. **Aggregate actors.** Businesses, clinics and shelters are single nodes with capacity; staffing and queueing are simplified (beds + staff + supply level).
5. **Coarse time.** 15-minute ticks with daily rounds at fixed hours (07:00 commute, 08:00 exposure, 10:00 treatment, 11:00 work, 18:00 contagion, 19:00 romance, 20:00 theft, 21:00 domestic). Sub-hour dynamics are not modelled.
6. **Disaster recovery is optimistic.** A daily volunteer faena reliably restores roads within the model; real recovery is slower and contested.
7. **Selection effects in tests.** The single-seed experiments (EXT_01–16) use one seed by construction. EXT_17 exists specifically so that no conclusion rests on one seed.
8. **Scale.** Extension rounds iterate the population once per day plus per-human health each tick; there is no regional partitioning of the extension yet. At million-agent scale this is a known cost (`SALTBOR_MILLION_AGENT_SPECIFICATION.md`), mitigated but not eliminated by LOD.
9. **Seasonal quiet.** Runs begin in the dry season (`year_frac < 0.5`), so flooding, vector-borne and rain-driven accident paths are dormant until the rainy season or an explicit `force_weather_condition` call. This is intended seasonality, but a short default run will show almost no environmental health events.
10. **Partial housing stock.** Only four residential units are registered with the housing engine, while households occupy six map locations. Damage and rent apply to the registered stock; displacement is applied by home location so unregistered dwellings are still affected by disasters.

---

## 6. Anti-stereotype and anti-determinism checks

* No fixed share of the population is assigned infidelity, crime, illness, poverty or success. Each outcome requires its stated preconditions and a random draw.
* Theft is modelled as an opportunity conditioned on co-location and cash difference, not as a property of a class of people.
* Unhoused status arises from arrears and shocks and can be exited through day labour and re-leasing (Phase 1.5 experiments J, M).
* Health outcomes distinguish exposure from infection, and infection from treatment: exposure does not guarantee infection (53–68 % of short exposures infect nobody), and illness does not guarantee care (unaffordable patients are recorded as `unaffordable` rather than treated).
* Romantic outcomes preserve the distinction between attraction, relationship stage, commitment and behaviour; intimacy is not depicted.

---

## 7. How to reproduce

```bash
# Full test suite (includes all 17 extension experiments)
python -m pytest -q

# Extension experiment report + JSON metrics
python experiments/run_phase15_extension_experiments.py

# Live simulation exercising the extension in the tick loop
python -m saltbor.main run --ticks 288 --report-interval 96

# Observability (API + web UI)
python -m saltbor.main serve
```
