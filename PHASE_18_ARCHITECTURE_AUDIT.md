# SALTBOR — FASE 1.8: AUDITORÍA DE ARQUITECTURA E INTEGRACIÓN
## Simulación Humana y Territorial Integrada: Interacción Real, Arquitectura Unificada y Vida Cotidiana Emergente

**Fecha de auditoría:** 13 de noviembre de 2026  
**Línea base:** SALTBOR Fase 1.7 (Commit `69cd11a`, 569/570 tests pasando, 1 fallo por semilla no determinista en decisión aleatoria aislada)  
**Entorno de ejecución:** Windows 11 / AMD Ryzen 7 8700G (16 CPUs) / 32 GB DDR5 / Python 3.14.5 / SQLite 3.49+ (WAL mode)  
**Autoridad:** Arquitecto Principal, Ingeniero de Simulación, Especialista en Sistemas Multiagente, Investigador de Vida Artificial y Responsable de Integración de SALTBOR.

---

## 1. RESUMEN EJECUTIVO DE LA AUDITORÍA

Se ha llevado a cabo una inspección forense exhaustiva del repositorio completo `sv people` (SALTBOR), analizando código fuente, contratos de clases, ciclo de ejecución de `SimulationRunner.step()`, `ExtensionRuntime`, `Orchestrator`, endpoints de FastAPI, esquemas de SQLite y enlaces visuales en `app.js` e `index.html`.

### Diagnóstico de la Situación Actual

SALTBOR posee una riqueza conceptual y algorítmica sin precedentes en simulación multiagente en El Salvador (D.L. 762, Centro Histórico de San Salvador, Suchitoto, ADESCOs, caliche salvadoreño, ODbL OSM con 151.251 entidades geográficas normalizadas, psicología cognitiva OCC y afrontamiento adaptativo). Sin embargo, la auditoría revela **brechas estructurales críticas entre sistemas que impiden la causalidad circular y la emergencia orgánica**:

1. **Desconexión entre Geografía Real y Trayectorias Humanas:**
   - Existe una base de datos SQLite con 151.251 objetos geográficos (`geography.sqlite`) y un enrutador Dijkstra sobre vías OSM reales (`osm_router.py`).
   - Sin embargo, los humanos en `SimulationRunner` se desplazan entre 16 waypoints abstractos mediante **teletransportación instantánea** (`activity_ticks_remaining = 1; current_location_id = target_loc_id` en `saltbor/population/human.py:469-472`).
   - No existe un motor que calcule y avance paso a paso la posición física del individuo a lo largo de la red vial considerando velocidad real (caminata vs vehículo), inclinación del terreno, clima (lluvia torrencial), fatiga física o bloqueos de vías (inundaciones, derrumbes).

2. **Lugares Planos sin Jerarquía de Capacidades:**
   - Los establecimientos y ubicaciones son en su mayoría meras etiquetas o registros en diccionarios.
   - Un centro comercial o mercado no modela adecuadamente su horario de apertura/cierre, capacidad máxima simultánea, puestos internos, inventario disponible o personal laboral presente.
   - Un hospital o clínica de salud no tiene camas limitadas ni requiere personal médico activo para atender pacientes; en `ExtensionRuntime`, el tratamiento se decide por probabilidad estocástica sin importar la saturación hospitalaria.

3. **Fragmentación del Ciclo de Vida Cotidiana:**
   - Las decisiones en `human.update()` se toman de forma reactiva tick a tick mediante una función de utilidad aislada (`DecisionEngine.decide()`).
   - No existe una noción de planificación cotidiana estructurada (despertar, higiene, desayuno, desplazamiento al trabajo, jornada laboral, almuerzo, compras en el camino, regreso al hogar, cena, convivencia familiar, descanso nocturno), con capacidad de improvisación, retraso o abandono ante emergencias.

4. **Fuga y Asimetría de la Causalidad Ambiental:**
   - Existen eventos de desastres climáticos (tormentas, inundaciones en quebradas, derrumbes en el Cerro Guazapa o Suchitoto), pero sus efectos no alteran la navegabilidad de la red vial en tiempo real ni impiden físicamente que un trabajador asista a su puesto.
   - La cadena causal: **Tormenta $\to$ Vía Bloqueada $\to$ Retraso o Cancelación $\to$ Pérdida de Ingreso Diario $\to$ Estrés Familiar $\to$ Solicitud de Ayuda Social $\to$ Registro en Memoria Histórica** existe como aspiración teórica pero está fracturada en su ejecución dinámica.

