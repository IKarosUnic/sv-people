# SALTBOR — Fase 1.7: auditoría e integración psicológica

## 1. Auditoría de la arquitectura previa

La inspección se hizo sobre el código real y el flujo de `SimulationRunner`, no sobre la existencia nominal de clases.

| Capacidad existente | Dónde vive | Estado antes de 1.7 |
|---|---|---|
| Emociones y perfil emocional | `saltbor/cognition/emotions/*` | Implementado e integrado en decisiones y memoria |
| Personalidad Big Five | `saltbor/cognition/personality/*` | Implementado; cambio por experiencia limitado |
| Memoria episódica/semántica/procedimental | `saltbor/cognition/memory/*` | Persistente; recuperación por filtros, sin índice asociativo ni reconstrucción |
| Decisión MAUT/GOAP/HTN | `saltbor/cognition/decision/*`, `problem_solving/*` | Implementado e integrado |
| Conocimiento individual | `saltbor/knowledge/layers/individual_graph.py` | Implementado |
| Metacognición, curiosidad, razonamiento | `saltbor/cognition/*` | Implementado |
| Relaciones, redes, grupos y comunidades | `saltbor/social/*` | Implementado |
| Romance, infidelidad, duelo | `saltbor/social/romance/*`, `grief` | Implementado; sin acoplamiento psicológico profundo |
| Cuerpo, salud, accidentes, ambiente | `saltbor/population/physical_state.py`, `health/*`, `accidents/*`, `world/environment/*` | Implementado |
| Economía, trabajo, vivienda | `saltbor/economy/*`, extensión 1.5 | Implementado |
| Geografía OSM y navegación | `saltbor/datasets/gis/*`, `world/geographic/*` | Implementado con atribución ODbL |
| Persistencia SQLite/WAL | `saltbor/persistence/*` | Esquema v3, checkpoints de extensión |
| API y frontend | `saltbor/visualization/api.py`, `web/app.js` | Paneles existentes, sin psicología integrada |

### Diagnóstico

- **No existía un estado psicológico persistente integrado.** Había emociones, rasgos y memoria, pero ninguna capa que los conectara causalmente con crisis, afrontamiento, apoyo y cuerpo.
- **No existía evaluación OCC individual.** Las emociones se actualizaban, pero un mismo acontecimiento no se reinterpretaba según metas, valores, expectativa, agencia y control.
- **No existía afrontamiento adaptativo.** No había estrategias con coste, beneficio diferido, aprendizaje ni resultados observados.
- **No existía crisis con inicio/duración/consecuencias/recuperación/recaída.** El estrés no tenía un proceso de desregulación con historial.
- **La recuperación de memoria no era asociativa ni reconstructiva.** No había índice por persona/lugar/tag, ni pérdida de fidelidad, ni contradicciones.
- **El apoyo social no era una transacción psicológica.** No modelaba rechazo, coste al proveedor ni asimetría.
- **No había LOD psicológico.** El coste habría sido lineal con la población.

No se duplicaron emociones, memoria, personalidad ni decisión: la capa nueva los orquesta y escribe en ellos.

## 2. Diagrama de integración

```
EventBus / SimulationRunner.step
        │
        ├── eventos nuevos (cursor) ──► PsychologicalEngine.process_events
        │                                   │
        │                                   ├── OCC Appraisal (metas, valores, control, agencia)
        │                                   ├── EmotionState / EmotionalProfile (existente)
        │                                   ├── creencias, timeline, memoria episódica
        │                                   └── estrés agudo
        │
        └── PsychologicalEngine.step_population (LOD FULL/ROUTINE/MACRO/DORMANT)
                    │
                    ├── BodySignals ◄── PhysicalState (hambre, sueño, salud, dolor, dinero)
                    ├── RegulationEngine (estrés crónico, autocontrol, esperanza, crisis)
                    ├── CopingEngine (26 estrategias, costes, apoyo, resultados diferidos)
                    ├── SocialSupportEngine (red, rechazo, estigma, reciprocidad)
                    ├── AssociativeRetrieval (recencia, importancia, relevancia, asociación)
                    ├── consecuencias mente→cuerpo
                    └── PsychologicalState + timeline + checkpoint JSON

SyntheticHuman.psychology ──► DecisionContext.psychological ──► DecisionEngine
        │                                                        (modificadores acotados)
        ├── MemoryEngine (tags/source_event_id)
        ├── GriefEngine / RomanceEngine / SocialEngine
        ├── SQLite: phase15_extension + psychology_timeline
        └── API /api/psychology/* + dossier + frontend
```

