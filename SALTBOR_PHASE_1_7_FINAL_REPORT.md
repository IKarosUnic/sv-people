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
| 20 | 0.033 | 0.0017 | 67.3 MB |
| 100 | 0.156 | 0.0016 | 70.7 MB |
| 500 | 1.219 | 0.0024 | 86.9 MB |
| 1.000 | 3.772 | 0.0038 | 105.4 MB |
| 10.000 | 51.848 | 0.0052 | 448.4 MB |

En ejecuciones previas, 10.000 individuos dieron **31.7–54.9 ms/tick** (0.0032–0.0055 ms/individuo). La variación refleja carga de la máquina; el motor psicológico aislado sigue por debajo de 60 ms/tick con 10.000 estados.

### Simulación completa

Cada tick incluye decisiones, eventos, cuerpo, redes, economía, psicología y SQLite. La inicialización y el checkpoint se cronometran aparte y no forman parte del ms/tick.

| Población | Ticks | Init | ms/tick | p95 | ms/agente | RSS | Checkpoint | SQLite | WAL | Timeline tras checkpoint |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 96 | 1.15 s | 7.52 | 11.53 | 0.376 | 89.7 MB | 0.148 s | 3.5 MB | 4.2 MB | 332 |
| 100 | 48 | 1.12 s | 77.14 | 126.29 | 0.771 | 145.8 MB | 1.351 s | 20.0 MB | 17.5 MB | 2.203 |
| 10.000 | 3 | 7.19 s | **68.102,5** | 83.175,7 | **6.810** | **1.142 MB** | **17.49 s** | 238.0 MB | 240.0 MB | 2.462 |

La simulación completa a 10.000 es **superlineal**: 100 → 10.000 multiplica la población por 100 y el tick por ~883 (77 ms → 68,1 s), mientras el coste por agente sube de 0,77 a 6,81 ms. No es apta para tiempo real a esa escala. El benchmark no aísla todavía qué motor causa el crecimiento; la cifra se reporta como medida, no como diagnóstico. El overview psicológico tarda 39,4 ms y el snapshot individual 0,096 ms a 10.000.

El tramo de 10.000 usó 1 tick de calentamiento y 3 medidos para acotar el tiempo; no se extrapola a 96 ticks. El checkpoint de 17,5 s y el RSS de 1,1 GB son parte del coste real medido.

### UI observada

El panel se revisó en un servidor real (FastAPI + Chromium, 1600×1000), no solo por sintaxis. La vista **Explorador Individual → dossier** muestra estrés agudo/crónico, autocontrol, esperanza, fatiga, soledad, apoyo percibido, bienestar, LOD, red, creencias, crisis, afrontamiento, timeline y recuerdo reconstruido con su nota de modelo funcional. Captura: `docs/reports/phase17_ui_psychology.png`.

Los endpoints `overview`, `individual`, `timeline` y `social` respondieron 200 con datos reales. La consola no mostró errores del panel psicológico; sí un 500 preexistente de `/api/geography/geojson` en la vista de mapa, ajeno a esta capa y no corregido en este cambio.

## 5. Pruebas y regresiones

- **561 tests pasan** (`python -m pytest -q`), 0 fallos.
- Fase 1.7 añadió 30: 6 de psicología, 21 de experimentos, 3 de contratos API.
- `python -m compileall -q saltbor` pasa.
- `node --check saltbor/visualization/web/app.js` pasa.
- Se corrigieron tres regresiones reales:
  1. El escalado tras cargar un checkpoint reutilizaba seriales y perdía individuos (20 → 30 en lugar de 50). Se sincroniza el `IdentityFactory` al máximo serial restaurado.
  2. Una solicitud de apoyo sin red no registraba rechazo ni coste de soledad.
  3. `INSERT OR REPLACE` en `humans` borraba la fila en cada checkpoint y el `ON DELETE CASCADE` eliminaba la línea de tiempo; como la escritura es incremental, el historial anterior se perdía. El upsert usa ahora `ON CONFLICT(uid) DO UPDATE` y hay una regresión que comprueba que el número de filas no disminuye.
- EXP_111_I (auditoría de rendimiento de una fase anterior) es sensible a la carga: pasó en aislamiento y en la ejecución final completa. No se rebajó su umbral.

## 6. Licencias y atribuciones

Ver `THIRD_PARTY_NOTICES.md`. No se incorporó código de terceros; solo se usaron ideas y referencias. OpenStreetMap sigue bajo ODbL 1.0 con atribución visible.

## 7. Limitaciones conocidas

- No hay consciencia fenomenológica ni diagnóstico clínico; las crisis son categorías de simulación.
- La memoria es funcional y reconstructiva, no un modelo neurocientífico.
- La personalidad cambia lentamente y con topes; no se busca “transformación dramática” garantizada.
- El determinismo exacto del motor psicológico está probado; el runner completo aún puede variar por el orden de eventos y el azar de otros motores.
- La UI se revisó visualmente en una captura real; no se hizo un recorrido exhaustivo de todos sus controles.
- Los edificios OSM son parciales (pilot bbox); los establecimientos simulados están marcados como tales.
- La simulación completa a 10.000 tarda 68,1 s/tick y consume 1,1 GB: es un límite medido, no una capacidad de tiempo real. El overview psicológico y el snapshot sí responden en decenas de milisegundos.
- El 500 de `/api/geography/geojson` observado en la vista de mapa es preexistente y queda fuera de este cambio.

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
| LOD / rendimiento | Sí | Sí | Sí | S + benchmark; 10k full = 68,1 s/tick |
| Persistencia / recarga | Sí | Sí | Sí | T, tests |
| API | Sí | Sí | Sí | 3 tests |
| Frontend | Sí | Sí | Parcial | Captura real + endpoints; sin recorrido exhaustivo |
| Determinismo del motor | Sí | Sí | Sí | R |
| Determinismo exacto del runner | Parcial | Sí | Parcial | Limitación declarada |

## 9. Reproducción

```bash
python -m pytest -q
python -m saltbor.simulation.experiments.phase17_experiments
python scripts/benchmark_phase17.py --full-populations 20,100,10000
```

Artefactos: `docs/reports/phase17_experiments.json`, `docs/reports/phase17_benchmark.json`.
