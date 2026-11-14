---
name: saltbor-scientific-validation
description: Falsifiable hypotheses, quantitative metrics, behavioral experiments, and multi-tier causality tracing.
---

# SKILL: Scientific Validation, Empirical Experiments & Causal Tracing (Phase 1.12 Extension)

## 1. Objetivo
Asegurar que cada subsistema y fase evolutiva de SALTBOR cuente con validación científica formal: planteamiento de hipótesis falsables, recolección de métricas numéricas verificables, ejecución de baterías de experimentos reproducibles y trazabilidad causal de extremo a extremo sin datos fabricados. En la Fase 1.12, se incorporan Modelos Causales Estructurales (SCM), intervención por *do-calculus* de Judea Pearl, estimación de efectos de tratamiento (ATE/CATE), análisis de mediación, sensibilidad global y ramificación contrafactual.

## 2. Cuándo Utilizarla
- Al diseñar las baterías de experimentos obligatorias de cada fase (`EXP_*`).
- Al formular modelos causales estructurales (SCM) y grafos DAG acíclicos.
- Al estimar efectos causales del tratamiento (ATE/CATE) y realizar pruebas de mediación (NDE/NIE).
- Al evaluar la sensibilidad paramétrica (OAT, Morris, Sobol) y detectar puntos de inflexión.
- Al ejecutar ramas contrafactuales paralelas sin fuga estocástica.
- Al clasificar el nivel de evidencia científica formal (`IMPLEMENTED`, `TESTED`, `EXPERIMENTALLY_EVALUATED`, `EMPIRICALLY_CALIBRATED`, `EXTERNALLY_VALIDATED`).
- Al redactar el reporte de resultados experimentales (`*_EXPERIMENT_RESULTS.md`) y limitaciones científicas.

## 3. Instrucciones de Trabajo
1. **Formular Hipótesis Falsables**:
   - Cada experimento debe plantear de 1 a 3 hipótesis explícitas que puedan resultar falsas bajo ciertas condiciones empíricas.
2. **Medir y Registrar Métricas Cuantitativas Reales**:
   - Todo resultado debe acompañarse de mediciones empíricas (`metrics` dict): valores iniciales, valores finales, deltas, tasas de transición, coeficientes de Gini o montos monetarios.
   - Prohibido utilizar valores simulados o hardcodeados en los resúmenes.
3. **Distinguir Estrictamente Correlación vs Causalidad**:
   - Separar: `CORRELATION`, `TEMPORAL_ASSOCIATION`, `MECHANISTIC_HYPOTHESIS`, `EXPERIMENTALLY_SUPPORTED`, `UNCERTAIN_CONFOUNDED`.
   - Utilizar el criterio de puerta trasera (Back-Door criterion) de Pearl para bloquear confusores.
4. **Diseñar Experimentos Gemelos o de Contraste**:
   - Para demostrar la causalidad de un mecanismo, diseñar parejas experimentales que varíen una sola variable independiente bajo semillas idénticas.
5. **Trazado Causal Multi-Nivel (9 Niveles)**:
   - Conectar desde el choque inicial y degradación ambiental hasta la decisión cognitiva, interacción social, flujo económico, deliberación institucional, consecuencia inmediata y resultado histórico a largo plazo.

## 4. Procedimientos y Métodos
- **Contratos de la Fase 1.12 (`saltbor/scientific/`)**:
  - `CausalInferenceEngine`: DAGs, SCMs, $do(X = x)$, ATE, CATE, Cohen's $d$, bootstrap 95% CI.
  - `ScientificExperimentationEngine`: Ejecución multi-semilla aislada con registro de semillas.
  - `ParameterSensitivityEngine`: Barridos OAT, cálculo de elasticidad y efectos elementales de Morris.
  - `CounterfactualCivilizationEngine`: Bifurcación en tick $T_{branch}$ y medición de divergencia.
  - `CausalEventTraceabilityEngine`: Reconstrucción retrospectiva de 9 niveles.
  - `ElSalvadorResearchContext`: Parámetros de los 14 departamentos de El Salvador y 151,251 entidades OSM.
  - `ScientificValidationFramework`: Verificación de los 8 criterios de validación y contraste con BCR/Banco Mundial/FAO.

- **Niveles de Validación Formal (`EvidenceValidationTier`)**:
  1. `IMPLEMENTED`: Código compila y ejecuta.
  2. `TESTED`: Pruebas de unidad e integración pasan al 100%.
  3. `EXPERIMENTALLY_EVALUATED`: Hipótesis confirmadas a través de múltiples semillas independientes.
  4. `EMPIRICALLY_CALIBRATED`: Parámetros calibrados contra rangos observados de fuentes oficiales (BCR, ONEC, FAO).
  5. `EXTERNALLY_VALIDATED`: Distribuciones emergentes contrastadas estadísticamente con series temporales externas.

## 5. Referencias y Repositorios Clave
- *The Logic of Scientific Discovery* (Karl Popper).
- *Causality: Models, Reasoning, and Inference* & *The Book of Why* (Judea Pearl).
- *Global Sensitivity Analysis: The Primer* (Andrea Saltelli et al.).
- `saltbor/scientific/`, `saltbor/simulation/experiments/phase112_scientific_experiments.py`.

## 6. Herramientas Requeridas
- `ScientificExperimentationEngine`, `CausalInferenceEngine`, `ParameterSensitivityEngine`.
- `BaseExperiment`, `ExperimentConfig`, `ExperimentResult`.
- `tests/test_scientific/`, `tests/test_experiments/test_phase112_scientific_experiments.py`.

## 7. Criterios de Validación
- Todos los experimentos de la fase pasan de forma determinista (`assert result.success is True`).
- Las hipótesis confirmadas cuentan con evidencia numérica trazable en `metrics`.
- El reporte de causalidad conecta las capas físicas, cognitivas, sociales, económicas e institucionales.
- Se documentan con honestidad las limitaciones y sesgos del modelo en `SCIENTIFIC_LIMITATIONS_REPORT.md`.

## 8. Limitaciones
- Los modelos experimentales simplifican el entorno para aislar la variable estudiada.
- Ningún resultado debe interpretarse como predicción exacta del comportamiento de ciudadanos salvadoreños reales.
