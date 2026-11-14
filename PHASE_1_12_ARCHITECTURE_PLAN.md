# PHASE 1.12 ARCHITECTURE & DESIGN SPECIFICATION
## Scientific Experimentation, Causal Inference & Civilization Research

**Date**: November 2026  
**Status**: APPROVED DESIGN SPECIFICATION  
**Target Environment**: Python 3.14.5, Windows 11, local-first offline execution  

---

## 1. Architectural Architecture & Module Structure

Phase 1.12 introduces a dedicated, high-performance, offline scientific experimentation and causal analysis subsystem located in `saltbor/scientific/`:

```
saltbor/scientific/
├── __init__.py                  # Public exports and high-level facade
├── models.py                    # Domain models, enums, dataclasses, pydantic schemas
├── causal.py                    # CausalInferenceEngine (SCM, Pearl's do-calculus, ATE, CATE, mediation, bootstrap)
├── experimentation.py           # ScientificExperimentationEngine (controlled, observational, longitudinal, multi-seed)
├── sensitivity.py               # ParameterSensitivityEngine (OAT, sweeps, factorial, Monte Carlo, Morris/Sobol)
├── counterfactual.py            # CounterfactualCivilizationEngine (isolated branch forking, trajectory divergence)
├── traceability.py              # CausalEventTraceabilityEngine (multi-tier causality from macro shocks to micro actions)
├── sampling.py                  # PopulationSamplingEngine (stratified sampling across 14 departments and demographics)
├── salvadoran_context.py        # ElSalvadorResearchContext (department profiles, OSM integration, economic/hazard indicators)
└── validation.py                # ScientificValidationFramework (evidence tiers, BCR/World Bank comparison)
```

And in `saltbor/simulation/experiments/`:
- `phase112_scientific_experiments.py`: Implements all 20 required experiments `EXP_112_A` through `EXP_112_T`.

And in `saltbor/visualization/`:
- `api.py`: FastAPI endpoints under `/api/scientific/*`.
- `web/index.html` & `web/app.js`: Interactive Scientific Research Workspace UI.

---

## 2. Core Scientific Data Models (`models.py`)

### 2.1 Enums
- `ExperimentType`: `CONTROLLED`, `OBSERVATIONAL`, `LONGITUDINAL`, `COMPARATIVE`, `COUNTERFACTUAL`, `ABLATION`
- `InterventionDomain`: `ENVIRONMENTAL`, `ECONOMIC`, `SOCIAL`, `INSTITUTIONAL`, `DEMOGRAPHIC`, `CULTURAL`
- `CausalRelationshipType`: `CORRELATION`, `TEMPORAL_ASSOCIATION`, `MECHANISTIC_HYPOTHESIS`, `EXPERIMENTALLY_SUPPORTED`, `UNCERTAIN_CONFOUNDED`
- `EvidenceValidationTier`: `IMPLEMENTED`, `TESTED`, `EXPERIMENTALLY_EVALUATED`, `EMPIRICALLY_CALIBRATED`, `EXTERNALLY_VALIDATED`
- `SensitivityClass`: `ROBUST`, `FRAGILE`, `NON_LINEAR`, `INTERACTIVE`, `UNCERTAIN`

### 2.2 Core Dataclasses
- `CausalVariable`: Name, domain, observable, description, baseline distribution.
- `CausalEdge`: Source, target, relation type, weight/strength, confidence, mechanism description, is_confounded.
- `StructuralCausalModel`: DAG of causal variables and edges, structural equations $Y = f(PA_Y, U_Y)$.
- `TreatmentEffectEstimate`: ATE, CATE, 95% Confidence Interval (bootstrap), Cohen's $d$, sample size, p-value, practical significance flag.
- `MediationResult`: Natural Direct Effect (NDE), Natural Indirect Effect (NIE), Total Effect (TE), Proportion Mediated.
- `ScientificExperimentProtocol`: Unique ID, research question, hypothesis, type, domain, independent vars, dependent vars, control vars, treatment spec, sampling spec, duration, seeds, measurement methodology, data provenance, limitations.
- `MultiSeedExperimentResult`: Aggregated metrics (mean, median, std, variance, 95% CI, distribution, outliers, failure rate), individual run results.
- `CounterfactualBranch`: Baseline trajectory vs counterfactual trajectory, divergence metrics over time, intervention tick, altered parameters.

