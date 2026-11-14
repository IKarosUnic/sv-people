---
name: saltbor-scientific-validation
description: Falsifiable hypotheses, quantitative metrics, behavioral experiments, and multi-tier causality tracing.
---

# SKILL: Scientific Validation, Empirical Experiments & Causal Tracing

## 1. Objetivo
Asegurar que cada subsistema y fase evolutiva de SALTBOR cuente con validación científica formal: planteamiento de hipótesis falsables, recolección de métricas numéricas verificables, ejecución de baterías de experimentos reproducibles y trazabilidad causal de extremo a extremo sin datos fabricados.

## 2. Cuándo Utilizarla
- Al diseñar las baterías de experimentos obligatorias de cada fase (`EXP_*`).
- Al redactar el reporte de resultados experimentales (`*_EXPERIMENT_RESULTS.md`).
- Al demostrar la causalidad de acontecimientos complejos (`*_CAUSALITY_REPORT.md`).
- Al contrastar condiciones contrapuestas (e.g. régimen Ostrom vs Tragedia de los Comunes).

## 3. Instrucciones de Trabajo
1. **Formular Hipótesis Falsables**:
   - Cada experimento debe plantear de 1 a 3 hipótesis explícitas que puedan resultar falsas bajo ciertas condiciones (e.g. *"Bajo ausencia de monitoreo, la extracción del pozo supera la recarga natural y agota el stock a menos del 20%"*).
2. **Medir y Registrar Métricas Cuantitativas Reales**:
   - Todo resultado debe acompañarse de mediciones empíricas (`metrics` dict): valores iniciales, valores finales, deltas, recuentos de miembros, tasas de transición, coeficientes de Gini o montos monetarios.
   - Prohibido utilizar valores simulados o hardcodeados en los resúmenes.
3. **Diseñar Experimentos Gemelos o de Contraste**:
   - Para demostrar la causalidad de un mecanismo, diseñar parejas experimentales que varíen una sola variable independiente (e.g., `EXP_19_I` con normas Ostrom vs `EXP_19_J` sin normas; `EXP_19_A` con alta confianza vs `EXP_19_W` con baja confianza).
4. **Trazado Causal Multi-Nivel**:
   - Demostrar que los acontecimientos no son decorativos: un choque ambiental debe impactar la geografía física, esto debe alterar la economía del agente, lo cual debe inducir frustración psicológica, motivar la deliberación cívica, movilizar trabajo físico y registrarse en la memoria histórica institucional.

## 4. Procedimientos y Métodos
- **Contrato de Resultado de Experimento (`ExperimentResult`)**:
  ```python
  @dataclass
  class ExperimentResult:
      experiment_id: str
      name: str
      success: bool
      summary: str
      hypotheses: list[dict[str, Any]] # [{"hypothesis": "...", "confirmed": True, "evidence": {...}}]
      metrics: dict[str, Any]
      observed_anomalies: list[str] = field(default_factory=list)
      duration_seconds: float = 0.0
  ```
- **Esquema de Reporte de Causalidad**:
  - Nivel 1: Choque físico/ambiental (lluvia, sismo, sequía).
  - Nivel 2: Degradación de recurso/infraestructura (pozo, carretera).
  - Nivel 3: Impacto microeconómico y cognitivo individual.
  - Nivel 4: Deliberación y decisión colectiva (asamblea ADESCO).
  - Nivel 5: Acción colectiva física y aporte de recursos (*faena*).
  - Nivel 6: Aplicación de normas y sanciones graduadas.
  - Nivel 7: Consolidación en memoria institucional y grafo de conocimiento.

## 5. Referencias y Repositorios Clave
- *The Logic of Scientific Discovery* (Karl Popper, sobre el criterio de falsabilidad).
- *The Book of Why: The New Science of Cause and Effect* (Judea Pearl, sobre diagramas causales y contrafactuales).
- `saltbor/simulation/experiments/base.py`, `saltbor/simulation/experiments/phase19_experiments.py`.

## 6. Herramientas Requeridas
- `BaseExperiment`, `ExperimentConfig`, `ExperimentResult`
- `tests/test_experiments/`

## 7. Criterios de Validación
- Todos los experimentos de la fase pasan de forma determinista (`assert result.success is True`).
- Las hipótesis confirmadas cuentan con evidencia numérica trazable en `metrics`.
- El reporte de causalidad conecta al menos 5 capas arquitectónicas distintas.

## 8. Limitaciones
- Los experimentos de laboratorio simplifican el entorno para aislar la variable estudiada; deben complementarse con pruebas de larga duración en el runner integrado.