## 3. Sistemas nuevos

| Archivo | Responsabilidad |
|---|---|
| `saltbor/psychology/models.py` | `PsychologicalState`, `AppraisalRecord`, `CopingEpisode`, `CrisisEpisode`, `LifeEventRecord`, `CopingProfile`; clamps y aproximación exponencial estable |
| `saltbor/psychology/appraisal.py` | Plantillas OCC por `EventType`, expectativa/control/agencia/valores/relación, inversión de valencia, `apply_appraisal` |
| `saltbor/psychology/coping.py` | 26 estrategias problema/emoción/evitación, afinidad de rasgos, factibilidad, utilidad, ejecución, costes, resolución diferida y aprendizaje EMA |
| `saltbor/psychology/regulation.py` | Dinámica cuerpo→mente, estrés agudo/crónico, fatiga, autocontrol, esperanza, crisis por presión/resistencia/umbral individual, sensibilidad, recuperación, residual y recaída |
| `saltbor/psychology/retrieval.py` | Índice asociativo, scoring, reconstrucción con pérdida de fidelidad y sesgo afectivo, contradicciones, olvido |
| `saltbor/psychology/support.py` | Evaluación de red/familia/pareja/amistades, apoyo objetivo vs percibido, solicitudes, rechazo, coste, estigma |
| `saltbor/psychology/engine.py` | Orquestador, LOD, eventos, snapshot, overview, checkpoint y persistencia incremental |
| `saltbor/simulation/experiments/phase17_common.py` | Harness de experimentos, agentes, redes, eventos, IC y Cohen d |
| `saltbor/simulation/experiments/phase17_experiments_a_j.py` | EXP_17_A … EXP_17_J |
| `saltbor/simulation/experiments/phase17_experiments_k_t.py` | EXP_17_K … EXP_17_T |
| `saltbor/simulation/experiments/phase17_experiments.py` | Agregador y ejecución del suite |
| `scripts/benchmark_phase17.py` | Benchmark aislado 20–10.000 y simulación completa 20/100/10.000 |

## 4. Sistemas existentes modificados

- `SyntheticHuman`: `psychology`, `_psych_regulation`, contexto psicológico en decisión y resumen de estado.
- `DecisionEngine`: `DecisionContext.psychological`; modulación acotada por actividad y factores “Psychological load”/“Crisis”.
- `SimulationRunner`: `self.psychology`, cursor de eventos, `process_events` + `step_population`, `ensure` al inicializar, `persist_timeline` en checkpoint.
- `ExtensionRuntime`: psicología en `to_dict`/`load_dict`.
- `events/types.py`: `APPRAISAL_FORMED`, `COPING_STRATEGY_USED`, `COPING_OUTCOME_RECORDED`, `PSYCHOLOGICAL_CRISIS_STARTED/RECOVERED/RELAPSE`, `SOCIAL_SUPPORT_REQUESTED/GRANTED/REFUSED`.
- `MemoryEngine`/`EpisodicRecord`: `source_event_id` y tags.
- `persistence/schema.py`: tabla `psychology_timeline`, índice `(human_uid, tick)`, esquema v4.
- `visualization/api.py`: endpoints y bloque de dossier; roster con `chronic_stress`, `self_control`, `in_crisis`.
- `visualization/web/app.js`: panel psicológico.
- `core/identity.py` + `population/factory.py` + `runner.py`: UUIDv5 deterministas por semilla/serial y sincronización de seriales al recargar. Sin esto, el escalado tras un checkpoint reutilizaba seriales y perdía individuos.
- `psychology/regulation.py`: corrección de signo en sensibilidad/recaída (las crisis previas ahora bajan el umbral, no lo suben).
- `psychology/support.py`: una solicitud sin red también registra rechazo y coste de soledad.
- `persistence/repositories.py`: el upsert de `humans` pasó de `INSERT OR REPLACE` a `ON CONFLICT(uid) DO UPDATE`. El `REPLACE` borraba la fila y el `ON DELETE CASCADE` eliminaba la línea de tiempo en cada checkpoint; al ser incremental, el historial anterior no se reescribía.

## 5. Persistencia

- Checkpoint JSON dentro de `phase15_extension` para el estado completo.
- Tabla incremental `psychology_timeline`:

```sql
CREATE TABLE psychology_timeline (
  human_uid TEXT NOT NULL,
  record_id TEXT NOT NULL,
  tick INTEGER NOT NULL,
  kind TEXT NOT NULL DEFAULT 'event',
  summary TEXT NOT NULL DEFAULT '',
  valence REAL NOT NULL DEFAULT 0.0,
  importance REAL NOT NULL DEFAULT 0.5,
  location_id TEXT,
  payload_json TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY (human_uid, record_id),
  FOREIGN KEY (human_uid) REFERENCES humans(uid) ON DELETE CASCADE
);
CREATE INDEX idx_psych_timeline_human_tick ON psychology_timeline(human_uid, tick);
```