---

## 3. Mathematical & Algorithmic Specifications

### 3.1 Causal Inference & Pearl's Do-Calculus
For an observational graph $G$ and intervention $do(X = x)$:
1. **Graph Surgery (Truncated Factorization)**: Remove all incoming directed edges to $X$: $G_{\overline{X}}$.
2. **Back-Door Criterion**: A set of variables $Z$ satisfies the back-door criterion relative to $(X, Y)$ if:
   - No node in $Z$ is a descendant of $X$.
   - $Z$ blocks every path between $X$ and $Y$ that contains an arrow into $X$ (backdoor paths).
3. **Average Treatment Effect (ATE)**:
   $$\text{ATE} = \mathbb{E}[Y \mid do(X = 1)] - \mathbb{E}[Y \mid do(X = 0)] = \sum_{z} (\mathbb{E}[Y \mid X=1, Z=z] - \mathbb{E}[Y \mid X=0, Z=z]) P(Z=z)$$
4. **Conditional Average Treatment Effect (CATE)**:
   $$\text{CATE}(v) = \mathbb{E}[Y \mid do(X = 1), V=v] - \mathbb{E}[Y \mid do(X = 0), V=v]$$
5. **Mediation Analysis (Baron-Kenny / Pearl)**:
   $$\text{TE} = \text{NDE} + \text{NIE}$$
   Where $\text{NIE}$ captures the effect transmitted through mediator $M$, and $\text{NDE}$ captures direct effect without $M$.
6. **Non-Parametric Bootstrap 95% Confidence Interval**:
   Resample observations with replacement $B = 1000$ times. Compute estimate $\hat{\theta}^{*b}$.
   $$CI_{95\%} = [\text{Quantile}(\hat{\theta}^*, 0.025), \text{Quantile}(\hat{\theta}^*, 0.975)]$$

### 3.2 Parameter Sensitivity & Morris/Sobol Screening
1. **One-At-A-Time (OAT)**:
   $$\text{Elasticity } E = \frac{\Delta Y / Y_0}{\Delta \theta / \theta_0}$$
2. **Morris Elementary Effects**:
   $$EE_i = \frac{Y(\theta_1, \dots, \theta_i + \Delta, \dots, \theta_k) - Y(\theta)}{\Delta}$$
   Calculate $\mu_i^*$ (overall importance) and $\sigma_i$ (non-linear / interaction effects).

---

## 4. Multi-Tier Causal Event Traceability

The `CausalEventTraceabilityEngine` establishes full backward and forward inspectability across 9 architectural tiers:

```
Tier 1: Initial Conditions & Exogenous Shock (e.g. Drought, Earthquake)
   ↓
Tier 2: Environmental Resource Degradation (Water table drop, Crop failure)
   ↓
Tier 3: Individual Cognitive Appraisal & Needs (Frustration, Hunger, Risk aversion)
   ↓
Tier 4: Social Interactions & Network Updates (Borrowing request, Grievance share)
   ↓
Tier 5: Economic Transactions & Liquidity Depletion (Fiado default, Asset sale)
   ↓
Tier 6: Institutional Deliberation & Governance (ADESCO meeting, Water rationing rule)
   ↓
Tier 7: Primary Immediate Consequence (Sanction issued, Faena organized)
   ↓
Tier 8: Secondary Cascading Consequence (Faction split, Out-migration)
   ↓
Tier 9: Long-Term Civilizational Outcome (Settlement abandonment, Cultural drift)
```

