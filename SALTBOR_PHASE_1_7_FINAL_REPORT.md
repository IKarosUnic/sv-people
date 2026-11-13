# SALTBOR — Fase 1.7: informe final

**Realismo psicológico, fragilidad humana y conducta adaptativa**

**Commit de implementación: `1a6105f74cac37d509e77e489fd6b0e64de2cc78`**

La Fase 1.7 está integrada en `SimulationRunner`, persistida en SQLite y observable por API/UI. No es un conjunto de motores aislados: cada tick procesa eventos nuevos, actualiza el estado psicológico con LOD y escribe en emoción, memoria, decisión, cuerpo, redes y economía existentes.

> SALTBOR no afirma consciencia fenomenológica ni equivalencia psicológica humana. Modela mecanismos funcionales y trayectorias verificables.

## 1. Qué se implementó

- Estado psicológico persistente con constitución, estado lento, estado agudo, creencias, hábitos y timeline.
- Evaluación OCC individual: metas, deseabilidad, expectativa, agencia, control, valores, relación, certeza e importancia.
- Afrontamiento problema/emoción/evitación: 26 estrategias con condiciones, costes, beneficios, riesgos, apoyo, resultado observado y aprendizaje EMA.
- Crisis por proceso continuo presión/resistencia/umbral individual, con causas, duración, comportamientos, recuperación, residual y recaída.
- Memoria asociativa indexada: recencia, importancia, relevancia, intensidad, accesibilidad, asociación; reconstrucción imperfecta, contradicciones y olvido.
- Apoyo social transaccional: red, familia, pareja, amistades; concesión, rechazo, coste, estigma, asimetría y persistencia de solicitudes.
- Cuerpo↔mente: hambre, sueño, salud, dolor, enfermedad y dinero modulan estrés/autocontrol; el descontrol modula alimentación, descanso y salud.
- Desarrollo biográfico lento y acotado: la personalidad cambia por repetición/intensidad/tiempo, no por un evento aislado.
- LOD psicológico: FULL 1, ROUTINE 2, MACRO 8, DORMANT 24 ticks, con integración analítica del tiempo transcurrido.
- API `/api/psychology/*`, bloque `psychology` en el dossier y panel en el frontend.

## 2. Integración real

```
SimulationRunner.step
  ├─ eventos nuevos por cursor → PsychologicalEngine.process_events
  ├─ PsychologicalEngine.step_population (LOD)
  ├─ EmotionState / EmotionalProfile / MemoryEngine / SocialEngine
  ├─ DecisionContext.psychological → DecisionEngine
  ├─ PhysicalState ←→ RegulationEngine
  ├─ phase15_extension (JSON) + psychology_timeline (SQLite)
  └─ API / frontend
```

La comprobación EXP_17_T encontró **683–758 appraisals**, **30–34 intentos de afrontamiento**, **3.840 trazas de decisión con el factor psicológico**, **406–469 filas de timeline** y **20/20 estados restaurados** tras checkpoint.

## 3. Experimentos EXP_17_A–T

Todos ejecutaron con múltiples semillas y controles cuando el diseño lo permitía. Resultado global: **53 hipótesis apoyadas, 5 inconclusas, 2 rechazadas**. Los rechazos e inconclusos se conservan; no se ajustaron para que parecieran positivos.