5. **Discrepancias Backend vs Frontend:**
   - La interfaz visual contiene paneles para visualizar indicadores macro, empleo, vivienda, psicología y mapa GIS.
   - Sin embargo, los inspectores de lugar carecen de desglose en vivo de capacidad, inventario y ocupantes simultáneos; la línea temporal muestra eventos aislados pero no permite la inspección del grafo causal retrospectivo (por qué ocurrió y qué consecuencias produjo).
   - El endpoint `/api/geography/geojson` requería parámetros estrictos de bounding box que fallaban cuando el visor frontend no delimitaba el frustum correctamente.

---

## 2. INVENTARIO Y CLASIFICACIÓN DE MOTORES EXISTENTES

Se evaluaron 122 subsistemas y motores del repositorio. A continuación se resume la clasificación técnica obligatoria:

| Clasificación | Definición | Cantidad de Subsistemas |
|:---|:---|:---:|
| **IMPLEMENTED** | Existe código funcional, estructuras de datos y métodos definidos. | 122 |
| **INTEGRATED** | Participa directamente en el ciclo real de simulación (`SimulationRunner.step()`, `ExtensionRuntime.step()` u orquestador activo). | 48 |
| **OBSERVABLE** | Sus estados, eventos o métricas pueden inspeccionarse mediante API REST y UI. | 36 |
| **VALIDATED** | Dispone de pruebas empíricas rigurosas y experimentos reproducibles en el banco de pruebas. | 34 |
| **DORMANT** | Existe código implementado, pero no se instancia ni ejecuta en la simulación activa (solo tests aislados). | 38 |
| **PARTIAL** | Opera en el runner pero con atajos sintéticos, teletransportación o sin propagación causal completa. | 36 |

### Motores Específicos Auditados

1. **`SyntheticHuman` / `PopulationRegistry`:**
   - **Estado:** INTEGRATED, OBSERVABLE, VALIDATED.
   - **Contrato:** Posee identidad inmutable (UUIDv5 determinista con semilla), `PhysicalState`, `PsychologicalState`, `Personality`, `EmotionState`, `MemoryEngine`, `GoalAutonomyLifecycle`.
   - **Gaps detectados:** La actualización de posición física es instantánea; no mantiene trayectoria continua en tránsito.

2. **`PsychologicalEngine` (Fase 1.7):**
   - **Estado:** INTEGRATED, OBSERVABLE, VALIDATED.
   - **Contrato:** Orquesta evaluación OCC, 26 estrategias de afrontamiento, desregulación/crisis, apoyo social transaccional, memoria asociativa y LOD cognitivo.
   - **Gaps detectados:** Falta acoplar el estrés por retrasos en el tráfico y la desesperación por desabastecimiento en comercios locales.

3. **`WorldHumanInteractionEngine` / `EnvironmentalHazardProfile`:**
   - **Estado:** PARTIAL, INTEGRATED.
   - **Contrato:** Evalúa riesgo de agua contaminada, genera desechos per cápita y permite faenas comunales de limpieza.
   - **Gaps detectados:** No bloquea físicamente caminos ni evalúa riesgos de deslave dinámicos sobre la red de transporte.

4. **`OSMRoadNetwork` / `osm_router.py`:**
   - **Estado:** IMPLEMENTED, VALIDATED (en tests aislados y endpoint REST).
   - **Contrato:** Enrutamiento Dijkstra sobre 121.344 tramos de vías reales de El Salvador con tiempos por clase de vía.
   - **Gaps detectados:** **DORMANT en la simulación activa.** Los agentes no consultan este enrutador en `human.update()`, sino que se teletransportan entre waypoints predefinidos.

5. **`CommercialEngine` / `EstablishmentCatalog`:**
   - **Estado:** PARTIAL, INTEGRATED.
   - **Contrato:** 7 intenciones de visita (mirar vitrinas sin comprar, comparar precios, compra directa, cenar pupusas).
   - **Gaps detectados:** No restringe el acceso si el establecimiento está físicamente cerrado por horario o fuera de capacidad de atención.

6. **`LaborMarketEngine` / `HousingEngine`:**
   - **Estado:** INTEGRATED, OBSERVABLE, VALIDATED.
   - **Contrato:** Vacantes de empleo, salarios de reserva, contratos de alquiler, mora y desalojos.
   - **Gaps detectados:** El desplazamiento entre vivienda y trabajo no incurre en costes de transporte ni tiempo real de viaje.