Migración no destructiva: `CREATE TABLE/INDEX IF NOT EXISTS`; `_SCHEMA_VERSION = 4`.

## 6. Contratos API

- `GET /api/psychology/overview` → agregados, crisis, coping, distribución y estadísticas.
- `GET /api/psychology/individual/{uid}` → snapshot completo (constitución, estado, creencias, crisis, coping, appraisals, timeline, memorias reconstruidas, modificadores).
- `GET /api/psychology/timeline/{uid}?limit=` → `uid`, `name`, `entries`, `crises`, `coping` desde estado real.
- `GET /api/psychology/social/{uid}` → nodos, aristas, apoyo, pareja, familia, tamaño de red.
- `GET /api/individuals` incluye `chronic_stress`, `self_control`, `in_crisis`.
- `GET /api/individuals/{uid}` incluye bloque `psychology`.

## 7. Matriz de estado

| Subsistema | Implementado | Integrado | Probado | Evidencia |
|---|---|---|---|---|
| Estado psicológico persistente | Sí | Sí | Sí | A–T, test de checkpoint, T |
| OCC y appraisal individual | Sí | Sí | Sí | B, F; inversión de valencia del despido |
| Emociones acopladas al sustrato | Sí | Sí | Sí | F, J, Q |
| Afrontamiento adaptativo | Sí | Sí | Sí | D, E; 26 estrategias |
| Aprendizaje de afrontamiento | Sí | Sí | Sí | E: preferencia no se corrigió (H3 rechazada) |
| Crisis y desregulación | Sí | Sí | Sí | C, O, P |
| Recuperación y recaída | Sí | Sí | Sí | P (3/3 recaída tras reexposición) |
| Memoria asociativa/reconstructiva | Sí | Sí | Sí | G, H |
| Apoyo social y rechazo | Sí | Sí | Sí | K; coste al proveedor |
| Romance, infidelidad, reconciliación | Sí | Sí | Sí | L: 12 separaciones, 2 reconciliaciones |
| Cuerpo↔mente | Sí | Sí | Sí | J |
| Desarrollo longitudinal | Sí | Sí | Sí | M: 25 años, deriva 0.024 |
| Diversidad conductual | Sí | Sí | Sí | N: entropía 0.74–0.77, asociación débil (H2 inconclusa) |
| Ablación causal | Sí | Sí | Sí | Q: evaluación, afrontamiento y apoyo cambian el resultado |
| LOD psicológico | Sí | Sí | Sí | S + benchmark: 10.000 aislado 51.8 ms/tick |
| Simulación completa 10.000 | Sí | Sí | Sí | Benchmark: 68.1 s/tick, 1.14 GB RSS, checkpoint 17.5 s |
| Persistencia y recarga | Sí | Sí | Sí | T: 20/20 estados; checkpoint conserva la timeline (300→332) |
| API | Sí | Sí | Sí | 3 tests de contrato |
| Frontend | Sí | Sí | Parcial | Captura real del panel + endpoints; sin recorrido exhaustivo |
| Determinismo del motor psicológico | Sí | Sí | Sí | R: firmas idénticas con misma semilla |
| Determinismo exacto de la simulación completa | Parcial | Sí | Parcial | UUIDv5 corrigió colisiones; el runner completo aún puede variar por orden de eventos/azar de otros motores |

## 8. Limitaciones conocidas

- La simulación no tiene consciencia fenomenológica; modela mecanismos funcionales.
- Las etiquetas de crisis son categorías de simulación, no diagnósticos clínicos.
- La memoria no es una copia literal; su reconstrucción es funcional, no neurocientífica.
- El determinismo exacto del runner completo no está garantizado; el motor psicológico sí es exacto con la misma semilla.
- Los edificios OSM son parciales (pilot bbox) y los establecimientos simulados están marcados como tales.
- La UI se revisó visualmente en una captura real; no se recorrieron todos sus controles.
- La simulación completa a 10.000 tarda 68.1 s/tick y 1.14 GB; no es tiempo real a esa escala. El benchmark no aísla aún el motor responsable del crecimiento superlineal.
- El 500 de `/api/geography/geojson` observado en la vista de mapa es preexistente, ajeno a la capa psicológica, y no se corrigió en este cambio.