| Exp | Tema | Resultado principal |
|---|---|---|
| A | Estrés agudo vs acumulativo | Pico 0.790 vs 0.703; AUC 46.6 vs 43.9; carga persistente tras cesar estresores |
| B | Mismo despido, seis biografías | Emociones dominantes distintas (`joy`, `frustration`); deseabilidad 1.31 de rango; r(neuroticismo, appraisal negativo)=0.48 |
| C | Colapso y recuperación | Misma presión: pico 0.248 vs 0.117 y autocontrol final 0.456 vs 0.813 (vulnerable vs resiliente) |
| D | Afrontamiento adaptativo | Problema −0.175, emoción −0.164, evitación −0.038 de estrés crónico; ventaja aguda de emoción no concluyente |
| E | Trade-offs | Alivio inmediato 0.103 y coste diferido −0.024; la preferencia evitativas **no** se corrigió (H3 rechazada) |
| F | OCC | El mismo despido produce `joy` en quien odiaba el trabajo y `frustration` en quien sostenía a su familia |
| G | Recuperación de memoria | Recencia, relevancia contextual y 7 candidatos examinados por consulta (no escaneo global) |
| H | Distorsión | Fidelidad 0.97 → 0.070 a 200 días; sesgo afectivo y contradicciones detectadas |
| I | Duelo | 13 valores distintos de tristeza a 30 días; con la misma personalidad, más apoyo **no** redujo la tristeza (H2 rechazada); 16/16 aún elevados a 180 días |
| J | Cuerpo–mente | Hambre/sueño elevan estrés (0.207/0.443 vs 0.031); dolor eleva fatiga y baja autocontrol; descontrol aumenta hambre |
| K | Apoyo social | Concesión 61.1% con red fuerte vs 0% aislado; soledad 0.774 vs 0.694; coste al proveedor 30.5 |
| L | Crisis de pareja | Confianza 0.810 → 0.486; 12 separaciones y 2 reconciliaciones; desenlaces no uniformes |
| M | Longitudinal 1/5/10/25 años | Deriva máxima de neuroticismo 0.024; dos trayectorias divergentes; cambio de afrontamiento no concluyente |
| N | Diversidad conductual | Entropía 0.74–0.77; asociación rasgo–estado débil (H2 inconclusa) |
| O | Adversidad múltiple | Pico compuesto 0.222 vs único 0.161; vulnerabilidad residual 0.249; creencia de seguridad 0.293 |
| P | Recuperación y recaída | 3/3 recuperados y 3/3 recayeron tras reexposición; residual máximo 0.269 |
| Q | Ablación causal | Sin evaluación: appraisal negativo 1.69 vs 3.99; sin afrontamiento: estrés 0.536 vs 0.431; sin apoyo: esperanza 1.0 vs 0.828 |
| R | Determinismo | Misma semilla = firma idéntica; distinta personalidad/semilla = trayectoria distinta |
| S | Benchmark sostenido | 1.000 individuos: 2.3 ms/tick, 109 MB RSS, checkpoint 1.56 MB |
| T | Simulación integrada | Appraisals, coping, trazas, checkpoint y recarga verificados dentro del runner |

### Lectura honesta

- **Apoyado**: acumulación, appraisal individual, crisis, cuerpo–mente, memoria reconstructiva, apoyo social transaccional (K), romance, adversidad, recaída, ablación, persistencia.
- **Inconcluso**: ventaja aguda de estrategias emocionales; corrección del aprendizaje evitativo; asociación rasgo–diversidad; escalado sublineal medido solo en el motor psicológico.
- **Rechazado**: la preferencia por procrastinación no disminuyó pese al coste diferido, y una red de apoyo más amplia no redujo la tristeza de duelo a 30 días (de hecho, fue 0.10 puntos mayor en pares del mismo perfil). Son resultados negativos del modelo actual, no efectos ocultos.

## 4. Benchmarks sostenidos

`docs/reports/phase17_benchmark.json`, Ryzen 7 8700G / 32 GB / Windows 11 / Python 3.14.5.

### Motor psicológico (aislado)

| Población | ms/tick | ms/individuo/tick | RSS |
|---:|---:|---:|---:|
| 20 | 0.032 | 0.0016 | 67.0 MB |
| 100 | 0.274 | 0.0027 | 70.3 MB |
| 500 | 1.312 | 0.0026 | 86.6 MB |
| 1.000 | 2.315 | 0.0023 | 105.7 MB |
| 10.000 | 54.880 | 0.0055 | 448.4 MB |

En una ejecución previa, 10.000 individuos dieron **31.7 ms/tick** y 0.0032 ms/individuo; la variación (31.7–54.9 ms) refleja carga de la máquina, no un cambio de algoritmo. Incluso el peor valor mantiene 10.000 individuos por debajo de 60 ms/tick.

### Simulación completa

