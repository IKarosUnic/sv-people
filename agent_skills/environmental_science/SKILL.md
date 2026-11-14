# SKILL: Environmental Science & Climate Systems
`agent_skills/environmental_science/SKILL.md`

## 1. Purpose & Domain Scope
Guides the modeling of physical climate, precipitation cycles, geological hazards, soil moisture, and their causal economic/behavioral repercussions in the simulated territory.

## 2. When to Use
- Implementing weather patterns, *época seca* (verano) vs *época lluviosa* (invierno), and temporal storms (*temporales*).
- Simulating hazards: landslides (e.g. Los Chorros), volcanic tremors, flash floods, and agricultural droughts.
- Calculating road travel speed penalties, impassable routes, and crop yield degradation.

## 3. Workflows & Procedures
1. **Seasonal State Calculation**: Drive temperature, humidity, and precipitation via empirical Salvadoran climate distributions.
2. **Hazard Triggering**: Link excessive cumulative rainfall to slope instability and road obstruction.
3. **Causal Feedback**: Broadcast weather alerts $\rightarrow$ agents re-evaluate travel plans $\rightarrow$ transport bottlenecks avoid disaster or cause economic delays.

## 4. Technical References
- *MARN El Salvador* (Ministerio de Medio Ambiente y Recursos Naturales) historical meteorological data.
- NOAA Climate Data Online; Köppen-Geiger climate classification (Aw/Am for El Salvador).

## 5. Validation Criteria
- Causal consequence: Rainfall directly affects road speed multiplier and crop yields.
- Deterministic reproducibility under fixed random seeds.
