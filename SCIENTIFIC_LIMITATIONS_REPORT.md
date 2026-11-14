# SALTBOR SCIENTIFIC LIMITATIONS, UNCERTAINTY BOUNDS & EPISTEMIC PRINCIPLES
## Formal Boundaries of Synthetic Human Simulation in El Salvador Reference Context

**Document Status**: MANDATORY SYSTEM DIRECTIVE & SCIENTIFIC AUDIT  
**Version**: Phase 1.12  
**Target Subsystem**: SALTBOR Scientific Experimentation & Causal Inference Infrastructure  
**Core Standard**: Popperian Falsifiability & Pearl's Structural Causal Epistemology  

---

## 1. Absolute Scientific Disclaimer

SALTBOR is a computational research laboratory and generative agent-based modeling environment. It is designed to evaluate **social, economic, psychological, and institutional mechanisms** grounded in formal social sciences (e.g., Ostrom's Common Pool Resource design principles, Granovetter's threshold models of collective behavior, OCC cognitive emotional appraisal, and double-entry accounting conservation).

> [!IMPORTANT]
> **SALTBOR DOES NOT PREDICT THE ACTUAL BEHAVIOR OF REAL SALVADORAN CITIZENS.**  
> It does not claim human consciousness, subjective sentience, or teleological historical inevitability.  
> Simulation outcomes must NEVER be presented as deterministic forecasts of actual Salvadoran policy outcomes or real historical events.

---

## 2. Epistemic Evidence Classification Tiers

To prevent scientific overclaiming, all claims, models, and outputs in SALTBOR must carry explicit evidence labels:

| Tier Label | Formal Criteria | What May Be Claimed | What May NOT Be Claimed |
| :--- | :--- | :--- | :--- |
| **`IMPLEMENTED`** | Code compiles and executes without crash. | Code functions according to algorithmic specification. | Cannot claim scientific validity or empirical accuracy. |
| **`TESTED`** | Unit, regression, and property tests pass deterministically. | Algorithmic logic is internally consistent and bug-free. | Cannot claim experimental hypothesis confirmation. |
| **`EXPERIMENTALLY_EVALUATED`** | Hypotheses confirmed across multiple independent seeds ($N \ge 3$) with bounded variance and documented confounders. | Emergent mechanism operates as hypothesized within the synthetic model. | Cannot claim empirical calibration to real-world data. |
| **`EMPIRICALLY_CALIBRATED`** | Model parameters and aggregate distributions match observed empirical bounds from official datasets (BCR, DIGESTYC/ONE, World Bank). | Model parameters reflect real aggregate statistical magnitudes of El Salvador. | Cannot claim external out-of-sample predictive validity. |
| **`EXTERNALLY_VALIDATED`** | Simulated emergent macro-patterns statistically match out-of-sample real historical or observational time-series. | Generative mechanism is structurally compatible with observed aggregate phenomena. | Cannot claim micro-level individual forecasting power. |

---

## 3. Methodological & Data Limitations

### 3.1 Geospatial Dataset Limitations (`geography.sqlite`)
1. **Source & License**: Derived from Geofabrik OpenStreetMap (ODbL 1.0, acquired November 2026).
2. **Partial Footprints**: While road networks (121,344 segments) and places (2,657) are comprehensive nationwide, building polygons (989) are partial outside San Salvador Centro.
3. **Missing Turn Restrictions**: Road connectivity is geometric and topological; complex municipal turn restrictions and real-time traffic signal timing are not captured.
4. **Elevation Approximations**: Departmental elevation means are parameterized; micro-topographical slope friction uses regional averages.

### 3.2 Microeconomic & Informal Transaction Limitations
1. **Unrecorded Informal Flows**: In El Salvador, informal commerce comprises 65-72% of employment (EHPM 2022). Informal credit (*fiado*) and petty street sales leave no paper trail. SALTBOR models these via double-entry synthetic ledgers; they are plausible mechanistic models, not transactional records of real businesses.
2. **Remittance Micro-Dynamics**: Official BCR statistics record aggregate remittance inflows ($7.5B+ annually, ~24% of GDP). However, the specific allocation between household consumption, health emergencies, and home construction is synthetically modeled based on social survey literature, not bank account monitoring.

### 3.3 Demographic & Cognitive Modeling Boundaries
1. **Diversity Principle**: Salvadoran citizens are heterogeneous. Individual behaviors cannot be inferred directly from national averages. SALTBOR strictly avoids cultural stereotyping; missing individual traits remain explicitly stochastic or uncertain.
2. **Bounded Rationality**: Synthetic agents act under bounded rationality, emotional appraisal, and incomplete knowledge. They are not hyper-rational utility maximizers, nor are they sentient beings.

---

## 4. Causal Inference Boundaries & Confounding Risks

### 4.1 Correlation vs Causation Distinctions
Under Judea Pearl's Structural Causal Models, SALTBOR strictly separates:
- **`CORRELATION`**: Statistical co-movement (e.g., higher rainfall and higher informal sales).
- **`TEMPORAL_ASSOCIATION`**: Event $A$ occurs before Event $B$, but mechanism is unverified.
- **`MECHANISTIC_HYPOTHESIS`**: Theoretical structural equation $Y = f(X, Z, U)$ linking variables.
- **`EXPERIMENTALLY_SUPPORTED`**: Tested via Pearl's $do(X = x)$ operator (graph surgery) with unblocked backdoor paths and bootstrap 95% confidence intervals.
- **`UNCERTAIN_CONFOUNDED`**: Backdoor paths remain unblocked by available control variables.

### 4.2 Counterfactual Reasoning Limits
Counterfactual trajectories ($Y_{X=x'}$) are evaluated by forking simulation state at tick $T_0$ under identical random seeds. While this isolates the internal mechanics of the intervention, it does not guarantee that real human societies would respond identically, as unmodeled exogenous geopolitical shifts could alter boundary rules.

---

## 5. Protocol for Handling Missing Information

When empirical data for a Salvadoran municipality, canton, or economic sector is missing:
1. **Explicit Uncertainty**: Label the parameter as `UNCERTAIN` or `UNVERIFIED_ESTIMATE`.
2. **Never Fabricate Data**: Do not invent fake census numbers or specific names.
3. **Range-Based Sensitivity**: Use parameter sweeps over plausible theoretical intervals rather than fixing an arbitrary single point estimate.
4. **Document Data Gaps**: Log missing information in the experimental protocol's `expected_limitations` metadata.