| Población | Ticks | ms/tick medio | p95 | RSS | SQLite | WAL | Timeline | Overview API |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 96 | 7.34 | 13.49 | 90.1 MB | 4 KB | 4.05 MB | 279 | 0.032 ms |
| 100 | 48 | 82.07 | 142.59 | 140.8 MB | 15.0 MB | 15.7 MB | 1.487 | 0.114 ms |

El snapshot individual tarda ~0.28–0.31 ms. La simulación completa a 10.000 no se ejecutó: mezclaría la capa psicológica con toda la arquitectura de agentes. Esa limitación está declarada, no ocultada.

## 5. Pruebas y regresiones

- **561 tests pasan** (`python -m pytest -q`), 0 fallos.
- Fase 1.7 añadió 30: 6 de psicología, 21 de experimentos, 3 de contratos API.
- `python -m compileall -q saltbor` pasa.
- `node --check saltbor/visualization/web/app.js` pasa.
- Se corrigieron dos regresiones reales detectadas por la suite:
  1. El escalado tras cargar un checkpoint reutilizaba seriales y perdía individuos (20 → 30 en lugar de 50). Se sincroniza el `IdentityFactory` al máximo serial restaurado.
  2. Una solicitud de apoyo sin red no registraba rechazo ni coste de soledad.
- EXP_111_I (auditoría de rendimiento de una fase anterior) es sensible a la carga: pasó en aislamiento y en la ejecución final completa. No se rebajó su umbral.

## 6. Licencias y atribuciones

Ver `THIRD_PARTY_NOTICES.md`. No se incorporó código de terceros; solo se usaron ideas y referencias. OpenStreetMap sigue bajo ODbL 1.0 con atribución visible.

## 7. Limitaciones conocidas

- No hay consciencia fenomenológica ni diagnóstico clínico; las crisis son categorías de simulación.
- La memoria es funcional y reconstructiva, no un modelo neurocientífico.
- La personalidad cambia lentamente y con topes; no se busca “transformación dramática” garantizada.
- El determinismo exacto del motor psicológico está probado; el runner completo aún puede variar por el orden de eventos y el azar de otros motores.
- La UI se validó por sintaxis y contratos API, pero **no se revisó visualmente** en esta fase.
- Los edificios OSM son parciales (pilot bbox); los establecimientos simulados están marcados como tales.
- El benchmark de 10.000 mide la capa psicológica, no la simulación completa.

## 8. Matriz de estado

| Subsistema | Implementado | Integrado | Probado | Evidencia |
|---|---|---|---|---|
| Estado psicológico persistente | Sí | Sí | Sí | A–T, checkpoint, T |
| OCC / appraisal individual | Sí | Sí | Sí | B, F |
| Afrontamiento adaptativo | Sí | Sí | Sí | D, E |
| Aprendizaje de afrontamiento | Sí | Sí | Sí | E: H3 rechazada |
| Crisis / desregulación | Sí | Sí | Sí | C, O, P |
| Recuperación / recaída | Sí | Sí | Sí | P |
| Memoria asociativa / distorsión | Sí | Sí | Sí | G, H |
| Apoyo social / rechazo | Sí | Sí | Sí | K |
| Romance / infidelidad / reconciliación | Sí | Sí | Sí | L |
| Cuerpo↔mente | Sí | Sí | Sí | J |
| Desarrollo longitudinal | Sí | Sí | Sí | M |
| Diversidad conductual | Sí | Sí | Sí | N |
| Ablación causal | Sí | Sí | Sí | Q |
| LOD / rendimiento | Sí | Sí | Sí | S + benchmark |
| Persistencia / recarga | Sí | Sí | Sí | T, tests |
| API | Sí | Sí | Sí | 3 tests |
| Frontend | Sí | Sí | Parcial | `node --check`; no revisión visual |
| Determinismo del motor | Sí | Sí | Sí | R |
| Determinismo exacto del runner | Parcial | Sí | Parcial | Limitación declarada |

## 9. Reproducción

```bash
python -m pytest -q
python -m saltbor.simulation.experiments.phase17_experiments
python scripts/benchmark_phase17.py --populations 20,100,500,1000,10000
```

Artefactos: `docs/reports/phase17_experiments.json`, `docs/reports/phase17_benchmark.json`.
