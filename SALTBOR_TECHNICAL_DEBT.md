# SALTBOR — INVENTARIO Y GESTIÓN DE DEUDA TÉCNICA
## REGISTRO DE CONSOLIDACIONES EJECUTADAS, VULNERABILIDADES REMANENTES Y PLAN DE REFACTORIZACIÓN

**Proyecto:** SALTBOR  
**Versión:** 1.1.0  
**Fecha:** 10 de Noviembre de 2026  
**Auditor:** Equipo Multidisciplinario de Ingeniería e Investigación SALTBOR

---

## 1. RESUMEN DE DEUDA TÉCNICA RESUELTA EN LA FASE 1.1

Durante la ejecución de la Fase 1.1 se detectaron y resolvieron 6 problemas estructurales críticos que amenazaban la estabilidad, reproducibilidad y persistencia del sistema:

### 1.1 Persistencia Incompleta de Memorias y Destrezas en SQLite
- **Diagnóstico:** El repositorio guardaba la entidad biológica del habitante, pero ignoraba sus recuerdos episódicos, destrezas aprendidas y hechos semánticos en `HumanRepository.save()`. Al recargar la simulación desde SQLite, los agentes perdían toda su historia biográfica y sus competencias laborales.
- **Acción Ejecutada en Fase 1.1:** Se implementó en `HumanRepository.save()` la serialización sistemática de `EpisodicRecord`, `Skill` y `SemanticFact`. Se incorporaron los métodos `save_semantic_fact` y `load_semantic_for_human` en `MemoryRepository`.
- **Estado:** **RESUELTO Y VALIDADO** en `EXP_11_P` y `test_persistence.py`.

### 1.2 Amnesia Cerebral en la Reconstrucción de Agentes
- **Diagnóstico:** Al cargar un habitante desde SQLite vía `HumanRepository.reconstruct_human()`, el objeto era instanciado sin sus motores cognitivos avanzados (`IndividualKnowledgeGraph`, `EpistemicInterface`, `AdvancedReasoningEngine`, `ProblemSolvingEngine`, `MetacognitionEngine`, `CreativeCombinationEngine`, `CuriosityEngine`, `CognitiveBrainArchitecture`), dejándolo como un autómata simplista.
- **Acción Ejecutada en Fase 1.1:** Se cablearon e instanciaron todos los motores cognitivos durante la reconstrucción del habitante, restaurando su corteza cerebral y grafo individual.
- **Estado:** **RESUELTO Y VALIDADO**.

### 1.3 Desconexión entre Relaciones Interpersonales y Grafo Social
- **Diagnóstico:** `SocialEngine` administraba las relaciones diádicas y `SocialNetworkEngine` administraba el grafo topológico de red social, pero no se comunicaban. Una interacción entre habitantes actualizaba la relación interpersonal pero no creaba ni ponderaba la arista correspondiente en el grafo de red.
- **Acción Ejecutada en Fase 1.1:** Se inyectó `self.social.network_engine = self.social_network` en `SimulationRunner`, sincronizando automáticamente las interacciones sociales con las aristas ponderadas de la red en tiempo real.
- **Estado:** **RESUELTO Y VALIDADO** en `EXP_11_D` y `EXP_11_T`.

### 1.4 Aislamiento de la Corteza Cerebral en la Toma de Decisiones
- **Diagnóstico:** `CognitiveBrainArchitecture` calculaba sesgos y activaciones, pero el motor de decisión `DecisionEngine.decide()` tomaba decisiones basándose únicamente en necesidades físicas y personalidad, ignorando las penalizaciones espaciales de la corteza parietal, la automaticidad cerebelosa y el humor límbico.
- **Acción Ejecutada en Fase 1.1:** Se integró la corteza cerebral en `DecisionEngine.decide()`, aplicando penalizaciones de distancia euclidiana/topológica y bonificaciones de automaticidad habitual en el cálculo de utilidad de cada actividad.
- **Estado:** **RESUELTO Y VALIDADO** en `EXP_11_K` y `EXP_11_S`.

### 1.5 Invocación de Comunidades Espontáneas
- **Diagnóstico:** `CommunityFormationEngine` existía como módulo pero nunca era invocado durante el ciclo principal de simulación.
- **Acción Ejecutada en Fase 1.1:** Se integró la verificación de formación espontánea de comunidades (`check_spontaneous_formation`) en el rollover diario de `SimulationRunner.step()`.
- **Estado:** **RESUELTO Y VALIDADO** en `EXP_11_E`.