7. **`HealthEngine` / `MisfortuneEngine`:**
   - **Estado:** INTEGRATED, OBSERVABLE, VALIDATED.
   - **Contrato:** Enfermedades diarreicas, dengue, respiratorias, accidentes laborales y de tráfico, desastres naturales.
   - **Gaps detectados:** La búsqueda de atención médica en la clínica no consume tiempo de espera ni depende de la disponibilidad de insumos farmacéuticos o médicos.

8. **`CausalEventGraph` / `EventBus`:**
   - **Estado:** INTEGRATED, OBSERVABLE, VALIDATED.
   - **Contrato:** Captura eventos, enlaza causas y efectos en un grafo acíclico dirigido.
   - **Gaps detectados:** No propaga la causalidad retardada desde el bloqueo vial hasta la desestabilización económica del hogar de manera automática sin intervención explícita.

9. **`HistoricalMemoryEngine` / `SalvadoranHistoricalMemoryEngine`:**
   - **Estado:** DORMANT en el runner general (solo llamado en eventos puntuales o tests).
   - **Contrato:** Registra narrativas culturales colectivas e interpretaciones históricas comunitarias.
   - **Gaps detectados:** No absorbe automáticamente las crisis comunitarias mayores (como inundaciones graves o hambrunas locales) para transformarlas en memoria histórica oral o de ADESCO.

---

## 3. IDENTIFICACIÓN DE DISCREPANCIAS Y DEUDA TÉCNICA

### 3.1. Funcionalidades en Backend ausentes en Frontend
- El frontend no visualiza la red de rutas activas de los agentes en tránsito continuo sobre el mapa (solo los muestra agrupados por nodo de destino).
- El grafo causal (`CausalEventGraph`) se calcula en el backend pero el frontend solo despliega una tabla plana de eventos sin navegación visual de causa-raíz y consecuencias derivadas.
- El inventario detallado de bienes de los comercios (maíz, frijol, queso, medicamentos) no tiene vista de inspección en el mapa.

### 3.2. Funcionalidades en Frontend desconectadas del Estado Real
- El modal de intervención permitía "inyecciones macroeconómicas" o "convocatorias de asambleas", pero algunas de estas acciones emitían eventos sin garantizar que el backend las incorporara a la dinámica contable de las familias afectadas.
- En la visualización de capas GIS, si la base de datos `geography.sqlite` no estaba montada en memoria en una vista regional amplia, MapLibre arrojaba errores en consola.

### 3.3. Determinismo y Manejo de Semillas
- Se identificó que `saltbor/cognition/decision/engine.py` y `saltbor/cognition/personality/traits.py` importaban el módulo estándar `random` de Python en lugar de utilizar exclusivamente `np.random.Generator` suministrado por `SimulationRunner.master_rng` o un RNG derivado de la semilla de cada individuo. Esto provocaba que pruebas de reproducibilidad estricta como `EXP_11_B` pudieran fallar intermitentemente cuando se ejecutaba la suite completa de pruebas.

---

## 4. ESTADO DE PERSISTENCIA Y MIGRACIONES

- El esquema de base de datos actual es la **Versión 4** (`_SCHEMA_VERSION = 4` en `saltbor/persistence/schema.py`).
- Incluye tablas para: `humans`, `memories_episodic`, `memories_semantic`, `memories_procedural`, `relationships`, `events_log`, `simulation_state`, `goals`, `cultural_elements`, `loans`, `businesses`, `institutions`, `multi_relationships`, `geo_entities`, `geo_establishments`, `social_edges`, `communities`, `collective_enterprises`, `reputation_profiles`, `labor_vacancies`, `labor_contracts`, `housing_units`, `housing_leases`, `commercial_establishments`, `psychology_timeline`.
- El estado de la extensión se persiste como documento JSON estructurado en `simulation_state` bajo la clave `phase15_extension`.
- La persistencia utiliza una transacción única en `checkpoint()` con soporte para transacciones anidadas, evitando bloqueos de WAL y minimizando el tiempo de I/O en disco.
- **Requisito para Fase 1.8:** Mantener compatibilidad absoluta con la versión 4, incorporando tablas e índices para trayectorias de viaje activas, bloqueos viales y capacidades físicas de lugares sin romper el esquema existente ni corromper datos anteriores.
