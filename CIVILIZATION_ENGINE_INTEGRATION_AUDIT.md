# CIVILIZATION ENGINE INTEGRATION AUDIT
## Component-by-Component Integration Mapping, Subsystem Gaps & Causal Wiring

**System**: SALTBOR Phase 1.11  
**Date**: November 2026  
**Audited Directory**: [saltbor/civilization/](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/) and related runtime coordinators  

---

## 1. Component Audit Matrix

The following table provides the comprehensive integration audit for every civilization engine implemented in SALTBOR, detailing its intended functionality, actual integration status in [runner.py](file:///c:/GIT%20HUB/sv%20people/saltbor/simulation/runner.py), and required wiring.

| Subsystem Component | File Path | Current Status | Integration Gap in Simulation Loop | Action Required in Phase 1.11 |
| :--- | :--- | :--- | :--- | :--- |
| `CivilizationEvolutionEngine` | [engine.py](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/engine.py) | **Implemented / Disconnected** | Exists as an isolated container instantiated only in unit tests. `SimulationRunner` does not hold an instance or invoke its `evolve_step()`. | Instantiate in `SimulationRunner`, register in `SimulationRuntimeOrchestrator`, and bind to daily/annual evolutionary ticks. |
| `SettlementEvolutionEngine` | [settlement.py](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/settlement.py) | **Implemented / Disconnected** | `runner.locations` uses static places (`LocationRegistry`). Settlements are not dynamically founded, grown, degraded, or abandoned based on inhabitant counts and resources. | Unify with `LocationRegistry` and GIS layers. Map physical places to parent settlements. Compute dynamic carrying capacity, water access, and decay. |
| `MultiGenerationalEngine` | [multigenerational.py](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/multigenerational.py) | **Implemented / Disconnected** | Lineage records exist in memory, but are not synchronized when `runner.population` individuals reproduce, age, or die during live simulation execution. | Wire directly to `LifeCycleEngine` and `SyntheticHuman` death/birth callbacks. Maintain family lineages and generation indices. |
| `HistoricalMemoryEngine` | [history.py](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/history.py) | **Implemented / Duplicated** | Runs parallel to `SalvadoranHistoricalMemoryEngine` in `saltbor/knowledge/salvadoran/history.py`. Live events in `EventBus` are not converted into ground-truth historical records. | Consolidate into unified `CivilizationalMemoryEngine`. Intercept high-importance events ($\text{importance} \ge 0.65$) from `EventBus` and archive them with oral drift and institutional fidelity. |
| `EconomicCivilizationEngine` | [economy.py](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/economy.py) | **Implemented / Disconnected** | Contains abstract sectoral production ($100.0$ per sector) and enterprise registry, but does not read or reflect actual transactions from `InformalCommerceEngine`, `LaborMarketEngine`, or `HouseholdLedger`. | Link enterprise liquidity to live commercial establishments. Aggregate actual microeconomic GDP, sector employment, and capital accumulation. |
| `TechnologicalEvolutionEngine` | [technology.py](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/technology.py) | **Implemented / Disconnected** | `ScientificThinkingEngine` conducts individual experiments, but discoveries are not registered into collective civilizational technology nodes, nor are they diffused to settlements. | Connect `EventType.HYPOTHESIS_CONFIRMED` to `TechnologicalEvolutionEngine`. Model material prerequisites, peer diffusion, and intergenerational knowledge loss. |
| `MigrationDynamicsEngine` | [migration.py](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/migration.py) | **Implemented / Disconnected** | Push-pull formulas exist, but live agents only move locally between coordinates in San Salvador without relocating their residence across settlements. | Enable inter-settlement relocation. Agents experiencing local environmental or economic distress evaluate destinations and permanently migrate. |
| `CivilizationResilienceEngine` | [resilience.py](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/resilience.py) | **Implemented / Standalone** | Crisis evaluation formulas exist, but are not triggered when real weather hazards (floods, droughts) occur in `IntegratedWorldSimulationEngine`. | Trigger crisis events upon environmental shocks from `EnvironmentEngine` and evaluate collective survival, pooling, or abandonment strategies. |
| `MultiSocietyInteractionEngine` | [interaction.py](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/interaction.py) | **Implemented / Disconnected** | Tracks diplomatic relations and trade treaties, but trade volume is disconnected from `RegionalTradeEngine` and road transport blockages. | Wire inter-society trade treaties to `RegionalTradeEngine` and transportation corridors. Adjust trust based on supply disruptions. |
| `HistoricalKnowledgeGraph` | [graph.py](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/graph.py) | **Implemented / Disconnected** | Wraps `KnowledgeGraphEngine`, but historical nodes (`HISTORICAL_EVENT`, `INNOVATION`, `SETTLEMENT`) are not queryable through the visualization API. | Expose historical graph queries via `/api/civilization/history/graph` and synchronize with `CausalEventGraph`. |
| `SocietalIdentityVector` | [society_vector.py](file:///c:/GIT%20HUB/sv%20people/saltbor/civilization/society_vector.py) | **Implemented / Standalone** | Computes 18-element normalized vector, but is not continuously updated or stored in history metrics snapshots. | Compute `SocietalIdentityVector` at midnight ticks and serialize it into `CivilizationMetricSnapshot` for comparative radar visualization. |

---

## 2. Execution Path & Event Flow Analysis

### 2.1 Current Execution Path in `SimulationRunner.step()`

```
SimulationRunner.step()
  ├── SimulationClock.tick()
  ├── EnvironmentEngine.step()
  ├── RegionalTradeEngine.step()
  ├── SimulationRuntimeOrchestrator.step()
  │     ├── Periodic: Weekly Cuchubales
  │     ├── Periodic: Monthly Remittances
  │     └── Event-Triggered: ADESCO, Judicial, Commerce, Education, Dialogue
  ├── Daily Cycle (tick_of_day == 0):
  │     ├── Household living expenses
  │     ├── Housing rent & eviction
  │     ├── Labor market payroll
  │     ├── Commerce accounting
  │     ├── Environmental impact recording
  │     ├── Culture & tradition decay
  │     ├── Social network decay
  │     ├── Norm evolution & CPR manager step
  │     └── Social stratification (Gini / Palma)
  ├── Agent update loop (Physical, Psychological, Decisions)
  ├── IntegratedWorldSimulationEngine.step() (Journeys, blockages, place occupancy)
  ├── PsychologicalEngine.step_population()
  └── Checkpoint (periodic)
```

### 2.2 Target Phase 1.11 Unified Execution Path

```
SimulationRunner.step()
  ├── [Existing Tick Operations]
  │
  ├── Daily Cycle (tick_of_day == 0):
  │     ├── [Existing Daily Operations]
  │     └── Civilization Daily Coordination:
  │           ├── CivilizationEvolutionEngine.step_daily()
  │           │     ├── Settlement carrying capacity & resource updates
  │           │     ├── Inter-settlement migration evaluations
  │           │     ├── Collective technology diffusion & knowledge decay
  │           │     └── Environmental feedback propagation
  │           ├── SocietalIdentityVector computation
  │           └── High-importance event archival into CivilizationalMemoryEngine
  │
  └── Longitudinal Macro Stepper (Annual / Multi-Year Leaps):
        ├── Batch demographic turnover (births, aging, mortality, inheritance)
        ├── Multi-generational knowledge transmission & loss
        ├── Settlement expansion, fragmentation, or abandonment
        ├── Structural economic shifts & business succession
        ├── Macro resilience evaluations & systemic adaptations
        └── Checkpoint snapshot persistence
```

---

## 3. Detailed Subsystem Gaps & Integration Blueprints

### 3.1 Gap 1: Dynamic Settlements & Carrying Capacity
- **Current State**: Locations in [catalog.py](file:///c:/GIT%20HUB/sv%20people/saltbor/world/locations/capabilities.py) are hardcoded strings (`mercado_central`, `tienda_san_pedro`, `plaza_central`).
- **Gap**: There is no structural representation of settlements that can grow from a *caserío* to a *ciudad*, or decay into an *abandoned* ruin when water fails or out-migration drains the population.
- **Blueprint**:
  - Attach each location to a parent `Settlement` ID.
  - Compute dynamic carrying capacity:
    $$\text{Capacity} = \text{BaseHousing} \times (0.4 \cdot \text{WaterAccess} + 0.3 \cdot \text{SoilFertility} + 0.3 \cdot \text{RoadConnectivity})$$
  - When $\text{Population} > \text{Capacity}$, trigger overcrowding penalties, increase disease risk, and spike out-migration pressure.

### 3.2 Gap 2: Generational Replacement & Inheritance
- **Current State**: In [human.py](file:///c:/GIT%20HUB/sv%20people/saltbor/population/human.py), agents age per tick. If an agent dies, they are removed from the population registry and their SQLite row is deleted in `_prune_deceased_rows()`.
- **Gap**: Wealth disappears into thin air upon death (violating accounting conservation rule #1), and surviving family members receive no inheritance. Skills are not transmitted to descendants.
- **Blueprint**:
  - Implement `execute_inheritance(deceased: SyntheticHuman, heirs: list[SyntheticHuman])`:
    - Liquid cash is split equally among heirs ($\sum \Delta \text{Money}_{\text{heirs}} = \text{Money}_{\text{deceased}}$).
    - Tools and enterprise ownership transfer to the primary heir.
    - If debts exist, they are charged against the estate before distribution.
    - Lineage records in `MultiGenerationalEngine` log the generational wealth transfer.

### 3.3 Gap 3: Historical Memory Fidelity & Distortion
- **Current State**: Events are logged in `EventBus.event_log` as ephemeral dataclass objects.
- **Gap**: There is no mechanism to simulate how historical events are remembered across generations, how details are forgotten, or how oral narratives diverge from institutional archives.
- **Blueprint**:
  - Wire `CivilizationalMemoryEngine`:
    - Objective ground truth recorded with full causal provenance.
    - Institutional archives preserve formal legal and municipal records.
    - Cultural narratives accumulate generational transmission drift:
      $$\text{Drift}_{g+1} = \text{Drift}_g + 0.08 \times (1.0 - \text{Fidelity})$$
    - After 3 generations ($75\text{ years}$), oral accounts retain key symbolic themes but mutate factual metrics.

### 3.4 Gap 4: Endogenous Technological Diffusion & Obsolescence
- **Current State**: Knowledge is stored in individual network graphs, but technologies never become obsolete, nor are they forgotten when key elders die.
- **Gap**: Phase 1.11 requires technologies to have material prerequisites, to potentially fail during experiments, and to become lost if no surviving practitioner transmits the skill.
- **Blueprint**:
  - Link `TechnologicalEvolutionEngine`:
    - Innovations require material resources (e.g. *bocashi fertilizer* requires organic waste; *loom* requires timber and metals).
    - If material runs out, technique cannot be practiced.
    - If practitioners drop to 0, technology status transitions to `InnovationStatus.FORGOTTEN` and must be rediscovered.

---

## 4. Integration Verification Gate

Before proceeding to implementation, this audit establishes the non-negotiable verification gates:
1. `CivilizationEvolutionEngine` must be imported and initialized in `SimulationRunner`.
2. All settlement changes must reflect in physical location availability.
3. Every economic transaction in civilization evolution must maintain exact double-entry conservation.
4. Pytest suite must pass 100% with no regressions.