### 1.6 Tolerancia a Formatos de UUID No Hexadecimales
- **Diagnóstico:** La función auxiliar `_uuid_or_none()` lanzaba `ValueError` al recibir identificadores sintéticos de recuerdos como `"mem_exp11_p_record"`.
- **Acción Ejecutada en Fase 1.1:** Se amplió el bloque `try/except` para devolver el string original cuando no cumple con el formato canónico de UUIDv4, garantizando robustez.
- **Estado:** **RESUELTO Y VALIDADO**.

---

## 2. INVENTARIO DE DEUDA TÉCNICA REMANENTE

A pesar de los avances de la Fase 1.1, se identificaron 5 áreas de deuda técnica técnica remanente que deben abordarse en las Fases 1.2 y 1.3:

| ID Deuda | Componente Afectado | Descripción del Problema | Impacto Técnico | Prioridad |
|:---:|---|---|---|:---:|
| **DT-01** | `saltbor/world/geographic/` | Coexistencia de nodos sintéticos antiguos (Fase 1-5) con el motor geográfico real `RealGeographicEngine` (Fase 8). | Confusión en resolución de rutas locales | **ALTA** |
| **DT-02** | `saltbor/events/bus.py` | Acumulación indefinida de eventos en `EventBus.event_log` en memoria RAM durante corridas ultra-largas ($>5,000$ ticks). | Crecimiento lineal de memoria heap | **MEDIA** |
| **DT-03** | `saltbor/population/physical_state.py` | Sobrecarga de validación de atributos Pydantic (`__setattr__`) en el bucle crítico de simulación (14% del CPU time). | Ralentización en poblaciones $>500$ agentes | **MEDIA** |
| **DT-04** | `saltbor/social/engine.py` | Búsqueda de compañeros de interacción social sin filtro espacial previo (complejidad $O(N^2)$). | Cuello de botella en alta densidad | **ALTA** |
| **DT-05** | `saltbor/persistence/` | Los checkpoints de disco en SQLite WAL son síncronos en el hilo principal de simulación. | Pequeños micro-stutters cada 100 ticks | **BAJA** |

---

## 3. MATRIZ DE RIESGO DE DEUDA REMANENTE

```text
  IMPACTO
    ▲
ALTO│                 [DT-04] Búsqueda Social O(N^2)
    │                 [DT-01] Dualidad Geográfica
    │
MED │  [DT-02] EventLog RAM
    │  [DT-03] Pydantic Slots
    │
BAJO│  [DT-05] Checkpoint Síncrono
    └────────────────────────────────────────►
      BAJA           MEDIA          ALTA     PROBABILIDAD
```

---

## 4. PLAN DE REFACTORIZACIÓN PRIORIZADO (FASES 1.2 Y 1.3)

### Fase 1.2 (Optimización Espacial y Rendimiento)
1. **Unificación Geográfica Definitiva (DT-01):**
   - Deprecar los grafos sintéticos abstractos.
   - Establecer `RealGeographicEngine` y la jerarquía de 262 distritos como la única fuente de verdad espacial en SALTBOR.
2. **Particionamiento Espacial para Búsquedas Sociales (DT-04):**
   - Implementar indexación por grilla espacial / distrito para que los agentes solo evalúen interacciones con vecinos situados a menos de $X$ kilómetros, reduciendo la complejidad a $O(N \cdot k)$.
3. **Poda y Descarga Periódica del EventLog (DT-02):**
   - Implementar un buffer circular para `EventBus.event_log` que descargue automáticamente eventos a SQLite y mantenga en RAM únicamente los últimos 200 ticks.

### Fase 1.3 (Rendimiento Extremo y Simulación Masiva)
1. **Migración a Dataclasses con Slots (DT-03):**
   - Reemplazar `BaseModel` de Pydantic en `PhysicalState` por dataclasses de Python 3.14 con `__slots__ = True` para eliminar la sobrecarga de validación en tiempo de ejecución.
2. **Persistencia en Segundo Plano (DT-05):**
   - Mover el volcado de checkpoints SQLite WAL a un hilo secundario de I/O para eliminar cualquier interrupción en el bucle de simulación.

---

## 5. CONCLUSIÓN

La deuda técnica de SALTBOR ha sido auditada y acotada con precisión quirúrgica. Las vulnerabilidades que comprometían la persistencia y la consistencia lógica han sido completamente subsanadas en la Fase 1.1. Las tareas remanentes están claramente calendarizadas para optimizar la escala y el rendimiento en la Fase 1.2.