Each edge connecting nodes across tiers is explicitly classified as:
- `DIRECT_CAUSE`: Counterfactually necessary and sufficient in simulation state.
- `CONTRIBUTING_FACTOR`: Increases probability/intensity but not singularly sufficient.
- `INDIRECT_EFFECT`: Transmitted through intermediate causal mediators.
- `COINCIDENTAL_CO_OCCURRENCE`: Statistically simultaneous without mechanistic link.

---

## 5. El Salvador Reference Grounding

Geographic grounding reuses `saltbor/datasets/gis/ingested/geography.sqlite` (151,251 OSM features) and defines realistic socioeconomic and environmental parameter profiles across all **14 departments**:

| Department | Zone | Geography | Dominant Economy | Key Vulnerability |
| :--- | :--- | :--- | :--- | :--- |
| **Ahuachapán** | Occidente | Volcanic highlands / border | Coffee, border commerce | Landslides, drought in dry corridor |
| **Santa Ana** | Occidente | Highland plateau, lake | Coffee, agro-industry, urban | Water stress, volcanic seismic risk |
| **Sonsonate** | Occidente | Coastal plain & mountains | Agriculture, port, tourism | Flooding, marine storm surge |
| **Chalatenango** | Norte | Mountainous highlands | Smallholder farming, dairy | Water isolation, slope erosion |
| **La Libertad** | Central | Coastal to mountain ridge | Commerce, services, tourism | Urban runoff, coastal storm impact |
| **San Salvador** | Central | Metropolitan valley | Commerce, informal trade, industry | High urban density, flood congestion |
| **Cuscatlán** | Central | Valley & hill slopes | Traditional crafts, commerce | Land fragmentation, seasonal drought |
| **La Paz** | Paracentral | Coastal lowlands & hills | Sugarcane, airport logistics | Flooding in lower river basins |
| **Cabañas** | Paracentral | Rugged interior hills | Smallholder subsistence, pasture | Severe drought in Corredor Seco |
| **San Vicente** | Paracentral | Volcano & valley plain | Sugarcane, small businesses | Landslides on volcanic slopes |
| **Usulután** | Oriente | Coastal plain, Bajo Lempa | Grains, fishing, agriculture | Severe flooding in Bajo Lempa |
| **San Miguel** | Oriente | Regional urban center / valley | Regional trade, cattle, remittances | Extreme heat, summer drought |
| **Morazán** | Oriente | Mountainous interior | Smallholder agro, community forestry | Remoteness, water access |
| **La Unión** | Oriente | Coastal gulf & volcanic hills | Fishing, port commerce, remittances | High salinity, extreme heat |

---

## 6. Scientific Validation & External Comparator Framework

The `ScientificValidationFramework` verifies simulation models against real empirical reference distributions while strictly adhering to honest epistemic boundaries:

1. **Evidence Labels**:
   - `IMPLEMENTED`: Code exists and compiles.
   - `TESTED`: Unit and integration tests pass deterministically.
   - `EXPERIMENTALLY_EVALUATED`: Evaluated through controlled multi-seed simulation trials.
   - `EMPIRICALLY_CALIBRATED`: Parameters calibrated against real external statistical ranges.
   - `EXTERNALLY_VALIDATED`: Simulated emergent distributions statistically compatible with observed real distributions within defined confidence bounds.

2. **Multilateral Reference Matrices**:
   - **BCR (Banco Central de Reserva)**: Remittance inflows (20-25% of household income in receiving areas), inflation rates, liquidity.
   - **DIGESTYC / ONE (EHPM)**: Informal employment rates (65-72%), poverty rates, multidimensional deprivation.
   - **FAO & MARN**: Agricultural yields, dry corridor drought frequencies, rainfall seasonality.
   - **CNR & OpenStreetMap**: Road connectivity, spatial settlement density.

Every comparison documents:
- Source agency & publication year.
- Measurement methodology.
- Coverage resolution.
- Epistemic disclaimer: SALTBOR models synthetic agent interactions; it does not claim to predict actual individual Salvadoran decisions.
